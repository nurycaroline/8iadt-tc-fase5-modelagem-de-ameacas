# STRIDE Report Quality — Specification

## Problem Statement

Ao rodar o pipeline em um diagrama AWS real (CloudFront, WAF, Shield, ALB, EC2/Solr, RDS, ElastiCache, EFS, KMS, CloudTrail, CloudWatch, Backup, subnets), **30 de 34 findings caíram no fallback `unknown` + "Information Disclosure"**. O relatório ficou poluído com falsos positivos genéricos, tratou serviços de proteção (WAF/Shield/KMS/CloudTrail) como superfícies vulneráveis, repetiu blocos idênticos para instâncias duplicadas e não fez análise STRIDE condizente com o papel de cada serviço. Review externo (análise de outra IA) confirmou os problemas.

**Causas-raiz identificadas no código:**

1. `data/class_map.yaml` não cobre o vocabulário real do detector (87 classes do dataset Kaggle); a normalização em `ClassFamilyMapper.to_family` não remove prefixos de vendor (`aws_`, `amazon_`, `azure_`, `gcp_`).
2. `StrideEngine` rotula todo componente sem mapeamento como `Information Disclosure` — categoria STRIDE inventada sem evidência.
3. A KB (`data/kb/threats.yaml`) não tem famílias para edge/CDN, observabilidade/auditoria e zonas de rede; componentes-controle recebem o mesmo tratamento de workloads.
4. O engine emite um bloco de findings por detecção — sem agrupamento por classe — inflando o relatório.

## Goals

- [ ] 100% do vocabulário de treino do detector resolve para família ≠ `unknown` (verificado por teste/CLI)
- [ ] Zero findings com categoria STRIDE inventada: componente não mapeado vira item de **inventário** ("Não classificado"), nunca "Information Disclosure"
- [ ] Componentes-controle (WAF, Shield, KMS, CloudTrail, CloudWatch, Backup) geram **verificações de eficácia/configuração**, não ameaças genéricas
- [ ] Relatório agrupado por componente (sem blocos duplicados), com sumário e métrica de cobertura de mapeamento
- [ ] Re-executando o diagrama AWS do usuário: ≤10% dos findings em fallback

## Out of Scope

| Feature | Reason |
| ------- | ------ |
| Detecção de fluxos/setas entre componentes | Sem dataset de setas (já excluído no spec do MVP); relações inferidas só por contenção de bbox (P3) |
| Análise de configuração real (Security Groups, NACLs, policies IAM) | A imagem não contém configuração; o relatório emite **verificações**, não conclusões sobre config |
| Retreino / melhoria do detector YOLO | Feature separada; aqui corrigimos o pós-processamento (map, KB, engine, report) |
| Geração de ameaças via LLM | AD-001 mantém pipeline determinístico regras + KB |
| Sincronização online com CVE | Fora do MVP (P3 do spec original) |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --------------------- | -------------- | --------- | ---------- |
| Fonte do vocabulário de classes do detector | `data/processed/classes.txt` (gerado na conversão VOC→YOLO) ou `names` dos pesos treinados; enquanto o dataset não estiver disponível no ambiente, semear o mapa com as classes observadas no relatório real (waf, shield, cloudfront, alb, kms, cloudtrail, cloudwatch, backup, efs, elasticache, solr, subnets, gateways, route53, auto_scaling…) | O vocabulário canônico vem do dataset; classes do relatório real são evidência direta do gap | n (assíncrono — validar com `check-map` após treino) |
| Conjunto de famílias novas | `edge` (cloudfront, waf, shield), `observability` (cloudtrail, cloudwatch, x_ray), `zone` (vpc, subnet públicas/privadas, availability_zone); `backup` entra em `storage` com papel controle; `elasticache` sai de `database` para `cache`? → **não**: permanece `database` (ameaças de dados aplicam) | Menor número de famílias que resolve as contradições apontadas; ElastiCache compartilha ameaças de dados em trânsito/repouso | n (default logado) |
| Semântica de "papel" (role) | `role` por família na KB: `workload` (default), `control` (security, observability, edge), `zone` (network zones), `external` (client) | Papel decide a fraseologia (ameaça vs. verificação) e o agrupamento no relatório | n (default logado) |
| Categoria do finding de inventário | `stride_category = "Não classificado"` e `mapped=False`; JSON mantém o campo com esse valor literal | Não inventar categoria STRIDE preserva credibilidade técnica; valor literal simples evita quebrar o schema | n (default logado) |
| Limiar de cobertura para warning | 80% (configurável via `STRIDE_MIN_COVERAGE`) | Abaixo disso o relatório vira ruído; valor inicial conservador | n (default logado) |
| Compatibilidade do JSON | Campos existentes preservados; novos campos aditivos (`role`, `instance_count`, `coverage`) | MVP sem consumidores externos; aditivo evita retrabalho nos testes atuais | n (default logado) |
| Zonas geram verificação única por zona | Subnet pública/privada → 1 verificação estrutural (SG/NACL/rotas) por zona detectada, não 1 ameaça por ícone | Review externo: marcar subnets genericamente como ID "não agrega valor técnico" | n (default logado) |

