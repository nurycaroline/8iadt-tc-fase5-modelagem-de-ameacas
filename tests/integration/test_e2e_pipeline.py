"""End-to-end pipeline integration with fake detector (T17) + DET-04 eval arches."""

from __future__ import annotations

from pathlib import Path

from stride_mvp.config import AppConfig
from stride_mvp.models import Detection
from stride_mvp.pipeline.run import run_pipeline

REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL = REPO_ROOT / "data" / "eval"

# Expected principal components from docs/eval-architectures.md
ARCH1_EXPECTED = {"client", "api", "database"}
ARCH2_EXPECTED = {"client", "compute", "storage", "database"}


class ScriptedDetector:
    """Returns predetermined detections (stands in for trained weights in CI)."""

    def __init__(self, class_names: set[str]) -> None:
        self.class_names = class_names

    def predict(self, image_path: Path) -> list[Detection]:
        _ = image_path
        return [
            Detection(name, 0.9, (float(i), float(i), float(i + 1), float(i + 1)))
            for i, name in enumerate(sorted(self.class_names))
        ]


def test_e2e_pipeline_with_fake_detector(tmp_path: Path) -> None:
    from PIL import Image

    image = tmp_path / "arch2.png"
    Image.new("RGB", (20, 20), color=(5, 5, 5)).save(image, format="PNG")
    out = tmp_path / "reports"
    report = run_pipeline(
        image,
        out,
        AppConfig(max_image_bytes=2_000_000),
        detector=ScriptedDetector({"rds", "ec2"}),
    )
    assert (out / "arch2.md").exists()
    assert (out / "arch2.json").exists()
    components = {f.component_class for f in report.findings}
    assert "rds" in components
    assert "ec2" in components


def test_eval_arch1_expected_components(tmp_path: Path) -> None:
    image = EVAL / "arch1" / "arch1.png"
    assert image.is_file()
    out = tmp_path / "reports"
    report = run_pipeline(
        image,
        out,
        AppConfig(max_image_bytes=2_000_000),
        detector=ScriptedDetector(ARCH1_EXPECTED),
    )
    components = {f.component_class for f in report.findings}
    assert ARCH1_EXPECTED.issubset(components)
    families = {d.family for d in report.detections}
    assert {"client", "api", "database"}.issubset(families)
    assert (out / "arch1.md").is_file()


def test_eval_arch2_expected_components(tmp_path: Path) -> None:
    image = EVAL / "arch2" / "arch2.png"
    assert image.is_file()
    out = tmp_path / "reports"
    report = run_pipeline(
        image,
        out,
        AppConfig(max_image_bytes=2_000_000),
        detector=ScriptedDetector(ARCH2_EXPECTED),
    )
    components = {f.component_class for f in report.findings}
    assert ARCH2_EXPECTED.issubset(components)
    assert (out / "arch2.md").is_file()


# Cenário AWS do review externo: serviços reais que antes caíam em fallback genérico.
AWS_REVIEW_COMPONENTS = {
    "cloudfront", "waf", "shield", "alb",
    "ec2", "solr", "auto_scaling",
    "rds", "elasticache", "efs", "backup",
    "kms", "cloudtrail", "cloudwatch",
    "public_subnet", "private_subnet",
}


def test_aws_review_scenario_no_generic_fallback_for_controls(tmp_path: Path) -> None:
    image = EVAL / "arch2" / "arch2.png"
    out = tmp_path / "reports"
    report = run_pipeline(
        image,
        out,
        AppConfig(max_image_bytes=2_000_000),
        detector=ScriptedDetector(AWS_REVIEW_COMPONENTS),
    )
    # Controles de proteção não devem cair no fallback genérico de inventário
    for control in ("waf", "shield", "kms", "cloudtrail", "cloudwatch"):
        control_findings = [f for f in report.findings if f.component_class == control]
        assert control_findings, f"{control} missing from findings"
        assert all(f.mapped for f in control_findings), (
            f"{control} fell back to inventory (not mapped)"
        )
        assert all(f.role == "control" for f in control_findings)
        # Nenhum controle deve usar o texto genérico de fallback ("superfície desconhecida")
        for f in control_findings:
            assert "superfície desconhecida" not in f.vulnerability_example.lower()
            assert "não classificado" not in f.stride_category.lower()
    # Cobertura alta: praticamente tudo mapeado
    assert report.coverage is not None
    assert report.coverage >= 0.9, f"coverage too low: {report.coverage}"
    # Nenhum finding em fallback deve usar categoria STRIDE inventada
    fallback_cats = {f.stride_category for f in report.findings if not f.mapped}
    assert fallback_cats.issubset({"Não classificado"})


