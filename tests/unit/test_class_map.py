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


def test_vendor_prefix_stripped_on_lookup() -> None:
    mapper = load_class_map()
    assert mapper.to_family("aws-waf") == mapper.to_family("waf")
    assert mapper.to_family("Amazon RDS") == "database"
    assert mapper.to_family("azure_sql_database") == mapper.to_family("sql_database")


def test_explicit_full_name_takes_precedence_over_base(tmp_path: Path) -> None:
    path = tmp_path / "map.yaml"
    path.write_text(
        "default_family: unknown\n"
        "families:\n"
        "  security: [aws_config]\n"
        "  observability: [config]\n",
        encoding="utf-8",
    )
    mapper = load_class_map(path)
    assert mapper.to_family("config") == "observability"
    assert mapper.to_family("aws_config") == "security"
    assert mapper.to_family("aws_config") != mapper.to_family("config")


def test_empty_class_falls_back() -> None:
    mapper = load_class_map()
    assert mapper.to_family("") == "unknown"
    assert mapper.to_family("   ") == "unknown"
