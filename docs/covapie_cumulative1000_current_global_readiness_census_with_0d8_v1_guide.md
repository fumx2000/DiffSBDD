# CovaPIE with-0D8 current global readiness census V1

## Scope

This deterministic additive successor consumes the published with-LCY census,
the published 0D8 ingestion matrix, and the published with-0D8 reconciliation.
It creates no new authority. It does not read or bind the formal decision
directly, execute its validator, refresh the priority queue, prepare the 4LH
review, alter training data, tensorize, or run training.

The census remains exactly 1000 rows and 47 columns in the predecessor order.
The canonical task contract remains exactly five semantic masks:

1. `warhead_only` / `A`
2. `linker_plus_warhead` / `B`
3. `scaffold_plus_warhead` / `B2`
4. `scaffold_only` / `B3`
5. `scaffold_plus_linker_plus_warhead` / `C`

There is no sixth task.

## Exact additive delta

Only the published 0D8 Exact4 at scale-up ranks 909 through 912 changes. The
996 non-target rows remain identical across all 47 fields. Selection is by
exact `canonical_event_id`, never by ligand component.

The authorized overlay contains 19 fields. Three are authorized but remain
false: `human_training_excluded`, `training_use_include`, and
`future_training_admission_candidate`. Each target changes the same other 16
fields. Every actual change is a member of the authorized set; every field
outside that set is unchanged.

## Published authority projection

The published ingestion and reconciliation establish, for the current 0D8
Exact4 only:

```text
current status=COMPLETED_HUMAN_NEGATIVE
task relevance=NOT_RELEVANT
chemistry=POSITIVE
training use=NOT_APPLICABLE
reactive pair=SG/C8, sample-authoritative
role profile=DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
W=[C8,OH], L=[], S=[C7,CA3,N3]
structurally applicable task ids=[0,3,4]
```

Structural applicability means authoritative role partition plus authoritative
structural task applicability. It does not mean that task labels, event task
rows, mask targets, admission, or tensor targets exist. Those remain false.
PRE remains `PRE_SOURCE_GRAPH_NOT_AVAILABLE / PRE_REACTION_UNRESOLVED`; observed
POST evidence is not promoted to geometry training authority.

The generic reconciliation remains Exact22 sources, Exact131 accepted facts,
22 stable identities, and no duplicate identity. It reports 155 completed
events in 26 units and 183 unreviewed events in 105 units.

## Resulting census

```text
global: CURRENTLY_UNREVIEWED 187 -> 183
        COMPLETED_HUMAN_NEGATIVE 66 -> 70
chemistry: POSITIVE 140 -> 144; UNRESOLVED 770 -> 766
task: NOT_RELEVANT 98 -> 102; UNRESOLVED 769 -> 765
training: NOT_APPLICABLE 98 -> 102; UNRESOLVED 770 -> 766
pair authority: 140 -> 144
role authority: 132 -> 136
mask structural labels: 132 -> 136
DIRECT profile: 80 -> 84
```

Exact5 structural applicability becomes `136 / 52 / 52 / 136 / 136`.
POST source/sample/training stays `867 / 21 / 17`; PRE authority/training stays
`0 / 0`. Training include, future candidacy, formal admission, and runtime
usability stay `60 / 43 / 5 / 17`.

The orthogonal `NOT_RELEVANT / POSITIVE / NOT_APPLICABLE` population is exactly
GVE Exact4 plus LCY Exact4 plus 0D8 Exact4, count 12. None is promoted to a
training sample by this refresh.

## Blockers and next review

Within the 144 chemistry-positive population, missing split, tensor, POST
training authority, training admission, and feature-semantics counts are
`103 / 103 / 127 / 139 / 144`. Their within-training-include counts remain
`35 / 31 / 43 / 55` where applicable.

The frozen queue is not rewritten. The derived next pending unit is current
rank 1, raw rank 26, review unit
`COVAPIE_BULK_REVIEW_UNIT_C4EFE734A5B0CF57`, ligand `4LH`, PDB `4Z16`, four
events. This stage does not start or prepare that review.

## Lineage, lifecycle, and training boundary

The predecessor Exact156 semantic bindings are preserved byte-for-byte and six
computational bindings are appended, yielding Exact162 with no identity or role
collision. The predecessor manifest is a separate validation identity. The new
manifest records no self SHA256, timestamps, machine paths, or live Git state.

The checker accepts exactly two publication placements: `CANDIDATE_UNTRACKED`
and `TRACKED_CLEAN`. The latter covers committed-unpushed, pushed-successor, and
later clean descendants while requiring ancestry and Exact7 publication
history. Mixed tracking, tracked dirt, staging, origin-behind state, ancestry
failure, and missing publication history fail closed.

This census is not training readiness. Step12D remains a smoke legality check,
not the final training-feature contract. The historical unknown atom-feature
policy and `feature_semantics_known=False` condition still require a formal
feature-semantics audit before training preparation or parameter updates. That
audit is not performed here.

## Verification

```bash
python scripts/check_covapie_cumulative1000_current_global_readiness_census_with_0d8_v1.py

python -m pytest -q \
  tests/test_covapie_cumulative1000_current_global_readiness_census_with_0d8_v1.py
```
