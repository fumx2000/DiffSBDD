# CovaPIE completed human decision reconciliation with G3H V1

## 目的与继承关系

已发布的 `covapie_completed_human_decision_reconciliation_v1` 在其发布边界内只消费 FFQ Exact8 与 POA Exact16；G3H 的正式人工决定及其 ingestion successor 当时尚未进入这条 generic reconciliation chain。因此旧实现保持原样，新模块以 additive successor 方式把 G3H Exact8 投影到同一套 normalized contract，再把 FFQ、POA、G3H 三个真实 source 交回旧 generic reconciler。

旧 reconciler 仍是算法的唯一 owner。新层直接复用它的 `SourceBinding`、`NormalizedCompletedDecisionFact`、`NormalizedDecisionSource`、`ReconciliationResult`、FFQ/POA projectors、历史 CSV loader 和 `reconcile_completed_human_decisions_v1`。排序、跨 source event collision、review-unit 完整覆盖、历史 prior-status 检查、overlay 字段以及 summary vocabulary 均未复制或分叉。

本轮没有修改 G3H human decision，也没有修改 FFQ、POA 或历史 reconciliation。三个 formal decision 均以固定相对路径、byte count 和 SHA256 只读绑定；历史 CSV 同样保持 immutable。successor 只在内存中生成 reconciliation result，不 materialize CSV、JSON、manifest、snapshot 或 census。

## Normalized completed-decision fact

normalized fact 是 generic reconciler 消费的最小 event-level 人工决定事实。它只携带：完成审核 identity、任务相关性、化学 disposition、训练用途 disposition 和 source provenance。它不重新解释 warhead/scaffold/linker atoms、reactive pair、reaction family、warhead rule、PRE/POST geometry 或 tensor readiness。

G3H Exact8 的人工化学判断均为 `POSITIVE`，当前训练用途均为 `EXCLUDE_FROM_TRAINING_ONLY`。这两者不矛盾：前者说明样本级共价化学获得人工支持；后者说明即使化学为正，该事件也不进入当前训练用途。training excluded 不是 chemistry negative，也不会把 status 改成 `COMPLETED_HUMAN_NEGATIVE`。因此 G3H 八条 normalized facts 全部是 `COMPLETED_HUMAN_POSITIVE`，但 `human_training_excluded=true`。

`EXCLUDE_FROM_TRAINING_ONLY` 也不是 training admission。本轮创建的 training admission 数为 0，dataset 未改变，未开始 tensor integration、loader/batch integration、model forward、loss、backward、optimizer 或参数更新。

## 当前 reconciliation 结果

真实 Exact3 sources 为 FFQ Exact8、POA Exact16、G3H Exact8，共 32 条 additive normalized facts。内存 reconciliation 覆盖历史 338-event population，得到 32 completed positive、24 completed negative、56 completed total、273 currently unreviewed、9 currently in progress，以及 282 pending。32 条 normalized facts 的训练 disposition 是 12 `INCLUDE` 与 20 `EXCLUDE_FROM_TRAINING_ONLY`。

相对旧 FFQ+POA runner，G3H delta 是 completed positive `+8`、pending `-8`、training excluded `+8`、`INCLUDE +0`、training admission `+0`。G3H 八个历史行此前均为 `CURRENTLY_UNREVIEWED`，successor 结果中均为 `COMPLETED_HUMAN_POSITIVE`；每行 authority source 只指向固定 G3H formal human decision path。

## Authority、mask 与 geometry 边界

G3H source 中已有的 sample-specific reactive-pair 与 role authority 仅作为既存 predecessor fact 保留和引用。本 reconciliation successor 不创建新的 pair authority 或 role authority，也不把 generic reconciliation 变成 role、geometry 或 tensor validator。

canonical V1 mask contract 仍严格是 Exact5：

1. `warhead_only` / A
2. `linker_plus_warhead` / B
3. `scaffold_plus_warhead` / B2
4. `scaffold_only` / B3
5. `scaffold_plus_linker_plus_warhead` / C

B3 未遗漏，没有第六种 mask，本轮也不重新 materialize masks。

G3H 的 PRE geometry 仍是 `PRE_REACTION_UNRESOLVED`。POST observed evidence 不会被复制成 PRE，不做 PRE zero-fill，也不创建 POST geometry training authority。

## Reconciliation 不等于 readiness census

本 successor 回答的是“当前已完成的人类决定如何叠加到固定 338-event 历史 population”，而不是“每个事件是否具备全套训练 authority”。后者还需要独立的 current global readiness census，涉及更广的 source-of-truth 与 readiness 字段，不能从 completed-decision reconciliation 的状态直接推断。

因此当前边界是：

- `CURRENT_GLOBAL_RECONCILIATION_G3H_GAP_CLOSED = true`
- `CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE = false`
- `ready_for_current_global_readiness_census_successor = true`
- `tensor_integration_not_started = true`
- `training_admission_not_started = true`
- `FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER = true`
- `ready_for_formal_training = false`

Step12D 仍只是 `SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT`。下一步才可能在单独授权下实现 current global readiness census；本轮不继续到 census、tensor 或 model。
