# CovaPIE cumulative1000 current global readiness census with NEQ V1

## Purpose and authority boundary

This additive derived refresh consumes the published YUN census, NEQ formal
human decision, NEQ ingestion matrix, and NEQ reconciliation. The predecessor
reports 89 chemistry-positive events, 36 training `INCLUDE` events, 53
`EXCLUDE_FROM_TRAINING_ONLY` events, and 19 future admission candidates.
Published NEQ contributes a source-derived Exact6 delta of +6 positive and +6
`EXCLUDE_FROM_TRAINING_ONLY`, producing totals of 95 and 59. `INCLUDE` remains
36 and future candidacy remains 19.

The refresh deep-copies all 1,000 predecessor rows, overlays only NEQ Exact6,
and leaves the other 994 dictionaries equal to the predecessor. It creates no
human, chemistry, pair, role, reusable, split, tensor, training-admission, or
training authority. Human-review status cites the NEQ formal decision;
chemistry, task, pair, role, and positive provenance cite the published NEQ
event matrix.

## NEQ projection and unchanged boundaries

NEQ ranks 597-602 cover PDBs 3V61 and 3V62, with three Cys22 and three Cys81
events. Every event retains the observed SG-C3 pair, ligand element C, and
source CCD C2-C3 `DOUB` evidence. The formal semantics are D1 `RELEVANT`, D2
`POSITIVE`, D3 `CONFIRM_OBSERVED_PAIR`, D4 candidate 7 with
`DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1`, and D5
`EXCLUDE_FROM_TRAINING_ONLY`.

The overlay changes exactly 17 census presentation/provenance fields per NEQ
event. It does not alter structural identity or evidence fields. It creates no
model-bound pair target, complete authoritative POST-adduct topology, POST
training authority, PRE authority, split authority, future candidacy, formal
admission, training materialization, or runtime usability.

Structural totals remain raw/exact/explicit/CCD-compatible 997/867/867/865.
Geometry remains POST source/sample/training 867/21/17 and PRE
source/sample/training 0/0/0. No POST-to-PRE promotion or PRE zero-fill is
performed.

## Canonical Exact5 and global counts

The global V1 mask contract remains exactly five tasks:

| ID | Semantic long name | Alias | Applicable count |
|---:|---|---|---:|
| 0 | `warhead_only` | A | 95 |
| 1 | `linker_plus_warhead` | B | 39 |
| 2 | `scaffold_plus_warhead` | B2 | 39 |
| 3 | `scaffold_only` | B3 | 95 |
| 4 | `scaffold_plus_linker_plus_warhead` | C | 95 |

No sixth task is introduced. The 39 strict rows support all five tasks; the 56
direct rows support A/B3/C (`[0,3,4]`). Pair and role sample authority both
become 95, while model-bound pair targets remain 41 and runtime targets remain
17.

Chemistry becomes 95 positive, 86 not established, and 819 unresolved. Task
relevance becomes 96 relevant, 86 not relevant, and 818 unresolved. Training
use becomes 36 `INCLUDE`, 59 `EXCLUDE_FROM_TRAINING_ONLY`, 86 not applicable,
and 819 unresolved.

## Human review, blockers, and next review unit

Within the frozen priority-review population of 338 events / 131 units, the
published reconciliation reports 78 positive events / 9 units, 24 negative
events / 4 units, 102 completed events / 13 units, and 236 pending events / 118
units. The global presentation count `COMPLETED_HUMAN_NEGATIVE=54` is a
different census and must not be replaced by the priority-review count 24.

Within the 95 positive events, human training exclusion is 59, missing split
authority is 54, missing tensor integration is 54, missing POST training
authority is 78, missing training admission is 90, and feature semantics are
pending for all 95. The corresponding within-`INCLUDE` counts are 11, 7, 19,
and 31. These blocker sets are non-exclusive and must not be summed.

The frozen 131-unit queue is filtered through published NEQ reconciliation;
no queue artifact is created or reordered by hand. NEQ disappears from the
pending set. The new first unit is
`COVAPIE_BULK_REVIEW_UNIT_BCA0E7B8C2B33410`: ligand CHT, five events, PDBs
4V3F and 5A2D. This refresh does not begin CHT review.

## Publication, training readiness, and reproducibility

Until this Exact7 is externally reviewed, committed, and pushed, the published
current global census remains YUN: 89 positive, 36 `INCLUDE`, 53 `EXCLUDE`, 19
future candidates, and NEQ `CURRENTLY_UNREVIEWED`. The uncommitted candidate is
95 positive, 36 `INCLUDE`, 59 `EXCLUDE`, 19 future candidates, with NEQ
`COMPLETED_HUMAN_POSITIVE`.

The candidate retains 5 formally admitted events, 17 runtime-usable events,
and 0 events ready for formal training. `READY_FOR_FORMAL_TRAINING` remains
false. Feature semantics remain `AUDIT_REQUIRED_LATER`; Step12D was only a
smoke legality check, not a final training-feature contract. A separate
feature-semantics audit must resolve the historical unknown atom-feature policy
before any formal training or training-preparation work.

The CSV, summary, and manifest are deterministic source-derived projections.
The manifest binds the four candidate contract files, the exact predecessor
and NEQ semantic inputs, and the CSV/summary outputs. It never records its own
SHA256. Projection digests are drift-detection contracts, not science or human
authority.
