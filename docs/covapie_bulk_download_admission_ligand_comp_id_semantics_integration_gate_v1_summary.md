# CovaPIE ligand component identifier semantics integration gate v1

Step14AU-D2 applies the frozen Step14AU-D1 `ligand_comp_id` contract to the
committed Step14AU-C2 effective view. The overlay changes only `ADMIT_003`, the
`ligand_comp_id` field, and the `ligand_comp_id_contract` evaluation context.
Every other rule, field, context, and remaining issue row is preserved exactly.

The integrated V1 contract accepts only an exact Python string containing 1 to
32 ASCII alphanumeric characters. Mixed-case input is normalized to uppercase;
no trimming, coercion, Unicode normalization, delimiter repair, or component-ID
generation is performed. A `ligand_comp_id` is one structure-local component
token. It is not SMILES, a chemical graph identity, or a duplicate identity
key. Passing syntax does not establish registry membership, raw-structure
presence, ligand class, drug-likeness, or training suitability.

D2 removes only `LIGAND_COMP_ID_SEMANTICS_UNRESOLVED` from the successor issue
inventory, reducing the effective blocker count from 11 to 10. Candidate record
ID and PDB identifier semantics remain integrated. The other ten domain
blockers remain unchanged, so overall admission evaluator rule logic is not
ready.

This metadata-only gate performs no external component-registry lookup, raw
structure traversal or read, candidate materialization, real admission
evaluation, queue generation, download, model execution, or training. The
canonical mask scope remains exactly `warhead_only / A`,
`linker_plus_warhead / B`, `scaffold_plus_warhead / B2`,
`scaffold_only / B3`, and `scaffold_plus_linker_plus_warhead / C`. Formal
training still requires a separate feature semantics audit.
