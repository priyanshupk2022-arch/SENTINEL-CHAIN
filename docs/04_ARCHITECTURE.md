# 04 SYSTEM ARCHITECTURE
## Logical Flow
1. **FastAPI Scheduler** -> triggers Scraper Run.
2. **Bright Data Cloud** -> hits **Chaos Proxy** -> receives HTML (mutated if Chaos=1).
3. **Validator** -> detects failure.
4. **Evidence Collector (Playwright)** -> extracts Screenshot + AOM.
5. **Diagnoser (Gemini 3.1 Pro)** -> outputs `RepairProposal`.
6. **Queue Worker** -> executes `bdata heal` -> polls `status` -> executes `bdata approve`.
7. **FastAPI Scheduler** -> triggers Re-run -> Validator -> Healthy.

## Runtime Architecture
*   **Backend:** 1 Uvicorn worker (Pinned to 1 for `asyncio.Queue` singleton).
*   **Database:** SQLite (WAL mode).
*   **Frontend:** Next.js 15 SPA.
