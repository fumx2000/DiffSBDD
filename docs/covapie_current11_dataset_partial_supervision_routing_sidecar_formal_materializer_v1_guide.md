# CovaPIE Current11 dataset routing sidecar formal materializer V1

This increment implements the formal file materializer for the published
Current11 dataset partial-supervision routing sidecar. It does not materialize
the formal target during implementation and does not authorize tensorization,
dataloader or model integration, loss consumption, or training.

The only public Python API is:

```python
materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_v1(
    *, repo_root: Path, state_root: Path, output_dir: Path
) -> dict[str, object]
```

The API always calls the published builder first and validates its in-memory
Exact4, Exact275 routing contract, Exact5 canonical masks (including
`scaffold_only` / `B3`), UNIT parity and provenance, and closed readiness. It
accepts no payload, routing, eligibility, policy, artifact, or byte overrides.

Publication requires an absolute output path outside the repository, a real
non-symlink parent chain, a missing target, and same-parent staging. The staging
directory starts at mode `0700`. Each Exact4 file is exclusively created,
fully written, fsynced, changed to mode `0644`, reread, and byte/SHA verified.
The staging directory is fsynced, changed to mode `0755`, and published once
with `renameat2(RENAME_NOREPLACE)`. The parent is then fsynced and the complete
published directory is revalidated. There is no overwrite, repair, copy, or
archive fallback.

On failure, cleanup is limited to the staging directory and files created by
that invocation. The recorded staging `st_dev`/`st_ino` and every staged file
identity are rechecked before removal. A cleanup identity mismatch or removal
failure is reported explicitly, with the original publication failure retained
as the cause; pre-existing or competing targets are never removed.

The CLI accepts exactly `--repo-root`, `--state-root`, `--output-dir`, and the
optional flag `--check`. Materialize mode requires a missing target. Check mode
requires an existing target, rebuilds fresh bytes, and performs read-only
verification of Exact4 inventory, modes, row counts, manifest semantics,
lifecycle, readiness, and absence of extra entries. The three CSV files remain
raw-byte and SHA256 equal to the fresh builder outputs.

The formal target retains the builder manifest lifecycle snapshot from its
materialization time. Later ordinary repository successors can legitimately
change only the fresh builder lifecycle fields `origin_main`, `ahead`, and
`behind`. Check validates both lifecycle objects strictly and compares complete
manifest projections with only that dynamic Exact3 removed. The stable
`base_commit`, `future_formal_subject`, `candidate_paths`, `lifecycle_profile`,
and `formal_candidate_commit` fields, plus every non-lifecycle manifest field,
must remain equal. Check mode never repairs, overwrites, chmods, or deletes, and
its summary reports the bytes, lines, and SHA256 actually stored in the formal
target rather than the fresh manifest's current dynamic identity.

The future formal path is:

```text
STATE_ROOT/formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1
```

After an explicit future authorization creates the real `formal-sidecars`
parent, the formal materialization command will be:

```bash
PYTHONDONTWRITEBYTECODE=1 python -B scripts/materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_v1.py \
  --repo-root /absolute/path/to/DiffSBDD-base \
  --state-root /absolute/path/to/covapie-state \
  --output-dir /absolute/path/to/covapie-state/formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1
```

Add `--check` to validate an already published target without mutation. Both
successful modes emit one canonical compact JSON line. Every failure emits only
the unified error token on stderr and exits with status 1. `-h`, `--help`,
unknown arguments, positional arguments, and overwrite/training options fail
closed.

Repository lifecycle reporting admits exactly the precommit candidate,
committed-unpushed, and published-successor profiles. Formal materialization
does not change the closed readiness boundaries: runtime consumption, tensor
materialization, dataloader integration, model integration, and training remain
unauthorized, and a feature-semantics re-audit remains required before training.
