# Operational Runbook

## Daily operation

1. Verify API health: `GET /health`
2. Verify queue depth / case statuses: `GET /cases`
3. Run training refresh if new dataset available: `POST /training/train`
4. Monitor failed cases and retry after root-cause review

## Incident handling

- OCR quality drop:
  - lower `OCR_CONFIDENCE_THRESHOLD` carefully
  - verify LandingAI credits and fallback behavior
- Research API outage:
  - continue with cached/internal evidence
  - mark research confidence as Amber
- Model artifact missing:
  - trigger training endpoint
  - verify checkpoint path permissions

## Human override protocol

- Every override requires:
  - reviewer identity
  - clear rationale
  - timestamped record via `POST /cases/{id}/override`

## Data retention

- Uploaded docs in `data/raw/uploads`
- Exports in `data/exports`
- Audit records in SQLite
- Apply retention and secure archival policy before production deployment
