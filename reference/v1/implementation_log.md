# Live Implementation Log

Date: 2026-03-05

## Build and validation events

1. Repository scaffolded with API, Web, scripts, docs, and test suites.
2. Public label/control fetch executed:
   - `python scripts/fetch_ibbi_data.py` -> 31 CIRP label rows.
   - `python scripts/fetch_nse_filings.py` -> NSE announcements API returned 500; fallback pulled NIFTY500 control universe (500 rows).
3. Real-feature training dataset built:
   - `MAX_FINANCIAL_FETCH_ROWS=120 python scripts/build_training_dataset.py`
   - output: 93 rows, feature source split:
     - `public_financial_api`: 62
     - `missing_public_financials`: 31
   - no class-conditional synthetic feature generation.
4. Model training pipeline executed:
   - `cd apps/api && python -m app.services.ml.train`
   - split: temporal (`cutoff_date=2024-06-15`)
   - model selected: logistic regression
   - metrics: AUC 0.75, PR-AUC 0.636, Brier 0.193
   - artifacts:
     - `data/checkpoints/risk_model.joblib`
     - `data/checkpoints/risk_model.metrics.json`
     - `data/checkpoints/risk_model.calibration.png`
     - `data/checkpoints/risk_model.confusion.png`
     - `data/checkpoints/risk_model.global_importance.png`
5. Orchestration upgraded to LangGraph default path with review gate and manual approval branch.
6. End-to-end underwriting run executed on LangGraph path:
   - `python scripts/seed_demo_case.py`
   - status: completed
   - decision: reject
   - exports:
     - `data/exports/4e3fdf76-fcf9-4ea3-bb2e-ca46b0daf515_cam.docx`
     - `data/exports/4e3fdf76-fcf9-4ea3-bb2e-ca46b0daf515_cam.pdf`
7. Frontend explainability upgrade completed:
   - SHAP waterfall rendering integrated in `apps/web/app/risk/page.tsx`.
8. Notebook and judge script added:
   - `notebooks/training_pipeline.ipynb`
   - `docs/judge_qa_script.md`
9. Backend validation:
   - `cd apps/api && ruff check app tests` -> all checks passed
   - `cd apps/api && pytest -q` -> 5 passed
10. Frontend validation:
   - `cd apps/web && npm run build` -> success (Next.js 16.1.6)
11. Human-in-loop validation:
   - low-evidence case run with `manual_approval=false` -> `status=needs_review`, exports blocked.
   - rerun with `manual_approval=true` -> `status=completed`, DOCX/PDF exported.
12. Critical remediation follow-up:
   - `scripts/fetch_ibbi_data.py` fixed to parse `Date of Announcement` (no empty IBBI dates).
   - `scripts/fetch_nse_filings.py` rebuilt to parse NSE CSV payload and emit:
     - `data/raw/nse_controls.csv` (2,323 rows)
     - `data/raw/nse_stress_labels.csv` (249 rows)
   - `scripts/build_training_dataset.py` rebuilt with:
     - source-date-only policy (no proxy/hash dates),
     - `eligible_for_model` + `ineligibility_reason`,
     - quality gates on class counts and feature diversity.
   - strict train run:
     - `MAX_FINANCIAL_FETCH_ROWS=0 python scripts/build_training_dataset.py`
     - `cd apps/api && python -m app.services.ml.train`
     - temporal split preserved, no random fallback.
13. Security hardening:
   - upload path traversal closed in `apps/api/app/api/routes/cases.py` using filename sanitization + resolved-path boundary checks.
   - Databricks SQL literal escaping added in `apps/api/app/services/databricks_client.py`.
   - regression tests added:
     - `apps/api/tests/integration/test_upload_security.py`
     - `apps/api/tests/unit/test_databricks_client.py`

## Compliance-focused remediation status

- LangGraph orchestration: implemented.
- Temporal split: implemented.
- Review Agent coverage gate: implemented.
- Calibration + confusion artifacts: implemented.
- Benchmark sanity comparison: implemented (`data/raw/rating_default_priors.csv`).
- Circular heuristics expanded to 6-signal scoring.
- Utilization and litigation/DSRA covenant triggers: implemented.
- Databricks compute pipeline hooks (features/reconciliation/scoring): implemented.
- SQL-injection and upload traversal remediations: implemented + tested.

## Notes

- Qdrant remains optional. If `QDRANT_URL` is unreachable, workflow continues without vector retrieval and logs a warning.
- OCR clients now fail over to local parsing if external endpoints are unreachable.
