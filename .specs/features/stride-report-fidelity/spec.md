# STRIDE Report Fidelity — Specification

## Problem Statement

Review externo (Gemini) dos relatórios reais `reports/arch1.md` (AWS) e `reports/arch2.md` (Azure) apontou a segunda rodada de problemas de credibilidade. A rodada 1 (`stride-report-quality`) eliminou fallbacks genéricos e tratou roles; agora o problema é **granularidade semântica** e **qualidade das detecções**:

**Arch1 (AWS) — semântica errada por família larga demais:**

1. **EFS e AWS Backup** recebem os textos de S3 ("políticas permissivas em bucket", "Block public access", "MFA delete") porque `efs`, `aws_elactic_file_system(nfs)_multi-az`, `backup` e `aws_backup` estão na família `storage`, cuja KB é escrita para object storage. EFS é NFS (mount targets, POSIX, criptografia em trânsito); Backup é gestão de vaults (políticas de vault, cross-account, vault lock).
2. **SES** recebe textos de SQS/SNS ("filas sem autenticação", "enchimento de fila / sem DLQ") porque `aws_simple_email_service` está em `messaging`. A ameaça real de SES é envio de e-mail em nome do domínio sem SPF/DKIM/DMARC.
3. **Auto Scaling** (`aws_autoscaling`, `auto_scaling*`) está em `compute` e replica "escape de container / IMDSv2". Auto Scaling não executa código; a ameaça é manipulação de políticas de escalonamento (DoS financeiro/exaustão).
4. **`aws_cloud` e `aws_region`** recebem ameaças de workload/zona ("Tampering" genérico). São fronteiras/escopos lógicos — classificá-los como ameaça é conceitualmente fraco.

**Arch2 (Azure) — semântica errada + detecções duplicadas:**

5. **`resource_group`/`azure_resource_groups`** estão em `compute` e recebem escape de container/Pod Security. Resource Group é agrupador lógico de gerenciamento (control plane), não infraestrutura executável.
6. **`logic_apps`/`azure_logic_apps`, `sass_services`, `azure_services`** estão em `compute` e recebem seccomp/IMDSv2/HPA. São serviços gerenciados/integração: as ameaças reais são vazamento de tokens de conectores, conectores inseguros, autorização de API, injeção de payload repassado sem validação e IAM/RBAC.
7. **Contagem inflada**: o relatório lista 2× `microsoft_entra`, 2× `resource_group`, 2× `api` quando o diagrama tem 1 de cada. O detector (treinado numa base Kaggle com poucos diagramas Azure similares) emite caixas duplicadas/sobrepostas da mesma classe; o engine conta todas (`instance_count = len(group)`), sem deduplicação espacial.
8. **Sem transparência de confiança**: o relatório não expõe a confiança das detecções, então o leitor não distingue detecções sólidas de prováveis falsos positivos.

**Causas-raiz no código:** `data/class_map.yaml` (alocações erradas de família), `data/kb/threats.yaml` (faltam famílias `filesystem`, `backup`, `email`, `scaling`, `integration`, `dependency` e o papel `scope`), `src/stride_mvp/stride/engine.py` (sem papel "escopo sem findings"), pipeline de detecção (sem dedupe espacial por IoU nem flag de baixa confiança).

## Goals

- [ ] Zero termos de tecnologia errada nos relatórios: EFS/Backup sem vocabulário S3; SES sem vocabulário de filas; Logic Apps/SaaS/Resource Group sem vocabulário de containers (verificado por testes de regressão com termos proibidos)
- [ ] Agrupadores lógicos (`resource_group`, `aws_cloud`, `aws_region`) nunca recebem findings STRIDE — aparecem apenas no sumário como escopo
- [ ] Detecções sobrepostas da mesma classe são deduplicadas (IoU); `instance_count` reflete o diagrama
- [ ] Relatório expõe confiança por componente e sinaliza detecções de baixa confiança como possíveis falsos positivos

## Out of Scope

