"""End-to-end pipeline integration with fake detector (T17)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from stride_mvp.config import AppConfig
from stride_mvp.models import Detection
from stride_mvp.pipeline.run import run_pipeline


class FakeDetector:
    def predict(self, image_path: Path) -> list[Detection]:
        _ = image_path
        return [
            Detection("rds", 0.9, (0, 0, 1, 1)),
            Detection("ec2", 0.85, (2, 2, 3, 3)),
        ]


def test_e2e_pipeline_with_fake_detector(tmp_path: Path) -> None:
    image = tmp_path / "arch2.png"
    Image.new("RGB", (20, 20), color=(5, 5, 5)).save(image, format="PNG")
    out = tmp_path / "reports"
    report = run_pipeline(
        image,
        out,
        AppConfig(max_image_bytes=2_000_000),
        detector=FakeDetector(),
    )
    assert (out / "arch2.md").exists()
    assert (out / "arch2.json").exists()
    components = {f.component_class for f in report.findings}
    assert "rds" in components
    assert "ec2" in components
