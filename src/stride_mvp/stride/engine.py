"""STRIDE analysis engine — detections + mapper + KB → ThreatReport."""

from __future__ import annotations

from dataclasses import replace

from stride_mvp.data.class_map import ClassFamilyMapper
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
    ) -> ThreatReport:
        notes: list[str] = []
        enriched: list[Detection] = []
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

        for det in detections:
            family = det.family or self.mapper.to_family(det.class_name)
            enriched.append(replace(det, family=family))

            if family == self.mapper.default_family:
                fb = self.kb.fallback_entry(family)
                findings.append(
                    ThreatFinding(
                        component_class=det.class_name,
                        family=family,
                        stride_category="Não classificado",
                        threat_description=fb.threat,
                        vulnerability_example=fb.vulnerability,
                        countermeasure=fb.countermeasure,
                        mapped=False,
                    )
                )
                notes.append(
                    f"Sem mapeamento KB específico para '{det.class_name}' "
                    f"(família={family}); componente registrado no inventário."
                )
                continue

            mapped_any = False
            for category in STRIDE_CATEGORIES:
                hits = self.kb.lookup(family, category)
                for hit in hits:
                    mapped_any = True
                    findings.append(
                        ThreatFinding(
                            component_class=det.class_name,
                            family=family,
                            stride_category=hit.stride,
                            threat_description=hit.threat,
                            vulnerability_example=hit.vulnerability,
                            countermeasure=hit.countermeasure,
                            mapped=True,
                        )
                    )

            if not mapped_any:
                fb = self.kb.fallback_entry(family)
                findings.append(
                    ThreatFinding(
                        component_class=det.class_name,
                        family=family,
                        stride_category="Não classificado",
                        threat_description=fb.threat,
                        vulnerability_example=fb.vulnerability,
                        countermeasure=fb.countermeasure,
                        mapped=False,
                    )
                )
                notes.append(
                    f"Sem mapeamento KB específico para '{det.class_name}' "
                    f"(família={family}); componente registrado no inventário."
                )

        return ThreatReport(
            source_image=source_image,
            detections=enriched,
            findings=findings,
            notes=notes,
        )
