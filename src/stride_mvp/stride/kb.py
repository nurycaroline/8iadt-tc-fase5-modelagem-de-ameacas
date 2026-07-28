"""Versioned STRIDE threat knowledge base (KB-01..04)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_KB_PATH = Path("data/kb/threats.yaml")


@dataclass(frozen=True)
class KBEntry:
    family: str
    stride: str
    threat: str
    vulnerability: str
    countermeasure: str


@dataclass(frozen=True)
class FallbackEntry:
    threat: str
    vulnerability: str
    countermeasure: str


@dataclass
class ThreatKB:
    entries: list[KBEntry]
    fallback: FallbackEntry
    version: int = 1

    @classmethod
    def load(cls, path: Path | None = None) -> ThreatKB:
        kb_path = Path(path) if path is not None else DEFAULT_KB_PATH
        raw = yaml.safe_load(kb_path.read_text(encoding="utf-8")) or {}
        fb = raw.get("fallback") or {}
        fallback = FallbackEntry(
            threat=str(fb.get("threat", "Ameaça genérica")),
            vulnerability=str(fb.get("vulnerability", "Não catalogada")),
            countermeasure=str(fb.get("countermeasure", "Revisar controles")),
        )
        entries: list[KBEntry] = []
        for item in raw.get("entries") or []:
            entries.append(
                KBEntry(
                    family=str(item["family"]),
                    stride=str(item["stride"]),
                    threat=str(item["threat"]),
                    vulnerability=str(item["vulnerability"]),
                    countermeasure=str(item["countermeasure"]),
                )
            )
        return cls(
            entries=entries,
            fallback=fallback,
            version=int(raw.get("version", 1)),
        )

    def lookup(self, family: str, category: str) -> list[KBEntry]:
        """Return KB entries matching family and STRIDE category (case-insensitive)."""
        fam = family.strip().lower()
        cat = category.strip().lower()
        return [
            e
            for e in self.entries
            if e.family.lower() == fam and e.stride.lower() == cat
        ]

    def fallback_entry(self, family: str) -> FallbackEntry:
        """Return the generic fallback (family documented for callers)."""
        _ = family  # reserved for future per-family fallbacks
        return self.fallback
