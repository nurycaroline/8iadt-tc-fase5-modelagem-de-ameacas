# STATE

## Decisions

### AD-001
- **Decision**: O MVP de modelagem de ameaças usa detecção supervisionada de componentes em imagem + pipeline híbrido (regras STRIDE + KB) — não LLM-only.
- **Reason**: O enunciado do hackathon exige dataset anotado, treino supervisionado e relatório STRIDE com vulnerabilidades/contramedidas.
- **Trade-off**: Menos “magia” generativa end-to-end; mais determinismo e alinhamento ao requisito de ML supervisionado.
- **Scope**: Feature `stride-threat-modeling-mvp` e qualquer extensão de análise por diagrama.
- **Date**: 2026-07-28
- **Status**: active

### AD-002
- **Decision**: Artefatos de especificação vivem em `.specs/` (STATE, features/[nome]/spec|context|design|tasks|validation).
- **Reason**: Convenção da skill tlc-spec-driven adotada no repositório.
- **Trade-off**: Docs de produto fora de `docs/` até Design/entrega; README de entrega virá depois.
- **Scope**: Todo o repositório / processo de feature.
- **Date**: 2026-07-28
- **Status**: active

### AD-003
- **Decision**: Dataset de treino do detector = Software Architecture Dataset no Kaggle (`carlosrian/software-architecture-dataset`); eval/demo complementar com Arquiteturas 1–2 do enunciado anotadas no mesmo pipeline.
- **Reason**: Escolha explícita do usuário; dataset já anotado (Pascal VOC), alinhado a hackathon FIAP e detecção de componentes em diagramas cloud.
- **Trade-off**: Classes são serviços cloud específicos (~87) — exige mapa classe→família para STRIDE/KB; binários grandes ficam fora do git (download documentado).
- **Scope**: Feature `stride-threat-modeling-mvp` (DATA-*, DET-*, KB lookup).
- **Date**: 2026-07-28
- **Status**: active

### AD-004
- **Decision**: Stack de detecção = Ultralytics YOLO11n (nano) com conversão Pascal VOC → labels YOLO.
- **Reason**: Approach A do design; NMS nativo, treino/inferência simples, alinhado ao dataset Kaggle VOC.
- **Trade-off**: Dependência do ecossistema Ultralytics; domain shift possível vs. diagramas genéricos do PDF (mitigado com `data/eval/` + fine-tune).
- **Scope**: Treino/inferência do MVP e scripts de métricas.
- **Date**: 2026-07-28
- **Status**: active

### AD-005
- **Decision**: Aplicação em Python 3.11+ (`src/stride_mvp` + `pyproject.toml`); testes com pytest; CLI Typer; UI P2 Gradio.
- **Reason**: Greenfield ML/CV; strong defaults de teste na ausência de guidelines do repo.
- **Trade-off**: Sem frontend React; Gradio só no P2.
- **Scope**: Todo o código do MVP.
- **Date**: 2026-07-28
- **Status**: active

### AD-006
- **Decision**: Instalação de deps via `uv` + pré-instalação de PyTorch do índice CPU (`scripts/install_deps.sh`); Docker e Cloud Agents seguem o mesmo caminho.
- **Reason**: `pip install -e ".[ml,…]"` puxava wheels CUDA multi-GB e resolvia lento; CPU basta para demo/inferência neste MVP.
- **Trade-off**: GPU local precisa de `STRIDE_TORCH_INDEX` apontando para índice CUDA.
- **Scope**: Setup local, Dockerfile, `.cursor/environment.json`.
- **Date**: 2026-08-03
- **Status**: active

### AD-007
- **Decision**: Componentes-controle (WAF, Shield, KMS, CloudTrail, CloudWatch, edge) geram **verificações de eficácia/configuração** (role `control`), não ameaças genéricas de exposição; componentes sem mapeamento viram **inventário** (categoria `Não classificado`), nunca "Information Disclosure" inventado. Detecções repetidas são agrupadas por classe (`instance_count`). Relatório expõe `coverage` com warning abaixo de `STRIDE_MIN_COVERAGE`.
- **Reason**: Review externo do relatório AWS real mostrou 30/34 findings em fallback genérico e controles tratados como superfícies vulneráveis — perda de credibilidade técnica.
- **Trade-off**: Menos findings totais (dedupe); componentes não classificados não recebem ameaça (mas ficam visíveis no inventário para curadoria).
- **Scope**: Feature `stride-report-quality` (class_map, KB v2 com `roles`, engine, report, CLI `check-map`).
- **Date**: 2026-08-05
- **Status**: active

## Handoff

- **Feature**: STRIDE Report Quality / `.specs/features/stride-report-quality/`
- **Phase / Task**: Execute T1–T12 concluído (12 commits) — Verifier pendente
- **Completed**: T1 aliases/vendor strip; T2 class_map v2 (edge/observability/zone + vocabulário AWS); T3 CLI check-map; T4 KB v2 roles; T5 entradas edge/observability/zone + consistência map↔KB; T6 fallback de inventário; T7 dedupe + role; T8 coverage + warning; T9 Markdown por role; T10 JSON v2; T11 e2e cenário AWS; T12 docs + AD-007. Gate full: 109 passed.
- **In-progress**: Verifier automático (feature-level validation)
- **Next step**: Verifier sub-agent (spec-anchored + discrimination sensor) → validation.md; após treino real, rodar `stride-mvp check-map` contra `classes.txt`/pesos para fechar MAP-02 canônico
- **Blockers**: none (CI usa ScriptedDetector; validação canônica do vocabulário exige artefatos do treino real)
- **Branch**: `cursor/stride-report-quality-spec-062c`

