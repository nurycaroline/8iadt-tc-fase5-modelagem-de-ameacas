"""Orchestrate validate → detect → map → STRIDE → report (PIPE-01/03/04)."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from stride_mvp.config import AppConfig, load_config
from stride_mvp.data.class_map import ClassFamilyMapper, load_class_map
from stride_mvp.models import Detection, ThreatReport
from stride_mvp.pipeline.validate import validate_image
from stride_mvp.stride.engine import StrideEngine
from stride_mvp.stride.kb import ThreatKB
from stride_mvp.stride.report import ReportRenderer


class DetectorProtocol(Protocol):
    def predict(self, image_path: Path) -> list[Detection]: ...


def run_pipeline(
    image: Path,
    out_dir: Path,
    cfg: AppConfig | None = None,
    *,
    detector: DetectorProtocol | None = None,
    mapper: ClassFamilyMapper | None = None,
    kb: ThreatKB | None = None,
    renderer: ReportRenderer | None = None,
) -> ThreatReport:
    """Run the full image→STRIDE report flow and write MD+JSON under ``out_dir``."""
    config = cfg or load_config()
    validate_image(image, max_bytes=config.max_image_bytes)

    if detector is None:
        from stride_mvp.detection.detector import ComponentDetector

        detector = ComponentDetector(config.model_path, conf=config.confidence)

    mapper = mapper or load_class_map()
    kb = kb or ThreatKB.load()
    renderer = renderer or ReportRenderer()

    detections = detector.predict(Path(image))
    engine = StrideEngine(kb, mapper)
    report = engine.analyze(detections, source_image=str(image))
    renderer.write(report, Path(out_dir), stem=Path(image).stem)
    return report
