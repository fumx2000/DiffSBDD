# CovaPIE ADMIT_010 unified adapter contract design gate v1

This design-only gate freezes the future unified adapter boundary for `ADMIT_010 / leakage_group_assignment_before_split`. It does not implement `_evaluate_registered_admit_010`, create an Exact10 registry or dispatcher, modify the current Exact9 runtime, or register ADMIT_010.

## Frozen contract

- Adapter identity: `covapie_admit_010_unified_adapter_v1`.
- Current registry order: `ADMIT_001` through `ADMIT_009`; future order appends only `ADMIT_010`.
- The future Exact10 runtime must reuse the current Exact9 public result/error types and public constants by object identity. Its first nine handler objects must also be reused by identity.
- The successor dispatcher must be a new function object with exactly the current dispatcher signature and must read the successor module's local immutable ten-entry registry. Reusing the current function object would retain its current module globals and nine-entry registry.
- Context gates run in the frozen order: batch exact `None`, evaluation `Mapping` plus required-key lookup, download exact `None`, stage exact `None`, then candidate `Mapping` and required-key lookup.
- Required Mapping values use one direct lookup. Only `KeyError` means absent; present values are forwarded without copying, normalization, sorting, deduplication, repair, or provider mapping.
- Context failure is an Exact6 `UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID` boundary with `adapter_ready=true`, no candidate access, no formal/oracle call, and no partial Exact13.
- Candidate non-Mapping and key absence return adapter-generated Exact13 invalid results with formal/oracle counts `0/0`.
- A successful candidate gate forwards the original leakage-group scalar and provenance object positionally to `evaluate_admit_010` exactly once.
- The returned object must have exact committed `Admit010EvaluationResult` type and pass complete Exact10 storage order, dataclass order, ordered-read, reconstruction, equality, and post-init invariant validation before the oracle is called.
- The committed design oracle receives the same two objects exactly once. Source and oracle-derived results must be fully equal across all Exact10 fields.
- Projection preserves source outcome fields and consumed fields, sets both normalized and validated values from `source.validated_candidate_fields`, and adds the frozen unified schema, rule name, and adapter ID.
- Source type, invariant, or oracle mismatch is `UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY` with `adapter_ready=false` and no partial Exact13.

## Evidence

The gate materializes exactly six deterministic artifacts: a 62-row contract, 39-row natural routing matrix, 85-row projection truth matrix, 35-row safety audit, byte-identical Exact11 issue inventory, and one manifest. The projection matrix contains all committed Exact71 cases in exact identity/order plus natural routing, candidate-envelope, source-validation, and oracle-mismatch cases.

The production gate and independent checker separately freeze an ordered Exact15 committed-source boundary at base `4090769a3036e4019a65ce93ae61bd5ac8408983`. Structural checks precede explicit byte reads, and expected, base-tree, and filesystem SHA256 values must agree. The checker owns its identities, schemas, reasons, source paths and hashes, row semantics, readiness expectations, manifest checks, and output hashes. Its `enforce_frozen_hashes=False` mode still rejects semantic tampering.

The output issue inventory is byte-identical to the ADMIT_010 standalone predecessor. `LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED` remains resolved. Unified coverage remains open for `ADMIT_010` through `ADMIT_015` with transition `admit_009_implemented_and_removed_from_open_coverage_scope`; this design step makes no issue transition and does not remove `ADMIT_010` from coverage.

## Readiness and stop boundary

The adapter contract, context routing, candidate projection, Exact10 source/oracle equality, Exact13 projection, and future identity obligations are frozen. The actual adapter is not implemented, `ADMIT_010` is not registered, provider mapping is not validated, and the real provider ID count remains zero. ADMIT_011, `evaluate_all_rules`, combined verdict, real candidate evaluation, bulk download, and training remain outside this step.

The only recommended next step is `implement_covapie_unified_dispatch_runtime_with_admit_001_to_010_v1`; it was not started here. Formal training still requires a separate feature-semantics audit. Step12D remains only a smoke-legality check, not a final training-feature contract.

## revised1 checker freeze and containment

The revised1 checker independently validates resolved output containment before directory iteration, output parsing or byte reads, and source verification. A parent-directory symlink therefore fails closed before any output or source byte is read; normal repository-relative and real absolute output directories remain accepted.

The checker now owns and enforces complete equality for every field and row of the Exact62 contract, Exact39 routing matrix, Exact85 projection truth matrix, and Exact35 safety audit, plus every scalar and nested value of the Exact123 manifest. Semantic-tamper tests exercise these complete freezes with frozen-output hash enforcement disabled, so refreshed CSV hashes cannot conceal contract drift.

This revised1 change is checker/test/documentation hardening only. It does not alter the adapter design, production gate, readiness, issue or coverage state, or any of the six frozen outputs.
