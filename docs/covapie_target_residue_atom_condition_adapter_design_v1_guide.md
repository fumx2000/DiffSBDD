# CovaPIE target-residue atom-condition adapter design V1

## 本步结论

本步只冻结数据接口、identity mapping 边界和 checkpoint compatibility 合同，不实现 adapter、gate、tensor、forward 或 loss。推荐的唯一 model-consumable 字段是：

```text
pocket_target_residue_atom_condition_indicator
```

它是与 pocket 节点一一对齐的布尔数组。Current11 的 11 份 pocket atom table 都能用 authority 的 `source_atom_site_id` 唯一找到目标原子，但仓库中没有证据证明这些 table 的行序就是未来 `pocket_coords` / `pocket_one_hot` 的节点顺序。因此正式结果是：

```text
current11_unique_mapping_count=0
current11_blocked_mapping_count=11
ready_for_adapter_implementation=false
recommended_next_step=implement_covapie_current11_pocket_atom_identity_alignment_v1
```

这里的 0/11 并不否定 authority 或 pocket table 中的唯一 identity；它表示尚未完成最后一段“pocket table 行号到 model pocket node 行号”的可证明绑定。

## Authority 和 adapter 的区别

Authority 回答“目标蛋白原子是谁”。每条正式记录包含 sample、PDB、model、auth/label residue identity、atom identity、`source_atom_site_id`、结构与证据 SHA，以及 authority record SHA。它是身份和 lineage 的审计事实。

Adapter 将这个身份映射到某个具体样本的 pocket node。只有证明 pocket identity table 的第 `i` 行与 `pocket_coords[i]`、`pocket_one_hot[i]` 是同一个原子，adapter 才能令 indicator 的第 `i` 位为 true。

Authority 的 20 个字段不能直接塞进 model。PDB 标识、字符串 SHA、auth/label 标识用于审计，不是数值 node feature；把它们混入 tensor 会引入 object/string array、无定义的编码语义和 checkpoint shape 变化。设计把输出分为：

- model-consumable numeric field：仅 indicator；
- audit-only mapping sidecar：保留完整 identity、lineage、match count、row-order binding、status 和 digest。

本步只设计 sidecar schema，不物化 sidecar。

## 当前 dataset、collate 和 model 接口

对仓库 exact bytes 的审计确认：

- `dataset.py` 对 `names/receptors` 以外字段，字段名含 `lig` 时按 `lig_mask` 切分，否则按 `pocket_mask` 切分。
- 同一文件的 `collate_fn` 对字段名含 `mask` 的字段重建 batch membership index；它不是简单拼接原始布尔值。
- 因而 condition 字段名不能含 `mask`，也不能错误包含 `lig`。它必须是 per-pocket-node array，不能是不受支持的 per-sample scalar，也不能是 string/object numpy array。
- `LigandPocketDDPM.get_ligand_and_pocket` 当前只给 ligand 和 pocket 构造 `x`、`one_hot`、`size`、`mask`。
- `ConditionalDDPM` 直接拼接 pocket `x` 和 `one_hot` 后传给 dynamics，没有独立 target-condition 参数。
- `pocket_one_hot` width 进入 `residue_nf`，而 `EGNNDynamics.residue_encoder` 的第一层输入宽度就是 `residue_nf`。

因此新增一个尚未被 model 消费的额外 batch key，不会改变现有 parameter/state dict；未来真正消费 indicator 的 gate 或 sidecar 路径必须另立设计和 checkpoint-compatibility gate。

## 推荐 representation

推荐 indicator 的合同为：

```text
storage domain: per-pocket-node
numpy dtype: bool
torch dtype: torch.bool
sample shape: [num_pocket_nodes]
batch shape: [sum(num_pocket_nodes)]
```

Current11 resolved covalent sample 每个 sample 必须恰好一个 true。未来显式 noncovalent sample 可以是零个 true；若 authority 声明 covalent/resolved，零个 true 必须失败；多于一个 true 总是失败。不得用“第一个 CYS”“唯一 SG”或 atom name 作为 fallback。

候选方案决策如下：

