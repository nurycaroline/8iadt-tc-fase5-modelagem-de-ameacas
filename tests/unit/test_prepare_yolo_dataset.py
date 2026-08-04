"""Tests for scripts/prepare_yolo_dataset.py helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "prepare_yolo_dataset.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("prepare_yolo_dataset", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def prep():
    return _load_script()


def _write_minimal_voc_xml(path: Path, name: str = "rds") -> None:
    path.write_text(
        f"""<?xml version="1.0"?>
<annotation>
  <size><width>100</width><height>100</height><depth>3</depth></size>
  <object>
    <name>{name}</name>
    <bndbox><xmin>10</xmin><ymin>10</ymin><xmax>50</xmax><ymax>40</ymax></bndbox>
  </object>
</annotation>
""",
        encoding="utf-8",
    )


def test_find_voc_root_flat_layout(tmp_path: Path, prep) -> None:
    root = tmp_path / "raw" / "dataset_augmented"
    root.mkdir(parents=True)
    _write_minimal_voc_xml(root / "img1.xml")
    (root / "img1.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    found = prep.find_voc_root(tmp_path / "raw")
    assert found == root


def test_find_voc_root_classic_annotations(tmp_path: Path, prep) -> None:
    voc = tmp_path / "raw" / "VOC"
    ann = voc / "Annotations"
    ann.mkdir(parents=True)
    _write_minimal_voc_xml(ann / "a.xml")
    found = prep.find_voc_root(tmp_path / "raw")
    assert found == voc


def test_prepare_flat_end_to_end(tmp_path: Path, prep) -> None:
    voc = tmp_path / "dataset_augmented"
    voc.mkdir()
    _write_minimal_voc_xml(voc / "img1.xml", "rds")
    _write_minimal_voc_xml(voc / "img2.xml", "ec2")
    (voc / "img1.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (voc / "img2.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    out = tmp_path / "processed"
    data_yaml = prep.prepare(tmp_path, out, val_ratio=0.5, seed=1)
    assert data_yaml.is_file()
    assert (out / "labels" / "img1.txt").is_file()
    assert (out / "images" / "img1.png").is_file()
    assert (out / "images" / "train").is_dir()
    text = data_yaml.read_text(encoding="utf-8")
    assert "names:" in text
    assert "rds" in text or "ec2" in text
