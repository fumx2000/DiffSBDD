# CovaPIE Current11 multi-boundary human-review submission compiler V1

## Purpose

This compiler converts a human-completed Current11 Exact3 multi-boundary
workspace into deterministic, strictly hashed submission-bundle JSON bytes.
It is a pure in-memory validation and compilation boundary. It does not write
or materialize a submission file.

## Exact compiler inputs and public API

The only public production API is:

```python
compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1(
    *,
    verified_multi_boundary_evidence_csv: bytes,
    multi_boundary_review_worklist_csv: bytes,
    readme_md: bytes,
    source_submission_bundle: bytes,
    source_ingestion_execution_bundle: bytes,
    repo_root: Path,
    submission_batch_id: str,
) -> bytes
```

All five payloads must be exact `bytes`; `repo_root` must be an exact `Path`;
and `submission_batch_id` must be an exact meaningful `str`. The compiler
rebuilds the blank Exact3 sidecar from the predecessor submission, execution
bundle, and committed repository context. Provided Evidence and README bytes
must be byte-identical to that reference. The Worklist must retain the exact
25-column schema, five-row order 000006–000010, and all first 14 frozen fields.

The input Worklist's `multi_boundary_review_record_sha256` must be empty in
every row. The compiler, not the reviewer workspace, calculates the formal
compiled review-record digest.

## Exact25 compiled record

Each of the five `submission_items` has these exact ordered fields:

1. `multi_boundary_review_record_version`
2. `item_index_0based`
3. `sample_index_row_id`
4. `pdb_id`
5. `ligand_comp_id`
6. `warhead_type_candidate_class_id`
7. `reaction_family_id`
8. `warhead_rule_id`
9. `source_evidence_record_sha256`
10. `source_v1_quarantine_authority_record_sha256`
11. `source_review_record_sha256`
12. `proposed_warhead_atom_ids`
13. `proposed_boundary_records`
14. `scope_caveat`
15. `review_decision`
16. `reviewed_warhead_atom_ids`
17. `reviewed_boundary_records`
18. `reviewer_id`
19. `review_rationale`
20. `review_notes`
21. `reviewer_provenance_attested`
22. `reviewer_provenance_attestor_id`
23. `submission_source_label`
24. `review_completed`
25. `multi_boundary_review_record_sha256`

Atom fields are `list[str]`, boundary fields are `list[dict[str, str]]`,
`item_index_0based` is an `int`, and the two completion/provenance fields are
`bool`. All other fields are strings.

## Exact10 bundle

The returned JSON object has these exact ordered fields:

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

The output is compact UTF-8 JSON with no BOM, NUL, or trailing newline and is
smaller than 1 MiB.

## Decision semantics

`accept_verified_two_boundary_proposal` requires parsed reviewed atoms and
boundaries to equal the parsed proposal exactly; JSON whitespace is not
semantically relevant.

`revise_two_boundary_atom_set_and_boundaries` requires a real semantic change.
The compiler reloads the committed parent graph and validates atom existence,
proper-subset status, connectivity, local reaction-center and leaving-group
coverage, preservation of local-center bonds, parent bond orders, canonical
boundary IDs, and exactly two graph-derived boundaries equal to the reviewed
boundaries. This validation is generic and is not hard-coded to sample 000008.

`quarantine` requires both reviewed atom and reviewed boundary lists to be
empty while completion, rationale, notes, reviewer identity, and attested
provenance remain complete.

## Digest rules

Each Exact25 record digest excludes
`multi_boundary_review_record_sha256`. The Exact10 bundle digest excludes
`multi_boundary_submission_bundle_sha256`. Both use SHA256 over canonical JSON
with `sort_keys=true`, `ensure_ascii=true`, `allow_nan=false`, and compact
separators. The final transport JSON uses `ensure_ascii=false`,
`allow_nan=false`, and compact separators.

## Formal preflight

Read the three exact human-completed workspace files and the exact predecessor
submission/execution files as bytes. Call the public compiler with:

```text
covapie_current11_multi_boundary_human_review_submission_batch_v1
```

Keep the returned bytes in memory. Parse and inspect the five records, decision
profile, record digests, source hashes, bundle digest, deterministic second
compile, and unchanged input bytes. Do not write the returned bytes during this
preflight.

## Boundary of this step

The compiler is not a multi-boundary adapter or ingestion implementation. Its
output is not authority and does not supersede the existing V1 quarantine
authority. It must not be used for training and creates no human gold, SMARTS,
masks, or training labels. The canonical mask contract remains exactly:
`warhead_only`, `linker_plus_warhead`, `scaffold_plus_warhead`,
`scaffold_only`, and `scaffold_plus_linker_plus_warhead`.

Formal training still requires a feature-semantics audit. Step12D remains only
a smoke legality check, not a final training-feature contract.

The only recommended next step is:

```text
materialize_covapie_current11_multi_boundary_human_review_submission_bundle_v1
```

Do not skip directly to multi-boundary ingestion or authority creation.
