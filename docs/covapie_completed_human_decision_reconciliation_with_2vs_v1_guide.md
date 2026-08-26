# CovaPIE completed human decision reconciliation with 2VS V1

## Purpose and authority boundary

This additive successor reconciles the frozen 2VS Exact8 completed human
decision into the priority-review status universe. It is an in-memory review
status reconciliation only. It does not refresh the global census, create
reusable chemistry authority, reinterpret sample-level chemistry, create
training admission, tensorize data, or execute or train a model.

The successor projects only the generic reconciliation fields: D1 task
relevance, D2 chemistry disposition, D5 training-use disposition, completed
status, source binding, event identity, and review-unit identity. D3 reactive
pair, D4 role partition, POST distance and frozen lexeme, the CA6=OA4 motif,
PRE boundaries, and AMSDH context remain owned by the formal decision and the
2VS ingestion owner. They are not converted into reconciliation dispositions.

## Why 2VS has no transition adapter

The original frozen historical reconciliation already contains the complete
2VS review unit
`COVAPIE_BULK_REVIEW_UNIT_5834329D9E2A1F22` as Exact8
`CURRENTLY_UNREVIEWED` rows. Every row is calibration eligible and has an
empty calibration exclusion reason. This directly satisfies the unchanged
generic reconciler's strict prior-state requirement.

Consequently, no 2VS transition adapter, state-normalization helper, or
transition artifact exists. The generic invariant
`PRIOR_REVIEW_STATUS_NOT_UNREVIEWED` remains strict: changing the whole 2VS
unit to a non-unreviewed state is rejected, while a one-row drift may be
rejected earlier as `HISTORICAL_REVIEW_UNIT_STATUS_MIXED`.

## Why the ONL adapter is still required

The frozen original historical reconciliation still contains ONL Exact9 in
`CURRENTLY_IN_PROGRESS`. The already-published ONL successor remains the one
and only owner of that historical transition. This successor calls its private
adapter exactly once in the production pipeline, after proving the original
2VS prior and before invoking the generic reconciler.

Every 2VS Exact8 row is compared before and after the ONL adapter. All fields,
including status, eligibility, exclusion reason, authority provenance, rank,
and review-unit identity, must be exactly equal. The ONL adapter therefore
normalizes only its published ONL Exact9 boundary and creates no 2VS
transition.

## Source composition and generic delegation

The existing PRF source loader supplies the published completed-decision
chain:

- FFQ8
- POA16
- G3H8
- ONL9
- PRF8

The thin 2VS projector calls the frozen 2VS ingestion owner's
`load_frozen_formal_decision_v1(repo_root)` and appends 2VS8. The final
composition has six source bindings, six review units, 57 normalized facts,
and no event collision. It reuses the generic `SourceBinding`,
`NormalizedCompletedDecisionFact`, `NormalizedDecisionSource`, and
`ReconciliationResult` types.

The final overlay is performed once by the unchanged
`generic.reconcile_completed_human_decisions_v1(adapted_historical, sources)`.
The successor does not reuse PRF reconciled rows, duplicate PRF projectors,
copy the ONL transition, or reproduce generic collision, coverage, ordering,
overlay, or summary logic.

## Exact 2VS projection

The formal authority is the repository-parent-relative file
`covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/2VS_COVAPIE_BULK_REVIEW_UNIT_5834329D9E2A1F22/formal-human-decision-v1/2vs_formal_human_decision_v1.json`,
SHA256
`49f33bb2a21669ddb7ab8e98cfa710380e031b280855d5f3ebe6796cde2d06aa`.

All Exact8 facts are completed human positive, `RELEVANT`, `POSITIVE`, and
`EXCLUDE_FROM_TRAINING_ONLY`, with `human_training_excluded=true` and no
training admission. Each final 2VS reconciled row names only that formal file
as current-status authority. Ingestion snapshots, matrices, successor paths,
the ONL adapter, and temporary normalization provenance are not final status
authority.

## Reconciliation result

The priority-review universe remains 338 events in 131 review units:

| Status | Events | Units |
| --- | ---: | ---: |
| Completed human positive | 57 | 6 |
| Completed human negative | 24 | 4 |
| Completed total | 81 | 10 |
| Currently unreviewed | 257 | 121 |
| Currently in progress | 0 | 0 |
| Pending | 257 | 121 |

The arithmetic is `57 + 24 = 81` and `81 + 257 = 338`. Across the 57
normalized completed facts, training dispositions are 12 `INCLUDE` and 45
`EXCLUDE_FROM_TRAINING_ONLY`.

Relative to the published PRF reconciliation, the local 2VS delta is +8
completed positive, +8 completed total, -8 unreviewed, -8 pending, -1 pending
unit, +8 training exclusion, +0 training include, and +0 training admission.

## Reconciliation is not a census refresh

The current published PRF-refreshed global census is frozen and remains at 66
chemistry-positive samples. This step does not modify or replace it. The local
2VS reconciliation delta makes the next global census refresh ready, and the
expected next chemistry-positive value is 74, but 74 is informational derived
state only and is not a published count in this step.

The full informational `EXPECTED_NEXT_CENSUS_DERIVATION` is:

| Field | Expected next value |
| --- | ---: |
| Chemistry positive | 74 |
| Chemistry unresolved | 840 |
| Task relevant | 75 |
| Task unresolved | 839 |
| Training INCLUDE | 29 |
| Training EXCLUDE | 45 |
| Training unresolved | 840 |
| Completed human positive | 57 |
| CURRENTLY_UNREVIEWED | 257 |
| Sample pair authority | 74 |
| Sample role authority | 74 |
| STRICT profile | 31 |
| DIRECT profile | 43 |
| Task A | 74 |
| Task B | 31 |
| Task B2 | 31 |
| Task B3 | 74 |
| Task C | 74 |
| Missing split within positive | 33 |
| Missing tensor within positive | 33 |
| Missing POST training authority | 57 |
| Missing admission | 69 |
| Feature-semantics pending positive | 74 |

The expected missing-tensor composition is G3H8, ONL9, PRF8, and 2VS8. None
of these informational values is materialized by this reconciliation.

## Canonical and training boundary

The global canonical V1 mask contract remains exactly:

1. `warhead_only` / A
2. `linker_plus_warhead` / B
3. `scaffold_plus_warhead` / B2
4. `scaffold_only` / B3
5. `scaffold_plus_linker_plus_warhead` / C

B3 remains present and no sixth task exists. This step does not materialize
pair authority, role authority, warhead atoms, motif, POST or PRE authority,
reaction family, warhead rule, warhead type, tensor targets, or training
admission.

`READY_FOR_TRAINING` remains false. Feature semantics remain
`AUDIT_REQUIRED_LATER`; Step12D was a smoke legality check, not a final
training-feature contract. A feature-semantics audit and resolution of the
historical unknown atom-feature policy are required before training work.

## Verification

Run the focused suite and checker without bytecode or pytest cache output:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -p no:cacheprovider -q \
  tests/test_covapie_completed_human_decision_reconciliation_with_2vs_v1.py
PYTHONDONTWRITEBYTECODE=1 python \
  scripts/check_covapie_completed_human_decision_reconciliation_with_2vs_v1.py
```

The checker is repository-lifecycle-neutral. It binds frozen predecessors and
the published census by bytes and SHA256, verifies the Exact4 candidate,
executes the real projector and generic reconciliation, proves the original
2VS prior and ONL non-interference, exercises strict prior-state failures,
checks source-order determinism, and reports census preservation separately
from the informational expected-next derivation.
