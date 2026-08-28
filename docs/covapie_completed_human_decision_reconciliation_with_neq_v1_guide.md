# CovaPIE completed human decision reconciliation with NEQ V1

## Scope

This metadata-only successor adds the frozen NEQ Exact6 completed human
decision to the published completed-decision reconciliation. It does not
materialize a global census, create tensors, admit training data, run a model,
or update parameters.

The production entry point is
`reconcile_real_completed_human_decisions_with_neq_v1(repo_root)`.

## Why NEQ has no transition adapter

All six original NEQ historical rows already have the generic reconciler's
required prior state:

- `current_review_status = CURRENTLY_UNREVIEWED`
- `calibration_eligible = true`
- `calibration_exclusion_reason = ""`

The successor proves the complete Exact6 event set, its single review-unit
identity, absence of missing, duplicate, or extra unit events, and the three
prior-state fields above. It does not rewrite an NEQ row or create an NEQ
transition helper.

The frozen historical population still contains ONL as the sole special unit
whose completed decision follows a `CURRENTLY_IN_PROGRESS` prior. The existing
ONL transition owner is therefore called exactly once. NEQ Exact6 rows are
compared before and after that call and must remain field-for-field identical.

## Source composition

The successor calls the published YUN source loader and appends one projected
NEQ source:

- FFQ: 8
- POA: 16
- G3H: 8
- ONL: 9
- PRF: 8
- 2VS: 8
- 1F8: 8
- YUN: 7
- NEQ: 6

The result is exactly 9 source bindings, 9 review units, and 78 collision-free
normalized facts. The generic reconciler is called exactly once on the
ONL-adapted historical rows and these nine sources.

## NEQ normalized semantics

The thin projector uses the NEQ ingestion owner's validated formal decision.
It projects only reconciliation fields and preserves the two cysteine-site
identities as a source-identity check: three Cys22 events and three Cys81
events.

All NEQ facts have:

- task relevance: `RELEVANT`
- chemistry: `POSITIVE`
- training disposition: `EXCLUDE_FROM_TRAINING_ONLY`
- `human_training_excluded = true`
- `training_admitted = false`
- `decision_finalized = true`

The sole final human-status authority is the frozen NEQ formal-decision path.
Ingestion snapshots, matrices, projectors, YUN/ONL successors, and temporary
ONL normalization are not final status authorities.

Relative to the published YUN reconciliation, NEQ contributes +6 completed
positive events, +6 completed events, -6 unreviewed/pending events, -1 pending
unit, +0 normalized `INCLUDE`, +6 normalized
`EXCLUDE_FROM_TRAINING_ONLY`, and +0 training admissions.

## Reconciled priority-review state

The in-memory reconciliation covers 338 events in 131 units:

- completed positive: 78 events / 9 units
- completed negative: 24 events / 4 units
- completed total: 102 events / 13 units
- currently unreviewed and pending: 236 events / 118 units
- currently in progress: 0 events / 0 units
- normalized training dispositions: 19 `INCLUDE`, 59 `EXCLUDE_FROM_TRAINING_ONLY`

## Global census boundary

This reconciliation is not a global census refresh. The published YUN census
remains authoritative with 89 positive events, 36 training `INCLUDE`, 53
training `EXCLUDE_FROM_TRAINING_ONLY`, and 19 future-admission candidates.

The following values are informational derivations for a future census
successor only: 95 positive, 36 `INCLUDE`, 59 `EXCLUDE_FROM_TRAINING_ONLY`, and
19 future candidates. The expected future blocker counts are 54 positive / 11
`INCLUDE` missing split authority, 54 / 7 missing tensor integration, 78 / 19
missing POST training authority, 90 / 31 missing admission, and 95 positive
events pending the feature-semantics audit.

After a future authoritative queue refresh, the expected pending head is CHT,
review unit `COVAPIE_BULK_REVIEW_UNIT_BCA0E7B8C2B33410`, with five events from
PDB entries 4V3F and 5A2D. This successor neither refreshes that queue nor
starts CHT review.

## Readiness

The NEQ completed decision is reconciled and the result is ready for a future
current-global-census refresh. It is not ready for training. Feature semantics
remain `AUDIT_REQUIRED_LATER`, and Step12D remains a smoke legality check rather
than a final training-feature contract. NEQ's source CCD `C2=C3 DOUB` plus the
observed SG-C3 connection is not promoted here to a complete authoritative
POST-adduct topology or a validated PRE topology.

Run the read-only checker with:

```bash
PYTHONPATH=src python scripts/check_covapie_completed_human_decision_reconciliation_with_neq_v1.py
```
