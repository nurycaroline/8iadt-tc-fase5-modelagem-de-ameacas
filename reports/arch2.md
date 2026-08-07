# Relatório de Modelagem de Ameaças (STRIDE)

**Imagem de origem:** `reports/arch2.png`

**Detecções:** 12
**Findings:** 27
**Cobertura de mapeamento:** 100%

## Sumário

| # | Componente | Família | Papel | Instâncias | Confiança | Categorias STRIDE |
|---|------------|---------|-------|-----------|-----------|------------------|
| 1 | sass_services | dependency | external | 1 | 1.00 | Spoofing, Tampering, Information Disclosure |
| 2 | api | api | workload | 2 | 0.99 | Spoofing, Tampering, Information Disclosure, Denial of Service, Elevation of Privilege |
| 3 | azure_services | azure_platform | workload | 2 | 0.99 | Spoofing, Information Disclosure, Elevation of Privilege |
| 4 | user | client | external | 1 | 0.99 | Spoofing, Tampering, Repudiation, Information Disclosure |
| 5 | developer_portal | api | workload | 1 | 0.99 | Spoofing, Tampering, Information Disclosure, Denial of Service, Elevation of Privilege |
| 6 | resource_group | management | scope | 2 | 0.99 | Escopo |
| 7 | microsoft_entra | security | control | 2 | 0.98 | Spoofing, Information Disclosure, Elevation of Privilege |
| 8 | logic_apps | integration | workload | 1 | 0.97 | Spoofing, Tampering, Elevation of Privilege |

## Ameaças por componente

### 1. api — Spoofing

- **Componente:** api
- **Família:** api
- **Papel:** workload
- **Instâncias:** 2
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Cliente forjado na API
- **Vulnerabilidade:** Ausência de autenticação forte
- **Contramedida:** OAuth2/OIDC, mTLS, API keys rotacionadas
- **Mapeado na KB:** sim

### 2. api — Tampering

- **Componente:** api
- **Família:** api
- **Papel:** workload
- **Instâncias:** 2
- **Categoria STRIDE:** Tampering
- **Ameaça:** Manipulação de payloads
- **Vulnerabilidade:** Validação de entrada insuficiente
- **Contramedida:** Schema validation, WAF, assinatura de requests
- **Mapeado na KB:** sim

### 3. api — Information Disclosure

- **Componente:** api
- **Família:** api
- **Papel:** workload
- **Instâncias:** 2
- **Categoria STRIDE:** Information Disclosure
- **Ameaça:** Vazamento via respostas de erro
- **Vulnerabilidade:** Stack traces e dados sensíveis em respostas
- **Contramedida:** Erros genéricos, mascaramento de PII
- **Mapeado na KB:** sim

### 4. api — Denial of Service

- **Componente:** api
- **Família:** api
- **Papel:** workload
- **Instâncias:** 2
- **Categoria STRIDE:** Denial of Service
- **Ameaça:** Flood na API
- **Vulnerabilidade:** Sem rate limiting
- **Contramedida:** Throttling, quotas por cliente, CDN
- **Mapeado na KB:** sim

### 5. api — Elevation of Privilege

- **Componente:** api
- **Família:** api
- **Papel:** workload
- **Instâncias:** 2
- **Categoria STRIDE:** Elevation of Privilege
- **Ameaça:** Bypass de autorização
- **Vulnerabilidade:** IDOR / falhas de checagem de escopo
- **Contramedida:** Autorização por recurso, testes de IDOR
- **Mapeado na KB:** sim

### 6. azure_services — Spoofing

- **Componente:** azure_services
- **Família:** azure_platform
- **Papel:** workload
- **Instâncias:** 2
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Chamadas à API Azure com identidade forjada ou credencial estática
- **Vulnerabilidade:** Service principal com segredo de longa duração em vez de Managed Identity
- **Contramedida:** Autenticar com Managed Identity; evitar secrets embutidos nas Logic Apps
- **Mapeado na KB:** sim

