# CovaPIE Current11 target-residue atom-condition authority V1

## 这一步解决什么问题

Source evidence 证明的是“此前恢复出的来源结构、原始 `_atom_site.id` 和 auth 身份有一条可复核的证据链”。Authority 则进一步证明“重新读取该来源结构后，同一个 exact `_atom_site` 行足以提供完整的条件记录”。两者职责不同，authority 消费并绑定 evidence，不改写 evidence。

正式 source evidence record 只有 13 个字段。它包含样本、PDB、来源结构 SHA、source atom-site ID、model、auth residue/atom 身份和记录摘要，但没有最终 20 字段 condition record 所需的元素类型、altloc 和 label namespace crosswalk。因此 13 字段 evidence 不能直接充当 20 字段 authority。

缺失的字段全部来自 evidence 所锚定的同一个 raw mmCIF `_atom_site` 行：

- `protein_type_symbol` 来自 `_atom_site.type_symbol`；
- `protein_label_alt_id` 来自 `_atom_site.label_alt_id`。`protein_label_alt_id=""` 只能由 exact raw 列中的显式 `.` 或 `?` 规范化得到；原始空字符串、quoted empty token 或纯空白 token 不能证明 altloc 来源，必须 fail closed；显式的 `A`、`B` 等非空 token 原样保留；
- label chain/component/sequence/atom 分别来自 `_atom_site.label_asym_id`、`label_comp_id`、`label_seq_id` 和 `label_atom_id`。

## 为什么唯一 selector 仍是 source atom-site ID

Authority 会重新读取 raw，但不会重新选择原子。唯一 selector 始终是 evidence 中冻结的 `source_atom_site_id`，且 `_atom_site.id` 必须恰好匹配一行。零行或多行都会使全部 11 个样本的构建失败。

这条边界排除了按 PDB ID 猜路径、唯一 CYS、atom name、occupancy、坐标或 nearest-neighbour 等 fallback。重新读取 raw 的目的只是复核已选 exact row 的 SHA、data block、model、auth 身份与 insertion，并从该行观察 type、altloc 和 label crosswalk。

label 字段不能从 auth 字段复制。mmCIF 的 label namespace 和 author namespace 是两套明确的数据列；即使某些样本的值碰巧相同，也必须分别从 raw 行读取。特别是 label sequence 可以与 auth sequence 不同。

## `resolved_authoritative` 和全有或全无

`resolved_authoritative` 表示该记录的 raw structure SHA、source atom-site ID 唯一性、evidence auth 身份、硫元素/CYS/SG 语义以及 label crosswalk 均已从同一 exact row 验证。它不是“推测正确”，也不是只凭 manifest 中的 ready 布尔值。

V1 不允许部分 authority。任一 sample 缺 raw、SHA 漂移、row 缺失或歧义、字段缺列、identity 漂移或 evidence/lineage 不一致时，builder 统一抛出 canonical `ValueError`，不会返回 10/11 bundle，也不会生成带空字段的 blocked record。

## 本步明确没有实现什么

Authority bundle 不是 model adapter、training label、mask 或 tensor；它也不修改模型、dataloader、forward、loss、checkpoint 或训练参数。`ready_for_target_residue_atom_condition_adapter_design=true` 只允许下一步进入 adapter design，不表示 adapter 已实现，更不表示可以训练。

正式训练前仍必须完成 feature-semantics audit。历史 Step12D 只是 smoke legality check，不是最终训练特征合同；`UNKNOWN_ATOM_FEATURE_POLICY` 和 `feature_semantics_known=False` 的历史状态仍需正式解决或审计。

## API 与输出合同

纯内存 API 为：

```python
build_covapie_current11_target_residue_atom_condition_authority_v1(
    *,
    source_formal_inventory: bytes,
    source_evidence_bundle: bytes,
    repo_root: Path,
) -> dict[str, Any]
```

它先以 predecessor compiler 重新生成 source-evidence canonical bytes，并要求与输入 evidence exact bytes 相同；随后再次运行 offline recovery evaluator，再复用其安全路径、普通文件读取、解码、mmCIF parser 和 optional-token normalization。Builder deterministic、无网络、无写入，且失败时只暴露本模块的 canonical `ValueError`。

Authority bundle 顶层恰好 20 个字段，包含冻结的 inventory、contract、source-evidence compiler、evidence bundle 和 offline recovery lineage，以及 11 条完整 authority records。每条 record 也恰好 20 个字段。record 和 bundle 摘要均使用排序键、ASCII、拒绝 NaN、紧凑 separators 的 canonical JSON，并在计算时排除自身摘要字段。

正式输出使用同目录随机临时 inode、exclusive create、文件与目录 `fsync`、hard-link no-clobber 发布。已存在且 bytes/metadata 完全相同时是 `idempotent_existing`；任何冲突或 symlink 都会 fail closed，绝不覆盖。

推荐的下一步仅为：

```text
design_covapie_target_residue_atom_condition_adapter_v1
```
