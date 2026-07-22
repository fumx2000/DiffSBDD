# CovaPIE ADMIT_013 formal evaluator interface contract v1

## Scope and lineage

This metadata-only Design contract is based on commit
`2eea08835c4ef88d5b810509134f8eef94e3e99e` (`add CovaPIE ADMIT_013
download outcome and integrity contract v1`), whose exact parent is
`30c644de3973ba2968ecaa8ebff97159c07678b9`. The base must be an ancestor of
`HEAD`; exact equality is not required. The ordered Exact25 source boundary
contains the current ADMIT_013 outcome/integrity source and Exact6, the
ADMIT_013 precondition Exact3, the ADMIT_012 field/formal/standalone/adapter
chain, the Exact12 runtime identity, and the Step14AT/AU-A registry, schema,
executability, field-semantics, and evaluation-context evidence. It does not
repeat the historical 545-file occurrence scan.

Every source must be tracked at the base commit, regular and non-symlink, with
a non-symlink parent chain. Current bytes must equal both the base blob and the
frozen SHA256 through a pinned no-follow descriptor read. Base lineage and all
sources are verified before any output is read. Raw, checkpoints, providers,
download execution, model/training files, and uncommitted candidate files are
not source authority.

## Future signature

The future public symbols are frozen, but are not defined by this stage:

```python
evaluate_admit_013(
    *,
    download_result_status: object = _MISSING,
    observed_http_status: object = _MISSING,
    observed_content_length_bytes: object = _MISSING,
    observed_sha256: object = _MISSING,
    expected_content_length_bytes: object = _MISSING,
    expected_sha256: object = _MISSING,
    explicit_integrity_verdict: object = _MISSING,
) -> Admit013EvaluationResult
```

All seven parameters are scalar and keyword-only, in the displayed order.
There are no positional parameters, `*args`, `**kwargs`, Mapping parameters,
policy-context parameters, or extra parameters. The future `_MISSING` is a
private singleton owned by the future evaluator module. It is distinct from
`None`, `False`, `0`, and the empty string. This Design stage uses a separately
named private Design sentinel; it is not a runtime implementation and never
appears in a result or generated record.

## Structural contract and precedence

The required Exact4 observations are, in order:

1. `download_result_status`: exact built-in `str`, `success | failure`.
2. `observed_http_status`: exact built-in `int`, inclusive structural range
   `100..599`; `bool` and subclasses are rejected.
3. `observed_content_length_bytes`: exact built-in `int`, minimum zero. Zero is
   structurally legal but always business-blocked.
4. `observed_sha256`: exact built-in `str`, ASCII lowercase `[0-9a-f]{64}`.

The optional Exact3 integrity authorities are, in order:

1. `expected_content_length_bytes`: when present, exact built-in non-negative
   `int`; a match is corroborating only.
2. `expected_sha256`: when present, exact built-in lowercase SHA256 string; an
   exact match is strong authority.
3. `explicit_integrity_verdict`: when present, exact built-in `str` in
   `verified | failed`; `verified` is strong authority and `failed` blocks.

Optional absence is legal and does not produce a structural missing reason.
No field is stripped, case-folded, converted, stringified, inferred, or
normalized. The complete phase order is:

1. `Exact4_presence`
2. `Exact4_type_value`
3. `Exact3_optional_authority_type_value`
4. `Exact7_business_outcome`
5. `passed`

The first failure returns immediately. Consequently every Exact4 presence
failure precedes every Exact4 type/value failure; every Exact4 structural
failure precedes every authority failure; and every authority failure precedes
status, HTTP, empty-content, mismatch, verdict, length, and missing-authority
business reasons.

## Closed outcome and reason contracts

The exact outcome vocabulary is `passed | blocked | invalid`. Exact4 missing
is blocked. Exact4 or Exact3 type/value invalidity is invalid. Exact7 business
failure is blocked. The Exact26 reason vocabulary contains the empty pass
reason, four Exact4 missing reasons, eight Exact4 type/value reasons, six
Exact3 type/value reasons, and these seven business reasons in precedence
order:

1. `DOWNLOAD_RESULT_STATUS_FAILURE`
2. `OBSERVED_HTTP_STATUS_NOT_SUCCESS`
3. `OBSERVED_CONTENT_EMPTY`
4. `OBSERVED_SHA256_MISMATCH`
5. `EXPLICIT_INTEGRITY_VERDICT_FAILED`
6. `OBSERVED_CONTENT_LENGTH_MISMATCH`
7. `INTEGRITY_AUTHORITY_MISSING`

Passing requires status `success`, HTTP `200..299`, nonzero content, agreement
of every provided authority, and either exact expected/observed SHA equality or
an explicit `verified`. Expected-length agreement alone, syntactically valid
observed SHA, 2xx, nonzero content, or any simpler conjunction is insufficient.
No provided mismatch or `failed` verdict can be overridden by another passing
authority.

