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

## Handoff

- **Feature**: STRIDE Threat Modeling MVP / `.specs/features/stride-threat-modeling-mvp/`
- **Phase / Task**: Specify — dataset confirmado (Kaggle); demais assumptions ainda abertas
- **Completed**: Decisão de dataset (AD-003)
- **In-progress**: `.specs/features/stride-threat-modeling-mvp/spec.md` — review das assumptions restantes
- **Next step**: Confirmar demais assumptions (YOLO-like, KB estática, CLI P1 / UI P2) ou seguir para Design
- **Blockers**: none críticos para Design; confirmação residual das outras assumptions
- **Uncommitted files**: updates em `.specs/**`
- **Branch**: `cursor/stride-threat-modeling-spec-bf8d`