def test_aws_review_scenario_dedupes_repeated_instances(tmp_path: Path) -> None:
    image = EVAL / "arch2" / "arch2.png"
    out = tmp_path / "reports"
    # 4 instâncias EC2 + 2 Solr → devem ser agrupadas
    dets = (
        [Detection("ec2", 0.9, (float(i), float(i), float(i + 1), float(i + 1)))
         for i in range(4)]
        + [Detection("solr", 0.8, (0.0, 0.0, 1.0, 1.0)),
            Detection("solr", 0.7, (1.0, 1.0, 2.0, 2.0))]
        + [Detection("rds", 0.9, (2.0, 2.0, 3.0, 3.0))]
    )

    class FixedDetector:
        def predict(self, image_path: Path) -> list[Detection]:
            _ = image_path
            return list(dets)

    report = run_pipeline(
        image,
        out,
        AppConfig(max_image_bytes=2_000_000),
        detector=FixedDetector(),
    )
    ec2 = [f for f in report.findings if f.component_class == "ec2"]
    solr = [f for f in report.findings if f.component_class == "solr"]
    assert all(f.instance_count == 4 for f in ec2)
    assert all(f.instance_count == 2 for f in solr)
    # 6 detecções EC2/Solr → 1 grupo cada (dedupe), não 6 blocos duplicados
    assert len({f.stride_category for f in ec2}) == len(ec2)
    assert (out / "arch2.md").is_file()


def _blob_for(report, class_name: str) -> str:
    parts = [
        f"{f.threat_description} {f.vulnerability_example} {f.countermeasure}"
        for f in report.findings
        if f.component_class == class_name
    ]
    return " ".join(parts).lower()


def test_fidelity_aws_arch1_semantics_forbid_wrong_vocab(tmp_path: Path) -> None:
    """REG-01 — Gemini review of arch1: EFS/Backup/SES/ASG/region semantics."""
    image = EVAL / "arch1" / "arch1.png"
    out = tmp_path / "reports"
    components = {
        "sei/sip",
        "rds",
        "alb",
        "efs",
        "backup",
        "aws_simple_email_service",
        "aws_autoscaling",
        "aws_region",
        "public_subnet",
        "vpc",
    }
    report = run_pipeline(
        image,
        out,
        AppConfig(max_image_bytes=2_000_000),
        detector=ScriptedDetector(components),
    )
    md = (out / "arch1.md").read_text(encoding="utf-8")

    efs = _blob_for(report, "efs")
    assert efs
    for forbidden in ("bucket", "block public access", "mfa delete"):
        assert forbidden not in efs
    assert "mount" in efs or "posix" in efs

    backup = _blob_for(report, "backup")
    assert backup
    assert "vault" in backup
    backup_findings = [f for f in report.findings if f.component_class == "backup"]
    assert all(f.role == "control" for f in backup_findings)

    ses = _blob_for(report, "aws_simple_email_service")
    assert ses
    for required in ("spf", "dkim", "dmarc"):
        assert required in ses
    for forbidden in ("fila", "dlq"):
        assert forbidden not in ses

    scaling = _blob_for(report, "aws_autoscaling")
    assert scaling
    for forbidden in ("escape de container", "imdsv2"):
        assert forbidden not in scaling
    scaling_findings = [
        f for f in report.findings if f.component_class == "aws_autoscaling"
    ]
    assert all(f.role == "control" for f in scaling_findings)

    region = [f for f in report.findings if f.component_class == "aws_region"]
    assert len(region) == 1
    assert region[0].role == "scope"
    assert region[0].stride_category == "Escopo"
    # Scope must not appear as a detailed STRIDE section heading
    assert "### 1. aws_region" not in md


