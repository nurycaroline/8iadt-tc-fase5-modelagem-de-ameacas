"""Smoke tests for Gradio UI factory (T21)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from stride_mvp.models import Detection, ThreatReport


def test_create_app_with_mocked_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("gradio")

    fake_report = ThreatReport(
        source_image="x.png",
        detections=[Detection("rds", 0.9, (0, 0, 1, 1), family="database")],
        findings=[],
        notes=["ok"],
    )

    def fake_pipeline(image_path, out_dir):
        _ = (image_path, out_dir)
        return fake_report

    # Avoid launching; just construct
    import stride_mvp.web.app as web_app

    monkeypatch.setattr(web_app, "run_pipeline", MagicMock())
    demo = web_app.create_app(pipeline_fn=fake_pipeline)
    assert demo is not None
