# CovaPIE Step14AU-E1-C insertion present-value grammar design gate v1

This metadata-only gate freezes the present-value lexical grammar for
`covalent_residue_insertion_code`, the exact `absent` / `present` / `unknown`
state-value combinations, exact-preservation policy, and the design for exact
`struct_conn` / `atom_site` agreement. It reads exactly 39 committed sources
from base commit `3aa53c1b06032b7dc93b3a14df4fe2374d8432fa`. Every source is verified as a
tracked base-tree blob and a current regular non-symlink file before any source
byte is read; expected base-tree and observed filesystem SHA256 values must
agree. CSV and JSON inputs are parsed only from the frozen in-memory snapshot.

The normative design constants are `PDBx/mmCIF V5`,
`_atom_site.pdbx_PDB_ins_code`, and the reference role
`_struct_conn.pdbx_ptnr1/2_PDB_ins_code references atom_site insertion code`.
The dictionary pattern is
`[][_,.;:"&<>()/\{}'\`~!@#$%A-Za-z0-9*|+-]*`; CovaPIE uses the same ASCII
character set with a nonempty `+` quantifier. Complete `.` and `?` values are
rejected outside the regex. Validation requires an exact `str`, rejects
subclasses, whitespace and non-ASCII input, uses compiled ASCII `fullmatch`,
and returns the input unchanged. It performs no trim, case-fold, coercion,
Unicode normalization, canonical rewrite, or semantic maximum-length check.

The generated unified example/truth table contains exactly 64 rows: 35 valid
present examples, 15 invalid present examples, and 14 state-value truth rows.
All 28 allowed punctuation characters are tested individually. A 4096-character
ASCII value is independently confirmed grammar-valid without embedding it in
the canonical CSV.

Every invalid state/value outcome blocks ADMIT_004 fail closed. The blocked
`unknown + ""` combination also blocks ADMIT_004 and is never promoted to
`absent`. Only the passed `absent + ""` and passed grammar-valid `present`
combinations do not block ADMIT_004.

A candidate present value requires explicit resolved evidence on both
`struct_conn` and `atom_site`, followed by four-way byte-for-byte exact equality
across the `struct_conn` value, `atom_site` value, candidate value, and
provenance value. The common exact value must also pass the present-value
grammar. No trimming, case-folding, normalization, coercion, one-sided
promotion, marker promotion, or conflict-side selection is allowed. Candidate
fields hold decoded exact values, not surrounding CIF quote delimiters.

The Phase 0 quote-class gap remains open: current P5-B logical values do not
reliably retain quoted versus unquoted lexical class. Accordingly,
`parser_quote_class_roundtrip_verified` and
`real_provider_present_value_roundtrip_ready` remain false. This gap does not
block freezing the candidate-value grammar, but this gate does not claim parser
or provider correctness.

All ten E1-B issues remain open. The residue identity issue is narrowed only by
the transition
`insertion_present_value_grammar_design_frozen_pending_successor_integration`;
it is not deleted. `REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT` remains blocking
with count 11. The E1-A Exact11 evidence is unchanged: 11/11 insertion states
remain `unknown` with empty values, 11/11 block ADMIT_004 with
`COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN`, and the auth/label
conflict split remains 3/8.

The gate is ready only for
`integrate_covapie_covalent_residue_insertion_present_value_grammar_v1`. The
grammar is not integrated into the effective schema, ADMIT_004 rule logic is
not ready, and no evaluator or candidate records exist. Real candidate
evaluation, bulk download, and training remain disallowed. A feature-semantics
audit remains required before formal training; Step12D smoke legality is not a
final training-feature contract.
