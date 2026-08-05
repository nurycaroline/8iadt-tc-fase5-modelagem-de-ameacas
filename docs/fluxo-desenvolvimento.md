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

O dataset Kaggle usa layout **flat** (`*.png` + `*.xml` na mesma pasta, tipicamente `dataset_augmented/`), não `Annotations/` + `JPEGImages/`.

```bash
# A partir da raiz do repo, com o venv ativo
python scripts/prepare_yolo_dataset.py
# ou com opções:
python scripts/prepare_yolo_dataset.py \
  --raw data/raw/software-architecture-dataset \
  --out data/processed \
  --val-ratio 0.2 \
  --seed 42
```

Gera `data/processed/labels/`, copia imagens para `data/processed/images/`, faz split train/val e escreve `data/processed/data.yaml`.

## 4. Treino

```python
from pathlib import Path
from stride_mvp.detection.train import train

best = train(Path("data/processed/data.yaml"), epochs=50, imgsz=640)
print(best)  # models/weights/best.pt (promovido a partir de train/weights/best.pt)
```

Após treino completo, promova o peso para o path padrão da app/Docker:

```bash
cp models/weights/train/weights/best.pt models/weights/best.pt
```

### 4.1 Treino no Mac (Apple Silicon — MPS)

No MacBook com chip Apple (M1/M2/M3/M4), use **Metal Performance Shaders (`mps`)**. Com `device=None` (default), `train()` escolhe automaticamente CUDA → MPS → CPU.

```bash
# Confirme MPS
python -c "import torch; print(torch.backends.mps.is_available())"  # True
```

**Smoke rápido** (valida pipeline antes do treino longo):

```python
from pathlib import Path
from stride_mvp.detection.train import train

train(
    Path("data/processed/data.yaml"),
    epochs=3,
    imgsz=512,
    device="mps",
    batch=32,       # fixo — NÃO use batch=-1 no Mac (AutoBatch é orientado a CUDA)
    workers=4,
    amp=True,
    fraction=0.1,   # 10% do dataset
)
```

**Treino de demo** (M4 Pro + 48 GB de exemplo):

```python
from pathlib import Path
from stride_mvp.detection.train import train

best = train(
    Path("data/processed/data.yaml"),
    epochs=50,
    imgsz=640,
    device="mps",
    batch=32,       # se não houver swap, teste 48–64
    workers=4,
    amp=True,
    cache=False,    # com muita RAM unificada, cache="ram" pode acelerar
)
print(best)
```

| Ajuste | Sugestão no Mac |
| ------ | --------------- |
| `device` | `"mps"` (ou auto-detect) |
| `batch` | Inteiro fixo (`16`→`32`→`64`); sem `batch=-1` |
| Modelo | Manter `yolo11n.pt` (já é o default) |
| `workers` | `4`–`8`; se travar o dataloader, use `0` |
| Instabilidade MPS | Tente `amp=False` e/ou `workers=0` |

Expectativa: MPS é bem mais rápido que CPU no Mac, mas ainda costuma ficar atrás de uma GPU NVIDIA (CUDA).

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

Edite `data/kb/threats.yaml` para adicionar ameaças por família × categoria STRIDE. A KB v2 declara o **papel** de cada família (`roles`): `workload` (default), `control` (security/observability/edge), `zone` (network zones), `external` (client). Componentes de controle geram **verificações de eficácia/configuração**, não ameaças genéricas de exposição.

### 6.1 Cobertura do vocabulário (check-map)

Após o treino, valide que toda classe do detector resolve para uma família STRIDE (evita relatórios degradando em fallback `unknown`):

```bash
# A partir do classes.txt gerado na conversão VOC→YOLO
stride-mvp check-map --classes data/processed/classes.txt
# Ou lendo 'names' diretamente dos pesos
stride-mvp check-map --weights models/weights/best.pt
```

Saída: lista classes sem mapeamento + exit ≠ 0 quando houver gap; exit 0 e "cobertura 100%" quando tudo resolver. Para fechar gaps, edite `data/class_map.yaml` e re rode o `check-map`.

### 6.2 Cobertura do relatório (coverage)

O relatório expõe `coverage` = detecções mapeadas / total. Quando `coverage < STRIDE_MIN_COVERAGE` (default 0.8), o CLI `analyze` emite um **warning** em stderr (sem mudar o exit code). Componentes não classificados aparecem na seção **"Inventário não classificado"** (categoria `Não classificado`), nunca como "Information Disclosure" inventado.

```bash
export STRIDE_MIN_COVERAGE=0.9   # mais rigoroso (opcional)
```

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
