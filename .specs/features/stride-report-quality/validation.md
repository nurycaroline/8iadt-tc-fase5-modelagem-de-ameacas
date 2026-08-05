# STRIDE Report Quality Validation

**Date**: 2026-08-05
**Spec**: `.specs/features/stride-report-quality/spec.md`
**Diff range**: `7f0a90d..HEAD` on branch `cursor/stride-report-quality-spec-062c`
**Verifier**: independent sub-agent (author ≠ verifier)

## Task Completion

T1–T12 all ✅ Done (see tasks.md). Implemented: vendor-prefix strip, class_map v2, check-map CLI, KB roles v2, KB entries edge/observability/zone, inventory fallback, per-class grouping, coverage metric, MD restructure, JSON v2, e2e AWS scenario, docs.

## Spec-Anchored Acceptance Criteria

### P1: Vocabulário

| Criterion | Spec outcome | `file:line` + assertion | Result |
| --------- | ------------ | --------------------- | ------ |
| MAP-01 vendor prefix | same family as base | `tests/unit/test_class_map.py:53-55` — `aws-waf==waf`, `Amazon RDS==database`, `azure_sql_database==sql_database` | ✅ PASS |
| MAP-01 precedence | full name wins | `tests/unit/test_class_map.py:68-70` — `config→observability`, `aws_config→security`, `!=` | ✅ PASS |
| MAP-02 100% vocab | all non-unknown | `tests/unit/test_class_map.py:106-108` — `missing == {}` over AWS_REVIEW_CLASSES; `:111-116` reclassifications | ⚠️ Spec-precision gap |
| MAP-03 check-map exit | exit 1 w/ list / exit 0 | `tests/integration/test_cli.py:65,73-74` | ✅ PASS |
| MAP-03 source ausente | exit ≠ 0 | `tests/integration/test_cli.py:79,84` | ✅ PASS (message text not asserted — EC1) |

### P1: KB role-aware

| Criterion | Spec outcome | `file:line` + assertion | Result |
| --------- | ------------ | --------------------- | ------ |
| KBX-01 roles | role per family; default workload | `tests/unit/test_kb.py:47-53` (v2), `:73-74` (v1 → workload) | ✅ PASS |
| KBX-02 edge | Spoofing origin + DoS WAF/Shield | `tests/unit/test_kb.py:81-82,89-90` | ✅ PASS |
| KBX-03 observability | Repudiation trail + Tampering log | `tests/unit/test_kb.py:97-98,106` | ✅ PASS |
| KBX-04 control | no generic exposure text | `tests/unit/test_kb.py:118-125`; `tests/unit/test_engine.py:113`; `tests/integration/test_e2e_pipeline.py:107-114` | ✅ PASS |
| KBX-05 zone | single structural verification | `tests/unit/test_kb.py:113` — `len(zone_entries)==1`; `tests/unit/test_engine.py:104-105` | ✅ PASS |
| KBX-06 map⊆KB | missing == [] | `tests/unit/test_kb.py:136-137` | ✅ PASS |

### P1: Fallback/agrupamento

| Criterion | Spec outcome | `file:line` + assertion | Result |
| --------- | ------------ | --------------------- | ------ |
| ENG-01 fallback | "Não classificado", mapped=False, no "Information Disclosure" | `tests/unit/test_engine.py:61,64-66,80-81` | ✅ PASS |
| ENG-02 grouping | instance_count=N, detections preserved | `tests/unit/test_engine.py:92,94`; `tests/integration/test_e2e_pipeline.py:148-149` | ⚠️ Spec-precision gap |
| ENG-03 coverage | value + warning + exit 0 | `tests/unit/test_engine.py:135,143,149`; `tests/integration/test_cli.py:105-106` | ✅ PASS (`STRIDE_MIN_COVERAGE` env override not directly asserted) |

### P2: Relatório

