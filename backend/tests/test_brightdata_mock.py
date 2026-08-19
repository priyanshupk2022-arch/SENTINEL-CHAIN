import pytest
import os
from backend.app.integrations.brightdata_client import BrightDataClient
from backend.app.integrations.web_unlocker_client import WebUnlockerClient

@pytest.mark.asyncio
async def test_brightdata_mock_session():
    os.environ["MOCK_BRIGHTDATA"] = "true"
    client = BrightDataClient()
    browser, page, cdp = await client.connect_session()
    
    assert browser is not None
    assert page is not None
    assert cdp is not None
    
    await page.goto("https://reddit.com")
    content = await page.content()
    assert "Reddit Thread Fixture" in content
    
    await browser.close()

@pytest.mark.asyncio
async def test_web_unlocker_mock():
    os.environ["MOCK_BRIGHTDATA"] = "true"
    client = WebUnlockerClient()
    content = await client.fetch("https://github.com")
    
    assert "GitHub Issues Fixture" in content
