# CovaPIE completed human decision reconciliation with PRF V1

## 目的与继承关系

本 successor 把 frozen PRF Exact8 formal human decision 纳入当前 completed-human-decision reconciliation。它只提供 metadata-only、read-only、in-memory reconciliation；不修改 historical CSV，不生成 CSV、JSON、manifest、snapshot、transition artifact 或 census，也不创建 model/training authority。

generic predecessor 仍是 historical parser、`SourceBinding`、`NormalizedCompletedDecisionFact`、`NormalizedDecisionSource`、`ReconciliationResult`、source ordering、collision、review-unit coverage、overlay 与 review summary 的唯一 owner。PRF successor 不复制这些类型或算法。PRF formal decision 只通过 frozen PRF ingestion owner 的 `load_frozen_formal_decision_v1(repo_root)` 加载，因此不复制 ingestion owner 的 formal validation。

## PRF 为什么不需要 transition adapter

PRF review unit `COVAPIE_BULK_REVIEW_UNIT_1569D77F66026B58` 的 Exact8 events 在 original frozen historical reconciliation 中全部已经是：

- `current_review_status=CURRENTLY_UNREVIEWED`
- `calibration_eligible=true`
- `calibration_exclusion_reason` 为空

该 review unit 的 historical event set 与 frozen PRF Exact8 完全相等，没有 missing、duplicate 或 extra。因此 PRF 直接满足 unchanged generic reconciler 的 completed-source prior-state invariant。`PRF_TRANSITION_ADAPTER_CREATED=false`；production module 不存在 `_adapt_prf_...` 或等价的 PRF state normalization。

如果 PRF prior 漂移，successor 的 original-state proof 会 fail closed。对 ONL-adapted rows 直接调用 generic 时，整个 PRF unit 漂移到非-unreviewed 状态会继续触发 frozen `PRIOR_REVIEW_STATUS_NOT_UNREVIEWED`。只漂移 Exact8 unit 中单独一行时，generic 会更早触发 `HISTORICAL_REVIEW_UNIT_STATUS_MIXED`；这是 generic 已冻结的 unit-consistency 保护顺序，不是规则放宽。

## 为什么 production 仍先复用 ONL transition owner

original frozen historical CSV 中，已发布的 ONL Exact9 仍保留 `CURRENTLY_IN_PROGRESS`。最终 cumulative reconciliation 同时包含 ONL，所以 production pipeline 必须是：

1. 由 generic owner 加载 original historical rows；
2. 独立证明 PRF original Exact8 是 `CURRENTLY_UNREVIEWED`；
3. exact 一次调用 published ONL private helper `_adapt_onl_in_progress_completion_for_generic_reconciliation_v1(...)`；
4. 证明 ONL adapter 前后 PRF Exact8 每一行、每一个字段完全相等；
5. 加载 FFQ、POA、G3H、ONL、PRF sources；
6. 调用 unchanged `generic.reconcile_completed_human_decisions_v1(adapted_historical, sources)`。

这是 ONL-specific transition 的复用，不是 PRF transition。ONL successor 继续独占该特殊 state-transition logic；PRF successor 不复制 helper、不把它加入 public API，也不创建第二套 transition logic。

不能放宽 generic 的 `PRIOR_REVIEW_STATUS_NOT_UNREVIEWED`。该 invariant 阻止 completed source 覆盖已有的非-unreviewed authority state，是跨 source 的通用保护。original historical rows 与全部五个 sources 直接调用 generic 仍必须因为 ONL prior 是 `CURRENTLY_IN_PROGRESS` 而失败。

## PRF Exact8 projection

PRF projector 只读取 ingestion owner 已严格验证的 formal binding 与 normalized events，并投影 reconciliation 所需字段。Exact8 identities 是：

