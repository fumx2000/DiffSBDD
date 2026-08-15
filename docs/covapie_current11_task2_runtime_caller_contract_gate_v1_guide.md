# CovaPIE Current11 Task2 Runtime Caller Contract Gate V1

## Purpose

This Exact4 freezes the contract for a future framework-independent Current11
Task2 runtime caller. It does not implement that caller, a Lightning hook, a
sidecar envelope, model integration, or training behavior.

The selected architecture is:

```text
additive_stateless_runtime_caller_with_explicit_rank_local_remap_and_compiler_contexts_v1
```

The future conceptual input order is `raw batch`, `remap_context`, and
`compiler_context`. The exact stage order is runtime observation extractor,
compiler bridge fast API, then remap-context fast API. Exact14 passes directly
to the compiler, and compiler success Exact18 passes directly to remap. Rename,
cast, repair, reorder, and schema reconstruction are forbidden.

## Environment and framework authority

Root `environment.yaml` is the primary reproducible compatibility authority:

```text
python=3.10.4
pytorch=2.0.1=*cuda11.8*
cudatoolkit=11.8
pytorch-lightning=1.8.4
```

The gate freezes its mode `0644`, 505 bytes, 29 LF, SHA256
`a63682607def274b362787a2bd9250a9192a1b898b13632285725901401ea156`,
and Git blob `9af8f3507cb691a0271bff36ba5341025c3a8bda`.

A prior engineering audit separately observed `/usr/bin/python`, Python 3.12.0,
PyTorch 2.5.1+cu124, and PyTorch Lightning 2.6.5. The gate records this only as
`corroborating_engineering_environment_snapshot`, with scope
`design_audit_observation_only`. It is not dependency authority, a runtime
execution requirement, or a claim about the environment currently executing
the checker. Exact active Python, PyTorch, and Lightning versions are not gate
preconditions. No package or environment change belongs to this gate.

Official PyTorch Lightning 1.8.4 source was audited at these paths:

