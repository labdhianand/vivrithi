# Intelli-Credit Hackathon Implementation Checklist

Status: `Execution checklist`
Owner: `Team Intelli-Credit`
Last Updated: `2026-03-15`

## Objective

Build a hosted, analyst-in-the-loop corporate credit underwriting workbench that satisfies the hackathon problem statement end-to-end:

1. Entity onboarding
2. Intelligent multi-format ingestion
3. Automated extraction and schema mapping
4. Secondary research and primary due-diligence integration
5. Explainable recommendation and CAM export

This checklist is implementation-oriented. It is not a feature wish list. Each item should be closed only when it is built, tested, and demoable.

## Build Principles

- [ ] Keep the product generic. Do not hardcode logic to a specific borrower, promoter, or sample dataset.
- [ ] Preserve analyst control at every high-risk step: classification, extraction review, note entry, and decision review.
- [ ] Never guess compulsory fields silently. If extraction fails, mark the field as missing and surface it clearly.
- [ ] Every important output must be traceable to evidence:
  - extracted field -> page or sheet source
  - research claim -> URL and verification status
  - score change -> explanation and supporting evidence
  - CAM section -> cited source evidence
- [ ] Optimize for trust, not just automation. The system should feel like a serious underwriting tool, not a generic chatbot.
- [ ] Keep the public app accessible without VPN while keeping the GPU host private behind WireGuard.

## Phase 0: Hackathon Gap Closure

### Product Alignment

- [ ] Confirm the final product scope exactly matches the four-stage hackathon journey:
  - onboarding
  - ingestion
  - extraction and schema mapping
  - analysis and reporting
- [ ] Confirm the product explicitly supports the five mandatory upload categories:
  - `ALM`
  - `Shareholding_Pattern`
  - `Borrowing_Profile`
  - `Annual_Report`
  - `Portfolio_Performance`
- [ ] Add support for image uploads if the brief or sample data includes scanned images outside PDFs.
- [ ] Enforce a case-level completeness check before final analysis:
  - all required document categories present or explicitly waived
  - compulsory extraction fields reviewed
  - mandatory analyst approvals complete

### Missing Workstreams From the Brief

- [ ] Add the structured-data workstream:
  - GST returns
  - bank statements
  - ITRs
  - optional Databricks ingestion path
- [ ] Define India-specific anomaly checks:
  - GSTR-2A vs GSTR-3B mismatch
  - GST vs bank statement revenue mismatch
  - circular trading indicators
  - rating deterioration
  - legal and litigation red flags
- [ ] Decide which structured-data capabilities are mandatory for demo and which are clearly marked as planned extensions.

## Phase 1: Core Platform Hardening

### Case and Workflow Model

- [ ] Define case lifecycle states clearly:
  - `draft`
  - `uploaded`
  - `processing`
  - `review_pending`
  - `analysis_ready`
  - `report_ready`
- [ ] Ensure the UI ribbon, case status, and backend status model all use the same state machine.
- [ ] Add per-document stage and progress tracking:
  - `queued`
  - `parsing`
  - `classifying`
  - `extracting`
  - `review_pending`
  - `approved`
  - `failed`
- [ ] Persist retry-safe job state so refreshes and reconnects do not lose progress.

### Security and Hosting Basics

- [ ] Move from local-only defaults to a public deployment profile.
- [ ] Add real API authentication for the hosted app.
- [ ] Add file upload size limits and content-type validation.
- [ ] Add persistent storage for uploaded files, extraction artifacts, and reports.
- [ ] Add error monitoring and request tracing for the hosted backend.

## Phase 2: Ingestion Pipeline

### Input Coverage

- [ ] Support these file types explicitly:
  - `pdf`
  - `xlsx`
  - `xls`
  - `csv`
  - `png`
  - `jpg`
  - `jpeg`
- [ ] Validate unsupported or malformed uploads with clean user-facing errors.
- [ ] Tag every file with:
  - original filename
  - mime type
  - upload timestamp
  - inferred document family
  - processing backend used

### Docling GPU Orchestration

- [ ] Route PDFs and spreadsheets through stock Docling.
- [ ] Use the A100 GPU host for high-latency document parsing.
- [ ] Keep the GPU host private and reachable only through WireGuard.
- [ ] Expose only the public frontend and backend without VPN.
- [ ] Use bounded parallel document processing for multi-file uploads.
- [ ] Use aggressive intra-document batching for long PDFs:
  - `page_batch_size`
  - `layout_batch_size`
  - `ocr_batch_size`
  - `table_batch_size`
- [ ] Benchmark and tune concurrency on the live A100 instead of assuming defaults.
- [ ] Capture per-document latency, page count, and pages-per-second telemetry.

