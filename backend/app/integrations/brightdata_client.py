import os
import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class BrightDataClient:
    def __init__(self):
        self.customer_id = os.getenv("BRIGHT_DATA_CUSTOMER_ID", "hl_mock")
        self.zone = os.getenv("BRIGHT_DATA_ZONE", "scraping_browser")
        self.password = os.getenv("BRIGHT_DATA_PASSWORD", "mock_pass")
        self.host = os.getenv("BRIGHT_DATA_HOST", "brd.superproxy.io:9222")
        self.mock_mode = os.getenv("MOCK_BRIGHTDATA", "false").lower() == "true"

    async def connect_session(self, country: str = "us"):
        """Connect to Bright Data Scraping Browser or return mock-routed local browser."""
        if self.mock_mode:
            return await self._create_mock_session()

        auth = f"brd-customer-{self.customer_id}-zone-{self.zone}-country-{country.lower()}:{self.password}"
        ws_endpoint = f"wss://{auth}@{self.host}"

        try:
            p = await async_playwright().start()
            browser = await p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = context.pages[0] if context.pages else await context.new_page()
            cdp = await context.new_cdp_session(page)

            # Bright Data-specific CDP extension for auto CAPTCHA solving
            try:
                await cdp.send("Captcha.setAutoSolve", {"autoSolve": True})
            except Exception:
                logger.warning("Captcha.setAutoSolve not available; CAPTCHA bypass via proxy headers")

            return browser, page, cdp
        except Exception as e:
            logger.error(f"Bright Data connection failed: {e}")
            raise ConnectionError(f"Cannot connect to Bright Data: {e}")

    async def _create_mock_session(self):
        """Returns a REAL local Playwright browser with page.route() intercepting
        all network requests and serving pre-recorded HTML fixture files.
        Downstream code receives real browser/page/cdp objects — no AttributeErrors."""
        p = await async_playwright().start()
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Intercept ALL requests and serve local HTML fixtures
        async def route_handler(route):
            from backend.app.integrations.mock_fixtures import MockFixtureManager
            fixture = MockFixtureManager.get_fixture(route.request.url)
            if fixture:
                await route.fulfill(status=200, content_type="text/html", body=fixture)
            else:
                await route.fulfill(status=200, content_type="text/html", body="<html><body>No fixture</body></html>")

        await page.route("**/*", route_handler)
        cdp = await context.new_cdp_session(page)
        return browser, page, cdp
