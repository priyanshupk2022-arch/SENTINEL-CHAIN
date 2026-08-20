# SENTINEL-CHAIN: Extraction Schema & Gemini 3.7 Synthesis

## 1. Schema Definition
An `ExtractionSchema` establishes a typed, versioned data extraction contract between the target website and Bright Data Scraper Studio.

### Field Types:
- `string`: Raw text, identifiers, summaries
- `number`: Numeric metrics, counts, scores
- `currency`: Monetary values, prices
- `date`: ISO timestamp or calendar date
- `url`: Permalinks, image links, asset endpoints
- `boolean`: Flags, in-stock indicators
- `array`: Nested list properties

## 2. Gemini 3.7 Flash Synthesis Protocol
1. User provides natural language prompt (e.g. *"Extract CVE ID, title, severity and date"*).
2. Playwright extracts candidate DOM classes, table headers, and ARIA tokens.
3. Gemini 3.7 Flash analyzes the combination and produces a validated JSON schema.
4. The user reviews and edits fields via the UI before deploying the scraper.
