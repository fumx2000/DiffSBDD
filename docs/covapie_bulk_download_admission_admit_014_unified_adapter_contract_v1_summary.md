# CovaPIE ADMIT_014 unified adapter contract v1

This design gate freezes, but does not implement, the future ADMIT_014
unified adapter. The committed standalone evaluator remains
`evaluate_admit_014`, with exact result type `Admit014EvaluationResult`.
The independent committed design oracle remains
`classify_admit_014_formal_evaluator_interface_design`, with exact result type
`Admit014EvaluationResultContractDesign`.

The future adapter identity is
`covapie_admit_014_unified_adapter_v1`. Its future handler is
`_evaluate_registered_admit_014(candidate_record: object, *,
batch_context: object, evaluation_context: object,
download_result_context: object, stage_authorization_context: object) ->
UnifiedAdmissionRuleEvaluation`. This handler is intentionally not defined by
this stage. The design evidence is an independent `inspect.Signature`: exactly
five required parameters, `candidate_record` positional-or-keyword, the four
contexts keyword-only, all annotated `object`, no variadic parameters, and
the design-only return annotation `UnifiedAdmissionRuleEvaluation`.

The fixed ordered Exact17 source boundary now records and verifies each real
Git identity from both `git ls-tree` and `git ls-files --stage`: exact path,
mode, 40-character lowercase blob ID, and index stage zero. Base-tree blob
bytes, index blob bytes, and the pinned filesystem bytes must be identical and
must match the frozen SHA256. No boolean blob placeholder is accepted.

Routing is frozen in this order:

1. `batch_context` must be exact `None`.
2. `evaluation_context` must be exact `None`.
3. `download_result_context` must be exact `None`.
4. `candidate_record` must be a `Mapping`; a non-Mapping returns the frozen
   invalid Exact13 result.
5. `stage_authorization_context` is forwarded without adapter prevalidation.
6. The formal evaluator is called exactly once.
7. Its standalone Exact9 is validated before the oracle is called.
8. The independent oracle is called exactly once with the same stage-context
   object.
9. All Exact9 field types and values must be equal.
10. The validated source is projected to the shared Exact13 result.

All 42 routing rows are executable evidence. Separate case specifications are
run through the simulator with instrumented candidate/stage mappings and
formal/oracle wrappers; dispatch result, reason, full result JSON, call order,
object identity, key accesses, and call counts are observed and compared with
the frozen expectation. `case_passed` is derived from that comparison. The
last 42 rows of the Exact61 truth matrix reuse those actual observations,
including the observed formal Exact9 representation, observed oracle Exact9
representation (or explicit `not_called`/exception evidence), and the full
Exact6 dispatch-error JSON for failed routes; they no longer copy expected
values into observed fields. The first 19 rows also derive `case_passed` from
the actual projected/simulated Exact13 type-and-value comparison.

`stage_authorization_context` is the only business authority, and
`current_stage_download_authorized` is its only ADMIT_014 target item. The
adapter performs zero direct target accesses and does not call iteration,
`len`, `.get`, or containment. A stable Mapping is accessed once by the formal
evaluator and once by the oracle, in that order. `None` and non-Mapping values
remain standalone business inputs, not context-routing errors. A stateful
Mapping that produces different formal and oracle results fails closed.

The shared Exact13 schema is unchanged. The common business fields and
`evaluator_io_used` are copied from Exact9. The schema version, rule name, and
adapter ID are fixed. An exact boolean canonical value is projected to the
lowercase string `"false"` or `"true"` in `normalized_values`.
`validated_candidate_fields` and `consumed_candidate_fields` are always empty.
`consumed_context_items` equals the standalone consumed stage-authorization
fields. The ADMIT_015 coexistence item
`current_stage_training_authorized` is never consumed or projected.

The future registry order is ADMIT_001 through ADMIT_014, preserving exact
object identity for the first thirteen handlers. ADMIT_015 remains known but
unregistered. The dispatcher remains single-rule; combined verdicts,
cross-rule aggregation, provider mapping, download execution, and mandatory
pre-download enforcement remain unimplemented.

This design resolves PRE_048 with 50 of 51 preconditions complete. PRE_049,
the registration/runtime boundary, remains the sole open blocking
precondition. The standalone Exact30 issue inventory is preserved
byte-for-byte with zero issue transitions, including coverage
`ADMIT_014|ADMIT_015`.

The independent checker re-runs the full routing, source/oracle negative, and
projection contracts after independently validating the candidate source and
all Exact17 Git blobs. It pins source and Exact6 output parent/root/leaf file
descriptors, retains all output leaf descriptors through a second inventory,
and revalidates six-field identities and lexical bindings. The manifest parser
rejects duplicate, missing, extra, or reordered top-level and frozen nested
keys. Lifecycle checks use `git check-ignore --no-index` and require the exact
same-stage Exact4, one derived root, Exact6, and the complete repository
untracked inventory to be exactly Exact10 before commit or empty after commit.

For a new output set, destination binding is checked immediately after the
no-replace rename, again after parent `fsync`, after the complete Exact6
post-read, and again after root `fsync`. Destination, parent, leaf,
extra/missing, and stat/open races fail closed. Existing identical sets remain
inode-preserving no-ops; `EEXIST` and GPFS `EINVAL` remain fail-closed with no
`os.replace` fallback.

Current permission remains false and the authorized ADMIT_014 download
execution count remains zero. No provider, network, download, or raw-data
operation is performed. No model, checkpoint, dataloader, or training path is
changed. A feature-semantics audit remains mandatory before training; Step12D
was a smoke legality check, not a final training-feature contract.

Recommended next step:
`implement_covapie_unified_dispatch_runtime_with_admit_001_to_014_v1`.
