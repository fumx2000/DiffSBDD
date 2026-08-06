# CovaPIE Current11 Task 2 batch-index remap contract gate V1

## Scope

This increment is a standard-library-only, read-only, deterministic, in-memory contract gate. It freezes how the published Current11 Task 2 pocket/ligand source-table row locators can be interpreted in four distinct index spaces. It does not implement the public remap adapter, materialize an instance or tensor, change a dataloader or model, authorize a head or loss, or make the project ready for training.

The only public API is:

```python
build_covapie_current11_task2_batch_index_remap_contract_gate_v1(
    *, repo_root: Path, state_root: Path
) -> dict[str, bytes]
```

Both roots must be absolute, resolved, non-symlink directories. The function performs no writes and returns an exact built-in `dict` containing six byte payloads in fixed order:

1. `current11_task2_batch_index_remap_contract_manifest.json`
2. `current11_task2_batch_index_remap_input_schema.json`
3. `current11_task2_batch_index_remap_output_schema.json`
4. `current11_task2_batch_index_remap_status_vocabulary.csv`
5. `current11_task2_batch_index_remap_reference_vectors.json`
6. `current11_task2_batch_index_remap_contract_gate_report.json`

The first five payloads form the stable contract. The report is excluded from the stable digest.

## Frozen index spaces

The gate keeps four spaces separate:

- `source_atom_table_data_row_index` is a zero-based CSV data-row ordinal, excluding the header, and is valid only with the exact repository-relative path, SHA256, and physical row order.
- `parser_sample_local_index` is the retained-heavy index within one sample and one role. It equals the number of earlier retained rows. Explicit hydrogen is removed; unsupported non-hydrogen or invalid symbols reject the complete sample.
- `collated_batch_segment_index` is in an independent ligand or pocket flat buffer. It equals the actual role-specific exclusive prefix offset for the batch sample plus the parser-local index.
- `dynamics_joint_global_node_index` is conditional on `ligand_segment_then_pocket_segment_v1`. Ligand global indices equal ligand segment indices; pocket global indices equal `N_lig + pocket_segment_index`.

Train shuffling changes only actual batch order and offsets. It does not change sample identity, table identity, source row, or parser-local index. Distributed remapping is rank-local. The canonical collate has no node padding; padding from another representation must not enter offsets.

## Exact join and closed outcomes

The only join contract is `exact_source_table_row_identity_to_order_preserving_parser_node_v1`. It simultaneously binds full sample identity, role, exact table path/hash/count/order, source row, atom identity and auth/label locators, parser schema/count, and the exact parser-local result. Coordinates are consistency-only. Distance, nearest-atom logic, feature equality, model logits, inferred labels, warhead or reaction labels, RDKit indices, atom-map numbers, and checkpoint bytes are forbidden selectors.

The private reference evaluator accepts only the declared Exact18 input vocabulary. Its required fields are the first Exact15 fields, and its only optional fields are `joint_layout_descriptor`, `debug_coordinates`, and `debug_rank_metadata`. The formal names `source_pair_values_int64`, `source_sample_offsets_int64`, `source_entry_validity_bool`, and `source_sample_validity_bool` are mandatory; their former private aliases are rejected as schema mismatches, as are missing required fields and unknown top-level fields. The projection and payload digests and the frozen parser/collate schema versions are validated before any successful numeric output is constructed.

Current11 reference inputs are compared against a separate private authority reconstructed from the projection provenance, heavy-atom validation matrix, and Exact22 source tables. For each source sample and role, the evaluator compares path, SHA256, row count and order, selected source and local indices, parser count, and all eight atom identity fields—including a present, type-exact `label_seq_id` even when its authoritative value is empty. This authority is not an adapter input field. The synthetic ragged case uses a separate private synthetic authority without adding a nineteenth input field. A complete non-source batch identity may have zero pairs, but malformed batch identity fields reach `BATCH_SAMPLE_IDENTITY_UNKNOWN`.

The CSV freezes 18 status values. `REMAPPED_EXACT` is the sole overall success. A source entry outside the actual batch is `NOT_IN_BATCH` and is omitted from numeric arrays without a `0` or `-1` placeholder. Absence of the optional joint layout produces a present-but-null `pair_values_joint_global_indices` field and `JOINT_INDEX_SPACE_UNAVAILABLE`; independent segment remap remains successful. A hard failure uses the deterministic first hard-failure status for both `remap_status` and `failure_reason` and emits no valid numeric remap arrays.

All index spaces are zero-based, so numeric zero is valid. What is forbidden is using zero, `-1`, or another numeric value as a missing sentinel. Negative indices are invalid, missing source entries are omitted from numeric arrays, and joint unavailability is represented only by JSON `null`. Input and output schema metadata gives every sample, pair, and offset field one exact logical shape rather than a union of possible shapes.

## Reference cases

The reference artifact independently derives the Current11 Exact22 source-to-local mappings from the published projection instance, payload lineage, committed heavy-atom validation matrix, and 22 exact atom tables. It includes the canonical Exact11 batch, reversed order, mixed order `[10,4,0,7,2]`, subset `[10,4,0]`, a valid no-joint case, and a synthetic ragged future case with pair counts `[2,0,1]` and a batch permutation. These are contract examples only. Future batch values must always be recomputed.

## Checker

Run the read-only checker with exactly two required arguments:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python \
  scripts/check_covapie_current11_task2_batch_index_remap_contract_gate_v1.py \
  --repo-root /absolute/path/to/DiffSBDD-base \
  --state-root /absolute/path/to/covapie-state
```

Success returns code 0, empty stderr, and one compact canonical JSON line containing only the gate report. Any invalid argument or contract drift returns code 1, empty stdout, and the single error token `COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_CONTRACT_GATE_V1_ERROR` on stderr. There is no output option and no file is materialized.

## Readiness boundary

The contract directly advances future work on the target-residue atom condition adapter and covalent pair prediction head, without implementing either. Role/mask/anchor encoding remains blocked by incomplete primary-role authority; pre/post geometry remains blocked by missing authoritative pre/post state; contrastive loss remains blocked by missing negative-sampling and loss authorization.

Checkpoint state dicts, parameter shapes, the base atom-feature width, and the EGNN/SE3 backbone require no change. A feature-semantics re-audit remains mandatory before training. Dataloader, model, loss, and training readiness are all false.
