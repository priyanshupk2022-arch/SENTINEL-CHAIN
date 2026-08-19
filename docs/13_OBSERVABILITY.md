# 13 OBSERVABILITY
*   **SSE Events:** The primary observability vector. Emits `[DAG_NODE_ID, STATUS, MESSAGE]`.
*   **Terminal UI:** Next.js frontend includes a terminal pane that consumes the `stdout` of the backend subprocesses to prove to judges that real CLI commands are executing.
