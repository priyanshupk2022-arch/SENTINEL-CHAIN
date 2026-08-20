# SENTINEL-CHAIN: Autonomous Target Monitoring & Failure Recovery

## 1. Scheduling Modes
- `MANUAL`: On-demand execution triggered via API or UI button.
- `INTERVAL_5M`: High-frequency polling (5-minute intervals).
- `INTERVAL_15M`: Standard production monitoring (15-minute intervals).
- `HOURLY`: Hourly aggregation cycle.
- `DAILY`: Daily summary harvesting.

## 2. Autonomous Self-Healing Pipeline
When an automated scrape returns empty or invalid records:
1. **Detection**: `FailureDetector` raises `BROKEN` state.
2. **Evidence**: `EvidenceCollector` harvests current DOM, AOM tree, and screenshot.
3. **Diagnosis**: `GeminiAIDiagnoser` synthesizes root cause & proposed selector.
4. **Validation**: `RepairValidator` enforces air-gapped shell injection and DOM element verification.
5. **Execution**: Bright Data CLI executes `bdata scraper heal` with the generated prompt.
6. **Approval & Re-run**: Fix is approved and re-run to verify 100% extraction before marking `HEALTHY`.
