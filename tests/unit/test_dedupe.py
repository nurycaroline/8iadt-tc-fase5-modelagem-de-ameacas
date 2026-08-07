"""Unit tests for spatial detection dedupe (DED-01..04)."""

from __future__ import annotations

from stride_mvp.detection.dedupe import containment, dedupe_detections, iou
from stride_mvp.models import Detection


def test_iou_identical_boxes_is_one() -> None:
    box = (0.0, 0.0, 10.0, 10.0)
    assert iou(box, box) == 1.0


def test_iou_disjoint_boxes_is_zero() -> None:
    assert iou((0.0, 0.0, 1.0, 1.0), (2.0, 2.0, 3.0, 3.0)) == 0.0


def test_containment_nested_box() -> None:
    outer = (0.0, 0.0, 10.0, 10.0)
    inner = (1.0, 1.0, 3.0, 3.0)
    assert containment(inner, outer) == 1.0
    assert containment(outer, inner) < 0.2


def test_dedupe_keeps_higher_confidence_when_iou_high() -> None:
    low = Detection("microsoft_entra", 0.4, (0.0, 0.0, 10.0, 10.0))
    high = Detection("microsoft_entra", 0.9, (1.0, 1.0, 11.0, 11.0))
    kept, removed = dedupe_detections([low, high], iou_threshold=0.5)
    assert removed == 1
    assert kept == [high]


def test_dedupe_by_containment_without_high_iou() -> None:
    outer = Detection("api", 0.8, (0.0, 0.0, 100.0, 100.0))
    inner = Detection("api", 0.6, (10.0, 10.0, 30.0, 30.0))
    # IoU of nested boxes is low, but containment of inner in outer is 1.0
    assert iou(outer.bbox_xyxy, inner.bbox_xyxy) < 0.5
    kept, removed = dedupe_detections([outer, inner], iou_threshold=0.5)
    assert removed == 1
    assert kept == [outer]


def test_dedupe_threshold_zero_is_noop() -> None:
    a = Detection("api", 0.9, (0.0, 0.0, 10.0, 10.0))
    b = Detection("api", 0.8, (0.0, 0.0, 10.0, 10.0))
    kept, removed = dedupe_detections([a, b], iou_threshold=0.0)
    assert removed == 0
    assert kept == [a, b]


def test_dedupe_preserves_disjoint_same_class() -> None:
    a = Detection("ec2", 0.9, (0.0, 0.0, 1.0, 1.0))
    b = Detection("ec2", 0.8, (5.0, 5.0, 6.0, 6.0))
    kept, removed = dedupe_detections([a, b], iou_threshold=0.5)
    assert removed == 0
    assert len(kept) == 2


def test_dedupe_never_removes_different_classes() -> None:
    zone = Detection("public_subnet", 0.9, (0.0, 0.0, 100.0, 100.0))
    alb = Detection("alb", 0.85, (10.0, 10.0, 40.0, 40.0))
    kept, removed = dedupe_detections([zone, alb], iou_threshold=0.5)
    assert removed == 0
    assert {d.class_name for d in kept} == {"public_subnet", "alb"}


def test_dedupe_chain_converges_to_one() -> None:
    a = Detection("microsoft_entra", 0.95, (0.0, 0.0, 10.0, 10.0))
    b = Detection("microsoft_entra", 0.80, (5.0, 0.0, 15.0, 10.0))
    c = Detection("microsoft_entra", 0.70, (10.0, 0.0, 20.0, 10.0))
    kept, removed = dedupe_detections([a, b, c], iou_threshold=0.3)
    assert removed == 2
    assert kept == [a]


def test_dedupe_normalizes_vendor_prefix_as_same_class() -> None:
    a = Detection("aws_waf", 0.9, (0.0, 0.0, 10.0, 10.0))
    b = Detection("waf", 0.7, (0.0, 0.0, 10.0, 10.0))
    kept, removed = dedupe_detections([a, b], iou_threshold=0.5)
    assert removed == 1
    assert kept[0].class_name == "aws_waf"
