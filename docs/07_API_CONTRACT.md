# 07 API CONTRACT
| METHOD | PATH | PURPOSE |
|---|---|---|
| GET | `/api/stream` | SSE Telemetry (React Flow updates) |
| GET | `/api/proxy/target` | Chaos Proxy for Bright Data Scraper |
| POST | `/api/chaos/enable` | Sets chaos level to 1 |
| POST | `/api/chaos/disable` | Sets chaos level to 0 |
| POST | `/api/scraper/trigger` | Manually kicks off the pipeline |
