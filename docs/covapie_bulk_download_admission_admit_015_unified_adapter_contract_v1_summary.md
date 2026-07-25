# CovaPIE ADMIT_015 unified adapter contract v1

This design gate freezes, but does not implement, the future ADMIT_015
unified adapter. The committed standalone evaluator remains
`evaluate_admit_015`, with exact result type `Admit015EvaluationResult`.
The independent committed design oracle remains
`classify_admit_015_formal_evaluator_interface_design`, with exact result type
`Admit015EvaluationResultContractDesign`.

The future adapter identity is
`covapie_admit_015_unified_adapter_v1`. Its future handler is
`_evaluate_registered_admit_015(candidate_record: object, *,
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
`current_stage_training_authorized` is its only ADMIT_015 target item. The
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
fields. The download coexistence item
`current_stage_download_authorized` is never consumed or projected.

The future registry order is ADMIT_001 through ADMIT_015, preserving exact
object identity for the first fourteen handlers. ADMIT_015 is currently known
but unregistered; the frozen future Exact15 state has an empty
known-not-registered set. The dispatcher remains single-rule; combined
verdicts, cross-rule aggregation, provider mapping, download execution, and
mandatory training-authorization enforcement remain unimplemented.

This design resolves only PRE_031. The Exact45 transition is
`complete=38`, `supported_but_not_frozen=0`, `incomplete=7`, and
`implementation_blocking=7`. The remaining open set is exactly PRE_032,
PRE_033, PRE_034, PRE_035, PRE_036, PRE_038, and PRE_042. The standalone
Exact30 issue inventory is preserved byte-for-byte with zero issue
transitions, including coverage `ADMIT_015`.

The revised2 review found that the first 19 Exact61 truth rows did not verify
`routing_condition`. The independent checker now reconstructs and compares
all ten fields of all 61 rows, while re-running the full routing,
source/oracle negative, and projection contracts after independently
validating the candidate source and all Exact17 Git blobs. Production and
checker source readers retain the leaf,
all parent, and repository-root descriptors until a final second leaf
descriptor and lexical-name check. Real late rename/recreate tests prove that
an old opened leaf cannot be returned after its lexical name has been rebound.

Production and checker Exact6 readers retain all six leaf descriptors while
performing an initial inventory, first leaf and root/parent binding pass,
second inventory, second leaf pass, and second root/parent pass. The checker
independently reconstructs and compares every field of Contract Exact54 and
Safety Exact32. It also constructs the complete expected Manifest and
recursively checks exact Python type, dictionary key order, list length/order,
and scalar value, including strict `bool` versus `int`. Synchronized
CSV/Manifest/SHA tampering therefore cannot bypass the semantic layer.

Lifecycle checks recursively scan `src/covalent_ext`, `scripts`, `tests`, and
`docs` without following symlinks. Under `data/derived/covalent_small`, only
matching first-level stage-family roots are entered recursively. Every
discovered stage-family path is checked with
`git check-ignore --no-index`; nested, ignored, tracked, forbidden-suffix,
oversized, symlink, sibling-root, and seventh-output artifacts are rejected.
The filesystem allowlist is exactly Exact10 plus its single Exact6 root.

For a new output set, destination binding is checked immediately after the
no-replace rename, again after parent `fsync`, after the complete Exact6
post-read, and again after root `fsync`. Destination, parent, leaf,
extra/missing, and stat/open races fail closed. Existing identical sets remain
inode-preserving no-ops. The staging descriptor and lexical name are checked
after open, before and after every leaf write, after staging `fsync`, after
parent binding, immediately before rename, and again inside
`_rename_noreplace` before the syscall. A foreign directory substituted at
the staging name cannot be published.

`EEXIST`, GPFS `EINVAL`, staging identity drift, and pre-publish rename
failures fail closed with no `os.replace` fallback. A staging path is reported
as authenticated and retained only after its descriptor/name binding is
reverified.

The revised3 review found that the held parent descriptor was not sufficient
to authenticate the complete retained filesystem path: the lexical parent
could be renamed and recreated while a relative staging lookup through the old
descriptor still succeeded. Retained-path authentication now verifies both
the lexical parent/held-parent binding and the staging-name/staging-descriptor
binding twice before reporting a path. Parent binding and staging binding are
also each checked twice inside `_rename_noreplace` before the syscall, so a
pre-call parent replacement cannot publish Exact6 into the moved old parent.
This is a fail-closed pre-syscall threat-model check, not a claim that ordinary
Linux provides an atomic parent-path compare-and-rename operation.

If either binding is lost, a foreign object at the last-known lexical name is
never described as owned; the failure reports no authenticated path, the
frozen six-field staging identity, and the last-known name as
non-authoritative evidence. Failure paths never use `unlink`, `remove`,
`rmdir`, or recursive deletion, and neither the owned object nor an
identity-uncertain or foreign object is deleted. Successful publication leaves
no staging residue. Exact5 output bytes and all adapter business semantics
remain unchanged by revised2 and revised3.

Current permission remains false and the authorized ADMIT_015 training
execution count remains zero. No provider, network, download, or raw-data
operation is performed. No model, checkpoint, dataloader, or training path is
changed. A feature-semantics audit remains mandatory before training; Step12D
was a smoke legality check, not a final training-feature contract.

Recommended next step:
`implement_covapie_unified_dispatch_runtime_with_admit_001_to_015_v1`.
