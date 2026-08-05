# LESSONS — auto-maintained by scripts/lessons.py

> Machine-owned. Do NOT hand-edit. Changes are overwritten on the next `lessons.py` write.
> Canonical state lives in `.specs/lessons.json`. Edit lessons only via the script.
> promote_threshold=2 distinct features · window_days=45 · quarantine_threshold=2

## Confirmed (load these at Specify/Design)

Corroborated across multiple features. Safe to apply as guidance.

_none_

## Candidates (under observation — do NOT load as guidance yet)

Seen once or not yet corroborated. Tracked, not trusted.

### L-001 — Eval-architecture ACs need assertions on expected component sets, not only fake-detector smoke that invents unrelated classes
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `detection,eval` · harmful: 0
- features: stride-threat-modeling-mvp
- evidence: DET-04 (detection,eval)
- last seen: 2026-07-28T20:59:28Z

### L-002 — UI smoke must assert upload input and report output wiring, not merely that the app object is non-null
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `web` · harmful: 0
- features: stride-threat-modeling-mvp
- evidence: UI-01/UI-02 (web)
- last seen: 2026-07-28T20:59:28Z

### L-003 — When the KB defines a full STRIDE category set for a family, assert that full set rather than a loose minimum count
- signal: `spec_precision_gap` · recurrence: 1 feature(s) · scope: `stride` · harmful: 0
- features: stride-threat-modeling-mvp
- evidence: STRIDE-01 (stride)
- last seen: 2026-07-28T20:59:28Z

### L-004 — Library-delegated behaviors named in the spec (e.g. NMS) still need a discriminating test or explicit documented contract
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `detection` · harmful: 0
- features: stride-threat-modeling-mvp
- evidence: edge:NMS (detection)
- last seen: 2026-07-28T20:59:28Z

### L-005 — Coverage accumulator tests must include an unmapped group before a mapped group in detection order so a mutated accumulator that always reports full coverage is detected.
- signal: `surviving_mutant` · recurrence: 1 feature(s) · scope: `stride/engine` · harmful: 0
- features: stride-report-quality
- evidence: src/stride_mvp/stride/engine.py:96 — mutant mapped_instances = total_instances survived test_coverage_mixed_mapped_and_unknown (stride/engine)
- last seen: 2026-08-05T19:41:40Z

### L-006 — When the spec says a grouping preserves the highest confidence, assert the max confidence value is reported per group, not just that detections are listed.
- signal: `spec_precision_gap` · recurrence: 1 feature(s) · scope: `stride/engine` · harmful: 0
- features: stride-report-quality
- evidence: ENG-02 — tests/unit/test_engine.py:84-94 (stride/engine)
- last seen: 2026-08-05T19:41:45Z

### L-007 — When the spec says empty report sections are omitted, assert each role section is omitted when empty, not just the inventory section.
- signal: `spec_precision_gap` · recurrence: 1 feature(s) · scope: `stride/report` · harmful: 0
- features: stride-report-quality
- evidence: REP-01 — tests/unit/test_report.py:148-158 (stride/report)
- last seen: 2026-08-05T19:41:45Z

### L-008 — When the spec requires 100% of the detector training vocabulary to resolve, assert against the canonical classes.txt/names, not just the seed vocabulary.
- signal: `spec_precision_gap` · recurrence: 1 feature(s) · scope: `stride/class_map` · harmful: 0
- features: stride-report-quality
- evidence: MAP-02 — tests/unit/test_class_map.py:104-108 (stride/class_map)
- last seen: 2026-08-05T19:41:45Z

### L-009 — When the spec requires an actionable error message with no stacktrace, assert stderr contains a human-readable message and no traceback, not just exit code != 0.
- signal: `spec_precision_gap` · recurrence: 1 feature(s) · scope: `stride/cli` · harmful: 0
- features: stride-report-quality
- evidence: EC1 — tests/integration/test_cli.py:77-84 (stride/cli)
- last seen: 2026-08-05T19:41:45Z

### L-010 — When the spec defines report structure for an edge case (e.g. all-unknown yields only summary + inventory), assert the section structure, not just the coverage value.
- signal: `spec_precision_gap` · recurrence: 1 feature(s) · scope: `stride/report` · harmful: 0
- features: stride-report-quality
- evidence: EC2 — tests/unit/test_engine.py:138-143 (stride/report)
- last seen: 2026-08-05T19:41:45Z

## Quarantined (failed when applied — ignore)

A confirmed lesson that recurred alongside failure. Kept for the maintainer to review.

_none_
