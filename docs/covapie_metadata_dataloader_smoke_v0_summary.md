# CovaPIE Metadata Dataloader Smoke v0 Retirement Summary

`covapie_metadata_dataloader_smoke_v0` is a retired legacy stage. It and
`covapie_metadata_dataloader_smoke_qa_gate_v0` form one atomic retirement
unit because the QA gate directly instantiates this stage's artifact-backed
dataset shim and calls its historical audit builders.

`CovapieMetadataDatasetSmoke` is a plain Python compatibility class, not a
`torch` Dataset. Its historical constructor reads the legacy 20x35 interface
preview and 20x45 final-dataset preview, so construction now fails closed
before any path or CSV access. The class symbol, `__len__`, `__getitem__`,
constants, aliases, and historical helper symbols remain available only for
import and provenance compatibility.

The historical 20x30 preview and audit artifacts are retained read-only and
must not be regenerated, migrated, copied, or rewritten. This retirement does
not create a canonical dataloader or a replacement QA v1 stage. S4 through S8
remain unretired; their feature evidence still requires re-anchoring after the
canonical 33-field final-dataset QA contract is available.

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

Formal training, fine-tuning, and real parameter updates remain blocked.
