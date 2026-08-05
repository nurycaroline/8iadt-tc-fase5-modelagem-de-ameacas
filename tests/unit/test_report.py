"""Unit tests for ReportRenderer (T13–T14)."""

from __future__ import annotations

import json
from pathlib import Path

from stride_mvp.models import Detection, ThreatFinding, ThreatReport
from stride_mvp.stride.report import ReportRenderer


def _sample_report() -> ThreatReport:
    return ThreatReport(
        source_image="arch1.png",
        detections=[
            Detection("rds", 0.9, (0, 0, 1, 1), family="database"),
        ],
        findings=[
            ThreatFinding(
                component_class="rds",
                family="database",
                stride_category="Information Disclosure",
                threat_description="Exposição de dados",
                vulnerability_example="ACL pública",
                countermeasure="Criptografia at-rest",
                mapped=True,
            )
        ],
        notes=[],
    )


def test_markdown_pt_br_lists_required_fields() -> None:
    md = ReportRenderer().to_markdown(_sample_report())
    assert "Componente" in md
    assert "Categoria STRIDE" in md
    assert "Ameaça" in md
    assert "Vulnerabilidade" in md
    assert "Contramedida" in md
    assert "rds" in md
    assert "Information Disclosure" in md


def test_json_mirrors_findings() -> None:
    raw = ReportRenderer().to_json(_sample_report())
    data = json.loads(raw)
    assert data["source_image"] == "arch1.png"
    assert len(data["findings"]) == 1
    assert data["findings"][0]["component_class"] == "rds"
    assert data["findings"][0]["countermeasure"] == "Criptografia at-rest"
    # Legacy fields preserved
    expected_keys = {
        "component_class", "family", "stride_category",
        "threat_description", "vulnerability_example",
        "countermeasure", "mapped",
    }
    assert expected_keys.issubset(data["findings"][0].keys())


def test_json_v2_includes_role_instance_count_and_coverage() -> None:
    data = json.loads(ReportRenderer().to_json(_full_report()))
    assert "coverage" in data
    assert data["coverage"] == 0.75
    for finding in data["findings"]:
        assert "role" in finding
        assert "instance_count" in finding
    ec2 = next(f for f in data["findings"] if f["component_class"] == "ec2")
    assert ec2["role"] == "workload"
    assert ec2["instance_count"] == 1
    waf = next(f for f in data["findings"] if f["component_class"] == "waf")
    assert waf["role"] == "control"


def test_write_creates_md_and_json(tmp_path: Path) -> None:
    md_path, json_path = ReportRenderer().write(_sample_report(), tmp_path, "arch1")
    assert md_path.is_file()
    assert json_path.is_file()
    assert md_path.name == "arch1.md"
    assert json.loads(json_path.read_text(encoding="utf-8"))["findings"]


def test_empty_findings_markdown_has_note() -> None:
    report = ThreatReport(
        source_image="empty.png",
        detections=[],
        findings=[],
        notes=["Nenhuma detecção acima do limiar; relatório sem ameaças inventadas."],
    )
    md = ReportRenderer().to_markdown(report)
    assert "Observações" in md
    assert "Nenhuma detecção" in md
    assert "Nenhuma ameaça listada" in md
    data = json.loads(ReportRenderer().to_json(report))
    assert data["findings"] == []


def _full_report() -> ThreatReport:
    return ThreatReport(
        source_image="aws.png",
        detections=[
            Detection("ec2", 0.9, (0, 0, 1, 1), family="compute"),
            Detection("waf", 0.8, (1, 1, 2, 2), family="edge"),
            Detection("public_subnet", 0.7, (2, 2, 3, 3), family="zone"),
            Detection("weird_thing", 0.5, (3, 3, 4, 4), family="unknown"),
        ],
        findings=[
            ThreatFinding(
                component_class="ec2", family="compute",
                stride_category="Denial of Service",
                threat_description="t", vulnerability_example="v",
                countermeasure="c", mapped=True, role="workload", instance_count=1,
            ),
            ThreatFinding(
                component_class="waf", family="edge",
                stride_category="Spoofing",
                threat_description="Bypass de origem",
                vulnerability_example="v", countermeasure="c",
                mapped=True, role="control", instance_count=1,
            ),
            ThreatFinding(
                component_class="public_subnet", family="zone",
                stride_category="Tampering",
                threat_description="t", vulnerability_example="v",
                countermeasure="c", mapped=True, role="zone", instance_count=1,
            ),
            ThreatFinding(
                component_class="weird_thing", family="unknown",
                stride_category="Não classificado",
                threat_description="t", vulnerability_example="v",
                countermeasure="c", mapped=False, role="workload", instance_count=1,
            ),
        ],
        notes=[],
        coverage=0.75,
    )


def test_markdown_sections_in_role_order() -> None:
    md = ReportRenderer().to_markdown(_full_report())
    idx_summary = md.index("## Sumário")
    idx_workload = md.index("## Ameaças por componente")
    idx_control = md.index("## Controles detectados — verificações")
    idx_zone = md.index("## Zonas de rede — verificações estruturais")
    idx_inventory = md.index("## Inventário não classificado")
    assert idx_summary < idx_workload < idx_control < idx_zone < idx_inventory


def test_markdown_omits_inventory_when_no_unknown() -> None:
    report = _full_report()
    report = ThreatReport(
        source_image=report.source_image,
        detections=report.detections[:3],
        findings=report.findings[:3],
        notes=[],
        coverage=1.0,
    )
    md = ReportRenderer().to_markdown(report)
    assert "Inventário não classificado" not in md


def test_markdown_omits_role_sections_when_absent() -> None:
    # Only a workload finding → control/zone/inventory sections must be absent.
    report = ThreatReport(
        source_image="w.png",
        detections=[Detection("ec2", 0.9, (0, 0, 1, 1), family="compute")],
        findings=[
            ThreatFinding(
                component_class="ec2", family="compute",
                stride_category="Denial of Service",
                threat_description="t", vulnerability_example="v",
                countermeasure="c", mapped=True, role="workload", instance_count=1,
            )
        ],
        notes=[],
        coverage=1.0,
    )
    md = ReportRenderer().to_markdown(report)
    assert "## Ameaças por componente" in md
    assert "Controles detectados" not in md
    assert "Zonas de rede" not in md
    assert "Inventário não classificado" not in md


def test_markdown_omits_workload_section_when_only_controls() -> None:
    report = ThreatReport(
        source_image="c.png",
        detections=[Detection("waf", 0.9, (0, 0, 1, 1), family="edge")],
        findings=[
            ThreatFinding(
                component_class="waf", family="edge",
                stride_category="Spoofing",
                threat_description="t", vulnerability_example="v",
                countermeasure="c", mapped=True, role="control", instance_count=1,
            )
        ],
        notes=[],
        coverage=1.0,
    )
    md = ReportRenderer().to_markdown(report)
    assert "Controles detectados" in md
    assert "## Ameaças por componente" not in md


def test_markdown_summary_table_lists_components() -> None:
    md = ReportRenderer().to_markdown(_full_report())
    assert "## Sumário" in md
    assert "ec2" in md
    assert "waf" in md
    assert "public_subnet" in md
    assert "weird_thing" in md
    assert "Papel" in md
    assert "Instâncias" in md


def test_markdown_coverage_shown() -> None:
    md = ReportRenderer().to_markdown(_full_report())
    assert "Cobertura de mapeamento" in md
    assert "75%" in md
