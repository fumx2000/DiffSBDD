# Current11 pocket atom identity alignment V1 指南

## 这一步解决什么

Adapter design 的 `0/11` 不是数据失败。此前 11 个 target 都已通过正式 authority 解析，并且每个 `source_atom_site_id` 在对应 pocket table 中恰好出现一次；design 唯一缺少的是一条正式规则，说明 CSV 行如何对应未来 `pocket_coords` 和 `pocket_one_hot` 的节点。这个 successor 用确定性的、保持顺序的 checkpoint 词表投影补上了该规则。

本步仍不是 adapter implementation，也不是训练准备或训练。它只生成 identity-alignment sidecar 证据。

## 两种 local index

`target_source_pocket_row_index` 是 target 在 `pocket_atom_table.csv` 物理数据行中的 0-based 位置。`target_retained_model_local_index` 是只保留 checkpoint 10D 词表原子后，target 在未来模型 pocket 节点中的 0-based 位置。

两者通过完整的 `source_row_to_retained_model_local_index` 关联：保留行得到连续 local index，删除行得到 `null`。因此不能假设两个 index 总是相等。

例如源顺序为：

```text
0 known C
1 unknown H
2 target S
3 known O
```

保持顺序地删除 H 后，retained 源行是 `[0,2,3]`，映射是 `[0,null,1,2]`，所以 target 从源 index `2` 变成 retained index `1`。若 unknown 行位于 target 后方，target index 不变。

## 为什么 keep/drop 必须保持相对顺序

冻结政策是 `drop_non_checkpoint_vocab_pocket_atoms_before_checkpoint_compatible_one_hot`。它只删除 checkpoint 10D 词表之外的 pocket 原子，不对保留行进行任何重排。这样，坐标、one-hot 和未来 indicator 都能从同一 retained row 序列构建：第 `i` 个 retained identity、坐标、one-hot 和 indicator 永远描述同一个原子。

禁止按元素、坐标或残基重新排序。padded tensor 的既有 flatten 行为同样按输入 mask 顺序保留节点相对顺序。

## 为什么不用坐标匹配

坐标是数值属性，不是 atom identity。float32 转换、中心化、旋转或其他变换都可能改变数值表示；不同原子也可能在错误或合成数据中拥有相同坐标。唯一 selector 仍是 authority 的 `source_atom_site_id`，随后必须核对 PDB、元素、atom name、residue、auth/label chain 和 sequence identity。坐标最近邻和任何 CYS/SG fallback 都被禁止。

## 三类顺序摘要

每条 record 都保存 source identity、原始坐标 token 和 type-symbol 序列的顺序敏感 SHA256。identity 摘要的每项包含 source row index、atom-site ID、PDB、元素、atom/residue name、auth/label chain 与 sequence ID 以及 raw source path。坐标序列摘要使用 CSV 中未排序的 `x/y/z` 原始文本 token，因此文本层面的漂移也会被检测。

retained identity 摘要只对 order-preserving keep/drop 后的 identity 序列计算。它绑定未来模型节点的身份顺序。

## coordinate 与 one-hot byte digest

alignment bundle 不保存训练 tensor。compiler 只在内存中按 retained 顺序构造：

- little-endian、C-contiguous、shape `[retained_count,3]` 的 IEEE-754 float32 坐标 bytes；
- little-endian float32、C-contiguous、shape `[retained_count,10]` 的 checkpoint one-hot bytes。

随后只保存两者 SHA256。未来 adapter 可以按同一规则产生实际 `pocket_coords` 和 `pocket_one_hot`，再比较 byte digest，从而同时验证节点顺序、坐标转换、one-hot 宽度与元素位置。bundle 本身没有 `.pt`、`.npz`、训练 tensor 或 training label。

## Unknown filtering 不等于 feature-semantics audit

Unknown filtering 回答的是“某个元素是否能用冻结 checkpoint 10D 词表表示，以及保留节点的顺序是什么”。它不会把未知元素随意映射为 `others`，也不会更改历史 `UNKNOWN_ATOM_FEATURE_POLICY`。

Feature-semantics audit 回答更广的问题：训练输入各 feature 的最终语义是否已被正式确认。Step12D 只是 smoke legality check，不是最终训练-feature contract。因此即使 Current11 alignment 为 11/11，正式训练前的 `feature_semantics_audit_required_before_training` 仍必须为 `true`，历史 `UNKNOWN_ATOM_FEATURE_POLICY` 与 `feature_semantics_known=False` 状态仍须解决或正式审计。

## 与五级 mask 的关系

