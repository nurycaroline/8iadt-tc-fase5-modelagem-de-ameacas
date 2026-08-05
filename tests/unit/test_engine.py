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
    # ENG-01: unmapped components must NOT get an invented STRIDE category
    assert report.findings[0].stride_category == "Não classificado"
    assert report.findings[0].stride_category != "Information Disclosure"
    assert any("fallback" in n.lower() or "inventário" in n.lower() for n in report.notes)


def test_unmapped_never_uses_information_disclosure() -> None:
    engine = StrideEngine(ThreatKB.load(), load_class_map())
    report = engine.analyze(
        [
            Detection("totally_unknown_xyz", 0.6, (0, 0, 1, 1)),
            Detection("also_unknown_abc", 0.5, (2, 2, 3, 3)),
        ]
    )
    fallback_cats = {
        f.stride_category for f in report.findings if not f.mapped
    }
    assert fallback_cats == {"Não classificado"}
    assert "Information Disclosure" not in fallback_cats


def test_duplicate_detections_grouped_with_instance_count() -> None:
    engine = StrideEngine(ThreatKB.load(), load_class_map())
    report = engine.analyze(
        [Detection("ec2", 0.8, (float(i), float(i), float(i + 1), float(i + 1)))
         for i in range(6)]
    )
    ec2_findings = [f for f in report.findings if f.component_class == "ec2"]
    assert ec2_findings, "ec2 findings missing"
    assert all(f.instance_count == 6 for f in ec2_findings)
    # All detections still listed individually in the report
    assert len(report.detections) == 6


def test_zone_grouped_single_verification_with_count() -> None:
    engine = StrideEngine(ThreatKB.load(), load_class_map())
    report = engine.analyze(
        [Detection("public_subnet", 0.9, (0, 0, 1, 1)),
         Detection("public_subnet", 0.7, (1, 1, 2, 2))]
    )
    zone_findings = [f for f in report.findings if f.family == "zone"]
    assert len(zone_findings) == 1
    assert zone_findings[0].instance_count == 2


def test_finding_role_propagated_from_kb() -> None:
    engine = StrideEngine(ThreatKB.load(), load_class_map())
    report = engine.analyze([Detection("waf", 0.9, (0, 0, 1, 1))])
    edge_findings = [f for f in report.findings if f.family == "edge"]
    assert edge_findings
    assert all(f.role == "control" for f in edge_findings)


def test_zero_detections_no_invented_threats() -> None:
    engine = StrideEngine(ThreatKB.load(), load_class_map())
    report = engine.analyze([], source_image="empty.png")
    assert report.findings == []
    assert report.detections == []
    assert any("detecção" in n.lower() or "deteccao" in n.lower() for n in report.notes)


def test_coverage_mixed_mapped_and_unknown() -> None:
    engine = StrideEngine(ThreatKB.load(), load_class_map())
    report = engine.analyze(
        [
            Detection("rds", 0.9, (0, 0, 1, 1)),
            Detection("ec2", 0.8, (1, 1, 2, 2)),
            Detection("ec2", 0.7, (2, 2, 3, 3)),
            Detection("totally_unknown_xyz", 0.5, (3, 3, 4, 4)),
        ]
    )
    # 3 mapped instances (rds + 2 ec2) / 4 total → 0.75
    assert report.coverage == 0.75


def test_coverage_all_unknown_is_zero() -> None:
    engine = StrideEngine(ThreatKB.load(), load_class_map())
    report = engine.analyze(
        [Detection("totally_unknown_xyz", 0.5, (0, 0, 1, 1))]
    )
    assert report.coverage == 0.0


def test_coverage_none_when_zero_detections() -> None:
    engine = StrideEngine(ThreatKB.load(), load_class_map())
    report = engine.analyze([])
    assert report.coverage is None
