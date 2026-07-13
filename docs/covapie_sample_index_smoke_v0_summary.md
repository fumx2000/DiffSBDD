# CovaPIE Sample Index Smoke v0 Retirement Summary

`covapie_sample_index_smoke_v0` is retired and superseded. Its historical
31-field CSV/JSON artifacts remain unchanged and read-only evidence; they are
not an executable or canonical sample-index contract.

The canonical successor is
`covapie_sample_index_materialization_smoke_v0`, with the tracked manifest at
`data/derived/covalent_small/covapie_sample_index_materialization_smoke_v0/covapie_sample_index_materialization_smoke_manifest.json`.
No 31-to-33-field pseudo-migration, alias, or dual-schema compatibility is
performed.

All public legacy production entrypoints fail closed with
`LegacyStageRetiredError` before reading historical inputs, checking readiness,
or generating output. The legacy check script is read-only and validates only
the shared retirement policy, registry, and tracked successor path. It does not
regenerate the historical CSV, JSON, manifest, or summary artifacts.

- `legacy_stage_retired=true`
- `legacy_stage_executable=false`
- `historical_artifacts_read_only=true`
- `legacy_artifact_regeneration_forbidden=true`
- `ready_for_training=false`
- `ready_to_train_now=false`
- `feature_semantics_audit_required_before_training=true`
- `recommended_next_step=covapie_sample_index_materialization_smoke`
