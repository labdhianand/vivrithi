# ML Data and Provenance

## Label strategy

- Positive label proxy: CIRP admission records from IBBI public announcements.
- Additional positive proxy: NSE announcements tagged with CIRP/default stress disclosures (`nse_stress_labels.csv`).
- Negative controls: NSE issuer universe (corporate announcements + NIFTY500 fallback controls).

## Feature strategy

- Financial ratio features are pulled from public financial statements (Yahoo Finance public API) for symbol-resolved entities.
- Missing financial fields are imputed using global (non-label-conditional) medians.
- Class-conditional synthetic feature generation is explicitly prohibited in the main pipeline.

## Data flow

1. `scripts/fetch_ibbi_data.py` -> `data/raw/ibbi_cirp_labels.csv`
2. `scripts/fetch_nse_filings.py` -> `data/raw/nse_controls.csv` + `data/raw/nse_stress_labels.csv`
3. `scripts/build_training_dataset.py` -> `data/processed/training_dataset.csv`
4. `app/services/ml/train.py` -> `data/checkpoints/risk_model.joblib`

## Temporal validation

- Train/test split is time-aware using `observation_date`.
- Only source-supplied parseable dates are accepted; missing dates are marked ineligible (no proxy/hash date fallback).
- Split metadata stored in `risk_model.metrics.json` under `split`.

## Validation artifacts

- Core metrics: AUC, PR-AUC, Brier.
- Calibration curve data and plot.
- Confusion matrices at policy thresholds.
- Global feature importance (data + plot).
- Rating-benchmark sanity comparison against `data/raw/rating_default_priors.csv`.

## Caveats

- Public-financial coverage differs by issuer and ticker availability; rows with weak coverage are tracked via `eligible_for_model` and `ineligibility_reason`.
- GST/bank/circular signals remain case-time features in underwriting and are not relied on as primary training features unless directly observed in training sources.
