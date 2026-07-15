# CovaPIE ligand component identifier semantics design gate v1

Step14AU-D1 freezes the CovaPIE V1 meaning and validation contract for
`ligand_comp_id`. It is a single, structure-local PDBx/mmCIF-style chemical
component token supplied as candidate metadata. It is not a SMILES string,
chemical graph identity, `candidate_record_id`, duplicate key, PDB entry ID,
or ligand atom name.

The input must have exact Python type `str`, contain 1 through 32 ASCII
alphanumeric characters, and match `^[A-Za-z0-9]{1,32}$`. Accepted mixed-case
values are normalized to uppercase, so `JUG`, `jug`, and `JuG` have the same
component-token identity. Validation does not trim, coerce, apply Unicode
normalization, or repair malformed input. Whitespace, missing-value markers,
Unicode, delimiters, and multi-component encodings fail closed.

Passing this syntax contract does not prove that a component exists in an
external registry, occurs in a raw structure, is a non-polymer or drug-like
ligand, has the expected chemical graph, is downloadable, or is suitable for
training. D1 performs no registry lookup and reads no raw or referenced
artifact content.

D1 is design-only. It validates the six committed Step14AU-C2 metadata outputs
and freezes the contract needed by `ADMIT_003`, the `ligand_comp_id` field, and
the `ligand_comp_id_contract` context. It does not integrate that contract into
the C2 effective view. `ADMIT_003` remains not ready and
`LIGAND_COMP_ID_SEMANTICS_UNRESOLVED` remains an effective blocker. A future D2
integration is expected to reduce the issue count from 11 to 10, subject to its
own independent validation.

No candidate record or download queue is materialized, no download is
authorized, and real candidate evaluation remains disabled. Training,
fine-tuning, and real parameter updates remain prohibited. The canonical mask
scope remains exactly `warhead_only / A`, `linker_plus_warhead / B`,
`scaffold_plus_warhead / B2`, `scaffold_only / B3`, and
`scaffold_plus_linker_plus_warhead / C`; no sixth mask is added. A feature
semantics audit is still required before formal training.
