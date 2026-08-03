"""Component detector: YOLO inference with confidence threshold (DET-02/03)."""

from __future__ import annotations

from pathlib import Path

from stride_mvp.config import resolve_model_path
from stride_mvp.models import Detection


class ComponentDetector:
    """Load YOLO weights and predict architecture component detections.

    Detections with confidence strictly below ``conf`` are excluded
    (not returned). Ultralytics may also apply its own conf filter;
    this class re-filters for a hard guarantee.
    """

    def __init__(self, weights: Path, conf: float = 0.25) -> None:
        from ultralytics import YOLO

        self.weights = resolve_model_path(Path(weights))
        self.conf = conf
        self._model = YOLO(str(self.weights))

    def predict(self, image_path: Path) -> list[Detection]:
        """Run inference; return detections at/above the confidence threshold."""
        results = self._model.predict(
            source=str(image_path),
            conf=self.conf,
            verbose=False,
        )
        return self._results_to_detections(results)

    def _results_to_detections(self, results: list) -> list[Detection]:
        detections: list[Detection] = []
        if not results:
            return detections

        names = getattr(self._model, "names", None) or {}
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None or len(boxes) == 0:
                continue
            for box in boxes:
                conf = float(box.conf[0]) if hasattr(box.conf, "__getitem__") else float(box.conf)
                if conf < self.conf:
                    continue
                cls_id = int(box.cls[0]) if hasattr(box.cls, "__getitem__") else int(box.cls)
                if isinstance(names, dict):
                    class_name = str(names.get(cls_id, cls_id))
                else:
                    class_name = str(names[cls_id]) if cls_id < len(names) else str(cls_id)
                xyxy = box.xyxy[0].tolist() if hasattr(box.xyxy[0], "tolist") else list(box.xyxy[0])
                detections.append(
                    Detection(
                        class_name=class_name,
                        confidence=conf,
                        bbox_xyxy=(float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])),
                    )
                )
        return detections
