"""CLI entrypoint for STRIDE MVP (analyze / prepare / train / ui)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from stride_mvp.config import load_config
from stride_mvp.pipeline.run import run_pipeline
from stride_mvp.pipeline.validate import ValidationError

app = typer.Typer(
    name="stride-mvp",
    help="MVP de modelagem de ameaças STRIDE a partir de diagramas.",
    no_args_is_help=True,
)

# Optional injectable detector for integration tests
_detector_override = None


def set_detector_override(detector) -> None:
    global _detector_override
    _detector_override = detector


@app.callback()
def main() -> None:
    """Stride MVP CLI."""


@app.command("analyze")
def analyze(
    image: Path = typer.Argument(..., exists=False, help="Caminho da imagem PNG/JPG"),
    out: Path = typer.Option(
        Path("reports"),
        "--out",
        "-o",
        help="Diretório de saída dos relatórios",
    ),
    conf: Optional[float] = typer.Option(
        None, "--conf", help="Limiar de confiança (override)"
    ),
) -> None:
    """Analisa um diagrama e grava relatório STRIDE (Markdown + JSON)."""
    cfg = load_config()
    if conf is not None:
        from dataclasses import replace

        cfg = replace(cfg, confidence=conf)
    try:
        report = run_pipeline(
            image,
            out,
            cfg,
            detector=_detector_override,
        )
    except ValidationError as exc:
        typer.secho(f"Erro de validação: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # noqa: BLE001
        typer.secho(f"Falha na análise: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.secho(
        f"Relatório gerado em {out}/{Path(image).stem}.md "
        f"({len(report.findings)} findings)",
        fg=typer.colors.GREEN,
    )


if __name__ == "__main__":
    app()
