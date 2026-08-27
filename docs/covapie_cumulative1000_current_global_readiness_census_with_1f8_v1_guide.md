# CovaPIE cumulative1000 current global readiness census with 1F8 V1

## Purpose and authority boundary

This is an additive derived current-state refresh. Its frozen predecessor is
the published 2VS-refreshed cumulative1000 census with 74 authoritative
chemistry-positive events. The already-published 1F8 formal human decision,
completed-decision ingestion, and completed-decision reconciliation provide an
exact source-derived delta of eight events. This successor therefore reports
82 authoritative positives.

The census itself creates no human, chemistry, reactive-pair, role, reusable,
split, tensor, training-admission, or training authority. It deep-copies the
predecessor computation and overlays only the 1F8 Exact8 at ranks 499 through
506. The other 992 row dictionaries remain equal to the predecessor. The
Exact8 changes are limited to the frozen Exact17 overlay fields; structural,
raw-evidence, and geometry-source fields remain unchanged.

## 1F8 source-derived projection

The 1F8 Exact8 becomes `COMPLETED_HUMAN_POSITIVE`, chemistry `POSITIVE`, task
relevance `RELEVANT`, and training use `EXCLUDE_FROM_TRAINING_ONLY`. The formal
decision supplies human-review authority. The published ingestion matrix
supplies chemistry, task, sample reactive-pair, sample role, training-use, and
authority provenance. The published reconciliation supplies current review
state.

1F8 contributes eight sample-authoritative pairs, eight sample-authoritative
roles, and eight `STRICT_LINKER_PRESENT_V1` profiles with all five structural
task labels available. It contributes no model-bound pair target, tensor
integration, POST training authority, PRE authority, complete PRE disulfide
reagent authority, split, admission, future admission candidate, or
runtime-usable sample. The refreshed totals are:

- sample-authoritative pair: 82
- published model-bound pair target: 41
- sample-authoritative role: 82
- strict-linker role: 39
- direct-attachment role: 43
- training `INCLUDE`: 29
- training `EXCLUDE_FROM_TRAINING_ONLY`: 53
- missing tensor integration within positive events: 41
  (`G3H` 8 + `ONL` 9 + `PRF` 8 + `2VS` 8 + `1F8` 8)

Training exclusion is not chemistry negativity. Chemistry is 82 positive, 0
negative, 86 not established, and 832 unresolved. Task relevance is 83
relevant, 86 not relevant, and 831 unresolved.

## Canonical Exact5 and geometry

The global V1 mask contract remains exactly five tasks:

| ID | Semantic long name | Alias | Applicable count |
|---:|---|---|---:|
| 0 | `warhead_only` | A | 82 |
| 1 | `linker_plus_warhead` | B | 39 |
| 2 | `scaffold_plus_warhead` | B2 | 39 |
| 3 | `scaffold_only` | B3 | 82 |
| 4 | `scaffold_plus_linker_plus_warhead` | C | 82 |

No sixth task is introduced. The 39 strict-linker rows support all five tasks;
the 43 direct-attachment rows support A/B3/C (`[0,3,4]`).

Geometry is unchanged. POST source/sample/training counts are 867/21/17 and PRE
source/sample/training counts are 0/0/0. The disulfide-trapping and retained-
fragment context does not create PRE topology or geometry, and no POST-to-PRE
promotion, PRE zero-fill, or precursor reconstruction is performed.

## Human-review queue

The frozen priority population contains 338 events in 131 units. Published 1F8
reconciliation gives 65 completed-positive events in 7 units, 24 completed-
negative events in 4 units, 89 completed events in 11 units, and 249 pending
events in 120 units.

The pending Top10 is recomputed from the full 131-unit queue using event count
descending, raw priority rank ascending, and review-unit ID as the stable tie-
break. It is not formed by manually deleting 1F8 from an older Top10. The new
first unit is `COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D`: ligand YUN, seven
events, PDBs 4LL0 and 4LRM, status `CURRENTLY_UNREVIEWED`. This refresh does not
perform a YUN human review.

`CURRENT_GLOBAL_RECONCILIATION_COMPLETE` and
`CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE` are true. The next recommended
mainline is `HIGH_YIELD_HUMAN_REVIEW_EXPANSION`.

## Training readiness and reproducibility

There are 12 future admission candidates, 17 current runtime-usable events, 5
formally admitted events, and 0 events ready for formal training. Global
materialization remains `NOT_COMPUTABLE_FROM_CURRENT_PUBLISHED_AUTHORITY`, and
`READY_FOR_FORMAL_TRAINING` remains false.

Feature semantics remain `FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER`. Step12D was
only `SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT`; this refresh is
not the required feature-semantics audit.

The CSV, summary, and manifest are deterministic source-derived projections.
The manifest binds the four candidate contract files, the frozen predecessor
and 1F8 semantic inputs, and the CSV/summary outputs. It never records its own
SHA256. The private census, summary, and semantic-binding digests are derived
projection contract digests only and do not create authority.
