# CovaPIE Step14AU-E1-B partial successor integration gate v1

This gate partially integrates the Step14AU-E1-A residue identity and exact
atom-name design into the Step14AU-E0-P3 effective admission matrices. It reads
exactly the six committed P3 outputs and six committed E1-A outputs. All source
paths are checked as tracked, regular, non-symlink files before the first source
byte is read; CSV and JSON documents are then parsed only from frozen in-memory
bytes with fixed SHA256 values from base commit
`b4a4f2e9385fd86d08ef69fc1cfb16bfa46e5377`.

The overlay preserves the 15-rule, 22-field, and 18-context shapes. It changes
only ADMIT_004 and ADMIT_005; the residue name, chain ID, residue index, and atom
name fields; and the `covalent_residue_identity_contract` context. The five
locator fields are byte-for-field identical to P3, including the incomplete
`covalent_residue_insertion_code` contract.

ADMIT_005 is ready because E1-A froze residue-name canonicalization and exact
`SG` semantics. ADMIT_004 remains not ready: the insertion-code present-value
grammar is not frozen, so the broad identity context remains incomplete. The
atom-name normalization issue is removed, while the identity issue is narrowed
to `covalent_residue_insertion_code` and ADMIT_004. The resulting counts are 15
rules, 22 fields, 18 contexts, 10 active issues, 6 complete rules, 11 complete
fields, and 8 ready contexts.

The E1-A Exact11 evidence remains unchanged: all 11 rows have valid frozen
identity and exact `SG` semantics and pass ADMIT_005 scope, but all 11 retain
unknown/empty insertion provenance and remain effectively blocked with
`COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN`. Unknown is never promoted
to absent.

This is metadata-only partial successor integration. It does not implement the
ADMIT_004 evaluator, create candidate or admission records, read raw structures,
run a parser or provider, access checkpoints, use model code, evaluate real
candidates, download data, or train. The next authorized design step is
`design_covapie_covalent_residue_insertion_present_value_grammar_v1`. A formal
feature-semantics audit remains required before training; historical Step12D
smoke legality must not be interpreted as a final training-feature contract.
