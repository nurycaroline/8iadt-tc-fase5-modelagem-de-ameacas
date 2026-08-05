"""Unit tests for YOLO training entrypoint (T8) — mocked Ultralytics."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from stride_mvp.detection.train import resolve_train_device, train


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
    monkeypatch.setattr(
        "stride_mvp.detection.train.resolve_train_device", lambda device=None: "cpu"
    )

    result = train(data_yaml, epochs=1, imgsz=320, project=project)
    promoted = project / "best.pt"
    assert result == promoted
    assert promoted.is_file()
    assert promoted.read_bytes() == best.read_bytes()
    fake_yolo_cls.assert_called_once_with("yolo11n.pt")
    kwargs = fake_model.train.call_args.kwargs
    assert kwargs["data"] == str(data_yaml)
    assert kwargs["epochs"] == 1
    assert kwargs["imgsz"] == 320
    assert kwargs["device"] == "cpu"
    assert kwargs["batch"] == 16
    assert kwargs["workers"] == 8
    assert kwargs["amp"] is True
    assert kwargs["cache"] is False
    assert kwargs["fraction"] == 1.0


def test_train_passes_mac_mps_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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

    result = train(
        data_yaml,
        epochs=3,
        imgsz=512,
        project=project,
        device="mps",
        batch=32,
        workers=4,
        amp=True,
        cache="ram",
        fraction=0.1,
    )
    promoted = project / "best.pt"
    assert result == promoted
    assert promoted.is_file()
    assert promoted.read_bytes() == best.read_bytes()
    kwargs = fake_model.train.call_args.kwargs
    assert kwargs["device"] == "mps"
    assert kwargs["batch"] == 32
    assert kwargs["workers"] == 4
    assert kwargs["amp"] is True
    assert kwargs["cache"] == "ram"
    assert kwargs["fraction"] == 0.1


def test_resolve_train_device_respects_explicit_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Even if CUDA/MPS would be available, explicit wins
    torch = ModuleType("torch")
    torch.cuda = SimpleNamespace(is_available=lambda: True)  # type: ignore[attr-defined]
    torch.backends = SimpleNamespace(  # type: ignore[attr-defined]
        mps=SimpleNamespace(is_available=lambda: True)
    )
    monkeypatch.setitem(sys.modules, "torch", torch)
    assert resolve_train_device("mps") == "mps"
    assert resolve_train_device(0) == 0
    assert resolve_train_device("cpu") == "cpu"


def test_resolve_train_device_prefers_mps_when_no_cuda(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    torch = ModuleType("torch")
    torch.cuda = SimpleNamespace(is_available=lambda: False)  # type: ignore[attr-defined]
    torch.backends = SimpleNamespace(  # type: ignore[attr-defined]
        mps=SimpleNamespace(is_available=lambda: True)
    )
    monkeypatch.setitem(sys.modules, "torch", torch)
    assert resolve_train_device() == "mps"


def test_resolve_train_device_falls_back_to_cpu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    torch = ModuleType("torch")
    torch.cuda = SimpleNamespace(is_available=lambda: False)  # type: ignore[attr-defined]
    torch.backends = SimpleNamespace(  # type: ignore[attr-defined]
        mps=SimpleNamespace(is_available=lambda: False)
    )
    monkeypatch.setitem(sys.modules, "torch", torch)
    assert resolve_train_device() == "cpu"
