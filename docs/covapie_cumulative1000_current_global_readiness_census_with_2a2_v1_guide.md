# CovaPIE cumulative1000 current global readiness census with 2A2 V1

## Purpose and authority boundary

This additive successor consumes the frozen published F24 census plus the
published 2A2 ingestion and reconciliation owners. It deep-copies all 1,000
F24 rows and overlays only the four 2A2 events at ranks 507-510. The other 996
row dictionaries remain equal to the predecessor.

The refresh projects existing authority. It creates no new human, chemistry,
reactive-pair, role, reaction-family, warhead-rule, warhead-type, PRE,
POST-training, minimal-seed, split, tensor, admission, runtime, training, or
parameter-update authority. `READY_FOR_TRAINING` and
`READY_FOR_FORMAL_TRAINING` remain false.

## Frozen inputs and filesystem boundary

The projection binds the published F24 owner and Exact3, the published 2A2
reconciliation owner, the published 2A2 ingestion owner, and its event matrix.
The priority queue remains an inherited predecessor binding and is checked
directly when deriving the pending queue.

The census does not parse or bind the external 2A2 formal JSON directly. The
published ingestion owner is the rich semantic boundary and exposes the
already-validated formal provenance used in `human_review_authority_source`.
New Git-owned source identities use path, byte count, SHA256, regular-file,
and non-symlink checks. They do not use an exact POSIX mode as semantic
authority. Exact7 modes of 0644 or 0664 and non-executable status are only
candidate hygiene.

`FILESYSTEM_MODE_AUTHORITY_TECH_DEBT` remains
`PENDING_DEDICATED_V2_CLEANUP_AFTER_2A2_CENSUS_PUBLICATION`. Historical
validators are unchanged; general source-binding V2 is outside this step.

## Exact4 2A2 projection

The four distinct PDB 3ORZ contexts are Cys148 SG to ligand 2A2 SD, review unit
`COVAPIE_BULK_REVIEW_UNIT_6B422BBF7FAD44F6`. Published ingestion proves D1
`RELEVANT`, chemistry `POSITIVE`, the sample pair SG/SD, human-selected role
candidate 4, `STRICT_LINKER_PRESENT_V1`, and D5
`EXCLUDE_FROM_TRAINING_ONLY`.

The role partition is:

- W: `[SD]`
- L: `[C1,C15,C16,C17,O18]`
- S: `[C20,C21,C23,C24,C25,C26,C27,C28,C29,C30,CL99,N19,N22]`

All five canonical tasks are structurally applicable. The global contract
remains exactly A, B, B2, B3, and C; B3 is present and there is no sixth task.
The matrix also proves that chemical-warhead authority is absent, the complete
PRE reagent is unavailable, PRE topology/geometry authority is absent, POST
source evidence exists but POST training authority does not, and minimal-seed
authority is absent. These rich fields remain upstream and do not expand the
census schema.

Each refreshed 2A2 row changes exactly these 17 fields:

- `canonical_mask_structural_labels_available`
- `chemistry_authority_source`
- `chemistry_disposition`
- `current_global_status`
- `current_review_status`
- `human_review_authority_source`
- `human_review_completed`
- `human_training_excluded`
- `positive_authority_source`
- `reactive_pair_sample_authoritative`
- `role_partition_sample_authoritative`
- `role_profile`
- `structurally_applicable_task_ids_json`
- `task_relevance_authority_source`
- `task_relevance_disposition`
- `training_materialization_allowed_current_source`
- `training_use_disposition`

`training_use_include` and `future_training_admission_candidate` remain false.
Pair and role sample authority become true, while pair training target, POST
training target, PRE authority, split, admission, and runtime usability remain
false.

## Refreshed counts

The refreshed state has 112 chemistry positives, 113 relevant events, 44
`INCLUDE`, 68 `EXCLUDE_FROM_TRAINING_ONLY`, and 27 future candidates. Pair and
role sample authority both total 112. Role profiles total 52 strict and 60
direct. Applicable-role counts are A=112, B=52, B2=52, B3=112, and C=112.

Chemistry is 112 positive, 86 not established, and 802 unresolved. Relevance
is 113 relevant, 86 not relevant, and 801 unresolved. Training use is 44
include, 68 excluded-only, 86 not applicable, and 802 unresolved. A positive
excluded event is not a chemistry negative.

Global geometry source state is unchanged: 867 POST-source events, 21 POST
sample-authoritative events, 17 POST training targets, and zero PRE sample or
training targets. Formal training admission remains 5 and current runtime
usability remains 17.

Blockers are derived from refreshed rows. Chemistry unresolved falls from 806
to 802; human exclusion within positive rises from 64 to 68; feature semantics
pending within positive rises from 108 to 112; and missing split, tensor,
POST-training, and admission blockers rise by four where their predicates
apply.

## Review state and next current pending unit

Within 338 priority-review events / 131 units, reconciliation contains 95
positive events / 13 units, 24 negative events / 4 units, and 119 completed
events / 17 units. Pending and unreviewed state is 219 events / 114 units;
in-progress state is zero.

Filtering the frozen priority queue through that reconciliation makes I12,
review unit `COVAPIE_BULK_REVIEW_UNIT_7D83F048AF8A2295`, the current pending
rank 1. Its immutable raw priority rank is 17, it covers four events, and its
PDBs are 1WOF and 2AMP. `I12_REVIEW_STARTED=false`; this refresh creates no I12
review material.

After publication, the recommended mainline is
`SOURCE_BINDING_FILESYSTEM_MODE_AUTHORITY_TECH_DEBT_V2`, but that cleanup is
not started here.

## Determinism and lifecycle

CSV, summary, and manifest are built in memory, validated, and materialized
deterministically. Consecutive memory builds and two temporary-directory
materializations must be byte-identical to live Exact3. The manifest records
no timestamps, host, PID, absolute paths, live Git state, or self SHA256.

The checker independently verifies frozen inputs, Exact4 prior and matrix
semantics, exact row/field delta, distributions, Exact5, geometry, review
counts, blockers, I12 queue head, digests, determinism, and authority boundary.
Its only successful lifecycle profiles are `CANDIDATE_UNTRACKED` and
`TRACKED_CLEAN`.

Feature semantics remain `AUDIT_REQUIRED_LATER`. Step12D was a smoke legality
check, not a final training-feature contract.
