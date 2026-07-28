# STRIDE Threat Modeling MVP

MVP de viabilidade: detecção supervisionada de componentes em diagramas de arquitetura + relatório STRIDE (vulnerabilidades e contramedidas).

## Setup rápido

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
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

## Layout

Ver `.specs/features/stride-threat-modeling-mvp/` para spec, design e tasks.
