# CovaPIE ADMIT_013 formal evaluator interface preconditions audit v1

## Scope and baseline

This read-only metadata audit is based on commit
`5ff12d358a633c44c333022f7e0ebe30f039d6fc` (`add CovaPIE unified dispatch
runtime with ADMIT_001 to ADMIT_012 v1`). It audits only the preconditions for
a future `ADMIT_013` evaluator. It does not implement `evaluate_admit_013`, an
`Admit013EvaluationResult`, an adapter, registration, an Exact13 runtime,
provider mapping, cross-rule aggregation, a combined verdict, network access,
a download, raw access, model/checkpoint work, or training.

## Frozen identity and shared structural evidence

The exact Step14AT rule is `ADMIT_013` / `download_failure_fail_closed`, with
`future_download_result`,
`non_success_or_integrity_failure_not_admitted`, blocking severity,
`download_failure_must_fail_closed`, and `post_download`. Both network and raw
requirements are false. The registry's
`ready_for_future_implementation=true` is an identity/readiness flag, not a
claim that rule semantics are complete.

The shared Exact4 order is `download_result_status`, `observed_http_status`,
`observed_content_length_bytes`, and `observed_sha256`. The committed
ADMIT_012 field contract freezes exact built-in types, rejects subclasses and
normalization, freezes status vocabulary `success | failure`, permits only
structural HTTP values 100 through 599, permits content length zero with no V1
upper bound, and requires lowercase ASCII `[0-9a-f]{64}`. Neither content
length nor SHA is recomputed from a file inside the evaluator. ADMIT_012 still
passes structurally legal `failure`, 4xx, and 5xx values; final disposition is
reserved for future ADMIT_013.

## Incomplete ADMIT_013 semantics

The Exact32 matrix contains 16 complete rows and 16 incomplete,
implementation-blocking rows. Rule identity, Exact4 identity/structure, the
fact that canonical `failure` must block, the distinction between SHA grammar
and integrity, and the pure in-memory/authorization boundary are complete.

The following remain unfrozen:

- ADMIT_013 envelope routing and whether candidate/batch/stage inputs are
  forbidden or `None`;
- whether ADMIT_013 revalidates Exact4 or consumes a prior formal ADMIT_012
  result; the current runtime dispatches one rule at a time and has no
  cross-rule prerequisite contract;
- the complete success/failure/HTTP outcome policy, explicit adoption of the
  future 200–299 bounds, and status/HTTP contradiction handling;
- zero-length business disposition, a trusted expected content length, and an
  observed-versus-expected length comparison;
- a trusted expected download SHA256, an observed-versus-expected SHA
  comparison, and an explicit integrity verdict;
- provider/transport failure taxonomy, multi-failure precedence, closed
  reasons, standalone signature, and formal result invariants.

Observed content length and observed SHA exist, but no authoritative
ADMIT_013 schema/context producer and consumer is assigned for expected
content length, trusted expected SHA256, or an explicit integrity verdict.
Source-boundary, artifact, checker, manifest, Git, and fixture hashes are
attestations or examples and cannot serve as expected download checksums. A
syntactically valid SHA is only a representation-valid observation, never an
integrity match verdict. No rule is invented that treats nonzero content,
valid-format SHA, 2xx plus nonzero content, or status `success` as sufficient
integrity.

## Evidence, issues, and readiness

The fixed source boundary contains 545 committed regular non-symlink blobs.
Its ordered path-list SHA256 is
`d0cfd2b25097e62a23af6c89339b606d07ebb176c298e406f47c1981953bc105`;
the ordered path/SHA-pair SHA256 is
`d81100221ae603ccc2e660a194d4f8da009e96c85130a1f29f3678163a696d2d`.
Every parent chain is checked before source bytes are read, and every source
uses an `O_NOFOLLOW` pinned descriptor with base/filesystem SHA equality.

The occurrence inventory has 9,517 rows: 386 primary contracts, 1,404 runtime
contracts, 4,480 committed design evidence rows, 148 historical/reference
rows, 465 test-fixture rows, 554 source-attestation rows, 115 documentation
rows, and 1,965 unrelated-text rows. The observed-value inventory has 9,520
rows, including three explicit authority-absence rows. It separates 465
synthetic fixtures, 554 source/artifact hashes, 74 historical download and 48
historical provider representations, 6,270 schema/contract representations,
115 documentation examples, 178 placeholders, 61 historical references, and
1,752 unrelated values. Authorized ADMIT_013 download executions and current
real ADMIT_013 download-result observations are both exactly zero.

The Exact16 runtime issue inventory is preserved byte-for-field and in order.
Seven new blocking ADMIT_013 semantic-gap issues are appended, producing
Exact23: routing responsibility, ADMIT_012 validation dependency, download
outcome policy, integrity comparison authority, multi-failure precedence,
standalone signature, and result contract. Unified coverage remains open for
`ADMIT_013|ADMIT_014|ADMIT_015`; cross-rule aggregation remains open.

Readiness is true only for the completed audit, rule identity, available
shared Exact4 structure, future pure in-memory feasibility, and the next
contract-design stage. It is false for all ADMIT_013 routing/outcome/integrity,
precedence/reason/signature/result freezes; evaluator/result/adapter/runtime
implementation; provider and real evaluation; bulk download; aggregation;
combined verdict; and training. Step12D remains
`smoke_legality_only_not_final_training_feature_contract`, and a feature
semantics audit remains mandatory before training.

The only recommended next step is
`design_covapie_admit_013_download_outcome_and_integrity_contract_v1`.

## Materialization

The Exact6 materializer retains set-atomic `RENAME_NOREPLACE`, exact-set
inode-preserving no-op behavior, pinned output traversal, and mismatch
fail-closed behavior. The single repository-filesystem publish attempt
returned GPFS `EINVAL`, published no target, used no `os.replace` fallback,
and left no staging residue. Two canonical sets were then built on supporting
temporary filesystems, proved byte-identical, SHA-verified, and transferred
through the exact six-file whitelist.
