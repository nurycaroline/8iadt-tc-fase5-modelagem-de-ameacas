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

## Quarantined (failed when applied — ignore)

A confirmed lesson that recurred alongside failure. Kept for the maintainer to review.

_none_
