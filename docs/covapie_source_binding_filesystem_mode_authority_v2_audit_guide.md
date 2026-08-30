# CovaPIE source-binding filesystem-mode authority V2 audit guide

## Scope

This Exact7 is a Phase-A, read-only audit and policy-design gate. It inventories
filesystem-mode handling in the published 2A2 census baseline and the bounded
`covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1`
authority surface. It does not implement V2 runtime behavior, rewrite a V1
validator, alter authority JSON, call `chmod`, start I12, or start training.

The repository scan universe is derived from the published baseline tree
`89a8cf17a235cdca9eecad275794a5a86be2e01d`. This prevents the new audit from
becoming a lifecycle-dependent self-input. Repository Python is scanned under:

- `src/covalent_ext/**/*.py`
- `scripts/check_covapie*.py`
- `tests/test_covapie*.py`

All baseline JSON under `data/derived/covalent_small/` is parsed as structured
data. The external scan reads Python only from `review-preparation-v1`,
`human-review-preview-v1`, and `formal-human-decision-v1`, and JSON only from
the latter two authority/provenance stages. Discovered Python is parsed with
`ast`; it is never executed.

## Semantic distinction

Semantic/source identity answers whether evidence bytes are the same. V2 uses
`path`, `path_namespace`, `byte_count`, and `sha256`. A Git consumer may also
use a Git blob ID and the Git-representable `100644`/`100755` file class when
the executable distinction is relevant.

Filesystem security/hygiene answers whether a source is safe to consume. It is
a separate gate: regular file, non-symlink, owner-readable, not world-writable,
and expected executable/non-executable class where relevant. Exact checkout
permissions such as `0600`, `0644`, or `0664` are not semantic identity.

Group write is not prohibited automatically. Published project evidence uses
`0664` legitimately, so the proposed gate accepts safe group-writable files
provided they are not world-writable and satisfy the remaining safety rules.
Candidate Exact7 files use the safe non-executable `0644`/`0664` family.

## Exact6 occurrence classes

Every inventoried occurrence has exactly one class:

1. `SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE`
2. `SECURITY_HYGIENE_MODE_CHECK`
3. `CANDIDATE_ARTIFACT_MODE_HYGIENE`
4. `GIT_EXECUTABLE_BIT_OR_FILE_CLASS_CONTRACT`
5. `REPORTING_OR_DIAGNOSTIC_MODE_METADATA`
6. `AMBIGUOUS_REQUIRES_HUMAN_REVIEW`

Each row also records one lifecycle class and one debt disposition. Historical
published V1 authority and its validators are immutable. Exact-mode coupling
there is preserved for provenance but must not propagate. Active/current
exact-mode semantic coupling is the bounded V2 migration surface. Security,
candidate, Git file-class, and reporting-only uses are preserved unless a row
explicitly requires review.

## Known 2A2 regression

The audit independently parses the historical 2A2 formal validator. Its
`read_bound_file` contract rejects a source through `SOURCE_DRIFT` when exact
mode, byte count, or SHA256 differs. The audit requires static proof of these
three bindings:

- `published_role_profile_runtime_owner`: `0644`
- `canonical_role_and_task_semantics_owner`: `0644`
- `published_1f8_event_task_label_availability`: `0600`

Identical bytes and SHA256 can therefore fail solely because a checkout
reconstructs `0664`. No live file needs to be modified to prove this contract.

## Negative control

The current published
`covapie_cumulative1000_current_global_readiness_census_with_2a2_v1` manifest
must contain exactly 108 semantic source bindings with only:

- `artifact_role`
- `path`
- `path_namespace`
- `byte_count`
- `sha256`

Their canonical digest must be
`964f4b3747d42a43d05d1adc6f432264ce546ef93f9faace23fa3379452bfd15`.
No exact POSIX mode field is permitted. This is the known-good V2 reference.

## Artifacts

The derived directory contains exactly:

- `covapie_source_binding_filesystem_mode_authority_v2_inventory.csv`
- `covapie_source_binding_filesystem_mode_authority_v2_summary.json`
- `covapie_source_binding_filesystem_mode_authority_v2_manifest.json`

The inventory has deterministic ordering and occurrence IDs. The summary
derives its class and disposition counts from the inventory. The manifest binds
the published baseline, every scanned source, the current 2A2 census reference,
the inventory, and the summary. Semantic bindings in the new manifest do not
contain runtime mode. The manifest has no timestamp, host, PID, absolute path,
or self-SHA.

## Validation

From the repository root, run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
pytest -p no:cacheprovider -q \
tests/test_covapie_source_binding_filesystem_mode_authority_v2_audit.py
```

Then run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
python scripts/check_covapie_source_binding_filesystem_mode_authority_v2_audit.py
```

The checker accepts exactly two success profiles:

- `CANDIDATE_UNTRACKED`: all and only Exact7 are ordinary untracked files.
- `TRACKED_CLEAN`: all Exact7 are tracked and the worktree/index are clean.

`TRACKED_CLEAN` covers both the exact one-commit successor before push, while
`origin/main` remains at the baseline, and the same successor after a normal
fast-forward push, when `origin/main` equals `HEAD`. These are repository-
relation subcases, not additional lifecycle profiles.

Partial tracking, staging, dirty files, or any extra ordinary untracked file
fails closed.

Run the published negative-control checker once:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
python scripts/check_covapie_cumulative1000_current_global_readiness_census_with_2a2_v1.py
```

## Minimal V2 implementation sequence

- V2-B1: add one common content-identity helper and a separate security policy.
- V2-B2: adopt it only in new/current active authority consumers identified by
  this inventory.
- V2-B3: add compatibility regression proving V1 validators and authority bytes
  remain untouched.
- V2-B4: prohibit exact numeric POSIX mode in future semantic-binding templates
  and checkers.

Historical repository HEAD/tree/subject/ahead-behind contracts are separate
future technical debt. They do not block this narrowly scoped mode design.

This gate does not establish training readiness. I12 remains unstarted,
`TRAINING_STARTED=false`, `READY_FOR_TRAINING=false`, and the feature-semantics
audit remains required later.
