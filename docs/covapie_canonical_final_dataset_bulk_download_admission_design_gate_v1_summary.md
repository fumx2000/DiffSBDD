# CovaPIE Canonical Final-Dataset Bulk-Download Admission Design Gate v1

## Scope

This metadata-only Step 14AT gate defines the machine-verifiable admission
contract required before a future candidate may enter a bulk-download queue.
It reads only the eight committed Step 14AS QA v1 outputs plus the committed
Step 14AR and Step 14AQ manifests. Artifact-reference paths are never opened.

The canonical final dataset remains a provenance baseline of 11 samples in 5
leakage groups with train/validation/test sample counts of 8/2/1 and group
counts of 2/2/1. It is not reinterpreted as a download candidate list.

## Admission Contract

The future record contract requires unique candidate identity, a valid PDB ID,
ligand identity, explicit covalent Cys SG identity, non-distance-only event
evidence, topology-restoration disposition, deduplication identity, leakage
group assignment, and future download integrity fields.

The 17-field schema is a lifecycle contract rather than a queue-entry form.
Twelve fields are required before download queue admission, `leakage_group_id`
is required before final split, and four observed result fields are required
only after download: `download_result_status`, `observed_http_status`,
`observed_content_length_bytes`, and `observed_sha256`. The observed fields
must not be fabricated as pre-download placeholders. A non-success result or
failed integrity validation is not admissible to later materialization.

The rule registry also requires fail-closed download failures and forbids raw
overwrite. A topology restoration candidate must have an approved template or
an explicit manual-review disposition; neither distance-only inference nor an
unapproved restoration can automatically admit a candidate.

## Boundaries

This gate does not access network resources, raw directories, structures,
artifact-reference targets, tensors, models, checkpoints, dataloaders, or
training. It creates neither a download queue nor a real download manifest.

The five canonical masks remain unchanged: `warhead_only`/`A`,
`linker_plus_warhead`/`B`, `scaffold_plus_warhead`/`B2`,
`scaffold_only`/`B3`, and `scaffold_plus_linker_plus_warhead`/`C`.

## Readiness

The normal design result sets
`ready_for_bulk_download_admission_implementation=true`, while
`ready_for_bulk_download_now=false`, `ready_for_training=false`, and
`ready_to_train_now=false`. Feature semantics audit remains required before
formal training, fine-tuning, or real parameter updates.

## Fail-Closed Evaluation

The gate independently validates source boundaries, the exact schema contract,
the exact 15-rule registry, and safety boundaries. Failed sections produce only
their matching blockers and issue rows, in fixed order: source boundary,
admission schema, admission rule, then safety. Any failed section sets
`ready_for_bulk_download_admission_implementation=false` and recommends
`resolve_covapie_bulk_download_admission_design_gate_blockers`.
