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
