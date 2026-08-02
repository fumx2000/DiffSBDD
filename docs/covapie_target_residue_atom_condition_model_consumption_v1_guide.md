# CovaPIE target-residue atom condition model consumption V1

## Scope and lineage

This successor implements the frozen model-consumption design at commit
`99425693056cd8800b9f93a19ea79a1e3e77c68e`. The bound design production SHA256
is `875e2095702526671d3ef032dca375ffd3bf5cd82038a34295c19cccc0d51817`, and
the bound design response SHA256 is
`958252bc355b5103c721a433c62341321ff8414d4e3407bdc35f70abbc638358`.

The implementation changes only these existing model sources:

- `lightning_modules.py`
- `equivariant_diffusion/dynamics.py`
- `equivariant_diffusion/conditional_model.py`
- `equivariant_diffusion/en_diffusion.py`

It does not implement repository CLI selector forwarding or the successor
model-consumption gate. It does not change the dataset, collate logic, EGNN
implementation, checkpoint, loss expressions, normalization, noise schedule,
or sample distributions.

## Checker lifecycle and repository scope

The design commit is the frozen implementation-design ancestor. It is not a
permanent requirement for the current `HEAD` value. The implementation checker
binds that commit by its existence, exact subject, unique parent, committed
design-production bytes, and production SHA256. It separately verifies with
`git merge-base --is-ancestor` that the design commit remains an ancestor of
`HEAD`. This remains valid before the implementation commit, after a local
implementation commit, and after that commit is pushed.

The candidate repository scope is the union of two read-only Git views:

```text
git diff --name-only <design-base-commit>
git ls-files --others --exclude-standard
```

Before commit, the first command reports the four modified model sources and
the second reports the four untracked support files. After commit, the first
command reports all eight implementation paths and the second is empty. Their
validated union is therefore the same exact eight-path scope in both states.

The checkpoint migration helper, targeted tests, implementation checker, and
guide are implementation support files; their presence does not mean repository
CLI forwarding was implemented. CLI forwarding is derived only from intersection
with the six frozen repository caller paths, together with direct SHA256 checks
of all six caller files. Any changed caller or caller-byte drift fails closed.
Likewise, the model-consumption gate fact is derived only from the four genuine
gate production/test/checker/guide path identities.

This checker lifecycle revision changes no model-consumption behavior,
parameter, checkpoint profile, migration behavior, or readiness result.

## Public model contract

The enable flag is `target_residue_atom_conditioning`. It is an exact `bool`
and defaults to `False` in both `LigandPocketDDPM` and `EGNNDynamics`.

The sidecar field and explicit argument are both named
`pocket_target_residue_atom_condition_indicator`. A present value must be a
one-dimensional `torch.bool` tensor aligned with the flattened pocket-node
order. Invalid model-consumption input raises the canonical error:

```text
COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_MODEL_CONSUMPTION_INVALID
```

No non-boolean condition is automatically cast. A condition cannot be supplied
when the enable flag is false.

## Parameter and injection

With conditioning disabled, `EGNNDynamics` registers
`target_residue_atom_condition_embedding` as `None`. The new key is therefore
absent from `state_dict()`, preserving the legacy state-key set and all existing
tensor shapes.

With conditioning enabled, the model creates exactly one additional parameter:

```text
name=target_residue_atom_condition_embedding
shape=[joint_nf]
initialization=all_zeros
requires_grad=true
```

For the bound full-atom checkpoint profile, `joint_nf=32` and the parameter
shape is `[32]`.

The injection occurs immediately after `residue_encoder(h_residues)` and before
atom/residue concatenation and time concatenation:

```python
h_residues = h_residues + (
    indicator.to(device=h_residues.device, dtype=h_residues.dtype).unsqueeze(1)
    * target_residue_atom_condition_embedding.unsqueeze(0)
)
```

The indicator is not appended to pocket one-hot features and does not change
atom, residue, joint, or EGNN input widths. It is not injected into coordinates,
edges, edge types, masks, the time channel, or coordinate-update masks. Zero
initialization gives exact initial output parity. A nonzero synthetic embedding
changes only the selected pocket hidden row at the injection point; ligand and
non-target pocket rows are not directly injected.

### Deterministic injection oracle

An earlier test oracle recovered the synthetic embedding by subtracting the
legacy hidden tensor from the conditioned hidden tensor. A random initialization
exposed a transient exact-equality failure in that oracle; rerunning unchanged
code passed. This was floating-point cancellation in the observation method,
not model-behavior drift. Although `(legacy + embedding) - legacy` equals the
embedding mathematically, the intermediate addition is rounded to the hidden
tensor dtype, so subtracting `legacy` need not recover the embedding bit for bit.

The targeted test and checker now clone the complete legacy hidden tensor, add
the embedding to the selected pocket row exactly as the model does, and compare
the complete observed hidden tensor directly with that expected tensor using
`torch.equal`. They also retain independent exact comparisons for ligand rows,
non-target pocket rows, the target row's time channel, and coordinates. This is
a stronger and deterministic oracle: it verifies every hidden value without a
subtractive cancellation step and without relaxing acceptance to a tolerance.