| 候选 | 决策 | 原因 |
|---|---|---|
| 向 `pocket_one_hot` 追加 channel | 拒绝 | 改变 `residue_nf` 及 checkpoint parameter shape |
| per-sample local index | 拒绝 | 当前 collate 不支持该 scalar 语义，且 node reorder 后脆弱 |
| per-sample target xyz | 拒绝 | 重复坐标会在 centering/rotation/transform 后漂移 |
| 坐标匹配 | 拒绝 | 浮点坐标不是 identity |
| per-pocket-node indicator | 接受 | 保持 node alignment，且不改变 feature width |
| 修改 EGNN state dict | 拒绝 | 破坏 base checkpoint compatibility |
| 独立 sidecar/gate | 接受 | 将 lineage 审计与 model numeric field 分离 |

## 为什么不重复存 target xyz 或 one-hot

Target atom coordinates 不作为独立 NPZ 字段。未来在 indicator cardinality 已验证后，从当前 tensor 动态派生：

```text
target_condition_xyz = pocket_coords[indicator]
target_condition_atom_one_hot = pocket_one_hot[indicator]
```

Pocket coordinates 可能已 center，之后也可能 rotation 或接受其他 transform。重复保存一份 xyz 很容易与实际 pocket tensor 漂移。Indicator 随 pocket node 顺序和相同 transform 保持一致：authority 管 identity，pocket tensor 管当前坐标。Target atom one-hot 同理从相同 node 读取，不重复保存。

其余 runtime views 也不持久化：

```text
target_condition_present
target_condition_local_index
target_condition_flat_index
target_condition_xyz
target_condition_atom_one_hot
```

这些值只能在 indicator cardinality 验证通过后派生。本步没有实现这些计算。

## Identity mapping 和 row-order 证据

首选且唯一 selector 是 `source_atom_site_id`，并交叉验证 authority 的完整 auth/label identity、model、altloc、insertion、元素和 source structure SHA。禁止以下猜测：

- 坐标最近邻或浮点 exact equality；
- 唯一 CYS、唯一 SG 或 atom-name fallback；
- 单字段 residue number；
- occupancy fallback；
- 按 PDB ID 猜节点位置。

Current11 的统一 sample index 指向 11 个 `pocket_atom_table.csv`。每份 table 中目标 `atom_site_id` 的 match count 均为 1，并能通过其 `source_raw_file` 回到 frozen mmCIF，验证完整 authority identity 和 source structure SHA。不过当前 NPZ writer、loader、batch adapter 与 feature projection 路径没有把这些 Current11 pocket table 行序绑定为 `pocket_coords/pocket_one_hot` 行序。历史三样本 pocket table 和历史 tensor 路径也不能替代 Current11 的绑定证据。

因此 proposed local pocket indices 只能作为 alignment 下一步的候选，不能生成 indicator：

```text
000001=88  000002=25  000003=19  000004=39  000005=37  000006=50
000007=48  000008=53  000009=52  000010=53  000011=84
```

只有独立 manifest 或同等直接证据证明：

```text
pocket atom table row order
== pocket_coords node order
== pocket_one_hot node order
```

才可把相应 record 提升为 `mapping_ready_unique`。仅有 full-protein atom table 或 authority 11/11 不足以宣称 adapter implementation ready。

## 五级 ligand mask 与 protein condition 正交

Canonical V1 仍然只有五个 mask。长语义名是 source of truth，短别名只用于显示：

| Long semantic name | Alias | 使用的 protein target condition |
|---|---:|---|
| `warhead_only` | A | 同一个 indicator |
| `linker_plus_warhead` | B | 同一个 indicator |
| `scaffold_plus_warhead` | B2 | 同一个 indicator |
| `scaffold_only` | B3 | 同一个 indicator |
| `scaffold_plus_linker_plus_warhead` | C | 同一个 indicator |

Target condition 描述蛋白目标原子，mask level 描述 ligand 编辑区域，两者正交。不得增加第六种 mask，不得按 mask level 改变 target atom identity，`scaffold_only` / B3 不得遗漏。

## Checkpoint compatibility 决策

V1 冻结：

