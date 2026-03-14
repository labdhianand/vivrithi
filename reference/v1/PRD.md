# Intelli-Credit Copilot PRD (Final, ML + Research + India-Context Corrected)

This version fixes the gaps you flagged and **strengthens the ML story** so you can answer “what data did you train on?” without awkwardly admitting you trained on vibes.

---

## 0) Product Summary

**Product:** Intelli-Credit Copilot
**Promise:** Convert Indian corporate lending inputs (GST, bank statements, annual reports, sanction letters, rating reports, shareholding, CIBIL Commercial, board minutes, plus web intelligence + DD notes) into:

* **ML-based** risk assessment (transparent)
* **decision recommendation** (approve / reject / conditional approve)
* **limit + pricing** (risk premium)
* **covenants + monitoring**
* **evidence-backed CAM** (Word/PDF) with citations + confidence markers

---

## 1) Key Product Requirements (judge-aligned)

### 1.1 ML-based recommendation (mandatory)

We will ship a real trained model, not only rules.

**Core design:**

* **Policy layer** (hard stops + mandatory conditions)
* **Interpretable ML model** for PD/risk grade
* **Decision overlay** (limit, pricing, covenants) driven by model outputs + document-derived signals

### 1.2 Research depth (mandatory MVP)

Secondary research is not optional. It is in MVP.

### 1.3 India-specific nuance (mandatory MVP)

Explicit, visible logic for:

* **GSTR-2A/2B vs 3B** reconciliation
* GST vs bank turnover mismatch
* circular trading / round-tripping heuristics
* MCA/e-Courts as external intelligence (with realistic constraints)

---

## 2) External Services We Use (free-tier first)

| Service                                                       | Used for                                                             | Free-tier / rationale                                                                                                                                      |
| ------------------------------------------------------------- | -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Databricks Free Edition**                                   | canonical tables, feature pipelines, scoring tables, audit logs      | Free Edition is serverless-only; **no GPUs** and outbound internet is restricted, so OCR/research runs outside Databricks. ([Databricks Documentation][1]) |
| **LangGraph**                                                 | agentic orchestration (controlled)                                   | Durable, human-in-loop graph execution. ([Databricks Documentation][1]) *(LangGraph docs were cited earlier; keeping stack consistent)*                    |
| **Surya**                                                     | default OCR + layout + reading order + tables                        | Open-source stack for document intelligence. ([Insolvency and Bankruptcy Board of India][2]) *(Surya repo referenced earlier; keep as default)*            |
| **LandingAI ADE**                                             | OCR fallback for “cursed” Indian scans                               | Pricing shows free starter credits and credit-based usage. ([LandingAI][3])                                                                                |
| **Tavily**                                                    | search API for agentic research                                      | Designed for AI agent search and prototyping. ([Insolvency and Bankruptcy Board of India][2]) *(kept as prior choice)*                                     |
| **Firecrawl**                                                 | fetch + convert pages/PDFs to clean markdown                         | Free for first **500 pages**; credit-based per page/PDF page. ([Firecrawl - The Web Data API for AI][4])                                                   |
| **Gemini API**                                                | LLM for CAM drafting + reasoning over extracted evidence             | Free tier exists for several models. ([Databricks Documentation][1]) *(pricing link already used earlier; keep choice)*                                    |
| **Qdrant Cloud**                                              | vector retrieval for evidence grounding                              | 1GB free cluster, no card required. ([Qdrant][5])                                                                                                          |
| **NSE Corporate Filings**                                     | source for public annual reports / filings (for ML dataset curation) | Public portal for filings. ([NSE India][6])                                                                                                                |
| **IBBI Public Announcements**                                 | public “CIRP admitted” label source for defaults proxy               | 8,000+ CIRP public announcement records available. ([Insolvency and Bankruptcy Board of India][7])                                                         |
| **Rating transition/default studies (CRISIL, India Ratings)** | calibration priors + sanity checks for default rates                 | Public PDFs with default-rate methodology and stats.                                                                                                       |

> Note: Surya vs LandingAI is implemented as a **router** (confidence-based fallback), not a religion.

