# CovaPIE Current11 multi-boundary human-review sidecar V1

## Purpose

This sidecar prepares a compatible human-review workspace for the five
Current11 V1-quarantined samples 000006–000010 whose candidate warhead sets
have exactly two graph-derived boundaries. It records candidate evidence only:
it does not make a human decision, create human gold or authority, supersede
V1 quarantine, generate SMARTS/masks/training labels, or run training.

## Exact source inputs

The production builder accepts only the exact submission bundle bytes, the
corresponding exact ingestion execution bundle bytes, and the exact repository
root `Path`. It recovers review/notes lineage from the submission, V1
quarantine authority lineage from the execution bundle, and proposal,
assignment, package, atom, bond, and parent-graph identity from the committed
authority context. It does not read a live review workspace, manual review
aids, dossiers, raw structures, snapshots, or network resources.

## CLI

Use an output path outside the Git repository whose parent already exists:

```bash
PYTHONPATH=src python -B \
  scripts/prepare_covapie_current11_multi_boundary_human_review_sidecar_v1.py \
  --repo-root /path/to/DiffSBDD-base \
  --submission-file /path/to/submission.json \
  --execution-file /path/to/execution.json \
  --output-dir /external/path/current11-multi-boundary-review-v1
```

The two inputs must be regular files, not symlinks. The output directory must
not exist. The CLI builds in a temporary sibling, publishes without clobbering,
and creates exactly three 0644 files:

- `verified_multi_boundary_evidence.csv`
- `multi_boundary_review_worklist.csv`
- `README.md`

## Frozen and human-fillable fields

The evidence CSV and the first 14 worklist fields are frozen. Do not edit the
evidence CSV or frozen worklist fields. The human-fillable worklist fields
begin with `review_decision`. A reviewer must explicitly provide the reviewed
atom set, exactly two ordered boundary records, reviewer identity, meaningful
rationale and notes, provenance attestation and attestor, source label,
completion state, and the future record digest. Proposed atoms and boundaries
are intentionally not copied into reviewed fields.

Only these future completed decisions are allowed:

- `accept_verified_two_boundary_proposal`
- `revise_two_boundary_atom_set_and_boundaries`
- `quarantine`

The initial `not_reviewed` value means only that review is incomplete. Samples
000009 and 000010 require an independent human determination of the final
multi-boundary gold core.

## V1 compatibility

The existing V1 quarantine authorities remain effective and are not modified
or superseded. Completing the sidecar does not automatically create authority.
The canonical mask contract remains exactly five tasks, including
`scaffold_only`; this sidecar adds no mask and is not training input. Formal
training still requires the feature-semantics audit, including resolution or
formal audit of the historical unknown-atom policy and
`feature_semantics_known=False`. Step12D remains a smoke legality check, not a
final training-feature contract.

## Verification

```bash
PY310=/path/to/covapie-env/bin/python3.10
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=src

"$PY310" -B -m pytest -q -p no:cacheprovider \
  tests/test_prepare_covapie_current11_multi_boundary_human_review_sidecar_v1.py
"$PY310" -B \
  scripts/check_prepare_covapie_current11_multi_boundary_human_review_sidecar_v1.py
```

## Next-step boundary

The only recommended next step is
`materialize_covapie_current11_multi_boundary_human_review_sidecar_workspace_v1`.
A future compiler/ingestion contract must be implemented and reviewed before
any multi-boundary authority can exist; this step must not jump to authority or
training.
