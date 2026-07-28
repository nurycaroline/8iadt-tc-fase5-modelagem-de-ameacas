# STRIDE Threat Modeling MVP — Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user — do not proceed without it.**

---

**Design**: `.specs/features/stride-threat-modeling-mvp/design.md`  
**Status**: Draft

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec — confirm before Execute. Guidelines found: **none** (repo greenfield) — strong defaults applied. Framework escolhido no Design: **pytest**.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Domain models / config | unit | Construtores + defaults + validação de campos usados pelos ACs | `tests/unit/test_*.py` | `pytest -q tests/unit` |
| Data (VOC→YOLO, class_map, split) | unit | Todos os ACs DATA-* aplicáveis + edge (XML inválido, classe unknown) | `tests/unit/test_data_*.py` | `pytest -q tests/unit` |
| Detection (detector threshold/NMS filter) | unit | DET-02/03 + edge zero detecções; mock do backend YOLO quando possível | `tests/unit/test_detector.py` | `pytest -q tests/unit` |
| STRIDE KB + engine + report | unit | 1:1 ACs STRIDE-* e KB-*; edge fallback / sem mapeamento / zero findings | `tests/unit/test_stride_*.py` | `pytest -q tests/unit` |
| Pipeline validate + run | unit + integration | PIPE-* happy + imagem inválida + zero detecções; integração com detector fake | `tests/unit/test_pipeline*.py`, `tests/integration/test_e2e_pipeline.py` | `pytest -q` |
| CLI | integration | Exit codes sucesso/erro; analisa fixture | `tests/integration/test_cli.py` | `pytest -q tests/integration` |
| Train script / eval metrics / UI / docs | none / smoke | Treino real GPU-bound → smoke de assinatura/CLI help; docs = review manual; UI = smoke se implementada | — | build / manual |

## Gate Check Commands

> Generated for greenfield Python — confirm before Execute.

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | Após tasks com unit tests | `pytest -q tests/unit` |
| Full | Após tasks com integration | `pytest -q` |
| Build | Fim de fase / config-only | `python -m compileall -q src && pytest -q` |

---

## Execution Plan

### Phase 1: Foundation

```
T1 → T2 → T3
```

### Phase 2: Dataset tooling

```
T4 → T5 → T6 → T7
```

### Phase 3: Detection

```
T8 → T9 → T10
```

### Phase 4: STRIDE + KB + Report

```
T11 → T12 → T13 → T14
```

### Phase 5: Pipeline + CLI

```
T15 → T16 → T17
```

### Phase 6: Eval samples + Docs (P2 docs)

```
T18 → T19
```

### Phase 7: Metrics (P3) + UI (P2)

```
T20 → T21
```

### Phase 8: Packaging / Demo (extra)

```
T22
```

> **T22 (Docker)** — pedida pelo usuário (não está no enunciado PDF). Encaixa **depois de T21**: a imagem empacota CLI + UI Gradio já funcionais; avaliadores reproduzem a demo com `docker compose up` sem instalar Python/YOLO localmente. Depende de T17 (CLI) e T21 (UI no compose).

---

## Task Breakdown

### T1: Scaffold do projeto Python

**What**: Criar `pyproject.toml`, package `src/stride_mvp/`, `.gitignore` (data/raw, *.pt, kaggle.json), e entrypoint console script placeholder.  
**Where**: `pyproject.toml`, `src/stride_mvp/__init__.py`, `.gitignore`  
**Depends on**: None  
**Reuses**: Layout do design.md  
**Requirement**: PIPE-01 (fundação)

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [x] `pip install -e ".[dev]"` (ou equivalente documentado) instala o pacote
- [x] `.gitignore` exclui `data/raw/`, `models/weights/*.pt`, credenciais Kaggle
- [x] Gate: `python -m compileall -q src`

**Tests**: none  
**Gate**: build  
**Commit**: `chore(stride): scaffold Python package and gitignore`

---

### T2: Domain models e AppConfig