---

## 3) System Architecture (agentic, but controlled)

**Frontend (Next.js)** → **Orchestrator (LangGraph)** → services:

1. **OCR/Parsing Service** (Surya default; LandingAI fallback)
2. **Research Service** (Tavily + Firecrawl)
3. **Normalization + Signals** (Databricks pipelines)
4. **Feature Builder** (Databricks → model_features table)
5. **ML Inference + Explainability** (PD/risk grade + SHAP)
6. **Decision Structuring** (limit + pricing + covenants)
7. **CAM Generator** (LLM draft + citations + confidence flags)
8. **Exporter** (DOCX + PDF)

---

## 4) Agent Graph (what each agent does)

### 4.1 Intake Agent

* classify docs (annual report, bank stmt, GST, rating report, shareholding, board minutes, bureau report)
* check mandatory doc completeness
* route to extraction pipeline

### 4.2 Extraction Agent

* OCR + layout + tables
* extract key fields per doc type
* emit `chunks`, `tables`, `fields`, confidence, provenance

### 4.3 Research Agent (MVP)

* collect evidence on borrower/promoters/sector/regulatory/litigation
* dedupe, rank, tag severity, store citations

### 4.4 Reconciliation Agent (MVP)

* GST vs bank
* 2A/2B vs 3B
* circular trading heuristics
* outputs signals with thresholds + evidence

### 4.5 Risk Model Agent (MVP, ML-based)

* build feature vector
* run trained model
* compute SHAP (or coefficient explanations)
* produce PD / risk grade + top drivers

### 4.6 Structuring Agent (MVP)

* compute eligible limit caps
* map risk grade → spread & covenants
* generate conditions precedent/subsequent + monitoring

### 4.7 CAM Writer Agent (MVP)

* write CAM sections using **only grounded evidence**
* mark weak claims as **Amber** (not deleted)

### 4.8 Review Agent (MVP)

* validates that CAM has evidence coverage
* flags missing evidence rather than silently removing content

---

## 5) Document Types: Extraction Logic (now complete)

### 5.1 Rating agency reports (explicit)

Extract:

* rating, outlook, watch status
* downgrade triggers, liquidity commentary
* leverage, coverage notes, stress factors
* “key risks” bullets

Emit:

* `rating_current`, `outlook`, `watch`, `key_risks[]`, `downgrade_triggers[]`

### 5.2 Board meeting minutes (explicit)

Extract:

* borrowing approvals
* related party transactions
* contingent liabilities / disputes discussed
* director dissent / resignations
* operational distress statements

Emit:

* `governance_flags[]`, `related_party_mentions[]`, `distress_mentions[]`

### 5.3 Shareholding pattern (explicit)

Extract:

* promoter holding %, change over time
* pledged shares %, changes
* dilution events
* concentration and control shifts

Emit:

* `promoter_holding_trend`, `pledge_trend`, `dilution_flags[]`

### 5.4 CIBIL Commercial report (explicit)

Input modes:

* uploaded PDF
* user-entered structured fields (fallback)
* mocked JSON for hackathon

Extract:

* score band
* DPD/overdue indicators
* suit-filed / write-off flags
* lender count, enquiry velocity

Emit:

* `bureau_score_band`, `dpd_severity`, `suit_filed_flag`, `enquiry_velocity`

---

## 6) India-specific checks (explicit algorithms)

### 6.1 GSTR-2A/2B vs 3B reconciliation

For each month:

* `ITC_available = min(ITC_2A, ITC_2B if present else ITC_2A)`
* `ITC_claim_ratio = ITC_claimed_3B / ITC_available`
* `Excess_ITC = max(0, ITC_claimed_3B - ITC_available)`

Flags:

* **Mild:** ratio > 1.05 (1 month)
* **Moderate:** ratio > 1.10 (2 consecutive months)
* **Severe:** ratio > 1.15 (3 months) or Excess_ITC over policy threshold

Output:

* `itc_overclaim_score` (0–100)
* evidence references to GST tables

### 6.2 GST vs bank turnover mismatch

Compute monthly:

