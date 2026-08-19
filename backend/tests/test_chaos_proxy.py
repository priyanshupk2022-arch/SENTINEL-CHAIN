import pytest
from backend.app.chaos.chaos_proxy import ChaosProxyManager, ChaosMode

@pytest.mark.asyncio
async def test_chaos_proxy_clean_mode():
    manager = ChaosProxyManager()
    manager.set_mode(ChaosMode.CLEAN)
    
    html = manager.get_target_html()
    assert "<table" in html
    assert "cve-id" in html
    assert "CVE-2026-4401" in html
    assert manager.get_current_mode() == ChaosMode.CLEAN

@pytest.mark.asyncio
async def test_chaos_proxy_mutations():
    manager = ChaosProxyManager()
    
    # 1. Test class_renamed mode
    manager.set_mode(ChaosMode.CLASS_RENAMED)
    html_renamed = manager.get_target_html()
    assert "vulnerability-badge" in html_renamed
    assert "class=\"cve-id\"" not in html_renamed
    assert "CVE-2026-4401" in html_renamed

    # 2. Test table_to_cards mode
    manager.set_mode(ChaosMode.TABLE_TO_CARDS)
    html_cards = manager.get_target_html()
    assert "<table" not in html_cards
    assert "exploit-card" in html_cards
    assert "threat-title" in html_cards
    assert "CVE-2026-4401" in html_cards

    # 3. Reset to clean
    manager.set_mode(ChaosMode.CLEAN)
    assert manager.get_current_mode() == ChaosMode.CLEAN
    assert "<table" in manager.get_target_html()