This oracle revision changes no model source, validator or resolver semantics,
checkpoint migration behavior, propagation path, or readiness result. The same
eight dynamics call sites remain bound, and model-consumption-gate and training
work remain outside this step.

## Top-level validation and static threading

`EnVariationalDiffusion` owns shared private resolution and validation helpers,
which `ConditionalDDPM` inherits. The resolver accepts either the pocket
dictionary field or the explicit argument. If both are present, their tensors
must be semantically equal. Neither input dictionary nor tensor is modified by
the resolver.

For a present indicator, top-level validation requires:

- tensor type, `torch.bool`, one dimension;
- length equal to pocket `x`, `one_hot`, and `mask` node counts;
- one-dimensional `torch.long` tensors for both `size` and `mask`;
- the sum of `size` equal to the flattened pocket-node count;
- `mask` blocks exactly matching the sample blocks defined by `size`;
- exactly one `True` pocket node in every sample.

`pocket["mask"]` is a tensor of integer sample IDs, not a generic numeric
array. A float or boolean mask can compare equal to integer IDs under Python
numeric equality while representing the wrong model semantics. The validator
therefore requires `torch.long` and reconstructs the expected mask with
`torch.arange` plus `torch.repeat_interleave`, then uses tensor equality.
Likewise, `pocket["size"]` is the authoritative per-sample node-count tensor and
must be nonempty `torch.long` with every size positive; integral-looking floats
and narrower integer dtypes are rejected without casting.

When dictionary and explicit condition sources are both present, each source is
validated independently as a one-dimensional `torch.bool` tensor with the same
shape before their values are compared. This ordering is required because
`torch.equal()` can report numeric equality across different dtypes, such as
`True` versus `1`. Equal bool sources still return the original dictionary
tensor, while bool/int and bool/float pseudo-equality fails closed.

All-false input, a zero-target sample in a mixed batch, multiple targets in one
sample, length drift, block drift, and explicit/dictionary conflict fail closed.
The complete per-sample cardinality scan occurs once at each top-level entry,
before normalization. Internal sampling methods do not repeat it.

The validated tensor is passed explicitly and reused unchanged at every
denoising timestep and final x/h prediction. The eight dynamics call sites are:

- `ConditionalDDPM.forward` main-t and eval-t0;
- `ConditionalDDPM.sample_p_zs_given_zt`;
- `ConditionalDDPM.sample_p_xh_given_z0`;
- `EnVariationalDiffusion.forward` main-t and eval-t0;
- `EnVariationalDiffusion.sample_p_zs_given_zt`;
- `EnVariationalDiffusion.sample_p_xh_given_z0`.

The top-level conditional paths are `forward`, `diversify`,
`sample_given_pocket`, and `inpaint`. The joint paths are `forward` and
`inpaint`. Both real `SimpleConditionalDDPM` overrides explicitly forward the
same named argument to `super()`. Unconditional joint `sample()` remains
unchanged and uses the internal default `None`.

The indicator is static metadata: it is not normalized, noised, centered,
rotated, decoded, added to `xh_pocket`, or included in reconstruction loss.

## Checkpoint profiles and migration

The bound base checkpoint is `checkpoints/crossdocked_fullatom_cond.ckpt`, size
`17861341`, SHA256
`07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c`.
Its 120 `ddpm.dynamics.*` keys strict-load into the disabled profile.

The public migration helper is:

```python
load_covapie_base_state_dict_into_target_residue_conditioned_model_v1(
    *,
    model,
    base_state_dict,
)
```

It validates that the enabled model state differs from the base state by
exactly this key:

```text
ddpm.dynamics.target_residue_atom_condition_embedding
```

It also verifies every shared shape and dtype, the enabled flag, the `[32]`
floating parameter shape, and all-zero initialization. It builds an in-memory
copy, fills only the new tensor from the current model, and calls
`model.load_state_dict(..., strict=True)`. It rejects any additional missing or
unexpected key, shared shape/dtype drift, and a nonzero new parameter. It never
uses blanket `strict=False`, reshapes old tensors, modifies the caller's base
mapping, or writes a checkpoint.

## Verification

Run the targeted suite and checker from the repository root:

```bash
pytest -q tests/test_covapie_target_residue_atom_condition_model_consumption_v1.py
python scripts/check_covapie_target_residue_atom_condition_model_consumption_v1.py
```

The checker reconstructs the frozen design response from committed baseline
sources in memory, checks the exact authorized AST method boundary, verifies the
real disabled/enabled checkpoint profiles and strict migration, exercises the
injection point, and fails before emitting facts if any readiness condition is
false.

## Readiness boundary

This implementation establishes model consumption only:

```text
model_consumption_implemented=true
indicator_passed_into_dynamics=true
indicator_consumed_by_model=true
checkpoint_migration_helper_implemented=true
repository_cli_selector_forwarding_implemented=false
model_consumption_gate_implemented=false
ready_for_model_consumption_gate=true
recommended_next_step=implement_covapie_target_residue_atom_condition_model_consumption_gate_v1
```

No training, fine-tuning, backward pass, optimizer step, parameter update, or
checkpoint write is authorized or performed. Formal training still requires a
feature-semantics audit. The historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False` state must be resolved or formally audited; the
Step12D smoke legality check is not a final training-feature contract.
