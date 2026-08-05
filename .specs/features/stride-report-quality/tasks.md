# STRIDE Report Quality — Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user — do not proceed without it.**

---

**Design**: `.specs/features/stride-report-quality/design.md`  
**Status**: Done (T1–T12 implemented; Verifier pending)

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec — confirm before Execute. Guidelines found: **none além do padrão pytest já estabelecido no repositório** (matriz herda o padrão da feature `stride-threat-modeling-mvp`).

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| ClassFamilyMapper (normalização/aliases) | unit | 1:1 ACs MAP-01/02 + edges (prefixo colidente, classe vazia) | `tests/unit/test_class_map.py` | `pytest -q tests/unit` |
| class_map.yaml + consistência map↔KB | unit | MAP-02, KBX-06 (toda família do map tem KB) | `tests/unit/test_class_map.py`, `tests/unit/test_kb.py` | `pytest -q tests/unit` |
| ThreatKB (roles, v1 compat) | unit | KBX-01 + edge YAML v1 sem roles | `tests/unit/test_kb.py` | `pytest -q tests/unit` |
| KB entries (edge/observability/zone) | unit | KBX-02/03/04/05 — asserts de conteúdo por família×categoria | `tests/unit/test_kb.py`, `tests/unit/test_engine.py` | `pytest -q tests/unit` |
| StrideEngine (agrupamento, fallback, coverage) | unit | 1:1 ENG-01/02/03 + edges (tudo unknown, zero detecções, confidências mistas) | `tests/unit/test_engine.py` | `pytest -q tests/unit` |
| ReportRenderer (seções por role, JSON v2) | unit | 1:1 REP-01/02 + edge seções vazias omitidas | `tests/unit/test_report.py` | `pytest -q tests/unit` |
| CLI check-map + warning coverage | integration | MAP-03 exit codes; ENG-03 stderr warning | `tests/integration/test_cli.py` | `pytest -q` |
| e2e pipeline (relatório novo nas eval arches) | integration | Regressão DET-04/PIPE-04 com novo layout | `tests/integration/test_e2e_pipeline.py` | `pytest -q` |
| Docs (fluxo/README) | none | review manual | — | build |

## Gate Check Commands

> Herdado do repositório — confirm before Execute.

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | Após tasks com unit tests | `pytest -q tests/unit` |
| Full | Após tasks com integration | `pytest -q` |
| Build | Fim de fase / config-only | `python -m compileall -q src && pytest -q` |

---

## Execution Plan

### Phase 1: Vocabulário e mapeamento

```
T1 → T2 → T3
```

### Phase 2: KB role-aware

```
T4 → T5
```

### Phase 3: Engine

```
T6 → T7 → T8
```

### Phase 4: Relatório + integração + docs

```
T9 → T10 → T11 → T12
```

---

## Task Breakdown

### T1: Normalização de aliases com strip de prefixo de vendor

**What**: Lookup em duas fases no `ClassFamilyMapper.to_family` — nome completo primeiro; sem match, remover prefixos `aws_`/`amazon_`/`azure_`/`gcp_`/`google_` e tentar o nome base.  
**Where**: `src/stride_mvp/data/class_map.py`, `tests/unit/test_class_map.py`  
**Depends on**: None  
**Reuses**: `_norm` existente (lower/underscore)  
**Requirement**: MAP-01

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] `aws-waf`, `Amazon RDS`, `azure_sql_database` resolvem igual a `waf`, `rds`, `sql_database`
- [ ] Nome completo explícito no YAML tem precedência sobre o base sem prefixo
- [ ] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(data): strip vendor prefixes in class-family lookup`

---

### T2: class_map v2 — famílias edge/observability/zone + vocabulário AWS real

**What**: Estender `data/class_map.yaml` com famílias `edge`, `observability`, `zone`; reclassificar `cloudfront`/`cdn`/`waf`→`edge`, `subnet`/`vpc`→`zone`; semear classes do relatório real (shield, solr, efs, backup, internet_gateway, nat_gateway, route53, auto_scaling, x_ray, config, availability_zone, public_subnet, private_subnet…).  
**Where**: `data/class_map.yaml`, `tests/unit/test_class_map.py`  
**Depends on**: T1  
**Reuses**: loader existente  
**Requirement**: MAP-02

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] Todas as classes citadas no review real resolvem para família ≠ `unknown` (teste parametrizado)
- [ ] `cloudfront` → `edge`; `public_subnet` → `zone`; `cloudtrail` → `observability`
- [ ] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(data): add edge/observability/zone families and AWS vocabulary`

