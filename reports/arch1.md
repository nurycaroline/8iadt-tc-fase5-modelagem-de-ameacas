# Relatório de Modelagem de Ameaças (STRIDE)

**Imagem de origem:** `reports/arch1.png`

**Detecções:** 31
**Findings:** 59
**Cobertura de mapeamento:** 100%

## Sumário

| # | Componente | Família | Papel | Instâncias | Confiança | Categorias STRIDE |
|---|------------|---------|-------|-----------|-----------|------------------|
| 1 | aws_backup | backup | control | 1 | 1.00 | Spoofing, Tampering |
| 2 | aws_elactic_file_system(nfs)_multi-az | filesystem | workload | 1 | 0.99 | Spoofing, Tampering, Information Disclosure |
| 3 | aws_elasticache | database | workload | 1 | 0.99 | Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege |
| 4 | aws_cloud_trail | observability | control | 1 | 0.99 | Tampering, Repudiation |
| 5 | aws_public_subnet | zone | zone | 4 | 0.99 | Tampering |
| 6 | aws_application_load_balancer | api | workload | 3 | 0.99 | Spoofing, Tampering, Information Disclosure, Denial of Service, Elevation of Privilege |
| 7 | aws_cloudfront | edge | control | 1 | 0.99 | Spoofing, Tampering, Denial of Service |
| 8 | aws_rds | database | workload | 2 | 0.98 | Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege |
| 9 | sei/sip | compute | workload | 3 | 0.98 | Spoofing, Tampering, Information Disclosure, Denial of Service, Elevation of Privilege |
| 10 | aws_cloudwatch | observability | control | 1 | 0.98 | Tampering, Repudiation |
| 11 | aws_simple_email_service | email | workload | 1 | 0.98 | Spoofing, Tampering, Denial of Service |
| 12 | aws_virtual_private_cloud | zone | zone | 1 | 0.97 | Tampering |
| 13 | user | client | external | 1 | 0.97 | Spoofing, Tampering, Repudiation, Information Disclosure |
| 14 | aws_private_subnet | zone | zone | 3 | 0.95 | Tampering |
| 15 | aws_waf | edge | control | 1 | 0.95 | Spoofing, Tampering, Denial of Service |
| 16 | aws_autoscaling | scaling | control | 2 | 0.95 | Tampering, Denial of Service |
| 17 | aws_cloud | management | scope | 1 | 0.94 | Escopo |
| 18 | solr | compute | workload | 1 | 0.94 | Spoofing, Tampering, Information Disclosure, Denial of Service, Elevation of Privilege |
| 19 | aws_key_management_service | security | control | 1 | 0.93 | Spoofing, Information Disclosure, Elevation of Privilege |
| 20 | aws_region | management | scope | 1 | 0.89 | Escopo |

## Ameaças por componente

### 1. aws_elactic_file_system(nfs)_multi-az — Spoofing

- **Componente:** aws_elactic_file_system(nfs)_multi-az
- **Família:** filesystem
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Montagem não autorizada do sistema de arquivos
- **Vulnerabilidade:** EFS Mount Targets expostos a subnets/SGs indevidos
- **Contramedida:** Restringir mount targets a subnets privadas e Security Groups least-privilege
- **Mapeado na KB:** sim

### 2. aws_elactic_file_system(nfs)_multi-az — Tampering

- **Componente:** aws_elactic_file_system(nfs)_multi-az
- **Família:** filesystem
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Tampering
- **Ameaça:** Alteração indevida de arquivos via permissões POSIX fracas
- **Vulnerabilidade:** POSIX permissions/ownership permissivos no share NFS
- **Contramedida:** Revisar UID/GID e permissões POSIX; habilitar access points com políticas
- **Mapeado na KB:** sim

### 3. aws_elactic_file_system(nfs)_multi-az — Information Disclosure

- **Componente:** aws_elactic_file_system(nfs)_multi-az
- **Família:** filesystem
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Information Disclosure
- **Ameaça:** Exposição de dados em trânsito ou em repouso no filesystem
- **Vulnerabilidade:** Ausência de criptografia em trânsito (TLS) ou em repouso
- **Contramedida:** Criptografia at-rest com KMS e montagem com TLS obrigatório
- **Mapeado na KB:** sim

