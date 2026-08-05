# Current11 GPFS atomic-alias routing sidecar materializer V2

## Scope

This increment implements a repository-only materializer and read-only checker. It does not perform formal materialization, create `STATE_ROOT/formal-sidecars`, generate tensors, integrate a runtime consumer, change a model, or authorize training. Before any future training work, the feature-semantics audit remains mandatory; Step12D was a smoke legality check, not a final training-feature contract.

The public module API is keyword-only:

```python
materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_gpfs_atomic_alias_v2(
    *,
    repo_root: Path,
    state_root: Path,
    output_path: Path,
) -> dict[str, object]
```

The CLI accepts only `--repo-root`, `--state-root`, `--output-path`, and the valueless `--check` flag. It has no default help interface and has no overwrite, repair, locking, rename, copy, digest, nonce, object-name, tensor, or training override.

## Frozen source and artifact contract

V2 verifies the published V1 materializer source SHA256 `5d189c0451a1aad515932bd4e537de9378b79fcbc2987f671d069e0db857aada`, then reuses its fresh-builder invocation and complete builder artifact validation. That validation binds the published builder SHA256 `1be932e473107a2944cf916c288580b614c7b6710556ca54c099d742971344a5`, Exact275 routing records, 11 samples, 25 semantic tasks, all five masks including `scaffold_only` / `B3`, UNIT_000001 parity, 50/225 provenance, global state counts, source bindings, and closed readiness fields. V2 never invokes V1 publication or `renameat2`.

The aggregate SHA256 begins with this exact domain tag, including its terminating NUL:

```text
COVAPIE_CURRENT11_DATASET_PARTIAL_SUPERVISION_ROUTING_SIDECAR_GPFS_ATOMIC_ALIAS_V2\0
```

It then frames each artifact in the builder's frozen Exact4 order: routing records CSV, task coverage CSV, sample coverage CSV, and manifest JSON. For each artifact it hashes the UTF-8 name length as an unsigned 8-byte big-endian integer, the name bytes, the payload length with the same framing, and the original payload bytes. It does not normalize the manifest or hash only per-file digest strings.

## Object and canonical layout

The canonical basename is exactly:

```text
current11-dataset-partial-supervision-routing-sidecar-v1
```

It is a relative symlink whose text is one same-parent object basename:

```text
.current11-dataset-partial-supervision-routing-sidecar-v2.object-sha256-<64 lowercase hex>-<32 lowercase hex>
```

The first field is the stored Exact4 aggregate; the second is `secrets.token_hex(16)` collision entropy and has no business meaning. V2 makes at most 64 exclusive same-parent object-directory attempts. It never reuses or removes an already existing hidden object.

Inputs must be exact `Path` objects and absolute lexical paths. Repository and state roots, the canonical parent, and every parent-chain component must be real non-symlink directories. The parent must already exist. The canonical must be outside the repository and lexically absent for materialization, including the broken-symlink case. V2 never creates the parent.

## Durable build and publication

V2 pins the parent using `O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC` and repeatedly checks its device, inode, mode, lexical identity, and descriptor identity. The hidden object is created exclusively at mode `0700`, pinned by a directory descriptor, and required to start empty.

Each Exact4 leaf is created relative to the object descriptor with `O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC` at mode `0600`. V2 writes all bytes, changes the file to `0644`, performs the final file `fsync`, closes it, reopens it without following symlinks, and verifies identity, bytes, SHA256, type, and mode. After the Exact4-only inventory and full V1 business contract pass, V2 recomputes the aggregate, changes the object to `0755`, fsyncs the object directory, rechecks every identity, and reconfirms canonical absence.

Publication is exactly one call equivalent to:

```python
os.symlink(
    object_basename,
    canonical_basename,
    target_is_directory=True,
    dir_fd=parent_fd,
)
```

The successful return of this call is the irreversible publication point. The relative missing-target operation is the no-overwrite authority on the target GPFS deployment. V2 records the alias identity and text immediately, fsyncs the parent, and performs a complete read-only post-publication verification. It does not rename, replace, copy, hard-link a directory, lock, repair, or retry alias publication.

Before publication, a failure may clean only the object and leaves created by that invocation, and only while all pinned identities, types, and inventories still match. An `EEXIST` competitor is never changed. If the competitor is clearly unrelated, V2 may clean its object; if it points to that object or ownership is ambiguous, both are preserved for review. Cleanup failure has a distinct token and retains the original failure as its cause. After successful publication, every later failure preserves both alias and object without rollback.

## Read-only check

`--check` first fresh-builds and validates source Exact4, pins the parent, requires the canonical entry to be a symlink, validates its one-component relative V2 object name, and requires strict resolution to the same-parent object. It rejects broken, absolute, slash-containing, `..`, malformed, or wrong-prefix links.

The object must be a real non-symlink directory at `0755` containing Exact4 only. Leaves must be regular non-symlink files at `0644`, with stable identities throughout each read. Stored Exact4 must pass the full V1 business validation, and its aggregate must match the digest embedded in the object name. The three stored CSV files must match fresh bytes and SHA256 exactly. Stored and fresh manifests are compared with the V1 stable lifecycle projection: only `origin_main`, `ahead`, and `behind` may differ, with their types and lifecycle contract still validated.

The check summary reports the stored object's actual manifest bytes and SHA256, not the current fresh manifest SHA. It also reports alias/object identities, link text, object name, aggregate, all stored artifact byte/line/SHA identities, counts, lifecycle, and readiness. Check performs no write, chmod, repair, relink, delete, or cleanup operation.

## CLI outcomes and readiness

Success returns code 0, empty stderr, and one compact canonical JSON line with sorted keys and no NaN. Every parse, validation, build, publication, or check failure returns code 1, empty stdout, and the unified error token on stderr.

Successful materialize/check summaries truthfully describe that tested target with `formal_sidecar_materialized=true`; this repository-only implementation phase does not claim that the future formal state target exists. The implementation readiness boundary remains:

- `gpfs_atomic_alias_materializer_v2_implemented=true`
- `ready_for_formal_sidecar_materialization_execution=true`
- `ready_for_tensor_projection_contract_design=false`
- `ready_for_tensor_materialization=false`
- `ready_for_dataloader_integration=false`
- `ready_for_model_integration=false`
- `feature_semantics_reaudit_required_before_training=true`
- `ready_for_training=false`

No formal command is run by this increment. A future authorized invocation must supply an already existing real parent and the exact canonical `output_path`.
