"""Unit tests for run_pipeline (T16)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from stride_mvp.config import AppConfig
from stride_mvp.data.class_map import load_class_map
from stride_mvp.models import Detection
from stride_mvp.pipeline.run import run_pipeline
from stride_mvp.pipeline.validate import ValidationError
from stride_mvp.stride.kb import ThreatKB


class FakeDetector:
    def __init__(self, detections: list[Detection] | None = None) -> None:
        self.detections = detections or [
            Detection("rds", 0.9, (0.0, 0.0, 10.0, 10.0)),
        ]

    def predict(self, image_path: Path) -> list[Detection]:
        _ = image_path
        return list(self.detections)


def _png(path: Path) -> None:
    Image.new("RGB", (16, 16), color=(10, 20, 30)).save(path, format="PNG")


def test_run_pipeline_writes_md_and_json(tmp_path: Path) -> None:
    image = tmp_path / "arch1.png"
    _png(image)
    out = tmp_path / "out"
    cfg = AppConfig(confidence=0.25, max_image_bytes=1_000_000)
    report = run_pipeline(
        image,
        out,
        cfg,
        detector=FakeDetector(),
        mapper=load_class_map(),
        kb=ThreatKB.load(),
    )
    assert (out / "arch1.md").is_file()
    assert (out / "arch1.json").is_file()
    assert report.findings
    assert any(f.component_class == "rds" for f in report.findings)


def test_invalid_image_raises_validation_error(tmp_path: Path) -> None:
    image = tmp_path / "bad.gif"
    image.write_bytes(b"GIF89a")
    with pytest.raises(ValidationError):
        run_pipeline(
            image,
            tmp_path / "out",
            AppConfig(max_image_bytes=1_000_000),
            detector=FakeDetector(),
        )
