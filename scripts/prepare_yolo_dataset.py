#!/usr/bin/env python3
"""Convert the Kaggle Software Architecture Dataset (Pascal VOC) to YOLO + split.

Handles the real Kaggle layout (flat PNG+XML under dataset_augmented/) and the
classic VOC layout (Annotations/ + JPEGImages/).

Usage (from repo root, with venv active):

    python scripts/prepare_yolo_dataset.py
    python scripts/prepare_yolo_dataset.py --raw data/raw/software-architecture-dataset
    python scripts/prepare_yolo_dataset.py --out data/processed --val-ratio 0.2 --seed 42
"""

from __future__ import annotations

import argparse
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Allow running without editable install when cwd is repo root
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from stride_mvp.data.split import write_split
from stride_mvp.data.voc_to_yolo import convert_voc_dir

DEFAULT_RAW = Path("data/raw/software-architecture-dataset")
DEFAULT_OUT = Path("data/processed")
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG")


def find_voc_root(raw: Path) -> Path:
    """Locate the directory that contains Pascal VOC XML annotations."""
    if not raw.exists():
        raise FileNotFoundError(
            f"Dataset path not found: {raw}\n"
            "Run ensure_dataset() / download first."
        )

    annotations = raw / "Annotations"
    if annotations.is_dir() and any(annotations.glob("*.xml")):
        return raw

    nested_ann = sorted(
        p for p in raw.rglob("Annotations") if p.is_dir() and any(p.glob("*.xml"))
    )
    if nested_ann:
        return nested_ann[0].parent

    # Flat layout (Kaggle): many *.xml next to *.png in the same folder
    flat_dirs = [
        p
        for p in raw.rglob("*")
        if p.is_dir() and any(p.glob("*.xml"))
    ]
    if raw.is_dir() and any(raw.glob("*.xml")):
        flat_dirs.append(raw)
    if not flat_dirs:
        raise FileNotFoundError(
            f"No Pascal VOC XML found under {raw}.\n"
            "Inspect with: find data/raw -name '*.xml' | head"
        )
    return max(flat_dirs, key=lambda p: len(list(p.glob("*.xml"))))


def discover_class_names(voc_root: Path) -> list[str]:
    """Collect unique object names from VOC XML files."""
    xml_paths = sorted((voc_root / "Annotations").glob("*.xml"))
    if not xml_paths:
        xml_paths = sorted(voc_root.glob("*.xml"))

    names: set[str] = set()
    for xml_path in xml_paths:
        root = ET.parse(xml_path).getroot()
        for obj in root.findall("object"):
            name = obj.findtext("name")
            if name:
                names.add(name.strip())
    if not names:
        raise RuntimeError(f"No object class names found in XMLs under {voc_root}")
    return sorted(names)


def find_image_for_stem(search_dirs: list[Path], stem: str) -> Path | None:
    for directory in search_dirs:
        for ext in IMAGE_EXTS:
            candidate = directory / f"{stem}{ext}"
            if candidate.is_file():
                return candidate
    return None


def image_search_dirs(voc_root: Path) -> list[Path]:
    dirs: list[Path] = []
    for name in ("JPEGImages", "images", "Images"):
        candidate = voc_root / name
        if candidate.is_dir():
            dirs.append(candidate)
    dirs.append(voc_root)  # flat layout: images beside XMLs
    # de-dupe while preserving order
    seen: set[Path] = set()
    unique: list[Path] = []
    for d in dirs:
        resolved = d.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(d)
    return unique


def copy_images(voc_root: Path, out: Path) -> int:
    """Copy images that have a matching YOLO label into ``out/images``."""
    labels_dir = out / "labels"
    img_out = out / "images"
    img_out.mkdir(parents=True, exist_ok=True)
    search = image_search_dirs(voc_root)

    copied = 0
    missing = 0
    for label in sorted(labels_dir.glob("*.txt")):
        src = find_image_for_stem(search, label.stem)
        if src is None:
            missing += 1
            continue
        shutil.copy2(src, img_out / src.name)
        copied += 1

    if copied == 0:
        raise FileNotFoundError(
            f"No images copied for labels in {labels_dir}. "
            f"Searched: {[str(d) for d in search]}"
        )
    if missing:
        print(f"warning: {missing} labels without matching image (skipped)")
    return copied


def prepare(
    raw: Path,
    out: Path,
    *,
    val_ratio: float = 0.2,
    seed: int = 42,
    skip_invalid: bool = True,
) -> Path:
    """Run VOC→YOLO conversion, image copy, and train/val split."""
    voc_root = find_voc_root(raw)
    print(f"VOC root: {voc_root}")

    class_names = discover_class_names(voc_root)
    print(f"classes: {len(class_names)}")

    out.mkdir(parents=True, exist_ok=True)
    stats = convert_voc_dir(
        voc_root, out, class_names, skip_invalid=skip_invalid
    )
    print(
        f"labels: converted={stats.converted} skipped={stats.skipped} "
        f"errors={len(stats.errors)}"
    )
    if stats.errors and skip_invalid:
        for err in stats.errors[:10]:
            print(f"  skip: {err}")
        if len(stats.errors) > 10:
            print(f"  ... and {len(stats.errors) - 10} more")

    n_img = copy_images(voc_root, out)
    print(f"images copied: {n_img}")

    data_yaml = write_split(
        out, val_ratio=val_ratio, seed=seed, class_names=class_names
    )
    print(f"data.yaml: {data_yaml}")
    return data_yaml


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Convert Kaggle Software Architecture Dataset (VOC XML) "
            "to YOLO labels + train/val split (data.yaml)."
        )
    )
    parser.add_argument(
        "--raw",
        type=Path,
        default=DEFAULT_RAW,
        help=f"Downloaded dataset root (default: {DEFAULT_RAW})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Processed YOLO dataset root (default: {DEFAULT_OUT})",
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.2,
        help="Validation split ratio (default: 0.2)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic split (default: 42)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on invalid XML instead of skipping",
    )
    args = parser.parse_args(argv)

    try:
        prepare(
            args.raw,
            args.out,
            val_ratio=args.val_ratio,
            seed=args.seed,
            skip_invalid=not args.strict,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
