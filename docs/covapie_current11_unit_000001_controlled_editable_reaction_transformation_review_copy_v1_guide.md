# CovaPIE Current11 controlled editable transformation review copy v1

## Scope

This increment implements the deterministic, controlled conversion of the
formally published immutable acquisition template into an initial editable
review-copy payload. It does not publish the formal review directory, fill or
validate transformation evidence, compile a submission, ingest a review, or
create authority, role, seed, tensor, model, or training outputs.

## Public API

`build_covapie_current11_unit_000001_controlled_editable_reaction_transformation_review_copy_v1(*, repo_root, state_root)`
is keyword-only, deterministic, silent on import, read-only, and returns the
initial Exact6 payload as `dict[str, bytes]`.

The builder validates the frozen source materializer commit, the published
immutable template canonical/object identity, all source file hashes and
modes, the Exact41 worklist contract, its Exact16 frozen values, its 25 blank
future fields, and the source readiness and non-authority assertions.

## Editable boundary

The output is an exclusive real directory using publication scheme
`exclusive_real_directory_editable_workspace_v1`. Only
`transformation_evidence_worklist.csv` may later be edited. Its Exact16 frozen
fields and one-row Exact41 structure must remain unchanged. The Exact25 future
fields are the only editable fields.

An empty string means unreviewed. An explicit canonical empty list means the
question was reviewed and no records were found; those states are distinct.
The README, schema templates, gap evidence, source inventory, and editable
review manifest are immutable reference files.

## CLI

The materializer accepts `--repo-root`, `--state-root`, optional
`--output-dir`, and `--check`. The default output is
`STATE_ROOT/manual-review/current11-reaction-transformation-review-v1`.
Publication refuses an existing target and uses inode-aware cleanup that never
deletes a replaced file or directory. `--check` is read-only and reports the
current worklist SHA and future nonblank count while continuing to report
semantic validation, direct-submission readiness, authority change, and
training readiness as false.

## Readiness boundary

This editable copy is not a submission or authority and does not establish a
reaction mechanism. The candidate valence ledger remains a gap signal only.
Future entries need independent semantic validation and attestation. The
feature-semantics audit remains mandatory before formal training, and
`ready_for_training=false`.
