# CovaPIE source-binding historical immutability proof V2

## Scope

This Phase-B3 component is a read-only proof of the filesystem-mode migration
history. It is unrelated to the canonical `scaffold_only` / `B3` mask alias.
The canonical task vocabulary remains exactly five tasks.

The proof compares the frozen Phase-A audit commit
`26555ff6240ee53c817726331c8353dcb62dc82e` with the published Phase-B2
endpoint `049d446e0fa854fab9986a9e2fb302d0b9547231`. Candidate HEAD is never used
as the Phase-B2 proof input.

## Public API

```python
from pathlib import Path

from covalent_ext.covapie_source_binding_historical_immutability_proof_v2 import (
    verify_covapie_source_binding_historical_immutability_proof_v2,
)

result = verify_covapie_source_binding_historical_immutability_proof_v2(
    repo_root=Path.cwd(),
)
```

The API returns a deterministic in-memory dictionary. It does not write a
manifest, snapshot, report, registry, cache, or data artifact.

## Evidence contract

The verifier fails closed unless all of the following remain exact:

- the eight-commit, single-parent Phase-A-to-Phase-B2 history;
- the additive-only Exact32 tracked delta;
- the Phase-A inventory, summary, and manifest Git-object bytes;
- all 1,755 frozen source bindings, comprising 1,727 repository sources and 28
  external `covapie-state` sources;
- all 2,171 frozen inventory classifications and their source coverage;
- the Exact8 original active V1 migration targets;
- the Exact3 known mode-regression references; and
- the published B1 policy and B2 active-consumer integration.

Frozen `byte_count` and SHA256 are content identity. Historical numeric POSIX
mode values remain provenance and are not replayed as live equality checks.
Safe non-executable `0644` and `0664` copies therefore remain valid when their
bytes are exact. World-writable files remain rejected by the B1 security gate.

Manifest paths are replayed only from the frozen binding list. A
`repository_relative` path must remain under the repository. A
`repository_parent_relative` path must remain under the sibling
`covapie-state` root. Absolute paths, `..`, unexpected namespaces, and symlink
escapes fail closed.

## Authority boundary

The effective authorities remain:

- filesystem source acceptance: `SOURCE_BINDING_POLICY_V2`;
- sample scientific projection: `PUBLISHED_V1_ARTIFACTS`;
- current global state: `PUBLISHED_2A2_V1_GLOBAL_CENSUS`; and
- historical immutability: `PHASE_A_AUDIT_FROZEN_SOURCE_BINDINGS`.

This proof does not rewrite a historical validator or authority, refresh the
current census, execute reconciliation, materialize data, start I12, or perform
training. Passing Phase B3 permits external review and a future Phase-B4 guard;
it does not establish training readiness. A feature-semantics audit remains a
formal prerequisite before training-preparation or parameter updates.

## Validation

Candidate-untracked verification:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
pytest -p no:cacheprovider -q \
tests/test_covapie_source_binding_historical_immutability_proof_v2.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
python scripts/check_covapie_source_binding_historical_immutability_proof_v2.py
```

The checker accepts exactly two lifecycle profiles:

- `CANDIDATE_UNTRACKED`: baseline HEAD and `origin/main`, with only the strict
  Phase-B3 Exact4 as ordinary untracked files; or
- `TRACKED_CLEAN`: one Exact4-only child commit of the baseline, or the same
  commit after publication when `origin/main` equals HEAD.

Partial, staged, dirty, extra-file, or multi-commit profiles are rejected.
