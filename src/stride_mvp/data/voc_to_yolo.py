"""Convert Pascal VOC annotations to YOLO label files (DATA-02)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


class VocConversionError(ValueError):
    """Raised when a VOC annotation cannot be converted."""


@dataclass
class ConvertStats:
    converted: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


def _text(el: ET.Element | None, tag: str) -> str | None:
    if el is None:
        return None
    child = el.find(tag)
    if child is None or child.text is None:
        return None
    return child.text.strip()


def voc_xml_to_yolo_lines(
    xml_text: str, class_names: list[str]
) -> list[str]:
    """Parse one VOC XML string into YOLO label lines.

    Raises:
        VocConversionError: invalid XML, missing size, or missing bbox fields.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise VocConversionError(f"invalid VOC XML: {exc}") from exc

    size = root.find("size")
    w_s = _text(size, "width")
    h_s = _text(size, "height")
    if not w_s or not h_s:
        raise VocConversionError("VOC annotation missing size/width/height")
    img_w = float(w_s)
    img_h = float(h_s)
    if img_w <= 0 or img_h <= 0:
        raise VocConversionError("VOC size width/height must be positive")

    name_to_id = {n: i for i, n in enumerate(class_names)}
    lines: list[str] = []
    for obj in root.findall("object"):
        name = _text(obj, "name")
        if not name:
            raise VocConversionError("VOC object missing name")
        if name not in name_to_id:
            raise VocConversionError(f"unknown class '{name}' not in class_names")
        box = obj.find("bndbox")
        xmin = _text(box, "xmin")
        ymin = _text(box, "ymin")
        xmax = _text(box, "xmax")
        ymax = _text(box, "ymax")
        if None in (xmin, ymin, xmax, ymax):
            raise VocConversionError("VOC object missing bbox (xmin/ymin/xmax/ymax)")
        x0, y0, x1, y1 = map(float, (xmin, ymin, xmax, ymax))
        xc = ((x0 + x1) / 2.0) / img_w
        yc = ((y0 + y1) / 2.0) / img_h
        bw = (x1 - x0) / img_w
        bh = (y1 - y0) / img_h
        for v in (xc, yc, bw, bh):
            if not 0.0 <= v <= 1.0:
                raise VocConversionError(
                    f"normalized YOLO box out of [0,1]: {xc=} {yc=} {bw=} {bh=}"
                )
        cls_id = name_to_id[name]
        lines.append(f"{cls_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")
    return lines


def convert_voc_dir(
    voc_root: Path,
    out_root: Path,
    class_names: list[str],
    *,
    skip_invalid: bool = False,
) -> ConvertStats:
    """Convert a VOC directory (Annotations/*.xml) to YOLO labels under ``out_root``.

    Writes ``labels/*.txt`` and ``classes.txt`` / ``names`` listing ``class_names``.
    When ``skip_invalid`` is True, bad XMLs are counted as skipped; otherwise raise.
    """
    annotations = sorted((voc_root / "Annotations").glob("*.xml"))
    if not annotations:
        annotations = sorted(voc_root.glob("*.xml"))

    labels_dir = out_root / "labels"
    labels_dir.mkdir(parents=True, exist_ok=True)
    (out_root / "classes.txt").write_text(
        "\n".join(class_names) + ("\n" if class_names else ""),
        encoding="utf-8",
    )
    (out_root / "names").write_text(
        "\n".join(class_names) + ("\n" if class_names else ""),
        encoding="utf-8",
    )

    stats = ConvertStats()
    for xml_path in annotations:
        try:
            lines = voc_xml_to_yolo_lines(
                xml_path.read_text(encoding="utf-8"), class_names
            )
        except VocConversionError as exc:
            if skip_invalid:
                stats.skipped += 1
                stats.errors.append(f"{xml_path.name}: {exc}")
                continue
            raise VocConversionError(f"{xml_path}: {exc}") from exc
        (labels_dir / f"{xml_path.stem}.txt").write_text(
            "\n".join(lines) + ("\n" if lines else ""),
            encoding="utf-8",
        )
        stats.converted += 1
    return stats
