# CovaPIE SR2 completed-human-decision reconciliation successor V1

## Scope

This additive metadata-only successor appends the published SR2 Exact4 formal
human decision to the published with-GD1 source chain and invokes the unchanged
generic Exact11 reconciler in memory. It does not materialize a reconciliation
artifact, refresh the census or queue, create task labels or tensor targets,
admit data to training, or run training.

The direct production dependencies are exactly:

1. `covapie_completed_human_decision_reconciliation_v1`
2. `covapie_completed_human_decision_reconciliation_with_gd1_v1`
3. `covapie_sr2_completed_decision_ingestion_and_task_label_availability_v1`

The generic reconciliation owner, with-GD1 predecessor, and SR2 ingestion
owner remain unchanged.

## Rich validation boundary

`project_sr2_completed_decision_v1()` first calls the published SR2 ingestion
owner. That owner SHA-binds the formal decision JSON and independently validates
its rich authority. The frozen formal validator is provenance identity only: it
is not imported, executed, called as a subprocess, or made a runtime dependency.

The successor then independently checks the returned rich contract before any
generic projection. The checks include:

- formal completion, human authority, and the formal semantic digest;
- the four SR2 events, ranks `321, 323, 337, 338`, priority rank `22`, and the
  single review unit `COVAPIE_BULK_REVIEW_UNIT_A9BBD5309D7A5C08`;
- D1 `RELEVANT`, D2 `POSITIVE`, D3 `CONFIRM_OBSERVED_PAIR`, D4
  `SELECT_CANDIDATE_15`, D5 `INCLUDE`, and the exact D6 identity;
- sample-only SG–C51 pair authority with no reusable or cross-structure rule;
- human-selected Candidate15, Direct profile, W/L/S counts `9/0/18`, the
  C9–N11 single-bond boundary, and applicable tasks `[0, 3, 4]`;
- the canonical five masks, including `scaffold_only` / `B3`, with no sixth
  task;
- unresolved PRE mapping, four POST evidence records, and the absence of PRE
  or POST training authority;
- the engineered Src S345C and T338M/S345C sample caveat, without native Src,
  EGFR C797/T790M, or cross-target authority;
- D5 `INCLUDE` as a training-use disposition only. It leaves formal training
  admission, materialization, tensor targets, current runtime usability, and
  parameter-update authorization false.

These rich fields are preconditions only. They are not generic fact fields.

## Generic Exact11 projection

Each SR2 event produces exactly one unchanged
`NormalizedCompletedDecisionFact` with these eleven fields:

```text
canonical_event_id
review_unit_id
human_review_completed
legacy_completed_review_status
task_relevance_disposition
chemistry_disposition
training_disposition
human_training_excluded
source_decision_schema
source_decision_sha256
source_binding_path
```

The four projections use:

```text
human_review_completed=true
legacy_completed_review_status=COMPLETED_HUMAN_POSITIVE
task_relevance_disposition=RELEVANT
chemistry_disposition=POSITIVE
training_disposition=INCLUDE
human_training_excluded=false
source_decision_schema=covapie_sr2_exact4_formal_human_decision_v1
source_decision_sha256=b41c84d6519efce267410d5e95b017366c9b5b8820a6f5878c9a893404b6defa
```

The authority path is the repository-parent-relative formal JSON:

```text
covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/SR2_COVAPIE_BULK_REVIEW_UNIT_A9BBD5309D7A5C08/formal-human-decision-v1/sr2_formal_human_decision_v1.json
```

It is not the ingestion snapshot, matrix, summary, or manifest. The generic
legacy status remains `COMPLETED_HUMAN_POSITIVE`; the richer
`COMPLETED_HUMAN_POSITIVE_TRAINING_CANDIDATE` token is not projected.

`INCLUDE` does not mean training admitted. The generic fact has no training
admission field, and this step does not establish training readiness. A future
feature-semantics audit remains required before formal training preparation or
parameter updates; the historical Step12D result was only a smoke legality
check, not a final training-feature contract.

## Source chain and in-memory result

The append-only source chain changes as follows:

```text
sources:                  18 -> 19
normalized facts:        115 -> 119
stable source identities: 18 -> 19
source collisions:              0
event collisions:               0
```

The first 18 sources and their facts remain value-equivalent to the published
with-GD1 predecessor. The historical universe remains 338 events in 131 review
units.

```text
                         before       after
completed positive      111 / 17     115 / 18
completed negative       28 / 5       28 / 5
completed total         139 / 22     143 / 23
unreviewed              199 / 109    195 / 108
in progress               0 / 0        0 / 0
```

Only the four SR2 rows change. The other 334 rows remain field-for-field
unchanged. The only changed row fields are:

```text
current_review_status
current_status_authority_sources_json
calibration_eligible
calibration_exclusion_reason
```

Each SR2 row becomes `COMPLETED_HUMAN_POSITIVE`, cites only the formal JSON,
sets `calibration_eligible=false`, and uses `COMPLETED_HUMAN_POSITIVE` as the
calibration exclusion reason. Calibration ineligibility means the row is no
longer pending human-review calibration; it does not negate the generic
training-use disposition `INCLUDE`.

## Public API

The exact public API is:

```text
CompletedDecisionReconciliationWithSR2Error
project_sr2_completed_decision_v1
load_real_completed_decision_sources_with_sr2_v1
reconcile_real_completed_human_decisions_with_sr2_v1
```

`reconcile_real_completed_human_decisions_with_sr2_v1()` returns the unchanged
generic `ReconciliationResult` and writes nothing.

## Validation

Run only the targeted test module:

```bash
PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}" \
PYTHONDONTWRITEBYTECODE=1 \
pytest -q -p no:cacheprovider \
tests/test_covapie_completed_human_decision_reconciliation_with_sr2_v1.py
```

Then run the read-only checker:

```bash
PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}" \
PYTHONDONTWRITEBYTECODE=1 \
python \
scripts/check_covapie_completed_human_decision_reconciliation_with_sr2_v1.py
```

The checker accepts the strict untracked candidate at baseline and future
tracked-clean publication states. Tracked-clean validation is ancestry-based;
it supports immediate committed-unpushed, immediate pushed, multiple later
commits, unrelated later commits, and `origin/main` between baseline and HEAD,
provided the branch is not behind.
