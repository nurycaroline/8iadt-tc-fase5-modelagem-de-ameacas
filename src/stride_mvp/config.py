"""Application configuration for inference thresholds and paths."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_CONFIDENCE = 0.25
DEFAULT_MAX_IMAGE_BYTES = 10 * 1024 * 1024
DEFAULT_MODEL_PATH = Path("models/weights/best.pt")
TRAIN_OUTPUT_MODEL_PATH = Path("models/weights/train/weights/best.pt")
DEFAULT_MIN_COVERAGE = 0.8
DEFAULT_DEDUPE_IOU = 0.5
DEFAULT_LOW_CONF = 0.50


class MissingWeightsError(FileNotFoundError):
    """Raised when YOLO weights cannot be resolved for inference."""


def _parse_unit_interval(name: str, raw: str | float | int) -> float:
    """Parse a float that must lie in ``[0, 1]``; raise actionable ValueError."""
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} deve ser um número entre 0 e 1 (recebido: {raw!r})."
        ) from exc
    if not 0.0 <= value <= 1.0:
        raise ValueError(
            f"{name} deve estar no intervalo [0, 1] (recebido: {value})."
        )
    return value


@dataclass(frozen=True)
class AppConfig:
    """Runtime settings for the STRIDE MVP pipeline."""

    confidence: float = DEFAULT_CONFIDENCE
    max_image_bytes: int = DEFAULT_MAX_IMAGE_BYTES
    model_path: Path = DEFAULT_MODEL_PATH
    min_coverage: float = DEFAULT_MIN_COVERAGE
    dedupe_iou: float = DEFAULT_DEDUPE_IOU
    low_conf: float = DEFAULT_LOW_CONF


def model_path_candidates(configured: Path) -> list[Path]:
    """Ordered candidate locations for YOLO ``best.pt``.

    Supports the promoted path (``…/best.pt``) and Ultralytics train output
    (``…/train/weights/best.pt``), including the Docker mount at ``/weights``.
    """
    configured = Path(configured)
    parent = configured.parent
    candidates = [
        configured,
        parent / "train" / "weights" / "best.pt",
        DEFAULT_MODEL_PATH,
        TRAIN_OUTPUT_MODEL_PATH,
    ]
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[Path] = []
    for path in candidates:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def resolve_model_path(configured: Path | None = None) -> Path:
    """Return the first existing weights file among known locations.

    Raises:
        MissingWeightsError: when no candidate file exists.
    """
    configured_path = Path(configured) if configured is not None else DEFAULT_MODEL_PATH
    candidates = model_path_candidates(configured_path)
    for path in candidates:
        if path.is_file():
            return path

    tried = ", ".join(str(p) for p in candidates)
    raise MissingWeightsError(
        "Pesos YOLO não encontrados. Treine o modelo ou monte "
        f"`best.pt` no volume (ex.: {configured_path}). "
        "Após o treino, o artefato fica em "
        f"`{TRAIN_OUTPUT_MODEL_PATH}` (também promovido para "
        f"`{DEFAULT_MODEL_PATH}`). Caminhos tentados: {tried}."
    )


def load_config(path: Path | None = None) -> AppConfig:
    """Load config from optional YAML, then apply env overrides.

    Env overrides:
    - ``STRIDE_CONF`` — confidence threshold (float)
    - ``STRIDE_MODEL_PATH`` — path to YOLO weights
    - ``STRIDE_MAX_IMAGE_BYTES`` — max upload size in bytes
    - ``STRIDE_MIN_COVERAGE`` — mapping coverage warning threshold
    - ``STRIDE_DEDUPE_IOU`` — spatial dedupe IoU threshold (0 disables)
    - ``STRIDE_LOW_CONF`` — low-confidence marker threshold (0 disables)
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
    min_coverage = float(data.get("min_coverage", DEFAULT_MIN_COVERAGE))
    dedupe_iou = _parse_unit_interval(
        "dedupe_iou", data.get("dedupe_iou", DEFAULT_DEDUPE_IOU)
    )
    low_conf = _parse_unit_interval(
        "low_conf", data.get("low_conf", DEFAULT_LOW_CONF)
    )

    if (env_conf := os.environ.get("STRIDE_CONF")) is not None:
        confidence = float(env_conf)
    if (env_model := os.environ.get("STRIDE_MODEL_PATH")) is not None:
        model_path = Path(env_model)
    if (env_max := os.environ.get("STRIDE_MAX_IMAGE_BYTES")) is not None:
        max_image_bytes = int(env_max)
    if (env_cov := os.environ.get("STRIDE_MIN_COVERAGE")) is not None:
        min_coverage = float(env_cov)
    if (env_iou := os.environ.get("STRIDE_DEDUPE_IOU")) is not None:
        dedupe_iou = _parse_unit_interval("STRIDE_DEDUPE_IOU", env_iou)
    if (env_low := os.environ.get("STRIDE_LOW_CONF")) is not None:
        low_conf = _parse_unit_interval("STRIDE_LOW_CONF", env_low)

    return AppConfig(
        confidence=confidence,
        max_image_bytes=max_image_bytes,
        model_path=model_path,
        min_coverage=min_coverage,
        dedupe_iou=dedupe_iou,
        low_conf=low_conf,
    )
