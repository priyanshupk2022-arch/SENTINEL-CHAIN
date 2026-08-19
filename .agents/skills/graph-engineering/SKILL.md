---
name: graph-engineering
description: 10/10 Institutional Graph Engineering Runtime for Antigravity 2.0. Integrates Dynamic Complexity Triage (Fast-Path vs Graph-Path), 3-Harness Isolation (Context, Capability, Agent), TDD Actor-Critic Anti-Cheat separation, 4-Tier Test Gates (Unit, E2E, Red-Team, Stress), Mechanical Exit-0 Verification, and Bounded Adaptive Recovery Loops.
---

# SKILL: 10/10 GRAPH ENGINEERING RUNTIME (ANTIGRAVITY 2.0)

Whenever the user requests to build, refactor, or test any feature, service, or architecture, strictly execute using this 10/10 Protocol:

---

## 🚦 PHASE 0: COMPLEXITY TRIAGE (ZERO LATENCY OVERHEAD)
Before generating any graph, evaluate task complexity:
- **FAST-PATH (Single-file change, cosmetic UI, config update):**
  - Execute direct edit ➔ Run workspace linter/typecheck ➔ Exit in < 3s.
  - Bypass graph compiler and heavy testing gates.
- **GRAPH-PATH (Multi-file feature, backend logic, APIs, security, pipelines):**
  - Escalate to Phase 1.

---

## 🗺️ PHASE 1: DYNAMIC GRAPH COMPILATION & THE 3 HARNESSES
1. **Dynamic DAG Decomposition:** Deconstruct the requirement into discrete, bounded nodes ($N_1, N_2, \dots, N_k$) with strict typed input/output contracts.
2. **Context Harness:** Isolate context per worker. Extract ONLY relevant schemas, models, and target files. Strictly forbid dumping whole-workspace context.
3. **Capability Harness:** Inject exact official library definitions, AST schemas, and docs directly into worker context (Zero fuzzy/hallucinated web prompts).
4. **Agent Harness:** Execute sub-agents in sandboxed environments with bounded tool permissions and execution timeouts.
5. **Plumbing via Code ($0 Tokens):** Deduplication, sorting, filtering, and joins MUST execute in zero-token deterministic code. Reserve LLM calls strictly for probabilistic synthesis.

---

## 🧪 PHASE 2: TDD ACTOR-CRITIC ISOLATION (ANTI-CHEAT GATE)
For every feature node, strictly separate the Critic and Actor roles:
1. **Tester Role (Critic):**
   - Reads requirements and authors the test suites **BEFORE** implementation code is written.
   - Verifies that tests initially FAIL (`exit_code != 0`) on the unimplemented baseline.
2. **4-Tier Test Taxonomy:**
   - **Unit Suite (`tests/unit/`):** Pure functions, algorithms, AST parsers, schema validations.
   - **E2E Integration Suite (`tests/e2e/`):** Complete user journeys (API ➔ Middleware ➔ DB/Service ➔ UI State/Response).
   - **Adversarial Red-Team Suite (`tests/redteam/`):** (Security/Gateway/Parser tasks) Malformed payloads, injection vectors, boundary violations, evasion techniques.
   - **Stress & Concurrency Suite (`tests/stress/`):** (Async/Pipeline tasks) 50+ concurrent requests, race conditions, memory leak checks, latency SLAs.
3. **Coder Role (Actor):**
   - Authors feature code.
   - **STRICT INVARIANT:** Coder has READ-ONLY access to test files. It is strictly forbidden from modifying test assertions to force a pass.

---

## ⚙️ PHASE 3: MULTI-GATE MECHANICAL VERIFICATION
Execute terminal verification commands sequentially:
1. `pytest tests/unit -v` (Exit 0 required)
2. `pytest tests/e2e -v` (Exit 0 required)
3. `pytest tests/redteam -v` (If applicable: 0 evasions, 0 false positives)
4. `pytest tests/stress -v` (If applicable: P95 latency within SLA, memory under ceiling)

---

## 🔁 PHASE 4: ADAPTIVE RECOVERY & HARD LOOP-BREAKER
If any mechanical test gate fails (`exit_code != 0`):
1. **Dynamic Expansion:** Insert recovery sub-nodes (`[Diagnose]` ➔ `[Scoped Fix]` ➔ `[Retest]`).
2. **Hash Failure Signature:** Compute `hash(error_trace + failed_assertion)`. If signature exists in `seen_failures`, abort immediately to safe fallback.
3. **Quoted Error Brief:** Feed exact terminal error output and failed assertion line back to Coder role.
4. **Progress Delta:** Failing test count must strictly decrease ($F_{n+1} < F_n$).
5. **Hard Budget:** Strictly maximum **2 repair iterations** per node.

---

## 📦 PHASE 5: ARTIFACT PERSISTENCE & REPORT
Emit an execution ledger containing:
- Executed DAG nodes and latency telemetry.
- Multi-tier test results (Unit, E2E, Red-Team, Stress pass counts).
- Final Exit-0 mechanical verification proof.
