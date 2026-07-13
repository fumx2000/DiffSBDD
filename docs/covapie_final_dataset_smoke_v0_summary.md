# CovaPIE Final Dataset Smoke v0 Retirement Summary

`covapie_final_dataset_smoke_v0` is retired and superseded. Its historical
45-field artifacts remain unchanged, read-only evidence. They are
non-executable and non-canonical; no 45-to-46-field pseudo-migration, alias, or
dual-schema compatibility is provided.

The canonical successor is
`covapie_final_dataset_materialization_smoke_v0`. Its retirement-policy
availability is `pending_commit`, and its frozen manifest path is
`data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0/covapie_final_dataset_materialization_smoke_manifest.json`.
The compatibility commit does not require that uncommitted Step14AR path to
exist in a clean HEAD. Filesystem validation for this pending successor is
explicitly deferred.

All public legacy producer and builder entrypoints fail closed before artifact
reads, writes, manifest construction, or readiness evaluation. The historical
root is never regenerated.

- `historical_artifacts_read_only=true`
- `legacy_artifact_regeneration_forbidden=true`
- `ready_for_training=false`
- `ready_to_train_now=false`
- `feature_semantics_audit_required_before_training=true`
- `recommended_next_step=covapie_final_dataset_materialization_smoke`
