# CovaPIE Step14AU-E1-D summary

## Scope

This metadata-only successor gate integrates the insertion present-value grammar frozen by Step14AU-E1-C into the effective admission matrices produced by Step14AU-E1-B. It does not implement ADMIT_004, execute a parser or provider, read raw structures, materialize candidate/admission records, download data, access checkpoints, or use model/training code.

## Frozen source boundary

The production gate reads exactly twelve committed artifacts in fixed order: the six E1-B effective admission outputs followed by the six E1-C grammar-design outputs. Before reading source content, it verifies that all twelve paths are safe relative paths, tracked, base-tree blobs, filesystem regular files, and non-symlinks. Expected, base-tree, and filesystem SHA256 values must agree. CSV and JSON parsing uses only the resulting in-memory `FrozenSourceSnapshot`; artifact references are not followed recursively.

Any source-boundary or predecessor-evidence failure yields zero integrated counts, false integration readiness, and false `all_checks_passed`. A failed run creates no success outputs.

## Effective overlays

- The 15-row rule matrix preserves its E1-B header and order. Only `ADMIT_004` changes: its semantics and deterministic rule logic become ready, its identity blocker is cleared, and E1-C is recorded as the integration source. This means a complete candidate record can deterministically yield passed, blocked, or invalid; it does not mean the real Exact11 rows pass.
- The 22-row field matrix preserves its E1-B header and order. Only `covalent_residue_insertion_code` changes. Its state/value contract, exact nonempty PDBx/mmCIF present-value grammar, exact-preserve/no-normalization policy, and exact validation become implementation-complete. The other four locator fields are byte-for-field unchanged.
- The 18-row context matrix preserves its E1-B header and order. Only `covalent_residue_identity_contract` changes to deterministic, exact, and implementation-ready.
- The issue inventory starts from the E1-C 10-row inventory and removes only `COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED`. The remaining nine rows retain their order and every field. `REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT` remains open, blocking, and count 11.

The resulting counts are rules/fields/contexts/issues `15/22/18/9`; complete/ready counts are `7/12/9`.

## Exact11 and readiness boundary

Exact11 remains 11 unknown insertion states with empty values, 11 insertion-blocked outcomes, and 11 effective blocked outcomes. The reason remains `COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN`; auth/label conflict and no-conflict counts remain 3 and 8. Unknown is never promoted to absent.

The effective insertion grammar, broad residue-identity contract, ADMIT_004 rule-logic readiness, ADMIT_005 rule-logic readiness, invalid-outcome fail-closed policy, and four-way exact-agreement policy are ready. The ADMIT_004 evaluator is not implemented. Parser quote-class roundtrip and real-provider present-value roundtrip remain unverified. Candidate records are not materialized, and real candidate evaluation, bulk download, and training remain disallowed.

The recommended next step is `implement_covapie_admit_004_rule_logic_interface_v1`; it is not implemented here. Formal training still requires a feature-semantics audit, including resolution or formal audit of the historical unknown atom-feature policy. Step12D remains only a smoke legality check, not a final training-feature contract.

## Outputs

The gate deterministically emits five CSV files and one JSON manifest. The manifest records exact12 lineage and verification, predecessor and integrated counts, resolved and remaining issues, Exact11 invariants, readiness boundaries, safety boundaries, output hashes for the five non-manifest outputs, and the recommended next step. It contains no timestamp, hostname, absolute path, or self-hash.
