"""Minimal Gradio UI for architecture upload → STRIDE report (UI-01/02)."""

from __future__ import annotations

from typing import Callable

from stride_mvp.web.analyze import analyze_upload


def create_app(pipeline_fn: Callable | None = None):
    """Build Gradio Blocks app; ``pipeline_fn`` injectable for tests."""
    import gradio as gr

    def _analyze(image) -> str:
        return analyze_upload(image, pipeline_fn=pipeline_fn)

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
