# CovaPIE ADMIT_011 unified adapter contract design gate v1

This design-only gate freezes the future unified adapter boundary for
`ADMIT_011 / raw_overwrite_forbidden`. It does not implement
`_evaluate_registered_admit_011`, modify or define `EVALUATOR_REGISTRY`, bind
`evaluate_admission_rule`, or change the current ADMIT_001–010 runtime.

The current registered order remains ADMIT_001–010. The future order appends
only ADMIT_011; ADMIT_001–015 remain the exact known-rule set. The adapter
candidate field is `raw_target_relative_path`. It consumes evaluation context
in contract-then-snapshot order, while calling the formal evaluator and the
independent design oracle in candidate-snapshot-contract positional order.
Every required Mapping value is read exactly once, Mapping subclasses and
unrelated keys are accepted, and the three original objects retain identity.

All context checks precede candidate access. Context failures are design-only
Exact6 `UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID` errors with
`adapter_ready=true`. Candidate non-Mapping and missing-field failures are
Exact13 invalid results with no formal or oracle call. After routing, the
formal `evaluate_admit_011` is called exactly once. Its return must be exact
`Admit011EvaluationResult`, with Exact10 storage/field order, exact built-in
types, successful reconstruction/post-init validation, and full invariants.
Only then is the exact `Admit011EvaluationResultDesign` oracle called once.
The oracle is independently reconstructed into formal Exact10 and all ten
values and types must match before projection.

Exact13 projection preserves the standalone outcome, reason, flags, validated
and consumed fields, and `evaluator_io_used=false`. Both `normalized_values`
and `validated_candidate_fields` equal `source.validated_candidate_fields`.
No path normalization, repair, decoding, filesystem resolution, copying,
provider mapping, or mutation occurs in the adapter algorithm.

The gate publishes exactly six deterministic artifacts: a 26-row contract,
33-row routing matrix, 84-row unified projection truth matrix containing all
47 historical cases, 32-row safety audit, byte-identical Exact11 issue
inventory, and one manifest. Its fixed ordered Exact16 source boundary is
rooted at `da7367cfdcf54bff8c30e05ba6f7d16cc5dbda2e` (`add CovaPIE ADMIT_011
standalone evaluator interface v1`) and attests the standalone source and six
evidence files, path-contract oracle/manifest/truth, current Exact10 runtime
source/manifest, and ADMIT_009/010 design precedents and manifests.

The evidence materializer performs a read-only structural preflight, builds
all payloads before mutation, pins parent/root/staging/leaf identities, writes
an exclusive same-directory staging set with `O_NOFOLLOW`, fsyncs files and
directories, and publishes with `renameat2(RENAME_NOREPLACE)`. An exact
existing set is an inode-preserving no-op; mismatch and race states fail
closed, and cleanup never removes unknown staging entries.

`RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED` remains resolved. Unified coverage
remains open for ADMIT_011–015, including ADMIT_011, and cross-rule aggregation
semantics remain open. Provider, download-integrity, combined-verdict, and
training blockers remain unchanged. The runtime adapter and registration are
false, as are provider mapping, real evaluation, bulk-download, checkpoint,
canonical-repository, and training readiness. A feature-semantics audit is
still mandatory before training; Step12D remains a smoke-legality check rather
than a final training-feature contract.

The only recommended next step is
`implement_covapie_unified_dispatch_runtime_with_admit_001_to_011_v1`; it was
not started in this stage.

## Revised1 exact semantic checker hardening

The revised checker owns and compares the complete ordered semantics of the
Exact26 contract (all six columns), Exact33 routing matrix (all thirteen
columns), Exact84 truth matrix (all eleven columns), and Exact32 safety audit
(all four columns). The truth check additionally freezes the
`exact10_to_exact13` behavior and the empty expected dispatch code. The
candidate-invalid JSON used by the routing oracle is constructed from
checker-owned literals rather than imported production helpers.

Negative tests mutate every governed column and representative row/column
shape properties, then recompute the corresponding manifest output SHA256.
This proves that the checker rejects synchronized semantic tampering instead
of relying only on a stale-hash mismatch. The production source and all six
published evidence files remain byte-for-byte unchanged.

The frozen routing evidence uses `mapping_subclass` and `extra_keys` as local
case identifiers in more than one matrix group. Because this revision may not
rewrite published evidence, routing identity is therefore frozen as the
ordered composite `(matrix_group, case_id)`; duplicate composite identities,
row reordering, row insertion, row removal, and any field-level drift all fail
closed.
