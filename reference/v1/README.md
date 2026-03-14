# Intelli-Credit Copilot

Production-style implementation baseline for Indian corporate credit underwriting with:
- LangGraph-based controlled agent orchestration
- Document ingestion (OCR + extraction + evidence graph)
- Secondary research intelligence
- India-specific reconciliation signals
- Explainable ML risk scoring
- Decisioning (limit, spread, covenants)
- CAM generation with evidence confidence markers
- Audit logs and reproducible workflows

## Monorepo layout

- `apps/api` FastAPI backend (orchestration + intelligence engine)
- `apps/web` Next.js portal (case dashboard and workbench)
- `scripts` dataset acquisition + real-feature building + seeding
- `data` raw/processed/training/demo artifacts
- `docs` architecture, operations, and demo walkthrough
- `apps/api/tests` backend unit/integration tests

## Quickstart

1. Copy env template:
   - `cp .env.example .env`
   - set strong `API_ACCESS_KEY` and `OVERRIDE_ACCESS_KEY` (minimum 24 chars, must differ)
2. Start backend and vector DB:
   - `docker compose up --build`
3. Seed a demo case:
   - `make seed-demo`
4. Run training pipeline:
   - `make fetch-data`
   - `make train`
   - optional notebook: `notebooks/training_pipeline.ipynb`
5. Open UI:
   - `http://localhost:3000`
6. Open API docs:
   - `http://localhost:8000/docs`

Frontend calls require `x-api-key` and override calls require `x-override-key`. You can configure both from the Settings page in the UI.

## Free-tier service strategy

- Databricks Free Edition (optional external warehouse)
- Qdrant Cloud free 1GB or local Qdrant container
- Tavily free plan for search
- Firecrawl free credits for fetch/clean
- OpenRouter `:free` models for drafting/reasoning
- Sarvam OCR as primary parser
- LandingAI credits as fallback OCR router

When integrations are missing, the workflow emits explicit degradation warnings and non-green confidence instead of synthetic-looking placeholder results.

## Reliability and trust controls

- Evidence-only claim generation with Green/Amber/Red confidence tags
- Policy hard-stops separated from ML score
- Audit event ledger for every workflow transition
- Explainability via SHAP and reason-code mapping
- Temporal split validation + calibration/confusion artifacts
- Counterfactual recommendations and threshold simulations

## Status

See the live progress tracker in `IMPLEMENTATION_CHECKLIST.md`.
