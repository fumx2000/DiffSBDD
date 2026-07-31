# CovaPIE Current11 multi-boundary submission adapter V1

## Purpose and public API

This adapter converts formal multi-boundary Exact10 JSON bytes into validated
in-memory ingestion envelopes. It validates one five-item batch atomically and
does not materialize a response file.

The only public production API is:

```python
adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1(
    *,
    source_payload: bytes,
) -> dict[str, Any]
```

`source_payload` must be exact `bytes`. The call does not write files, access
the network, inspect Git or a repository root, call the sidecar or compiler,
build authority context, evaluate ingestion, or create authority.

## Strict JSON boundary

The payload must be nonempty and strictly smaller than 1 MiB. BOM, NUL, and a
trailing newline are forbidden. It must decode as UTF-8 and parse as strict
JSON with an exact top-level `dict`. Duplicate keys at any depth and
`NaN`/`Infinity` constants are rejected; input is never repaired.

Validation priority is bytes, JSON, bundle schema/types/version/batch/count,
item schema/types/order/uniqueness, record digests, completion/provenance,
atoms/boundaries, and decision semantics. The first item in item-index order
wins among failures of the same class. Any failure produces an atomic failed
Exact9 response with no result records or adapted submissions.

## Exact10 input bundle

The ordered input fields are:

1. `multi_boundary_submission_bundle_version`
2. `source_submission_bundle_sha256`
3. `source_ingestion_execution_bundle_filesystem_sha256`
4. `source_ingestion_execution_bundle_sha256`
5. `source_verified_multi_boundary_evidence_csv_sha256`
6. `source_multi_boundary_review_worklist_csv_sha256`
7. `source_readme_sha256`
8. `submission_batch_id`
9. `submission_items`
10. `multi_boundary_submission_bundle_sha256`

The version is
`covapie_current11_multi_boundary_human_review_submission_bundle_v1`.
All six lineage SHA fields and the internal bundle SHA are lowercase 64-hex
strings. The batch ID is meaningful, and `submission_items` contains exactly
five records ordered 000006–000010.

Each Exact25 record has the ordered fields
`multi_boundary_review_record_version`, `item_index_0based`,
`sample_index_row_id`, `pdb_id`, `ligand_comp_id`,
`warhead_type_candidate_class_id`, `reaction_family_id`, `warhead_rule_id`,
the three `source_*_record_sha256` fields, `proposed_warhead_atom_ids`,
`proposed_boundary_records`, `scope_caveat`, `review_decision`,
`reviewed_warhead_atom_ids`, `reviewed_boundary_records`, `reviewer_id`,
`review_rationale`, `review_notes`, `reviewer_provenance_attested`,
`reviewer_provenance_attestor_id`, `submission_source_label`,
`review_completed`, and `multi_boundary_review_record_sha256`.

The item index is an exact `int`, not `bool`; atom fields are exact
`list[str]`; boundary fields are exact `list[dict[str, str]]`; completion and
provenance flags are exact `bool`; and all other fields are exact strings.
Samples and record digests are unique.

Atom IDs are meaningful, UTF-8 encodable, unique, and UTF-8 sorted. A boundary
record has the exact ordered fields `warhead_attachment_atom_id`,
`nonwarhead_boundary_atom_id`, `boundary_bond_order`, and `boundary_bond_id`.
Endpoints are meaningful and distinct. The normalized bond order is exactly
one of `aromatic`, `double`, or `single`. The ID is
`<UTF8-low>|<UTF8-high>|<bond_order>`. Records are UTF-8 sorted by ID, and
boundary IDs and unordered endpoint pairs are unique. The adapter does not
import RDKit or infer a parent graph.

## Decision semantics

Every decision requires completed review, attested provenance, and meaningful
reviewer, attestor, rationale, notes, and source label.

- `accept_verified_two_boundary_proposal` requires nonempty proposed/reviewed
  atoms, exactly two proposed/reviewed boundaries, and exact equality between
  reviewed and proposed values.
- `revise_two_boundary_atom_set_and_boundaries` has the same nonempty and
  two-boundary requirements, but atoms or boundaries must differ.
- `quarantine` requires empty reviewed atoms and boundaries. Proposed evidence
  may remain populated.

The compiler already validated revision graph semantics. This adapter has no
`repo_root` and deliberately does not repeat parent-graph validation. Future
ingestion must validate the committed graph and V1 authority lineage again.

## Exact9 response, Exact12 result, and Exact12 envelope

The response fields are, in order:

1. `multi_boundary_submission_adapter_response_version`
2. `source_payload_sha256`
3. `canonical_source_bundle_sha256`
4. `submission_batch_id`
5. `adapter_passed`
6. `reason`
7. `adapter_result_records`
8. `adapted_submissions`
9. `multi_boundary_submission_adapter_response_sha256`

