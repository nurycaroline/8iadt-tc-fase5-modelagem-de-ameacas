# STRIDE Report Quality — Design

**Spec**: `.specs/features/stride-report-quality/spec.md`  
**Escopo**: Large (4 subsistemas: class_map, KB, engine, report) — sem componentes novos, só evolução dos existentes.

## Decisões de arquitetura

### 1. Normalização de aliases (MAP-01)

`ClassFamilyMapper.to_family` ganha um passo de normalização adicional: após lower/underscore, remover prefixos de vendor (`aws_`, `amazon_`, `azure_`, `gcp_`, `google_`) e tentar lookup do nome base quando o nome completo não resolver. O prefixo só é removido no **lookup** (segunda tentativa) — nomes completos explícitos no YAML continuam tendo precedência.

```python
key = _norm(class_name)              # lower, espaços/hífens → _
family = map.get(key)
if family is None:
    family = map.get(_strip_vendor(key))  # aws_waf → waf
return family or default_family
```

### 2. class_map v2 (MAP-02)

`data/class_map.yaml` estendido com:

- Famílias novas: `edge` (cloudfront, waf, shield, cdn), `observability` (cloudtrail, cloudwatch, x_ray, config), `zone` (vpc, public_subnet, private_subnet, subnet, availability_zone).
- Reclassificações: `cloudfront`/`cdn` saem de `network` → `edge`; `waf` sai de `security` → `edge`; `subnet`/`vpc` saem de `network` → `zone`.
- Vocabulário semeado com as classes do relatório real (solr, efs, backup, internet_gateway, nat_gateway, route53, auto_scaling, shield…). A cobertura canônica é validada depois pelo `check-map` contra `classes.txt`/pesos.

### 3. KB schema v2 (KBX-01)

`data/kb/threats.yaml` ganha bloco `roles` no topo (família → role); entradas continuam iguais. `ThreatKB` expõe `role(family) -> str` com default `workload`. `version: 2`. Loader aceita v1 (sem `roles`) aplicando default — compat com fixtures existentes.

```yaml
version: 2
roles:
  security: control
  observability: control
  edge: control
  zone: zone
  client: external
# demais famílias: workload (default)
```

### 4. Engine: agrupamento + fallback + coverage (ENG-01..03)

`StrideEngine.analyze`:

1. Agrupa detecções por `class_name` normalizado → `(family, instance_count, detections)`.
2. Por grupo mapeado: findings da KB como hoje, com `role` e `instance_count` novos no `ThreatFinding`.
3. Por grupo não mapeado: UM finding `stride_category="Não classificado"`, `mapped=False`, texto de inventário (novo texto no `fallback` da KB, sem STRIDE).
4. Grupos `role=zone`: emite apenas as entradas da família `zone` (verificação estrutural única por classe de zona).
5. Calcula `coverage = grupos_mapeados_ponderados_por_instância / total_detecções` e grava em `ThreatReport.coverage: float | None` (None quando zero detecções).

`ThreatFinding` ganha `role: str = "workload"` e `instance_count: int = 1` (defaults preservam construção existente nos testes). `ThreatReport` ganha `coverage: float | None = None`.

CLI `analyze`: após o pipeline, warning em stderr se `coverage is not None and coverage < limiar` (`STRIDE_MIN_COVERAGE`, default 0.8); exit code inalterado.

### 5. Report v2 (REP-01, REP-02)

`ReportRenderer.to_markdown` reorganizado em seções por role (sumário em tabela; workloads; controles; zonas; inventário — vazias omitidas). `to_json` adiciona `coverage` no topo e `role`/`instance_count` por finding; campos atuais intactos.

### 6. CLI `check-map` (MAP-03)

Novo comando: lê classes de `--classes classes.txt` OU extrai `names` de pesos (`--weights best.pt`, requer ultralytics). Imprime não mapeadas; exit 1 se houver, 0 caso contrário. Erro acionável quando fonte ausente.

## Impacto nos testes existentes

- `test_engine.py`: fallback agora "Não classificado" — testes de fallback atualizados de acordo com o novo AC (mudança de spec, não enfraquecimento).
- `test_report.py`: layout MD novo — asserts de conteúdo (componente/categoria/contramedida presentes) mantidos, asserts de estrutura atualizados.
- Demais suites intactas; `ThreatFinding`/`ThreatReport` com defaults evita quebra em construção posicional? **Não** — construção atual é por keyword nos testes; defaults cobrem.

## Riscos

| Risco | Mitigação |
| ----- | --------- |
| Vocabulário real do dataset diverge do semeado | `check-map` (MAP-03) roda pós-treino e falha listando gaps; completar YAML é mecânico |
| Strip de prefixo causar colisão (ex.: `aws_config` vs `config` genérico) | Lookup em duas fases: nome completo primeiro, base depois |
| Verifier anterior usava fallback antigo | validation.md da feature antiga permanece histórico; nova feature tem novo ciclo |