---

### T3: CLI `check-map` (auditoria de cobertura do vocabulário)

**What**: Comando `stride-mvp check-map --classes <classes.txt>` (ou `--weights best.pt` lendo `names`) que lista classes sem família e sai ≠ 0 quando houver gap; erro acionável se a fonte não existir.  
**Where**: `src/stride_mvp/cli.py`, `src/stride_mvp/data/class_map.py` (helper `unmapped_classes`), `tests/integration/test_cli.py`  
**Depends on**: T2  
**Reuses**: `load_class_map`, padrão Typer do CLI  
**Requirement**: MAP-03

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] classes.txt com classe não mapeada → lista no stdout + exit 1
- [ ] Todas mapeadas → exit 0; fonte ausente → mensagem clara + exit ≠ 0
- [ ] Gate: `pytest -q`

**Tests**: integration  
**Gate**: full  
**Commit**: `feat(cli): add check-map vocabulary coverage command`

---

### T4: KB schema v2 — roles por família + compat v1

**What**: Bloco `roles` no `threats.yaml` (security/observability/edge→`control`, zone→`zone`, client→`external`), `ThreatKB.role(family)` com default `workload`, loader compat com YAML v1 sem `roles`.  
**Where**: `data/kb/threats.yaml`, `src/stride_mvp/stride/kb.py`, `tests/unit/test_kb.py`  
**Depends on**: T2  
**Reuses**: `ThreatKB.load` existente  
**Requirement**: KBX-01

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] `role("edge") == "control"`, `role("database") == "workload"`, YAML v1 → tudo `workload`
- [ ] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(stride): add family roles to threat KB schema`

---

### T5: Entradas KB para edge, observability e zone + consistência map↔KB

**What**: Entradas role-aware: `edge` (Spoofing bypass de origem CloudFront→ALB; DoS eficácia WAF/Shield), `observability` (Repudiation trilha/retensão; Tampering logs), `zone` (verificação estrutural única SG/NACL/rotas); fraseologia de verificação para `role: control`; novo texto de fallback de inventário; teste garantindo que toda família do class_map tem entrada na KB.  
**Where**: `data/kb/threats.yaml`, `tests/unit/test_kb.py`  
**Depends on**: T4  
**Reuses**: schema v2 de T4  
**Requirement**: KBX-02, KBX-03, KBX-04, KBX-05, KBX-06

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] `lookup("edge","Spoofing")` menciona restrição de origem; `lookup("observability","Repudiation")` menciona trilha de auditoria
- [ ] Nenhuma entrada de família `control` usa o texto genérico de exposição
- [ ] Teste de consistência: `families(class_map) - {unknown} ⊆ families(kb)`
- [ ] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(stride): add role-aware KB entries for edge, observability and zones`

---

### T6: Fallback semântico de inventário no engine

**What**: Componente sem família mapeada gera finding `stride_category="Não classificado"`, `mapped=False`, texto de inventário — remover o rótulo fixo "Information Disclosure"; atualizar testes de fallback existentes ao novo AC.  
**Where**: `src/stride_mvp/stride/engine.py`, `tests/unit/test_engine.py`  
**Depends on**: T5  
**Reuses**: `fallback_entry` (texto novo de T5)  
**Requirement**: ENG-01

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] Detecção `solr` sem mapa → finding "Não classificado"; nenhum finding fallback com categoria STRIDE
- [ ] STRIDE-04 preservado: componente nunca omitido
- [ ] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(stride): replace invented STRIDE category with inventory fallback`

---

### T7: Agrupamento de detecções por classe (dedupe)

**What**: `ThreatFinding` ganha `role: str = "workload"` e `instance_count: int = 1`; engine agrupa detecções por classe normalizada, emitindo um conjunto de findings por classe com contagem; `detections` do report inalterado.  
**Where**: `src/stride_mvp/models.py`, `src/stride_mvp/stride/engine.py`, `tests/unit/test_engine.py`  
**Depends on**: T6  
**Reuses**: `ThreatKB.role` de T4  
**Requirement**: ENG-02, KBX-04 (role propagado ao finding)

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] 6 detecções `ec2` → findings únicos com `instance_count=6`
- [ ] Zona detectada 2× → 1 verificação com `instance_count=2`
- [ ] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(stride): group findings per component class with instance count`

