"""Unit tests for YOLO training entrypoint (T8) — mocked Ultralytics."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from stride_mvp.detection.train import train


def test_train_returns_best_pt_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data_yaml = tmp_path / "data.yaml"
    data_yaml.write_text("train: x\nval: y\nnames: {0: rds}\n", encoding="utf-8")
    project = tmp_path / "weights"
    best = project / "train" / "weights" / "best.pt"
    best.parent.mkdir(parents=True)
    best.write_bytes(b"fake")

    fake_model = MagicMock()
    fake_model.train.return_value = SimpleNamespace(save_dir=str(project / "train"))
    fake_yolo_cls = MagicMock(return_value=fake_model)

    ultra = ModuleType("ultralytics")
    ultra.YOLO = fake_yolo_cls  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ultralytics", ultra)

    result = train(data_yaml, epochs=1, imgsz=320, project=project)
    assert result == best
    fake_yolo_cls.assert_called_once_with("yolo11n.pt")
    kwargs = fake_model.train.call_args.kwargs
    assert kwargs["data"] == str(data_yaml)
    assert kwargs["epochs"] == 1
    assert kwargs["imgsz"] == 320
