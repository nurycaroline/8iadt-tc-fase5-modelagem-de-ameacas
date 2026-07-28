"""Unit tests for eval metrics (T20) — mocked Ultralytics."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from stride_mvp.detection.eval_metrics import evaluate


def test_evaluate_returns_map_and_writes_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    weights = tmp_path / "best.pt"
    weights.write_bytes(b"x")
    data_yaml = tmp_path / "data.yaml"
    data_yaml.write_text("train: a\nval: b\n", encoding="utf-8")
    out = tmp_path / "metrics.json"

    fake_metrics = SimpleNamespace(box=SimpleNamespace(map=0.42, map50=0.55))
    fake_model = MagicMock()
    fake_model.val.return_value = fake_metrics
    ultra = ModuleType("ultralytics")
    ultra.YOLO = MagicMock(return_value=fake_model)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ultralytics", ultra)

    value = evaluate(weights, data_yaml, out_path=out)
    assert value == pytest.approx(0.42)
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["map"] == pytest.approx(0.42)
    assert payload["weights"] == str(weights)
