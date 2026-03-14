# End-to-End Demo Data Sourcing (Web-Verified)

Date verified: March 5, 2026

## 1) Service keys and env generation sites

Map each env var to where you generate it.

| Env var | Where to get it | Notes |
|---|---|---|
| `OPENROUTER_API_KEY` + optional `OPENROUTER_MODEL` | https://openrouter.ai/keys | Create API key and select a `:free` model (or let the client auto-discover one). |
| `TAVILY_API_KEY` | https://app.tavily.com/ | Create account, then generate API key in Tavily platform. |
| `FIRECRAWL_API_KEY` | https://www.firecrawl.dev/app | Create account and API key from Firecrawl dashboard. |
| `LANDINGAI_API_KEY` | https://va.landing.ai/ | LandingAI API key for OCR fallback (`LANDINGAI_ENDPOINT` already in `.env.example`). |
| `DATABRICKS_HOST` `DATABRICKS_TOKEN` `DATABRICKS_WAREHOUSE_ID` | https://www.databricks.com/learn/free-edition | Free Edition workspace + SQL warehouse credentials. |
| `QDRANT_URL` `QDRANT_API_KEY` | https://cloud.qdrant.io/ | Optional cloud vector DB. Local default `http://localhost:6333` also works. |
| `SARVAM_API_KEY` | https://docs.sarvam.ai/enterprise/api-reference-docs/doc-intelligence/initialise-document-intelligence-job | Primary OCR provider key (base URL defaults to `https://api.sarvam.ai`). |

Operational envs already in project:
- [`.env.example`](/Users/aroraji/vivriti/.env.example)

## 2) Data sources for demo documents

### Public downloadable docs (issuer pack)

Prepared pack in:
- [`data/demo_pack_upl/public_source_docs`](/Users/aroraji/vivriti/data/demo_pack_upl/public_source_docs)

Source URLs used:
- UPL annual report PDF: https://www.upl-ltd.com/financial_result_and_report_pdfs/UPL_Limited_AR_FY2024-25.pdf
- UPL board outcome filing: https://nsearchives.nseindia.com/corporate/UPL_12052025125929_Results.pdf
- UPL credit rating revision filing: https://nsearchives.nseindia.com/corporate/UPL_22052025101509_RevisionincreditratingUPLCorp_1.pdf
- UPL shareholding update filing: https://nsearchives.nseindia.com/corporate/UPL_27032024190806_Updating_of_past_shareholding_patterns.pdf
- UPL AGM outcome filing: https://nsearchives.nseindia.com/corporate/UPL_25072025205652_AGMoutcomeletter.pdf

### Public ML/proxy datasets

- IBBI CIRP announcements: https://ibbi.gov.in/public-announcement
- NSE corporate filings/announcements: https://www.nseindia.com/companies-listing/corporate-filings-announcements

Generated files:
- [`data/raw/ibbi_cirp_labels.csv`](/Users/aroraji/vivriti/data/raw/ibbi_cirp_labels.csv)
- [`data/raw/nse_controls.csv`](/Users/aroraji/vivriti/data/raw/nse_controls.csv)
- [`data/raw/nse_stress_labels.csv`](/Users/aroraji/vivriti/data/raw/nse_stress_labels.csv)

### Confidential docs (not publicly obtainable)

These cannot be legally or practically sourced from open web for a borrower-level case:
- GST returns
- Bank statements
- CIBIL Commercial report
- Bank sanction letter
- DD site-visit note

Project includes simulated equivalents for demo in:
- [`data/demo_pack_upl/confidential_simulated_docs`](/Users/aroraji/vivriti/data/demo_pack_upl/confidential_simulated_docs)

## 3) One-command demo pack generation

Script (already run and committed outputs):
- [`scripts/build_e2e_demo_pack.py`](/Users/aroraji/vivriti/scripts/build_e2e_demo_pack.py)

Run:
```bash
python scripts/build_e2e_demo_pack.py
```

It writes:
- manifest: [`data/demo_pack_upl/manifest.json`](/Users/aroraji/vivriti/data/demo_pack_upl/manifest.json)
- run notes: [`data/demo_pack_upl/README.md`](/Users/aroraji/vivriti/data/demo_pack_upl/README.md)

## 4) End-to-end execution using this pack

Automated uploader + run script:
- [`scripts/run_e2e_demo_from_pack.py`](/Users/aroraji/vivriti/scripts/run_e2e_demo_from_pack.py)

Example:
```bash
python scripts/run_e2e_demo_from_pack.py --mode blended --manual-approval
```

Modes:
- `blended`: public PDFs + simulated confidential docs (recommended for judges)
- `public_only`: only web-sourced docs
- `simulated_only`: deterministic parser-friendly run

## 5) Extra India-context research sources to wire into narrative

- MCA V3 portal: https://www.mca.gov.in/content/mca/global/en/mca/master-data/MDS.html
- eCourts Services: https://services.ecourts.gov.in/ecourtindia_v6/
- RBI circulars/notifications (for regulatory context): https://www.rbi.org.in/

## 6) What else you may need as services

Strongly recommended:
- OCR runtime for PDFs (Sarvam primary; LandingAI fallback key).
- Research APIs (Tavily + Firecrawl) to make secondary-intel live during demo.
- Qdrant (local Docker is fine) for retrieval-backed CAM citations.

Optional:
- Databricks Free Edition sink for audit/scoring tables. Core demo can run without it, but judges may value the pipeline story.
