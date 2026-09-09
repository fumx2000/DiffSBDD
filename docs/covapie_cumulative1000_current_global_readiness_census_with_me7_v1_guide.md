# CovaPIE cumulative1000 current global readiness census with ME7 V1

This stage is a metadata-only successor to the published with-PYR census. It
consumes the published ME7 reconciliation and ME7 event-task availability
matrix, refreshes exactly three events, and creates no new review or training
authority. It does not modify the frozen priority queue and does not start EI3.

## Exact7 candidate

The candidate consists of one owner, one checker, one targeted test file, this
guide, and the three files in
`data/derived/covalent_small/covapie_cumulative1000_current_global_readiness_census_with_me7_v1/`.
The output directory must contain exactly the census CSV, summary JSON, and
manifest JSON. All seven files are ordinary UTF-8/LF regular non-executable
files smaller than 1 MiB.

## Source and overlay contract

The frozen with-PYR computation, CSV, summary, and manifest are reproduced and
cross-checked before overlay. Its 192 semantic source bindings remain an exact
prefix. Six bindings are appended: with-PYR owner/CSV/summary, ME7
reconciliation owner, ME7 ingestion owner, and ME7 matrix. The predecessor
manifest, reconciliation artifact, and frozen queue remain separate validation
bindings. Repository-relative sources must also equal their baseline Git blobs.

The only target is review unit
`COVAPIE_BULK_REVIEW_UNIT_3CF0AB1696EEA129`, ranks 528, 529, and 531, with the
three full event IDs declared by the ME7 ingestion owner. Unit, event, rank,
PDB, and matrix identity are all cross-checked. The other ME7 rows, including
ranks 527, 530, and 533, remain unchanged.

The 79-column ME7 matrix is adapted explicitly. Pair authority comes from
`pair_sample_authority`; role authority and profile come from
`role_partition_sample_authoritative` and `role_profile_derived_state`;
structural-label authority comes from
`canonical_mask_structural_labels_available`; training inclusion is derived by
comparing `training_disposition` with `INCLUDE`. JSON `null` for the raw role
profile and structurally applicable task IDs stays `null`; it is never replaced
with an empty or non-empty task list.

Exactly 19 fields are authorized for overlay. Seven remain unchanged and 12
actually change. The result keeps 47 columns, 1,000 ordered unique events, three
changed target rows, zero changed non-target rows, and 997 unchanged rows.

## Derived state

The refresh produces 160 globally unreviewed events, 81 completed-human-negative
events, 178 completed events in 32 units, 167 chemistry-positive events, 113
task-not-relevant events, and 113 training-not-applicable events. Pair authority
is 167 while role authority and canonical structural-label authority remain
156. Canonical task applicability remains `[156,56,56,156,156]`, including
`scaffold_only` / B3 and no sixth task.

The orthogonal task-negative/chemistry-positive population is the historical
20-event set union the ME7 Exact3, for 23 events. Blockers are non-exclusive and
must not be summed. Historical row-level formal admission remains five, while
this refresh admits no new event and leaves ready-for-formal-training at zero.

The frozen queue is fully re-filtered and sorted. The next pending unit is EI3,
`COVAPIE_BULK_REVIEW_UNIT_79526304E5FB38A6`, raw priority rank 33, current
pending rank 1, with three events and PDB IDs `["5ARB","5ARC","5ARD"]`.

## APIs and deterministic materialization

The owner exports the family-standard five-item API: error type, compute,
validate, build, and materialize. Compute/build are write-free. Materialize may
write only the exact output directory. CSV and JSON use canonical deterministic
serialization; the manifest binds owner/checker/tests/guide plus CSV/summary,
does not bind its own hash, and records no timestamps, hostnames, PIDs, absolute
machine paths, or live Git state.

Run the checker with the existing interpreter:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src" \
python -B scripts/check_covapie_cumulative1000_current_global_readiness_census_with_me7_v1.py
```

On success, stdout begins with one JSON report. Its lifecycle profile is at
`repository.profile`; the report location is the first JSON value on stdout and
no extra report file is created. The JSON is followed by the fixed marker
`COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_ME7_V1_PASS=true`,
then `lifecycle=...` and the fixed count/boundary markers. On failure the command
returns nonzero and prints the same pass marker with `false` plus `ERROR=...`.

The real worktree supports `CANDIDATE_UNTRACKED` and `TRACKED_CLEAN`. The first
requires baseline HEAD/origin, 0/0 ahead/behind, and exactly the seven ordinary
untracked paths. Tracked-clean verifies one stage-0 `100644` index record per
Exact7 path and supports committed-unpushed, published, and applicable clean
descendants while rejecting missing, mixed, extra-untracked, executable,
symlink, and nonzero-stage states.

## Stop boundary

No formal/candidate/scientific/preparation validator is executed here. No
review state, queue artifact, task-label rows, mask tensors, training admission,
parameter update, commit, or push is created. A feature-semantics audit remains
required before training; Step12D remains only a smoke-legality check, not a
final training-feature contract.
