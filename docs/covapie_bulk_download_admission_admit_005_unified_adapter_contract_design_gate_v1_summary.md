# CovaPIE ADMIT_005 unified adapter contract design gate v1

This design-only gate freezes the future `ADMIT_005` unified adapter contract. It does not implement an adapter, extend `EVALUATOR_REGISTRY`, modify the Phase 4 runtime, implement `evaluate_all_rules`, or begin `ADMIT_006` work.

The production design gate is Python-standard-library-only. It does not import or execute the standalone evaluator, Phase 4 runtime, semantic-oracle module, or any other project module. All predecessor AST/CSV/JSON facts are parsed only from bytes in the structurally and cryptographically validated `FrozenSourceSnapshot`. Live predecessor execution and Phase 2 type-identity checks belong exclusively to tests and the checker.

## Frozen future identity

- Rule ID: `ADMIT_005`
- Rule name: `cys_sg_scope_only_v1`
- Adapter ID: `covapie_admit_005_unified_adapter_v1`
- Formal evaluator: `evaluate_admit_005`
- Future registry order: `ADMIT_001` through `ADMIT_005`
- Recommended next step: `implement_covapie_unified_dispatch_runtime_with_admit_001_to_005_v1`

The future implementation must reuse the existing Phase 4 public API and the Phase 2 `UnifiedAdmissionRuleEvaluation`, `UnifiedAdmissionDispatchError`, result schema, Exact13 result fields, Exact6 dispatch-error fields, and global outcome vocabulary by object identity.

## Execution contract

The fixed order is global rule-ID type validation, known-rule validation, registered/adapter-ready validation, the four context checks, candidate Mapping validation, required residue field, required atom field, one positional formal evaluator call, exact source validation, independent oracle derivation, Exact10 source/oracle equivalence, and Exact13 construction.

All four contexts are None-only in this order: batch, evaluation, download-result, and stage-authorization. A context failure is an Exact6 `UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID` dispatch error with `known_rule=true`, `callable_discovered=true`, and `adapter_ready=true`; no formal evaluator, oracle, or partial result is permitted.

Candidate projection uses `isinstance(candidate_record, Mapping)`. Mapping subclasses are accepted, extra fields are ignored, and the candidate is neither copied nor modified. The two required fields are `covalent_residue_name` then `covalent_residue_atom_name`; their original objects are passed positionally without trimming, uppercasing, coercion, or scalar prevalidation. Candidate envelope failures are Exact13 `invalid` results consuming both fields and no context, with no evaluator or oracle call.

## Source, oracle, and projection contract

The formal evaluator is called exactly once. Source handling is explicitly two-stage. Stage A validates exact `Admit005EvaluationResult` type, rejecting subclasses, followed by Exact10 field types/order, rule ID, consumed fields, no-I/O flag, and cross-field invariants. Stage A occurs before any oracle call; type or invariant failure therefore has scope-oracle and atom-oracle counts of zero.

Only after Stage A passes does Stage B independently call `classify_admit_004_admit_005_atom_scope_design` and `validate_generic_covalent_residue_atom_name` exactly once each with the original objects. The complete expected Exact10 result must equal the formal source before Exact13 construction. An oracle mismatch therefore has exact call counts `scope=1` and `atom=1`. The standalone production evaluator call graph remains independent and does not call these design-oracle helpers.

Wrong source type fails with `ADMIT_005_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID`. Source invariant or source/oracle mismatch fails with `ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID`. Both use `UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY`, set `adapter_ready=false`, and return no partial result.

Exact10 outcome, flags, reason, validated fields, consumed fields, and I/O flag pass through exactly. `normalized_values` equals `source.validated_candidate_fields`. Residue-invalid results contain no normalized/validated fields; atom-invalid results contain only canonical residue; passed and rejected results preserve residue-then-atom fields. `rejected` remains `rejected` and is never remapped to `blocked` or `invalid`.

## Evidence counts and readiness

- Contract: 46 unique frozen rows.
- Candidate/context routing matrix: 13 unique rows.
- Truth matrix: 43 unique cases: candidate envelope 7, context routing 5, standalone Exact22 projection 22, source fail-closed 7, boundary 2.
- Safety audit: 30 non-padding rows.
- Issue inventory: predecessor Exact11 copied without field or row changes.

The checker independently freezes SHA256 for all six materialized outputs, including the manifest, in `EXPECTED_OUTPUT_SHA256`. Direct disk hashes must match that constant in addition to dynamic payload and manifest validation.

The provider blocker remains open/blocking with count 11. Unified rule coverage remains open/blocking and still includes `ADMIT_005`; cross-rule aggregation semantics remain open/blocking.

The gate permits only readiness for the next adapter implementation step. The adapter is not implemented, `ADMIT_005` is not registered, Phase 4 is unchanged, real candidate and Exact11 evaluation were not performed, and bulk download and training remain forbidden. Step12D remains only a smoke legality check, not a final training-feature contract. A feature-semantics audit, including formal resolution or audit of historical unknown feature semantics, remains mandatory before training.
