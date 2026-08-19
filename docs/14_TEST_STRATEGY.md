# 14 TEST STRATEGY
*   **Unit:** Pytest for Pydantic schemas and CLI argument construction.
*   **Integration:** Chaos Proxy validation (ensuring CSS is actually scrambled).
*   **E2E (The Demo Run):** Healthy -> Enable Chaos -> Detect Failure -> Heal -> Approve -> Re-run -> Healthy.

## Hackathon MVP Constraints
**OMISSION:** Testing for distributed queue drops, WAL concurrency locks, and pod restart failure modes is explicitly omitted. This is an accepted Hackathon MVP constraint to maximize feature velocity within the 3-day window.
