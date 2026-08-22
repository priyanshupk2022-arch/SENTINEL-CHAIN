# SENTINEL-CHAIN — Codebase Audit (ox-alpha)

**Date:** 2026-08-22 · **Auditor:** ox-alpha (primary engineering agent)
**Repo:** C:/Users/priya/SENTINEL-CHAIN (github.com/priyanshupk2022-arch/SENTINEL-CHAIN @ c1a47fe)
**Mission scope:** Post-pivot audit → "Autonomous Cyber Intelligence Acquisition & Exposure Correlation Engine". No redesign, no new features.

---

## PHASE 0 — Capability Audit (actual environment)

| Capability | Status | Notes |
|---|---|---|
| terminal | ✅ | git-bash on Windows 11 |
| filesystem | ✅ | full access |
| git / gh CLI | ✅ | authed as priyanshupk2022-arch (scopes: repo, workflow, gist, read:org) |
| Python 3.11 + pytest | ✅ | venv at .venv |
| Node 22 + npm | ✅ | frontend deps installable |
| Docker | ❌ NOT available | docker-compose untested locally |
| subagents | ✅ | used 4 parallel auditors (transcripts in hermes cache) |
| browser/Playwright | ✅ (runtime dep of product) | chromium install required for evidence tests |

## PHASE 1 — Product Contract Summary

