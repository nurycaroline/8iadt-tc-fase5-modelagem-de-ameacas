# stride-report-fidelity Validation

**Date**: 2026-08-07
**Spec**: `.specs/features/stride-report-fidelity/spec.md`
**Diff range**: `origin/main..HEAD` (`c97df97..a875634`, branch `cursor/stride-report-fidelity-spec-7757`)
**Verifier**: independent sub-agent (author ≠ verifier)

---

## Task Completion

| Task | Status | Notes |
| ---- | ------ | ----- |
| T1 | ✅ Done | Commit `0d919cc` — checkboxes in tasks.md still unchecked (process only) |
| T2 | ✅ Done | Commit `8b85347` |
| T3 | ✅ Done | Commit `2ea5a7b` |
| T4 | ✅ Done | Commit `5075a97` |
| T5 | ✅ Done | Commit `897b65e` |
| T6 | ✅ Done | Commit `a75076e` |
| T7 | ✅ Done | Commit `acacbcf` |
| T8 | ✅ Done | Commit `66ca345` |
| T9 | ✅ Done | Commit `a875634` (AD-008 + handoff) |

---

## Spec-Anchored Acceptance Criteria

| Criterion (WHEN X THEN Y) | Spec-defined outcome | `file:line` + assertion | Result |
| ------------------------- | -------------------- | ----------------------- | ------ |
| SEM-01 EFS → `filesystem`; no S3 vocab; mount/POSIX/crypto | family `filesystem`; forbid `bucket`/`Block public access`/`MFA delete`; cover mount targets / POSIX / encryption | `tests/unit/test_class_map.py:143` — `assert got == expected` (`efs`→`filesystem`); `tests/unit/test_kb.py:158-160` — `assert forbidden not in blob` + `assert "mount" in blob or "posix" in blob`; `tests/integration/test_e2e_pipeline.py:190-192` — same forbid + mount/posix on report blob | ✅ PASS |
| SEM-02 Backup → `backup` role `control`; vault / cross-account / vault lock | family `backup`, role `control`; vault access / cross-account / Vault Lock themes | `tests/unit/test_kb.py:210-214` — `assert kb.role("backup") == "control"` + `assert "vault" in blob`; `tests/integration/test_e2e_pipeline.py:197-198` — `assert all(f.role == "control" …)` + `assert "vault" in backup`; KB content includes Vault Lock + cross-account (`data/kb/threats.yaml:146-147`) | ✅ PASS |
| SEM-03 SES → `email`; SPF/DKIM/DMARC; no fila/DLQ | family `email`; require spf/dkim/dmarc; forbid fila/dlq | `tests/unit/test_class_map.py:128-129`; `tests/unit/test_kb.py:170-173`; `tests/integration/test_e2e_pipeline.py:202-205` | ✅ PASS |
| SEM-04 Auto Scaling → `scaling` control; no container/IMDSv2; scaling DoS | family `scaling`, role `control`; forbid escape de container / IMDSv2 | `tests/unit/test_class_map.py:129-132`; `tests/unit/test_kb.py:178-186`; `tests/integration/test_e2e_pipeline.py:209-214` | ✅ PASS |
| SEM-05 `aws_cloud`/`aws_region` → zero STRIDE; role `scope`; mapped in coverage | role `scope`, category `Escopo`, not in STRIDE_CATEGORIES; coverage counts mapped; no detail heading | `tests/unit/test_engine.py:225-232` — `coverage == 1.0`, `role == "scope"`, `stride_category == "Escopo"`, `not in STRIDE_CATEGORIES`; `tests/unit/test_report.py:399-401`; `tests/integration/test_e2e_pipeline.py:217-221` | ✅ PASS |
| SEM-06 map↔KB: non-scope families ≥1 entry; scope exempt | missing families list empty after exempting scope | `tests/unit/test_kb.py:136-142` — `assert missing == []` with `scope_families` exempt; `tests/unit/test_kb.py:147-148` — management scope, no entries | ✅ PASS |
| AZR-01 `resource_group` → zero STRIDE, role `scope` | same scope mechanism as SEM-05 | `tests/unit/test_engine.py:226-231`; `tests/unit/test_report.py:399-401`; `tests/integration/test_e2e_pipeline.py:262-266` | ✅ PASS |
| AZR-02 Logic Apps → `integration`; tokens/schema/API auth; MI/RBAC; no container vocab | family `integration`; forbid container/seccomp/IMDSv2/HPA; require Managed Identity or RBAC | `tests/unit/test_class_map.py:138-139`; `tests/unit/test_kb.py:198-205`; `tests/integration/test_e2e_pipeline.py:271-275` | ✅ PASS |
| AZR-03 `sass_services`/`azure_services` → `dependency` external; third-party trust; no containers | family `dependency`, role `external`; no container vocab | `tests/unit/test_class_map.py:140-141`; `tests/unit/test_kb.py:191-199`; `tests/integration/test_e2e_pipeline.py:268-272` | ✅ PASS |
| DED-01 same-class IoU≥thr OR containment≥0.8 → keep highest conf | removed==1, kept==[high] / kept==[outer] | `tests/unit/test_dedupe.py:28-30`, `:37-40`; `tests/unit/test_pipeline_run.py:102-105` | ✅ PASS |
| DED-02 `STRIDE_DEDUPE_IOU` default 0.5; 0 disables | defaults; env override; threshold 0 no-op | `tests/unit/test_models_config.py:102-113`; `tests/unit/test_dedupe.py:46-48`; `tests/unit/test_pipeline_run.py:122-123` | ✅ PASS |
| DED-03 disjoint same-class preserved | removed==0, len(kept)==2 | `tests/unit/test_dedupe.py:54-56` | ✅ PASS |
| DED-04 different classes overlapping preserved | removed==0; both class names kept | `tests/unit/test_dedupe.py:62-64` | ✅ PASS |
| CONF-01 Markdown summary confidence column (max, 2 dp) | column `Confiança`; value formatted `.2f` | `tests/unit/test_report.py:303-304` — `assert "Confiança" in md` + `assert "0.32" in md` | ✅ PASS |
| CONF-02 max conf < `STRIDE_LOW_CONF` → ⚠ + note; 0 disables | ⚠ + falsos positivos note; high conf unmarked; low_conf=0 → all False | `tests/unit/test_report.py:305-306`, `:332-333`; `tests/unit/test_engine.py:253-256`, `:265` | ✅ PASS |
| CONF-03 JSON `max_confidence` + `low_confidence`; existing fields kept | JSON fields present with expected values | `tests/unit/test_report.py:358-359` — `finding["max_confidence"] == pytest.approx(0.77)` + `finding["low_confidence"] is False` | ✅ PASS |
| REG-01 AWS arch1 scripted scenario: SEM-01..05 term asserts | forbidden/required terms + scope for region | `tests/integration/test_e2e_pipeline.py:164-221` (full scenario) | ✅ PASS |
| REG-02 Azure arch2: dedupe counts, RG scope, no container vocab | entra instance_count=1; RG scope; logic/saas forbid container vocab | `tests/integration/test_e2e_pipeline.py:252-275` | ✅ PASS |

