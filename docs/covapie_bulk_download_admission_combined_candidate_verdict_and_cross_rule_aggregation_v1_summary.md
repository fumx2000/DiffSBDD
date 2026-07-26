# CovaPIE combined candidate verdict and cross-rule aggregation v1

This stage implements the frozen pure in-memory combined-candidate verdict and
cross-rule aggregation contract. The production API consumes only an
already-generated ordered tuple of actual
`UnifiedAdmissionRuleEvaluation` values:

```python
aggregate_admission_rule_evaluations(
    scope_id: str,
    *,
    ordered_rule_evaluations: tuple[UnifiedAdmissionRuleEvaluation, ...],
) -> CombinedAdmissionCandidateVerdict
```

The runtime validates the actual Exact13 child representation, the Exact4
scope memberships, the Exact8 fail-closed precedence, and the complete ordered
invalid/blocked/failing projections. It preserves a fully valid input tuple by
identity. Structural, admissibility, and outcome phases scan the full vector.
Runtime-valid `rejected` children are aggregation-inadmissible. Exact-shape
nested duplicates remain permitted and are not interpreted, merged,
deduplicated, copied, or rebuilt by the aggregator.

The public aggregation path performs no dispatcher or handler call and no
filesystem, Git, network, provider, download, raw-data, torch, model,
checkpoint, dataloader, or training operation. A passed combined verdict
describes only the admission-layer vector for its scope. It does not grant
action permission and does not implement stage-global orchestration.

The implementation resolves only `PRE_036`. The resulting PRE counts are
43 complete, 0 supported-but-not-frozen, 2 incomplete, and 2
implementation-blocking. `PRE_038` and `PRE_042` remain open. Step12D remains
only a smoke legality check; the historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False` state still require a formal feature-semantics
audit before training. `ready_for_training` remains false.

The evidence set contains an Exact49 runtime contract, the Exact201/23
implementation truth matrix using the actual runtime type, an Exact30 safety
audit, an Exact45 PRE transition inventory, byte-identical Exact30 issue
continuity, and a deterministic manifest. The recommended next step is exactly:

`design_covapie_stage_global_rule_evaluation_orchestration_contract_v1`

## Lifecycle and formal-main post-commit closure

This revision changes checker lifecycle enforcement only; the aggregation
business implementation and its five CSV evidence files remain byte-identical.
The earlier checker skipped the contents of the formal derived root, so an
ignored extra leaf, directory, empty directory, or nested path could escape the
final lifecycle even though Git still reported only Exact10. It also hard-coded
post-commit validation to two worktrees. A detached candidate passing that
topology did not prove that the formal single-worktree commit on `main` could
pass.

Revised1 restores the predecessor's bounded, FD-pinned recursive inventory for
the repository root, four support roots, derived parent, formal derived root,
and all six held regular leaves. It rejects ignored and empty residue without
depending on Git's untracked inventory, and it validates both supported
post-commit closures: formal `main` with one worktree and detached candidate
with `main` at the base across exactly two worktrees. The second complete
lifecycle runs after candidate validation and is the final filesystem, Git, and
candidate validation operation.

`PRE_036` remains the only transition. Stage-global orchestration is still not
implemented, the feature-semantics audit remains incomplete, and
`ready_for_training` remains false.

## Persistent ref namespace lifecycle closure

The aggregation business implementation and the FD-pinned lifecycle revision
remain unchanged. The earlier checker inspected only `refs/heads` and
`refs/tags`, so an arbitrary persistent ref in another namespace could survive
both lifecycle passes. The revised checker records the complete deterministic
Git ref inventory as normalized refname, object SHA, and object type tuples,
then requires the records to remain byte-for-byte stable across the initial,
prefinal, and final closures.

The only local branch ref is `refs/heads/main`. The remote whitelist contains
only `refs/remotes/origin/main` and optional `refs/remotes/origin/HEAD`.
Platform-managed records under `refs/codex/turn-diffs` are explicitly allowed,
preserved, and included in snapshot equality; all other persistent namespaces
fail closed. The `main` ref must also match the main worktree HEAD in the
single-worktree formal-main and two-worktree detached-candidate topologies.

Production and all five CSV evidence files remain byte-identical. `PRE_036`
remains the only transition, orchestration is still unimplemented, the
feature-semantics audit remains incomplete, and `ready_for_training` remains
false.

## Platform and remote ref trust-boundary closure

The aggregation business implementation and the complete-ref-inventory
lifecycle revision remain unchanged. The earlier namespace policy trusted
every child of `refs/codex/turn-diffs` without authenticating either its
platform-managed name shape or its Git object type. That allowed a task,
stage, or candidate ref to be disguised inside the platform prefix.

The revised policy freezes an anchored, full-match grammar for the two
observed managed forms: capture refs contain a 13-digit identifier, lowercase
RFC 4122 UUIDv4, and terminal `base`; checkpoint refs contain two 64-character
lowercase hexadecimal identifiers, a 13-digit identifier, and lowercase RFC
4122 UUIDv4. Only tree objects are trusted under those names. Commit, tag,
blob, task, stage, candidate, temporary, backup, and review disguises fail
closed. The complete structured ref records still participate in exact
initial, prefinal, and final lifecycle equality.

Remote names are no longer sufficient by themselves. In pre-commit state,
`main`, `HEAD`, and the base commit coincide, and an optional `origin/main`
must remain at the base. A formal-main post-commit remote may point only to
the base or the committed candidate HEAD. A detached post-commit candidate
requires both local and optional remote `main` to remain at the base, so the
candidate is not retained by a remote ref. Whenever `origin/HEAD` exists, its
resolved object must equal `origin/main`.

Production and all five CSV evidence files remain byte-identical. `PRE_036`
remains the only transition, stage-global orchestration is still not
implemented, the feature-semantics audit remains incomplete, and
`ready_for_training` remains false.
