"""Spatial deduplication of overlapping detections (DED-01..04)."""

from __future__ import annotations

from stride_mvp.data.class_map import _normalize, _strip_vendor
from stride_mvp.models import Detection

# Fraction of the smaller box that must lie inside the other to count as duplicate.
_CONTAINMENT_THRESHOLD = 0.8
# Same-class boxes whose centers are closer than this × avg diagonal are duplicates
# (covers near-miss IoU on diagram icon double-reads).
_CENTER_DIST_RATIO = 0.55


def iou(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    """Intersection-over-union of two ``xyxy`` boxes."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0.0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0.0 else 0.0


def containment(
    inner: tuple[float, float, float, float],
    outer: tuple[float, float, float, float],
) -> float:
    """Fraction of ``inner`` area that intersects ``outer``."""
    ax1, ay1, ax2, ay2 = inner
    bx1, by1, bx2, by2 = outer
    area_inner = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    if area_inner <= 0.0:
        return 0.0
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    return inter / area_inner


def center_distance_ratio(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    """Distance between box centers divided by the average diagonal length."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    acx, acy = (ax1 + ax2) / 2.0, (ay1 + ay2) / 2.0
    bcx, bcy = (bx1 + bx2) / 2.0, (by1 + by2) / 2.0
    dist = ((acx - bcx) ** 2 + (acy - bcy) ** 2) ** 0.5
    diag_a = ((ax2 - ax1) ** 2 + (ay2 - ay1) ** 2) ** 0.5
    diag_b = ((bx2 - bx1) ** 2 + (by2 - by1) ** 2) ** 0.5
    avg_diag = (diag_a + diag_b) / 2.0
    if avg_diag <= 0.0:
        return float("inf")
    return dist / avg_diag


def _class_key(class_name: str) -> str:
    return _strip_vendor(_normalize(class_name))


def _is_duplicate(
    a: Detection,
    b: Detection,
    *,
    iou_threshold: float,
) -> bool:
    if _class_key(a.class_name) != _class_key(b.class_name):
        return False
    if iou(a.bbox_xyxy, b.bbox_xyxy) >= iou_threshold:
        return True
    # Either box mostly inside the other counts as the same instance.
    if containment(a.bbox_xyxy, b.bbox_xyxy) >= _CONTAINMENT_THRESHOLD:
        return True
    if containment(b.bbox_xyxy, a.bbox_xyxy) >= _CONTAINMENT_THRESHOLD:
        return True
    # Near-miss double-reads of the same diagram icon (low IoU, close centers).
    if center_distance_ratio(a.bbox_xyxy, b.bbox_xyxy) <= _CENTER_DIST_RATIO:
        return True
    return False


def dedupe_detections(
    detections: list[Detection],
    *,
    iou_threshold: float = 0.3,
) -> tuple[list[Detection], int]:
    """Keep highest-confidence detection per overlapping same-class cluster.

    Overlap is transitive within a class (A~B and B~C ⇒ one cluster).
    A pair matches if IoU ≥ threshold, containment ≥ 0.8, or centers are close
    relative to box size (diagram icon double-reads).
    Returns ``(survivors, removed_count)``. ``iou_threshold <= 0`` disables
    dedupe (returns the input list unchanged).
    """
    if iou_threshold <= 0.0 or len(detections) <= 1:
        return list(detections), 0

    n = len(detections)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    for i in range(n):
        for j in range(i + 1, n):
            if _is_duplicate(
                detections[i], detections[j], iou_threshold=iou_threshold
            ):
                union(i, j)

    clusters: dict[int, list[int]] = {}
    for i in range(n):
        clusters.setdefault(find(i), []).append(i)

    kept_indices: list[int] = []
    for members in clusters.values():
        best = max(members, key=lambda idx: detections[idx].confidence)
        kept_indices.append(best)
    kept_indices.sort()
    kept = [detections[i] for i in kept_indices]
    removed = n - len(kept)
    return kept, removed