**Status**: ✅ All 18 ACs covered with evidence-or-zero citations matching spec outcomes

---

## Discrimination Sensor

| Mutation | File:line | Description | Killed? |
| -------- | --------- | ----------- | ------- |
| 1 | `data/class_map.yaml` (efs under `storage`) | Put `efs` back in `storage` family | ✅ Killed — `test_fidelity_reallocations_match_semantic_families` + REG-01 (`'bucket' not in efs`) |
| 2 | `src/stride_mvp/detection/dedupe.py` early-return | Disable all dedupe (`if True: return list, 0`) | ✅ Killed — DED unit tests + pipeline + REG-02 (`len(entra_dets) == 1`) |
| 3 | `src/stride_mvp/stride/engine.py` `is_low` | Force `is_low = False` (never mark low confidence) | ✅ Killed — `test_findings_carry_max_confidence_and_low_flag` (`rds.low_confidence is True`) |

**Sensor depth**: lightweight (3 behavior-level mutations)
**Scratch protocol**: mutate → pytest → `git checkout -- <files>`; working tree left clean
**Result**: 3/3 killed — PASS ✅

---

## Interactive UAT Results

N/A — backend/pipeline feature; automated checks sufficient per validate.md.

---

## Code Quality

| Principle | Status |
| --------- | ------ |
| Minimum code | ✅ |
| Surgical changes | ✅ — scoped to map/KB/dedupe/config/engine/pipeline/report + tests |
| No scope creep | ✅ — no YOLO retrain; out-of-scope labels untouched |
| Matches patterns | ✅ — env walrus pattern, ScriptedDetector e2e, KB v2 roles |
| Spec-anchored outcome check | ✅ |
| Per-layer Coverage Expectation met | ✅ — unit for map/KB/dedupe/engine/config/report/pipeline; integration for REG |
| Every test maps to a spec requirement / edge / Done-when | ✅ |
| Documented guidelines followed: none beyond pytest.ini — strong defaults applied | ✅ |