**What**: Implementar `Detection`, `ThreatFinding`, `ThreatReport` e `AppConfig`/`load_config` com limiar de confiança e `max_image_bytes`.  
**Where**: `src/stride_mvp/models.py`, `src/stride_mvp/config.py`, `tests/unit/test_models_config.py`  
**Depends on**: T1  
**Reuses**: Design § Data Models  
**Requirement**: DET-02, DET-03, PIPE-02

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [x] Modelos exportados e instanciáveis
- [x] Config lê defaults + override de path/env
- [x] Unit tests cobrem defaults e campos obrigatórios
- [x] Gate: `pytest -q tests/unit` passa

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(stride): add domain models and app config`

---

### T3: Bootstrap pytest

**What**: Garantir layout `tests/unit` e `tests/integration`, deps `pytest` em `[dev]`, e um smoke test de import do pacote.  
**Where**: `tests/unit/test_smoke_import.py`, `pyproject.toml` (modify)  
**Depends on**: T2  
**Reuses**: T1 package  
**Requirement**: — (qualidade / gate)

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [x] `pytest -q` coleta e passa smoke + testes T2
- [x] Comandos do Gate Check Commands documentados no README stub ou pyproject

**Tests**: unit  
**Gate**: quick  
**Commit**: `test(stride): bootstrap pytest layout and smoke import`

---

### T4: Script/docs de download do dataset Kaggle

**What**: Implementar `ensure_dataset` (ou CLI `prepare-data download`) que documenta e tenta baixar `carlosrian/software-architecture-dataset` para `data/raw/`, com erro claro se credenciais ausentes.  
**Where**: `src/stride_mvp/data/download.py`, `tests/unit/test_download.py`, trecho em README  
**Depends on**: T3  
**Reuses**: AD-003  
**Requirement**: DATA-01

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [x] Path de destino e nome do dataset documentados
- [x] Sem credenciais → erro com mensagem acionável (testado com mock/monkeypatch)
- [x] Não requer download real no CI
- [x] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(data): add Kaggle dataset download helper`

---

### T5: class_map.yaml + ClassFamilyMapper

**What**: Criar `data/class_map.yaml` (classes Kaggle → famílias) e `load_class_map` / `to_family` com fallback `unknown`.  
**Where**: `data/class_map.yaml`, `src/stride_mvp/data/class_map.py`, `tests/unit/test_class_map.py`  
**Depends on**: T4  
**Reuses**: Design ClassMap  
**Requirement**: DATA-02, KB-04

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [x] Mapa cobre famílias usadas pela KB (database, compute, api, storage, network, security, messaging, client/user, unknown)
- [x] Classe conhecida → família; desconhecida → `unknown`
- [x] Unit tests 1:1 para esses comportamentos
- [x] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(data): add Kaggle class-to-family map`

---

### T6: Conversor Pascal VOC → YOLO

**What**: Converter diretório VOC (XML + imagens) para labels YOLO normalizados e `classes.txt`/`names`.  
**Where**: `src/stride_mvp/data/voc_to_yolo.py`, `tests/unit/test_voc_to_yolo.py` (fixture XML mínimo)  
**Depends on**: T5  
**Reuses**: Ultralytics label format  
**Requirement**: DATA-02

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [x] Fixture VOC → arquivo `.txt` com `class xc yc w h` em [0,1]
- [x] XML inválido / bbox ausente → erro ou skip documentado (testado)
- [x] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(data): convert Pascal VOC annotations to YOLO`

---

### T7: Split train/val + gerador data.yaml

**What**: Gerar split determinístico e `data.yaml` Ultralytics a partir de `data/processed/`.  
**Where**: `src/stride_mvp/data/split.py`, `tests/unit/test_split.py`  
**Depends on**: T6  
**Reuses**: Design TrainValSplit  
**Requirement**: DATA-01, DET-01

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [x] `data.yaml` contém `train`, `val`, `names`
- [x] Seed fixa → split reproduzível (teste)
- [x] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(data): write train/val split and Ultralytics data.yaml`

---

### T8: Script de treino YOLO

**What**: `train()` chama Ultralytics, persiste `best.pt` + metadados de classes sob `models/weights/`.  
**Where**: `src/stride_mvp/detection/train.py`, `tests/unit/test_train.py` (mock `ultralytics.YOLO`)  
**Depends on**: T7  
**Reuses**: AD-004  
**Requirement**: DET-01

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [x] Interface `train(data_yaml, epochs, imgsz, project) -> Path`
- [x] Teste com mock não executa treino real e verifica path retornado
- [x] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(detection): add YOLO training entrypoint`

