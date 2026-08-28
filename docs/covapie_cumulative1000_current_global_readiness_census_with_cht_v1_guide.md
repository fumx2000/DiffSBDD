# CovaPIE cumulative1000 current global readiness census with CHT V1

## Purpose and authority boundary

This additive derived refresh consumes the published NEQ census, CHT formal
human decision, CHT ingestion matrix, and CHT reconciliation. The predecessor
reports 95 chemistry-positive events, 36 training `INCLUDE` events, 59
`EXCLUDE_FROM_TRAINING_ONLY` events, and 19 future admission candidates.
Published CHT contributes a source-derived Exact5 delta of +5 positive and +5
`EXCLUDE_FROM_TRAINING_ONLY`, producing totals of 100 and 64. `INCLUDE`
remains 36 and future candidacy remains 19.

The refresh deep-copies all 1,000 predecessor rows, overlays only CHT Exact5,
and leaves the other 995 dictionaries equal to the predecessor. It creates no
human, chemistry, pair, role, reusable, split, tensor, training-admission, or
training authority. Human-review status cites the CHT formal decision;
chemistry, task, pair, role, and positive provenance cite the published CHT
event matrix.

## CHT projection and unchanged boundaries

CHT ranks 913-915 and 958-959 cover PDBs 4V3F and 5A2D, with five Cys450
events. Every event retains the observed SG-C4 structural evidence. The formal
semantics are task-relevant positive chemistry, candidate 2 with
`STRICT_LINKER_PRESENT_V1`, W `[C4,O6]`, L `[C5]`, S `[C6,C7,C8,N1]`, and
`EXCLUDE_FROM_TRAINING_ONLY`.

The overlay changes exactly 17 census presentation/provenance fields per CHT
event. It does not alter structural identity or evidence fields. It creates no
model-bound pair target, complete authoritative POST-adduct topology, POST
training authority, PRE C4=O or geometry authority, split authority, future
candidacy, formal admission, training materialization, or runtime usability.

Structural totals remain raw/exact/explicit/CCD-compatible 997/867/867/865.
Geometry remains POST source/sample/training 867/21/17 and PRE
source/sample/training 0/0/0. No POST-to-PRE promotion or PRE zero-fill is
performed.

## Canonical Exact5 and global counts

The global V1 mask contract remains exactly five tasks:

| ID | Semantic long name | Alias | Applicable count |
|---:|---|---|---:|
| 0 | `warhead_only` | A | 100 |
| 1 | `linker_plus_warhead` | B | 44 |
| 2 | `scaffold_plus_warhead` | B2 | 44 |
| 3 | `scaffold_only` | B3 | 100 |
| 4 | `scaffold_plus_linker_plus_warhead` | C | 100 |

No sixth task is introduced. The 44 strict rows support all five tasks; the 56
direct rows support A/B3/C (`[0,3,4]`). Pair and role sample authority both
become 100, while model-bound pair targets remain 41 and runtime targets remain
17.

Chemistry becomes 100 positive, 86 not established, and 814 unresolved. Task
relevance becomes 101 relevant, 86 not relevant, and 813 unresolved. Training
use becomes 36 `INCLUDE`, 64 `EXCLUDE_FROM_TRAINING_ONLY`, 86 not applicable,
and 814 unresolved.

## Human review, blockers, and next review unit

Within the frozen priority-review population of 338 events / 131 units, the
published reconciliation reports 83 positive events / 10 units, 24 negative
events / 4 units, 107 completed events / 14 units, and 231 pending events / 117
units. The global presentation count `COMPLETED_HUMAN_NEGATIVE=54` is a
different census and must not be replaced by the priority-review count 24.

Within the 100 positive events, human training exclusion is 64, missing split
authority is 59, missing tensor integration is 59, missing POST training
authority is 83, missing training admission is 95, and feature semantics are
pending for all 100. The corresponding within-`INCLUDE` counts are 11, 7, 19,
and 31. Pair and role authority are absent for 900 of all 1,000 events but none
of the 100 positive events. These blocker sets are non-exclusive and must not
be summed.

The frozen 131-unit queue is filtered through published CHT reconciliation;
no queue artifact is created or reordered by hand. CHT disappears from the
pending set. The new first unit is
`COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450`: ligand OZJ, four events, PDB
4CL8. This refresh does not begin OZJ review.

## Publication, training readiness, and reproducibility

Until this Exact7 is externally reviewed, committed, and pushed, the published
current global census remains NEQ: 95 positive, 96 relevant, 36 `INCLUDE`, 59
`EXCLUDE`, 19 future candidates, and CHT `CURRENTLY_UNREVIEWED`. The
uncommitted candidate is 100 positive, 101 relevant, 36 `INCLUDE`, 64
`EXCLUDE`, and 19 future candidates, with CHT `COMPLETED_HUMAN_POSITIVE` and
OZJ as the pending queue head.

The candidate retains 5 formally admitted events, 17 runtime-usable events,
and 0 events ready for formal training. `READY_FOR_FORMAL_TRAINING` remains
false. Feature semantics remain `AUDIT_REQUIRED_LATER`; Step12D was only a
smoke legality check, not a final training-feature contract. A separate
feature-semantics audit must resolve the historical unknown atom-feature policy
before formal training or training-preparation work.

The CSV, summary, and manifest are deterministic source-derived projections.
The manifest binds the candidate contract files, the exact predecessor and CHT
semantic inputs, and the CSV/summary outputs. It never records its own SHA256.
Projection digests are drift-detection contracts, not science or human
authority.