### 4. aws_elasticache — Spoofing

- **Componente:** aws_elasticache
- **Família:** database
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Autenticação fraca ao banco de dados
- **Vulnerabilidade:** Credenciais padrão ou compartilhadas
- **Contramedida:** IAM/roles, rotação de segredos, MFA onde aplicável
- **Mapeado na KB:** sim

### 5. aws_elasticache — Tampering

- **Componente:** aws_elasticache
- **Família:** database
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Tampering
- **Ameaça:** Alteração não autorizada de dados
- **Vulnerabilidade:** Ausência de controles de integridade / auditoria
- **Contramedida:** Controles de escrita, checksums, audit logs imutáveis
- **Mapeado na KB:** sim

### 6. aws_elasticache — Repudiation

- **Componente:** aws_elasticache
- **Família:** database
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Repudiation
- **Ameaça:** Ações sem rastreabilidade
- **Vulnerabilidade:** Logs de acesso ausentes ou incompletos
- **Contramedida:** Auditoria completa de queries e acessos privilegiados
- **Mapeado na KB:** sim

### 7. aws_elasticache — Information Disclosure

- **Componente:** aws_elasticache
- **Família:** database
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Information Disclosure
- **Ameaça:** Exposição de dados em repouso ou em trânsito
- **Vulnerabilidade:** Instância/cluster de DB sem criptografia ou exposta via Security Groups/Subnets
- **Contramedida:** Criptografia at-rest, least privilege, private endpoints
- **Mapeado na KB:** sim

### 8. aws_elasticache — Denial of Service

- **Componente:** aws_elasticache
- **Família:** database
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Denial of Service
- **Ameaça:** Indisponibilidade do banco
- **Vulnerabilidade:** Sem limites de conexão / sem réplicas
- **Contramedida:** Rate limiting, autoscaling de leituras, backups testados
- **Mapeado na KB:** sim

### 9. aws_elasticache — Elevation of Privilege

- **Componente:** aws_elasticache
- **Família:** database
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Elevation of Privilege
- **Ameaça:** Escalação de privilégios no SGBD
- **Vulnerabilidade:** Usuário da aplicação com permissões excessivas
- **Contramedida:** Princípio do menor privilégio e roles separadas
- **Mapeado na KB:** sim

### 10. aws_application_load_balancer — Spoofing

- **Componente:** aws_application_load_balancer
- **Família:** api
- **Papel:** workload
- **Instâncias:** 3
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Cliente forjado na API
- **Vulnerabilidade:** Ausência de autenticação forte
- **Contramedida:** OAuth2/OIDC, mTLS, API keys rotacionadas
- **Mapeado na KB:** sim

### 11. aws_application_load_balancer — Tampering

- **Componente:** aws_application_load_balancer
- **Família:** api
- **Papel:** workload
- **Instâncias:** 3
- **Categoria STRIDE:** Tampering
- **Ameaça:** Manipulação de payloads
- **Vulnerabilidade:** Validação de entrada insuficiente
- **Contramedida:** Schema validation, WAF, assinatura de requests
- **Mapeado na KB:** sim

### 12. aws_application_load_balancer — Information Disclosure

- **Componente:** aws_application_load_balancer
- **Família:** api
- **Papel:** workload
- **Instâncias:** 3
- **Categoria STRIDE:** Information Disclosure
- **Ameaça:** Vazamento via respostas de erro
- **Vulnerabilidade:** Stack traces e dados sensíveis em respostas
- **Contramedida:** Erros genéricos, mascaramento de PII
- **Mapeado na KB:** sim

### 13. aws_application_load_balancer — Denial of Service

- **Componente:** aws_application_load_balancer
- **Família:** api
- **Papel:** workload
- **Instâncias:** 3
- **Categoria STRIDE:** Denial of Service
- **Ameaça:** Flood na API
- **Vulnerabilidade:** Sem rate limiting
- **Contramedida:** Throttling, quotas por cliente, CDN
- **Mapeado na KB:** sim