### 7. azure_services — Information Disclosure

- **Componente:** azure_services
- **Família:** azure_platform
- **Papel:** workload
- **Instâncias:** 2
- **Categoria STRIDE:** Information Disclosure
- **Ameaça:** Exposição de dados via APIs Azure mal escopadas
- **Vulnerabilidade:** Permissões de leitura amplas em subscriptions/resources
- **Contramedida:** Escopos mínimos por recurso e Private Endpoints onde aplicável
- **Mapeado na KB:** sim

### 8. azure_services — Elevation of Privilege

- **Componente:** azure_services
- **Família:** azure_platform
- **Papel:** workload
- **Instâncias:** 2
- **Categoria STRIDE:** Elevation of Privilege
- **Ameaça:** Escalonamento via RBAC Azure excessivo
- **Vulnerabilidade:** Role assignments amplas (Owner/Contributor) no Resource Group alvo
- **Contramedida:** RBAC least-privilege nas identities que chamam o Azure Resource Manager
- **Mapeado na KB:** sim

### 9. developer_portal — Spoofing

- **Componente:** developer_portal
- **Família:** api
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Cliente forjado na API
- **Vulnerabilidade:** Ausência de autenticação forte
- **Contramedida:** OAuth2/OIDC, mTLS, API keys rotacionadas
- **Mapeado na KB:** sim

### 10. developer_portal — Tampering

- **Componente:** developer_portal
- **Família:** api
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Tampering
- **Ameaça:** Manipulação de payloads
- **Vulnerabilidade:** Validação de entrada insuficiente
- **Contramedida:** Schema validation, WAF, assinatura de requests
- **Mapeado na KB:** sim

### 11. developer_portal — Information Disclosure

- **Componente:** developer_portal
- **Família:** api
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Information Disclosure
- **Ameaça:** Vazamento via respostas de erro
- **Vulnerabilidade:** Stack traces e dados sensíveis em respostas
- **Contramedida:** Erros genéricos, mascaramento de PII
- **Mapeado na KB:** sim

### 12. developer_portal — Denial of Service

- **Componente:** developer_portal
- **Família:** api
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Denial of Service
- **Ameaça:** Flood na API
- **Vulnerabilidade:** Sem rate limiting
- **Contramedida:** Throttling, quotas por cliente, CDN
- **Mapeado na KB:** sim

### 13. developer_portal — Elevation of Privilege

- **Componente:** developer_portal
- **Família:** api
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Elevation of Privilege
- **Ameaça:** Bypass de autorização
- **Vulnerabilidade:** IDOR / falhas de checagem de escopo
- **Contramedida:** Autorização por recurso, testes de IDOR
- **Mapeado na KB:** sim

### 14. logic_apps — Spoofing

- **Componente:** logic_apps
- **Família:** integration
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Uso indevido de conectores / identidades de integração
- **Vulnerabilidade:** Tokens de conectores de longa duração ou credenciais compartilhadas
- **Contramedida:** Managed Identity para autenticar backends; rotacionar secrets de conectores
- **Mapeado na KB:** sim

### 15. logic_apps — Tampering

- **Componente:** logic_apps
- **Família:** integration
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Tampering
- **Ameaça:** Injeção de payload malicioso repassado sem sanitização
- **Vulnerabilidade:** Ausência de validação de schema na entrada da Logic App
- **Contramedida:** Validação de schema na entrada e rejeição de payloads fora do contrato
- **Mapeado na KB:** sim

### 16. logic_apps — Elevation of Privilege

- **Componente:** logic_apps
- **Família:** integration
- **Papel:** workload
- **Instâncias:** 1
- **Categoria STRIDE:** Elevation of Privilege
- **Ameaça:** Escalonamento via autorização fraca na orquestração
- **Vulnerabilidade:** Conectores com escopos excessivos / RBAC frouxo
- **Contramedida:** RBAC least-privilege nas Logic Apps e escopos mínimos nos conectores
- **Mapeado na KB:** sim