本步只处理 per-pocket-node target identity 与节点顺序，不改变 ligand mask 语义。canonical V1 仍精确包含：

1. `warhead_only` / A
2. `linker_plus_warhead` / B
3. `scaffold_plus_warhead` / B2
4. `scaffold_only` / B3
5. `scaffold_plus_linker_plus_warhead` / C

没有省略 B3，也没有添加第六或第七种 mask。五级 mask 与 pocket identity alignment 正交。

## 为什么 alignment 成功后才允许实现 adapter

若没有 alignment，adapter 即使找到正确 CSV target，也无法证明 indicator 的位置对应 checkpoint-compatible `pocket_coords` 与 `pocket_one_hot`。11/11 alignment 成功后，未来 adapter 才有唯一、可复算、可用 digest 验证的顺序合同。因此本 bundle 的下一步可以是 `implement_covapie_target_residue_atom_condition_adapter_v1`，但本步没有开始该实现。

## 为什么不修改 dataset、model、forward 或 loss

identity alignment 是数据 lineage 与顺序 sidecar，不需要改变模型架构或 checkpoint 参数形状。它也不创建 adapter 字段，所以不应提前修改 dataset、dataloader、model、forward 或 loss。保持这些路径不变既维护 checkpoint compatibility，也把本步严格限制在唯一 blocker：`pocket_table_row_order_not_bound_to_pocket_coords_and_pocket_one_hot`。

## 发布与失败关闭

public compiler 是 keyword-only、纯内存、确定性、无网络、零写入 API。正式 bundle 只有在 11/11 都为 `alignment_ready_unique` 时才能通过私有 materializer 发布。发布采用同目录 exclusive temp、0600 初始权限、partial-write loop、0644 最终权限、file fsync、重读验证、hard-link no-clobber、同 inode temp 清理和 parent fsync。

若目标已存在且 bytes 与 metadata 精确相同，结果是 `idempotent_existing`；symlink、内容冲突或 metadata 冲突均失败且绝不覆盖。任何 target 缺失、重复、identity 漂移、target 被 projection 删除、schema/坐标/投影不合法都失败关闭。

## Bundle 自摘要与冻结 lineage

Bundle 自摘要只能证明“这些字段彼此组成了一份内部一致的内容”，不能证明其中声明的 authority、adapter design、checkpoint 或 Current11 顺序就是被批准的正式 lineage。攻击者可以修改字段后重新计算自摘要；因此 materializer 前的 validator 还必须逐字段钉死 authority transport/internal/production SHA、adapter-design production/response SHA、checkpoint vocabulary policy path/SHA 以及 checkpoint path/SHA。

Current11 的正式 sample order 固定为 `CYS_SG_SAMPLE_INDEX_000001` 至 `CYS_SG_SAMPLE_INDEX_000011`。只重排 `sample_order` 必须拒绝；同时重排 `sample_order` 和 records 也必须拒绝，不能通过维持二者表面一致来改变正式 Current11 顺序。Validator 还检查 sample ID、record SHA、authority-record SHA 和 condition-evidence SHA 的唯一性，并检查所有 record lineage 摘要的格式。

Private materializer 只接受 lineage、固定顺序、record 合同与 digest 全部合法的 bundle。本次增强只收紧 fail-closed validation，不改变 projection、11 条正式 alignment、record SHA、bundle canonical bytes 或下一步建议。

## 正式 record 与 bundle digest 冻结

格式合法、保持唯一且重新签名的 record 仍不一定属于正确 lineage。例如，交换两个 sample 的合法 `source_authority_record_sha256` 后分别重算 record 与 bundle 自摘要，所有字段在格式层面仍然自洽，却已把 authority 证据绑定到错误 sample。将 retained-coordinate bytes digest 换成另一个合法 SHA 并重新签名也有同样问题。

因此 Current11 V1 不仅冻结顶层来源与 sample 顺序，还冻结 11 条正式 `pocket_atom_identity_alignment_record_sha256` 的精确序列。Bundle 的 internal SHA 和 canonical transport SHA 也必须分别等于已经独立验证的正式值。自摘要负责证明内部一致，冻结 digest 负责证明内容就是获准发布的 Current11 V1；二者缺一不可。

Private materializer 因而只接受这一份精确的正式 canonical bundle。任何 sample 集合、pocket table、checkpoint vocabulary、projection policy 或正式 record 内容的变化都应进入新版本，不能通过重新签名冒充 V1。本次修订不改变 projection、正式 11/11 alignment、正式 bundle 字节或 adapter 下一步边界。
