from types import SimpleNamespace

from backend.app.services.recommendation import check_hard_stops


def research_item(
    *,
    category: str,
    severity: str,
    title: str = "signal",
    summary: str = "",
    verification_status: str | None = None,
    entity_scope: str | None = None,
):
    return SimpleNamespace(
        category=category,
        severity=severity,
        title=title,
        summary=summary,
        verification_status=verification_status,
        entity_scope=entity_scope,
    )


def test_check_hard_stops_requires_verified_borrower_or_promoter_legal_match() -> None:
    hard_stops = check_hard_stops(
        [
            research_item(
                category="legal",
                severity="high",
                title="Generic NCLT cause list",
                verification_status="unverified",
                entity_scope="generic",
            ),
            research_item(
                category="legal",
                severity="high",
                title="Borrower insolvency petition",
                verification_status="verified",
                entity_scope="borrower",
            ),
        ],
        cross_checks=[],
    )

    assert hard_stops == ["High severity legal findings present."]