- Canonical pipeline: TARGET→COLLECTOR→RUN→FAILURE→EVIDENCE→DIAGNOSIS(→HEAL→APPROVE→RE-RUN→VERIFY.
- Docs: docs/01..23 complete; README still carries pre-pivot "Exploit-DB/CVE Harvester" framing (drift).
- main.py title/description already generalized ("Autonomous Web Intelligence & Self-Healing Platform") ✅

---

## FINDINGS LEDGER (FILE | ROLE | VERDICT | REASON | DEPS | RISK)

### P0 — Blockers
1. `frontend/src/lib/utils.ts` | shadcn cn() helper | **FIXED (added)** | Missing file broke entire Next build (`Module not found: '@/lib/utils'`, 7 imports). clsx+tailwind-merge already in package.json. | clsx, tailwind-merge | P0→resolved pending rebuild
2. `backend/pyproject.toml` | dependency manifest | **REFACTOR** | Name/version still `radar-x-backend` "Self-Healing Market Intelligence Engine" (pre-pivot). MISSING runtime deps: `beautifulsoup4`, `requests` (imported by validator/evidence_collector/target_inspector/diagnoser). Tests cannot even load conftest without them. Declared-but-unused: onnxruntime, tree-sitter(+html), scipy. | all backend | P0
3. `.env.example` | config template | **REFACTOR** | Documents RADAR-X-era vars (`BRIGHT_DATA_CUSTOMER_ID/PASSWORD/HOST`, `MOCK_BRIGHTDATA`, `DATABASE_URL ...radar_x.db`). Actual config.py uses: GEMINI_API_KEY, GEMINI_MODEL, BRIGHT_DATA_API_KEY, DATABASE_PATH(sentinel_chain.db), CLI_TIMEOUT_SECONDS, HEAL_TIMEOUT_SECONDS. `MOCK_BRIGHTDATA=true` default misleads about mock mode which does not exist on the production path. | — | P0 (docs/config drift)

### P1 — High
4. `backend/app/integrations/scraper_studio.py` | webhook receiver | **DELETE** | Imports `backend.app.scanner.wtp_scorer` — module/dir does not exist. Import would crash. Zero importers (verified by grep). Dead code. | none (dead) | P1
5. `backend/app/integrations/brightdata_client.py` | alt acquisition path (CDP/proxy via Playwright) | **DELETE** | Duplicate acquisition implementation; unused; mock defaults (`hl_mock`, `mock_pass`); contradicts canonical CLI contract. | playwright | P1
6. `backend/app/integrations/web_unlocker_client.py` | alt acquisition path (httpx) | **DELETE** | Duplicate; unused; mock defaults; contradicts canonical CLI contract. | httpx | P1
7. `backend/app/integrations/mock_fixtures.py` | fake HTML fixtures | **DELETE** | Unused fixture strings; risk of fixture-as-production if ever wired. | — | P1
8. `backend/app/engine/diagnoser.py:113-114` | AI response parsing | **REFACTOR** | Confidence inflation: if model returns confidence <0.8 it is forcibly raised to 0.85, defeating the deterministic gate's purpose (gate then always passes on AI path). Should clamp to reject, not inflate. Also logs hardcoded "Gemini 3.7 Flash" string while model is configurable. | — | P1 (safety-gate integrity)
9. `backend/app/main.py:44-50` | CORS | **REFACTOR** | `allow_origins=["*"]` with `allow_credentials=True` — invalid/insecure combo; browsers reject wildcard+credentials; any origin can call mutating endpoints. Restrict to localhost dev origins. | — | P1
10. Auth on ALL mutating endpoints (/api/chaos/mutate, /api/scrapers/* heal/approve, /api/targets/*) | API surface | **REFACTOR/ACCEPT** | Zero authentication anywhere. Acceptable for local demo-only tool; must be documented as known limitation before any deployment. | — | P1 (deployment blocker only)

### P2 — Medium
11. `.archive/` (~120 files: legacy AEGIS SaaS app, billing/auth/rbac/forensics + old tests + stale DBs) | dead legacy code | **DELETE** | Pre-pivot product entirely; unreferenced by active code. Bloats repo & confuses audits. | — | P2
12. `scratch/check_stream_details.py, check_video.py, get_chat.py` | scratch scripts | **DELETE** | Unrelated one-off scripts (video/chat probing). | — | P2
13. `data/*.db` committed binaries (aegis_audit.db, aegis_saas.db, token_revocation.db, data/test/) | stale artifacts | **DELETE + gitignore** | Legacy AEGIS DBs; runtime DB should be sentinel_chain.db (gitignored). | — | P2
14. `README.md` | product framing | **REFACTOR** | Still says "Exploit-DB/CVE harvester"; benchmark table labels simulation honestly (good); Quickstart references backend/requirements.txt which does not exist (pyproject instead); badge claims need re-verification after fixes. | — | P2
15. `routes_discovery.py PUBLIC_TARGET_CATALOG` | curated suggestions | **KEEP (annotate)** | Hardcoded catalog is legitimate UX (5 targets incl. Exploit-DB, NVD, books, quotes, HN). But `"status": "ACCESSIBLE"` is asserted without checking — relabel as "catalog_status" or verify lazily. | — | P2
16. `chaos_proxy.py SAMPLE_VULNERABILITIES` | chaos demo target | **KEEP** | Intentional transparent chaos-demo target (documented in README §2). Clearly a controlled fixture serving /api/proxy/target — acceptable as long as labeled demo. | — | P2 (accepted-by-design)
17. `diagnoser.py` uses `requests` (sync) inside `asyncio.to_thread` with 3.5s timeout | AI client | **REFACTOR (optional)** | Works, but httpx.AsyncClient is already a dep and cleaner. Low priority. | requests | P3
18. `validator.py DANGEROUS_SHELL_PATTERNS` includes `--[a-zA-Z0-9_-]+` flag ban + shell metachars | repair gate | **KEEP** | Combined with argv exec (shell=False) and `--` delimiter in build_heal_command, injection surface is well covered. Note: patterns also block legit English words like "bash"/"exec" in prompts — conservative is fine. | — | OK
19. `eval/live_truth_audit.py SimulatedLocalCliRunner` | offline harness | **KEEP** | Explicitly named simulated subclass; benchmark honesty preserved. Ensure final reports keep SIMULATED label (they do per README table). | — | OK
20. `frontend/src/components/*` (26 components incl. screens) | UI layer | **KEEP (frozen)** | Mission forbids frontend redesign; only build fix applied (utils.ts). | — | —

### Verified-correct core (no action)
- `engine/cli_runner.py` BrightDataCliRunner: `asyncio.create_subprocess_exec` (shell=False ✅), argv list ✅, timeouts + kill on TimeoutError ✅, collector-id sanitization `[a-zA-Z0-9_-]` ✅, `--` delimiter before repair prompt ✅, JSON extraction robust ✅, status_label from payload ✅. Canonical runner confirmed used by orchestrator & routes_scrapers (grep-verified; duplicate runners are dead files).
- `engine/recovery_orchestrator.py`: full RUN→…→VERIFY loop implemented against canonical services; persists DynamicRecord (is_simulated=False only for real runs) + legacy ThreatRecord when CVE-like key present; emits SSE telemetry.
- `engine/validator.py`: confidence gate ≥0.8 (see finding #8), selector must resolve in DOM via BeautifulSoup.select with raw-token fallback.
- `config.py`: GEMINI_MODEL env-driven default gemini-3.7-flash; diagnoser reads settings.GEMINI_MODEL (no hardcoded model in request URL) ✅; fallback = deterministic heuristic with source_type=HEURISTIC_FALLBACK, model_used=deterministic-rule-engine ✅.
- `security/url_validator.py`: scheme allowlist (http/https), private/reserved IP ranges blocked incl. link-local metadata range (169.254.x present in PRIVATE_IP_NETWORKS).
- `evidence_collector.py`: Playwright headless, 15s nav timeout, DOM pruning (scripts/styles stripped), AOM snapshot w/ BS4 fallback, optional screenshot.

### Data-truth map (dashboard sources)
| Source | Classification |
|---|---|
| GET /api/threats | REAL (reads threat_records written only by real orchestrator runs) |
| GET /api/targets/*/records (dynamic_records) | REAL (written post-run/re-run) |
| SSE /api/telemetry/events | REAL (orchestrator-emitted events) |
| GET /api/proxy/target (ChaosProxy HTML) | FIXTURE-BY-DESIGN (transparent chaos target, labeled in README/UI) |
| routes_discovery catalog | HARDCODED (curated suggestions; ACCESSIBLE label overstated) |
| brightdata_client / web_unlocker / mock_fixtures | DEAD (never imported by active path) |

### Remaining risks (not fixed by design/scope)
- No auth (P1, documented limitation)
- SSRF validation exists for inspector paths; evidence_collector navigates URLs directly — confirm url_validator is enforced at every entry point during Phase 12 regression
- CORS wildcard (fix planned)
- Real cloud Bright Data path UNTESTED (needs live API key) — classified SIMULATION-READY / CLOUD-PENDING until golden path proves otherwise

---
*Test/build results appended in Phase 8 section of release-readiness doc.*
