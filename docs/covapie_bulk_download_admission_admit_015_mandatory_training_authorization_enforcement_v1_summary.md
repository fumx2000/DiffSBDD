# CovaPIE ADMIT_015 mandatory training-authorization enforcement v1

This stage implements the frozen standalone, pure in-memory ADMIT_015
mandatory training-authorization guard. It does not connect the guard to a
training orchestrator and does not invoke a dataloader, model, checkpoint,
forward path, loss, backward pass, optimizer, scheduler, parameter update, or
training-output path.

## Revised2 manifest hash truth closure

Revised1 changed the checker, tests, and summary after their earlier hashes
had already been written into the manifest. Keeping that manifest
byte-identical was therefore incompatible with its claim that
`output_sha256` describes the current Exact10 files. Revised2 updates the
manifest so all nine non-manifest output paths identify their current bytes.
The manifest continues to exclude its own hash.

The checker no longer freezes the manifest hash or embeds a frozen hash of its
own bytes. It reads the checker, tests, and summary through the repository
relative no-follow reader and uses their current hashes only to verify the
manifest's integrity declarations. Those dynamic values do not provide API,
error, pass-invariant, PRE, readiness, mask, scope, or next-step semantics.
The checker continues to own those expected semantics locally.

Production and all five CSV files remain byte-identical. The public guard and
its business contract are unchanged; Revised2 changes only support-file hash
truth and its verification policy.

## Implemented public boundary

The public API is exactly:

```text
require_admit_015_training_authorization(candidate_record: Mapping[str, object], *, stage_authorization_context: Mapping[str, object] | None) -> UnifiedAdmissionRuleEvaluation
```

Each invocation owns exactly one call to the committed Exact15
`evaluate_admission_rule` dispatcher. It selects `ADMIT_015`, forwards the
original candidate and stage-context objects, and supplies `None` for batch,
evaluation, and download-result context. The guard does not inspect, iterate,
copy, or reinterpret either input object.

The signature accepts no dispatcher, precomputed result, bool permission,
combined verdict, or ADMIT_014 permission. Such keywords fail with Python
`TypeError` before the Exact15 runtime is called. The public-function AST has
one dispatcher call site and no loop, recursion, retry, dynamic import,
fallback, aggregation, combined-verdict branch, or ADMIT_014 branch.

## Exact pass validation

Only an exact, non-subclass
`UnifiedAdmissionRuleEvaluation` can return. The guard validates:

- exact `vars()` dictionary and Exact13 storage order;
- the runtime dataclass's Exact13 field order;
- exact top-level `str`, `bool`, and `tuple` types;
- reconstruction equality;
- schema `covapie_unified_admission_rule_evaluation_v1`;
- rule `ADMIT_015`;
- exact `outcome="passed"`, `passed=True`,
  `blocks_candidate=False`, and empty reason;
- normalized authorization
  `(("current_stage_training_authorized", "true"),)`;
- empty validated and consumed candidate fields;
- consumed context
  `("current_stage_training_authorized",)`;
- `evaluator_io_used=False`;
- adapter `covapie_admit_015_unified_adapter_v1`.

A canonical pass returns the original runtime result object by identity. It
does not rebuild the result and performs no later action.

## Frozen fail-closed errors

`Admit015TrainingAuthorizationEnforcementError` is an exact frozen dataclass
subclass of `RuntimeError`. Its ordered fields are `schema_version`,
`error_code`, `admission_rule_id`, and `reason`, and all values require exact
built-in `str`. The schema and rule are fixed; the deterministic reason is
always the error code. Original dispatcher exception details are not copied
into the error.

The Exact6 vocabulary is:

1. `ADMIT_015_TRAINING_AUTHORIZATION_DISPATCH_FAILED`
2. `ADMIT_015_TRAINING_AUTHORIZATION_RESULT_INVALID`
3. `ADMIT_015_TRAINING_AUTHORIZATION_DENIED`
4. `ADMIT_015_TRAINING_AUTHORIZATION_REPLAY_FORBIDDEN`
5. `ADMIT_015_TRAINING_AUTHORIZATION_REPEATED_CALL_FORBIDDEN`
6. `ADMIT_015_TRAINING_AUTHORIZATION_OVERRIDE_FORBIDDEN`

Dispatcher exceptions reach the first code, wrong result types and subclasses
reach the second, and exact-type denial or contract drift reaches the third.
The last three remain
`reserved_unreachable_by_exact_public_signature`; no hidden parameter or
signature override was added to manufacture reachability.

## Safety and readiness

