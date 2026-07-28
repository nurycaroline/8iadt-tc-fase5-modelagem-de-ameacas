# STRIDE Threat Modeling MVP

MVP de viabilidade: detecção supervisionada de componentes em diagramas de arquitetura + relatório STRIDE (vulnerabilidades e contramedidas).

## Setup rápido

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Gate local (build):

```bash
python -m compileall -q src
pytest -q   # após bootstrap de testes (T3+)
```

## Layout

Ver `.specs/features/stride-threat-modeling-mvp/` para spec, design e tasks.
