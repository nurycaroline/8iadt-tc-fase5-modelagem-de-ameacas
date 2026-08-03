# Fluxo de desenvolvimento — STRIDE Threat Modeling MVP

Documento do fluxo usado para construir o MVP (DOC-01, DOC-02).

## Visão geral

1. Obter dataset anotado (Kaggle Pascal VOC)
2. Mapear classes → famílias STRIDE (`data/class_map.yaml`)
3. Converter VOC → YOLO e gerar split + `data.yaml`
4. Treinar detector YOLO (Ultralytics)
5. Inferir componentes em diagramas
6. Analisar STRIDE via KB versionada (`data/kb/threats.yaml`)
7. Gerar relatório Markdown + JSON
8. (Opcional) UI Gradio e Docker para demo

## 1. Setup

Preferir o script rápido (`uv` + PyTorch CPU):

```bash
bash scripts/install_deps.sh              # default: dev,ml,ui
source .venv/bin/activate
# Completo com Kaggle: bash scripts/install_deps.sh 'dev,ml,ui,kaggle'
```

## 2. Dataset Kaggle

Dataset: `carlosrian/software-architecture-dataset`  
Destino: `data/raw/software-architecture-dataset`

```bash
# Credenciais: ~/.kaggle/kaggle.json ou KAGGLE_USERNAME + KAGGLE_KEY
python -c "from stride_mvp.data.download import ensure_dataset; print(ensure_dataset())"
```

## 3. Conversão e split

```python
from pathlib import Path
from stride_mvp.data.voc_to_yolo import convert_voc_dir
from stride_mvp.data.split import write_split

voc = Path("data/raw/software-architecture-dataset")
out = Path("data/processed")
# class_names = lista lida do dataset
# convert_voc_dir(voc, out, class_names)
# write_split(out, val_ratio=0.2, seed=42, class_names=class_names)
```

## 4. Treino

```python
from pathlib import Path
from stride_mvp.detection.train import train

best = train(Path("data/processed/data.yaml"), epochs=50, imgsz=640)
print(best)  # models/weights/best.pt (promovido a partir de train/weights/best.pt)
```

**Contratos de edge:**

- **NMS**: feito pelo Ultralytics YOLO na inferência (`ComponentDetector.predict`); o MVP não reimplementa NMS.
- **Treino interrompido**: não promover `best.pt` parcial — só use o artefato após corrida completa (ou restaure checkpoint documentado). Corridas parciais ≠ modelo pronto para demo.
- **Caminho Docker/UI**: após treino completo, `best.pt` é copiado para `models/weights/best.pt` (`STRIDE_MODEL_PATH=/weights/best.pt` no compose). O resolver também aceita o layout Ultralytics `…/train/weights/best.pt`.

## 5. Inferência + STRIDE (CLI)

```bash
export STRIDE_MODEL_PATH=models/weights/best.pt
stride-mvp analyze data/eval/arch1/arch1.png --out reports
stride-mvp analyze data/eval/arch2/arch2.png --out reports
```

## 6. Knowledge Base

Edite `data/kb/threats.yaml` para adicionar ameaças por família × categoria STRIDE. O motor usa fallback quando não há entrada específica.

## 7. UI Gradio (P2)

```bash
bash scripts/install_deps.sh ui   # se ainda não instalou a extra ui
stride-mvp ui
# ou: python -m stride_mvp.web.app
```

## 8. Docker (reprodução da demo)

Ver seção Docker no `README.md` (`docker compose up`).

## Testes

```bash
pytest -q tests/unit   # quick
pytest -q              # full
python -m compileall -q src && pytest -q  # build
```