### 14. aws_application_load_balancer — Elevation of Privilege

- **Componente:** aws_application_load_balancer
- **Família:** api
- **Papel:** workload
- **Instâncias:** 3
- **Categoria STRIDE:** Elevation of Privilege
- **Ameaça:** Bypass de autorização
- **Vulnerabilidade:** IDOR / falhas de checagem de escopo
- **Contramedida:** Autorização por recurso, testes de IDOR
- **Mapeado na KB:** sim

### 15. aws_rds — Spoofing

- **Componente:** aws_rds
- **Família:** database
- **Papel:** workload
- **Instâncias:** 2
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Autenticação fraca ao banco de dados
- **Vulnerabilidade:** Credenciais padrão ou compartilhadas
- **Contramedida:** IAM/roles, rotação de segredos, MFA onde aplicável
- **Mapeado na KB:** sim

### 16. aws_rds — Tampering

- **Componente:** aws_rds
- **Família:** database
- **Papel:** workload
- **Instâncias:** 2
- **Categoria STRIDE:** Tampering
- **Ameaça:** Alteração não autorizada de dados
- **Vulnerabilidade:** Ausência de controles de integridade / auditoria
- **Contramedida:** Controles de escrita, checksums, audit logs imutáveis
- **Mapeado na KB:** sim

### 17. aws_rds — Repudiation

- **Componente:** aws_rds
- **Família:** database
- **Papel:** workload
- **Instâncias:** 2
- **Categoria STRIDE:** Repudiation
- **Ameaça:** Ações sem rastreabilidade
- **Vulnerabilidade:** Logs de acesso ausentes ou incompletos
- **Contramedida:** Auditoria completa de queries e acessos privilegiados
- **Mapeado na KB:** sim

### 18. aws_rds — Information Disclosure

- **Componente:** aws_rds
- **Família:** database
- **Papel:** workload
- **Instâncias:** 2
- **Categoria STRIDE:** Information Disclosure
- **Ameaça:** Exposição de dados em repouso ou em trânsito
- **Vulnerabilidade:** Instância/cluster de DB sem criptografia ou exposta via Security Groups/Subnets
- **Contramedida:** Criptografia at-rest, least privilege, private endpoints
- **Mapeado na KB:** sim

### 19. aws_rds — Denial of Service

- **Componente:** aws_rds
- **Família:** database
- **Papel:** workload
- **Instâncias:** 2
- **Categoria STRIDE:** Denial of Service
- **Ameaça:** Indisponibilidade do banco
- **Vulnerabilidade:** Sem limites de conexão / sem réplicas
- **Contramedida:** Rate limiting, autoscaling de leituras, backups testados
- **Mapeado na KB:** sim

### 20. aws_rds — Elevation of Privilege

- **Componente:** aws_rds
- **Família:** database
- **Papel:** workload
- **Instâncias:** 2
- **Categoria STRIDE:** Elevation of Privilege
- **Ameaça:** Escalação de privilégios no SGBD
- **Vulnerabilidade:** Usuário da aplicação com permissões excessivas
- **Contramedida:** Princípio do menor privilégio e roles separadas
- **Mapeado na KB:** sim

### 21. sei/sip — Spoofing

- **Componente:** sei/sip
- **Família:** compute
- **Papel:** workload
- **Instâncias:** 3
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Impersonação de instância ou função
- **Vulnerabilidade:** Metadados de instância expostos / identidade fraca
- **Contramedida:** IMDSv2, identities de workload, segmentação
- **Mapeado na KB:** sim

### 22. sei/sip — Tampering

- **Componente:** sei/sip
- **Família:** compute
- **Papel:** workload
- **Instâncias:** 3
- **Categoria STRIDE:** Tampering
- **Ameaça:** Código ou imagem adulterados
- **Vulnerabilidade:** Imagens sem assinatura / supply chain frágil
- **Contramedida:** Assinatura de imagens, SBOM, registries privados
- **Mapeado na KB:** sim

### 23. sei/sip — Information Disclosure

