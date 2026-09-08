# CovaPIE cumulative1000 current readiness census with PYR V1

This metadata-only successor validates the published with-6OA census and then
projects the published PYR Exact4 reconciliation and ingestion matrix into the
same ordered 1000-row, 47-column census. It does not reinterpret the approved
PYR decision and creates no new authority.

## Projection contract

- PYR is the exact published review unit
  `COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4`, ranks 46–49.
- All four events become human-completed chemistry-positive, task-relevant
  samples whose training disposition is `EXCLUDE_FROM_TRAINING_ONLY`.
- The authorized overlay contains 19 fields. Two remain byte-equivalent to the
  predecessor (`training_use_include` and
  `future_training_admission_candidate`), so 17 fields change per PYR row.
- Exactly four rows change, no non-PYR row changes, and 996 rows remain equal to
  the predecessor.
- The canonical V1 task set remains exactly five tasks: `warhead_only`,
  `linker_plus_warhead`, `scaffold_plus_warhead`, `scaffold_only`, and
  `scaffold_plus_linker_plus_warhead`. B3 is `scaffold_only`; no sixth task
  exists.

Human-review positivity and training exclusion are deliberately independent.
PYR adds four positive/relevant events and four human training exclusions, but
adds no training include, future-admission candidate, task label, tensor target,
formal training admission, or parameter-update authority.

## Pending display

The frozen priority queue is not changed. Pending units are re-filtered against
the published reconciliation and sorted by the existing event-yield rule. PYR
and the completed-negative AS2 unit are excluded. The first current pending unit
is ME7 (`COVAPIE_BULK_REVIEW_UNIT_3CF0AB1696EEA129`), raw priority rank 32,
with three exact events across both `3QVY` and `3QVZ`. The summary and manifest
use `next_priority_review_pdb_ids=["3QVY","3QVZ"]`; the obsolete scalar
`next_priority_review_pdb` is forbidden.

## Outputs and verification

The producer writes only the three files under
`data/derived/covalent_small/covapie_cumulative1000_current_global_readiness_census_with_pyr_v1/`.
Together with the owner, checker, tests, and this guide, they form Exact7.

Run the independent checker with bytecode disabled:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src" \
python scripts/check_covapie_cumulative1000_current_global_readiness_census_with_pyr_v1.py
```

The checker accepts either an exact untracked candidate on the frozen baseline
or a clean tracked publication/descendant with Git index stage 0 and mode
100644. It independently checks source identities, 4/0/996 and 19/2/17 deltas,
row-derived counts and event-set digests, ME7's complete multi-PDB identity, 192
semantic bindings, dynamic manifest bindings, deterministic bytes, strict
semantic tamper rejection, Git lifecycle, and forbidden-file hygiene.

## Training boundary

This refresh performs no queue refresh, next review, label or tensor
materialization, model forward, loss, backward pass, optimizer step, fine-tune,
training, commit, or push. Step12D remains a smoke legality check, not a final
training-feature contract. A feature-semantics audit remains required before any
training preparation or training; completing that audit would not cancel PYR's
approved training exclusion.