---

### T8: Métrica de cobertura + warning no CLI

**What**: `ThreatReport.coverage: float | None` (None com zero detecções) calculado no engine; CLI `analyze` emite warning em stderr quando `coverage < STRIDE_MIN_COVERAGE` (default 0.8) sem mudar exit code.  
**Where**: `src/stride_mvp/models.py`, `src/stride_mvp/stride/engine.py`, `src/stride_mvp/cli.py`, `src/stride_mvp/config.py`, `tests/unit/test_engine.py`, `tests/integration/test_cli.py`  
**Depends on**: T7  
**Reuses**: padrão de env override do `load_config`  
**Requirement**: ENG-03

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] 3 mapeadas + 1 unknown → coverage 0.75; zero detecções → None
- [ ] CLI: coverage 0.5 → warning stderr + exit 0
- [ ] Gate: `pytest -q`

**Tests**: unit + integration  
**Gate**: full  
**Commit**: `feat(stride): add mapping coverage metric and low-coverage warning`

---

### T9: Markdown reestruturado por papel

**What**: `to_markdown` com sumário (tabela componente×família×role×instâncias×categorias) e seções: Ameaças por componente, Controles detectados — verificações, Zonas de rede — verificações estruturais, Inventário não classificado; seções vazias omitidas.  
**Where**: `src/stride_mvp/stride/report.py`, `tests/unit/test_report.py`  
**Depends on**: T8  
**Reuses**: `_finding_md` existente  
**Requirement**: REP-01

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] Fixture workload+controle+zona+unknown → 5 seções na ordem do AC
- [ ] Sem unknown → seção de inventário ausente
- [ ] Conteúdos obrigatórios de STRIDE-03 (componente, categoria, ameaça, vulnerabilidade, contramedida) preservados
- [ ] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(stride): restructure Markdown report by component role`

---

### T10: JSON v2 (role, instance_count, coverage)

**What**: `to_json` inclui `coverage` no topo e `role`/`instance_count` por finding, mantendo campos atuais.  
**Where**: `src/stride_mvp/stride/report.py`, `tests/unit/test_report.py`  
**Depends on**: T9  
**Reuses**: payload atual  
**Requirement**: REP-02

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] JSON parseável com novos campos; campos antigos intactos (teste de chaves)
- [ ] Gate: `pytest -q tests/unit`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(stride): extend JSON report with role, instance count and coverage`

---

### T11: Regressão e2e com relatório novo + cenário AWS

**What**: Atualizar e2e das eval arches ao novo layout e adicionar cenário integração com `ScriptedDetector` simulando o diagrama AWS do review (waf, shield, cloudfront, alb, ec2, solr, rds, elasticache, efs, kms, cloudtrail, cloudwatch, backup, subnets) — assert: fallback ≤10% dos findings, controles na seção correta, dedupe efetivo.  
**Where**: `tests/integration/test_e2e_pipeline.py`  
**Depends on**: T10  
**Reuses**: `ScriptedDetector` existente  
**Requirement**: MAP-02, KBX-04, ENG-01..03, REP-01 (integração)

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] Cenário AWS: zero findings "Information Disclosure" para WAF/Shield/KMS/CloudTrail; coverage ≥ 0.9
- [ ] e2e arch1/arch2 verdes com novo layout
- [ ] Gate: `pytest -q`

**Tests**: integration  
**Gate**: full  
**Commit**: `test(stride): cover AWS review scenario end to end`

---

### T12: Docs — fluxo, README e registro de decisão

**What**: Documentar `check-map`, coverage/limiar, famílias/roles novos em `docs/fluxo-desenvolvimento.md` + README; registrar decisão AD-007 (controles ≠ superfícies; unknown = inventário) no `.specs/STATE.md`.  
**Where**: `README.md`, `docs/fluxo-desenvolvimento.md`, `.specs/STATE.md`  
**Depends on**: T11  
**Reuses**: —  
**Requirement**: REP-01 (doc), rastreabilidade

