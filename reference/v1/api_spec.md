# API Surface Summary

## Health
- `GET /health`

## Cases
- `POST /cases`
- `GET /cases`
- `GET /cases/{case_id}`
- `POST /cases/{case_id}/documents`
- `POST /cases/{case_id}/upload`
- `GET /cases/{case_id}/documents`
- `POST /cases/{case_id}/run?manual_approval={bool}&use_langgraph={bool}`
- `GET /cases/{case_id}/evidence`
- `GET /cases/{case_id}/audit`
- `POST /cases/{case_id}/override`
- `POST /cases/{case_id}/search`

## Training
- `POST /training/train`
- `GET /training/metrics`

## Demo
- `POST /demo/seed-and-run`

See interactive OpenAPI docs at `/docs`.
