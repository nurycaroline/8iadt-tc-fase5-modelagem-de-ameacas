"""Smoke + AC tests for Gradio UI (UI-01/UI-02)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

from stride_mvp.models import Detection, ThreatFinding, ThreatReport
from stride_mvp.web.analyze import analyze_upload


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


def test_analyze_upload_reports_missing_weights(tmp_path: Path) -> None:
    from stride_mvp.config import MissingWeightsError

    image = tmp_path / "upload.png"
    Image.new("RGB", (8, 8), color=(1, 1, 1)).save(image, format="PNG")

    def boom(*_args):
        raise MissingWeightsError(
            "Pesos YOLO não encontrados. Treine o modelo ou monte `best.pt`."
        )

    md = analyze_upload(str(image), out_dir=tmp_path / "out", pipeline_fn=boom)
    assert md.startswith("**Erro:**")
    assert "Pesos YOLO não encontrados" in md


def test_analyze_upload_reports_validation_error(tmp_path: Path) -> None:
    from stride_mvp.pipeline.validate import ValidationError

    image = tmp_path / "upload.png"
    Image.new("RGB", (8, 8), color=(1, 1, 1)).save(image, format="PNG")

    def boom(*_args):
        raise ValidationError("formato inválido")

    md = analyze_upload(str(image), out_dir=tmp_path / "out", pipeline_fn=boom)
    assert md.startswith("**Erro de validação:**")
    assert "formato inválido" in md
