"""Application configuration for inference thresholds and paths."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_CONFIDENCE = 0.25
DEFAULT_MAX_IMAGE_BYTES = 10 * 1024 * 1024
DEFAULT_MODEL_PATH = Path("models/weights/best.pt")


@dataclass(frozen=True)
class AppConfig:
    """Runtime settings for the STRIDE MVP pipeline."""

    confidence: float = DEFAULT_CONFIDENCE
    max_image_bytes: int = DEFAULT_MAX_IMAGE_BYTES
    model_path: Path = DEFAULT_MODEL_PATH


def load_config(path: Path | None = None) -> AppConfig:
    """Load config from optional YAML, then apply env overrides.

    Env overrides:
    - ``STRIDE_CONF`` — confidence threshold (float)
    - ``STRIDE_MODEL_PATH`` — path to YOLO weights
    - ``STRIDE_MAX_IMAGE_BYTES`` — max upload size in bytes
    """
    data: dict = {}
    if path is not None:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            raise ValueError(f"Config file must be a mapping: {path}")
        data = raw

    confidence = float(data.get("confidence", DEFAULT_CONFIDENCE))
    max_image_bytes = int(data.get("max_image_bytes", DEFAULT_MAX_IMAGE_BYTES))
    model_path = Path(data.get("model_path", DEFAULT_MODEL_PATH))

    if (env_conf := os.environ.get("STRIDE_CONF")) is not None:
        confidence = float(env_conf)
    if (env_model := os.environ.get("STRIDE_MODEL_PATH")) is not None:
        model_path = Path(env_model)
    if (env_max := os.environ.get("STRIDE_MAX_IMAGE_BYTES")) is not None:
        max_image_bytes = int(env_max)

    return AppConfig(
        confidence=confidence,
        max_image_bytes=max_image_bytes,
        model_path=model_path,
    )
