from __future__ import annotations

import asyncio
from datetime import date

from backend.app.models.case import Case
from backend.app.services import research_agent


def test_run_secondary_research_prioritizes_official_sources_and_dedupes(
    monkeypatch,
) -> None:
    async def fake_tavily_search(query: str, max_results: int = 5, include_domains=None) -> list[dict]:
        if include_domains and "nclt.gov.in" in include_domains:
            return [
                {
                    "title": "NCLT order involving Aavas Financiers Limited",
                    "url": "https://nclt.gov.in/case-status/order-42",
                    "content": "NCLT order referencing litigation around the company.",
                }
            ]
        if include_domains and "rbi.org.in" in include_domains:
            return [
                {
                    "title": "RBI liquidity circular",
                    "url": "https://rbi.org.in/scripts/NotificationUser.aspx?id=1",
                    "content": "",
                }
            ]
        if include_domains and "nseindia.com" in include_domains:
            return [
                {
                    "title": "Aavas corporate announcement",
                    "url": "https://www.nseindia.com/companies-listing/corporate-filings-announcements?symbol=AAVAS",
                    "content": "CARE AA reaffirmed for the company.",
                }
            ]
        return [
            {
                "title": "Aavas Financiers Limited raises funding",
                "url": "https://news.example.com/aavas-funding?utm_source=test",
                "content": "Aavas Financiers Limited reported growth and a stable outlook.",
            }
        ]

    async def fake_duckduckgo_search(query: str, max_results: int = 5, site_filters=None) -> list[dict]:
        if site_filters and "nclt.gov.in" in site_filters:
            return [
                {
                    "title": "Duplicate NCLT result",
                    "url": "https://nclt.gov.in/case-status/order-42?ref=search",
                    "content": "Duplicate legal result.",
                }
            ]
        if site_filters and "rbi.org.in" in site_filters:
            return []
        return [
            {
                "title": "Promoter governance update",
                "url": "https://news.example.com/promoter-governance",
                "content": "Promoter governance remained stable after board changes.",
            }
        ]

    async def fake_fetch_page_context(url: str) -> dict:
        if "rbi.org.in" in url:
            return {
                "title": "Reserve Bank of India circular on HFC liquidity",
                "summary": "Official RBI circular tightening liquidity risk governance for housing finance companies.",
                "published_date": date(2026, 1, 15),
            }
        return {}

    monkeypatch.setattr(research_agent, "tavily_search", fake_tavily_search)
    monkeypatch.setattr(research_agent, "duckduckgo_search", fake_duckduckgo_search)
    monkeypatch.setattr(research_agent, "fetch_page_context", fake_fetch_page_context)
    monkeypatch.setattr(
        research_agent,
        "get_market_data",
        lambda nse_symbol: {"current_price": 1900.0, "market_cap_crore": 15000.0},
    )

    case = Case(company_name="Aavas Financiers Limited", sector="Housing Finance")
    results = asyncio.run(research_agent.run_secondary_research(case, nse_symbol="AAVAS"))

    nclt_results = [
        item for item in results if (item.get("source_url") or "").startswith("https://nclt.gov.in/")
    ]
    assert len(nclt_results) == 1

    official_domains = [
        research_agent._extract_domain(item.get("source_url") or "")
        for item in results[:3]
        if item.get("source_url")
    ]
    assert any(domain in {"rbi.org.in", "nclt.gov.in", "nseindia.com"} for domain in official_domains)

    rbi_item = next(item for item in results if item.get("source_name") == "Reserve Bank of India")
    assert rbi_item["published_date"] == date(2026, 1, 15)
    assert "Official RBI circular" in rbi_item["summary"]
    assert rbi_item["category"] == "regulatory"
    assert rbi_item["affected_c"] == "Conditions"

    legal_item = next(item for item in results if item["category"] == "legal")
    assert legal_item["affected_c"] == "Character"
    assert legal_item["severity"] in {"high", "medium"}

    market_item = next(item for item in results if item["source_name"] == "yfinance")
    assert market_item["category"] == "market"
    assert market_item["affected_c"] == "Conditions"


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
