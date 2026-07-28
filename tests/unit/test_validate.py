"""Unit tests for ImageValidator (T15)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from stride_mvp.pipeline.validate import ValidationError, validate_image


def _write_png(path: Path, size: tuple[int, int] = (8, 8)) -> None:
    Image.new("RGB", size, color=(20, 40, 60)).save(path, format="PNG")


def test_valid_png(tmp_path: Path) -> None:
    path = tmp_path / "arch.png"
    _write_png(path)
    assert validate_image(path, max_bytes=1_000_000) == path


def test_valid_jpg(tmp_path: Path) -> None:
    path = tmp_path / "arch.jpg"
    Image.new("RGB", (8, 8), color=(1, 2, 3)).save(path, format="JPEG")
    assert validate_image(path, max_bytes=1_000_000) == path


def test_rejects_invalid_extension(tmp_path: Path) -> None:
    path = tmp_path / "arch.gif"
    path.write_bytes(b"GIF89a")
    with pytest.raises(ValidationError, match="formato"):
        validate_image(path, max_bytes=1_000_000)


def test_rejects_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.png"
    path.write_bytes(b"")
    with pytest.raises(ValidationError, match="vazio"):
        validate_image(path, max_bytes=1_000_000)


def test_rejects_oversized(tmp_path: Path) -> None:
    path = tmp_path / "big.png"
    _write_png(path)
    with pytest.raises(ValidationError, match="tamanho"):
        validate_image(path, max_bytes=1)
