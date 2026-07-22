# CovaPIE ADMIT_013 download outcome and integrity contract v1

## Scope and lineage

This metadata-only design is based on commit
`30c644de3973ba2968ecaa8ebff97159c07678b9` (`add CovaPIE ADMIT_013 formal
evaluator preconditions audit v1`), whose exact parent is
`5ff12d358a633c44c333022f7e0ebe30f039d6fc`. The source boundary is an
explicit Exact22 set of committed Step14AT, Step14AU-A, ADMIT_012, Exact12
runtime, and ADMIT_013 precondition evidence. It does not repeat the historical
545-file occurrence scan.

The frozen base commit identity is checked independently from the current
checkout. The base must be an ancestor of `HEAD`, so the design is valid both
before its commit and in a clean descendant candidate. Exact equality between
`HEAD` and the base is not required. Every Exact22 filesystem byte must still
equal both its base-commit blob and frozen SHA; a non-ancestor or later source
drift fails before any output is read.

The rule identity remains `ADMIT_013` / `download_failure_fail_closed`, with
`future_download_result`, `non_success_or_integrity_failure_not_admitted`,
`download_failure_must_fail_closed`, and `post_download`.

## Dependency and routing boundary

ADMIT_012 may be a logical pipeline prerequisite, but ADMIT_013 does not
consume `Admit012EvaluationResult` or any other cross-rule Python result
object. A future standalone ADMIT_013 evaluator must perform the shared Exact4
presence/type/value checks itself before applying this business policy.

The Exact4 order remains `download_result_status`, `observed_http_status`,
`observed_content_length_bytes`, and `observed_sha256`, sourced only from
`download_result_context`. Integrity authority is sourced only from
`evaluation_context`. Candidate, batch, stage-authorization, and fallback
envelopes are forbidden. The future evaluator remains pure in-memory and may
not normalize, infer, read files or networks, consult a provider, or recompute
observations.

## Outcome policy

HTTP success is exactly the inclusive range 200 through 299. Status `failure`
always blocks and has highest business precedence, including when HTTP is 2xx
or other observations appear valid. Status `success` with a non-2xx status
blocks. Status `success` with 2xx only continues to content and integrity
checks; it does not pass by itself.

An observed content length of zero always blocks, even if expected length is
zero, SHA values match, or a verifier says `verified`. Structural legality of
zero under ADMIT_012 is therefore distinct from ADMIT_013 admission.

Passing requires all of the following: status `success`, HTTP 2xx, positive
observed length, agreement of every provided trusted authority, and at least
one strong authority. A strong authority is either an exact expected/observed
SHA match or explicit verdict `verified`. Expected-length agreement alone,
nonzero content plus syntactically valid SHA, or any simpler subset is
insufficient.

## Integrity authority

The closed authority set is:

1. `expected_content_length_bytes`: optional exact built-in `int`, subclasses
   and `bool` rejected, minimum zero, no normalization. When present it must
   equal the observed length, but it is never sufficient alone.
2. `expected_sha256`: optional exact built-in `str`, exactly ASCII lowercase
   `[0-9a-f]{64}`, no normalization. It must come from a trusted provider
   manifest, trusted pre-download catalog, or separately approved equivalent
   authority. A mismatch blocks; an exact match is strong authority.
3. `explicit_integrity_verdict`: optional exact built-in `str` in the closed
   enum `verified | failed`, with no normalization. Only a future designated
   verifier may produce it. `failed` blocks; `verified` is strong authority but
   cannot override another provided mismatch.

Candidate self-report, fixtures, artifact/checker/Git/source-boundary hashes,
historical pilot values, and an observed SHA generated after the same download
are forbidden pseudo-authorities. Authority provenance belongs to the future
adapter/caller; the evaluator consumes only routed in-memory values.

## Failure vocabulary and evidence

Business evaluation follows shared Exact4 and authority structural validation.
The closed outcome-level precedence is:

1. `DOWNLOAD_RESULT_STATUS_FAILURE`
2. `OBSERVED_HTTP_STATUS_NOT_SUCCESS`
3. `OBSERVED_CONTENT_EMPTY`
4. `OBSERVED_SHA256_MISMATCH`
5. `EXPLICIT_INTEGRITY_VERDICT_FAILED`
6. `OBSERVED_CONTENT_LENGTH_MISMATCH`
7. `INTEGRITY_AUTHORITY_MISSING`
8. passed with an empty reason

There is no catch-all, `UNKNOWN`, `OTHER`, or free-text reason. The 23-case
truth matrix includes three passing cases, all required single-failure cases,
double/triple conflicts, and every adjacent business-precedence conflict.

## Issue transitions and readiness

The Exact23 predecessor issue identities and order are retained. Five rows
carry explicit successor transitions to effective `resolved`: routing
responsibility, ADMIT_012 validation dependency, download outcome policy,
integrity comparison authority, and multi-failure precedence. Standalone
signature and formal result contract remain open. Unified coverage remains
open for `ADMIT_013|ADMIT_014|ADMIT_015`, and cross-rule aggregation remains
open.

The design resolves Exact32 preconditions `PRE_013`, `PRE_014`, `PRE_015`,
`PRE_016`, `PRE_018` through `PRE_024`, and `PRE_026` through `PRE_028`.
`PRE_029` and `PRE_030` remain open for the next formal-interface design.

The recommended next step is exactly
`design_covapie_admit_013_formal_evaluator_interface_contract_v1`. Evaluator,
result type, adapter, registry, Exact13 runtime, provider mapping, real provider
evaluation, bulk download, aggregation, combined verdict, and training remain
false. Step12D remains a smoke legality check, not a final training-feature
contract; a feature-semantics audit remains mandatory before training.

## Materialization

The Exact6 set uses exact inventory checks, no symlinks, no overwrite,
inode-preserving exact-set no-op behavior, and `RENAME_NOREPLACE`. GPFS
`EINVAL` fails closed without an `os.replace` fallback and without staging
residue. After a successful rename, the output parent directory is opened with
`O_DIRECTORY | O_CLOEXEC` and fsynced before postverification; fsync failure is
not swallowed. Production and checker each open the non-symlink output root as
a pinned directory FD and open every frozen regular leaf by name with
`dir_fd=root_fd`, then recheck parent, root, inventory, and all leaf identities.
The checker independently reconstructs all canonical rows and the manifest,
verifies source lineage before reading outputs, and pins all output bytes and
frozen SHA256 values.

The Exact10 stage inventory is lifecycle-scoped independently of ancestry.
The frozen base must be an ancestor of `HEAD`, but all ten paths being
untracked means `pre_commit` whether `HEAD` is the base itself or any valid
descendant. All ten paths being tracked with clean stage-scoped working-tree
and index diffs means `post_commit`. Partial, missing, ignored, dirty, or staged
Exact10 states fail closed. Unrelated commits, untracked files, staged files,
and ignored Python/pytest caches do not determine this stage lifecycle, while
any extra file under this stage's Exact6 output root is rejected.
