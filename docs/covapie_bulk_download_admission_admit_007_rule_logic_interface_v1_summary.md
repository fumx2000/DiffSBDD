# CovaPIE ADMIT_007 standalone evaluator interface v1

## Scope and result

This increment implements the standalone, pure-in-memory ADMIT_007 evaluator:

```python
evaluate_admit_007(
    covalent_event_evidence_source: object,
    allowed_covalent_evidence_classes: object,
) -> Admit007EvaluationResult
```

Both arguments are required. The interface accepts a direct scalar and direct
context only. It does not accept candidate or evaluation-context mappings and
does not implement an adapter, registry entry, runtime route, provider mapping,
real-candidate evaluation, download, or training behavior.

`Admit007EvaluationResult` is a frozen dataclass with these exact ordered fields:

1. `admission_rule_id`
2. `outcome`
3. `passed`
4. `blocks_candidate`
5. `reason`
6. `canonical_covalent_event_evidence_source`
7. `validated_candidate_fields`
8. `consumed_candidate_fields`
9. `consumed_context_items`
10. `evaluator_io_used`

Direct construction fails closed unless all types and cross-field semantic
invariants agree. The result always consumes
`("covalent_event_evidence_source",)` and
`("allowed_covalent_evidence_classes",)`, and `evaluator_io_used` is exact
`False`.

## Frozen semantics

The canonical Exact3 enumeration is, in order:

1. `explicit_structure_bond_record`
2. `explicit_curated_covalent_annotation`
3. `distance_only_inference`

The allowed Exact2 context is the exact tuple containing the first two members
in that order. Scalar validation precedence is exact built-in `str`, nonempty,
ASCII, syntax `[a-z][a-z0-9_]{0,63}`, then Exact3 membership. Context validation
independently requires an exact tuple and then exact member types, content, and
order. Evaluator precedence is scalar failure, context failure, then canonical
member classification.

Either explicit member passes with an empty reason. `distance_only_inference`
is blocked with `DISTANCE_ONLY_INFERENCE_NOT_ADMISSIBLE`. Malformed, unknown, or
context-invalid input is invalid with its exact validation reason. A valid
canonical scalar is retained and reported as validated even when context is
invalid; malformed or unknown scalar input has empty canonical and validated
state. No trimming, case conversion, aliasing, normalization, or repair occurs.

The historical lowercase registry reason
`distance_only_inference_not_admissible` is source evidence only and never
enters the standalone reason vocabulary. Candidate-key missing and
`covalent_event_evidence_missing` remain outside this direct-scalar interface.

## Independent truth and purity evidence

The materialized synthetic truth matrix executes the new evaluator over the
complete committed Exact37 predecessor corpus:

- canonical: 3
- scalar type: 6
- empty/syntax: 11
- unknown: 5
- context: 12

Expected semantics come from a separately implemented local oracle and are
cross-checked field-by-field against the committed
`classify_admit_006_admit_007_evidence_design` oracle. The new evaluator does
not call or import that classifier. AST transitive
call-graph checks constrain the evaluator closure to `evaluate_admit_007`,
`_validate_scalar`, `_validate_context`, and `_result`, and reject design-oracle,
materialization, filesystem, Git, subprocess, network, adapter, runtime, and
provider calls.

## Fixed committed-source boundary

The ordered minimal boundary contains 10 committed sources. All structural
checks finish before the first explicit source-byte read, documents are parsed
only from frozen snapshot bytes, and artifact-reference paths are not followed.

1. ADMIT_007 precondition manifest: readiness baseline.
2. ADMIT_007 Exact19 precondition matrix.
3. Evidence-source enum design source: normative Exact3/Exact2 definitions and oracle identity.
4. Evidence-source enum manifest: committed counts, precedence, readiness, and hashes.
5. Evidence-source truth matrix: complete committed Exact37 expectations.
6. ADMIT_006/ADMIT_007 responsibility matrix: explicit/distance ownership and reasons.
7. Current unified runtime source: literal Exact6 registry and absent ADMIT_007 registration.
8. Current Exact6 runtime manifest.
9. Current Exact6 runtime Exact11 issue inventory preservation baseline.
10. ADMIT_006 standalone source: established frozen-result/materialization structure.

Every path and SHA256 is frozen in the source-boundary output and manifest.

## Issue and readiness transition

The predecessor Exact11 issue order and schema are preserved.
`COVALENT_EVIDENCE_ENUM_UNRESOLVED` remains resolved and unchanged.
`UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE` remains open, but ADMIT_007 is
still present in its `affected_rules`, which remain ADMIT_007 through ADMIT_015. A
standalone evaluator without an adapter and runtime registration does not
complete unified-engine coverage. The complete issue inventory is preserved
byte-for-byte from the current Exact6 runtime predecessor.

Readiness is true only for the completed standalone result/scalar/context/reason
contracts, independent oracle and synthetic truth evidence, readiness for
ADMIT_007 adapter-contract design, and the mandatory pre-training feature
semantics audit. Adapter, runtime registration, ADMIT_008, all-rule coverage, provider,
real-evaluation, bulk-download, and training readiness remain false.

The recommended next step is
`design_covapie_admit_007_unified_adapter_contract_v1`. This increment stops
before that step.

## Training boundary

Before formal training, fine-tuning, training preparation, or any real parameter
update, a separate feature-semantics audit remains mandatory. Step12D was a smoke
legality check only, not a final training-feature contract. The historical
`UNKNOWN_ATOM_FEATURE_POLICY` and `feature_semantics_known=False` state must be
resolved or formally audited first.
