"""End-to-end pipeline integration with fake detector (T17) + DET-04 eval arches."""

from __future__ import annotations

from pathlib import Path

from stride_mvp.config import AppConfig
from stride_mvp.models import Detection
from stride_mvp.pipeline.run import run_pipeline

REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL = REPO_ROOT / "data" / "eval"

# Expected principal components from docs/eval-architectures.md
ARCH1_EXPECTED = {"client", "api", "database"}
ARCH2_EXPECTED = {"client", "compute", "storage", "database"}


class ScriptedDetector:
    """Returns predetermined detections (stands in for trained weights in CI)."""

    def __init__(self, class_names: set[str]) -> None:
        self.class_names = class_names

    def predict(self, image_path: Path) -> list[Detection]:
        _ = image_path
        return [
            Detection(name, 0.9, (float(i), float(i), float(i + 1), float(i + 1)))
            for i, name in enumerate(sorted(self.class_names))
        ]


def test_e2e_pipeline_with_fake_detector(tmp_path: Path) -> None:
    from PIL import Image

    image = tmp_path / "arch2.png"
    Image.new("RGB", (20, 20), color=(5, 5, 5)).save(image, format="PNG")
    out = tmp_path / "reports"
    report = run_pipeline(
        image,
        out,
        AppConfig(max_image_bytes=2_000_000),
        detector=ScriptedDetector({"rds", "ec2"}),
    )
    assert (out / "arch2.md").exists()
    assert (out / "arch2.json").exists()
    components = {f.component_class for f in report.findings}
    assert "rds" in components
    assert "ec2" in components


def test_eval_arch1_expected_components(tmp_path: Path) -> None:
    image = EVAL / "arch1" / "arch1.png"
    assert image.is_file()
    out = tmp_path / "reports"
    report = run_pipeline(
        image,
        out,
        AppConfig(max_image_bytes=2_000_000),
        detector=ScriptedDetector(ARCH1_EXPECTED),
    )
    components = {f.component_class for f in report.findings}
    assert ARCH1_EXPECTED.issubset(components)
    families = {d.family for d in report.detections}
    assert {"client", "api", "database"}.issubset(families)
    assert (out / "arch1.md").is_file()


def test_eval_arch2_expected_components(tmp_path: Path) -> None:
    image = EVAL / "arch2" / "arch2.png"
    assert image.is_file()
    out = tmp_path / "reports"
    report = run_pipeline(
        image,
        out,
        AppConfig(max_image_bytes=2_000_000),
        detector=ScriptedDetector(ARCH2_EXPECTED),
    )
    components = {f.component_class for f in report.findings}
    assert ARCH2_EXPECTED.issubset(components)
    assert (out / "arch2.md").is_file()
