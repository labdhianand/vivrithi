# Intelli-Credit V2 — Complete Build Specification

> **Purpose**: This document is the single source of truth for building the Intelli-Credit Copilot V2 from scratch. It is written for an AI coding agent (Codex) to follow step by step. Every module, endpoint, schema, and UI component is specified here.

---

## 1. Product Summary

**Intelli-Credit Copilot** is a hosted web application that automates enterprise credit underwriting for Indian corporates and NBFCs. It transforms raw, unstructured financial documents into a comprehensive, AI-backed Credit Appraisal Memo (CAM).

### The User Journey (4 Stages)

1. **Entity Onboarding** — Capture company details (CIN, PAN, sector, turnover) and loan request (type, amount, tenure, rate).
2. **Intelligent Data Ingestion** — Upload 5 document types: ALM, Shareholding Pattern, Borrowing Profile, Annual Report, Portfolio/Performance Data. System auto-classifies with human-in-the-loop approval.
3. **Automated Extraction & Schema Mapping** — Parse documents via a multi-backend pipeline. Extract structured data using dynamic, user-configurable schemas. Maintain bounding box provenance for every extracted value.
4. **Pre-Cognitive Analysis & Reporting** — Secondary research (news, legal, regulatory, market). Cross-document triangulation. Five Cs credit scoring with explainable reasoning. SWOT analysis. Downloadable CAM (Word/PDF).

### Evaluation Criteria (from judges)

- **Operational Excellence**: Stable app, flawless uploads and forms
- **Extraction Accuracy**: Complex, non-standard Indian financial tables parsed correctly
- **Analytical Depth**: Quality of secondary research and "pre-cognitive" risk signals
- **User Experience**: Intuitive and fast journey from raw PDF to final report
- **Explainability**: AI can "walk the judge through" its logic
- **Indian Context Sensitivity**: Understanding of NBFC/HFC regulations, RBI/NHB guidelines, IndAS

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND (Next.js)                 │
│  /onboarding  /upload  /extraction  /analysis /report│
└───────────────────────┬─────────────────────────────┘
                        │ REST API
┌───────────────────────▼─────────────────────────────┐
│                   BACKEND (FastAPI)                   │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │
│  │ PDF      │  │ Classify │  │ Extract            │ │
│  │ Triage   │──│ & Route  │──│ (Schema-guided)    │ │
│  └──────────┘  └──────────┘  └────────────────────┘ │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │
│  │ Research │  │ Cross-   │  │ Five Cs Scorer     │ │
│  │ Agent    │  │ Verify   │  │ + Recommendation   │ │
│  └──────────┘  └──────────┘  └────────────────────┘ │
│                                                      │
│  ┌──────────┐  ┌──────────┐                         │
│  │ CAM Gen  │  │ Exporter │                         │
│  └──────────┘  └──────────┘                         │
└───────────────────────┬─────────────────────────────┘
                        │
          ┌─────────────┼──────────────┐
          │             │              │
     PostgreSQL    File Storage    External APIs
     (Supabase)    (Supabase)     (LandingAI, Claude,
                                   Tavily, yfinance)
```

---

## 3. Tech Stack

### Frontend
- **Next.js 14** (App Router) with TypeScript
- **Tailwind CSS** + **shadcn/ui** component library
- **react-pdf** (or `@react-pdf-viewer/core`) for PDF rendering with bounding box overlays
- **TanStack Table** for editable data tables
- **Zustand** for client state management
- **Deployed on Vercel**

### Backend
- **Python 3.11+** with **FastAPI**
- **SQLAlchemy 2.0** ORM with async support
- **Pydantic v2** for all data validation and schemas
- **BackgroundTasks** (FastAPI built-in) for async PDF processing — skip Celery for hackathon simplicity
- **Deployed on Railway or Render**

### PDF Processing
| Tool | Install / Access | Purpose |
|---|---|---|
| **PyMuPDF (fitz)** | `pip install pymupdf` | Page triage: digital vs scanned detection, page image rendering, text layer extraction |
| **pdfplumber** | `pip install pdfplumber` | Digital PDF table extraction with character-level bounding boxes |
| **LandingAI API** | REST API, key required | Complex/scanned table extraction with bounding boxes (agentic document analysis endpoint) |
| **Claude API** | `pip install anthropic` | Vision fallback for difficult pages, document classification, schema-guided extraction, SWOT/CAM generation |

### Database & Storage
- **Supabase** (PostgreSQL + Storage + optional Auth)
- Tables for: cases, documents, pages, extractions, schemas, research_items, analyst_notes, scores, reports
- File storage for uploaded PDFs and generated reports

### Secondary Research
- **Tavily API** — programmatic web search for news, regulatory filings, litigation
- **yfinance** — stock data, peer comparison
- **BeautifulSoup** — targeted scraping if needed

### Report Generation
- **python-docx** — Word CAM export
- **WeasyPrint** or **reportlab** — PDF CAM export

---

## 4. Project Structure

```
vivriti/
├── BUILD_SPEC.md              # This file
├── claude_data/               # Sample test data (existing)
│
├── frontend/                  # Next.js application
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── .env.local             # NEXT_PUBLIC_API_URL
│   │
│   ├── app/
│   │   ├── layout.tsx         # Root layout with sidebar nav
│   │   ├── page.tsx           # Landing / dashboard
│   │   │
│   │   ├── onboarding/
│   │   │   └── page.tsx       # Stage 1: Entity + Loan form
│   │   │
│   │   ├── cases/
│   │   │   ├── page.tsx       # Case list
│   │   │   └── [caseId]/
│   │   │       ├── page.tsx           # Case overview
│   │   │       ├── upload/
│   │   │       │   └── page.tsx       # Stage 2: Document upload
│   │   │       ├── classify/
│   │   │       │   └── page.tsx       # Stage 3a: Classification review
│   │   │       ├── extraction/
│   │   │       │   ├── page.tsx       # Stage 3b: Extraction overview
│   │   │       │   └── [docId]/
│   │   │       │       └── page.tsx   # Per-doc extraction with PDF viewer + bbox
│   │   │       ├── schema/
│   │   │       │   └── page.tsx       # Stage 3c: Dynamic schema editor
│   │   │       ├── analysis/
│   │   │       │   ├── page.tsx       # Stage 4 overview
│   │   │       │   ├── research/
│   │   │       │   │   └── page.tsx   # Secondary research results
│   │   │       │   ├── notes/
│   │   │       │   │   └── page.tsx   # Analyst notes input
│   │   │       │   ├── cross-check/
│   │   │       │   │   └── page.tsx   # Cross-document verification
│   │   │       │   └── five-cs/
│   │   │       │       └── page.tsx   # Five Cs scoring breakdown
│   │   │       └── report/
│   │   │           └── page.tsx       # Final CAM view + download
│   │   │
│   │   └── api/                       # Next.js API routes (proxy if needed)
│   │
│   ├── components/
│   │   ├── ui/                        # shadcn/ui components (button, card, input, etc.)
│   │   ├── layout/
│   │   │   ├── sidebar.tsx
│   │   │   ├── header.tsx
│   │   │   └── stage-stepper.tsx      # Visual progress through 4 stages
│   │   ├── onboarding/
│   │   │   ├── entity-form.tsx
│   │   │   └── loan-form.tsx
│   │   ├── upload/
│   │   │   ├── dropzone.tsx           # Drag-and-drop file upload
│   │   │   └── upload-progress.tsx
│   │   ├── classification/
│   │   │   └── classification-card.tsx # Shows auto-classification with approve/deny/edit
│   │   ├── extraction/
│   │   │   ├── pdf-viewer.tsx         # PDF rendering with bbox overlay layer
│   │   │   ├── bbox-overlay.tsx       # SVG overlay for bounding boxes on PDF pages
│   │   │   ├── extracted-data-table.tsx # Editable table showing extracted key-value pairs
│   │   │   └── confidence-badge.tsx   # Green/Amber/Red confidence indicator
│   │   ├── schema/
│   │   │   └── schema-editor.tsx      # Add/remove/edit fields in extraction schema
│   │   ├── research/
│   │   │   ├── research-card.tsx      # Individual research finding with source link
│   │   │   └── sentiment-badge.tsx
│   │   ├── analysis/
│   │   │   ├── five-cs-radar.tsx      # Radar/spider chart for Five Cs scores
│   │   │   ├── score-card.tsx         # Individual C score with reasoning
│   │   │   ├── swot-grid.tsx          # 2x2 SWOT display
│   │   │   └── recommendation-panel.tsx # Final decision with reasoning chain
│   │   ├── notes/
│   │   │   └── analyst-note-form.tsx  # Free-text + tag input for field notes
│   │   └── report/
│   │       ├── cam-preview.tsx        # Rendered CAM sections
│   │       └── download-buttons.tsx   # DOCX + PDF download
│   │
│   └── lib/
│       ├── api.ts                     # API client (fetch wrapper for backend)
│       ├── types.ts                   # TypeScript types matching backend schemas
│       └── utils.ts
│
├── backend/                   # FastAPI application
│   ├── pyproject.toml         # Dependencies: fastapi, uvicorn, sqlalchemy, pydantic,
│   │                          #   pymupdf, pdfplumber, anthropic, python-docx, etc.
│   ├── .env                   # API keys: ANTHROPIC_API_KEY, LANDING_AI_API_KEY,
│   │                          #   TAVILY_API_KEY, SUPABASE_URL, SUPABASE_KEY
│   │
│   ├── app/
│   │   ├── main.py            # FastAPI app factory, CORS, lifespan events
│   │   ├── config.py          # Settings from env vars (pydantic-settings)
│   │   ├── database.py        # SQLAlchemy engine, session factory, Base
│   │   │
│   │   ├── models/            # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── case.py        # Case model (entity + loan details)
│   │   │   ├── document.py    # Document model (uploaded file metadata)
│   │   │   ├── page.py        # Page model (per-page triage results)
│   │   │   ├── extraction.py  # Extraction model (field, value, bbox, confidence)
│   │   │   ├── schema.py      # Schema model (user-defined extraction schemas)
│   │   │   ├── research.py    # ResearchItem model (news, legal, regulatory findings)
│   │   │   ├── analyst_note.py # AnalystNote model (primary insights from credit officer)
│   │   │   ├── score.py       # Score model (Five Cs sub-scores + overall)
│   │   │   └── report.py      # Report model (generated CAM metadata)
│   │   │
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── case.py
│   │   │   ├── document.py
│   │   │   ├── extraction.py
│   │   │   ├── schema.py
│   │   │   ├── research.py
│   │   │   ├── analysis.py
│   │   │   └── report.py
│   │   │
│   │   ├── api/               # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── router.py      # Main router aggregating all sub-routers
│   │   │   ├── cases.py       # CRUD for cases + entity onboarding
│   │   │   ├── documents.py   # Upload, list, classify documents
│   │   │   ├── extraction.py  # Trigger extraction, get/edit extracted data
│   │   │   ├── schemas.py     # CRUD for dynamic extraction schemas
│   │   │   ├── research.py    # Trigger + view secondary research
│   │   │   ├── notes.py       # CRUD for analyst notes
│   │   │   ├── analysis.py    # Five Cs scoring, cross-verification, recommendation
│   │   │   └── reports.py     # Generate + download CAM
│   │   │
│   │   ├── services/          # Core business logic
│   │   │   ├── __init__.py
│   │   │   ├── pdf_triage.py          # Page-level digital/scanned + table detection
│   │   │   ├── parser_router.py       # Route pages to correct parser backend
│   │   │   ├── parser_pdfplumber.py   # Digital PDF parsing with pdfplumber
│   │   │   ├── parser_landingai.py    # LandingAI API integration for complex tables
│   │   │   ├── parser_vision.py       # Claude Vision API for difficult pages
│   │   │   ├── markdown_builder.py    # Assemble per-document raw Markdown with bbox annotations
│   │   │   ├── classifier.py          # Document type classification using LLM
│   │   │   ├── extractor.py           # Schema-guided structured extraction from raw MD
│   │   │   ├── research_agent.py      # Secondary research: Tavily + yfinance + scraping
│   │   │   ├── cross_verifier.py      # Cross-document triangulation checks
│   │   │   ├── five_cs_scorer.py      # Five Cs credit scoring framework
│   │   │   ├── recommendation.py      # Final decision: approve/reject/conditional + reasoning
│   │   │   ├── swot_generator.py      # SWOT analysis using LLM + extracted data
│   │   │   ├── cam_generator.py       # CAM narrative generation (LLM-backed)
│   │   │   └── exporter.py            # DOCX + PDF export
│   │   │
│   │   └── extraction_schemas/        # Default schemas per document type
│   │       ├── __init__.py
│   │       ├── alm.py
│   │       ├── shareholding.py
│   │       ├── borrowing.py
│   │       ├── financials.py
│   │       └── annual_report.py
│   │
│   └── tests/
│       ├── test_pdf_triage.py
│       ├── test_extraction.py
│       └── test_five_cs.py
│
└── data/                      # Existing data directory
    └── challenge_doc_corpus/  # Test documents
