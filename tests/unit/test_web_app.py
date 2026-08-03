"""Smoke + AC tests for Gradio UI (UI-01/UI-02)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest
from PIL import Image

from stride_mvp.models import Detection, ThreatFinding, ThreatReport
from stride_mvp.web.analyze import _coerce_image_path, analyze_upload


def test_create_app_exposes_upload_and_report_components(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("gradio")
    import stride_mvp.web.app as web_app

    monkeypatch.setattr(web_app, "analyze_upload", MagicMock(return_value="ok"))
    demo = web_app.create_app(pipeline_fn=lambda *_: None)
    assert demo is not None
    # Gradio Blocks store children; ensure Image + Markdown present in config
    config = demo.get_config_file() if hasattr(demo, "get_config_file") else None
    serialized = str(config) if config is not None else str(demo)
    assert "Diagrama" in serialized or "Image" in serialized
    assert "Relatório" in serialized or "Markdown" in serialized
    assert "diagram-input" in serialized
    assert "clipboard" in web_app.PASTE_FALLBACK_JS
    assert "Ctrl+V" in serialized or "colar" in serialized.lower()


def test_create_app_image_prefers_upload_and_clipboard_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("gradio")
    import stride_mvp.web.app as web_app

    monkeypatch.setattr(web_app, "analyze_upload", MagicMock(return_value="ok"))
    demo = web_app.create_app(pipeline_fn=lambda *_: None)
    config = demo.get_config_file()
    image_comps = [
        c
        for c in config.get("components", [])
        if c.get("props", {}).get("label") == "Diagrama"
        or c.get("type") == "image"
    ]
    assert image_comps, "expected Diagrama Image component in Gradio config"
    sources = image_comps[0]["props"].get("sources") or []
    assert "upload" in sources
    assert "clipboard" in sources
    assert "webcam" not in sources
    assert image_comps[0]["props"].get("format") == "png"
    assert image_comps[0]["props"].get("elem_id") == "diagram-input"


def test_analyze_upload_returns_markdown_report(tmp_path: Path) -> None:
    image = tmp_path / "upload.png"
    Image.new("RGB", (8, 8), color=(1, 1, 1)).save(image, format="PNG")

    fake_report = ThreatReport(
        source_image=str(image),
        detections=[Detection("rds", 0.9, (0, 0, 1, 1), family="database")],
        findings=[
            ThreatFinding(
                component_class="rds",
                family="database",
                stride_category="Information Disclosure",
                threat_description="Exposição",
                vulnerability_example="ACL",
                countermeasure="Criptografia",
                mapped=True,
            )
        ],
        notes=[],
    )

    md = analyze_upload(
        str(image),
        out_dir=tmp_path / "out",
        pipeline_fn=lambda *_: fake_report,
    )
    assert "Relatório de Modelagem de Ameaças" in md
    assert "rds" in md
    assert "Contramedida" in md


def test_analyze_upload_prompts_when_missing_image() -> None:
    assert "Envie uma imagem" in analyze_upload(None)


def test_coerce_image_path_accepts_pil_and_numpy(tmp_path: Path) -> None:
    pil = Image.new("RGB", (4, 4), color=(9, 9, 9))
    path = _coerce_image_path(pil, tmp_path)
    assert path.is_file()

    arr = np.zeros((4, 4, 3), dtype=np.uint8)
    path2 = _coerce_image_path(arr, tmp_path)
    assert path2.is_file()


def test_analyze_upload_handles_pil_paste_payload(tmp_path: Path) -> None:
    pil = Image.new("RGB", (6, 6), color=(2, 3, 4))
    fake_report = ThreatReport(
        source_image="pasted",
        detections=[],
        findings=[],
        notes=["ok"],
    )
    md = analyze_upload(
        pil,
        out_dir=tmp_path / "out",
        pipeline_fn=lambda *_: fake_report,
    )
    assert "Relatório de Modelagem de Ameaças" in md


def test_analyze_upload_handles_filedata_dict(tmp_path: Path) -> None:
    image = tmp_path / "clip.png"
    Image.new("RGB", (3, 3), color=(5, 5, 5)).save(image, format="PNG")
    fake_report = ThreatReport(
        source_image=str(image),
        detections=[],
        findings=[],
        notes=[],
    )
    md = analyze_upload(
        {"path": str(image), "orig_name": "clip.png"},
        out_dir=tmp_path / "out",
        pipeline_fn=lambda *_: fake_report,
    )
    assert "Relatório" in md
