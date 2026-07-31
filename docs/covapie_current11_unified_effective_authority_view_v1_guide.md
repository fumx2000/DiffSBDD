# CovaPIE Current11 unified effective authority view V1

## 当前阶段

本阶段实现纯内存、确定性的 Current11 unified effective authority read model。它消费已经存在的 legacy V1 submission、legacy V1 execution、multi-boundary execution 和正式 multi-boundary authority bundle，返回派生 view 的 exact JSON bytes。本阶段不物化正式 view 文件。

公开 API 只有：

```python
build_covapie_current11_unified_effective_authority_view_v1(
    *,
    source_v1_submission_bundle: bytes,
    source_v1_ingestion_execution_bundle: bytes,
    source_multi_boundary_ingestion_execution_bundle: bytes,
    source_multi_boundary_authority_bundle: bytes,
    repo_root: Path,
) -> bytes
```

四份 payload 必须是 exact `bytes`，`repo_root` 必须是当前平台的 exact `Path`。Builder 不提供 CLI，也不写文件。

## Authority namespace 与 selection

Source authority 保持两个异构 namespace：

- `legacy_exact_one_boundary_v1`：legacy exact-one authority；
- `exact_two_boundaries_multi_boundary_v1`：multi-boundary Exact29 authority。

Unified view 使用 wrapper，而不是 schema flattening。每条 wrapper 的 `effective_authority_record` 都是相应 source authority 的完整深拷贝；legacy 原字段与顺序不变，multi-boundary Exact29 原字段与顺序也不变。View 不改写 source namespace，也不表示某个 source namespace 被 supersede。

Committed precedence design 是唯一 selection authority。Builder 每次只调用一次 committed reference design，并独立重算 design response digest 与 11 条 resolution digest。选择结果固定为：

- `000001`–`000005`、`000011`：6 条 legacy exact-one；
- `000006`–`000010`：5 条 multi-boundary exact-two。

Legacy source 和 multi-boundary source 均不被修改。尤其是 `000006`–`000010` 的 legacy quarantine records 仍完整保留在 legacy source execution 中；只有派生 view 选择对应 multi-boundary authority，不执行删除、unquarantine 或 source rewrite。

## Exact10 effective record

每条 derived record 精确包含以下 10 个有序字段：

1. `unified_effective_authority_record_version`
2. `sample_index_row_id`
3. `effective_authority_namespace`
4. `effective_boundary_cardinality`
5. `precedence_reason`
6. `source_resolution_record_sha256`
7. `source_authority_record_sha256`
8. `source_authority_record_version`
9. `effective_authority_record`
10. `unified_effective_authority_record_sha256`

Record version 是 `covapie_current11_unified_effective_authority_record_v1`。Resolution sample、namespace、cardinality、reason 与 effective authority digest 必须逐条匹配；source authority sample 与 digest 也必须相同。

## Exact16 view

顶层 view 精确包含以下 16 个有序字段：

1. `unified_effective_authority_view_version`
2. `source_v1_submission_bundle_filesystem_sha256`
3. `source_v1_ingestion_execution_bundle_filesystem_sha256`
4. `source_v1_ingestion_execution_bundle_sha256`
5. `source_multi_boundary_ingestion_execution_bundle_filesystem_sha256`
6. `source_multi_boundary_ingestion_execution_bundle_sha256`
7. `source_multi_boundary_authority_bundle_filesystem_sha256`
8. `source_multi_boundary_authority_bundle_sha256`
9. `source_unified_precedence_design_version`
10. `source_unified_precedence_design_response_sha256`
11. `sample_order`
12. `effective_authority_records`
13. `effective_authority_record_count`
14. `effective_legacy_exact_one_count`
15. `effective_multi_boundary_exact_two_count`
16. `unified_effective_authority_view_sha256`

View version 是 `covapie_current11_unified_effective_authority_view_v1`。Sample order 固定为 `CYS_SG_SAMPLE_INDEX_000001` 到 `CYS_SG_SAMPLE_INDEX_000011`，统计必须为 11 total、6 legacy、5 multi-boundary。

## JSON 与 digest 合同

Record 和 view 的 internal digest 排除自身 digest 字段，并使用 `sort_keys=True`、`ensure_ascii=True`、`allow_nan=False`、紧凑 separators 的 canonical JSON 后计算 SHA256。Transport 保持 insertion order，使用 `ensure_ascii=False`、`allow_nan=False`、紧凑 separators，不排序、不缩进、无 trailing newline、BOM、NUL 或 raw newline，且小于 2 MiB。

Builder 执行 strict ordered round-trip，并保证相同输入产生 byte-identical 输出。嵌入 authority 使用深拷贝；修改返回 bytes 的 decode 对象不会影响 source execution、authority bundle、其他 effective records 或下一次 build。

## 语义与训练边界

该 view 是 derived read model，不是 source authority namespace rewrite、unified gold、human gold 或 training data。本阶段只返回 bytes，不创建正式 view、unified gold、human gold、SMARTS、mask 或训练标签，也不执行训练、反向传播、optimizer step 或参数更新。该 view 不得直接用于训练。

Canonical V1 masks 仍精确为五种：`warhead_only` / A、`linker_plus_warhead` / B、`scaffold_plus_warhead` / B2、`scaffold_only` / B3、`scaffold_plus_linker_plus_warhead` / C；不得遗漏 B3，也不得增加第六或第七种 mask。

正式训练前仍必须执行 feature-semantics audit，并解决或正式审计历史 `UNKNOWN_ATOM_FEATURE_POLICY` 与 `feature_semantics_known=False` 状态。Step12D 仍只是 smoke legality check，不是最终 training-feature contract，也不能证明 training readiness。

## 唯一下一步建议

```text
materialize_covapie_current11_unified_effective_authority_view_v1
```
