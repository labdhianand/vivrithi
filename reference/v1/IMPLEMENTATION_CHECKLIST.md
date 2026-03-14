# Intelli-Credit Copilot Live Implementation Checklist

This checklist is updated live during build-out.

## 1. Foundation
- [x] Repository scaffold created
- [x] Root configs (`README`, `.env.example`, compose, Makefile)
- [x] API service bootstrapped
- [x] Web portal bootstrapped
- [x] End-to-end local run verified

## 2. Data and Evidence Layer
- [x] Case schema and persistence models
- [x] Evidence store (vector + metadata)
- [x] Provenance ledger for every extracted field
- [x] Audit event log service

## 3. OCR + Extraction
- [x] Sarvam integration (default OCR provider)
- [x] LandingAI fallback router
- [x] Parsers for annual report, bank statement, GST, rating report
- [x] Parsers for board minutes, shareholding, CIBIL commercial
- [x] Confidence scoring and extraction quality metrics

## 4. Research Intelligence
- [x] Tavily search connector
- [x] Firecrawl fetch and markdown normalizer
- [x] Deduping, severity tagging, and citations
- [x] Research evidence integration into case graph

## 5. India Reconciliation Signals
- [x] GSTR-2A/2B vs 3B reconciliation algorithm
- [x] GST vs bank turnover mismatch algorithm
- [x] Circular trading / round-tripping heuristics
- [x] Signal threshold policy and scoring output

## 6. ML and Explainability
- [x] Dataset acquisition scripts (IBBI + NSE)
- [x] Synthetic dataset generator removed from mainline repository
- [x] Feature builder pipeline
- [x] Training pipeline (XGBoost + logistic fallback)
- [x] Inference pipeline + SHAP explainability
- [x] Calibration and metrics report artifacts

## 7. Decisioning and Structuring
- [x] Policy hard-stop engine
- [x] Decision overlay (approve/reject/conditional)
- [x] Limit, spread, and covenant recommendation engine
- [x] Counterfactual recommendation output

## 8. CAM and Export
- [x] CAM writer with Green/Amber/Red claims
- [x] Evidence-linked narrative sections
- [x] OpenRouter (`:free` model auto-discovery) for CAM LLM refinement
- [x] DOCX export
- [x] PDF export

## 9. Frontend Workbench
- [x] Case dashboard
- [x] Evidence explorer
- [x] Research console
- [x] Risk workbench (PD, SHAP, policy)
- [x] CAM studio and export controls

## 10. Ops and Governance
- [x] Security and secrets runbook
- [x] Model/data versioning policy
- [x] Human override and approval workflow
- [x] Monitoring and incident playbook

## 11. Validation and Demo
- [x] Seeded demo case
- [x] Full workflow dry run
- [x] Demo walkthrough doc
- [x] Known gaps and next milestones documented

## 12. Audit Remediation (Current Cycle)
- [x] Replace synthetic-feature-first ML training with real-feature extraction from public reports
- [x] Add LangGraph orchestration as default run path
- [x] Add time-aware train/test split
- [x] Add automated Review Agent evidence-coverage gate
- [x] Add calibration curve + confusion matrix artifacts
- [x] Add sanity calibration against rating default studies
- [x] Add SHAP waterfall visualization in frontend
- [x] Add training notebook (`.ipynb`) with reproducible flow
- [x] Complete all circular trading heuristics (6/6)
- [x] Upgrade Databricks integration from sink to compute pipelines
- [x] Add utilization and litigation-linked DSRA covenant triggers
- [x] Add judge demo narrative and Q&A script

## 13. Critical Fixes (Security + Data Integrity)
- [x] Removed proxy/hash observation dates from dataset generation
- [x] Enforced source-date-only temporal split with fail-closed behavior
- [x] Added dataset quality gates for eligible rows and feature diversity
- [x] Added NSE stress-label ingestion and real announcement-date parsing
- [x] Enforced LangGraph-required orchestration path by default
- [x] Added safe SQL literal escaping in Databricks write pipeline
- [x] Added upload filename sanitization and traversal-safe path resolution
- [x] Added regression tests for SQL injection and upload path traversal

## 14. Remediation Wave (Issues 5-18)
- [x] External-service silent fallbacks now return degraded status with explicit warnings and non-green confidence
- [x] Qdrant vectorization replaced with lexical semantic hashing vectors (512-dim) and typed filter query
- [x] Explainability output now distinguishes `tree_shap` from non-SHAP attribution methods
- [x] Review Agent validates rendered CAM coverage and runs post-CAM draft before export routing
- [x] Endpoint authentication enforced for cases, training, and demo routes; override requires separate key
- [x] CORS no longer uses wildcard origins with credentials
- [x] Frontend workbench now includes evidence explorer, audit viewer, override form, file upload, and structured risk/cam views
- [x] CAM renderer upgraded from raw text dump to structured markdown + confidence tags + authenticated download actions
- [x] Exporter upgraded to parse headings/lists/tables/bold for DOCX and formatted PDF output
- [x] Structuring engine fixed for revenue-based limit logic and independent monitoring covenant list
- [x] Circularity score now includes group-alias linkage weight in aggregate score
- [x] Policy engine expanded with financial ratio, downgrade, and litigation checks
- [x] Unit/integration tests expanded across parsers, policy, structuring, exporter, explainability, and auth/CORS
- [x] Foreign key constraints added for documents/evidence/audit records and SQLite FK enforcement enabled
- [x] Heavy service clients moved to app-scoped runtime cache instead of per-request initialization

## 15. Integration Validation (Latest Run: 2026-03-07)
- [x] External key smoke test script added (`scripts/smoke_test_external_services.py`)
- [x] OpenRouter key validated (`/models` + `/chat/completions` using a `:free` model)
- [x] Tavily key validated (`/search`)
- [x] Firecrawl key validated (`/v1/scrape`)
- [x] LandingAI key validated (`/v1/tools/agentic-document-analysis`)
- [x] Sarvam key validated (job init/upload/start/status/download, real PDF OCR)
- [ ] Databricks SQL API test blocked pending `DATABRICKS_HOST` and `DATABRICKS_WAREHOUSE_ID`
- [x] End-to-end simulated-only demo run completed and recorded (`data/demo_run_logs/e2e_demo_run_2026-03-07_simulated.case.json`)
- [x] Blended pack path remains available (`scripts/run_e2e_demo_from_pack.py --mode blended`) for extended runtime demos
