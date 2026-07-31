# CovaPIE Current11 Multi-Boundary Ingestion Execution Bundle V1

## Purpose

This step builds a deterministic execution receipt for the five Current11
multi-boundary human-review ingestion records. The receipt exists only as
returned JSON bytes in memory. It records exact source lineage, the committed
public-interface response, and the five candidate authority records produced
by a fresh successful batch.

The builder does not write or materialize the receipt. It does not create a
multi-boundary authority store, create unified gold authority, or modify the
legacy V1 authority.

## Builder API

The production module exports only:

```python
def build_covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1(
    *,
    adapter_response_payload: bytes,
    source_multi_boundary_submission_bundle: bytes,
    source_v1_submission_bundle: bytes,
    source_v1_ingestion_execution_bundle: bytes,
    repo_root: Path,
) -> bytes:
```

All arguments are keyword-only. The four payloads must be exact `bytes`, and
`repo_root` must be an exact platform `Path` type. The return value is
deterministic JSON `bytes`, not a dictionary or a file path.

The implementation is pinned to public-interface commit
`653bacfb31e69ccfd37f29dcffd77116c9305370`. The production public-interface
source SHA256 is
`f17a33e52ede082e5a28f20b8a70e4b3d40ca30b69823b4050b2104a3545b0d5`.

## Exact16 schema

The top-level fields occur in this exact transport order:

1. `multi_boundary_ingestion_execution_bundle_version`
2. `source_v1_submission_bundle_sha256`
3. `source_v1_ingestion_execution_bundle_filesystem_sha256`
4. `source_v1_ingestion_execution_bundle_sha256`
5. `source_multi_boundary_submission_bundle_filesystem_sha256`
6. `source_multi_boundary_submission_bundle_sha256`
7. `source_adapter_response_filesystem_sha256`
8. `source_adapter_response_sha256`
9. `submission_batch_id`
10. `ingestion_interface_response_version`
11. `authority_context_record_sha256`
12. `batch_passed`
13. `ingestion_result_records`
14. `new_authority_records`
15. `ingestion_interface_response_sha256`
16. `multi_boundary_ingestion_execution_bundle_sha256`

The version is
`covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1`.
The nested evidence consists of five Exact18 ingestion results and five
Exact29 candidate authority records, copied in their committed field order.

## Source lineage

Every filesystem SHA is the SHA256 of the corresponding exact input bytes:

- the V1 submission bundle;
- the predecessor V1 ingestion execution bundle;
- the multi-boundary submission bundle;
- the multi-boundary adapter response.

The predecessor execution, multi-boundary submission, and adapter response
internal digests are extracted only after strict validation. Validation
requires strict UTF-8 JSON objects, exact field inventories, no duplicate
keys, no BOM, NUL, trailing newline, NaN, or Infinity, and independently
recomputed stored internal digests. The committed pure validation helpers are
reused; no compiler or adapter regenerates any input.

The public response authority-context SHA is retained unchanged. The public
interface already validates the complete four-input authority-context
lineage. In addition, the builder rebuilds the committed single-boundary
authority context once and validates it with the committed predecessor design
validator. Its trusted context-record SHA is the independent expected value
for validating the predecessor V1 execution.

The predecessor execution's stored context SHA is never used as its own
expected value. A substituted stored context is rejected even if an attacker
also refreshes the predecessor Exact6 interface-response digest and Exact12
execution digest. This extra context build validates source lineage only; it
does not construct a competing authority-context or ingestion semantics.

The Exact16 top-level source lineage and every embedded Exact29 authority
source lineage must also agree. All five authorities must reference the
current validated multi-boundary submission and adapter-response internal
digests. For each sample, the embedded V1 quarantine-authority and review
record SHAs must equal those in the same sample's quarantined authority from
the current validated predecessor V1 execution.

An Exact6 response whose Exact18 and Exact29 records and all internal digests
are individually valid is still rejected when those embedded source SHAs
refer to different inputs. This receipt-level cross-link adds no
authority-context build, does not invoke ingestion again, and does not
construct unified gold.

## Public interface as the sole execution source

Each build calls exactly once:

```python
public_interface.evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1(
    adapter_response_payload=adapter_response_payload,
    source_multi_boundary_submission_bundle=
        source_multi_boundary_submission_bundle,
    source_v1_submission_bundle=source_v1_submission_bundle,
    source_v1_ingestion_execution_bundle=
        source_v1_ingestion_execution_bundle,
    repo_root=repo_root,
)
```

The default fresh existing-authority state is used; no existing-authority
argument is passed. The builder does not directly call the private reference
evaluator and does not reconstruct ingestion, graph, replay, conflict, or
candidate-authority semantics. It does not invoke the compiler,
multi-boundary adapter, or predecessor ingestion evaluator.

