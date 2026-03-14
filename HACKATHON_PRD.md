# Intelli-Credit Hackathon PRD

Version: `v1.0`
Status: `Draft for build execution`
Owner: `Team Intelli-Credit`
Last Updated: `2026-03-14`

## 1. Executive Summary

### Product Name
`Intelli-Credit Copilot`

### One-Line Pitch
An explainable, hosted AI credit underwriting workbench for Indian corporate lending that converts uploaded financial documents, external intelligence, and analyst due diligence into a defensible Credit Appraisal Memo (`CAM`) with recommendation, limit, pricing, and reasoning.

### Hackathon Goal
Build a web application, accessible without a VPN, that guides a credit analyst from raw entity onboarding and document upload to a final downloadable assessment report with:

- multi-format ingestion
- analyst-in-the-loop classification and extraction
- secondary research and risk triangulation
- explainable recommendation on whether to lend, how much to lend, and at what risk premium

### Why This Product
Indian corporate credit appraisal currently suffers from a data paradox: there is abundant data, but loan assessment remains slow, manual, fragmented, and inconsistent. Analysts must combine structured filings, messy PDFs, external research, and qualitative field observations. Important early warning signals are often buried across sources and missed.

This product compresses that workflow into a single operating system for credit managers.

## 2. Problem Statement

Credit managers evaluating mid-sized Indian corporates must piece together:

- structured financial data such as GST returns, ITRs, and bank statements
- unstructured financial and legal documents such as annual reports, rating reports, sanction letters, board minutes, and shareholding patterns
- external intelligence such as sector news, MCA filings, regulatory changes, and litigation
- primary due diligence such as site visit notes or management interview observations

The current process is:

- slow, often taking days or weeks
- high latency and labor intensive
- difficult to audit
- vulnerable to human bias
- weak at identifying subtle contradictions or emerging risk signals

The hackathon requires a hosted application that automates the end-to-end preparation of a comprehensive credit appraisal while preserving explainability and analyst control.

## 3. Product Vision

Create a digital credit manager that:

- ingests messy enterprise credit data reliably
- extracts facts into structured schemas with provenance
- performs targeted secondary research on the borrower, promoters, sector, and regulatory environment
- incorporates analyst due diligence inputs rather than replacing them
- produces a transparent lending recommendation and professional CAM

The product must feel like a serious underwriting tool, not a generic document chatbot.

## 4. Product Goals

### Primary Goals

- Reduce time from raw documents to first-pass appraisal from days to minutes.
- Improve extraction quality for Indian financial tables and scanned PDFs.
- Surface early warning signals across internal and external sources.
- Keep a human reviewer in control for classification, extraction corrections, and qualitative overlays.
- Generate an explainable recommendation with evidence trails and citations.
- Deliver a stable hosted web application for the final hackathon demo.

### Secondary Goals

- Create reusable case records and schemas for future borrowers.
- Support auditor-style traceability from final recommendation back to raw evidence.
- Make the system adaptable to NBFC, HFC, and mid-market corporate credit cases.

### Non-Goals for Hackathon MVP

- Fully automated straight-through approval without analyst review.
- Production-grade integrations with every Indian data source.
- Real disbursement, LOS, LMS, or core banking connectivity.
- Perfect OCR on every document type under every scan condition.
- Full legal opinion or collateral valuation workflows.

## 5. Users and Personas

### Primary User
`Credit Analyst / Credit Manager`

Responsibilities:

- onboard a borrowing entity
- upload and validate financial documents
- review auto-classification and extraction
- enter site visit and management notes
- review research signals and final recommendation
- download and present the CAM

Pain points:

- document sprawl
- repeated manual data extraction
- lack of cross-document consistency checks
- poor visibility into hidden risks
- time pressure to prepare credit notes quickly

### Secondary User
`Credit Approver / Risk Committee Reviewer`

Responsibilities:

- consume the CAM
- understand why the tool recommended approval or rejection
- inspect evidence and risk drivers

Needs:

- clear reasoning
- concise risk summary
- confidence markers
- traceability to sources

### Tertiary User
`Relationship Manager / Underwriting Ops`

Responsibilities:

- upload case documents
- complete onboarding data
- coordinate missing documents

Needs:

- simple workflow
- clear missing-data prompts
- minimal training burden

## 6. Hackathon Alignment

This PRD directly maps to the hackathon brief.

### Three Required Pillars

#### 1. Data Ingestor

- ingest structured and unstructured files
- parse PDFs, images, and spreadsheets
- classify required document types
- extract key commitments, exposures, financial tables, and risk indicators
- support high-latency processing for heavy documents

#### 2. Research Agent

- crawl news and public web sources
- detect promoter, sector, litigation, and regulatory signals
- incorporate analyst-entered primary due diligence notes
- triangulate external research with internal documents