| Feature | Reason |
| ------- | ------ |
| Retreino/fine-tune do YOLO com mais dados Azure | Causa-raiz da duplicação é escassez de exemplos Azure na base Kaggle; exige anotação de novos diagramas + treino (GPU). Feature separada recomendada (`detector-azure-robustness`); aqui mitigamos com dedupe + transparência de confiança |
| Realocar labels não citados no review (`azure_devops`, `azure_machine_learning`, `azure_databricks`…) | Sem evidência de dano em relatório real; evitar churn de KB sem review. Ficam em `compute` até próxima auditoria |
| Geração de ameaças via LLM / RAG | AD-001 mantém pipeline determinístico regras + KB |
| Detecção de fluxos/setas | Já excluído nas specs anteriores |
| Dedupe entre classes diferentes | Zonas legitimamente contêm workloads (bbox aninhado é esperado); dedupe é sempre intra-classe |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --------------------- | -------------- | --------- | ---------- |
| Novas famílias | `filesystem` (efs…), `backup` (aws_backup…), `email` (ses), `scaling` (auto_scaling…), `integration` (logic_apps…), `dependency` (sass_services, azure_services), `management` (resource_group, aws_cloud, aws_region) | Menor conjunto que resolve todos os apontamentos do review sem explodir a KB | n (default logado) |
| Papel das novas famílias | `filesystem`/`email`/`integration` = workload; `backup`/`scaling` = control (verificações); `dependency` = external; `management` = novo papel `scope` | Backup/AutoScaling são serviços de gestão (verificar config); SaaS externo é dependência de terceiro; RG/região são escopos | n (default logado) |
| Semântica do papel `scope` | Zero findings STRIDE; componente aparece no sumário com role `scope`; conta como **mapeado** na coverage | Review: classificar região/RG como ameaça "não agrega valor técnico"; coverage não deve cair por reconhecer um escopo | n (default logado) |
| `azure_vm_scale_sets` | Permanece em `compute` | Diferente do ASG (ícone de política), VM Scale Set representa as VMs que executam código | n (default logado) |
| Onde vive o dedupe | Função pura no pipeline (pós-detecção, pré-engine), aplicada a qualquer detector (YOLO ou Scripted) | Testável sem pesos; CI usa ScriptedDetector | n (default logado) |
| Critério de duplicata | Mesma classe (normalizada) e IoU ≥ 0.5 **ou** contenção ≥ 0.8 de uma caixa na outra; mantém a de maior confiança | Cobre caixas quase idênticas e caixa-dentro-de-caixa da mesma classe | n (default logado) |
| Configuração do dedupe | `STRIDE_DEDUPE_IOU` (default 0.5); valor 0 desativa | Consistente com `STRIDE_MIN_COVERAGE`; escape hatch p/ depurar detector | n (default logado) |
| Limiar de baixa confiança | `STRIDE_LOW_CONF` (default 0.50); marca ⚠ no sumário + nota explicando possível falso positivo por base de treino limitada; valor 0 desativa | Responde honestamente à "alucinação" do arch2 sem esconder detecções | n (default logado) |
| JSON | Aditivo: `max_confidence` e `low_confidence` por finding/grupo; campos atuais preservados | Mesma política da rodada 1 (sem consumidores externos) | n (default logado) |
| Consistência map↔KB (KBX-06) | Famílias com role `scope` são isentas de entradas na KB; todas as demais novas famílias exigem ≥1 entrada | `scope` por definição não tem ameaças | n (default logado) |
| Textos exatos das novas entradas de KB | Escritos na implementação; as ACs fixam os **termos obrigatórios** (ex.: SPF/DKIM/DMARC) e **proibidos** (ex.: "bucket" p/ EFS) | Spec define resultado verificável, não prosa final | n (default logado) |

**Open questions:** none — modo assíncrono; defaults acima valem até contraordem do usuário.

---

## User Stories

### P1: Semântica AWS correta (EFS, Backup, SES, Auto Scaling, escopos) ⭐ MVP

**User Story**: Como analista de segurança, quero que cada serviço AWS receba ameaças da sua tecnologia real, para que o relatório arch1 passe em auditoria sem falsos positivos de "copiar e colar".

**Why P1**: Apontamentos 1–4 do review do arch1 — erros "graves" nas palavras do reviewer.

**Acceptance Criteria**:

1. WHEN um componente EFS (`efs`, `aws_elactic_file_system(nfs)_multi-az`) for analisado THEN os findings SHALL vir da família `filesystem`, cobrindo mount targets não autorizados, criptografia em trânsito/repouso e permissões POSIX — e SHALL NOT conter os termos "bucket", "Block public access" ou "MFA delete" (SEM-01)
2. WHEN um componente AWS Backup (`backup`, `aws_backup`) for analisado THEN os findings SHALL vir da família `backup` com role `control`, formulados como verificações de política de acesso ao vault, cross-account backup e imutabilidade (vault lock) (SEM-02)
3. WHEN um componente SES (`aws_simple_email_service`, `ses`) for analisado THEN os findings SHALL vir da família `email`, com Spoofing de domínio de e-mail e contramedida citando SPF, DKIM e DMARC — e SHALL NOT conter os termos "fila" ou "DLQ" (SEM-03)
4. WHEN um componente de Auto Scaling (`auto_scaling`, `auto_scaling_group`, `aws_autoscaling`, `aws_amazon_ec2_auto_scaling`) for analisado THEN os findings SHALL vir da família `scaling` com role `control`, cobrindo manipulação de políticas de escalonamento (DoS financeiro/exaustão) — e SHALL NOT conter "escape de container" ou "IMDSv2" (SEM-04)
5. WHEN `aws_cloud` ou `aws_region` forem detectados THEN o sistema SHALL emitir zero findings STRIDE para eles, listá-los no sumário com role `scope` e contá-los como mapeados na coverage (SEM-05)
6. WHEN o teste de consistência map↔KB rodar THEN toda família nova não-`scope` SHALL ter ≥1 entrada na KB e famílias `scope` SHALL ser isentas (SEM-06)