- **Componente:** sei/sip
- **Família:** compute
- **Papel:** workload
- **Instâncias:** 3
- **Categoria STRIDE:** Information Disclosure
- **Ameaça:** Vazamento de segredos em runtime
- **Vulnerabilidade:** Variáveis de ambiente com secrets em claro
- **Contramedida:** Secrets manager, volumes criptografados
- **Mapeado na KB:** sim

### 24. sei/sip — Denial of Service

- **Componente:** sei/sip
- **Família:** compute
- **Papel:** workload
- **Instâncias:** 3
- **Categoria STRIDE:** Denial of Service
- **Ameaça:** Esgotamento de CPU/memória
- **Vulnerabilidade:** Sem quotas ou autoscaling
- **Contramedida:** Quotas, HPA, circuit breakers
- **Mapeado na KB:** sim

### 25. sei/sip — Elevation of Privilege

- **Componente:** sei/sip
- **Família:** compute
- **Papel:** workload
- **Instâncias:** 3
- **Categoria STRIDE:** Elevation of Privilege
- **Ameaça:** Escape de container / host
- **Vulnerabilidade:** Containers privilegiados
- **Contramedida:** Pod security, non-root, seccomp
- **Mapeado na KB:** sim

### 26. aws_simple_email_service — Spoofing

- **Componente:** aws_simple_email_service
- **Família:** email
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Envio de e-mails em nome do domínio sem autenticação
- **Vulnerabilidade:** Domínio sem validação adequada de remetente
- **Contramedida:** Configurar SPF, DKIM e DMARC estritos no domínio verificado do SES
- **Mapeado na KB:** sim

### 27. aws_simple_email_service — Tampering

- **Componente:** aws_simple_email_service
- **Família:** email
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Tampering
- **Ameaça:** Conteúdo de e-mail adulterado ou templates comprometidos
- **Vulnerabilidade:** Templates/identidades SES editáveis sem revisão
- **Contramedida:** Controlar identidades verificadas via IAM least-privilege e revisar templates
- **Mapeado na KB:** sim

### 28. aws_simple_email_service — Denial of Service

- **Componente:** aws_simple_email_service
- **Família:** email
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Denial of Service
- **Ameaça:** Abuso de cotas de envio / reputação
- **Vulnerabilidade:** Sem limites de taxa ou monitoramento de bounce/complaint
- **Contramedida:** Configurar limites de envio, alarms de reputação e sandbox/produção controlados
- **Mapeado na KB:** sim

### 29. solr — Spoofing

- **Componente:** solr
- **Família:** compute
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Impersonação de instância ou função
- **Vulnerabilidade:** Metadados de instância expostos / identidade fraca
- **Contramedida:** IMDSv2, identities de workload, segmentação
- **Mapeado na KB:** sim

### 30. solr — Tampering

- **Componente:** solr
- **Família:** compute
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Tampering
- **Ameaça:** Código ou imagem adulterados
- **Vulnerabilidade:** Imagens sem assinatura / supply chain frágil
- **Contramedida:** Assinatura de imagens, SBOM, registries privados
- **Mapeado na KB:** sim

### 31. solr — Information Disclosure

- **Componente:** solr
- **Família:** compute
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Information Disclosure
- **Ameaça:** Vazamento de segredos em runtime
- **Vulnerabilidade:** Variáveis de ambiente com secrets em claro
- **Contramedida:** Secrets manager, volumes criptografados
- **Mapeado na KB:** sim

### 32. solr — Denial of Service

- **Componente:** solr
- **Família:** compute
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Denial of Service
- **Ameaça:** Esgotamento de CPU/memória
- **Vulnerabilidade:** Sem quotas ou autoscaling
- **Contramedida:** Quotas, HPA, circuit breakers
- **Mapeado na KB:** sim

### 33. solr — Elevation of Privilege

- **Componente:** solr
- **Família:** compute
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Elevation of Privilege
- **Ameaça:** Escape de container / host
- **Vulnerabilidade:** Containers privilegiados
- **Contramedida:** Pod security, non-root, seccomp
- **Mapeado na KB:** sim