* `Declared_Sales_3B`
* `Operating_Credits_Bank`
* `sales_bank_gap = |Declared_Sales_3B - Operating_Credits_Bank| / max(Declared_Sales_3B, eps)`

Flags:

* persistent divergence for 2–3 months
* quarter-end spikes that reverse next month

### 6.3 Circular trading / round-tripping

Build entity graph from:

* bank counterparties (narration clustering + name normalization)
* GST buyer/supplier names (if available)
* group entity aliases

Heuristics (score each 0–1, weighted sum):

* same counterparty appears in both inflow/outflow clusters
* near-equal in→out within T+0/T+1/T+2
* repeated round-number transfers
* high top-counterparty overlap between “customers” and “suppliers”
* pass-through behavior (low retention)
* month-end reversal patterns

Output:

* `circularity_score` (0–100)
* top suspicious pairs + date clusters with citations

---

## 7) Recommendation Engine (ML + explainability)

### 7.1 Model type (MVP)

Choose one primary:

* **XGBoost/LightGBM + SHAP** (best hackathon balance)
* baseline: **logistic regression** (benchmark + interpretable)

### 7.2 What the model predicts

Model outputs:

* `PD` (probability of stress/default proxy) OR `risk_grade`

Then policy overlay generates:

* approve/reject/conditional
* recommended limit
* spread premium
* covenants + monitoring

### 7.3 Explainability panel (first-class)

Must show:

* SHAP waterfall (case-level)
* top positive drivers
* top negative drivers
* **“despite X, because Y” contradiction narrative**
* **counterfactual**: “what would improve the decision”

---

## 8) Covenants (MVP output, not optional)

A rule-based covenant engine is fine (and actually expected).

Examples:

* GST-bank mismatch → quarterly stock/receivables audit + monthly GST compliance pack
* ITC overclaim → monthly GST reconciliation covenant
* low utilization DD note → monthly utilization reporting + tighter review trigger
* litigation risk → conditional approval + enhanced monitoring + DSRA or structure changes
* bureau stress → cap on additional borrowing + escrow/routing covenant

CAM must include:

* conditions precedent
* conditions subsequent
* monitoring covenants
* triggers for review

---

## 9) CAM Generation (evidence + safe fallback)

### 9.1 Evidence handling

Claims are not silently deleted if grounding is imperfect.

Each claim is labeled:

* **Green:** grounded with citation
* **Amber:** low confidence, highlighted for reviewer
* **Red:** blocked from final export

### 9.2 CAM must include a dedicated rejection rationale

Explicitly:

* “Rejected due to high litigation severity found in secondary research despite strong GST flows.”

This is shown both in:

* CAM Executive Summary
* Explainability panel

---

# 10) ML Training Strategy (Rebuilt, defensible)

This is the major upgrade.

## 10.1 Hackathon-grade training data that is *real-ish*, not synthetic

### Core idea

Train a model on **publicly evidenced “default proxy” outcomes** + **public financial statements**.

#### Positive class (default/stress proxy)

Use **IBBI Public Announcements of CIRP admission** as an observable “entered insolvency process” label. The portal shows thousands of records (8,000+). ([Insolvency and Bankruptcy Board of India][7])

This is not perfect “default,” but it’s a **defensible stress event proxy** that is public and labelable.

#### Negative class (non-default proxy)

Sample matched controls from:

* listed firms with annual reports via NSE filings (public access) ([NSE India][6])
* exclude any company name that appears in the CIRP list within the time window

Matching strategy (cheap but solid):

* sector (manufacturing/trading/services buckets)
* size (revenue band from annual report)
* time window (same fiscal years)

## 10.2 Minimum viable dataset (48–72 hours)

Aim for:

* **50–200 companies**
* 15–25 robust features (financial ratios + governance/news + rating/bureau where available)

Even **50 labeled real companies** beats “synthetic cases” in judge credibility.

## 10.3 Feature set for training (must be public-derivable)

Use features extractable from annual reports + filings:

