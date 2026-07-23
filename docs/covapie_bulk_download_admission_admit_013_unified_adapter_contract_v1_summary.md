# CovaPIE ADMIT_013 unified adapter contract design v1

This design-only stage freezes the future ADMIT_013 adapter without defining
`_evaluate_registered_admit_013`, changing `EVALUATOR_REGISTRY`, or modifying
the current ADMIT_001–ADMIT_012 runtime. It performs no provider mapping,
network access, download, raw-data access, model/checkpoint/dataloader work,
training, combined candidate verdict, or cross-rule aggregation.

## Identity and lifecycle

- Rule: `ADMIT_013` / `download_failure_fail_closed`
- Adapter: `covapie_admit_013_unified_adapter_v1`
- Formal evaluator/result: `evaluate_admit_013` / `Admit013EvaluationResult`
- Independent oracle/result: `classify_admit_013_formal_evaluator_interface_design` / `Admit013EvaluationResultContractDesign`
- Future handler name: `_evaluate_registered_admit_013` (not implemented here)
- Evidence runtime: CPython 3.10.4; every artifact-build entry point, including
  a caller-supplied prebuilt state, and the checker reject all other runtimes
- Base: `da7bf5258365ecebde20ba1f09081b075312ebaf`
- Source boundary: fixed ordered Exact19 inputs must be tracked in the current
  index and match the committed base-tree blobs; pinned no-follow reads verify
  the lexical root, parent chain, and leaf again after every read
- Candidate lifecycle: all Exact10 untracked before commit or all Exact10 tracked after a descendant commit; mixed/staged/dirty/missing/ignored/extra states fail closed
- Exact6 verification: the checker freezes every leaf's full identity before
  traversal, then rechecks the root, exact inventory, and all leaf identities
  after the complete traversal
- Publisher verification: both existing-set reuse and successful rename verify
  the destination name-to-inode binding, parent/root identities, Exact6
  inventory, and full leaf identities before reporting success

## Five-envelope routing

The future signature has `candidate_record` plus keyword-only
`batch_context`, `evaluation_context`, `download_result_context`, and
`stage_authorization_context`. The exact precedence is:

1. `batch_context_must_be_none`
2. `evaluation_context_mapping_validation`
3. `download_result_context_mapping_validation`
4. `stage_authorization_context_must_be_none`
5. `candidate_record_mapping_validation`
6. `download_result_exact4_required_lookup_first_missing_stops`
7. `integrity_authority_exact3_optional_lookup_all`
8. `formal_evaluator_exactly_once`
9. `standalone_source_exact12_validation`
10. `independent_design_oracle_exactly_once`
11. `full_exact12_exact_type_value_equality`
12. `typed_to_string_exact13_projection`

Batch and stage authorization must be exact `None`. Evaluation and download
contexts must be `Mapping` instances. A non-Mapping candidate is not a
dispatch exception: it returns an invalid, blocking Exact13 result with reason
`ADMIT_013_CANDIDATE_RECORD_MAPPING_INVALID`, four empty tuple fields, false
evaluator I/O, and zero formal/oracle/candidate-key calls.

Context failures use `UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID` with
`known_rule=true`, `callable_discovered=true`, and `adapter_ready=true`.
Envelope reasons are `ADMIT_013_BATCH_CONTEXT_MUST_BE_NONE`,
`ADMIT_013_EVALUATION_CONTEXT_MAPPING_REQUIRED`,
`ADMIT_013_DOWNLOAD_RESULT_CONTEXT_MAPPING_REQUIRED`, and
`ADMIT_013_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE`. Non-`KeyError` lookup
failures use `ADMIT_013_DOWNLOAD_RESULT_CONTEXT_LOOKUP_FAILED` or
`ADMIT_013_EVALUATION_CONTEXT_LOOKUP_FAILED`.

## Exact4 and Exact3 lookup

The adapter performs ordered `__getitem__` lookups for
`download_result_status`, `observed_http_status`,
`observed_content_length_bytes`, and `observed_sha256`. A first `KeyError`
omits that keyword, stops later Exact4 lookups, skips all authority lookups,
and still calls the formal evaluator once so its private default produces the
committed missing reason. The adapter neither imports nor injects the private
missing sentinel and never substitutes `None`.

Only after Exact4 is complete, it looks up all three optional authority keys:
`expected_content_length_bytes`, `expected_sha256`, and
`explicit_integrity_verdict`. A `KeyError` omits that keyword and continues to
later authority keys. Every present object is forwarded by identity.

## Exact12 validation and oracle equivalence

The formal evaluator is called exactly once. Its result must be the exact
`Admit013EvaluationResult` type with exact dataclass/storage order, exact
top-level types, successful reconstruction, the frozen outcome/reason and pair
invariants, and `evaluator_io_used=false`. A wrong type produces
`ADMIT_013_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID`; all other source, oracle,
storage, type, invariant, or equality failures produce
`ADMIT_013_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID`. Both use
`UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY` and set `adapter_ready=false`.

After source validation, the committed Design oracle is called exactly once
with the same kwargs. Its exact Design result is converted to formal Exact12,
then every field is compared for exact type, value, and order before any
projection.

## Exact12 to shared Exact13

The shared Exact13 schema is unchanged. `normalized_values` contains canonical
download observations in Exact4 order followed by provided-valid authority
pairs in Exact3 order. Exact integers become canonical decimal `str(value)`;
exact strings remain unchanged. Subclasses and booleans are rejected.

The shared field names are historical:

- `validated_candidate_fields` carries validated download-result observation string pairs only.
- `consumed_candidate_fields` carries consumed download-result observation names.
- Neither field implies any `candidate_record` sourcing; candidate key access is always zero.
- `consumed_context_items` carries consumed integrity-authority lookup names.
- Authority pairs appear in `normalized_values`, never in `validated_candidate_fields`.

## Registry and readiness

The current order remains `ADMIT_001` through `ADMIT_012`. The future order,
future callable-discovered IDs, and future adapter-ready IDs append
`ADMIT_013`, while `ADMIT_014` and `ADMIT_015` remain known but unregistered.
The first twelve handler object identities must be preserved.

The contract, Exact4/Exact3 routing, Exact12-to-Exact13 projection, and future
runtime readiness are frozen. The adapter itself, registration, and the
ADMIT_001–ADMIT_013 runtime remain unimplemented. Provider mapping, real
evaluation/download readiness, combined verdict, aggregation, and training
readiness remain false. Step12D remains only a smoke-legality check; a
feature-semantics audit is still required before training.

Recommended next step:
`implement_covapie_unified_dispatch_runtime_with_admit_001_to_013_v1`.
