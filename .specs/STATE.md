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

## Handoff

- **Feature**: STRIDE Threat Modeling MVP / `.specs/features/stride-threat-modeling-mvp/`
- **Phase / Task**: Specify — spec.md + context.md criados; aguardando confirmação do usuário
- **Completed**: none (implementação ainda não iniciada)
- **In-progress**: `.specs/features/stride-threat-modeling-mvp/spec.md` — spec draft pronta para review
- **Next step**: Usuário confirma (ou ajusta) assumptions/P1–P3; em seguida fase Design (`design.md`)
- **Blockers**: Confirmação das assumptions (detecção YOLO-like, KB estática, CLI P1, UI P2, pt-BR)
- **Uncommitted files**: `.specs/**` (a commitar nesta sessão)
- **Branch**: `cursor/stride-threat-modeling-spec-bf8d`
