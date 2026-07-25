# CovaPIE combined candidate verdict and cross-rule aggregation contract v1

## Scope

This design-only stage freezes the future pure in-memory cross-rule aggregation
API, its Exact15 single-rule input validation, the immutable combined verdict
Exact13 result, deterministic fail-closed precedence, full-vector aggregation,
and readiness for the next implementation stage.

It does not implement `aggregate_admission_rule_evaluations`, the future
`CombinedAdmissionCandidateVerdict` class, a dispatcher loop, a single-rule
handler call, an orchestrator, provider/network/download/raw work, or any
training action.

## Revised1 runtime-input compatibility

The original contract correctly froze the combined-verdict and aggregation
outcome as Exact3, but incorrectly described that subset as the complete
runtime vocabulary. Revised1 separates the runtime structural Exact4 from the
aggregation-admissible Exact3. It also removes the unsupported nested
uniqueness requirement and directly adds the actual runtime type owner to the
committed source boundary.

This compatibility revision does not change the future verdict Exact13, the
Exact4 scope memberships, or the Exact6 nonempty reasons. PRE, issues,
readiness, permission, and execution counts are unchanged. No aggregator,
combined-verdict runtime, dispatcher/handler call, or orchestrator is
implemented. Feature semantics remain incomplete and
`ready_for_training=false`.

## Stage-owned staging namespace closure

The runtime-input compatibility business revision above is unchanged. The
materializer had incorrectly retained the predecessor
`.combined-permission-semantics-stage-` staging prefix, which does not belong
to this stage's namespace. Because Git does not report empty directories, an
empty retained staging directory could also escape the checker's prior
derived-parent stage-family filter.

Materializer staging names now begin with the complete current `STAGE` plus
`.__staging__.`. The FD-pinned derived-parent scanner rejects both current
stage-owned staging directories and the legacy misnamed prefix, including
empty and partial retained staging, without relying on Git empty-directory
visibility. Staging symlinks are rejected without following their external
targets.

All five CSV artifacts remain byte-identical. This infrastructure closure
does not implement the aggregator or combined-verdict runtime, and it does
not change feature-semantics or training readiness:
`ready_for_training=false`.

## Embedded-stage residue lifecycle closure

The stage-owned staging namespace fix remains unchanged. A subsequent
checker regression narrowed support-root same-stage matching from substring
to prefix matching, allowing ignored names such as
`prefix_<STAGE>_residue` to escape both Git inventory and the recursive
scanner.

The four bounded support roots (`src/covalent_ext`, `scripts`, `tests`, and
`docs`) now treat the complete `STAGE` token at any basename position as
same-stage. When a matching directory is found, all descendants remain
observed even when their own names do not contain the stage token. The
derived parent retains its separate prefix-based current/legacy staging and
matching-root policy. An unrelated ignored regular file whose basename and
parent are outside the stage family remains allowed.

Production materializer behavior, the five CSV artifacts, and the aggregation
business contract remain unchanged. No aggregator or combined-verdict runtime
is implemented; feature semantics remain incomplete and
`ready_for_training=false`.

## Future public API

```python
aggregate_admission_rule_evaluations(
    scope_id: str,
    *,
    ordered_rule_evaluations:
        tuple[UnifiedAdmissionRuleEvaluation, ...],
) -> CombinedAdmissionCandidateVerdict
```

`scope_id` is positional-or-keyword and `ordered_rule_evaluations` is required
and keyword-only. There are no defaults, variadic parameters, candidate or
context inputs, dispatcher or registry injection, or override/fallback inputs.
The aggregator consumes an already generated and validated ordered result
vector. Dispatcher and single-rule handler call counts are both zero.

The module's
`classify_combined_candidate_verdict_contract_design` function is an
independent pure-memory contract oracle. Its two frozen mirror dataclasses are
not the future production classes and the child mirror is not the Exact15
runtime class.

## Exact13 input

The ordered vector element contract inherits the Exact15 runtime
`UnifiedAdmissionRuleEvaluation` fields:

1. `schema_version`
2. `admission_rule_id`
3. `admission_rule_name`
4. `outcome`
5. `passed`
6. `blocks_candidate`
7. `reason`
8. `normalized_values`
9. `validated_candidate_fields`
10. `consumed_candidate_fields`
11. `consumed_context_items`
12. `evaluator_io_used`
13. `adapter_id`

Exact type, `vars` key order, dataclass field order, top-level types,
reconstruction equality, schema, result invariants, no evaluator I/O, and
exact nested tuple structure are validated before membership. The actual
runtime type is owned by the minimal unified dispatch shell with ADMIT_004 and
allows the Exact4 outcome vocabulary
`passed|blocked|invalid|rejected`.