def test_fidelity_azure_arch2_semantics_and_spatial_dedupe(tmp_path: Path) -> None:
    """REG-02 — Gemini review of arch2: Azure semantics + overlapping duplicates."""
    image = EVAL / "arch2" / "arch2.png"
    out = tmp_path / "reports"

    dets = [
        Detection("microsoft_entra", 0.4, (0.0, 0.0, 10.0, 10.0)),
        Detection("microsoft_entra", 0.88, (1.0, 1.0, 11.0, 11.0)),
        Detection("resource_group", 0.9, (20.0, 20.0, 30.0, 30.0)),
        Detection("api", 0.85, (40.0, 40.0, 50.0, 50.0)),
        Detection("logic_apps", 0.8, (60.0, 60.0, 70.0, 70.0)),
        Detection("sass_services", 0.75, (80.0, 80.0, 90.0, 90.0)),
        Detection("azure_services", 0.7, (100.0, 100.0, 110.0, 110.0)),
    ]

    class FixedDetector:
        def predict(self, image_path: Path) -> list[Detection]:
            _ = image_path
            return list(dets)

    report = run_pipeline(
        image,
        out,
        AppConfig(max_image_bytes=2_000_000, dedupe_iou=0.5, low_conf=0.5),
        detector=FixedDetector(),
    )
    md = (out / "arch2.md").read_text(encoding="utf-8")

    # Overlapping entra collapsed to 1 instance
    entra_dets = [d for d in report.detections if d.class_name == "microsoft_entra"]
    assert len(entra_dets) == 1
    entra_findings = [
        f for f in report.findings if f.component_class == "microsoft_entra"
    ]
    assert entra_findings
    assert all(f.instance_count == 1 for f in entra_findings)

    # Resource group is scope — no STRIDE categories
    rg = [f for f in report.findings if f.component_class == "resource_group"]
    assert len(rg) == 1
    assert rg[0].role == "scope"
    assert rg[0].stride_category == "Escopo"
    assert "### 1. resource_group" not in md

    for name in ("logic_apps", "sass_services"):
        blob = _blob_for(report, name)
        assert blob, f"{name} missing findings"
        for forbidden in ("container", "seccomp", "imdsv2", "hpa"):
            assert forbidden not in blob, f"{name} still uses {forbidden}"

    logic = _blob_for(report, "logic_apps")
    assert "managed identity" in logic or "rbac" in logic

    azure = _blob_for(report, "azure_services")
    assert azure
    assert "managed identity" in azure
    for forbidden in ("conectores saas", "conector saas", "consentimento"):
        assert forbidden not in azure
    azure_findings = [
        f for f in report.findings if f.component_class == "azure_services"
    ]
    assert all(f.family == "azure_platform" for f in azure_findings)


def test_fidelity_backend_rest_soap_requires_mtls(tmp_path: Path) -> None:
    """REST/SOAP backends must surface mTLS / secure transport findings."""
    image = EVAL / "arch2" / "arch2.png"
    out = tmp_path / "reports"
    report = run_pipeline(
        image,
        out,
        AppConfig(max_image_bytes=2_000_000),
        detector=ScriptedDetector({"rest_api", "soap", "api"}),
    )
    for name in ("rest_api", "soap"):
        blob = _blob_for(report, name)
        assert blob, f"{name} missing"
        assert "mtls" in blob
        findings = [f for f in report.findings if f.component_class == name]
        assert all(f.family == "backend" for f in findings)


def test_fidelity_database_disclosure_forbids_bucket(tmp_path: Path) -> None:
    image = EVAL / "arch1" / "arch1.png"
    out = tmp_path / "reports"
    report = run_pipeline(
        image,
        out,
        AppConfig(max_image_bytes=2_000_000),
        detector=ScriptedDetector({"rds", "elasticache"}),
    )
    for name in ("rds", "elasticache"):
        blob = _blob_for(report, name)
        assert "bucket" not in blob
