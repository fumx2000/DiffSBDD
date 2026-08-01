# CovaPIE target-residue atom-condition runtime bridge design V1

## 这一步设计了什么

Dataset gate 和 runtime bridge 是两个不同边界。前序 adapter gate 已证明正式 Current11 indicator 能进入 `ProcessedLigandPocketDataset`，并在 `collate_fn` 后仍是与 pocket node 对齐的扁平 `torch.bool` tensor。本设计审计的是下一段路：collated batch 进入 `LigandPocketDDPM.get_ligand_and_pocket()` 后，字段如何留在 pocket runtime dictionary 中。

当前代码会在这里停住 indicator。Dataset 和 collate 保留了
`pocket_target_residue_atom_condition_indicator`，但
`get_ligand_and_pocket()` 当前只构造 `x`、`one_hot`、`size`、`mask`，所以 indicator 尚未跨过 Lightning 边界。本步没有修改该函数，也没有实现 bridge。

## 选定的表示

V1 选择在 pocket runtime dictionary 中使用完全同名的 boolean sidecar：

```text
source batch key:
pocket_target_residue_atom_condition_indicator

destination pocket key:
pocket_target_residue_atom_condition_indicator

dtype: torch.bool
shape: [sum(num_pocket_nodes)]
domain: per_pocket_node
device: 与 pocket["x"] 相同
node order: 与 pocket["x"] 和 pocket["one_hot"] 完全相同
```

这个方案不增加第二个短别名，不改变 pocket one-hot 宽度，不改变现有函数返回值数量，也不改变 base state dict。现有 `ConditionalDDPM` 只读取 pocket 的 `x`、`one_hot`、`size`、`mask`；因此 sidecar 可以先被保存而不被模型消费。

不能把 indicator 追加到 `pocket_one_hot`。那会增加 `residue_nf`，进而改变 residue encoder 输入宽度和 checkpoint tensor shape。把目标保存成 per-sample local index 也不安全：flat collate 或 node reorder 后它不会自然与 node tensor 对齐。

## 三类存在性语义

Current11 resolved-covalent profile 要求字段存在。每个 sample 的长度必须等于 `num_pocket_nodes`，dtype 必须是 `torch.bool`，并且恰好一个值为真；真值 node 必须与正式 adapter-gate 一致。

Legacy checkpoint-compatible profile 可以完全没有这个字段。字段缺失时，未来 bridge 不应创建伪 indicator、不应创建全 False tensor、也不应猜 target。destination key 同样缺失，旧 ligand/pocket dictionary 的 shape、返回值和 state-dict 行为保持不变。

V1 不允许把“字段存在但某个 sample 全 False”静默解释成 noncovalent。当前还没有正式的 `target_condition_present`、covalent/noncovalent task identity 或 missing-label 合同，因此 `mixed_noncovalent_zero_target_semantics_deferred=true`。这只是暂缓 mixed 语义，不增加第六种 mask。

## Normalize、坐标与派生 view

`EnVariationalDiffusion.normalize()` 当前只给 `pocket["x"]` 和
`pocket["one_hot"]` 重新赋值，并返回同一个 dictionary；其他 key 会被保留。因此未来 sidecar 可以穿过 normalize，但它本身不会被归一化。

Bridge 只保存 indicator。以下值只能在 runtime 从当前 pocket tensor 派生，不应持久化：

```python
target_condition_flat_indices = torch.nonzero(indicator, as_tuple=False).flatten()
target_condition_xyz = pocket["x"][indicator]
target_condition_atom_one_hot = pocket["one_hot"][indicator]
target_condition_batch_ids = pocket["mask"][indicator]
```

这里的 xyz 使用当时已经 center/normalize 后的 pocket 坐标。identity 始终由 indicator 提供，不能反过来用浮点坐标搜索 identity。重复持久化 target xyz 或 atom one-hot 会在 centering、rotation 或 normalization 后产生漂移风险。

## 路径对称性审计

训练路径 `training_step -> forward`、validation/test 的 `_shared_eval -> forward`，以及三个 collated given-pocket 路径：

- `sample_and_analyze_given_pocket`
- `sample_and_save_given_pocket`
- `sample_chain_and_save_given_pocket`

都调用 `get_ligand_and_pocket()`。因此，在这些 collated batch 路径上，未来最小 bridge 可以共用同一个入口。

审计还发现实际存在的外部 PDB 路径
`generate_ligands -> prepare_pocket -> ConditionalDDPM.sample_given_pocket_or_inpaint`
直接构造 pocket dictionary，绕过 `get_ligand_and_pocket()`。它目前符合 legacy 字段缺失行为，但不满足“所有 given-pocket/inpainting 路径共享 bridge”的强对称条件。按 fail-closed 合同，本设计冻结：

```text
ready_for_runtime_bridge_implementation=false
recommended_next_step=resolve_covapie_external_pocket_runtime_bridge_path_coverage_v1
```

这不是 model blocker，也不是训练授权；它是下一步实施前必须明确解决或正式限定的入口覆盖 blocker。

## Bridge 仍不等于 model consumption

即使未来 indicator 被放入 pocket dictionary，`ConditionalDDPM` 和
`EGNNDynamics.forward` 当前也不会读取它。本设计没有改变 DDPM 签名、EGNN
签名、condition encoder、forward、loss 或任何参数。Bridge preservation 和
model consumption 是两个独立阶段。

V1 的 canonical mask 仍严格只有五个：

1. `warhead_only`
2. `linker_plus_warhead`
3. `scaffold_plus_warhead`
4. `scaffold_only`
5. `scaffold_plus_linker_plus_warhead`

indicator 是 pocket target identity sidecar，不是第六种 mask。

若入口覆盖 blocker 得到正式解决，预期最小 implementation 边界仍是
`lightning_modules.py` 中的 `LigandPocketDDPM.get_ligand_and_pocket()`，并配套独立测试、checker 和 guide；不得借此修改 dataset、collate、DDPM dynamics、EGNN、forward 或 loss。

最后，正式训练前仍必须执行 feature-semantics audit。历史 Step12D 只是 smoke legality check，不是最终 training-feature contract；`UNKNOWN_ATOM_FEATURE_POLICY` 和历史 `feature_semantics_known=False` 状态仍需解决或正式审计。
