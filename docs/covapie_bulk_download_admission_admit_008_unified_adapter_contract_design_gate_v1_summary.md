# CovaPIE ADMIT_008 unified adapter contract design gate v1

This design-only gate freezes the future unified adapter contract for `ADMIT_008 / topology_restoration_disposition`. The adapter identity is `covapie_admit_008_unified_adapter_v1`; its formal evaluator is `evaluate_admit_008`, and its independent design oracle is `classify_admit_008_topology_restoration_disposition_design`.

The future Exact8 runtime must reuse the current Exact7 `evaluate_admission_rule`, `UnifiedAdmissionRuleEvaluation`, `UnifiedAdmissionDispatchError`, Exact13 result schema, Exact6 dispatch-error schema, known-rule vocabulary, and global dispatch precedence by identity. The frozen registry order is ADMIT_001 through ADMIT_008, while the committed runtime remains ADMIT_001 through ADMIT_007.

Context routing is fail-closed in batch, evaluation Mapping, evaluation required-key, download-result, then stage-authorization order. Only `evaluation_context` is a Mapping; its `allowed_topology_restoration_dispositions` value is retrieved once and forwarded unchanged. Context failures occur before candidate access.

The candidate envelope accepts Mapping subclasses and ignores unrelated fields. Only absence of `topology_restoration_disposition` is adapter missing (`topology_restoration_disposition_missing`). Exact `None`, exact empty string, empty string subclasses, whitespace, malformed values, and unknown canonical-looking strings are forwarded unchanged to the standalone evaluator. Candidate non-Mapping is an adapter-generated invalid Exact13 result.

After the candidate gate, the formal evaluator is called exactly once positionally. Its return must have the exact committed `Admit008EvaluationResult` type, Exact10 field/storage order, successful committed-dataclass reconstruction, equality, and complete cross-field invariants. Only then is the committed independent oracle called once with the same two original objects. Complete Exact10 equality is required before Exact13 projection.

Projection preserves passed, both distinct blocked outcomes and reasons, scalar-invalid empty canonical state, and context-invalid canonical pairs. `normalized_values` is exactly `source.validated_candidate_fields`. The generated evidence contains 54 contract rows, an Exact26 routing matrix, 52 natural truth rows, 40 safety rows, a byte-identical Exact11 issue inventory, and one manifest. All 17 committed source inputs are pinned to the base-tree and filesystem SHA256 values.

No adapter handler, registry entry, runtime modification, provider mapping, real candidate evaluation, ADMIT_009 work, aggregation, raw access, download, model execution, or training is performed. The next authorized step is `implement_covapie_unified_dispatch_runtime_with_admit_001_to_008_v1`. A separate feature-semantics audit remains mandatory before training; Step12D was only a smoke legality check, not the final training-feature contract.
