# CovaPIE target-residue atom-condition runtime bridge V1

本步实现的是 sidecar preservation，不是 model consumption。换句话说，target-residue indicator 现在能随 pocket runtime dictionary 穿过数据与外部 Python API 边界，但 DDPM、EGNN、forward、loss 和任何模型参数都不会读取它。

## Collated batch 到 pocket dictionary

当 collated batch 含有 `pocket_target_residue_atom_condition_indicator` 时，`LigandPocketDDPM.get_ligand_and_pocket()` 会先验证它已经是与 pocket node 一一对齐的一维 `torch.bool` tensor。它还会交叉检查 `pocket_mask` 与 `num_pocket_nodes`，要求每个 sample 精确有一个 `True`。验证成功后，同名字段进入 pocket dictionary；原有 `x`、`one_hot`、`size`、`mask` 不变。

字段缺失时保持 legacy 行为，不创建全 `False` tensor。全 `False` 不能表达“旧 caller 没提供语义”和“已确认没有 target”之间的区别，而且会掩盖缺失条件，因此这里必须保持 key absent。

正式 Current11 是 11 个已解析 covalent sample，所以每个 sample 必须有且仅有一个 target。它们拼接后共有 2202 个 pocket nodes、11 个 `True`；这个 cardinality 约束同时防止 target 丢失、重复和跨 sample 错位。

## 外部 PDB selector

`generate_ligands()` 现在显式接收 `target_residue_atom_condition_spec`，并只把它传给 `prepare_pocket()`。V1 selector 必须是 Exact6 dict：`chain_id`、`residue_sequence_number`、`residue_insertion_code`、`residue_name`、`atom_name`、`element`。其中 insertion code 只能是单个空格，目标语义固定为 `CYS`、`SG`、`S`。

定位只发生在 `prepare_pocket()` 已按既有 full-atom 规则构建的真实 `pocket_atoms` 列表中。定位同时匹配 chain、标准 residue id 三元组、residue name、atom name 和 element，并要求精确一个结果。坐标、PDB atom serial、用户 local index、最近 reference ligand、自动推断唯一 CYS/SG 都不参与 identity；target 不在 selected pocket 时也不会自动追加。

selector 存在时必须使用 `full-atom` pocket。CA representation 没有 SG atom node，若接受 selector 就无法让 indicator 与真实 node identity 对齐，因此会 fail closed。disordered residue、disordered atom、非空 altloc 和 checkpoint pocket vocabulary 缺少 `S` 也会被拒绝。

## Repeat 与采样分支

目标首先在单个基础 pocket block 中形成一个 `True`，随后用完整 block 顺序执行 `base_indicator.repeat(repeats)`。这与 `pocket_coord.repeat(repeats, 1)`、`pocket_one_hot.repeat(repeats, 1)` 和 pocket mask 的 sample 排列完全一致，所以 `pocket["mask"][indicator]` 必须等于 `arange(repeats)`。

conditional generation 和 inpainting 都接收 `prepare_pocket()` 返回的同一个 pocket 对象，因此携带同一 sidecar。selector 是显式 API 参数，不进入 `**kwargs`，也不会传给 DDPM sample 或 inpaint 参数。

indicator 不追加到 `pocket["one_hot"]`。追加会改变 feature width、模型维度和 checkpoint tensor shape，把本步越界变成模型架构变更；同名 sidecar 能在不改 state dict 的前提下保存语义。

## 本步边界和后续工作

本步不修改 CLI、batch CLI 或 notebook caller。外部 Python API 已具备显式 selector surface，但 repository caller 如何采集并转发 Exact6 selector 是独立接口工作，不应在 runtime bridge 中隐式猜测。

修改前的 external path resolution、runtime bridge design 和 adapter gate 精确冻结了旧 `lightning_modules.py` SHA。它们在授权源码改变后按设计不再是 post-change 绿色回归，不能通过修改旧 SHA、旧 bundle 或旧测试来“修复”。本步改用新的 targeted tests、checker，以及不依赖旧 Lightning SHA 的后续回归证明实现边界。

checker 中的 `BASE_COMMIT` 是授权源码差异的比较基线，不是永久要求当前 `HEAD` 停留的位置。未提交时 `HEAD` 可以与它相等；产生正常单父实施 commit 后，`BASE_COMMIT` 应当是新 `HEAD` 的祖先。因此 post-commit 检查使用 `git merge-base --is-ancestor`，而不是比较 `HEAD == BASE_COMMIT`。旧 source-freeze 套件仍只作为实施前证据，不会在提交后改写成新源码合同。

Legacy repository caller 的兼容性也不是写死的布尔结论。checker 会逐个核验 `generate_ligands.py`、顶层测试/优化/inpaint caller、demo 和 notebook 的冻结 SHA，并拒绝绝对路径、路径穿越、symlink、缺失文件和内容漂移。本次 lifecycle 修订只增强 checker、tests 和说明文档，runtime bridge 实现内容保持逐字节不变。

下一步应独立实现 `implement_covapie_target_residue_atom_condition_runtime_bridge_gate_v1`，用新的 successor gate 固化本步 runtime 证据；本步不会提前创建或改写该 gate。

最后，Step12D 仍只是 smoke legality check，不是最终 training-feature contract。正式训练、微调、backward、optimizer step 或参数更新之前仍必须完成 feature-semantics audit，并正式解决或审计历史 `UNKNOWN_ATOM_FEATURE_POLICY` 与 `feature_semantics_known=False` 状态。dataset materialization、QA、sampling、checkpoint loading 和本 runtime bridge 都不能单独证明 training readiness。
