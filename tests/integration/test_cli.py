"""Integration tests for CLI analyze (T17)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from typer.testing import CliRunner

from stride_mvp.cli import app, set_detector_override
from stride_mvp.models import Detection

runner = CliRunner()


class FakeDetector:
    def predict(self, image_path: Path) -> list[Detection]:
        _ = image_path
        return [Detection("rds", 0.95, (0.0, 0.0, 5.0, 5.0))]


def test_analyze_help() -> None:
    result = runner.invoke(app, ["analyze", "--help"])
    assert result.exit_code == 0
    assert "IMAGE" in result.stdout or "imagem" in result.stdout.lower()


def test_analyze_valid_image(tmp_path: Path) -> None:
    image = tmp_path / "arch.png"
    Image.new("RGB", (12, 12), color=(1, 2, 3)).save(image, format="PNG")
    out = tmp_path / "reports"
    set_detector_override(FakeDetector())
    try:
        result = runner.invoke(app, ["analyze", str(image), "--out", str(out)])
    finally:
        set_detector_override(None)
    assert result.exit_code == 0, result.stdout + result.stderr
    assert (out / "arch.md").is_file()
    assert (out / "arch.json").is_file()


def test_analyze_invalid_image_nonzero_exit(tmp_path: Path) -> None:
    image = tmp_path / "bad.txt"
    image.write_text("nope", encoding="utf-8")
    set_detector_override(FakeDetector())
    try:
        result = runner.invoke(
            app, ["analyze", str(image), "--out", str(tmp_path / "out")]
        )
    finally:
        set_detector_override(None)
    assert result.exit_code != 0
