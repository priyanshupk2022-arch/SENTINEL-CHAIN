import time
import logging
import uuid
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime
from backend.app.config import get_settings
from backend.app.storage.db import DatabaseManager
from backend.app.models.domain import (
    ScraperJobState, ThreatRecord, EvidenceBundle, TelemetryEvent,
    Target, TargetStatus, DynamicRecord, ExtractionSchema, ScraperRun
)
from backend.app.models.repair_proposal import RepairProposal
from backend.app.engine.cli_runner import BrightDataCliRunner, CliExecutionResult
from backend.app.engine.evidence_collector import EvidenceCollector
from backend.app.engine.diagnoser import GeminiAIDiagnoser
from backend.app.engine.validator import RepairValidator

logger = logging.getLogger("sentinel.recovery_orchestrator")

class RecoveryOrchestrator:
    def __init__(
        self,
        db: Optional[DatabaseManager] = None,
        cli_runner: Optional[BrightDataCliRunner] = None,
        evidence_collector: Optional[EvidenceCollector] = None,
        diagnoser: Optional[GeminiAIDiagnoser] = None,
        validator: Optional[RepairValidator] = None
    ):
        settings = get_settings()
        self.db = db or DatabaseManager(settings.DATABASE_PATH)
        self.cli_runner = cli_runner or BrightDataCliRunner()
        self.evidence_collector = evidence_collector or EvidenceCollector()
        self.diagnoser = diagnoser or GeminiAIDiagnoser()
        self.validator = validator or RepairValidator()
        self._telemetry_listeners: List[Callable[[TelemetryEvent], Awaitable[None]]] = []

    def subscribe_telemetry(self, listener: Callable[[TelemetryEvent], Awaitable[None]]) -> None:
        self._telemetry_listeners.append(listener)

    async def _emit_event(
        self,
        node_id: str,
        status: str,
        message: str,
        payload: Optional[Dict[str, Any]] = None,
        target_id: Optional[str] = None
    ) -> None:
        event = TelemetryEvent(
            target_id=target_id,
            node_id=node_id,
            status=status,
            message=message,
            payload=payload or {}
        )
        try:
            if self.db:
                await self.db.save_telemetry_event(event)
        except Exception as e:
            logger.warning(f"Failed to persist telemetry event: {e}")

        # Dispatch to live SSE subscribers
        for listener in self._telemetry_listeners:
            try:
                await listener(event)
            except Exception as e:
                logger.warning(f"Error dispatching telemetry event: {e}")

    async def execute_scraper_cycle(
        self,
        collector_id: str,
        target_url: str,
        target_id: Optional[str] = None,
        scraper_id: Optional[str] = None,
        auto_heal: bool = True
    ) -> Dict[str, Any]:
        """
        Orchestrates the complete target-agnostic autonomous scraping & self-healing lifecycle:
        RUN -> INSPECT -> [FAILURE] -> EVIDENCE -> DIAGNOSIS -> VALIDATION -> HEAL -> APPROVE -> RE-RUN -> HEALTHY
        """
        start_time = time.time()
        run_id = str(uuid.uuid4())
        logger.info(f"Starting scraper cycle for target {target_id or 'default'} (collector: {collector_id}) on {target_url}")

        # Update target state to RUNNING if target exists
        if target_id and self.db:
            target = await self.db.get_target(target_id)
            if target:
                target.status = TargetStatus.RUNNING
                target.last_run = datetime.utcnow()
                await self.db.save_target(target)

        # Step 1: RUN SCRAPER
        await self._emit_event("runner", "RUNNING", f"Executing Bright Data collector {collector_id}", target_id=target_id)
        run_res: CliExecutionResult = await self.cli_runner.run_scraper(collector_id, target_url)

        extracted_data = self._extract_records_from_result(run_res)

        # Step 2: CHECK IF HEALTHY
        if len(extracted_data) > 0:
            await self._emit_event(
                "verifier", "HEALTHY",
                f"Scraper execution healthy, extracted {len(extracted_data)} records",
                {"count": len(extracted_data)},
                target_id=target_id
            )
            await self._persist_records(target_id, run_id, extracted_data)
            await self._update_target_status(target_id, TargetStatus.HEALTHY)
            
            return {
                "run_id": run_id,
                "target_id": target_id,
                "collector_id": collector_id,
                "final_state": ScraperJobState.HEALTHY,
                "recovered": False,
                "extracted_records": extracted_data,
                "duration_ms": (time.time() - start_time) * 1000.0
            }

        # Step 3: FAILURE DETECTED
        error_msg = run_res.stderr or "Empty results returned from scraper execution"
        await self._emit_event(
            "detector", "BROKEN",
            f"Scraper broken: {error_msg}",
            {"exit_code": run_res.exit_code, "stdout": run_res.stdout},
            target_id=target_id
        )

        if not auto_heal:
            await self._update_target_status(target_id, TargetStatus.FAILED)
            return {
                "run_id": run_id,
                "target_id": target_id,
                "collector_id": collector_id,
                "final_state": ScraperJobState.BROKEN,
                "recovered": False,
                "error": error_msg,
                "duration_ms": (time.time() - start_time) * 1000.0
            }

        # Step 4: EVIDENCE COLLECTION
        await self._emit_event(
            "evidence", "EVIDENCE_COLLECTING",
            f"Harvesting DOM, AOM, and screenshot from {target_url}",
            target_id=target_id
        )
        evidence: EvidenceBundle = await self.evidence_collector.collect_from_url(target_url, error_message=error_msg)
        await self._emit_event(
            "evidence", "EVIDENCE_COLLECTED",
            "Rendered DOM and AOM tree extracted",
            {"dom_length": len(evidence.pruned_dom)},
            target_id=target_id
        )

        # Step 5: AI DIAGNOSIS
        await self._emit_event("diagnoser", "DIAGNOSING", "Sending evidence bundle to Gemini 3.7 Flash", target_id=target_id)
        
        # Determine target field to heal
        schema = await self.db.get_latest_schema(target_id) if target_id and self.db else None
        target_field = schema.fields[0].name if schema and schema.fields else "target_data"

        proposal: RepairProposal = await self.diagnoser.diagnose_and_propose(
            evidence,
            target_field=target_field,
            schema_context=schema.model_dump() if schema else None
        )
        await self._emit_event(
            "diagnoser", "DIAGNOSED",
            f"Gemini diagnosis: {proposal.diagnosis}",
            proposal.model_dump(),
            target_id=target_id
        )

        # Step 6: DETERMINISTIC VALIDATION
        is_valid, validation_reason = self.validator.validate(proposal, evidence.pruned_dom)
        if not is_valid:
            await self._emit_event(
                "validator", "REJECTED",
                f"Validation rejected proposal: {validation_reason}",
                target_id=target_id
            )
            await self._update_target_status(target_id, TargetStatus.FAILED)
            return {
                "run_id": run_id,
                "target_id": target_id,
                "collector_id": collector_id,
                "final_state": ScraperJobState.FAILED,
                "recovered": False,
                "error": f"RepairProposal validation failed: {validation_reason}",
                "duration_ms": (time.time() - start_time) * 1000.0
            }
        await self._emit_event(
            "validator", "VALIDATED",
            "Repair proposal passed deterministic safety and DOM checks",
            target_id=target_id
        )

        # Step 7: BRIGHT DATA HEAL
        await self._emit_event(
            "healer", "HEALING",
            f"Executing bdata scraper heal with prompt: {proposal.repair_prompt}",
            target_id=target_id
        )
        heal_res: CliExecutionResult = await self.cli_runner.heal_scraper(collector_id, target_url, proposal.repair_prompt)
        await self._emit_event(
            "healer", "AWAITING_APPROVAL",
            "Heal envelope received",
            {"status": heal_res.status_label, "output": heal_res.stdout},
            target_id=target_id
        )

        # Step 8: APPROVE FIX
        await self._emit_event(
            "approval", "APPROVING",
            f"Approving fix on collector {collector_id}",
            target_id=target_id
        )
        approve_res: CliExecutionResult = await self.cli_runner.approve_scraper(collector_id, target_url)
        await self._emit_event(
            "approval", "APPROVED",
            "Collector schema fix approved",
            {"status": approve_res.status_label},
            target_id=target_id
        )

        # Step 9: RE-RUN & FINAL VERIFICATION
        await self._emit_event("verifier", "RE_RUNNING", "Re-running scraper after approval", target_id=target_id)
        rerun_res: CliExecutionResult = await self.cli_runner.run_scraper(collector_id, target_url)
        final_records = self._extract_records_from_result(rerun_res)

        if len(final_records) > 0:
            await self._emit_event(
                "verifier", "HEALTHY",
                f"Self-healing complete! Successfully extracted {len(final_records)} records",
                {"count": len(final_records)},
                target_id=target_id
            )
            await self._persist_records(target_id, run_id, final_records)
            await self._update_target_status(target_id, TargetStatus.HEALTHY, healed=True)

            return {
                "run_id": run_id,
                "target_id": target_id,
                "collector_id": collector_id,
                "final_state": ScraperJobState.HEALTHY,
                "recovered": True,
                "extracted_records": final_records,
                "repair_proposal": proposal.model_dump(),
                "duration_ms": (time.time() - start_time) * 1000.0
            }
        else:
            await self._emit_event("verifier", "FAILED", "Re-run after heal returned empty results", target_id=target_id)
            await self._update_target_status(target_id, TargetStatus.FAILED)
            return {
                "run_id": run_id,
                "target_id": target_id,
                "collector_id": collector_id,
                "final_state": ScraperJobState.FAILED,
                "recovered": False,
                "error": "Post-heal re-run produced zero records",
                "duration_ms": (time.time() - start_time) * 1000.0
            }

    def _extract_records_from_result(self, result: CliExecutionResult) -> List[Dict[str, Any]]:
        """Parses output rows from CLI JSON response."""
        if not result or result.exit_code != 0:
            return []
        data = result.parsed_json
        if isinstance(data, list):
            return [r for r in data if isinstance(r, dict) and any(r.values())]
        elif isinstance(data, dict):
            if "data" in data and isinstance(data["data"], list):
                return data["data"]
            elif any(data.values()):
                return [data]
        return []

    async def _persist_records(self, target_id: Optional[str], run_id: str, records: List[Dict[str, Any]]) -> None:
        if not self.db:
            return
        
        # 1. Save to generic dynamic_records
        effective_target_id = target_id or "default_target"
        for r in records:
            dynamic_rec = DynamicRecord(
                target_id=effective_target_id,
                run_id=run_id,
                data=r,
                is_simulated=False
            )
            await self.db.save_dynamic_record(dynamic_rec)

            # 2. Also save to legacy threat_records if CVE-like identifier is found
            cve_id = r.get("cve_id") or r.get("id") or r.get("CVE") or r.get("cve")
            if cve_id:
                threat = ThreatRecord(
                    cve_id=str(cve_id),
                    title=str(r.get("title") or r.get("description") or r.get("name") or ""),
                    severity=str(r.get("severity") or r.get("impact") or "HIGH").upper(),
                    published_date=str(r.get("date") or r.get("published") or r.get("published_date") or ""),
                    url=str(r.get("url") or ""),
                    source="Target Harvester",
                    raw_payload=r
                )
                await self.db.save_threat_record(threat)

    async def _update_target_status(self, target_id: Optional[str], status: TargetStatus, healed: bool = False) -> None:
        if not target_id or not self.db:
            return
        target = await self.db.get_target(target_id)
        if target:
            target.status = status
            target.health = 1.0 if status == TargetStatus.HEALTHY else (0.5 if status == TargetStatus.DEGRADED else 0.0)
            if healed:
                target.last_healed = datetime.utcnow()
            await self.db.save_target(target)
