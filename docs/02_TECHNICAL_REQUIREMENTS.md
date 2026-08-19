# 02 TECHNICAL REQUIREMENTS
| ID | REQUIREMENT | RATIONALE | DEPENDENCIES |
|---|---|---|---|
| TR-01 | FastAPI Backend | Async I/O needed for CLI wrapping and SSE streaming | Python 3.11+ |
| TR-02 | SQLite WAL | Concurrent reads (SSE) during write operations | `aiosqlite` |
| TR-03 | React Flow UI | Visual DAG mapping required for Suit-Up judging | `@xyflow/react` |
| TR-04 | Playwright (Evidence) | Needed for Screenshots and Accessibility Object Model (AOM) extraction | `playwright` |
| TR-05 | Gemini 3.1 Pro | Multimodal spatial reasoning over complex DOMs | `google-generativeai` |
| TR-06 | Subprocess (No Shell) | Security boundary for CLI execution | `asyncio.create_subprocess_exec` |
