# CovaPIE completed human decision reconciliation with ONL V1

## 目的与继承关系

本 successor 把 frozen ONL Exact9 formal human decision 纳入当前 completed-human-decision reconciliation。它是 additive、metadata-only、in-memory capability；不修改历史 reconciliation，不 materialize CSV、JSON、manifest、snapshot、transition artifact 或 global census。

最终 Exact4 source composition 是 FFQ Exact8、POA Exact16、G3H Exact8、ONL Exact9，共 4 个 source bindings、4 个 review units 和 41 条无 collision 的 normalized facts。FFQ、POA、G3H 由既有 G3H successor loader 提供；ONL formal decision 的完整验证仍由既有 ONL ingestion owner 的 `load_frozen_formal_decision_v1` 提供。

generic predecessor 仍是 historical parser、normalized dataclass、source ordering、cross-source collision、review-unit coverage、overlay 和 final review summary 的唯一 owner。新 successor 不创建 `SourceBinding`、`NormalizedCompletedDecisionFact`、`NormalizedDecisionSource` 或 `ReconciliationResult` 的替代类型，也不复制 generic overlay 算法。

## G3H 与 ONL prior state 的关键区别

G3H Exact8 在 frozen historical reconciliation 中的 prior status 全部是 `CURRENTLY_UNREVIEWED`，所以 G3H source 可以直接交给 generic reconciler。

ONL Exact9 的 prior status 则全部是 `CURRENTLY_IN_PROGRESS`。历史 338-event population 中恰好只有这 9 个 events 是 in progress，且只属于 `COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74` 这 1 个 review unit。若把 original historical rows 与 FFQ/POA/G3H/ONL sources 直接传给 generic reconciler，调用必须继续以 `PRIOR_REVIEW_STATUS_NOT_UNREVIEWED` 失败。

不能放宽 generic rule。该规则阻止任意 completed source 覆盖已有的非-unreviewed authority state，是所有 source 共用的安全 invariant；为了 ONL 接受任意 `CURRENTLY_IN_PROGRESS` 会削弱 predecessor 的通用保护。

## Private algorithmic transition adapter

ONL successor 使用 exact-unit-specific private adapter。它先独立证明：

- historical population 是 Exact338 events / Exact131 review units；
- ONL formal source 已由 frozen ingestion owner 完整验证并 finalized；
- ONL review unit 是 Exact9，event IDs 无 missing、duplicate 或 extra；
- Exact9 prior 均为 `CURRENTLY_IN_PROGRESS`、`calibration_eligible=false`、`calibration_exclusion_reason=CURRENTLY_IN_PROGRESS`；
- 全局 in-progress inventory 正好是 ONL Exact9 / Exact1 unit。

证明成功后，adapter 深拷贝 historical rows，并且只在 private working copy 的 ONL Exact9 上做 generic-precondition normalization：

| 字段 | frozen prior | private working value |
|---|---|---|
| `current_review_status` | `CURRENTLY_IN_PROGRESS` | `CURRENTLY_UNREVIEWED` |
| `calibration_eligible` | `false` | `true` |
| `calibration_exclusion_reason` | `CURRENTLY_IN_PROGRESS` | empty string |

`raw_priority_rank`、`raw_review_unit_id`、`raw_unit_event_count`、`canonical_event_id` 和 `current_status_authority_sources_json` 均不改变；所有非 ONL rows 保持 byte-for-field 相等。adapter 不修改调用方输入，不写回 historical CSV，不创建 provenance，也不暴露为 public API 或新 human authority。

这是 private algorithmic transition adapter，不是 historical authority rewrite。临时 `CURRENTLY_UNREVIEWED` 仅用于满足 unchanged generic precondition。随后 generic reconciler 仍执行 coverage、collision、sorting、overlay 与 summary；最终 ONL rows 直接成为 `COMPLETED_HUMAN_POSITIVE`，authority source 只指向 frozen ONL formal human decision，绝不输出临时状态或 adapter authority。

## ONL normalized facts 与最终 reconciliation

ONL projector 只从 ingestion owner 已验证的 formal binding 和 normalized Exact9 events 读取 completed-decision 所需的 event identity、D1 task relevance、D2 chemistry disposition、D5 training disposition、completion 与 source provenance。它不把 role、pair、geometry、warhead 或 reaction-family fields 解释成 reconciliation disposition。

ONL Exact9 全部投影为：

- `human_review_completed=true`
- `COMPLETED_HUMAN_POSITIVE`
- `RELEVANT`
- `POSITIVE`
- `EXCLUDE_FROM_TRAINING_ONLY`
- `human_training_excluded=true`

Exact41 normalized facts 的训练 disposition 是 12 `INCLUDE` 与 29 `EXCLUDE_FROM_TRAINING_ONLY`。training exclusion 不是 chemistry negative，也不是 training admission。

最终 338-event in-memory reconciliation 是：

| 状态 | events | review units |
|---|---:|---:|
| completed positive | 41 | 4 |
| completed negative | 24 | 4 |
| completed total | 65 | 8 |
| currently unreviewed | 273 | 123 |
| currently in progress | 0 | 0 |
| pending | 273 | 123 |

相对 published G3H reconciliation predecessor，ONL delta 是 positive `+9`、in progress `-9`、pending `-9`、training excluded `+9`、training include `+0`、training admission `+0`。

## Reconciliation 不等于 global census refresh

本轮 published current global readiness census 不变，published chemistry-positive count 仍为 49。successor 只证明 ONL reconciliation local authoritative-positive delta 为 `+9`，因此 `ready_for_current_global_census_refresh=true`，下一次单独授权的 census refresh 预期 derived positive count 为 58。58 不是本轮 published count；本轮 `global_census_update=NOT_DONE`。

下一步是单独的 current global readiness census refresh successor。本模块没有 production census owner 职责，也不能 materialize 58。

## Mask、geometry 与 training 边界

global canonical V1 mask contract 保持 Exact5：

1. `warhead_only` / A
2. `linker_plus_warhead` / B
3. `scaffold_plus_warhead` / B2
4. `scaffold_only` / B3
5. `scaffold_plus_linker_plus_warhead` / C

B3 存在，没有第六 task。reconciliation 本身不处理或重新 materialize masks。

本轮不创建 pair authority、role authority、POST authority、PRE authority、reaction-family authority、warhead authority、tensor target 或 training admission。PRE 仍 unresolved；不做 POST-to-PRE copy，不做 PRE zero-fill。没有 loader、batch、forward、auxiliary head、loss、backward、optimizer、fine-tune、training 或参数更新。

feature semantics 状态仍为 `AUDIT_REQUIRED_LATER`，`READY_FOR_TRAINING=false`。Step12D 仍只是 smoke legality check，不是 final training-feature contract。
