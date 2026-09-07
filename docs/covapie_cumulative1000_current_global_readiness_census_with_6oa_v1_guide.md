# CovaPIE with-6OA current global readiness census V1

## Purpose and frozen inputs

This deterministic additive successor consumes the published with-NWJ census,
the published 6OA completed-decision reconciliation, and the published 6OA
event task-label-availability matrix. It preserves the predecessor's 1000-row,
47-column order and overlays only the Exact4 canonical event identities at
scale-up ranks 855–858. Selection is never ligand-wide, distance-based, or
guessed from a review-unit name.

The frozen priority queue, predecessor manifest, and published reconciliation
artifact are validation identities. They are not duplicate semantic bindings.
The census does not bind or read the formal 6OA JSON directly and does not
import, execute, or subprocess its formal validator. Published ingestion and
reconciliation remain the validated authority-consumption chain.

## Exact19 overlay and task-domain-negative semantics

Only 6OA Exact4 changes. All 996 non-6OA rows remain exact semantic copies of
the predecessor. The authorized overlay has 19 fields. These three fields stay
false-to-false:

- `future_training_admission_candidate`
- `human_training_excluded`
- `training_use_include`

The other 16 fields change. In particular,
`training_materialization_allowed_current_source` changes from an empty string
to the literal string `false`.

The projected state is:

```text
legacy status=COMPLETED_HUMAN_NEGATIVE
source D2=OUT_OF_DOMAIN
normalized task relevance=NOT_RELEVANT
chemistry=POSITIVE
training use=NOT_APPLICABLE
reactive pair=SG/C5, sample-authoritative
role profile=DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
W=[C5,O3]
L=[]
minimal seed=[C3,C4]
primary anchor=C4
structurally applicable task ids=[0,3,4]
```

`COMPLETED_HUMAN_NEGATIVE` is the historical task-domain-negative lane. It is
not chemistry-negative. The source decision `OUT_OF_DOMAIN` is preserved by
ingestion while the generic reconciliation projection is
`OUT_OF_DOMAIN_TO_NOT_RELEVANT`.

The canonical task contract remains exactly:

1. `warhead_only` / `A`
2. `linker_plus_warhead` / `B`
3. `scaffold_plus_warhead` / `B2`
4. `scaffold_only` / `B3`
5. `scaffold_plus_linker_plus_warhead` / `C`

`B3` is present and there is no sixth task. Structural applicability is not a
task label, mask tensor, split, admission, or runtime authority.

## Resulting census and preserved boundaries

```text
global: CURRENTLY_UNREVIEWED 171 -> 167
        COMPLETED_HUMAN_NEGATIVE 74 -> 78
        COMPLETED_HUMAN_POSITIVE 123 -> 123
human review: completed events/units 167/29 -> 171/30
              negative events/units 44/9 -> 48/10
chemistry: POSITIVE 156 -> 160; UNRESOLVED 754 -> 750
task: NOT_RELEVANT 106 -> 110; UNRESOLVED 753 -> 749
training: NOT_APPLICABLE 106 -> 110; UNRESOLVED 754 -> 750
pair authority: 156 -> 160
role authority: 148 -> 152
mask structural labels: 148 -> 152
STRICT profile: 56 -> 56
DIRECT profile: 92 -> 96
Exact5 applicability: [148,56,56,148,148] -> [152,56,56,152,152]
```

Training include, future candidacy, human training exclusion, formal admission,
and runtime usability remain `68 / 51 / 72 / 5 / 17`. POST source, sample, and
training counts remain `867 / 21 / 17`; PRE authority and PRE training remain
`0 / 0`. The rank-857 short POST distance remains published source evidence,
not census geometry authority or a training target.

The orthogonal `NOT_RELEVANT / POSITIVE / NOT_APPLICABLE` population is exactly
GVE, LCY, 0D8, TP2, and 6OA Exact4: 20 events. Stale exact12 and exact16 markers
are rejected.

Blockers are overlapping populations and must not be summed. The refreshed
chemistry-positive population is 160 and the training-include population is 68.
Within chemistry positive, missing split, tensor integration, POST training
authority, training admission, and feature semantics are
`119 / 119 / 143 / 155 / 160`. Their within-training-include values remain
`43 / 39 / 51 / 63` where applicable.

## Lineage and next pending unit

The published reconciliation has 26 sources, 147 accepted facts, and 338 rows.
The predecessor's ordered 180 semantic bindings are retained byte-semantically
as an exact prefix. Exactly six source bindings are appended, yielding 186
unique `(path_namespace, path)` identities with no role collision.

The frozen queue plus reconciled statuses derive PYR as current pending rank 1:
raw priority rank 30, unit
`COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4`, PDB `1F8M`, scale-up ranks
46–49, four events. 6OA is no longer pending. This stage does not refresh the
queue and does not create or start PYR review state.

## Authority and training boundary

This census refresh creates no new human, scientific, chemistry, pair, role, or
reusable authority. It creates no task-label rows, mask/tensor targets, split,
training admission, materialization permission, model usability, or parameter
update authorization. It does not change loaders, model forward paths, losses,
datasets, or the queue and does not run training.

This census is not training readiness. Step12D remains a smoke legality check,
not the final training-feature contract. The historical unknown atom-feature
policy and `feature_semantics_known=False` state still require a formal
feature-semantics audit before training preparation or parameter updates. That
audit is not performed here.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python scripts/check_covapie_cumulative1000_current_global_readiness_census_with_6oa_v1.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -q tests/test_covapie_cumulative1000_current_global_readiness_census_with_6oa_v1.py
```
