# Tasks: SENTINEL-CHAIN Implementation (100X EDITION)
**Feature:** Autonomous Cybersecurity & Supply Chain Threat Hunter  
**Spec Link:** [.specify/specs/001-sentinel-chain-spec.md](file:///c:/Users/priya/Documents/antigravity/modest-planck/.specify/specs/001-sentinel-chain-spec.md)  
**Plan Link:** [.specify/plans/001-sentinel-chain-plan.md](file:///c:/Users/priya/Documents/antigravity/modest-planck/.specify/plans/001-sentinel-chain-plan.md)  

---

## Phase 1: Setup & Shared Infrastructure

- [ ] **T001**: Clean and align backend folder layout.
- [ ] **T002**: Align `backend/pyproject.toml` with strict dependencies (`fastapi`, `uvicorn`, `httpx`, `pydantic>=2.6`, `aiosqlite`, `google-generativeai`, `beautifulsoup4`).
- [ ] **T003**: Populate `backend/data/fixtures/` with pre-recorded offline fixtures (including raw HTML for the diagnoser).

---

## Phase 2: Foundational Layer (Data Models & Storage)

- [ ] **T004**: Implement `backend/app/storage/models.py` with Pydantic v2 schemas (`ThreatRecord`, `HealEvent`, `BlastNode`).
- [ ] **T005**: Implement `backend/app/storage/db.py` SQLite WAL mode manager.
- [ ] **T006**: Implement `backend/app/integrations/mock_fixtures.py`.

---

## Phase 3: User Story 1 (P1) - 100X Autonomous Sentinel Heal Loop

- [ ] **T007**: Implement `backend/app/integrations/bdata_client.py`.
- [ ] **T008**: Implement `backend/app/sentinel/diagnoser_agent.py` (100X UPGRADE).
  - Uses Gemini to diff broken HTML vs working schema to generate the exact repair string required by `bdata scraper heal`.
- [ ] **T009**: Implement `backend/app/sentinel/heal_loop.py` state machine:
  - Empty Payload -> Trigger Diagnoser -> Pass prompt to `bdata heal` -> `approve` -> Resume.
- [ ] **T010**: Implement `backend/app/chaos/chaos_engine.py` (DOM mutation injection).

---

## Phase 4: User Story 2 (P1) - 100X AI Threat Triage & Blast Radius

- [ ] **T011**: Implement `backend/app/triage/threat_scorer.py` (CVSS/EPSS scoring).
- [ ] **T012**: Implement `backend/app/triage/blast_radius.py` (100X UPGRADE).
  - Maps incoming CVEs against a mocked dependency graph to determine which microservices are compromised.
- [ ] **T013**: Implement `backend/app/triage/playbook_generator.py` (Remediation synthesis).

---

## Phase 5: User Story 3 (P2) - Palantir SOC Cyber War Room Dashboard

- [ ] **T014**: Implement `frontend/src/hooks/useThreatTelemetry.ts` SSE hook.
- [ ] **T015**: Implement `frontend/src/components/TopSOCBar.tsx`.
- [ ] **T016**: Implement `frontend/src/components/BlastRadiusGraph.tsx` (100X UPGRADE).
  - Uses `@xyflow/react` to show infection spreading across infrastructure nodes in real-time.
- [ ] **T017**: Implement `frontend/src/components/DiagnoserTerminal.tsx` (100X UPGRADE).
  - Terminal-style readout showing the AI auto-diagnoser identifying the broken DOM element.
- [ ] **T018**: Implement `frontend/src/components/LiveThreatStream.tsx` & `TargetFeedPanel.tsx`.
- [ ] **T019**: Wire all components into `frontend/src/app/page.tsx`.

---

## Phase 6: System Verification & Hackathon Packaging

- [ ] **T020**: Implement `backend/app/main.py`.
- [ ] **T021**: Test full stack launch via `docker compose up`.
- [ ] **T022**: Finalize Demo Video Script showing the 100X features.
