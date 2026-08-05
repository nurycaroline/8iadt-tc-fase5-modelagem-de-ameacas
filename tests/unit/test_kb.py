"""Unit tests for ThreatKB (T11)."""

from __future__ import annotations

from pathlib import Path

from stride_mvp.stride.kb import ThreatKB


def test_kb_loads_from_versioned_yaml() -> None:
    kb = ThreatKB.load()
    assert kb.version >= 1
    assert len(kb.entries) > 0
    assert kb.fallback.threat


def test_lookup_database_information_disclosure() -> None:
    kb = ThreatKB.load()
    hits = kb.lookup("database", "Information Disclosure")
    assert len(hits) >= 1
    assert hits[0].vulnerability
    assert hits[0].countermeasure


def test_fallback_for_missing_family(tmp_path: Path) -> None:
    path = tmp_path / "kb.yaml"
    path.write_text(
        "version: 1\n"
        "fallback:\n"
        "  threat: Genérica\n"
        "  vulnerability: Desconhecida\n"
        "  countermeasure: Revisar\n"
        "entries: []\n",
        encoding="utf-8",
    )
    kb = ThreatKB.load(path)
    assert kb.lookup("database", "Spoofing") == []
    fb = kb.fallback_entry("database")
    assert fb.threat == "Genérica"
    assert fb.vulnerability == "Desconhecida"
    assert fb.countermeasure == "Revisar"


def test_roles_loaded_from_v2_yaml() -> None:
    kb = ThreatKB.load()
    assert kb.version >= 2
    assert kb.role("edge") == "control"
    assert kb.role("observability") == "control"
    assert kb.role("security") == "control"
    assert kb.role("zone") == "zone"
    assert kb.role("client") == "external"
    assert kb.role("database") == "workload"
    assert kb.role("compute") == "workload"


def test_roles_default_workload_for_v1_yaml(tmp_path: Path) -> None:
    path = tmp_path / "kb.yaml"
    path.write_text(
        "version: 1\n"
        "fallback:\n"
        "  threat: Genérica\n"
        "  vulnerability: Desconhecida\n"
        "  countermeasure: Revisar\n"
        "entries:\n"
        "  - family: database\n"
        "    stride: Spoofing\n"
        "    threat: t\n"
        "    vulnerability: v\n"
        "    countermeasure: c\n",
        encoding="utf-8",
    )
    kb = ThreatKB.load(path)
    assert kb.role("edge") == "workload"
    assert kb.role("database") == "workload"


def test_edge_spoofing_mentions_origin_restriction() -> None:
    kb = ThreatKB.load()
    hits = kb.lookup("edge", "Spoofing")
    assert hits, "edge/Spoofing entry missing"
    text = (hits[0].threat + " " + hits[0].countermeasure).lower()
    assert "origem" in text or "cloudfront" in text


def test_edge_denial_of_service_mentions_waf_shield_efficacy() -> None:
    kb = ThreatKB.load()
    hits = kb.lookup("edge", "Denial of Service")
    assert hits
    text = (hits[0].vulnerability + " " + hits[0].countermeasure).lower()
    assert "waf" in text or "shield" in text


def test_observability_repudiation_mentions_audit_trail() -> None:
    kb = ThreatKB.load()
    hits = kb.lookup("observability", "Repudiation")
    assert hits
    text = (hits[0].threat + " " + hits[0].countermeasure).lower()
    assert "trilha" in text or "auditor" in text or "cloudtrail" in text


def test_observability_tampering_mentions_log_integrity() -> None:
    kb = ThreatKB.load()
    hits = kb.lookup("observability", "Tampering")
    assert hits
    text = (hits[0].threat + " " + hits[0].countermeasure).lower()
    assert "log" in text


def test_zone_has_single_structural_verification_entry() -> None:
    kb = ThreatKB.load()
    zone_entries = [e for e in kb.entries if e.family.lower() == "zone"]
    assert zone_entries, "zone entries missing"
    assert len(zone_entries) == 1, "zone should have a single structural verification entry"


def test_control_families_do_not_use_generic_exposure_text() -> None:
    kb = ThreatKB.load()
    control_families = {f for f, r in kb.roles.items() if r == "control"}
    forbidden = ("superfície desconhecida", "exposição de dados")
    for entry in kb.entries:
        if entry.family.lower() in control_families:
            blob = (entry.threat + " " + entry.vulnerability).lower()
            assert not any(w in blob for w in forbidden), (
                f"control family {entry.family} uses generic exposure text: {entry.threat}"
            )


def test_every_class_map_family_has_kb_entry() -> None:
    from stride_mvp.data.class_map import load_class_map

    mapper = load_class_map()
    kb = ThreatKB.load()
    kb_families = kb.families()
    # ``user`` is a synonym of ``client`` (alias added by the class_map loader)
    kb_families = kb_families | {"user"}
    missing = sorted(f for f in mapper.families if f != "unknown" and f not in kb_families)
    assert missing == [], f"families without KB entries: {missing}"