**Independent Test**: Detecções fake `[aws_efs, aws_backup, ses, aws_autoscaling, aws_region]` → nenhum termo proibido, Backup/Scaling nas seções de controle, região só no sumário.

---

### P1: Semântica Azure correta (Resource Group, Logic Apps, SaaS) ⭐ MVP

**User Story**: Como analista, quero que serviços gerenciados Azure recebam ameaças de integração/IAM (não de containers), para que o relatório arch2 faça sentido técnico para a arquitetura Azure.

**Why P1**: Apontamentos 5–6 do review do arch2 — "erros conceituais graves".

**Acceptance Criteria**:

1. WHEN `resource_group`/`azure_resource_groups` for detectado THEN o sistema SHALL emitir zero findings STRIDE, listando-o no sumário com role `scope` (mesmo mecanismo de SEM-05) (AZR-01)
2. WHEN um Logic Apps (`logic_apps`, `azure_logic_apps`) for analisado THEN os findings SHALL vir da família `integration`, cobrindo vazamento de tokens/credenciais de conectores, injeção de payload repassado sem validação de schema e autorização de API, com contramedidas citando Managed Identity e RBAC — e SHALL NOT conter "container", "seccomp", "IMDSv2" ou "HPA" (AZR-02)
3. WHEN `sass_services` ou `azure_services` for analisado THEN os findings SHALL vir da família `dependency` com role `external`, cobrindo confiança em terceiro (vazamento de tokens de integração, escopos de consentimento excessivos, conectores inseguros) — sem vocabulário de containers (AZR-03)

**Independent Test**: Detecções fake `[resource_group, logic_apps, sass_services, azure_services]` → zero findings para RG; demais sem nenhum termo proibido de container.

---

### P1: Deduplicação espacial de detecções ⭐ MVP

**User Story**: Como leitor do relatório, quero que caixas duplicadas da mesma classe (artefato do detector) sejam colapsadas, para que `instance_count` reflita o diagrama real.

**Why P1**: Apontamento 7 do arch2 (2× entra/rg/api vs 1 no diagrama); base de treino com poucos exemplos Azure produz caixas sobrepostas.

**Acceptance Criteria**:

1. WHEN duas ou mais detecções da mesma classe (nome normalizado) tiverem IoU ≥ limiar OU uma caixa estiver ≥80% contida na outra THEN o pipeline SHALL manter apenas a detecção de maior confiança antes da análise STRIDE (DED-01)
2. WHEN o limiar for configurado via `STRIDE_DEDUPE_IOU` THEN o sistema SHALL usá-lo (default 0.5); valor 0 SHALL desativar o dedupe preservando o comportamento atual (DED-02)
3. WHEN detecções da mesma classe forem espacialmente disjuntas (IoU < limiar, sem contenção) THEN ambas SHALL ser preservadas com `instance_count` correto — dedupe nunca remove instâncias legítimas (DED-03)
4. WHEN detecções de classes diferentes se sobrepuserem (ex.: workload dentro de zona) THEN nenhuma SHALL ser removida (DED-04)

**Independent Test**: 2 caixas `microsoft_entra` com IoU 0.7 + 1 caixa `api` disjunta → relatório com `microsoft_entra` instance_count=1 e `api` instance_count=1.

---

### P2: Transparência de confiança no relatório

**User Story**: Como avaliador, quero ver a confiança de cada detecção e um aviso de possível falso positivo quando ela for baixa, para calibrar minha leitura em diagramas fora da distribuição de treino (caso Azure).

**Why P2**: Apontamento 8; mitigação honesta da "alucinação" enquanto o retreino não acontece. Depende do dedupe para os números fazerem sentido.

**Acceptance Criteria**:

1. WHEN o sumário Markdown for renderizado THEN SHALL incluir coluna de confiança (máxima do grupo, 2 casas decimais) por componente (CONF-01)
2. WHEN a confiança máxima de um grupo for < `STRIDE_LOW_CONF` (default 0.50) THEN o componente SHALL ser marcado no sumário (⚠) e o relatório SHALL conter nota explicando que detecções de baixa confiança podem ser falsos positivos do detector; valor 0 SHALL desativar a marcação (CONF-02)
3. WHEN o JSON for gerado THEN SHALL incluir `max_confidence` e `low_confidence` por grupo de findings, mantendo todos os campos atuais (CONF-03)

