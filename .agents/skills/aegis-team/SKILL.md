---
name: aegis-team
description: Master Multi-Agent Team Orchestration Skill for Aegis (AI Security Guardrail Proxy). Coordinates the 17-agent engineering collective, enforces DAG execution pipelines, and mediates the Debate Protocol.
---

# 🛡️ Aegis 17-Agent Engineering Collective & Orchestration System

Welcome to the **Aegis Engineering Collective**. This skill provides the complete orchestration engine, agent directory, and protocol dynamics required to build, test, audit, and deploy **Aegis** (Self-Hosted AI Security Guardrail Proxy).

---

## 🗺️ Multi-Agent Architecture & Dependency Graph

```mermaid
graph TB
    subgraph "🧠 Command & Orchestration"
        ARCH["🏗️ Chief Architect<br/>(Adjudicator)"]
    end

    subgraph "🔬 Intelligence & Threat Modeling"
        RESEARCHER["🔍 Deep Researcher"]
        THREAT["☠️ Threat Intel Analyst"]
    end

    subgraph "⚙️ Core Systems Engineering"
        BACKEND["⚡ Backend Engineer<br/>(FastAPI / Proxy)"]
        FORENSIC["🔬 Forensic Engine<br/>Engineer"]
        CRYPTO["🔐 Cryptography &<br/>Security Engineer"]
        INFRA["🐳 DevOps & Infra<br/>Engineer"]
    end

    subgraph "🎨 Experience & Integrations"
        UIDESIGNER["🎨 UI/UX Designer<br/>(Stitch Expert)"]
        FRONTEND["💻 Frontend Engineer<br/>(Dashboard / SSE)"]
        DXENG["📦 DX & Integrations<br/>Engineer"]
    end

    subgraph "🛡️ Quality, Security & Compliance"
        REDTEAM["🔴 Red Team<br/>Operator"]
        QA["🧪 QA & Test<br/>Engineer"]
        PERF["⚡ Performance &<br/>Chaos Engineer"]
        SECAUDIT["🛡️ Security<br/>Auditor"]
        COMPLIANCE["⚖️ Compliance &<br/>Privacy Officer"]
    end

    subgraph "📝 Documentation & Growth"
        DOCWRITER["📝 Tech Writer &<br/>Docs Engineer"]
        GTM["🚀 GTM & Growth<br/>Strategist"]
    end

    ARCH --> RESEARCHER
    ARCH --> THREAT
    ARCH --> BACKEND
    ARCH --> FORENSIC
    ARCH --> CRYPTO
    ARCH --> INFRA
    ARCH --> UIDESIGNER
    ARCH --> FRONTEND
    ARCH --> DXENG
    ARCH --> REDTEAM
    ARCH --> QA
    ARCH --> PERF
    ARCH --> SECAUDIT
    ARCH --> COMPLIANCE
    ARCH --> DOCWRITER
    ARCH --> GTM

    RESEARCHER -.-> BACKEND
    RESEARCHER -.-> FORENSIC
    THREAT -.-> REDTEAM
    THREAT -.-> FORENSIC
    UIDESIGNER -.-> FRONTEND
    BACKEND -.-> QA
    FORENSIC -.-> QA
    REDTEAM -.-> SECAUDIT
    PERF -.-> INFRA
    DXENG -.-> DOCWRITER
    COMPLIANCE -.-> FORENSIC
```

---

## 🗣️ The Debate Protocol (Consensus Mechanism)

When a security conflict emerges between safety and usability:
1. **Challenge Phase**: `aegis-red-team` creates an adversarial exploit payload that bypasses current detection.
2. **Defense Phase**: `aegis-forensic-eng` evaluates false positive risks across 1,000+ benchmark benign documents.
3. **Adjudication Phase**: `aegis-chief-architect` analyzes AST and token distribution, ruling on whether to refine detection rules or adjust policy thresholds.
4. **Validation Phase**: `aegis-qa-eng` and `aegis-sec-auditor` run the updated 4-tier test harness to verify zero regressions.

```mermaid
sequenceDiagram
    participant Architect as 🏗️ Chief Architect
    participant Forensic as 🔬 Forensic Eng
    participant RedTeam as 🔴 Red Team
    participant QA as 🧪 QA Engineer
    
    Architect->>Forensic: Implement Detection Rule
    Architect->>RedTeam: Attack New Detection Rule
    RedTeam-->>Architect: OBJECTION! Found bypass (Payload X)
    
    rect rgb(230, 240, 255)
        Note over Architect,RedTeam: 🗣️ DEBATE PROTOCOL ACTIVATED
        Forensic->>Architect: Risk Assessment: Blocking X broadly increases False Positives by 2.1%.
        RedTeam->>Architect: Exploit Severity: Critical (CVSS 9.1). Allows direct prompt injection.
        Architect->>Forensic: Ruling: Apply targeted Unicode AST normalizer prior to regex evaluation.
    end
    
    Forensic->>QA: Push refined engine code
    RedTeam->>QA: Push adversarial test suite
    QA-->>Architect: All 4 test tiers pass with Exit Code 0.
```

---

## 📂 Sub-Agent Directory & Skill Index

Every agent is defined as an individual persistent skill accessible in `.agents/skills/`:

| Skill Name | Role | Focus Area |
|------------|------|------------|
| `aegis-chief-architect` | Chief Architect & Adjudicator | Orchestration, Architecture, Debate Rulings |
| `aegis-deep-researcher` | Research & Intelligence Analyst | Threat research, Python library benchmarks |
| `aegis-threat-intel` | Threat Intelligence Analyst | STRIDE threat models, Unicode steganography taxonomy |
| `aegis-backend-eng` | Senior Backend Engineer | FastAPI async proxy, SQLite WAL, <20ms latency SLA |
| `aegis-forensic-eng` | Document Forensics Specialist | Multi-layer PDF/DOCX parsing, font/color contrast |
| `aegis-crypto-eng` | Cryptography & Security Engineer | Offline Ed25519 license verification, zero-trust |
| `aegis-devops` | Infrastructure & DevOps Specialist | Docker multi-arch, Compose, K8s manifests |
| `aegis-ui-designer` | Senior Product Designer | Stitch MCP, dark-mode design system, Diff Inspector |
| `aegis-frontend-eng` | Frontend Dashboard Engineer | Jinja2 + Tailwind + Alpine.js / Vite SPA, SSE streams |
| `aegis-dx-eng` | DX & Integration Engineer | LiteLLM/LangChain SDKs, ATS webhooks (Greenhouse) |
| `aegis-red-team` | Adversarial Red Team Operator | Evasion payloads, jailbreak test batteries |
| `aegis-qa-eng` | Quality Assurance & Test Engineer | 4-tier test architecture, pytest automation |
| `aegis-perf-eng` | Performance & Chaos Engineer | Locust load tests, latency profiling, chaos injection |
| `aegis-sec-auditor` | Application Security Auditor | Static analysis (Bandit/Semgrep), zero-telemetry audit |
| `aegis-compliance` | Data Privacy & Compliance Officer | PII masking (Presidio), GDPR/HIPAA/SOC2 mapping |
| `aegis-tech-writer` | Technical Writer & Docs Engineer | README, Quickstart, Architecture & API references |
| `aegis-gtm` | Technical GTM Lead | Exploit teardowns, CTO positioning, ROI models |
