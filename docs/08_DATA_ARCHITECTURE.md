# 08 DATA ARCHITECTURE
**Database:** SQLite (Hackathon MVP). `PRAGMA journal_mode=WAL;` is mandatory for concurrent SSE reads.

**Tables:**
1. `threat_records`: `id` (PK), `cve_id` (UNIQUE), `severity`, `timestamp`.
2. `pipeline_events`: `id` (PK), `node_id`, `status`, `message`, `timestamp`.

**Classification:** In-memory queues and SQLite are HACKATHON MVP. Not suitable for multi-node distributed production without Redis/Postgres.
