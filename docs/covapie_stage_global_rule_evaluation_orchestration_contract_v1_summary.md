# CovaPIE stage-global rule evaluation orchestration contract v1

This stage freezes a design contract only. It does not implement
`orchestrate_stage_admission_scope`, a dispatcher loop, a candidate runtime
loop, or an aggregator call. It performs no provider, network, raw-data,
download, model, checkpoint, dataloader, or training action and grants no
current or action permission.

The independent checker recognizes exactly four repository lifecycle modes:
`pre_commit`, `detached_candidate_post_commit`,
`formal_main_post_commit_unpushed`, and `formal_main_post_push`. The formal
commit subject is frozen as
`add CovaPIE stage-global rule evaluation orchestration contract v1`.
Formal-main validation requires a single-parent commit directly above the
frozen BASE, an Exact10-only diff, ten regular `100644` modes, a clean
one-worktree topology, and lifecycle-specific closure of `main`,
`origin/main`, and symbolic `origin/HEAD`. Thus the checker remains executable
both before and after a formal push. Detached-candidate verification remains a
separate preflight and is not a substitute for formal-main lifecycle closure.

## Frozen future surface

The future production signature is:

```python
orchestrate_stage_admission_scope(
    scope_id: str,
    candidate_inputs: tuple[AdmissionCandidateOrchestrationInput, ...],
    *,
    batch_context: Mapping[str, object] | None,
    stage_authorization_context: Mapping[str, object] | None,
) -> StageAdmissionOrchestrationResult
```

The input envelope is a frozen, non-slotted Exact3 dataclass:
`candidate_record`, `evaluation_context`, and `download_result_context`.
Candidate results are frozen, non-slotted Exact5 values; the stage result is a
frozen, non-slotted Exact12 value with schema
`covapie_stage_admission_orchestration_result_v1`; and the frozen error
projection is an `Exception` with Exact8 fields and Exact8 codes. All four
future API parameters are required (`inspect.Parameter.empty`), and the CSV
records each default as `absent`. All top-level inputs are validated before
any future dispatcher attempt; a validation failure raises the same error
type with projection `(-1, "", 0, 0, code, "")`.

## Partition and cardinality

ADMIT_014 is stage-global in all Exact4 scopes. ADMIT_015 is stage-global only
for `training_execution_admission_permission`. Their order is ADMIT_014 then
ADMIT_015, each is evaluated exactly once per top-level invocation, and the
same result object is reused by identity in every candidate vector. They
receive the same immutable empty candidate sentinel and only the caller's
stage-authorization context identity.

Candidate-scoped rule counts are 10, 12, 13, and 13. For candidate count `N`,
dispatcher cardinalities are respectively `1 + 10*N`, `1 + 12*N`,
`1 + 13*N`, and `2 + 13*N`. Aggregation cardinality is always `N`, exactly
once per candidate.

The Exact53 occurrence plan preserves candidate tuple order, scope membership
order, handler-proven context routing, and zero-based vector position.
ADMIT_001 and ADMIT_009 receive batch context; ADMIT_004, ADMIT_006 through
ADMIT_013 (including ADMIT_009) receive candidate evaluation context;
ADMIT_012 and ADMIT_013 receive download-result context. Other candidate
context channels are `None`. ADMIT_014 and ADMIT_015 receive only stage
authorization context.

## Assembly and failure semantics

Each complete candidate vector is rebuilt in exact scope-required order by
inserting the already-produced candidate and stage-global result objects
without copying, reconstructing, re-evaluating, outcome sorting, or category
grouping. Normal `passed`, `blocked`, `invalid`, and `rejected` results do not
short-circuit orchestration; `rejected` remains the aggregator's fail-closed
responsibility. A dispatcher or aggregator exception is an orchestration
error and stops further attempts immediately without returning a partial
stage result or granting permission. Future runtime catches are limited to
`Exception`, delivery is `raise StageAdmissionOrchestrationError(...) from
cause`, `cause_type` is the exception class name, and neither `repr(cause)`
nor nondeterministic cause text enters the reason.

Failure counts are attempt-inclusive. With `G` stage-global rules, `R`
candidate rules, zero-based candidate `i`, one-based candidate-rule position
`j`, and one-based stage-rule position `k`, stage dispatch projects
`(-1, stage_rule_id, k, 0)`, candidate dispatch projects
`(i, candidate_rule_id, G+i*R+j, i)`, and candidate aggregation projects
`(i, "", G+(i+1)*R, i+1)`. Evidence covers all four scopes, candidate indices
0/1/2, first/middle/last rule positions, both training stage rules, and every
candidate aggregation position.

Pure validators fail closed on the Unified Exact13 and Combined Exact13
contracts, including exact type and storage order, reconstruction, schemas,
field projections, expected identities, and complete-vector membership. For
normal `passed`/`blocked`/`invalid` vectors, the combined validator requires
the aggregator verdict to retain the exact input tuple identity and its full
ordered diagnostics.

Unified `rejected` is structurally legal, so orchestration forwards the
complete scope-ordered vector without reinterpretation. The committed
aggregator admits only `passed`, `blocked`, and `invalid` child outcomes;
therefore any `rejected` child triggers its canonical fail-closed verdict:
`outcome="invalid"`, `passed=false`, `blocks_scope_action=true`,
`reason="COMBINED_ADMISSION_RULE_EVALUATION_INVARIANT_INVALID"`, the expected
`required_rule_ids`, and empty `evaluated_rule_ids`, `rule_evaluations`, and
all diagnostic tuples. The combined validator accepts exactly this projection
and no broader invalid verdict. Rejected admissibility failure precedes normal
outcome projection, including rejected mixed with blocked, invalid, or other
rejected children. This remains fail closed and is not reported as aggregator
result corruption.

## Evidence and readiness

The design evidence contains Exact54 API/result/error rows, Exact53 scope-rule
occurrence rows, 307 deterministic truth rows in 50 groups, and Exact30 safety
rows. The Exact30 issue inventory is byte-identical to its predecessor.
Effective PRE counts remain `43/0/2/2`, with no transition and PRE_038 and
PRE_042 still incomplete and implementation-blocking.

`current_permission=false`,
`authorized_admit_015_training_execution_count=0`, and actual
dispatcher/handler/aggregator calls are `0/0/0`.
`action_permission_granted` is always false in V1, even when every combined
verdict passes; a future bridge from diagnostics to action permission requires
a separate contract and gate.

This stage is ready only for
`implement_covapie_stage_global_rule_evaluation_orchestration_v1`.
It is not ready for training. Step12D was a smoke legality check, not a final
training-feature contract. The feature-semantics audit remains mandatory, and
the historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False` states remain unresolved.