### 34. user — Spoofing

- **Componente:** user
- **Família:** client
- **Papel:** external
- **Instâncias:** 1
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Usuário forjado no cliente
- **Vulnerabilidade:** Sessões previsíveis / sem MFA
- **Contramedida:** MFA, cookies seguros, binding de sessão
- **Mapeado na KB:** sim

### 35. user — Tampering

- **Componente:** user
- **Família:** client
- **Papel:** external
- **Instâncias:** 1
- **Categoria STRIDE:** Tampering
- **Ameaça:** Manipulação do cliente
- **Vulnerabilidade:** Lógica sensível só no front-end
- **Contramedida:** Validação server-side, attested clients
- **Mapeado na KB:** sim

### 36. user — Repudiation

- **Componente:** user
- **Família:** client
- **Papel:** external
- **Instâncias:** 1
- **Categoria STRIDE:** Repudiation
- **Ameaça:** Ações do usuário sem prova
- **Vulnerabilidade:** Sem trilha de auditoria no cliente→servidor
- **Contramedida:** Logs de autenticação e ações críticas
- **Mapeado na KB:** sim

### 37. user — Information Disclosure

- **Componente:** user
- **Família:** client
- **Papel:** external
- **Instâncias:** 1
- **Categoria STRIDE:** Information Disclosure
- **Ameaça:** Dados sensíveis no dispositivo
- **Vulnerabilidade:** Cache/localStorage com PII
- **Contramedida:** Minimizar dados locais, criptografia de storage
- **Mapeado na KB:** sim
## Controles detectados — verificações

### 1. aws_backup — Spoofing

- **Componente:** aws_backup
- **Família:** backup
- **Papel:** control
- **Instâncias:** 1
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Acesso indevido ao vault de backup
- **Vulnerabilidade:** Políticas de acesso ao Backup Vault excessivamente amplas
- **Contramedida:** Restringir IAM ao vault, Vault Access Policies e auditoria de quem restaura
- **Mapeado na KB:** sim

### 2. aws_backup — Tampering

- **Componente:** aws_backup
- **Família:** backup
- **Papel:** control
- **Instâncias:** 1
- **Categoria STRIDE:** Tampering
- **Ameaça:** Exclusão ou alteração de backups protegidos
- **Vulnerabilidade:** Ausência de Vault Lock / imutabilidade; cross-account backup não controlado
- **Contramedida:** Habilitar Vault Lock (compliance mode), bloquear cross-account não autorizado e alertar exclusões
- **Mapeado na KB:** sim

### 3. aws_cloud_trail — Tampering

- **Componente:** aws_cloud_trail
- **Família:** observability
- **Papel:** control
- **Instâncias:** 1
- **Categoria STRIDE:** Tampering
- **Ameaça:** Logs/métricas adulteráveis
- **Vulnerabilidade:** Log group sem proteção contra exclusão/alteração; sem alertas de mute
- **Contramedida:** Lock de exclusão de log groups, alarmes do CloudWatch para 'mute' e alterações de retenção, exportação imutável
- **Mapeado na KB:** sim

### 4. aws_cloud_trail — Repudiation

- **Componente:** aws_cloud_trail
- **Família:** observability
- **Papel:** control
- **Instâncias:** 1
- **Categoria STRIDE:** Repudiation
- **Ameaça:** Trilha de auditoria desativada ou com retenção insuficiente
- **Vulnerabilidade:** CloudTrail em região única, sem eventos de dados, ou retenção curta; logs sem proteção
- **Contramedida:** CloudTrail multi-região com eventos de dados, log file integrity validation, retenção ≥ 1 ano e alertas de desativação
- **Mapeado na KB:** sim

### 5. aws_cloudfront — Spoofing

- **Componente:** aws_cloudfront
- **Família:** edge
- **Papel:** control
- **Instâncias:** 1
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Bypass de origem — requisições chegam ao ALB sem passar pelo CloudFront
- **Vulnerabilidade:** ALB/origem aceita tráfego de qualquer origem; ausência de cabeçalho customizado ou restrição por VPC/SG
- **Contramedida:** Restringir a origem: SG do ALB liberando só os prefixos do CloudFront, cabeçalho customizado de origem ou Origin Access Control
- **Mapeado na KB:** sim

