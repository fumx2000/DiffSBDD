# CovaPIE completed human decision reconciliation with 2A2 V1

## Scope

This metadata-only thin successor adds the published 2A2 Exact4 completed
human decision to the F24 completed-decision source chain and performs one
generic in-memory reconciliation. It does not alter the formal decision or
ingestion, create a rich-label authority, write reconciliation artifacts,
refresh the global census or priority queue, start I12 review, admit training
data, tensorize data, execute a model, or update parameters.

The production entry point is
`reconcile_real_completed_human_decisions_with_2a2_v1(repo_root)`.

## Validated upstream authority and narrow generic projection

The published 2A2 ingestion owner remains the rich semantic validation
boundary. The reconciliation projector calls its validated formal-decision
loader and proves the following before projecting a generic fact:

- D1 `RELEVANT`, D2 `POSITIVE`, D3 `CONFIRM_OBSERVED_PAIR`, D4
  `SELECT_CANDIDATE_4`, and D5 `EXCLUDE_FROM_TRAINING_ONLY`;
- `STRICT_LINKER_PRESENT_V1` with W `[SD]`, L
  `[C1,C15,C16,C17,O18]`, and S
  `[C20,C21,C23,C24,C25,C26,C27,C28,C29,C30,CL99,N19,N22]`;
- all five canonical tasks are applicable, including `scaffold_only` / B3;
- `chemical_warhead_atom_ids` is null and chemical-warhead human authority is
  false;
- complete PRE reagent, PRE topology, PRE geometry, minimal-seed, and POST
  geometry training authorities are false;
- future training candidacy, training admission, runtime usability, and
  parameter-update authority are false;
- the 1F8 precedent did not replace independent 2A2 review, independent review
  is complete, and the stale `2A2_independent_human_review_still_required`
  field is absent.

Only the unchanged `generic.NormalizedCompletedDecisionFact` contract is
projected. Each 2A2 fact contains event and review-unit identity, completed
positive status, relevant and positive dispositions,
`EXCLUDE_FROM_TRAINING_ONLY`, `human_training_excluded = true`, and frozen
source provenance.

Role atoms and profile, chemical-warhead detail, selected candidate, task
applicability, engineered-site context, PRE/POST semantics, minimal seed,
future candidacy, training admission, reaction family, warhead rule, and
warhead type remain upstream. They are not fields in the generic fact, and
the reconciliation successor is not a second rich-label store.

The ingestion binding calls its external location `project_parent_relative`.
After validating that complete binding, the projector uses the generic
owner's equivalent `repository_parent_relative` namespace while preserving
the path, byte count, SHA256, schema, and review-unit provenance.

## Exact4 identity and historical prior

The review unit is `COVAPIE_BULK_REVIEW_UNIT_6B422BBF7FAD44F6`:

- rank 507:
  `COVAPIE_CYS_SG_EVENT_V1:3ORZ:A:CYS:148-:SG:E:2A2:SD`
- rank 508:
  `COVAPIE_CYS_SG_EVENT_V1:3ORZ:B:CYS:148-:SG:G:2A2:SD`
- rank 509:
  `COVAPIE_CYS_SG_EVENT_V1:3ORZ:C:CYS:148-:SG:I:2A2:SD`
- rank 510:
  `COVAPIE_CYS_SG_EVENT_V1:3ORZ:D:CYS:148-:SG:K:2A2:SD`

The historical generic rows must contain exactly these four unique events in
that one review unit with:

- `current_review_status = CURRENTLY_UNREVIEWED`
- `calibration_eligible = true`
- `calibration_exclusion_reason = ""`

2A2 needs no transition adapter. ONL remains the sole historical special
transition owner and its published normalization is called once. All four
2A2 rows must remain field-for-field equal before and after ONL normalization.

## Exact13 composition and one reconciliation authority

The successor calls the published F24 source loader once and appends one 2A2
source. The source fact-count signature is:

```text
[8,16,8,9,8,8,8,7,6,5,4,4,4]
```

This yields 13 source bindings, 13 unique review units, and 95 unique,
collision-free normalized facts. The F24 reconciliation result is not used as
an overlay. The generic reconciler is called once on ONL-normalized historical
rows and the complete Exact13 source tuple. Reversing source order produces
the same result under generic canonical ordering.

## In-memory result

The generic result covers 338 events in 131 review units:

- completed positive: 95 events / 13 units;
- completed negative: 24 events / 4 units;
- completed total: 119 events / 17 units;
- currently unreviewed: 219 events / 114 units;
- currently in progress: 0 events / 0 units;
- normalized training dispositions: 27 `INCLUDE` and 68
  `EXCLUDE_FROM_TRAINING_ONLY`.

Relative to the F24 reconciliation, the 2A2 delta is +4 positive events, +1
positive unit, +4 completed events, +1 completed unit, -4 pending events, -1
pending unit, +0 `INCLUDE`, and +4 `EXCLUDE_FROM_TRAINING_ONLY`.

All four 2A2 rows reconcile to `COMPLETED_HUMAN_POSITIVE`. A positive human
chemistry review is compatible with training exclusion; exclusion does not
convert the completed review status to negative.

## Current census, future information, and next pending unit

The current authoritative global census remains the published F24 census.
Its counts remain:

```text
positive=108 relevant=109 INCLUDE=44 EXCLUDE=64 future=27
pair=108 role=108 STRICT=48 DIRECT=60
A=108 B=48 B2=48 B3=108 C=108
```

2A2 remains `CURRENTLY_UNREVIEWED` in that census. This step does not update
the global census or priority queue.

The checker independently derives the possible future post-2A2 census values
as `INFORMATIONAL_ONLY`, `NOT_CURRENT_GLOBAL_STATE`, and
`NOT_MATERIALIZED_THIS_STEP`:

```text
positive=112 relevant=113 INCLUDE=44 EXCLUDE=68 future=27
pair=112 role=112 STRICT=52 DIRECT=60
A=112 B=52 B2=52 B3=112 C=112
```

It also derives, without production hardcoding, the next unreviewed unit from
the reconciliation result: I12,
`COVAPIE_BULK_REVIEW_UNIT_7D83F048AF8A2295`, raw priority rank 17, four
events across PDBs 1WOF and 2AMP. This is informational only and I12 review is
not started.

## Readiness and deferred technical debt

The candidate is uncommitted and unpushed. Reconciliation output is not
written. Global census refresh, priority refresh, I12 review, training
admission, split, tensor, loader, model, loss, optimizer, and parameter-update
work remain not started. `READY_FOR_TRAINING=false`.

A feature-semantics audit remains required before formal training work.
Step12D remains
`SMOKE_LEGALITY_VALIDATION_ONLY_NOT_FINAL_TRAINING_FEATURE_CONTRACT`.

Exact POSIX filesystem-mode authority technical debt is not changed here. It
is deferred until after 2A2 end-to-end closure, following the 2A2 global
census refresh and before training-preparation expansion.

Run the targeted suite and checker with:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
pytest -p no:cacheprovider -q \
tests/test_covapie_completed_human_decision_reconciliation_with_2a2_v1.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
python scripts/check_covapie_completed_human_decision_reconciliation_with_2a2_v1.py
```
