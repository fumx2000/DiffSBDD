# CovaPIE with-TP2 current global readiness census V1

## Purpose and frozen inputs

This deterministic additive successor combines the published with-4LH census,
the published TP2 ingestion matrix, and the published with-TP2 reconciliation.
It keeps the census at exactly 1000 rows and 47 columns in predecessor order.
Selection is by the four exact canonical event identities at scale-up ranks
42–45, never by ligand name and never by raw review-unit priority rank 27.

The frozen priority queue is validation input only and is not rewritten. The
predecessor manifest and published TP2 reconciliation artifact are separate
validation bindings, not computational-source bindings. This layer does
not directly parse or interpret the formal TP2 decision and does not directly
execute a formal, scientific, or candidate validator. The published
reconciliation and ingestion APIs retain their own read-only validation of
frozen external sources, so the full call chain may read that external state.

## Exact19 overlay and STRICT Exact5

Only TP2 Exact4 changes; all 996 non-target rows remain semantic copies of the
predecessor. The authorized overlay has 19 fields. These three remain
false-to-false: `future_training_admission_candidate`,
`human_training_excluded`, and `training_use_include`. The other 16 fields
actually change, including
`training_materialization_allowed_current_source` from empty string to the
string `false`.

The projected TP2 state is:

```text
status=COMPLETED_HUMAN_NEGATIVE
task relevance=NOT_RELEVANT
chemistry=POSITIVE
training use=NOT_APPLICABLE
reactive pair=SG/S1, sample-authoritative
role profile=STRICT_LINKER_PRESENT_V1
W=[S1]
L=[C2,C3,N4]
S=[C5,O21,C6,C20,C19,C18,N7,S8,O16,O17,C9,C10,C11,C12,C13,C14,C15]
boundaries=[S1-C2/SING,N4-C5/SING]
minimal seed=[C5,O21,C6]
primary anchor=C5
structurally applicable task ids=[0,1,2,3,4]
```

The canonical task contract remains exactly:

1. `warhead_only` / `A`
2. `linker_plus_warhead` / `B`
3. `scaffold_plus_warhead` / `B2`
4. `scaffold_only` / `B3`
5. `scaffold_plus_linker_plus_warhead` / `C`

`B3` is present and there is no sixth task. Structural applicability is not a
task label, mask tensor, split, training admission, or runtime authority.

## Resulting census and preserved boundaries

```text
chemistry: POSITIVE 148 -> 152; UNRESOLVED 762 -> 758
task: NOT_RELEVANT 102 -> 106; UNRESOLVED 761 -> 757
training: NOT_APPLICABLE 102 -> 106; UNRESOLVED 762 -> 758
global: CURRENTLY_UNREVIEWED 179 -> 175
        COMPLETED_HUMAN_NEGATIVE 70 -> 74
pair authority: 148 -> 152
role authority: 140 -> 144
mask structural labels: 140 -> 144
STRICT profile: 52 -> 56
DIRECT profile: 88 -> 88
Exact5 applicability: [140,52,52,140,140] -> [144,56,56,144,144]
```

Training include, future candidacy, formal admission, and runtime usability
remain `64 / 47 / 5 / 17`. TP2 contributes zero to each. POST
source/sample/training remains `867 / 21 / 17`, because TP2 already had POST
source evidence in the predecessor. PRE authority/training remains `0 / 0`.

The orthogonal `NOT_RELEVANT / POSITIVE / NOT_APPLICABLE` population is exactly
GVE Exact4 plus LCY Exact4 plus 0D8 Exact4 plus TP2 Exact4, count 16. The former
Exact12 statement is predecessor-only and is not a current-global assertion.

Blockers keep their existing non-exclusive definitions. Within chemistry
positive, missing split, tensor integration, POST training authority, training
admission, and feature semantics are `111 / 111 / 135 / 147 / 152`. Their
within-training-include values remain `39 / 35 / 47 / 59` where applicable.

## Reconciliation, lineage, and next pending unit

The published reconciliation remains 24 sources, 139 accepted facts, and 338
rows. Its priority-review summary is 119/19 completed-positive events/units,
44/9 completed-negative, 163/28 completed-total, and 175/103 unreviewed. These
figures are distinct from global census counts.

The predecessor's ordered 168 semantic bindings are preserved as an exact
prefix. Six computational bindings are appended, yielding 174 with no semantic
identity or role collision. The manifest contains no self SHA256, timestamp,
hostname, PID, absolute machine path, or live Git state.

The frozen queue plus current reconciled statuses derive NWJ as pending rank 1:
raw priority rank 28, review unit
`COVAPIE_BULK_REVIEW_UNIT_DE7AFABE9D079CDF`, PDB `4CM5`, four events. TP2 is
absent from the pending set. This stage does not refresh the queue and does not
prepare, start, or decide NWJ.

## Non-goals and training warning

This stage creates no human or scientific authority, task labels, tensor mask
targets, split, training admission, model usability, or parameter update. It
does not change a loader, model forward path, loss, dataset, or queue, and it
does not run training.

This census is not training readiness. Step12D remains a smoke legality check,
not the final training-feature contract. The historical unknown atom-feature
policy and `feature_semantics_known=False` state require a formal
feature-semantics audit before training preparation or parameter updates. That
audit is not performed here.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python scripts/check_covapie_cumulative1000_current_global_readiness_census_with_tp2_v1.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -q tests/test_covapie_cumulative1000_current_global_readiness_census_with_tp2_v1.py --durations=5
```
