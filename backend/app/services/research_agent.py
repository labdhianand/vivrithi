from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import date
from typing import Optional
from urllib.parse import parse_qs, quote_plus, unquote, urlsplit, urlunsplit

from firecrawl import FirecrawlApp

from ..config import get_settings
from ..models.case import Case
from ..models.extraction import Extraction
from .utils import clamp


logger = logging.getLogger(__name__)
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
_firecrawl_client: Optional[FirecrawlApp] = None


OFFICIAL_SOURCE_NAMES = {
    "rbi.org.in": "Reserve Bank of India",
    "nhb.org.in": "National Housing Bank",
    "sebi.gov.in": "SEBI",
    "mca.gov.in": "Ministry of Corporate Affairs",
    "nclt.gov.in": "National Company Law Tribunal",
    "nclat.nic.in": "NCLAT",
    "ibbi.gov.in": "IBBI",
    "ecourts.gov.in": "e-Courts",
    "drt.gov.in": "Debt Recovery Tribunal",
    "nseindia.com": "NSE India",
    "bseindia.com": "BSE India",
    "trendlyne.com": "Trendlyne",
    "moneycontrol.com": "Moneycontrol",
    "screener.in": "Screener.in",
}
OFFICIAL_DOMAINS = tuple(OFFICIAL_SOURCE_NAMES.keys())
REGULATORY_DOMAINS = {"rbi.org.in", "nhb.org.in", "sebi.gov.in", "mca.gov.in"}
LEGAL_DOMAINS = {"nclt.gov.in", "nclat.nic.in", "ibbi.gov.in", "ecourts.gov.in", "drt.gov.in"}
MARKET_DOMAINS = {"nseindia.com", "bseindia.com"}
NEGATIVE_TERMS = [
    "downgrade",
    "default",
    "litigation",
    "fraud",
    "decline",
    "stress",
    "probe",
    "insolvency",
    "penalty",
    "show cause",
    "willful defaulter",
]
POSITIVE_TERMS = ["upgrade", "growth", "profit", "expansion", "improved", "stable", "reaffirmed"]
COMPANY_STOPWORDS = {
    "limited",
    "ltd",
    "company",
    "co",
    "india",
    "private",
    "public",
    "the",
    "and",
    "of",
}
WEAK_MATCH_TOKENS = {
    "home",
    "first",
    "finance",
    "financial",
    "housing",
    "bank",
    "capital",
    "credit",
    "fund",
    "funding",
    "real",
    "estate",
}


@dataclass(frozen=True, slots=True)
class SearchPlan:
    name: str
    query: str
    category: str
    scope_hint: str
    include_domains: tuple[str, ...] = ()
    max_results: int = 3


@dataclass(frozen=True, slots=True)
class ResearchContext:
    company_name: str
    company_aliases: tuple[str, ...]
    company_tokens: tuple[str, ...]
    promoter_names: tuple[str, ...]
    promoter_tokens: tuple[str, ...]
    nse_symbol: str | None
    cin: str | None
    sector_terms: tuple[str, ...]
    subsector_terms: tuple[str, ...]
    rating_terms: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EntityMatch:
    scope: str
    score: float
    status: str
    matched_terms: tuple[str, ...]
    explanation: str


def _configured_firecrawl_key() -> str:
    settings = get_settings()
    return settings.firecrawl_api_key or FIRECRAWL_API_KEY


def _get_client() -> FirecrawlApp:
    global _firecrawl_client
    api_key = _configured_firecrawl_key()
    if not api_key:
        raise RuntimeError("FIRECRAWL_API_KEY is not configured")
    if _firecrawl_client is None:
        _firecrawl_client = FirecrawlApp(api_key=api_key)
    return _firecrawl_client


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


def _json_dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True)


def _normalize_phrase(value: str) -> str:
    return re.sub(r"[^a-z0-9% ]+", " ", value.lower()).strip()


