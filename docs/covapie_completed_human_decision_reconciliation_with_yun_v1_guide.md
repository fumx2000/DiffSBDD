# CovaPIE completed human decision reconciliation with YUN V1

## Purpose and authority boundary

This additive successor reconciles the frozen YUN Exact7 completed human
decision into the priority-review status universe. It is an in-memory review
status overlay only. It does not refresh the global census, reinterpret YUN
chemistry, create reusable authority, admit or materialize training data,
tensorize data, execute a model, or train.

The projector consumes only event and review-unit identity, completed status,
D1 task relevance, D2 chemistry disposition, D5 training-use disposition,
`human_training_excluded`, `training_admitted`, and the formal source binding.
SG-to-CAN pairing, CAN element C, Candidate4, the W/L/S partition, DIRECT task
set `[0, 3, 4]`, PD168393/acrylamide/Michael-addition context, the observed
CAO-CAN `SING` bond, PRE boundaries, and future-admission candidacy remain
owned by the formal decision and YUN ingestion layer.

## Why YUN has no transition adapter

The original historical reconciliation already contains the complete review
unit `COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D` as seven
`CURRENTLY_UNREVIEWED` rows. Every row is calibration eligible and has an
empty exclusion reason. This is the unchanged generic reconciler's required
prior state, so no YUN adapter, prior rewrite, status normalization, or
transition artifact is created.

A whole-unit non-unreviewed drift remains rejected as
`PRIOR_REVIEW_STATUS_NOT_UNREVIEWED`; a single-row drift may be rejected first
as `HISTORICAL_REVIEW_UNIT_STATUS_MIXED` according to generic validation order.

## Why the ONL adapter is still called

The frozen original historical data still contains ONL Exact9 as
`CURRENTLY_IN_PROGRESS`. The published ONL successor remains the sole owner of
that historical transition, so this successor calls its existing private
helper exactly once. Every YUN Exact7 row is compared before and after the
call, and all fields must remain exactly equal. The ONL adapter therefore
changes no YUN state.

## Source composition and reconciliation

The published 1F8 source loader supplies FFQ8, POA16, G3H8, ONL9, PRF8, 2VS8,
and 1F8 Exact8: seven bindings and 65 collision-free facts. The thin YUN
projector calls the YUN ingestion owner's
`load_frozen_formal_decision_v1(repo_root)` and appends YUN Exact7. The final
composition is:

`FFQ8 + POA16 + G3H8 + ONL9 + PRF8 + 2VS8 + 1F8 8 + YUN7`

This yields eight bindings, eight review units, and 72 collision-free facts
with vector `[8, 16, 8, 9, 8, 8, 8, 7]`. The projector reuses generic
`SourceBinding`, `NormalizedCompletedDecisionFact`, and
`NormalizedDecisionSource`; the unchanged generic reconciler is invoked once
for the final overlay and returns its existing `ReconciliationResult`.

All YUN facts are completed human positive, `RELEVANT`, `POSITIVE`, and
`INCLUDE`, with `human_training_excluded=false` and `training_admitted=false`.
The sole final current-status authority is:

`covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/YUN_COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D/formal-human-decision-v1/yun_formal_human_decision_v1.json`

Its SHA256 is
`b4eeebe03354e820d9658225997c34b58b41c66f4dfe126230024306816e1140`.
Ingestion snapshots, matrices, ingestion/reconciliation owners, the 1F8 or ONL
successors, the ONL adapter, and temporary normalization provenance are not
final human-status authorities.

The resulting priority-review universe is:

| Status | Events | Units |
| --- | ---: | ---: |
| Completed human positive | 72 | 8 |
| Completed human negative | 24 | 4 |
| Completed total | 96 | 12 |
| Currently unreviewed | 242 | 119 |
| Currently in progress | 0 | 0 |
| Pending | 242 | 119 |

The arithmetic is `72 + 24 = 96` and `96 + 242 = 338`. Across the 72
normalized facts, training dispositions are 19 `INCLUDE` and 53
`EXCLUDE_FROM_TRAINING_ONLY`. Relative to the published 1F8 reconciliation,
YUN contributes +7 positive, +7 completed, -7 unreviewed, -7 pending, -1
pending unit, +7 `INCLUDE`, +0 training exclusion, and +0 admission.

## Reconciliation is not a census refresh

The current published 1F8-refreshed global census remains byte-identical:

- chemistry positive: 82
- training `INCLUDE`: 29
- future training candidates: 12

This step creates no census CSV, JSON, summary, snapshot, or manifest. The
expected next values—89 positive, 36 `INCLUDE`, and 19 future candidates—are
`INFORMATIONAL_ONLY` and are not published state.

The informational future blocker derivation is 48 positive / 11 `INCLUDE`
missing split, 48 / 7 missing tensor, 72 / 19 missing POST training authority,
84 / 31 missing admission, and 89 positive with feature semantics pending.
Because YUN7 is `INCLUDE`, not all tensor-missing rows are training-excluded.

The expected next pending unit after a future authoritative census refresh is
NEQ Exact6, `COVAPIE_BULK_REVIEW_UNIT_0E0F340A9F98DA62`, with PDBs 3V61 and
3V62. That queue refresh and NEQ review are outside this step.

## Canonical and training boundary

The canonical V1 mask contract remains exactly five tasks:

1. `warhead_only` / A
2. `linker_plus_warhead` / B
3. `scaffold_plus_warhead` / B2
4. `scaffold_only` / B3
5. `scaffold_plus_linker_plus_warhead` / C

B3 remains present and there is no sixth task. `READY_FOR_TRAINING` remains
false, and feature semantics remain `AUDIT_REQUIRED_LATER`. Step12D was a
smoke legality check, not a final training-feature contract. A formal
feature-semantics audit, including the historical unknown atom-feature policy
and the observed POST CAO-CAN `SING` versus generator PRE electrophile
semantics, remains mandatory before training preparation.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -p no:cacheprovider -q \
  tests/test_covapie_completed_human_decision_reconciliation_with_yun_v1.py
PYTHONDONTWRITEBYTECODE=1 python \
  scripts/check_covapie_completed_human_decision_reconciliation_with_yun_v1.py
```

The checker is repository-lifecycle-neutral: it does not depend on HEAD,
ahead/behind, or commit subject. It binds frozen predecessors and current
census Exact4; validates candidate Exact4; proves the original YUN prior and
ONL non-interference; exercises generic fail-closed gates and source-order
determinism; and keeps published census values separate from informational
expected-next derivations.
