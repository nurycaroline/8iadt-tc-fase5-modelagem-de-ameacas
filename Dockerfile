# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh

# Metadata first: dependency layer stays cached when only source changes.
COPY pyproject.toml README.md ./
RUN mkdir -p src/stride_mvp \
    && printf '"""Stub for dependency-layer install."""\n' > src/stride_mvp/__init__.py \
    && uv pip install --system --no-cache \
         torch torchvision \
         --index-url https://download.pytorch.org/whl/cpu \
    && uv pip install --system --no-cache -e ".[ml,ui]" \
    && rm -rf src

COPY src ./src
COPY data/class_map.yaml ./data/class_map.yaml
COPY data/kb ./data/kb
COPY data/eval ./data/eval

# Refresh editable install with real sources (deps already present → fast).
RUN uv pip install --system --no-cache -e ".[ml,ui]"

ENV STRIDE_MODEL_PATH=/weights/best.pt
ENV PYTHONUNBUFFERED=1

EXPOSE 7860

ENTRYPOINT ["stride-mvp"]
CMD ["ui", "--host", "0.0.0.0", "--port", "7860"]
