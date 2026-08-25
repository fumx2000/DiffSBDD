# CovaPIE cumulative1000 current global readiness census V1

## 目的与 authority 边界

本步骤把 frozen cumulative1000、结构处理结果、current completed-human-decision reconciliation、legacy human authority、current runtime-positive authority、FFQ/POA/G3H event projections、正式 split 与 Exact5 语义汇成唯一的 1000-event current global readiness 总账。

`CURRENT GLOBAL READINESS CENSUS IS A DERIVED PROJECTION, NOT AN AUTHORITY CREATION LAYER.`

production owner 只读并 SHA-bind 已发布来源，调用已发布 owner，构造确定性的 event-level projection，再 materialize census CSV、summary JSON 和 manifest JSON。它不创建或修改 human decision、chemistry identity、reaction family、warhead rule、warhead type、reusable chemistry、split authority 或 training admission；不下载结构，不访问 scientific network，不 tensorize，不调用模型，不执行 forward、loss、backward、optimizer、fine-tune、参数更新或训练，也不修改 dataset。

## Frozen universe 与结构来源

universe 固定为 ranks 1–1000 的 1000 个唯一 canonical event IDs；canonical event-set SHA256 为 `f74d4e568d97ac23e2bc2cba2e8473e6705b726daf92204868efb1afbe0453ce`。其中有 546 个唯一 PDB 和 416 个唯一 ligand component。

结构列只由 ranks 1–500 与 ranks 501–1000 两段已发布 processing outcomes 生成，不从 human label 反推。当前结构计数为：raw structure 997、exact CYS-SG event 867、explicit covalent evidence 867、distance-only 0、full-coordinate POST evidence 867、CCD graph complete 865、feature compatible/structural processing success 865、representation gap 78、feature incompatible 2。

`reactive_pair_raw_structural_evidence` 只表示 feature-compatible 的结构 pair evidence，共 865；它不是 sample-level training label authority。`post_geometry_source_evidence_available` 共 867，也不能自行升级为 POST training authority。

## Human reconciliation 与 global presentation status

priority review population 是 338 events / 131 units。production owner 必须实际调用 `reconcile_real_completed_human_decisions_with_g3h_v1(...)`，而不是复制 FFQ、POA、G3H overlay。current reconciliation 为 32 completed positive、24 completed negative、56 completed total、273 unreviewed、9 in progress、282 pending；pending units 为 124。

`current_global_status` 只是 mutually exclusive 的展示 bucket，不是 authority。实现先验证来源集合互不冲突并恰好覆盖 universe，随后按以下冻结顺序呈现：

1. priority review population 的 current reconciliation status；
2. legacy completed task-negative；
3. completed partial authority；
4. current runtime-model usable；
5. published exact auto-negative；
6. leakage conflict、structural incomplete、representation gap、feature incompatible。

Exact11 分布为 273 unreviewed、9 in progress、32 completed human positive、54 completed human negative、1 completed partial authority、17 current runtime usable、32 published exact auto-negative、369 leakage conflict、133 structural incomplete、78 representation gap、2 feature incompatible。

Top pending units 按 event count 降序、原 priority rank 升序、review unit ID 稳定排序，从 raw priority queue 加 current reconciliation 动态计算。当前首位是 `COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74`，9 events，状态为 `CURRENTLY_IN_PROGRESS`。本步骤没有开始 ONL review，也没有作出任何新的人类决定。

## Chemistry、task relevance 与 training use

chemistry identity、task relevance 和 training use 是三个独立维度：

- chemistry：49 `POSITIVE`、0 `NEGATIVE`、86 `NOT_ESTABLISHED`、865 `UNRESOLVED`；
- task relevance：50 `RELEVANT`、86 `NOT_RELEVANT`、864 `UNRESOLVED`；
- training use：29 `INCLUDE`、20 `EXCLUDE_FROM_TRAINING_ONLY`、86 `NOT_APPLICABLE`、865 `UNRESOLVED`。

49 positives 的无碰撞 composition 是 current runtime 17、FFQ 8、POA 16、G3H 8。另有 1 个 legacy partial event 只建立 task relevance，未建立 chemistry identity，所以它属于 task relevant，但 chemistry 与 training use 仍 unresolved。

