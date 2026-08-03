# CovaPIE five-module training-path completion-gap audit V1

## CovaPIE 大主线

本审计把主线固定为：

```text
authority
  → five-mask materialization
  → five formal modules
  → loader / batch / forward / loss
  → supervised training
  → Stage2 RL
```

当前只做静态缺口审计。它不读取 checkpoint，不导入 Torch，不构造模型，
不执行 forward、runtime smoke、tensorization、训练、参数更新、reward 或 RL，
也不提交或推送 Git 变更。

## 固定证据快照与生命周期

审计结论来自固定 source snapshot：

- commit: `be1add10f47911dffea4b7fdf48dcfee36d6edba`
- tree: `8bca3bd8de003f8494e7bbf996a345c0ce0421ca`
- subject: `record CovaPIE bounded repository CLI conditioned smoke terminal result v1`

仓库证据通过 `git show <source_snapshot>:<path>` 读取，而不是从未来 live
工作树读取。因此审计本身提交后，不会把自己的提交误当作新的模型证据。

审计支持三个 fail-closed 生命周期：

1. `audit_precommit_candidate`：HEAD 与 origin 都是 source snapshot，四个审计文件
   恰好是 ordinary-untracked 候选文件。
2. `audit_committed_unpushed`：HEAD 是唯一审计提交，父提交是 source snapshot，
   subject 必须精确为
   `add CovaPIE five-module training-path completion gap audit v1`，origin 仍是
   source snapshot，ahead/behind 为 1/0，工作树干净。
3. `audit_published_successor`：审计提交同时是 HEAD 与 origin 的祖先；允许未来
   与本审计四文件无关的 successor，但四个 live 文件必须与审计提交中的 blob、
   path 和 mode 完全一致。

错误 subject、parent、path 集合、mode、blob 或 live self-drift 都会拒绝。

## 五个 formal model modules

历史提交 `160cdb…`、`335a03…`、`1cdbca…` 共同约束以下五模块分类：

1. `target_residue_atom_condition_adapter`
2. `role_mask_anchor_distance_encoding`
3. `ligand_residue_atom_pair_prediction_head`
4. `pre_post_covalent_geometry_prediction_head`
5. `ligand_residue_pair_contrastive_loss`

`warhead_type_prediction` 不是 canonical module。`warhead_type_identity` 是监督
信号，其未来 consumer 可以是 optional head、condition encoding 或 evaluation-only；
这项架构选择尚未作出，也不能暗中引入第六模块。pair prediction head 与 pair
contrastive loss 是两个独立模块：后者依赖前者的 logits，但不能合并成一个矩阵。

## 八个 supervision signals

独立的信号层按以下顺序返回：

1. `warhead_type_identity`
2. `warhead_atom_set`
3. `ligand_internal_warhead_boundary`
4. `target_residue_atom_condition`
5. `ligand_atom_to_residue_atom_pair`
6. `pre_post_covalent_geometry`
7. `scaffold_linker_anchor_atom_roles`
8. `contrastive_negative_sampling_policy`

每条信号记录都含 status、authority coverage、evidence paths/commits、model
consumer、remaining gap、blocking modules 和 training-approved 布尔值。

Warhead type authority 覆盖为 11/11，但训练 vocabulary 尚未冻结、unknown-label
policy 尚未最终化、consumer placement 尚未决定，所以：

```text
WARHEAD_TYPE_SUPERVISION_MODEL_CONSUMER_UNRESOLVED
warhead_type_training_approved=false
warhead_type_consumer_resolved=false
```

11/11 authority coverage 不等于训练批准。

## canonical five-mask contract

长语义名是唯一语义来源，短别名只用于显示：

1. `warhead_only` / A
2. `linker_plus_warhead` / B
3. `scaffold_plus_warhead` / B2
4. `scaffold_only` / B3
5. `scaffold_plus_linker_plus_warhead` / C

B2 与 B3 不可互换，B3 不可省略，不允许第六或第七 mask。

## 17 维模块矩阵

每个模块都按同一 17 维顺序审计：semantic contract、source authority、schema、
label compilation、materialized dataset、loader、collate/batch、model input、head、
forward、supervised loss、loss config、checkpoint compatibility、unit tests、formal
gate、real runtime evidence、training readiness。

| Module | Complete | Partial | Missing | Blocked | N/A | Ready |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `target_residue_atom_condition_adapter` | 11 | 2 | 0 | 2 | 2 | false |
| `role_mask_anchor_distance_encoding` | 2 | 12 | 1 | 1 | 1 | false |
| `ligand_residue_atom_pair_prediction_head` | 3 | 4 | 8 | 2 | 0 | false |
| `pre_post_covalent_geometry_prediction_head` | 0 | 6 | 9 | 2 | 0 | false |
| `ligand_residue_pair_contrastive_loss` | 3 | 4 | 7 | 2 | 1 | false |

这些计数由逐维 status 重新计算，`training_ready_module_count=0` 也由矩阵结论
推导，不是把历史名称或历史计数硬编码到响应中。

