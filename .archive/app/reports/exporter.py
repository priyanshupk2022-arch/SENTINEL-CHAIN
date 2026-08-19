"""Tenant-Scoped Audit & Forensic Report Exporter (CSV & JSON)."""
import csv
import io
import json
from typing import List, Dict, Any, Optional

from app.models.database import db

class ReportExporter:
    @staticmethod
    async def export_audit_csv(organization_id: str, limit: int = 1000) -> str:
        """Generates tenant-isolated CSV export of audit logs."""
        logs = await db.get_audit_logs(limit=limit, organization_id=organization_id)
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Timestamp", "Endpoint", "Status", "Risk Score",
            "Latency (ms)", "Findings Count", "Categories", "Actor Type"
        ])

        for log in logs:
            writer.writerow([
                log.get("id"),
                log.get("timestamp"),
                log.get("endpoint"),
                log.get("status"),
                log.get("risk_score"),
                log.get("latency_ms"),
                log.get("findings_count"),
                ";".join(log.get("categories", [])),
                log.get("actor_type")
            ])

        return output.getvalue()

    @staticmethod
    async def export_audit_json(organization_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Generates tenant-isolated JSON export of audit logs."""
        return await db.get_audit_logs(limit=limit, organization_id=organization_id)

report_exporter = ReportExporter()
