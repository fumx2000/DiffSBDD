# CovaPIE Current11 multi-boundary ingestion contract design V1

## Design purpose

This step freezes the V1 contract for consuming a completed Current11
multi-boundary human-review submission. It supplies a private reference
evaluator for tests and formal preflight only. The evaluator constructs
candidate ingestion results and candidate authority records in memory.

This step does not expose a public ingestion implementation, write an
execution bundle, create an authority file, or change any existing V1
authority.

## Future public API

The future implementation is frozen to this signature:

```python
def evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1(
    *,
    adapter_response_payload: bytes,
    source_multi_boundary_submission_bundle: bytes,
    source_v1_submission_bundle: bytes,
    source_v1_ingestion_execution_bundle: bytes,
    repo_root: Path,
    existing_multi_boundary_authority_records: Sequence[
        Mapping[str, Any]
    ] = (),
) -> dict[str, Any]:
```

The design module does not define or export that function. Its `__all__` is
empty. The private reference evaluator is not a supported runtime interface.

## Required exact-byte inputs

Future ingestion consumes four exact byte strings:

1. the multi-boundary adapter response transport;
2. the source multi-boundary submission bundle;
3. the predecessor V1 submission bundle;
4. the predecessor V1 ingestion execution bundle.

The contract rejects substituted parsed objects. It validates byte transport,
strict JSON, exact field inventories, versions, item order, exact item counts,
record digests, bundle digests, and response digests. Filesystem SHA values
are always recomputed from the supplied bytes. Internal digests are recomputed
from canonical JSON with `sort_keys=true`, `ensure_ascii=true`,
`allow_nan=false`, and separators `(",", ":")`, excluding only the record's
own digest field.

## Adapter, submission, and V1 linkage

The adapter response must be an Exact9 passed response with five independently
validated result records and five independently validated ready ingestion
envelopes in sample order 000006–000010. Its source-payload SHA must equal the
exact multi-boundary submission bytes. Its canonical source-bundle SHA must
equal the submission's internal bundle SHA. Each envelope review payload must
be deeply equal to its source submission record.

The multi-boundary submission is Exact10 and contains five Exact25 review
records. Its predecessor submission and execution SHA fields must match the
exact V1 inputs. The V1 execution is Exact12, has a valid internal digest, and
must refer to the supplied V1 submission. Its authority-context and interface
lineage are revalidated through the committed predecessor implementation.
The execution's `source_submission_bundle_sha256` is checked against the
exact V1 submission bytes. Its `source_canonical_bundle_sha256` is checked
independently by strictly parsing those same bytes, serializing the parsed
object with the frozen canonical JSON rules, and hashing that canonical byte
string.

Before accepting the V1 execution, ingestion obtains the current committed
single-boundary authority context. The execution's
`authority_context_record_sha256` must exactly equal that committed context
digest; being lowercase 64-hex is not sufficient. Ingestion reconstructs the
predecessor Exact6 interface response from the execution's response version,
authority-context digest, batch status, 11 result records, 11 authority
records, and stored interface-response digest. It independently recomputes the
Exact6 digest, validates the committed predecessor response version, validates
every nested result and authority with the committed validators, checks the
top-level and nested batch identities, and closes each result-to-authority
link.

The contract does not receive the predecessor V1 adapter-response exact bytes.
Consequently, `submission_adapter_response_sha256` is the only predecessor
source digest in this lineage that cannot be compared byte-for-byte with its
source transport. It must be lowercase 64-hex and is protected through the
execution's canonical internal digest, but the contract does not claim a
comparison with an unavailable adapter-response transport.

Samples 000006–000010 must each have exactly one predecessor V1 authority.
Every such authority must remain `quarantined`, have
`sample_quarantined=true`, and have
`exact_one_attachment_boundary_authority_available=false`. The multi-boundary
review record must cite the exact predecessor authority and review digests.

## Multi-boundary authority context

The Exact10 context records, in order:

1. its multi-boundary context version;
2. the committed single-boundary authority-context digest;
3. the V1 submission filesystem digest;
4. the V1 execution filesystem digest;
5. the V1 execution internal digest;
6. the multi-boundary submission filesystem digest;
7. the multi-boundary submission internal digest;
8. the adapter-response filesystem digest;
9. the adapter-response internal digest;
10. its own canonical record digest.

