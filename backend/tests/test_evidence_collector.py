import pytest
from backend.app.engine.evidence_collector import PlaywrightEvidenceCollector
from backend.app.chaos.chaos_proxy import ChaosProxyManager, ChaosMode
from backend.app.models.domain import EvidenceBundle

@pytest.mark.asyncio
async def test_evidence_collector_pruning():
    collector = PlaywrightEvidenceCollector()
    raw_html = """
    <html>
        <head><style>.bad { display: none; }</style><script>alert(1);</script></head>
        <body>
            <noscript>Enable JS</noscript>
            <table class="exploit-table">
                <tr><td class="cve-id">CVE-2026-1111</td><td>Test Vulnerability</td></tr>
            </table>
        </body>
    </html>
    """
    pruned = collector.prune_html(raw_html)
    assert "<script" not in pruned
    assert "<style" not in pruned
    assert "<noscript" not in pruned
    assert "cve-id" in pruned
    assert "CVE-2026-1111" in pruned

@pytest.mark.asyncio
async def test_evidence_collector_bundle_generation():
    collector = PlaywrightEvidenceCollector()
    manager = ChaosProxyManager()
    manager.set_mode(ChaosMode.CLEAN)
    html = manager.get_target_html()

    bundle = await collector.collect_from_html(
        target_url="http://127.0.0.1:8000/api/proxy/target",
        html_content=html,
        error_message="Selector .cve-id failed to match"
    )

    assert isinstance(bundle, EvidenceBundle)
    assert bundle.target_url == "http://127.0.0.1:8000/api/proxy/target"
    assert "Selector .cve-id failed" in bundle.error_message
    assert len(bundle.pruned_dom) > 0
    assert "CVE-2026-4401" in bundle.pruned_dom
