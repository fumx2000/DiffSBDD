# CovaPIE cumulative1000 readiness census with SR2 V1

This additive successor freezes the published with-GD1 census as its direct
predecessor. It consumes SR2 authority only through the published SR2 ingestion
and completed-decision reconciliation owners; the census owner does not read or
bind the formal human-decision file and does not execute its validator.

The refresh deep-copies all 1,000 predecessor rows and overlays only the frozen
SR2 Exact4 event IDs at ranks 321, 323, 337, and 338 in
`COVAPIE_BULK_REVIEW_UNIT_A9BBD5309D7A5C08`. Each target uses the published
positive/DIRECT semantics: `RELEVANT`, `POSITIVE`, SG–C51 sample pair authority,
DIRECT candidate 15, W/L/S counts 9/0/18, the C9–N11 SING boundary, and
structurally applicable task IDs `[0,3,4]`.

The human decision is `INCLUDE`, so `training_use_include=true` and
`future_training_admission_candidate=true`, while
`human_training_excluded=false`. It remains a candidate requiring independent
future admission: formal admission, materialization, tensor targets, runtime
usability, and training all remain false. The authorized overlay is Exact19,
but the independently derived actual delta is Exact18 because
`human_training_excluded` was already false. The other 996 rows remain
field-for-field identical.

The published SR2 ingestion matrix records one supporting PRE source graph per
event and zero compatible mappings. `PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE` and
`PRE_REACTION_UNRESOLVED` create no census PRE geometry authority. Those rich
provenance fields remain upstream rather than expanding the unchanged 47-column
census schema. Global usable PRE source/sample/training counts remain 0/0/0;
POST source/sample/training counts remain 867/21/17. No POST-to-PRE copy, PRE
zero-fill, or POST target promotion is performed.

The global canonical contract remains exactly A, B, B2, B3, and C:
`warhead_only`, `linker_plus_warhead`, `scaffold_plus_warhead`,
`scaffold_only`, and `scaffold_plus_linker_plus_warhead`. B3 remains present
and no sixth task exists. SR2 raises A, B3, and C applicability to 132 while B
and B2 remain 52; it does not change the global task set.

The frozen priority queue is consumed read-only and combined with the published
with-SR2 reconciliation statuses. Completed units are removed before all
pending units are re-ranked by event yield and raw priority; current rank is not
computed by subtracting a constant. The source-derived next pending unit is raw
rank 23, `COVAPIE_BULK_REVIEW_UNIT_AAB4DCC7D3073222`, ligand GVE, with four
events across 2J7Q, 3KW5, and 5CRA. This census only records readiness for GVE
review preparation. It does not refresh the queue or start GVE review.

The materialized census, summary, and manifest are deterministic UTF-8/LF
outputs. Semantic lineage preserves all 138 predecessor bindings in order and
appends exactly six: the with-GD1 owner/census/summary and the SR2 reconciliation
owner/ingestion owner/event matrix. The with-GD1 manifest is validation identity
only. The resulting semantic-binding count is 144 with no duplicate identity,
and the manifest does not record its own SHA256.

The checker supports strict untracked Exact7 on baseline
`e58d4644c97ccab079e12991551e18d61cf874e9` and future tracked-clean descendants.
Tracked-clean validation permits multiple commits, unrelated later committed
paths, and `origin/main` at any ancestor between baseline and HEAD, while
requiring behind=0 and all Exact7 paths in `BASELINE..HEAD`.

Generic reconciled fact counts and global census counts are deliberately
different populations. Reconciliation has INCLUDE/EXCLUDE/NOT_APPLICABLE
43/72/4 among 119 facts; the 1,000-row census has
INCLUDE/EXCLUDE/NOT_APPLICABLE/UNRESOLVED 60/72/90/778.

This step creates no new human or scientific authority, reusable chemistry,
pair, role, reaction-family, warhead-rule, split, tensor, admission, loader,
batch, model, loss, optimizer, parameter-update, or training artifact.
`CENSUS_REFRESH=true`, `QUEUE_REFRESH=false`, `GVE_REVIEW_STARTED=false`,
`TRAINING_STARTED=false`, and `READY_FOR_TRAINING=false`. The historical
`UNKNOWN_ATOM_FEATURE_POLICY` / `feature_semantics_known=False` debt still
requires a formal feature-semantics audit. Step12D remains a smoke legality
check, not a final training-feature contract.
