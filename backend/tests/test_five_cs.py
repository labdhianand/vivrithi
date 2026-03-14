from types import SimpleNamespace

from backend.app.services.five_cs_scorer import score_five_cs, score_to_grade


def extraction(key: str, numeric: str | None = None, text: str | None = None):
    return SimpleNamespace(
        schema_field_key=key,
        value_numeric=None if numeric is None else __import__("decimal").Decimal(numeric),
        user_edited_value=None,
        value=text,
    )


def research(category: str, severity: str, sentiment: str = "neutral", title: str = "signal"):
    return SimpleNamespace(category=category, severity=severity, sentiment=sentiment, title=title)


def note(affected_c: str, risk_adjustment: int, note_type: str = "note", content: str = "analyst comment"):
    return SimpleNamespace(affected_c=affected_c, risk_adjustment=risk_adjustment, note_type=note_type, content=content)


def test_score_to_grade_mapping() -> None:
    assert score_to_grade(88) == "AAA"
    assert score_to_grade(76) == "AA"
    assert score_to_grade(61) == "BBB"
    assert score_to_grade(22) == "D"


def test_score_five_cs_returns_reasonable_scores() -> None:
    extractions = [
        extraction("promoter_holding_percent", "48.95"),
        extraction("profit_after_tax", "17004.57"),
        extraction("gnpa_percent", "1.19"),
        extraction("nnpa_percent", "0.79"),
        extraction("crar_percent", "46.39"),
        extraction("debt_equity_ratio", "3.07"),
        extraction("net_worth_lakhs", "485813.55"),
        extraction("lcr_ratio", "151.7"),
        extraction("rating_action", text="Reaffirmed"),
    ]
    research_items = [research("sector", "low", sentiment="neutral"), research("legal", "low")]
    notes = [note("Character", 3), note("Conditions", -2)]

    result = score_five_cs(extractions, research_items, notes)

    assert result["overall_score"] >= 60
    assert result["risk_grade"] in {"A", "AA", "AAA", "BBB"}
    assert result["character"].score > 60
    assert result["capacity"].score > 70

