# CovaPIE Step14AU-E1-E2 summary

Step14AU-E1-E2 integrates the frozen Step14AU-E1-E1 generic atom identity and
record-level identity evidence-context design into the effective bulk-download
admission view. It is a metadata-only reconciliation gate. It does not implement
`evaluate_admit_004`, execute a parser or provider, materialize candidate or
admission records, evaluate candidates, access raw data or provenance references,
download data, or open training.

## Frozen source boundary

The gate consumes exactly twelve committed outputs in their declared order: six
Step14AU-E1-D outputs followed by six Step14AU-E1-E1 outputs. Before reading any
source bytes, it verifies all twelve paths are tracked, regular non-symlink files
and regular blobs in base commit
`d7995cb28b616c2097ae8ee2fbd77dc3761a4a01`. It then requires the declared,
base-tree, and filesystem SHA-256 values to match. CSV and JSON are parsed only
from the resulting `FrozenSourceSnapshot` bytes; referenced provenance or artifact
paths are not opened recursively.

Any missing, untracked, symlinked, non-blob, hash-drifted, or base-tree-drifted
source fails closed with zero integrated counts, false integration readiness,
false `all_checks_passed`, and no success materialization.

## Direct predecessor validation

The E1-D effective view is required to contain 15 rules, 22 fields, 18 contexts,
and 9 active issues. Its complete/ready counts remain 7 rules, 12 fields, and 9
contexts. ADMIT_004 must still have its exact nine candidate dependencies, only
`covalent_residue_identity_contract` as evaluation context, and the historical
atom field contract `must be SG for v1 Cys scope`. The Exact11 remains 11 unknown,
empty, and effectively blocked rows with reason
`COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN`.

The E1-E1 design is required to have 28/28 passing contract rows, 36/36 passing
truth rows in groups 8/8/8/12, and 10 active issues. The generic atom, ADMIT_004 /
ADMIT_005 scope separation, evidence-context schema, exact-nine attestation
binding, and E1-C grammar reuse claims must be frozen; successor integration must
be ready while the pre-integration reconciled interface remains not ready.

## Authorized reconciliation

Only ADMIT_004 changes in the rule matrix. Its evaluation context becomes
`covalent_residue_identity_contract|covalent_residue_identity_evidence_context`;
the other fourteen rule rows remain byte-for-field equivalent to E1-D.

Only `covalent_residue_atom_name` changes in the field matrix. Its effective
source contract is:

`generic exact non-empty ASCII atom identity; whitespace and complete dot/question markers forbidden; exact-preserve; no semantic maximum`

The field remains a candidate-record field depended on by ADMIT_004 and ADMIT_005.
`normalization_defined=true` means explicit no-normalization/exact preservation.
The other twenty-one field rows remain unchanged.

The context matrix inserts exactly one row immediately after
`covalent_residue_identity_contract`:
`covalent_residue_identity_evidence_context`, scoped as
`evaluation_record_evidence`, supplied by the future caller for ADMIT_004, with no
filesystem or network access inside the evaluator. All original eighteen context
rows remain unchanged.

The integration removes only
`ADMIT_004_GENERIC_ATOM_AND_EVIDENCE_CONTEXT_SEMANTICS_UNRESOLVED`. The remaining
nine issues are unchanged from both E1-E1 and E1-D. In particular,
`REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT` remains open, blocking, and count 11.

## Effective counts and readiness boundary

The reconciled view contains 15 rules, 22 fields, 19 contexts, and 9 active
issues. Its complete/ready counts are 7 rules, 12 fields, and 10 contexts. Generic
atom semantics, ADMIT_004/ADMIT_005 scope separation, the record evidence context,
and exact-nine candidate attestation binding are integrated. The reconciled
ADMIT_004 rule-logic interface is ready for implementation; ADMIT_005 remains
rule-logic ready.

The ADMIT_004 evaluator and unified rule engine remain unimplemented. Parser quote
roundtrip and real-provider present-value roundtrip remain unverified, provider
blocking rows remain unresolved, and candidate records remain unmaterialized.
Real candidate evaluation, bulk download, and training remain closed. A feature
semantics audit is still required before training; Step12D remains only a smoke
legality check, not a final training-feature contract.

The recommended next step is
`implement_covapie_admit_004_rule_logic_interface_v1`.

## Materialization path safety

Before the first output byte is written, the formal materializer uses `os.lstat`
to require the output root to be a real, non-symlink directory and to inspect
every existing entry. It rejects extra names and rejects any legal output name
that is a symlink or non-regular entry without deleting, overwriting, or repairing
it. A newly created output root is checked again before entry preflight.

Each output is written through a temporary regular file in the destination
directory, flushed and synchronized with `os.fsync`, and installed with atomic
`os.replace`; residual temporary files are removed in `finally`. Consequently,
an output-name symlink is never followed to overwrite an external victim, all
unsafe entries are rejected before any other output is changed, and successful
repeated materialization leaves no `.tmp` or `.part` files.

## Deterministic outputs

- `covapie_admit_004_generic_atom_identity_evidence_context_reconciled_rule_matrix.csv`: `bcc794debeb4d8287d06db9891dd7f0c085e0cc96ba50b14b8b34d3e768ff676`
- `covapie_admit_004_generic_atom_identity_evidence_context_reconciled_field_matrix.csv`: `3b9783910012c4910491a05cb7936fe425d86e7dea9d42d774e2c794228a8177`
- `covapie_admit_004_generic_atom_identity_evidence_context_reconciled_context_matrix.csv`: `26e6eac422d00805aaad336024c2ec9d75038620e280c8d48fa89ef60a451cd1`
- `covapie_admit_004_generic_atom_identity_evidence_context_integration_safety_audit.csv`: `ae5d266cf6ca0369ab8da08b529d7e9b89ba169ffd903abff1009ecc9d00623c`
- `covapie_admit_004_generic_atom_identity_evidence_context_integration_issue_inventory.csv`: `7cf0a9ff421ba987655c4dac4564c04dbaa854cd4f725b18136642f223762d30`
- `covapie_admit_004_generic_atom_identity_evidence_context_reconciliation_integration_manifest.json`: `3c03b711e74fd023be187b64a757e69f8fc03bcb1af19c88325e7fdeb226012d`
