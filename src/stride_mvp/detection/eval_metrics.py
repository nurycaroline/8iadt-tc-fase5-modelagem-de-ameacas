"""Validation metrics export via Ultralytics model.val() (MET-01/02)."""

from __future__ import annotations

import json
from pathlib import Path


def evaluate(
    weights: Path,
    data_yaml: Path,
    out_path: Path | None = None,
) -> float:
    """Run validation and persist aggregate mAP to JSON; return the metric."""
    from ultralytics import YOLO

    model = YOLO(str(weights))
    metrics = model.val(data=str(data_yaml))
    # Prefer mAP50-95, then mAP50
    map_value = float(
        getattr(metrics.box, "map", None)
        or getattr(metrics.box, "map50", 0.0)
        or 0.0
    )
    destination = (
        Path(out_path)
        if out_path is not None
        else Path("models/weights/metrics.json")
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "weights": str(weights),
        "data": str(data_yaml),
        "map": map_value,
    }
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return map_value
