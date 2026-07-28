"""Unit tests for Pascal VOC → YOLO conversion (T6)."""

from __future__ import annotations

from pathlib import Path

import pytest

from stride_mvp.data.voc_to_yolo import (
    VocConversionError,
    convert_voc_dir,
    voc_xml_to_yolo_lines,
)

MINI_VOC = """\
<annotation>
  <size>
    <width>100</width>
    <height>200</height>
  </size>
  <object>
    <name>rds</name>
    <bndbox>
      <xmin>10</xmin>
      <ymin>20</ymin>
      <xmax>50</xmax>
      <ymax>80</ymax>
    </bndbox>
  </object>
</annotation>
"""


def test_fixture_voc_to_normalized_yolo_line() -> None:
    lines = voc_xml_to_yolo_lines(MINI_VOC, ["rds", "ec2"])
    assert len(lines) == 1
    cls, xc, yc, w, h = lines[0].split()
    assert cls == "0"
    assert float(xc) == pytest.approx(0.30, abs=1e-5)
    assert float(yc) == pytest.approx(0.25, abs=1e-5)
    assert float(w) == pytest.approx(0.40, abs=1e-5)
    assert float(h) == pytest.approx(0.30, abs=1e-5)
    for v in (float(xc), float(yc), float(w), float(h)):
        assert 0.0 <= v <= 1.0


def test_invalid_xml_raises() -> None:
    with pytest.raises(VocConversionError, match="invalid VOC XML"):
        voc_xml_to_yolo_lines("<not-closed>", ["rds"])


def test_missing_bbox_raises() -> None:
    xml = """\
    <annotation>
      <size><width>10</width><height>10</height></size>
      <object><name>rds</name><bndbox><xmin>1</xmin></bndbox></object>
    </annotation>
    """
    with pytest.raises(VocConversionError, match="bbox"):
        voc_xml_to_yolo_lines(xml, ["rds"])


def test_convert_voc_dir_writes_labels_and_classes(tmp_path: Path) -> None:
    ann = tmp_path / "voc" / "Annotations"
    ann.mkdir(parents=True)
    (ann / "img1.xml").write_text(MINI_VOC, encoding="utf-8")
    out = tmp_path / "yolo"
    stats = convert_voc_dir(tmp_path / "voc", out, ["rds", "ec2"])
    assert stats.converted == 1
    label = (out / "labels" / "img1.txt").read_text(encoding="utf-8").strip()
    assert label.startswith("0 ")
    assert (out / "classes.txt").read_text(encoding="utf-8").splitlines() == [
        "rds",
        "ec2",
    ]


def test_convert_voc_dir_skip_invalid(tmp_path: Path) -> None:
    ann = tmp_path / "voc" / "Annotations"
    ann.mkdir(parents=True)
    (ann / "bad.xml").write_text("<broken", encoding="utf-8")
    (ann / "good.xml").write_text(MINI_VOC, encoding="utf-8")
    out = tmp_path / "yolo"
    stats = convert_voc_dir(
        tmp_path / "voc", out, ["rds"], skip_invalid=True
    )
    assert stats.converted == 1
    assert stats.skipped == 1