#### 3. Recommendation Engine

- generate a professional CAM
- score borrower risk with transparent logic
- recommend approve, reject, or conditional approve
- suggest limit, interest premium, and key covenants

### Required Hosted User Journey

The app must support the four required stages:

1. Entity Onboarding
2. Intelligent Data Ingestion
3. Automated Extraction and Schema Mapping
4. Pre-Cognitive Secondary Analysis and Reporting

## 7. Success Criteria

### Judge-Facing Success Criteria

#### Operational Excellence

- hosted application works without VPN
- uploads, forms, extraction jobs, and report downloads work reliably
- app state is recoverable if a step is refreshed

#### Extraction Accuracy

- correctly classifies the five mandatory document types
- handles non-standard tables and scanned Indian financial PDFs
- allows users to correct extracted values instead of failing silently

#### Analytical Depth

- surfaces relevant secondary research beyond uploaded documents
- identifies contradictions and risk markers across sources
- captures India-specific credit signals rather than generic text summaries

#### Explainability

- recommendation is not a black box
- each score and final decision has evidence-backed reasons
- CAM can walk a judge through the logic clearly

#### Indian Context Sensitivity

- understands GST reconciliations and related anomalies
- supports Indian corporate document types and lender workflows
- recognizes regulatory and litigation context relevant to India

### Product Metrics

- time to complete a first-pass appraisal
- percentage of uploaded documents correctly classified
- percentage of schema fields auto-filled before analyst edits
- number of surfaced risk signals per case
- time from final review to CAM download

## 8. Scope of the MVP

### Mandatory MVP Capabilities

- hosted web app with frontend and backend
- case creation and entity onboarding
- upload flow for five mandatory document categories
- auto-classification with user approval/edit
- schema-driven extraction into normalized case data
- external research on company, promoters, sector, and litigation/regulation
- analyst notes input and integration into scoring
- explainable scoring and recommendation
- downloadable report in at least one professional format, ideally both DOCX and PDF

### Nice-to-Have if Time Permits

- OCR confidence overlays on source pages
- side-by-side source viewer and extracted data editor
- case comparison across peers
- sensitivity simulation for loan amount and pricing
- multiple report templates for different lender personas

## 9. Functional Requirements

## 9.1 Stage 1: Entity Onboarding

### Objective
Capture the base identity of the borrower and the proposed credit request before document ingestion begins.

### Required Inputs

- entity name
- CIN
- PAN
- sector
- subsector
- incorporation type
- geography
- turnover band
- existing lender relationships if available

### Loan Inputs

- loan type
- requested amount
- requested tenure
- target interest rate if provided
- purpose of loan
- collateral summary if known

### Product Requirements

- multi-step form UX is preferred
- input validation for key fields
- save draft capability
- create a case record immediately after onboarding starts
- show document checklist as soon as onboarding is complete

### Acceptance Criteria

- user can create a new case in under three minutes
- incomplete mandatory fields block progression
- case ID is generated and persisted

## 9.2 Stage 2: Intelligent Data Ingestion

### Objective
Allow secure upload and case binding of required credit documents.

### Required Document Types

- ALM
- Shareholding Pattern
- Borrowing Profile
- Annual Reports
- Portfolio Cuts / Performance Data

### Additional Useful Inputs

- sanction letters from other banks
- legal notices
- rating agency reports
- board meeting minutes
- due diligence visit images or notes
- bank statements
- GST returns

### Product Requirements

- drag-and-drop upload UI
- support PDF, image, spreadsheet, and text uploads where relevant
- auto-detect and categorize uploads
- allow user to approve, reject, or re-label classification
- preserve original files with timestamps and source metadata
- queue long-running parsing jobs asynchronously
- show processing status per document

### Acceptance Criteria

- user can upload all required files in one case
- app shows upload, parsing, and classification states clearly
- misclassified files can be corrected before extraction proceeds

## 9.3 Stage 3: Automated Extraction and Schema Mapping

### Objective
Convert raw documents into structured case data with confidence markers and editable mappings.

### Core Requirements

- extract tables, text blocks, metadata, and key fields from each uploaded file
- map extracted values into configurable schemas
- allow users to define or adjust output schema fields
- support human-in-the-loop edits for extracted values
- store provenance linking extracted facts back to document and page

### Required Extraction Outputs by Document Type

#### ALM

- maturity buckets
- asset-liability mismatches
- liquidity coverage indicators
- near-term liabilities

#### Shareholding Pattern

- promoter holding
- public holding
- institutional participation
- changes in shareholding
- pledges if present

#### Borrowing Profile

- lender-wise exposure
- instrument type
- maturity distribution
- secured vs unsecured mix
- covenants if visible