The combined-permission aggregation subset remains Exact3:
`passed|blocked|invalid`. A `rejected` child is therefore runtime structurally
valid but aggregation-inadmissible; it fails closed with
`COMBINED_ADMISSION_RULE_EVALUATION_INVARIANT_INVALID` and no child object is
retained. This does not add `rejected` to the future combined-verdict outcome.

The runtime nested contract freezes shape, not uniqueness. Duplicate keys in
`normalized_values` or `validated_candidate_fields`, and duplicate strings in
`consumed_candidate_fields` or `consumed_context_items`, are permitted. The
aggregator does not interpret, merge, deduplicate, copy, or reconstruct these
payloads.

## Exact4 memberships

- `download_execution_permission`: ordered Exact11
- `post_download_acceptance_permission`: ordered Exact13
- `pre_final_split_acceptance_permission`: ordered Exact14
- `training_execution_admission_permission`: ordered Exact15

The precise IDs and order are inherited unchanged from the committed combined
permission contract.

## Future Exact13 verdict

`CombinedAdmissionCandidateVerdict` is frozen as:

1. `schema_version`
2. `scope_id`
3. `outcome`
4. `passed`
5. `blocks_scope_action`
6. `reason`
7. `required_rule_ids`
8. `evaluated_rule_ids`
9. `rule_evaluations`
10. `invalid_rule_ids`
11. `blocked_rule_ids`
12. `failing_rule_ids`
13. `aggregation_io_used`

The fixed schema is `covapie_combined_admission_candidate_verdict_v1`.
Only a runtime-structurally valid, aggregation-admissible, membership-valid
vector retains child results, and it retains the exact input tuple object
without copying, reconstruction, reordering, scoring, weighting, voting, or
fallback.

## Reasons and precedence

Pass uses an empty reason. The closed six nonempty reasons are:

1. `COMBINED_ADMISSION_SCOPE_ID_INVALID`
2. `COMBINED_ADMISSION_RULE_EVALUATION_VECTOR_TYPE_INVALID`
3. `COMBINED_ADMISSION_RULE_EVALUATION_INVARIANT_INVALID`
4. `COMBINED_ADMISSION_RULE_MEMBERSHIP_INVALID`
5. `COMBINED_ADMISSION_REQUIRED_RULE_INVALID`
6. `COMBINED_ADMISSION_REQUIRED_RULE_BLOCKED`

Validation order is scope, exact tuple vector, all child runtime Exact13
structure, all child aggregation identity/outcome admissibility, full exact
membership, all invalid child outcomes, all blocked child outcomes, then all
passed. Known-rule name/adapter mappings and the aggregation Exact3 subset are
checked in the aggregation-admissibility phase; otherwise structurally valid
unknown rule IDs remain for membership validation. Outcome priority is
`invalid > blocked > passed`, but only after structure, aggregation
admissibility, and membership validation.

The full vector is scanned to collect all invalid, blocked, and failing rule
IDs in required order. There is no child-outcome short circuit.

## Continuity and readiness

PRE remains `42/0/3/3`; `PRE_036`, `PRE_038`, and `PRE_042` remain open.
`PRE_036` requires “implemented only after contract”, so this contract-only
stage does not resolve it.

The Exact30 issue inventory is inherited byte-identically with zero
transitions and no new issue. The only open issues remain
`COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED` and
`REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT`.

The contract and implementation-readiness flags are true. Aggregator,
combined verdict, dispatcher call-order, stage-global orchestration, training
integration, feature-semantics audit, and real-training readiness flags remain
false. `current_permission=false` and the authorized ADMIT_015 training
execution count remains zero.

The canonical five-mask contract retains `scaffold_only` / `B3`. A
feature-semantics audit remains mandatory before training: Step12D was only a
smoke legality check, and historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False` remain unresolved.

## Evidence and next step

The deterministic evidence set contains public API, result, truth-matrix,
safety, byte-identical issue inventory, and canonical manifest artifacts.
Production generation, checker-local reconstruction, disk observation, source
attestation, recursive lifecycle checks, and materializer hardening must all
agree.

The runtime-input compatibility revision expands the ordered committed source
boundary from Exact11 to Exact12 by directly attesting the actual type owner.
Its public API evidence is Exact24, result evidence remains Exact19, and the
truth matrix is 201 rows across 23 groups. Tests construct actual runtime
`rejected` and duplicate-nested objects before projecting them into the design
mirror.

Recommended next step:

`implement_covapie_combined_candidate_verdict_and_cross_rule_aggregation_v1`
