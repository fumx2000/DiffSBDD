# CovaPIE YUN source-binding successor V2-B2-1 guide

## Purpose

This step is the first active-consumer migration onto the published B1
source-binding policy. It adds a thin YUN compatibility successor and changes
only active filesystem acceptance:

```text
exact content identity
+ filesystem security
+ executable class
- exact numeric POSIX mode equality
```

YUN V1 remains the frozen scientific owner. Its production source, checker,
tests, snapshot, matrix, summary, and manifest are byte-preserved. This step
does not replace or rematerialize V1 outputs, create V2 data artifacts, update
another consumer, start I12, or train.

## Public API

The V2 production module exports exactly:

```python
YUNSourceBindingV2Error

load_frozen_yun_authority_v2(
    *,
    repo_root: Path,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]

verify_published_yun_v1_projection_v2(
    *,
    repo_root: Path,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]
```

There is no materialization API, registry, cache, global resolver framework,
or mutation API.

## Source-read boundary

Every authority source consumed by the loader is read through the published
B1 `verify_bound_source_v2()` helper. The loader verifies the exact byte count
and SHA256 plus these filesystem requirements:

```text
regular file
non-symlink
owner-readable
not world-writable
expected executable class
```

The successor resolves only the frozen namespaces YUN already uses:

```text
repository_relative
repository_parent_relative
project_parent_relative
```

Namespace strings in returned provenance remain historical. The local
resolver does not establish a global resolution framework.

The successor does not call V1 `_verify_payload()`, the V1 loader, V1 source
binding helpers, V1 artifact builders, or V1 materialization paths. After B1
has returned verified bytes, the successor reuses only frozen V1 constants and
pure semantic projection helpers. The independent checker guards that boundary
with AST and transitive local-call analysis.

## Legacy mode provenance and executable class

The six frozen review-package records retain their historical mode values:

```text
0644
0644
0644
0644
0644
0755
```

These values are classified as both:

```text
LEGACY_PROVENANCE_METADATA_PRESERVED
SECURITY_EXECUTABLE_CLASS_INPUT
```

The live mode never replaces the historical record. V2 derives only whether
an executable bit was historically present. It does not compare the live mode
to the exact legacy number.

For a non-executable reviewed source with unchanged bytes and SHA256:

```text
0644 PASS
0664 PASS
0600 PASS
0660 PASS
0666 FAIL: world writable
```

For the executable review-package validator with unchanged bytes and SHA256:

```text
0755 PASS
0775 PASS
0750 PASS
0700 PASS
0644 FAIL: executable class missing
0777 FAIL: world writable
```

This is the intended contrast with the V1 exact-mode contract, under which a
historical `0644` binding presented at safe live mode `0664` would fail with
`BOUND_SOURCE_MODE_MISMATCH`.

## Frozen YUN science

The same formal decision remains authoritative:

```text
review unit = COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D
event count = 7
D1 = RELEVANT
D2 = POSITIVE
D3 = CONFIRM_OBSERVED_PAIR
D4 = SELECT_CANDIDATE_4
D5 = INCLUDE
role profile = DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
warhead = NAS, CAW, OAC, CAO, CAN
linker = empty
applicable canonical tasks = 0, 3, 4
```

The canonical vocabulary remains the semantic Exact5:

```text
warhead_only
linker_plus_warhead
scaffold_plus_warhead
scaffold_only
scaffold_plus_linker_plus_warhead
```

`scaffold_only` / B3 remains present. No sixth task is created.

## Scientific-equivalence and artifact proof

The compatibility verifier reconstructs the V1 snapshot, matrix, and summary
in memory from the V2-verified formal source and pure V1 projection logic. The
derived bytes must exactly equal the already published V1 bytes. The published
manifest is independently content-bound and its source, output, task, and
authority-boundary records are checked.

No artifact is written. The existing published snapshot, matrix, summary, and
manifest remain the sole YUN V1 outputs.

## PRE, POST, and training boundary

The migration does not reinterpret scientific or training readiness:

```text
POST source evidence count = 7
POST training authority count = 0
PRE geometry authority count = 0
PRE precursor topology authority count = 0
PRE reconstruction count = 0
future training admission candidate = true
formal training admitted = false
training materialization allowed = false
current runtime model usable = false
READY_FOR_TRAINING = false
```

D5 INCLUDE is still future-admission candidacy, not training admission, tensor
authority, runtime usability, materialization authority, or permission for a
parameter update.

## Lifecycle and next boundary

The checker accepts exactly two successful lifecycle profiles:

```text
CANDIDATE_UNTRACKED
TRACKED_CLEAN
```

The candidate profile requires the published baseline at both `HEAD` and
`origin/main`, no working or cached diff, and exactly the V2 Exact4 as ordinary
untracked files. The tracked-clean profile requires one exact child commit
whose changed paths are the same Exact4, either one commit ahead of the
baseline remote or published with the remote at that child.

A successful candidate establishes:

```text
YUN_V2_SUCCESSOR_IMPLEMENTED = true
YUN_V1_BYTES_PRESERVED = true
YUN_V1_ARTIFACTS_PRESERVED = true
YUN_EXACT_POSIX_SEMANTIC_MODE_RETIRED_FROM_V2_ACTIVE_PATH = true
READY_FOR_V2_B2_2_NEQ_SUCCESSOR = true
V2_B2_COMPLETE = false
```

NEQ, CHT, OZJ, F24, 2A2, and integration remain future work. I12 review and
training are not started. Before formal training or any parameter update, the
feature-semantics audit remains required, including the historical
`UNKNOWN_ATOM_FEATURE_POLICY` / `feature_semantics_known=False` state. Step12D
remains a smoke legality check, not a final training-feature contract.
