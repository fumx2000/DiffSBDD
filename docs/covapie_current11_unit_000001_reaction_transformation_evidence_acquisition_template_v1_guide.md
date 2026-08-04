# CovaPIE Current11 UNIT_000001 transformation template materializer v1

This increment implements a deterministic, metadata-only builder and a safe
publisher for the initial reaction-transformation evidence acquisition
template. It does not materialize the formal state target.

## Boundary

The builder validates the published overlay commit, the five SHA-bound overlay
data artifacts, and the frozen family/rule workspace and UNIT_000001 dossier.
It reads no structure files, performs no network or chemistry-tool access, and
does not generate atom maps, post-reaction states, SMARTS, review answers, or
approval decisions.

The Exact6 payload is:

1. `README.md`
2. `transformation_evidence_worklist.csv`
3. `structured_json_schema_templates.json`
4. `sample_transformation_gap_evidence.csv`
5. `source_authority_inventory_snapshot.csv`
6. `template_manifest.json`

The one-row worklist inherits all 41 overlay fields in byte-stable order. Its
16 frozen/derived values are preserved and all 25 future fields remain empty.
The eight structured JSON values are placeholder schemas, not answers. The
two-row gap evidence and 35-row authority inventory are copied byte-for-byte
from the formal overlay commit.

## Publication

The CLI uses `relative_symlink_to_immutable_sibling_v1`. It creates a mode-0755
hidden object directory, writes each mode-0644 file with exclusive creation,
validates the complete tree, and creates the canonical relative symlink with
no-replace semantics. Cleanup is inode-aware and never removes a competing
entry.

The default canonical target is:

```text
STATE_ROOT/manual-review/current11-reaction-transformation-evidence-acquisition-template-v1
```

`--check` is read-only. A caller may use `--output-dir` with the exact canonical
basename under a temporary `manual-review` directory for isolated validation.
Do not run non-`--check` publication against the formal state root during this
increment.

## Readiness

The template is ready only for a later controlled editable copy. It is not a
submission or authority artifact. The candidate valence ledger remains a gap
signal only, formal post-reaction authority remains absent, and a
feature-semantics successor audit is still required before training.
`ready_for_training=false`.