```

---

## 5. Database Schema

### 5.1 `cases` table
```sql
CREATE TABLE cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Entity details
    company_name TEXT NOT NULL,
    cin TEXT,                          -- Corporate Identity Number
    pan TEXT,
    sector TEXT,                       -- e.g., "Housing Finance", "NBFC-HFC"
    subsector TEXT,
    turnover_crore DECIMAL,
    incorporation_date DATE,
    registered_office TEXT,
    -- Loan request details
    loan_type TEXT,                    -- "Term Loan", "Working Capital", "NCD"
    loan_amount_crore DECIMAL,
    loan_tenure_months INTEGER,
    proposed_rate_percent DECIMAL,
    loan_purpose TEXT,
    -- Status
    status TEXT DEFAULT 'onboarding',  -- onboarding | documents_uploaded | extracting |
                                       -- extracted | analyzing | report_ready
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### 5.2 `documents` table
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    -- File info
    original_filename TEXT NOT NULL,
    stored_path TEXT NOT NULL,         -- Path in file storage
    file_size_bytes BIGINT,
    mime_type TEXT,
    sha256_hash TEXT,
    -- Classification
    auto_category TEXT,               -- ALM | Shareholding_Pattern | Borrowing_Profile |
                                      -- Annual_Report | Portfolio_Performance
    auto_category_confidence DECIMAL,
    user_category TEXT,               -- User-approved category (may differ from auto)
    classification_status TEXT DEFAULT 'pending', -- pending | auto_classified | user_approved
    -- Processing status
    processing_status TEXT DEFAULT 'pending', -- pending | triaging | parsing | extracting |
                                              -- extracted | error
    total_pages INTEGER,
    raw_markdown TEXT,                -- Full document raw MD after parsing
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 5.3 `pages` table
```sql
CREATE TABLE pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    -- Triage results
    is_scanned BOOLEAN,
    has_tables BOOLEAN,
    content_type TEXT,                -- cover_letter | financial_table | narrative |
                                      -- chart | signature_page | blank
    -- Parsing
    parser_used TEXT,                 -- pdfplumber | landingai | claude_vision | skip
    raw_text TEXT,                    -- Extracted text for this page
    raw_markdown TEXT,                -- Formatted markdown for this page
    page_image_path TEXT,             -- Path to rendered page image (for bbox overlay)
    -- Metadata
    parsing_confidence DECIMAL,
    parsing_duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 5.4 `extractions` table
```sql
CREATE TABLE extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    page_id UUID REFERENCES pages(id),
    -- Extracted data point
    schema_field_key TEXT NOT NULL,   -- e.g., "hqla_total", "promoter_holding_percent"
    field_label TEXT,                 -- Human-readable label
    value TEXT,                       -- Extracted value as string
    value_type TEXT,                  -- number | percentage | text | date | currency
    value_numeric DECIMAL,           -- Parsed numeric value if applicable
    -- Provenance (bounding box)
    source_page_number INTEGER,
    bbox_x1 DECIMAL,                 -- Top-left x (as fraction of page width, 0-1)
    bbox_y1 DECIMAL,                 -- Top-left y
    bbox_x2 DECIMAL,                 -- Bottom-right x
    bbox_y2 DECIMAL,                 -- Bottom-right y
    -- Quality
    confidence DECIMAL,              -- 0.0 to 1.0
    extraction_method TEXT,          -- pdfplumber | landingai | claude_vision | llm_inferred
    -- Human-in-the-loop
    user_verified BOOLEAN DEFAULT FALSE,
    user_edited_value TEXT,          -- If user modified the extracted value
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 5.5 `extraction_schemas` table
```sql
CREATE TABLE extraction_schemas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    document_category TEXT NOT NULL,  -- ALM | Shareholding_Pattern | etc.
    schema_version INTEGER DEFAULT 1,
    -- Schema definition as JSON
    fields JSONB NOT NULL,           -- Array of {key, label, type, required, description}
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### 5.6 `research_items` table
```sql
CREATE TABLE research_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    -- Research result
    category TEXT NOT NULL,          -- news | legal | regulatory | market | sector | promoter
    title TEXT,
    summary TEXT,
    source_url TEXT,
    source_name TEXT,                -- e.g., "Economic Times", "MCA Portal", "RBI Circular"
    published_date DATE,
    -- Analysis
    sentiment TEXT,                  -- positive | negative | neutral
    severity TEXT,                   -- low | medium | high | critical
    relevance_score DECIMAL,
    -- Impact on credit assessment
    affected_c TEXT,                 -- Which of Five Cs this impacts: Character | Capacity |
                                     -- Capital | Collateral | Conditions
    impact_description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 5.7 `analyst_notes` table
