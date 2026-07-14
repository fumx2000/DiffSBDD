# CovaPIE PDB Identifier Semantics Integration Gate v1

Step14AU-B2 is a read-only successor overlay. It copies the committed
Step14AU-A admission-precondition metadata and applies the committed Step14AU-B1
PDB syntax contract only to `ADMIT_002`, `pdb_id`, and
`pdb_id_format_contract`.

The overlay closes `PDB_ID_FORMAT_SEMANTICS_UNRESOLVED` in its effective view.
The historical Step14AU-A files remain unchanged. The other twelve semantic
blockers remain domain blockers, not B2 implementation failures.

`evaluate_admit_002_pdb_identifier` only validates and canonicalizes syntax. It
does not claim archive existence, access raw data, evaluate candidates, or
grant download or training permission.

Normal B2 readiness permits future evaluator-interface implementation, but not
overall admission rule logic, candidate evaluation, bulk download, training,
fine-tuning, or parameter updates. Feature semantics audit remains required
before formal training.

The canonical masks remain exactly `warhead_only/A`, `linker_plus_warhead/B`,
`scaffold_plus_warhead/B2`, `scaffold_only/B3`, and
`scaffold_plus_linker_plus_warhead/C`.
