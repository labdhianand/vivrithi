# Judge Q&A Script (Cross-Examination Ready)

## 1) What data did you train on?

Our training labels are from public CIRP admissions (IBBI) as stress-event proxies, and non-default controls from public NSE-listed issuers. Financial features are pulled from public financial statements via symbol-linked data extraction, with explicit missingness tracking and non-label-conditional imputation.

## 2) Did you train on synthetic data?

No. Production training uses only `data/processed/training_dataset.csv` from public-source ingestion and feature extraction pipelines. The synthetic generator was removed from the mainline repository.

## 3) How do you validate model quality?

We run temporal split validation (older observations for train, newer for test), and publish AUC, PR-AUC, Brier score, calibration curve, confusion matrix at policy thresholds, and global feature importance.

## 4) How do you prevent black-box decisions?

Decisioning is three-layered:
1. policy hard-stops,
2. ML PD/risk grade,
3. structuring overlay.

Case-level explainability includes a SHAP-style waterfall, top risk-up and risk-down drivers, contradiction narrative, and counterfactual actions.

## 5) What if OCR is poor?

OCR is confidence-routed: Sarvam primary, LandingAI fallback. Low-confidence evidence is retained and marked Amber/Red; it is never silently dropped.

## 6) How do you handle hallucination risk in CAM?

CAM generation is evidence-bounded. Every claim is tagged Green/Amber/Red and linked to citation metadata. A Review Agent checks coverage before export and blocks export when critical evidence coverage fails.

## 7) What is India-specific in your risk logic?

- GSTR-2A/2B vs 3B ITC over-claim scoring
- GST vs bank turnover mismatch scoring
- Circularity heuristics (6 signals including near-equal T+2 movement, pass-through behavior, and month-end reversals)

## 8) How are covenants tied to risk?

Covenants are directly triggered by risk signals:
- GST mismatch and ITC anomalies -> monthly/quarterly compliance covenants
- utilization concerns -> monthly utilization reporting
- litigation severity -> DSRA and structural protection triggers

## 9) Where does LangGraph fit?

The run path is LangGraph-based with explicit agent nodes, conditional routing, and a manual-review hold path. Review gates can pause final export until manual approval.

## 10) What remains before full production rollout?

- stronger issuer-level annual report extraction coverage for positive labels,
- deployment hardening (SSO/RBAC/KMS),
- full observability and SLA monitoring,
- governed benchmark refresh from latest rating studies.
