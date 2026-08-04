"""YOLO training entrypoint (DET-01)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal


def resolve_train_device(device: str | int | None = None) -> str | int:
    """Pick a training device: explicit override, else CUDA → MPS → CPU."""
    if device is not None:
        return device
    try:
        import torch
    except ImportError:
        return "cpu"
    if torch.cuda.is_available():
        return 0
    mps = getattr(torch.backends, "mps", None)
    if mps is not None and mps.is_available():
        return "mps"
    return "cpu"


def train(
    data_yaml: Path,
    epochs: int = 50,
    imgsz: int = 640,
    project: Path | None = None,
    model_name: str = "yolo11n.pt",
    *,
    device: str | int | None = None,
    batch: int = 16,
    workers: int = 8,
    amp: bool = True,
    cache: bool | Literal["ram", "disk"] = False,
    fraction: float = 1.0,
) -> Path:
    """Train Ultralytics YOLO and return path to ``best.pt``.

    Persists weights under ``project`` (default ``models/weights``).

    On Apple Silicon, pass ``device="mps"`` (or leave ``device=None`` to
    auto-select MPS when available). Use a fixed ``batch`` on MPS — do not
    rely on Ultralytics AutoBatch (``batch=-1``), which is CUDA-oriented.
    """
    from ultralytics import YOLO

    out_project = Path(project) if project is not None else Path("models/weights")
    out_project.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_train_device(device)

    model = YOLO(model_name)
    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        project=str(out_project),
        name="train",
        exist_ok=True,
        device=resolved_device,
        batch=batch,
        workers=workers,
        amp=amp,
        cache=cache,
        fraction=fraction,
    )

    # Ultralytics exposes save_dir on the trainer / results
    save_dir = Path(getattr(results, "save_dir", out_project / "train"))
    best = save_dir / "weights" / "best.pt"
    if not best.is_file():
        # Fallback common layout
        alt = out_project / "train" / "weights" / "best.pt"
        if alt.is_file():
            return alt
        raise FileNotFoundError(f"training finished but best.pt not found under {save_dir}")
    return best
