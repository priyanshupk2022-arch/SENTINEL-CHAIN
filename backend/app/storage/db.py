import aiosqlite
import asyncio
import json
import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.app.models.domain import (
    Target, TargetStatus, TargetInspection, ExtractionSchema, ExtractionField,
    ScraperDefinition, ScraperRun, DynamicRecord, ThreatRecord, TelemetryEvent, MonitorSchedule
)

logger = logging.getLogger("sentinel.storage")

DEFAULT_TARGET_ID = "default_target"

class DatabaseManager:
    _instances: Dict[str, "DatabaseManager"] = {}

    def __new__(cls, db_path: Optional[str] = None):
        actual_path = db_path or os.path.join(os.getcwd(), "data", "sentinel_chain.db")
        norm_path = os.path.normpath(os.path.abspath(actual_path))
        if norm_path not in cls._instances:
            instance = super(DatabaseManager, cls).__new__(cls)
            instance.db_path = norm_path
            instance._conn = None
            instance._lock = None
            instance._initialized = False
            cls._instances[norm_path] = instance
        return cls._instances[norm_path]

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def initialize(self):
        if self._conn is not None:
            return
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._lock = asyncio.Lock()
        self._conn = await aiosqlite.connect(self.db_path, timeout=30.0)
        self._conn.row_factory = aiosqlite.Row
        
        # Configure WAL mode & busy timeout for high concurrency
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA synchronous=NORMAL;")
        await self._conn.execute("PRAGMA foreign_keys=OFF;")  # Loose enforcement for backward-compat
        await self._conn.execute("PRAGMA busy_timeout=30000;")

        # 1. Product Targets Table
        await self._conn.execute("""
        CREATE TABLE IF NOT EXISTS targets (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            domain TEXT,
            status TEXT DEFAULT 'READY',
            health REAL DEFAULT 1.0,
            monitoring_enabled INTEGER DEFAULT 0,
            schedule TEXT DEFAULT 'MANUAL',
            last_run TEXT,
            last_healed TEXT,
            is_demo INTEGER DEFAULT 0,
            configuration TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)

        # Seed default demo target
        now_iso = datetime.utcnow().isoformat()
        await self._conn.execute("""
        INSERT OR IGNORE INTO targets (id, name, url, domain, status, health, monitoring_enabled, schedule, is_demo, configuration, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            DEFAULT_TARGET_ID, "Exploit-DB Security Target", "http://127.0.0.1:8000/api/proxy/target",
            "127.0.0.1", "READY", 1.0, 0, "MANUAL", 1, "{}", now_iso, now_iso
        ))

        # 2. Target Inspections Table
        await self._conn.execute("""
        CREATE TABLE IF NOT EXISTS target_inspections (
            id TEXT PRIMARY KEY,
            target_id TEXT NOT NULL,
            url TEXT NOT NULL,
            final_url TEXT,
            status_code INTEGER,
            page_title TEXT,
            page_type TEXT,
            rendering_required INTEGER DEFAULT 0,
            candidate_fields TEXT,
            candidate_selectors TEXT,
            candidate_containers TEXT,
            sample_records TEXT,
            warnings TEXT,
            inspection_timestamp TEXT NOT NULL
        );
        """)

        # 3. Extraction Schemas Table
        await self._conn.execute("""
        CREATE TABLE IF NOT EXISTS extraction_schemas (
            id TEXT PRIMARY KEY,
            target_id TEXT NOT NULL,
            name TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            intent_prompt TEXT,
            fields TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)

        # 4. Scraper Definitions Table
        await self._conn.execute("""
        CREATE TABLE IF NOT EXISTS scraper_definitions (
            id TEXT PRIMARY KEY,
            target_id TEXT NOT NULL,
            schema_id TEXT,
            name TEXT NOT NULL,
            collector_id TEXT NOT NULL,
            instructions TEXT,
            status TEXT DEFAULT 'ACTIVE',
            version INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)

        # 5. Scraper Runs Table
        await self._conn.execute("""
        CREATE TABLE IF NOT EXISTS scraper_runs (
            id TEXT PRIMARY KEY,
            target_id TEXT NOT NULL,
            scraper_id TEXT,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            status TEXT NOT NULL,
            records_count INTEGER DEFAULT 0,
            duration_ms REAL DEFAULT 0.0,
            recovered INTEGER DEFAULT 0,
            error TEXT
        );
        """)

        # 6. Dynamic Records Table (Target-Agnostic)
        await self._conn.execute("""
        CREATE TABLE IF NOT EXISTS dynamic_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id TEXT NOT NULL,
            run_id TEXT NOT NULL,
            data TEXT NOT NULL,
            is_simulated INTEGER DEFAULT 0,
            timestamp TEXT NOT NULL
        );
        """)

        # 7. Legacy Threat Records Table (Preserved for compatibility)
        await self._conn.execute("""
        CREATE TABLE IF NOT EXISTS threat_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cve_id TEXT UNIQUE NOT NULL,
            title TEXT,
            severity TEXT DEFAULT 'UNKNOWN',
            published_date TEXT,
            url TEXT,
            source TEXT DEFAULT 'Exploit-DB',
            raw_payload TEXT,
            timestamp TEXT NOT NULL
        );
        """)

        # 8. Pipeline Telemetry Events Table
        await self._conn.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            target_id TEXT,
            node_id TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            payload TEXT
        );
        """)

        # Safe schema migration check for target_id in pipeline_events
        try:
            await self._conn.execute("ALTER TABLE pipeline_events ADD COLUMN target_id TEXT;")
        except Exception:
            pass  # Already exists

        # 9. Scraper Jobs Queue Table
        await self._conn.execute("""
        CREATE TABLE IF NOT EXISTS scraper_jobs (
            job_id TEXT PRIMARY KEY,
            collector_id TEXT NOT NULL,
            target_url TEXT NOT NULL,
            state TEXT NOT NULL,
            recovered INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        await self._conn.commit()
        self._initialized = True
        logger.info(f"Database initialized at {self.db_path} with WAL mode.")

    async def get_journal_mode(self) -> str:
        if not self._conn:
            await self.initialize()
        cursor = await self._conn.execute("PRAGMA journal_mode;")
        row = await cursor.fetchone()
        return row[0] if row else "wal"

    # =========================================================================
    # TARGET CRUD OPERATIONS
    # =========================================================================

    async def save_target(self, target: Target) -> bool:
        if not self._conn:
            await self.initialize()
        config_str = json.dumps(target.configuration) if target.configuration else "{}"
        last_run_str = target.last_run.isoformat() if target.last_run else None
        last_healed_str = target.last_healed.isoformat() if target.last_healed else None
        created_str = target.created_at.isoformat() if hasattr(target.created_at, "isoformat") else str(target.created_at)
        updated_str = target.updated_at.isoformat() if hasattr(target.updated_at, "isoformat") else str(target.updated_at)

        async with self._get_lock():
            await self._conn.execute("""
            INSERT INTO targets (id, name, url, domain, status, health, monitoring_enabled, schedule, last_run, last_healed, is_demo, configuration, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                url=excluded.url,
                domain=excluded.domain,
                status=excluded.status,
                health=excluded.health,
                monitoring_enabled=excluded.monitoring_enabled,
                schedule=excluded.schedule,
                last_run=excluded.last_run,
                last_healed=excluded.last_healed,
                is_demo=excluded.is_demo,
                configuration=excluded.configuration,
                updated_at=excluded.updated_at
            """, (
                target.id, target.name, target.url, target.domain, target.status.value,
                target.health, 1 if target.monitoring_enabled else 0, target.schedule.value,
                last_run_str, last_healed_str, 1 if target.is_demo else 0,
                config_str, created_str, updated_str
            ))
            await self._conn.commit()
        return True

    async def get_target(self, target_id: str) -> Optional[Target]:
        if not self._conn:
            await self.initialize()
        cursor = await self._conn.execute("SELECT * FROM targets WHERE id = ?", (target_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        r = dict(row)
        return Target(
            id=r["id"],
            name=r["name"],
            url=r["url"],
            domain=r["domain"] or "",
            status=TargetStatus(r["status"]),
            health=float(r["health"]),
            monitoring_enabled=bool(r["monitoring_enabled"]),
            schedule=MonitorSchedule(r["schedule"] or "MANUAL"),
            last_run=datetime.fromisoformat(r["last_run"]) if r["last_run"] else None,
            last_healed=datetime.fromisoformat(r["last_healed"]) if r["last_healed"] else None,
            is_demo=bool(r["is_demo"]),
            configuration=json.loads(r["configuration"]) if r["configuration"] else {},
            created_at=datetime.fromisoformat(r["created_at"]),
            updated_at=datetime.fromisoformat(r["updated_at"])
        )

    async def list_targets(self) -> List[Target]:
        if not self._conn:
            await self.initialize()
        cursor = await self._conn.execute("SELECT * FROM targets ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        results = []
        for row in rows:
            r = dict(row)
            results.append(Target(
                id=r["id"],
                name=r["name"],
                url=r["url"],
                domain=r["domain"] or "",
                status=TargetStatus(r["status"]),
                health=float(r["health"]),
                monitoring_enabled=bool(r["monitoring_enabled"]),
                schedule=MonitorSchedule(r["schedule"] or "MANUAL"),
                last_run=datetime.fromisoformat(r["last_run"]) if r["last_run"] else None,
                last_healed=datetime.fromisoformat(r["last_healed"]) if r["last_healed"] else None,
                is_demo=bool(r["is_demo"]),
                configuration=json.loads(r["configuration"]) if r["configuration"] else {},
                created_at=datetime.fromisoformat(r["created_at"]),
                updated_at=datetime.fromisoformat(r["updated_at"])
            ))
        return results

    async def delete_target(self, target_id: str) -> bool:
        if not self._conn:
            await self.initialize()
        async with self._get_lock():
            await self._conn.execute("DELETE FROM targets WHERE id = ?", (target_id,))
            await self._conn.commit()
        return True

    # =========================================================================
    # TARGET INSPECTION OPERATIONS
    # =========================================================================

    async def save_inspection(self, insp: TargetInspection) -> bool:
        if not self._conn:
            await self.initialize()
        async with self._get_lock():
            await self._conn.execute("""
            INSERT OR REPLACE INTO target_inspections (
                id, target_id, url, final_url, status_code, page_title, page_type, rendering_required,
                candidate_fields, candidate_selectors, candidate_containers, sample_records, warnings, inspection_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                insp.id, insp.target_id, insp.url, insp.final_url, insp.status_code,
                insp.page_title, insp.page_type.value, 1 if insp.rendering_required else 0,
                json.dumps(insp.candidate_fields), json.dumps(insp.candidate_selectors),
                json.dumps(insp.candidate_containers), json.dumps(insp.sample_records),
                json.dumps(insp.warnings), insp.inspection_timestamp.isoformat()
            ))
            await self._conn.commit()
        return True

    async def get_latest_inspection(self, target_id: str) -> Optional[Dict[str, Any]]:
        if not self._conn:
            await self.initialize()
        cursor = await self._conn.execute("""
        SELECT * FROM target_inspections WHERE target_id = ? ORDER BY inspection_timestamp DESC LIMIT 1
        """, (target_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        r = dict(row)
        for key in ["candidate_fields", "candidate_selectors", "candidate_containers", "sample_records", "warnings"]:
            if r.get(key):
                try:
                    r[key] = json.loads(r[key])
                except Exception:
                    pass
        return r

    # =========================================================================
    # EXTRACTION SCHEMA OPERATIONS
    # =========================================================================

    async def save_schema(self, schema: ExtractionSchema) -> bool:
        if not self._conn:
            await self.initialize()
        fields_str = json.dumps([f.model_dump() for f in schema.fields])
        async with self._get_lock():
            await self._conn.execute("""
            INSERT OR REPLACE INTO extraction_schemas (id, target_id, name, version, intent_prompt, fields, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                schema.id, schema.target_id, schema.name, schema.version,
                schema.intent_prompt, fields_str,
                schema.created_at.isoformat(), schema.updated_at.isoformat()
            ))
            await self._conn.commit()
        return True

    async def get_latest_schema(self, target_id: str) -> Optional[ExtractionSchema]:
        if not self._conn:
            await self.initialize()
        cursor = await self._conn.execute("""
        SELECT * FROM extraction_schemas WHERE target_id = ? ORDER BY version DESC LIMIT 1
        """, (target_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        r = dict(row)
        fields_raw = json.loads(r["fields"]) if r["fields"] else []
        fields = [ExtractionField(**f) for f in fields_raw]
        return ExtractionSchema(
            id=r["id"],
            target_id=r["target_id"],
            name=r["name"],
            version=r["version"],
            intent_prompt=r["intent_prompt"],
            fields=fields,
            created_at=datetime.fromisoformat(r["created_at"]),
            updated_at=datetime.fromisoformat(r["updated_at"])
        )

    # =========================================================================
    # SCRAPER DEFINITION OPERATIONS
    # =========================================================================

    async def save_scraper_def(self, scraper: ScraperDefinition) -> bool:
        if not self._conn:
            await self.initialize()
        async with self._get_lock():
            await self._conn.execute("""
            INSERT OR REPLACE INTO scraper_definitions (id, target_id, schema_id, name, collector_id, instructions, status, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scraper.id, scraper.target_id, scraper.schema_id, scraper.name,
                scraper.collector_id, scraper.instructions, scraper.status,
                scraper.version, scraper.created_at.isoformat(), scraper.updated_at.isoformat()
            ))
            await self._conn.commit()
        return True

    async def get_scraper_def(self, target_id: str) -> Optional[ScraperDefinition]:
        if not self._conn:
            await self.initialize()
        cursor = await self._conn.execute("""
        SELECT * FROM scraper_definitions WHERE target_id = ? ORDER BY version DESC LIMIT 1
        """, (target_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        r = dict(row)
        return ScraperDefinition(
            id=r["id"],
            target_id=r["target_id"],
            schema_id=r["schema_id"],
            name=r["name"],
            collector_id=r["collector_id"],
            instructions=r["instructions"] or "",
            status=r["status"],
            version=r["version"],
            created_at=datetime.fromisoformat(r["created_at"]),
            updated_at=datetime.fromisoformat(r["updated_at"])
        )

    # =========================================================================
    # DYNAMIC RECORD & RUN OPERATIONS
    # =========================================================================

    async def save_dynamic_record(self, record: DynamicRecord) -> bool:
        if not self._conn:
            await self.initialize()
        data_str = json.dumps(record.data)
        async with self._get_lock():
            await self._conn.execute("""
            INSERT INTO dynamic_records (target_id, run_id, data, is_simulated, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """, (
                record.target_id, record.run_id, data_str,
                1 if record.is_simulated else 0, record.timestamp.isoformat()
            ))
            await self._conn.commit()
        return True

    async def get_target_records(self, target_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        if not self._conn:
            await self.initialize()
        cursor = await self._conn.execute("""
        SELECT id, target_id, run_id, data, is_simulated, timestamp
        FROM dynamic_records
        WHERE target_id = ?
        ORDER BY id DESC
        LIMIT ?
        """, (target_id, limit))
        rows = await cursor.fetchall()
        result = []
        for r in rows:
            row_dict = dict(r)
            if row_dict.get("data"):
                try:
                    row_dict["data"] = json.loads(row_dict["data"])
                except Exception:
                    pass
            result.append(row_dict)
        return result

    # =========================================================================
    # LEGACY / TELEMETRY OPERATIONS (PRESERVED)
    # =========================================================================

    async def save_threat_record(self, record: ThreatRecord) -> bool:
        if not self._conn:
            await self.initialize()
        payload_str = json.dumps(record.raw_payload) if record.raw_payload else None
        ts_str = record.timestamp.isoformat() if hasattr(record.timestamp, "isoformat") else str(record.timestamp)

        for attempt in range(5):
            try:
                async with self._get_lock():
                    await self._conn.execute("""
                    INSERT INTO threat_records (cve_id, title, severity, published_date, url, source, raw_payload, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(cve_id) DO UPDATE SET
                        title=excluded.title,
                        severity=excluded.severity,
                        published_date=excluded.published_date,
                        url=excluded.url,
                        raw_payload=excluded.raw_payload,
                        timestamp=excluded.timestamp
                    """, (
                        record.cve_id, record.title, record.severity, record.published_date,
                        record.url, record.source, payload_str, ts_str
                    ))
                    await self._conn.commit()
                return True
            except Exception as e:
                if "locked" in str(e).lower() and attempt < 4:
                    await asyncio.sleep(0.05 * (2 ** attempt))
                    continue
                logger.warning(f"Failed to save threat record: {e}")
                return False
        return False

    async def get_recent_threats(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self._conn:
            await self.initialize()
        cursor = await self._conn.execute("""
        SELECT id, cve_id, title, severity, published_date, url, source, raw_payload, timestamp
        FROM threat_records
        ORDER BY id DESC
        LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        result = []
        for r in rows:
            row_dict = dict(r)
            if row_dict.get("raw_payload"):
                try:
                    row_dict["raw_payload"] = json.loads(row_dict["raw_payload"])
                except Exception:
                    pass
            result.append(row_dict)
        return result

    async def save_telemetry_event(self, event: TelemetryEvent) -> int:
        if not self._conn:
            await self.initialize()
        payload_str = json.dumps(event.payload) if event.payload else None
        ts_str = event.timestamp.isoformat() if hasattr(event.timestamp, "isoformat") else str(event.timestamp)

        for attempt in range(5):
            try:
                async with self._get_lock():
                    cursor = await self._conn.execute("""
                    INSERT INTO pipeline_events (timestamp, target_id, node_id, status, message, payload)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (ts_str, event.target_id, event.node_id, event.status, event.message, payload_str))
                    await self._conn.commit()
                    return cursor.lastrowid
            except Exception as e:
                if "locked" in str(e).lower() and attempt < 4:
                    await asyncio.sleep(0.05 * (2 ** attempt))
                    continue
                logger.warning(f"Failed to save telemetry event: {e}")
                return 0
        return 0

    async def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self._conn:
            await self.initialize()
        cursor = await self._conn.execute("""
        SELECT id, timestamp, target_id, node_id, status, message, payload
        FROM pipeline_events
        ORDER BY id DESC
        LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        result = []
        for r in rows:
            row_dict = dict(r)
            if row_dict.get("payload"):
                try:
                    row_dict["payload"] = json.loads(row_dict["payload"])
                except Exception:
                    pass
            result.append(row_dict)
        return result

    async def close(self):
        if self._conn:
            try:
                await self._conn.close()
            except Exception:
                pass
            self._conn = None
            self._lock = None
            self._initialized = False

# Aliases
SQLiteStorage = DatabaseManager
Database = DatabaseManager
