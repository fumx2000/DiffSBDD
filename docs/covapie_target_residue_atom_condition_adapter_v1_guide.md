# CovaPIE target-residue atom condition adapter V1 指南

## Alignment 与 adapter 的区别

Alignment 回答“正式 pocket atom table 的哪一行，在 checkpoint-compatible 投影后对应哪个 retained model-local node”。它绑定原子身份、原始行顺序、投影规则，以及 retained pocket 的坐标和 one-hot byte digest。Adapter 不再进行身份或坐标匹配；它只消费 alignment 已确定的 `retained_pocket_node_count` 与 `target_retained_model_local_index`，生成现有 dataset 能携带的布尔字段。

因此本步没有坐标匹配、唯一 CYS/SG fallback、PDB index 猜测或节点重排。Alignment 若不是正式 compiler 的 canonical exact bytes，adapter 会 fail closed。

## Indicator 如何生成

对每个样本，先创建长度为 `retained_pocket_node_count` 的全 `False` 列表，再把 `target_retained_model_local_index` 位置设为 `True`：

```python
indicator = [False] * retained_pocket_node_count
indicator[target_retained_model_local_index] = True
```

输出字段名是 `pocket_target_residue_atom_condition_indicator`。它是 `per_pocket_node`、NumPy `bool`、PyTorch `torch.bool`，单样本形状为 `[num_pocket_nodes]`。每条正式记录的长度必须等于 retained node 数，必须且只能有一个 `True`，且真值位置必须等于 alignment 给出的 retained local index。

Source CSV row index 不能直接使用，因为 checkpoint vocabulary 投影会丢弃不受支持的 pocket atoms；原始表行号与 retained model-local node index 并不相同。只有 alignment 的 order-preserving projection 映射具有这里需要的语义。

## 为什么字段名不能含 `lig` 或 `mask`

现有 `ProcessedLigandPocketDataset` 对不含 `lig` 的字段使用 `pocket_mask` 边界拆分，所以该字段会按 pocket node 边界拆成单样本序列。Collate 对名称含 `mask` 的字段会重建 batch membership index；indicator 不是 membership mask，因此名称刻意不含 `mask`，collate 会按原顺序直接拼接并保留 `torch.bool` dtype。

临时双样本 NPZ 验证确认：单样本长度分别等于各自 `num_pocket_nodes`，collated shape 为所有 pocket node 数之和，样本边界与两个真值位置均保持不变。无需修改 `dataset.py`。

## 为什么不重复保存坐标或 one-hot

Adapter record 不保存 `pocket_coords`、`pocket_one_hot`、`target_xyz` 或 `target_atom_one_hot`。未来若运行时 gate 与模型接线获得正式授权，可从同一批 pocket 数据派生：

```python
target_condition_xyz = pocket_coords[indicator]
target_condition_atom_one_hot = pocket_one_hot[indicator]
```

这样不会制造第二份可能漂移的坐标或特征来源。Alignment 已保留坐标与 one-hot 的 byte digest；adapter 的 indicator digest 只绑定布尔选择序列，不替代那些 lineage digest。

Indicator digest 的编码固定为：按 indicator 顺序把 `False` 编码为一个 uint8 `0` byte，把 `True` 编码为一个 uint8 `1` byte，然后对连续 bytes 计算 SHA256：

```python
sha256(bytes(1 if value else 0 for value in indicator))
```

## Checkpoint compatibility 与模型边界

本步生成的是额外 batch key，没有追加到 `pocket_one_hot`，没有改变 `atom_nf`、`residue_nf` 或 joint feature width，也没有新增 base-model parameter、state-dict key 或 checkpoint tensor shape。`EGNNDynamics`、`ConditionalDDPM`、`LigandPocketDDPM`、forward 和 loss 均未修改。

现有模型消费的 key 保持不变；indicator 在本步不会传入模型，也不会触发 model forward、backward、optimizer step、训练或 fine-tune。正式 checkpoint 仅作为既有兼容性边界被验证，未被重新保存。

## 五级 mask 为什么共用同一个 protein indicator

Canonical V1 mask 合同仍精确包含五种语义：

1. `warhead_only`
2. `linker_plus_warhead`
3. `scaffold_plus_warhead`
4. `scaffold_only`
5. `scaffold_plus_linker_plus_warhead`

这些 mask 描述 ligand 侧不同生成/保留区域；target-residue protein atom 的身份不随 ligand mask 改变。因此五种任务共用同一个 per-pocket-node protein indicator，不增加第六种 mask，也不按 mask 复制 indicator。

## Adapter 完成后仍需 gate 与 feature-semantics audit

本 bundle 证明正式 authority、正式 alignment 与布尔 adapter 记录可以确定性连接，并建议下一步为 `implement_covapie_target_residue_atom_condition_adapter_gate_v1`。Gate 尚未实现；它需要独立核验正式发布产物及后续接线是否满足 fail-closed 条件，不能由本步的 builder/test 自证替代。

正式训练前仍必须进行 feature-semantics audit。历史 Step12D 只是 smoke legality check，不是最终训练特征合同；历史 `UNKNOWN_ATOM_FEATURE_POLICY` 与 `feature_semantics_known=False` 状态仍需解决或正式审计。Dataset 兼容、bundle 物化、checkpoint loading 或单步 smoke 都不能推出训练 readiness。