| Criterion | Spec outcome | `file:line` + assertion | Result |
| --------- | ------------ | --------------------- | ------ |
| REP-01 MD order | ordered sections; empty omitted | `tests/unit/test_report.py:140-145,158,163-169` | ⚠️ Spec-precision gap |
| REP-02 JSON v2 | coverage top; role+instance_count per finding; legacy keys | `tests/unit/test_report.py:62-71,52-57` | ✅ PASS |

**Status**: ⚠️ 14/14 ACs have evidence; 4 spec-precision gaps flagged (MAP-02, ENG-02, REP-01, ENG-03 env-override).

## Discrimination Sensor

| # | Mutation | File:line | Description | Killed? |
| - | -------- | --------- | ----------- | ------ |
| 1 | `src/stride_mvp/stride/engine.py:125` | Reverted fallback `stride_category` `"Não classificado"` → `"Information Disclosure"` | Expected `test_unmapped_never_uses_information_disclosure` + `test_unmapped_component_gets_explicit_fallback_finding` to fail | ✅ Killed (`AssertionError: 'Information Disclosure' == 'Não classificado'`) |
| 2 | `src/stride_mvp/stride/engine.py:96` | Changed `mapped_instances += count` → `mapped_instances = total_instances` | Expected `test_coverage_mixed_mapped_and_unknown` to fail | ❌ Survived — full suite (109 tests) still passes |
| 3 | `src/stride_mvp/data/class_map.py:19-23` | `_strip_vendor` returns `key` unchanged | Expected `test_vendor_prefix_stripped_on_lookup` to fail | ✅ Killed (`AssertionError: 'unknown' == 'edge'`) |

**Sensor depth**: lightweight (3 targeted behavior-level mutations)
**Result**: 2/3 killed — ❌ FAIL (one surviving mutant → fix task)

### Why mutant #2 survives

`StrideEngine.analyze` iterates groups in insertion order. In `test_coverage_mixed_mapped_and_unknown` the order is `rds` (mapped, count 1) → `ec2` (mapped, count 2) → `totally_unknown_xyz` (unmapped, `continue`s before reaching the `mapped_instances` branch). At each `mapped_instances = total_instances` assignment, `total_instances` has only accumulated the *mapped* groups seen so far (1, then 3); the unknown group's count is added to `total_instances` *after* the last assignment. So mutated `mapped_instances` (3) equals correct `mapped_instances` (1+2=3), and `coverage = 3/4 = 0.75` matches the assertion. `test_coverage_all_unknown_is_zero` never triggers the mutated branch (no `mapped_any` ever True). The mutant is equivalent on every existing test.

A discriminating test would place an unmapped group *before* a mapped group in detection order (e.g. `[unknown, rds, ec2]`): then at the mapped assignment `total_instances` already includes the unknown count, so mutated `mapped_instances` would equal `total` → `coverage = 1.0` ≠ correct `0.75`.

## Edge Cases

- [x] **EC1**: pesos/`classes.txt` ausentes → falha com mensagem acionável (não stacktrace).
  - Evidence: `tests/integration/test_cli.py:77-79` and `:82-84` — `exit_code != 0`.
  - ⚠️ Spec-precision gap: tests assert exit code only; "mensagem acionável (não stacktrace)" not asserted.
- [x] **EC2**: todas não mapeadas → `coverage = 0.0`, warning, relatório só sumário + inventário.
  - Evidence: `tests/unit/test_engine.py:138-143` — `coverage == 0.0`; `tests/integration/test_cli.py:87-106` covers warning path.
  - ⚠️ Spec-precision gap: report *structure* (only summary + inventory) in the all-unknown case is not asserted.
- [x] **EC3**: nenhum unknown → seção inventário omitida.
  - Evidence: `tests/unit/test_report.py:148-158` — `"Inventário não classificado" not in md`. ✅ PASS
- [x] **EC4**: família no `class_map` sem entrada KB → teste KBX-06 falha no CI.
  - Evidence: `tests/unit/test_kb.py:128-137` — `missing == []`. ✅ PASS