**Tools**:
- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:
- [ ] Seção "Cobertura do vocabulário" com comando copy-paste do `check-map`
- [ ] AD-007 registrado
- [ ] Gate: build (`python -m compileall -q src && pytest -q`)

**Tests**: none  
**Gate**: build  
**Commit**: `docs(stride): document vocabulary coverage and role-aware analysis`

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4

Phase 1:  T1 ──→ T2 ──→ T3
Phase 2:  T4 ──→ T5
Phase 3:  T6 ──→ T7 ──→ T8
Phase 4:  T9 ──→ T10 ──→ T11 ──→ T12
```

**Batch packing (Execute):** 12 tasks → 2 workers sugeridos  
- Batch A: Phases 1–2 (T1–T5)  
- Batch B: Phases 3–4 (T6–T12)  

Oferecer sub-agents no Execute (offer-then-confirm). Verifier automático após T12.

> **P3 (CTX-01/02)** fora deste plano — criar tasks só se o usuário confirmar após o PASS desta feature.

---

## Task Granularity Check

| Task | Scope | Status |
| ---- | ----- | ------ |
| T1 Alias normalization | 1 função + tests | ✅ |
| T2 class_map v2 | 1 yaml + tests | ✅ |
| T3 check-map CLI | 1 comando + helper | ✅ |
| T4 KB roles | 1 schema change | ✅ |
| T5 KB entries | 1 yaml + consistency test | ✅ |
| T6 Fallback semântico | 1 branch do engine | ✅ |
| T7 Dedupe | models + engine (coesos) | ✅ |
| T8 Coverage + warning | metric + CLI hook (coesos) | ✅ |
| T9 Markdown v2 | 1 renderer | ✅ |
| T10 JSON v2 | 1 método | ✅ |
| T11 e2e AWS | tests only | ✅ |
| T12 Docs + AD-006 | docs only | ✅ |

## Diagram-Definition Cross-Check

| Task | Depends On (body) | Diagram Shows | Status |
| ---- | ----------------- | ------------- | ------ |
| T1 | None | (start) | ✅ |
| T2 | T1 | T1→T2 | ✅ |
| T3 | T2 | T2→T3 | ✅ |
| T4 | T2 | Phase 1→Phase 2 | ✅ |
| T5 | T4 | T4→T5 | ✅ |
| T6 | T5 | Phase 2→Phase 3 | ✅ |
| T7 | T6 | T6→T7 | ✅ |
| T8 | T7 | T7→T8 | ✅ |
| T9 | T8 | Phase 3→Phase 4 | ✅ |
| T10 | T9 | T9→T10 | ✅ |
| T11 | T10 | T10→T11 | ✅ |
| T12 | T11 | T11→T12 | ✅ |

## Test Co-location Validation

| Task | Code Layer | Matrix Requires | Task Says | Status |
| ---- | ---------- | --------------- | --------- | ------ |
| T1 | class_map | unit | unit | ✅ |
| T2 | class_map yaml | unit | unit | ✅ |
| T3 | CLI | integration | integration | ✅ |
| T4 | KB | unit | unit | ✅ |
| T5 | KB entries | unit | unit | ✅ |
| T6 | engine | unit | unit | ✅ |
| T7 | models + engine | unit | unit | ✅ |
| T8 | engine + CLI | unit + integration | unit + integration | ✅ |
| T9 | report | unit | unit | ✅ |
| T10 | report | unit | unit | ✅ |
| T11 | e2e | integration | integration | ✅ |
| T12 | docs | none | none | ✅ |

---

## Requirement Traceability (tasks)

| Requirement ID | Task(s) |
| -------------- | ------- |
| MAP-01 | T1 |
| MAP-02 | T2, T11 |
| MAP-03 | T3 |
| KBX-01 | T4 |
| KBX-02 | T5 |
| KBX-03 | T5 |
| KBX-04 | T5, T7, T11 |
| KBX-05 | T5, T7 |
| KBX-06 | T5 |
| ENG-01 | T6, T11 |
| ENG-02 | T7, T11 |
| ENG-03 | T8, T11 |
| REP-01 | T9, T11, T12 |
| REP-02 | T10 |
| CTX-01 | — (P3, sem task) |
| CTX-02 | — (P3, sem task) |

**Coverage:** 16 total, 14 mapped to tasks, 2 unmapped (P3 deliberado) ⚠️
