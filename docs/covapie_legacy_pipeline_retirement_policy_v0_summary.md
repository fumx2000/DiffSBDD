# CovaPIE Legacy Pipeline Retirement Policy Foundation v0

This foundation freezes the retirement policy for thirteen legacy Step13-style
sample-index, split/leakage, final-dataset, and dataloader-interface stages.
It is metadata-only policy code. It does not execute a legacy producer and it
does not read, rewrite, migrate, or regenerate historical derived artifacts.

The current sample-index contract has 33 fields. The current final-dataset
schema uses `final_dataset_field`. Legacy 31-field and 45-field contracts are
not accepted as aliases and are not migrated through dual-field validators.

All registered legacy stages are retired, non-executable, not ready for
training, and blocked from artifact regeneration. Historical artifacts remain
read-only evidence. A successful policy validation means that the retirement
contract is internally correct; it does not make a legacy stage executable.

Successor availability is restricted to `tracked`, `pending_commit`,
`not_materialized`, and `redesign_pending`. The registry contains four tracked
successor references that resolve to three unique manifest files. Legacy split
smoke and split QA intentionally share the Step14AQ unified leakage-split
manifest. Reference count and physical file count are therefore distinct.
Only tracked successor manifest paths receive an optional read-only filesystem
check. Manifest contents are not opened or parsed.

The tenth registry entry retires
`covapie_dataloader_smoke_design_gate_v0`. The eleventh and twelfth entries
retire `covapie_metadata_dataloader_smoke_v0` and
`covapie_metadata_dataloader_smoke_qa_gate_v0` atomically. S2 historically
constructed a plain Python shim by reading legacy 20x35 and 20x45 previews;
S3 directly instantiated that constructor and reused three S2 audit builders.
The thirteenth entry retires `covapie_actual_dataloader_design_gate_v0`.
S1 through S4 have no materialized successor, use `redesign_pending`, and point
callers to `covapie_final_dataset_qa_gate_v1`. Their historical artifacts remain
read-only and must not be regenerated. S5 through S8 are not retired by this
batch and their feature-semantics evidence still requires re-anchoring.

The tracked legacy final-dataset QA stage remains
`covapie_final_dataset_qa_gate_v0`. The future Step14AR-based canonical QA
stage is frozen as `covapie_final_dataset_qa_gate_v1`. This foundation does not
create QA v1 code or artifacts and does not modify the Step14AR manifest.

The policy does not access raw data, import model or dataloader runtime code,
create tensors, write training artifacts, or permit training. Feature semantics
audit remains required before formal training, fine-tuning, or real parameter
updates.