- [x] **EC5**: detecções duplicadas com confidências distintas → `instance_count` correto e detecções individuais mantidas no JSON.
  - Evidence: `tests/unit/test_engine.py:84-94` (distinct confidences 0.8/0.7…); `tests/integration/test_e2e_pipeline.py:123-152` (ec2 0.9×4, solr 0.8/0.7). ✅ PASS (implicit — "maior confiança" not separately asserted; see ENG-02 gap)
- [x] **EC6**: KB v2 carregando YAML v1 sem `role` → default `workload`.
  - Evidence: `tests/unit/test_kb.py:56-74` — `role("edge") == "workload"`, `role("database") == "workload"`. ✅ PASS
- [x] **EC7**: zero detecções → comportamento atual preservado, coverage omitido (None).
  - Evidence: `tests/unit/test_engine.py:116-121` — `findings == []`, note present; `:146-149` — `coverage is None`. ✅ PASS

## Code Quality

| Principle | Status |
| --------- | ------ |
| Minimum code (no features beyond what was asked) | ✅ |
| Surgical changes (only touched files required) | ✅ |
| No scope creep | ✅ |
| Matches existing patterns/style | ✅ |
| Spec-anchored outcome check (asserted values match spec) | ⚠️ 4 spec-precision gaps |
| Per-layer Coverage Expectation met (domain 1:1 ACs; routes happy+edge+error) | ✅ |
| Every test maps to a spec requirement — no unclaimed tests | ✅ |
| Documented guidelines followed: none — strong defaults applied (pytest pattern inherited from `stride-threat-modeling-mvp`) | ✅ |

## Gate Check

- **Gate command**: `source /workspace/.venv/bin/activate && python -m compileall -q /workspace/src && pytest -q` (run from `/workspace`)
- **Result**: 109 passed, 0 failed, 0 skipped (exit 0)
- **Test count before feature** (at `7f0a90d`): 75 tests collected
- **Test count after feature** (HEAD): 109 tests collected
- **Delta**: +34 new tests
- **Skipped tests**: none
- **Failures**: none

## Fix Plans

### Fix 1: Strengthen `test_coverage_mixed_mapped_and_unknown` to kill mutant #2

- **Root cause**: The test's detection order (mapped groups first, unmapped last) makes the mutated `mapped_instances = total_instances` equivalent to the correct accumulator on this input. The unknown group `continue`s before the assignment, so its count is added to `total_instances` only after the last assignment.
- **Fix task**: Add a case to `test_coverage_mixed_mapped_and_unknown` (or a new test) where an unmapped detection precedes a mapped one — e.g. `[Detection("totally_unknown_xyz", ...), Detection("rds", ...), Detection("ec2", ...), Detection("ec2", ...)]` — and assert `coverage == 0.75`. The mutant would yield `1.0` and fail.
- **Priority**: Major (weak coverage test; coverage is a P1 success criterion)

### Fix 2 (spec-precision, minor): Assert "maior confiança preservada" for ENG-02

- **Root cause**: Spec says "preservando a maior confiança nas detecções listadas"; tests assert `instance_count` and `detections` length but not that the highest confidence is reported per group.
- **Fix task**: Add an assertion that the representative finding (or the `detections` block) for a grouped class reports/preserves the max confidence among the grouped detections — or clarify the spec if "maior confiança" only means the `detections` list is preserved verbatim.
- **Priority**: Minor (spec ambiguous; current behavior preserves all detections)

### Fix 3 (spec-precision, minor): Assert empty-section omission for all roles in REP-01

- **Root cause**: Spec says "seções vazias são omitidas"; only the inventory section omission is tested.
- **Fix task**: Add a test where one role group is absent (e.g. no `zone` detections) and assert the corresponding section header is absent from the Markdown.
- **Priority**: Minor

### Fix 4 (spec-precision, minor): Assert actionable error message for EC1