#### Annual Report

- P&L
- balance sheet
- cash flow
- auditor comments
- notes to accounts
- management commentary
- contingent liabilities
- related party transactions

#### Portfolio Cuts / Performance Data

- vintage performance
- asset quality metrics
- segment mix
- delinquency trends
- concentration signals

### Schema Requirements

- default schema templates for each document type
- user-editable fields, labels, and expected output types
- support numeric, textual, boolean, date, list, and table outputs
- version extraction schema per case

### Acceptance Criteria

- each required document type produces a structured extraction record
- analyst can edit incorrect values before final analysis
- final analysis uses the edited values, not only the raw auto-extraction

## 9.4 Stage 4: Pre-Cognitive Secondary Analysis and Reporting

### Objective
Enrich the case with web-scale research, analyst notes, and explainable decisioning.

### Secondary Research Requirements

- search the web for company-specific news
- search for promoter-related signals
- search for sector and subsector headwinds
- search for relevant RBI, MCA, SEBI, and market signals
- search for litigation and legal disputes
- rank findings by relevance and severity
- attach source URLs, dates, and snippets

### Primary Insight Integration

- provide a note-taking portal for credit officer observations
- support tags such as operations, governance, plant visit, management quality, utilization, collections, collateral, litigation
- allow notes to affect the scoring logic transparently

### Final Analysis Requirements

- triangulate extracted document facts with external research and analyst notes
- generate SWOT
- generate Five Cs of Credit analysis
- generate risk signals and contradictions
- generate final recommendation with reasons
- export professional report

### Acceptance Criteria

- final report contains both uploaded-document analysis and secondary research
- final recommendation references explicit supporting evidence
- user can download final report from the web app

## 10. Recommendation Engine Requirements

### Decision Outputs

The engine must produce:

- recommendation: approve / conditional approve / reject
- recommended loan limit
- indicative interest premium or pricing band
- key reasons for decision
- key monitoring conditions or covenants

### Explainability Requirements

The recommendation must explicitly answer:

- why approval or rejection was reached
- what signals increased or decreased risk
- how analyst notes altered the outcome
- what contradictions or missing data reduce confidence

### Model Design Principles

The hackathon expects ML-based reasoning, but the solution must remain transparent.

Recommended design:

- `policy layer` for hard-stop rules and data sufficiency gates
- `scoring layer` for explainable weighted risk scoring or interpretable ML
- `structuring layer` for mapping score bands to limit, pricing, and conditions

### Illustrative Hard Stops

- critical litigation with direct repayment impact
- severe data inconsistency between uploaded financial sources
- negative net worth combined with stressed cash flow and weak external signals
- material governance red flags

### Illustrative Positive Drivers

- stable cash generation
- healthy liquidity profile
- improving borrowing mix
- favorable sector context
- clean governance and promoter signals

## 11. India-Specific Underwriting Logic

The product must visibly demonstrate Indian context awareness.

### Must-Have India-Specific Checks

- GSTR-2A or 2B versus 3B mismatch logic
- GST versus bank statement turnover mismatch
- circular trading or revenue inflation heuristics
- promoter and pledge interpretation in listed-entity contexts
- rating report interpretation for Indian agencies and lender comfort
- sector and regulatory references relevant to RBI, MCA, SEBI, and Indian courts

### How These Should Appear in Product

- as explicit risk checks in the analysis view
- as evidence-backed bullets in the CAM
- as explainable score drivers rather than hidden heuristics

## 12. Research Agent Requirements

### Search Targets

- borrower company
- promoters and directors
- group companies if identifiable
- sector and subsector
- macro and regulatory changes
- litigation and disputes

### Research Output Model

Each finding should include:

- title
- source
- URL
- publication or filing date
- category
- severity
- short summary
- relevance to credit decision

### Product Rules

- do not dump raw search results into the report
- cluster duplicate findings
- prefer recent and relevant sources
- distinguish fact from inference
- keep source links visible to judges and users

## 13. CAM Requirements

### Required CAM Sections

- borrower overview
- facility request summary
- document coverage and data quality summary
- business and sector overview
- financial summary
- management and governance summary
- lender and borrowing profile
- key risks and mitigants
- Five Cs analysis
- SWOT
- recommendation
- proposed structure, limit, and pricing
- monitoring conditions and next steps

### Report Output Requirements

- professional formatting
- easy to scan in demo conditions
- downloadable as DOCX and/or PDF
- evidence-backed statements
- visible confidence or caution markers where uncertainty remains

## 14. User Experience Requirements

### UX Principles

- simple, linear, four-stage flow
- no dead ends
- visible progress at every stage
- heavy workflows must show status, not freeze
- review screens should support human correction quickly
- final recommendation should be inspectable, not hidden inside long prose