---

### T9: ComponentDetector (inferência + limiar)

**What**: Carregar pesos e retornar `list[Detection]` filtrando por `conf`; documentar comportamento abaixo do limiar (exclusão).  
**Where**: `src/stride_mvp/detection/detector.py`, `tests/unit/test_detector.py`  
**Depends on**: T8, T2  
**Reuses**: models.Detection  
**Requirement**: DET-02, DET-03

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [x] `predict` retorna classe, confiança, bbox
- [x] Detecções &lt; conf excluídas (teste com mock de results)
- [x] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(detection): implement component detector with confidence threshold`

---

### T10: Edge cases do detector (zero detecções / classe unknown prep)

**What**: Garantir que lista vazia é retorno válido e que class names desconhecidos ao mapa não quebram o detector (family preenchida depois).  
**Where**: `tests/unit/test_detector.py` (extend), opcional helper em detector  
**Depends on**: T9  
**Reuses**: T9  
**Requirement**: DET-02; Edge: zero detecções

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] Teste explícito de zero detecções
- [ ] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `test(detection): cover zero-detection edge case`

---

### T11: Threat KB YAML + loader

**What**: Criar `data/kb/threats.yaml` (entradas por família×STRIDE + fallback) e `ThreatKB.load` / `lookup` / `fallback`.  
**Where**: `data/kb/threats.yaml`, `src/stride_mvp/stride/kb.py`, `tests/unit/test_kb.py`  
**Depends on**: T10  
**Reuses**: Design Threat KB  
**Requirement**: KB-01, KB-02, KB-03, KB-04

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] KB versionada no repo (não hardcode)
- [ ] Lookup `database` + Information Disclosure retorna vulnerabilidade + contramedida
- [ ] Fallback funciona para família ausente
- [ ] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(stride): add versioned threat knowledge base`

---

### T12: StrideEngine

**What**: Dado detections + mapper + KB, produzir `ThreatReport` cobrindo categorias STRIDE aplicáveis; componente sem mapeamento → finding `mapped=False` / fallback (nunca omitir).  
**Where**: `src/stride_mvp/stride/engine.py`, `tests/unit/test_engine.py`  
**Depends on**: T11, T5, T9  
**Reuses**: ThreatKB, ClassFamilyMapper  
**Requirement**: STRIDE-01, STRIDE-02, STRIDE-04

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] Teste com detections mock cobre menção a cada componente
- [ ] Categorias STRIDE presentes onde KB/regras aplicam
- [ ] Sem mapeamento → finding explícito
- [ ] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(stride): implement STRIDE analysis engine`

---

### T13: ReportRenderer Markdown + JSON (pt-BR)

**What**: Renderizar e gravar `reports/{stem}.md` e `.json` a partir de `ThreatReport`.  
**Where**: `src/stride_mvp/stride/report.py`, `tests/unit/test_report.py`  
**Depends on**: T12  
**Reuses**: ThreatReport  
**Requirement**: STRIDE-03, PIPE-03

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] Markdown em pt-BR lista componente, categoria, ameaça, vulnerabilidade, contramedida
- [ ] JSON parseável espelha findings
- [ ] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(stride): render Markdown and JSON threat reports`

---

### T14: Testes de edge da KB incompleta / zero findings no relatório

**What**: Cobrir edge cases do spec: KB incompleta (fallback) e zero detecções → relatório sem ameaças inventadas + note.  
**Where**: `tests/unit/test_engine.py`, `tests/unit/test_report.py` (extend)  
**Depends on**: T13  
**Reuses**: T12–T13  
**Requirement**: STRIDE-04; Edge cases

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] Testes dos dois edges passam
- [ ] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `test(stride): cover KB fallback and empty-detection report notes`

