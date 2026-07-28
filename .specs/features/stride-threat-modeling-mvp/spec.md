# STRIDE Threat Modeling MVP — Specification

## Problem Statement

Arquitetos e desenvolvedores precisam modelar ameaças de segurança a partir de diagramas de arquitetura, mas o processo STRIDE é manual, lento e depende de especialistas. A FIAP Software Security quer validar a viabilidade de uma feature que, a partir de uma **imagem** de diagrama de arquitetura, identifica componentes com IA supervisionada e gera automaticamente um **Relatório de Modelagem de Ameaças STRIDE**, com vulnerabilidades e contramedidas por componente.

## Goals

- [ ] Detectar componentes de arquitetura (usuário, servidor, banco, API, etc.) a partir de imagem de diagrama, com modelo treinado de forma supervisionada
- [ ] Gerar Relatório de Modelagem de Ameaças baseado em STRIDE para as arquiteturas de avaliação do hackathon
- [ ] Associar vulnerabilidades e contramedidas a cada ameaça/componente identificado
- [ ] Entregar documentação do fluxo de desenvolvimento, repositório no GitHub e material para vídeo de até 15 minutos

## Out of Scope

Explicitamente excluído para evitar scope creep no MVP do hackathon.

| Feature | Reason |
| ------- | ------ |
| Detecção de fluxos/data flows com setas como entidades de treino | MVP foca em **componentes**; fluxos podem ser inferidos por regras/heurística pós-detecção, sem dataset de setas |
| Autenticação de usuários / multi-tenant | MVP de viabilidade; uso local/demo |
| Integração contínua com scanners SAST/DAST em produção | Fora do escopo do hackathon |
| Treino de modelo de linguagem do zero para gerar STRIDE | Geração STRIDE via regras + base de conhecimento (e opcionalmente LLM já treinado), não treino de LLM |
| App mobile | Entrega web/CLI suficiente |
| Correção automática de vulnerabilidades no código | Apenas modelagem e recomendações |
| Dataset massivo de produção (milhares de imagens rotuladas) | MVP: dataset mínimo viável anotado para demo e métricas básicas |
| Garantia de cobertura CVE em tempo real | Base estática/curada no MVP; sync online opcional P3 |

---

## Assumptions & Open Questions

