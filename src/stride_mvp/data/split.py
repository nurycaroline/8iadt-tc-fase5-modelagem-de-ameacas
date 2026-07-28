"""Deterministic train/val split and Ultralytics data.yaml (DATA-01, DET-01)."""

from __future__ import annotations

import random
import shutil
from pathlib import Path

import yaml


def _list_image_stems(images_dir: Path) -> list[str]:
    stems: list[str] = []
    for pattern in ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.PNG"):
        for path in images_dir.glob(pattern):
            stems.append(path.stem)
    return sorted(set(stems))


def _find_image(images_dir: Path, stem: str) -> Path | None:
    for ext in (".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"):
        candidate = images_dir / f"{stem}{ext}"
        if candidate.is_file():
            return candidate
    return None


def write_split(
    processed_root: Path,
    val_ratio: float = 0.2,
    seed: int = 42,
    class_names: list[str] | None = None,
) -> Path:
    """Split ``processed_root`` into train/val and write Ultralytics ``data.yaml``.

    Expects ``images/`` and ``labels/`` under ``processed_root`` (flat files).
    Creates ``images/{train,val}`` and ``labels/{train,val}``, then
    ``data.yaml`` with keys ``train``, ``val``, and ``names``.
    """
    if not 0.0 < val_ratio < 1.0:
        raise ValueError("val_ratio must be between 0 and 1 (exclusive)")

    images_dir = processed_root / "images"
    labels_dir = processed_root / "labels"
    stems = _list_image_stems(images_dir)
    if not stems:
        raise FileNotFoundError(f"no images found under {images_dir}")

    rng = random.Random(seed)
    shuffled = list(stems)
    rng.shuffle(shuffled)
    n_val = max(1, int(round(len(shuffled) * val_ratio))) if len(shuffled) > 1 else 0
    if len(shuffled) == 1:
        n_val = 0
    val_stems = set(shuffled[:n_val])
    train_stems = [s for s in shuffled if s not in val_stems]
    if not train_stems and val_stems:
        # keep at least one train sample
        moved = val_stems.pop()
        train_stems = [moved]

    for split_name, split_stems in (
        ("train", train_stems),
        ("val", sorted(val_stems)),
    ):
        (images_dir / split_name).mkdir(parents=True, exist_ok=True)
        (labels_dir / split_name).mkdir(parents=True, exist_ok=True)
        for stem in split_stems:
            img = _find_image(images_dir, stem)
            if img is None:
                continue
            shutil.copy2(img, images_dir / split_name / img.name)
            label = labels_dir / f"{stem}.txt"
            if label.is_file():
                shutil.copy2(label, labels_dir / split_name / label.name)
            else:
                (labels_dir / split_name / f"{stem}.txt").write_text(
                    "", encoding="utf-8"
                )

    if class_names is None:
        classes_file = processed_root / "classes.txt"
        if classes_file.is_file():
            class_names = [
                line.strip()
                for line in classes_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        else:
            class_names = []

    data_yaml = {
        "path": str(processed_root.resolve()),
        "train": "images/train",
        "val": "images/val" if val_stems else "images/train",
        "names": {i: name for i, name in enumerate(class_names)},
    }
    out = processed_root / "data.yaml"
    out.write_text(yaml.safe_dump(data_yaml, sort_keys=False), encoding="utf-8")
    return out
