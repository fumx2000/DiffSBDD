# CovaPIE Current11 review submission adapter design v1

## Scope

This step freezes the contract for a future in-memory submission adapter. It
does not implement the future public adapter, ingest a real review, read a
submission file, or materialize a review, envelope, result, or authority.

The future keyword-only API is:

```python
def adapt_current11_warhead_boundary_review_submission_bundle_v1(
    *,
    source_payload: bytes,
) -> dict[str, Any]:
```

No repository root, path, filename, pre-parsed dictionary, review record,
authority context, package map, option map, proposal map, or graph input is
admitted.

## Frozen input contract

`source_payload` must have exact type `bytes`, contain 1 through 1,048,576
bytes, decode as strict UTF-8 without a BOM, and contain one standard JSON
value. Duplicate object keys, NUL-containing invalid JSON, comments, JSON5,
trailing values, NaN, Infinity, and negative Infinity are rejected. Literal
NUL and NUL produced by JSON `\u0000` unescaping are rejected in every object
key and string value. JSON parser recursion and overflow exceptions fail
closed as `SOURCE_PAYLOAD_JSON_INVALID` without leaking Python exception text.
The syntax parse preserves every ordered object pair and scans every key and
value iteratively before duplicate-key rejection, so NUL is globally prior to
duplicate keys even when a later duplicate would overwrite the NUL-containing
value. A literal backslash followed by `u0000` remains ordinary string text
and is not rejected as NUL.
No value is coerced, normalized, stripped, case-folded, repaired, or invented.
The raw bytes are the sole authority for parsing, classification, bundle
identity, response status, response reason, and ordered result reasons. A
frozen, deterministic, side-effect-free source analysis plan performs this
work once for both the private reference evaluator and its response validator.
The validator reparses the raw bytes and accepts no caller-supplied parsed
bundle.

The bundle is ordered Exact3:

1. `submission_bundle_version`
2. `submission_batch_id`
3. `submission_items`

Each of 1 through 11 ordered items is Exact5:

1. `submission_item_version`
2. `review_record_payload`
3. `reviewer_provenance_attested`
4. `reviewer_provenance_attestor_id`
5. `submission_source_label`

The review payload is the committed Exact26 review schema without
`review_record_sha256`, leaving ordered Exact25. Exact integers reject
booleans, the selected index is an exact nonnegative integer or `None`, and
the reviewed atom IDs are an exact `list[str]`, ordered by UTF-8 encoded bytes
and unique. An empty list remains valid; the adapter does not check graph
existence, warhead membership, or boundary chemistry. V1 admits only
`select_admitted_candidate`, `revise_atom_set_and_boundary`, and `quarantine`;
`not_reviewed` is not a completed decision.

## Derived fields and atomicity

The future adapter may derive only the review digest, the fixed envelope
version and linkage fields, the submitted-payload digest, the envelope digest,
and response/result digests. Review, submitted-payload, and envelope digests
delegate the committed ingestion-design structural authorities rather than
maintaining a parallel digest domain. Human review fields are copied exactly.

Each successful item yields an in-memory tuple containing one Exact26 review
and one Exact9 provenance envelope. Item order is preserved. All item-specific
validation completes before global duplicate checks. Derived-review-SHA
duplicates take precedence over sample duplicates because an exact duplicate
review necessarily duplicates its sample. Bundle adaptation is all-or-nothing:
one invalid item makes `adapted_submissions` empty, consumes no item, and marks
otherwise-valid peers `ADAPTER_ATOMICITY_ABORTED`.

The adapter response is Exact9 and each item result is Exact12. The frozen
Exact2 result-effect table binds adapted results to `PASSED`, populated
lowercase SHA values and both true effect flags; invalid results use a formal
failure reason, blank SHA values and both false effect flags. The validator
checks contiguous indices, order, source/bundle digests, review/envelope
digests, submitted-payload digest, batch/sample/provenance linkage and the
original Exact25 item. It also requires passed state, response reason, result
count, every item/atomic/duplicate reason, and adapted count to equal the
unique raw-source classification plan. Thus source-A/bundle-B substitution, a
valid source forged as failure, or an invalid source forged as success remains
invalid after every nested and outer digest is recomputed. Successful
envelopes additionally require the exact committed envelope version, exact
types and the formal digest; reordered records, type subclasses, or a rehashed
wrong version fail closed. The public reason
vocabulary contains exactly 24
codes and its deterministic precedence contains exactly 16 entries. Internal
exception text is never a public reason.

## Authority boundary

Adapter success means only that strict JSON, schema, provenance construction,
and deterministic digest checks passed. It does not approve review identity,
candidate eligibility, revised chemistry, reviewer authority, ingestion,
family, rule, SMARTS, gold labels, or training labels.

The committed review-ingestion interface v1 remains the sole chemical and
identity semantic authority. Four synthetic adapted cases—select, revise,
quarantine, and a two-sample partial bundle—pass its public authority-context
builder and public evaluator entirely in memory. The downstream validation
does not call the interface's lifecycle-bound `build_result`.

## Evidence and readiness

The design evidence freezes Exact14 contracts, Exact28 synthetic truth cases
(4 adapted and 24 invalid), Exact11 Current11 readiness rows, and Exact47
fail-closed mutations. The checker independently reparses and classifies raw
source, trusts no external parsed bundle, binds response and result reasons to
that classification, validates canonical atom lists and all three formal
derived-record digest authorities, independently verifies pair-preserving
NUL/duplicate precedence, executes rehashed attacks, and runs the shared hermetic
Git lifecycle harness. It reports its generated candidate commit rather than
the current HEAD. The three core tables are populated only when both
predecessor/source validation and design validation succeed.

All actual lifecycle counts remain zero: submission payloads, completed
reviews, human provenance envelopes, adapted submissions, ingestion results,
and authorities. The submission-adapter design is complete and implementation
is ready, while real adaptation and real ingestion execution remain closed.

The canonical masks remain exactly:

1. `warhead_only`
2. `linker_plus_warhead`
3. `scaffold_plus_warhead`
4. `scaffold_only`
5. `scaffold_plus_linker_plus_warhead`

Integrated/planned covalent model modules remain 0/5. SMARTS, role, seed, mask,
tensor, model, and training gates remain closed. Formal training still
requires a feature-semantics audit; Step12D remains a smoke legality check
only.

## Recommended next engineering step

`implement_covapie_current11_warhead_atom_set_and_attachment_boundary_review_submission_adapter_v1`