def _tokenize(value: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", value.lower()) if token]


def _unique_phrases(values: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = _compact_text(value)
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        ordered.append(normalized)
    return tuple(ordered)


def _extract_promoter_names(extractions: list[Extraction] | None) -> tuple[str, ...]:
    if not extractions:
        return ()
    names: list[str] = []
    for extraction in extractions:
        if extraction.schema_field_key != "promoter_name":
            continue
        raw_value = _compact_text(extraction.user_edited_value or extraction.value)
        if not raw_value:
            continue
        for part in re.split(r"[;\n]+", raw_value):
            part = _compact_text(part)
            if len(part) >= 5:
                names.append(part)
    return _unique_phrases(names)


def _company_aliases(company_name: str) -> tuple[str, ...]:
    full = _compact_text(company_name)
    tokens = _tokenize(company_name)
    trimmed = [token for token in tokens if token not in COMPANY_STOPWORDS]
    aliases = [full]
    if trimmed:
        aliases.append(" ".join(trimmed))
    if len(trimmed) >= 2:
        aliases.append(" ".join(trimmed[:2]))
    return _unique_phrases([alias for alias in aliases if len(alias) >= 5])


def _sector_terms(case: Case) -> tuple[str, ...]:
    values = [case.sector or "", case.subsector or ""]
    phrases: list[str] = []
    for value in values:
        compact = _compact_text(value)
        if compact:
            phrases.append(compact)
            tokens = [token for token in _tokenize(compact) if len(token) >= 4]
            if tokens:
                phrases.append(" ".join(tokens))
    return _unique_phrases(phrases)


def _rating_terms(extractions: list[Extraction] | None) -> tuple[str, ...]:
    if not extractions:
        return ()
    values: list[str] = []
    for extraction in extractions:
        if extraction.schema_field_key not in {"rating_action", "long_term_rating", "long_term_outlook", "rating_agency"}:
            continue
        value = _compact_text(extraction.user_edited_value or extraction.value)
        if len(value) >= 3:
            values.append(value)
    return _unique_phrases(values)


def build_research_context(
    case: Case,
    *,
    nse_symbol: str | None = None,
    extractions: list[Extraction] | None = None,
) -> ResearchContext:
    company_aliases = _company_aliases(case.company_name)
    company_tokens = tuple(
        token for token in _tokenize(" ".join(company_aliases)) if len(token) >= 4 and token not in WEAK_MATCH_TOKENS
    )
    promoter_names = _extract_promoter_names(extractions)
    promoter_tokens = tuple(token for token in _tokenize(" ".join(promoter_names)) if len(token) >= 4)
    sector_terms = _sector_terms(case)
    subsector_terms = _unique_phrases([case.subsector or ""])
    rating_terms = _rating_terms(extractions)
    return ResearchContext(
        company_name=_compact_text(case.company_name),
        company_aliases=company_aliases,
        company_tokens=company_tokens,
        promoter_names=promoter_names,
        promoter_tokens=promoter_tokens,
        nse_symbol=_compact_text(nse_symbol).upper() or None,
        cin=_compact_text(case.cin).upper() or None,
        sector_terms=sector_terms,
        subsector_terms=subsector_terms,
        rating_terms=rating_terms,
    )


def analyze_sentiment(snippet: str) -> str:
    lowered = snippet.lower()
    neg_score = sum(word in lowered for word in NEGATIVE_TERMS)
    pos_score = sum(word in lowered for word in POSITIVE_TERMS)
    if neg_score > pos_score:
        return "negative"
    if pos_score > neg_score:
        return "positive"
    return "neutral"


def classify_research_category(query: str, title: str, url: str) -> str:
    joined = f"{query} {title} {url}".lower()
    domain = _extract_domain(url)
    if _domain_matches(domain, LEGAL_DOMAINS):
        return "legal"
    if _domain_matches(domain, REGULATORY_DOMAINS):
        return "regulatory"
    if _domain_matches(domain, MARKET_DOMAINS):
        return "market"
    if any(term in joined for term in ["litigation", "nclt", "nclat", "drt", "insolvency", "court"]):
        return "legal"
    if any(term in joined for term in ["rbi", "nhb", "sebi", "regulation", "circular", "inspection", "penalty"]):
        return "regulatory"
    if "promoter" in joined or "director" in joined or "governance" in joined:
        return "promoter"
    if "sector" in joined or "outlook" in joined or "macro" in joined:
        return "sector"
    if "market" in joined or "stock" in joined or "announcement" in joined:
        return "market"
    return "news"


async def tavily_search(
    query: str,
    *,
    max_results: int = 5,
    include_domains: tuple[str, ...] | None = None,
) -> list[dict]:
    try:
        decorated_query = query
        if include_domains:
            decorated_query = f"{query} {' '.join(f'site:{domain}' for domain in include_domains)}"

        def _search() -> list[dict]:
            raw_results = _get_client().search(decorated_query, limit=max_results)
            if isinstance(raw_results, dict):
                items = raw_results.get("data")
                if isinstance(items, list):
                    return items
            if isinstance(raw_results, list):
                return raw_results
            return []

        results = await asyncio.to_thread(_search)
        normalized: list[dict] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("markdown", item.get("description", "")),
                    "summary": item.get("description", ""),
                    "published_date": item.get("publishedDate") or item.get("published_date"),
                }
            )
        return normalized
    except Exception as exc:
        logger.error("Firecrawl search failed for '%s': %s", query, exc)
        return []


