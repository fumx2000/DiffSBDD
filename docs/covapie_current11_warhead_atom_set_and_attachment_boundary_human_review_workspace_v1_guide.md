# CovaPIE Current11 warhead atom-set and attachment-boundary review workspace v1

## Purpose and current state

This step turns the committed Current11 review packages into a practical
external workspace for real human review. It does not perform chemical review,
choose a candidate, run the submission compiler, call the public submission
adapter, run ingestion, or create authority while preparing the workspace.

The frozen package contains 11 samples and 200 candidate options: 185 are
review-eligible and 15 are review-ineligible. All 11 samples begin with
`review_decision=not_reviewed` and `review_completed=false`.

## Prepare the workspace

Use only the fixed environment:

```bash
PY310="/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/covapie-envs/diffsbdd-legacy-test-v1/bin/python3.10"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=src

"$PY310" -B \
  scripts/prepare_covapie_current11_warhead_atom_set_and_attachment_boundary_human_review_workspace_v1.py \
  --repo-root /cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/DiffSBDD-base \
  --output-dir /cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/covapie-state/manual-review/current11-warhead-boundary-v1
```

Both arguments are required. The output must be outside the repository. An
existing empty directory is accepted; an existing non-empty directory is
rejected without overwriting or deleting its contents.

The workspace contains exactly:

- `review_worklist.csv`
- `eligible_candidate_options.csv`
- `README.md`

These are manual working files and must not be added to Git.

## Review workflow

`review_worklist.csv` has one row for each of the 11 samples. Match it to
`eligible_candidate_options.csv` with `sample_index_row_id`.
`candidate_option_row_start_0based` is inclusive and
`candidate_option_row_end_exclusive` is exclusive; these spans refer to the
original complete 200-row source file. Because the workspace copy omits 15
ineligible options, the spans are not direct physical row numbers in the
filtered file. Use `option_order_within_sample_0based` within the matched
sample.

The identity fields through `candidate_option_row_end_exclusive` are frozen
and must not be edited. The only final decisions are:

- `select_admitted_candidate`
- `revise_atom_set_and_boundary`
- `quarantine`

`not_reviewed` means incomplete and cannot be submitted.

For `select_admitted_candidate`, enter the selected bridge-candidate index and
its source bridge-candidate SHA256, then fill all reviewed atom and boundary
fields. For `revise_atom_set_and_boundary`, keep both selected-candidate fields
empty and manually fill the reviewed atom and boundary fields. For
`quarantine`, keep the selected-candidate and reviewed boundary fields empty,
and keep the reviewed atom set as `[]`.

A real reviewer must supply `reviewer_id` and `review_rationale`. A real human
must change `reviewer_provenance_attested` to `true` and identify the attestor.
Only after the row is complete should `review_completed` be changed to `true`.
The generated workspace makes none of these changes automatically.

The committed package directory retains the complete 200-row options source.
The workspace copies only the 185 rows whose frozen `review_eligible` field is
`true`; it preserves all 28 fields, source order, atom IDs, boundaries, and
candidate hashes without recalculating chemistry.

## Compile a completed workspace

The implemented production function
`compile_covapie_current11_real_human_review_submission_bundle_v1` compiles
the completed worklist and frozen option/package inputs entirely in memory.
Use its CLI with all four required arguments:

```bash
"$PY310" -B \
  scripts/compile_covapie_current11_real_human_review_submission_bundle_v1.py \
  --repo-root /path/to/DiffSBDD-base \
  --workspace-dir /path/to/completed/current11-workspace \
  --output-file /external/existing-directory/submission.json \
  --submission-batch-id covapie_current11_real_human_review_submission_batch_v1
```

`--output-file` must be a complete path outside the Git repository. Its parent
directory must already exist, and the CLI refuses an existing file or symlink;
it never overwrites a submission. Compilation validates the strict JSON with
the public adapter, but it does not run ingestion or create authority.

Samples `000006`–`000010` remain fail-closed `quarantine` entries. Their
multi-boundary notes are preserved, but this exact-one-boundary compiler does
not automatically repair them or start a multi-boundary extension.

## Verification

Verify workspace preparation with the fixed interpreter:

```bash
"$PY310" -B -m pytest -q -p no:cacheprovider \
  tests/test_prepare_covapie_current11_warhead_atom_set_and_attachment_boundary_human_review_workspace_v1.py

"$PY310" -B \
  scripts/check_prepare_covapie_current11_warhead_atom_set_and_attachment_boundary_human_review_workspace_v1.py
```

Verify completed-workspace compilation separately:

```bash
"$PY310" -B -m pytest -q -p no:cacheprovider \
  tests/test_covapie_current11_real_human_review_submission_bundle_compiler_v1.py

"$PY310" -B \
  scripts/check_covapie_current11_real_human_review_submission_bundle_compiler_v1.py
```

## Handoff boundary

This workspace is not itself a formal submission bundle. After actual review,
the implemented compiler can produce strict adapter-accepted JSON at the
explicit external output path. That compilation is still neither ingestion
nor authority creation; any later `perform_covapie_current11_real_human_review_v1`
action remains a separate gated step.

The canonical mask set remains exactly `warhead_only`,
`linker_plus_warhead`, `scaffold_plus_warhead`, `scaffold_only`, and
`scaffold_plus_linker_plus_warhead`. Integrated/planned covalent model modules
remain 0/5 and training is not ready. Formal training still requires a
feature-semantics audit; Step12D remains a smoke legality check, not a final
training-feature contract.