Toda ambiguidade resolvida ou registrada aqui — nada fica silenciosamente indefinido. Premissas definidas pelo agente (modo assíncrono) com base no enunciado do hackathon; confirmaçõessubstituem estes defaults.

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --------------------- | -------------- | --------- | ---------- |
| Abordagem de detecção de componentes | Object detection supervisionada (ex.: YOLO/RT-DETR ou equivalente) sobre bounding boxes de componentes no diagrama | Enunciado exige dataset anotado + treino supervisionado para identificar componentes | n |
| Geração STRIDE após detecção | Pipeline híbrido: (1) mapa componente→categorias STRIDE por regras; (2) enriquecimento com KB de vulnerabilidades/contramedidas; (3) opcional LLM só para redigir o relatório | Evita depender só de LLM (não atende “treino supervisionado”) e entrega relatório legível | n |
| Interface do MVP | Upload de imagem via API/CLI + relatório Markdown/HTML; UI web mínima opcional (P2) | Suficiente para demo e avaliação nas arquiteturas de teste | n |
| Dataset | **Confirmado:** [Software Architecture Dataset (Kaggle — carlosrian)](https://www.kaggle.com/datasets/carlosrian/software-architecture-dataset) como base de treino (~8k imagens aumentadas, Pascal VOC, componentes cloud AWS/Azure/GCP). Complementar com imagens/anotações das Arquiteturas 1–2 do enunciado (e equivalentes) para avaliação/demo | Atende “buscar dataset” + anotações VOC prontas; avaliação do hackathon exige cobertura das figuras do PDF | y |
| Classes de componentes | Partir das **87 classes de serviços cloud** do dataset Kaggle no treino; manter um **mapa de famílias** (ex.: database, api, compute, storage, network, security, messaging, user/client) para o lookup STRIDE/KB — sem reinventar vocabulário paralelo no treino | Alinha o detector ao dataset escolhido; STRIDE opera em famílias, não em 87 ameaças distintas por serviço | y |
| Base de vulnerabilidades/contramedidas | KB estática versionada (YAML/JSON) mapeando componente + categoria STRIDE → ameaças, exemplos de vulnerabilidade, contramedidas | Determinístico, auditável, demo estável sem depender de rede | n |
| Idioma do relatório | Português (pt-BR) | Enunciado e entrega acadêmica em PT | n |
| Critério de sucesso na avaliação | Rodar nas Arquiteturas 1 e 2 do PDF e produzir relatório STRIDE completo com componentes detectados | Critério explícito de avaliação do hackathon | n |
| Auth / rate limit | N/A no MVP — ferramenta local/demo sem login | Hackathon de viabilidade | n |
| Persistência de análises | Opcional: salvar último resultado em arquivo; sem banco obrigatório | Simplifica MVP | n |

**Open questions:** nenhuma pendente sem registro — todas as áreas cinzentas estão como assumptions acima (aguardam confirmação do usuário).

---

## User Stories

### P1: Dataset anotado de diagramas de arquitetura ⭐ MVP

**User Story**: Como time de ML/segurança, quero um dataset de imagens de diagramas de arquitetura anotado com bounding boxes e classes de componentes, para treinar um detector supervisionado.

**Why P1**: Sem dataset anotado não há treino supervisionado exigido pelo enunciado.

**Acceptance Criteria**:

1. WHEN o dataset for preparado THEN o sistema SHALL usar o **Software Architecture Dataset (Kaggle — carlosrian)** como fonte principal de treino, com download/uso documentado (path local ou script; sem commit obrigatório dos ~8k binários no git se LFS/ignore for usado)
2. WHEN uma imagem anotada do Kaggle for lida THEN cada anotação SHALL estar em Pascal VOC (XML) ou convertida para o formato de treino escolhido (ex.: YOLO), preservando bounding box e classe de componente
3. WHEN o vocabulário de classes for consultado THEN o sistema SHALL documentar as classes do Kaggle usadas no treino e o **mapa classe→família** usado pela KB STRIDE
4. WHEN as Arquiteturas 1–2 do enunciado (ou equivalentes) forem usadas na avaliação/demo THEN essas imagens SHALL existir no repo (ou path documentado), anotadas no mesmo pipeline, mesmo que o volume principal de treino venha do Kaggle

**Independent Test**: Baixar/apontar o Kaggle, listar N imagens com XML VOC válido; confirmar presença das imagens de avaliação estilo Figuras 1–2.

---

### P1: Treinar detector supervisionado de componentes ⭐ MVP

**User Story**: Como time de ML, quero treinar um modelo supervisionado que localize e classifique componentes em uma imagem de diagrama, para alimentar a modelagem STRIDE.

**Why P1**: Objetivo central do hackathon — IA que interpreta o diagrama automaticamente.

**Acceptance Criteria**:

1. WHEN o pipeline de treino for executado com o dataset anotado THEN o sistema SHALL produzir artefatos de modelo persistidos (pesos + metadados de classes)
2. WHEN uma imagem de diagrama válida for submetida à inferência THEN o modelo SHALL retornar uma lista de detecções com `classe`, `confiança` e `bounding_box`
3. WHEN a confiança de uma detecção for abaixo de um limiar configurável THEN o sistema SHALL excluir ou marcar essa detecção como baixa confiança (comportamento documentado)
4. WHEN a inferência for executada nas Arquiteturas 1 e 2 (ou imagens equivalentes no dataset de avaliação) THEN o sistema SHALL retornar pelo menos os componentes principais esperados dessas arquiteturas (servidores/apps, bancos, clientes/usuários quando presentes)

**Independent Test**: Rodar inferência em uma imagem de teste conhecida e verificar JSON/lista de detecções com classes corretas nos componentes principais.

---

### P1: Relatório de Modelagem de Ameaças STRIDE ⭐ MVP

**User Story**: Como analista de segurança, quero um relatório STRIDE gerado a partir dos componentes detectados, para identificar ameaças sem modelagem manual completa.

**Why P1**: Entregável de negócio do MVP — “Relatório de Modelagem de Ameaças baseado em STRIDE”.

**Acceptance Criteria**:

1. WHEN componentes forem detectados em um diagrama THEN o sistema SHALL gerar um relatório que cubra as categorias STRIDE aplicáveis: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege
2. WHEN um componente tiver ameaças mapeadas THEN o relatório SHALL listar, para cada ameaça relevante: componente afetado, categoria STRIDE, descrição da ameaça
3. WHEN o relatório for gerado THEN o formato de saída SHALL ser Markdown e/ou HTML legível para humanos (além de JSON estruturado opcional)
4. WHEN um tipo de componente não tiver mapeamento STRIDE na KB THEN o relatório SHALL indicar explicitamente “sem mapeamento” / ameaça genérica documentada — nunca omitir o componente sem menção

**Independent Test**: A partir de uma lista mock de componentes (sem modelo), gerar relatório e verificar presença das 6 categorias STRIDE onde aplicável e menção a cada componente.

---

### P1: Vulnerabilidades e contramedidas por componente/ameaça ⭐ MVP

**User Story**: Como analista de segurança, quero ver vulnerabilidades relacionadas e contramedidas específicas para cada ameaça, para priorizar mitigação.

**Why P1**: Exigência explícita do enunciado.

**Acceptance Criteria**:

1. WHEN uma ameaça STRIDE for emitida para um componente THEN o sistema SHALL incluir pelo menos um exemplo de vulnerabilidade relacionada (nome/descrição; CVE opcional se existir na KB)
2. WHEN uma ameaça STRIDE for emitida THEN o sistema SHALL incluir pelo menos uma contramedida específica e acionável
3. WHEN a KB for consultada THEN o conteúdo SHALL ser versionável no repositório (arquivos de dados, não hardcode espalhado)
4. WHEN um componente for detectado THEN o sistema SHALL buscar entradas na KB pela combinação componente (ou família) + categoria STRIDE

**Independent Test**: Para `database` + Information Disclosure, verificar que a saída inclui vulnerabilidade + contramedida vindas da KB.

---

### P1: Pipeline ponta a ponta (imagem → relatório) ⭐ MVP

**User Story**: Como avaliador do hackathon, quero enviar uma imagem de arquitetura e receber o relatório completo, para validar a viabilidade da feature.

**Why P1**: Demo e critério de avaliação exigem fluxo completo.

**Acceptance Criteria**:

1. WHEN o usuário fornecer o caminho/arquivo de uma imagem de diagrama válida THEN o sistema SHALL executar detecção → mapeamento STRIDE → enriquecimento KB → emissão do relatório sem passos manuais intermediários obrigatórios
2. WHEN a imagem for inválida (formato não suportado, arquivo corrompido, vazio) THEN o sistema SHALL falhar com mensagem clara e código de saída/erro não-zero (CLI) ou status de erro (API)
3. WHEN o pipeline concluir com sucesso THEN o sistema SHALL persistir ou imprimir o relatório em local/stdout documentado
4. WHEN o pipeline for executado nas Arquiteturas de teste do enunciado THEN SHALL produzir relatório completo utilizável na demonstração

**Independent Test**: Um comando/script documentado processa `samples/arch1.png` e gera `reports/arch1.md`.

---

### P2: Documentação do fluxo de desenvolvimento

**User Story**: Como avaliador, quero documentação detalhando o fluxo usado para desenvolver a solução, para entender dataset, treino, inferência e geração STRIDE.

**Why P2**: Entregável obrigatório do hackathon; pode acompanhar o MVP técnico.

**Acceptance Criteria**:

1. WHEN o README/docs for aberto THEN SHALL descrever: origem do dataset, processo de anotação, treino, inferência, geração STRIDE e como reproduzir a demo
2. WHEN um avaliador seguir as instruções THEN SHALL conseguir rodar o pipeline nas imagens de avaliação (ou equivalentes) sem conhecimento prévio do código

**Independent Test**: Checklist de reprodução seguido por pessoa/agente externo usando só a documentação.

---

### P2: UI web mínima de upload

**User Story**: Como demonstrador, quero uma página simples para enviar a imagem e ver o relatório, para gravar o vídeo de até 15 minutos com mais clareza.

**Why P2**: Facilita o vídeo; CLI sozinha já cumpre viabilidade técnica.

**Acceptance Criteria**:

1. WHEN o usuário acessar a UI THEN SHALL poder selecionar/enviar uma imagem de diagrama
2. WHEN o processamento terminar THEN SHALL exibir o relatório (ou link/arquivo gerado) na mesma sessão

**Independent Test**: Upload de imagem de teste na UI e visualização do relatório.

---

### P3: Métricas de qualidade do detector

**User Story**: Como time de ML, quero métricas básicas (mAP ou precision/recall por classe) no conjunto de validação, para evidenciar a qualidade do modelo no vídeo/docs.

**Why P3**: Fortalece a narrativa de viabilidade; não bloqueia a demo.

**Acceptance Criteria**:

1. WHEN a avaliação do modelo for executada THEN o sistema SHALL reportar pelo menos uma métrica agregada de detecção no split de validação
2. WHEN o relatório de métricas for gerado THEN SHALL ser salvável/versionável junto aos artefatos de treino

**Independent Test**: Rodar script de eval e inspecionar arquivo/stdout com métrica numérica.

---

## Edge Cases

- WHEN a imagem não contém diagramas reconhecíveis / zero detecções acima do limiar THEN o sistema SHALL informar que nenhum componente foi detectado e não inventar ameaças
- WHEN houver detecções duplicadas sobrepostas do mesmo componente THEN o sistema SHALL aplicar NMS (ou equivalente) e emitir uma ocorrência por instância após supressão
- WHEN o modelo detectar classe fora do vocabulário esperado (erro de configuração) THEN o sistema SHALL rejeitar ou mapear para “unknown” e registrar no relatório/log
- WHEN a KB estiver incompleta para uma classe THEN o sistema SHALL ainda listar o componente e aplicar fallback genérico STRIDE documentado
- WHEN o arquivo de imagem exceder um tamanho máximo configurado THEN o sistema SHALL rejeitar com mensagem clara
- WHEN o treino for interrompido THEN artefatos parciais NÃO SHALL ser publicados como modelo “pronto” sem flag/documentação explícita

---

## Implicit-Requirement Dimensions Sweep

| Dimension | Resolution |
| --------- | ---------- |
| Input validation & bounds | Formatos PNG/JPG; tamanho máximo configurável; rejeição com erro claro (P1 pipeline) |
| Failure / partial-failure states | Falha de inferência/treino → erro explícito; zero detecções → mensagem sem relatório inventado |
| Idempotency / retry / duplicate handling | Pipeline local idempotente por entrada; NMS para duplicatas espaciais |
| Auth boundaries & rate limits | N/A — MVP local/demo sem auth |
| Concurrency / ordering | N/A — processamento sequencial por imagem no MVP |
| Data lifecycle / expiry | Relatórios/artefatos locais; sem TTL obrigatório |
| Observability | Logs básicos de pipeline (início, N detecções, fim/erro); métricas de treino se P3 |
| External-dependency failure | KB local; se LLM opcional falhar, relatório regra+KB ainda SHALL ser emitido |
| State-transition integrity | N/A — sem máquina de estados de usuário; fluxo linear imagem→relatório |

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| -------------- | ----- | ----- | ------ |
| DATA-01 | P1: Dataset anotado | Design | Pending |
| DATA-02 | P1: Dataset anotado — vocabulário de classes | Design | Pending |
| DATA-03 | P1: Dataset — cobertura estilo Figuras 1–2 | Design | Pending |
| DET-01 | P1: Treinar detector — artefatos de modelo | Design | Pending |
| DET-02 | P1: Inferência retorna classe/confiança/bbox | Design | Pending |
| DET-03 | P1: Limiar de confiança | Design | Pending |
| DET-04 | P1: Inferência nas arquiteturas de avaliação | Design | Pending |
| STRIDE-01 | P1: Relatório cobre categorias STRIDE | Design | Pending |
| STRIDE-02 | P1: Ameaça com componente + categoria + descrição | Design | Pending |
| STRIDE-03 | P1: Formato Markdown/HTML | Design | Pending |
| STRIDE-04 | P1: Componente sem mapeamento tratado | Design | Pending |
| KB-01 | P1: Vulnerabilidade por ameaça | Design | Pending |
| KB-02 | P1: Contramedida por ameaça | Design | Pending |
| KB-03 | P1: KB versionável no repo | Design | Pending |
| KB-04 | P1: Lookup por componente + STRIDE | Design | Pending |
| PIPE-01 | P1: Pipeline ponta a ponta | Design | Pending |
| PIPE-02 | P1: Erro em imagem inválida | Design | Pending |
| PIPE-03 | P1: Persistência/stdout do relatório | Design | Pending |
| PIPE-04 | P1: Demo nas arquiteturas de teste | Design | Pending |
| DOC-01 | P2: Documentação do fluxo | - | Pending |
| DOC-02 | P2: Reprodução via docs | - | Pending |
| UI-01 | P2: Upload na UI | - | Pending |
| UI-02 | P2: Exibir relatório | - | Pending |
| MET-01 | P3: Métrica agregada de detecção | - | Pending |
| MET-02 | P3: Relatório de métricas persistido | - | Pending |

**ID format:** `DATA|DET|STRIDE|KB|PIPE|DOC|UI|MET`-NN

**Status values:** Pending → In Design → In Tasks → Implementing → Verified

**Coverage:** 25 total, 0 mapped to tasks, 25 unmapped (esperado — fase Specify; Tasks ainda não iniciada)

---

## Success Criteria

- [ ] Pipeline reproduzível: imagem de arquitetura → componentes detectados → relatório STRIDE com vulnerabilidades e contramedidas
- [ ] Dataset anotado + modelo treinado versionados/documentados no repositório
- [ ] Arquiteturas de avaliação do hackathon (Figuras 1 e 2 ou equivalentes) processadas com relatório completo
- [ ] Documentação do fluxo de desenvolvimento pronta para entrega
- [ ] Repositório GitHub organizado para submissão (vídeo fica a cargo do time, fora do código)