1. `COVAPIE_CYS_SG_EVENT_V1:3S19:A:CYS:194-:SG:E:PRF:C10`
2. `COVAPIE_CYS_SG_EVENT_V1:3S19:B:CYS:194-:SG:G:PRF:C10`
3. `COVAPIE_CYS_SG_EVENT_V1:3S19:C:CYS:194-:SG:I:PRF:C10`
4. `COVAPIE_CYS_SG_EVENT_V1:3S19:D:CYS:194-:SG:K:PRF:C10`
5. `COVAPIE_CYS_SG_EVENT_V1:3UXJ:A:CYS:194-:SG:E:PRF:C10`
6. `COVAPIE_CYS_SG_EVENT_V1:3UXJ:B:CYS:194-:SG:I:PRF:C10`
7. `COVAPIE_CYS_SG_EVENT_V1:3UXJ:C:CYS:194-:SG:O:PRF:C10`
8. `COVAPIE_CYS_SG_EVENT_V1:3UXJ:D:CYS:194-:SG:S:PRF:C10`

全部 facts 都是 `human_review_completed=true`、`COMPLETED_HUMAN_POSITIVE`、`RELEVANT`、`POSITIVE`、`EXCLUDE_FROM_TRAINING_ONLY`、`human_training_excluded=true`。status provenance 只绑定 frozen formal path：

`covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/PRF_COVAPIE_BULK_REVIEW_UNIT_1569D77F66026B58/formal-human-decision-v1/prf_formal_human_decision_v1.json`

PRF ingestion snapshot、ONL adapter 或 temporary normalization 不会成为 status authority。D3 pair、D4 role、geometry、product/PRE topology 与 warhead atoms 仍由各自 source owner 保存，不被 projector 解释为 generic reconciliation disposition。

## Final Exact5 sources 与 reconciliation

最终 source composition 是 FFQ Exact8、POA Exact16、G3H Exact8、ONL Exact9、PRF Exact8，共 5 个 source bindings、5 个 review units 与 49 个无 collision 的 normalized facts。

| 状态 | events | review units |
|---|---:|---:|
| completed positive | 49 | 5 |
| completed negative | 24 | 4 |
| completed total | 73 | 9 |
| currently unreviewed | 265 | 122 |
| currently in progress | 0 | 0 |
| pending | 265 | 122 |

算术保持 `49 + 24 = 73` 与 `73 + 265 = 338`。Exact49 normalized training dispositions 是 12 `INCLUDE` 与 37 `EXCLUDE_FROM_TRAINING_ONLY`。

相对 published ONL reconciliation，PRF delta 是 completed positive `+8`、completed total `+8`、unreviewed `-8`、pending `-8`、pending unit `-1`、training excluded `+8`、training include `+0`、training admission `+0`、in progress `0`。PRF 从 unreviewed 完成，不是从 in-progress transition。

## Reconciliation 不等于 census refresh

本轮不更新 current published global census。published chemistry-positive count 仍为 58，`global_census_update=NOT_DONE`。PRF reconciliation local positive delta 是 `+8`，所以 `ready_for_current_global_census_refresh=true`，下一次单独授权的 census refresh 预期 derived global positive count 是 66；66 不是本轮 materialized published count。

以下仅是 `EXPECTED_NEXT_CENSUS_DERIVATION`，本轮不 materialize：task relevant 67、training exclude 37、completed human positive 49、`CURRENTLY_UNREVIEWED` 265、pair authority 66、role authority 66、DIRECT profile 35、STRICT profile 31；Exact5 applicability 预期为 A 66、B 31、B2 31、B3 66、C 66。

## Mask、chemistry authority 与 training 边界

global canonical V1 mask contract 保持 Exact5：

1. `warhead_only` / A
2. `linker_plus_warhead` / B
3. `scaffold_plus_warhead` / B2
4. `scaffold_only` / B3
5. `scaffold_plus_linker_plus_warhead` / C

B3 必须存在，没有第六 task。本 reconciliation 不处理或 materialize role/mask，不创建 pair authority、role authority、PRE topology、PRE geometry、POST training authority、nitrile warhead type、reaction family、reusable chemistry、tensor target 或 training admission。

没有 loader、batch、forward、auxiliary head、loss、backward、optimizer、fine-tune、training 或参数更新。feature semantics 仍为 `AUDIT_REQUIRED_LATER`，`READY_FOR_TRAINING=false`。Step12D 仍只是 smoke legality check，不是 final training-feature contract；formal training 前仍必须完成 feature-semantics audit，并解决或正式审计历史 `UNKNOWN_ATOM_FEATURE_POLICY` 与 `feature_semantics_known=False` 状态。
