# STRIDE Report Fidelity — Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.**

---

**Design**: `.specs/features/stride-report-fidelity/design.md`
**Status**: Approved

---

## Test Coverage Matrix

> Guidelines found: none beyond `pyproject.toml` `[tool.pytest.ini_options]` — strong defaults applied. Floor: existing unit/integration style in `tests/`.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| class_map YAML / mapper | unit | Families of reallocated labels match SEM/AZR | `tests/unit/test_class_map.py` | `pytest -q tests/unit` |
| KB YAML / ThreatKB | unit | Required terms present; forbidden terms absent; scope exempt from map↔KB | `tests/unit/test_kb.py` | `pytest -q tests/unit` |
| AppConfig / models | unit | Env overrides + bounds validation; new fields | `tests/unit/test_models_config.py` | `pytest -q tests/unit` |
| Spatial dedupe | unit | All DED ACs + edge cases (chain, cross-class, threshold 0) | `tests/unit/test_dedupe.py` | `pytest -q tests/unit` |
| StrideEngine | unit | Scope zero STRIDE; confidence flags; coverage | `tests/unit/test_engine.py` | `pytest -q tests/unit` |
| Pipeline wiring | unit | Dedupe called; notes when removals | `tests/unit/test_pipeline_run.py` | `pytest -q tests/unit` |
| ReportRenderer | unit | Confidence column, ⚠, JSON fields, scope only in summary | `tests/unit/test_report.py` | `pytest -q tests/unit` |
| E2E fidelity | integration | REG-01/REG-02 forbidden/required terms + counts | `tests/integration/test_e2e_pipeline.py` | `pytest -q` |

## Gate Check Commands

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | After unit-only tasks | `pytest -q tests/unit` |
| Full | After integration / last phase task | `pytest -q` |
| Build | Phase completion / config-only | `python -m compileall -q src && pytest -q` |

---

## Execution Plan

### Phase 1: Data (map + KB)

```
T1 → T2
```

### Phase 2: Config, dedupe, engine, pipeline

```
T3 → T4 → T5 → T6
```

### Phase 3: Report + regression + decision log

```
T7 → T8 → T9
```

---

## Task Breakdown

### T1: Realocar labels no class_map

**What**: Mover labels AWS/Azure para famílias `filesystem`, `backup`, `email`, `scaling`, `integration`, `dependency`, `management`; adicionar alias `ses`.
**Where**: `data/class_map.yaml`, `tests/unit/test_class_map.py`
**Depends on**: None
**Reuses**: Padrão de famílias existentes
**Requirement**: SEM-01..05, AZR-01..03 (mapeamento)

**Done when**:

- [ ] Labels listados no design estão nas famílias novas (não mais em storage/messaging/compute/zone)
- [ ] Testes unitários assertam `to_family` para cada label realocado
- [ ] `AWS_REVIEW_CLASSES` atualizado (`efs`→`filesystem`, `backup`→`backup`, `auto_scaling`→`scaling`)
- [ ] Gate: `pytest -q tests/unit/test_class_map.py`

**Tests**: unit
**Gate**: quick
**Commit**: `fix(class-map): reallocate EFS/Backup/SES/scaling/Azure labels to semantic families`

---

### T2: Entradas KB das novas famílias + role scope

**What**: Adicionar roles e entradas STRIDE em `threats.yaml`; isentar `scope` no teste map↔KB; testes de termos obrigatórios/proibidos.
**Where**: `data/kb/threats.yaml`, `tests/unit/test_kb.py`
**Depends on**: T1
**Reuses**: Estrutura KB v2 (roles + entries)
**Requirement**: SEM-01..06, AZR-02..03, KBX-style

**Done when**:

- [ ] Roles: backup/scaling=control, dependency=external, management=scope
- [ ] filesystem sem "bucket"/"Block public access"/"MFA delete"; com mount/POSIX/criptografia
- [ ] email com SPF/DKIM/DMARC; sem "fila"/"DLQ"
- [ ] scaling sem "escape de container"/"IMDSv2"
- [ ] integration/dependency sem "container"/"seccomp"/"IMDSv2"/"HPA"; com Managed Identity/RBAC ou tokens
- [ ] `test_every_class_map_family_has_kb_entry` isenta role `scope`
- [ ] Gate: `pytest -q tests/unit/test_kb.py tests/unit/test_class_map.py`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(kb): add filesystem/backup/email/scaling/integration/dependency families and scope role`

---

### T3: Config e modelos — limiares e campos de confiança

**What**: `dedupe_iou`/`low_conf` em AppConfig + env; validação [0,1]; campos `max_confidence`/`low_confidence` em ThreatFinding.
**Where**: `src/stride_mvp/config.py`, `src/stride_mvp/models.py`, `tests/unit/test_models_config.py`
**Depends on**: None (pode seguir T2 em série)
**Reuses**: Padrão `STRIDE_MIN_COVERAGE`
**Requirement**: DED-02, CONF-02, CONF-03

**Done when**:

- [ ] Defaults 0.5 / 0.50; env `STRIDE_DEDUPE_IOU` / `STRIDE_LOW_CONF`
- [ ] Valor fora de [0,1] ou não numérico → ValueError acionável
- [ ] ThreatFinding aceita os novos campos com defaults seguros
- [ ] Gate: `pytest -q tests/unit/test_models_config.py`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(config): add STRIDE_DEDUPE_IOU and STRIDE_LOW_CONF with bounds validation`

---

### T4: Dedupe espacial puro

**What**: Módulo `detection/dedupe.py` com IoU, contenção e NMS intra-classe greedy.
**Where**: `src/stride_mvp/detection/dedupe.py`, `tests/unit/test_dedupe.py`
**Depends on**: T3 (só conceitualmente; não importa config)
**Reuses**: `_normalize`/`_strip_vendor` de class_map
**Requirement**: DED-01..04

**Done when**:

- [ ] IoU≥limiar ou contenção≥0.8 remove a de menor confiança
- [ ] threshold 0 = no-op
- [ ] Caixas disjuntas preservadas; classes diferentes preservadas
- [ ] Cadeia A~B~C converge para 1
- [ ] Gate: `pytest -q tests/unit/test_dedupe.py`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(detection): add spatial intra-class dedupe by IoU and containment`

---

### T5: Engine — scope sem STRIDE + confiança

**What**: Role `scope` → finding marcador; cobertura conta como mapeado; anexar max_confidence/low_confidence.
**Where**: `src/stride_mvp/stride/engine.py`, `tests/unit/test_engine.py`
**Depends on**: T2, T3
**Reuses**: `_add_inventory_finding` pattern
**Requirement**: SEM-05, AZR-01, CONF-02, SEM-06

**Done when**:

- [ ] `resource_group`/`aws_region` → 1 finding role=scope, categoria Escopo, sem categorias STRIDE clássicas
- [ ] coverage inclui scope como mapped
- [ ] low_conf marca findings quando max conf < limiar; limiar 0 desliga
- [ ] Gate: `pytest -q tests/unit/test_engine.py`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(engine): emit scope markers without STRIDE and attach detection confidence`

---

### T6: Pipeline — wire dedupe + low_conf

**What**: Chamar dedupe após predict; nota se removidas; passar low_conf ao engine.
**Where**: `src/stride_mvp/pipeline/run.py`, `tests/unit/test_pipeline_run.py`
**Depends on**: T4, T5
**Reuses**: run_pipeline injection pattern
**Requirement**: DED-01, DED-02

**Done when**:

- [ ] Duas caixas sobrepostas mesma classe → 1 detecção no report
- [ ] Note menciona remoções quando >0
- [ ] Gate: `pytest -q tests/unit/test_pipeline_run.py`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(pipeline): dedupe detections before STRIDE analysis`

---

### T7: Relatório — confiança e scope no sumário

**What**: Coluna Confiança; ⚠; nota de baixa confiança; JSON aditivo; scope só no sumário.
**Where**: `src/stride_mvp/stride/report.py`, `tests/unit/test_report.py`
**Depends on**: T5
**Reuses**: `_summary_table` / ROLE_TITLES
**Requirement**: CONF-01..03, SEM-05

**Done when**:

- [ ] Sumário tem coluna Confiança
- [ ] low_confidence → ⚠ no nome + nota no MD
- [ ] JSON inclui max_confidence e low_confidence
- [ ] Findings scope não aparecem em seções de ameaça/controle
- [ ] Gate: `pytest -q tests/unit/test_report.py`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(report): show confidence column, low-conf warning, and scope-only summary rows`

---

### T8: Regressão e2e arch1/arch2 (fidelity)

**What**: Cenários ScriptedDetector replicando componentes do review Gemini com asserções de termos e contagens.
**Where**: `tests/integration/test_e2e_pipeline.py`
**Depends on**: T1–T7
**Reuses**: ScriptedDetector / FixedDetector
**Requirement**: REG-01, REG-02

**Done when**:

- [ ] REG-01 AWS: EFS/Backup/SES/ASG/region passam termos obrigatórios/proibidos
- [ ] REG-02 Azure: entra duplicado colapsa; RG sem STRIDE; Logic Apps/SaaS sem container vocab
- [ ] Gate: `pytest -q` (full)

**Tests**: integration
**Gate**: full
**Commit**: `test(fidelity): add arch1/arch2 regression scenarios from Gemini review`

---

### T9: AD-008 + handoff STATE

**What**: Registrar AD-008 (famílias, scope, limiares) e atualizar Handoff.
**Where**: `.specs/STATE.md`
**Depends on**: T8
**Reuses**: Formato AD-NNN
**Requirement**: (processo / memory)

**Done when**:

- [ ] AD-008 active documentando decisões desta feature
- [ ] Handoff aponta Execute completo + Verifier
- [ ] Gate: `python -m compileall -q src && pytest -q`

**Tests**: none
**Gate**: build
**Commit**: `docs(state): record AD-008 stride-report-fidelity decisions and handoff`

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3

Phase 1:  T1 ──→ T2
Phase 2:  T3 ──→ T4 ──→ T5 ──→ T6
Phase 3:  T7 ──→ T8 ──→ T9
```

Total: 9 tasks (single batch — execute inline).

---

## Diagram-Definition Cross-Check

| Task | Depends On (body) | Diagram Shows | Status |
| ---- | ----------------- | ------------- | ------ |
| T1 | None | (start) | ✅ |
| T2 | T1 | T1→T2 | ✅ |
| T3 | None | (start Phase 2) | ✅ |
| T4 | T3 | T3→T4 | ✅ |
| T5 | T2, T3 | after T2+T3 via T4→T5 (phase order) | ✅ |
| T6 | T4, T5 | T5→T6 | ✅ |
| T7 | T5 | T6→T7 (phase) | ✅ |
| T8 | T1–T7 | T7→T8 | ✅ |
| T9 | T8 | T8→T9 | ✅ |

## Test Co-location Validation

| Task | Layer | Matrix Requires | Task Says | Status |
| ---- | ----- | --------------- | --------- | ------ |
| T1 | class_map | unit | unit | ✅ |
| T2 | KB | unit | unit | ✅ |
| T3 | config/models | unit | unit | ✅ |
| T4 | dedupe | unit | unit | ✅ |
| T5 | engine | unit | unit | ✅ |
| T6 | pipeline | unit | unit | ✅ |
| T7 | report | unit | unit | ✅ |
| T8 | e2e | integration | integration | ✅ |
| T9 | docs | none | none | ✅ |
