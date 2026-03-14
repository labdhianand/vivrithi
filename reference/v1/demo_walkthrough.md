# Demo Walkthrough

## Goal

Demonstrate a complete underwriting cycle from intake to CAM export.

## Steps

1. Start services:
   - `docker compose up --build`
2. Prepare data:
   - `python scripts/fetch_ibbi_data.py`
   - `python scripts/fetch_nse_filings.py`
   - `python scripts/build_training_dataset.py`
3. Train model:
   - `cd apps/api && python -m app.services.ml.train`
4. Run end-to-end case:
   - `python scripts/seed_demo_case.py`
   - or web-backed blended pack:
     - `python scripts/build_e2e_demo_pack.py`
     - `python scripts/run_e2e_demo_from_pack.py --mode blended --manual-approval`
5. Open portal:
   - `http://localhost:3000`

## What to show in UI

1. Overview
   - model metrics (AUC, PR-AUC)
   - completed case count
2. Cases
   - selected case status and decision
   - run controls
3. Research
   - citation-backed intelligence rows
4. Risk
   - PD and grade
   - SHAP waterfall + top-driver contributions
   - policy hard-stops and covenants
5. CAM Studio
   - generated markdown
   - DOCX/PDF artifact paths
6. Review gate
   - run with `manual_approval=false` to demonstrate hold path
   - rerun with `manual_approval=true` to finalize export

## Narrative script

- Show reconciliation anomalies and their score contribution.
- Show contradiction narrative: "despite X, because Y".
- Show counterfactual recommendations.
- Show evidence confidence tags and rejection rationale where relevant.
- Show temporal split, calibration curve, confusion matrix, and benchmark sanity table from training metrics.