### 17. sass_services — Spoofing

- **Componente:** sass_services
- **Família:** dependency
- **Papel:** external
- **Instâncias:** 1
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Impersonação via tokens de integração de terceiros
- **Vulnerabilidade:** Vazamento de tokens OAuth/API keys de SaaS
- **Contramedida:** Credenciais de curta duração, rotação e vault para secrets de integração
- **Mapeado na KB:** sim

### 18. sass_services — Tampering

- **Componente:** sass_services
- **Família:** dependency
- **Papel:** external
- **Instâncias:** 1
- **Categoria STRIDE:** Tampering
- **Ameaça:** Conector SaaS inseguro adulterando dados de integração
- **Vulnerabilidade:** Dependência de terceiro sem controles de integridade/contrato
- **Contramedida:** Contratos de integração, validação de resposta e monitoramento de anomalias
- **Mapeado na KB:** sim

### 19. sass_services — Information Disclosure

- **Componente:** sass_services
- **Família:** dependency
- **Papel:** external
- **Instâncias:** 1
- **Categoria STRIDE:** Information Disclosure
- **Ameaça:** Exposição de dados a conectores SaaS com consentimento excessivo
- **Vulnerabilidade:** Escopos de consentimento amplos em conectores externos
- **Contramedida:** Revisar escopos OAuth, princípio do menor privilégio e conectores aprovados
- **Mapeado na KB:** sim

### 20. user — Spoofing

- **Componente:** user
- **Família:** client
- **Papel:** external
- **Instâncias:** 1
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Usuário forjado no cliente
- **Vulnerabilidade:** Sessões previsíveis / sem MFA
- **Contramedida:** MFA, cookies seguros, binding de sessão
- **Mapeado na KB:** sim

### 21. user — Tampering

- **Componente:** user
- **Família:** client
- **Papel:** external
- **Instâncias:** 1
- **Categoria STRIDE:** Tampering
- **Ameaça:** Manipulação do cliente
- **Vulnerabilidade:** Lógica sensível só no front-end
- **Contramedida:** Validação server-side, attested clients
- **Mapeado na KB:** sim

### 22. user — Repudiation

- **Componente:** user
- **Família:** client
- **Papel:** external
- **Instâncias:** 1
- **Categoria STRIDE:** Repudiation
- **Ameaça:** Ações do usuário sem prova
- **Vulnerabilidade:** Sem trilha de auditoria no cliente→servidor
- **Contramedida:** Logs de autenticação e ações críticas
- **Mapeado na KB:** sim

### 23. user — Information Disclosure

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

### 1. microsoft_entra — Spoofing

- **Componente:** microsoft_entra
- **Família:** security
- **Papel:** control
- **Instâncias:** 2
- **Categoria STRIDE:** Spoofing
- **Ameaça:** Uso indevido de identidades
- **Vulnerabilidade:** Chaves de longa duração
- **Contramedida:** Credenciais de curta duração, rotação
- **Mapeado na KB:** sim

### 2. microsoft_entra — Information Disclosure

- **Componente:** microsoft_entra
- **Família:** security
- **Papel:** control
- **Instâncias:** 2
- **Categoria STRIDE:** Information Disclosure
- **Ameaça:** Segredos expostos
- **Vulnerabilidade:** Secrets em repositório ou logs
- **Contramedida:** Vault/KMS, scanning de secrets
- **Mapeado na KB:** sim

### 3. microsoft_entra — Elevation of Privilege

- **Componente:** microsoft_entra
- **Família:** security
- **Papel:** control
- **Instâncias:** 2
- **Categoria STRIDE:** Elevation of Privilege
- **Ameaça:** Políticas IAM excessivas
- **Vulnerabilidade:** Wildcards em actions/resources
- **Contramedida:** Least privilege, access analyzer
- **Mapeado na KB:** sim