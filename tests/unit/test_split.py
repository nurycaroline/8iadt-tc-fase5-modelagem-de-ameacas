"""Unit tests for train/val split and data.yaml (T7)."""

from __future__ import annotations

from pathlib import Path

import yaml

from stride_mvp.data.split import write_split


def _make_processed(root: Path, n: int = 10) -> None:
    images = root / "images"
    labels = root / "labels"
    images.mkdir(parents=True)
    labels.mkdir(parents=True)
    (root / "classes.txt").write_text("rds\nec2\n", encoding="utf-8")
    for i in range(n):
        (images / f"img{i}.jpg").write_bytes(b"\xff\xd8\xff")  # minimal jpeg-ish
        (labels / f"img{i}.txt").write_text("0 0.5 0.5 0.1 0.1\n", encoding="utf-8")


def test_data_yaml_contains_train_val_names(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    _make_processed(processed, n=10)
    yaml_path = write_split(processed, val_ratio=0.2, seed=42)
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    assert "train" in data
    assert "val" in data
    assert "names" in data
    assert data["names"][0] == "rds"
    assert data["names"][1] == "ec2"
    assert (processed / "images" / "train").is_dir()
    assert (processed / "images" / "val").is_dir()


def test_fixed_seed_is_reproducible(tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    _make_processed(a, n=10)
    _make_processed(b, n=10)
    write_split(a, val_ratio=0.3, seed=7)
    write_split(b, val_ratio=0.3, seed=7)
    train_a = sorted(p.name for p in (a / "images" / "train").iterdir())
    train_b = sorted(p.name for p in (b / "images" / "train").iterdir())
    val_a = sorted(p.name for p in (a / "images" / "val").iterdir())
    val_b = sorted(p.name for p in (b / "images" / "val").iterdir())
    assert train_a == train_b
    assert val_a == val_b


def test_different_seeds_can_differ(tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    _make_processed(a, n=20)
    _make_processed(b, n=20)
    write_split(a, val_ratio=0.3, seed=1)
    write_split(b, val_ratio=0.3, seed=2)
    val_a = sorted(p.name for p in (a / "images" / "val").iterdir())
    val_b = sorted(p.name for p in (b / "images" / "val").iterdir())
    assert val_a != val_b
