# CovaPIE Current11 runtime sample and role-order carrier contract gate V1

This gate freezes the contract that a future Current11 runtime carrier materializer must satisfy. It is read-only, deterministic, stdlib-only apart from local `covalent_ext` predecessors, and returns all evidence as bytes in memory. It does not create an NPZ, a carrier manifest instance, a batch descriptor, a tensor, or a compiler.

## Public API

The module exposes one keyword-only API:

```python
build_covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, bytes]
```

The exact built-in dictionary contains, in order:

1. `current11_runtime_sample_and_role_order_carrier_contract_manifest.json`
2. `current11_runtime_sample_key_registry.csv`
3. `current11_runtime_role_order_registry.json`
4. `current11_runtime_carrier_manifest_schema.json`
5. `current11_runtime_sample_and_role_order_carrier_status_vocabulary.csv`
6. `current11_runtime_sample_and_role_order_carrier_contract_gate_report.json`

Only the first five artifacts participate in the stable contract digest. The report is self-excluded.
The digest domain is the exact NUL-terminated byte string
`COVAPIE_CURRENT11_RUNTIME_SAMPLE_AND_ROLE_ORDER_CARRIER_CONTRACT_GATE_V1\0`;
an ASCII space, line feed, or second NUL is not part of the framing.

Before claiming the adapter predecessor passed, the gate calls the published
`build_covapie_current11_task2_batch_index_remap_adapter_v1` API exactly once per
build with a deep copy of the canonical Exact18 input. It validates the returned
Exact2 order, both frozen byte identities, `REMAPPED_EXACT`/`NONE`, the public
adapter report status, the remap contract digest, and independently recomputes
the stable output digest using stdlib framing. Private adapter execution and
serialization helpers are not predecessor authority. The repository Exact4
precommit compatibility filter encloses this public call and is restored in a
`finally` boundary; any fifth untracked file remains visible and fails closed.

## Frozen sample-key contract

The sole schema is `covapie_sample_index_row_id_in_names_v1`. A future `ProcessedLigandPocketDataset.names` carrier must be rank-one in actual materialized sample order, and every value must be the exact, nonempty, trimmed, unique UTF-8 `sample_index_row_id`. Basename extraction, path normalization, case folding, prefix stripping, and fuzzy matching are forbidden.

`receptors` is optional consistency evidence whose recommended Current11 value is the exact PDB ID. It is never an identity authority and cannot replace `names`. Batch ordinal, coordinates, features, counts, distances, and filesystem metadata are not sample identity inputs.

The in-memory CSV binds the Current11 Exact11 relation:

```text
sample_index_row_id
  -> sample_preparation_input_id
  -> pdb_id
  -> ligand_comp_id
```

The three JUG samples remain unambiguous because identity is the exact row ID, not ligand component ID.

## Frozen role-order contract

The sole schema is `order_preserving_checkpoint_heavy_projection_v1`. Ligand and pocket are independent role spaces. For each of 11 samples and each role, the registry binds the exact source-table relative path, source SHA256, row count, explicit-H filtering result, retained-heavy count, full projected source-row vector, full nullable source-to-projected vector, and full projected Exact8 atom-identity sequence digest.

The Exact8 identity fields are:

1. `atom_site_id`
2. `atom_name`
3. `type_symbol`
4. `residue_name_or_ligand_comp_id`
5. `auth_asym_id`
6. `auth_seq_id`
7. `label_asym_id`
8. `label_seq_id`

Explicit hydrogen maps to JSON `null`; a `-1` sentinel is forbidden. Unsupported non-hydrogen or invalid element syntax rejects the whole sample. Surviving rows retain strict physical CSV data-row order and receive contiguous local indices. The selected Task2 endpoint is only a cross-check and cannot replace the full order binding.

The frozen retained counts are 2202 pocket nodes and 323 ligand nodes. The gate independently re-reads all 22 source tables and recomputes 329 pocket and 16 ligand explicit-H exclusions, with zero unsupported non-hydrogen rows.

## Runtime schema boundary

The future manifest schema requires an actual state-root-relative runtime artifact path and SHA256 of the actual artifact bytes. It binds the names array, optional receptors evidence, sample offsets and lengths, per-sample role-record digests, flat projected-row order, and flat atom-identity order.

V1 permits no padding, crop, atom reorder, role exchange, or virtual nodes. `AppendVirtualNodes` is detected in the existing source and explicitly excluded by `no_virtual_nodes_v1`.

Checkpoint compatibility uses the canonical five-field boundary:
`checkpoint_state_dict_change_required`,
`base_model_parameter_shape_change_required`,
`base_atom_feature_width_change_required`,
`egnn_or_se3_backbone_change_required`, and `checkpoint_bytes_read` are all
false. The older generic parameter-shape and atom-feature-width aliases are not
part of this contract. No checkpoint bytes or model code are read or changed.

The historical target-residue temporary NPZ probe is reference feasibility evidence only. Its source shows temporary-directory isolation, Exact11 Unicode names and PDB receptors, dataset/collate transport checks, and cleanup. It is not a formal runtime carrier, formal names binding, or formal role-order authority.

The V1 and V2 routing-sidecar materializers remain evidence that the formal routing sidecar exists while runtime consumer, tensor materialization, and dataloader readiness are false. They do not materialize this runtime carrier.

## Checker

Run the checker without bytecode or cache output:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 \
python scripts/check_covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1.py \
  --repo-root /absolute/path/to/DiffSBDD-base \
  --state-root /absolute/path/to/covapie-state
```

Success returns code 0, empty stderr, and one compact canonical JSON line containing only the gate report. Any missing, abbreviated, extra, output, materialization, NPZ, tensor, dataloader, model, loss, or training argument fails with the fixed error token. The checker writes no files.

## Readiness and next increment

Passing this gate means the contract and both in-memory registries exist. It does not mean a formal runtime carrier or formal NPZ exists. Runtime sample-key availability, runtime role-order binding availability, compiler readiness, dataloader/model/loss readiness, and training readiness remain false.

The only recommended next increment is `implement_covapie_current11_runtime_sample_and_role_order_carrier_materializer_v1`. That increment may materialize formal carrier evidence under the state root and bind actual runtime artifact bytes, but must not commit an NPZ or implement the batch descriptor compiler. A feature-semantics re-audit remains mandatory before training.
