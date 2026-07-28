"""Unit tests for Kaggle dataset download helper (T4 / DATA-01)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from stride_mvp.data.download import (
    DATASET_SLUG,
    DEFAULT_DEST,
    DatasetCredentialsError,
    ensure_dataset,
)


def test_dataset_slug_and_default_dest_documented() -> None:
    assert DATASET_SLUG == "carlosrian/software-architecture-dataset"
    assert DEFAULT_DEST == Path("data/raw/software-architecture-dataset")


def test_ensure_dataset_raises_actionable_error_without_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    monkeypatch.setattr(
        "stride_mvp.data.download._kaggle_credentials_present",
        lambda: False,
    )
    dest = tmp_path / "raw"
    with pytest.raises(DatasetCredentialsError) as exc:
        ensure_dataset(dest)
    msg = str(exc.value)
    assert "kaggle" in msg.lower()
    assert "credentials" in msg.lower() or "credencia" in msg.lower() or "kaggle.json" in msg


def test_ensure_dataset_skips_download_if_already_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "software-architecture-dataset"
    dest.mkdir()
    (dest / "marker.txt").write_text("ok", encoding="utf-8")
    download = MagicMock()
    monkeypatch.setattr("stride_mvp.data.download._download_via_kaggle", download)
    result = ensure_dataset(dest)
    assert result == dest
    download.assert_not_called()


def test_ensure_dataset_calls_api_when_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "software-architecture-dataset"
    monkeypatch.setattr(
        "stride_mvp.data.download._kaggle_credentials_present",
        lambda: True,
    )

    def fake_download(slug: str, target: Path) -> None:
        target.mkdir(parents=True, exist_ok=True)
        (target / "downloaded.txt").write_text(slug, encoding="utf-8")

    monkeypatch.setattr("stride_mvp.data.download._download_via_kaggle", fake_download)
    result = ensure_dataset(dest)
    assert result == dest
    assert (dest / "downloaded.txt").read_text(encoding="utf-8") == DATASET_SLUG
