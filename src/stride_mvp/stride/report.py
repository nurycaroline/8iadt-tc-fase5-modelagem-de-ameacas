"""Render ThreatReport to Markdown (pt-BR) and JSON (STRIDE-03, PIPE-03)."""

from __future__ import annotations

import json
from pathlib import Path

from stride_mvp.models import ThreatFinding, ThreatReport


class ReportRenderer:
    """Serialize and persist threat reports."""

    def to_markdown(self, report: ThreatReport) -> str:
        lines = [
            "# Relatório de Modelagem de Ameaças (STRIDE)",
            "",
            f"**Imagem de origem:** `{report.source_image}`",
            "",
            f"**Detecções:** {len(report.detections)}",
            f"**Findings:** {len(report.findings)}",
            "",
        ]
        if report.notes:
            lines.append("## Observações")
            lines.append("")
            for note in report.notes:
                lines.append(f"- {note}")
            lines.append("")

        lines.append("## Ameaças identificadas")
        lines.append("")
        if not report.findings:
            lines.append("_Nenhuma ameaça listada._")
            lines.append("")
            return "\n".join(lines)

        for i, finding in enumerate(report.findings, start=1):
            lines.extend(self._finding_md(i, finding))
        return "\n".join(lines)

    def _finding_md(self, index: int, finding: ThreatFinding) -> list[str]:
        mapped = "sim" if finding.mapped else "não (fallback)"
        return [
            f"### {index}. {finding.component_class} — {finding.stride_category}",
            "",
            f"- **Componente:** {finding.component_class}",
            f"- **Família:** {finding.family}",
            f"- **Categoria STRIDE:** {finding.stride_category}",
            f"- **Ameaça:** {finding.threat_description}",
            f"- **Vulnerabilidade:** {finding.vulnerability_example}",
            f"- **Contramedida:** {finding.countermeasure}",
            f"- **Mapeado na KB:** {mapped}",
            "",
        ]

    def to_json(self, report: ThreatReport) -> str:
        payload = {
            "source_image": report.source_image,
            "notes": list(report.notes),
            "detections": [
                {
                    "class_name": d.class_name,
                    "confidence": d.confidence,
                    "bbox_xyxy": list(d.bbox_xyxy),
                    "family": d.family,
                }
                for d in report.detections
            ],
            "findings": [
                {
                    "component_class": f.component_class,
                    "family": f.family,
                    "stride_category": f.stride_category,
                    "threat_description": f.threat_description,
                    "vulnerability_example": f.vulnerability_example,
                    "countermeasure": f.countermeasure,
                    "mapped": f.mapped,
                }
                for f in report.findings
            ],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def write(
        self, report: ThreatReport, out_dir: Path, stem: str
    ) -> tuple[Path, Path]:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        md_path = out_dir / f"{stem}.md"
        json_path = out_dir / f"{stem}.json"
        md_path.write_text(self.to_markdown(report), encoding="utf-8")
        json_path.write_text(self.to_json(report) + "\n", encoding="utf-8")
        return md_path, json_path
