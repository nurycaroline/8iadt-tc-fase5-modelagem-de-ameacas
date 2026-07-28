"""Unit tests for domain models and AppConfig (T2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from stride_mvp.config import AppConfig, load_config
from stride_mvp.models import Detection, ThreatFinding, ThreatReport


def test_detection_requires_core_fields() -> None:
    det = Detection(
        class_name="rds",
        confidence=0.91,
        bbox_xyxy=(10.0, 20.0, 110.0, 120.0),
    )
    assert det.class_name == "rds"
    assert det.confidence == 0.91
    assert det.bbox_xyxy == (10.0, 20.0, 110.0, 120.0)
    assert det.family is None


def test_detection_accepts_optional_family() -> None:
    det = Detection(
        class_name="rds",
        confidence=0.5,
        bbox_xyxy=(0.0, 0.0, 1.0, 1.0),
        family="database",
    )
    assert det.family == "database"


def test_threat_finding_required_fields() -> None:
    finding = ThreatFinding(
        component_class="rds",
        family="database",
        stride_category="Information Disclosure",
        threat_description="Exposição de dados",
        vulnerability_example="ACL pública",
        countermeasure="Criptografia at-rest",
        mapped=True,
    )
    assert finding.mapped is True
    assert finding.stride_category == "Information Disclosure"


def test_threat_report_defaults_empty_notes() -> None:
    report = ThreatReport(
        source_image="arch1.png",
        detections=[],
        findings=[],
    )
    assert report.notes == []
    assert report.detections == []
    assert report.findings == []


def test_load_config_defaults() -> None:
    cfg = load_config()
    assert isinstance(cfg, AppConfig)
    assert cfg.confidence == pytest.approx(0.25)
    assert cfg.max_image_bytes == 10 * 1024 * 1024
    assert cfg.model_path.name.endswith(".pt") or cfg.model_path.as_posix()


def test_load_config_from_yaml(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        "confidence: 0.4\nmax_image_bytes: 2048\nmodel_path: /tmp/custom.pt\n",
        encoding="utf-8",
    )
    cfg = load_config(path)
    assert cfg.confidence == pytest.approx(0.4)
    assert cfg.max_image_bytes == 2048
    assert cfg.model_path == Path("/tmp/custom.pt")


def test_load_config_env_overrides(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("confidence: 0.4\n", encoding="utf-8")
    monkeypatch.setenv("STRIDE_CONF", "0.55")
    monkeypatch.setenv("STRIDE_MODEL_PATH", "/weights/best.pt")
    cfg = load_config(path)
    assert cfg.confidence == pytest.approx(0.55)
    assert cfg.model_path == Path("/weights/best.pt")
