# CovaPIE cumulative1000 current global readiness census with 2VS V1

## Purpose and authority boundary

This is an additive, derived current-state refresh. The frozen predecessor is
the published PRF-refreshed cumulative1000 census, which contains 66
authoritative chemistry-positive events. The already-published 2VS formal human
decision, completed-decision ingestion, and completed-decision reconciliation
provide an exact source-derived delta of eight events. This successor therefore
reports 74 authoritative positives.

The census does not create or reinterpret human, chemistry, reactive-pair,
role, reusable, split, tensor, training-admission, or training authority. It
deep-copies the predecessor computation and overlays only the eight 2VS rows at
ranks 848, 849, 850, 851, 859, 860, 861, and 862. The other 992 row dictionaries
remain equal to the predecessor. Structural, raw-evidence, and geometry-source
fields remain unchanged for all eight overlaid events.

## 2VS projection

The 2VS Exact8 becomes `COMPLETED_HUMAN_POSITIVE`, chemistry `POSITIVE`, task
relevance `RELEVANT`, and training use `EXCLUDE_FROM_TRAINING_ONLY`. The
published ingestion matrix supplies sample chemistry, task, reactive-pair, and
role projections. The formal decision supplies human-review authority. The
reconciliation module supplies current review state; it is not used as a
pair/role chemistry authority source.

2VS contributes eight sample-authoritative pairs, eight sample-authoritative
roles, and eight `DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1` profiles. It contributes
no model-bound pair target, tensor integration, POST training authority, PRE
authority, split, admission, future admission candidate, or runtime-usable
sample. As a result:

- sample-authoritative pair count: 74
- published model-bound pair target count: 41
- sample-authoritative role count: 74
- strict-linker role count: 31
- direct-attachment role count: 43
- training `INCLUDE`: 29
- training `EXCLUDE_FROM_TRAINING_ONLY`: 45
- missing tensor integration within positive events: 33
  (`G3H` 8 + `ONL` 9 + `PRF` 8 + `2VS` 8)

Training exclusion is not chemistry negativity. Chemistry remains 74 positive,
0 negative, 86 not established, and 840 unresolved. Task relevance is 75
relevant, 86 not relevant, and 839 unresolved.

## Canonical tasks and geometry

The global V1 contract remains exactly five tasks:

| ID | Semantic long name | Alias | Applicable count |
|---:|---|---|---:|
| 0 | `warhead_only` | A | 74 |
| 1 | `linker_plus_warhead` | B | 31 |
| 2 | `scaffold_plus_warhead` | B2 | 31 |
| 3 | `scaffold_only` | B3 | 74 |
| 4 | `scaffold_plus_linker_plus_warhead` | C | 74 |

No sixth task is introduced. The 31 strict-linker rows support all five tasks;
the 43 direct-attachment rows support A/B3/C (`[0,3,4]`).

## Geometry and human-review queue

Geometry is unchanged: POST source/sample/training counts are 867/21/17 and PRE
source/sample/training counts are 0/0/0. No POST-to-PRE promotion, PRE zero-fill,
or precursor reconstruction is performed.

The full frozen priority population contains 338 events in 131 units. Published
reconciliation now gives 57 positive events in 6 units, 24 negative events in 4
units, 81 completed events in 10 units, and 257 pending events in 121 units.

The pending Top10 is recomputed from the full 131-unit queue using event count
descending, raw priority rank ascending, and review-unit ID as the stable
tie-break. It is not produced by manually deleting 2VS from an old Top10. The
new first unit is
`COVAPIE_BULK_REVIEW_UNIT_9723B0F9EC07CC81`: ligand 1F8, eight events, PDB 3ORX,
status `CURRENTLY_UNREVIEWED`.

`CURRENT_GLOBAL_RECONCILIATION_COMPLETE` and
`CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE` are true. The next recommended
mainline is `HIGH_YIELD_HUMAN_REVIEW_EXPANSION`, but this step does not perform
the 1F8 review.

## Training readiness

There are 12 future admission candidates, 17 current runtime-usable events, 5
formally admitted events, and 0 events ready for formal training. Global
materialization remains
`NOT_COMPUTABLE_FROM_CURRENT_PUBLISHED_AUTHORITY` and
`READY_FOR_FORMAL_TRAINING` remains false.

Feature semantics remain `FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER`. Step12D was
only `SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT`; this refresh is
not the required feature-semantics audit.

## Reproducibility

The CSV, summary, and manifest are deterministic source-derived projections.
The manifest binds the four candidate contract files, the frozen predecessor
and 2VS semantic inputs, and the CSV/summary outputs; it never records its own
SHA256. Private census, summary, and semantic-binding digests are projection
contract digests only and do not create authority.