All Exact11 protected-action counts are zero on canonical pass as well as
blocked, invalid, dispatcher-error, and drift paths:

1. dataloader instantiation
2. checkpoint loading
3. model initialization
4. model forward
5. loss computation
6. backward
7. optimizer creation
8. scheduler creation
9. parameter update
10. checkpoint write
11. training-result materialization

The guard's synthetic pass changes neither global permission nor training
execution count. `current_permission` remains false and
`authorized_admit_015_training_execution_count` remains zero.

The PRE state remains Exact45 with 41 complete, zero
supported-but-not-frozen, four incomplete, and four implementation-blocking
rows. PRE_034 remains resolved; PRE_035, PRE_036, PRE_038, and PRE_042 remain
open. The Exact30 issue inventory is inherited byte-for-byte with zero
transitions.

This stage makes these readiness values true:

- `mandatory_training_authorization_enforcement_api_frozen`
- `mandatory_training_authorization_enforcement_implemented`
- `ready_for_combined_permission_semantics_contract_design`

Combined permission semantics, combined candidate verdict, cross-rule
aggregation, training-orchestrator integration, feature-semantics completion,
historical unknown-atom-policy resolution, real-training readiness, and
ready-for-training remain false.

Step12D remains a smoke legality check rather than a final training-feature
contract. A feature-semantics audit is still mandatory before any training,
and historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False` remain unresolved.

## Evidence

The stage adds exactly ten files: production, checker, tests, this summary,
four implementation/runtime/safety contract CSVs, the byte-identical Exact30
issue inventory, and one manifest.

The checker owns its expected semantics locally. It freezes the production
and Exact5 CSV hashes; reconstructs every ordered field of
all Exact38 implementation, Exact33 error/result, Exact23 truth, and Exact11
protected-action rows; and compares the Exact30 issue inventory byte-for-byte
with its committed predecessor. Candidate rows, manifest booleans, and
manifest-reported output hashes are actual evidence only and are never used as
expected authority.

The complete expected manifest is also reconstructed locally without a frozen
manifest hash. Recursive comparison requires exact Python types, dictionary
key inventory and order, list length and order, and scalar equality. Duplicate
JSON keys and nested missing, extra, reordered, or type-substituted values fail
closed. This covers base identity, source boundaries, Exact10 order, public
API, Exact6 errors, Exact13 pass invariants, protected actions, PRE and issue
continuity, readiness, canonical five-mask semantics including
`scaffold_only` / `B3`, Step12D and feature-semantics warnings, scope, all
nine current output hashes, and the recommended next step.

The committed source boundary independently attests the Exact15 runtime source
and manifest plus the predecessor enforcement-contract source, manifest, and
issue inventory. For each source, the checker pins the path, SHA256, base-tree
mode and blob, current stage-0 index mode and blob, Git blob bytes, and
filesystem bytes. The fixed base must remain an ancestor throughout the check,
and Git and filesystem bytes must agree.

## Race-safe artifact and lifecycle validation

The Exact6 evidence reader is descriptor-pinned and no-follow. It fixes the
parent and derived-root identities, opens the directory and all six regular
leaves with no-follow semantics, keeps every leaf descriptor open through the
check, and repeats all identities and inventories before a final parent/root
binding check. Root, parent, or leaf replacement—including a same-byte inode
replacement—fails closed, as do symlinks, missing or extra leaves, forbidden
suffixes, and files larger than 100 MiB.

The Exact10 lifecycle validator recursively holds directory descriptors under
the bounded source, script, test, and documentation roots and scans matching
derived-stage roots from their parent. It rejects symlinks before name
filtering and rejects tracked, ignored, or nonignored residue. Initial and
final HEAD, ancestry, index, status, inventories, and six-field identities must
remain unchanged. A base worktree is valid only as an exact untracked
`pre_commit` state; a descendant candidate is valid only as a clean
`post_commit` state whose nonempty commit chain changes exactly the ten
authorized regular `100644` files. Allow-empty HEAD drift is rejected.

Tests exercise synchronized CSV-and-manifest tampering, complete nested
manifest tampering, production/runtime drift, Exact6 replacement races,
external-target-safe symlink rejection, residue under every bounded root,
matching derived siblings, top-root replacement, normal pre- and post-commit
states, descendant-base pre-commit state, and allow-empty HEAD drift.

No existing tracked file was modified and no dependency was installed. The
production module, checker, and targeted stage tests execute no training,
forward, loss, backward, optimizer, checkpoint, provider, network, download,
or raw-data operation.
