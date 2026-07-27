# CovaPIE bulk-download orchestration action-permission bridge runtime v1

This increment implements the frozen bridge design contract as a deterministic,
pure in-memory runtime. The public evaluator accepts only an exact stage
orchestration result and an exact call-site decision as required keyword-only
arguments. It returns the shared frozen Exact19 decision type.

The runtime independently validates the complete StageResult, CandidateResult,
call-site decision, download scope, zero-I/O state, untransitioned source, and
the exact 15-field source-lineage projection. It does not delegate to the design
classifier or private predecessor helpers.

The current canonical chain remains blocked because ADMIT_014 is blocked. A
separate authorization mapping with `current_stage_download_authorized=True`
produces an all-passed source pair and an `eligible` bridge decision. Eligibility
does not grant permission: every runtime output keeps action permission,
download invocation, and bridge I/O false.

Evidence covers the committed design contract's exact 50 case IDs in seven
groups and records 950 field-level expected/design/runtime Exact19 comparisons.
The reserved reason
`ACTION_PERMISSION_BRIDGE_CALL_SITE_DECISION_NOT_PERMISSION_PENDING` remains
unreachable because exact lineage admits no authorized-decision exception.

No provider, network, raw structure, download, model, checkpoint, dataloader,
forward, loss, backward, optimizer, scheduler, parameter update, checkpoint
write, or training operation is used. `ready_for_download` and
`ready_for_training` remain false. Step12D remains only a smoke legality check;
the unresolved feature-semantics audit is still required before training.

Recommended next step:
`run_covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_v1`.