### Upload UX

- [ ] Start document processing automatically after upload.
- [ ] Show real progress bars with:
  - current stage
  - processed pages
  - total pages
  - failure state if any
- [ ] Hide approval controls until processing is finished.
- [ ] Move documents ready for approval to the top automatically.
- [ ] Show a clear “missing required document types” panel in the upload/classify flow.

## Phase 3: Document Classification

### Classification Engine

- [ ] Use Gemini as the only text LLM provider for document classification.
- [ ] Use parsed content, filename, page signals, and table signals as model input.
- [ ] Normalize and validate LLM output before accepting it.
- [ ] Add fallback behavior that is controlled and transparent:
  - if Gemini fails, classify as `needs_review`
  - do not silently auto-assign a high-confidence category
- [ ] Add explicit confidence bands:
  - `high`
  - `medium`
  - `low`
  - `needs_review`

### Human-in-the-Loop Controls

- [ ] Allow the analyst to approve, edit, or reject the assigned category.
- [ ] Record whether the final category was:
  - auto-approved
  - analyst-corrected
  - analyst-rejected
- [ ] Use analyst corrections as feedback data for future classifier improvement.

### Acceptance Criteria

- [ ] The five hackathon document categories classify correctly on the sample corpus with analyst approval available.
- [ ] Generic filenames do not break classification.
- [ ] Misclassified files are visibly recoverable in the UI.

## Phase 4: Dynamic Schema Mapping

### Schema System

- [ ] Keep the five hackathon categories as first-class defaults, but do not hardcode the product to only those categories.
- [ ] Support case-level editable schemas per category.
- [ ] Allow the user to add, remove, relabel, and mark fields as required.
- [ ] Store extraction hints per field:
  - row aliases
  - column header aliases
  - section aliases
  - preferred units
  - summary or total preference
  - current-period column preference
- [ ] Support schema versioning so reruns are reproducible.

### Schema UX

- [ ] Show the current extracted value beside each schema field.
- [ ] Show required vs optional clearly.
- [ ] Show confidence, extraction method, and source page or sheet for each field.
- [ ] Show missing compulsory fields prominently.
- [ ] Allow re-run extraction after schema edits.

### Acceptance Criteria

- [ ] A user can change the schema for a case and rerun extraction against the new schema.
- [ ] The mapper works on both PDF-derived tables and spreadsheet-native tables.
- [ ] Schema changes affect future extraction runs without corrupting prior versions.

## Phase 5: Extraction Engine

### Generic Table Normalization

- [ ] Normalize every parsed table into a common structure:
  - row label
  - column header
  - section header
  - value
  - unit
  - page or sheet
  - bounding box or cell reference
  - row type: detail, subtotal, total
- [ ] Build a generic schema-aware mapper on top of the normalized table model.
- [ ] Use row semantics plus column header plus section context to identify the best field match.
- [ ] Do not rely on row count or fixed row positions.
- [ ] Handle tables with inserted rows, reordered rows, or extra detail rows.

### Required-Field Behavior

- [ ] If a compulsory field is not extractable with confidence, mark it as `missing_required`.
- [ ] Do not backfill missing compulsory fields with guessed values.
- [ ] Surface missing compulsory fields in:
  - extraction page
  - schema page
  - analysis summary
  - CAM exceptions or missing-data section

### Evidence and Review

- [ ] Preserve PDF page bounding boxes for extracted values.
- [ ] Preserve spreadsheet evidence as:
  - sheet name
  - row label
  - column header
  - raw cell value
- [ ] Allow the analyst to inspect evidence and edit extracted values.
- [ ] Record analyst overrides separately from model output.

### Category-Specific Coverage

- [ ] Harden `ALM` extraction.
- [ ] Harden `Shareholding_Pattern` extraction.
- [ ] Harden `Borrowing_Profile` extraction.
- [ ] Harden `Portfolio_Performance` extraction.
- [ ] Harden `Annual_Report` extraction for key facts, risks, and financial highlights.

### Acceptance Criteria

- [ ] The extractor works on messy financial tables without relying on one sample document layout.
- [ ] Missing or weak fields are clearly surfaced.
- [ ] Every extracted value shown in analysis or CAM can be traced back to source evidence.

## Phase 6: Structured Data Synthesis

### Source Adapters

- [ ] Add ingestion for:
  - GST returns
  - bank statements
  - ITRs
  - optional Databricks source tables
- [ ] Define normalized schemas for each structured source.
- [ ] Support manual upload and optional warehouse ingestion.

### Credit-Specific Cross Checks

