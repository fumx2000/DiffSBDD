# CovaPIE Current11 runtime sample and role-order carrier materializer V1

## Scope

This increment implements a deterministic runtime carrier builder and a GPFS-safe
relative-alias publisher. It does not execute formal materialization in the real
state root. It does not implement a batch descriptor compiler, dataloader
integration, model integration, loss integration, or training.

The sole public API is:

```python
materialize_covapie_current11_runtime_sample_and_role_order_carrier_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, object]
```

The canonical output is derived only from `state_root`:

```text
formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1
```

There are no output, schema, digest, registry, or array overrides.

## Authority and reconstruction

Every candidate build verifies the frozen carrier-contract gate module and
checker identities. It invokes the published gate public API twice through a
narrow precommit compatibility wrapper and requires the Exact6 bytes to be
identical. The wrapper filters only the four exact untracked implementation
paths from the two Git status forms used by predecessors. All other repository
state remains visible and fail-closed.

The gate chain is evaluated against the read-only authority state at
`repo_root.parent / "covapie-state"`. The API `state_root` remains the sole
source of the carrier canonical publication path. Before a candidate is built,
the materializer independently verifies that the API state root contains the
exact formal routing relative symlink, hidden object, four leaf modes, and four
leaf hashes. This split lets a temporary mirror contain only the frozen formal
routing object while preventing it from substituting different routing bytes.

The sample registry, role-order registry, and carrier schema from the gate
Exact6 are the only semantic authority. The published schema artifact is first
validated as an exact deterministic contract, including all nested fields and
its frozen digest. A private instance validator is then applied both immediately
after manifest construction and whenever a candidate bundle is validated. It
requires the Exact18 manifest semantics, runtime path and artifact digest,
sample order, readiness, exact names and receptors bindings, and every required
role-buffer field and false constraint. Unknown or missing published contract
fields fail closed. The materializer verifies all 22 source
table paths, hashes, headers, row counts, full projected-row vectors, nullable
source-to-projected vectors, selected endpoint parity, retained and excluded-H
counts, role-record digests, and projected Exact8 identity-sequence digests.
Design Markdown is not read as authority.

Coordinates are reconstructed from the exact source-table `x`, `y`, and `z`
columns before centering. Features are reconstructed from `type_symbol` in the
fixed channel order `C,N,O,S,B,Br,Cl,P,I,F`. Explicit hydrogen is excluded and
unsupported non-hydrogen rejects the complete build. No coordinate centering,
noise, rotation, padding, crop, virtual node, reorder, sentinel, placeholder,
or fabricated ligand data is allowed. Source row count is checked directly
against every role-order record. Coordinates must remain finite both as parsed
Python floats and after conversion to the runtime `<f4` representation.

## Deterministic NPZ

The NPZ contains exactly these arrays in order:

1. `names`
2. `receptors`
3. `lig_mask`
4. `pocket_mask`
5. `lig_coords`
6. `pocket_coords`
7. `lig_one_hot`
8. `pocket_one_hot`
9. `lig_source_row_index`
10. `pocket_source_row_index`
11. `lig_parser_local_index`
12. `pocket_parser_local_index`

Each entry is written through `numpy.lib.format.write_array` as a C-contiguous
`.npy` V1.0 payload with pickle disabled. The ZIP uses `ZIP_STORED`, a fixed
1980-01-01 timestamp, Unix creator metadata, regular-file mode 0644, empty
extra fields and comments, no directory entries, and an empty archive comment.
`numpy.savez` and `numpy.savez_compressed` are not used.

## Formal Exact4 and publication

The formal object contains exactly:

1. `current11_runtime_sample_and_role_order_carrier.npz`
2. `current11_runtime_sample_and_role_order_carrier_manifest.json`
3. `current11_runtime_sample_and_role_order_carrier_array_inventory.csv`
4. `current11_runtime_sample_and_role_order_carrier_binding_report.json`

The manifest has the frozen Exact18 top-level contract. Its `names_binding`
uses the published semantic representation: Exact11 strings framed as compact
canonical JSON, whose SHA256 is
`e20c1a3f764757ffac99b8e812a4caba23500270edd352ed159fdb18867a28ac`.
That semantic digest is independently recomputed and cannot be replaced by the
Unicode array's raw C-order digest. `receptors_binding` is explicitly
consistency-only. The inventory and provenance separately bind the actual raw
C-order and `.npy` bytes of every array. Only `names` is authorized as sample
identity; coordinates and one-hot are not identity, and source/local arrays are
role-order evidence.

The publisher creates one initially empty mode-0700 hidden object directory,
writes and fsyncs each mode-0644 leaf, fsyncs and rereads the object, changes the
object to mode 0755, verifies it again, publishes one relative canonical
symlink without replacement, fsyncs the parent, and verifies the published
object again. Before any prepublication cleanup, the canonical entry is
classified without following it as absent, pointing to this object, or
unrelated. Cleanup is allowed only for absent or unrelated canonical state; a
concurrent canonical that points to this object preserves the object and the
original operation still fails closed. Cleanup failure has a separate token.

Immediately before a successful return, both publication and existing-object
verification revalidate parent identity, canonical symlink identity and exact
relative target, object identity and mode 0755, and every Exact4 leaf identity
and mode 0644. Postpublication drift fails closed and never triggers automatic
cleanup of the published object.

## Checker and current readiness

The checker accepts only `--repo-root` and `--state-root` and never writes
state. With the real canonical absent it returns
`PASS_MATERIALIZER_IMPLEMENTATION_ONLY`, reports the deterministic candidate,
and keeps all formal runtime availability values false. A future existing
canonical is verified through `_verify_existing` and returns
`PASS_FORMAL_RUNTIME_CARRIER_MATERIALIZED`.

Repository tests include the full non-monkeypatch public path against an
ephemeral state mirror: gate Exact6 rebuild, all 22 source-table rebuilds,
candidate construction, publication, and a fresh `_verify_existing` rebuild.
They also exercise absent and unrelated cleanup, concurrent canonical adoption,
postpublication alias and parent drift, normal final revalidation, and the
independent cleanup-failure token. Torch and `dataset.py` are ordinary required
runtime dependencies in the dataset-consumer test; missing imports fail rather
than skip.

This implementation makes formal materialization execution ready, but formal
materialization has not occurred. Batch descriptor compiler implementation,
dataloader/model/loss integration, and training remain unavailable. A feature
semantics re-audit is still required before training. The historical Step12D
result was a smoke legality check, not a final training-feature contract.
