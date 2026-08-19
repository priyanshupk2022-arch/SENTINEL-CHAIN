# Feature Specification: SENTINEL-CHAIN
**Project Codename:** `SENTINEL-CHAIN` (Cybersecurity & Supply Chain Threat Hunter)  
**Hackathon:** "Into the Scrape-Verse" (WeMakeDevs × Bright Data, Aug 17–23, 2026)  
**Target Tracks:** 🥇 Grand Prize ($5,000 NVIDIA DGX Spark) · 🎨 Best UI (Apple iPad) · 💻 Clean Code (Keychron)  
**Created:** August 18, 2026  
**Status:** Approved Specification  

---

## 1. Executive Summary & Problem Context
In 2026, software supply chain attacks (such as the *Shai-Hulud Worm*, *Axios/LiteLLM poisoned releases*, and *xz-utils style latent backdoors*) infected hundreds of open-source packages, exfiltrating AWS and GitHub secrets from thousands of enterprise environments. Attackers increasingly distribute zero-day exploit PoCs, weaponized payload scripts, and exfiltrated credentials across ephemeral pastebins, security forums, and mutated GitHub repositories that vanish or alter layouts in under an hour.

Security teams (SOC analysts, Incident Responders, and DevOps leads) struggle with two fatal challenges:
1. **Scraper Fragility & Bot Blocks:** Threat portals and exploit repositories deploy aggressive anti-scraping protections (Cloudflare Turnstile, browser fingerprinting, and dynamic layout mutations) that break traditional scrapers.
2. **Alert Fatigue & Inactionable Data:** Raw security dumps are messy and unstructured. Teams need instant CVSS 4.0 severity scoring, exact affected package version matching, and an executable 1-click remediation command.

**SENTINEL-CHAIN** solves this by pairing Bright Data Scraper Studio & CLI (`bdata`) with an **Autonomous Self-Healing Sentinel Loop** and an **AI Threat Triage Engine** to deliver real-time, actionable cyber threat intelligence into a Palantir-grade Cyber War Room dashboard.

---

## 2. User Stories & Prioritized Journeys

### User Story 1: Autonomous Self-Healing Threat Stream (Priority: P1 - Hackathon Hero)
As a Security Engineer, I want the scraper pipeline to automatically detect when a threat feed (e.g. Exploit-DB or security advisory page) changes its DOM structure, trigger Bright Data's AI self-healing (`bdata scraper heal`), auto-approve the repair, and resume live threat ingestion without manual intervention or pipeline downtime.

* **Independent Test:** Inject a simulated schema/DOM mutation into a target scraper. Verify that the backend catches the failure, calls `bdata scraper heal`, applies `bdata scraper approve`, and resumes stream within < 45 seconds with 0 dropped threat records.
* **Acceptance Scenarios:**
  1. **Given** an active scraper stream from Exploit-DB, **When** the page mutates its CSS/DOM tree, **Then** the UI transitions from `GREEN (ACTIVE)` to `AMBER (HEALING_IN_PROGRESS)`, the heal loop executes, and the status returns to `GREEN (HEALED)` with the repair timeline logged.

### User Story 2: AI Threat Triage & Remediation Playbook (Priority: P1 - Core Intelligence)
As a SOC Analyst, I want incoming exploit dumps and CVE feeds to be parsed into structured intelligence: extracting CVE numbers, affected tech stacks/versions, CVSS 4.0 / EPSS exploitability scores, and an instant Bash/Terraform mitigation command.

* **Independent Test:** Ingest raw unformatted exploit text. Verify that Gemini Flash extracts valid JSON matching `ThreatRecord` schema, scoring CVSS severity between 0.0–10.0 and generating an executable bash patch script.
* **Acceptance Scenarios:**
  1. **Given** a raw exploit post for Nginx buffer overflow, **When** processed by the triage engine, **Then** it generates `severity: "CRITICAL"`, `cvss: 9.8`, `affected: ["nginx <= 1.24.0"]`, and `remediation: "sudo apt-get update && sudo apt-get install --only-upgrade nginx"`.

