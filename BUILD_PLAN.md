# Intelli-Credit Build Plan

## Objective

Deliver a hosted underwriting workbench that satisfies the hackathon flow end-to-end:

1. Entity onboarding
2. Multi-format document upload
3. Auto-classification and schema extraction
4. Secondary research and due diligence integration
5. Explainable recommendation
6. Downloadable CAM with source-backed evidence

This build plan reflects the implemented architecture. The earlier Mistral-first plan is obsolete and should not be used.

## Architecture

### Application Topology

```text
Public User
  -> Frontend (public URL, no VPN)
  -> Backend API (public URL, no VPN)
  -> SQLite / persistent volume
  -> Tavily and public web sources
  -> Remote Docling GPU worker over private network

Backend API
  -> WireGuard-connected route
  -> SSH to moslab@10.2.36.58
  -> Docling on A100 80GB
```

### Parsing Strategy

- All uploaded PDFs and spreadsheets route through stock Docling.
- PDFs use the remote GPU host with CUDA-enabled Docling.
- Long PDFs use intra-document parallelism through Docling batch controls:
  - `page_batch_size`
  - `layout_batch_size`
  - `ocr_batch_size`
- Multi-document uploads use case-level parallel processing with bounded concurrency.
- No Mistral path is part of the plan.

### Evidence Strategy

- Extracted fields retain source page and bounding-box provenance.
- The extraction UI can jump to the originating page and overlay the box.
- Five Cs factors and CAM sections now carry evidence references so judges can trace claims back to source documents.

## Current State

### Implemented

- Public-facing frontend and backend application flow
- Case onboarding and CRUD
- Upload support for:
  - `pdf`
  - `xlsx`
  - `xls`
  - `csv`
- Remote Docling backend selection as the default ingestion path
- Remote Docling GPU bootstrap and execution over SSH
- Parallel case-level document processing endpoint
- Intra-document batching for large PDFs on the GPU host
- Bounding-box-aware extraction persistence
- Extraction viewer with page overlay support
- Evidence references carried into:
  - Five Cs factors
  - Recommendation signals
  - CAM sections
- CAM DOCX and PDF generation
- Secondary research and explainable recommendation pipeline

### Explicitly Not Included

- Demo seeding or fake precomputed walkthroughs
- Mistral OCR
- FastFork Docling path

## Required Build Tracks

### Track 1: Remote Docling GPU Ingestion

Status: `implemented`

Scope:

- Route all uploaded documents through `docling_remote`
- Use `ThreadedStandardPdfPipeline` on CUDA for PDFs
- Use Docling default conversion for spreadsheets
- Persist per-page markdown, text, tables, and boxes
- Keep case-level parallel processing bounded to avoid GPU starvation

Key files:

- `backend/app/services/runtime/docling_remote.py`
- `backend/app/services/runtime/docling_gpu_worker.py`
- `backend/app/services/document_pipeline.py`
- `backend/app/api/documents.py`

### Track 2: Analyst-Facing Evidence Provenance

Status: `implemented`

Scope:

- Preserve extraction page numbers and normalized boxes
- Allow extraction-page deep linking from analysis/report surfaces
- Show provenance chips in the analysis and report UI

Key files:

- `backend/app/services/evidence_refs.py`
- `backend/app/services/five_cs_scorer.py`
- `backend/app/services/recommendation.py`
- `backend/app/services/cam_generator.py`
- `frontend/components/evidence/evidence-pills.tsx`

### Track 3: Recommendation and CAM

Status: `already present, now provenance-aware`

Scope:

- Five Cs scoring
- Cross-verification checks
- Secondary research
- Recommendation logic
- CAM preview and export

Risk:

- Quality is only as good as upstream classification and extraction accuracy

### Track 4: Public Hosting with WireGuard-Only GPU

Status: `architecture defined, deployment pending`

Recommended hackathon deployment:

1. Host the backend on a public VM or VPS that can also join WireGuard.
2. Expose the backend publicly with Caddy or Nginx over HTTPS.
3. Keep the GPU host private on WireGuard only.
4. Let the backend reach `10.2.36.58` over WireGuard and run remote Docling over SSH.
5. Host the frontend either:
   - on the same public VM, or
   - on Vercel pointing to the public backend URL

Why this is the right hackathon shape:

- users access the product without VPN
- the GPU remains private
- the backend can still orchestrate the GPU directly
- this avoids building a queue/agent system unless time demands it

Fallback architecture if managed backend hosting is mandatory:

- Public backend writes jobs to a cloud queue or database
- A small WireGuard-connected worker polls jobs over outbound HTTPS
- The worker runs Docling on `moslabserver` and uploads results back

That pull-worker architecture is safer for production, but slower to build for the hackathon.

### Track 5: OneDrive Validation

Status: `in progress and repeatable`

Validation dataset:

- `OneDrive_1_14-3-2026/ALM`
- `OneDrive_1_14-3-2026/BP`
- `OneDrive_1_14-3-2026/PC`
- `OneDrive_1_14-3-2026/SHP`
- `OneDrive_1_14-3-2026/annual`

Validation goal:

- prove that the pipeline can classify, extract, analyze, and generate a CAM on the real challenge corpus
- measure both per-document latency and full-case latency
- identify where classification heuristics still need corpus tuning

## Operational Decisions

### Parallelism Defaults

- Document-level concurrency: `4`
- Remote PDF batch sizes:
  - `page_batch_size=128`
  - `layout_batch_size=128`
  - `ocr_batch_size=96`
  - `table_batch_size=4`

These defaults are tuned for the A100 80GB target and should be verified under live load with `nvidia-smi`.

### Classification Policy

- Classification is still analyst-in-the-loop.
- The system auto-classifies first.
- The user can approve, reject, or correct the category.
- Generic challenge file names require stronger content heuristics than normal business filenames.

### Report Policy

- CAM generation should run only after document processing and analysis complete.
- Every major analytical section should include provenance references where available.

## Known Risks

### Risk 1: Generic Hackathon Filenames

Files such as `file 01.xlsx` create weaker filename signals, so classification must rely on content more heavily than normal uploads.

Mitigation:

- strengthen content heuristics against the OneDrive corpus
- keep user approval in the loop

### Risk 2: Annual Reports with Embedded ALM Disclosures

Annual reports can contain LCR and liquidity tables, which can bias heuristics toward ALM.

Mitigation:

- weight integrated-report and statutory-report markers more strongly
- reduce raw page-count bias from table-heavy documents

### Risk 3: Public Hosting vs Private GPU Connectivity

A managed backend that cannot join WireGuard will not be able to reach the GPU host directly.

Mitigation:

- prefer a public VM backend that is also on WireGuard
- keep the GPU private

## Verification Checklist

- Upload all supported document formats from the browser
- Process all documents in parallel from the case screen
- Confirm Docling GPU execution on `10.2.36.58`
- Verify page boxes are visible in extraction review for PDF-based evidence
- Run analysis successfully with research enrichment
- Generate CAM in DOCX and PDF
- Access the full application without a VPN

## Immediate Next Steps

1. Finish tuning classification on the OneDrive corpus.
2. Re-run the full OneDrive case after the classifier changes.
3. Package deployment as a public backend plus WireGuard-connected GPU path.
4. Add a lightweight operator playbook for demo-day startup and recovery.
