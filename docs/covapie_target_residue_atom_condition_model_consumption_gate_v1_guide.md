# CovaPIE target-residue atom-condition model-consumption gate V1

## 这一步解决什么问题

这一步是已提交 model consumption 实现的正式 successor gate。它不再改模型，
而是把“实现存在”升级为“冻结来源、真实运行证据、负路径证据和可发布 bundle
都同时成立”。生产入口只接收正式 runtime-bridge gate bundle 的 bytes 和仓库
根目录，返回 canonical、确定性的 Exact43 结果。

三个阶段应明确区分：

- Runtime bridge 负责从口袋准备结果产生并携带
  `pocket_target_residue_atom_condition_indicator`，但不让模型消费它。
- Model consumption 把这个长语义字段穿过训练、评估、采样和 inpainting 路径，
  并在 dynamics 中真正读取它。
- Model-consumption gate 不增加新行为；它独立重建证据，确认已提交行为满足
  冻结合同，随后发布正式 gate bundle。

## 模型怎样读取目标 Cys-SG 条件

启用 `target_residue_atom_conditioning` 时，`EGNNDynamics` 精确增加一个
长度为 32 的可训练向量
`target_residue_atom_condition_embedding`。`forward` 先用原有
`residue_encoder` 得到口袋节点 hidden 表示，再只对 bool indicator 为真的那一
行加上该向量。注入发生在 ligand/pocket hidden 拼接和 time feature 拼接之前。
因此 ligand 行不被直接注入，非目标 pocket 行保持原值，坐标也不被条件注入
修改。

该参数以全零初始化。全零时，有条件路径与旧路径逐元素相同，保证 checkpoint
兼容和初始输出 parity。非零测试不使用“两个输出相减等于 embedding”这种会
掩盖共同错误的判断；gate 从 legacy encoded hidden 的完整副本直接构造期望
hidden，再比较完整张量。这个 oracle 循环 16 个固定 seed，并在 API 返回前恢复
调用者的 CPU RNG state。

## Gate 怎样独立重建证据

Gate 不执行当前 workspace 中旧的 implementation checker。它独立完成：

1. 严格解析正式 runtime-bridge gate bundle，绑定 transport SHA、internal SHA、
   canonical JSON、11 条 Current11 lineage 和 11/2202/11 汇总。
2. 绑定 implementation commit 的单父、空 body、tree、subject、精确 8 文件
   scope/stat，以及 working-tree、commit blob、冻结 SHA 三方字节一致性。
3. 相对 design commit 比较 AST，只允许 Lightning 一个方法、dynamics 两个
   方法、conditional 指定八个方法、en-diffusion 指定四个方法加两个 helper
   发生变化。
4. 枚举真实 `self.dynamics` 调用，要求精确 8 个调用点都显式传递长语义字段；
   同时确认 loss、normalize、noise representation 和 unconditional joint sample
   的 AST 未变。
5. 真实构造 disabled/enabled `EGNNDynamics`，加载正式 checkpoint，并调用真实
   migration helper。
6. 用 tiny 真实 dynamics 和 capture EGNN 重建 zero-init 与 direct-expected-hidden
   注入 oracle，不执行 backward 或 optimizer step。

旧 implementation checker 冻结的是相对 design commit 的精确 8 路径。新增本
gate 的四个授权文件后，候选范围自然变成 12 路径，所以旧 checker 应按原合同
fail closed。为了让它在 successor workspace 继续绿色而隐藏、删除 gate 文件，
或修改旧 checker，都会破坏历史证据。本 gate 只绑定旧 checker 的冻结文件 SHA
及其 gate 文件出现前的成功 stdout SHA，不把旧 checker 的当前成功作为条件。

## 为什么 Current11 不跑完整 EGNN

Current11 的 11 个样本合计 2202 个 pocket 节点。完整 EGNN 会构造近似
O(N²) 的图；这对验证 indicator 的 dtype、长度、mask、size 和每样本 cardinality
既无必要又浪费内存。Gate 在内存中构造 `[2202,3]` 的 `x`、`[2202,10]` 的
`one_hot`、long `size/mask` 和 bool indicator，然后调用真实
`EnVariationalDiffusion` validator。模型注入行为由 tiny dynamics oracle 单独
验证，两种证据各自回答一个明确问题。

## Checkpoint 的三个 profile

