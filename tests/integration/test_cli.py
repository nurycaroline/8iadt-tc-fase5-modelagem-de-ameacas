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


def test_check_map_help() -> None:
    result = runner.invoke(app, ["check-map", "--help"])
    assert result.exit_code == 0
    assert "classes" in result.stdout.lower() or "classes" in (result.stderr or "").lower()


def test_check_map_all_mapped_exits_zero(tmp_path: Path) -> None:
    classes = tmp_path / "classes.txt"
    classes.write_text("rds\nec2\nwaf\ncloudfront\n", encoding="utf-8")
    result = runner.invoke(app, ["check-map", "--classes", str(classes)])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "100%" in result.stdout or "100%" in (result.stderr or "")


def test_check_map_unmapped_class_exits_nonzero(tmp_path: Path) -> None:
    classes = tmp_path / "classes.txt"
    classes.write_text("rds\ntotally_unknown_xyz\n", encoding="utf-8")
    result = runner.invoke(app, ["check-map", "--classes", str(classes)])
    assert result.exit_code != 0
    assert "totally_unknown_xyz" in (result.stderr or "") or "totally_unknown_xyz" in result.stdout


def test_check_map_missing_source_exits_nonzero(tmp_path: Path) -> None:
    result = runner.invoke(app, ["check-map", "--classes", str(tmp_path / "nope.txt")])
    assert result.exit_code != 0
    # EC1: actionable message, not a traceback
    err = (result.stderr or "") + result.stdout
    assert "não encontrado" in err.lower() or "nope.txt" in err
    assert "Traceback" not in err


def test_check_map_no_source_exits_nonzero() -> None:
    result = runner.invoke(app, ["check-map"])
    assert result.exit_code != 0


def test_analyze_low_coverage_warns_but_exits_zero(tmp_path: Path) -> None:
    image = tmp_path / "arch.png"
    Image.new("RGB", (12, 12), color=(1, 2, 3)).save(image, format="PNG")
    out = tmp_path / "reports"

    class MixedDetector:
        def predict(self, image_path: Path) -> list[Detection]:
            _ = image_path
            return [
                Detection("rds", 0.9, (0.0, 0.0, 5.0, 5.0)),
                Detection("totally_unknown_xyz", 0.5, (1.0, 1.0, 2.0, 2.0)),
            ]

    set_detector_override(MixedDetector())
    try:
        result = runner.invoke(app, ["analyze", str(image), "--out", str(out)])
    finally:
        set_detector_override(None)
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "cobertura" in (result.stderr or "").lower() or "cobertura" in result.stdout.lower()
