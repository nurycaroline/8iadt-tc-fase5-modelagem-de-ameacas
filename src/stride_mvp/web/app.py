"""Minimal Gradio UI for architecture upload → STRIDE report (UI-01/02)."""

from __future__ import annotations

from typing import Callable

from stride_mvp.web.analyze import analyze_upload

# Gradio's "Paste from Clipboard" button uses navigator.clipboard.read(), which
# browsers only expose in secure contexts (HTTPS or http://localhost). On plain
# HTTP (e.g. LAN IP / docker host) that API is undefined and the button fails.
# Ctrl+V uses the paste event's clipboardData and works without that API.
PASTE_FALLBACK_JS = """
(() => {
  const DIAGRAM_ROOT = "#diagram-input";

  function findFileInput() {
    const root = document.querySelector(DIAGRAM_ROOT);
    if (!root) return null;
    return root.querySelector('input[type="file"]');
  }

  function assignFile(input, file) {
    const dt = new DataTransfer();
    dt.items.add(file);
    input.files = dt.files;
    input.dispatchEvent(new Event("change", { bubbles: true }));
    input.dispatchEvent(new Event("input", { bubbles: true }));
  }

  document.addEventListener(
    "paste",
    (event) => {
      const items = event.clipboardData && event.clipboardData.items;
      if (!items || !items.length) return;
      const input = findFileInput();
      if (!input) return;
      for (const item of items) {
        if (!item.type || !item.type.startsWith("image/")) continue;
        const file = item.getAsFile();
        if (!file) continue;
        event.preventDefault();
        assignFile(input, file);
        return;
      }
    },
    true
  );

  document.addEventListener(
    "click",
    (event) => {
      const btn =
        event.target && event.target.closest
          ? event.target.closest('button[aria-label="Paste from clipboard"]')
          : null;
      if (!btn) return;
      if (window.isSecureContext && navigator.clipboard && navigator.clipboard.read) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      alert(
        "Colar da área de transferência não está disponível neste contexto " +
          "(use https:// ou http://localhost).\\n\\n" +
          "Alternativas: Ctrl+V / Cmd+V com uma imagem copiada, ou Upload/arrastar o arquivo."
      );
    },
    true
  );
})();
"""


def create_app(pipeline_fn: Callable | None = None):
    """Build Gradio Blocks app; ``pipeline_fn`` injectable for tests."""
    import gradio as gr

    def _analyze(image) -> str:
        return analyze_upload(image, pipeline_fn=pipeline_fn)

    with gr.Blocks(title="STRIDE Threat Modeling MVP") as demo:
        gr.Markdown("# STRIDE Threat Modeling MVP")
        gr.Markdown(
            "Envie um diagrama de arquitetura (PNG/JPG) para gerar o relatório STRIDE.  \n"
            "Dica: **Upload**, arrastar o arquivo, ou **Ctrl+V / Cmd+V** para colar uma imagem.  \n"
            "O botão *Paste from Clipboard* só funciona em `https://` ou `http://localhost`."
        )
        inp = gr.Image(
            type="filepath",
            label="Diagrama",
            sources=["upload", "clipboard"],
            format="png",
            elem_id="diagram-input",
            height=360,
        )
        out = gr.Markdown(label="Relatório")
        btn = gr.Button("Analisar", variant="primary")
        btn.click(_analyze, inputs=inp, outputs=out)
    return demo


def launch_app(
    demo=None,
    *,
    pipeline_fn: Callable | None = None,
    server_name: str = "0.0.0.0",
    server_port: int = 7860,
):
    """Launch Gradio with clipboard paste fallback JS (Gradio 6: js on launch)."""
    app = demo if demo is not None else create_app(pipeline_fn=pipeline_fn)
    return app.launch(
        server_name=server_name,
        server_port=server_port,
        js=PASTE_FALLBACK_JS,
    )


def main() -> None:
    launch_app()


if __name__ == "__main__":
    main()
