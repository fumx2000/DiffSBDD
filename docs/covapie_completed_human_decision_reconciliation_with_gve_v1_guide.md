# CovaPIE GVE completed-human-decision reconciliation successor V1

## Scope

This additive metadata-only successor appends the published GVE Exact4 formal
human decision to the published with-SR2 source chain and invokes the unchanged
generic Exact11 reconciler in memory. It does not materialize reconciliation
output, modify or refresh the census, refresh the queue, select a role partition,
create mask authority, admit data to training, create tensor targets, or train.

The direct production dependencies are exactly:

1. `covapie_completed_human_decision_reconciliation_v1`
2. `covapie_completed_human_decision_reconciliation_with_sr2_v1`
3. `covapie_gve_completed_decision_ingestion_and_task_label_availability_v1`

The generic owner, with-SR2 predecessor, GVE ingestion owner, current census,
and historical priority reconciliation remain unchanged.

## Rich validation boundary

`project_gve_completed_decision_v1()` calls the published GVE ingestion owner.
That owner SHA-binds the formal decision JSON and independently validates its
rich authority. The frozen formal validator remains provenance identity only:
it is not imported, parsed, executed, called as a subprocess, or made a runtime
dependency.

Before projection, the successor independently checks:

- the Exact4 events at ranks `295, 296, 480, 986` in review unit
  `COVAPIE_BULK_REVIEW_UNIT_AAB4DCC7D3073222`;
- D1 `NOT_RELEVANT`, D2 `POSITIVE`, D3 `CONFIRM_OBSERVED_PAIR`, D4
  `UNRESOLVED`, and D5 `NOT_APPLICABLE`;
- sample-only SG–CB pair authority, with no all-GVE, legacy 1XD3, reusable, or
  cross-structure promotion;
- no selected role candidate, no W/L/S partition, no role or task-applicability
  sample authority, and role profile `NOT_ESTABLISHED`;
- the canonical five semantic masks, including `scaffold_only` / `B3`, with no
  sixth task and no sample mask authority;
- four PRE source graphs, zero compatible mappings,
  `PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE`, and `PRE_REACTION_UNRESOLVED`;
- four POST evidence events, with zero POST training authority or target;
- D5 `NOT_APPLICABLE` without converting it to
  `EXCLUDE_FROM_TRAINING_ONLY`. `human_training_excluded` remains false;
- no future training candidate, formal training admission, materialization,
  tensor target, runtime usability, parameter-update authority, census refresh,
  or queue refresh.

These rich fields are preconditions only. They are not generic fact fields.

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

Every GVE fact uses:

```text
human_review_completed=true
legacy_completed_review_status=COMPLETED_HUMAN_NEGATIVE
task_relevance_disposition=NOT_RELEVANT
chemistry_disposition=POSITIVE
training_disposition=NOT_APPLICABLE
human_training_excluded=false
source_decision_schema=covapie_gve_exact4_formal_human_decision_v1
source_decision_sha256=0df008d9fe2e142120a22ce6797aaf633725d4627eb6ca8e1be9f869ad0896e2
```

The combination is intentional. Lifecycle status, task relevance, chemistry,
and training disposition are independent axes. In particular, D1 does not
collapse D2, and the rich `COMPLETED_TASK_DOMAIN_NEGATIVE` lane token does not
become the generic legacy status.

The generic authority is the formal JSON, bound in the generic
`repository_parent_relative` namespace:

```text
covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/GVE_COVAPIE_BULK_REVIEW_UNIT_AAB4DCC7D3073222/formal-human-decision-v1/gve_formal_human_decision_v1.json
```

The ingestion owner's `project_parent_relative` term is ingestion provenance
vocabulary only. No ingestion snapshot, matrix, summary, or manifest is used as
generic authority.

## Historical and source-chain contracts

The published historical reconciliation contains exactly the current GVE
Exact4 at raw priority rank `23`, with raw unit count `4`. All four rows are
initially `CURRENTLY_UNREVIEWED` and calibration eligible. It contains zero
legacy 1XD3 GVE events, so that informational context cannot collide with this
current raw review unit.

The append-only source chain changes as follows:

```text
sources:                   19 -> 20
normalized facts:         119 -> 123
stable source identities:  19 -> 20
source collisions:                 0
event collisions:                  0
```

The first 19 sources and facts remain value-equivalent to the published
with-SR2 predecessor. GVE is appended last.

## In-memory reconciliation result

The historical universe remains 338 events in 131 review units.

```text
                         before       after
completed positive      115 / 18     115 / 18
completed negative       28 / 5       32 / 6
completed total         143 / 23     147 / 24
unreviewed              195 / 108    191 / 107
in progress               0 / 0        0 / 0
```

Only the four GVE rows change. The other 334 rows remain field-for-field
identical. The exact changed field set is:

```text
current_review_status
current_status_authority_sources_json
calibration_eligible
calibration_exclusion_reason
```

Each GVE row becomes `COMPLETED_HUMAN_NEGATIVE`, cites only the formal JSON,
sets `calibration_eligible=false`, and uses `COMPLETED_HUMAN_NEGATIVE` as its
calibration exclusion reason.

## Census and training boundaries

The known legacy census cross-field assumption—`NOT_RELEVANT` implying
chemistry `NOT_ESTABLISHED`—is preserved as downstream implementation debt. It
must not override the human D2 `POSITIVE` decision. This successor performs no
census compatibility fix and no census or queue refresh. A dedicated with-GVE
census cross-field audit is required later.

This step is not training readiness. Before formal training preparation or any
parameter update, a feature-semantics audit remains required. Historical
Step12D was a smoke legality check, not a final training-feature contract.

## Public API

```text
CompletedDecisionReconciliationWithGVEError
project_gve_completed_decision_v1
load_real_completed_decision_sources_with_gve_v1
reconcile_real_completed_human_decisions_with_gve_v1
```

No writer, materializer, cache, or registry API is exposed.

## Validation

Run only the targeted tests:

```bash
PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}" \
PYTHONDONTWRITEBYTECODE=1 \
pytest -q -p no:cacheprovider \
tests/test_covapie_completed_human_decision_reconciliation_with_gve_v1.py
```

Then run the read-only checker:

```bash
PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}" \
PYTHONDONTWRITEBYTECODE=1 \
python \
scripts/check_covapie_completed_human_decision_reconciliation_with_gve_v1.py
```

The checker accepts the strict untracked candidate at baseline and future
tracked-clean publication states. Its ancestry-based tracked-clean gate supports
committed-unpushed, pushed, multiple later commits, unrelated later commits,
and `origin/main` between baseline and HEAD, provided the branch is not behind.
