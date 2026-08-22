# SENTINEL-CHAIN — Release Readiness Report (ox-alpha)

**Date:** 2026-08-22 · **Commit:** be9a7cf (+this) · **Next mission:** Cinematic Landing Page + Premium SaaS UI/UX

---

## CODEBASE STATUS
- Legacy purge complete: `.archive/` (AEGIS SaaS), dead integrations (`brightdata_client`, `web_unlocker_client`, `mock_fixtures`, broken `scraper_studio`), stale DBs removed from tracking.
- `pyproject.toml` renamed to sentinel-chain-backend; deps match actual imports (bs4 + requests added; onnxruntime/tree-sitter/scipy dropped).
- `.env.example` matches real config surface; mock-mode vars removed (no mock path exists on production).
- **Classification:** VERIFIED BY RUNTIME (tests/build/eval all green post-cleanup)

## PRODUCT STATUS
- Working pipeline: Target onboarding → inspection → schema synthesis → acquisition (CLI) → failure detect → evidence (Playwright) → AI/heuristic diagnosis → deterministic gate → heal → approve → re-run → verify.
- **GAP (documented, not built — per mission rules):** pivot's Correlation / ExposureRecord / Asset-context layers have ZERO code and ZERO docs mentions. Current product = Acquisition + Self-Healing only. Next mission owner must decide: build layer or re-scope claim.
- Multi-target support: REAL (Target model, per-target schemas, dynamic records).
- **Classification:** VERIFIED BY TEST (healing chain) · CORRELATION/EXPOSURE = NOT IMPLEMENTED

## BRIGHT DATA STATUS
- Production path wired to canonical `BrightDataCliRunner`: `asyncio.create_subprocess_exec` (shell=False), argv list, timeouts w/ kill, collector-id sanitization, `--` delimited repair prompt, JSON block extraction, status labels.
- Reviewer 2 confirmed: "genuinely wired, no simulated shortcut in run path."
- **Real cloud execution:** ADAPTER READY — NOT VERIFIED (needs live BRIGHT_DATA_API_KEY).
- **Classification:** VERIFIED BY CODE + TEST (local) · CLOUD = SIMULATION ONLY until live run

## AI STATUS
- Config-driven model (`GEMINI_MODEL`, default gemini-3.7-flash) read at runtime by `GeminiAIDiagnoser`; REST inference via generativelanguage.googleapis.com; heuristic fallback labeled (`source_type=HEURISTIC_FALLBACK`, `model_used=deterministic-rule-engine`).
- **Fixed:** confidence-inflation bug removed — gate now sees true scores (this initially dropped benchmark honesty to 83.8% before selector fixes restored 100%).
- **Remaining risk (Reviewer 3, P2):** DOM/AOM content interpolated into prompts without fencing — malicious page could attempt instruction injection. Mitigation available (delimit + sanitize); deferred as gate still validates output deterministically.
- **Classification:** VERIFIED BY CODE · FALLBACK VERIFIED BY TEST (0/10 live calls in truth audit)

## SECURITY STATUS
| Control | Status |
|---|---|
| SSRF validator (schemes, private/reserved IP incl. metadata 169.254.x) | PRESENT — enforcement at every entry point needs regression pass |
| Repair prompt shell injection | BLOCKED (metachars, flags, commands + NEW control-char/NUL rule) — 20/20 adversarial |
| CLI argument injection | MITIGATED (argv exec + `--` delimiter + id sanitization) |
| CORS | FIXED — localhost dev origins only |
| Auth | **NONE** — all mutating endpoints open; LOCAL DEMO ONLY, do not deploy |
| Selector verification | BS4 select + token fallback (Reviewer 4: fallback weak, P3) |
| DNS-rebinding/TOCTOU | NOT ADDRESSED (P3) |
- No "100% secure" claim made. Tested controls listed above; rest = remaining risk.
- **Classification:** VERIFIED BY TEST (injection suite) · AUTH ABSENCE = KNOWN LIMITATION

## TEST STATUS
- Backend pytest: **18/18 PASS** (0.66s)
- Golden eval (honest gates): **100/100** — Happy 40/40, Edge 40/40, Adversarial 20/20 → PASS
- Live truth audit: golden path 10/10 recovery, simulation-labeled, latency math consistent (Δ0.00ms)
- Frontend: `next build` CLEAN (fixed missing `src/lib/utils.ts`)
- **Classification:** VERIFIED BY TEST + RUNTIME

## REAL CLOUD STATUS
NOT VERIFIED. All metrics above are simulation-mode. One command away once API key provided:
run any target through `/api/scrapers/run` with live `BRIGHT_DATA_API_KEY`.

## KNOWN LIMITATIONS (judge-facing honesty list)
1. Zero authentication — local demo tool only.
2. In-memory job queue — state lost on restart; cross-loop wait can mislabel jobs (Reviewer 1).
3. Correlation/Exposure layers from pivot thesis: not implemented.
4. Cloud Bright Data path unverified against live collector.
5. Collector ID `c_sentinel_cve_threats` duplicated in ~7 code sites; `DEFAULT_COLLECTOR_ID` config unused (Reviewer 0) — consistency debt, not a bug.
6. DOM content unfenced in AI prompts (P2, mitigated downstream by deterministic gate).
7. Discovery catalog `"status":"ACCESSIBLE"` asserted without live check.

## REMAINING BLOCKERS FOR NEXT MISSION
None blocking UI work. Recommended pre-demo order:
1. Live-cloud verification run (needs API key)
2. Prompt-fencing patch (small)
3. Decide correlation/exposure scope BEFORE frontend claims anything about it

## CLAIM CLASSIFICATION SUMMARY
| Claim | Class |
|---|---|
| Self-healing loop works end-to-end (local sim) | VERIFIED BY RUNTIME |
| Injection defense 20/20 | VERIFIED BY TEST |
| Canonical CLI runner on prod path | VERIFIED BY CODE |
| Model config env-driven | VERIFIED BY CODE |
| Frontend builds | VERIFIED BY RUNTIME |
| Real cloud healing | SIMULATION ONLY / NOT VERIFIED |
| Correlation & Exposure engine | NOT IMPLEMENTED |
