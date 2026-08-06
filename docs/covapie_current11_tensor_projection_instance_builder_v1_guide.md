# CovaPIE Current11 tensor projection instance builder V1

## Scope

This increment assembles the published Current11 routing contract and audited
payload bundle into a deterministic Exact11 by Exact25 projection instance. The
instance and its report are returned as bytes and are never written to disk.

The only public API is:

```python
build_covapie_current11_tensor_projection_instance_v1(
    *, repo_root: Path, state_root: Path
) -> dict[str, bytes]
```

The Exact2 result contains, in order:

1. `current11_tensor_projection_instance.json`
2. `current11_tensor_projection_instance_builder_report.json`

## Contract boundaries

The instance has the frozen Exact24 fields and uses the formal routing records
as the source for every routing matrix. Only tasks 0, 1, 2, 6, and 12 carry the
published audited payloads. Their 55 validity cells are combined with routing
eligibility to produce 55 data-availability cells. The five audited tasks are
not the five canonical generation masks.

All 25 candidate slots are empty, candidate validity is all false, and both the
loss-authorization and runtime-consumer matrices are all false. The 55
candidate-eligible routing cells remain visible only as routing metadata.

The canonical generation-mask order remains `warhead_only` (A),
`linker_plus_warhead` (B), `scaffold_plus_warhead` (B2), `scaffold_only` (B3),
and `scaffold_plus_linker_plus_warhead` (C). No sample generation-mask labels
are produced.

Task 2 values are source-table row indices and require a separately authorized
row-index to batch-index remap adapter before any model use. Task 6 preserves
raw reviewed tokens, including the valid F1 token without inventing a numeric
ligand-atom mapping. Task 12 is observed-complex geometry only and is not pre-
or post-covalent geometry.

## Read-only verification

Run the checker with both roots:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python \
  scripts/check_covapie_current11_tensor_projection_instance_builder_v1.py \
  --repo-root /absolute/path/to/DiffSBDD-base \
  --state-root /absolute/path/to/covapie-state
```

On success it prints one compact JSON line containing only the builder report.
It does not materialize the instance. Unsupported output, override, tensor,
candidate, loss, or training arguments fail with the single checker error
token.

The builder verifies the published payload-builder module identity, invokes it
twice, verifies Exact8 byte identity and frozen digests, independently reads the
formal routing sidecar, assembles the stable instance twice, and verifies that
the formal sidecar snapshot is unchanged. During untracked development only,
a local compatibility observation hides precisely this increment's four
`?? path` entries from the historical predecessor status check; every other
status entry remains visible and fails closed.

## Readiness

This increment permits design of a Task 2 batch-index remap contract only. It
does not authorize a dataloader, model integration, loss, tensor artifact,
training, or formal materialization. Step12D remains a smoke legality check,
not a final feature contract. `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False` still require a feature-semantics re-audit
before training.