Its version is
`covapie_current11_multi_boundary_human_review_ingestion_authority_context_v1`.
The private evaluator invokes the multi-boundary sidecar builder exactly once.
The committed single-boundary authority-context builder is invoked once inside
that builder and once more for reviewed-graph validation.

## Reviewed graph revalidation

Accept and revise decisions are checked against committed proposal,
assignment, package identity, parent-atom, and parent-bond authority. The
evaluator does not invoke RDKit and does not infer parent bonds.

The reviewed atom IDs must be unique, UTF-8 sorted, present in the parent
graph, and a proper subset of the parent atom set. Their induced subgraph must
be connected. They must contain every local reaction-center atom, required
leaving-group atom, and both endpoints of every local reaction-center bond.

Exactly two boundary bonds must be derived from the committed parent graph.
The graph-derived boundary records must exactly equal the reviewed boundary
records, including endpoint roles, normalized bond order, canonical bond ID,
and order. The attachment endpoint must be in the reviewed set and the
nonwarhead endpoint outside it.

An accept decision must exactly preserve the proposal. A revise decision must
differ from the proposal in at least one reviewed value. A quarantine decision
must have empty reviewed atoms and boundaries and cannot produce active
authority.

## Legacy V1 coexistence

The legacy namespace is `exact_one_boundary_v1`. The new namespace is
`exact_two_boundaries_multi_boundary_v1`. They may coexist in parallel.

Legacy V1 authority records are immutable. New multi-boundary authority
records cite the predecessor V1 quarantine-authority digest but do not edit,
delete, activate, supersede, or disguise that predecessor. A future unified
gold-view precedence rule is not implemented.

## Exact29 candidate authority

Each in-memory authority candidate has exactly 29 ordered fields and version
`covapie_current11_reviewed_warhead_atom_set_and_exact_two_boundaries_authority_v1`.
It cites the source submission, adapter response, review record, ingestion
envelope, evidence record, predecessor V1 quarantine authority, and predecessor
V1 review.

Accept and revise produce an active candidate with:

```text
authority_disposition=reviewed_multi_boundary_authority_materialized
complete_warhead_atom_set_authority_available=true
exact_two_attachment_boundaries_authority_available=true
sample_quarantined=false
v1_quarantine_authority_unchanged=true
authority_status=active
```

Quarantine produces a quarantined candidate with:

```text
authority_disposition=reviewed_multi_boundary_quarantine_recorded
complete_warhead_atom_set_authority_available=false
exact_two_attachment_boundaries_authority_available=false
sample_quarantined=true
v1_quarantine_authority_unchanged=true
authority_status=quarantined
```

Reviewer rationale and notes are retained only as SHA256 values in candidate
authority. No durable multi-boundary authority is created in this step.

Caller-supplied `existing_multi_boundary_authority_records` are untrusted
new-namespace input. The same strict Exact29 validator used for newly built
candidates validates every existing record before replay or conflict
classification. It requires an exact dict and field order; exact bool, list,
and string types; the exact version; all lineage, review, evidence, rationale,
notes, and record SHA fields as lowercase 64-hex; and a recomputable record
digest.

Identity and provenance strings must be nonempty, have no leading or trailing
whitespace or NUL, and be valid UTF-8 without lone surrogates. Reviewed atom
IDs must be meaningful strings, unique, and UTF-8 sorted. Every boundary must
be an ordered Exact4 record with distinct meaningful endpoints, a committed
normalized bond order, canonical bond ID, unique unordered endpoint pair, and
UTF-8 boundary-ID order. For every active accept or revise authority, the
boundary attachment endpoint must belong to `reviewed_warhead_atom_ids`, and
the nonwarhead endpoint must be outside that reviewed set. Active and
quarantine records must exactly satisfy their respective decision effects.
Any violation, including an endpoint-role mismatch, is
`EXISTING_AUTHORITY_SET_INVALID`.

## Exact18 ingestion result