**Open questions:** none — modo assíncrono; defaults acima valem até contraordem do usuário.

---

## User Stories

### P1: Cobertura do vocabulário de classes ⭐ MVP

**User Story**: Como analista de segurança, quero que toda classe emitida pelo detector resolva para uma família STRIDE conhecida, para que o relatório não degenere em fallbacks genéricos.

**Why P1**: Causa-raiz nº 1 — 30/34 findings caíram em `unknown`.

**Acceptance Criteria**:

1. WHEN `ClassFamilyMapper.to_family` receber nome com prefixo de vendor (`aws-waf`, `Amazon RDS`, `azure_sql_database`) THEN o sistema SHALL normalizar (case, espaços, hífens, prefixos `aws_`/`amazon_`/`azure_`/`gcp_`/`google_`) e resolver a mesma família do nome base (MAP-01)
2. WHEN o vocabulário do detector for conferido contra o mapa (via `classes.txt` ou `names` dos pesos) THEN 100% das classes SHALL resolver para família ≠ `unknown` (MAP-02)
3. WHEN `stride-mvp check-map --classes <arquivo|pesos>` rodar com classes não mapeadas THEN o comando SHALL listar cada classe faltante e sair com código ≠ 0; sem faltantes → exit 0 (MAP-03)

**Independent Test**: Rodar `check-map` contra a lista de classes do dataset e contra os nomes vistos no relatório real; exit 0 e nenhum `unknown`.

---

### P1: KB role-aware para serviços gerenciados ⭐ MVP

**User Story**: Como analista, quero que a KB conheça o papel de cada família (workload, controle, zona) e tenha ameaças específicas por função, para que WAF/Shield não apareçam como "vulneráveis por superfície desconhecida".

**Why P1**: Causa-raiz nº 3 — contradições de segurança apontadas no review.

**Acceptance Criteria**:

1. WHEN a KB for carregada THEN cada família SHALL declarar `role` (`workload` | `control` | `zone` | `external`), default `workload` (KBX-01)
2. WHEN um componente de família `edge` for analisado THEN os findings SHALL cobrir Spoofing (bypass de origem — ALB deve aceitar só tráfego do CloudFront) e Denial of Service (eficácia do WAF/Shield), com contramedidas específicas de edge (KBX-02)
3. WHEN um componente de família `observability` for analisado THEN os findings SHALL cobrir Repudiation (trilha desativada/retenção insuficiente) e Tampering (logs adulteráveis), formulados como verificação do controle (KBX-03)
4. WHEN um componente com `role: control` for analisado THEN a descrição SHALL ser formulada como verificação de eficácia/configuração do controle, nunca como ameaça genérica de exposição (KBX-04)
5. WHEN uma zona de rede (subnet pública/privada, VPC) for detectada THEN o sistema SHALL emitir no máximo UMA verificação estrutural por zona (SG/NACL/rotas), sem fallback "Information Disclosure" (KBX-05)
6. WHEN famílias declaradas em `class_map.yaml` forem cruzadas com a KB THEN toda família não-`unknown` SHALL ter ao menos uma entrada na KB (teste de consistência map↔KB) (KBX-06)

**Independent Test**: Analisar detecções fake `[waf, cloudtrail, public_subnet]` e verificar que nenhum finding usa o texto de fallback nem categoria inventada.

---

### P1: Fallback semântico e agrupamento ⭐ MVP

**User Story**: Como leitor do relatório, quero que componentes não classificados apareçam como inventário (não como ameaça inventada) e que instâncias repetidas sejam agrupadas, para um relatório limpo e crível.

**Why P1**: Causas-raiz nº 2 e 4 — relatório "poluído com falsos positivos genéricos".

**Acceptance Criteria**:

1. WHEN uma classe não tiver família mapeada THEN o finding SHALL usar `stride_category = "Não classificado"`, `mapped=False`, e texto orientando inventariar o componente — nunca "Information Disclosure" (ENG-01)
2. WHEN N detecções da mesma classe existirem THEN o engine SHALL produzir UM conjunto de findings para a classe com `instance_count = N` (deduplicação), preservando a maior confiança nas detecções listadas (ENG-02)
3. WHEN o relatório for gerado THEN SHALL incluir a métrica `coverage` = detecções mapeadas / total (0–1), e o CLI SHALL emitir warning em stderr quando coverage < limiar (default 0.8, override `STRIDE_MIN_COVERAGE`) sem alterar o exit code (ENG-03)