Each build therefore performs three committed authority-context builder
calls: two inside the public interface's existing ingestion path and one for
the builder's independent predecessor source-lineage validation. The
predecessor ingestion evaluator call count remains zero. The public interface
remains the sole source of ingestion execution semantics.

The committed `design._validate_interface_response(...)` validates the Exact6
response and every nested Exact18 and Exact29 record. The Exact6 view and its
stored response digest are also independently reconstructed and checked.

## Fresh-only semantics

An execution receipt is returned only for the first successful ingestion:

- `batch_passed=true`;
- exactly five passed results and five new authorities;
- no replay and no conflict flags;
- every result consumed its review record and ingestion envelope;
- samples are ordered from
  `CYS_SG_SAMPLE_INDEX_000006` through
  `CYS_SG_SAMPLE_INDEX_000010`;
- the decision profile is four
  `accept_verified_two_boundary_proposal`, one
  `revise_two_boundary_atom_set_and_boundaries`, and zero `quarantine`;
- all five candidate authorities are active, non-quarantined, complete
  warhead-atom-set, exact-two-boundary authorities;
- all five retain `v1_quarantine_authority_unchanged=true`.

A failed response, full or mixed replay, conflict, quarantine authority,
malformed nested record, wrong order, or wrong decision profile is rejected
with:

```text
ValueError("MULTI_BOUNDARY_INGESTION_EXECUTION_RESPONSE_INVALID")
```

No ingestion reason vocabulary is added.

## Result-authority linkage

At each of the five positions, the result and authority must agree on:

- sample ID;
- source multi-boundary review-record SHA;
- source ingestion-envelope SHA;
- review decision;
- authority disposition;
- authority-record SHA.

The result `authority_record_sha256` must equal the authority
`multi_boundary_authority_record_sha256`, and all five authority SHAs must be
unique. A mismatch blocks serialization.

Before serialization, every embedded authority is additionally cross-linked
to the Exact16 sources: its multi-boundary submission and adapter-response
SHAs must identify the current inputs, and its predecessor authority and
review SHAs must identify the same sample in the current predecessor V1
execution. A stale or substituted source reference is rejected even when the
authority, corresponding result, and Exact6 response have all been rehashed
correctly.

## JSON and digest contract

The execution internal digest is the SHA256 of canonical JSON for the first
15 fields:

```python
sha256(
    json.dumps(
        {
            field: bundle[field]
            for field in EXACT16_FIELDS
            if field
            != "multi_boundary_ingestion_execution_bundle_sha256"
        },
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
)
```

Transport uses insertion order, not sorted keys:

```python
json.dumps(
    bundle,
    ensure_ascii=False,
    allow_nan=False,
    separators=(",", ":"),
).encode("utf-8")
```

The transport is smaller than 1 MiB, has no indentation, BOM, NUL, raw
newline, or trailing newline, and preserves Exact16 field order after strict
round-trip decoding. Tuples from the public response naturally serialize as
JSON arrays. Consecutive builds from identical exact bytes are byte-identical.

## Formal in-memory preflight

Formal preflight reads the four approved formal files as exact bytes, records
their snapshots, and calls the builder twice. It validates:

- deterministic, byte-identical Exact16 transports;
- successful five-result and five-candidate-authority semantics;
- five active exact-two-boundary candidates with unchanged V1 quarantine
  lineage;
- strict round trip and both internal and transport digests;
- unchanged formal inputs;
- no filesystem write, execution file, or authority file.

Formal preflight reports the observed execution internal SHA, transport SHA,
and transport size; those values are not pre-assumed. It remains an in-memory
preflight and does not authorize materialization.

## Execution and authority boundary

The five embedded candidate authority records are evidence of this execution.
They are not a durable multi-boundary authority store and are not a unified
gold authority store. Unified gold precedence is not implemented. The legacy
V1 authority remains unchanged.

This step returns execution bytes only. It creates no formal execution file,
authority JSON or CSV, human gold, SMARTS, masks, or training labels. The
execution receipt must not be used for training.

The canonical mask contract remains exactly five tasks:

1. `warhead_only` / `A`
2. `linker_plus_warhead` / `B`
3. `scaffold_plus_warhead` / `B2`
4. `scaffold_only` / `B3`
5. `scaffold_plus_linker_plus_warhead` / `C`

Formal training still requires a feature-semantics audit. Step12D remains only
a smoke legality check, not a final training-feature contract.

## Next step

The only recommended next step is:

```text
materialize_covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1
```

That future step concerns execution-receipt materialization only. It is not a
recommendation to materialize authority directly.
