"""Download helper for the Kaggle software-architecture dataset (DATA-01)."""

from __future__ import annotations

import os
from pathlib import Path

DATASET_SLUG = "carlosrian/software-architecture-dataset"
DEFAULT_DEST = Path("data/raw/software-architecture-dataset")


class DatasetCredentialsError(RuntimeError):
    """Raised when Kaggle credentials are missing or unusable."""


def _kaggle_credentials_present() -> bool:
    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        return True
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    return kaggle_json.is_file()


def _download_via_kaggle(slug: str, target: Path) -> None:
    """Download and unzip dataset into ``target`` using the Kaggle API."""
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    target.mkdir(parents=True, exist_ok=True)
    api.dataset_download_files(slug, path=str(target), unzip=True)


def ensure_dataset(dest: Path | None = None) -> Path:
    """Ensure the Kaggle architecture dataset exists under ``dest``.

    Destination defaults to ``data/raw/software-architecture-dataset``.
    Does not perform a real download when the directory already contains files.
    Requires Kaggle credentials (``~/.kaggle/kaggle.json`` or
    ``KAGGLE_USERNAME`` / ``KAGGLE_KEY``).
    """
    target = Path(dest) if dest is not None else DEFAULT_DEST
    if target.is_dir() and any(target.iterdir()):
        return target

    if not _kaggle_credentials_present():
        raise DatasetCredentialsError(
            "Kaggle credentials missing. Place kaggle.json in ~/.kaggle/ "
            "(chmod 600) or set KAGGLE_USERNAME and KAGGLE_KEY. "
            f"Then retry to download dataset '{DATASET_SLUG}' into {target}."
        )

    _download_via_kaggle(DATASET_SLUG, target)
    return target
