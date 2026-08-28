# CovaPIE cumulative1000 current global readiness census with YUN V1

## Purpose and authority boundary

This additive derived refresh consumes the published 1F8 census, YUN formal
human decision, YUN ingestion, and YUN reconciliation. The predecessor reports
82 chemistry-positive events, 29 training `INCLUDE` events, and 12 future
admission candidates. Published YUN contributes a source-derived Exact7 delta
of +7 positive, +7 `INCLUDE`, and +7 future candidates, producing totals of
89, 36, and 19 respectively.

The refresh deep-copies all 1,000 predecessor rows, overlays only YUN Exact7,
and leaves the other 993 dictionaries equal to the predecessor. It creates no
human, chemistry, pair, role, reusable, split, tensor, training-admission, or
training authority. Human-review status cites the YUN formal decision;
chemistry, task, pair, role, and positive provenance cite the published YUN
ingestion matrix.

## YUN projection and unchanged boundaries

YUN Exact7 becomes `COMPLETED_HUMAN_POSITIVE`, chemistry `POSITIVE`, task
relevance `RELEVANT`, and training use `INCLUDE`. It contributes seven
sample-authoritative pairs, seven sample-authoritative roles, and seven
`DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1` profiles. Future candidacy remains
`CANDIDATE_REQUIRES_INDEPENDENT_FUTURE_ADMISSION` in its published source; the
census represents that fact through its existing boolean column and does not
add a new column.

YUN adds no model-bound pair target, tensor integration, POST training
authority, PRE authority, split authority, formal admission, training
materialization, or runtime usability. The refreshed pair count is 89 while
the model-bound pair count remains 41. Role counts are 39 strict and 50 direct.
Geometry is unchanged at POST source/sample/training 867/21/17 and PRE
source/sample/training 0/0/0.

The global V1 mask contract remains exactly five tasks:

| ID | Semantic long name | Alias | Applicable count |
|---:|---|---|---:|
| 0 | `warhead_only` | A | 89 |
| 1 | `linker_plus_warhead` | B | 39 |
| 2 | `scaffold_plus_warhead` | B2 | 39 |
| 3 | `scaffold_only` | B3 | 89 |
| 4 | `scaffold_plus_linker_plus_warhead` | C | 89 |

No sixth task is introduced. The 39 strict rows support all five tasks; the 50
direct rows support A/B3/C (`[0,3,4]`).

## Blockers and next review unit

Missing tensor integration rises from 41 to 48 positive events: G3H 8, ONL 9,
PRF 8, 2VS 8, 1F8 8, and YUN 7. Seven of those 48 are training `INCLUDE`
events, so `all_missing_are_training_excluded_population` is now false.
Missing split authority is 48 positive / 11 `INCLUDE`; missing POST training
authority is 72 / 19; and missing training admission is 84 / 31.

The full frozen 131-unit queue is dynamically reranked after published YUN
reconciliation. There are 242 pending events in 119 units. The new first unit
is `COVAPIE_BULK_REVIEW_UNIT_0E0F340A9F98DA62`: ligand NEQ, six events, PDBs
3V61 and 3V62. This refresh does not perform NEQ human review.

## Training readiness and reproducibility

The refreshed census has 19 future admission candidates, 17 runtime-usable
events, 5 formally admitted events, and 0 events ready for formal training.
Global materialization remains
`NOT_COMPUTABLE_FROM_CURRENT_PUBLISHED_AUTHORITY`, and
`READY_FOR_FORMAL_TRAINING` remains false.

Feature semantics remain `FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER`. Step12D was
only `SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT`. A later audit
must resolve the historical unknown atom-feature policy and the YUN observed
POST CAO-CAN single-bond context versus generator PRE electrophile semantics.

The CSV, summary, and manifest are deterministic source-derived projections.
The manifest binds the four candidate contract files, the exact predecessor
and YUN semantic inputs, and the CSV/summary outputs. It never records its own
SHA256. Private projection digests are drift-detection contracts, not
authority.
