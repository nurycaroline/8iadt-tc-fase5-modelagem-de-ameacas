"""Unit tests for class→family mapper (T5 / DATA-02, KB-04)."""

from __future__ import annotations

from pathlib import Path

from stride_mvp.data.class_map import load_class_map

REQUIRED_FAMILIES = {
    "database",
    "compute",
    "api",
    "storage",
    "network",
    "security",
    "messaging",
    "client",
    "unknown",
}


def test_default_class_map_covers_required_families() -> None:
    mapper = load_class_map()
    assert REQUIRED_FAMILIES.issubset(mapper.families)


def test_known_class_maps_to_family() -> None:
    mapper = load_class_map()
    assert mapper.to_family("rds") == "database"
    assert mapper.to_family("EC2") == "compute"
    assert mapper.to_family("api_gateway") == "api"
    assert mapper.to_family("user") == "client"


def test_unknown_class_falls_back() -> None:
    mapper = load_class_map()
    assert mapper.to_family("totally_unknown_xyz") == "unknown"


def test_load_class_map_from_custom_path(tmp_path: Path) -> None:
    path = tmp_path / "map.yaml"
    path.write_text(
        "default_family: unknown\nfamilies:\n  database: [mydb]\n",
        encoding="utf-8",
    )
    mapper = load_class_map(path)
    assert mapper.to_family("mydb") == "database"
    assert mapper.to_family("other") == "unknown"
