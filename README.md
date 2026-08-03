# STRIDE Threat Modeling MVP

MVP de viabilidade: detecção supervisionada de componentes em diagramas de arquitetura + relatório STRIDE (vulnerabilidades e contramedidas).

Documentação completa do fluxo: [`docs/fluxo-desenvolvimento.md`](docs/fluxo-desenvolvimento.md)  
Arquiteturas de avaliação: [`docs/eval-architectures.md`](docs/eval-architectures.md)

## Setup rápido

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,ml,ui,kaggle]"
```

## Comandos principais

```bash
# Dataset (prepare-data / download)
python -c "from stride_mvp.data.download import ensure_dataset; print(ensure_dataset())"

# Treino (após VOC→YOLO + data.yaml)
python -c "from pathlib import Path; from stride_mvp.detection.train import train; print(train(Path('data/processed/data.yaml'), epochs=50))"

# Análise nas imagens de eval
export STRIDE_MODEL_PATH=models/weights/train/weights/best.pt
stride-mvp analyze data/eval/arch1/arch1.png --out reports
stride-mvp analyze data/eval/arch2/arch2.png --out reports

# UI Gradio
stride-mvp ui
# Abra http://localhost:7860 — Upload, arrastar, ou Ctrl+V/Cmd+V para colar o diagrama.
# O botão "Paste from Clipboard" do Gradio só funciona em https:// ou http://localhost.
```

## Testes (gates)

| Gate | Quando | Comando |
| ---- | ------ | ------- |
| Quick | unit tests | `pytest -q tests/unit` |
| Full | + integration | `pytest -q` |
| Build | fim de fase / config | `python -m compileall -q src && pytest -q` |

```bash
pytest -q tests/unit
pytest -q
```

## Dataset (Kaggle)

Dataset: `carlosrian/software-architecture-dataset` → `data/raw/software-architecture-dataset`.

```bash
# Requires ~/.kaggle/kaggle.json or KAGGLE_USERNAME + KAGGLE_KEY
python -c "from stride_mvp.data.download import ensure_dataset; ensure_dataset()"
```

## Docker

```bash
docker compose build
docker compose up
# UI em http://localhost:7860
# CLI: docker compose run --rm app analyze /data/eval/arch1/arch1.png --out /reports
```

Monte pesos em `./models/weights` (volume). Não embute `.pt` grandes na imagem.

## Layout

Ver `.specs/features/stride-threat-modeling-mvp/` para spec, design e tasks.
