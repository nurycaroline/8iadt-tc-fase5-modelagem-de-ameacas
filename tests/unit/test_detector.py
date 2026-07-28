"""Unit tests for ComponentDetector (T9–T10)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from stride_mvp.detection.detector import ComponentDetector
from stride_mvp.models import Detection


def _install_fake_yolo(monkeypatch: pytest.MonkeyPatch, model: MagicMock) -> None:
    ultra = ModuleType("ultralytics")
    ultra.YOLO = MagicMock(return_value=model)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ultralytics", ultra)


def _box(cls_id: int, conf: float, xyxy: tuple[float, float, float, float]) -> SimpleNamespace:
    return SimpleNamespace(
        cls=[cls_id],
        conf=[conf],
        xyxy=[list(xyxy)],
    )


def test_predict_returns_class_conf_bbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    weights = tmp_path / "best.pt"
    weights.write_bytes(b"x")
    image = tmp_path / "arch.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")

    model = MagicMock()
    model.names = {0: "rds", 1: "ec2"}
    model.predict.return_value = [
        SimpleNamespace(boxes=[_box(0, 0.91, (10.0, 20.0, 30.0, 40.0))])
    ]
    _install_fake_yolo(monkeypatch, model)

    detector = ComponentDetector(weights, conf=0.25)
    dets = detector.predict(image)
    assert len(dets) == 1
    assert isinstance(dets[0], Detection)
    assert dets[0].class_name == "rds"
    assert dets[0].confidence == pytest.approx(0.91)
    assert dets[0].bbox_xyxy == (10.0, 20.0, 30.0, 40.0)


def test_below_threshold_excluded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    weights = tmp_path / "best.pt"
    weights.write_bytes(b"x")
    image = tmp_path / "arch.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")

    model = MagicMock()
    model.names = {0: "rds", 1: "ec2"}
    model.predict.return_value = [
        SimpleNamespace(
            boxes=[
                _box(0, 0.90, (0.0, 0.0, 1.0, 1.0)),
                _box(1, 0.10, (2.0, 2.0, 3.0, 3.0)),
            ]
        )
    ]
    _install_fake_yolo(monkeypatch, model)

    detector = ComponentDetector(weights, conf=0.25)
    # Bypass ultralytics conf filter: inject raw results through helper
    dets = detector._results_to_detections(model.predict.return_value)
    assert len(dets) == 1
    assert dets[0].class_name == "rds"


def test_zero_detections_returns_empty_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    weights = tmp_path / "best.pt"
    weights.write_bytes(b"x")
    image = tmp_path / "arch.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")

    model = MagicMock()
    model.names = {0: "rds"}
    model.predict.return_value = [SimpleNamespace(boxes=[])]
    _install_fake_yolo(monkeypatch, model)

    detector = ComponentDetector(weights, conf=0.25)
    assert detector.predict(image) == []


def test_zero_detections_when_results_list_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    weights = tmp_path / "best.pt"
    weights.write_bytes(b"x")
    model = MagicMock()
    model.names = {0: "rds"}
    _install_fake_yolo(monkeypatch, model)
    detector = ComponentDetector(weights, conf=0.25)
    assert detector._results_to_detections([]) == []


def test_unknown_class_name_still_returns_detection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unknown labels are fine at detect time; family is filled later by mapper."""
    weights = tmp_path / "best.pt"
    weights.write_bytes(b"x")
    image = tmp_path / "arch.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")

    model = MagicMock()
    model.names = {0: "brand_new_cloud_thing"}
    model.predict.return_value = [
        SimpleNamespace(boxes=[_box(0, 0.8, (1.0, 2.0, 3.0, 4.0))])
    ]
    _install_fake_yolo(monkeypatch, model)

    detector = ComponentDetector(weights, conf=0.25)
    dets = detector.predict(image)
    assert len(dets) == 1
    assert dets[0].class_name == "brand_new_cloud_thing"
    assert dets[0].family is None
