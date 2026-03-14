# Service Setup (Free Tier)

## 1. Environment

Populate `.env` from `.env.example`.
For a judge-demo-ready key mapping, use `.env.demo.template` as reference.

Required for local minimum:
- `DATABASE_URL`
- `QDRANT_URL`

Optional but recommended:
- `TAVILY_API_KEY`
- `FIRECRAWL_API_KEY`
- `OPENROUTER_API_KEY` (+ optional `OPENROUTER_MODEL`)
- `SARVAM_API_KEY`
- `LANDINGAI_API_KEY`
- `DATABRICKS_HOST` + `DATABRICKS_TOKEN` + `DATABRICKS_WAREHOUSE_ID`

## 2. Launch

- `docker compose up --build`
- API docs: `http://localhost:8000/docs`
- UI: `http://localhost:3000`

## 3. Data bootstrap

- `python scripts/fetch_ibbi_data.py`
- `python scripts/fetch_nse_filings.py`
- `python scripts/build_training_dataset.py`
- `cd apps/api && python -m app.services.ml.train`

## 4. Seed and execute full demo

- `python scripts/seed_demo_case.py`
- Optional manual review resume path:
  - `POST /cases/{case_id}/run?manual_approval=false` (may hold export)
  - `POST /cases/{case_id}/run?manual_approval=true` (finalize after approval)

Artifacts:
- CAM DOCX/PDF in `data/exports/`
- Model artifact in `data/checkpoints/`
- Training provenance in `data/processed/training_dataset.provenance.json`
- Notebook workflow in `notebooks/training_pipeline.ipynb`
