# CovaPIE target-residue atom-condition adapter gate V1

## 这一步验证什么

Adapter 和 adapter gate 的职责不同。Adapter 把正式 authority 与 pocket alignment 转成每个 retained pocket node 对应的布尔 indicator；gate 不重新发明这个转换，而是独立消费三份正式 bundle，并检查这个 indicator 经过现有 `ProcessedLigandPocketDataset` 的拆分和 collate 后仍保持正确。Gate 的边界停在 dataset runtime，不连接模型。

Gate 必须重新调用正式 adapter builder，并用 adapter 自己的 canonical serializer 生成 bytes，再与输入 adapter bundle 做逐字节比较。只比较内部 SHA 不够，因为不同编码、非 canonical JSON 或额外传输字节可能表达相似对象，却不是已经批准的正式工件。Exact-byte binding 同时证明 gate 使用的是同一份 authority、alignment 与 adapter 生产逻辑。

## 为什么重新构建 retained pocket arrays

Indicator 的 local index 只有绑定到正式 retained pocket 顺序才有意义。因此 gate 重新运行 alignment compiler，读取 11 份正式 pocket atom table，验证各自 SHA，并严格按 `retained_source_pocket_row_indices` 的既有顺序取行。它不排序、不重新匹配，也不靠坐标寻找 target。

所选行被重新编码为 little-endian float32 coordinates（宽度 3）与 checkpoint-compatible one-hot（宽度 10）。两组 bytes 都必须匹配 alignment record 的冻结摘要。Target 行还必须是硫原子 `S`，在正式 checkpoint vocabulary 中对应 feature index 3。这个检查把 indicator 位置绑定到原子身份和 checkpoint 特征语义，而不是绑定到可能重复或受舍入影响的坐标。

## 为什么使用全 Current11 临时 NPZ

双样本 synthetic fixture 只能发现简单的 split 问题，不能证明 11 个不同 pocket 长度的完整 prefix-sum、sample order 和末端边界都正确。Gate 因而把所有 Current11 样本放入同一个临时 NPZ：每个样本仅配一个确定性的 dummy ligand node，而 pocket coordinates、pocket one-hot 和 indicator 全部来自正式重建结果。

这个 NPZ 位于系统临时目录，并在 public API 返回前连同临时目录一起删除。它只是把数组送入现有 loader 的短生命周期 runtime 容器，不是正式数据物化；它不会进入仓库、`data/derived`、`covapie-state` 或 manual-review，也不会留下训练 tensor。

## Local index 与 collated flat index

`target_retained_model_local_index` 是 target 在单个样本 retained pocket 中的位置。例如第二个样本的 local index 是 15。Collate 会把 11 个 pocket 顺序拼接，因此它的 flat index 是前面所有 pocket node 数的 prefix sum 加 local index；第二个样本的 flat index 是 `66 + 15 = 81`。Gate 实际计算 prefix sum，并确认正式 flat indices 为：

```text
49, 81, 182, 299, 505, 712, 988, 1260, 1516, 1766, 2058
```

## Dataset 与 center 不变性

Gate 通过 `importlib` 实际加载现有 `dataset.py`，分别用 `center=False` 和 `center=True` 实例化 `ProcessedLigandPocketDataset`，再调用其真实 `collate_fn`。它检查每个 indicator 的 `torch.bool` dtype、长度、唯一真值位置，以及 collated 后的总长度、真值数量、names、receptors 和 pocket one-hot 宽度。

单样本 pocket 顺序正确，加上 collated indicator 顺序正确，仍不能自动证明 collated pocket arrays 没有被重排：错误的 collate 实现理论上可以只重排 coordinates 或 one-hot，而保留 indicator。Gate 因而先按正式 sample 顺序建立唯一的 expected concatenation，并要求 collated pocket coordinates 和 pocket one-hot 的完整 little-endian float32、C-contiguous ordered bytes 分别精确相等。Shape、sum 或无序集合比较都不足以证明 node-order binding。

每个 collated flat true index 还会重新索引 collated pocket one-hot；该行必须只有 feature index 3 为 `1.0`，且行和为 `1.0`。这证明 flat indicator 与对应的硫原子行仍绑定，而不是仅仅各自拥有看似正确的总数。验证仍不使用坐标匹配。

Centering 只应平移 coordinates。Indicator 和 one-hot 表示节点身份与特征，不是空间量，所以 `center=True` 前后的每样本 indicator bytes、真值位置、collated indicator、collated pocket one-hot 及节点顺序必须完全不变。Gate 不要求居中后的坐标仍匹配原始 coordinate digest，因为平移本来就会改变坐标 bytes。

这项 collated node-order 修订只加强运行时验证，不增加 record 或 bundle 字段，也不改变 digest 算法或任何正式数据结果。因此 11 条正式 gate record SHA 与正式 gate bundle bytes 保持不变。

## 明确不做的事情

Gate 不把 `pocket_target_residue_atom_condition_indicator` append 到 `pocket_one_hot`，不改变 `atom_nf`、`residue_nf` 或 `joint_nf`，也不改变 base state-dict key 或 checkpoint tensor shape。它不修改 dataset、dataloader、NPZ writer、Lightning、EGNN、ConditionalDDPM、forward 或 loss；不调用 model forward、backward 或 optimizer step；不创建 training label，也不训练或 fine-tune。

五级 canonical mask 仍精确是 `warhead_only`、`linker_plus_warhead`、`scaffold_plus_warhead`、`scaffold_only`、`scaffold_plus_linker_plus_warhead`。Target-residue indicator 是独立的 per-pocket-node runtime 字段，不是第六个 mask，因此 adapter gate 不改变 mask contract，尤其不会遗漏 `scaffold_only`。

## 通过以后仍然需要什么

Gate 通过只证明现有 dataset split、dtype、collate 顺序和 flat target 位置可以承载该字段。下一步是 `design_covapie_target_residue_atom_condition_runtime_bridge_v1`：先设计 indicator 如何越过 dataset 边界，再决定是否以及怎样接入后续 runtime。当前步骤没有实现 runtime bridge。

正式训练前仍必须完成 feature-semantics audit。历史 `UNKNOWN_ATOM_FEATURE_POLICY` 与 `feature_semantics_known=False` 状态不能由一次 runtime gate 消除；Step12D 也只是 smoke legality check，不是最终训练特征合同。因此 dataset gate、sampling、checkpoint load 或单步 smoke 均不得被解释为 training readiness。
