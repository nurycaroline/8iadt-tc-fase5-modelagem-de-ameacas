"""YOLO training entrypoint (DET-01)."""

from __future__ import annotations

from pathlib import Path


def train(
    data_yaml: Path,
    epochs: int = 50,
    imgsz: int = 640,
    project: Path | None = None,
    model_name: str = "yolo11n.pt",
) -> Path:
    """Train Ultralytics YOLO and return path to ``best.pt``.

    Persists weights under ``project`` (default ``models/weights``).
    """
    from ultralytics import YOLO

    out_project = Path(project) if project is not None else Path("models/weights")
    out_project.mkdir(parents=True, exist_ok=True)

    model = YOLO(model_name)
    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        project=str(out_project),
        name="train",
        exist_ok=True,
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
