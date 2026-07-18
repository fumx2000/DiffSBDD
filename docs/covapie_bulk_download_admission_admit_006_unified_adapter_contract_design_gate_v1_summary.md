# CovaPIE ADMIT_006 unified adapter contract design gate v1

This design-only gate freezes the future `ADMIT_006` adapter contract without implementing a handler or modifying the current Exact5 runtime registry.

The future registration identity is `ADMIT_006` / `explicit_covalent_event_evidence` / `covapie_admit_006_unified_adapter_v1`. The formal evaluator remains `evaluate_admit_006`, and the future registry order is `ADMIT_001` through `ADMIT_006`. The adapter must reuse the existing `evaluate_admission_rule`, `UnifiedAdmissionRuleEvaluation`, `UnifiedAdmissionDispatchError`, Exact13 result, and Exact6 dispatch-error identities.

Execution precedence is frozen as global ID validation, known-rule validation, adapter readiness, four ordered context-envelope gates, candidate Mapping validation, required-field presence, adapter missing-value classification, one positional formal-evaluator call, exact-type and Exact10 invariant validation, one independent oracle derivation, complete Exact10 equality, and Exact13 construction. All context routing completes before candidate access. Source prevalidation completes before the independent oracle.

`evaluation_context` accepts `Mapping` subclasses, requires `allowed_covalent_evidence_classes`, ignores extra keys, and routes the original value object without internal prevalidation. The other three contexts require exact `None`. Envelope failures produce Exact6 dispatch errors; routed value failures remain standalone semantic failures and project to Exact13 invalid results.

The candidate accepts `Mapping` subclasses and ignores extra fields without copying or mutation. A non-Mapping candidate produces Exact13 invalid with `ADMIT_006_CANDIDATE_RECORD_MAPPING_INVALID`. A missing key, exact `None`, or exact built-in empty string produces `covalent_event_evidence_missing` without evaluator or oracle calls. Empty string subclasses, whitespace, malformed objects, and `distance_only_inference` are not missing and reach the standalone evaluator unchanged.

The source must be exact `Admit006EvaluationResult`; subclasses and all Exact10 invariant violations fail with `UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY`. Only after this validation may the independent `classify_admit_006_admit_007_evidence_design` oracle run once on the same original objects. Complete mismatch prevents Exact13 projection.

Projection preserves standalone outcome semantics. Explicit evidence passes; distance-only evidence remains `blocked`; scalar-invalid results retain empty canonical state; context-invalid results with valid scalar retain their canonical and validated pair. `normalized_values` is exactly the standalone `validated_candidate_fields` and adds no normalization.

Evidence consists of 43 contract rows, 23 non-padding routing rows, and 56 projection rows: standalone Exact37 (37), adapter candidate invalid (4), routing dispatch (5), source failures (4), projection semantics (4), and runtime boundary (2). The predecessor Exact11 issue inventory is emitted byte-identically. `UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE` remains open and still includes `ADMIT_006`.

The gate marks readiness only for `implement_covapie_unified_dispatch_runtime_with_admit_001_to_006_v1`. It does not claim an implemented adapter, registration, ADMIT_007 work, provider mapping, real evaluation, bulk-download readiness, or training readiness. A feature-semantics audit remains mandatory before training; Step12D was only a smoke legality check, not the final training-feature contract.
