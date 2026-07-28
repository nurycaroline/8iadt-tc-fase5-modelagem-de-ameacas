"""CLI entrypoint (placeholder until analyze/train commands land)."""

from __future__ import annotations

import typer

app = typer.Typer(
    name="stride-mvp",
    help="MVP de modelagem de ameaças STRIDE a partir de diagramas.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """Stride MVP CLI."""


if __name__ == "__main__":
    app()
