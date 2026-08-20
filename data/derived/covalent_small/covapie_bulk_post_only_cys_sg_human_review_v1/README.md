# CovaPIE post-only CYS-SG human-review workspace V1

This is an additive human-review execution workspace for the 36 SHA-bound
review units and 123 events in the frozen post-only triage packet. It is not a
production chemistry authority, an authorized-population update, or a training
sample materializer.

## Frozen machine evidence and mutable decisions

The machine evidence remains byte-identical under `data/derived/covalent_small/covapie_bulk_post_only_cys_sg_training_candidate_triage_v1`.
The decision overlay stores only `review_unit_id` / `canonical_event_id`
references plus human-entered fields and an append-only hash-chained history.
Do not edit the frozen packet. Use the record-decision CLI for all overlay
changes so prior values remain auditable.

Initial state: all 36 units are `UNREVIEWED`; every chemistry, relevance,
reviewer, geometry, and event-use decision is blank.

## Review ordering only

Priority is derived only from the frozen unit-level machine-status
distribution. It is not a scientific outcome or approval recommendation.

- P0: 18 units / 39 events
- P1: 4 units / 10 events
- P2: 10 units / 37 events
- P3: 4 units / 37 events

Every priority retains all of its units. P0 is not approved; P3 is not
rejected.

## Commands

```bash
python scripts/build_covapie_bulk_post_only_cys_sg_human_review_v1.py
python scripts/show_covapie_bulk_post_only_cys_sg_review_unit_v1.py --next
python scripts/show_covapie_bulk_post_only_cys_sg_review_unit_v1.py --unit-id UNIT_ID
python scripts/record_covapie_bulk_post_only_cys_sg_review_decision_v1.py --help
python scripts/check_covapie_bulk_post_only_cys_sg_human_review_v1.py
```

The build command initializes the workspace only when it is absent, or
idempotently verifies an exact initial empty workspace. **DO NOT use the build
command to reset human decisions.** It has no force-reset mode and refuses to
reinitialize any workspace containing human decisions or history. Missing,
partial, drifted, or internally inconsistent workspaces also fail closed and
must use a separate explicit administrative recovery workflow.

The record CLI supports separate `unit-relevance`, `unit-chemistry`, `event`,
and `unit-status` operations. It verifies every baseline and authority SHA
before writing, writes the overlay atomically, rebuilds progress from the
validated overlay, and never modifies a registry or frozen baseline artifact.
Changing a relevant unit that already has chemistry/event content to
not-relevant or deferred fails unless `unit-relevance --clear-downstream` is
explicitly supplied. That flag appends every actual downstream clear to the
history hash chain before recording the corrected relevance; it never deletes
the earlier decisions or history.

For a relevant completed unit, the exact CCD heavy atoms must be partitioned
into mutually exclusive scaffold/linker/warhead sets. The warhead set must
contain the frozen reactive atom. Event decisions remain independent even
inside a multi-event unit. Radius-2 topology absence does not force exclusion;
it remains unavailable for radius2-dependent auxiliary labels.

Current11 candidate-only family IDs are not accepted as existing approved
authority. A reviewer who cannot map safely to the SHA-bound approved family
must use `NEW_WARHEAD_FAMILY_REQUIRES_AUTHORITY_REVIEW` and provide a proposal label. The proposal is
not reusable production authority.
