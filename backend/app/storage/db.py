import aiosqlite
import asyncio
import json
import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.app.models.domain import ThreatRecord, TelemetryEvent

logger = logging.getLogger("sentinel.storage")

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
        await self._conn.execute("PRAGMA foreign_keys=ON;")
        await self._conn.execute("PRAGMA busy_timeout=30000;")

        # Create tables
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

        await self._conn.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            node_id TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            payload TEXT
        );
        """)

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

    async def get_journal_mode(self) -> str:
        if not self._conn:
            await self.initialize()
        cursor = await self._conn.execute("PRAGMA journal_mode;")
        row = await cursor.fetchone()
        return row[0] if row else "wal"

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
                        record.cve_id,
                        record.title,
                        record.severity,
                        record.published_date,
                        record.url,
                        record.source,
                        payload_str,
                        ts_str
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
                    INSERT INTO pipeline_events (timestamp, node_id, status, message, payload)
                    VALUES (?, ?, ?, ?, ?)
                    """, (ts_str, event.node_id, event.status, event.message, payload_str))
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
        SELECT id, timestamp, node_id, status, message, payload
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
