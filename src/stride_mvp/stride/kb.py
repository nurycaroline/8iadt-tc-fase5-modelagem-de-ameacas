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
    roles: dict[str, str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.roles is None:
            self.roles = {}

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
        roles_raw = raw.get("roles") or {}
        roles: dict[str, str] = {}
        if isinstance(roles_raw, dict):
            for family, role in roles_raw.items():
                roles[str(family).strip().lower()] = str(role).strip().lower()
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
            roles=roles,
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

    def role(self, family: str) -> str:
        """Return the role of a family (default ``workload``)."""
        return self.roles.get(family.strip().lower(), "workload")

    def families(self) -> set[str]:
        """Return all families that have at least one KB entry."""
        return {e.family.lower() for e in self.entries}

    def fallback_entry(self, family: str) -> FallbackEntry:
        """Return the generic fallback (family documented for callers)."""
        _ = family  # reserved for future per-family fallbacks
        return self.fallback
