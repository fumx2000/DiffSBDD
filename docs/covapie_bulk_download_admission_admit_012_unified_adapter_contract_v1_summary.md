# CovaPIE ADMIT_012 unified adapter contract v1

## Scope and baseline

This is a design-only gate for the future `ADMIT_012` unified adapter. The
frozen base is `16bedd92f97a4c52743f4f923d5c42ae8fee9a84` (`add CovaPIE
ADMIT_012 standalone evaluator interface v1`). It adds no handler, registry
entry, dispatcher route, public runtime result type, provider mapping,
download execution, ADMIT_013 judgment, model/checkpoint change, or training.

The fixed source boundary is ordered Exact19. Its path-list SHA256 is
`c541a32eb23ac4bc0e95f4778923b6d24f62cc8623c6b25992725c32eb66c233`;
its ordered path/SHA-pair SHA256 is
`e40b85438e3f2068efd3747b050763a9ee9d98e92baebca928c20a3fcb9b2f4e`.
Every source is tracked at the base, a regular non-symlink blob beneath a
non-symlink parent chain, and is read through an `O_NOFOLLOW` pinned file
descriptor only after all structural checks pass. No raw or checkpoint path
is in the boundary.

## Frozen identity and registry contract

- Rule: `ADMIT_012` / `future_download_integrity_fields_required`
- Adapter: `covapie_admit_012_unified_adapter_v1`
- Formal evaluator/result: `evaluate_admit_012` / `Admit012EvaluationResult`
- Independent oracle: `classify_admit_012_formal_evaluator_interface_design`
- Current registry: ordered `ADMIT_001` through `ADMIT_011`
- Future registry: ordered `ADMIT_001` through `ADMIT_012`
- `ADMIT_013` through `ADMIT_015` remain known and unregistered after that
  future increment; all existing Exact11 handler identities remain unchanged.

## Five-envelope routing and precedence

The future handler shape remains `handler(candidate_record, *,
batch_context, evaluation_context, download_result_context,
stage_authorization_context)`. Routing is frozen in this order:

1. `batch_context` must be `None`.
2. `evaluation_context` must be a `Mapping`.
3. Look up, exactly once and in order,
   `allowed_download_result_statuses`, `successful_http_status_contract`,
   `content_length_contract`, and `sha256_format_contract`.
4. `download_result_context` must be a `Mapping`.
5. `stage_authorization_context` must be `None`.
6. `candidate_record` must be a `Mapping`; no candidate key may be queried,
   enumerated, or used as an ADMIT_012 formal input.
7. Look up the Exact4 download-result keys in frozen order. At the first
   missing key, stop all later lookups and omit that keyword and every later
   field keyword from the formal/oracle calls.
8. Call the standalone formal evaluator once; validate its complete Exact10;
   call the independent oracle once; require full typed Exact10 equality; then
   project to Exact13.

All routing failures prevent later envelope access and have zero formal and
oracle calls. Context failures use
`UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID` with these exact reasons:

- `ADMIT_012_BATCH_CONTEXT_MUST_BE_NONE`
- `ADMIT_012_EVALUATION_CONTEXT_MAPPING_REQUIRED`
- `ADMIT_012_ALLOWED_DOWNLOAD_RESULT_STATUSES_REQUIRED`
- `ADMIT_012_SUCCESSFUL_HTTP_STATUS_CONTRACT_REQUIRED`
- `ADMIT_012_CONTENT_LENGTH_CONTRACT_REQUIRED`
- `ADMIT_012_SHA256_FORMAT_CONTRACT_REQUIRED`
- `ADMIT_012_DOWNLOAD_RESULT_CONTEXT_MAPPING_REQUIRED`
- `ADMIT_012_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE`

A non-`Mapping` candidate returns the frozen invalid Exact13 with reason
`ADMIT_012_CANDIDATE_RECORD_MAPPING_INVALID`, empty pair/consumed-field
tuples, the Exact4 policy-context consumption tuple, and zero formal/oracle
calls. Empty and unrelated-field candidate mappings are accepted envelopes.

The adapter never imports or forwards the standalone private missing
sentinel. Present `None`, `False`, and zero values are preserved as present
objects. Every present field and policy-context object is passed by original
identity, without copying, normalization, conversion, or whole-envelope
forwarding.

## Exact10 validation, oracle equality, and Exact13 projection

The formal source must have exact type `Admit012EvaluationResult`, an exact
built-in `dict` storage map in the standalone Exact10 field order, the frozen
dataclass order and top-level built-in types, successful reconstruction,
`admission_rule_id == "ADMIT_012"`, `evaluator_io_used is False`, and all
standalone reason-specific invariants. Wrong type yields
`ADMIT_012_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID`; every other source or oracle
failure yields `ADMIT_012_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID`. Both use
`UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY` and fail closed.

The oracle result is independently type/storage/order/type/reconstruction
validated and converted to the formal Exact10 type. Equality covers every
Exact10 value and its exact type, not merely outcome, pass flag, and reason.

The existing public Exact13 remains byte- and object-contract compatible: its
two pair fields accept exact string pairs only. The frozen helper
`project_download_result_pairs_to_exact_string_pairs` maps an already
validated ordered pair prefix as follows:

- `download_result_status`: exact string unchanged
- `observed_http_status`: exact integer to canonical base-10 `str(value)`
- `observed_content_length_bytes`: exact integer to canonical base-10
  `str(value)`
- `observed_sha256`: exact string unchanged

It preserves field names, order, prefix length, empty tuples, lowercase SHA,
zero, and arbitrarily large integer decimal forms. It rejects `bool`, integer
subclasses, string subclasses, and non-exact pair containers. It does not use
`repr`, strip, lowercase, prefix, or type-tag values.

Exact13 `normalized_values` carries the string projection of
`canonical_download_result_record`; `validated_candidate_fields` carries the
string projection of `validated_download_result_fields`;
`consumed_candidate_fields` carries `consumed_download_result_fields`; and
`consumed_context_items` is passed through. The names
`validated_candidate_fields` and `consumed_candidate_fields` are historical
Exact13 field names: for ADMIT_012 their payload has download-result semantics
and does not imply any value came from `candidate_record`.

## Evidence and readiness

The exact six derived outputs contain:

- Exact36 contract rows
- Exact43 routing/lookup/call-count rows
- Exact148 truth rows: the complete Exact105 formal/oracle/Exact13 projection
  followed by all Exact43 routing/source/oracle/projection/registry cases
- Exact31 safety rows
- the predecessor Exact16 issue inventory, byte-identical
- one manifest with the source boundary, output hashes, closed readiness, and
  no self-hash

The seven ADMIT_012 field/interface issues remain resolved. Both
`UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE` and
`UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED` remain open;
coverage remains exactly `ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015`.

The adapter contract, typed projection, and download-result routing contract
are ready for implementation. The adapter is not implemented, ADMIT_012 is
not registered, and the Exact12 runtime does not exist. Provider mapping,
real-provider evaluation, bulk download, combined verdicts, and training are
not ready. A feature-semantics audit is still required before training, and
Step12D remains `smoke_legality_only_not_final_training_feature_contract`.

The recommended and only newly authorized next step is
`implement_covapie_unified_dispatch_runtime_with_admit_001_to_012_v1`.

## Materialization note

The repository GPFS returned `EINVAL` for `RENAME_NOREPLACE`. Publication
failed closed without `os.replace` fallback or staging residue. The six-file
set was then built independently twice on a supporting temporary filesystem;
both sets were byte-identical before the verified set was transferred through
the controlled exact-file whitelist. Re-running against an identical existing
set is inode-preserving; any mismatch fails without repair.
