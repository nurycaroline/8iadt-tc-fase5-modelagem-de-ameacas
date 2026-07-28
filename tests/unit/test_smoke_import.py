"""Smoke test: package import works after editable install."""

from __future__ import annotations

import stride_mvp


def test_package_importable() -> None:
    assert hasattr(stride_mvp, "__version__")
    assert stride_mvp.__version__