### User Story 3: Palantir SOC Mission Control Dashboard (Priority: P2 - Suit-Up Track)
As a CISO or Security Lead, I want a high-density, dark obsidian cyber defense dashboard featuring an interactive `@xyflow/react` Execution DAG, a 2D Threat Vector Matrix (Exploitability vs Impact), a 60 FPS streaming threat feed, and a 1-click Chaos Sabotage button to demonstrate resilience.

* **Independent Test:** Launch Next.js dashboard at 60 FPS. Verify SSE telemetry streaming, real-time node animations on the DAG flow, and interactive hover states on threat scatter plots.

---

## 3. Requirements

### Functional Requirements

* **FR-001 (Bright Data Scraper Studio Integration):** System MUST create and invoke scrapers via Bright Data `bdata` CLI (`bdata scraper create`, `bdata scraper run`) and REST endpoint (`POST /dca/trigger`).
* **FR-002 (Autonomous Sentinel Loop):** System MUST monitor data ingestion streams and automatically trigger `bdata scraper heal <id> "<issue>"` and `bdata scraper approve <id>` upon error detection.
* **FR-003 (Long-Tail Threat Feeds):** System MUST support long-tail threat presets:
  1. `Exploit-DB Zero-Days & PoCs`
  2. `PacketStorm Security Advisories`
  3. `GitHub Open-Source Supply Chain Alerts`
  4. `Ephemeral Pastebin & Breach Disclosures`
* **FR-004 (AI Threat Scorer):** System MUST extract structured `ThreatRecord` objects containing: CVE ID, Threat Actor, Severity (Low/Med/High/Critical), CVSS 4.0 Score, EPSS %, Affected Versions, and Bash Remediation Script.
* **FR-005 (Real-Time SSE Bus):** System MUST stream telemetry, heal events, and threat records over `GET /api/stream/telemetry` using Server-Sent Events.
* **FR-006 (Zero-Drop SQLite WAL):** System MUST persist all threats and heal event logs into a high-concurrency SQLite database using WAL mode.
* **FR-007 (Deterministic Offline Mock Mode):** System MUST support `MOCK_BRIGHTDATA=true` to execute 100% offline using pre-recorded security threat fixtures with zero external network dependencies.

### Key Data Entities

```typescript
export interface ThreatRecord {
  id: string;
  source: "ExploitDB" | "PacketStorm" | "GitHubAdvisory" | "Pastebin";
  target_url: string;
  cve_id?: string;
  title: string;
  threat_actor?: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  cvss_score: number;       // 0.0 - 10.0
  epss_percentile: number;  // 0 - 100%
  affected_packages: string[];
  exploit_poc_snippet: string;
  remediation_command: string;
  timestamp: string;
}

export interface HealEvent {
  collector_id: string;
  target_url: string;
  trigger_reason: string;
  status: "DETECTED" | "HEALING" | "APPROVED" | "RECOVERED";
  duration_ms: number;
  repaired_selectors: string[];
  timestamp: string;
}
```

---

## 4. Success Criteria & Judging Alignment

* **SC-001 (Web-Slinger Track - Bright Data Depth):** Complete programmatic utilization of Scraper Studio Collector IDs, Web Unlocker bypass, and the autonomous `bdata heal` loop.
* **SC-002 (Suit-Up Track - Best UI):** 60 FPS Palantir-style cyber defense dashboard using Google Stitch obsidian tokens, animated Execution DAG, and real-time threat matrix.
* **SC-003 (Spider-Sense Track - Clean Code):** Pydantic v2 + TypeScript type safety, 90%+ automated test coverage, and single-command launch (`docker compose up`).
* **SC-004 (Performance SLA):** Threat triage throughput $\ge 500$ threats/minute, sub-45s end-to-end self-healing cycle, and container memory footprint $< 512\text{ MB}$.
