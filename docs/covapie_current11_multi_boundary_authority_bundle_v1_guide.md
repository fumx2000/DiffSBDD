# Current11 multi-boundary authority bundle v1

## Current stage

This stage follows the committed Current11 authority-materialization
precondition and unified-precedence design. It implements one deterministic,
pure in-memory builder. The builder returns an authority-bundle JSON payload as
exact `bytes`; it does not write or materialize that payload.

The public API is:

```python
build_covapie_current11_multi_boundary_authority_bundle_v1(
    *,
    source_v1_submission_bundle: bytes,
    source_v1_ingestion_execution_bundle: bytes,
    source_multi_boundary_ingestion_execution_bundle: bytes,
    repo_root: Path,
) -> bytes
```

All three payloads must be exact `bytes`, and `repo_root` must be the exact
platform `Path` type.

## Authority namespace and selection

The bundle namespace is
`exact_two_boundaries_multi_boundary_v1`. The committed precedence design is
the only authority for the Current11 6+5 selection: six legacy exact-one
authorities and five multi-boundary exact-two authorities. The builder calls
that design exactly once and does not reproduce its precedence algorithm.

This bundle contains only the five reviewed active Exact29 authorities for
`CYS_SG_SAMPLE_INDEX_000006` through
`CYS_SG_SAMPLE_INDEX_000010`. Authorities for legacy-only samples `000001`
through `000005` and `000011` do not enter this bundle. The legacy V1 authority
namespace remains unchanged.

For each selected sample, the design resolution and authority record must agree
on the sample, active status, multi-boundary authority SHA, effective authority
SHA, namespace, and boundary cardinality two. Selected resolution SHAs and
authority SHAs are each unique. Every authority preserves its same-sample V1
quarantine-authority and V1 review backlinks.

## Exact16 schema

The top-level insertion order is:

1. `multi_boundary_authority_bundle_version`
2. `authority_namespace`
3. `source_v1_ingestion_execution_bundle_filesystem_sha256`
4. `source_v1_ingestion_execution_bundle_sha256`
5. `source_multi_boundary_ingestion_execution_bundle_filesystem_sha256`
6. `source_multi_boundary_ingestion_execution_bundle_sha256`
7. `source_unified_precedence_design_version`
8. `source_unified_precedence_design_response_sha256`
9. `selected_resolution_record_sha256s`
10. `sample_order`
11. `authority_records`
12. `authority_record_count`
13. `active_authority_count`
14. `exact_two_boundary_authority_count`
15. `v1_quarantine_backlink_count`
16. `multi_boundary_authority_bundle_sha256`

The two execution sources are recorded with both their filesystem-byte SHA256
and committed internal bundle SHA256. The precedence design version and its
validated response SHA256 preserve the selection lineage.

## JSON and digest contract

The internal bundle digest is SHA256 over canonical JSON containing the other
15 fields: keys sorted, ASCII escaped, non-finite numbers rejected, and compact
separators. Transport JSON preserves Exact16 insertion order, uses UTF-8 and
compact separators, does not sort keys or indent, and has no BOM, NUL, raw
newline, or trailing newline. The payload is smaller than 1 MiB and strict
ordered decoding must round-trip.

Collections are tuples while the bundle is assembled in memory and become JSON
arrays in transport. Exact29 authorities are deep-copied in committed field
order. Repeated calls are byte-identical, source payloads and parsed authority
objects remain unchanged, and mutating a decoded return value cannot affect a
source execution or a later builder result.

## Scope boundary

This step only returns multi-boundary authority bundle bytes in memory. It does
not create a durable authority file, unified effective-authority view, unified
gold, human gold, SMARTS, masks, training labels, or parameter updates. It does
not rerun ingestion and does not invoke the submission compiler, adapter,
public ingestion interface, private evaluator, or execution builder. The legacy
V1 authority and formal execution receipts are unchanged.

The canonical mask contract remains exactly five tasks:

1. `warhead_only` / `A`
2. `linker_plus_warhead` / `B`
3. `scaffold_plus_warhead` / `B2`
4. `scaffold_only` / `B3`
5. `scaffold_plus_linker_plus_warhead` / `C`

This bundle must not be used directly for training. Formal training still
requires a feature-semantics audit, including resolution or formal audit of the
historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False` state. Step12D remains only a smoke legality
check, not a final training-feature contract.

## Only recommended next step

`materialize_covapie_current11_multi_boundary_authority_bundle_v1`
