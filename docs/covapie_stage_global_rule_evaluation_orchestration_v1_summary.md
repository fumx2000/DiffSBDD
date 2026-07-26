# CovaPIE stage-global rule evaluation orchestration runtime V1

This increment implements the committed stage-global orchestration design as
a pure in-memory runtime. It calls the committed Exact15 single-rule
dispatcher and committed combined-candidate aggregator. It does not perform
provider access, network access, downloads, raw-data access, model or
checkpoint access, dataloader work, forward/loss/backward execution,
optimization, parameter updates, or training.

The production runtime is byte-identical to the manually reviewed
implementation (`SHA256
5b5b85eceee3a9aada2dc6ae57c8af4a365dfc74677facdceeda7f0bde8a86bc`).
This revision changes only the independent checker, tests, summary, and
derived evidence.

## Runtime boundary

The only orchestration function is:

```python
orchestrate_stage_admission_scope(
    scope_id,
    candidate_inputs,
    *,
    batch_context,
    stage_authorization_context,
)
```

The input, candidate-result, stage-result, and error classes are aliases of
the committed design-contract classes and therefore preserve class identity.
Top-level validation fails closed before any child runtime call.

For every top-level invocation, `ADMIT_014` runs once before candidate rules
in all four scopes. `ADMIT_015` additionally runs once, after `ADMIT_014`,
only for `training_execution_admission_permission`. Both rules receive the
shared immutable stage-global candidate sentinel, no batch/evaluation/download
context, and the caller's stage-authorization mapping by identity.

Candidate rules retain input order and canonical scope order. `ADMIT_001`
receives the caller batch context. `ADMIT_004`, `ADMIT_006`, `ADMIT_007`,
`ADMIT_008`, `ADMIT_010`, and `ADMIT_011` receive the candidate evaluation
context. `ADMIT_009` receives both batch and evaluation contexts.
`ADMIT_012` and `ADMIT_013` receive evaluation and download-result contexts.
`ADMIT_002`, `ADMIT_003`, and `ADMIT_005` receive no context. Candidate rules
never receive the caller stage-authorization context. Mapping objects are
forwarded by identity and are not copied.

Each complete candidate vector is assembled exactly once in
`REQUIRED_RULE_IDS` order. The already-produced stage results are reused by
identity in every candidate vector. The exact vector object passed to the
aggregator is stored in the candidate result. Normal passed/blocked/invalid
verdicts retain that vector by identity. A rejected child is still passed
unchanged to the real aggregator and yields its canonical invalid,
empty-diagnostics verdict.

Passed, blocked, invalid, and rejected outcomes do not short-circuit
diagnostics. Only a callable exception or malformed child result stops
orchestration. Callable `Exception` failures are projected with deterministic,
attempt-inclusive coordinates and explicit cause chaining. Malformed results
are rejected outside the callable `try` block without a cause.
`KeyboardInterrupt`, `SystemExit`, and other `BaseException` values propagate
unchanged.

The independent checker executes the complete stage and candidate exception
coordinate matrices and verifies the error code, candidate and rule
coordinates, attempt-inclusive dispatcher and aggregator counts, cause
presence and type, non-leaking reason, actual call counts, and stopping
boundary. Its training-scope `N=3` corruption probes cover wrong type, wrong
scope, copied normal vector, rejected wrong reason, and rejected nonempty
diagnostics at candidate 1. In every case candidate 2 and aggregator attempt 3
remain uncalled, and no partial stage result is returned.

## Repository lifecycle closure

The checker recognizes exactly four lifecycle modes: pre-commit, detached
candidate post-commit, formal-main post-commit unpushed, and formal-main
post-push. Each immutable snapshot freezes HEAD, complete index bytes,
porcelain status bytes, ordered persistent refs, current branch, ordered
worktree records, symbolic `origin/HEAD`, its resolved OID, and lifecycle
mode. The complete first and final snapshots must be identical.

The pre-commit and formal-main modes require one exact main worktree. The
detached mode requires exactly two real worktrees: main at the committed BASE
and the current detached candidate. Persistent refs are closed to main,
origin/main, symbolic origin/HEAD, and platform refs matching the predecessor's
full grammar, tree-object type, and blocked-term policy. Extra branches, tags,
refs, worktrees, or origin/HEAD drift fail closed.

The returned stage result always records `orchestration_io_used=False` and
`action_permission_granted=False`. A passed diagnostic result does not execute
or authorize download or training.

## Readiness and feature semantics

Current permission is false. Action permission is false. This implementation
is not ready for training and does not start training.

PRE continuity is inherited from the committed predecessor manifest:
`row_count=45`, `complete_count=43`, `incomplete_count=2`,
`implementation_blocking_count=2`, and no transitions. The two remaining open
preconditions are `PRE_038` and `PRE_042`.

Step12D was a smoke legality check, not a final training-feature contract.
`UNKNOWN_ATOM_FEATURE_POLICY` remains unresolved and
`feature_semantics_known=False` remains unresolved. A feature-semantics audit
is mandatory before formal training, fine-tuning, backward passes, optimizer
steps, or parameter updates.

The canonical mask contract remains exactly:

1. `warhead_only / A`
2. `linker_plus_warhead / B`
3. `scaffold_plus_warhead / B2`
4. `scaffold_only / B3`
5. `scaffold_plus_linker_plus_warhead / C`

No sixth mask is introduced.

The recommended next step is
`run_covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1`.
That step is only a controlled in-memory integration smoke; it is not a
download or training operation.
