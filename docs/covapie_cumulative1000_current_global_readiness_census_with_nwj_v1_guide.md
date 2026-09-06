# CovaPIE with-NWJ current global readiness census V1

## Purpose and frozen inputs

This deterministic additive successor combines the published with-TP2 census,
the published NWJ ingestion matrix, and the published with-NWJ reconciliation.
It keeps the census at exactly 1000 rows and 47 columns in predecessor order.
Selection is by the four exact canonical event identities at scale-up ranks
674–677, never by ligand name and never by raw review-unit priority rank 28.

The frozen priority queue is validation input only and is not rewritten. The
predecessor manifest and published NWJ reconciliation artifact are separate
validation bindings, not computational-source bindings. This layer does
not directly parse or interpret the formal NWJ decision and does not directly
execute a formal, scientific, or candidate validator. The published
reconciliation and ingestion APIs retain their own read-only validation of
frozen external sources, so the full call chain may read that external state.

## Exact19 overlay and DIRECT Exact5 applicability

Only NWJ Exact4 changes; all 996 non-target rows remain semantic copies of the
predecessor. The authorized overlay has 19 fields. Only
`human_training_excluded` remains false-to-false. The other 18 fields
actually change, including
`training_materialization_allowed_current_source` from empty string to the
string `false`.

The projected NWJ state is:

```text
status=COMPLETED_HUMAN_POSITIVE
task relevance=RELEVANT
chemistry=POSITIVE
training use=INCLUDE
reactive pair=SG/CAV, sample-authoritative
role profile=DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
W=[CAV,OAE]
L=[]
minimal seed=[CAX,CAI,CAK]
primary anchor=CAX
structurally applicable task ids=[0,3,4]
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
chemistry: POSITIVE 152 -> 156; UNRESOLVED 758 -> 754
task: RELEVANT 137 -> 141; UNRESOLVED 757 -> 753
training: INCLUDE 64 -> 68; UNRESOLVED 758 -> 754
global: CURRENTLY_UNREVIEWED 175 -> 171
        COMPLETED_HUMAN_POSITIVE 119 -> 123
pair authority: 152 -> 156
role authority: 144 -> 148
mask structural labels: 144 -> 148
STRICT profile: 56 -> 56
DIRECT profile: 88 -> 92
Exact5 applicability: [144,56,56,144,144] -> [148,56,56,148,148]
```

Training include and future candidacy become `68 / 51`; formal admission and
runtime usability remain `5 / 17`. NWJ contributes four only to the first two. POST
source/sample/training remains `867 / 21 / 17`, because NWJ already had POST
source evidence in the predecessor. PRE authority/training remains `0 / 0`.

The orthogonal `NOT_RELEVANT / POSITIVE / NOT_APPLICABLE` population is exactly
GVE Exact4 plus LCY Exact4 plus 0D8 Exact4 plus TP2 Exact4, count 16. NWJ is
RELEVANT and therefore is not part of this orthogonal population.

Blockers keep their existing non-exclusive definitions. Within chemistry
positive, missing split, tensor integration, POST training authority, training
admission, and feature semantics are `115 / 115 / 139 / 151 / 156`. Their
within-training-include values are `43 / 39 / 51 / 63` where applicable.

## Reconciliation, lineage, and next pending unit

The published reconciliation contains 25 sources, 143 accepted facts, and 338
rows. Its priority-review summary is 123/20 completed-positive events/units,
44/9 completed-negative, 167/29 completed-total, and 171/102 unreviewed. These
figures are distinct from global census counts.

The predecessor's ordered 174 semantic bindings are preserved as an exact
prefix. Six computational bindings are appended, yielding 180 with no semantic
identity or role collision. The manifest contains no self SHA256, timestamp,
hostname, PID, absolute machine path, or live Git state.

The frozen queue plus current reconciled statuses derive 6OA as pending rank 1:
raw priority rank 29, review unit
`COVAPIE_BULK_REVIEW_UNIT_E800FEC791DFDA72`, PDB `4OU2`, four events. NWJ is
absent from the pending set. This stage does not refresh the queue and does not
prepare, start, or decide 6OA.

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
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python scripts/check_covapie_cumulative1000_current_global_readiness_census_with_nwj_v1.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -q tests/test_covapie_cumulative1000_current_global_readiness_census_with_nwj_v1.py --durations=5
```
