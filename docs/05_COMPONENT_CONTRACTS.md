# 05 COMPONENT CONTRACTS
*   **QueueManager:** Singleton `asyncio.Queue`. Enforces strict serial execution of CLI commands to prevent `.bdata` config locking.
*   **ChaosProxy:** FastAPI endpoint `GET /api/proxy/target`. Fetches live Exploit-DB, scrambles CSS if chaos is enabled, returns to Bright Data.
*   **EvidenceExtractor:** Headless Playwright. Input: URL. Output: `(Screenshot, AOM)`.
*   **Diagnoser:** Gemini wrapper. Input: `EvidenceBundle`. Output: `RepairProposal` (Pydantic).
*   **TelemetryHub:** Asyncio Event emitter. Broadcasts to `/api/stream`.
