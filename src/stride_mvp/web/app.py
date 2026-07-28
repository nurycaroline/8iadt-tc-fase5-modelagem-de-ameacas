"""Minimal Gradio UI for architecture upload → STRIDE report (UI-01/02)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from stride_mvp.config import load_config
from stride_mvp.pipeline.run import run_pipeline
from stride_mvp.stride.report import ReportRenderer


def create_app(pipeline_fn: Callable | None = None):
    """Build Gradio Blocks app; ``pipeline_fn`` injectable for tests."""
    import gradio as gr

    run = pipeline_fn or (
        lambda image_path, out_dir: run_pipeline(
            Path(image_path), Path(out_dir), load_config()
        )
    )
    renderer = ReportRenderer()

    def _analyze(image) -> str:
        if image is None:
            return "Envie uma imagem PNG/JPG."
        out_dir = Path("reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        # Gradio may pass a path string or numpy/PIL — normalize to path when possible
        image_path = Path(image) if not hasattr(image, "save") else None
        if image_path is None:
            tmp = out_dir / "_upload.png"
            image.save(tmp)
            image_path = tmp
        report = run(image_path, out_dir)
        return renderer.to_markdown(report)

    with gr.Blocks(title="STRIDE Threat Modeling MVP") as demo:
        gr.Markdown("# STRIDE Threat Modeling MVP")
        gr.Markdown("Envie um diagrama de arquitetura para gerar o relatório STRIDE.")
        inp = gr.Image(type="filepath", label="Diagrama")
        out = gr.Markdown(label="Relatório")
        btn = gr.Button("Analisar")
        btn.click(_analyze, inputs=inp, outputs=out)
    return demo


def main() -> None:
    create_app().launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
