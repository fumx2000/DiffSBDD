# GD1 completed-human-decision reconciliation V1

This additive metadata-only successor consumes the published GD1 Exact4 rich
authority through
`covapie_gd1_completed_decision_ingestion_and_task_label_availability_v1`,
projects only the unchanged generic Exact11 fact contract, appends that source
to the published with-4M5 chain, and reconciles the fixed 338-row historical
population in memory.

The direct source-chain predecessor is
`covapie_completed_human_decision_reconciliation_with_4m5_v1`. The successor
proves the predecessor as 17 sources, 111 facts, 17 review units, and 17 stable
source identities, then appends one four-fact GD1 source to obtain 18, 115, 18,
and 18 respectively. It neither forks the generic reconciler nor modifies any
published predecessor.

Before projection, the successor fail-closes on the published human completion,
D1-D5, SG-C77 pair, Candidate0 DIRECT role partition, W/L/S counts 2/0/11,
canonical Exact5 including B3, PRE unresolved state, POST Exact4 evidence, and
the training-exclusion boundary. The formal validator remains provenance bytes
only: it is not imported, executed, or invoked as a subprocess.

Each GD1 generic fact remains chemistry-positive and review-positive while
independently carrying `training_disposition=EXCLUDE_FROM_TRAINING_ONLY` and
`human_training_excluded=true`. Training exclusion must never convert the
legacy completed status to `COMPLETED_HUMAN_NEGATIVE`.

The generic source binding points to the frozen formal GD1 JSON in the
repository-parent namespace (33,315 bytes, SHA256
`ffb8b0c237be2065908d2da6e041fdc57fb2706f19f91ce87d1524bd3aaa9068`).
No ingestion snapshot, matrix, manifest, or owner file becomes decision
authority.

The in-memory reconciliation changes exactly the four GD1 rows and preserves
the other 334 byte-for-value row mappings and row order. Only
`current_review_status`, `current_status_authority_sources_json`,
`calibration_eligible`, and `calibration_exclusion_reason` change. The resulting
summary is positive 111/17, negative 28/5, completed 139/22, in-progress 0/0,
and unreviewed 199/109.

Run the targeted validation with:

```bash
PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}" \
PYTHONDONTWRITEBYTECODE=1 \
pytest -q -p no:cacheprovider \
tests/test_covapie_completed_human_decision_reconciliation_with_gd1_v1.py

PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}" \
PYTHONDONTWRITEBYTECODE=1 \
python scripts/check_covapie_completed_human_decision_reconciliation_with_gd1_v1.py
```

This step creates no materialized output, census or queue refresh, task labels,
tensors, training admission, or model activity. `READY_FOR_TRAINING` remains
false, and a feature-semantics audit remains required before any future formal
training work.