- [ ] Build GST vs bank statement reconciliation.
- [ ] Build sales trend comparison across GST, statements, and uploaded financials.
- [ ] Build circular trading heuristics:
  - repeated round-number inflows
  - same-day inward and outward patterns
  - concentrated counterparty loops
- [ ] Build mismatch flags for:
  - declared turnover vs bank flows
  - rating narrative vs debt profile
  - shareholding disclosures vs extracted shareholding tables

### Acceptance Criteria

- [ ] The platform can explain why a structured-data anomaly was flagged.
- [ ] Structured findings appear in Five Cs and CAM with source references.

## Phase 7: Research Agent

### Retrieval Strategy

- [ ] Use Tavily for targeted search discovery.
- [ ] Use Firecrawl to fetch and clean relevant pages.
- [ ] Organize research around entity scopes:
  - borrower
  - promoter
  - group company
  - sector
  - subsector
  - macro
  - regulatory
  - litigation
- [ ] Build query plans from live case context, not hardcoded company names.
- [ ] Use extracted facts to enrich search:
  - company name
  - CIN
  - PAN if appropriate and safe
  - NSE or BSE symbol
  - promoter names
  - sector
  - subsector
  - rating agency mentions

### Verification and Relevance

- [ ] Add entity verification to every research item:
  - `verified`
  - `probable`
  - `contextual`
  - `rejected`
- [ ] Store match explanation, matched terms, and entity match score.
- [ ] Do not let generic official pages become borrower-specific adverse findings.
- [ ] Distinguish:
  - borrower-specific risk
  - promoter-specific risk
  - sector headwind
  - macro context
  - generic background noise

### Research UX

- [ ] Show research grouped by scope and verification state.
- [ ] Show why an item matters.
- [ ] Allow the analyst to discard irrelevant research items.
- [ ] Show contradictions and corroborations against uploaded documents.

### Acceptance Criteria

- [ ] Research findings are relevant, local, and credit-useful.
- [ ] Generic legal or regulatory pages do not falsely penalize the borrower.
- [ ] The system can explain exactly why a research item affects `Character`, `Conditions`, or neither.

## Phase 8: Primary Due-Diligence Integration

### Note Capture

- [ ] Provide a dedicated portal for analyst notes:
  - site visit observations
  - management commentary
  - channel checks
  - collateral observations
- [ ] Support note metadata:
  - author
  - timestamp
  - note type
  - affected Five C
  - confidence

### Note Interpretation

- [ ] Interpret notes into structured signals, not just free text:
  - capacity utilization concern
  - governance concern
  - management comfort
  - collateral concern
  - operational weakness
  - fraud or diversion suspicion
- [ ] Show how note-derived signals changed the score.
- [ ] Preserve manual override capability for the analyst.

### Acceptance Criteria

- [ ] A note like “Factory operating at 40% capacity” visibly affects `Capacity`.
- [ ] The analysis summary shows which note changed the score and why.

## Phase 9: Triangulation and Reasoning Engine

### Evidence Fusion

- [ ] Build a contradiction and corroboration layer across:
  - extracted documents
  - structured data
  - research findings
  - analyst notes
- [ ] Label each major signal as:
  - corroborated
  - contradicted
  - contextual
  - unverified
  - missing evidence
- [ ] Ensure borrower-specific evidence is separated from sector or macro context.

### Explainable Scoring

- [ ] Keep the Five Cs scoring model explicit and inspectable.
- [ ] Show the input drivers for:
  - `Character`
  - `Capacity`
  - `Capital`
  - `Collateral`
  - `Conditions`
- [ ] Show positive drivers, negative drivers, and missing data penalties.
- [ ] Ensure only verified borrower-relevant findings drive hard-stop logic.

### Recommendation Logic

- [ ] Generate a recommendation with:
  - approve or reject or conditional approve
  - recommended amount
  - suggested risk premium
  - key covenants or mitigants
- [ ] Explain:
  - why the borrower was approved or rejected
  - what capped the amount
  - what increased pricing
  - what evidence was decisive
- [ ] Add scenario logic:
  - what would need to improve for the case to move from reject to conditional approve

### Acceptance Criteria

- [ ] A judge can walk from the final recommendation back to source evidence without ambiguity.
- [ ] The recommendation is transparent and not visibly black-box.

## Phase 10: SWOT and CAM Generation

### SWOT

- [ ] Generate SWOT from verified evidence only.
- [ ] Separate internal facts from external context.
- [ ] Avoid generic or unsupported bullet points.

### CAM Structure

