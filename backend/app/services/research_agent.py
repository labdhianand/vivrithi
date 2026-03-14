from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from datetime import date
from urllib.parse import parse_qs, quote_plus, unquote, urlsplit, urlunsplit

import httpx
import yfinance as yf
from bs4 import BeautifulSoup

from ..config import get_settings
from ..models.case import Case
from .utils import clamp


OFFICIAL_SOURCE_NAMES = {
    "rbi.org.in": "Reserve Bank of India",
    "nhb.org.in": "National Housing Bank",
    "sebi.gov.in": "SEBI",
    "mca.gov.in": "Ministry of Corporate Affairs",
    "nclt.gov.in": "National Company Law Tribunal",
    "nclat.nic.in": "NCLAT",
    "ibbi.gov.in": "IBBI",
    "nseindia.com": "NSE India",
    "bseindia.com": "BSE India",
}
OFFICIAL_DOMAINS = tuple(OFFICIAL_SOURCE_NAMES.keys())
REGULATORY_DOMAINS = {"rbi.org.in", "nhb.org.in", "sebi.gov.in", "mca.gov.in", "ibbi.gov.in"}
LEGAL_DOMAINS = {"nclt.gov.in", "nclat.nic.in", "ibbi.gov.in", "mca.gov.in"}
MARKET_DOMAINS = {"nseindia.com", "bseindia.com"}
NEGATIVE_TERMS = ["downgrade", "default", "litigation", "fraud", "decline", "stress", "probe", "insolvency"]
POSITIVE_TERMS = ["upgrade", "growth", "profit", "expansion", "improved", "stable", "reaffirmed"]


@dataclass(frozen=True, slots=True)
class SearchPlan:
    name: str
    query: str
    category: str
    include_domains: tuple[str, ...] = ()
    max_results: int = 4


def _compact_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def _unwrap_redirect_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlsplit(url)
    query = parse_qs(parsed.query)
    if "uddg" in query and query["uddg"]:
        return unquote(query["uddg"][0])
    return url


def _extract_domain(url: str) -> str:
    if not url:
        return ""
    parsed = urlsplit(_unwrap_redirect_url(url))
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def _canonicalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlsplit(_unwrap_redirect_url(url))
    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", ""))


def _domain_matches(domain: str, candidates: set[str] | tuple[str, ...]) -> bool:
    return any(domain == candidate or domain.endswith(f".{candidate}") for candidate in candidates)


def _is_official_domain(domain: str) -> bool:
    return _domain_matches(domain, OFFICIAL_DOMAINS)


def _source_name_for_url(url: str) -> str | None:
    domain = _extract_domain(url)
    for candidate, label in OFFICIAL_SOURCE_NAMES.items():
        if domain == candidate or domain.endswith(f".{candidate}"):
            return label
    return domain or None


def _maybe_parse_date(value: object) -> date | None:
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    iso_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if iso_match:
        year, month, day = (int(part) for part in iso_match.groups())
        return date(year, month, day)
    dmy_match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", text)
    if dmy_match:
        day, month, year = (int(part) for part in dmy_match.groups())
        return date(year, month, day)
    return None


def analyze_sentiment(snippet: str) -> str:
    lowered = snippet.lower()
    neg_score = sum(word in lowered for word in NEGATIVE_TERMS)
    pos_score = sum(word in lowered for word in POSITIVE_TERMS)
    if neg_score > pos_score:
        return "negative"
    if pos_score > neg_score:
        return "positive"
    return "neutral"


def assess_severity(snippet: str, company_name: str) -> str:
    lowered = snippet.lower()
    if any(word in lowered for word in ["default", "insolvency", "fraud", "downgrade", "nclt", "nclat"]):
        return "high"
    if any(word in lowered for word in ["probe", "delay", "volatility", "litigation"]):
        return "medium"
    if company_name.lower() in lowered:
        return "low"
    return "low"


def classify_research_category(query: str, title: str, url: str) -> str:
    joined = f"{query} {title} {url}".lower()
    domain = _extract_domain(url)
    if _domain_matches(domain, LEGAL_DOMAINS):
        return "legal"
    if _domain_matches(domain, REGULATORY_DOMAINS):
        return "regulatory"
    if _domain_matches(domain, MARKET_DOMAINS):
        return "market"
    if "litigation" in joined or "nclt" in joined or "court" in joined:
        return "legal"
    if "rbi" in joined or "nhb" in joined or "sebi" in joined or "regulation" in joined:
        return "regulatory"
    if "promoter" in joined or "director" in joined:
        return "promoter"
    if "sector" in joined or "outlook" in joined:
        return "sector"
    if "market" in joined or "stock" in joined:
        return "market"
    return "news"


