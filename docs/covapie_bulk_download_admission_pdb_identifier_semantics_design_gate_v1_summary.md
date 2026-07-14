# CovaPIE PDB Identifier Semantics Design Gate V1

Step14AU-B1 freezes syntax-only PDB identifier semantics for a future
admission evaluator. It accepts legacy four-character IDs and twelve-character
extended IDs, then canonicalizes valid values to lowercase extended form.

Legacy conversion is exactly `pdb_0000 + legacy.lower()`. For example, `1ABC`
becomes `pdb_00001abc`. Extended input accepts mixed ASCII case and is
canonicalized to lowercase.

The contract does not trim whitespace and accepts ASCII only. Syntax validation
does not establish archive existence, coordinate availability, withdrawal
status, or download readiness. The gate does not use network access, download
data, or read raw structures.

The normalization examples include real tab and newline inputs. Their CSV
representations are escaped only for display, and every example must pass the
exact fail-closed validator. The manifest lists all five CSV outputs plus
itself, while `output_sha256` records only the five non-manifest files.

This gate resolves only `PDB_ID_FORMAT_SEMANTICS_UNRESOLVED` as a frozen design
contract. The other twelve Step14AU-A blockers remain unresolved. It does not
authorize evaluator rule logic, real candidate evaluation, bulk download,
training, fine-tuning, or parameter updates. Feature semantics audit remains
required before training.