```text
append_to_pocket_one_hot=false
change_atom_nf=false
change_residue_nf=false
change_joint_nf=false
modify_EGNNDynamics=false
modify_ConditionalDDPM=false
modify_LigandPocketDDPM=false
new_base_model_parameter=false
base_state_dict_key_change=false
base_checkpoint_tensor_shape_change=false
```

冻结 checkpoint 为 `checkpoints/crossdocked_fullatom_cond.ckpt`，size `17861341`，SHA256 `07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c`。本步只读验证 bytes，没有加载后保存 checkpoint。

不修改 forward/loss 的原因很直接：本步只回答“未来数据字段是什么、身份怎样可靠映射、现有 checkpoint 怎样保持不变”。如何让模型消费 target condition 会涉及新的计算语义、gate、forward path 和 checkpoint compatibility，超出本步授权。

## 实际审计的路径与 SHA256

四个强制 runtime 文件：

| Path | SHA256 |
|---|---|
| `dataset.py` | `d1c548185521692ca14be062e34d5bea617f8d3c89a22eaef4ddb13a52907c99` |
| `lightning_modules.py` | `2b771068eda19b6f783e12ff483a02ab6ef8264108f3af5e486d3381fb1e7fb6` |
| `equivariant_diffusion/dynamics.py` | `16b008598de7c61c0b5575e3af02f9b1a9e6697559864df1591314e4b4ec6b9f` |
| `equivariant_diffusion/conditional_model.py` | `260bb941e05a3beaa0f1aef7aebba86aa2474d5f5db75637ec1498e3ad0e47b4` |

Preprocessing、identity/order、collate 和 checkpoint smoke 的实际生产路径包括：

| Role | Paths |
|---|---|
| NPZ writers | `process_crossdock.py`, `process_bindingmoad.py`, `scripts/materialize_training_tensor_npz_v0.py` |
| Current11 pocket producers | `src/covalent_ext/covapie_sample_preparation_execution_smoke.py`, `src/covalent_ext/covapie_independent_group_expansion_batch_sample_preparation_execution_smoke.py` |
| Current11 sample index | `data/derived/covalent_small/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/unified_sample_index.csv` |
| Historical full-atom/pocket | `src/covalent_ext/real_covalent_confirmed_candidate_full_atom_extraction_smoke.py`, `src/covalent_ext/real_covalent_confirmed_candidate_pocket_extraction_smoke.py` |
| Tensor/batch conversion | `src/covalent_ext/npz_dataset.py`, `src/covalent_ext/diffsbdd_input_adapter.py`, `src/covalent_ext/real_covalent_feature_semantics_audit_debug.py` |
| Collate/pocket tests | `tests/test_training_tensor_npz_dataloader_v0.py`, `tests/test_real_covalent_confirmed_candidate_pocket_extraction_smoke_v0.py` |
| Checkpoint-compatible smoke | `src/covalent_ext/checkpoint_compatible_pretrained_load_smoke.py`, `tests/test_checkpoint_compatible_instantiation_wrapper_v0.py` |

Production response 的 `current_runtime_interface_records` 冻结上述每个路径的 exact SHA；任何漂移都 fail closed。11 个 Current11 pocket table 的 path 与 SHA 则逐条记录在 mapping audit 中。

## Exact20 reference response

私有、keyword-only API：

```python
_reference_design_covapie_target_residue_atom_condition_adapter_v1(
    *,
    source_authority_bundle: bytes,
    repo_root: Path,
) -> dict[str, Any]
```

它是 deterministic、纯内存、零写入、无网络，不修改输入，不返回 `Path`。所有异常统一为 canonical `ValueError`。Response 按任务中名字虽称 Exact19、实际明确的 20 个字段实现；最后一个字段是排除自身后 canonical JSON 的 SHA256。

## 训练边界

这份设计不表示训练已准备好。Step12D 只是 smoke legality check，不是最终 training-feature contract。正式训练、fine-tuning、backward、optimizer step 或 parameter update 前仍必须执行 feature-semantics audit，并正式解决或审计历史 `UNKNOWN_ATOM_FEATURE_POLICY` 和 `feature_semantics_known=False` 状态。Pocket identity alignment、adapter implementation、未来 condition-consumption gate 与 feature semantics audit 是不同的后续步骤，不能互相替代。
