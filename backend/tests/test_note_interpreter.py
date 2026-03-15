from backend.app.services.note_interpreter import interpret_note


def test_interpret_note_detects_capacity_concern() -> None:
    result = interpret_note("Factory found operating at 40% capacity and collections were weak.", "site_visit")

    assert result["affected_c"] == "Capacity"
    assert result["sentiment"] == "negative"
    assert result["risk_adjustment"] <= -8


def test_interpret_note_detects_capital_support() -> None:
    result = interpret_note("Management highlighted strong capital position and comfortable CRAR levels.")

    assert result["affected_c"] == "Capital"
    assert result["sentiment"] == "positive"
    assert result["risk_adjustment"] >= 5
