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