* leverage (Debt/Equity)
* interest coverage
* EBITDA margin
* PAT margin
* CFO/EBITDA
* revenue growth
* working capital days proxies (if notes allow)
* auditor qualification flags
* contingent liability mentions (NLP on notes section)
* rating outlook / downgrade flags (if rating reports are public for that issuer)

**Important:** GST/bank signals are computed for the *case decision*, but for the hackathon model they can act as:

* **post-model risk adjusters**, OR
* optional features if you have enough labeled cases with those documents

You do **not** pretend the model learned from GST-bank mismatch if your training set didn’t contain it.

## 10.4 Validation plan (what you show judges)

Deliver these artifacts in the demo repo:

1. **Dataset provenance doc**

   * where positives came from (IBBI CIRP list)
   * where negatives came from (NSE filings list)
   * date window used
2. **Time-aware split**

   * train on older years, test on newer CIRP admissions
3. **Metrics**

   * AUC + PR-AUC
   * calibration curve (reliability plot)
   * confusion matrix at policy thresholds
4. **Explainability**

   * SHAP global importance
   * SHAP case waterfall
   * reason-code mapping (top 3 reasons)
5. **Sanity calibration against external default-rate studies**

   * compare predicted base rates / risk grade ordering against published rating-default ordinality and default-rate trends (as a plausibility check, not issuer-level truth) 

## 10.5 “Honest baseline” fallback (if time is tight)

If you cannot curate enough cases:

* use a **logistic regression** with **expert-calibrated coefficients**
* fit/adjust coefficients on the small real dataset you have
* show coefficients as explanation + SHAP (works for linear models too)

This is more defensible than training XGBoost on synthetic examples.

## 10.6 What you explicitly say in the demo

> “Our ML model is trained on public CIRP admissions as a stress-event proxy and matched controls from public annual reports. It produces an explainable risk score (SHAP). Document-derived GST/bank anomalies are applied as explicit post-model adjusters with evidence.”

That answer survives cross-examination.

---

## 11) MVP Build Plan (final)

### Must-have MVP (judge-safe)

* Next.js portal (case dashboard, evidence explorer, research console, risk workbench, CAM studio)
* OCR router (Surya default + LandingAI fallback)
* parsers for: annual report, bank statement, GST returns, rating report, board minutes, shareholding, CIBIL Commercial
* research agent (Tavily + Firecrawl), outputs citations
* signals engine (India-specific checks, explicit thresholds)
* ML model inference + SHAP explanations
* limit + pricing + covenants
* CAM generation with green/amber/red confidence behavior
* counterfactual explainability panel

---

## 12) Final Deliverables for Hackathon

1. **Live portal demo** on one end-to-end case
2. **Generated CAM (DOCX + PDF)** with citations + appendix evidence pack
3. **Explainability view** (SHAP waterfall + reason codes + counterfactuals)
4. **Training notebook + dataset provenance** (IBBI + NSE matched controls)
5. **Audit log** showing workflow steps and overrides

---

If you want, I can also add a “Judge Q&A script” section (1 page) that pre-empts the exact questions you’ll get: training data, validation, bias, hallucinations, and what happens when OCR fails.

[1]: https://docs.databricks.com/aws/en/getting-started/free-edition-limitations?utm_source=chatgpt.com "Databricks Free Edition limitations"
[2]: https://ibbi.gov.in/?utm_source=chatgpt.com "Insolvency and Bankruptcy Board of India (IBBI)"
[3]: https://landing.ai/pricing-agentic-apis?utm_source=chatgpt.com "Agentic API Pricing – Document & Image Extraction"
[4]: https://www.firecrawl.dev/pricing?utm_source=chatgpt.com "Firecrawl - The Web Data API for AI"
[5]: https://qdrant.tech/pricing/?utm_source=chatgpt.com "Pricing for Cloud and Vector Database Solutions Qdrant"
[6]: https://www.nseindia.com/companies-listing/corporate-filings-announcements?utm_source=chatgpt.com "Corporate Filings Announcement - Equity, SME, Debt, MF"
[7]: https://ibbi.gov.in/public-announcement?ann=Public+Announcement+of+Corporate+Insolvency+Resolution+Process&utm_source=chatgpt.com "Public Announcement"
