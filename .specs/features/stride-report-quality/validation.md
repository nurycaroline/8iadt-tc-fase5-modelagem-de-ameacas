# STRIDE Report Quality Validation

**Date**: 2026-08-05
**Spec**: `.specs/features/stride-report-quality/spec.md`
**Diff range**: `7f0a90d..HEAD` (`ed40e9f`) on branch `cursor/stride-report-quality-spec-062c`
**Verifier**: independent sub-agent (author ≠ verifier)
**Iteration**: 2/3 (re-verify after fixes in `ed40e9f`)

---

## Task Completion

T1–T12 all ✅ Done (see tasks.md). Implemented: vendor-prefix strip, class_map v2, check-map CLI, KB roles v2, KB entries edge/observability/zone, inventory fallback, per-class grouping, coverage metric, MD restructure, JSON v2, e2e AWS scenario, docs.

---

## Spec-Anchored Acceptance Criteria

### P1: Vocabulário

| Criterion | Spec outcome | `file:line` + assertion | Result |
| --------- | ------------ | --------------------- | ------ |
| MAP-01 vendor prefix | same family as base | `tests/unit/test_class_map.py:53-55` — `aws-waf==waf`, `Amazon RDS==database`, `azure_sql_database==sql_database` | ✅ PASS |
| MAP-01 precedence | full name wins | `tests/unit/test_class_map.py:68-70` — `config→observability`, `aws_config→security`, `!=` | ✅ PASS |
| MAP-02 100% vocab | all non-unknown | `tests/unit/test_class_map.py:106-108` — `missing == {}` over `AWS_REVIEW_CLASSES`; `:111-116` reclassifications | ✅ Verified against seeded vocabulary; canonical closure async (needs real `classes.txt`/weights) |
| MAP-03 check-map exit | exit 1 w/ list / exit 0 | `tests/integration/test_cli.py:65,73-74` | ✅ PASS |
| MAP-03 source ausente | exit ≠ 0 + actionable msg | `tests/integration/test_cli.py:77-83` — `exit_code != 0`, `"não encontrado" in err or "nope.txt"`, `"Traceback" not in err` | ✅ PASS |

### P1: KB role-aware

| Criterion | Spec outcome | `file:line` + assertion | Result |
| --------- | ------------ | --------------------- | ------ |
| KBX-01 roles | role per family; default workload | `tests/unit/test_kb.py:47-53` (v2), `:73-74` (v1 → workload) | ✅ PASS |
| KBX-02 edge | Spoofing origin + DoS WAF/Shield | `tests/unit/test_kb.py:81-82,89-90` | ✅ PASS |
| KBX-03 observability | Repudiation trail + Tampering log | `tests/unit/test_kb.py:97-98,106` | ✅ PASS |
| KBX-04 control | no generic exposure text | `tests/unit/test_kb.py:118-125`; `tests/unit/test_engine.py:122-127`; `tests/integration/test_e2e_pipeline.py:107-114` | ✅ PASS |
| KBX-05 zone | single structural verification | `tests/unit/test_kb.py:113` — `len(zone_entries)==1`; `tests/unit/test_engine.py:111-119` | ✅ PASS |
| KBX-06 map⊆KB | missing == [] | `tests/unit/test_kb.py:136-137` | ✅ PASS |

### P1: Fallback/agrupamento

| Criterion | Spec outcome | `file:line` + assertion | Result |
| --------- | ------------ | --------------------- | ------ |
| ENG-01 fallback | "Não classificado", mapped=False, no "Information Disclosure" | `tests/unit/test_engine.py:61,64-66,80-81` | ✅ PASS |
| ENG-02 grouping | instance_count=N, detections preserved, maior confiança | `tests/unit/test_engine.py:84-94` (instance_count + detections); `tests/unit/test_engine.py:97-108` — `max(confs)==0.95`, `0.95 in confs` (maior confiança preservada); `tests/integration/test_e2e_pipeline.py:148-149` | ✅ PASS |
| ENG-03 coverage | value + warning + exit 0 + env override | `tests/unit/test_engine.py:135,143,149`; `tests/integration/test_cli.py:105-106`; `tests/unit/test_models_config.py:90-95` — `monkeypatch.setenv("STRIDE_MIN_COVERAGE","0.95")` → `min_coverage==0.95` | ✅ PASS |

### P2: Relatório

| Criterion | Spec outcome | `file:line` + assertion | Result |
| --------- | ------------ | --------------------- | ------ |
| REP-01 MD order | ordered sections; empty omitted (all roles) | `tests/unit/test_report.py:138-145` (order); `:148-158` (inventory omitted); `:161-181` (workload-only → control/zone/inventory absent); `:184-201` (control-only → workload absent) | ✅ PASS |
| REP-02 JSON v2 | coverage top; role+instance_count per finding; legacy keys | `tests/unit/test_report.py:60-71,52-57` | ✅ PASS |

**Status**: ✅ All 14 ACs covered with spec-anchored evidence. Remaining async gap: MAP-02 canonical-vocabulary closure (needs real `classes.txt`/weights; `check-map` exists and seeded-vocabulary test passes).

