# CovaPIE LCY completed-human-decision reconciliation successor V1

## Scope

This additive metadata-only successor appends the published LCY 4R0O Exact4
formal human decision to the published with-GVE source chain and invokes the
unchanged generic Exact11 reconciler in memory. It does not materialize a
reconciliation CSV, summary, or manifest; refresh a census or queue; prepare a
next-review package; create role or mask authority; admit data to training;
create tensor targets; or train.

The direct production dependencies are exactly:

1. `covapie_completed_human_decision_reconciliation_v1`
2. `covapie_completed_human_decision_reconciliation_with_gve_v1`
3. `covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1`

No GVE ingestion module is a direct dependency. The generic owner, with-GVE
predecessor, LCY ingestion owner, historical population, census, and priority
queue remain unchanged.

## Rich validation boundary

`project_lcy_completed_decision_v1()` calls the published LCY ingestion owner.
That owner SHA-binds the formal decision JSON and independently validates its
rich authority. The frozen formal validator remains provenance identity only:
it is not imported, parsed, executed, called as a subprocess, or made a runtime
dependency.

Before projection, the successor independently checks:

- the 4R0O Exact4 at scaleup ranks `898, 899, 900, 901`, raw priority rank
  `24`, and review unit `COVAPIE_BULK_REVIEW_UNIT_BA488AF51EDD8ED6`;
- D1 `NOT_RELEVANT`, D2 `POSITIVE`, D3 `CONFIRM_OBSERVED_PAIR`, D4
  `UNRESOLVED`, D5 `NOT_APPLICABLE`, and the exact D6 byte count and SHA256;
- the exact six-value formal authority true-set: human formal authority plus
  sample task-relevance, positive-chemistry, reactive-pair, and training-use
  disposition authority;
- sample-only SG–C1 pair authority and POST distances `1.699831`, `1.696052`,
  `1.696490`, and `1.700175`, with no all-LCY, 3A2G, or reusable promotion;
- zero policy-selectable D4 candidates and three evidence-only singleton
  diagnostics, with no selected role, W/L/S, role authority, task-applicability
  authority, or mask authority;
- the canonical five semantic masks, including `scaffold_only` / `B3`, with no
  sixth task;
- one PRE source graph per event, zero compatible mappings,
  `PRE_REACTION_UNRESOLVED`, and no PRE authority;
- four POST evidence events, with no POST training authority or target;
- D5 `NOT_APPLICABLE` without converting it to
  `EXCLUDE_FROM_TRAINING_ONLY`; `human_training_excluded` remains false;
- no future training candidate, formal training admission, materialization,
  tensor target, runtime usability, parameter-update authority, census refresh,
  queue refresh, commit, or push.

These rich fields are projection preconditions only. They are not added to the
generic fact schema.

## Generic Exact11 projection

Each event produces exactly one unchanged `NormalizedCompletedDecisionFact`
with these fields, in this order:

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

Every LCY fact uses:

```text
human_review_completed=true
legacy_completed_review_status=COMPLETED_HUMAN_NEGATIVE
task_relevance_disposition=NOT_RELEVANT
chemistry_disposition=POSITIVE
training_disposition=NOT_APPLICABLE
human_training_excluded=false
source_decision_schema=covapie_lcy_exact4_formal_human_decision_v1
source_decision_sha256=d7c7b427b87b13fa61188bd6b14a3e9dd3a37e4a170176222685065d419a3387
```

The combination is intentional. Lifecycle status, task relevance, chemistry,
and training disposition are independent axes. D1 does not collapse D2, and
the rich `COMPLETED_TASK_DOMAIN_NEGATIVE` lane token does not replace the
generic legacy status.

The generic authority is the 32,277-byte formal JSON, bound in the generic
`repository_parent_relative` namespace:

```text
covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/LCY_COVAPIE_BULK_REVIEW_UNIT_BA488AF51EDD8ED6/formal-human-decision-v1/lcy_formal_human_decision_v1.json
```

The ingestion owner's `project_parent_relative` term is ingestion provenance
vocabulary only. No ingestion snapshot, matrix, summary, or manifest is used as
generic authority.

## Historical and source-chain contracts

The fixed historical population contains the four 4R0O target events as one
complete, currently unreviewed, calibration-eligible review unit at raw rank
`24`. It also contains the separate same-component 3A2G event in a different
review unit. That 3A2G row is not a target, remains field-for-field identical,
and receives no decision, pair, role, PRE, training, or other authority.

The append-only source chain changes as follows:

```text
sources:                   20 -> 21
normalized facts:         123 -> 127
review units:              20 -> 21
stable source identities:  20 -> 21
event collisions:                  0
review-unit collisions:            0
stable-source collisions:          0
```

The first 20 sources remain value-equivalent to the published with-GVE
predecessor. LCY is appended last. The LCY source contains only the 4R0O
Exact4; selection is never ligand-wide.

## In-memory reconciliation result

The historical universe remains 338 events in 131 review units.

```text
                         before       after
completed positive      115 / 18     115 / 18
completed negative       32 / 6       36 / 7
completed total         147 / 24     151 / 25
unreviewed              191 / 107    187 / 106
in progress               0 / 0        0 / 0
```

Only the four 4R0O LCY rows change. The other 334 rows, including 3A2G, remain
field-for-field identical and retain their order. The exact changed field set
is:

```text
current_review_status
current_status_authority_sources_json
calibration_eligible
calibration_exclusion_reason
```

Each target row becomes `COMPLETED_HUMAN_NEGATIVE`, cites only the LCY formal
JSON, sets `calibration_eligible=false`, and uses
`COMPLETED_HUMAN_NEGATIVE` as its calibration exclusion reason. The completed
positive count remains unchanged despite chemistry being positive.

## Census and training boundaries

This step creates no with-LCY census and does not modify the with-GVE or base
census or the priority queue. It performs no next-review preparation.

This step is not training readiness. Before formal training preparation or any
parameter update, a feature-semantics audit remains required. Historical
Step12D was a smoke legality check, not a final training-feature contract.

## Public API

```text
CompletedDecisionReconciliationWithLCYError
project_lcy_completed_decision_v1
load_real_completed_decision_sources_with_lcy_v1
reconcile_real_completed_human_decisions_with_lcy_v1
```

No writer, materializer, cache, registry, or singleton API is exposed.

## Validation

Run only the targeted tests:

```bash
PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}" \
PYTHONDONTWRITEBYTECODE=1 \
pytest -q -p no:cacheprovider \
tests/test_covapie_completed_human_decision_reconciliation_with_lcy_v1.py
```

Then run the read-only checker:

```bash
PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}" \
PYTHONDONTWRITEBYTECODE=1 \
python \
scripts/check_covapie_completed_human_decision_reconciliation_with_lcy_v1.py
```

The checker accepts the strict untracked Exact4 candidate at baseline and
future tracked-clean publication states. Its ancestry gate supports
committed-unpushed, pushed, multiple later commits, unrelated later commits,
and `origin/main` between baseline and HEAD, provided the branch is not behind.