async def tavily_search(
    query: str,
    max_results: int = 5,
    include_domains: tuple[str, ...] | None = None,
) -> list[dict]:
    settings = get_settings()
    if not settings.tavily_api_key:
        return []
    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "search_depth": "advanced",
        "max_results": max_results,
        "include_answer": False,
    }
    if include_domains:
        payload["include_domains"] = list(include_domains)
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post("https://api.tavily.com/search", json=payload)
            response.raise_for_status()
        return response.json().get("results", [])
    except Exception:
        return []


async def duckduckgo_search(
    query: str,
    max_results: int = 5,
    site_filters: tuple[str, ...] | None = None,
) -> list[dict]:
    decorated_query = query
    if site_filters:
        decorated_query = f"{query} {' '.join(f'site:{domain}' for domain in site_filters)}"
    url = f"https://duckduckgo.com/html/?q={quote_plus(decorated_query)}"
    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
    except Exception:
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    items: list[dict] = []
    for result in soup.select(".result")[:max_results]:
        link = result.select_one(".result__a")
        snippet = result.select_one(".result__snippet")
        if not link:
            continue
        items.append(
            {
                "title": link.get_text(" ", strip=True),
                "url": _unwrap_redirect_url(link.get("href", "")),
                "content": snippet.get_text(" ", strip=True) if snippet else "",
            }
        )
    return items


