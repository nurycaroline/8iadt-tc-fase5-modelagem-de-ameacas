"""Validate architecture diagram images before inference (PIPE-02)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg"}


class ValidationError(ValueError):
    """Raised when an input image fails validation."""


def validate_image(path: Path, max_bytes: int) -> Path:
    """Validate path, format (PNG/JPG), non-empty, and size ≤ max_bytes."""
    image_path = Path(path)
    if not image_path.is_file():
        raise ValidationError(f"arquivo não encontrado: {image_path}")

    suffix = image_path.suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ValidationError(
            f"formato inválido '{suffix}'; use PNG ou JPG ({image_path})"
        )

    size = image_path.stat().st_size
    if size == 0:
        raise ValidationError(f"arquivo vazio: {image_path}")
    if size > max_bytes:
        raise ValidationError(
            f"imagem excede o tamanho máximo ({size} > {max_bytes} bytes): {image_path}"
        )

    try:
        with Image.open(image_path) as img:
            img.verify()
    except Exception as exc:  # noqa: BLE001 — surface as ValidationError
        raise ValidationError(f"imagem corrompida ou ilegível: {image_path}") from exc

    return image_path
