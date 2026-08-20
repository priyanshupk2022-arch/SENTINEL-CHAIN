# SENTINEL-CHAIN: Target Domain Model & Multi-Target Isolation

## 1. Domain Entities

### `Target`
- `id`: UUID
- `name`: String
- `url`: Validated HTTP/HTTPS URL
- `domain`: Fully qualified hostname
- `status`: `READY` | `INSPECTING` | `RUNNING` | `HEALTHY` | `DEGRADED` | `FAILED` | `HEALING` | `DISABLED`
- `health`: Float (0.0 to 1.0)
- `monitoring_enabled`: Boolean
- `schedule`: `MANUAL` | `INTERVAL_5M` | `INTERVAL_15M` | `HOURLY` | `DAILY`
- `is_demo`: Boolean (Distinguishes production targets from controlled chaos sandboxes)

### `TargetInspection`
- `target_id`: Foreign key
- `page_type`: `TABLE` | `CARD_GRID` | `ARTICLE_LIST` | `SINGLE_DOCUMENT`
- `candidate_fields`: Discovered semantic properties
- `candidate_selectors`: Key CSS selectors for containers and children
- `sample_records`: Initial preview records

## 2. Multi-Target Concurrency & Isolation
All runs, schemas, records, and SSE events are strictly partitioned by `target_id` to prevent cross-target state pollution.
