# 12 RELIABILITY ARCHITECTURE
*   **CLI Hangs:** `asyncio.wait_for(timeout=30)` enforced on all subprocess calls. `SIGKILL` on timeout.
*   **Queue Overflow:** `asyncio.Queue(maxsize=10)`. Drops new requests if backlogged.
*   **Worker Crash:** State is ephemeral. If FastAPI restarts, pending repairs are lost. (Accepted Hackathon MVP constraint).
*   **LLM Hallucination:** 2 retries allowed. If schema fails repeatedly, pipeline halts.
