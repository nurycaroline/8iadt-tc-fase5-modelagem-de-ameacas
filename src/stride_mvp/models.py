"""Domain models for detection and STRIDE threat reports."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Detection:
    """A single architecture-component detection from the vision model."""

    class_name: str
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]
    family: str | None = None


@dataclass(frozen=True)
class ThreatFinding:
    """One STRIDE finding tied to a detected (or fallback) component."""

    component_class: str
    family: str
    stride_category: str
    threat_description: str
    vulnerability_example: str
    countermeasure: str
    mapped: bool
    role: str = "workload"
    instance_count: int = 1


@dataclass
class ThreatReport:
    """Aggregated analysis result for one architecture image."""

    source_image: str
    detections: list[Detection]
    findings: list[ThreatFinding]
    notes: list[str] = field(default_factory=list)
    coverage: float | None = None