async def duckduckgo_search(
    query: str,
    *,
    max_results: int = 5,
    site_filters: tuple[str, ...] | None = None,
) -> list[dict]:
    return await tavily_search(query, max_results=max_results, include_domains=site_filters)


async def firecrawl_scrape(url: str) -> dict:
    if not url:
        return {}
    try:
        def _scrape() -> dict:
            raw_result = _get_client().scrape_url(
                url,
                params={"formats": ["markdown"]},
            )
            return raw_result if isinstance(raw_result, dict) else {}

        body = await asyncio.to_thread(_scrape)
    except Exception as exc:
        logger.error("Firecrawl scrape failed for %s: %s", url, exc)
        return {}
    data = body.get("data") if isinstance(body.get("data"), dict) else body
    if not isinstance(data, dict):
        return {}
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    return {
        "title": _compact_text(str(data.get("title") or metadata.get("title") or "")),
        "summary": _compact_text(
            str(
                data.get("description")
                or metadata.get("description")
                or metadata.get("excerpt")
                or ""
            )
        ),
        "markdown": _compact_text(str(data.get("markdown") or data.get("content") or "")),
        "published_date": _maybe_parse_date(
            data.get("publishedDate")
            or metadata.get("publishedTime")
            or metadata.get("publishedDate")
            or ""
        ),
    }


def _firecrawl_search_sync(
    query: str,
    *,
    limit: int = 5,
    include_domains: tuple[str, ...] | None = None,
) -> list[dict]:
    try:
        decorated_query = query
        if include_domains:
            decorated_query = f"{query} {' '.join(f'site:{domain}' for domain in include_domains)}"
        raw_results = _get_client().search(decorated_query, limit=limit)
        if isinstance(raw_results, dict):
            items = raw_results.get("data")
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
        if isinstance(raw_results, list):
            return [item for item in raw_results if isinstance(item, dict)]
    except Exception as exc:
        logger.error("Firecrawl search failed for '%s': %s", query, exc)
    return []


def _firecrawl_scrape_markdown_sync(url: str) -> str:
    if not url:
        return ""
    try:
        raw_result = _get_client().scrape_url(url, params={"formats": ["markdown"]})
    except Exception as exc:
        logger.error("Firecrawl scrape failed for %s: %s", url, exc)
        return ""
    data = raw_result.get("data") if isinstance(raw_result, dict) and isinstance(raw_result.get("data"), dict) else raw_result
    if not isinstance(data, dict):
        return ""
    return _compact_text(str(data.get("markdown") or data.get("content") or ""))


def _search_items_from_firecrawl(
    query: str,
    *,
    limit: int = 5,
    include_domains: tuple[str, ...] | None = None,
) -> list[dict]:
    items: list[dict] = []
    for result in _firecrawl_search_sync(query, limit=limit, include_domains=include_domains):
        items.append(
            {
                "title": _compact_text(str(result.get("title") or "")),
                "url": _compact_text(str(result.get("url") or "")),
                "summary": _compact_text(
                    str(result.get("markdown") or result.get("description") or result.get("content") or "")
                )[:600],
                "source": "firecrawl_search",
            }
        )
    return items


