# CovaPIE cumulative1000 current global readiness census with F24 V1

## Purpose and authority boundary

This additive derived refresh consumes the published OZJ census, published F24
reconciliation, source-derived F24 ingestion matrix, and frozen external F24
formal human decision. The predecessor reports 104 chemistry-positive events,
105 task-relevant events, 40 training `INCLUDE` events, 64
`EXCLUDE_FROM_TRAINING_ONLY` events, and 23 future-admission candidates.
Published F24 contributes an Exact4 delta of +4 positive, +4 relevant, +4
`INCLUDE`, and +4 ingestion-derived future candidates. The refreshed totals
are 108 positive, 109 relevant, 44 `INCLUDE`, 64 excluded, and 27 future
candidates.

The implementation deep-copies all 1,000 predecessor rows, overlays only the
four F24 events at ranks 593-596, and leaves the other 996 dictionaries equal
to the predecessor. The census is a projection of published lineage, not a
creator of human, chemistry, pair, role, split, tensor, geometry-training,
minimal-seed, training-admission, runtime, or parameter-update authority.

## F24 projection and rich upstream semantics

F24 covers four distinct PDB 3V4X contexts, all with Cys111 SG attached to
ligand atom C8. The frozen decisions are D1 `RELEVANT`, D2 `POSITIVE`, D3
`CONFIRM_OBSERVED_PAIR`, D4 `REVISE_ROLE_PARTITION`, and D5 `INCLUDE`.
The selected machine-candidate index remains empty. The human-revised role is
`DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1`: W is
`[C1,C2,C4,C8,O2,O5,O6]`, L is empty, and S is
`[C10,C11,C12,C13,C14,C16,C18,C20,C21,C3,C5,C6,C7,C9,O1,O4]`.

Ingestion separately proves the beta-lactone chemical core
`[C1,C2,C8,O2,O6]`. That chemical 5-set is intentionally distinct from the
canonical role-region 7-set. The global census keeps its predecessor schema;
it does not add chemical-core, D6, or beta-lactone columns. Current role and
task fields project the canonical role semantics, not the smaller chemical
core.

The overlay changes exactly 18 current-authority fields per event. Structural
identity and evidence remain byte-for-field identical. Pair and role sample
authority become true; model-bound pair target, POST training authority, PRE
authority, formal split, formal admission, materialization, and runtime use
remain false. D5 `INCLUDE` and future candidacy are not training admission.

## Canonical Exact5 and global counts

The global V1 mask contract remains exactly five tasks:

| ID | Semantic long name | Alias | Applicable authoritative-role rows |
|---:|---|---|---:|
| 0 | `warhead_only` | A | 108 |
| 1 | `linker_plus_warhead` | B | 48 |
| 2 | `scaffold_plus_warhead` | B2 | 48 |
| 3 | `scaffold_only` | B3 | 108 |
| 4 | `scaffold_plus_linker_plus_warhead` | C | 108 |

F24 contributes only A/B3/C, or task IDs `[0,3,4]`; it does not contribute to
B or B2. B3 is present and no sixth task exists. The authoritative role rows
are 48 strict and 60 direct, with zero other profiles. Sample-level pair and
role authority both total 108.

Chemistry becomes 108 positive, 86 not established, and 806 unresolved. Task
relevance becomes 109 relevant, 86 not relevant, and 805 unresolved. Training
use becomes 44 `INCLUDE`, 64 `EXCLUDE_FROM_TRAINING_ONLY`, 86 not applicable,
and 806 unresolved. The global status distribution includes 91
`COMPLETED_HUMAN_POSITIVE` and 223 `CURRENTLY_UNREVIEWED`; the 108 chemistry
positives are a distinct measure.

## Human review, blockers, and next pending unit

Within the frozen priority population of 338 events / 131 units, published F24
reconciliation reports 91 positive events / 12 units, 24 negative events / 4
units, 115 completed events / 16 units, and 223 pending events / 115 units.
There are no in-progress events or units.

Blocker denominators are recomputed for the refreshed populations and use
`within_positive_108` and `within_include_44`; stale predecessor keys are not
current. Missing split, tensor integration, POST training authority, training
admission, and feature-semantics audit remain blockers. These counts are
non-exclusive.

The frozen 131-unit raw queue is not rewritten. Filtering it through published
F24 reconciliation makes ligand 2A2, review unit
`COVAPIE_BULK_REVIEW_UNIT_6B422BBF7FAD44F6`, the current pending head with four
events. Its current pending rank is 1 while its immutable raw historical
priority rank remains 16. This refresh does not start 2A2 review or create a
2A2 package.

## Reproducibility and training boundary

The CSV, summary, and manifest are deterministic source-derived projections.
Two in-memory builds and two independent directory materializations must be
byte-identical to live outputs. The manifest binds candidate files, exact
predecessor and F24 inputs, and CSV/summary outputs, but never records its own
SHA256, timestamps, machine paths, PID, host, or live Git state.

`READY_FOR_TRAINING` and `READY_FOR_FORMAL_TRAINING` remain false. Feature
semantics remain `AUDIT_REQUIRED_LATER`; Step12D was only a smoke legality
validation and not a final training-feature contract. No training,
fine-tuning, backward pass, optimizer step, parameter update, candidate
evaluation, split, tensorization, loader/model/loss work, or training
materialization is authorized by this census refresh.
