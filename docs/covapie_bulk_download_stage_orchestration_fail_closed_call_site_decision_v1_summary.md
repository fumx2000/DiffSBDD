# CovaPIE bulk-download orchestration fail-closed call-site decision V1

This increment implements the formal deterministic, in-memory call-site
decision API:

```python
evaluate_bulk_download_stage_orchestration_call_site(
    *,
    orchestration_result:
        StageAdmissionOrchestrationResult | None,
    orchestration_error:
        StageAdmissionOrchestrationError | None,
) -> BulkDownloadStageOrchestrationCallSiteDecisionDesign
```

The runtime reuses the committed Exact15 decision class by identity. It
independently enforces exact-one-of input cardinality, exact source types,
Exact8 orchestration-error validity, the deep Exact12 stage-result and Exact5
candidate-result graph, committed Unified and Combined validators, retained
identity requirements, scope, orchestration-I/O, permission, and candidate
precedence. It does not call the frozen design classifier or its private
helpers.

All decisions keep `download_action_invoked=false` and
`call_site_io_used=false`. V1 has zero authorized decisions and no download
callable. A true action permission is treated as an unauthorized transition.

The checker independently constructs the closed 77-case, 11-group source
registry. For every case it compares the runtime Exact15 projection with both
the frozen truth CSV and the committed design classifier. The field-level
matrix therefore contains `77 × 15 = 1155` rows, all with exact-type and
three-way parity.

The current committed-orchestrator path uses
`scope=download_execution_permission`, one candidate, and an `ADMIT_014`
blocked verdict. The runtime projects candidate index `0` as blocked and
returns `BULK_DOWNLOAD_CANDIDATE_VERDICT_BLOCKED`, with no permission, action,
or call-site I/O.

The issue inventory remains byte-identical to the design-contract stage.
`COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED` and
`REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT` remain open.

The canonical V1 mask contract remains exactly:

1. `warhead_only / A`
2. `linker_plus_warhead / B`
3. `scaffold_plus_warhead / B2`
4. `scaffold_only / B3`
5. `scaffold_plus_linker_plus_warhead / C`

Step12D was a smoke legality check, not a final training-feature contract.
`UNKNOWN_ATOM_FEATURE_POLICY` remains unresolved and
`feature_semantics_known=False`. A feature-semantics audit remains mandatory
before formal training; this increment performs no model, data-loader,
optimization, parameter-update, checkpoint, provider, network, raw-data, or
training operation.

The recommended next step is
`run_covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_in_memory_integration_smoke_v1`.
That step must also perform no real download.
