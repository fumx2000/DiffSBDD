# CovaPIE ADMIT_009 unified adapter contract design gate v1

This design-only gate freezes the future unified adapter boundary for `ADMIT_009 / duplicate_identity_precheck`. It does not implement `_evaluate_registered_admit_009`, create an evaluator registry, modify the Exact8 runtime, or create an Exact9 runtime.

## Frozen contract

- Adapter identity: `covapie_admit_009_unified_adapter_v1`.
- Current registry order: `ADMIT_001` through `ADMIT_008`; future order appends only `ADMIT_009`.
- The future Exact9 runtime must reuse the Exact8 public result type, dispatch error type, and public schema/error constants by object identity. Its first eight handler objects must also be reused by identity.
- Exact9 cannot reuse the Exact8 `evaluate_admission_rule` function object: a Python function retains the globals of the module where it was defined, so that object would continue reading Exact8's eight-entry registry. Exact9 must define a new successor dispatcher with the complete Exact8 signature and dispatch semantics, while reading Exact9's own nine-entry `EVALUATOR_REGISTRY`. The new function is therefore not identical to Exact8's dispatcher; this is a design contract only, not a runtime implementation.
- Context gates run in the frozen order: batch Mapping and required key, evaluation Mapping and required key, download `None`, stage `None`, then candidate Mapping and required key.
- Required Mapping values use one direct lookup. Only `KeyError` means absent; present values are forwarded without copying, normalization, sorting, deduplication, repair, or provider mapping.
- Context failure is an Exact6 `UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID` boundary with `adapter_ready=true`, no candidate access, no formal/oracle call, and no partial Exact13.
- Candidate non-Mapping and key absence return adapter-generated Exact13 invalid results with formal/oracle counts `0/0`.
- A successful candidate gate forwards the original scalar, batch, and policy objects positionally to `evaluate_admit_009` exactly once.
- The returned object must have exact committed `Admit009EvaluationResult` type and pass complete Exact10 storage order, dataclass order, ordered-read, reconstruction, equality, and post-init invariant validation before the oracle is called.
- The committed design oracle receives the same three objects exactly once. Source and oracle-derived results must be fully equal across all Exact10 fields.
- Projection preserves source outcome fields and consumed fields, sets both normalized and validated values from `source.validated_candidate_fields`, and adds the frozen unified schema, rule name, and adapter ID.
- Source type, invariant, or oracle mismatch is `UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY` with `adapter_ready=false` and no partial Exact13.

## Evidence

The gate materializes exactly six deterministic artifacts: a 75-row contract, 52-row natural routing matrix, 49-row projection truth matrix, 35-row safety audit, byte-identical Exact11 issue inventory, and one manifest. The manifest has 130 top-level keys and an exact 36-item readiness map containing 20 true and 16 false values.

The production gate and independent checker separately freeze an ordered Exact18 committed-source boundary at base `0c80b0b8ac4e5f874a99c9f8da03f530ad7cc09e`. Structural checks precede explicit byte reads, and expected, base-tree, and filesystem SHA256 values must agree. The checker owns its identities, schemas, reasons, source paths and hashes, row semantics, readiness expectations, manifest checks, and output hashes. Its `enforce_frozen_hashes=False` mode still rejects semantic tampering.

The output issue inventory is byte-identical to the ADMIT_009 standalone predecessor. `DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED` remains resolved with transition `duplicate_identity_key_contract_frozen_v1`. Unified coverage remains open for `ADMIT_009` through `ADMIT_015`; this design step makes no issue transition and does not remove `ADMIT_009` from coverage.

## Readiness and stop boundary

The adapter contract, context routing, candidate projection, source/oracle equality, and future identity obligations are frozen. The actual adapter is not implemented, `ADMIT_009` is not registered, provider mapping is not validated, and the real provider key count remains zero. `ADMIT_010`, `evaluate_all_rules`, combined verdict, real candidate evaluation, bulk download, and training remain outside this step.

The only recommended next step is `implement_covapie_unified_dispatch_runtime_with_admit_001_to_009_v1`; it was not started here. Formal training still requires a separate feature-semantics audit. Step12D remains only a smoke-legality check, not a final training-feature contract.
