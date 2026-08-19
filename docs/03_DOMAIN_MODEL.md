# 03 DOMAIN MODEL
*   **ScraperJob:** Represents the Bright Data Collector. Lifecycle: IDLE -> RUNNING -> BROKEN -> HEALING -> AWAITING_APPROVAL -> IDLE.
*   **ThreatRecord:** Extracted CVE data (cve_id, severity, url).
*   **EvidenceBundle:** Context sent to LLM (Screenshot, AOM, Pruned HTML).
*   **RepairProposal:** Typed output from LLM (diagnosis, proposed_selector, repair_prompt).
*   **TelemetryEvent:** SSE packet (timestamp, node_id, status, payload).
