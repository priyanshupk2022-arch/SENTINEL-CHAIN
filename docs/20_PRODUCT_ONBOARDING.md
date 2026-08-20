# SENTINEL-CHAIN: Product Onboarding & Discovery Architecture

## 1. Overview
SENTINEL-CHAIN provides a user-driven, zero-friction onboarding flow allowing operators to monitor arbitrary public websites, extract structured entities, and maintain self-healing resilience against DOM mutations.

## 2. Onboarding Workflow
```
+---------------------------+
| User Provides Target URL  |
+-------------+-------------+
              |
              v
+---------------------------+
| SSRF Security Validation  |  --> Reject 127.0.0.1, 169.254.169.254, Private CIDRs
+-------------+-------------+
              | (Passed)
              v
+---------------------------+
| Target Deep Inspection    |  --> Headless Playwright: DOM, AOM, Tables, Cards, Fields
+-------------+-------------+
              |
              v
+---------------------------+
| Natural Language Intent   |  --> "Extract product title, price, rating, stock"
+-------------+-------------+
              |
              v
+---------------------------+
| Gemini 3.7 Flash Schema   |  --> Strongly-typed ExtractionSchema with validation rules
+-------------+-------------+
              |
              v
+---------------------------+
| Human Review & Scraper    |  --> Binds Target + Schema -> Active Bright Data Collector
+---------------------------+
```

## 3. Web Discovery Catalog
Operators can search the built-in public target catalog via `/api/discovery/search` for pre-configured domains (Exploit-DB, NIST NVD, Books to Scrape, Quotes Directory, Hacker News).
