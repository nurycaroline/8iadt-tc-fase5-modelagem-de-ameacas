"""Analyze helpers for Gradio UI (testable without launching the server)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from stride_mvp.config import load_config
from stride_mvp.pipeline.run import run_pipeline
from stride_mvp.stride.report import ReportRenderer


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

    run = pipeline_fn or (
        lambda image_path, out: run_pipeline(
            Path(image_path), Path(out), load_config()
        )
    )
    renderer = ReportRenderer()

    image_path = Path(image) if not hasattr(image, "save") else None
    if image_path is None:
        tmp = destination / "_upload.png"
        image.save(tmp)
        image_path = tmp

    report = run(image_path, destination)
    return renderer.to_markdown(report)
