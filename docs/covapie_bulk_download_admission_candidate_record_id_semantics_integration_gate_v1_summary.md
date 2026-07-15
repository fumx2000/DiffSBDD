# CovaPIE Candidate Record ID Semantics Integration Gate v1

Step14AU-C2 is a deterministic, metadata-only successor overlay. It reads the
six committed Step14AU-B2 effective-view outputs and the six committed
Step14AU-C1 design outputs. It does not follow artifact references or inspect
raw structures.

The overlay applies the frozen C1 candidate record ID contract to exactly three
B2 rows:

- `ADMIT_001`
- the `candidate_record_id` field
- the `candidate_record_id_contract` evaluation context

All other rule, field, and context rows remain field-for-field identical to
Step14AU-B2. The successor issue inventory removes only
`CANDIDATE_RECORD_ID_SEMANTICS_UNRESOLVED`, reducing the blocker count from 12
to 11. PDB identifier semantics remain integrated.

Candidate record IDs are record keys. This step does not resolve the separate
duplicate identity key contract, materialize candidate records, execute real
admission, create a download queue, download data, or authorize training.
Overall evaluator rule logic is therefore not ready.

The canonical mask set remains exactly:

1. `warhead_only` / `A`
2. `linker_plus_warhead` / `B`
3. `scaffold_plus_warhead` / `B2`
4. `scaffold_only` / `B3`
5. `scaffold_plus_linker_plus_warhead` / `C`

Real candidate evaluation, bulk download, training, fine-tuning, and parameter
updates remain prohibited. A feature semantics audit is still required before
formal training.