```sql
CREATE TABLE analyst_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    -- Note content
    note_type TEXT,                  -- site_visit | management_meeting | market_feedback |
                                     -- regulatory_observation | other
    content TEXT NOT NULL,
    -- Impact
    affected_c TEXT,                 -- Character | Capacity | Capital | Collateral | Conditions
    sentiment TEXT,                  -- positive | negative | neutral
    risk_adjustment INTEGER,        -- How many points to adjust risk score (-10 to +10)
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 5.8 `scores` table
```sql
CREATE TABLE scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    -- Five Cs scores (each 0-100)
    character_score INTEGER,
    character_reasoning TEXT,        -- JSON: {factors: [{signal, source, impact, evidence}]}
    capacity_score INTEGER,
    capacity_reasoning TEXT,
    capital_score INTEGER,
    capital_reasoning TEXT,
    collateral_score INTEGER,
    collateral_reasoning TEXT,
    conditions_score INTEGER,
    conditions_reasoning TEXT,
    -- Aggregate
    overall_score INTEGER,          -- Weighted composite
    risk_grade TEXT,                 -- AAA | AA | A | BBB | BB | B | C | D
    -- Decision
    recommendation TEXT,            -- approve | conditional_approve | reject
    recommended_amount_crore DECIMAL,
    recommended_rate_percent DECIMAL,
    recommended_tenure_months INTEGER,
    -- Reasoning
    decision_reasoning TEXT,         -- Full explanation narrative
    key_strengths JSONB,            -- Array of strength statements with evidence refs
    key_risks JSONB,                -- Array of risk statements with evidence refs
    conditions_precedent JSONB,     -- Required before disbursement
    conditions_subsequent JSONB,    -- Required after disbursement
    monitoring_covenants JSONB,     -- Ongoing monitoring requirements
    -- SWOT
    swot JSONB,                     -- {strengths: [], weaknesses: [], opportunities: [], threats: []}
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 5.9 `reports` table
```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    -- Report metadata
    report_type TEXT DEFAULT 'cam', -- cam | summary
    format TEXT,                    -- docx | pdf
    stored_path TEXT,              -- File storage path
    generated_at TIMESTAMPTZ DEFAULT now(),
    -- Content sections (for preview)
    sections JSONB                  -- Array of {title, content_markdown, evidence_refs[]}
);
```

---

## 6. API Endpoints

### 6.1 Cases
```
POST   /api/cases                    # Create case with entity + loan details
GET    /api/cases                    # List all cases
GET    /api/cases/{case_id}          # Get case details with status
PATCH  /api/cases/{case_id}          # Update case details
```

### 6.2 Documents
```
POST   /api/cases/{case_id}/documents/upload    # Upload PDF(s) — multipart form
GET    /api/cases/{case_id}/documents            # List documents for case
GET    /api/documents/{doc_id}                   # Get document details + classification
PATCH  /api/documents/{doc_id}/classify          # User approves/edits classification
POST   /api/documents/{doc_id}/process           # Trigger full processing pipeline
GET    /api/documents/{doc_id}/pages             # Get per-page triage results
GET    /api/documents/{doc_id}/pages/{page_num}/image  # Get rendered page image
GET    /api/documents/{doc_id}/markdown           # Get full raw markdown
```

### 6.3 Extraction
```
GET    /api/documents/{doc_id}/extractions       # Get all extracted fields for document
PATCH  /api/extractions/{extraction_id}          # User edits an extracted value
POST   /api/documents/{doc_id}/extract           # Re-run extraction with current schema
```

### 6.4 Schemas
```
GET    /api/schemas/defaults/{category}           # Get default schema for doc category
GET    /api/cases/{case_id}/schemas               # Get case-specific schemas
POST   /api/cases/{case_id}/schemas               # Create/update custom schema
PUT    /api/cases/{case_id}/schemas/{schema_id}   # Update schema fields
```

### 6.5 Research
```
POST   /api/cases/{case_id}/research/run          # Trigger secondary research
GET    /api/cases/{case_id}/research               # Get all research findings
DELETE /api/research/{item_id}                     # Remove irrelevant finding
```

### 6.6 Analyst Notes
```
POST   /api/cases/{case_id}/notes                 # Add analyst note
GET    /api/cases/{case_id}/notes                  # List notes
DELETE /api/notes/{note_id}                        # Remove note
```

### 6.7 Analysis & Scoring
```
POST   /api/cases/{case_id}/analyze               # Run full analysis pipeline
GET    /api/cases/{case_id}/cross-verification     # Get cross-document check results
GET    /api/cases/{case_id}/five-cs                # Get Five Cs breakdown
GET    /api/cases/{case_id}/recommendation         # Get final recommendation + reasoning
GET    /api/cases/{case_id}/swot                   # Get SWOT analysis
```

### 6.8 Reports
```
POST   /api/cases/{case_id}/reports/generate       # Generate CAM
GET    /api/cases/{case_id}/reports                 # List generated reports
GET    /api/reports/{report_id}/preview             # Get report sections for preview
GET    /api/reports/{report_id}/download/{format}   # Download DOCX or PDF
```

---

## 7. PDF Processing Pipeline (The Core)

This is the most critical component. Every PDF goes through this pipeline:

### 7.1 Page-Level Triage (`pdf_triage.py`)

For each uploaded PDF:

1. **Open with PyMuPDF** (`fitz.open(path)`)
2. **For each page:**
   - Extract text via `page.get_text("text")`
   - Count characters. If `len(text.strip()) < 50` and page has images → **scanned**
   - Detect tables: check for `page.get_drawings()` (lines/rects suggesting table borders) OR use pdfplumber's `page.find_tables()` on digital pages
   - Classify content type:
     - If text contains "Dear Sir/Madam" or "To, The National Stock Exchange" → `cover_letter`
     - If has tables with financial data → `financial_table`
     - If mostly prose text → `narrative`
     - If very little text + images → `chart_or_infographic`
     - If only signatures/stamps → `signature_page`
     - If nearly empty → `blank`
   - Render page as PNG image: `page.get_pixmap(matrix=fitz.Matrix(2, 2))` and save for frontend bbox overlay

3. **Store triage results** in `pages` table

```python
# Pseudo-code for pdf_triage.py
class PageTriageResult:
    page_number: int
    is_scanned: bool
    has_tables: bool
    content_type: str  # cover_letter | financial_table | narrative | chart | signature_page | blank
    text_content: str
    image_path: str    # Path to rendered page image

def triage_document(pdf_path: str) -> list[PageTriageResult]:
    doc = fitz.open(pdf_path)
    results = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        is_scanned = len(text.strip()) < 50 and len(page.get_images()) > 0
        # ... detection logic ...
        # Render page image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        image_path = f"pages/{doc_id}/page_{page_num + 1}.png"
        pix.save(image_path)
        results.append(PageTriageResult(...))
    return results
```

### 7.2 Parser Router (`parser_router.py`)

Routes each page to the best parser based on triage results:

```python
def route_page(triage: PageTriageResult) -> str:
    if triage.content_type == "blank" or triage.content_type == "signature_page":
        return "skip"
    if triage.has_tables:
        if triage.is_scanned:
            return "landingai"         # Best for scanned tables
        else:
            return "pdfplumber"        # Fast + accurate for digital tables, fallback to landingai
    if triage.is_scanned:
        return "claude_vision"         # Scanned narrative text
    return "pdfplumber"                # Digital narrative text
```

### 7.3 Parser: pdfplumber (`parser_pdfplumber.py`)

For digital pages:

```python
import pdfplumber

def parse_page_pdfplumber(pdf_path: str, page_num: int) -> ParsedPage:
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]

        # Extract tables with bounding boxes
        tables = page.find_tables()
        table_results = []
        for table in tables:
            bbox = table.bbox  # (x0, y0, x1, y1) in PDF coordinates
            rows = table.extract()
            table_results.append({
                "bbox": normalize_bbox(bbox, page.width, page.height),  # Convert to 0-1 range
                "rows": rows,
                "markdown": table_to_markdown(rows)
            })

        # Extract text with character-level positions
        chars = page.chars
        text = page.extract_text()

        return ParsedPage(
            text=text,
            tables=table_results,
            markdown=build_page_markdown(text, table_results),
            bounding_boxes=extract_field_bboxes(chars, table_results)
        )
```

### 7.4 Parser: LandingAI (`parser_landingai.py`)

For complex/scanned tables:

```python
import httpx

LANDING_AI_URL = "https://api.landing.ai/v1/tools/agentic-document-analysis"

async def parse_page_landingai(page_image_path: str, prompt: str = None) -> ParsedPage:
    """Send page image to LandingAI for table extraction."""
    with open(page_image_path, "rb") as f:
        response = await httpx.AsyncClient().post(
            LANDING_AI_URL,
            headers={"Authorization": f"Bearer {LANDING_AI_API_KEY}"},
            files={"image": f},
            data={"prompt": prompt or "Extract all tables and text from this financial document page. Return structured data with bounding boxes."}
        )
    result = response.json()
    # LandingAI returns structured data with bounding boxes natively
    return ParsedPage(
        text=result.get("text", ""),
        tables=result.get("tables", []),
        markdown=result.get("markdown", ""),
        bounding_boxes=result.get("bounding_boxes", [])
    )
```