---

## Discrimination Sensor

Sensor runs in scratch (`/tmp/scratch_verify`); working tree never mutated. Originals restored after each mutation; `git status` clean and full suite green (115 passed) at end.

| # | Mutation | File:line | Description | Killed? |
| - | -------- | --------- | ----------- | ------ |
| 1 | `src/stride_mvp/stride/engine.py:125` | Reverted fallback `stride_category` `"Não classificado"` → `"Information Disclosure"` | Expected `test_unmapped_never_uses_information_disclosure` + `test_unmapped_component_gets_explicit_fallback_finding` to fail | ✅ Killed (`AssertionError: 'Information Disclosure' == 'Não classificado'`) |
| 2 | `src/stride_mvp/stride/engine.py:96` | Changed `mapped_instances += count` → `mapped_instances = total_instances` | Expected `test_coverage_unmapped_before_mapped_orders_correctly` to fail (was the surviving mutant in iter 1) | ✅ Killed (`AssertionError: assert 1.0 == 0.75`) |
| 3 | `src/stride_mvp/data/class_map.py:19-23` | `_strip_vendor` returns `key` unchanged | Expected `test_vendor_prefix_stripped_on_lookup` to fail | ✅ Killed (`AssertionError: assert 'unknown' == 'edge'`) |

**Sensor depth**: lightweight (3 targeted behavior-level mutations)
**Result**: 3/3 killed — ✅ PASS

### Note on mutant #2

The previously surviving mutant is now killed by `test_coverage_unmapped_before_mapped_orders_correctly` (`tests/unit/test_engine.py:152-164`), which places an unmapped group (`totally_unknown_xyz`) *before* mapped groups (`rds`, `ec2`×2). Under the mutant `mapped_instances = total_instances`, by the time the mapped branch runs `total_instances` already includes the unknown count (1), so mutated `mapped_instances` becomes 4 → `coverage = 4/4 = 1.0`, while the correct value is `3/4 = 0.75`. The test asserts `0.75` and fails the mutant. Confirmed manually: mutant yields `coverage=1.0`, test asserts `0.75`.

---

## Edge Cases

- [x] **EC1**: pesos/`classes.txt` ausentes → falha com mensagem acionável (não stacktrace).
  - Evidence: `tests/integration/test_cli.py:77-83` — `exit_code != 0`, `"não encontrado" in err or "nope.txt" in err`, `"Traceback" not in err`. ✅ PASS
  - ⚠️ Minor residual: `test_check_map_no_source_exits_nonzero` (`tests/integration/test_cli.py:86-88`, no `--classes`/`--weights` at all) asserts exit code only; the actionable usage message emitted by `cli.py:162-167` is not asserted. Spec edge case is scoped to "pesos/classes.txt não disponíveis", so the no-source case is adjacent rather than in-scope.
- [x] **EC2**: todas não mapeadas → `coverage = 0.0`, warning, relatório só sumário + inventário.
  - Evidence: `tests/unit/test_engine.py:167-172` — `coverage == 0.0`; `tests/unit/test_engine.py:181-198` — rendered MD has `## Sumário` and `## Inventário não classificado` but not `Ameaças por componente`, `Controles detectados`, or `Zonas de rede`; `tests/integration/test_cli.py:87-106` covers warning path. ✅ PASS
- [x] **EC3**: nenhum unknown → seção inventário omitida.
  - Evidence: `tests/unit/test_report.py:148-158` — `"Inventário não classificado" not in md`. ✅ PASS
- [x] **EC4**: família no `class_map` sem entrada KB → teste KBX-06 falha no CI.
  - Evidence: `tests/unit/test_kb.py:128-137` — `missing == []`. ✅ PASS
- [x] **EC5**: detecções duplicadas com confidências distintas → `instance_count` correto, detecções mantidas, maior confiança preservada.
  - Evidence: `tests/unit/test_engine.py:84-94` (distinct confidences, `instance_count==6`, `len(detections)==6`); `tests/unit/test_engine.py:97-108` (`max(confs)==0.95`, `0.95 in confs`); `tests/integration/test_e2e_pipeline.py:123-152`. ✅ PASS
- [x] **EC6**: KB v2 carregando YAML v1 sem `role` → default `workload`.
  - Evidence: `tests/unit/test_kb.py:56-74` — `role("edge")=="workload"`, `role("database")=="workload"`. ✅ PASS
- [x] **EC7**: zero detecções → comportamento atual preservado, coverage omitido (None).
  - Evidence: `tests/unit/test_engine.py:130-135` — `findings == []`, note present; `:175-178` — `coverage is None`. ✅ PASS

---

## Code Quality

| Principle | Status |
| --------- | ------ |
| Minimum code (no features beyond what was asked) | ✅ |
| Surgical changes (only touched files required) | ✅ |
| No scope creep | ✅ |
| Matches existing patterns/style | ✅ |
| Spec-anchored outcome check (asserted values match spec) | ✅ |
| Per-layer Coverage Expectation met (domain 1:1 ACs; routes happy+edge+error) | ✅ |
| Every test maps to a spec requirement — no unclaimed tests | ✅ |
| Documented guidelines followed: none — strong defaults applied (pytest pattern inherited from `stride-threat-modeling-mvp`) | ✅ |

