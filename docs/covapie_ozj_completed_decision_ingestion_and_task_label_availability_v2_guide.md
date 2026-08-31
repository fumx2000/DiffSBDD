# CovaPIE OZJ source-binding successor V2

## Scope

This additive successor changes only active source-binding acceptance for the
published OZJ V1 scientific projection. It does not modify or rematerialize OZJ
V1, refresh the global census, create training admission, start F24 or I12, or
perform model or training work.

The V2 publication inventory is exactly four text files: the production owner,
the independent checker, the targeted tests, and this guide. There is no V2
snapshot, matrix, summary, manifest, CSV, or JSON artifact.

## Source-binding migration

Every source consumed by the V2 owner is verified through the published B1
`verify_bound_source_v2()` gate. The gate requires a regular non-symlink,
owner-readable and non-world-writable file, the expected executable class, and
exact byte count and SHA256. Parsing uses the verified in-memory bytes.

The six frozen OZJ review-package sources preserve their historical mode
metadata as `0664` six times. That metadata is provenance and executable-class
input only; it is not a live numeric-mode equality. All six sources, including
`ligand_ozj_review_package_v1.py`, have `expected_executable=false`. Safe
non-executable modes such as `0600`, `0644`, `0660`, and `0664` therefore retain
the same authority, while executable-class drift and world-writable files fail
closed.

## Dual published predecessors

OZJ V2 binds the published CHT V2 owner and checker and actively calls the CHT
V2 V1-projection verifier. This preserves the frozen CHT V1 STRICT Exact5
matrix as the architecture precedent.

OZJ V2 also binds the published YUN V2 owner and checker and actively calls the
YUN V2 V1-projection verifier. This preserves the frozen YUN V1 matrix and
formal decision as the INCLUDE and future-admission-candidate precedent.

Neither predecessor replaces its frozen V1 scientific provenance. OZJ V2 does
not fall back to the OZJ, CHT, or YUN V1 source gates.

## Frozen scientific projection

The authority remains the four-event `4CL8` Exact4 review unit
`COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450`. The approved decisions remain D1
`RELEVANT`, D2 `POSITIVE`, D3 observed `SG` to `CAF`, D4 candidate 1, D5
`INCLUDE`, and the exact frozen D6 target-directed, structure-based-designed
TbPTR1 native-Cys168 medicinal antiparasitic covalent-inhibitor context.

The role profile remains `STRICT_LINKER_PRESENT_V1`. The warhead is exactly
`[CAF,OAD]`, the linker is exactly `[CAG,CAH,CAI,CAJ,CAP,CAQ]`, and the
scaffold remains the frozen thirteen-atom set. All canonical tasks A, B, B2,
B3, and C apply; task IDs are `[0,1,2,3,4]`, B3 is present, and no sixth task is
created.

D5 `INCLUDE` continues to derive future-admission candidacy during ingestion.
It does not create formal training admission. Training materialization,
runtime-model usability, parameter updates, and `READY_FOR_TRAINING` all remain
false.

Source CAF-OAD bond-order provenance and the explicit observed SG-CAF event
connection remain distinct evidence. Neither is promoted to complete POST
adduct topology authority. POST geometry training authority, PRE topology and
geometry authority, PRE reconstruction, POST bond-order reconstruction,
POST-to-PRE copying, and PRE zero filling all remain absent.

## Verification

Run the targeted tests:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
pytest -p no:cacheprovider -q \
tests/test_covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py
```

Run the independent checker:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
python scripts/check_covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py
```

The checker accepts only `CANDIDATE_UNTRACKED` at the published baseline or a
single exact-child `TRACKED_CLEAN` commit containing the strict Exact4. It
independently freezes OZJ V1 code and artifacts, both V2 predecessors, the B1
helper, the unchanged 2A2 census, mode/security regressions, the pure-helper
call graph, scientific equivalence, and the training boundary.

OZJ V2 is readiness evidence only for the later V2-B2-5 F24 successor. V2-B2 is
not complete. A feature-semantics audit remains required before any formal
training preparation or parameter update; Step12D was a smoke legality check,
not a final training-feature contract.
