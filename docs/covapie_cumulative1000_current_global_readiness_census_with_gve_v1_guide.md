# CovaPIE with-GVE current global readiness census V1

## Scope

This additive successor consumes the frozen with-SR2 1000-row census, the
published GVE completed-decision ingestion matrix, and the published with-GVE
generic reconciliation. It does not modify predecessor artifacts, refresh the
priority queue, prepare the LCY review, create training authority, or run
training.

The census schema remains exactly 47 columns and the canonical task contract
remains exactly five semantic masks:

1. `warhead_only` / `A`
2. `linker_plus_warhead` / `B`
3. `scaffold_plus_warhead` / `B2`
4. `scaffold_only` / `B3`
5. `scaffold_plus_linker_plus_warhead` / `C`

There is no sixth task.

## Exact additive delta

Only the four published GVE event identities at scale-up ranks 295, 296, 480,
and 986 are overlaid. Selection is by exact `canonical_event_id`, never by the
ligand component name. All 996 non-target rows, including the two historical
1XD3 GVE rows and the rank-322 SR2 row, remain field-for-field identical to the
with-SR2 predecessor.

The authorized overlay contains 15 fields. Three authoritative negative
decisions—`human_training_excluded`, `training_use_include`, and
`future_training_admission_candidate`—remain `false` and therefore do not
appear in the actual delta. Every target row changes the same remaining 12
fields.

## Orthogonal GVE semantics

The published human decision establishes, for GVE Exact4 only:

```text
task_relevance_disposition=NOT_RELEVANT
chemistry_disposition=POSITIVE
training_use_disposition=NOT_APPLICABLE
reactive_pair_sample_authoritative=true
```

`positive_authority_source` records positive chemistry/sample provenance. It
does not mean training inclusion, generative-supervision eligibility, future
training candidacy, or formal training admission. It therefore points to the
published GVE event matrix while all of those training states remain false.

GVE D4 remains unresolved. The successor does not create a role profile, role
authority, structural mask labels, or structurally applicable task IDs. It also
creates no pair training target, POST training authority, PRE authority,
formal split, formal admission, or runtime usability.

## Successor-local cross-field contract

The historical base validator is not applied to final with-GVE rows. This
successor independently enforces:

```text
EXCLUDE_FROM_TRAINING_ONLY => chemistry POSITIVE
chemistry NOT_ESTABLISHED => task NOT_RELEVANT
task NOT_RELEVANT => training NOT_APPLICABLE
```

Task-negative chemistry has exactly two allowed populations:

- the unchanged predecessor Exact90 uses
  `NOT_RELEVANT / NOT_ESTABLISHED / NOT_APPLICABLE`;
- GVE Exact4 uses `NOT_RELEVANT / POSITIVE / NOT_APPLICABLE` and must carry the
  exact published GVE matrix identity plus explicit human task and chemistry
  authority.

Every other task-negative chemistry population fails closed. In particular,
there is no general relaxation for arbitrary `NOT_RELEVANT` rows.

## Resulting census

The refreshed principal counts are:

```text
chemistry: POSITIVE=136, NEGATIVE=0, NOT_ESTABLISHED=90, UNRESOLVED=774
task: RELEVANT=133, NOT_RELEVANT=94, UNRESOLVED=773
training: INCLUDE=60, EXCLUDE_FROM_TRAINING_ONLY=72,
          NOT_APPLICABLE=94, UNRESOLVED=774
pair authority=136
role authority=132
mask authority=132
```

Exact5 applicability remains `132 / 52 / 52 / 132 / 132`. POST
source/sample/training remains `867 / 21 / 17`; PRE remains `0 / 0 / 0`.

The summary uses population-neutral blocker keys such as
`within_chemistry_positive` and `within_training_include`. Historical names
such as `within_positive_132` are prohibited in the with-GVE summary.

## Next pending review and training boundary

The frozen queue combined with the with-GVE reconciliation derives LCY as the
next pending unit: current pending rank 1, raw priority rank 24, review unit
`COVAPIE_BULK_REVIEW_UNIT_BA488AF51EDD8ED6`, PDB `4R0O`, four events.
This census does not start that review.

This successor is not training readiness. Step12D remains a smoke legality
check, not the final training-feature contract. A feature-semantics audit is
still required before formal training preparation or parameter updates.

## Verification

Run only the targeted suite and the matching checker:

```bash
PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}" \
PYTHONDONTWRITEBYTECODE=1 \
pytest -q -p no:cacheprovider \
tests/test_covapie_cumulative1000_current_global_readiness_census_with_gve_v1.py

PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}" \
PYTHONDONTWRITEBYTECODE=1 \
python scripts/check_covapie_cumulative1000_current_global_readiness_census_with_gve_v1.py
```
