# CovaPIE with-LCY current global readiness census V1

## Scope

This deterministic additive successor consumes the published with-GVE
1000-row census, the published LCY completed-decision ingestion matrix, and the
published with-LCY generic reconciliation. It creates no human or scientific
authority. It does not modify predecessor artifacts, refresh the priority
queue, prepare the 0D8 review, admit training data, or run training.

The schema remains exactly 47 columns. The canonical task contract remains
exactly five semantic masks:

1. `warhead_only` / `A`
2. `linker_plus_warhead` / `B`
3. `scaffold_plus_warhead` / `B2`
4. `scaffold_only` / `B3`
5. `scaffold_plus_linker_plus_warhead` / `C`

There is no sixth task.

## Exact additive delta

Only the four published LCY event identities at scale-up ranks 898 through 901
are overlaid. Selection is by exact `canonical_event_id`, never by
`ligand_component_id`. Every one of the 996 non-target rows remains identical
across all 47 fields. This explicitly includes the published GVE Exact4 rows
and the separate same-component control
`COVAPIE_CYS_SG_EVENT_V1:3A2G:A:CYS:102-:SG:G:LCY:C1`.

The authorized overlay contains 15 fields. Three fields remain false and are
authorized but unchanged: `human_training_excluded`, `training_use_include`,
and `future_training_admission_candidate`. Every LCY target row changes the
same remaining 12 fields; no role, mask, PRE/POST-training, split, admission,
or runtime field changes.

## LCY authority projection

The already-published authority establishes, for LCY Exact4 only:

```text
current status=COMPLETED_HUMAN_NEGATIVE
task relevance=NOT_RELEVANT
chemistry=POSITIVE
training use=NOT_APPLICABLE
sample reactive-pair authority=true
protein/ligand pair=SG/C1
```

Role partition authority and task applicability remain unknown. The ingestion
matrix retains all five canonical task rows, including `scaffold_only / B3`,
with null applicability values and no mask targets.

## Successor-local cross-field contract

The historical base validator is not applied to final rows because its global
`NOT_RELEVANT => chemistry NOT_ESTABLISHED` assumption predates the published
GVE and LCY orthogonal decisions. This successor permits exactly:

- the unchanged legacy Exact90 population:
  `NOT_RELEVANT / NOT_ESTABLISHED / NOT_APPLICABLE`;
- the published GVE Exact4 population:
  `NOT_RELEVANT / POSITIVE / NOT_APPLICABLE`;
- the new LCY Exact4 population with the same tuple.

Thus the chemistry-positive task-negative population is exactly the union of
GVE Exact4 and LCY Exact4, count 8. There is no global relaxation and no ninth
event is accepted.

## Resulting census

```text
chemistry: POSITIVE=140, NEGATIVE=0, NOT_ESTABLISHED=90, UNRESOLVED=770
task: RELEVANT=133, NOT_RELEVANT=98, UNRESOLVED=769
training: INCLUDE=60, EXCLUDE_FROM_TRAINING_ONLY=72,
          NOT_APPLICABLE=98, UNRESOLVED=770
pair authority=140
role authority=132
mask authority=132
```

Exact5 applicability remains `132 / 52 / 52 / 132 / 132`. POST
source/sample/training remains `867 / 21 / 17`; PRE remains `0 / 0 / 0`.
Training include, human exclusion, future candidacy, formal admission, and
runtime usability remain `60 / 72 / 43 / 5 / 17`.

## Reconciliation and next pending unit

The published with-LCY reconciliation proves 21 source bindings, 127
normalized facts, and 21 stable identities. Its completed population is
151 events in 25 review units; 187 events in 106 units remain unreviewed.

The frozen queue is not rewritten. Combined with current reconciliation it
derives the next pending unit as current rank 1, raw priority rank 25, review
unit `COVAPIE_BULK_REVIEW_UNIT_BF1809E89D22D405`, ligand `0D8`, PDB `4V37`,
four events. This successor does not begin 0D8 review preparation.

## Lineage, determinism, and training boundary

The manifest carries the predecessor's published Exact150 semantic bindings
unchanged and appends exactly six local bindings, yielding Exact156 with no
identity or source-role collision. The predecessor manifest is bound
separately as validation identity and the successor manifest never records its
own SHA256.

The CSV and JSON outputs contain no timestamp, hostname, PID, UUID, absolute
machine path, or live Git state. Independent builds must be byte-identical.

This census is not training readiness. Step12D remains a smoke legality check,
not the final training-feature contract. The historical unknown atom-feature
policy and `feature_semantics_known=False` condition still require a formal
feature-semantics audit before training preparation or parameter updates.

## Verification

Run only the targeted suite and matching checker:

```bash
PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}" \
PYTHONDONTWRITEBYTECODE=1 \
pytest -q -p no:cacheprovider \
tests/test_covapie_cumulative1000_current_global_readiness_census_with_lcy_v1.py

PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}" \
PYTHONDONTWRITEBYTECODE=1 \
python scripts/check_covapie_cumulative1000_current_global_readiness_census_with_lcy_v1.py
```
