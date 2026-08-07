# CovaPIE Current11 Runtime Batch Observation Extractor V1

This product is the pure in-memory transport boundary between one non-empty `ProcessedLigandPocketDataset.collate_fn` batch and the published Current11 Task 2 batch-descriptor compiler Input Exact14. It consumes only the supplied batch. It does not import or call the dataset, compiler, compiler gate, remap adapter, dataloader, model, forward path, head, or loss; it performs no filesystem or formal-state access.

## Public API

```python
from covalent_ext.covapie_current11_runtime_batch_observation_extractor_v1 import (
    extract_covapie_current11_runtime_batch_observation_v1,
)

observation = extract_covapie_current11_runtime_batch_observation_v1(batch=batch)
```

The sole argument is keyword-only and must be an exact built-in `dict`. Success returns an exact built-in dictionary in frozen Exact14 order. Failure raises a private `ValueError` subclass with the exact message/args token:

```text
COVAPIE_CURRENT11_RUNTIME_BATCH_OBSERVATION_EXTRACTOR_V1_ERROR
```

Its stable `.reason` is exactly one of `missing_names`, `invalid_sample_key_scalar`, `invalid_role_length`, `invalid_membership`, `unsupported_empty_batch`, `virtual_nodes_not_supported`, `buffer_length_mismatch`, and `unsupported_runtime_type`. No partial Exact14 is returned.

## Runtime conversion

`names` and `receptors` must be exact built-in lists. Elements may be exact built-in `str` or exact `numpy.str_`; NumPy strings are converted through `.item()` and must yield exact built-in strings. Sample keys must be nonempty and already free of surrounding whitespace. The extractor performs no basename extraction, path parsing, normalization, case-folding, fuzzy matching, encoding guess, or arbitrary `str(value)` conversion. Duplicate and unknown well-formed sample keys remain compiler responsibilities.

`num_lig_atoms` and `num_pocket_nodes` must be rank-one CPU Torch tensors of batch length with non-boolean integral dtype and nonnegative values. They become exact built-in `list[int]`. Floating lengths are rejected even when mathematically integral.

`lig_mask` and `pocket_mask` must be rank-one CPU Torch tensors. Integral non-boolean and real floating dtypes are accepted. Floating values are checked for finiteness, mathematical integrality, and nonnegativity before conversion. Converted masks must exactly equal the expanded batch ordinals derived from the corresponding lengths. This extractor is the sole float-to-int transport normalization boundary; the compiler continues to receive only exact Python integers.

The actual runtime has separate ligand and pocket buffers, not a unified joint tensor. The extractor therefore emits `joint_layout_descriptor=None`. It never guesses `ligand_segment_then_pocket_segment_v1`.

The formal carrier has no virtual nodes. The output policy is `no_virtual_nodes_v1`. An optional `num_virtual_atoms` tensor is accepted only when it has the valid length-tensor shape/type/device and every value is exactly zero. Nonzero, malformed, or any other virtual-named payload fails closed.

The four required consistency buffers are `lig_coords`, `lig_one_hot`, `pocket_coords`, and `pocket_one_hot`. Each must be a rank-one-or-greater CPU Torch tensor whose leading dimension equals the relevant summed role lengths. Only these four built-in leading dimensions are transported. Coordinates, features, and auxiliary source/parser index tensors are never copied into JSON and never select identity.

The current dataset `collate_fn([])` raises `IndexError("list index out of range")`; it provides no empty runtime batch authority. Accordingly, validly decoded `names=[]` fails with `unsupported_empty_batch`, independently of the compiler's own empty-observation support.

## Output Exact14

The exact order is:

1. `schema_version`
2. `runtime_batch_schema_version`
3. `sample_key_schema_version`
4. `batch_sample_keys`
5. `ligand_lengths`
6. `pocket_lengths`
7. `ligand_membership`
8. `pocket_membership`
9. `joint_layout_descriptor`
10. `virtual_node_policy`
11. `receptors`
12. `consistency_buffer_lengths`
13. `debug_coordinates`
14. `debug_rank_metadata`

The fixed schemas are `covapie_current11_task2_batch_descriptor_compiler_input_v1`, `processed_ligand_pocket_dataset_collate_observation_no_virtual_v1`, and `covapie_sample_index_row_id_in_names_v1`. Joint/debug values are `None`. Before return, the implementation asserts exact field order and strict `json.dumps(..., ensure_ascii=True, allow_nan=False)` compatibility. No Torch or NumPy object escapes.

## Performance and integration boundary

Runtime is `O(B + L + P)`, with no authority rebuild or I/O. The input dictionary, lists, and tensors are never mutated. The current compiler still rebuilds/verifies Exact6 on every public call; an immutable preverified authority/cache boundary is required before a real DataLoader hot loop. This extractor does not solve or bypass that requirement.

The extractor implementation and focused tests do not make DataLoader, model, loss, or training integration ready. A feature-semantics re-audit remains mandatory before training; Step12D was a smoke legality check, not the final training-feature contract.

## Checker

Run the extractor-only checker with exactly two arguments:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 \
python scripts/check_covapie_current11_runtime_batch_observation_extractor_v1.py \
  --repo-root /absolute/path/to/DiffSBDD-base \
  --state-root /absolute/path/to/covapie-state
```

It verifies the tracked `dataset.py` blob, loads the formal carrier through the current dataset with `center=False`, checks canonical/subset/singleton extraction and one malformed membership, and proves before/after repository/formal identity. It never calls the compiler, adapter, or gate. Success emits one compact JSON line with status `PASS_RUNTIME_BATCH_OBSERVATION_EXTRACTOR_ONLY`; failure emits only the fixed extractor token on stderr and exits 1.

The checker pins the published extractor predecessor commit as an ancestry floor, not as the only admissible current `HEAD`. It accepts the precommit base, a committed-but-unpushed successor, and published descendant commits when the base remains an ancestor on `main`. It does not use `origin/main` for lifecycle admission. The frozen `dataset.py` blob and formal carrier/routing identities remain strict, while the before/after repository snapshot (including HEAD and origin) proves that one checker invocation performs no repository write.

Readiness after this increment is limited to `runtime_batch_observation_extractor_implemented=true`, `runtime_batch_observation_extractor_passed=true`, and `ready_for_runtime_batch_observation_extractor_integration_smoke=true`. DataLoader/model/loss/training readiness remain false.