**Independent Test**: 6 detecções `solr` sem mapeamento → 1 item de inventário com `instance_count=6`, coverage 0.0, warning no stderr, exit 0.

---

### P2: Relatório reestruturado por papel

**User Story**: Como avaliador, quero o Markdown organizado em sumário, ameaças por workload, verificações de controles e inventário, para achar rápido o que importa.

**Why P2**: Valor de leitura; depende dos P1 para ter conteúdo correto.

**Acceptance Criteria**:

1. WHEN o Markdown for renderizado THEN SHALL conter, nesta ordem: sumário (tabela componente × família × role × instâncias × categorias), "Ameaças por componente" (role workload/external), "Controles detectados — verificações" (role control), "Zonas de rede — verificações estruturais" (role zone) e "Inventário não classificado" (unknown); seções vazias são omitidas (REP-01)
2. WHEN o JSON for gerado THEN SHALL incluir `role` e `instance_count` por finding e `coverage` no topo, mantendo todos os campos atuais (REP-02)

**Independent Test**: Fixture com workload + controle + zona + unknown → 5 seções presentes; remover unknown → seção de inventário omitida.

---

### P3: Contexto posicional por contenção de bbox

**User Story**: Como analista, quero que workloads dentro de uma zona detectada herdem esse contexto (ex.: ALB em subnet pública é o padrão esperado), para reduzir apontamentos sem valor.

**Why P3**: Refinamento; exige zonas bem detectadas para valer o custo.

**Acceptance Criteria**:

1. WHEN o bbox de um workload estiver ≥80% contido no bbox de uma zona THEN o relatório SHALL anotar a zona no componente (ex.: `alb (public_subnet)`) (CTX-01)
2. WHEN um workload que não seja edge/api estiver contido em zona pública THEN o sistema SHALL adicionar verificação de exposição indevida; ALB/edge em zona pública SHALL ser anotado como padrão esperado, sem finding extra (CTX-02)

---

## Edge Cases

- WHEN os pesos/`classes.txt` não estiverem disponíveis para `check-map` THEN o comando SHALL falhar com mensagem acionável (não stacktrace)
- WHEN todas as detecções forem não mapeadas THEN coverage = 0.0, warning emitido, relatório contém apenas sumário + inventário
- WHEN não houver nenhum unknown THEN a seção de inventário SHALL ser omitida
- WHEN uma família existir no `class_map.yaml` sem entrada na KB THEN o teste de consistência (KBX-06) SHALL falhar no CI
- WHEN detecções duplicadas tiverem confidências distintas THEN o agrupamento SHALL reportar `instance_count` correto e manter as detecções individuais no JSON (`detections` inalterado)
- WHEN a KB v2 (`role`) carregar um YAML v1 sem `role` THEN o loader SHALL aplicar default `workload` (compat retroativa)
- WHEN zero detecções THEN comportamento atual preservado (nota "sem ameaças inventadas") com coverage omitido ou 1.0 — definido como **omitido** (sem denominador)

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| -------------- | ----- | ----- | ------ |
| MAP-01 | P1: Vocabulário | Tasks | Pending |
| MAP-02 | P1: Vocabulário | Tasks | Pending |
| MAP-03 | P1: Vocabulário | Tasks | Pending |
| KBX-01 | P1: KB role-aware | Tasks | Pending |
| KBX-02 | P1: KB role-aware | Tasks | Pending |
| KBX-03 | P1: KB role-aware | Tasks | Pending |
| KBX-04 | P1: KB role-aware | Tasks | Pending |
| KBX-05 | P1: KB role-aware | Tasks | Pending |
| KBX-06 | P1: KB role-aware | Tasks | Pending |
| ENG-01 | P1: Fallback/agrupamento | Tasks | Pending |
| ENG-02 | P1: Fallback/agrupamento | Tasks | Pending |
| ENG-03 | P1: Fallback/agrupamento | Tasks | Pending |
| REP-01 | P2: Relatório | Tasks | Pending |
| REP-02 | P2: Relatório | Tasks | Pending |
| CTX-01 | P3: Contexto posicional | — | Pending |
| CTX-02 | P3: Contexto posicional | — | Pending |

**Coverage:** 16 total, 14 mapeados em tasks (P1+P2), 2 P3 sem task (implementar só se sobrar orçamento) ⚠️

---

## Success Criteria

- [ ] `stride-mvp check-map` passa (exit 0) contra o vocabulário de treino
- [ ] Re-execução do diagrama AWS real: ≤10% findings fallback; WAF/Shield/KMS/CloudTrail nas seções de controle com fraseologia de verificação
- [ ] Nenhum bloco de finding duplicado para instâncias repetidas da mesma classe
- [ ] Métrica de cobertura visível no MD e JSON; warning quando < 0.8
- [ ] Suite completa verde (58+ testes atuais preservados + novos)
