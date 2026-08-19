import aiosqlite
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.app.models.domain import ThreatRecord, TelemetryEvent

class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            data_dir = os.path.join(os.getcwd(), "data")
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, "sentinel_chain.db")
        else:
            self.db_path = db_path
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._conn: Optional[aiosqlite.Connection] = None

    async def initialize(self):
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        
        # Configure WAL mode for concurrent SSE reads & writes
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA synchronous=NORMAL;")
        await self._conn.execute("PRAGMA foreign_keys=ON;")

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
            collector_id TEXT PRIMARY KEY,
            target_url TEXT NOT NULL,
            state TEXT NOT NULL,
            last_run_at TEXT,
            last_healed_at TEXT,
            error_count INTEGER DEFAULT 0,
            schema_json TEXT
        );
        """)

        await self._conn.commit()

    async def get_journal_mode(self) -> str:
        if not self._conn:
            await self.initialize()
        cursor = await self._conn.execute("PRAGMA journal_mode;")
        row = await cursor.fetchone()
        return row[0] if row else ""

    async def save_threat_record(self, threat: ThreatRecord) -> bool:
        if not self._conn:
            await self.initialize()
        payload_str = json.dumps(threat.raw_payload) if threat.raw_payload else None
        ts_str = threat.timestamp.isoformat()
        try:
            await self._conn.execute("""
            INSERT INTO threat_records (cve_id, title, severity, published_date, url, source, raw_payload, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(cve_id) DO UPDATE SET
                title=excluded.title,
                severity=excluded.severity,
                url=excluded.url,
                raw_payload=excluded.raw_payload,
                timestamp=excluded.timestamp
            """, (threat.cve_id, threat.title, threat.severity, threat.published_date, threat.url, threat.source, payload_str, ts_str))
            await self._conn.commit()
            return True
        except Exception as e:
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
        ts_str = event.timestamp.isoformat()
        cursor = await self._conn.execute("""
        INSERT INTO pipeline_events (timestamp, node_id, status, message, payload)
        VALUES (?, ?, ?, ?, ?)
        """, (ts_str, event.node_id, event.status, event.message, payload_str))
        await self._conn.commit()
        return cursor.lastrowid

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
            await self._conn.close()
            self._conn = None