---

## Edge Cases

- [x] Dedupe removals → survivors only in `report.detections` + note — `tests/unit/test_pipeline_run.py:102-106` (`len(report.detections) == 2`, `"Dedupe espacial" in notes`)
- [x] All-scope report → coverage 1.0 — `tests/unit/test_engine.py:235-239`; scope omitted from threat sections — `tests/unit/test_report.py:67` skip + `:399-401`
- [x] KB without declared role → default `workload` — `tests/unit/test_kb.py:56-74` (`test_roles_default_workload_for_v1_yaml`)
- [x] Invalid `STRIDE_DEDUPE_IOU` / `STRIDE_LOW_CONF` → actionable ValueError — `tests/unit/test_models_config.py:116-129`
- [x] Chain A~B~C converges to one — `tests/unit/test_dedupe.py:71-73`
- [x] Post-reallocation vocabulary resolves ≠ unknown — `tests/unit/test_class_map.py:146-152` (`test_kaggle_vocabulary_full_coverage`) + AWS review set `:104-108`

---

## Gate Check

- **Gate command**: `source /workspace/.venv/bin/activate && python -m compileall -q src && pytest -q`
- **Result**: 154 passed, 0 failed, 0 skipped
- **Test count before feature** (`origin/main`): 119 `test_*` functions
- **Test count after feature** (`HEAD`): 154 `test_*` functions
- **Delta**: +35 new tests
- **Skipped tests**: none
- **Failures**: none
- **Test integrity**: count increased; no evidence of weakened/deleted prior asserts in feature diff

---

## Fix Plans

None — no AC gaps, no surviving mutants, no gate failures.

---

## Requirement Traceability Update

| Requirement | Previous Status | New Status |
| ----------- | --------------- | ---------- |
| SEM-01..06 | Design / Pending | ✅ Verified |
| AZR-01..03 | Design / Pending | ✅ Verified |
| DED-01..04 | Design / Pending | ✅ Verified |
| CONF-01..03 | Design / Pending | ✅ Verified |
| REG-01..02 | Design / Pending | ✅ Verified |

---

## Summary

**Overall**: ✅ Ready

**Spec-anchored check**: 18/18 ACs matched spec outcome | 0 spec-precision gaps
**Sensor**: 3/3 mutations killed
**Gate**: 154 passed

**What works**: Semantic family reallocations + KB terms; scope role without STRIDE findings; spatial dedupe (IoU/containment/chain); confidence column/⚠/JSON fields; arch1/arch2 fidelity regressions.

**Issues found**: none (tasks.md Done-when checkboxes remain unchecked — documentation hygiene only, not a product gap)

**Next steps**: Mark feature verified; no fix tasks.
