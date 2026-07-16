# CovaPIE Step14AU-E1-A summary

This design gate freezes the V1 residue-identity and atom-name semantics needed by a future ADMIT_004 successor integration. It does not implement an ADMIT_004 evaluator, alter the effective admission schema, or materialize candidate records.

## Frozen semantics

- Residue names are exact Python strings using the frozen component grammar `^[A-Za-z0-9]{1,32}$`. Valid inputs are canonicalized to uppercase, so `CYS`, `cys`, and `Cys` canonicalize to `CYS`; whitespace, missing markers, empty values, non-ASCII values, and non-strings are invalid.
- Locator namespace is exact lowercase `auth` or `label`. Chain and index are exact, non-empty ASCII lexical strings; they are not trimmed or coerced, and an index is never converted to an integer.
- Candidate chain and index must be one complete pair from the selected namespace. A complete selected pair may pass when the other namespace differs; the difference is recorded as an auth/label conflict. Mixed or mismatched pairs are invalid.
- The V1 atom-name contract accepts only exact `SG`. Case repair, whitespace repair, element names, and aliases are rejected.
- Provenance source IDs preserve the P2 grammar exactly: `^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$`. They are exact Python strings of length 1–256 with no trimming or coercion; SHA evidence remains exact lowercase 64-hex.
- ADMIT_004 identity grammar remains separate from ADMIT_005 Cys/SG scope. A valid non-CYS component passes the ADMIT_004 identity grammar and is rejected by ADMIT_005.
- Effective outcome priority is `invalid > rejected > blocked > passed`. Valid identity with `unknown` and empty insertion evidence remains blocked by `COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN`; it is not promoted to absent.

## Frozen evidence

The source boundary is the exact ordered set of 22 committed sources recorded in the contract and manifest. All structural checks complete before the first source byte is read; CSV and JSON documents are parsed only from the frozen in-memory bytes.

The fixed truth table contains 16 cases and all 16 pass. Case 10 now explicitly constructs candidate `A/7` from auth chain `A` and label index `7`, while the complete auth and label pairs are `A/42` and `L/7`; case 11 remains the independent ordinary selected-namespace mismatch. The exact11 audit uses a keyed `binding_row_id` join over P6-A, P6-C, and P6-D evidence in canonical binding order. All 11 rows have canonical residue `CYS`, exact candidate and matched atom `SG`, namespace `auth`, valid selected auth pairs, ADMIT_005 scope `passed`, and effective outcome `blocked`. The auth/label conflict split is 3 conflict and 8 no-conflict rows.

The P6-D issue inventory remains 11 open blocking issues. `COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED` and `COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED` transition only to `design_frozen_pending_successor_integration`; every other issue remains `unchanged_open`, including 11 `REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT` rows.

## Readiness boundary

The design is ready only for `integrate_covapie_admit_004_residue_identity_and_atom_name_semantics_v1`. Residue and atom-name semantics are not integrated into the effective schema, ADMIT_004 rule logic is not ready, candidate records do not exist, and real candidate evaluation, bulk download, and training remain disallowed. A feature-semantics audit remains mandatory before formal training; the historical Step12D smoke legality check is not a final training-feature contract, and the historical `UNKNOWN_ATOM_FEATURE_POLICY` / `feature_semantics_known=False` state remains subject to that audit.

No raw path was read, no parser or provider was called, no checkpoint was accessed, and no model, forward, loss, dataloader, optimizer, or training code was modified or executed.
