# CovaPIE cumulative1000 readiness census with GD1 V1

This additive successor freezes the published with-4M5 census as its direct
predecessor. It consumes GD1 authority only through the published GD1 ingestion
and completed-decision reconciliation owners; the census owner does not read or
bind the formal human-decision file and does not execute its validator.

The refresh deep-copies all 1,000 predecessor rows and overlays only the frozen
GD1 Exact4 event IDs at ranks 691–694 in
`COVAPIE_BULK_REVIEW_UNIT_9FFA5A52A3113C6E`. Each target uses the published
positive/DIRECT semantics: `RELEVANT`, `POSITIVE`, SG–C77 sample pair authority,
`DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1`, and structurally applicable task IDs
`[0,3,4]`. The human decision is `EXCLUDE_FROM_TRAINING_ONLY`, so
`human_training_excluded=true`, `training_use_include=false`, and
`future_training_admission_candidate=false`. The authorized overlay is Exact19,
but the source-derived actual delta is Exact17 because the latter two false
values were already false. The other 996 rows remain field-for-field identical.

The published GD1 ingestion matrix records no supporting PRE source graph and no
PRE topology, geometry, or coordinate authority. Those rich provenance fields
are validation inputs, not additions to the unchanged 47-column census schema.
Global usable PRE source, sample, and training-target counts remain 0/0/0. POST
evidence was already present in the predecessor, so POST source/sample/training
counts remain 867/21/17 and no POST evidence is promoted to a target.

The global canonical contract remains exactly A, B, B2, B3, and C:
`warhead_only`, `linker_plus_warhead`, `scaffold_plus_warhead`,
`scaffold_only`, and `scaffold_plus_linker_plus_warhead`. B3 remains present
and no sixth task exists. GD1's DIRECT sample applicability raises A, B3, and C
to 128 while B and B2 remain 52; it does not change the global task set.

The frozen priority queue is consumed read-only and combined with the published
with-GD1 reconciliation statuses. Completed review units, including GD1, are
filtered out before pending units are sorted by event yield and raw priority.
The next pending unit is recorded from that dynamic result; no next ligand is
hard-coded into the owner. No queue artifact is created or modified and the next
review is not started.

The three materialized outputs are deterministic UTF-8/LF census, summary, and
manifest bytes. Semantic lineage preserves all predecessor bindings in order and
appends exactly six source bindings: with-4M5 owner/census/summary and GD1
reconciliation owner/ingestion owner/event matrix. The with-4M5 manifest is a
validation identity, not new scientific authority. Bindings use
`covapie_source_binding_policy_v2`; numeric POSIX mode is not semantic identity,
and the manifest does not record its own SHA256.

The checker supports the strict untracked Exact7 on baseline
`5d86db98a993ade9b787845c834f6cca6062f542` and future tracked-clean descendants.
Tracked-clean validation permits multiple commits, unrelated later committed
paths, and `origin/main` at any ancestor between the baseline and HEAD, while
requiring behind=0 and all Exact7 paths in `BASELINE..HEAD`.

This step creates no new human or scientific authority, reusable chemistry,
pair, role, reaction-family, warhead-rule, split, tensor, admission, loader,
batch, model, loss, optimizer, parameter-update, or training artifact.
`CENSUS_REFRESH=true`, `QUEUE_REFRESH=false`, `NEXT_REVIEW_STARTED=false`,
`TRAINING_STARTED=false`, and `READY_FOR_TRAINING=false`. Feature semantics still
require a later audit; Step12D remains a smoke legality check, not a final
training-feature contract.
