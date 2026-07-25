# CovaPIE ADMIT_015 mandatory training-authorization enforcement contract v1

This design-only stage freezes the future mandatory ADMIT_015 training guard.
It does not implement the guard, connect it to a training orchestrator, or
perform any training, model, checkpoint, provider, network, download, or raw
data operation.

## Frozen future API

The future public entry point is exactly:

```text
require_admit_015_training_authorization(candidate_record: Mapping[str, object], *, stage_authorization_context: Mapping[str, object] | None) -> UnifiedAdmissionRuleEvaluation
```

The future guard owns the call to the committed Exact15 single-rule runtime.
For each future real training invocation it must call that runtime exactly
once, select `ADMIT_015`, pass `None` for `batch_context`,
`evaluation_context`, and `download_result_context`, and forward the same
`stage_authorization_context` object.

The future API accepts neither a precomputed bool nor a precomputed or replayed
ADMIT_015 result. It accepts no combined verdict and no ADMIT_014 download
permission. Candidate fields, manifests, configuration, CLI values,
environment values, checkpoints, models, and dataloaders are not authorization
sources.

## Return and error contract

Only a fully validated exact
`UnifiedAdmissionRuleEvaluation` may return. Subclasses are rejected. Its
Exact13 field order is frozen, and release requires all of the following:

- schema `covapie_unified_admission_rule_evaluation_v1`;
- rule ID `ADMIT_015`;
- `outcome="passed"`, `passed=True`, `blocks_candidate=False`;
- empty reason and `evaluator_io_used=False`;
- adapter `covapie_admit_015_unified_adapter_v1`;
- normalized value
  `(("current_stage_training_authorized", "true"),)`;
- empty validated and consumed candidate fields;
- consumed context exactly
  `("current_stage_training_authorized",)`.

The future exact error type is
`Admit015TrainingAuthorizationEnforcementError`, with ordered fields
`schema_version`, `error_code`, `admission_rule_id`, and `reason`.
All four fields have exact built-in type `str`; the frozen constructor
representation is
`Admit015TrainingAuthorizationEnforcementError(schema_version: str, error_code: str, admission_rule_id: str, reason: str)`.
Dispatcher errors, wrong result type or subclass, field/type/value drift, every non-pass
outcome, contradictions, replay, repeated-call attempts, and override attempts
all raise fail closed.

A pass releases only a future in-memory continuation verdict. It does not
execute training and does not establish feature semantics, checkpoint
compatibility, dataset readiness, provider readiness, or real-training
readiness.

## Protected action boundary

The guard must precede exactly these 11 actions:

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

Every blocked, invalid, error, or drift path leaves all 11 counts at zero.
Neither a combined verdict nor ADMIT_014 download permission can release them.
The pure in-memory design simulator also leaves all counts at zero for its
synthetic pass cases.

## Evidence and transitions

The evidence consists of one API-contract CSV, the Exact11 protected-action
boundary, an Exact29 truth matrix across 23 groups, an Exact28 safety audit, a
byte-identical Exact30 issue inventory, and one manifest. The truth matrix
covers canonical pass and block, invalid candidate, missing or false
authorization, dispatcher failure, exact-type/subclass rejection, Exact13
drift and contradiction, replay and repeated-call attempts, ADMIT_014
isolation, combined-verdict non-override, protected-action zero counts, and
the design-only pass boundary.

Only PRE_034 is resolved. The Exact45 successor state is:

```text
complete=41
supported-but-not-frozen=0
incomplete=4
implementation-blocking=4
```

The remaining open set is exactly PRE_035, PRE_036, PRE_038, and PRE_042.
Combined permission semantics, cross-rule aggregation, feature semantics, and
real-training readiness remain unresolved.

The Exact30 inventory contains no matching ADMIT_015 mandatory-enforcement API
issue, so it is preserved byte-for-byte and has zero transitions. The required
open issues remain:

- `COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED`
- `REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT`
- `UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED`

Current permission remains false and the authorized ADMIT_015 real-training
execution count remains zero. Mandatory enforcement implementation, combined
candidate verdict, cross-rule aggregation, feature-semantics completion,
historical unknown-atom-policy resolution, and real-training readiness all
remain false.

The canonical V1 masks remain exactly
`warhead_only/A`, `linker_plus_warhead/B`,
`scaffold_plus_warhead/B2`, `scaffold_only/B3`, and
`scaffold_plus_linker_plus_warhead/C`. Step12D remains a smoke-legality check,
not a final training-feature contract. An explicit feature-semantics audit is
still mandatory before training.

## Revised1 checker closure

The frozen future API and every business conclusion above are unchanged.
Revised1 closes three checker-infrastructure gaps: the old checker used the
candidate artifact builder as its expected authority, its lifecycle scan was
limited to the derived parent, and its Exact6 reader returned after the final
leaf traversal without a final inventory and root/parent binding.

The checker now reconstructs the full evidence set and all 64 manifest keys
from checker-local frozen semantics, treating the candidate simulator only as
observed behavior. Its lifecycle inherits the Exact15 runtime checker's
FD-pinned, no-follow recursive scan across `src/covalent_ext`, `scripts`,
`tests`, and `docs`; the Exact6 reader ends with final inventory followed by
the final lexical/FD root-parent binding. Production and all six evidence
outputs remain byte-identical.

Recommended next step:

```text
implement_covapie_admit_015_mandatory_training_authorization_enforcement_v1
```
