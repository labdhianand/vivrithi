# V1 Reference Wrap

Assessment date: March 10, 2026

## Purpose

This document freezes the current repository as a reference baseline for a rebuild. It does not propose implementing V2 inside the current package layout. The goal is to preserve product intent, reusable domain logic, and demo assets while avoiding a direct carry-forward of the current runtime structure.

## Executive Read

The repository is a working prototype, not a clean package foundation.

- The backend in `apps/api` is the real center of gravity.
- The frontend in `apps/web` is a thin workbench around that backend.
- Root-level docs describe a larger, cleaner monorepo contract than the package tooling currently enforces.
- The codebase has already started to drift at the contract level: runtime behavior, tests, and documentation no longer align perfectly.
- The correct rebuild posture is `archive for reference, then start V2 from a new package skeleton`.

## Current Package Map

### Runtime packages

- `apps/api`
  - FastAPI backend package with the orchestration flow, document extraction, research, reconciliation, ML inference, policy, structuring, CAM generation, and export.
  - Python package manifest exists in `apps/api/pyproject.toml`.
- `apps/web`
  - Next.js frontend package used as a dashboard and workbench.
  - Node package manifest exists in `apps/web/package.json`.

### Non-package but important project areas

- `data`
  - Demo pack, raw labels, training datasets, model artifacts, exports, and the SQLite database.
- `scripts`
  - Data acquisition, training dataset generation, demo seeding, smoke tests.
- `docs`
  - Product, architecture, operations, demo, and provenance documents.
- Root files
  - `README.md`, `PRD.md`, `IMPLEMENTATION_CHECKLIST.md`, `.env.example`, `docker-compose.yml`, `Makefile`.

### Missing package-level structure

- No root `package.json`
- No `pnpm-workspace.yaml`
- No `turbo.json`
- No `nx.json`
- No root Python workspace packaging

This means the repository behaves like two app directories plus supporting assets, not like a properly governed monorepo.

## Actual Runtime Surface

### Backend

The backend contains the majority of product behavior.

- Approximate code size in `apps/api/app`: 6.8k lines
- Main entrypoint: `apps/api/app/main.py`
- Main orchestration concentration: `apps/api/app/services/orchestrator.py`
- Important service clusters:
  - OCR and parsing
  - research
  - reconciliation
  - feature building
  - ML train/infer/explain
  - policy and structuring
  - CAM generation and export

Observation: the package is functional, but too much product logic is centralized in the orchestration and services layer to be a clean baseline for a rebuild.

### Frontend

The frontend is much smaller.

- Approximate code size in `apps/web`: 1.8k lines excluding generated artifacts
- Key routes:
  - dashboard
  - cases workbench
  - research
  - risk
  - CAM
  - settings
- API access is concentrated in `apps/web/lib/api.ts`

Observation: the UI is a control console, not yet a strong package boundary or domain model source.

## Documentation vs Code Alignment

The repository claims a stable monorepo architecture in `README.md` and `docs/architecture.md`, but the implementation is more prototype-like.

Examples:

- Root docs present a monorepo with strong service boundaries, but no root workspace tooling exists.
- The backend claims LangGraph-first controlled orchestration, but sequential fallback logic still exists in code.
- The review/manual approval path changed the meaning of decisions, but tests still assume only terminal credit decisions.

This is not fatal for a prototype. It is a bad starting point for V2 packaging.

## Validation Snapshot

Validation run performed on March 10, 2026:

- Backend tests: `51 passed, 1 failed`
- Failing test: `apps/api/tests/integration/test_health_and_demo.py::test_demo_seed_and_run_endpoint`
- Cause of drift:
  - test expects `approve | conditional_approve | reject`
  - orchestrator can now return `manual_review` when the model abstains

This matters because it shows that workflow semantics are already ahead of the package contract.

## Reuse Matrix

### Preserve as reference only

- `PRD.md`
- `README.md`
- `docs/architecture.md`
- `docs/api_spec.md`
- `docs/demo_walkthrough.md`
- `docs/ml_provenance.md`
- `IMPLEMENTATION_CHECKLIST.md`
- `data/demo_pack_upl`
- selected `data/raw` and `data/processed` artifacts that explain training provenance

### Reuse as domain contract inputs

- `apps/api/app/models/schemas.py`
- `apps/api/app/models/entities.py`
- document type vocabulary in `apps/api/app/api/routes/cases.py`
- decision and review-state vocabulary from the orchestrator and route layer

These are useful for extracting the domain model, but should be rewritten into cleaner V2 modules rather than copied verbatim.

### Mine for logic, do not carry forward structurally

- `apps/api/app/services/reconciliation.py`
- `apps/api/app/services/feature_builder.py`
- `apps/api/app/services/policy_engine.py`
- `apps/api/app/services/structuring_engine.py`
- `apps/api/app/services/exporter.py`

These files contain useful business logic and heuristics, but the current service breakup is not a good architecture template.

### Do not use as V2 foundation

- generated exports under `data/exports`
- model checkpoints under `data/checkpoints`
- local database `data/intelli_credit.db`
- generated runtime state such as `.next`, `node_modules`, `.pytest_cache`, `.ruff_cache`
- the current orchestration package layout

## Why V2 Should Not Start In-Place

1. The repository has no meaningful git baseline yet.
   The git root is above this project, and the current `main` branch has no commits.

2. Runtime artifacts and source are co-located.
   This is manageable for a prototype, but it blurs package boundaries and makes clean versioning harder.

3. Product behavior is concentrated in large service files.
   That usually produces fast prototypes and slow rebuilds unless the next version starts from explicit domain boundaries.

4. Documentation, tests, and behavior are already drifting.
   Rebuilding inside the same structure increases the chance of accidental carry-forward of V1 assumptions.

## Freeze Boundary Recommendation

Treat this repository as `V1 reference`.

Recommended freeze actions before any V2 implementation:

1. Keep the current tree intact.
2. Do not refactor V1 toward V2 inside the same runtime folders.
3. Create a dedicated archive boundary such as:
   - a filesystem copy like `vivriti-v1-reference`
   - or a git repository initialized specifically for this project with a first commit named `v1-reference-wrap`
4. Exclude generated runtime directories from that baseline snapshot where practical:
   - `apps/web/.next`
   - `apps/web/node_modules`
   - `apps/api/.pytest_cache`
   - `apps/api/.ruff_cache`
5. Keep demo, provenance, and selected data assets that justify the product story.

## Recommended V2 Starting Principle

Start V2 from package boundaries, not from routes or UI pages.

The first V2 design unit should be:

- domain model
- decision state machine
- document contract
- evidence contract
- workflow stages
- external adapter boundary

Only after those are stable should new runtime packages be created.

## Non-Build Next Step

The next correct step is not coding. It is to produce a V2 package map and migration boundary document based on this wrap:

- what packages exist in V2
- what moves as concepts
- what is archived
- what gets rewritten from zero

That should happen before any rebuild work starts.