### 7.5 Parser: Claude Vision (`parser_vision.py`)

Fallback for difficult pages:

```python
from anthropic import Anthropic
import base64

async def parse_page_claude_vision(page_image_path: str) -> ParsedPage:
    """Use Claude's vision capability to extract content from a page image."""
    client = Anthropic()
    with open(page_image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
                {"type": "text", "text": """Extract all text and tables from this financial document page.
Return as structured markdown. For each table, provide the data in markdown table format.
For each key data point, estimate the bounding box as [x1, y1, x2, y2] where coordinates
are fractions of page dimensions (0 to 1)."""}
            ]
        }]
    )
    # Parse Claude's response into structured format
    return parse_claude_response(response.content[0].text)
```

### 7.6 Markdown Builder (`markdown_builder.py`)

After all pages are parsed, assemble a single document markdown:

```python
def build_document_markdown(pages: list[ParsedPage], document_id: str) -> str:
    """
    Build a single markdown document from parsed pages.
    Each section is annotated with source page and bounding box references.
    """
    sections = []
    for page in pages:
        if page.content_type == "skip":
            continue
        section = f"<!-- PAGE {page.page_number} -->\n"
        section += f"## Page {page.page_number}\n\n"
        section += page.markdown
        section += "\n\n"
        sections.append(section)
    return "\n".join(sections)
```

---

## 8. Document Classification (`classifier.py`)

After triage and initial parsing, classify each document:

```python
async def classify_document(document_id: str, first_pages_markdown: str) -> ClassificationResult:
    """
    Use Claude to classify a document based on its first 2-3 pages.
    Returns category + confidence.
    """
    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"""Classify this Indian financial document into exactly ONE of these categories:

1. ALM - Asset-Liability Management / Liquidity Coverage Ratio disclosure
2. Shareholding_Pattern - SEBI quarterly shareholding pattern filing
3. Borrowing_Profile - Credit rating letters, borrowing details, lender breakdowns
4. Annual_Report - Annual report including financial statements, P&L, balance sheet, cash flow
5. Portfolio_Performance - Quarterly financial results, portfolio data, NPA data

Document content (first pages):
---
{first_pages_markdown[:3000]}
---

Respond in JSON: {{"category": "...", "confidence": 0.0-1.0, "reasoning": "..."}}"""
        }]
    )
    return parse_classification_response(response.content[0].text)
```

**Compound document detection**: If a single PDF spans multiple categories (like the CARE rating file which has a cover letter + multiple rating letters + annexures), the classifier should flag this:

```python
async def detect_compound_document(full_markdown: str) -> list[DocumentSection]:
    """Detect if a single PDF contains multiple logical documents."""
    # Look for multiple letter headers, date changes, distinct sections
    # Return section boundaries with suggested sub-categories
    ...
```

---

## 9. Default Extraction Schemas

### 9.1 ALM Schema (`extraction_schemas/alm.py`)

```python
ALM_DEFAULT_SCHEMA = {
    "category": "ALM",
    "fields": [
        {"key": "reporting_date", "label": "Reporting Date", "type": "date", "required": True},
        {"key": "hqla_total_unweighted", "label": "HQLA Total (Unweighted)", "type": "currency_lakhs", "required": True},
        {"key": "hqla_total_weighted", "label": "HQLA Total (Weighted)", "type": "currency_lakhs", "required": True},
        {"key": "cash_outflow_deposits", "label": "Cash Outflow - Deposits", "type": "currency_lakhs"},
        {"key": "cash_outflow_unsecured_wholesale", "label": "Cash Outflow - Unsecured Wholesale", "type": "currency_lakhs"},
        {"key": "cash_outflow_secured_wholesale", "label": "Cash Outflow - Secured Wholesale", "type": "currency_lakhs"},
        {"key": "cash_outflow_credit_facilities", "label": "Cash Outflow - Credit & Liquidity Facilities", "type": "currency_lakhs"},
        {"key": "cash_outflow_other_contractual", "label": "Cash Outflow - Other Contractual", "type": "currency_lakhs"},
        {"key": "cash_outflow_other_contingent", "label": "Cash Outflow - Other Contingent", "type": "currency_lakhs"},
        {"key": "total_cash_outflows_unweighted", "label": "Total Cash Outflows (Unweighted)", "type": "currency_lakhs", "required": True},
        {"key": "total_cash_outflows_weighted", "label": "Total Cash Outflows (Weighted)", "type": "currency_lakhs", "required": True},
        {"key": "cash_inflow_secured_lending", "label": "Cash Inflow - Secured Lending", "type": "currency_lakhs"},
        {"key": "cash_inflow_performing_exposures", "label": "Cash Inflow - Performing Exposures", "type": "currency_lakhs"},
        {"key": "cash_inflow_other", "label": "Cash Inflow - Other", "type": "currency_lakhs"},
        {"key": "total_cash_inflows_unweighted", "label": "Total Cash Inflows (Unweighted)", "type": "currency_lakhs", "required": True},
        {"key": "total_cash_inflows_weighted", "label": "Total Cash Inflows (Weighted)", "type": "currency_lakhs", "required": True},
        {"key": "total_net_cash_outflows", "label": "Total Net Cash Outflows", "type": "currency_lakhs"},
        {"key": "lcr_ratio", "label": "Liquidity Coverage Ratio (%)", "type": "percentage", "required": True},
        {"key": "lcr_qualitative_notes", "label": "Qualitative Disclosure Notes", "type": "text"}
    ]
}
```

### 9.2 Shareholding Schema (`extraction_schemas/shareholding.py`)

```python
SHAREHOLDING_DEFAULT_SCHEMA = {
    "category": "Shareholding_Pattern",
    "fields": [
        {"key": "reporting_quarter", "label": "Reporting Quarter", "type": "text", "required": True},
        {"key": "company_name", "label": "Company Name", "type": "text"},
        {"key": "scrip_code", "label": "Scrip Code (BSE)", "type": "text"},
        {"key": "nse_symbol", "label": "NSE Symbol", "type": "text"},
        {"key": "isin", "label": "ISIN", "type": "text"},
        {"key": "total_shares", "label": "Total Shares", "type": "number", "required": True},
        {"key": "promoter_holding_percent", "label": "Promoter & Promoter Group (%)", "type": "percentage", "required": True},
        {"key": "promoter_shares", "label": "Promoter Shares", "type": "number"},
        {"key": "promoter_name", "label": "Key Promoter Name", "type": "text"},
        {"key": "public_holding_percent", "label": "Public Shareholding (%)", "type": "percentage", "required": True},
        {"key": "fpi_holding_percent", "label": "Foreign Portfolio Investors (%)", "type": "percentage"},
        {"key": "mutual_fund_holding_percent", "label": "Mutual Funds (%)", "type": "percentage"},
        {"key": "insurance_holding_percent", "label": "Insurance Companies (%)", "type": "percentage"},
        {"key": "dii_holding_percent", "label": "Domestic Institutional Investors (%)", "type": "percentage"},
        {"key": "retail_holding_percent", "label": "Retail Investors (%)", "type": "percentage"},
        {"key": "shares_pledged_percent", "label": "Shares Pledged (% of promoter)", "type": "percentage"},
        {"key": "shares_under_ndu", "label": "Shares Under Non-Disposal Undertaking", "type": "number"},
        {"key": "esop_outstanding", "label": "ESOPs Outstanding", "type": "number"},
        {"key": "foreign_ownership_limit_utilized", "label": "Foreign Ownership Limit Utilized (%)", "type": "percentage"},
        {"key": "top_shareholders", "label": "Top Shareholders", "type": "json",
         "description": "Array of {name, shares, percent}"}
    ]
}
```

### 9.3 Borrowing Profile Schema (`extraction_schemas/borrowing.py`)

```python
BORROWING_DEFAULT_SCHEMA = {
    "category": "Borrowing_Profile",
    "fields": [
        {"key": "rating_agency", "label": "Rating Agency", "type": "text", "required": True},
        {"key": "rating_date", "label": "Rating Date", "type": "date"},
        {"key": "long_term_rating", "label": "Long-Term Rating", "type": "text", "required": True},
        {"key": "long_term_outlook", "label": "Outlook", "type": "text", "required": True},
        {"key": "rating_action", "label": "Rating Action", "type": "text", "required": True},
        {"key": "short_term_rating", "label": "Short-Term Rating", "type": "text"},
        {"key": "total_rated_facilities_crore", "label": "Total Rated Facilities (Rs. crore)", "type": "currency_crore", "required": True},
        {"key": "term_loan_total_crore", "label": "Term Loan Total (Rs. crore)", "type": "currency_crore"},
        {"key": "ncd_total_crore", "label": "NCD Total (Rs. crore)", "type": "currency_crore"},
        {"key": "cp_total_crore", "label": "Commercial Paper Total (Rs. crore)", "type": "currency_crore"},
        {"key": "fund_based_limits_crore", "label": "Fund-Based Limits (Rs. crore)", "type": "currency_crore"},
        {"key": "lender_wise_breakdown", "label": "Lender-Wise Breakdown", "type": "json",
         "description": "Array of {lender_name, facility_type, amount_crore}"},
        {"key": "ncd_instruments", "label": "NCD Instrument Details", "type": "json",
         "description": "Array of {isin, coupon_rate, maturity_date, amount_crore}"},
        {"key": "key_rating_strengths", "label": "Key Rating Strengths", "type": "text"},
        {"key": "key_rating_concerns", "label": "Key Rating Concerns", "type": "text"}
    ]
}
```

