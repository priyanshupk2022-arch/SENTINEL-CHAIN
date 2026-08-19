# 01 PRODUCT REQUIREMENTS DOCUMENT (PRD)
**Product:** SENTINEL-CHAIN
**Target Users:** SOC Analysts, CTI Researchers, Hackathon Judges.

## 1. Problem & Thesis
*   **Problem:** CTI scrapers break silently during DOM mutations (the "Exploit-to-Patch Gap"), causing blind spots.
*   **Thesis:** Combining Bright Data's cloud-healing with Gemini 3.1 Pro's spatial reasoning creates a zero-downtime intelligence feed.

## 2. Golden User Journey (SOC Analyst View)
1. SOC Analyst monitors the Palantir-style Threat Dashboard.
2. Exploit-DB mutates its CSS, attempting to blind the analyst to a new Zero-Day.
3. Sentinel autonomous pipeline detects the breakage; a visual DAG alerts the analyst that the feed is HEALING.
4. In the background, the pipeline self-heals via Bright Data without analyst intervention.
5. The pipeline resumes ingestion. The Zero-Day exploit appears on the dashboard without human engineering effort.

## 3. Core Requirements
*   **REQ-01:** System must orchestrate `bdata` CLI autonomously.
*   **REQ-02:** LLM output must be structurally validated before CLI construction.
*   **REQ-03:** Telemetry must be streamed to the UI via SSE for real-time visibility.
*   **REQ-04:** Demo requires a deterministic Chaos Proxy to force scraper failure on live cloud requests.
