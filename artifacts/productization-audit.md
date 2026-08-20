# SENTINEL-CHAIN: Productization & Real-Worldization Audit
**Date:** 2026-08-20  
**Status:** PHASE 0 COMPLETE  
**Primary Architect:** Principal AI Product & System Architect

---

## 1. System Inventory & Classification Matrix

| Component / Pattern | Current Implementation | Target Classification | Planned Migration Action |
|---|---|---|---|
| **Target URL** | Fixed `http://localhost:8000/api/proxy/target` in `config.py` | **MIGRATION TARGET** | Generalize to dynamic user-submitted URL with SSRF/private IP protection, live inspection engine, and multi-target registry. |
| **Data Model (`ThreatRecord`)** | Hardcoded fields (`cve_id`, `severity`, `Exploit-DB`) | **MIGRATION TARGET** | Expand to generalized `Target`, `ExtractionSchema`, `ScraperDefinition`, `RunResult`, and dynamic record storage. Keep `threat_records` for legacy/demo compatibility. |
| **Bright Data CLI Runner** | Hardcoded default collector `c_sentinel_cve_threats` | **EXTEND** | Support dynamic `collector_id` mapped per scraper definition and target, preserving safe `shell=False` execution. |
| **Gemini Diagnoser** | Prompts tuned for `cve_id` and table/card mutations | **EXTEND / GENERALIZE** | Generalize prompt and heuristic fallback to work with arbitrary target schemas (e.g. `price`, `title`, `author`, `status`, `name`) across table, card-grid, and article/document structures. |
| **Recovery Orchestrator** | Executes single collector cycle; calls `_persist_threat_records` | **EXTEND / GENERALIZE** | Parameterize with `target_id`, `scraper_id`, and `schema`. Persist dynamic run results and emit enriched SSE telemetry frames. |
| **Playwright Evidence Collector** | Pruned DOM + AOM tree snapshot | **KEEP & ENHANCE** | Proven 10/10 technical moat. Add screenshot base64, candidate selector extraction, and page type detection. |
| **Deterministic Validator** | Regex for dangerous shell tokens & DOM selector query check | **KEEP & EXPAND** | Retain 100% of the injection defense while validating arbitrary target selectors against pruned DOM. |
| **Chaos Proxy** | Mutations: `clean`, `class_renamed`, `table_to_cards`, `deep_nesting` | **KEEP UNDER DEMO/TEST MODE** | Isolate to the controlled demo target so production scrapers operate on real live websites without synthetic interference. |
| **React Flow DAG** | Hardcoded 8-stage pipeline | **KEEP & ADAPT** | Wire to real-time dynamic SSE events with target-specific lifecycle states. |
| **Frontend UI** | SecOps Cockpit + GSAP Landing Page | **EXPAND TO FULL PLATFORM** | Add Target Onboarding (URL + Search Discovery), Inspection View, Schema Intent & Reviewer, Target Workspace, Results Table, and Monitoring Scheduler. |

---

## 2. Dependency Map of Hardcoded Assumptions

1. **Assumptions in `backend/app/models/domain.py`**:
   - `ThreatRecord` contains `cve_id`, `severity`, `source="Exploit-DB"`.
   - *Fix:* Create `Target`, `TargetInspection`, `ExtractionSchema`, `ExtractionField`, `ScraperDefinition`, `ScraperRun`, `RunResult`, `MonitorSchedule`.

2. **Assumptions in `backend/app/storage/db.py`**:
   - Only `threat_records`, `pipeline_events`, and `scraper_jobs` tables exist.
   - *Fix:* Add `targets`, `extraction_schemas`, `scraper_definitions`, `scraper_runs`, `run_results`, `monitors`, `audit_events` tables with proper WAL foreign keys.

3. **Assumptions in `backend/app/engine/recovery_orchestrator.py`**:
   - Target field assumed `cve_id`. Result parsing assumed CVE fields.
   - *Fix:* Accept `target_id`, `schema_id`, `target_field` list, dynamic record normalizer.

4. **Assumptions in `backend/app/engine/diagnoser.py`**:
   - Default heuristic and prompt tailored for CVE tags.
   - *Fix:* Make diagnoser target-schema agnostic with generic failure taxonomy (`SELECTOR_DRIFT`, `DOM_RESTRUCTURE`, `FIELD_MISSING`, `SCHEMA_MISMATCH`, etc.).

---

## 3. Productization Invariants
- ✅ Real user URL onboarding with SSRF protection (reject private IP ranges `127.0.0.0/8`, `10.0.0.0/8`, `192.168.0.0/16`, `169.254.0.0/16`, AWS metadata `169.254.169.254`, etc. unless in explicit local test mode).
- ✅ Real Playwright + HTTP target inspection (DOM, AOM, semantic cards/tables, candidate fields).
- ✅ Natural language extraction intent parsed into strongly typed `ExtractionSchema` via Gemini 3.7 Flash.
- ✅ Human review and live editing of extraction schema.
- ✅ Dynamic target-specific scraper runs, real dynamic data display, and scheduled monitoring.
- ✅ Target-agnostic self-healing across 3 target classes: Tables, Card Grids, and Article/Document lists.
- ✅ Clean visual distinction between Real Production Data vs Demo/Simulated Data.
