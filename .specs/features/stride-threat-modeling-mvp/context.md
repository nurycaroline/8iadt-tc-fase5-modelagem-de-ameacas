# STRIDE Threat Modeling MVP — Context

**Gathered:** 2026-07-28
**Spec:** `.specs/features/stride-threat-modeling-mvp/spec.md`
**Status:** Ready for Execute — Design + Tasks drafts written; awaiting user approval

---

## Feature Boundary

MVP de viabilidade: a partir de **imagem** de diagrama de arquitetura de software, um **detector supervisionado** identifica componentes; um pipeline gera **Relatório de Modelagem de Ameaças STRIDE** enriquecido com **vulnerabilidades e contramedidas** a partir de uma KB versionada. Inclui dataset anotado, treino, inferência e documentação do fluxo. Exclui auth, integração SAST/DAST, treino de LLM do zero e remediação automática de código.

---

## Implementation Decisions

### Detecção de componentes (visão)

- Abordagem: object detection supervisionada com bounding boxes (YOLO-family ou equivalente leve).
- Vocabulário mínimo de classes documentado na spec (user, client, web_server, api, application, database, cache, queue_broker, external_service, firewall_gateway, load_balancer, storage).
- Inferência retorna classe + confiança + bbox; limiar configurável.

### Geração STRIDE e relatório

- Híbrido determinístico: regras componente→STRIDE + KB de vulnerabilidades/contramedidas.
- LLM opcional apenas para redação/polimento do relatório; falha do LLM não bloqueia saída regra+KB.
- Idioma do relatório: pt-BR.
- Formatos: Markdown (obrigatório) e HTML opcional; JSON estruturado desejável para testes.

### Dataset e anotação

- **Confirmado pelo usuário (2026-07-28):** base de treino = [Software Architecture Dataset (Kaggle — carlosrian)](https://www.kaggle.com/datasets/carlosrian/software-architecture-dataset) (~8k PNG aumentados, Pascal VOC, ~87 tipos de serviço cloud AWS/Azure/GCP).
- Converter VOC → formato do treino (ex.: YOLO) no Design; documentar download (Kaggle CLI/API) e o que versionar no git vs. ignore/LFS.
- Manter mapa `classe Kaggle → família` para KB STRIDE (database, compute, api, storage, network, security, messaging, client/user, etc.).
- Complementar com imagens anotadas das Arquiteturas 1–2 do enunciado (avaliação/demo), no mesmo pipeline de labels.
- Split train/val documentado.

### Interface e demo

- P1: CLI/script/API local imagem→relatório.
- P2: UI web mínima de upload se houver tempo.
- Sem autenticação no MVP.

### Knowledge base

- Arquivos YAML/JSON versionados mapeando (família de componente, categoria STRIDE) → ameaças, vulnerabilidades exemplo, contramedidas.
- Sem dependência obrigatória de API CVE online no MVP.

### Agent's Discretion

- Tamanho do subset de treino smoke vs full Kaggle (docs devem cobrir ambos).
- Se Gradio (T21) for cortado por tempo, CLI+docs bastam para P1; UI permanece P2 no tasks.md.
- Checkpoint demo pré-treinado vs treinar do zero no ambiente do avaliador.

### Declined / Undiscussed Gray Areas → Assumptions

Todas as gray areas abaixo **não foram discutidas com o usuário** (sessão assíncrona), exceto dataset. Defaults e racionales:

1. Object detection vs VLM puro → object detection supervisionada (**AD-004: Ultralytics YOLO11n**)
2. STRIDE por regras+KB vs LLM-only → híbrido regras+KB (LLM fora do P1)
3. CLI vs web-first → CLI/API P1, Gradio UI P2 (T21)
4. **Dataset → confirmado: Kaggle Software Architecture Dataset (carlosrian)** + anotações das Figuras 1–2 para eval
5. KB estática vs CVE live → estática versionada YAML
6. Auth → N/A no MVP
7. Stack app → **AD-005: Python + pytest + Typer**

---

## Specific References

- Enunciado: *Hackathon — Modelagem de ameaças utilizando IA* (FIAP Software Security / IADT Fase 5)
- Metodologia: STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege)
- Avaliação: Arquitetura 1 e Arquitetura 2 (figuras do PDF do enunciado)
- Dataset (confirmado): [Software Architecture Dataset — Kaggle/carlosrian](https://www.kaggle.com/datasets/carlosrian/software-architecture-dataset)
- Entregáveis acadêmicos: documentação do fluxo, vídeo ≤15 min, link GitHub

---

## Deferred Ideas

- Detecção supervisionada de data flows/setas como classes
- Sync contínuo com NVD/CVE
- Multi-usuário / histórico de análises em banco
- Plugin IDE / CI gate em PRs
- Fine-tuning de VLM multimodal end-to-end no lugar do detector