### 6. aws_cloudfront — Tampering

- **Componente:** aws_cloudfront
- **Família:** edge
- **Papel:** control
- **Instâncias:** 1
- **Categoria STRIDE:** Tampering
- **Ameaça:** Manipulação de regras do WAF/Shield
- **Vulnerabilidade:** Regras WAF versionadas sem aprovação; permissões amplas de edição
- **Contramedida:** WAF em IaC/terraform, revisão obrigatória, change management e alertas de alteração
- **Mapeado na KB:** sim

### 7. aws_cloudfront — Denial of Service

- **Componente:** aws_cloudfront
- **Família:** edge
- **Papel:** control
- **Instâncias:** 1
- **Categoria STRIDE:** Denial of Service
- **Ameaça:** Ataques volumétricos/l7 não mitigados na borda
- **Vulnerabilidade:** WAF/Shield desabilitados ou com regras em modo de contagem; rate limit ausente
- **Contramedida:** Habilitar AWS Shield Advanced/WAF em modo de bloqueio, rate limiting por IP/URI e monitoramento de eficácia
- **Mapeado na KB:** sim

### 8. aws_cloudwatch — Tampering

- **Componente:** aws_cloudwatch
- **Família:** observability
- **Papel:** control
- **Instâncias:** 1
- **Categoria STRIDE:** Tampering
- **Ameaça:** Logs/métricas adulteráveis
- **Vulnerabilidade:** Log group sem proteção contra exclusão/alteração; sem alertas de mute
- **Contramedida:** Lock de exclusão de log groups, alarmes do CloudWatch para 'mute' e alterações de retenção, exportação imutável
- **Mapeado na KB:** sim

### 9. aws_cloudwatch — Repudiation

- **Componente:** aws_cloudwatch
- **Família:** observability
- **Papel:** control
- **Instâncias:** 1
- **Categoria STRIDE:** Repudiation
- **Ameaça:** Trilha de auditoria desativada ou com retenção insuficiente
- **Vulnerabilidade:** CloudTrail em região única, sem eventos de dados, ou retenção curta; logs sem proteção
- **Contramedida:** CloudTrail multi-região com eventos de dados, log file integrity validation, retenção ≥ 1 ano e alertas de desativação
- **Mapeado na KB:** sim

### 10. aws_waf — Spoofing

- **Componente:** aws_waf
- **Família:** edge
- **Papel:** control
- **Instâncias:** 1
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Bypass de origem — requisições chegam ao ALB sem passar pelo CloudFront
- **Vulnerabilidade:** ALB/origem aceita tráfego de qualquer origem; ausência de cabeçalho customizado ou restrição por VPC/SG
- **Contramedida:** Restringir a origem: SG do ALB liberando só os prefixos do CloudFront, cabeçalho customizado de origem ou Origin Access Control
- **Mapeado na KB:** sim

### 11. aws_waf — Tampering

- **Componente:** aws_waf
- **Família:** edge
- **Papel:** control
- **Instâncias:** 1
- **Categoria STRIDE:** Tampering
- **Ameaça:** Manipulação de regras do WAF/Shield
- **Vulnerabilidade:** Regras WAF versionadas sem aprovação; permissões amplas de edição
- **Contramedida:** WAF em IaC/terraform, revisão obrigatória, change management e alertas de alteração
- **Mapeado na KB:** sim

### 12. aws_waf — Denial of Service

- **Componente:** aws_waf
- **Família:** edge
- **Papel:** control
- **Instâncias:** 1
- **Categoria STRIDE:** Denial of Service
- **Ameaça:** Ataques volumétricos/l7 não mitigados na borda
- **Vulnerabilidade:** WAF/Shield desabilitados ou com regras em modo de contagem; rate limit ausente
- **Contramedida:** Habilitar AWS Shield Advanced/WAF em modo de bloqueio, rate limiting por IP/URI e monitoramento de eficácia
- **Mapeado na KB:** sim