## Future Exact12 result contract

The future formal result type name is `Admit013EvaluationResult`, but the type
is not defined here. Its exact field order is:

1. `admission_rule_id`
2. `outcome`
3. `passed`
4. `blocks_candidate`
5. `reason`
6. `canonical_download_result_record`
7. `canonical_integrity_authority_record`
8. `validated_download_result_fields`
9. `validated_integrity_authority_fields`
10. `consumed_download_result_fields`
11. `consumed_integrity_authority_fields`
12. `evaluator_io_used`

The string and boolean fields require exact built-in types. All record and
name-sequence fields require exact built-in tuples. Canonical records are exact
outer tuples of exact two-item pair tuples: pair names are exact strings in
canonical order, and values retain their original exact type. Lists, tuple or
pair subclasses, mappings, duplicates, reorder, extra pairs, stringification,
normalization, and missing sentinels are rejected.

On an Exact4 missing failure both canonical records are empty, validated
download names contain the existing presence prefix before the failure, and
consumed download names include the failed lookup. On an Exact4 type/value
failure both canonical records are empty, the complete Exact4 was consumed,
and validated names stop before the failing field.

After Exact4 structural success, the canonical download record is complete.
On an authority structural failure, the authority canonical record and
validated names contain only earlier provided-valid authorities; missing
earlier optional authorities are omitted. The consumed authority tuple includes
every checked name through the failing authority, including missing names.
For business-blocked and passed results, all Exact4 and Exact3 names were
consumed; canonical/validated authority entries include only provided-valid
authorities.

The result invariants are `passed == (outcome == "passed")`,
`blocks_candidate == (outcome != "passed")`, an empty reason exactly when
passed, and `evaluator_io_used is False`.

## Routing and purity

The future adapter may route Exact4 only from `download_result_context` and
Exact3 only from `evaluation_context`. Candidate, batch, stage-authorization,
fallback, filesystem, network, raw, provider, and in-evaluator download sources
are forbidden. The standalone evaluator consumes only the seven scalar
keywords. It does not access a Mapping envelope, open a file, compute SHA or
content length, access the network/provider/raw state, execute a download,
normalize, or infer.

ADMIT_012 may be a logical prerequisite in a future combined pipeline, but
ADMIT_013 does not consume `Admit012EvaluationResult`, a
`prior_admit_012_result` parameter, or any cross-rule Python result object.
Aggregation and combined verdict behavior are not implemented.

## Evidence, issues, and readiness

The deterministic truth matrix has 128 rows: 79 field/authority/cross-phase
cases, the exact 23 inherited business cases, and 26 exact result-contract
negative cases. It covers the required boundary values, subclasses, malformed
containers/pairs, sentinel rejection, result storage/order, and all structural
versus business precedence edges.

The Exact23 issue identities and order are inherited. Only
`ADMIT_013_STANDALONE_SIGNATURE_UNRESOLVED` and
`ADMIT_013_RESULT_CONTRACT_UNRESOLVED` receive successor effective resolution,
with action `resolved_by_successor_formal_interface_contract_design`. Unified
coverage remains open for `ADMIT_013|ADMIT_014|ADMIT_015`; cross-rule
aggregation remains open. Provider, adapter, registry, runtime, download, and
training issues are not resolved.

The contract is ready only for
`implement_covapie_admit_013_standalone_evaluator_interface_v1`. It does not
implement `evaluate_admit_013`, `Admit013EvaluationResult`, rule logic, an
adapter, registration, Exact13 runtime, provider mapping/evaluation, bulk
download, combined verdict, aggregation, or training. Step12D remains a smoke
legality check, not a final training-feature contract. A feature-semantics
audit, including the historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False` state, remains mandatory before training.

## Materialization and lifecycle

The Exact6 publisher uses an exact inventory, non-symlink output root and
regular leaves, build-before-mutation, `O_EXCL` staging leaves, leaf and staging
directory fsync, `RENAME_NOREPLACE`, output-parent fsync, and pinned-root-FD
postverification. Root descriptors use `O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC`;
leaf opens use `dir_fd=root_fd`. GPFS `EINVAL` fails closed without an
`os.replace` fallback or staging residue. A byte-identical existing Exact6 is
an inode-preserving no-op; mismatch or replacement races fail closed.

The lifecycle-scoped Exact10 consists only of the four source/checker/test/doc
files and six derived outputs. All ten untracked is `pre_commit`; all ten
tracked with clean stage-scoped working and index diffs is `post_commit`.
Mixed, staged-stage, dirty, missing, ignored, symlink, oversized, forbidden
suffix, or extra same-stage output state fails closed. Unrelated commits,
untracked/staged files, and ignored caches do not determine this stage's
lifecycle after base ancestry has been verified.
