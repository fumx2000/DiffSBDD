# CovaPIE Step14AU-E1-E4 Phase 2 summary

This phase implements the minimal unified admission dispatch shell. It is a
single-rule runtime, not the completed unified rule engine.

## Implemented boundary

- `UnifiedAdmissionRuleEvaluation` is a frozen Exact13 dataclass with schema
  version `covapie_unified_admission_rule_evaluation_v1`.
- `UnifiedAdmissionDispatchError` is a frozen Exact6 exception dataclass. Its
  exception arguments are initialized so `str(error) == error.reason`.
- `evaluate_admission_rule` evaluates exactly one requested rule.
- The immutable runtime registry contains exactly one entry: `ADMIT_004`,
  `covalent_residue_identity_present`.
- ADMIT_001 through ADMIT_003 fail closed as callable-discovered rules whose
  adapter contracts are not ready.
- ADMIT_005 through ADMIT_015 fail closed as known, unregistered rules.
- Unknown IDs and non-exact-string IDs fail closed before context validation.

## ADMIT_004 routing and adapter

ADMIT_004 requires `batch_context`, `download_result_context`, and
`stage_authorization_context` to be `None`. `evaluation_context` must be a
`Mapping`; the same object is passed through to the standalone evaluator.
Validation order is batch, evaluation, download result, then stage
authorization.

Mapping candidate inputs are projected to the standalone exact nine fields in
the standalone field order. Existing values are passed without trimming,
coercion, normalization, or copying, and extra candidate fields are excluded.
A non-Mapping candidate is passed through so the standalone evaluator can
return its `invalid` rule result. The original candidate and context are not
mutated.

The adapter requires an exact `Admit004EvaluationResult`, validates its rule
ID, outcome and boolean invariants, no-IO claim, and exact consumed-field
tuple, and maps it to the frozen unified result with adapter ID
`covapie_admit_004_unified_adapter_v1`. An adapter invariant failure raises a
dispatch error and never returns a partial result.

## Evidence and readiness

The materializer verifies the ordered Exact12 committed sources. It completes
all source structure checks before the first source-byte read, compares the
expected, base-tree, and filesystem SHA256 values, parses CSV/JSON/Python AST
only from the frozen snapshot bytes, and does not recursively open artifact
references.

The synthetic dispatch truth matrix contains exactly 24 unique cases:

- 3 passed
- 4 blocked
- 3 invalid rule results
- 14 dispatch errors

The registry audit contains exactly 15 ordered rules. The Phase 1 issue
inventory is copied field-for-field with all 12 issues still active; the real
provider blocker remains open/blocking with count 11.

The minimal single-rule dispatch shell is ready, and only ADMIT_004 is
registered. ADMIT_001 through ADMIT_003 adapters are not implemented.
ADMIT_005 through ADMIT_015 are not registered. No all-rules evaluation,
combined candidate verdict, cross-rule aggregation, or cross-rule precedence
is implemented. No real candidate or Exact11 evaluation was performed.

Bulk download and training remain forbidden. Step12D remains only a smoke
legality check, not a final training-feature contract. A feature-semantics
audit, including formal resolution or audit of the historical
`UNKNOWN_ATOM_FEATURE_POLICY` and `feature_semantics_known=False` state, is
required before formal training or any parameter updates.

Recommended next step:
`design_covapie_unified_admission_legacy_evaluator_adapter_contracts_for_admit_001_to_003_v1`.
