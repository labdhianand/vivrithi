from __future__ import annotations

import logging
from collections import defaultdict
from decimal import Decimal

from ..models.document import Document
from ..models.extraction import Extraction
from ..models.research import ResearchItem
from .llm_text import generate_json, has_text_llm

logger = logging.getLogger(__name__)


def _active_value(extraction: Extraction) -> str | None:
    return extraction.user_edited_value or extraction.value


def _active_numeric(extraction: Extraction) -> Decimal | None:
    return extraction.value_numeric


def _pick(extractions: list[Extraction], category: str, key: str) -> Extraction | None:
    for extraction in extractions:
        if extraction.document.user_category == category and extraction.schema_field_key == key:
            return extraction
    return None


def cross_verify(case_id: str, documents: list[Document], extractions: list[Extraction]) -> list[dict]:
    grouped_by_doc = defaultdict(list)
    for extraction in extractions:
        grouped_by_doc[extraction.document_id].append(extraction)
    checks: list[dict] = []

    # 1. LCR Consistency (ALM vs Financial Results)
    alm_lcr = _pick(extractions, "ALM", "lcr_ratio")
    fin_lcr = _pick(extractions, "Portfolio_Performance", "lcr_percent")
    if alm_lcr and fin_lcr and _active_numeric(alm_lcr) is not None and _active_numeric(fin_lcr) is not None:
        diff = abs(_active_numeric(alm_lcr) - _active_numeric(fin_lcr))
        checks.append(
            {
                "case_id": case_id,
                "check_name": "LCR Consistency",
                "doc_a": "ALM Disclosure",
                "doc_b": "Financial Results",
                "value_a": _active_value(alm_lcr),
                "value_b": _active_value(fin_lcr),
                "discrepancy": diff,
                "status": "match" if diff < 1 else "mismatch",
                "note": f"LCR difference {diff:.2f} percentage points",
            }
        )

    # 2. Net Worth Consistency (Financial Results vs Annual Report)
    fin_net_worth = _pick(extractions, "Portfolio_Performance", "net_worth_lakhs")
    annual_net_worth = _pick(extractions, "Annual_Report", "net_worth_crore")
    if fin_net_worth and annual_net_worth and _active_numeric(fin_net_worth) and _active_numeric(annual_net_worth):
        annual_lakhs = _active_numeric(annual_net_worth) * Decimal("100")
        diff = abs(_active_numeric(fin_net_worth) - annual_lakhs)
        checks.append(
            {
                "case_id": case_id,
                "check_name": "Net Worth Consistency",
                "doc_a": "Financial Results",
                "doc_b": "Annual Report",
                "value_a": _active_value(fin_net_worth),
                "value_b": _active_value(annual_net_worth),
                "discrepancy": diff,
                "status": "match" if diff <= Decimal("5000") else "mismatch",
                "note": "Annual report figure converted to lakhs for comparison.",
            }
        )

    # 3. Rating Presence Check
    rating = _pick(extractions, "Borrowing_Profile", "long_term_rating")
    if rating:
        checks.append(
            {
                "case_id": case_id,
                "check_name": "Rating Presence",
                "doc_a": "Borrowing Profile",
                "doc_b": None,
                "value_a": _active_value(rating),
                "value_b": None,
                "discrepancy": Decimal("0"),
                "status": "match" if _active_value(rating) else "mismatch",
                "note": "Borrowing profile should disclose a current rating.",
            }
        )

    # 4. Revenue Consistency (Annual Report vs Financial Results)
    annual_revenue = _pick(extractions, "Annual_Report", "total_revenue_crore")
    fin_revenue = _pick(extractions, "Portfolio_Performance", "total_revenue_operations")
    if annual_revenue and fin_revenue and _active_numeric(annual_revenue) and _active_numeric(fin_revenue):
        # Financial results may be in lakhs, annual report in crore
        fin_val = _active_numeric(fin_revenue)
        annual_val = _active_numeric(annual_revenue)
        # Try to normalize: if financial results value >> annual report, it is likely in lakhs
        if fin_val > annual_val * Decimal("50"):
            fin_val = fin_val / Decimal("100")  # Convert lakhs to crore
        diff = abs(fin_val - annual_val)
        pct_diff = (diff / annual_val * 100) if annual_val else Decimal("0")
        checks.append(
            {
                "case_id": case_id,
                "check_name": "Revenue Consistency",
                "doc_a": "Annual Report",
                "doc_b": "Financial Results",
                "value_a": _active_value(annual_revenue),
                "value_b": _active_value(fin_revenue),
                "discrepancy": pct_diff,
                "status": "match" if pct_diff < Decimal("5") else "mismatch",
                "note": f"Revenue diverges by {pct_diff:.1f}% across documents.",
            }
        )

    # 5. CRAR Consistency (Financial Results vs Annual Report)
    fin_crar = _pick(extractions, "Portfolio_Performance", "crar_percent")
    annual_crar = _pick(extractions, "Annual_Report", "crar_percent")
    if not annual_crar:
        annual_crar = _pick(extractions, "Annual_Report", "capital_adequacy_ratio")
    if fin_crar and annual_crar and _active_numeric(fin_crar) and _active_numeric(annual_crar):
        diff = abs(_active_numeric(fin_crar) - _active_numeric(annual_crar))
        checks.append(
            {
                "case_id": case_id,
                "check_name": "CRAR Consistency",
                "doc_a": "Financial Results",
                "doc_b": "Annual Report",
                "value_a": _active_value(fin_crar),
                "value_b": _active_value(annual_crar),
                "discrepancy": diff,
                "status": "match" if diff < Decimal("1") else "mismatch",
                "note": f"Capital adequacy ratio differs by {diff:.2f} pp across disclosures.",
            }
        )

    # 6. GNPA Consistency across documents
    fin_gnpa = _pick(extractions, "Portfolio_Performance", "gnpa_percent")
    annual_gnpa = _pick(extractions, "Annual_Report", "gnpa_percent")
    if fin_gnpa and annual_gnpa and _active_numeric(fin_gnpa) and _active_numeric(annual_gnpa):
        diff = abs(_active_numeric(fin_gnpa) - _active_numeric(annual_gnpa))
        checks.append(
            {
                "case_id": case_id,
                "check_name": "GNPA Consistency",
                "doc_a": "Financial Results",
                "doc_b": "Annual Report",
                "value_a": _active_value(fin_gnpa),
                "value_b": _active_value(annual_gnpa),
                "discrepancy": diff,
                "status": "match" if diff < Decimal("0.5") else "mismatch",
                "note": f"Gross NPA ratio differs by {diff:.2f} pp.",
            }
        )

    # 7. Promoter Holding vs Shareholding Pattern
    sh_promoter = _pick(extractions, "Shareholding_Pattern", "promoter_holding_percent")
    annual_promoter = _pick(extractions, "Annual_Report", "promoter_holding_percent")
    if sh_promoter and annual_promoter and _active_numeric(sh_promoter) and _active_numeric(annual_promoter):
        diff = abs(_active_numeric(sh_promoter) - _active_numeric(annual_promoter))
        checks.append(
            {
                "case_id": case_id,
                "check_name": "Promoter Holding Consistency",
                "doc_a": "Shareholding Pattern",
                "doc_b": "Annual Report",
                "value_a": _active_value(sh_promoter),
                "value_b": _active_value(annual_promoter),
                "discrepancy": diff,
                "status": "match" if diff < Decimal("2") else "mismatch",
                "note": f"Promoter holding differs by {diff:.2f} pp across filings.",
            }
        )

    # 8. Debt-Equity Ratio Cross-Check
    fin_de = _pick(extractions, "Portfolio_Performance", "debt_equity_ratio")
    annual_de = _pick(extractions, "Annual_Report", "debt_equity_ratio")
    if fin_de and annual_de and _active_numeric(fin_de) and _active_numeric(annual_de):
        diff = abs(_active_numeric(fin_de) - _active_numeric(annual_de))
        checks.append(
            {
                "case_id": case_id,
                "check_name": "Debt-Equity Ratio Consistency",
                "doc_a": "Financial Results",
                "doc_b": "Annual Report",
                "value_a": _active_value(fin_de),
                "value_b": _active_value(annual_de),
                "discrepancy": diff,
                "status": "match" if diff < Decimal("0.5") else "mismatch",
                "note": f"Debt-equity ratio diverges by {diff:.2f}x between sources.",
            }
        )

    # 9. GST/Revenue Circular Trading Check (heuristic)
    total_income = _pick(extractions, "Portfolio_Performance", "total_income")
    interest_income = _pick(extractions, "Portfolio_Performance", "interest_income")
    fee_income = _pick(extractions, "Portfolio_Performance", "fee_commission_income")
    if total_income and interest_income and _active_numeric(total_income) and _active_numeric(interest_income):
        ti = _active_numeric(total_income)
        ii = _active_numeric(interest_income)
        fi = _active_numeric(fee_income) if fee_income and _active_numeric(fee_income) else Decimal("0")
        core_income = ii + fi
        if ti > 0:
            non_core_pct = ((ti - core_income) / ti) * 100
            checks.append(
                {
                    "case_id": case_id,
                    "check_name": "Non-Core Income Concentration",
                    "doc_a": "Financial Results",
                    "doc_b": None,
                    "value_a": f"{non_core_pct:.1f}%",
                    "value_b": _active_value(total_income),
                    "discrepancy": non_core_pct,
                    "status": "match" if non_core_pct < Decimal("25") else "mismatch",
                    "note": (
                        f"{non_core_pct:.1f}% of total income is non-core. "
                        "High non-core income may indicate revenue inflation or circular trading."
                    ),
                }
            )

    # 10. GST-Revenue Reasonableness Check (Indian regulatory context)
    revenue_ext = _pick(extractions, "Annual_Report", "total_revenue_crore")
    if not revenue_ext:
        revenue_ext = _pick(extractions, "Portfolio_Performance", "total_revenue_operations")
    gst_turnover = _pick(extractions, "GST_Returns", "turnover_reported")
    if revenue_ext and _active_value(revenue_ext):
        if gst_turnover and _active_numeric(gst_turnover) and _active_numeric(revenue_ext):
            rev_val = _active_numeric(revenue_ext)
            gst_val = _active_numeric(gst_turnover)
            # Normalize if GST is in lakhs
            if gst_val > rev_val * Decimal("50"):
                gst_val = gst_val / Decimal("100")
            diff = abs(rev_val - gst_val)
            pct_diff = (diff / rev_val * 100) if rev_val else Decimal("0")
            checks.append(
                {
                    "case_id": case_id,
                    "check_name": "GST-Revenue Reasonableness",
                    "doc_a": "Revenue Disclosure",
                    "doc_b": "GST Returns",
                    "value_a": _active_value(revenue_ext),
                    "value_b": _active_value(gst_turnover),
                    "discrepancy": pct_diff,
                    "status": "match" if pct_diff < Decimal("10") else "mismatch",
                    "note": f"GST turnover diverges by {pct_diff:.1f}% from reported revenue.",
                }
            )
        else:
            # Revenue exists but no GST data available — informational flag
            checks.append(
                {
                    "case_id": case_id,
                    "check_name": "GST-Revenue Reasonableness",
                    "doc_a": "Revenue Disclosure",
                    "doc_b": "GST Returns",
                    "value_a": _active_value(revenue_ext),
                    "value_b": "Not available",
                    "discrepancy": Decimal("0"),
                    "status": "match",
                    "note": (
                        "GST filing data not available for reconciliation. "
                        "Recommend obtaining GSTR-2A/3B for revenue verification."
                    ),
                }
            )

    return checks