### 9.4 Financial Results Schema (`extraction_schemas/financials.py`)

```python
FINANCIALS_DEFAULT_SCHEMA = {
    "category": "Portfolio_Performance",
    "fields": [
        {"key": "reporting_period", "label": "Reporting Period", "type": "text", "required": True},
        {"key": "interest_income", "label": "Interest Income (lakhs)", "type": "currency_lakhs", "required": True},
        {"key": "fee_commission_income", "label": "Fees & Commission Income (lakhs)", "type": "currency_lakhs"},
        {"key": "total_revenue_operations", "label": "Total Revenue from Operations (lakhs)", "type": "currency_lakhs", "required": True},
        {"key": "total_income", "label": "Total Income (lakhs)", "type": "currency_lakhs", "required": True},
        {"key": "finance_costs", "label": "Finance Costs (lakhs)", "type": "currency_lakhs"},
        {"key": "employee_benefits", "label": "Employee Benefits (lakhs)", "type": "currency_lakhs"},
        {"key": "impairment_expense", "label": "Impairment on Financial Instruments (lakhs)", "type": "currency_lakhs"},
        {"key": "total_expenses", "label": "Total Expenses (lakhs)", "type": "currency_lakhs"},
        {"key": "profit_before_tax", "label": "Profit Before Tax (lakhs)", "type": "currency_lakhs", "required": True},
        {"key": "profit_after_tax", "label": "Profit After Tax (lakhs)", "type": "currency_lakhs", "required": True},
        {"key": "eps_basic", "label": "EPS Basic (Rs.)", "type": "number"},
        {"key": "eps_diluted", "label": "EPS Diluted (Rs.)", "type": "number"},
        {"key": "debt_equity_ratio", "label": "Debt-Equity Ratio", "type": "number"},
        {"key": "net_worth_lakhs", "label": "Net Worth (lakhs)", "type": "currency_lakhs"},
        {"key": "net_profit_margin", "label": "Net Profit Margin (%)", "type": "percentage"},
        {"key": "gnpa_percent", "label": "Gross NPA (%)", "type": "percentage"},
        {"key": "nnpa_percent", "label": "Net NPA (%)", "type": "percentage"},
        {"key": "provision_coverage_ratio", "label": "Provision Coverage Ratio (%)", "type": "percentage"},
        {"key": "crar_percent", "label": "Capital Risk Adequacy Ratio (%)", "type": "percentage"},
        {"key": "lcr_percent", "label": "Liquidity Coverage Ratio (%)", "type": "percentage"},
        {"key": "total_debts_to_total_assets", "label": "Total Debts to Total Assets", "type": "number"},
        {"key": "loan_assignment_count", "label": "Loans Assigned (count)", "type": "number"},
        {"key": "loan_assignment_amount_lakhs", "label": "Loans Assigned (amount, lakhs)", "type": "currency_lakhs"},
        {"key": "co_lending_count", "label": "Co-Lending Loans (count)", "type": "number"},
        {"key": "co_lending_amount_lakhs", "label": "Co-Lending Amount (lakhs)", "type": "currency_lakhs"}
    ]
}
```

### 9.5 Annual Report Schema (`extraction_schemas/annual_report.py`)

```python
ANNUAL_REPORT_DEFAULT_SCHEMA = {
    "category": "Annual_Report",
    "fields": [
        {"key": "fiscal_year", "label": "Fiscal Year", "type": "text", "required": True},
        {"key": "aum_crore", "label": "Assets Under Management (crore)", "type": "currency_crore"},
        {"key": "net_worth_crore", "label": "Net Worth (crore)", "type": "currency_crore"},
        {"key": "total_revenue_crore", "label": "Total Revenue (crore)", "type": "currency_crore"},
        {"key": "pat_crore", "label": "Profit After Tax (crore)", "type": "currency_crore"},
        {"key": "disbursements_crore", "label": "Disbursements (crore)", "type": "currency_crore"},
        {"key": "roe_percent", "label": "Return on Equity (%)", "type": "percentage"},
        {"key": "roa_percent", "label": "Return on Assets (%)", "type": "percentage"},
        {"key": "nim_percent", "label": "Net Interest Margin (%)", "type": "percentage"},
        {"key": "spread_percent", "label": "Spread (%)", "type": "percentage"},
        {"key": "eps", "label": "Earnings Per Share (Rs.)", "type": "number"},
        {"key": "branch_count", "label": "Number of Branches", "type": "number"},
        {"key": "employee_count", "label": "Number of Employees", "type": "number"},
        {"key": "customer_count", "label": "Number of Customers", "type": "number"},
        {"key": "states_present", "label": "States of Presence", "type": "number"},
        {"key": "housing_loan_percent", "label": "Housing Loan % of Book", "type": "percentage"},
        {"key": "non_housing_loan_percent", "label": "Non-Housing Loan % of Book", "type": "percentage"},
        {"key": "auditor_name", "label": "Statutory Auditor", "type": "text"},
        {"key": "auditor_qualification", "label": "Auditor Qualification/Emphasis", "type": "text"},
        {"key": "board_composition", "label": "Board Composition Summary", "type": "text"},
        {"key": "key_risks_mentioned", "label": "Key Risks Mentioned", "type": "json",
         "description": "Array of risk statements from MD&A / Risk Management section"},
        {"key": "related_party_transactions", "label": "Material Related Party Transactions", "type": "text"},
        {"key": "contingent_liabilities_crore", "label": "Contingent Liabilities (crore)", "type": "currency_crore"}
    ]
}
```

---

## 10. Schema-Guided Extraction (`extractor.py`)

This is the bridge between raw markdown and structured data:

```python
async def extract_with_schema(
    document_markdown: str,
    schema: dict,
    pages: list[PageTriageResult]
) -> list[ExtractionResult]:
    """
    Use Claude to extract structured data from document markdown
    according to the provided schema.
    Returns extracted values with bounding box references.
    """
    fields_description = "\n".join([
        f"- {f['key']} ({f['type']}): {f['label']}"
        + (f" [REQUIRED]" if f.get('required') else "")
        + (f" — {f['description']}" if f.get('description') else "")
        for f in schema['fields']
    ])

    prompt = f"""Extract the following fields from this financial document.
For each field, provide:
1. The extracted value
2. The page number where you found it
3. Your confidence (0.0 to 1.0)
4. The approximate bounding box as [x1, y1, x2, y2] where values are fractions (0 to 1) of page dimensions

Fields to extract:
{fields_description}

Document content:
---
{document_markdown}
---

Respond as JSON array: [
  {{
    "key": "field_key",
    "value": "extracted value",
    "value_numeric": 123.45,
    "page_number": 1,
    "confidence": 0.95,
    "bbox": [0.1, 0.2, 0.5, 0.3],
    "extraction_note": "any relevant context"
  }},
  ...
]

For fields you cannot find, include them with value null and confidence 0.
For JSON-type fields (like arrays), provide the full JSON structure as the value."""

    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )
    return parse_extraction_response(response.content[0].text)
```

---

## 11. Dynamic Schema System

### How It Works

1. When a document is classified, the system loads the **default schema** for that category
2. The user can view and modify the schema before extraction:
   - **Add fields**: User specifies key, label, type, and optional description
   - **Remove fields**: User can drop fields they don't need
   - **Edit fields**: Change labels, types, or mark as required
   - **Add computed fields**: e.g., "net_cash_outflow = total_outflows - total_inflows"
3. Modified schemas are saved per-case (so different cases can have different schemas)
4. Extraction runs against the user's schema (default or customized)

### Frontend Schema Editor Component

The schema editor UI should be a table where each row is a field:

```
| Key              | Label                    | Type          | Required | Actions     |
|------------------|--------------------------|---------------|----------|-------------|
| hqla_total       | HQLA Total (Weighted)    | currency_lakhs| Yes      | [Edit][Del] |
| lcr_ratio        | Liquidity Coverage Ratio  | percentage    | Yes      | [Edit][Del] |
| ...              | ...                      | ...           | ...      | ...         |
|                  | [+ Add Field]            |               |          |             |
```

Supported field types: `text`, `number`, `percentage`, `currency_lakhs`, `currency_crore`, `date`, `json`

---

## 12. Bounding Box Provenance System

### Data Flow

```
PDF Page → Parser extracts value + bbox coordinates → Stored in extractions table
    → Frontend loads page image + bbox overlay → User sees exactly where data came from
    → CAM report includes source citations (doc name, page number, bbox)
```

### Bounding Box Normalization