- [ ] Produce a professional CAM in both DOCX and PDF.
- [ ] Cover at least:
  - executive summary
  - borrower overview
  - facility request
  - document summary
  - extracted financial highlights
  - structured-data findings
  - secondary research
  - due-diligence notes
  - Five Cs
  - SWOT
  - final recommendation
  - key risks and mitigants
  - missing data or review exceptions
- [ ] Use a formal memo style with clean typography and section hierarchy.
- [ ] Include citations or evidence references throughout.

### Report UX

- [ ] Show a readable in-app report preview.
- [ ] Allow download of PDF and DOCX.
- [ ] Ensure the export matches the preview closely enough for demo confidence.

### Acceptance Criteria

- [ ] The CAM looks credit-committee-ready, not like a raw markdown dump.
- [ ] The report is explainable, visually polished, and easy to defend live.

## Phase 11: Public Deployment and GPU Networking

### Deployment Topology

- [ ] Host the frontend publicly over HTTPS.
- [ ] Host the backend publicly over HTTPS.
- [ ] Keep the GPU host private behind WireGuard.
- [ ] Allow the backend to reach the GPU host over WireGuard only.
- [ ] Keep secrets out of the frontend and out of Git.

### Operational Readiness

- [ ] Add health checks for:
  - frontend
  - backend
  - database
  - Tavily
  - Firecrawl
  - Gemini
  - remote Docling connectivity
- [ ] Add simple admin visibility for failed document jobs and report generation failures.
- [ ] Add retry flow for failed research or parsing jobs.

### Acceptance Criteria

- [ ] The full app is demoable from an external network without VPN.
- [ ] GPU parsing still works through the backend-private network path.

## Phase 12: Testing and Validation

### Functional Testing

- [ ] Test the full pipeline on the provided five-document sample set.
- [ ] Test with at least one second borrower corpus, if available.
- [ ] Test a case with missing documents.
- [ ] Test a case with weak OCR or scanned pages.
- [ ] Test a case with spreadsheets instead of PDF tables.

### Quality Testing

- [ ] Validate classification accuracy on the sample set.
- [ ] Validate extraction on required fields for each category.
- [ ] Validate research precision:
  - borrower-specific
  - promoter-specific
  - sector-specific
  - legal and litigation
- [ ] Validate score explainability against expected reasoning.
- [ ] Validate CAM formatting on both macOS and Windows viewers.

### Performance Testing

- [ ] Measure full case turnaround time.
- [ ] Measure per-document throughput on the A100.
- [ ] Measure large annual report processing time.
- [ ] Confirm the UI stays responsive during background jobs.

## Final Demo Checklist

- [ ] Hosted public URL works without VPN.
- [ ] Onboarding form is stable and fast.
- [ ] Required document upload flow is clear.
- [ ] Processing starts automatically and shows honest progress.
- [ ] Classification can be reviewed and corrected.
- [ ] Extraction page shows evidence and bounding boxes or cell references.
- [ ] Schema page shows required fields and current extracted values.
- [ ] Research page shows verified, relevant external intelligence.
- [ ] Analyst note entry visibly affects analysis.
- [ ] Five Cs explanation is understandable in under two minutes.
- [ ] CAM preview is polished.
- [ ] PDF and DOCX export both open cleanly.
- [ ] One strong end-to-end demo case is rehearsed.
- [ ] One backup demo case is ready.
- [ ] A short failure-handling story is ready for judges:
  - what happens if extraction misses a field
  - what happens if research is ambiguous
  - why analyst oversight is preserved

## Build Order Recommendation

Close work in this order:

- [ ] 1. Core reliability: status model, upload flow, progress, retries
- [ ] 2. Extraction correctness: schema-aware mapper, missing required fields, evidence
- [ ] 3. Research quality: verified entity matching, Tavily plus Firecrawl, relevance control
- [ ] 4. Triangulation: contradictions, corroborations, source fusion
- [ ] 5. Recommendation quality: Five Cs hardening, explainable limits and pricing
- [ ] 6. CAM quality: polished memo export and preview
- [ ] 7. Structured data: GST, bank statement, ITR, Databricks path
- [ ] 8. Public deployment and operational hardening

## Definition of Done

This project is demo-ready only when all of the following are true:

- [ ] A public user can complete the full flow without VPN.
- [ ] The five required document types can be uploaded, processed, reviewed, and used in analysis.
- [ ] Extraction is accurate enough that required fields are mostly correct and missing fields are surfaced honestly.
- [ ] Research is relevant and verified enough that it improves, rather than pollutes, underwriting.
- [ ] Analyst notes visibly affect the recommendation.
- [ ] The recommendation is explainable and evidence-backed.
- [ ] The final CAM is polished, downloadable, and defensible in front of judges.