---

### T15: ImageValidator

**What**: Validar path, formato PNG/JPG, não-vazio, `max_bytes`; levantar `ValidationError`.  
**Where**: `src/stride_mvp/pipeline/validate.py`, `tests/unit/test_validate.py`  
**Depends on**: T14  
**Reuses**: AppConfig.max_image_bytes  
**Requirement**: PIPE-02; Edge tamanho máximo

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] Happy path PNG/JPG fixture
- [ ] Rejeita extensão inválida, vazio, oversized
- [ ] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(pipeline): validate input architecture images`

---

### T16: Pipeline run_pipeline

**What**: Orquestrar validate → detect → map families → STRIDE → write report; retornar `ThreatReport`.  
**Where**: `src/stride_mvp/pipeline/run.py`, `tests/unit/test_pipeline_run.py` (detector fake)  
**Depends on**: T15, T9, T5, T12, T13  
**Reuses**: todos os componentes P1  
**Requirement**: PIPE-01, PIPE-03, PIPE-04

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] Com detector fake, gera MD+JSON em `out_dir`
- [ ] Imagem inválida propaga ValidationError
- [ ] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(pipeline): orchestrate image-to-STRIDE report flow`

---

### T17: CLI analyze + teste de integração

**What**: Comando CLI `analyze IMAGE --out DIR` (exit 0/1) e teste de integração ponta a ponta com detector fake injetável ou weights mock.  
**Where**: `src/stride_mvp/cli.py`, `tests/integration/test_cli.py`, `tests/integration/test_e2e_pipeline.py`  
**Depends on**: T16  
**Reuses**: Pipeline  
**Requirement**: PIPE-01, PIPE-02, PIPE-03

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] `stride-mvp analyze --help` funciona
- [ ] Integração: imagem válida → arquivos de relatório; inválida → exit ≠ 0
- [ ] Gate: `pytest -q`

**Tests**: integration  
**Gate**: full  
**Commit**: `feat(cli): add analyze command and e2e integration tests`

---

### T18: Amostras de avaliação Arquiteturas 1–2

**What**: Adicionar `data/eval/` com imagens (ou placeholders documentados + script) e labels YOLO para as arquiteturas de teste; checklist do que deve ser detectado.  
**Where**: `data/eval/`, `docs/eval-architectures.md`  
**Depends on**: T17  
**Reuses**: DATA-03  
**Requirement**: DATA-03, DET-04, PIPE-04

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] Pelo menos 2 imagens de eval referenciadas (arch1, arch2) com labels ou instrução de anotação Label Studio/YOLO
- [ ] Doc lista componentes esperados por figura
- [ ] Gate: build (`compileall` + `pytest -q` sem regressão)

**Tests**: none  
**Gate**: build  
**Commit**: `docs(data): add eval architecture samples and expected components`

---

### T19: Documentação do fluxo de desenvolvimento (P2)

**What**: README + `docs/fluxo-desenvolvimento.md` cobrindo dataset Kaggle, anotação/conversão, treino, inferência, STRIDE/KB e como reproduzir a demo.  
**Where**: `README.md`, `docs/fluxo-desenvolvimento.md`  
**Depends on**: T17, T18  
**Reuses**: —  
**Requirement**: DOC-01, DOC-02

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] Seções obrigatórias do AC presentes
- [ ] Comandos copy-paste para `prepare-data`, `train`, `analyze` nas eval images
- [ ] Gate: build

**Tests**: none  
**Gate**: build  
**Commit**: `docs: detail development flow and demo reproduction`

---

### T20: Métricas de validação do detector (P3)

