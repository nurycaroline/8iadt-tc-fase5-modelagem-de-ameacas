# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY data/class_map.yaml ./data/class_map.yaml
COPY data/kb ./data/kb
COPY data/eval ./data/eval

RUN pip install --no-cache-dir -e ".[ml,ui]"

ENV STRIDE_MODEL_PATH=/weights/best.pt
ENV PYTHONUNBUFFERED=1

EXPOSE 7860

ENTRYPOINT ["stride-mvp"]
CMD ["ui", "--host", "0.0.0.0", "--port", "7860"]
