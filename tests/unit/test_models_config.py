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


def test_load_config_min_coverage_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    from stride_mvp.config import DEFAULT_MIN_COVERAGE

    assert load_config().min_coverage == pytest.approx(DEFAULT_MIN_COVERAGE)
    monkeypatch.setenv("STRIDE_MIN_COVERAGE", "0.95")
    assert load_config().min_coverage == pytest.approx(0.95)


def test_load_config_dedupe_and_low_conf_defaults() -> None:
    from stride_mvp.config import DEFAULT_DEDUPE_IOU, DEFAULT_LOW_CONF

    cfg = load_config()
    assert cfg.dedupe_iou == pytest.approx(DEFAULT_DEDUPE_IOU)
    assert cfg.low_conf == pytest.approx(DEFAULT_LOW_CONF)


def test_load_config_dedupe_and_low_conf_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STRIDE_DEDUPE_IOU", "0.7")
    monkeypatch.setenv("STRIDE_LOW_CONF", "0.3")
    cfg = load_config()
    assert cfg.dedupe_iou == pytest.approx(0.7)
    assert cfg.low_conf == pytest.approx(0.3)


def test_load_config_rejects_out_of_range_dedupe_iou(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STRIDE_DEDUPE_IOU", "1.5")
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        load_config()


def test_load_config_rejects_non_numeric_low_conf(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STRIDE_LOW_CONF", "abc")
    with pytest.raises(ValueError, match="número"):
        load_config()


def test_threat_finding_confidence_fields_default() -> None:
    finding = ThreatFinding(
        component_class="rds",
        family="database",
        stride_category="Spoofing",
        threat_description="t",
        vulnerability_example="v",
        countermeasure="c",
        mapped=True,
    )
    assert finding.max_confidence is None
    assert finding.low_confidence is False


def test_threat_finding_accepts_confidence_fields() -> None:
    finding = ThreatFinding(
        component_class="api",
        family="api",
        stride_category="Spoofing",
        threat_description="t",
        vulnerability_example="v",
        countermeasure="c",
        mapped=True,
        max_confidence=0.32,
        low_confidence=True,
    )
    assert finding.max_confidence == pytest.approx(0.32)
    assert finding.low_confidence is True


def test_resolve_model_path_uses_configured_when_present(tmp_path: Path) -> None:
    from stride_mvp.config import resolve_model_path

    weights = tmp_path / "best.pt"
    weights.write_bytes(b"x")
    assert resolve_model_path(weights) == weights


def test_resolve_model_path_falls_back_to_train_output(tmp_path: Path) -> None:
    from stride_mvp.config import resolve_model_path

    configured = tmp_path / "best.pt"
    train_best = tmp_path / "train" / "weights" / "best.pt"
    train_best.parent.mkdir(parents=True)
    train_best.write_bytes(b"trained")
    assert resolve_model_path(configured) == train_best


def test_resolve_model_path_raises_clear_error_when_missing(tmp_path: Path) -> None:
    from stride_mvp.config import MissingWeightsError, resolve_model_path

    missing = tmp_path / "missing" / "best.pt"
    with pytest.raises(MissingWeightsError, match="Pesos YOLO não encontrados"):
        resolve_model_path(missing)
