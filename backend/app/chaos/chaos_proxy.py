import logging
from enum import Enum
from typing import Dict, Any, List

logger = logging.getLogger("sentinel.chaos_proxy")

class ChaosMode(str, Enum):
    CLEAN = "clean"
    CLASS_RENAMED = "class_renamed"
    TABLE_TO_CARDS = "table_to_cards"
    DEEP_NESTING = "deep_nesting"
    CONTAINER_WRAP = "container_wrap"

SAMPLE_VULNERABILITIES = [
    {
        "cve_id": "CVE-2026-4401",
        "title": "OpenSSL ASN.1 Parsing Remote Buffer Overflow",
        "severity": "CRITICAL",
        "date": "2026-08-15",
        "author": "Security Research Labs",
        "type": "Remote"
    },
    {
        "cve_id": "CVE-2026-9021",
        "title": "Linux Kernel eBPF Privilege Escalation via Map Use-After-Free",
        "severity": "HIGH",
        "date": "2026-08-14",
        "author": "Kernel Guard",
        "type": "Local"
    },
    {
        "cve_id": "CVE-2026-3199",
        "title": "Kubernetes Ingress-NGINX Header Injection RCE",
        "severity": "CRITICAL",
        "date": "2026-08-12",
        "author": "CloudSec Team",
        "type": "Remote"
    },
    {
        "cve_id": "CVE-2026-7810",
        "title": "PostgreSQL Stored Procedure Memory Disclosure",
        "severity": "MEDIUM",
        "date": "2026-08-10",
        "author": "Database Audit Group",
        "type": "Authenticated"
    }
]

class ChaosProxyManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChaosProxyManager, cls).__new__(cls)
            cls._instance._mode = ChaosMode.CLEAN
        return cls._instance

    def set_mode(self, mode: ChaosMode) -> ChaosMode:
        self._mode = mode
        logger.info(f"Chaos mode set to: {self._mode}")
        return self._mode

    def get_current_mode(self) -> ChaosMode:
        return self._mode

    def get_target_html(self) -> str:
        """Generates dynamic HTML representing the target threat intelligence feed based on active chaos mode."""
        if self._mode == ChaosMode.CLEAN:
            return self._render_clean_table()
        elif self._mode == ChaosMode.CLASS_RENAMED:
            return self._render_class_renamed()
        elif self._mode == ChaosMode.TABLE_TO_CARDS:
            return self._render_table_to_cards()
        elif self._mode == ChaosMode.DEEP_NESTING:
            return self._render_deep_nesting()
        else:
            return self._render_clean_table()

    def _render_clean_table(self) -> str:
        rows_html = ""
        for v in SAMPLE_VULNERABILITIES:
            rows_html += f"""
            <tr class="cve-row" data-id="{v['cve_id']}">
                <td class="cve-id" aria-label="CVE Identifier">{v['cve_id']}</td>
                <td class="cve-title" aria-label="Vulnerability Title">{v['title']}</td>
                <td class="cve-severity severity-{v['severity'].lower()}" aria-label="Severity Level">{v['severity']}</td>
                <td class="cve-date" aria-label="Publish Date">{v['date']}</td>
                <td class="cve-author">{v['author']}</td>
            </tr>
            """
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Exploit-DB Vulnerability Intelligence Feed (Clean Baseline)</title>
    <style>
        body {{ font-family: monospace; background: #0f172a; color: #f8fafc; padding: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #334155; padding: 12px; text-align: left; }}
        th {{ background: #1e293b; color: #38bdf8; }}
        .cve-id {{ color: #38bdf8; font-weight: bold; }}
        .severity-critical {{ color: #ef4444; font-weight: bold; }}
        .severity-high {{ color: #f97316; }}
        .severity-medium {{ color: #eab308; }}
    </style>
</head>
<body>
    <h1>Verified Exploit Database - Security Intelligence</h1>
    <div id="vulnerability-container">
        <table class="exploit-table" role="table" aria-label="CVE List">
            <thead>
                <tr>
                    <th>CVE ID</th>
                    <th>Vulnerability Title</th>
                    <th>Severity</th>
                    <th>Date</th>
                    <th>Author</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
</body>
</html>"""

    def _render_class_renamed(self) -> str:
        rows_html = ""
        for v in SAMPLE_VULNERABILITIES:
            rows_html += f"""
            <tr class="vulnerability-item-row" data-threat-ref="{v['cve_id']}">
                <td class="vulnerability-badge" aria-label="CVE Identifier">{v['cve_id']}</td>
                <td class="vulnerability-summary" aria-label="Vulnerability Title">{v['title']}</td>
                <td class="threat-rank level-{v['severity'].lower()}" aria-label="Severity Level">{v['severity']}</td>
                <td class="timestamp-column" aria-label="Publish Date">{v['date']}</td>
                <td class="researcher-name">{v['author']}</td>
            </tr>
            """
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Exploit-DB Vulnerability Feed (Mutated: Class Renamed)</title>
</head>
<body>
    <h1>Verified Exploit Database - Security Intelligence</h1>
    <div id="vulnerability-container">
        <table class="threat-data-grid" role="table" aria-label="CVE List">
            <thead>
                <tr>
                    <th>Identifier</th>
                    <th>Description</th>
                    <th>Impact</th>
                    <th>Disclosed</th>
                    <th>Researcher</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
</body>
</html>"""

    def _render_table_to_cards(self) -> str:
        cards_html = ""
        for v in SAMPLE_VULNERABILITIES:
            cards_html += f"""
            <article class="exploit-card" data-cve="{v['cve_id']}">
                <div class="card-header">
                    <span class="threat-badge-id" aria-label="CVE Identifier">{v['cve_id']}</span>
                    <span class="threat-severity-pill pill-{v['severity'].lower()}" aria-label="Severity Level">{v['severity']}</span>
                </div>
                <h3 class="threat-title" aria-label="Vulnerability Title">{v['title']}</h3>
                <div class="card-footer">
                    <span class="disclosure-time" aria-label="Publish Date">{v['date']}</span>
                    <span class="credit-author">{v['author']}</span>
                </div>
            </article>
            """
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Exploit-DB Redesign (Mutated: Table to Cards)</title>
</head>
<body>
    <h1>Verified Exploit Database - Security Intelligence</h1>
    <div class="threat-cards-feed" role="feed" aria-label="Vulnerability Cards">
        {cards_html}
    </div>
</body>
</html>"""

    def _render_deep_nesting(self) -> str:
        items_html = ""
        for v in SAMPLE_VULNERABILITIES:
            items_html += f"""
            <div class="threat-block">
                <section class="nested-wrapper">
                    <header class="block-top">
                        <div class="code-wrapper">
                            <span class="cve-ref-label" aria-label="CVE Identifier">{v['cve_id']}</span>
                        </div>
                        <div class="rating-box">
                            <span class="severity-rating">{v['severity']}</span>
                        </div>
                    </header>
                    <main class="block-body">
                        <p class="summary-text" aria-label="Vulnerability Title">{v['title']}</p>
                    </main>
                </section>
            </div>
            """
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Exploit-DB Mutated (Deep Nested Layout)</title>
</head>
<body>
    <div id="app-root">
        <main class="main-content">
            <div class="feed-container">
                {items_html}
            </div>
        </main>
    </div>
</body>
</html>"""
