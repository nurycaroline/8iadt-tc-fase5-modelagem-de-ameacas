O código está pronto e validado (PASS). O que falta é o caminho operacional na sua máquina — treinar o YOLO real e fechar a auditoria do vocabulário (MAP-02). Passo a passo exato:

---

### 0. Pré-requisitos
- Python 3.11+ na sua máquina
- Conta Kaggle + API token (`kaggle.json`)
- **GPU recomendada** (CUDA no Linux/Windows, ou MPS no Mac Apple Silicon). CPU funciona mas é lento.

---

### 1. Clonar e instalar
```bash
git clone https://github.com/nurycaroline/8iadt-tc-fase5-modelagem-de-ameacas.git
cd 8iadt-tc-fase5-modelagem-de-ameacas
git checkout cursor/stride-report-quality-spec-062c   # branch com as correções

bash scripts/install_deps.sh 'dev,ml,ui,kaggle'
source .venv/bin/activate

# GPU NVIDIA (opcional): reinstale torch CUDA
# STRIDE_TORCH_INDEX=https://download.pytorch.org/whl/cu124 bash scripts/install_deps.sh 'dev,ml,ui,kaggle'
```
Confirme: `pytest -q` → **115 passed**.

---

### 2. Credenciais Kaggle
Kaggle → Account → **Create New Token** → baixa `kaggle.json`.
```bash
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

---

### 3. Baixar o dataset
```bash
python -c "from stride_mvp.data.download import ensure_dataset; print(ensure_dataset())"
# → data/raw/software-architecture-dataset
```

---

### 4. Converter VOC → YOLO + split
```bash
python scripts/prepare_yolo_dataset.py
# gera data/processed/{images,labels}/ + data/processed/classes.txt + data/processed/data.yaml
```

---

### 5. Auditar o vocabulário (fecha o MAP-02 pendente)
```bash
stride-mvp check-map --classes data/processed/classes.txt
```
- **exit 0 + "cobertura 100%"** → tudo mapeado, pode treinar.
- **exit 1 + lista de classes** → edite `data/class_map.yaml` adicionando as classes faltantes nas famílias corretas, e rode de novo até passar.

---

### 6. Treinar o YOLO
**Linux/Windows com GPU NVIDIA:**
```bash
python -c "from pathlib import Path; from stride_mvp.detection.train import train; print(train(Path('data/processed/data.yaml'), epochs=50, imgsz=640))"
```
**Mac (Apple Silicon):**
```bash
python -c "from pathlib import Path; from stride_mvp.detection.train import train; print(train(Path('data/processed/data.yaml'), epochs=50, imgsz=640, device='mps', batch=32))"
```
Saída: `models/weights/best.pt` (já promovido de `train/weights/best.pt`).

> Só use o `best.pt` se o treino **terminar completo** (corrida parcial ≠ modelo pronto).

---

### 7. Métricas (opcional)
```bash
stride-mvp eval --weights models/weights/best.pt --data data/processed/data.yaml --out models/weights/metrics.json
cat models/weights/metrics.json
```

---

### 8. Demo nas arquiteturas de avaliação
```bash
export STRIDE_MODEL_PATH=models/weights/best.pt

stride-mvp analyze data/eval/arch1/arch1.png --out reports
stride-mvp analyze data/eval/arch2/arch2.png --out reports
```
Abra `reports/arch1.md` e `reports/arch2.md`. Com as correções, você deve ver:
- WAF/Shield/KMS/CloudTrail/CloudWatch na seção **"Controles detectados — verificações"** (role=control), não como ameaças genéricas
- Subnets em **"Zonas de rede — verificações estruturais"**
- Sem blocos duplicados (instâncias repetidas agrupadas com `instance_count`)
- Sem "Information Disclosure" inventado; componentes não mapeados em **"Inventário não classificado"**
- Se a cobertura ficar < 80%, o CLI emite um warning no stderr

---

### 9. UI Gradio (opcional)
```bash
export STRIDE_MODEL_PATH=models/weights/best.pt
stride-mvp ui
# http://localhost:7860 → upload do diagrama → relatório Markdown
```

---

### 10. Docker (opcional)
```bash
docker compose build
docker compose up
# UI: http://localhost:7860 (pesos montados de ./models/weights)
```