**What**: Script/CLI `eval` que roda `model.val()` (ou equivalente) e persiste métrica agregada (mAP) em `models/weights/metrics.json`.  
**Where**: `src/stride_mvp/detection/eval_metrics.py`, `tests/unit/test_eval_metrics.py` (mock), CLI hook  
**Depends on**: T19  
**Reuses**: Trainer weights  
**Requirement**: MET-01, MET-02

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] Interface retorna métrica numérica agregada
- [ ] Persistência em arquivo versionável (path documentado)
- [ ] Teste com mock não precisa GPU
- [ ] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(detection): add validation metrics export`

---

### T21: UI web mínima Gradio (P2)

**What**: App Gradio: upload de imagem → chama `run_pipeline` → exibe Markdown do relatório.  
**Where**: `src/stride_mvp/web/app.py`, `tests/unit/test_web_app.py` (smoke create_app / mock pipeline)  
**Depends on**: T20  
**Reuses**: Pipeline  
**Requirement**: UI-01, UI-02

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] Upload + display cobertos por smoke test com pipeline mock
- [ ] README documenta `stride-mvp ui` ou `python -m stride_mvp.web.app`
- [ ] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(web): add minimal Gradio upload UI for demo`

---

### T22: Docker + Compose para demo reproduzível

**What**: Adicionar `Dockerfile` (+ `.dockerignore`) e `docker-compose.yml` para rodar a demo (CLI `analyze` e/ou UI Gradio) com pesos montados em volume; documentar build/run no README.  
**Where**: `Dockerfile`, `.dockerignore`, `docker-compose.yml`, trecho em `README.md`  
**Depends on**: T17, T21  
**Reuses**: CLI + Gradio app; `models/weights/` via volume (não embutir `.pt` na imagem se grande)  
**Requirement**: DOC-02 (reprodução); extra usuário (Docker)

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] `docker build` sobe imagem baseada em Python 3.11+ com o pacote instalado
- [ ] `docker compose up` (ou comando documentado) expõe a UI Gradio **ou** permite `docker compose run … analyze IMAGE`
- [ ] `.dockerignore` exclui `data/raw/`, `.git`, venvs, pesos grandes desnecessários ao build
- [ ] README tem seção Docker copy-paste
- [ ] Gate: build (`python -m compileall -q src && pytest -q`) — smoke de sintaxe Compose opcional se `docker` disponível

**Tests**: none  
**Gate**: build  
**Commit**: `build(docker): add Dockerfile and compose for demo`

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7 → Phase 8

