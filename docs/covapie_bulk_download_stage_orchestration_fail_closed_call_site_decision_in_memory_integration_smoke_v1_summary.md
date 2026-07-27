# CovaPIE call-site decision actual-chain in-memory integration smoke V1

This increment connects the committed canonical in-memory fixtures to the
actual stage orchestrator and then to the committed bulk-download call-site
decision runtime. The public no-argument API returns a frozen report with six
observations:

1. the single-candidate fixture through all four canonical scopes;
2. the two-candidate fixture through the training scope; and
3. an invalid-scope request that produces and passes through the actual
   `StageAdmissionOrchestrationError`.

The download scope reaches the current `ADMIT_014` block and produces
`BULK_DOWNLOAD_CANDIDATE_VERDICT_BLOCKED`. The other three Exact4 scopes and
the two-candidate training scope produce
`BULK_DOWNLOAD_STAGE_SCOPE_INVALID`; wrong-scope precedence deliberately
suppresses candidate diagnostic indexes. The actual invalid-scope error
produces `BULK_DOWNLOAD_ORCHESTRATION_ERROR_FAIL_CLOSED`.

The smoke freezes and compares the actual orchestrator, decision runtime,
dispatcher, evaluator registry, all registered handler identities, and
aggregator before and after execution. Success evidence uses no replacement,
injection, forged error, design classifier, decision private helper, action
callable, or fallback implementation.

The independent checker executes its own five result chains and one error
chain. It constructs the expected Exact15 projections from the committed
contract semantics and verifies all 75 result-field rows and 15 error-field
rows with exact types. Three public reports, their serialized bytes, three
result matrices, three error matrices, and all generated evidence are
deterministic.

No download callable is accepted or invoked. Authorized decisions, download
actions, and call-site I/O all remain zero. Provider, network, raw-data,
model, checkpoint, data-loader, forward, loss, backward, optimizer,
parameter-update, and training operations are absent.

The canonical V1 mask contract remains exactly:

1. `warhead_only / A`
2. `linker_plus_warhead / B`
3. `scaffold_plus_warhead / B2`
4. `scaffold_only / B3`
5. `scaffold_plus_linker_plus_warhead / C`

The inherited issue inventory is byte-identical. The effective-open issues
remain `COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED` and
`REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT`.

Step12D was a smoke legality check, not a final training-feature contract.
`UNKNOWN_ATOM_FEATURE_POLICY` remains unresolved,
`feature_semantics_known=False`, and a feature-semantics audit remains
mandatory before formal training. Both download readiness and training
readiness remain false.

The recommended next step is
`design_covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_v1`.
That design step must not perform a real download.
