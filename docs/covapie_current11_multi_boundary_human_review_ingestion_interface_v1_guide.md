# CovaPIE Current11 Multi-Boundary Human-Review Ingestion Interface V1

## Purpose

This step provides the stable public, in-memory ingestion call boundary for
the five Current11 multi-boundary human-review records. It exposes candidate
authority records for validation and later execution planning. It does not
persist an interface response, create durable authority, or modify the legacy
V1 authority namespace.

The implementation is
`covapie_current11_multi_boundary_human_review_ingestion_interface_v1`.
Its design baseline is commit
`bccd85194fbd19a55a77e998f5b9bcab5465b751`, whose production design module
has SHA256
`91899640e89cc462aac0a28245873da12ba573b8658a30e193da7ec9fac92771`.

## Public API

The module exports only:

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

All arguments are keyword-only. The four payload arguments are exact bytes.
The optional existing-authority sequence supports fresh, replay, mixed replay,
and conflict evaluation without creating an authority store.

## Thin-wrapper architecture

The committed
`covapie_current11_multi_boundary_human_review_ingestion_contract_design_v1`
module is the sole semantic authority. Each public evaluation calls its
private reference evaluator exactly once:

```python
design._reference_evaluate_covapie_current11_multi_boundary_ingestion_v1(...)
```

The public layer does not reconstruct candidate authority, validate the graph
independently, classify replay or conflict, invoke the compiler, invoke the
multi-boundary adapter, or invoke the predecessor single-boundary ingestion
evaluator. It adds only:

1. exact-byte and deepcopyable existing-authority input snapshots;
2. one call to the committed reference evaluator;
3. a deep copy of the reference response;
4. committed response validation and mutable-alias isolation checks.

The wrapper returns a distinct response object that is deeply equal to the
private response. It does not alter reasons, results, context SHA values,
candidate records, or response SHA values.

## Exact response contracts

The returned object preserves the design field order and exact types:

- Exact6 multi-boundary ingestion interface response;
- Exact18 ingestion result records;
- Exact29 candidate authority records.

Validation is delegated to the committed
`design._validate_interface_response(...)`, which also validates every nested
Exact18 and Exact29 record and their canonical digests. A normal fail-closed
response remains a normal return with `batch_passed=false`.

Only an internal public-wrapper failure raises:

```text
ValueError("INGESTION_RESPONSE_INVARIANT_INVALID")
```

This includes an invalid private response, committed response-validator
failure, caller-input mutation by the private evaluator, deepcopy failure, or
response-isolation failure. No new ingestion reason vocabulary is introduced.

## Fresh, replay, conflict, and atomicity

The public interface preserves the committed semantics:

- Fresh: five passed results and five new active candidate authorities.
- Full replay: five `IDEMPOTENT_REPLAY` results and no new authorities.
- Mixed replay: only fresh candidate authorities are returned, in source
  order.
- Conflict: the specific record receives
  `CONFLICTING_REVIEW_REINGESTION`, all other records receive
  `BATCH_ATOMICITY_ABORTED`, and no new authorities are returned.
- Malformed existing authority: the specific reason is
  `EXISTING_AUTHORITY_SET_INVALID`, not conflict.
- Any blocking record aborts the batch atomically.

The boundary endpoint roles, reviewed graph contract, V1 canonical submission
lineage, and V1 Exact6 execution lineage remain those frozen by the design.

## Input and response isolation

The wrapper checks that all exact-byte inputs remain byte-identical. When the
existing-authority input can be deep-copied, the wrapper creates two
independent copies: a comparison snapshot that is never supplied to the
private evaluator, and a separate evaluation copy made from that snapshot.
The private evaluator receives only the evaluation copy, never the caller's
original object. After evaluation, both the caller object and the evaluation
copy must remain deeply equal to the comparison snapshot.

The absence of a deepcopy exception does not by itself prove independence.
Before calling the private evaluator, the wrapper verifies that the original,
comparison snapshot, and evaluation copy have distinct root identities. It
also collects builtin mutable `dict`, `list`, `set`, and `bytearray`
identities and requires all three object graphs to be pairwise alias-free.
A deceptive `__deepcopy__` that returns its input, or a builtin container copy
that shares mutable nested containers, is rejected before private evaluation.
The failure is
`ValueError("INGESTION_RESPONSE_INVARIANT_INVALID")`, the private call count
remains zero, and the caller object remains unchanged.

If the private evaluator incorrectly modifies the evaluation copy, the caller
object still remains unchanged and the wrapper raises:

```text
ValueError("INGESTION_RESPONSE_INVARIANT_INVALID")
```

An existing-authority input whose first snapshot raises the expected
`TypeError`, `ValueError`, or `RecursionError` remains delegated to the
committed design for its normal fail-closed classification. Any other ordinary
deepcopy exception is wrapped as the same public-wrapper invariant error, with
the original exception retained as its cause. The private response is
deep-copied, validated, and checked for mutable container aliases before it is
returned.

Consequently, modifying one returned response cannot modify the private
response, caller-owned existing-authority records, or a later evaluation.

## Formal preflight

Formal preflight is a pure in-memory operation. It reads the four exact-byte
formal inputs, evaluates the committed private reference once for comparison,
and calls the public interface twice. It must establish:

- public/private deep parity;
- `batch_passed=true`;
- five results and five active candidate authorities;
- exactly two reviewed attachment boundaries for all five candidates;
- unchanged V1 quarantine-authority lineage for all five candidates;
- deterministic responses and unchanged inputs;
- no filesystem write, durable authority file, interface response file, or
  execution file.

Any formal context, authority, result, or response digest change is a
fail-closed stop condition. Formal preflight does not authorize
materialization.

## Implementation boundary

This interface returns candidate multi-boundary authority only in memory.
It creates no durable authority and does not edit or delete legacy V1
authority. Parallel legacy exact-one-boundary and candidate
exact-two-boundaries namespaces therefore remain unchanged.

Unified gold precedence is not implemented. This step does not generate human
gold, SMARTS, masks, training labels, or any execution bundle, and it must not
be used for training or parameter updates.

The canonical V1 mask contract remains exactly:

1. `warhead_only` / `A`
2. `linker_plus_warhead` / `B`
3. `scaffold_plus_warhead` / `B2`
4. `scaffold_only` / `B3`
5. `scaffold_plus_linker_plus_warhead` / `C`

Before any training or fine-tuning, CovaPIE still requires a feature-semantics
audit. The historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False` state must be resolved or formally audited.
Step12D was a smoke legality check, not a final training-feature contract.

The only recommended next step is:

```text
implement_covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1
```

That later step must be separately authorized and gated. It must not be
replaced by directly materializing authority files.