def get_market_data(nse_symbol: str | None) -> dict | None:
    return None


def search_company_news(company_name: str, sector: str) -> list[dict]:
    return _search_items_from_firecrawl(
        f"{company_name} {sector} India financial news 2024 2025",
        limit=5,
    )


def search_litigation(company_name: str) -> list[dict]:
    return _search_items_from_firecrawl(
        f"{company_name} India court case NPA default legal notice",
        limit=5,
    )


def search_promoter_background(company_name: str) -> list[dict]:
    return _search_items_from_firecrawl(
        f"{company_name} promoter director India background management",
        limit=5,
    )


def search_sector_outlook(sector: str) -> list[dict]:
    return _search_items_from_firecrawl(
        f"India {sector} sector outlook RBI SEBI regulation 2024 2025",
        limit=5,
    )


def scrape_mca_data(cin: str) -> str:
    return _firecrawl_scrape_markdown_sync(f"https://www.zaubacorp.com/company/NA/{cin}")


def run_research(company_name: str, sector: str, cin: str) -> dict:
    logger.info("Starting Firecrawl research for %s", company_name)

    news = search_company_news(company_name, sector)
    litigation = search_litigation(company_name)
    promoter = search_promoter_background(company_name)
    sector_data = search_sector_outlook(sector)
    mca_data = scrape_mca_data(cin)

    logger.info(
        "Research complete: %s news, %s litigation, %s promoter items",
        len(news),
        len(litigation),
        len(promoter),
    )

    return {
        "news": news,
        "litigation": litigation,
        "promoter_info": promoter,
        "sector_outlook": sector_data,
        "mca_data": mca_data,
        "company_name": company_name,
        "sector": sector,
        "cin": cin,
        "research_tool": "firecrawl",
    }


