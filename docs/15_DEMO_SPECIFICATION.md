# 15 DEMO SPECIFICATION
**The Problem:** Mutating the judge's local browser doesn't break the remote Bright Data scraper.
**The Solution (Transparent Chaos Proxy):**
1. Bright Data is configured to scrape `https://our-backend/api/proxy/target`.
2. Our backend proxies traffic to Exploit-DB.
3. **REAL:** The scraper, the failure, the AI, the CLI heal.
4. **CONTROLLED:** The UI "Chaos Slider" mutates the HTML inside our proxy *before* it reaches Bright Data, guaranteeing a deterministic failure within the 2-minute demo window.
