#!/usr/bin/env bash
# Fast, idempotent dependency install for local + Cursor Cloud Agents.
#
# Bottleneck avoided: default Linux wheels for torch often pull CUDA (~2GB+).
# We pre-install CPU torch from the PyTorch CPU index, then install project extras.
#
# Usage:
#   bash scripts/install_deps.sh              # default: dev,ml,ui
#   bash scripts/install_deps.sh dev          # tests only (fast)
#   bash scripts/install_deps.sh 'dev,ml,ui,kaggle'
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

EXTRAS="${1:-dev,ml,ui}"
PYTHON_VERSION="${STRIDE_PYTHON:-3.11}"

export PATH="${HOME}/.local/bin:/usr/local/bin:${PATH}"

if ! command -v uv >/dev/null 2>&1; then
  echo "==> Installing uv (fast Python package manager)"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:/usr/local/bin:${PATH}"
fi

if [[ ! -d .venv ]]; then
  echo "==> Creating .venv (Python ${PYTHON_VERSION})"
  uv venv --python "${PYTHON_VERSION}" .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Pre-installing CPU PyTorch (avoids multi-GB CUDA wheels)"
uv pip install --python .venv/bin/python \
  torch torchvision \
  --index-url https://download.pytorch.org/whl/cpu

echo "==> Installing stride-mvp[${EXTRAS}]"
uv pip install --python .venv/bin/python -e ".[${EXTRAS}]"

echo "==> Done. Activate with: source .venv/bin/activate"