- [training fit loop](https://github.com/Lightning-AI/lightning/blob/1.8.4/src/pytorch_lightning/loops/fit_loop.py)
- [evaluation loop](https://github.com/Lightning-AI/lightning/blob/1.8.4/src/pytorch_lightning/loops/dataloader/evaluation_loop.py)
- [data fetching](https://github.com/Lightning-AI/lightning/blob/1.8.4/src/pytorch_lightning/utilities/fetching.py)
- [strategy transfer](https://github.com/Lightning-AI/lightning/blob/1.8.4/src/pytorch_lightning/strategies/strategy.py)
- [module transfer handler](https://github.com/Lightning-AI/lightning/blob/1.8.4/src/pytorch_lightning/core/module.py)
- [batch-transfer hooks](https://github.com/Lightning-AI/lightning/blob/1.8.4/src/pytorch_lightning/core/hooks.py)

The repository-declared version and the historical corroborating snapshot agree
on the audited order:

```text
DataLoader output
-> on_before_batch_transfer
-> transfer_batch_to_device
-> on_after_batch_transfer
-> training/validation/test step
```

The selected insertion claim is deliberately scoped:

```text
selected_lightning_insertion_point=on_before_batch_transfer
selected_cpu_safe_insertion_point_for_audited_single_device_and_DDP_runtime
single_device_supported_scope=true
DDP_supported_scope=true
DataParallel_not_supported_by_this_v1=true
hook_mechanism_is_predict_extensible=true
current_predict_integration_proven=false
```

The hook runs in each rank's trainer process after the DataLoader yields, not in
a DataLoader worker. Worker context construction and pickling are unnecessary.

## Exact11 result

The future caller returns an exact built-in dictionary with schema
`covapie_current11_task2_runtime_caller_result_v1` and this field order:

1. `schema_version`
2. `runtime_status`
3. `failure_stage`
4. `failure_reason`
5. `compiler_status`
6. `remap_status`
7. `batch_sample_keys_or_none`
8. `compiler_failure_output10_or_none`
9. `remap_output17_or_none`
10. `provenance`
11. `readiness`

Whole success Output10 and transient success Exact18 are not retained. Exact18
exists only across the compiler-to-remap call boundary. A compiler failure
retains the whole failure Output10; any reached remap terminal retains the whole
Output17.

## Terminal routing

The exact terminal classes are `programming_error`, `extractor_failure`,
`compiler_failure`, `remap_failure`, and `full_success`.

Programming errors are exception-only and normalize to
`COVAPIE_CURRENT11_TASK2_RUNTIME_CALLER_V1_ERROR` with exception chaining. This
includes reached-stage context/product invariant violations, malformed product
shape or schema, unknown status, and field-order inconsistency.

The future caller normalizes ordinary `Exception` instances only. It does not
catch `BaseException`; `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`
propagate unchanged. This constraint applies to the future caller wrapper, not
to the already published extractor, compiler, or remap products.

An extractor failure is returned only for the published extractor token and its
eight frozen reasons. It short-circuits compiler and remap. Device copy-back,
name normalization, membership recasting, virtual-node stripping, and batch
repair are forbidden.

A compiler failure is possible only after extractor success. Compiler success
requires `compiler_status=COMPILED_EXACT`, `failure_reason=NONE`, and an exact
built-in Exact18 dictionary. `JOINT_LAYOUT_UNAVAILABLE` is a published component
status, not an allowed overall `compiler_status`. The exact structured overall
compiler failures are:

```text
BATCH_OBSERVATION_SCHEMA_MISMATCH
BATCH_SAMPLE_KEY_INVALID
BATCH_SAMPLE_KEY_DUPLICATED
BATCH_SAMPLE_KEY_UNKNOWN
BATCH_SAMPLE_KEY_AMBIGUOUS
SOURCE_CONTRACT_MISMATCH
IDENTITY_PROVIDER_MISSING
IDENTITY_PROVIDER_MISMATCH
ROLE_TABLE_AUTHORITY_MISSING
ROLE_LENGTH_MISMATCH
MEMBERSHIP_MASK_MISMATCH
VIRTUAL_NODE_POLICY_MISMATCH
NON_SOURCE_SAMPLE_NOT_ADMISSIBLE_IN_CURRENT11_COMPILER_V1
```

A structured compiler failure requires one of those exact statuses,
`failure_reason == compiler_status`, and
`adapter_input_exact18 is None`. It preserves the whole failure Output10 and
does not call remap. A top-level `JOINT_LAYOUT_UNAVAILABLE`, even with a matching
reason and no Exact18, is a programming error.

Remap runs exactly once only after `COMPILED_EXACT`. Remap success requires
`remap_status=REMAPPED_EXACT` and `failure_reason=NONE`. The exact structured
overall remap failures are:

```text
SOURCE_SAMPLE_DUPLICATED
BATCH_SAMPLE_IDENTITY_UNKNOWN
BATCH_SAMPLE_DUPLICATED
SCHEMA_VERSION_MISMATCH
SOURCE_TABLE_IDENTITY_MISMATCH
SOURCE_ROW_OUT_OF_RANGE
SOURCE_ATOM_IDENTITY_MISMATCH
ROLE_MISMATCH
PARSER_ATOM_NOT_FOUND
PARSER_ATOM_NOT_UNIQUE
PARSER_COUNT_MISMATCH
COLLATE_OFFSET_MISSING
COLLATE_LENGTH_MISMATCH
BATCH_INDEX_OUT_OF_RANGE
ENTRY_INVALID
```

A structured remap failure requires one of those exact statuses and
`failure_reason == remap_status`. Any status/reason inconsistency is a
programming error and is never repaired or rewritten. Full success requires
both exact success statuses. Missing joint indices caused by
`joint_layout_descriptor=None` remain successful when Output17 is
`REMAPPED_EXACT` with `failure_reason=NONE`; its provenance may still record
`joint_index_status=JOINT_INDEX_SPACE_UNAVAILABLE`. `NOT_IN_BATCH` is a
source-entry-only status, and `JOINT_INDEX_SPACE_UNAVAILABLE` is a joint-index
component status. Neither is allowed as the top-level `remap_status`; seeing
either there is a programming error even when its failure reason matches.

## Repository lifecycle publication boundary

The only lifecycle types are `precommit-untracked` and
`clean-tracked-successor`. A clean tracked successor is published only when
`HEAD == origin/main`, ahead and behind are both zero, the base commit is an
ancestor of HEAD, all Exact4 paths are tracked at stage 0, their worktree blobs
equal their HEAD blobs, and the working tree is clean. A clean local commit that
is ahead of `origin/main` is rejected; it is not labeled a published successor.

## Context and mutation boundary

Each single-device process or DDP rank builds one remap context at startup and
derives one compiler context from that exact remap-context object. The same
remap context is retained for fast remap. Per batch, both context build counts
are zero. There is no global singleton or cross-process mutable context.

The caller must leave the raw batch, compiler observation, and remap Exact18
unchanged. It must not insert a sidecar in place. The independent
`pocket_target_residue_atom_condition_indicator` is ignored by the extractor
and does not select Task2 identity. V1 is `virtual_nodes=false` only; nonzero or
malformed virtual-node payload fails at the extractor without stripping or
repair.

## Readiness boundary

Passing this gate sets:

```text
runtime_caller_contract_gate_implemented=true
runtime_caller_contract_gate_passed=true
ready_for_runtime_caller_implementation=true
ready_for_dataloader_integration=false
ready_for_model_integration=false
ready_for_loss_integration=false
feature_semantics_reaudit_required_before_training=true
step12d_smoke_is_final_training_feature_contract=false
ready_for_training=false
```

The canonical masks remain exactly `warhead_only/A`,
`linker_plus_warhead/B`, `scaffold_plus_warhead/B2`, `scaffold_only/B3`, and
`scaffold_plus_linker_plus_warhead/C`.

## Run the gate

From repository root:

```bash
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 python -B \
  scripts/check_covapie_current11_task2_runtime_caller_contract_gate_v1.py \
  --repo-root "$PWD" \
  --state-root "$(dirname "$PWD")/covapie-state"

PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 pytest -q \
  tests/test_covapie_current11_task2_runtime_caller_contract_gate_v1.py
```

The checker materializes its seven JSON artifacts only in memory, verifies a
before/after filesystem and Git snapshot, and writes one deterministic JSON
line to stdout. It does not perform runtime caller, hook, forward, backward,
optimizer, training, or artifact-write work.
