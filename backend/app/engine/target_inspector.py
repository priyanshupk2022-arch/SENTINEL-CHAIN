import logging
import urllib.parse
import re
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional, Tuple
import requests
from playwright.async_api import async_playwright
from backend.app.models.domain import TargetInspection, PageType
from backend.app.security.url_validator import SecurityUrlValidator

logger = logging.getLogger("sentinel.inspector")

class TargetInspectionEngine:
    def __init__(self, headless: bool = True):
        self.headless = headless

    async def inspect_target(self, target_id: str, url: str) -> TargetInspection:
        """
        Performs real-world deep inspection of a target website:
        - Validates SSRF & protocol
        - Renders DOM via headless Chromium
        - Classifies page type (Table, Card Grid, Article List)
        - Extracts candidate fields, selectors, containers, and preview records
        """
        # 1. Security & SSRF Validation
        is_valid, reason, canonical_url = SecurityUrlValidator.validate_url(url)
        if not is_valid:
            return TargetInspection(
                target_id=target_id,
                url=url,
                status_code=400,
                page_title="Security Rejected",
                page_type=PageType.UNKNOWN,
                warnings=[f"SSRF Security Policy Rejection: {reason}"]
            )

        target_url = canonical_url or url
        logger.info(f"Initiating deep inspection on target: {target_url}")

        raw_html = ""
        status_code = 200
        final_url = target_url
        page_title = ""
        warnings = []
        rendering_required = False

        # Attempt Playwright rendering
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page(viewport={"width": 1280, "height": 800})
                
                response = await page.goto(target_url, wait_until="domcontentloaded", timeout=12000)
                if response:
                    status_code = response.status
                    final_url = response.url
                
                page_title = await page.title()
                raw_html = await page.content()
                await browser.close()
                rendering_required = True
        except Exception as pw_err:
            logger.warning(f"Playwright inspection error ({pw_err}), falling back to HTTP GET...")
            warnings.append(f"Headless rendering fallback: {str(pw_err)}")
            try:
                res = requests.get(target_url, timeout=5, headers={"User-Agent": "Sentinel-Chain/1.0 WebInspector"})
                status_code = res.status_code
                final_url = res.url
                raw_html = res.text
            except Exception as http_err:
                logger.error(f"HTTP inspection failed for {target_url}: {http_err}")
                return TargetInspection(
                    target_id=target_id,
                    url=target_url,
                    status_code=500,
                    page_title="Unreachable Target",
                    page_type=PageType.UNKNOWN,
                    warnings=[f"Failed to connect to target: {str(http_err)}"]
                )

        # Parse and analyze semantic DOM
        soup = BeautifulSoup(raw_html, "html.parser")
        if not page_title and soup.title:
            page_title = soup.title.get_text(strip=True)

        page_type, candidate_containers, candidate_selectors, candidate_fields, sample_records = self._analyze_dom_structure(soup)

        return TargetInspection(
            target_id=target_id,
            url=target_url,
            final_url=final_url,
            status_code=status_code,
            page_title=page_title or "Untitled Target",
            page_type=page_type,
            rendering_required=rendering_required,
            candidate_fields=candidate_fields,
            candidate_selectors=candidate_selectors,
            candidate_containers=candidate_containers,
            sample_records=sample_records,
            warnings=warnings
        )

    def _analyze_dom_structure(self, soup: BeautifulSoup) -> Tuple[PageType, List[str], Dict[str, str], List[str], List[Dict[str, Any]]]:
        candidate_fields = set()
        candidate_selectors = {}
        candidate_containers = []
        sample_records = []
        page_type = PageType.UNKNOWN

        # 1. Check for Tables
        tables = soup.find_all("table")
        if tables:
            page_type = PageType.TABLE
            candidate_containers.append("table tr")
            for table in tables[:2]:
                for th in table.find_all(["th", "td"]):
                    txt = th.get_text(strip=True).lower()
                    clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', txt).strip('_')
                    if clean_key and len(clean_key) < 30:
                        candidate_fields.add(clean_key)
                
                # Sample rows
                rows = table.find_all("tr")
                for r in rows[1:6]:
                    cols = [td.get_text(strip=True) for td in r.find_all("td")]
                    if cols:
                        sample_records.append({f"col_{i+1}": val for i, val in enumerate(cols[:6])})
            
            candidate_selectors = {"table_row": "tr", "table_cell": "td"}

        # 2. Check for Articles / Cards
        cards = soup.find_all(["article", "div"], class_=lambda c: c and any(k in str(c).lower() for k in ["card", "item", "product", "threat", "row", "post"]))
        if len(cards) >= 3 and page_type != PageType.TABLE:
            page_type = PageType.CARD_GRID
            container_cls = cards[0].get("class", ["card"])[0]
            candidate_containers.append(f".{container_cls}")
            candidate_selectors["card_container"] = f".{container_cls}"

            for card in cards[:5]:
                headings = card.find_all(["h1", "h2", "h3", "h4", "a", "span", "p"])
                record = {}
                for el in headings[:6]:
                    cls_names = el.get("class", [])
                    txt = el.get_text(strip=True)
                    if txt and len(txt) < 100:
                        field_key = cls_names[0] if cls_names else el.name
                        record[field_key] = txt
                        candidate_fields.add(field_key.lower().replace("-", "_"))
                if record:
                    sample_records.append(record)

        # 3. Default list or document fallback
        if not candidate_fields:
            candidate_fields = {"title", "link", "description", "content"}
            candidate_selectors = {"item": "div", "title": "h1, h2, h3", "description": "p"}
            if page_type == PageType.UNKNOWN:
                page_type = PageType.ARTICLE_LIST

        # Auto-detect common semantic patterns
        common_candidates = ["title", "price", "rating", "cve_id", "severity", "date", "status", "author", "category"]
        page_text = soup.get_text().lower()
        for cand in common_candidates:
            if cand in page_text or cand.replace("_", " ") in page_text:
                candidate_fields.add(cand)

        return page_type, candidate_containers, candidate_selectors, sorted(list(candidate_fields))[:15], sample_records[:5]