def _build_search_plans(context: ResearchContext) -> list[SearchPlan]:
    settings = get_settings()
    per_plan_results = min(4, max(2, settings.research_max_results // 6))
    sector_query = context.subsector_terms[0] if context.subsector_terms else (context.sector_terms[0] if context.sector_terms else "India NBFC")
    plans = [
        SearchPlan(
            name="borrower_news",
            query=f'"{context.company_name}" quarterly results funding rating outlook',
            category="news",
            scope_hint="borrower",
            max_results=per_plan_results,
        ),
        SearchPlan(
            name="borrower_market",
            query=f'"{context.company_name}" exchange filing investor presentation corporate announcement',
            category="market",
            scope_hint="borrower",
            include_domains=("nseindia.com", "bseindia.com"),
            max_results=per_plan_results,
        ),
        SearchPlan(
            name="rating_actions",
            query=f'"{context.company_name}" CARE ICRA CRISIL rating press release',
            category="news",
            scope_hint="borrower",
            max_results=per_plan_results,
        ),
        SearchPlan(
            name="promoter_governance",
            query=f'"{context.company_name}" promoter director resignation governance',
            category="promoter",
            scope_hint="promoter",
            max_results=per_plan_results,
        ),
        SearchPlan(
            name="legal_borrower",
            query=f'"{context.company_name}" NCLT NCLAT DRT insolvency petition order',
            category="legal",
            scope_hint="borrower",
            include_domains=("nclt.gov.in", "nclat.nic.in", "ibbi.gov.in", "ecourts.gov.in", "drt.gov.in"),
            max_results=per_plan_results,
        ),
        SearchPlan(
            name="regulatory_borrower",
            query=f'"{context.company_name}" RBI NHB SEBI inspection penalty circular action',
            category="regulatory",
            scope_hint="borrower",
            include_domains=("rbi.org.in", "nhb.org.in", "sebi.gov.in", "mca.gov.in"),
            max_results=per_plan_results,
        ),
        SearchPlan(
            name="sector_regulation",
            query=f"{sector_query} RBI NHB circular funding liquidity asset quality",
            category="regulatory",
            scope_hint="sector",
            include_domains=("rbi.org.in", "nhb.org.in", "sebi.gov.in"),
            max_results=per_plan_results,
        ),
        SearchPlan(
            name="sector_headwinds",
            query=f"{sector_query} India outlook asset quality liquidity funding costs",
            category="sector",
            scope_hint="sector",
            max_results=per_plan_results,
        ),
        SearchPlan(
            name="macro_conditions",
            query='India NBFC HFC funding cost liquidity outlook RBI',
            category="sector",
            scope_hint="macro",
            include_domains=("rbi.org.in", "nhb.org.in"),
            max_results=max(2, per_plan_results - 1),
        ),
    ]
    # Indian regulatory context: GST, CIBIL, RBI-specific searches
    plans.append(
        SearchPlan(
            name="gst_compliance",
            query=f'"{context.company_name}" GST GSTR compliance evasion invoice mismatch',
            category="regulatory",
            scope_hint="borrower",
            max_results=per_plan_results,
        )
    )
    plans.append(
        SearchPlan(
            name="cibil_check",
            query=f'"{context.company_name}" CIBIL credit bureau default NPA wilful defaulter',
            category="legal",
            scope_hint="borrower",
            max_results=per_plan_results,
        )
    )
    plans.append(
        SearchPlan(
            name="rbi_regulatory",
            query=f'"{context.company_name}" RBI regulatory action penalty direction',
            category="regulatory",
            scope_hint="borrower",
            include_domains=("rbi.org.in",),
            max_results=per_plan_results,
        )
    )
    # Indian financial data source targeting
    plans.append(
        SearchPlan(
            name="indian_financial_data",
            query=f'"{context.company_name}" financials quarterly results analysis',
            category="market",
            scope_hint="borrower",
            include_domains=("trendlyne.com", "moneycontrol.com", "screener.in"),
            max_results=per_plan_results,
        )
    )
    if context.cin:
        plans.append(
            SearchPlan(
                name="mca_lookup",
                query=f'"{context.cin}" MCA director charges annual return',
                category="promoter",
                scope_hint="borrower",
                include_domains=("mca.gov.in",),
                max_results=max(2, per_plan_results - 1),
            )
        )
    return plans


async def _execute_search_plan(plan: SearchPlan) -> list[dict]:
    primary_call = tavily_search(
        plan.query,
        max_results=plan.max_results,
        include_domains=plan.include_domains or None,
    )
    primary_results = await primary_call if asyncio.iscoroutine(primary_call) else primary_call
    if primary_results:
        return primary_results
    fallback_call = duckduckgo_search(
        plan.query,
        max_results=plan.max_results,
        site_filters=plan.include_domains or None,
    )
    return await fallback_call if asyncio.iscoroutine(fallback_call) else fallback_call


def _score_search_relevance(plan: SearchPlan, context: ResearchContext, title: str, summary: str, url: str) -> float:
    domain = _extract_domain(url)
    joined = f"{title} {summary}".lower()
    score = 0.10
    if _is_official_domain(domain):
        score += 0.10
    if any(alias.lower() in joined for alias in context.company_aliases):
        score += 0.32
    if context.nse_symbol and re.search(rf"\b{re.escape(context.nse_symbol.lower())}\b", joined):
        score += 0.10
    if context.cin and context.cin.lower() in joined:
        score += 0.25
    if any(term.lower() in joined for term in context.promoter_names):
        score += 0.12
    if plan.scope_hint in {"sector", "macro"} and any(term.lower() in joined for term in context.sector_terms):
        score += 0.14
    if any(term in joined for term in NEGATIVE_TERMS + POSITIVE_TERMS):
        score += 0.05
    if len(summary) > 120:
        score += 0.04
    return clamp(score, 0.05, 1.0)


def _normalize_result(plan: SearchPlan, context: ResearchContext, result: dict) -> dict | None:
    title = _compact_text(result.get("title"))
    summary = _compact_text(result.get("content") or result.get("snippet") or result.get("summary"))
    url = _unwrap_redirect_url(result.get("url", ""))
    if not title and not summary:
        return None
    category = classify_research_category(plan.query, title, url) or plan.category
    published_date = (
        _maybe_parse_date(result.get("published_date"))
        or _maybe_parse_date(result.get("published"))
        or _maybe_parse_date(result.get("date"))
    )
    return {
        "plan_name": plan.name,
        "category": category,
        "scope_hint": plan.scope_hint,
        "title": title or summary[:140],
        "summary": summary,
        "source_url": url or None,
        "source_name": _source_name_for_url(url),
        "published_date": published_date,
        "base_relevance": _score_search_relevance(plan, context, title, summary, url),
    }


def _dedupe_research_items(items: list[dict]) -> list[dict]:
    deduped: dict[str, dict] = {}
    for item in items:
        key = _canonicalize_url(item.get("source_url") or "") or _compact_text(item.get("title")).lower()
        existing = deduped.get(key)
        if existing is None or float(item.get("base_relevance") or 0) > float(existing.get("base_relevance") or 0):
            deduped[key] = item
    return list(deduped.values())


def _select_scrape_candidates(items: list[dict]) -> list[dict]:
    settings = get_settings()

    def candidate_key(item: dict) -> tuple[int, float]:
        domain = _extract_domain(item.get("source_url") or "")
        return (1 if _is_official_domain(domain) else 0, float(item.get("base_relevance") or 0))

    candidates = [item for item in items if item.get("source_url")]
    candidates.sort(key=candidate_key, reverse=True)
    return candidates[: settings.research_max_pages_to_scrape]


async def _enrich_with_firecrawl(items: list[dict]) -> None:
    semaphore = asyncio.Semaphore(4)

    async def scrape(item: dict) -> None:
        async with semaphore:
            payload = await firecrawl_scrape(item.get("source_url") or "")
        if not payload:
            return
        item["scraped_title"] = payload.get("title") or ""
        item["scraped_summary"] = payload.get("summary") or ""
        item["scraped_markdown"] = payload.get("markdown") or ""
        if payload.get("published_date") and not item.get("published_date"):
            item["published_date"] = payload["published_date"]

    await asyncio.gather(*(scrape(item) for item in _select_scrape_candidates(items)))


def _combined_text(item: dict) -> str:
    return _compact_text(
        " ".join(
            [
                str(item.get("title") or ""),
                str(item.get("summary") or ""),
                str(item.get("scraped_title") or ""),
                str(item.get("scraped_summary") or ""),
                str(item.get("scraped_markdown") or "")[:4000],
            ]
        )
    )


def _match_context(text: str, context: ResearchContext, scope_hint: str) -> EntityMatch:
    lowered = text.lower()
    matched_terms: list[str] = []
    scope = "generic"
    score = 0.0

    if context.cin and context.cin.lower() in lowered:
        matched_terms.append(f"CIN:{context.cin}")
        score = max(score, 0.98)
        scope = "borrower"
    if context.nse_symbol and re.search(rf"\b{re.escape(context.nse_symbol.lower())}\b", lowered):
        matched_terms.append(f"NSE:{context.nse_symbol}")
        score = max(score, 0.84)
        scope = "borrower"

    company_hits = [alias for alias in context.company_aliases if alias.lower() in lowered]
    if company_hits:
        matched_terms.extend(f"company:{alias}" for alias in company_hits[:3])
        score = max(score, 0.78 if len(max(company_hits, key=len)) >= 12 else 0.64)
        scope = "borrower"
    else:
        company_token_hits = [
            token for token in context.company_tokens if re.search(rf"\b{re.escape(token)}\b", lowered)
        ]
        if len(company_token_hits) >= 2:
            matched_terms.extend(f"token:{token}" for token in company_token_hits[:3])
            score = max(score, 0.58)
            scope = "borrower"

    promoter_hits = [name for name in context.promoter_names if name.lower() in lowered]
    if promoter_hits:
        matched_terms.extend(f"promoter:{name}" for name in promoter_hits[:2])
        score = max(score, 0.74)
        scope = "promoter"
    else:
        promoter_token_hits = [token for token in context.promoter_tokens if re.search(rf"\b{re.escape(token)}\b", lowered)]
        if len(promoter_token_hits) >= 2 and scope != "borrower":
            matched_terms.extend(f"promoter_token:{token}" for token in promoter_token_hits[:3])
            score = max(score, 0.52)
            scope = "promoter"

    sector_hits = [term for term in context.sector_terms if term.lower() in lowered]
    if sector_hits and scope == "generic":
        matched_terms.extend(f"sector:{term}" for term in sector_hits[:2])
        score = max(score, 0.42)
        scope = "sector" if scope_hint != "macro" else "macro"

    if scope_hint == "macro" and score < 0.35:
        score = max(score, 0.35)
        scope = "macro"
        matched_terms.append("macro-context")

    settings = get_settings()
    if score >= 0.75:
        status = "verified"
    elif score >= settings.research_min_entity_match_score:
        status = "probable"
    elif score >= settings.research_contextual_match_score and scope in {"sector", "macro"}:
        status = "contextual"
    else:
        status = "unverified"

    explanation = f"{scope} match at {score:.2f}"
    if matched_terms:
        explanation += f" via {', '.join(matched_terms[:4])}"
    return EntityMatch(
        scope=scope,
        score=score,
        status=status,
        matched_terms=tuple(matched_terms[:8]),
        explanation=explanation,
    )


def _triangulate_terms(text: str, extractions: list[Extraction] | None) -> tuple[str, ...]:
    if not extractions:
        return ()
    lowered = text.lower()
    matched: list[str] = []
    for extraction in extractions:
        if extraction.schema_field_key not in {"rating_action", "long_term_rating", "long_term_outlook", "rating_agency", "promoter_name"}:
            continue
        value = _compact_text(extraction.user_edited_value or extraction.value)
        if len(value) < 3:
            continue
        if value.lower() in lowered:
            matched.append(f"{extraction.schema_field_key}:{value}")
    return tuple(matched[:6])


def _assess_severity(item: dict, context: ResearchContext, match: EntityMatch) -> str:
    lowered = _combined_text(item).lower()
    adverse_hits = [term for term in NEGATIVE_TERMS if term in lowered]
    positive_hits = [term for term in POSITIVE_TERMS if term in lowered]
    category = item.get("category") or "news"

    if category == "legal":
        if match.status in {"verified", "probable"} and match.scope in {"borrower", "promoter"}:
            return "high" if adverse_hits else "medium"
        return "low"
    if category == "regulatory":
        if match.status == "verified" and match.scope == "borrower" and adverse_hits:
            return "high"
        if match.status in {"verified", "probable", "contextual"} and adverse_hits:
            return "medium"
        return "low"
    if category == "promoter":
        if match.status in {"verified", "probable"} and adverse_hits:
            return "high" if any(term in lowered for term in ["fraud", "default", "probe"]) else "medium"
        return "low"
    if category == "sector":
        return "medium" if adverse_hits else "low"
    if positive_hits and not adverse_hits:
        return "low"
    return "medium" if adverse_hits and match.status in {"verified", "probable"} else "low"


def _final_summary(item: dict) -> str:
    scraped_summary = _compact_text(item.get("scraped_summary") or "")
    if scraped_summary:
        return scraped_summary[:500]
    markdown = _compact_text(item.get("scraped_markdown") or "")
    if markdown:
        return markdown[:500]
    return _compact_text(item.get("summary") or "")[:500]


def _should_keep_item(item: dict, match: EntityMatch) -> bool:
    category = item.get("category") or "news"
    if category in {"legal", "promoter", "market", "news"}:
        return match.status in {"verified", "probable"}
    if category == "regulatory":
        return match.status in {"verified", "probable", "contextual"}
    if category == "sector":
        return match.status in {"verified", "probable", "contextual"}
    return match.status != "unverified"


def _final_relevance(item: dict, match: EntityMatch) -> float:
    score = float(item.get("base_relevance") or 0)
    score += match.score * 0.32
    if match.status == "verified":
        score += 0.14
    elif match.status == "probable":
        score += 0.08
    elif match.status == "contextual":
        score += 0.04
    return clamp(score, 0.05, 1.0)


def enrich_research_with_impact(items: list[dict]) -> list[dict]:
    for item in items:
        category = item.get("category")
        scope = item.get("entity_scope")
        if category in {"legal", "promoter"} and scope in {"borrower", "promoter"}:
            item["affected_c"] = "Character"
            item["impact_description"] = "Borrower or promoter-specific governance or legal developments affect management credibility."
        elif category == "regulatory":
            item["affected_c"] = "Conditions"
            item["impact_description"] = "Regulatory developments may alter compliance burden, liquidity planning, or funding access."
        elif category == "market":
            item["affected_c"] = "Conditions"
            item["impact_description"] = "Market and exchange disclosures influence funding access and external market perception."
        elif category == "sector":
            item["affected_c"] = "Conditions"
            item["impact_description"] = "Sector or macro trends influence future asset quality, funding costs, and growth."
        else:
            item["affected_c"] = "Capacity"
            item["impact_description"] = "Borrower-specific operating and performance news may affect repayment capacity."
    return items


def _sort_research_items(items: list[dict]) -> list[dict]:
    status_rank = {"verified": 3, "probable": 2, "contextual": 1, "unverified": 0}
    severity_rank = {"high": 3, "medium": 2, "low": 1, None: 0}
    scope_rank = {"borrower": 4, "promoter": 3, "sector": 2, "macro": 1, "generic": 0}

    def sort_key(item: dict) -> tuple[int, int, int, float, str]:
        domain = _extract_domain(item.get("source_url") or "")
        published = item.get("published_date")
        return (
            status_rank.get(item.get("verification_status"), 0),
            scope_rank.get(item.get("entity_scope"), 0),
            1 if _is_official_domain(domain) else severity_rank.get(item.get("severity"), 0),
            float(item.get("relevance_score") or 0),
            published.isoformat() if isinstance(published, date) else "",
        )

    return sorted(items, key=sort_key, reverse=True)


async def run_secondary_research(
    case: Case,
    *,
    nse_symbol: str | None = None,
    extractions: list[Extraction] | None = None,
) -> list[dict]:
    settings = get_settings()
    context = build_research_context(case, nse_symbol=nse_symbol, extractions=extractions)
    plans = _build_search_plans(context)
    raw_batches = await asyncio.gather(*(_execute_search_plan(plan) for plan in plans))

    items: list[dict] = []
    for plan, raw_results in zip(plans, raw_batches):
        for result in raw_results[: plan.max_results]:
            normalized = _normalize_result(plan, context, result)
            if normalized:
                items.append(normalized)

    items = _dedupe_research_items(items)
    await _enrich_with_firecrawl(items)

    filtered: list[dict] = []
    for item in items:
        combined_text = _combined_text(item)
        match = _match_context(combined_text, context, item.get("scope_hint") or "borrower")
        triangulation_terms = _triangulate_terms(combined_text, extractions)
        matched_terms = list(match.matched_terms)
        matched_terms.extend(term for term in triangulation_terms if term not in matched_terms)
        if not _should_keep_item(item, match):
            continue
        sentiment = analyze_sentiment(combined_text)
        severity = _assess_severity(item, context, match)
        filtered.append(
            {
                "category": item["category"],
                "title": item.get("scraped_title") or item.get("title"),
                "summary": _final_summary(item),
                "source_url": item.get("source_url"),
                "source_name": item.get("source_name"),
                "published_date": item.get("published_date") or date.today(),
                "sentiment": sentiment,
                "severity": severity,
                "relevance_score": _final_relevance(item, match),
                "entity_scope": match.scope,
                "entity_match_score": clamp(match.score, 0.0, 1.0),
                "verification_status": match.status,
                "matched_terms": _json_dumps(matched_terms),
                "match_explanation": match.explanation,
            }
        )

    market_data = get_market_data(nse_symbol)
    if market_data:
        filtered.append(
            {
                "category": "market",
                "title": f"{case.company_name} market snapshot",
                "summary": _json_dumps(market_data),
                "source_url": None,
                "source_name": "yfinance",
                "published_date": date.today(),
                "sentiment": "neutral",
                "severity": "low",
                "relevance_score": 0.72,
                "entity_scope": "borrower",
                "entity_match_score": 1.0,
                "verification_status": "verified",
                "matched_terms": _json_dumps([f"NSE:{nse_symbol}"] if nse_symbol else []),
                "match_explanation": "Market data is directly keyed off the borrower trading symbol.",
            }
        )

    filtered = enrich_research_with_impact(filtered)
    filtered = _sort_research_items(filtered)
    return filtered[: settings.research_max_results]
