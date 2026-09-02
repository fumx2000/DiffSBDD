# CovaPIE 4M5 completed-decision reconciliation V1

This metadata-only successor loads the published 4M5 Exact4 human decision
through the 4M5 ingestion owner and appends its narrow generic projection to
the published with-CER reconciliation chain. The unchanged generic owner
returns a deterministic in-memory result; no reconciliation CSV or JSON is
materialized.

Before projection, the successor validates the rich 4M5 authority: Exact4
identity and ranks 973–976, D1–D5, observed SG–C15 pair scope, Candidate 0
DIRECT role partition with W/L/S counts 9/0/16, Exact5 mask contract with B3,
no sixth task, and sample applicability `[0, 3, 4]`. It also proves one PRE
source graph per event, zero mappings, mapping-incompatible and unresolved PRE
status, no PRE topology or geometry authority, and the absence of reusable or
training authority. Rich pair, role, mask, atom, PRE/POST, warhead,
reaction-family, and admission fields stay outside the generic Exact11 fact.

Each 4M5 event projects to `COMPLETED_HUMAN_POSITIVE`, `RELEVANT`, `POSITIVE`,
and `INCLUDE`, with `human_training_excluded=false` and frozen formal-decision
provenance. `INCLUDE` is only the human training-use disposition: formal
training admission, materialization, tensor targets, and training remain false.

The with-CER predecessor contains 16 sources and 107 facts. 4M5 produces the
seventeenth source and 111 unique facts. Both reconciliations retain the same
338-row schema and order. Exactly four 4M5 rows change in the four standard
reconciliation fields; all 334 non-4M5 rows remain field-identical. The summary
changes from 103/15 to 107/16 positive events/units, keeps negative counts at
28/5, changes completed totals from 131/20 to 135/21, and changes unreviewed
counts from 207/111 to 203/110. In-progress counts remain 0/0.

This step creates no new human or scientific authority. It performs no census
refresh, priority-queue refresh, task-label materialization, tensorization,
model work, or training. `RECONCILIATION_COMPLETE_IN_MEMORY=true`, while
`READY_FOR_TRAINING=false` and the later feature-semantics audit requirement
remain explicit.
