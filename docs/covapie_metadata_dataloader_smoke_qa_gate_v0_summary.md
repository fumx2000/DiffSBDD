# CovaPIE Metadata Dataloader Smoke QA Gate v0 Retirement Summary

`covapie_metadata_dataloader_smoke_qa_gate_v0` is retired atomically with
`covapie_metadata_dataloader_smoke_v0`. The legacy QA implementation directly
instantiates the S2 artifact-backed constructor and invokes S2 key-coverage,
mask-distribution, and blocker-runtime builders. Leaving either side executable
would preserve a partial admission path into the obsolete 20x35/20x45 data
contract.

All artifact, constructor-wrapper, historical builder, readiness, safety, and
run entrypoints now fail closed before invoking S2 or reading CSV/JSON paths.
Existing preview and audit artifacts remain unchanged and read-only; no data is
migrated or copied.

S4 retains import compatibility because it consumes only constants, paths,
schema metadata, historical aliases, and readiness/artifact references from
this module. S4 through S8 have not been retired in this batch. Their feature
evidence remains pending re-anchoring after the canonical 33-field
final-dataset QA stage is materialized.

The exact retirement policy is:

- `legacy_stage_retired=true`
- `legacy_stage_executable=false`
- `successor_availability=redesign_pending`
- `superseded_by_stage=None`
- `superseded_by_manifest_path=None`
- `historical_artifacts_read_only=true`
- `legacy_artifact_regeneration_forbidden=true`
- `ready_for_training=false`
- `ready_to_train_now=false`
- `feature_semantics_audit_required_before_training=true`
- `recommended_next_step=covapie_final_dataset_qa_gate_v1`
- `blocking_reasons=(legacy_stage_superseded, dataloader_interface_redesign_pending)`

No canonical dataloader, QA v1, tensor, checkpoint, or training artifact is
created by this retirement.
