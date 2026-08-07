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


# Classes observed in the real AWS diagram review (must not fall back to unknown).
AWS_REVIEW_CLASSES = {
    "cloudfront": "edge",
    "waf": "edge",
    "shield": "edge",
    "alb": "api",
    "ec2": "compute",
    "solr": "compute",
    "auto_scaling": "scaling",
    "rds": "database",
    "elasticache": "database",
    "efs": "filesystem",
    "backup": "backup",
    "kms": "security",
    "cloudtrail": "observability",
    "cloudwatch": "observability",
    "public_subnet": "zone",
    "private_subnet": "zone",
    "vpc": "zone",
    "internet_gateway": "network",
    "nat_gateway": "network",
    "route53": "network",
}


def test_aws_review_vocabulary_resolves_without_fallback() -> None:
    mapper = load_class_map()
    missing = {c: mapper.to_family(c) for c in AWS_REVIEW_CLASSES
              if mapper.to_family(c) == "unknown"}
    assert missing == {}, f"classes fell back to unknown: {missing}"


def test_reclassifications_match_v2() -> None:
    mapper = load_class_map()
    assert mapper.to_family("cloudfront") == "edge"
    assert mapper.to_family("public_subnet") == "zone"
    assert mapper.to_family("cloudtrail") == "observability"
    assert mapper.to_family("waf") == "edge"


def test_fidelity_reallocations_match_semantic_families() -> None:
    """SEM/AZR map reallocations from Gemini review (stride-report-fidelity)."""
    mapper = load_class_map()
    expected = {
        "efs": "filesystem",
        "aws_elactic_file_system(nfs)_multi-az": "filesystem",
        "backup": "backup",
        "aws_backup": "backup",
        "ses": "email",
        "aws_simple_email_service": "email",
        "auto_scaling": "scaling",
        "auto_scaling_group": "scaling",
        "aws_autoscaling": "scaling",
        "aws_amazon_ec2_auto_scaling": "scaling",
        "aws_cloud": "management",
        "aws_region": "management",
        "resource_group": "management",
        "azure_resource_groups": "management",
        "logic_apps": "integration",
        "azure_logic_apps": "integration",
        "sass_services": "dependency",
        "azure_services": "azure_platform",
        "rest_api": "backend",
        "soap": "backend",
    }
    got = {label: mapper.to_family(label) for label in expected}
    assert got == expected


def test_kaggle_vocabulary_full_coverage() -> None:
    # MAP-02 canonical closure: every real Kaggle class resolves to a family.
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "kaggle_classes.txt"
    names = [n for n in fixture.read_text(encoding="utf-8").splitlines() if n.strip()]
    mapper = load_class_map()
    unmapped = [n for n in names if mapper.to_family(n) == "unknown"]
    assert unmapped == [], f"{len(unmapped)} unmapped: {unmapped}"