---

## Gate Check

- **Gate command**: `source /workspace/.venv/bin/activate && python -m compileall -q /workspace/src && pytest -q` (run from `/workspace`)
- **Result**: 115 passed, 0 failed, 0 skipped (exit 0)
- **Test count before feature** (at `7f0a90d`): 75 tests collected
- **Test count after feature** (HEAD `ed40e9f`): 115 tests collected
- **Delta**: +40 new tests (+34 in iter 1, +6 in iter 2 fix commit `ed40e9f`)
- **Skipped tests**: none
- **Failures**: none

**Test Integrity Check**: test count increased monotonically (75 → 109 → 115); no assertions weakened; new tests are additive and map to spec ACs/edge cases.

---

## Fix Plans

No new fix plans required. All iter-1 fix tasks resolved in `ed40e9f`:

- ✅ Fix 1 (Major, surviving mutant #2): closed by `test_coverage_unmapped_before_mapped_orders_correctly`.
- ✅ Fix 2 (Minor, ENG-02 "maior confiança"): closed by `test_grouping_preserves_highest_confidence_detection`.
- ✅ Fix 3 (Minor, REP-01 empty-section omission for non-inventory roles): closed by `test_markdown_omits_role_sections_when_absent` + `test_markdown_omits_workload_section_when_only_controls`.
- ✅ Fix 4 (Minor, EC1 actionable error): closed by strengthened `test_check_map_missing_source_exits_nonzero` (asserts message + no traceback).
- ✅ Fix 5 (Minor, EC2 report structure): closed by `test_all_unmapped_report_has_only_summary_and_inventory`.
- ✅ Fix 6 (Minor, ENG-03 env override): closed by `test_load_config_min_coverage_env_override`.

### Remaining ranked gaps (all Minor / async — non-blocking)

1. **MAP-02 canonical-vocabulary closure** (async, acknowledged): `check-map` exists and passes against the seeded AWS-review vocabulary, but 100% closure against the real detector `classes.txt`/weights cannot be verified until the dataset/weights are available in the environment. Not actionable in this iteration.
2. **EC1 no-source usage message not asserted** (Minor, spec-adjacent): `test_check_map_no_source_exits_nonzero` asserts exit code only; the actionable usage string emitted by `cli.py:162-167` ("Informe --classes ...") is not asserted. The spec edge case is scoped to "pesos/classes.txt não disponíveis", which is covered; the no-source case is a usage error adjacent to the edge case.

---

## Requirement Traceability Update

| Requirement | Previous Status (iter 1) | New Status (iter 2) |
| ----------- | ------------------------ | ------------------- |
| MAP-01 | ✅ Verified | ✅ Verified |
| MAP-02 | ⚠️ Verified (seeded; canonical async) | ⚠️ Verified against seeded vocabulary; canonical closure async |
| MAP-03 | ✅ Verified | ✅ Verified |
| KBX-01 | ✅ Verified | ✅ Verified |
| KBX-02 | ✅ Verified | ✅ Verified |
| KBX-03 | ✅ Verified | ✅ Verified |
| KBX-04 | ✅ Verified | ✅ Verified |
| KBX-05 | ✅ Verified | ✅ Verified |
| KBX-06 | ✅ Verified | ✅ Verified |
| ENG-01 | ✅ Verified | ✅ Verified |
| ENG-02 | ⚠️ Verified (maior confiança gap) | ✅ Verified |
| ENG-03 | ⚠️ Verified (env-override gap) | ✅ Verified |
| REP-01 | ⚠️ Verified (empty-section gap) | ✅ Verified |
| REP-02 | ✅ Verified | ✅ Verified |
| CTX-01 | — (P3, out of scope) | — (P3, out of scope) |
| CTX-02 | — (P3, out of scope) | — (P3, out of scope) |

---

## Summary

**Overall**: ✅ Ready

**Spec-anchored check**: 14/14 ACs matched spec outcome (all spec-precision gaps from iter 1 closed); 1 async gap (MAP-02 canonical closure) acknowledged.
**Sensor**: 3/3 mutations killed (previously surviving mutant #2 now killed).
**Gate**: 115 passed, 0 failed.

**What works**: All 12 tasks implemented; gate green (+40 tests since base); 14/14 ACs have file:line evidence with spec-anchored assertions; KB roles, edge/observability/zone entries, inventory fallback, per-class grouping with highest-confidence preservation, coverage metric with env-override, MD/JSON v2 with role-ordered sections and empty-section omission, e2e AWS scenario all behave per spec on the tested inputs.

**Issues found**: None blocking. Two non-blocking residual items (MAP-02 async canonical closure; EC1 no-source usage message not asserted — spec-adjacent only).

**Next steps**: Feature ready to merge. MAP-02 canonical closure to be re-verified asynchronously once the detector `classes.txt`/weights are available; re-run `stride-mvp check-map --classes <real> --weights <real>` and confirm exit 0.
