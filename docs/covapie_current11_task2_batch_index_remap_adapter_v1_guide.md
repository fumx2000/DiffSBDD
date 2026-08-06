# CovaPIE Current11 Task 2 batch-index remap adapter V1

This increment implements a public, deterministic, fail-closed, read-only, stdlib-only adapter for the frozen Current11 Task 2 batch-index remap contract. It does not modify the dataset, parser, collate function, dataloader, model, forward path, head, loss, or training code.

## Public API

The module `covalent_ext.covapie_current11_task2_batch_index_remap_adapter_v1` exports exactly:

```python
build_covapie_current11_task2_batch_index_remap_adapter_v1(
    *,
    repo_root: Path,
    state_root: Path,
    adapter_input: dict[str, object],
) -> dict[str, bytes]
```

The input must be an exact built-in dictionary. The adapter deep-copies it before validation and never mutates caller-owned data. It accepts the frozen Exact18 vocabulary: the first 15 fields are required and only `joint_layout_descriptor`, `debug_coordinates`, and `debug_rank_metadata` are optional.

Every invocation verifies the published remap contract gate module identity and calls its sole public API twice. The resulting Exact6 must be byte-identical and match every frozen artifact identity and the stable contract digest. Manifest, input schema, output schema, status CSV, and reference-vector authority are parsed from those stable bytes; Markdown is never contract authority. The adapter independently performs the remap and does not call the gate's private reference evaluator.

During precommit development, the gate observation filters only the four exact `??` paths belonging to this increment. All other Git states remain visible and fail closed. The original observation function is restored in a `finally` block. A clean published successor needs no filtering.

## In-memory artifacts

The return value is an exact built-in dictionary with two byte values in this order:

1. `current11_task2_batch_index_remap_output.json`
2. `current11_task2_batch_index_remap_adapter_report.json`

Both are canonical UTF-8 JSON with sorted keys, two-space indentation, ASCII escaping, no NaN or infinity, and exactly one terminal LF. Neither artifact is written to disk. The stable digest frames only the remap output under the domain `COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_ADAPTER_V1\0`; the report is excluded.

The output carries the frozen Exact17 vocabulary. Numeric pairs remain in pocket-then-ligand column order. Segment indices are computed independently in pocket and ligand flat spaces. For `ligand_segment_then_pocket_segment_v1`, joint indices are `[N_ligand + pocket_segment, ligand_segment]`. When the joint descriptor is absent or null, segment remap still succeeds and the joint field is null with `JOINT_INDEX_SPACE_UNAVAILABLE` provenance.

Source samples outside the actual batch receive `NOT_IN_BATCH` outcomes and create no numeric placeholder. A complete non-source batch sample is legal, contributes zero Task 2 pairs, and must still provide structurally valid role tables, parser counts, offsets, and membership masks. Zero is a valid source, local, segment, or joint index; negative indices are rejected.

Batch role lengths, offsets, and membership masks use exact built-in integer-list semantics: booleans and floats cannot stand in for int64 values. Offsets must be the exact exclusive prefix sum before any segment arithmetic or indexing occurs, and membership values must be exact in-range batch ordinals. Invalid layout descriptors return a deterministic contract-level Exact2 rather than leaking a Python indexing exception.

Every role table, including a non-source zero-pair table, carries safe repository-relative provenance. Its selected source row and parser-local index must be in bounds, the selected source-to-parser mapping must exist and agree exactly with the declared local index, and its Exact8 atom identity must use exact trimmed strings (with an empty `label_seq_id` explicitly allowed). Non-source paths are structurally validated but are not read as Current11 authority; Current11 tables remain subject to full published Exact22 comparison.

The Current11 `source_sample_order` is compared with type-aware authority semantics rather than ordinary Python dictionary equality. Each source record has the exact published key set; every value must have the same exact built-in type and value as authority, and `source_sample_index` is an exact integer equal to its zero-based ordinal. Consequently booleans and numerically equal floats cannot impersonate source indices. Batch joins remain based on the four frozen string identity fields, so this rule does not require a complete non-source batch sample to belong to Current11.

Hard failures return a valid Exact2 with empty numeric arrays, a null joint field, a deterministic closed-vocabulary status, and `FAIL_CLOSED_INPUT_REJECTED` in the report. Non-dictionary, non-JSON, non-finite, root, identity-drift, formal-state-drift, and internal-invariant failures raise the single adapter `ValueError` token.

## Checker

Run the checker without materializing output:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python scripts/check_covapie_current11_task2_batch_index_remap_adapter_v1.py \
  --repo-root /absolute/path/to/DiffSBDD-base \
  --state-root /absolute/path/to/covapie-state
```

Only those two required arguments are accepted. Success prints one compact JSON line containing the adapter report and writes nothing. Failure prints only `COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_ADAPTER_V1_ERROR` to stderr.

## Readiness boundary

This adapter advances only pure batch-descriptor remap and compiler design. It does not materialize a formal remap, torch tensor, or NumPy artifact. Dataloader, model, forward, and loss integration remain unauthorized and not ready. A feature-semantics re-audit remains mandatory before training; this increment does not make the project ready for training.