- **Root cause**: Spec says "mensagem acionável (não stacktrace)"; tests assert exit code only.
- **Fix task**: For `test_check_map_missing_source_exits_nonzero` and `test_check_map_no_source_exits_nonzero`, assert that stderr contains a human-readable message (e.g. "não encontrado" / "Informe --classes") and that no Python traceback appears.
- **Priority**: Minor

### Fix 5 (spec-precision, minor): Assert report structure in all-unknown case (EC2)

- **Root cause**: Spec says "relatório contém apenas sumário + inventário" when all detections are unmapped; only the coverage value is tested.
- **Fix task**: Add a test that runs the engine on all-unmapped detections and asserts the rendered Markdown contains `## Sumário` and `## Inventário não classificado` but none of `Ameaças por componente`, `Controles detectados`, `Zonas de rede`.
- **Priority**: Minor

### Fix 6 (spec-precision, minor): Directly assert `STRIDE_MIN_COVERAGE` env override (ENG-03)

- **Root cause**: `config.py:106-107` reads `STRIDE_MIN_COVERAGE` but no test exercises the env override; the warning threshold is only tested at the default.
- **Fix task**: Add a test (in `tests/unit/test_models_config.py` or `tests/integration/test_cli.py`) that sets `STRIDE_MIN_COVERAGE` via `monkeypatch.setenv` and asserts `cfg.min_coverage` changes (and/or the CLI warning fires at the overridden threshold).
- **Priority**: Minor

## Requirement Traceability Update

| Requirement | Previous Status | New Status |
| ----------- | --------------- | ---------- |
| MAP-01 | Pending | ✅ Verified |
| MAP-02 | Pending | ⚠️ Verified (seeded vocab only; canonical vocab async via check-map) |
| MAP-03 | Pending | ✅ Verified |
| KBX-01 | Pending | ✅ Verified |
| KBX-02 | Pending | ✅ Verified |
| KBX-03 | Pending | ✅ Verified |
| KBX-04 | Pending | ✅ Verified |
| KBX-05 | Pending | ✅ Verified |
| KBX-06 | Pending | ✅ Verified |
| ENG-01 | Pending | ✅ Verified |
| ENG-02 | Pending | ⚠️ Verified (instance_count yes; "maior confiança" gap) |
| ENG-03 | Pending | ⚠️ Verified (env-override gap) |
| REP-01 | Pending | ⚠️ Verified (order yes; empty-section omission gap) |
| REP-02 | Pending | ✅ Verified |
| CTX-01 | Pending | — (P3, out of scope) |
| CTX-02 | Pending | — (P3, out of scope) |

## Summary

**Overall**: ❌ Not Ready (one surviving mutant)

**Spec-anchored check**: 14/14 ACs matched spec outcome (evidence present); 4 spec-precision gaps flagged
**Sensor**: 2/3 mutations killed
**Gate**: 109 passed, 0 failed

**What works**: All 12 tasks implemented; gate green (+34 tests); 14/14 ACs have file:line evidence; KB roles, edge/observability/zone entries, inventory fallback, per-class grouping, coverage metric, MD/JSON v2, e2e AWS scenario all behave per spec on the tested inputs.

**Issues found**:
1. Surviving mutant #2 in `engine.py` coverage accumulator — `test_coverage_mixed_mapped_and_unknown` does not discriminate `mapped_instances = total_instances` because of iteration order. Fix: add a test with an unmapped group before a mapped group.
2. 4 spec-precision gaps (MAP-02 canonical vocab; ENG-02 "maior confiança"; REP-01 empty-section omission for non-inventory roles; ENG-03 `STRIDE_MIN_COVERAGE` env override) + 2 edge-case message/structure gaps (EC1, EC2).

**Next steps**: Route Fix 1 (Major) to an implementer; Fixes 2–6 (Minor, spec-precision) can be batched. Re-verify after fixes (max 3 fix→re-verify iterations).
