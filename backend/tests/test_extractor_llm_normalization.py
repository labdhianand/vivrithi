from backend.app.services.extractor import _coerce_bbox, _coerce_confidence, _coerce_page_number


def test_coerce_page_number_handles_missing_values() -> None:
    assert _coerce_page_number(None) is None
    assert _coerce_page_number("3") == 3
    assert _coerce_page_number("0") is None


def test_coerce_confidence_falls_back_on_null() -> None:
    assert _coerce_confidence(None) == 0.75
    assert _coerce_confidence("0.91") == 0.91


def test_coerce_bbox_ignores_invalid_coordinates() -> None:
    assert _coerce_bbox(None) is None
    assert _coerce_bbox([0.1, "0.2", None, "bad"]) == (0.1, 0.2)