### Target adapter

Current11 authority、selector/indicator schema、adapter、loader/collate、model
condition consumption、checkpoint migration 和 CLI gates 基本完整。head/output 与
独立 supervised loss 正确标为 N/A。剩余阻塞是正式 split-bound sidecar、训练配置、
Exact67 runtime evidence、unknown-atom runtime enforcement 和最终集成 revalidation。

### Role/mask/anchor-distance encoding

该矩阵继承 five-mask 证据，并扩展 per-atom roles、minimal seed、task-C anchor、
anchor distance、generated/fixed partition 和 active-region masked diffusion loss。
当前只有 warhead atom-set/boundary authority；完整 scaffold/linker/anchor roles 与
task-C anchor authority、最终 tensor materialization、active training integration 都未完成。

### Pair head

只负责 candidate tensor、positive index、pair representation、pair logits、pair-head
supervised loss 与兼容性。Current11 positive atom mapping 是 11/11，但 metadata 尚未
成为 loader/batch tensor，head、forward output 和 pair-head loss 都不存在。

### Geometry head

post-covalent bond distance 覆盖 11/11；完整 pre/post authority 为 0/11。必须先冻结
components、units、reference frame、periodicity 与 validity，再谈 tensor、head 或 loss。

### Pair contrastive loss

`335a03…` 冻结了 positive pair、同 sample deterministic negatives、ordering、offsets、
`pair_contrastive_sample_loss_mask` 和 zero-negative 行为，并明确：

```text
random_negative_sampling_allowed=false
hard_negative_mining_allowed=false
cross_sample_negatives_allowed=false
```

它没有独立 head；forward 必须依赖 pair logits。现有 loss-mask design 不是已实现的
contrastive objective。dataset tensors、leakage grouping integration、pair logits、objective、
weight 与 checkpoint policy 都仍阻塞训练。

## Feature-semantics 当前状态

必须按两个历史快照分层解释：

- `5b2013281b03d7bd3e0c59b9985e52494263c69f` 完成 final feature-semantics
  contract audit；该审计发现当时 policy 未解析。
- `160cdbda8800a535b5c0a81d501babfae9a8615b` 随后完成 unknown-atom policy
  resolution，并记录 `feature_semantics_known=true`。

因此当前冻结状态是：

```text
feature_semantics_contract_audit_completed=true
unknown_atom_policy_contract_resolved=true
feature_semantics_known_at_resolution_snapshot=true
protein_unknown_atom_policy=fail_closed_rejection_required_for_checkpoint_compatibility
ligand_unknown_atom_policy=fail_closed_rejection_required_for_checkpoint_compatibility
checkpoint_10d_channel_order_preserved=true
silent_zero_vector_fallback_allowed=false
```

仍未完成的是：

```text
unknown_atom_runtime_enforcement_integrated=false
feature_semantics_runtime_enforcement_integrated=false
canonical_mask_tensors_materialized=false
ready_for_tensorization=false
ready_for_model_integration=false
ready_for_training=false
final_training_feature_semantics_revalidation_required=true
```

所以不能再声称“feature audit 从未完成”或把历史
`feature_semantics_known=false` 当作当前状态。正确结论是：初始审计与 policy contract
已完成，但最终 loader/model integration 后仍需 runtime enforcement 和训练前 revalidation。
Step12D 只验证 smoke legality，不是最终 training-feature contract。

## Prioritized gap queue

1. P0：`role_mask_anchor_distance_encoding` 的 per-atom role、minimal seed、task-C
   anchor authority 与 five-mask materialization contract。
2. P1：target indicator split-bound sidecar。
3. P1：warhead vocabulary、unknown-label policy 与 consumer placement contract。
4. P1：pair candidates/positives/offsets/loss masks tensors。
5. P1：完整 pre/post geometry authority。
6. P2：pair head/logits/head loss。
7. P2：pair contrastive objective/weight/pair-head dependency。
8. P2：geometry head/loss。
9. P3：target-condition training config。
10. P4：runtime warning 与未来 re-execution policy；任何重执行都需要新的明确授权。

唯一推荐的下一增量仍是：

```text
resolve_covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1
```

它归属于 `role_mask_anchor_distance_encoding`，只处理 authority/schema/materialization
contract 与 fail-closed tests，不执行训练或模型改造。

## API、确定性与安全边界

唯一 public API：

```python
evaluate_covapie_five_module_training_path_completion_gap_audit_v1(
    *, repo_root: Path,
) -> dict[str, object]
```

所有失败统一为：

```text
COVAPIE_FIVE_MODULE_TRAINING_PATH_COMPLETION_GAP_AUDIT_INVALID
```

响应按固定字段顺序返回，末字段 `response_sha256` 是其余字段 canonical JSON 的
SHA256。checker 连续评估两次并要求 byte-identical；只有在 module/signal 数、feature
状态、训练/RL false、推荐项和所有 fail-closed cross-check 都成立后才打印报告。
