# CovaPIE Dataloader Smoke Design Gate v0 Retirement Summary

`covapie_dataloader_smoke_design_gate_v0` is retired and non-executable. Its
inputs belong to the retired legacy dataloader-interface QA and 20x35/20x45
preview lineage. That lineage is not the current canonical 33-field final
dataset contract.

The historical root under
`data/derived/covalent_small/covapie_dataloader_smoke_design_gate_v0` remains
read-only evidence. It must not be regenerated, rewritten, or migrated through
schema aliases or dual validators. The check script validates retirement policy
only and does not execute the historical producer or read its artifacts.

No canonical dataloader replacement is created here. Successor availability is
`redesign_pending`; `superseded_by_stage` and
`superseded_by_manifest_path` are both `None`. The recommended next step is
`covapie_final_dataset_qa_gate_v1`.

The downstream metadata-dataloader stages and the remaining S2-S8 admission
chain are not retired by this change. In particular, the S5-S8 feature
semantics evidence still requires an explicit re-anchor before any retirement
decision.

The stage remains unavailable for training:

- `legacy_stage_retired=true`
- `legacy_stage_executable=false`
- `historical_artifacts_read_only=true`
- `legacy_artifact_regeneration_forbidden=true`
- `ready_for_training=false`
- `ready_to_train_now=false`
- `feature_semantics_audit_required_before_training=true`
