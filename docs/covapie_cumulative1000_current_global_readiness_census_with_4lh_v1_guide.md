# CovaPIE cumulative1000 current global readiness census with 4LH V1

## Purpose and predecessor

This deterministic metadata-only refresh deep-copies the published with-0D8
cumulative1000 census and overlays only the published 4LH Exact4. The published
4LH ingestion matrix supplies chemistry, task, pair, role, and training-use
projection facts; the published with-4LH reconciliation supplies completed
review status. This stage creates no new human or scientific authority and does
not directly read or bind the external formal-decision JSON.

The result remains exactly 1000 rows and 47 columns. Exactly four events at
ranks 950–953 change, while all 996 non-target rows remain field-identical to
the predecessor. The 19-field overlay changes 18 fields per 4LH row;
`human_training_excluded=false` is the sole authorized unchanged field.

## 4LH delta and Exact5 semantics

The four 4LH rows become `COMPLETED_HUMAN_POSITIVE`, chemistry `POSITIVE`, task
`RELEVANT`, and human training-use disposition `INCLUDE`. Their SG/CAP pair and
`DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1` role partition are sample-authoritative,
with `W=[CAP,CAQ,CBE,OAE,NBA]`, an empty linker, 31 scaffold atoms, and
structurally applicable task IDs `[0,3,4]`.

The canonical task contract is unchanged and contains exactly:

1. `warhead_only` / `A`
2. `linker_plus_warhead` / `B`
3. `scaffold_plus_warhead` / `B2`
4. `scaffold_only` / `B3`
5. `scaffold_plus_linker_plus_warhead` / `C`

`B3` is present and there is no sixth task. Structural applicability is not an
authoritative task-label row or a training mask target.

## Geometry and training boundary

4LH already had POST source evidence in the predecessor, so global POST
source/sample/training counts remain `867 / 21 / 17`. PRE mapping remains
`PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS`, PRE status remains
`PRE_REACTION_UNRESOLVED`, and global PRE authority/training counts remain
`0 / 0`. No POST-to-PRE copy, PRE zero fill, reconstruction, or reaction
inference is performed.

4LH `INCLUDE` is human disposition only. No formal training admission is
created. Formal admission and current-runtime usability remain `5 / 17`; no
split, tensor, training dataset, parameter update, or training operation occurs.
A feature-semantics audit is still required later, and Step12D remains only a
smoke-legality check rather than a final training-feature contract.

## Counts, lineage, and next review

Chemistry positive becomes 148, task relevant 137, training include 64, pair
authority 148, role authority 140, mask structural labels 140, DIRECT profile
88, and future training candidates 47. STRICT profile stays 52. The orthogonal
task-negative/chemistry-positive population remains exactly the GVE, LCY, and
0D8 Exact4 sets, count 12.

The exact 162 predecessor semantic bindings are preserved and six roles are
appended, yielding 168 bindings with no semantic-identity or source-role
collision. Source-binding policy V2 is used. The predecessor manifest remains a
separate validation identity, and the new manifest contains no self SHA256,
timestamp, machine-specific absolute path, or live Git state.

The frozen queue is read-only. Combining it with refreshed current statuses
selects `COVAPIE_BULK_REVIEW_UNIT_C750E9F706F9E0AF` (`TP2`) as current pending
rank 1, raw priority rank 27, with four events. TP2 is selected as next pending,
but review is not started or prepared and the queue is not refreshed.

## Validation and non-goals

```bash
python scripts/check_covapie_cumulative1000_current_global_readiness_census_with_4lh_v1.py
PYTHONPATH=src python -m pytest -q tests/test_covapie_cumulative1000_current_global_readiness_census_with_4lh_v1.py
git diff --check
git status --short
```

The checker supports `CANDIDATE_UNTRACKED` and `TRACKED_CLEAN`, including later
clean descendants without hardcoding a future successor SHA. This stage does
not publish, refresh the queue, prepare or start TP2 review, admit training,
modify loaders/models/losses, train, or perform the feature-semantics audit.
