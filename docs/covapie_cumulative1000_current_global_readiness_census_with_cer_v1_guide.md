# CovaPIE cumulative1000 readiness census with CER V1

This additive successor freezes the published with-1N0 census as its unique
predecessor. It consumes CER authority only through the published CER ingestion
and completed-decision reconciliation owners; the census owner does not read or
bind the formal human-decision file and does not execute its validator.

The refresh deep-copies all 1,000 predecessor rows and overlays only the frozen
CER Exact4 event IDs at ranks 52–55 in
`COVAPIE_BULK_REVIEW_UNIT_946339D19F961B4A`. Each target uses the published
positive/DIRECT semantics: `RELEVANT`, `POSITIVE`, SG–C2 sample pair authority,
`DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1`, structurally applicable task IDs
`[0,3,4]`, and `INCLUDE`. Exactly 4 rows change in the Exact18 overlay field
set; the other 996 rows remain field-for-field identical.

The global canonical contract remains exactly A, B, B2, B3, and C:
`warhead_only`, `linker_plus_warhead`, `scaffold_plus_warhead`,
`scaffold_only`, and `scaffold_plus_linker_plus_warhead`. B3 remains present
and no sixth task exists. CER's DIRECT sample applicability changes A, B3, and
C counts only; it does not change the global task set.

The frozen priority queue is read only to re-rank currently pending review
units from the refreshed reconciliation state. CER is no longer pending, and
current pending rank 1 is source-derived 4M5, raw priority rank 20,
`COVAPIE_BULK_REVIEW_UNIT_9E98765987D25C42`, with four events across 5AZT and
5AZV. No queue artifact is created or modified, and 4M5 review is not started.

The three materialized outputs are deterministic UTF-8/LF census, summary, and
manifest bytes. Source bindings use `covapie_source_binding_policy_v2`; the
manifest has no self SHA. The checker accepts the strict untracked Exact7 on
the frozen baseline and future tracked-clean descendants without requiring a
single commit or excluding later unrelated committed successors.

This step creates no new human or scientific authority, reusable chemistry,
pair, role, reaction-family, warhead-rule, split, tensor, admission, loader,
batch, model, loss, optimizer, parameter-update, or training artifact.
`QUEUE_REFRESH=false`, `TRAINING_STARTED=false`, and
`READY_FOR_TRAINING=false`. Feature semantics still require a later audit;
Step12D remains a smoke legality check, not a final training-feature contract.
