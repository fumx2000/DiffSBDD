# CovaPIE post-only CYS-SG training-candidate triage V1

This additive lane contains 123 review candidates in
36 chemistry-bounded review units. It does not grant
production chemistry authority and it does not materialize training samples.

## Boundary

A post-only V1 training candidate is an explicit, feature-compatible Cys-SG
event with recoverable observed post-complex ligand and pocket coordinates and
without a terminal leakage conflict or representation gap. Accurate
experimental pre-covalent geometry is not required for candidate review. PRE
status remains diagnostic and may support chemistry interpretation.

Existing production chemistry authority rules are unchanged. Source labels are
supporting triage evidence only; they are not exact chemistry signatures,
human approvals, warhead truth, or production admission. Review decisions must
be supplied by a human in the blank fields of `covapie_bulk_post_only_training_human_review_packet_v1.json`.

## Two-level human-review workflow

First, review `training_domain_relevance_decision` at unit level. If the human
decision is `NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK`, exclude the unit and
do not spend time assigning warhead or role labels. Only a human decision of
`RELEVANT_FOR_COVAPIE_POST_ONLY_V1` proceeds to unit-level warhead family,
warhead atom set, reactive-atom confirmation, and scaffold/linker/warhead role
decisions.

Second, review every `events_for_review` record independently. The blank
`post_geometry_training_usable`, `event_training_use_decision`, and
`event_exclusion_reason` fields are event/pose-level decisions; they must not be
propagated from another event in the same chemistry unit. The packet provides
the complete SHA-bound CCD atom/bond evidence and representative observed
heavy-atom coordinates needed for chemistry review. These are evidence, not
new authority.

## Population

- Canonical events: 2387
- Known existing events excluded from the new lane: 27
- New events: 2360
- Structurally eligible new events: 218
- Post-only review candidates: 123
- Existing-group leakage conflicts blocked: 88
- Representation gaps blocked: 7
- Outside structural eligibility: 2142

The 23 predecessor clusters are retained only for review ordering and batching.
The 36 review units retain component identity, reactive
atom, and CCD graph identity. Reactive-center topology is also uniform within
each unit when available; 4 units expose a
uniformly unavailable topology state and are retained only inside the stricter
exact component/reactive-atom/CCD-graph boundary. Clusters must never be used
as chemistry authority, decision-propagation, or training-label authority
units. There are 25 multi-event units containing
112 events; their geometry decisions remain
independent.
