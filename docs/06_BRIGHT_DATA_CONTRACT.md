# 06 BRIGHT DATA CONTRACT
**Canonical Sequence:**
1. `bdata scraper run <id>` -> returns JSON.
2. `bdata scraper heal <id> "<prompt>"` -> Transitions collector to preview sandbox.
3. *POLLING LOOP:* Check `bdata scraper status` until `state == "awaiting_approval"`. Timeout 300s.
4. `bdata scraper approve <id>` -> Commits the code to production.
5. *PROPAGATION DELAY:* `asyncio.sleep(10)` (Assumption: Cloud takes a few seconds to propagate).
6. `bdata scraper run <id>` -> Verify recovery.

**Security & Concurrency:** All commands executed via `asyncio.create_subprocess_exec(*args)` to prevent Event Loop Deadlocks (FastAPI must remain unblocked to serve the Chaos Proxy).
