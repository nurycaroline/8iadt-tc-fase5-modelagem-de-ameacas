"""Map detector class names to STRIDE component families (DATA-02, KB-04)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_CLASS_MAP_PATH = Path("data/class_map.yaml")
DEFAULT_FAMILY = "unknown"
VENDOR_PREFIXES = ("aws_", "amazon_", "azure_", "gcp_", "google_")


def _normalize(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def _strip_vendor(key: str) -> str:
    for prefix in VENDOR_PREFIXES:
        if key.startswith(prefix):
            return key[len(prefix):]
    return key


@dataclass
class ClassFamilyMapper:
    """Lookup class_name → family with ``unknown`` fallback."""

    class_to_family: dict[str, str]
    default_family: str = DEFAULT_FAMILY
    _families: set[str] = field(default_factory=set, repr=False)

    def to_family(self, class_name: str) -> str:
        key = _normalize(class_name)
        family = self.class_to_family.get(key)
        if family is None:
            family = self.class_to_family.get(_strip_vendor(key))
        return family if family is not None else self.default_family

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
            key = _normalize(str(name))
            class_to_family[key] = str(family)

    # client/user alias: YAML key is ``client``; accept ``user`` as synonym family label
    if "client" in family_names:
        family_names.add("user")

    return ClassFamilyMapper(
        class_to_family=class_to_family,
        default_family=default_family,
        _families=family_names | {default_family},
    )


def unmapped_classes(class_names: list[str], mapper: ClassFamilyMapper) -> list[str]:
    """Return class names that resolve to the ``default_family`` (unknown)."""
    return [name for name in class_names if mapper.to_family(name) == mapper.default_family]


def read_class_names_from_weights(weights: Path) -> list[str]:
    """Read the ``names`` list from a YOLO weights file via Ultralytics."""
    from ultralytics import YOLO

    model = YOLO(str(weights))
    names = getattr(model, "names", None)
    if not names:
        return []
    if isinstance(names, dict):
        return [str(v) for v in names.values()]
    return [str(n) for n in names]
