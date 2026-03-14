from __future__ import annotations

import asyncio
from pathlib import Path

from backend.app.services.runtime import build_fast_artifact, render_overlay_pdf


def test_render_overlay_pdf_from_fast_artifact(tmp_path) -> None:
    pdf_path = Path("claude_data/Aavas_Financiers/ALM/Disclosure_on_Liquidity_Coverage_Ratio_Q3_FY26.pdf")
    artifact = asyncio.run(build_fast_artifact(pdf_path, category="ALM", max_workers=2))
    overlay_path = tmp_path / "overlay.pdf"

    render_overlay_pdf(pdf_path, artifact, overlay_path)

    assert overlay_path.exists()
    assert overlay_path.stat().st_size > 0
