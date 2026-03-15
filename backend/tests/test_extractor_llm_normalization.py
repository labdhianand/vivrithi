import asyncio

from backend.app.services.extractor import _coerce_bbox, _coerce_confidence, _coerce_page_number, _llm_extract


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


def test_llm_extract_returns_none_when_llm_errors(monkeypatch) -> None:
    async def _run() -> None:
        monkeypatch.setattr("backend.app.services.extractor.has_text_llm", lambda: True)

        def _raise(*args, **kwargs):
            raise RuntimeError("quota exceeded")

        monkeypatch.setattr("backend.app.services.extractor.generate_json", _raise)
        result = await _llm_extract(
            "<!-- PAGE 1 --> Gross NPA 1.8%",
            {"fields": [{"key": "gnpa_percent", "type": "percentage", "label": "GNPA %"}]},
            pages=None,
        )
        assert result is None

    asyncio.run(_run())
