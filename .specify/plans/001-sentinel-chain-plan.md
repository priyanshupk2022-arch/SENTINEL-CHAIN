# Implementation Plan: SENTINEL-CHAIN (100X EDITION)
**Feature:** Autonomous Cybersecurity & Supply Chain Threat Hunter  
**Spec Link:** [.specify/specs/001-sentinel-chain-spec.md](file:///c:/Users/priya/Documents/antigravity/modest-planck/.specify/specs/001-sentinel-chain-spec.md)  
**Date:** August 18, 2026  
**Status:** Approved Technical Plan (100X Elevated)  

---

## 1. The 100X Technical Architecture (Agentic Triage & Auto-Diagnoser)

```
[Target Sources: Exploit-DB, PacketStorm, GitHub PoC Advisories, Pastebin]
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. BRIGHT DATA DATA ACQUISITION (`bdata_client.py`)                         │
│ • bdata scraper run <c_*> <URL> --output json                               │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. 100X UPGRADE: DOM-DIFFING AUTO-DIAGNOSER (`diagnoser_agent.py`)          │
│ • PROBLEM: `bdata heal` needs a human to tell it *what* broke.              │
│ • SOLUTION: If payload is empty, our Gemini Diagnoser fetches the raw HTML, │
│   compares it against the expected schema, and autonomously generates the   │
│   EXACT repair prompt (e.g., "Table class changed from .cve to #vuln-box"). │
│ • It then feeds this perfect prompt into `bdata scraper heal`!              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. 100X UPGRADE: BLAST RADIUS & SUPPLY CHAIN GRAPH (`blast_radius.py`)      │
│ • Takes scraped CVE/0-day data and cross-references it against a defined    │
│   Infrastructure Graph (e.g., matching vulnerable NPM/PyPI packages).       │
│ • Calculates "Blast Radius" — exactly which microservices are compromised.  │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. 100X UPGRADE: AGENTIC PATCH VERIFICATION (`sandbox_runner.py`)           │
│ • Synthesizes the remediation script (Bash/Terraform).                      │
│ • Runs the script against a simulated ephemeral container to VERIFY the     │
│   patch actually works before deploying it to the UI.                       │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 5. PALANTIR SOC CYBER WAR ROOM (Dashboard)                                  │
│ • Visualizes the Blast Radius Infection Graph in real-time.                 │
│ • Shows the Auto-Diagnoser's exact thought process during a heal event.     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Layout (100X Additions)

```text
c:\Users\priya\Documents\antigravity\modest-planck\
├── backend/
│   ├── app/
│   │   ├── sentinel/
│   │   │   ├── heal_loop.py          
│   │   │   └── diagnoser_agent.py    # NEW: Gemini DOM-Diffing AI to write heal prompts
│   │   ├── triage/
│   │   │   ├── threat_scorer.py      
│   │   │   ├── blast_radius.py       # NEW: Maps CVEs to infrastructure dependency graph
│   │   │   └── sandbox_runner.py     # NEW: Verifies remediation scripts safely
│   ├── tests/
│   │   ├── test_diagnoser.py
│   │   └── test_blast_radius.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── BlastRadiusGraph.tsx  # NEW: 3D/Interactive node graph showing infection spread
│   │   │   ├── DiagnoserTerminal.tsx # NEW: Shows the AI thinking to heal the scraper
```
