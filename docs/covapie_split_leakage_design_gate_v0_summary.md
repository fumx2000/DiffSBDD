# CovaPIE Split Leakage Design Gate v0 Retirement Summary

`covapie_split_leakage_design_gate_v0` is retired and superseded. Its historical derived root remains unchanged, read-only evidence. It is non-executable, non-canonical, and no longer supplies current pipeline admission evidence.

The tracked canonical successor is `covapie_leakage_split_design_gate_v0`, with manifest `data/derived/covalent_small/covapie_leakage_split_design_gate_v0/covapie_leakage_split_design_gate_manifest.json`.

All public legacy execution entrypoints fail closed with `LegacyStageRetiredError` before filesystem reads, artifact generation, manifest construction, readiness checks, or calls along the old split/leakage chain. The check script is read-only and validates only the shared retirement registry, exact successor contract, tracked successor paths, and training boundary. It never regenerates the old split/leakage artifacts.

- `successor_availability=tracked`
- `historical_artifacts_read_only=true`
- `legacy_artifact_regeneration_forbidden=true`
- `ready_for_training=false`
- `ready_to_train_now=false`
- `feature_semantics_audit_required_before_training=true`
- `recommended_next_step=covapie_leakage_split_design_gate`