def llm_triangulate(
    case_id: str,
    extractions: list[Extraction],
    research_items: list[ResearchItem],
) -> list[dict]:
    """Use LLM to find contradictions/corroborations between extracted data and research."""
    if not has_text_llm() or not research_items:
        return []

    # Gather key extraction pairs
    kv_pairs = []
    for ext in extractions:
        val = ext.user_edited_value or ext.value
        if val and len(str(val)) >= 2:
            kv_pairs.append(f"{ext.field_label or ext.schema_field_key}: {val}")
    if not kv_pairs:
        return []

    # Gather top research summaries
    research_summaries = []
    for item in research_items[:5]:
        title = item.title or ""
        summary = item.summary or ""
        source = getattr(item, "source_name", "") or ""
        research_summaries.append(f"[{source}] {title}: {summary[:200]}")

    prompt = f"""You are a credit analyst reviewing extracted financial data against secondary research findings.

EXTRACTED DATA:
{chr(10).join(kv_pairs[:30])}

RESEARCH FINDINGS:
{chr(10).join(research_summaries)}

Identify up to 3 contradictions or corroborations between the extracted financial data and the research findings.
Return a JSON array where each element has:
- "check_name": short name for this check (e.g., "Rating vs Research Sentiment")
- "status": "match" (corroboration) or "mismatch" (contradiction)
- "note": one-sentence explanation
- "source_a": which extracted field
- "source_b": which research finding

Return ONLY a JSON array, no markdown."""

    try:
        result = generate_json(prompt)
        if not isinstance(result, list):
            return []
        checks = []
        for item in result[:3]:
            if not isinstance(item, dict):
                continue
            checks.append({
                "case_id": case_id,
                "check_name": f"LLM: {item.get('check_name', 'Triangulation')}",
                "doc_a": str(item.get("source_a", "")),
                "doc_b": str(item.get("source_b", "")),
                "value_a": None,
                "value_b": None,
                "discrepancy": Decimal("0"),
                "status": item.get("status", "match"),
                "note": str(item.get("note", "")),
            })
        return checks
    except Exception:
        logger.warning("LLM triangulation failed", exc_info=True)
        return []