Phase 1:  T1 ──→ T2 ──→ T3
Phase 2:  T4 ──→ T5 ──→ T6 ──→ T7
Phase 3:  T8 ──→ T9 ──→ T10
Phase 4:  T11 ──→ T12 ──→ T13 ──→ T14
Phase 5:  T15 ──→ T16 ──→ T17
Phase 6:  T18 ──→ T19
Phase 7:  T20 ──→ T21
Phase 8:  T22
```

**Batch packing (Execute):** ~22 tasks → ~3 workers sugeridos  
- Batch A: Phases 1–2 (T1–T7)  
- Batch B: Phases 3–4 (T8–T14)  
- Batch C: Phases 5–8 (T15–T22)  

Oferecer sub-agents no Execute (offer-then-confirm).

---

## Task Granularity Check

| Task | Scope | Status |
| ---- | ----- | ------ |
| T1 Scaffold | package/config files | ✅ |
| T2 Models+config | 2 arquivos coesos + tests | ✅ |
| T3 Pytest bootstrap | test harness | ✅ |
| T4 Download helper | 1 módulo | ✅ |
| T5 Class map | 1 módulo + yaml | ✅ |
| T6 VOC→YOLO | 1 função/módulo | ✅ |
| T7 Split | 1 módulo | ✅ |
| T8 Train | 1 entrypoint | ✅ |
| T9 Detector | 1 classe | ✅ |
| T10 Edge detector tests | tests only | ✅ |
| T11 KB | yaml + loader | ✅ |
| T12 Engine | 1 módulo | ✅ |
| T13 Report | 1 módulo | ✅ |
| T14 Edge stride tests | tests only | ✅ |
| T15 Validator | 1 módulo | ✅ |
| T16 Pipeline | 1 orquestrador | ✅ |
| T17 CLI + integration | CLI + tests (coesos) | ✅ |
| T18 Eval samples | data + doc | ✅ |
| T19 Docs | docs only | ✅ |
| T20 Metrics | 1 módulo | ✅ |
| T21 Gradio UI | 1 app | ✅ |
| T22 Docker | Dockerfile + compose | ✅ |

---

## Diagram-Definition Cross-Check

| Task | Depends On (body) | Diagram Shows | Status |
| ---- | ----------------- | ------------- | ------ |
| T1 | None | (start) | ✅ |
| T2 | T1 | T1→T2 | ✅ |
| T3 | T2 | T2→T3 | ✅ |
| T4 | T3 | T3→T4 | ✅ |
| T5 | T4 | T4→T5 | ✅ |
| T6 | T5 | T5→T6 | ✅ |
| T7 | T6 | T6→T7 | ✅ |
| T8 | T7 | T7→T8 | ✅ |
| T9 | T8, T2 | T8→T9 (T2 prior phase) | ✅ |
| T10 | T9 | T9→T10 | ✅ |
| T11 | T10 | T10→T11 | ✅ |
| T12 | T11, T5, T9 | T11→T12 | ✅ |
| T13 | T12 | T12→T13 | ✅ |
| T14 | T13 | T13→T14 | ✅ |
| T15 | T14 | T14→T15 | ✅ |
| T16 | T15, T9, T5, T12, T13 | T15→T16 | ✅ |
| T17 | T16 | T16→T17 | ✅ |
| T18 | T17 | T17→T18 | ✅ |
| T19 | T17, T18 | T18→T19 | ✅ |
| T20 | T19 | T19→T20 | ✅ |
| T21 | T20 | T20→T21 | ✅ |
| T22 | T17, T21 | T21→T22 | ✅ |

---

## Test Co-location Validation

| Task | Code Layer | Matrix Requires | Task Says | Status |
| ---- | ---------- | --------------- | --------- | ------ |
| T1 | config/scaffold | none | none | ✅ |
| T2 | domain/config | unit | unit | ✅ |
| T3 | test harness | unit | unit | ✅ |
| T4 | data download | unit | unit | ✅ |
| T5 | class_map | unit | unit | ✅ |
| T6 | voc_to_yolo | unit | unit | ✅ |
| T7 | split | unit | unit | ✅ |
| T8 | train | unit | unit | ✅ |
| T9 | detector | unit | unit | ✅ |
| T10 | detector edges | unit | unit | ✅ |
| T11 | KB | unit | unit | ✅ |
| T12 | engine | unit | unit | ✅ |
| T13 | report | unit | unit | ✅ |
| T14 | engine/report edges | unit | unit | ✅ |
| T15 | validate | unit | unit | ✅ |
| T16 | pipeline | unit | unit | ✅ |
| T17 | CLI / e2e | integration | integration | ✅ |
| T18 | data/docs | none | none | ✅ |
| T19 | docs | none | none | ✅ |
| T20 | eval_metrics | unit | unit | ✅ |
| T21 | web UI | unit | unit | ✅ |
| T22 | docker packaging | none | none | ✅ |

---

## Requirement Traceability (tasks)

| Requirement ID | Task(s) |
| -------------- | ------- |
| DATA-01 | T4, T7 |
| DATA-02 | T5, T6 |
| DATA-03 | T18 |
| DET-01 | T7, T8 |
| DET-02 | T9, T10 |
| DET-03 | T2, T9 |
| DET-04 | T18, T16 |
| STRIDE-01 | T12 |
| STRIDE-02 | T12 |
| STRIDE-03 | T13 |
| STRIDE-04 | T12, T14 |
| KB-01 | T11 |
| KB-02 | T11 |
| KB-03 | T11 |
| KB-04 | T5, T11 |
| PIPE-01 | T1, T16, T17 |
| PIPE-02 | T15, T17 |
| PIPE-03 | T13, T16, T17 |
| PIPE-04 | T16, T18 |
| DOC-01 | T19 |
| DOC-02 | T19, T22 |
| UI-01 | T21 |
| UI-02 | T21 |
| MET-01 | T20 |
| MET-02 | T20 |

**Coverage:** 25 total, 25 mapped to tasks, 0 unmapped (+ T22 extra Docker → DOC-02)
