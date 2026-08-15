# CovaPIE Current11 Task2 Runtime Caller V1

## Purpose and authority

This Exact4 implements the framework-independent, stateless Current11 Task2
runtime caller authorized by published contract commit
`b1dd9e44ba2877a46d9622b2a24612e523f1a100` and stable contract digest
`098c66343e2e924ea75ce6619cac7aa9b46baabd7f0143e80e652764660a1c20`.
The selected architecture remains
`additive_stateless_runtime_caller_with_explicit_rank_local_remap_and_compiler_contexts_v1`.

This implementation does not add a Lightning hook, DataLoader sidecar
packaging, model/head/forward/loss integration, checkpoint access, training, or
context construction.

## Public API

The production module exports only:

```python
run_covapie_current11_task2_runtime_caller_v1(
    *,
    batch: dict[str, object],
    remap_context: object,
    compiler_context: object,
) -> dict[str, object]
```

The caller owns neither context. Each process or DDP rank must build one remap
context at startup, derive one compiler context from that exact remap context,
and retain both. Per batch, both context-build counts are zero.

## Hot-path stage order

Every call uses this strict order:

```text
raw batch
-> runtime observation extractor exactly once
-> compiler bridge fast API exactly once if extraction succeeds
-> remap-context fast API exactly once only for COMPILED_EXACT
-> Exact11 runtime result
```

The Exact14 observation is passed directly to the compiler. Compiler-success
Exact18 is passed directly to remap and remains transient. The caller does not
copy, rename, cast, repair, reorder, or reconstruct either handoff product. It
does not retain successful Output10 or Exact18.

The production import boundary is Python standard library plus the published
runtime observation extractor, compiler-context bridge fast owner, and
remap-context fast owner. The hot path performs no filesystem, Git, subprocess,
artifact, report, cache, model, backward, optimizer, or training work.

## Exact11 result and terminal routing

The exact built-in result dictionary uses schema
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

Returned terminal statuses are `extractor_failure`, `compiler_failure`,
`remap_failure`, and `full_success`. Programming errors are exception-only:
the caller raises
`ValueError("COVAPIE_CURRENT11_TASK2_RUNTIME_CALLER_V1_ERROR")` with a non-null
cause. It catches `Exception`, not `BaseException`, so `KeyboardInterrupt`,
`SystemExit`, and `GeneratorExit` raised at its direct stage-call boundaries
propagate unchanged.

An extractor failure is returned only when the published error token is paired
with one of its frozen eight reasons. It short-circuits compiler and remap. A
compiler failure is returned only for one of the frozen thirteen overall
failure statuses, with a matching failure reason and no Exact18; it retains the
same whole Output10 and does not call remap. A remap failure is returned only
for one of the frozen fifteen overall failure statuses with a matching reason;
it retains the same whole Output17.

Compiler success requires `COMPILED_EXACT` with `failure_reason=NONE` and exact
Exact18. Remap success requires `REMAPPED_EXACT` with `failure_reason=NONE`.
Top-level compiler `JOINT_LAYOUT_UNAVAILABLE` and top-level remap `NOT_IN_BATCH`
or `JOINT_INDEX_SPACE_UNAVAILABLE` are programming errors, not returned
failures.

When the input has `joint_layout_descriptor=None`, a valid Output17 may have
`pair_values_joint_global_indices=None` and provenance
`joint_index_status=JOINT_INDEX_SPACE_UNAVAILABLE`. If its top-level status is
still `REMAPPED_EXACT`, the runtime result is `full_success`.

## Mutation and sidecar boundary

The caller is read-only with respect to the raw batch, Exact14 observation, and
Exact18 handoff. It does not clone a tensor batch for runtime checking. Tests
verify tensor identity, dtype, device, shape, `_version`, and content, plus
dict/list identity and content.

An extra `pocket_target_residue_atom_condition_indicator` field is ignored and
does not participate in Task2 identity selection. V1 supports no virtual nodes.
A nonzero or malformed virtual payload returns extractor failure with
`virtual_nodes_not_supported`, without repair, stripping, or retry.

## Provenance and readiness

Every returned terminal receives fresh deterministic built-in provenance and
readiness dictionaries. Provenance freezes the selected architecture, contract
commit, contract digest, and `runtime_caller_implemented=true`. It contains no
timestamp, absolute path, PID, rank, device, mutable context, or design-report
identity.

Implementation readiness is:

```text
runtime_caller_contract_gate_implemented=true
runtime_caller_contract_gate_passed=true
runtime_caller_implemented=true
ready_for_runtime_caller_implementation=false
ready_for_dataloader_integration=false
ready_for_model_integration=false
ready_for_loss_integration=false
feature_semantics_reaudit_required_before_training=true
step12d_smoke_is_final_training_feature_contract=false
ready_for_training=false
```

Step12D remains a smoke legality check, not a final training-feature contract.
A feature-semantics re-audit, including the historical unknown atom-feature
policy, remains mandatory before training.

## Checker and tests

The checker accepts only the `precommit-untracked` and
`clean-tracked-successor` repository profiles. It pins the published contract
commit, gate/source identities, stable contract digest, and ancestry without
calling the published contract-gate builder. It performs context acquisition
outside the per-batch hot path, exercises four formal collate orderings plus
extractor/compiler failures, verifies call counts and repository immutability,
and writes exactly one compact deterministic JSON line.

Run from repository root:

```bash
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 python -B \
  scripts/check_covapie_current11_task2_runtime_caller_v1.py \
  --repo-root "$PWD" \
  --state-root "$(dirname "$PWD")/covapie-state"

PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 pytest -q \
  tests/test_covapie_current11_task2_runtime_caller_v1.py
```

The targeted tests cover all four returned terminals, structured failure
retention, malformed products, overall-status eligibility, status/reason
invariants, control-flow `BaseException` propagation, fresh metadata, no
mutation, no per-batch I/O/context construction, target-residue independence,
virtual-node fail-closed behavior, lifecycle profiles, and deterministic
checker output.
