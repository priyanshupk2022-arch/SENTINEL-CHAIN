import base64
import logging
import re
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright
from backend.app.models.domain import EvidenceBundle

logger = logging.getLogger("sentinel.evidence_collector")

class EvidenceCollector:
    def __init__(self, headless: bool = True):
        self.headless = headless

    def prune_html(self, raw_html: str, max_chars: int = 50000) -> str:
        """
        Removes scripts, styles, SVGs, iframes, noscripts, and non-semantic attributes
        to reduce HTML payload from ~2MB to ~30-50KB semantic tree for Gemini.
        """
        if not raw_html:
            return ""
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            for tag in soup(["script", "style", "svg", "noscript", "iframe", "link", "meta"]):
                tag.decompose()

            cleaned_html = str(soup)
            cleaned_html = re.sub(r'\n\s*\n', '\n', cleaned_html)
            if len(cleaned_html) > max_chars:
                cleaned_html = cleaned_html[:max_chars] + "\n<!-- [TRUNCATED] -->"
            return cleaned_html
        except Exception as e:
            logger.warning(f"Error during HTML pruning: {e}")
            return raw_html[:max_chars]

    def _extract_aom_text(self, soup: BeautifulSoup) -> str:
        lines = []
        for el in soup.find_all(["h1", "h2", "h3", "table", "tr", "th", "td", "article", "button", "a", "span", "div"]):
            aria_label = el.get("aria-label")
            role = el.get("role")
            data_id = el.get("data-id") or el.get("data-cve") or el.get("data-threat-ref")
            text = el.get_text(strip=True)
            if aria_label or role or data_id or (el.name in ["h1", "h2", "h3", "th", "td"] and text):
                tag_desc = f"[{el.name}]"
                if role:
                    tag_desc += f"(role={role})"
                if aria_label:
                    tag_desc += f"(label='{aria_label}')"
                if data_id:
                    tag_desc += f"(data-ref='{data_id}')"
                if text and len(text) < 100:
                    tag_desc += f" -> '{text}'"
                lines.append(tag_desc)
        return "\n".join(lines[:100])

    async def collect_from_html(self, target_url: str, html_content: str, error_message: str = "") -> EvidenceBundle:
        pruned = self.prune_html(html_content)
        soup = BeautifulSoup(html_content, "html.parser")
        aom = self._extract_aom_text(soup)
        return EvidenceBundle(
            target_url=target_url,
            error_message=error_message or "Selector extraction failed",
            status_code=200,
            pruned_dom=pruned,
            aom_tree=aom,
            screenshot_b64=None
        )

    async def collect_from_url(self, target_url: str, error_message: str = "", capture_screenshot: bool = True) -> EvidenceBundle:
        logger.info(f"Opening Playwright for evidence collection at {target_url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page(viewport={"width": 1280, "height": 800})
            try:
                response = await page.goto(target_url, wait_until="networkidle", timeout=15000)
                status_code = response.status if response else 200
                raw_html = await page.content()
                pruned_dom = self.prune_html(raw_html)

                aom_tree = ""
                try:
                    snapshot = await page.accessibility.snapshot()
                    if snapshot:
                        aom_tree = str(snapshot)
                except Exception:
                    soup = BeautifulSoup(raw_html, "html.parser")
                    aom_tree = self._extract_aom_text(soup)

                screenshot_b64 = None
                if capture_screenshot:
                    try:
                        screenshot_bytes = await page.screenshot(type="png", full_page=False)
                        screenshot_b64 = "data:image/png;base64," + base64.b64encode(screenshot_bytes).decode("utf-8")
                    except Exception as e:
                        logger.warning(f"Failed to capture screenshot: {e}")

                await browser.close()

                return EvidenceBundle(
                    target_url=target_url,
                    error_message=error_message or f"Scraper failure on {target_url}",
                    status_code=status_code,
                    pruned_dom=pruned_dom,
                    aom_tree=aom_tree,
                    screenshot_b64=screenshot_b64
                )
            except Exception as e:
                await browser.close()
                logger.error(f"Playwright navigation error for {target_url}: {e}")
                return EvidenceBundle(
                    target_url=target_url,
                    error_message=f"Navigation/Rendering failure: {str(e)}",
                    status_code=500,
                    pruned_dom="",
                    aom_tree="",
                    screenshot_b64=None
                )

# Aliases
PlaywrightEvidenceCollector = EvidenceCollector
