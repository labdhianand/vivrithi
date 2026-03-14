# Intelli-Credit Copilot Architecture

## 1. System Topology

- Frontend: Next.js portal (`apps/web`)
- Backend: FastAPI orchestration and decision engine (`apps/api`)
- Workflow engine: LangGraph state graph (default execution path)
- Persistence: SQLite (`data/intelli_credit.db`)
- Vector retrieval: Qdrant (local container or Qdrant Cloud free)
- Optional warehouse compute + sink: Databricks Free Edition SQL API

## 2. Core Workflow

1. Case creation and document intake
2. OCR routing
   - Sarvam as primary
   - LandingAI fallback when confidence is below threshold
3. Document-type extraction
   - annual report
   - bank statement
   - GST return
   - rating report
   - board minutes
   - shareholding pattern
   - CIBIL commercial
4. Research collection
   - Tavily discovery
   - Firecrawl normalization
5. India reconciliation checks
   - GSTR-2A/2B vs 3B
   - GST vs bank mismatch
   - circularity heuristics
6. Feature construction
7. ML inference and explainability
8. Policy overlay and decision
9. Structuring: limit + spread + covenants
10. CAM drafting and export
11. Audit and override capture
12. Review Agent evidence-coverage validation gate

## 3. Trust and Control Plane

- Hard-stop policy layer independent of model output
- Evidence metadata tracked per claim (Green/Amber/Red)
- Every major step emits immutable audit events
- Manual override captured with reviewer, timestamp, rationale
- Counterfactual recommendations generated for remediation
- Manual review hold path when coverage checks fail (human-in-loop)

## 4. Free-tier service adapters

- Tavily: `app/services/tavily_client.py`
- Firecrawl: `app/services/firecrawl_client.py`
- OpenRouter: `app/services/openrouter_client.py`
- Sarvam: `app/services/sarvam_client.py`
- LandingAI: `app/services/landingai_client.py`
- Qdrant: `app/services/qdrant_store.py`
- Databricks: `app/services/databricks_client.py`
- LangGraph orchestration: `app/services/orchestrator.py`

All are optional and fail-safe. If a key is missing, the workflow still runs with transparent fallback behavior.
