# CovaPIE completed human decision reconciliation with 1F8 V1

## Purpose and authority boundary

This additive successor reconciles the frozen 1F8 Exact8 completed human
decision into the priority-review status universe. It is an in-memory review
status overlay only. It does not refresh the global census, reinterpret 1F8
chemistry, create reusable authority, admit training data, tensorize data, or
execute or train a model.

The projector consumes only D1 task relevance, D2 chemistry disposition, D5
training-use disposition, completed status, event and review-unit identities,
and the formal source binding. Candidate7, SG-to-SD pairing, SD element S,
STRICT W/L/S roles, engineered PDK1 T148C and disulfide-trapping context,
retained-fragment context, POST distances, and PRE boundaries remain owned by
the formal decision and ingestion owner. Reconciliation does not reinterpret
or rematerialize those fields.

## Why 1F8 has no transition adapter

The original historical reconciliation already contains the complete review
unit `COVAPIE_BULK_REVIEW_UNIT_9723B0F9EC07CC81` as Exact8
`CURRENTLY_UNREVIEWED` rows. Each row is calibration eligible with an empty
exclusion reason. This is exactly the unchanged generic reconciler's required
prior state, so no 1F8 adapter, state normalization, prior rewrite, or
transition artifact is created.

The strict generic failures remain unchanged. A whole-unit non-unreviewed
drift is rejected as `PRIOR_REVIEW_STATUS_NOT_UNREVIEWED`; a one-row drift may
be rejected earlier as `HISTORICAL_REVIEW_UNIT_STATUS_MIXED`.

## Why the ONL adapter is still called

The frozen original historical data still contains ONL Exact9 as
`CURRENTLY_IN_PROGRESS`. The published ONL successor remains the single owner
of that historical transition. The 1F8 successor calls the existing private
ONL helper exactly once before generic reconciliation and does not copy it.

Every 1F8 row is compared before and after this call. All fields must remain
exactly equal, including status, eligibility, exclusion reason, authority
sources, rank, event identity, and review-unit identity. Thus the ONL adapter
changes no 1F8 state.

## Source composition and result

The published 2VS source loader supplies FFQ8, POA16, G3H8, ONL9, PRF8, and
2VS8. The thin 1F8 projector calls
`load_frozen_formal_decision_v1(repo_root)` on the 1F8 ingestion owner and
appends 1F8 Exact8. The final composition has seven source bindings, seven
review units, 65 collision-free normalized facts, and fact counts
`[8, 16, 8, 9, 8, 8, 8]`.

The projector reuses the generic `SourceBinding`,
`NormalizedCompletedDecisionFact`, and `NormalizedDecisionSource` types. The
unchanged generic reconciler performs the single final overlay and returns its
existing `ReconciliationResult`; no source projector or reconciliation
algorithm is duplicated.

All 1F8 facts are completed human positive, `RELEVANT`, `POSITIVE`, and
`EXCLUDE_FROM_TRAINING_ONLY`, with `human_training_excluded=true`. The only
final current-status authority for each 1F8 row is the frozen formal file:

`covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/1F8_COVAPIE_BULK_REVIEW_UNIT_9723B0F9EC07CC81/formal-human-decision-v1/1f8_formal_human_decision_v1.json`

Its SHA256 is
`6a73022e20e2562f95197b9f314b92b0ecead1cebbadf1c17d5ca292eee59e96`.
Ingestion snapshots, matrices, successor modules, the ONL adapter, and
temporary normalization provenance are not final status authorities.

The reconciled priority-review universe remains 338 events and 131 units:

| Status | Events | Units |
| --- | ---: | ---: |
| Completed human positive | 65 | 7 |
| Completed human negative | 24 | 4 |
| Completed total | 89 | 11 |
| Currently unreviewed | 249 | 120 |
| Currently in progress | 0 | 0 |
| Pending | 249 | 120 |

The arithmetic is `65 + 24 = 89` and `89 + 249 = 338`. Across Exact65 facts,
training dispositions are 12 `INCLUDE` and 53
`EXCLUDE_FROM_TRAINING_ONLY`. Relative to the published 2VS reconciliation,
1F8 contributes +8 positive, +8 completed total, -8 unreviewed, -8 pending,
-1 pending unit, +8 training exclusion, +0 training include, and +0 training
admission.

## Reconciliation is not a census refresh

The current published 2VS-refreshed global census remains byte-identical with
74 chemistry-positive samples. This step creates no census CSV, summary, or
manifest. The expected next positive value is 82 (`74 + 8`), but this is only
`EXPECTED_NEXT_CENSUS_DERIVATION`, not published global state. Likewise, YUN
Exact7 is only the informational expected next pending head; its review and an
authoritative queue refresh belong to later work.

## Canonical and training boundary

The canonical V1 mask contract remains exactly:

1. `warhead_only` / A
2. `linker_plus_warhead` / B
3. `scaffold_plus_warhead` / B2
4. `scaffold_only` / B3
5. `scaffold_plus_linker_plus_warhead` / C

B3 remains present and there is no sixth task. `READY_FOR_TRAINING` remains
false and feature semantics remain `AUDIT_REQUIRED_LATER`. Step12D was a smoke
legality check, not a final training-feature contract. A feature-semantics
audit and resolution of the historical unknown atom-feature policy are still
required before training work.

## Verification

Run the focused suite and checker without bytecode or pytest cache output:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -p no:cacheprovider -q \
  tests/test_covapie_completed_human_decision_reconciliation_with_1f8_v1.py
PYTHONDONTWRITEBYTECODE=1 python \
  scripts/check_covapie_completed_human_decision_reconciliation_with_1f8_v1.py
```

The checker is repository-lifecycle-neutral. It binds all frozen predecessors,
the 1F8 formal authority, and the current census Exact4; verifies the candidate
Exact4; proves the original 1F8 prior and ONL non-interference; exercises
generic fail-closed gates; checks source-order determinism; and keeps census
preservation separate from informational expected-next values.
