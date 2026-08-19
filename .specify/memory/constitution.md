# 🛡️ SENTINEL-CHAIN Constitution
**Project Codename:** `SENTINEL-CHAIN` (Cybersecurity & Supply Chain Threat Hunter)  
**Hackathon Target:** *"Into the Scrape-Verse"* (WeMakeDevs × Bright Data, Aug 17–23, 2026)  
**Target Tracks:** 🥇 Grand Prize ($5,000 NVIDIA DGX Spark) · 🎨 Best UI (Apple iPad) · 💻 Clean Code (Keychron)  

---

## Core Principles

### I. Spec-Driven Architecture & Contract-First
Every feature, data pipeline, and AI analyzer must be anchored by an explicit specification and schema before implementation. No "vibe coding." All inputs and outputs must adhere to strict Pydantic v2 schemas and TypeScript contracts.

### II. Native Bright Data Scraper Studio Interoperability
Bright Data Scraper Studio and the `bdata` CLI form the non-negotiable core acquisition engine. Every scraper is identified by a `c_*` Collector ID. Scrapers target long-tail, anti-bot-protected cybersecurity feeds (Exploit-DB, PacketStorm, GitHub Security Advisories, Ephemeral Pastebins) where Bright Data's Web Unlocker and Scraping Browser provide essential anti-fingerprinting and Turnstile bypass.

### III. Zero-Human Autonomous Self-Healing Sentinel Loop
Bright Data provides the manual CLI command `bdata scraper heal`. SENTINEL-CHAIN provides the **Autonomous Sentinel Loop**: 
- Continuously monitors data stream integrity.
- Automatically catches schema breakages or empty extraction frames.
- Invokes `bdata scraper heal <collector_id> "<what broke>"` programmatically.
- Validates the proposed repair and auto-approves via `bdata scraper approve <collector_id>`.
- Resumes data collection with zero human intervention and logs healing events to the live telemetry stream.

### IV. Actionable Cyber Threat Intelligence (Zero Noise)
Raw scraped text is never dumped as-is. The AI Intelligence Layer must:
1. Extract CVE identifiers, 0-day exploit code, affected software/package versions, and threat actor indicators.
2. Predict CVSS 4.0 / EPSS exploitability scores ($0.0 - 10.0$).
3. Match against protected company infrastructure stacks.
4. Synthesize an executable 1-click **Automated Remediation Playbook** (Bash/Terraform patch command).

### V. Palantir SOC High-Density Aesthetics (Zero Generic AI Slop)
The UI must deliver a high-density, tier-1 Cyber War Room aesthetic:
- Matte Obsidian void backgrounds (`#07090E`), hairline borders (`rgba(255,255,255,0.08)`), and pulsing neon crimson/amber alerts.
- Interactive `@xyflow/react` Execution DAG with dynamic animated particle edges.
- 2D Threat Matrix (Exploitability vs Business Impact).
- 60 FPS TanStack Virtual streaming feed.

### VI. Deterministic Offline Testability & Mock Fixtures
The complete pipeline must be 100% testable and runnable offline with `MOCK_BRIGHTDATA=true`. Pre-recorded JSON and HTML fixtures of real Exploit-DB pages, GitHub PoCs, and CVE advisories allow judges to run the entire system offline in one command with zero setup or API rate limits.

---

## Technical Constraints & Safety Rules

1. **Safety Rule:** `INVALID EXTRACTION > EMPTY EXTRACTION` (Returning null is safer than returning false threat intelligence).
2. **Public Data Compliance:** Scrape only publicly available security advisories, vulnerability disclosures, and public repositories. No credential-stuffing, paywalled, or login-walled scraping.
3. **Memory Footprint:** Full Docker Compose stack must run under `< 512 MB RAM`.

---

## Governance

This Constitution supersedes all ad-hoc instructions. Any architectural amendment requires documentation in the spec repository.

**Version:** 1.0.0 | **Ratified:** August 18, 2026 | **Author:** Priyanshu (Cybersecurity & Full-Stack Lead)