Success uses version
`covapie_current11_multi_boundary_human_review_submission_adapter_response_v1`,
`adapter_passed=True`, `reason="PASSED"`, and exact five-element tuples for
results and envelopes.

Each Exact12 result contains, in order, its result version, item index, batch
ID, sample ID, `outcome`, `passed`, `reason`, source review-record SHA,
ingestion-envelope SHA, `consumed_submission_item`, `ready_for_ingestion`, and
result SHA. Success fixes outcome to `adapted`, both booleans to true, and
reason to `PASSED`.

Each Exact12 envelope contains, in order, its envelope version, batch ID, item
index, sample ID, source bundle SHA, source review-record SHA,
`review_record_payload`, duplicated provenance flag and attestor, source
label, `ready_for_ingestion`, and envelope SHA. `review_record_payload` is a
deep copy of the Exact25 record. The five envelope SHAs are unique. Envelopes
are readiness messages, not authority records.

## Digest rules

Record, bundle, envelope, result, and response digests independently exclude
their own digest field. SHA256 is calculated over canonical JSON with
`sort_keys=true`, `ensure_ascii=true`, `allow_nan=false`, and separators
`(",", ":")`. `source_payload_sha256` hashes the exact transport bytes.

## Failure reasons

The frozen vocabulary is:

```text
PASSED
SOURCE_PAYLOAD_EXACT_TYPE_INVALID
SOURCE_PAYLOAD_SIZE_INVALID
SOURCE_PAYLOAD_UTF8_INVALID
SOURCE_PAYLOAD_BOM_FORBIDDEN
SOURCE_PAYLOAD_NUL_FORBIDDEN
SOURCE_PAYLOAD_TRAILING_NEWLINE_FORBIDDEN
SOURCE_PAYLOAD_JSON_INVALID
SOURCE_PAYLOAD_DUPLICATE_KEY
SOURCE_PAYLOAD_NONFINITE_INVALID
SUBMISSION_BUNDLE_FIELD_INVENTORY_MISMATCH
SUBMISSION_BUNDLE_EXACT_TYPE_INVALID
SUBMISSION_BUNDLE_VERSION_MISMATCH
SUBMISSION_BATCH_ID_NOT_MEANINGFUL
SUBMISSION_ITEM_COUNT_INVALID
SUBMISSION_BUNDLE_DIGEST_INVALID
SUBMISSION_ITEM_FIELD_INVENTORY_MISMATCH
SUBMISSION_ITEM_EXACT_TYPE_INVALID
SUBMISSION_ITEM_ORDER_INVALID
SUBMISSION_SAMPLE_ORDER_INVALID
DUPLICATE_SAMPLE_IN_BUNDLE
REVIEW_RECORD_DIGEST_INVALID
DUPLICATE_REVIEW_DIGEST_IN_BUNDLE
REVIEW_DECISION_INVALID
REVIEW_COMPLETION_INVALID
REVIEWER_PROVENANCE_INVALID
ATOM_SET_INVALID
BOUNDARY_RECORDS_INVALID
ACCEPT_SEMANTICS_INVALID
REVISION_SEMANTICS_INVALID
QUARANTINE_SEMANTICS_INVALID
ADAPTER_RESPONSE_INVARIANT_INVALID
```

A normal validation failure returns the failed Exact9 response. Only failure
to establish the response contract itself raises
`ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")`.

## Formal preflight and next-stage boundary

Formal preflight reads the formal submission payload as exact bytes, verifies
transport SHA
`1e59537e6802d5500f4adce418a481a5b730968f4ecdfa73b8c90c7946e2ee24`
and internal bundle SHA
`1b0ba84d03cbf67b7b4fcd6b6309ad493b0b61b6f402c775a7d0802cb0e3462c`,
calls the public adapter twice, and checks 4/1/0 decisions, five ready
envelopes, deterministic deep equality, unchanged input, and no writes. The
responses remain only in memory.

The adapter does not implement ingestion and does not create or modify
authority. The existing V1 quarantine authority remains effective. Its output
must not be used for training and creates no human gold, SMARTS, masks, or
training labels. Canonical masks remain exactly `warhead_only`,
`linker_plus_warhead`, `scaffold_plus_warhead`, `scaffold_only`, and
`scaffold_plus_linker_plus_warhead`.

Formal training still requires a feature-semantics audit. Step12D remains only
a smoke legality check, not a final training-feature contract.

The only recommended next step is:

```text
materialize_covapie_current11_multi_boundary_human_review_submission_adapter_response_v1
```

Do not skip directly to ingestion or authority creation.
