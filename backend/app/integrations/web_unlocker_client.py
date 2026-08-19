import os
import httpx
import logging

logger = logging.getLogger(__name__)

class WebUnlockerClient:
    def __init__(self):
        self.customer_id = os.getenv("BRIGHT_DATA_CUSTOMER_ID", "hl_mock")
        self.wu_zone = os.getenv("BRIGHT_DATA_WU_ZONE", "web_unlocker")
        self.password = os.getenv("BRIGHT_DATA_PASSWORD", "mock_pass")
        self.mock_mode = os.getenv("MOCK_BRIGHTDATA", "false").lower() == "true"
        self.proxy_url = (
            f"http://brd-customer-{self.customer_id}-zone-{self.wu_zone}:{self.password}"
            f"@brd.superproxy.io:44445"
        )

    async def fetch(self, url: str) -> str:
        """Fetch URL content via Bright Data Web Unlocker or mock fixtures."""
        if self.mock_mode:
            from backend.app.integrations.mock_fixtures import MockFixtureManager
            return MockFixtureManager.get_fixture(url) or ""

        try:
            async with httpx.AsyncClient(proxy=self.proxy_url, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Web Unlocker fetch failed for {url}: {e}")
            raise
