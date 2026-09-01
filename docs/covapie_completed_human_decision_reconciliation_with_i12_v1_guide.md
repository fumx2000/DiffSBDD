# I12 completed-decision reconciliation V1

## Purpose

This candidate connects the published rich I12 ingestion authority to the
unchanged generic completed-decision reconciler. It creates one narrow Exact4
source, appends it to the published Exact13 source chain, and returns an
in-memory reconciliation result. It creates no reconciliation data artifact.

## Rich-to-narrow boundary

The production owner calls the published I12 ingestion owner's
`load_frozen_formal_decision_v1` API. Before projection it checks the finalized
D1–D5 decisions, Exact4 event and rank identity, Candidate 0 direct-attachment
role profile, task applicability `[0, 3, 4]`, PRE/POST limitations, chemical
and reusable-authority limitations, future-candidate distinction, and the
absence of training admission.

Only the unchanged 11-field `NormalizedCompletedDecisionFact` is projected:
event and review-unit identity, completed-positive status, relevant/positive/
include dispositions, `human_training_excluded=false`, and source provenance.
Rich chemical, atom-role, boundary, geometry, seed, future-candidate, and
training-admission fields are not projected.

The ingestion binding retains its `project_parent_relative` namespace. The
generic `SourceBinding` uses the predecessor vocabulary
`repository_parent_relative`. I12 source acceptance is inherited from the
published ingestion owner's V2 content and executable-class verification; the
reconciliation owner does not reopen the formal JSON or introduce another
filesystem binding.

## Source and historical transition

The published predecessor has 13 sources and 95 collision-free facts. I12 is
appended at the end as the four-event fourteenth source, producing 99 unique
facts and 14 distinct review-unit and stable source identities.

The historical I12 unit consists exactly of the four expected events at raw
priority rank 17. Each is currently unreviewed, calibration eligible, and has
no exclusion reason. The published ONL normalization remains the sole
transition adapter and changes zero I12 rows. No I12-specific adapter exists.

## Expected in-memory result

The 338-event, 131-unit universe reconciles to 99 positive events in 14 units,
24 negative events in 4 units, 123 completed events in 18 units, no in-progress
events, and 215 unreviewed events in 113 units. Each I12 event transitions from
`CURRENTLY_UNREVIEWED` to `COMPLETED_HUMAN_POSITIVE` with relevant, positive,
include semantics.

This step does not refresh the global census or priority queue, materialize a
reconciliation CSV, tensorize data, or start training. `READY_FOR_TRAINING`
remains false; a later feature-semantics audit is still required. The new
reconciliation Python files are intended to be clean from birth under the B4
future source-binding guard.