async def fetch_page_context(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
    except Exception:
        return {}
    soup = BeautifulSoup(response.text, "html.parser")
    title = _compact_text(soup.title.get_text(" ", strip=True) if soup.title else "")
    meta_description = ""
    published_date = None
    for meta in soup.find_all("meta"):
        key = (meta.get("property") or meta.get("name") or "").lower()
        content = _compact_text(meta.get("content", ""))
        if not meta_description and key in {"description", "og:description", "twitter:description"}:
            meta_description = content
        if published_date is None and key in {
            "article:published_time",
            "article:modified_time",
            "publishdate",
            "pubdate",
            "date",
            "dc.date",
        }:
            published_date = _maybe_parse_date(content)
    if not meta_description:
        paragraphs = [
            _compact_text(paragraph.get_text(" ", strip=True))
            for paragraph in soup.find_all("p")
            if _compact_text(paragraph.get_text(" ", strip=True))
        ]
        meta_description = " ".join(paragraphs[:2]).strip()
    return {"title": title, "summary": meta_description, "published_date": published_date}


def get_market_data(nse_symbol: str | None) -> dict | None:
    if not nse_symbol:
        return None
    try:
        ticker = yf.Ticker(f"{nse_symbol}.NS")
        info = ticker.info or {}
        history = ticker.history(period="1y")
        if history.empty:
            one_year_return = None
        else:
            start = float(history["Close"].iloc[0])
            end = float(history["Close"].iloc[-1])
            one_year_return = round(((end - start) / start) * 100, 2) if start else None
        return {
            "current_price": info.get("currentPrice"),
            "market_cap_crore": round(info.get("marketCap", 0) / 1e7, 2) if info.get("marketCap") else None,
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "one_year_return_percent": one_year_return,
        }
    except Exception:
        return None


async def enrich_research_with_impact(items: list[dict], case: Case) -> list[dict]:
    sector = (case.sector or "").lower()
    for item in items:
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        if item["category"] == "legal":
            item["affected_c"] = "Character"
            item["impact_description"] = "Legal proceedings can weaken governance and execution certainty."
        elif item["category"] == "regulatory":
            item["affected_c"] = "Conditions"
            item["impact_description"] = "Regulatory changes can alter funding, compliance, or capital needs."
        elif item["category"] == "market":
            item["affected_c"] = "Conditions"
            item["impact_description"] = "Market pricing and sentiment affect funding access."
        elif "promoter" in text:
            item["affected_c"] = "Character"
            item["impact_description"] = "Promoter developments influence governance assessment."
        elif sector and sector in text:
            item["affected_c"] = "Conditions"
            item["impact_description"] = "Sector trends influence portfolio growth and risk."
        else:
            item["affected_c"] = "Capacity"
            item["impact_description"] = "News flow may impact operating performance."
    return items


def _build_search_plans(case: Case) -> list[SearchPlan]:
    sector = case.sector or case.subsector or "India NBFC"
    company = _compact_text(case.company_name)
    plans = [
        SearchPlan(
            name="company_news",
            query=f'"{company}" quarterly results funding rating news',
            category="news",
        ),
        SearchPlan(
            name="legal_orders",
            query=f'"{company}" NCLT NCLAT insolvency petition order',
            category="legal",
            include_domains=("nclt.gov.in", "nclat.nic.in", "ibbi.gov.in", "mca.gov.in"),
        ),
        SearchPlan(
            name="regulatory_actions",
            query=f'"{company}" RBI NHB SEBI regulatory action circular inspection',
            category="regulatory",
            include_domains=("rbi.org.in", "nhb.org.in", "sebi.gov.in", "mca.gov.in"),
        ),
        SearchPlan(
            name="exchange_filings",
            query=f'"{company}" corporate announcement shareholding rating filing',
            category="market",
            include_domains=("nseindia.com", "bseindia.com"),
        ),
        SearchPlan(
            name="promoter_governance",
            query=f'"{company}" promoter director resignation governance',
            category="promoter",
        ),
        SearchPlan(
            name="sector_regulation",
            query=f"{sector} RBI NHB circular funding outlook asset quality",
            category="sector",
            include_domains=("rbi.org.in", "nhb.org.in", "sebi.gov.in"),
        ),
        SearchPlan(
            name="sector_news",
            query=f"{sector} India outlook growth asset quality liquidity",
            category="sector",
        ),
    ]
    if case.cin:
        plans.append(
            SearchPlan(
                name="mca_company_lookup",
                query=f'"{case.cin}" MCA company directors charges',
                category="promoter",
                include_domains=("mca.gov.in",),
            )
        )

    # India-specific: MCA filings and ROC returns
    plans.append(
        SearchPlan(
            name="mca_filings",
            query=f'"{company}" MCA ROC annual return charge satisfaction director change',
            category="regulatory",
            include_domains=("mca.gov.in", "tofler.in", "zaubacorp.com"),
        )
    )

    # India-specific: e-Courts litigation search
    plans.append(
        SearchPlan(
            name="ecourts_litigation",
            query=f'"{company}" litigation court case pending disposed NCLT DRT',
            category="legal",
            include_domains=("ecourts.gov.in", "indiankanoon.org", "nclt.gov.in", "drt.gov.in"),
        )
    )

    # India-specific: GST compliance and filings
    plans.append(
        SearchPlan(
            name="gst_compliance",
            query=f'"{company}" GST return filing compliance GSTR penalty notice',
            category="regulatory",
        )
    )

    # India-specific: CIBIL / Credit Information
    plans.append(
        SearchPlan(
            name="cibil_commercial",
            query=f'"{company}" CIBIL commercial credit report score bureau',
            category="promoter",
        )
    )

    # India-specific: RBI defaulter list / willful defaulter
    plans.append(
        SearchPlan(
            name="rbi_defaulter_check",
            query=f'"{company}" RBI willful defaulter SMA NPA classification',
            category="legal",
            include_domains=("rbi.org.in",),
        )
    )

    return plans


async def _execute_search_plan(plan: SearchPlan) -> list[dict]:
    tavily_task = asyncio.create_task(
        tavily_search(plan.query, max_results=plan.max_results, include_domains=plan.include_domains or None)
    )
    ddg_task = asyncio.create_task(
        duckduckgo_search(plan.query, max_results=plan.max_results, site_filters=plan.include_domains or None)
    )
    tavily_results, ddg_results = await asyncio.gather(tavily_task, ddg_task)
    merged: list[dict] = []
    seen: set[str] = set()
    for result in [*tavily_results, *ddg_results]:
        url = result.get("url", "")
        key = _canonicalize_url(url) or _compact_text(result.get("title"))
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(result)
    return merged


def _score_relevance(plan: SearchPlan, case: Case, title: str, summary: str, url: str) -> float:
    domain = _extract_domain(url)
    joined = f"{title} {summary}".lower()
    company_name = (case.company_name or "").lower()
    sector = (case.sector or case.subsector or "").lower()
    score = 0.35
    if _is_official_domain(domain):
        score += 0.28
    if company_name and company_name in joined:
        score += 0.16
    if sector and sector in joined:
        score += 0.08
    if plan.category in {"legal", "regulatory", "market"}:
        score += 0.06
    if any(term in joined for term in NEGATIVE_TERMS + POSITIVE_TERMS):
        score += 0.05
    if len(summary) > 120:
        score += 0.05
    return clamp(score, 0.1, 1.0)


def _normalize_result(plan: SearchPlan, case: Case, result: dict) -> dict | None:
    title = _compact_text(result.get("title"))
    summary = _compact_text(result.get("content") or result.get("snippet") or result.get("summary"))
    url = result.get("url", "")
    if not title and not summary:
        return None
    category = classify_research_category(plan.query, title, url) or plan.category
    combined_text = _compact_text(f"{title} {summary}")
    published_date = (
        _maybe_parse_date(result.get("published_date"))
        or _maybe_parse_date(result.get("published"))
        or _maybe_parse_date(result.get("date"))
        or date.today()
    )
    return {
        "category": category,
        "title": title or summary[:140],
        "summary": summary,
        "source_url": url or None,
        "source_name": _source_name_for_url(url),
        "published_date": published_date,
        "sentiment": analyze_sentiment(combined_text),
        "severity": assess_severity(combined_text, case.company_name),
        "relevance_score": _score_relevance(plan, case, title, summary, url),
    }


def _dedupe_research_items(items: list[dict]) -> list[dict]:
    deduped: dict[str, dict] = {}
    for item in items:
        key = _canonicalize_url(item.get("source_url") or "") or _compact_text(item.get("title")).lower()
        existing = deduped.get(key)
        if existing is None or float(item.get("relevance_score") or 0) > float(existing.get("relevance_score") or 0):
            deduped[key] = item
    return list(deduped.values())


async def _enrich_official_context(items: list[dict]) -> list[dict]:
    candidates = [
        item
        for item in items
        if item.get("source_url")
        and _is_official_domain(_extract_domain(item["source_url"]))
        and (len(item.get("summary") or "") < 120 or item.get("published_date") is None)
    ][:6]
    if not candidates:
        return items
    contexts = await asyncio.gather(*(fetch_page_context(item["source_url"]) for item in candidates))
    for item, context in zip(candidates, contexts):
        if context.get("summary") and len(context["summary"]) > len(item.get("summary") or ""):
            item["summary"] = _compact_text(context["summary"])
        if context.get("title") and len(context["title"]) > len(item.get("title") or ""):
            item["title"] = context["title"]
        if context.get("published_date"):
            item["published_date"] = context["published_date"]
        item["source_name"] = item.get("source_name") or _source_name_for_url(item.get("source_url") or "")
    return items


def _sort_research_items(items: list[dict]) -> list[dict]:
    severity_rank = {"high": 3, "medium": 2, "low": 1, None: 0}

    def sort_key(item: dict) -> tuple[int, float, int, str]:
        domain = _extract_domain(item.get("source_url") or "")
        published = item.get("published_date")
        return (
            1 if _is_official_domain(domain) else 0,
            float(item.get("relevance_score") or 0),
            severity_rank.get(item.get("severity"), 0),
            published.isoformat() if isinstance(published, date) else "",
        )

    return sorted(items, key=sort_key, reverse=True)


async def run_secondary_research(case: Case, nse_symbol: str | None = None) -> list[dict]:
    plans = _build_search_plans(case)
    raw_batches = await asyncio.gather(*(_execute_search_plan(plan) for plan in plans))
    items: list[dict] = []
    for plan, raw_results in zip(plans, raw_batches):
        for result in raw_results[: plan.max_results]:
            normalized = _normalize_result(plan, case, result)
            if normalized:
                items.append(normalized)

    market_data = get_market_data(nse_symbol)
    if market_data:
        items.append(
            {
                "category": "market",
                "title": f"{case.company_name} market snapshot",
                "summary": json.dumps(market_data, ensure_ascii=True),
                "source_url": None,
                "source_name": "yfinance",
                "published_date": date.today(),
                "sentiment": "neutral",
                "severity": "low",
                "relevance_score": 0.7,
            }
        )
    items = _dedupe_research_items(items)
    items = await _enrich_official_context(items)
    items = await enrich_research_with_impact(items, case)
    return _sort_research_items(items)
