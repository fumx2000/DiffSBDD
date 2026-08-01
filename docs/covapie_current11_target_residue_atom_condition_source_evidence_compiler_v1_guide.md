# Current11 target-residue atom-condition source-evidence compiler v1

## 这一步做什么

offline source recovery 回答的是“现有本地原始结构能否为每个 Current11 样本唯一找回目标原子，并把来源链验证完整”。它负责读取冻结的 source inventory、raw mmCIF、locator sidecar 和 protein atom table，验证 exact bytes、唯一 `_atom_site` 行、蛋白表绑定、CYS/SG identity 与 insertion provenance。

source-evidence compiler 回答的是“如何把 recovery 已经验证通过的结果整理成一个稳定、可追溯的正式 evidence bundle”。它调用已提交的 recovery evaluator，严格检查 Exact14 response、11 条 recovery record 及所有冻结 SHA，然后逐条复制 `proposed_condition_evidence_record`。它不自行选择原子，也不改变 recovery 的结论。

## 为什么只复制 proposed evidence

每条 proposed evidence 已经绑定 sample、PDB/ligand、raw structure filesystem SHA、唯一 atom-site ID、model、auth residue/atom 和 insertion。compiler 原样复制这些字段，可以保持 recovery 与正式 bundle 之间一对一的摘要链，避免第二套实现产生不同解释。

因此 compiler 不重新解析 raw mmCIF，也不实现另一个 atom selector。解析和选择只属于冻结的 offline recovery evaluator；compiler 只验证其 production bytes、response digest、record digest 和 evidence digest。正式 source inventory 也保持 exact bytes 不变：它是 recovery 的输入证据，不是 compiler 的输出模板。

## insertion 空字符串的含义

`protein_pdbx_PDB_ins_code=""` 不是缺省填值。offline recovery 必须先观察并核对 `_struct_conn`、`_atom_site` 和 provider projection 中的显式 `.` 或 `?` token；只有 provenance 完整一致时，才把该 token 规范化为空字符串。compiler 保留 recovery 给出的空字符串，不重新推断。

## evidence 不是 authority

bundle 中的 13 字段 record 是 source evidence，不是 target-residue atom-condition authority。它没有 authority、label、warhead、mask 或训练字段，也不是 adapter 或 tensor。`ready_for_target_residue_atom_condition_authority_materialization=true` 只说明下一步可以消费这份 evidence；它不在本步创建 authority。

## lineage 如何追溯

顶层 lineage 从正式 bundle 依次指向：

1. `source_formal_inventory_transport_sha256` 和 `source_formal_inventory_sha256`：冻结 inventory 的 exact bytes 与内部摘要；
2. `source_offline_recovery_production_sha256`：执行 raw recovery 的已提交 Python 源文件；
3. `source_offline_recovery_design_response_sha256`：完整 Exact14 recovery response；
4. `source_offline_recovery_record_sha256s`：按 `CYS_SG_SAMPLE_INDEX_000001` 至 `000011` 排列的 11 条 recovery record；
5. 每条 `condition_evidence_record_sha256`：从对应 recovery record 原样复制的 evidence。

`source_evidence_bundle_sha256` 使用 sorted-key canonical JSON 计算并排除自身字段。正式 JSON 也使用相同 canonical encoding，无 BOM、NUL 或 trailing newline。

## API 与安全发布

公开 API 是 keyword-only 的纯内存函数：

```python
compile_covapie_current11_target_residue_atom_condition_source_evidence_v1(
    *, source_formal_inventory: bytes, repo_root: Path
) -> dict[str, Any]
```

compile 不写文件、不依赖当前工作目录，也不修改输入或 predecessor 常量。私有 materialization helper 只用于受控发布：同目录独占临时文件、`fsync`、hard-link no-clobber；目标已存在时只接受 metadata 合法且 bytes 完全相同的幂等结果，冲突不会覆盖。

## 下一步和训练门禁

下一步可由 `implement_covapie_current11_target_residue_atom_condition_authority_v1` 读取正式 bundle，复验所有 lineage 与 record digest，再建立 target-residue atom-condition authority。authority 的 schema、消费规则与失败边界应在下一步单独定义，本 compiler 不预先实现。

即使 evidence bundle 和后续 authority 都通过，正式训练前仍必须进行 feature-semantics audit。历史 Step12D 只是 smoke legality check，不是最终训练特征合同；`UNKNOWN_ATOM_FEATURE_POLICY` 与历史 `feature_semantics_known=False` 状态仍须解决或正式审计。不得从本 bundle 推断训练 readiness，也不得据此开始 fine-tune、backward、optimizer step 或任何参数更新。
