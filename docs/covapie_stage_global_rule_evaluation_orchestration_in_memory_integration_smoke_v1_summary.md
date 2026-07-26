# CovaPIE stage-global orchestration in-memory integration smoke V1

This increment exercises the committed stage-global orchestrator, the
ADMIT_001–015 unified dispatcher and standalone adapters, and the committed
combined aggregator with canonical synthetic objects held entirely in memory.
The successful evidence path does not replace a dispatcher, handler registry,
aggregator, or orchestrator callable.

Two fixed fixture profiles are covered. The single-candidate profile runs all
four canonical permission scopes while retaining the same candidate and
context object identities. The two-candidate profile runs the training
admission scope with distinct candidate identities, unique candidate-record
and duplicate-identity keys, a complete ADMIT_001 batch identity vector, and
an empty pre-existing ADMIT_009 duplicate-key snapshot.

The committed runtime outcome is intentionally not an all-pass claim.
ADMIT_001–013 pass for the audited synthetic values. ADMIT_014 returns
`blocked / BULK_DOWNLOAD_NOT_AUTHORIZED`; ADMIT_015 returns
`blocked / TRAINING_NOT_AUTHORIZED` in the training scope. The combined
verdict is therefore `blocked / COMBINED_ADMISSION_REQUIRED_RULE_BLOCKED`.
Every orchestration result has `orchestration_io_used=false` and
`action_permission_granted=false`.

The checker independently repeats the committed context routing, direct
dispatcher calls, complete ordered-vector construction, and combined
aggregation. It compares all Exact13 unified result fields, all Exact13
combined verdict fields, and the stage-result membership, partition,
cardinality, safety, and permission fields. Three smoke executions,
serializations, scope matrices, parity matrices, and evidence builds must be
byte-identical.

Field parity and object identity are deliberately separate claims. Field
parity compares deterministic values across the orchestrator execution and a
second, independent direct dispatcher-plus-aggregator execution. It does not
claim that objects from those two executions share identity.

Object identity is instead verified inside each individual execution graph
with `is`. For every scope and candidate, each stage-global rule result in the
candidate's ordered vector is the same object held in that execution's
stage-global result tuple. For every canonical normal
passed/blocked/invalid aggregation branch, the combined verdict's
`rule_evaluations` is the same tuple object supplied as its ordered vector.
The orchestrator graph and direct-baseline graph are checked independently;
an equal copied stage result or vector fails closed.

The issue inventory is inherited byte-for-byte from the committed
orchestration runtime. The effective-open issues remain exactly
`COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED` and
`REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT`.

This smoke does not perform network access, provider execution, download,
raw-data access, Torch/model/checkpoint/dataloader work, forward or loss
evaluation, backward propagation, optimizer/scheduler steps, parameter
updates, checkpoint writes, or training.

Training readiness remains closed. Step12D was a smoke legality check, not a
final training-feature contract. `UNKNOWN_ATOM_FEATURE_POLICY` remains
unresolved, `feature_semantics_known=False`, and a feature-semantics audit is
required before formal training or any parameter update.

The canonical mask contract remains exactly:

1. `warhead_only / A`
2. `linker_plus_warhead / B`
3. `scaffold_plus_warhead / B2`
4. `scaffold_only / B3`
5. `scaffold_plus_linker_plus_warhead / C`

The recommended next step is
`design_covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_v1`.
That step should design fail-closed consumption of orchestration diagnostics
without executing a real download.
