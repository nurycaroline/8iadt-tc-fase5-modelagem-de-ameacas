"""STRIDE analysis engine — detections + mapper + KB → ThreatReport."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace

from stride_mvp.data.class_map import ClassFamilyMapper, _normalize, _strip_vendor
from stride_mvp.models import Detection, ThreatFinding, ThreatReport
from stride_mvp.stride.kb import ThreatKB

# Categories considered when expanding KB hits for a family
STRIDE_CATEGORIES = (
    "Spoofing",
    "Tampering",
    "Repudiation",
    "Information Disclosure",
    "Denial of Service",
    "Elevation of Privilege",
)


class StrideEngine:
    """Produce a ThreatReport covering applicable STRIDE categories."""

    def __init__(self, kb: ThreatKB, mapper: ClassFamilyMapper) -> None:
        self.kb = kb
        self.mapper = mapper

    def analyze(
        self,
        detections: list[Detection],
        *,
        source_image: str = "",
        low_conf: float = 0.5,
    ) -> ThreatReport:
        notes: list[str] = []
        findings: list[ThreatFinding] = []

        if not detections:
            notes.append(
                "Nenhuma detecção acima do limiar; relatório sem ameaças inventadas."
            )
            return ThreatReport(
                source_image=source_image,
                detections=[],
                findings=[],
                notes=notes,
            )

        # Enrich every detection with its family (kept individually in the report).
        enriched: list[Detection] = [
            replace(d, family=d.family or self.mapper.to_family(d.class_name))
            for d in detections
        ]

        # Group detections by normalized class name (vendor-stripped so that
        # ``aws-waf`` and ``waf`` collapse into one group) → one finding set per class.
        groups: dict[str, list[Detection]] = defaultdict(list)
        for det in enriched:
            groups[_strip_vendor(_normalize(det.class_name))].append(det)

        total_instances = 0
        mapped_instances = 0

        for class_key, group_dets in groups.items():
            rep = group_dets[0]
            family = rep.family or self.mapper.default_family
            count = len(group_dets)
            total_instances += count
            max_conf = max(d.confidence for d in group_dets)
            is_low = bool(low_conf > 0.0 and max_conf < low_conf)

            if family == self.mapper.default_family:
                self._add_inventory_finding(
                    findings,
                    notes,
                    rep.class_name,
                    family,
                    count,
                    max_confidence=max_conf,
                    low_confidence=is_low,
                )
                continue

            role = self.kb.role(family)
            if role == "scope":
                findings.append(
                    ThreatFinding(
                        component_class=rep.class_name,
                        family=family,
                        stride_category="Escopo",
                        threat_description=(
                            "Componente de escopo/agrupamento — sem superfície "
                            "de ameaça própria"
                        ),
                        vulnerability_example=(
                            "Não aplicável — fronteira lógica de gerenciamento"
                        ),
                        countermeasure=(
                            "Manter inventário do escopo; aplicar controles nos "
                            "workloads contidos"
                        ),
                        mapped=True,
                        role="scope",
                        instance_count=count,
                        max_confidence=max_conf,
                        low_confidence=is_low,
                    )
                )
                mapped_instances += count
                continue

            mapped_any = False
            for category in STRIDE_CATEGORIES:
                for hit in self.kb.lookup(family, category):
                    mapped_any = True
                    findings.append(
                        ThreatFinding(
                            component_class=rep.class_name,
                            family=family,
                            stride_category=hit.stride,
                            threat_description=hit.threat,
                            vulnerability_example=hit.vulnerability,
                            countermeasure=hit.countermeasure,
                            mapped=True,
                            role=role,
                            instance_count=count,
                            max_confidence=max_conf,
                            low_confidence=is_low,
                        )
                    )

            if mapped_any:
                mapped_instances += count
            else:
                self._add_inventory_finding(
                    findings,
                    notes,
                    rep.class_name,
                    family,
                    count,
                    max_confidence=max_conf,
                    low_confidence=is_low,
                )

        coverage = mapped_instances / total_instances if total_instances else None

        return ThreatReport(
            source_image=source_image,
            detections=enriched,
            findings=findings,
            notes=notes,
            coverage=coverage,
        )

    def _add_inventory_finding(
        self,
        findings: list[ThreatFinding],
        notes: list[str],
        class_name: str,
        family: str,
        count: int,
        *,
        max_confidence: float | None = None,
        low_confidence: bool = False,
    ) -> None:
        fb = self.kb.fallback_entry(family)
        findings.append(
            ThreatFinding(
                component_class=class_name,
                family=family,
                stride_category="Não classificado",
                threat_description=fb.threat,
                vulnerability_example=fb.vulnerability,
                countermeasure=fb.countermeasure,
                mapped=False,
                role="workload",
                instance_count=count,
                max_confidence=max_confidence,
                low_confidence=low_confidence,
            )
        )
        notes.append(
            f"Sem mapeamento KB específico para '{class_name}' "
            f"(família={family}); componente registrado no inventário."
        )
