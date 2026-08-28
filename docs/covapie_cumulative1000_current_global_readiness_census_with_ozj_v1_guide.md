# CovaPIE cumulative1000 current global readiness census with OZJ V1

## Purpose and authority boundary

This additive derived refresh consumes the published CHT census, OZJ formal
human decision, OZJ ingestion matrix, and OZJ reconciliation. The predecessor
reports 100 chemistry-positive events, 101 task-relevant events, 36 training
`INCLUDE` events, 64 `EXCLUDE_FROM_TRAINING_ONLY` events, and 19 future
admission candidates. Published OZJ contributes a source-derived Exact4 delta
of +4 positive, +4 `INCLUDE`, and +4 ingestion-derived future candidates.
The candidate totals are therefore 104 positive, 105 relevant, 40 `INCLUDE`,
64 excluded, and 23 future candidates.

The refresh deep-copies all 1,000 predecessor rows, overlays only OZJ Exact4,
and leaves the other 996 dictionaries equal to the predecessor. It creates no
new human, chemistry, pair, role, reusable, split, tensor, training-admission,
or training authority. Human-review status cites the OZJ formal decision;
chemistry, task, pair, role, positive provenance, and future candidacy are
projected from the published OZJ event matrix.

## OZJ projection and unchanged boundaries

OZJ ranks 670-673 cover four PDB 4CL8 Cys168 events. Every event retains its
observed SG-CAF structural evidence. The published semantics are task-relevant
positive chemistry, Candidate1 with `STRICT_LINKER_PRESENT_V1`, W
`[CAF,OAD]`, L `[CAG,CAH,CAI,CAJ,CAP,CAQ]`, S
`[C2,C4,C5,C6,CAE,CAR,CAS,N1,N3,NAA,NAB,NAC,NAM]`, and human training use
`INCLUDE`.

The overlay changes exactly 18 fields per OZJ event.
`human_training_excluded` remains false and is not a changed field. The
ingestion-derived future-candidate flag becomes true, while formal split,
formal admission, materialization, and runtime usability remain false.
Future candidacy is not admission: the global counts are 23 future candidates,
5 formally admitted events, and 17 runtime-usable events.

Structural totals remain raw/exact/explicit/CCD-compatible 997/867/867/865.
Geometry remains POST source/sample/training 867/21/17 and PRE
source/sample/training 0/0/0. No POST-to-PRE promotion, PRE zero-fill, or new
geometry training authority is created.

## Canonical Exact5 and global counts

The global V1 mask contract remains exactly five tasks:

| ID | Semantic long name | Alias | Applicable count |
|---:|---|---|---:|
| 0 | `warhead_only` | A | 104 |
| 1 | `linker_plus_warhead` | B | 48 |
| 2 | `scaffold_plus_warhead` | B2 | 48 |
| 3 | `scaffold_only` | B3 | 104 |
| 4 | `scaffold_plus_linker_plus_warhead` | C | 104 |

No sixth task is introduced. The 48 strict rows support all five tasks; the 56
direct rows support A/B3/C. Pair and role sample authority both become 104,
while model-bound pair targets remain 41 and runtime targets remain 17.

Chemistry becomes 104 positive, 86 not established, and 810 unresolved. Task
relevance becomes 105 relevant, 86 not relevant, and 809 unresolved. Training
use becomes 40 `INCLUDE`, 64 `EXCLUDE_FROM_TRAINING_ONLY`, 86 not
applicable, and 810 unresolved.

## Human review, blockers, and next review unit

Within the frozen priority-review population of 338 events / 131 units, the
published OZJ reconciliation reports 87 positive events / 11 units, 24
negative events / 4 units, 111 completed events / 15 units, and 227 pending
events / 116 units. The global `COMPLETED_HUMAN_NEGATIVE=54` count remains a
separate census measure.

Within the 104 positive events, human training exclusion is 64, missing split
authority is 63, missing tensor integration is 63, missing POST training
authority is 87, missing training admission is 99, and feature semantics are
pending for all 104. The corresponding within-`INCLUDE` counts are
15, 11, 23, and 35. Pair and role authority are absent for 896 of all 1,000
events but none of the positive events. These blocker sets are non-exclusive.

The frozen 131-unit queue is filtered through published OZJ reconciliation;
no queue artifact is created or reordered. OZJ disappears from the pending
set. The next unit is `COVAPIE_BULK_REVIEW_UNIT_2557BFE1E3B5C4C5`: ligand
F24, four events, PDB 3V4X. This refresh does not start F24 review or create an
F24 package.

## Publication, training readiness, and reproducibility

Until this Exact7 is externally reviewed, committed, and pushed, the published
current global census remains CHT: 100 positive, 101 relevant, 36 `INCLUDE`,
64 excluded, 19 future candidates, and OZJ `CURRENTLY_UNREVIEWED`. The
uncommitted candidate is 104 positive, 105 relevant, 40 `INCLUDE`, 64
excluded, and 23 future candidates, with OZJ
`COMPLETED_HUMAN_POSITIVE` and F24 as the pending head.

`READY_FOR_FORMAL_TRAINING` remains false. Feature semantics remain
`AUDIT_REQUIRED_LATER`; Step12D was only a smoke legality check, not a final
training-feature contract. The OZJ 3-formylphenyl/TbPTR1 context and CAF-OAD
source evidence must not be promoted to PRE topology, complete POST topology,
warhead/reaction-family authority, or training features without the separate
feature-semantics audit.

The CSV, summary, and manifest are deterministic source-derived projections.
The manifest binds the candidate files, exact predecessor and OZJ inputs, and
CSV/summary outputs, but never records its own SHA256. Projection digests are
drift-detection contracts, not science or human authority.
