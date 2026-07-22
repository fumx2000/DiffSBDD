# CovaPIE ADMIT_012 formal evaluator interface contract v1

## Scope

This independent design stage freezes the future standalone ADMIT_012 evaluator interface and formal result contract. It is based on commit `727ef05f7e7bb4d7bda4eedd2ae0f3da2b4e993e` (`add CovaPIE ADMIT_012 download integrity field contract v1`) and a fixed Exact30 committed-source boundary.

The stage is design-only. It does not define `evaluate_admit_012` or the formal `Admit012EvaluationResult`; it does not implement a standalone evaluator, unified adapter, registry entry, dispatcher route, ADMIT_013, provider mapping, download execution, model/checkpoint operation, or training.

## Frozen routing and signature

The future adapter obtains only these scalars from `download_result_context`, in order:

1. `download_result_status`
2. `observed_http_status`
3. `observed_content_length_bytes`
4. `observed_sha256`

It obtains only these policy values from `evaluation_context`, in order:

1. `allowed_download_result_statuses`
2. `successful_http_status_contract`
3. `content_length_contract`
4. `sha256_format_contract`

`candidate_record`, `batch_context`, `stage_authorization_context`, filesystem, network, raw data, provider state, and download execution are forbidden sources. The standalone evaluator receives explicit scalar/context arguments, never a whole Mapping.

The future signature is frozen as:

```python
def evaluate_admit_012(
    *,
    download_result_status: object = _MISSING,
    observed_http_status: object = _MISSING,
    observed_content_length_bytes: object = _MISSING,
    observed_sha256: object = _MISSING,
    allowed_download_result_statuses: object,
    successful_http_status_contract: object,
    content_length_contract: object,
    sha256_format_contract: object,
) -> Admit012EvaluationResult
```

All parameters are keyword-only. The four field defaults share a future private singleton; the four contexts are required by the Python signature. Missing policy contexts are therefore caller/adapter routing failures, not result values.

## Exact policy context representations

All outer containers and every nested pair are exact built-in tuples. Keys and string values are exact built-in strings; integers and booleans are not interchangeable. Subclasses, aliases, normalization, mappings, regex objects, additions, omissions, duplicates, and reordering are rejected.

```python
allowed_download_result_statuses = ("success", "failure")

successful_http_status_contract = (
    ("legal_minimum", 100),
    ("legal_maximum", 599),
    ("future_success_minimum", 200),
    ("future_success_maximum", 299),
    ("admit_012_executes_success_judgment", False),
)

content_length_contract = (
    ("legal_minimum", 0),
    ("legal_maximum", None),
    ("zero_allowed", True),
    ("recomputed_from_file_inside_evaluator", False),
)

sha256_format_contract = (
    ("length", 64),
    ("grammar", "[0-9a-f]{64}"),
    ("case_policy", "ASCII_lowercase_only"),
    ("normalization_allowed", False),
    ("recomputed_from_file_inside_evaluator", False),
)
```

Each context has distinct `*_TYPE_INVALID` and `*_CONTENT_INVALID` reasons, yielding Exact8 context reasons. The closed full reason vocabulary is the empty string, the predecessor Exact12 field reasons, and these Exact8 context reasons.

## Exact10 result and invariants

The future formal result has this exact order:

1. `admission_rule_id`
2. `outcome`
3. `passed`
4. `blocks_candidate`
5. `reason`
6. `canonical_download_result_record`
7. `validated_download_result_fields`
8. `consumed_download_result_fields`
9. `consumed_context_items`
10. `evaluator_io_used`

The outcome vocabulary is `passed`, `blocked`, and `invalid`. Missing fields produce `blocked`; present but invalid fields and invalid contexts produce `invalid`; fully valid fields and contexts produce `passed`. A legal `failure` status and legal 4xx or 5xx HTTP status remain `passed` because success/download-integrity judgment belongs to future ADMIT_013.

The canonical record is either empty or an exact ordered Exact4 tuple of exact pair tuples. Validated fields are an ordered pair-tuple prefix excluding the failing field. Consumed fields and contexts report the exact prefixes actually read. Context failures retain the complete canonical and validated Exact4. `evaluator_io_used` is always exact `False`.

Universal invariants are `passed == (outcome == "passed")`, `blocks_candidate == (outcome != "passed")`, and an empty reason if and only if the outcome is `passed`.

## Validation precedence and evidence

Validation is frozen as four fail-fast phases:

1. Exact4 presence, in field order.
2. Exact4 exact type then value, in field order.
3. Exact4 context exact outer type then exact content, in context order.
4. Passed.

The truth matrix contains 105 rows: all 52 predecessor field cases projected unchanged into valid contexts, 39 detailed context cases, 6 cross-phase precedence cases, and 8 negative result-invariant cases. The contract, routing, source, and issue outputs contain 70, 27, 30, and 16 rows respectively.

The checker is standard-library-only, independently rebuilds semantics, reads the Exact6 output through pinned file descriptors, freezes all six output SHA256 values, and still rejects synchronized semantic tampering when frozen-hash enforcement is disabled.

The production materializer retains the predecessor `RENAME_NOREPLACE` policy. An `EINVAL` from the repository filesystem is a fail-closed result with no `os.replace` fallback; the single canonical output set is generated on a supporting temporary filesystem, byte/SHA verified, and added to the working tree through controlled patches.

## Issue and readiness transition

The Exact16 issue inventory is preserved. The routing-responsibility, standalone-signature, and result-contract issues become resolved through `admit_012_formal_evaluator_interface_contract_frozen_v1`. Previously resolved field-contract issues remain resolved. Unified coverage and cross-rule aggregation remain open, and coverage remains exactly `ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015`.

The interface is ready only for `implement_covapie_admit_012_standalone_evaluator_interface_v1`. Rule logic, the formal evaluator/result implementation, adapter, Exact12 runtime registration, provider mapping, real provider evaluation, bulk download, combined candidate verdict, and training remain false. Step12D remains `smoke_legality_only_not_final_training_feature_contract`, and a feature-semantics audit remains mandatory before training.
