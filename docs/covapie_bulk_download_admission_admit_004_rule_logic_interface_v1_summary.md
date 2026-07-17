# CovaPIE ADMIT_004 rule-logic interface v1

Step14AU-E1-E3 implements the standalone public function
`evaluate_admit_004(candidate_record, evaluation_context)` as deterministic,
pure in-memory rule logic. It returns the frozen ten-field
`Admit004EvaluationResult` and consumes the canonical exact-nine candidate
field tuple in its frozen order.

The evaluator validates candidate syntax, canonicalizes only the residue name
to uppercase after validating its raw value, binds evidence attestations to all
nine original candidate values before canonicalization, and enforces the
frozen `invalid > blocked > passed` outcome precedence. ADMIT_004 accepts a
valid generic atom identity; CYS/SG scope remains the responsibility of
ADMIT_005.

The synthetic truth matrix contains exactly 50 unique evaluator executions:
6 passed, 7 blocked, 19 candidate-invalid, and 18 context-invalid. All 50 pass.
The exact12 committed source boundary and its expected/base-tree/filesystem
SHA256 values are verified before evidence parsing, with all structural checks
completed before the first source-byte read.

The nine E1-E2 active issues are preserved field-for-field and in their
original order. `REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT` remains open and
blocking with count 11. Exact11 is retained only as the frozen metadata
invariant: count 11, expected blocked count 11, and reason
`COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN`; no real Exact11 row was
evaluated.

The materializer preflights the complete output directory before its first
write, rejects symlink and non-regular entries without modifying their targets,
and writes each file through a same-directory temporary file using flush,
`fsync`, and atomic replacement. Consecutive materializations are
byte-identical and leave no `.tmp` or `.part` entries.

This step makes the standalone evaluator ready for future unified-engine
integration. It does not integrate that engine, read raw data, dereference
provenance artifacts, execute a parser/provider, materialize candidate or
admission records, evaluate real candidates, download data, access checkpoints,
or perform model/training work. Candidate evaluation, bulk download, and
training remain prohibited. A feature-semantics audit remains mandatory before
formal training; Step12D remains a smoke legality check rather than a final
training-feature contract.

Recommended next step:
`integrate_covapie_admit_004_rule_logic_interface_into_unified_engine_v1`.
