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
