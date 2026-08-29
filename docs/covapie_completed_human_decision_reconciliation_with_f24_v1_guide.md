# CovaPIE completed human decision reconciliation with F24 V1

## Scope

This metadata-only successor adds the published F24 Exact4 completed human
decision to the OZJ completed-decision source chain. It performs one in-memory
generic reconciliation. It does not ingest or rewrite the human decision,
materialize reconciliation output, refresh the global census or priority
queue, admit training data, split or tensorize data, run a model, or update
parameters.

The production entry point is
`reconcile_real_completed_human_decisions_with_f24_v1(repo_root)`.

## Rich ingestion authority and narrow reconciliation fact

The published F24 ingestion owner remains the complete sample-level rich
authority. The thin projector calls its public validated formal-decision
loader and proves the following before projection:

- D1 `RELEVANT`, D2 `POSITIVE`, D3 `CONFIRM_OBSERVED_PAIR`, D4
  `REVISE_ROLE_PARTITION`, and D5 `INCLUDE`;
- the chemical-warhead 5-set `[C1,C2,C8,O2,O6]`;
- the intentionally distinct warhead-role 7-set
  `[C1,C2,C4,C8,O2,O5,O6]`;
- the `DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1` profile, empty linker, and the
  single C2-C5 `SING` scaffold-warhead boundary;
- no selected machine candidate;
- all five canonical tasks, including `scaffold_only` / B3, with F24
  applicability exactly `warhead_only` / A, `scaffold_only` / B3, and
  `scaffold_plus_linker_plus_warhead` / C;
- ingestion-derived future candidacy is true, candidacy is not admission,
  `training_admitted` is false, and formal training readiness is false.

The generic reconciliation contract owns only completed-decision facts. Each
F24 projection therefore contains the event and unit identities, completed
positive status, relevant/positive/INCLUDE dispositions,
`human_training_excluded = false`, and frozen source provenance. Chemical
atoms, role atoms/profile/boundary, task applicability, minimal seed,
PRE/POST interpretation, future candidacy, reaction family, warhead rule, and
warhead type are not projected into `NormalizedCompletedDecisionFact` because
those dimensions are outside that contract.

Those meanings have not been deleted or flattened. They continue to be owned
and published by the F24 ingestion/census lineage; reconciliation deliberately
does not become a second ingestion, chemical-warhead, or role authority.

The ingestion binding names its location `project_parent_relative`; the
generic owner's frozen vocabulary names the same repository-parent location
`repository_parent_relative`. The projector validates the complete ingestion
binding first, then uses the generic namespace while preserving the path,
byte count, SHA256, schema, and review-unit provenance.

## F24 Exact4 and original prior

The single review unit is
`COVAPIE_BULK_REVIEW_UNIT_2557BFE1E3B5C4C5`. Its four distinct PDB 3V4X
contexts are ranks 593 through 596:

- `COVAPIE_CYS_SG_EVENT_V1:3V4X:A:CYS:111-:SG:E:F24:C8`
- `COVAPIE_CYS_SG_EVENT_V1:3V4X:B:CYS:111-:SG:F:F24:C8`
- `COVAPIE_CYS_SG_EVENT_V1:3V4X:C:CYS:111-:SG:G:F24:C8`
- `COVAPIE_CYS_SG_EVENT_V1:3V4X:D:CYS:111-:SG:H:F24:C8`

The original generic historical rows already satisfy the exact prior:

- `current_review_status = CURRENTLY_UNREVIEWED`
- `calibration_eligible = true`
- `calibration_exclusion_reason = ""`

The successor proves the Exact4 event set, single unit, and absence of missing,
duplicate, or extra unit events. It does not rewrite an F24 row and creates no
F24 transition adapter.

ONL remains the sole special transition from `CURRENTLY_IN_PROGRESS` to the
generic completed-decision precondition. Its published adapter is called once.
All F24 rows must remain field-for-field equal before and after that call.

## Source composition and one generic reconciliation

The successor calls the published OZJ source loader exactly once and appends
one F24 source:

- FFQ 8, POA 16, G3H 8, ONL 9, PRF 8, 2VS 8;
- 1F8 8, YUN 7, NEQ 6, CHT 5, OZJ 4, F24 4.

The result is exactly 12 source bindings, 12 unique review units, and 91
collision-free normalized facts. The OZJ reconciliation result is not used as
an overlay. The unchanged generic reconciler is called exactly once on the
ONL-adapted historical rows and all twelve sources. Reversing source order
produces the same semantic result under generic canonical ordering.

## In-memory result

The actual generic result covers 338 events in 131 units:

- completed positive: 91 events / 12 units;
- completed negative: 24 events / 4 units;
- completed total: 115 events / 16 units;
- currently unreviewed and pending: 223 events / 115 units;
- currently in progress: 0 events / 0 units;
- normalized training dispositions: 27 `INCLUDE` and 64
  `EXCLUDE_FROM_TRAINING_ONLY`.

All four F24 identities remain distinct and reconcile to
`COMPLETED_HUMAN_POSITIVE`. Their narrow facts remain relevant, positive,
`INCLUDE`, and not human-training-excluded. `INCLUDE` is a human training-use
disposition, not training admission or runtime authorization.

The checker derives the next unreviewed review unit deterministically from the
generic reconciliation result. Production code does not hardcode it and this
step does not refresh the priority queue.

## Current global census and informational future values

The published current census remains
`covapie_cumulative1000_current_global_readiness_census_with_ozj_v1`. Its
authoritative counts remain 104 positive, 105 relevant, 40 `INCLUDE`, 64
`EXCLUDE_FROM_TRAINING_ONLY`, 23 future candidates, 104 pair authorities, and
104 role authorities. F24 remains `CURRENTLY_UNREVIEWED` there. No current
census artifact is changed by this successor.

The checker independently derives the following as `INFORMATIONAL_ONLY`,
`NOT_CURRENT_GLOBAL_STATE`, and `NOT_MATERIALIZED_THIS_STEP` for a possible
future census successor:

- 108 positive, 109 relevant, 44 `INCLUDE`, 64 `EXCLUDE`;
- 27 future candidates, 108 pair authorities, 108 role authorities;
- 48 strict-profile and 60 direct-profile events;
- authoritative applicability A=108, B=48, B2=48, B3=108, C=108.

## Readiness and validation

This uncommitted, unpushed candidate is ready only for external review. Global
census refresh, priority-queue refresh, training admission, split, and tensor
work remain not started. It is not ready for training.

Feature semantics still require a later audit. Step12D remains
`SMOKE_LEGALITY_VALIDATION_ONLY_NOT_FINAL_TRAINING_FEATURE_CONTRACT`, not a
final training-feature contract.

Run the repository-state-neutral checker with:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
python scripts/check_covapie_completed_human_decision_reconciliation_with_f24_v1.py
```
