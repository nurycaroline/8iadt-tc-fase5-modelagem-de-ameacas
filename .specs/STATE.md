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

## Handoff

- **Feature**: STRIDE Threat Modeling MVP / `.specs/features/stride-threat-modeling-mvp/`
- **Phase / Task**: Execute completo (T1–T22) — aguardando Verifier
- **Completed**: Specify, Design, Tasks; T1–T22 (incl. Docker extra)
- **In-progress**: none
- **Next step**: Verifier automático (validation.md) + treino real YOLO com dataset Kaggle quando houver GPU/credenciais
- **Blockers**: none (pesos `.pt` ainda não treinados — demo usa mock/detector injetável nos testes)
- **Branch**: `feat/stride-mvp-execute`
