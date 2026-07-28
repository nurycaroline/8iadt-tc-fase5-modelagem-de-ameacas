"""Map detector class names to STRIDE component families (DATA-02, KB-04)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_CLASS_MAP_PATH = Path("data/class_map.yaml")
DEFAULT_FAMILY = "unknown"


@dataclass
class ClassFamilyMapper:
    """Lookup class_name → family with ``unknown`` fallback."""

    class_to_family: dict[str, str]
    default_family: str = DEFAULT_FAMILY
    _families: set[str] = field(default_factory=set, repr=False)

    def to_family(self, class_name: str) -> str:
        key = class_name.strip().lower().replace(" ", "_").replace("-", "_")
        return self.class_to_family.get(key, self.default_family)

    @property
    def families(self) -> set[str]:
        return set(self._families)


def load_class_map(path: Path | None = None) -> ClassFamilyMapper:
    """Load ``data/class_map.yaml`` (or ``path``) into a mapper."""
    map_path = Path(path) if path is not None else DEFAULT_CLASS_MAP_PATH
    raw = yaml.safe_load(map_path.read_text(encoding="utf-8")) or {}
    default_family = str(raw.get("default_family", DEFAULT_FAMILY))
    families = raw.get("families") or {}
    if not isinstance(families, dict):
        raise ValueError(f"families must be a mapping in {map_path}")

    class_to_family: dict[str, str] = {}
    family_names: set[str] = set()
    for family, classes in families.items():
        family_names.add(str(family))
        for name in classes or []:
            key = str(name).strip().lower().replace(" ", "_").replace("-", "_")
            class_to_family[key] = str(family)

    # client/user alias: YAML key is ``client``; accept ``user`` as synonym family label
    if "client" in family_names:
        family_names.add("user")

    return ClassFamilyMapper(
        class_to_family=class_to_family,
        default_family=default_family,
        _families=family_names | {default_family},
    )
