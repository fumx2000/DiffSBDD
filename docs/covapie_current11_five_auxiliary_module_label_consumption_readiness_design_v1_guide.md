# Current11 五个辅助模块标签消费 readiness 设计指南

## 本步回答什么

Current11 unified effective authority view 已把 11 个样本的有效人工 authority 统一到一个正式视图：`000001–000005` 和 `000011` 使用 legacy exact-one authority，`000006–000010` 使用 multi-boundary exact-two authority。该视图已经能权威回答 warhead 类型、warhead atom set 以及配体内部 warhead attachment boundary，但它并不等于可直接消费的训练标签集合。

本步只做纯内存、fail-closed 的设计审计。它不生成标签或 tensor，不实现 adapter、encoding、head 或 loss，不修改 forward、loss、data loader 或模型，也不执行训练。

## Authority view 为什么不等于训练标签

Authority view 保存的是经过评审和 precedence 选择后的事实及其 lineage。模型标签还需要冻结模型可消费的 vocabulary、unknown policy、索引空间、样本级 protein-side identity、单位、reference frame、negative sampling 与 leakage policy 等语义。`source_*_sha256`、reviewer 信息、评审决定、precedence 原因和各类 record/view digest 用于追溯与 gate；它们不能作为预测输入特征。尤其是 `precedence_reason` 只能用于审计，不能泄漏给模型。

正式训练前仍必须完成 feature-semantics audit，并解决历史 `UNKNOWN_ATOM_FEATURE_POLICY` 与 `feature_semantics_known=False` 状态。Step12D 只是 smoke legality check，不是最终训练特征合同，也不能证明生产或训练 readiness。

## 三类核心辅助监督信号

三类核心监督目标是：

1. `warhead_type_supervision`：需要把已审定的 warhead class/reaction family/rule ID 映射到冻结 vocabulary，并定义 unknown policy。
2. `ligand_atom_to_residue_atom_pair_supervision`：需要明确一个 ligand reactive atom 与一个 protein residue atom 组成的 canonical positive pair。
3. `pre_post_covalent_geometry_supervision`：需要 pair 对应的 pre/post distance、angle、dihedral，以及 units、reference frame 和 validity。

当前最成熟的是 warhead type identity 与 warhead atom set。前者在 11/11 样本都有 authority，但只有完成 vocabulary、unknown policy 和 feature-semantics audit 后才能成为训练特征；后者在 11/11 样本已经 authority-ready。

## 两种 boundary 绝不能混淆

现有 legacy 字段 `reviewed_warhead_attachment_atom_id`、`reviewed_nonwarhead_boundary_atom_id`、`reviewed_boundary_bond_id`，以及 multi 的 `reviewed_boundary_records`，描述的是：

```text
ligand warhead atom <-> ligand non-warhead atom
```

pair head 所需的却是：

```text
ligand reactive atom <-> protein residue atom
```

例如未来 Cys-SG scope 中的 ligand atom 与 residue SG。两者语义不同；`ligand_internal_boundary_is_not_ligand_residue_covalent_pair=true`。现有 ligand-internal boundary 不能被声明为 pair-head positive label。

## 八个 signal 的状态

| Signal | 当前状态 | 仍缺什么 |
| --- | --- | --- |
| `warhead_type_identity` | `authority_ready_requires_vocabulary_audit`，11/11 | class vocabulary、unknown policy、feature semantics |
| `warhead_atom_set` | `authority_ready`，11/11 | 本 authority 层无缺失 |
| `ligand_internal_warhead_boundary` | `authority_ready`，11/11 | 不得解释为 protein pair |
| `target_residue_atom_condition` | `partial_requires_additional_contract` | chain、residue name/number、insertion code、residue atom name 的 canonical 样本级合同 |
| `ligand_atom_to_residue_atom_pair` | `absent_requires_new_authority` | protein-side atom 与 canonical positive pair |
| `pre_post_covalent_geometry` | `absent_requires_new_authority` | pre/post distance、angle、dihedral、units、frame、validity |
| `scaffold_linker_anchor_atom_roles` | `partial_requires_additional_contract` | scaffold/linker/anchor/minimal-seed 的样本级 atom-role authority |
| `contrastive_negative_sampling_policy` | `absent_requires_new_authority` | positive pair ID、negative group、hard-negative 与 leakage-safe exclusion policy |

项目限定为 Cys-SG 不能替代每个样本的 canonical target condition；同样，warhead atom set 不能替代完整的 scaffold/linker/anchor atom-role partition。

## Canonical masks

权威来源是 `src/covalent_ext/covapie_tensor_label_and_loss_mask_contract_design_v1.py`，source SHA256 为：

```text
3d2d03cda56dfb4a54370444f255f9bb0ab433aaeb837901e769098272ff51ac
```

Canonical V1 精确包含五种 mask：

| Semantic name | Display alias |
| --- | --- |
| `warhead_only` | `A` |
| `linker_plus_warhead` | `B` |
| `scaffold_plus_warhead` | `B2` |
| `scaffold_only` | `B3` |
| `scaffold_plus_linker_plus_warhead` | `C` |

`scaffold_only/B3` 不可遗漏，不能增加第六或第七种 mask。短别名只用于展示，semantic long name 才是语义来源。

## 五个未来模块的依赖与结论

| 模块 | 当前可用基础 | 缺失或 partial | 结论 |
| --- | --- | --- | --- |
| `target_residue_atom_condition_adapter` | 项目级 Cys-SG scope | canonical 样本级 target residue atom condition | `partial_foundation_only` |
| `role_mask_anchor_encoding` | 五级 mask、warhead atom set、ligand-internal boundary | scaffold/linker/anchor/minimal-seed atom roles | `partial_foundation_only` |
| `covalent_pair_prediction_head` | 不能把 ligand-internal boundary 当 pair | target condition、ligand–residue positive pair | `blocked_missing_canonical_labels` |
| `pre_post_geometry_prediction_head` | 无 canonical geometry label | canonical pair、pre/post geometry contract | `blocked_missing_canonical_labels` |
| `covalent_pair_contrastive_loss` | 无可消费 sampling authority | canonical positive pair、negative sampling policy、leakage-safe grouping、pair-head semantics | `blocked_missing_canonical_labels` |

因此五个模块全部 `implementation_allowed=false`、`training_allowed=false`；`implementation_ready_module_count=0` 且 `ready_for_model_module_implementation=false`。当前不应实现 head、adapter、encoding、forward 或 loss，也不允许训练或参数更新。

## 唯一建议下一步

```text
design_covapie_target_residue_atom_condition_contract_v1
```

本步不直接实现该合同，完成审计后应停止并等待人工复审。
