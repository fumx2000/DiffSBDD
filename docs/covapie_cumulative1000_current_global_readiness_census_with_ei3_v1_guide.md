# CovaPIE cumulative1000 current global readiness census with EI3 V1

This stage is a metadata-only successor to the published with-ME7 census. It
consumes the published EI3 reconciliation and EI3 event-task availability
matrix, refreshes exactly three events, and creates no new review or training
authority. It does not modify the frozen priority queue or start the next review.

## Exact7 candidate

The candidate consists of one owner, one checker, one targeted test file, this
guide, and the three files in
`data/derived/covalent_small/covapie_cumulative1000_current_global_readiness_census_with_ei3_v1/`.
The output directory must contain exactly the census CSV, summary JSON, and
manifest JSON. All seven files are ordinary UTF-8/LF regular non-executable
files smaller than 1 MiB.

## Source and overlay contract

The frozen with-ME7 computation, CSV, summary, and manifest are reproduced and
cross-checked before overlay. Its 198 semantic source bindings remain an exact
prefix. Six bindings are appended: with-ME7 owner/CSV/summary, EI3
reconciliation owner, EI3 ingestion owner, and EI3 matrix. The predecessor
manifest, reconciliation artifact, and frozen queue remain separate validation
bindings. The successor therefore has 204 semantic bindings. Repository-relative
sources must also equal their baseline Git blobs.

The only target is review unit
`COVAPIE_BULK_REVIEW_UNIT_79526304E5FB38A6`, ranks 967, 968, and 969, with the
three full event IDs declared by the EI3 ingestion owner. Unit, event, rank,
PDB, and matrix identity are all cross-checked. Every other census row remains
unchanged.

The 81-column EI3 matrix is adapted explicitly. Pair authority comes from
`pair_sample_authority`; role authority and profile come from
`role_partition_sample_authoritative` and `role_profile_derived_state`;
structural-label authority comes from
`canonical_mask_structural_labels_available`; training inclusion is derived by
comparing `training_disposition` with `INCLUDE`. JSON `null` for the raw role
profile, role/seed fields, and structurally applicable task IDs stays literal
JSON `null`; it is never replaced with an empty or non-empty array. Target
covalent connection counts remain `[1,1,1]`; metal-context counts `[0,0,2]`
remain context and never become additional covalent events.

Exactly 19 fields are authorized for overlay. Seven remain unchanged and 12
actually change. The result keeps 47 columns, 1,000 ordered unique events, three
changed target rows, zero changed non-target rows, and 997 unchanged rows.

## Derived state

The refresh produces 157 globally unreviewed events, 84 completed-human-negative
events, 181 completed events in 33 units, 170 chemistry-positive events, 116
task-not-relevant events, and 116 training-not-applicable events. Pair authority
is 170 while role authority and canonical structural-label authority remain
156. Canonical task applicability remains `[156,56,56,156,156]`, including
`scaffold_only` / B3 and no sixth task.

The orthogonal task-negative/chemistry-positive population is the predecessor
23-event set union the EI3 Exact3, for 26 events. Blockers are non-exclusive and
must not be summed. Historical row-level formal admission remains five, while
this refresh admits no new event and leaves ready-for-formal-training at zero.

The frozen queue is read-only, then re-filtered and sorted in memory. The next
pending unit is AZP, `COVAPIE_BULK_REVIEW_UNIT_7FB64BA2D198B24F`, raw priority
rank 34, current pending rank 1, with three events and PDB IDs `["2A5I","2A5K"]`.
This metadata does not authorize starting AZP.

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
python -B scripts/check_covapie_cumulative1000_current_global_readiness_census_with_ei3_v1.py
```

On success, stdout begins with one JSON report. Its lifecycle profile is at
`repository.profile`; the report location is the first JSON value on stdout and
no extra report file is created. The JSON is followed by the fixed marker
`COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_EI3_V1_PASS=true`,
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
final training-feature contract. After external review and publication of this
census, sequential review expansion pauses and the project turns to label/model
input gaps for already-INCLUDE candidates; that next line is not started here.