**Independent Test**: Grupo com confiança 0.32 → linha marcada + nota presente; com 0.9 → sem marca; `STRIDE_LOW_CONF=0` → sem marcas.

---

### P2: Regressão dos cenários reais (arch1/arch2)

**User Story**: Como mantenedor, quero testes e2e que reproduzam os componentes dos relatórios reais e proíbam os termos errados, para que os erros apontados pelo review nunca regridam.

**Why P2**: Trava de qualidade; consolida SEM/AZR/DED em cenários fiéis aos relatórios auditados.

**Acceptance Criteria**:

1. WHEN o cenário AWS (detecções scripted replicando arch1: sei/sip, rds, alb, efs, backup, ses, autoscaling, subnets, vpc, region…) rodar no pipeline THEN o Markdown SHALL passar nas asserções de termos proibidos/obrigatórios de SEM-01..05 (REG-01)
2. WHEN o cenário Azure (replicando arch2: microsoft_entra duplicado sobreposto, resource_group, api, logic_apps, sass_services, azure_services…) rodar THEN o Markdown SHALL mostrar contagens deduplicadas, zero findings para resource_group e nenhum vocabulário de container nos serviços gerenciados (REG-02)

**Independent Test**: `pytest tests/integration -k fidelity` verde; quebra se alguém devolver `efs` para `storage` ou remover o dedupe.

---

## Edge Cases

- WHEN o dedupe remover uma detecção THEN a lista `detections` do JSON SHALL conter apenas as detecções sobreviventes (o relatório descreve o que foi considerado), e o número de removidas SHALL aparecer em `notes`
- WHEN todas as detecções de um relatório forem de famílias `scope` THEN coverage = 1.0 e o relatório contém apenas o sumário (sem seções de ameaças)
- WHEN a KB v2 atual (sem role `scope`) for carregada THEN o loader SHALL manter compat (famílias sem role declarado → `workload`)
- WHEN `STRIDE_DEDUPE_IOU` ou `STRIDE_LOW_CONF` tiverem valores inválidos (não numéricos, fora de [0,1]) THEN o CLI SHALL falhar com mensagem acionável, não stacktrace
- WHEN três ou mais caixas da mesma classe se sobrepuserem em cadeia (A~B, B~C) THEN o dedupe SHALL convergir para uma única detecção (greedy por confiança decrescente)
- WHEN `check-map` rodar após a realocação THEN 100% do vocabulário existente SHALL continuar resolvendo para família ≠ `unknown` (nenhum label órfão criado pela mudança)

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| -------------- | ----- | ----- | ------ |
| SEM-01 | P1: Semântica AWS | Design | Pending |
| SEM-02 | P1: Semântica AWS | Design | Pending |
| SEM-03 | P1: Semântica AWS | Design | Pending |
| SEM-04 | P1: Semântica AWS | Design | Pending |
| SEM-05 | P1: Semântica AWS | Design | Pending |
| SEM-06 | P1: Semântica AWS | Design | Pending |
| AZR-01 | P1: Semântica Azure | Design | Pending |
| AZR-02 | P1: Semântica Azure | Design | Pending |
| AZR-03 | P1: Semântica Azure | Design | Pending |
| DED-01 | P1: Dedupe espacial | Design | Pending |
| DED-02 | P1: Dedupe espacial | Design | Pending |
| DED-03 | P1: Dedupe espacial | Design | Pending |
| DED-04 | P1: Dedupe espacial | Design | Pending |
| CONF-01 | P2: Confiança | Design | Pending |
| CONF-02 | P2: Confiança | Design | Pending |
| CONF-03 | P2: Confiança | Design | Pending |
| REG-01 | P2: Regressão | Design | Pending |
| REG-02 | P2: Regressão | Design | Pending |

**Coverage:** 18 total, 0 mapeados em tasks (aguardando confirmação da spec → Design → Tasks) ⚠️

---

## Success Criteria

- [ ] Re-execução do arch1: blocos de EFS, Backup, SES e Auto Scaling com vocabulário da tecnologia correta; `aws_cloud`/`aws_region` sem findings
- [ ] Re-execução do arch2: `resource_group` sem findings; Logic Apps/SaaS com ameaças de integração/IAM; contagens iguais ao diagrama após dedupe; componentes de baixa confiança marcados
- [ ] `stride-mvp check-map` exit 0 (nenhum label órfão após realocação)
- [ ] Suite completa verde (109 testes atuais preservados + novos de SEM/AZR/DED/CONF/REG)
