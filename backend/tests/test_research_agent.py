from __future__ import annotations

import asyncio
import json
from datetime import date
from types import SimpleNamespace

from backend.app.models.case import Case
from backend.app.services import research_agent


def extraction(key: str, value: str):
    return SimpleNamespace(schema_field_key=key, value=value, user_edited_value=None)


def test_run_secondary_research_filters_generic_official_legal_pages(monkeypatch) -> None:
    async def fake_tavily_search(query: str, *, max_results: int = 5, include_domains=None) -> list[dict]:
        if "NCLT NCLAT DRT" in query:
            return [
                {
                    "title": "Cause List - NCLT",
                    "url": "https://nclt.gov.in/cause-list/generic-case-list",
                    "content": "Generic tribunal cause list.",
                },
                {
                    "title": "NCLT order involving Aavas Financiers Limited",
                    "url": "https://nclt.gov.in/case-status/aavas-order-42",
                    "content": "Tribunal order concerning Aavas Financiers Limited.",
                },
            ]
        if "exchange filing" in query:
            return [
                {
                    "title": "AAVAS corporate announcement",
                    "url": "https://www.nseindia.com/companies-listing/corporate-filings-announcements?symbol=AAVAS",
                    "content": "AAVAS confirms investor presentation.",
                }
            ]
        if "RBI NHB circular funding liquidity asset quality" in query:
            return [
                {
                    "title": "RBI circular for housing finance companies",
                    "url": "https://www.rbi.org.in/Scripts/NotificationUser.aspx?id=999",
                    "content": "Housing finance companies must strengthen liquidity risk governance.",
                }
            ]
        return []

    async def fake_firecrawl_scrape(url: str) -> dict:
        if "aavas-order-42" in url:
            return {
                "title": "NCLT order involving Aavas Financiers Limited",
                "summary": "Borrower-specific order referencing Aavas Financiers Limited.",
                "markdown": "Aavas Financiers Limited was named in the matter before NCLT.",
                "published_date": date(2026, 1, 15),
            }
        if "NotificationUser.aspx?id=999" in url:
            return {
                "title": "RBI circular for housing finance companies",
                "summary": "Liquidity governance requirements for housing finance companies.",
                "markdown": "This circular applies to housing finance companies and impacts liquidity governance.",
                "published_date": date(2026, 1, 10),
            }
        return {
            "title": "Generic page",
            "summary": "Generic official page without borrower mention.",
            "markdown": "This page does not mention the borrower.",
            "published_date": None,
        }

    monkeypatch.setattr(research_agent, "tavily_search", fake_tavily_search)
    monkeypatch.setattr(research_agent, "duckduckgo_search", lambda *args, **kwargs: [])
    monkeypatch.setattr(research_agent, "firecrawl_scrape", fake_firecrawl_scrape)
    monkeypatch.setattr(research_agent, "get_market_data", lambda nse_symbol: None)

    case = Case(company_name="Aavas Financiers Limited", sector="Housing Finance")
    results = asyncio.run(
        research_agent.run_secondary_research(
            case,
            nse_symbol="AAVAS",
            extractions=[extraction("promoter_name", "Saurabh Sharma")],
        )
    )

    assert not any("generic-case-list" in (item.get("source_url") or "") for item in results)

    legal_item = next(item for item in results if item["category"] == "legal")
    assert legal_item["entity_scope"] == "borrower"
    assert legal_item["verification_status"] == "verified"
    assert legal_item["severity"] in {"medium", "high"}

    regulatory_item = next(item for item in results if item["category"] == "regulatory")
    assert regulatory_item["entity_scope"] in {"sector", "macro"}
    assert regulatory_item["verification_status"] in {"contextual", "verified"}


def test_run_secondary_research_uses_extracted_terms_for_match_metadata(monkeypatch) -> None:
    async def fake_tavily_search(query: str, *, max_results: int = 5, include_domains=None) -> list[dict]:
        if "CARE ICRA CRISIL rating" in query:
            return [
                {
                    "title": "CARE reaffirms rating for Aavas Financiers Limited",
                    "url": "https://ratings.example.com/aavas-care-rating",
                    "content": "CARE AA reaffirmed for Aavas Financiers Limited.",
                }
            ]
        return []

    async def fake_firecrawl_scrape(url: str) -> dict:
        return {
            "title": "CARE reaffirms rating for Aavas Financiers Limited",
            "summary": "CARE AA reaffirmed; outlook stable.",
            "markdown": "Aavas Financiers Limited rating action: Reaffirmed. Long-term rating: CARE AA. Rating agency: CARE Ratings Limited.",
            "published_date": date(2026, 1, 20),
        }

    monkeypatch.setattr(research_agent, "tavily_search", fake_tavily_search)
    monkeypatch.setattr(research_agent, "duckduckgo_search", lambda *args, **kwargs: [])
    monkeypatch.setattr(research_agent, "firecrawl_scrape", fake_firecrawl_scrape)
    monkeypatch.setattr(research_agent, "get_market_data", lambda nse_symbol: None)

    case = Case(company_name="Aavas Financiers Limited", sector="Housing Finance")
    results = asyncio.run(
        research_agent.run_secondary_research(
            case,
            nse_symbol="AAVAS",
            extractions=[
                extraction("rating_action", "Reaffirmed"),
                extraction("long_term_rating", "CARE AA"),
                extraction("rating_agency", "CARE Ratings Limited"),
            ],
        )
    )

    rating_item = next(item for item in results if "CARE reaffirms rating" in (item["title"] or ""))
    matched_terms = json.loads(rating_item["matched_terms"])
    assert any(term.startswith("company:") for term in matched_terms)
    assert any(term.startswith("rating_action:") or term.startswith("long_term_rating:") for term in matched_terms)
    assert rating_item["verification_status"] == "verified"


def test_classify_research_category_prefers_official_domains() -> None:
    assert (
        research_agent.classify_research_category(
            "generic query",
            "Some title",
            "https://www.rbi.org.in/scripts/NotificationUser.aspx?id=1",
        )
        == "regulatory"
    )
    assert (
        research_agent.classify_research_category(
            "generic query",
            "Case listing",
            "https://nclt.gov.in/case-status/order-42",
        )
        == "legal"
    )


def test_unwrap_redirect_url_extracts_duckduckgo_target() -> None:
    redirected = (
        "//duckduckgo.com/l/?uddg="
        "https%3A%2F%2Fwww.rbi.org.in%2FScripts%2FNotificationUser.aspx%3Fid%3D1"
    )
    assert (
        research_agent._unwrap_redirect_url(redirected)
        == "https://www.rbi.org.in/Scripts/NotificationUser.aspx?id=1"
    )
