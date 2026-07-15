# CovaPIE Step14AU-E0-P3 Summary

Step14AU-E0-P3 creates a deterministic, metadata-only successor admission
schema with 22 candidate fields. It reads only the six committed Step14AU-D2
outputs and six committed Step14AU-E0-P2 outputs. It does not follow artifact
references or read raw structures and checkpoints.

## Schema Transition

All 17 D2 field rows are retained byte-for-byte at the row level. The following
five fields are appended in this fixed order:

1. `covalent_residue_locator_namespace`
2. `covalent_residue_insertion_code_state`
3. `covalent_residue_insertion_code`
4. `covalent_residue_locator_provenance_source_id`
5. `covalent_residue_locator_provenance_sha256`

Only `ADMIT_004` changes, and only its candidate-field dependencies and three
integration-lineage columns change. Its semantics, readiness, implementation
disposition, and two blockers remain unchanged. The other 14 rule rows are
preserved field-for-field.

All 18 evaluation-context rows remain unchanged. The domain issue inventory
also remains the same 10-row D2 inventory. The P2 internal
`COVALENT_RESIDUE_LOCATOR_EXTENSION_NOT_YET_INTEGRATED` issue is resolved by
this successor view, while
`COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_NOT_YET_EXPORTABLE` remains open.

## Boundaries

The integration is not a data backfill. The 11 existing samples still have
unknown insertion-code provenance, and zero samples are fully provable before
download. A real candidate metadata provider has not populated the five new
fields, and parser insertion-code support has not been implemented.

`ADMIT_004` remains not ready. E1 residue identity semantics remains not ready,
and atom-name normalization remains an independent blocker. The canonical mask
set remains exactly `warhead_only/A`, `linker_plus_warhead/B`,
`scaffold_plus_warhead/B2`, `scaffold_only/B3`, and
`scaffold_plus_linker_plus_warhead/C`.

No candidate evaluation, queue materialization, bulk download, model access,
or training is authorized. Formal training, fine-tuning, or real parameter
updates still require a separate feature semantics audit.