Each input item produces one Exact18 result whenever batch identity can be
formed. A fresh successful result uses `PASSED`; an exact replay uses
`IDEMPOTENT_REPLAY` and does not duplicate the authority in
`new_authority_records`.

A different valid existing new-namespace authority for the same sample is
`CONFLICTING_REVIEW_REINGESTION`. Existing records from the legacy V1
namespace are invalid inputs to the new-namespace existing-authority set.
Malformed caller input is rejected as `EXISTING_AUTHORITY_SET_INVALID`; it is
never treated as a valid conflict.

## Exact6 interface response

The response version is
`covapie_current11_multi_boundary_human_review_ingestion_interface_response_v1`.
Its result and authority collections are tuples, preserve input order, and
have a canonical response digest that excludes only itself.

Fresh formal design preflight expects five passed results and five active
candidate authorities. The response and every nested record exist only in
memory.

## Replay, conflict, and batch atomicity

Fresh ingestion returns five new authority candidates. Full replay returns
five passed replay results and no new candidates. Mixed fresh and replay input
returns only the fresh candidates.

Any record, envelope, lineage, graph, existing-set, or conflict failure fails
the whole batch closed. The first failing item retains its specific reason;
all otherwise acceptable items use `BATCH_ATOMICITY_ABORTED`.
`new_authority_records` is empty. When a severe adapter or batch schema error
prevents stable item identity, a failed response may contain zero results.

## Reason vocabulary

The frozen vocabulary is:

```text
PASSED
IDEMPOTENT_REPLAY
BATCH_SIZE_INVALID
SUBMISSION_BATCH_ID_MISMATCH
DUPLICATE_SAMPLE_IN_BATCH
DUPLICATE_REVIEW_RECORD_SHA_IN_BATCH
ADAPTER_RESPONSE_INVALID
ADAPTER_RESPONSE_NOT_PASSED
SOURCE_SUBMISSION_LINKAGE_MISMATCH
SOURCE_V1_LINEAGE_MISMATCH
INGESTION_AUTHORITY_CONTEXT_INVALID
REVIEW_RECORD_DIGEST_INVALID
INGESTION_ENVELOPE_DIGEST_INVALID
ENVELOPE_REVIEW_LINKAGE_MISMATCH
REVIEW_IDENTITY_LINKAGE_MISMATCH
REVIEW_NOT_COMPLETED
REVIEWER_PROVENANCE_INVALID
REVIEW_DECISION_INVALID
V1_QUARANTINE_AUTHORITY_LINEAGE_MISMATCH
PARENT_GRAPH_LINEAGE_MISMATCH
REVIEWED_GRAPH_INVARIANT_INVALID
EXISTING_AUTHORITY_SET_INVALID
CONFLICTING_REVIEW_REINGESTION
BATCH_ATOMICITY_ABORTED
INGESTION_RESPONSE_INVARIANT_INVALID
```

Validation precedence is adapter/source bytes, batch identity and duplicates,
authority context, existing authority set, V1 lineage, envelope and record
identity, completion/provenance/decision, committed graph, conflict, batch
atomicity, and response invariant.

## Formal design preflight

Formal preflight calls only the private evaluator with the four frozen formal
exact-byte inputs and repository root. It validates five ready envelopes, five
passed results, five active candidate authorities, five exact-two-boundary
authorities, and five unchanged V1 quarantine lineages.

Preflight must also prove deterministic output, unchanged inputs, zero
compiler calls, zero multi-boundary adapter calls, zero predecessor ingestion
evaluator calls, and zero filesystem writes. It does not materialize a durable
authority or execution asset.

## Implementation boundary

This design does not create human gold, SMARTS, masks, or training labels. It
does not run a model or training. The canonical masks remain exactly:

1. `warhead_only`;
2. `linker_plus_warhead`;
3. `scaffold_plus_warhead`;
4. `scaffold_only`;
5. `scaffold_plus_linker_plus_warhead`.

This design must not be used as training readiness evidence. Formal training
still requires a feature-semantics audit, including resolution or formal audit
of the historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False` state. Step12D remains a smoke legality check,
not a final training-feature contract.

The only next step suggested by this design is:

```text
implement_covapie_current11_multi_boundary_human_review_ingestion_interface_v1
```
