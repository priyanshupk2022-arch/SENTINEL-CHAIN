import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Query

logger = logging.getLogger("sentinel.api.discovery")
router = APIRouter(prefix="/api/discovery", tags=["Discovery"])

PUBLIC_TARGET_CATALOG = [
    {
        "id": "cve-exploit-db",
        "name": "Exploit-DB Security Advisories",
        "domain": "exploit-db.com",
        "url": "https://www.exploit-db.com/",
        "description": "Public archive of exploits and software vulnerability advisories.",
        "category": "Cybersecurity / Threat Intelligence",
        "status": "ACCESSIBLE",
        "suggested_fields": ["cve_id", "title", "published_date", "author", "type", "platform"]
    },
    {
        "id": "nvd-nist-cve",
        "name": "NIST National Vulnerability Database",
        "domain": "nvd.nist.gov",
        "url": "https://nvd.nist.gov/vuln/search",
        "description": "U.S. government repository of standards-based vulnerability management data.",
        "category": "Cybersecurity / Standards",
        "status": "ACCESSIBLE",
        "suggested_fields": ["cve_id", "description", "cvss_score", "published_date"]
    },
    {
        "id": "books-toscrape",
        "name": "Books to Scrape Catalog",
        "domain": "books.toscrape.com",
        "url": "http://books.toscrape.com/",
        "description": "Public bookstore catalog with category browsing, pricing, and stock status.",
        "category": "E-Commerce / Retail",
        "status": "ACCESSIBLE",
        "suggested_fields": ["product_name", "price", "rating", "availability", "upc"]
    },
    {
        "id": "quotes-toscrape",
        "name": "Quotes Archive Directory",
        "domain": "quotes.toscrape.com",
        "url": "http://quotes.toscrape.com/",
        "description": "Public directory of famous quotes categorized by authors and topical tags.",
        "category": "Media / Public Directory",
        "status": "ACCESSIBLE",
        "suggested_fields": ["quote", "author", "tags"]
    },
    {
        "id": "hacker-news",
        "name": "Hacker News Technical Stream",
        "domain": "news.ycombinator.com",
        "url": "https://news.ycombinator.com/",
        "description": "Real-time tech news feed with links, points, and discussion counts.",
        "category": "News / Feeds",
        "status": "ACCESSIBLE",
        "suggested_fields": ["headline", "url", "points", "author", "comments_count"]
    }
]

@router.get("/search", response_model=List[Dict[str, Any]])
async def search_discovery_targets(query: str = Query(default="", min_length=0)):
    """
    Returns candidate public targets matching the user's discovery query.
    """
    q = query.lower().strip()
    if not q:
        return PUBLIC_TARGET_CATALOG

    results = []
    for item in PUBLIC_TARGET_CATALOG:
        match_score = 0
        if q in item["name"].lower():
            match_score += 3
        if q in item["description"].lower():
            match_score += 2
        if q in item["category"].lower():
            match_score += 2
        if any(q in f for f in item["suggested_fields"]):
            match_score += 1

        if match_score > 0:
            results.append(item)

    return results if results else PUBLIC_TARGET_CATALOG[:3]
