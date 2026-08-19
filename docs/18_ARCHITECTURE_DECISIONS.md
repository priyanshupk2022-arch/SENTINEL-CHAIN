# 18 ARCHITECTURE DECISIONS (ADRs)
*   **ADR 1: Singleton asyncio.Queue.** Decided against Redis to reduce hackathon infrastructure bloat. Consequence: Must pin Uvicorn to 1 worker.
*   **ADR 2: Transparent Chaos Proxy.** Decided against local Playwright network interception because remote Bright Data scrapers bypass local intercepts. Consequence: Requires hosting a pass-through API.
*   **ADR 3: Subprocess `shell=False`.** Decided against arbitrary bash execution. Consequence: Secure execution boundary established.