All bounding boxes are stored as **fractions of page dimensions** (0 to 1):
- `bbox_x1`: left edge as fraction of page width
- `bbox_y1`: top edge as fraction of page height
- `bbox_x2`: right edge as fraction of page width
- `bbox_y2`: bottom edge as fraction of page height

This makes them resolution-independent and easy to overlay on the frontend.

### Frontend PDF Viewer with Bbox Overlay

```tsx
// components/extraction/pdf-viewer.tsx
// Renders a page image with SVG overlay rectangles for bounding boxes
// When user hovers over an extracted value in the data table,
// the corresponding bbox highlights on the PDF page
// When user clicks a bbox on the PDF, the corresponding extraction is highlighted in the table
```

---

## 13. Secondary Research Agent (`research_agent.py`)

### Research Categories

For each case, run parallel research streams:

1. **Company News**: Recent news about the entity (last 12 months)
2. **Promoter News**: News about key promoters/directors
3. **Sector Analysis**: Sector-specific headwinds/tailwinds
4. **Regulatory**: Recent RBI/NHB/SEBI circulars affecting the entity
5. **Legal/Litigation**: Court cases, NCLT, arbitration
6. **Market Data**: Stock price, peer comparison (if listed)

### Implementation

```python
async def run_secondary_research(case: Case) -> list[ResearchItem]:
    """Run all research streams in parallel."""
    company_name = case.company_name
    sector = case.sector

    queries = [
        f"{company_name} latest news financial",
        f"{company_name} litigation legal case NCLT",
        f"{company_name} RBI NHB regulatory action",
        f"{company_name} promoter director news",
        f"{sector} India sector outlook 2025 2026",
        f"RBI NBFC HFC regulations latest circular 2025",
    ]

    results = []
    for query in queries:
        # Use Tavily for search
        search_results = await tavily_search(query, max_results=5)
        for sr in search_results:
            item = ResearchItem(
                case_id=case.id,
                category=classify_research_category(query, sr),
                title=sr.title,
                summary=sr.snippet,
                source_url=sr.url,
                source_name=extract_source_name(sr.url),
                published_date=sr.published_date,
                sentiment=analyze_sentiment(sr.snippet),
                severity=assess_severity(sr.snippet, company_name),
                relevance_score=sr.relevance_score,
            )
            results.append(item)

    # Use Claude to analyze impact on Five Cs
    results = await enrich_research_with_impact(results, case)
    return results
```

### Market Data (yfinance)

```python
import yfinance as yf

def get_market_data(nse_symbol: str) -> dict:
    """Fetch stock data for listed entities."""
    ticker = yf.Ticker(f"{nse_symbol}.NS")
    info = ticker.info
    hist = ticker.history(period="1y")
    return {
        "current_price": info.get("currentPrice"),
        "market_cap_crore": info.get("marketCap", 0) / 1e7,
        "pe_ratio": info.get("trailingPE"),
        "pb_ratio": info.get("priceToBook"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "1y_return_percent": calculate_1y_return(hist),
        "avg_volume": info.get("averageVolume"),
    }
```

---

## 14. Cross-Document Verification (`cross_verifier.py`)

Triangulate data across documents to catch inconsistencies:

```python
async def cross_verify(case_id: str) -> list[CrossCheckResult]:
    """
    Compare extracted data across documents for the same case.
    Flag discrepancies.
    """
    checks = []

    # 1. LCR consistency: ALM doc vs Financial Results Annexure
    alm_lcr = get_extraction(case_id, "ALM", "lcr_ratio")
    fin_lcr = get_extraction(case_id, "Portfolio_Performance", "lcr_percent")
    if alm_lcr and fin_lcr:
        diff = abs(alm_lcr.value_numeric - fin_lcr.value_numeric)
        checks.append(CrossCheckResult(
            check_name="LCR Consistency",
            doc_a="ALM Disclosure",
            doc_b="Financial Results",
            value_a=f"{alm_lcr.value_numeric}%",
            value_b=f"{fin_lcr.value_numeric}%",
            discrepancy=diff,
            status="match" if diff < 1.0 else "mismatch",
            note=f"LCR values differ by {diff:.2f}pp" if diff >= 1.0 else "Consistent"
        ))

    # 2. Net worth consistency: Financial Results vs Annual Report
    # 3. Total borrowing: Borrowing Profile rated amount vs Balance Sheet total borrowing
    # 4. Promoter holding: Shareholding Pattern vs Annual Report company overview
    # 5. Rating: Borrowing Profile rating vs any rating mentioned in Annual Report
    # 6. Branch count: Annual Report figure vs any other mention
    # 7. Employee count consistency

    return checks
```

---

## 15. Five Cs Credit Scoring Framework (`five_cs_scorer.py`)

### Scoring Logic

Each C is scored 0-100 with explicit reasoning:

```python
async def score_five_cs(case_id: str) -> FiveCsScore:
    """
    Score entity on Five Cs of Credit using extracted data,
    research findings, and analyst notes.
    """
    extractions = get_all_extractions(case_id)
    research = get_research_items(case_id)
    notes = get_analyst_notes(case_id)

    # CHARACTER (0-100): Promoter quality, governance, management integrity
    character = score_character(
        promoter_holding=extractions.get("promoter_holding_percent"),
        shares_pledged=extractions.get("shares_pledged_percent"),
        ndu_shares=extractions.get("shares_under_ndu"),
        rating_action=extractions.get("rating_action"),
        promoter_news=[r for r in research if r.category == "promoter"],
        legal_findings=[r for r in research if r.category == "legal"],
        governance_notes=[n for n in notes if n.affected_c == "Character"],
        board_composition=extractions.get("board_composition"),
    )

    # CAPACITY (0-100): Revenue trends, profitability, operating efficiency
    capacity = score_capacity(
        revenue=extractions.get("total_revenue_operations"),
        pat=extractions.get("profit_after_tax"),
        nim=extractions.get("nim_percent"),
        eps=extractions.get("eps_basic"),
        net_profit_margin=extractions.get("net_profit_margin"),
        gnpa=extractions.get("gnpa_percent"),
        nnpa=extractions.get("nnpa_percent"),
        capacity_notes=[n for n in notes if n.affected_c == "Capacity"],
    )

    # CAPITAL (0-100): Net worth, CRAR, leverage adequacy
    capital = score_capital(
        net_worth=extractions.get("net_worth_lakhs"),
        crar=extractions.get("crar_percent"),
        debt_equity=extractions.get("debt_equity_ratio"),
        total_debts_to_assets=extractions.get("total_debts_to_total_assets"),
    )

    # COLLATERAL (0-100): Security cover, asset quality
    collateral = score_collateral(
        gnpa=extractions.get("gnpa_percent"),
        nnpa=extractions.get("nnpa_percent"),
        provision_coverage=extractions.get("provision_coverage_ratio"),
        security_cover_ratio=extractions.get("security_cover_ratio"),  # From NCD disclosure
        tangible_security=extractions.get("tangible_security_coverage"),
    )

    # CONDITIONS (0-100): Sector outlook, regulatory environment, macro
    conditions = score_conditions(
        lcr=extractions.get("lcr_ratio") or extractions.get("lcr_percent"),
        sector_research=[r for r in research if r.category == "sector"],
        regulatory_research=[r for r in research if r.category == "regulatory"],
        market_data=get_market_data(extractions.get("nse_symbol")),
        conditions_notes=[n for n in notes if n.affected_c == "Conditions"],
    )

    # OVERALL weighted score
    weights = {"character": 0.20, "capacity": 0.25, "capital": 0.25, "collateral": 0.15, "conditions": 0.15}
    overall = (
        character.score * weights["character"] +
        capacity.score * weights["capacity"] +
        capital.score * weights["capital"] +
        collateral.score * weights["collateral"] +
        conditions.score * weights["conditions"]
    )

    # Map to risk grade
    risk_grade = score_to_grade(overall)

    return FiveCsScore(
        character=character,
        capacity=capacity,
        capital=capital,
        collateral=collateral,
        conditions=conditions,
        overall_score=round(overall),
        risk_grade=risk_grade,
    )
```

### Score-to-Grade Mapping

```python
def score_to_grade(score: float) -> str:
    if score >= 85: return "AAA"
    if score >= 75: return "AA"
    if score >= 65: return "A"
    if score >= 55: return "BBB"
    if score >= 45: return "BB"
    if score >= 35: return "B"
    if score >= 25: return "C"
    return "D"
```

### Sub-Score Computation Example (Character)