### 13. aws_autoscaling — Tampering

- **Componente:** aws_autoscaling
- **Família:** scaling
- **Papel:** control
- **Instâncias:** 2
- **Categoria STRIDE:** Tampering
- **Ameaça:** Manipulação de políticas de Auto Scaling
- **Vulnerabilidade:** Permissões amplas para alterar desired/min/max capacity
- **Contramedida:** Restringir IAM de UpdateAutoScalingGroup, mudanças via IaC com revisão
- **Mapeado na KB:** sim

### 14. aws_autoscaling — Denial of Service

- **Componente:** aws_autoscaling
- **Família:** scaling
- **Papel:** control
- **Instâncias:** 2
- **Categoria STRIDE:** Denial of Service
- **Ameaça:** DoS financeiro ou exaustão por escalonamento abusivo
- **Vulnerabilidade:** Limites de capacidade ausentes ou max capacity excessivo
- **Contramedida:** Definir max capacity, budgets/alerts de custo e revisar políticas de scaling
- **Mapeado na KB:** sim

### 15. aws_key_management_service — Spoofing

- **Componente:** aws_key_management_service
- **Família:** security
- **Papel:** control
- **Instâncias:** 1
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Uso indevido de identidades
- **Vulnerabilidade:** Chaves de longa duração
- **Contramedida:** Credenciais de curta duração, rotação
- **Mapeado na KB:** sim

### 16. aws_key_management_service — Information Disclosure

- **Componente:** aws_key_management_service
- **Família:** security
- **Papel:** control
- **Instâncias:** 1
- **Categoria STRIDE:** Information Disclosure
- **Ameaça:** Segredos expostos
- **Vulnerabilidade:** Secrets em repositório ou logs
- **Contramedida:** Vault/KMS, scanning de secrets
- **Mapeado na KB:** sim

### 17. aws_key_management_service — Elevation of Privilege

- **Componente:** aws_key_management_service
- **Família:** security
- **Papel:** control
- **Instâncias:** 1
- **Categoria STRIDE:** Elevation of Privilege
- **Ameaça:** Políticas IAM excessivas
- **Vulnerabilidade:** Wildcards em actions/resources
- **Contramedida:** Least privilege, access analyzer
- **Mapeado na KB:** sim
## Zonas de rede — verificações estruturais

### 1. aws_public_subnet — Tampering

- **Componente:** aws_public_subnet
- **Família:** zone
- **Papel:** zone
- **Instâncias:** 4
- **Categoria STRIDE:** Tampering
- **Ameaça:** Configuração de zona expõe workloads indevidamente
- **Vulnerabilidade:** Security Groups/NACLs permissivos; rotas públicas para recursos privados; ausência de isolamento
- **Contramedida:** Revisar SG/NACLs (least privilege), rotas, e garantir que workloads não-edge fiquem em subnets privadas
- **Mapeado na KB:** sim

### 2. aws_virtual_private_cloud — Tampering

- **Componente:** aws_virtual_private_cloud
- **Família:** zone
- **Papel:** zone
- **Instâncias:** 1
- **Categoria STRIDE:** Tampering
- **Ameaça:** Configuração de zona expõe workloads indevidamente
- **Vulnerabilidade:** Security Groups/NACLs permissivos; rotas públicas para recursos privados; ausência de isolamento
- **Contramedida:** Revisar SG/NACLs (least privilege), rotas, e garantir que workloads não-edge fiquem em subnets privadas
- **Mapeado na KB:** sim

### 3. aws_private_subnet — Tampering

- **Componente:** aws_private_subnet
- **Família:** zone
- **Papel:** zone
- **Instâncias:** 3
- **Categoria STRIDE:** Tampering
- **Ameaça:** Configuração de zona expõe workloads indevidamente
- **Vulnerabilidade:** Security Groups/NACLs permissivos; rotas públicas para recursos privados; ausência de isolamento
- **Contramedida:** Revisar SG/NACLs (least privilege), rotas, e garantir que workloads não-edge fiquem em subnets privadas
- **Mapeado na KB:** sim