54 human-negative events 与 32 exact auto-negative events 合成 86 task-not-relevant。这里的 negative 是 task domain disposition，不是 chemistry `NEGATIVE`；这 86 events 的 chemistry 必须是 `NOT_ESTABLISHED`，training use 必须是 `NOT_APPLICABLE`。G3H Exact8 与其他 training-excluded positives 仍是 chemistry `POSITIVE`；`EXCLUDE_FROM_TRAINING_ONLY` 不能被解释成 chemistry negative。

## Pair、role 与 canonical Exact5

sample-level authoritative pair 和 role partition 都是 49。published model-bound pair target constructible 是 41：current runtime 17、FFQ 8、POA 16；G3H 8 保留 sample authority，但尚无 published G3H model-bound integration，因此贡献 training target 0。FFQ 的既有 bounded adapter 与 POA 的 inactive preview 只用于证明 current projection 中的 constructibility；本步骤不调用它们，也不从 preview 创建 training authority。

role profiles 为 31 `STRICT_LINKER_PRESENT_V1` 与 18 `DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1`。canonical V1 永远只有 Exact5：

1. `warhead_only` / A：49 applicable；
2. `linker_plus_warhead` / B：31 applicable；
3. `scaffold_plus_warhead` / B2：31 applicable；
4. `scaffold_only` / B3：49 applicable；
5. `scaffold_plus_linker_plus_warhead` / C：49 applicable。

31 strict-profile events 适用 all five；18 direct-profile events 只适用 A/B3/C。没有 role authority 的 951 rows 使用 JSON `null` 表示 applicability unknown，而不是空列表或五个 false。B3 不得遗漏，不允许第六 task。

## Geometry 与 training stages

POST source evidence 为 867，POST sample authority 为 21，POST training target 为 17。PRE source、sample authority 和 training target 均为 0；PRE 不是 V1 hard requirement。禁止 POST→PRE，禁止 PRE zero-fill。

training use `INCLUDE` 29 不等于 training admission。explicit future-admission candidates 为 12（FFQ 4、POA 8、G3H 0），current runtime-model usable 为 17，formal training admitted 为 5，ready for formal training 为 0。future candidate、runtime usable、formal split member 和 formal training admitted 是不同阶段，CSV 保留独立字段，不创建模糊的 `training_ready`。

不同 published owners 没有统一的 global `training_materialization_allowed` authority，因此 summary 固定记录 `NOT_COMPUTABLE_FROM_CURRENT_PUBLISHED_AUTHORITY`，绝不能强行计算成 0。per-row 字段只在 source 明确提供时记录 `true`/`false`，否则留空。

feature semantics 状态仍为 `FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER`，audit 未执行。Step12D 仍只是 `SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT`，不能据此推断 training readiness。

## Non-exclusive blockers

blocker buckets 可以重叠，不得相加为 1000。当前 chemistry unresolved 865/1000；pair authority absent 951/1000，但 positive subset 为 0；role authority absent 951/1000，但 positive subset 为 0。49 positives 内，human training exclusion 20、missing split 8、missing model-bound pair integration 8（全部 G3H excluded）、missing POST training authority 32、missing training admission 44、feature semantics pending 49。29 INCLUDE 内对应 missing split 4、missing tensor integration 0、missing POST training authority 12、missing admission 24。

## Determinism、manifest 与下一步

Exact3 outputs 使用 UTF-8、LF、单个 final LF，无 BOM/NUL/CR、trailing whitespace、timestamp、hostname、PID、absolute path 或 live Git lifecycle fields。checker 在两个不同 temporary directories 连续 materialize，要求 Exact3 byte-for-byte identical；随后独立解析 1000-row CSV，重算核心集合、计数和 SHA，验证 summary、所有 semantic source bindings、production/checker/tests/guide bindings 以及 output bindings。manifest 不在自身内部记录自己的 SHA256。

当前结论：

- `CURRENT_GLOBAL_RECONCILIATION_COMPLETE = true`
- `CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE = true`
- `READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_SELECTION = true`
- `READY_FOR_FORMAL_TRAINING = false`
- `NEXT_RECOMMENDED_MAINLINE = HIGH_YIELD_HUMAN_REVIEW_EXPANSION`

下一优先候选是 `COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74`。本轮结束后停止，等待外部审核；不 commit、不 push、不开始 ONL human review。