### Critical UX Screens

- onboarding form
- upload and classification review
- schema and extraction review
- research and analyst notes
- scoring and recommendation dashboard
- final report preview and download

### Demo-Friendly Design Requirement

In the hackathon demo, judges should understand the workflow in under two minutes.

The app should therefore emphasize:

- clarity of stages
- visible extracted outputs
- visible external research
- visible scoring rationale
- professional final report

## 15. Data and System Architecture

### High-Level Architecture

- `Frontend`: hosted web application for analysts
- `Backend`: APIs, orchestration, extraction jobs, scoring, and report generation
- `Storage`: uploaded files, extracted structured data, reports, and case state
- `Research Layer`: web search and source retrieval
- `Scoring Layer`: explainable decisioning service

### Databricks Positioning

The hackathon statement explicitly mentions Databricks for multi-source ingestion.

For product design, data should conceptually flow through:

- `Bronze`: raw uploaded files, external research fetches, analyst notes
- `Silver`: classified documents, normalized extracted tables, structured case schema
- `Gold`: scored case features, risk signals, recommendation outputs, report artifacts

For the prototype, implementation may use local or standard app storage if needed, but the data model should remain Databricks-compatible.

## 16. Core Data Objects

### Case

- entity details
- loan request
- case status

### Document

- file metadata
- category
- classification state
- parse status

### Extraction

- field name
- extracted value
- value type
- confidence
- provenance
- reviewer override

### Research Finding

- source metadata
- finding category
- severity
- summary

### Analyst Note

- note text
- tags
- author
- timestamp
- impact on score if used

### Scorecard

- sub-scores
- overall score
- key drivers
- policy flags
- recommendation

### Report

- generated narrative
- export metadata
- download status

## 17. Non-Functional Requirements

### Hosting

- accessible publicly without VPN
- stable enough for live demo
- basic authentication or gated access preferred

### Performance

- onboarding actions should feel immediate
- upload acknowledgement should be near-instant
- long extraction jobs can be asynchronous but must show progress
- final report generation should complete within demo-acceptable time

### Reliability

- retries or graceful fallback for failed research or extraction steps
- preserve intermediate case state
- do not lose uploaded files or edited values on refresh

### Auditability

- every final claim in analysis should trace back to evidence or analyst input
- reviewer overrides should be preserved

### Security

- case data isolated per session or user
- uploaded files stored securely
- no exposed secrets in frontend

## 18. MVP Prioritization

### P0: Must Ship

- onboarding
- upload and document classification
- extraction for the five required document types
- editable schema/extraction review
- secondary research
- analyst notes
- explainable scoring
- CAM/report generation
- hosted deployment

### P1: Should Ship If Time Allows

- source page previews and provenance drill-down
- confidence indicators
- richer pricing and covenant logic
- stronger document comparison and contradiction detection

### P2: Post-Hackathon

- deep integrations with MCA or court systems
- historical portfolio calibration
- borrower benchmarking against peers
- collaborative review workflows

## 19. Risks and Mitigations

### Risk: OCR or parsing quality is inconsistent

Mitigation:

- human-in-the-loop correction
- schema review step
- confidence markers
- selective fallback parsing strategies

### Risk: research results are noisy

Mitigation:

- source ranking
- deduplication
- evidence tagging
- restrict report claims to relevant findings

### Risk: recommendation appears like a black box

Mitigation:

- explicit score drivers
- policy flags
- evidence citations
- visible analyst-note impact

### Risk: demo instability

Mitigation:

- preload sample cases
- support asynchronous jobs with saved state
- optimize the demo path around the provided challenge corpus

## 20. Demo Narrative

The final demo should tell a tight story:

1. onboard a borrower and requested facility
2. upload the five required documents
3. show auto-classification and structured extraction
4. show secondary research and analyst note integration
5. show explainable score breakdown and risk drivers
6. show final CAM and downloadable report

The key message to judges:

This is not just a parser. It is a decision-support system for Indian credit underwriting.

## 21. Acceptance Criteria

The PRD is satisfied for hackathon MVP if:

- a user can create a case and upload the five required document types
- the system classifies and extracts structured information from those documents
- the user can review or edit extracted outputs
- the system fetches and displays external research findings
- the user can enter due diligence notes
- the system generates an explainable recommendation on lend / limit / pricing
- the final report can be viewed and downloaded from the hosted web app

## 22. Build Recommendation

The product should be implemented as a narrow but polished underwriting workbench:

- deep enough to show serious credit intelligence
- small enough to finish during the hackathon
- opinionated enough to feel like a real lender workflow

The winning angle is:

`explainable underwriting intelligence for Indian corporate credit`

not generic OCR, not generic chatbot, and not generic report generation.
