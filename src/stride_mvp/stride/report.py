"""Render ThreatReport to Markdown (pt-BR) and JSON (STRIDE-03, PIPE-03)."""

from __future__ import annotations

import json
from pathlib import Path

from stride_mvp.models import ThreatFinding, ThreatReport

ROLE_TITLES = {
    "workload": "Ameaças por componente",
    "external": "Ameaças por componente",  # rendered together with workload
    "control": "Controles detectados — verificações",
    "zone": "Zonas de rede — verificações estruturais",
}
# Roles that share the "Ameaças por componente" section (rendered together).
THREAT_SECTION_ROLES = ("workload", "external")


class ReportRenderer:
    """Serialize and persist threat reports."""

    def to_markdown(self, report: ThreatReport) -> str:
        lines: list[str] = [
            "# Relatório de Modelagem de Ameaças (STRIDE)",
            "",
            f"**Imagem de origem:** `{report.source_image}`",
            "",
            f"**Detecções:** {len(report.detections)}",
            f"**Findings:** {len(report.findings)}",
        ]
        if report.coverage is not None:
            lines.append(f"**Cobertura de mapeamento:** {report.coverage:.0%}")
        lines.append("")

        if report.notes:
            lines.append("## Observações")
            lines.append("")
            for note in report.notes:
                lines.append(f"- {note}")
            lines.append("")

        if not report.findings:
            lines.append("## Ameaças identificadas")
            lines.append("")
            lines.append("_Nenhuma ameaça listada._")
            lines.append("")
            return "\n".join(lines)

        lines.extend(self._summary_table(report.findings))
        lines.append("")

        # Group findings by role, preserving role order; unknown → inventory section.
        by_role: dict[str, list[ThreatFinding]] = {}
        for f in report.findings:
            if not f.mapped:
                by_role.setdefault("__inventory__", []).append(f)
            else:
                by_role.setdefault(f.role, []).append(f)

        # Render workload + external together in one "Ameaças por componente" section.
        threat_findings = []
        for role in THREAT_SECTION_ROLES:
            threat_findings.extend(by_role.get(role, []))
        if threat_findings:
            lines.append(f"## {ROLE_TITLES['workload']}")
            lines.append("")
            for i, finding in enumerate(threat_findings, start=1):
                lines.extend(self._finding_md(i, finding))
            lines.pop()  # trailing blank line

        for role in ("control", "zone"):
            group = by_role.get(role)
            if not group:
                continue
            lines.append(f"## {ROLE_TITLES[role]}")
            lines.append("")
            for i, finding in enumerate(group, start=1):
                lines.extend(self._finding_md(i, finding))
            lines.pop()  # trailing blank line

        inventory = by_role.get("__inventory__")
        if inventory:
            lines.append("## Inventário não classificado")
            lines.append("")
            lines.append(
                "Componentes sem mapeamento para família STRIDE — inventariar "
                "antes de assumir risco:"
            )
            lines.append("")
            for i, finding in enumerate(inventory, start=1):
                lines.extend(self._finding_md(i, finding))
            lines.pop()

        return "\n".join(lines)

    def _summary_table(self, findings: list[ThreatFinding]) -> list[str]:
        lines = [
            "## Sumário",
            "",
            "| # | Componente | Família | Papel | Instâncias | Categorias STRIDE |",
            "|---|------------|---------|-------|-----------|------------------|",
        ]
        # Aggregate one row per component (categories collapsed) — not one per finding.
        per_component: dict[str, ThreatFinding] = {}
        order: list[str] = []
        cats_by_component: dict[str, list[str]] = {}
        for f in findings:
            if f.component_class not in per_component:
                per_component[f.component_class] = f
                order.append(f.component_class)
                cats_by_component[f.component_class] = []
            cats_by_component[f.component_class].append(f.stride_category)
        for i, cls in enumerate(order, start=1):
            f = per_component[cls]
            cats = ", ".join(cats_by_component[cls])
            lines.append(
                f"| {i} | {f.component_class} | {f.family} | {f.role} "
                f"| {f.instance_count} | {cats} |"
            )
        return lines

    def _finding_md(self, index: int, finding: ThreatFinding) -> list[str]:
        mapped = "sim" if finding.mapped else "não (inventário)"
        return [
            f"### {index}. {finding.component_class} — {finding.stride_category}",
            "",
            f"- **Componente:** {finding.component_class}",
            f"- **Família:** {finding.family}",
            f"- **Papel:** {finding.role}",
            f"- **Instâncias:** {finding.instance_count}",
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
            "coverage": report.coverage,
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
                    "role": f.role,
                    "instance_count": f.instance_count,
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
