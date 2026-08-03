"""Analyze helpers for Gradio UI (testable without launching the server)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from PIL import Image
from stride_mvp.config import load_config
from stride_mvp.pipeline.run import run_pipeline
from stride_mvp.stride.report import ReportRenderer


def _coerce_image_path(image: Any, destination: Path) -> Path:
    """Normalize Gradio upload/paste payloads to a local image path."""
    if image is None:
        raise ValueError("missing image")

    if isinstance(image, (str, Path)):
        path = Path(image)
        if not path.is_file():
            raise FileNotFoundError(f"Imagem não encontrada: {path}")
        return path

    # Gradio FileData-like dict (some versions / raw payloads)
    if isinstance(image, dict):
        for key in ("path", "name", "orig_name"):
            raw = image.get(key)
            if raw and Path(raw).is_file():
                return Path(raw)
        raise ValueError("payload de imagem inválido")

    destination.mkdir(parents=True, exist_ok=True)
    tmp = destination / "_upload.png"

    if hasattr(image, "save"):
        image.save(tmp)
        return tmp

    # numpy / array-like from Gradio type=numpy
    try:
        import numpy as np

        if isinstance(image, np.ndarray):
            Image.fromarray(image.astype("uint8")).save(tmp)
            return tmp
    except ImportError:
        pass

    raise TypeError(f"tipo de imagem não suportado: {type(image)!r}")


def analyze_upload(
    image,
    *,
    out_dir: Path | None = None,
    pipeline_fn: Callable | None = None,
) -> str:
    """Process an uploaded diagram and return Markdown report text (UI-01/02)."""
    if image is None:
        return "Envie uma imagem PNG/JPG."

    destination = Path(out_dir) if out_dir is not None else Path("reports")
    destination.mkdir(parents=True, exist_ok=True)

    try:
        image_path = _coerce_image_path(image, destination)
    except (OSError, TypeError, ValueError) as exc:
        return f"Não foi possível ler a imagem colada/enviada: {exc}"

    run = pipeline_fn or (
        lambda image_path, out: run_pipeline(
            Path(image_path), Path(out), load_config()
        )
    )
    renderer = ReportRenderer()
    report = run(image_path, destination)
    return renderer.to_markdown(report)