- Disabled：开关为 false，不存在新 state key；120 个 dynamics state keys 与正式
  checkpoint 严格加载，missing/unexpected 均为空。
- Enabled：开关为 true，只增加
  `target_residue_atom_condition_embedding`；shape 为 `[32]`，全零且
  `requires_grad=true`，所有已有 key 和 shape 不变。
- Migration：真实 helper 只补
  `ddpm.dynamics.target_residue_atom_condition_embedding` 一个 key，最终
  `strict=True` 加载。Gate 还验证额外 missing、unexpected、shape drift、dtype
  drift 和非零新参数全部 fail closed；不使用 blanket `strict=False`。

正式 checkpoint 只读。Gate 在加载前后验证其 17,861,341 bytes 和 SHA256，
不会写 checkpoint。

## 负路径和 fail-closed 语义

Validator 必须拒绝 float/bool/int32 mask、float/bool/int32 size、全 false、任一
样本零目标、任一样本多目标，以及 bool/int、bool/float 的数值伪相等双来源。
双来源只有 shape、dtype、内容都完全相同的 bool tensor 才可接受。Public API
把所有失败统一为：

```text
COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_MODEL_CONSUMPTION_GATE_INVALID
```

API 不联网、不写文件、不返回 Path 或 tensor，也不改变输入。正式 bundle 的写入
只由 checker 调用内部 materializer 完成：目标不存在时原子发布；相同 bytes 已
存在时返回 `idempotent_existing` 且不触碰 inode/mtime；不同 bytes、symlink、
非普通文件、非 0644 或多 hard-link 目标都 fail closed。

## Runtime gate lineage 与 RNG 证据修订

正式 runtime bundle 与 runtime gate commit/source 是两层不同证据。前者证明
已发布 Current11 数据、lineage 和汇总值的 transport/internal identity；后者证明
生成和验证这份 bundle 的 gate 源码确实来自冻结的历史 commit。Exact43 中的
`source_runtime_bridge_gate_commit` 因而不能只是一个常量标签。

Gate 会真实读取 runtime-gate commit 的唯一 parent 和 subject，并把冻结
production 路径的 working-tree bytes、commit blob bytes 和 SHA256 三方绑定；
同时验证该 commit 是 model-consumption implementation、当前 HEAD 和
`origin/main` 的 ancestor/equal。当前 import 的 `runtime_gate.__file__` 也必须解析
到同一冻结 production 路径，避免从别处加载同名 module。所有这些证据共同进入
readiness；任何一项漂移都 canonical fail closed。

RNG 证据也必须由产生 oracle 的 helper 自己建立。`_injection_evidence()` 在入口
保存 CPU RNG state，在 `try` 中运行 16 个固定 seed，并在自身 `finally` 中恢复；
返回前再逐字节比较恢复后的 state，比较结果才写入
`cpu_rng_state_restored`。Public API 会在构造 response 和 digest 前恢复并验证其
入口 state；外层 `finally` 只作为异常路径的最终安全网，不能替代 helper 的直接
恢复证据。

Response digest 计算时所有嵌套 contract 已最终定稿。digest 计算后不再修改
`oracle_contract`、response 或其他嵌套对象。本修订只增强证据真实性，不改变
Exact43 字段、字段顺序、结果值、正式 bundle bytes、模型、checkpoint 或 readiness
结论。

## CLI、mask 和下一步边界

六个 repository CLI/notebook caller 仍按冻结 SHA 保持不变，所以：

```text
repository_cli_selector_forwarding_implemented=false
```

Gate 成功仅表示 model consumption 已有正式证据，下一步才是：

```text
design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1
```

五级 canonical mask 合同完全不变：`warhead_only`、
`linker_plus_warhead`、`scaffold_plus_warhead`、`scaffold_only`、
`scaffold_plus_linker_plus_warhead`。`scaffold_only` 不能省略，也没有第六个 mask。

## 训练仍未获授权

本 gate 只做只读验证和纯内存 oracle，不进行 training、fine-tune、backward、
optimizer step、参数学习或 checkpoint 写入。Step12D 仍只是 smoke legality check，
不是最终训练 feature 合同。正式训练前必须完成 feature-semantics audit，并解决
或正式审计历史状态：

```text
UNKNOWN_ATOM_FEATURE_POLICY
feature_semantics_known=False
```

因此 gate 成功时仍必须报告：

```text
training_or_parameter_update=false
feature_semantics_audit_required_before_training=true
```
