# CovaPIE Current11 Task 2 Batch Descriptor Compiler V1

This module implements the frozen Current11 Task 2 batch descriptor compiler as a pure, in-memory product API. It validates a caller-supplied runtime batch observation and, on success, produces the Exact18 input expected by the separately published batch-index remap adapter.

It does not extract observations from a dataloader, read tensors or checkpoints, execute remapping, write artifacts, change the dataset/model/forward/head/loss path, or authorize training.

## Public API

```python
from pathlib import Path

from covalent_ext.covapie_current11_task2_batch_descriptor_compiler_v1 import (
    compile_covapie_current11_task2_batch_descriptor_v1,
)

result = compile_covapie_current11_task2_batch_descriptor_v1(
    repo_root=Path("/absolute/path/to/DiffSBDD-base"),
    state_root=Path("/absolute/path/to/covapie-state"),
    observation=runtime_observation,
)
```

All arguments are keyword-only. `repo_root` and `state_root` must be absolute, canonical directories. `observation` must be an exact built-in `dict`.

Every call rebuilds the compiler contract Exact6 through the contract gate's sole public API. The compiler verifies the frozen bytes, artifact order, stable digest, schemas, status vocabulary, Exact16 validation order, 35 reference IDs, formal carrier binding, provider digest, and readiness. It then deep-copies Source Exact10 from the canonical reference Exact18 and the 11-sample/22-role identity provider from the reference vectors. Runtime observations cannot supply or override either authority.

Authority, root, gate, formal-state, provider, or internal-invariant failures raise exactly:

```text
COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_V1_ERROR
```

Malformed or inconsistent runtime observations are normal product inputs. They return a fail-closed Output Exact10 with a closed hard status, the same `failure_reason`, and `adapter_input_exact18=None`; they do not raise the product error token.

## Input Exact14

The exact field order is:

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
11. `receptors` (optional)
12. `consistency_buffer_lengths` (optional)
13. `debug_coordinates` (optional)
14. `debug_rank_metadata` (optional)

Fields 1–10 are required. Unknown fields fail closed. Source-contract override fields return `SOURCE_CONTRACT_MISMATCH`; all other forbidden or unknown fields return `BATCH_OBSERVATION_SCHEMA_MISMATCH` according to the frozen validation order.

Sample keys are exact, nonempty, trimmed strings in actual batch order. There is no basename, case-fold, fuzzy, coordinate, feature, or distance identity fallback. Duplicate keys are rejected. A Current11-shaped non-source key is not admissible in V1.

Lengths and membership entries must be exact Python integers; booleans and floats are rejected. Role lengths must equal the pinned parser output counts, and membership masks must equal expanded batch ordinals. Offsets are compiler-derived exclusive prefix sums only. The V1 virtual-node policy is exactly `no_virtual_nodes_v1`.

The joint descriptor is either `ligand_segment_then_pocket_segment_v1` or `None`. A null descriptor leaves overall compilation successful and reports `JOINT_LAYOUT_UNAVAILABLE` only for the joint component. Receptors are consistency-only. Debug fields are `None` or exact JSON-safe dictionaries, are deep-copied for transport, and never participate in identity.

## Output and composition

The Output Exact10 order is:

1. `schema_version`
2. `compiler_status`
3. `failure_reason`
4. `adapter_input_exact18`
5. `batch_sample_key_outcomes`
6. `source_contract_digest`
7. `identity_provider_digest`
8. `runtime_schema_binding`
9. `provenance`
10. `readiness`

A success returns `COMPILED_EXACT`, `failure_reason="NONE"`, and all 18 adapter fields in frozen order. The first 10 fields are deep-copied pinned source authority. The final eight contain actual batch identity/order, selected provider tables, validated role lengths and membership, compiler-derived offsets, the optional joint descriptor, and deep-copied debug transport.

The compiler never calls the remap adapter. A consumer may independently pass the successful `adapter_input_exact18` to `build_covapie_current11_task2_batch_index_remap_adapter_v1`. The canonical, reversed, mixed, subset, no-joint, and empty reference batches compose as `REMAPPED_EXACT`; the empty batch produces empty pair batch indices, and the no-joint batch produces null joint-global indices. Hard failures must never be sent to the adapter.

The 35 published reference records comprise 6 success cases, 24 observation-expressible hard failures, and 5 evaluator-only authority perturbations. Product calls reproduce the 30 runtime-observation cases after the two documented product-stage readiness/provenance changes. The five authority perturbations are enforced at the stronger product boundary: altered or unavailable frozen gate authority raises the fixed compiler error token rather than being accepted as runtime input.

## Checker

Run the dedicated checker with only the two accepted CLI arguments:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 \
python scripts/check_covapie_current11_task2_batch_descriptor_compiler_v1.py \
  --repo-root /absolute/path/to/DiffSBDD-base \
  --state-root /absolute/path/to/covapie-state
```

On success it writes one compact JSON line with status `PASS_IN_MEMORY_TASK2_BATCH_DESCRIPTOR_COMPILER_ONLY`. It checks all six success shapes, two representative hard failures, independent 6/6 public-adapter composition, empty/no-joint behavior, and before/after repository and formal-state identity. Failure writes no stdout, writes only the fixed compiler error token to stderr, and exits with status 1.

## Readiness boundary

This product advances `task2_batch_descriptor_compiler_implemented` to true and closes `ready_for_task2_batch_descriptor_compiler_implementation`. The runtime batch observation extractor remains unimplemented. Dataloader, model, and loss integration remain false. Training remains false.

Before any formal training, fine-tuning, training preparation, backward pass, optimizer step, or parameter update, CovaPIE still requires an explicit feature-semantics audit. Step12D was a smoke legality check, not a final training-feature contract. The historical `UNKNOWN_ATOM_FEATURE_POLICY` and `feature_semantics_known=False` state must be resolved or formally audited first.
