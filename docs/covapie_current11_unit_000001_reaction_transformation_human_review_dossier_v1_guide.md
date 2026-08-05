# CovaPIE Current11 UNIT_000001 transformation review dossier v1

This increment implements a deterministic, non-authoritative human review
dossier. It reads and validates the controlled editable transformation review
workspace, the immutable acquisition template, the existing family/rule
workspace, and the existing UNIT_000001 family/rule dossier. It does not write
any of those sources.

`transformation_evidence_worklist.csv` is the controlled workspace's only
mutable source. Its Exact41 header and Exact16 frozen fields remain invariant,
while its Exact25 future fields may be filled by a later controlled human
workflow. The five reference files remain byte-frozen. The initial blank
worklist SHA is an initial snapshot witness, not a live worklist invariant.

## Public API

```python
build_covapie_current11_unit_000001_reaction_transformation_human_review_dossier_v1(
    *, repo_root: Path, state_root: Path
) -> dict[str, bytes]
```

The keyword-only builder is silent, read-only, metadata/review-aid only, and
returns the dossier Exact8 in memory. It does not inspect raw structures, use
chemistry toolkits, access the network, run models, or perform training.

## Exact8

The dossier contains `README.md`, the byte-copied
`candidate_local_graph.svg`, a frozen transformation summary, a blank Exact25
questionnaire, byte-copied gap/source/schema references, and a manifest. The
manifest hashes the other seven files and never hashes itself.

The candidate graph is not post-state authority. The pre-reaction sum 4 and
conditional sum 5 are gap signals only. No atom map, post-state, bond-order
delta, charge, protonation, leaving-group, reversibility, SMARTS, approval,
attestation, submission, ingestion, or authority answer is generated.

The dossier neither copies the mutable worklist nor captures its future
answers. Later Exact25 edits therefore do not change any byte of the dossier
Exact8. Source checking validates the live Exact41/Exact16 structural contract
and the five immutable reference SHA values without treating nonblank future
fields as semantic approval, submission readiness, or authority.

## CLI and publication boundary

The CLI accepts `--repo-root`, `--state-root`, optional `--output-dir`, and
`--check`. Its default output is:

```text
STATE_ROOT/manual-review-aids/current11-reaction-transformation-review-v1/
CURRENT11_REACTION_TRANSFORMATION_REVIEW_UNIT_000001
```

Materialization uses exclusive real-directory creation, mode `0755`, and
Exact8 regular files with mode `0644`. It refuses an existing target and only
cleans up exact inodes created by the failing invocation. Replaced files or
directories are preserved and cause a fail-closed error. `--check` is
read-only and revalidates sources, generated contents, hashes, blank answers,
non-authoritative flags, and blocked readiness. Its runtime report may expose
the current worklist SHA and future nonblank count, but those dynamic values
are not stored in the dossier or manifest. Raw state/output path spellings are
checked lexically; relative paths and symlink aliases are rejected.

Publication tests must use a temporary state root. This implementation step
does not create the formal dossier target.

## Readiness

The dossier is ready only for human evidence acquisition. Updating the formal
worklist is a separate controlled step, followed by independent semantic
validation and identity/full-semantics attestation. A feature-semantics audit
remains required before training. `ready_for_training=false`.
