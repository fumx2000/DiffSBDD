# CovaPIE unified ADMIT_001–ADMIT_004 runtime v1

Step14AU-E1-E4 Phase 4 adds a successor single-rule runtime without changing the Phase 2 runtime or the Phase 3 design gate.

## Runtime contract

- `evaluate_admission_rule` preserves the Phase 2 public signature.
- `UnifiedAdmissionRuleEvaluation` and `UnifiedAdmissionDispatchError` are imported and re-exported from Phase 2 with object identity preserved. Their Exact13 result fields, Exact6 error fields, and five error codes are unchanged.
- The immutable registry contains, in order, `ADMIT_001`, `ADMIT_002`, `ADMIT_003`, and `ADMIT_004`.
- `ADMIT_005`–`ADMIT_015` remain unregistered and fail closed with `UNIFIED_ADMISSION_RULE_NOT_REGISTERED`.
- No all-rules evaluator, combined candidate verdict, or cross-rule aggregation is implemented.

## Legacy adapters

ADMIT_001, ADMIT_002, and ADMIT_003 validate context routing before candidate projection. Candidate values and the ADMIT_001 batch object are forwarded by identity, extra candidate fields are excluded, and inputs are not mutated. Non-Mapping candidates and missing required fields return the six frozen adapter-side invalid payloads without calling either evaluator.

Each valid adapter path calls its committed legacy evaluator once, validates the exact `dict` type, ordered key set, rule ID, Boolean field, and string fields, then calls its independent pure semantic oracle once. The legacy result must equal the oracle-derived expected dictionary field by field. Source type, invariant/equivalence, and unmapped-reason failures return no partial result and fail closed with `UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY`.

ADMIT_004 delegates to the Phase 2 public runtime exactly once. Result identity from that delegation is retained, and direct Phase 2 and successor error fields are equal.

## Evidence boundary and outputs

The materializer freezes the ordered Exact14 source boundary at base commit `759f19b8e84d68a531b791ff683033812549ce80`. All 14 tracked/base-tree/filesystem structure checks complete before the first source-byte read. Expected, base-tree, and filesystem SHA256 values must match, and Python AST, CSV, and JSON documents are parsed only from frozen snapshot bytes.

The six deterministic outputs contain:

- 34 runtime contract rows;
- 56 unique synthetic truth cases: 8 passed, 4 blocked, 24 invalid rule results, and 20 dispatch errors;
- 15 ordered registry audit rows;
- the exact executed/not-executed safety inventory;
- 11 active issues, obtained only by removing `UNIFIED_ADMISSION_LEGACY_EVALUATOR_ADAPTER_IMPLEMENTATION_PENDING` from the Phase 3 Exact12 inventory;
- a fail-closed readiness manifest with no timestamp, absolute path, or manifest self-hash.

The provider blocker remains open and blocking with count 11. ADMIT_005–ADMIT_015 coverage, the unified 15-rule engine, combined verdict semantics, real candidate evaluation, bulk download, and training remain blocked. A feature-semantics audit is still required before formal training; Step12D remains only a smoke legality check, not a final training-feature contract.

Recommended next step: `audit_covapie_admit_005_formal_evaluator_interface_preconditions_v1`.