```python
def score_character(
    promoter_holding, shares_pledged, ndu_shares, rating_action,
    promoter_news, legal_findings, governance_notes, board_composition
) -> CScore:
    score = 70  # Base score
    factors = []

    # Promoter holding strength
    if promoter_holding and promoter_holding > 50:
        score += 5
        factors.append({"signal": "Strong promoter holding", "impact": +5,
                        "evidence": f"Promoter holds {promoter_holding}%"})
    elif promoter_holding and promoter_holding < 20:
        score -= 10
        factors.append({"signal": "Low promoter holding", "impact": -10,
                        "evidence": f"Promoter holds only {promoter_holding}%"})

    # Pledge/NDU risk
    if shares_pledged and shares_pledged > 20:
        score -= 15
        factors.append({"signal": "High share pledge", "impact": -15,
                        "evidence": f"{shares_pledged}% of promoter shares pledged"})

    # Rating action
    if rating_action and "upgrade" in rating_action.lower():
        score += 10
        factors.append({"signal": "Recent rating upgrade", "impact": +10,
                        "evidence": f"Rating action: {rating_action}"})
    elif rating_action and "downgrade" in rating_action.lower():
        score -= 20
        factors.append({"signal": "Recent rating downgrade", "impact": -20,
                        "evidence": f"Rating action: {rating_action}"})

    # Negative news
    severe_news = [n for n in promoter_news if n.severity in ("high", "critical")]
    if severe_news:
        score -= len(severe_news) * 5
        factors.append({"signal": f"{len(severe_news)} severe promoter news items",
                        "impact": -len(severe_news) * 5,
                        "evidence": "; ".join([n.title for n in severe_news])})

    # Legal/litigation
    legal_severe = [l for l in legal_findings if l.severity in ("high", "critical")]
    if legal_severe:
        score -= len(legal_severe) * 8
        factors.append({"signal": f"{len(legal_severe)} high-severity legal findings",
                        "impact": -len(legal_severe) * 8,
                        "evidence": "; ".join([l.title for l in legal_severe])})

    # Analyst notes
    for note in governance_notes:
        score += note.risk_adjustment
        factors.append({"signal": f"Analyst note: {note.note_type}",
                        "impact": note.risk_adjustment,
                        "evidence": note.content[:200]})

    score = max(0, min(100, score))
    return CScore(
        c_name="Character",
        score=score,
        reasoning=json.dumps({"factors": factors}),
        summary=generate_character_summary(score, factors)
    )
```

---

## 16. Recommendation Engine (`recommendation.py`)

```python
async def generate_recommendation(case_id: str) -> Recommendation:
    """Generate final credit recommendation with explainable reasoning."""
    case = get_case(case_id)
    five_cs = get_five_cs_score(case_id)
    cross_checks = get_cross_verification(case_id)
    research = get_research_items(case_id)
    notes = get_analyst_notes(case_id)

    # Decision logic
    if five_cs.overall_score >= 65:
        decision = "approve"
    elif five_cs.overall_score >= 45:
        decision = "conditional_approve"
    else:
        decision = "reject"

    # Hard stops (override any score)
    hard_stop_reasons = check_hard_stops(five_cs, research, cross_checks)
    if hard_stop_reasons:
        decision = "reject"

    # Recommended amount (for approve/conditional)
    if decision != "reject":
        max_amount = calculate_eligible_limit(case, five_cs)
        recommended_amount = min(case.loan_amount_crore, max_amount)
    else:
        recommended_amount = 0

    # Recommended rate
    base_rate = 9.0  # Base lending rate
    risk_premium = calculate_risk_premium(five_cs.risk_grade)
    recommended_rate = base_rate + risk_premium

    # Generate reasoning narrative using Claude
    reasoning = await generate_reasoning_narrative(
        case, five_cs, decision, research, notes, cross_checks
    )

    # Generate conditions and covenants
    conditions = generate_conditions(case, five_cs, research)

    return Recommendation(
        decision=decision,
        recommended_amount_crore=recommended_amount,
        recommended_rate_percent=recommended_rate,
        recommended_tenure_months=case.loan_tenure_months,
        risk_grade=five_cs.risk_grade,
        overall_score=five_cs.overall_score,
        decision_reasoning=reasoning,
        key_strengths=extract_strengths(five_cs),
        key_risks=extract_risks(five_cs, research),
        hard_stop_reasons=hard_stop_reasons,
        conditions_precedent=conditions["precedent"],
        conditions_subsequent=conditions["subsequent"],
        monitoring_covenants=conditions["monitoring"],
    )
```

### Hard Stop Checks

```python
def check_hard_stops(five_cs, research, cross_checks) -> list[str]:
    """Policy-level hard stops that override model scores."""
    reasons = []

    # CRAR below RBI minimum (15% for NBFCs)
    crar = get_extraction_value("crar_percent")
    if crar and crar < 15:
        reasons.append(f"CRAR at {crar}% is below RBI minimum of 15%")

    # Active NCLT/IBC proceedings
    ibc = [r for r in research if "NCLT" in r.title or "IBC" in r.title or "CIRP" in r.title]
    if any(r.severity == "critical" for r in ibc):
        reasons.append("Active insolvency/CIRP proceedings detected")

    # Fraud/willful defaulter flags
    fraud = [r for r in research if "fraud" in r.title.lower() or "willful default" in r.title.lower()]
    if fraud:
        reasons.append("Fraud or willful default allegations found")

    # Major cross-doc discrepancies
    critical_mismatches = [c for c in cross_checks if c.status == "mismatch" and c.discrepancy > 10]
    if critical_mismatches:
        reasons.append(f"Critical data discrepancies found in {len(critical_mismatches)} cross-checks")

    return reasons
```

---

## 17. SWOT Generator (`swot_generator.py`)

```python
async def generate_swot(case_id: str) -> dict:
    """Generate SWOT analysis using Claude with all available data."""
    case = get_case(case_id)
    five_cs = get_five_cs_score(case_id)
    research = get_research_items(case_id)
    extractions = get_all_extractions(case_id)

    prompt = f"""Generate a comprehensive SWOT analysis for {case.company_name}
based on the following data. Each point must cite specific evidence.

Company: {case.company_name}
Sector: {case.sector}

Financial Data:
{format_extractions_for_prompt(extractions)}

Five Cs Scores:
- Character: {five_cs.character.score}/100
- Capacity: {five_cs.capacity.score}/100
- Capital: {five_cs.capital.score}/100
- Collateral: {five_cs.collateral.score}/100
- Conditions: {five_cs.conditions.score}/100

Secondary Research Findings:
{format_research_for_prompt(research)}

Return JSON:
{{
  "strengths": [
    {{"point": "...", "evidence": "...", "source": "..."}}
  ],
  "weaknesses": [...],
  "opportunities": [...],
  "threats": [...]
}}

Each category should have 3-5 points. Every point must reference specific data."""

    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    return parse_swot_response(response.content[0].text)
```

---

## 18. CAM Generator (`cam_generator.py`)

### CAM Structure

The Credit Appraisal Memo follows this structure:

```python
CAM_SECTIONS = [
    {
        "id": "executive_summary",
        "title": "Executive Summary",
        "description": "1-page summary: entity, loan request, recommendation, key rationale"
    },
    {
        "id": "company_background",
        "title": "Company Background & Promoter Profile",
        "description": "History, promoter details, management team, governance"
    },
    {
        "id": "industry_analysis",
        "title": "Industry & Sector Analysis",
        "description": "Sector outlook, competitive landscape, regulatory environment"
    },
    {
        "id": "financial_analysis",
        "title": "Financial Analysis",
        "description": "P&L analysis, balance sheet, key ratios, trend analysis"
    },
    {
        "id": "asset_quality",
        "title": "Asset Quality & Portfolio Analysis",
        "description": "NPA trends, provision coverage, portfolio composition, collection efficiency"
    },
    {
        "id": "liquidity_alm",
        "title": "Liquidity & ALM Position",
        "description": "LCR analysis, ALM maturity profile, funding sources"
    },
    {
        "id": "borrowing_profile",
        "title": "Borrowing Profile & Credit Rating",
        "description": "Existing borrowings, lender-wise breakdown, rating history"
    },
    {
        "id": "five_cs_assessment",
        "title": "Five Cs Credit Assessment",
        "description": "Detailed scoring on Character, Capacity, Capital, Collateral, Conditions"
    },
    {
        "id": "secondary_research",
        "title": "Secondary Research & External Intelligence",
        "description": "News, legal, regulatory findings with impact assessment"
    },
    {
        "id": "cross_verification",
        "title": "Cross-Document Verification",
        "description": "Data consistency checks across submitted documents"
    },
    {
        "id": "risk_matrix",
        "title": "Risk Matrix",
        "description": "Key risks with likelihood, impact, and mitigation"
    },
    {
        "id": "swot",
        "title": "SWOT Analysis",
        "description": "Strengths, Weaknesses, Opportunities, Threats"
    },
    {
        "id": "recommendation",
        "title": "Recommendation",
        "description": "Decision, amount, rate, tenure, conditions, covenants, monitoring"
    },
    {
        "id": "appendix",
        "title": "Appendix: Source Provenance",
        "description": "Document-level source references with page numbers for all cited data"
    }
]
```

### Generation Approach

Each section is generated independently by Claude, grounded in extracted data and research:

```python
async def generate_cam_section(section_id: str, case_data: dict) -> CamSection:
    """Generate one section of the CAM."""
    section_spec = [s for s in CAM_SECTIONS if s["id"] == section_id][0]

    prompt = f"""Write the "{section_spec['title']}" section of a Credit Appraisal Memo
for {case_data['company_name']}.

Section purpose: {section_spec['description']}

Use ONLY the data provided below. Mark any claim with [EVIDENCE: source_doc, page_X] references.

Available data:
{json.dumps(case_data['relevant_data'], indent=2)}

Write in professional credit analyst tone. Be specific with numbers.
Output in markdown format."""

    # Generate with Claude
    response = await call_claude(prompt)

    return CamSection(
        section_id=section_id,
        title=section_spec["title"],
        content_markdown=response,
        evidence_refs=extract_evidence_refs(response)
    )
```

---

## 19. Exporter (`exporter.py`)

### DOCX Export

```python
from docx import Document
from docx.shared import Inches, Pt, RGBColor

def export_cam_docx(case: Case, sections: list[CamSection], output_path: str):
    """Generate a professional Word document CAM."""
    doc = Document()

    # Title page
    doc.add_heading("Credit Appraisal Memo", level=0)
    doc.add_heading(case.company_name, level=1)
    doc.add_paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}")
    doc.add_paragraph(f"CIN: {case.cin}")
    doc.add_paragraph(f"Loan Request: Rs. {case.loan_amount_crore} crore")
    doc.add_page_break()

    # Table of contents placeholder
    doc.add_heading("Table of Contents", level=1)
    for section in sections:
        doc.add_paragraph(section.title, style="List Number")
    doc.add_page_break()

    # Sections
    for section in sections:
        doc.add_heading(section.title, level=1)
        # Parse markdown and add formatted content
        add_markdown_to_docx(doc, section.content_markdown)
        doc.add_page_break()

    doc.save(output_path)
```

---

## 20. Frontend Implementation Notes

### Key UI Patterns

1. **Stage Stepper**: A persistent header showing the 4 stages (Onboarding → Upload → Extraction → Report) with current stage highlighted. Navigation between stages only allowed when prerequisites are met.

2. **PDF Viewer with Bbox Overlay**: The extraction page shows a split view:
   - Left: PDF page rendered as image with SVG bbox rectangles overlaid
   - Right: Editable data table showing extracted key-value pairs
   - Linking: Hover on a table row → highlight bbox on PDF. Click bbox → scroll to table row.

3. **Classification Cards**: After upload, show each document as a card with auto-detected category, confidence score, and approve/edit/deny buttons.

4. **Schema Editor**: Table-based editor where users can add/remove/edit extraction fields. Changes immediately saved and available for re-extraction.

5. **Five Cs Radar Chart**: Spider/radar chart showing 5 axes, one for each C. Clicking any axis drills into the detailed factors for that C.

6. **Recommendation Panel**: Traffic-light display (green/yellow/red) with the decision, followed by collapsible sections for reasoning, conditions, and covenants.

### API Client Pattern

```typescript
// frontend/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function createCase(data: CreateCaseInput): Promise<Case> {
  const res = await fetch(`${API_BASE}/api/cases`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function uploadDocuments(caseId: string, files: File[]): Promise<Document[]> {
  const formData = new FormData();
  files.forEach((f) => formData.append("files", f));
  const res = await fetch(`${API_BASE}/api/cases/${caseId}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}

// ... similar for all endpoints
```

---

## 21. Environment Variables

### Backend (`.env`)
```
# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
DATABASE_URL=postgresql://...

# File storage
STORAGE_BUCKET=intelli-credit-docs

# AI/ML APIs
ANTHROPIC_API_KEY=sk-ant-...
LANDING_AI_API_KEY=...

# Research
TAVILY_API_KEY=tvly-...

# App
APP_ENV=development
CORS_ORIGINS=http://localhost:3000
```

### Frontend (`.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 22. Build Order (Recommended Sequence)

Build in this order — each step produces a demoable increment:

### Phase 1: Foundation (Day 1)
1. Backend: FastAPI scaffold, database models, health endpoint
2. Frontend: Next.js scaffold, layout, sidebar, stage stepper
3. Entity onboarding form (Stage 1) — both frontend and backend CRUD
4. Document upload endpoint + dropzone UI (Stage 2)

### Phase 2: PDF Pipeline (Day 1-2)
5. `pdf_triage.py` — page-level classification
6. `parser_pdfplumber.py` — digital PDF parsing
7. `parser_landingai.py` — LandingAI integration
8. `parser_vision.py` — Claude Vision fallback
9. `parser_router.py` — routing logic
10. `markdown_builder.py` — assemble per-document markdown
11. `classifier.py` — document auto-classification

### Phase 3: Extraction (Day 2)
12. Default extraction schemas (all 5 document types)
13. `extractor.py` — schema-guided extraction with Claude
14. Extraction API endpoints
15. Frontend: classification review cards
16. Frontend: PDF viewer with bbox overlay
17. Frontend: extracted data table (editable)
18. Frontend: schema editor

### Phase 4: Analysis (Day 2-3)
19. `research_agent.py` — Tavily + yfinance integration
20. `cross_verifier.py` — cross-document checks
21. `five_cs_scorer.py` — scoring framework
22. `recommendation.py` — decision logic
23. `swot_generator.py` — SWOT via Claude
24. Frontend: research results view
25. Frontend: analyst notes input
26. Frontend: Five Cs radar + breakdown
27. Frontend: recommendation panel

### Phase 5: Report & Polish (Day 3)
28. `cam_generator.py` — section-by-section CAM generation
29. `exporter.py` — DOCX + PDF export
30. Frontend: CAM preview + download
31. End-to-end testing with sample data
32. Deploy frontend (Vercel) + backend (Railway)
33. Polish UI, fix edge cases

---

## 23. Sample Test Data

Located at `claude_data/` — use for end-to-end testing:

**Aavas Financiers Limited** (primary test entity):
- `Aavas_Financiers/ALM/Disclosure_on_Liquidity_Coverage_Ratio_Q3_FY26.pdf` (2 pages, digital)
- `Aavas_Financiers/Shareholding_Pattern/Shareholding_Pattern_Q3_FY26.pdf` (8 pages, web-generated)
- `Aavas_Financiers/Borrowing_Profile/Credit_Rating_Reaffirmation_CARE_2024-12-13.pdf` (10 pages, compound doc)
- `Aavas_Financiers/Portfolio_Cuts_Performance/Financial_Result_Q3_FY26.pdf` (10 pages, SCANNED)
- `Aavas_Financiers/Annual_Report/Annual_Report_FY2024-25.pdf` (321 pages, 7.8MB)

**Home First Finance** (secondary test entity):
- Same 5 document types available for comparison testing

### Expected Extraction Results (Aavas — for validation)

| Field | Expected Value | Source |
|---|---|---|
| LCR Ratio | 151.7% | ALM, page 1 |
| HQLA Total | Rs. 23,203 lakhs | ALM, page 1 |
| Promoter Holding | 48.95% | Shareholding, Table I |
| Promoter Name | Aquilo House Pte. Ltd. | Shareholding, Table II |
| FPI Holding | ~24.72% | Shareholding, Table III |
| Credit Rating | CARE AA; Stable | Borrowing Profile, page 1 |
| Total Rated Facilities | Rs. 9,662 crore | Borrowing Profile, Annexure 1 |
| Q3 FY26 Revenue | Rs. 67,419.52 lakhs | Financial Results, page 4 |
| Q3 FY26 PAT | Rs. 17,004.57 lakhs | Financial Results, page 4 |
| D/E Ratio | 3.07 | Financial Results, Annexure A |
| GNPA | 1.19% | Financial Results, Annexure A |
| NNPA | 0.79% | Financial Results, Annexure A |
| CRAR | 46.39% | Financial Results, Annexure A |
| Net Worth | Rs. 4,85,813.55 lakhs | Financial Results, Annexure A |
| AUM | Rs. 20,420 crore | Annual Report, page 5 |

---

## 24. Deployment

### Backend (Railway)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/pyproject.toml backend/
RUN pip install -e backend/
COPY backend/ backend/
EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend (Vercel)
- Connect GitHub repo, set root directory to `frontend/`
- Set `NEXT_PUBLIC_API_URL` environment variable to Railway backend URL
- Deploy

---

## 25. What "Done" Looks Like

A judge should be able to:

1. Open the web app
2. Fill in entity details for Aavas Financiers
3. Upload the 5 sample PDFs
4. See auto-classification results and approve them
5. View extraction results with bounding box overlays on the source PDFs
6. Optionally modify the extraction schema and re-extract
7. View secondary research findings (news, regulatory, market data)
8. Add analyst notes (e.g., "Management change from Kedaara to CVC Capital Partners in 2025 — monitor governance transition")
9. See Five Cs scoring breakdown with explicit reasoning chains
10. See cross-document verification results
11. View the final recommendation (approve/conditional/reject) with full reasoning
12. View SWOT analysis
13. Download a professional CAM document (Word/PDF)
14. Click on any data point in the report and trace it back to the exact page and bounding box of the source PDF

That's the complete specification. Build it.
