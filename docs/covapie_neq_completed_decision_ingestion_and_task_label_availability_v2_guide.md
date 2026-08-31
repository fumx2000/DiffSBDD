# CovaPIE NEQ completed-decision source-binding successor V2

## Scope

This additive V2 successor changes only the active filesystem acceptance policy
used to read the frozen NEQ authority. It does not modify the NEQ V1 owner,
checker, tests, snapshot, matrix, summary, manifest, formal human decision, or
frozen review package.

The successor consists of exactly four repository files:

1. `src/covalent_ext/covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py`
2. `scripts/check_covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py`
3. `tests/test_covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py`
4. `docs/covapie_neq_completed_decision_ingestion_and_task_label_availability_v2_guide.md`

There are no V2 materialized snapshot, matrix, summary, manifest, CSV, or JSON
files.

## Published dependencies

The active reader binds the published B1 common policy:

```text
src/covalent_ext/covapie_source_binding_policy_v2.py
SHA256=c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee
```

It also binds and exercises the published YUN V2 successor as the upstream V2
migration precedent:

```text
src/covalent_ext/covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py
SHA256=a10c929ea86258ac39bc787b3108d622b65c97617e62b19a44bf3711fbffbd52
published commit=5a34e260e57598ab62905f0171e43a67acc188e2
```

YUN V2 supplies only the proven source-binding migration pattern. The published
YUN V1 matrix remains the frozen scientific and schema precedent.

## Source-binding policy

Every direct authority or source read performed by NEQ V2 is routed through
`verify_bound_source_v2()`. Acceptance requires all of the following:

- a regular non-symlink file;
- owner readability;
- no world-write bit;
- the expected executable class;
- exact byte count;
- exact SHA256;
- stable filesystem identity across the read.

Historical mode strings remain present in returned provenance. They are not
compared to the live numeric POSIX mode. They are used only to derive the
expected executable class:

```text
0600, 0644, 0660, 0664 -> non-executable
0755                   -> executable
```

Consequently, safe checkout mode drift within the same executable class is
accepted. World-writable sources, symlinks, byte-count changes, content changes,
and executable-class changes fail closed.

## Public API

```python
NEQSourceBindingV2Error

load_frozen_neq_authority_v2(
    *,
    repo_root: Path,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]

verify_published_neq_v1_projection_v2(
    *,
    repo_root: Path,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]
```

The API is read-only. There is no materialization, mutation, cache, registry, or
global resolver API.

## V1 reuse boundary

NEQ V2 verifies sources itself and then reuses only NEQ V1 pure in-memory
scientific functions. Static transitive call-graph checks reject reuse that can
reach the V1 exact-mode gate, a source loader, artifact construction entry point,
materialization, or materialized-output checking.

The active V2 path does not call the NEQ V1 `_verify_payload` function or the YUN
V1 source loader. The YUN V2 projection is called where the upstream migration
precedent is required.

## Frozen NEQ science

The formal authority remains the current NEQ Exact6 decision:

```text
event count=6
D1=RELEVANT
D2=POSITIVE
D3=CONFIRM_OBSERVED_PAIR
protein atom=SG
ligand atom=C3
D4=SELECT_CANDIDATE_7
D5=EXCLUDE_FROM_TRAINING_ONLY
D6=frozen NEM-mediated PCNA Cys22/Cys81 context
```

The site distribution remains three CYS:22- events and three CYS:81- events.
The role profile and partition remain:

```text
role profile=DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
warhead=[C1,C2,C3,C4,N1,O1,O2]
linker=[]
scaffold=[C5,C6]
```

The canonical task contract remains exactly five tasks:

1. `warhead_only` / A
2. `linker_plus_warhead` / B
3. `scaffold_plus_warhead` / B2
4. `scaffold_only` / B3
5. `scaffold_plus_linker_plus_warhead` / C

The structurally applicable task IDs for the direct profile remain `[0, 3, 4]`.
D5 exclusion does not alter structural applicability and does not convert the
positive chemistry decision into a negative decision.

## Topology and training boundary

The source CCD C2=C3 double-bond record remains frozen component provenance. It
does not create PRE or complete POST authority. The following remain false or
zero as appropriate:

```text
POST_geometry_training_label_available_now=false
PRE_geometry_authority_available=false
PRE_precursor_topology_authority_available=false
PRE_reconstruction_performed=false
POST_bond_order_reconstruction_performed=false
```

NEQ remains scientifically relevant and positive while excluded from training:

```text
human_training_excluded=true
candidate_for_future_training_admission=false
training_admitted=false
training_materialization_allowed_now=false
current_runtime_model_usable=false
READY_FOR_TRAINING=false
```

Step12D remains a smoke legality check, not a final training-feature contract. A
feature-semantics audit is still required before any formal training work.

## Published V1 equivalence

`verify_published_neq_v1_projection_v2()` loads source authority through V2,
rebuilds the V1 snapshot, matrix, and summary in memory with pure V1 semantics,
and requires exact byte equality with the published files. The published
manifest is bound by byte count and SHA256, then its scientific and authority
fields are checked independently. No V2 manifest is generated.

## Validation

Run the targeted suite:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
pytest -p no:cacheprovider -q \
tests/test_covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py
```

Run the independent checker:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
python \
scripts/check_covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py
```

The checker accepts exactly two lifecycle profiles:

- `CANDIDATE_UNTRACKED`: baseline HEAD and origin with only the strict Exact4 as
  ordinary untracked files;
- `TRACKED_CLEAN`: a clean one-parent Exact4-only child of the baseline, either
  one commit ahead of origin or already published at origin.

Partial, staged, dirty, mixed, or extra-file states fail closed.

## Current global boundary

This successor does not refresh or reconcile the global census. The checker
binds the current published 2A2 census and requires the existing counts:

```text
positive=112
relevant=113
INCLUDE=44
EXCLUDE=68
future=27
pair=112
role=112
A=112
B=52
B2=52
B3=112
C=112
```

Successful validation establishes readiness only for external review and the
next CHT source-binding successor step. It does not establish V2-B2 completion
or training readiness.
