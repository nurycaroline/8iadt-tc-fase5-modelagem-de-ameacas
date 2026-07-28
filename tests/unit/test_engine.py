"""Unit tests for StrideEngine (T12, T14 edges)."""

from __future__ import annotations

from pathlib import Path

from stride_mvp.data.class_map import load_class_map
from stride_mvp.models import Detection
from stride_mvp.stride.engine import STRIDE_CATEGORIES, StrideEngine
from stride_mvp.stride.kb import ThreatKB


def test_analyze_mentions_each_component() -> None:
    kb = ThreatKB.load()
    mapper = load_class_map()
    engine = StrideEngine(kb, mapper)
    detections = [
        Detection("rds", 0.9, (0, 0, 1, 1)),
        Detection("ec2", 0.8, (1, 1, 2, 2)),
    ]
    report = engine.analyze(detections, source_image="arch.png")
    classes = {f.component_class for f in report.findings}
    assert "rds" in classes
    assert "ec2" in classes
    assert len(report.detections) == 2
    assert all(d.family for d in report.detections)


def test_stride_categories_present_for_database() -> None:
    kb = ThreatKB.load()
    mapper = load_class_map()
    engine = StrideEngine(kb, mapper)
    report = engine.analyze(
        [Detection("rds", 0.9, (0, 0, 1, 1))],
        source_image="db.png",
    )
    cats = {f.stride_category for f in report.findings if f.component_class == "rds"}
    # KB lists all six STRIDE categories for database
    assert set(STRIDE_CATEGORIES).issubset(cats)


def test_unmapped_component_gets_explicit_fallback_finding(tmp_path: Path) -> None:
    kb_path = tmp_path / "kb.yaml"
    kb_path.write_text(
        "version: 1\n"
        "fallback:\n"
        "  threat: Fallback threat\n"
        "  vulnerability: Fallback vuln\n"
        "  countermeasure: Fallback fix\n"
        "entries: []\n",
        encoding="utf-8",
    )
    map_path = tmp_path / "map.yaml"
    map_path.write_text(
        "default_family: unknown\nfamilies:\n  database: [rds]\n",
        encoding="utf-8",
    )
    engine = StrideEngine(ThreatKB.load(kb_path), load_class_map(map_path))
    report = engine.analyze([Detection("weird_thing", 0.7, (0, 0, 1, 1))])
    assert len(report.findings) == 1
    assert report.findings[0].mapped is False
    assert "Fallback" in report.findings[0].threat_description
    assert any("fallback" in n.lower() or "mapeamento" in n.lower() for n in report.notes)


def test_zero_detections_no_invented_threats() -> None:
    engine = StrideEngine(ThreatKB.load(), load_class_map())
    report = engine.analyze([], source_image="empty.png")
    assert report.findings == []
    assert report.detections == []
    assert any("detecção" in n.lower() or "deteccao" in n.lower() for n in report.notes)
