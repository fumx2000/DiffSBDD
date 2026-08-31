# CovaPIE CHT source-binding successor V2

## Scope

This additive V2 successor changes only active filesystem acceptance for the
published CHT V1 authority. It creates no dataset artifact, authority,
materialization path, cache, registry, training admission, tensor target, model
execution, or parameter-update authorization. The CHT V1 owner, checker, tests,
snapshot, matrix, summary, and manifest remain frozen byte-for-byte.

The Exact4 successor consists only of its production module, independent
checker, targeted tests, and this guide. OZJ V2, I12, global census refresh, and
training are outside this step.

## Public API

The production module exports exactly:

```python
CHTSourceBindingV2Error

load_frozen_cht_authority_v2(
    *,
    repo_root: Path,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]

verify_published_cht_v1_projection_v2(
    *,
    repo_root: Path,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]
```

Both operations are read-only. Overrides exist only for fail-closed tests and
are restricted to the frozen source inventory.

## Source-binding policy

Every source consumed directly by the CHT V2 production path is read through
the published B1 `verify_bound_source_v2()` helper. The combined gate requires
a regular non-symlink, owner-readable, non-world-writable source of the expected
executable class, followed by exact byte-count and SHA256 identity checks and a
stability check across the read.

The six historical CHT review-package modes remain provenance metadata:

```text
0644 0644 0644 0644 0644 0755
```

V2 derives only executable versus non-executable class from those values. Safe
checkout drift within the same class is accepted: non-executable `0600`, `0644`,
`0660`, and `0664`; executable `0700`, `0750`, `0755`, and `0775`. World-writable
sources, symlinks, identity drift, and executable-class drift fail closed. V2
does not compare a live numeric POSIX mode with a historical numeric mode.

## Published predecessor chain

The active migration chain for this step is:

```text
B1 combined source-binding policy
  -> published NEQ V2 successor
  -> CHT V2 successor
```

CHT V2 binds the published NEQ V2 owner and checker and actively calls the NEQ
V2 read-only V1 projection verifier. The NEQ V1 owner and matrix remain frozen
scientific, schema, and EXCLUDE-vocabulary precedents; CHT V2 does not call the
NEQ V1 or CHT V1 source loaders. Only CHT V1 helpers proven transitively free of
source and mutation paths are reused for in-memory scientific projection.

## Preserved CHT science

The frozen authority remains the five-event review unit
`COVAPIE_BULK_REVIEW_UNIT_BCA0E7B8C2B33410` over PDB contexts 4V3F and 5A2D,
all at `CYS:450-`. D1 through D5 remain RELEVANT, POSITIVE,
CONFIRM_OBSERVED_PAIR, SELECT_CANDIDATE_2, and
EXCLUDE_FROM_TRAINING_ONLY. D6 remains the frozen betaine-aldehyde-mediated,
reversible Cys450 thiohemiacetal, physiological non-medicinal context.

The reactive pair remains SG to C4. The selected
`STRICT_LINKER_PRESENT_V1` partition remains:

```text
heavy atoms = [C4,C5,C6,C7,C8,N1,O6]
warhead     = [C4,O6]
linker      = [C5]
scaffold    = [C6,C7,C8,N1]
```

All five canonical tasks remain structurally applicable with IDs
`[0,1,2,3,4]`: `warhead_only` (A), `linker_plus_warhead` (B),
`scaffold_plus_warhead` (B2), `scaffold_only` (B3), and
`scaffold_plus_linker_plus_warhead` (C). There is no sixth task. D5 exclusion
does not turn the positive chemistry into a negative and does not alter task
applicability.

POST source evidence remains present for all five events, while POST geometry
training authority, PRE geometry authority, PRE precursor-topology authority,
and PRE reconstruction remain zero. POST-to-PRE copying and PRE zero fill remain
false. Training exclusion remains true; future candidacy, admission,
materialization, runtime usability, and readiness for training remain false.

## Verification

Run the targeted tests and independent checker from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
pytest -p no:cacheprovider -q \
tests/test_covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
python \
scripts/check_covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py
```

The checker accepts exactly `CANDIDATE_UNTRACKED` and `TRACKED_CLEAN`. It binds
the published B1 and NEQ V2 dependencies, all frozen CHT V1 code and artifacts,
the historical review sources, and the unchanged current 2A2 census. It also
checks the production AST and transitive V1 helper graph, exercises safe and
unsafe mode cases, source-identity failures, the V1 exact-mode false-failure
contrast, scientific equivalence, Exact5 applicability, and the training
boundary.

Success makes the thin CHT successor ready for external review and permits only
the later OZJ successor step. It does not complete V2 B2 and does not establish
training readiness. A feature-semantics audit remains required before any
formal training or parameter update; Step12D was only a smoke legality check,
not the final training-feature contract.
