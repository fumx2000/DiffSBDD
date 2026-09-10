# CovaPIE POST 分量与监督适用性限定验证 V1

## 决策与范围

本轮基于 `2b60b5df57e422db1055162be4045a32ad157e32`，只使用 CPU
合成 supervision 与 diffusion trace。没有调用 FFQ adapter、Exact16 authority
binder、真实 tensorizer/DataLoader、扩散模型 forward、checkpoint、Trainer、
optimizer 或参数更新，也没有生成真实 FFQ 标签。

真实函数 `compute_covapie_current11_training_losses_v1` 现在显式区分两个用途：

- `post_geometry_loss_purpose="existing_component_masks_v1"` 是默认值，只保留
  BASELINE 已发布的 component-mask 执行行为；该名称不代表所有样本均获批准，
  也不替代样本 authority。
- `post_geometry_loss_purpose="independent_hidden_post_distance_v1"` 才启用本轮
  最终资格检查。该用途是 loss 解释，不是第六个 canonical task/mask。

针对“独立预测隐藏 POST 距离”用途，POST loss 的候选资格必须同时满足：

1. 上游明确请求 POST loss，且 POST target/component 有效；
2. sample 已准入，task/蛋白反应端点条件有效，positive pair 完整且一致；
3. 从 `positive_candidate_index` 取到的 ligand flat index 对应端点确实为
   generated，且不为 fixed。

该判断不得把上游的 `false` 请求提升为 `true`。fixed ligand 反应端点不属于
这一“隐藏端点预测”成功指标；其观测值可以原样保留为 diagnostic/context，
不能删除或改写。

这不是对所有历史 geometry loss 的 hidden-only 全局改写，也不是对所有 fixed
端点 geometry loss 的全局否定。fixed-context 一致性或
重建若要成为训练目标，必须另行定义用途、target、mask 和成功指标；本轮没有
为它授权。新分支已位于真实 loss 函数并由合成测试直接调用，但 Current11
Lightning、mixed-profile bridge、batch/smoke 入口、Exact16 binder 和 FFQ
adapter 均未迁移；省略参数的历史调用仍执行默认用途，不能据此声称 hidden-POST
策略已运行。因此本轮没有形成全局最终门控闭环。

## 实际接口、索引和单位

静态读取确认的两分量 registry 仍为：

| index | 语义 | 单位 |
|---:|---|---|
| 0 | `PRE_COVALENT_REACTIVE_PAIR_DISTANCE_ANGSTROM` | angstrom |
| 1 | `POST_COVALENT_REACTIVE_PAIR_DISTANCE_ANGSTROM` | angstrom |

接口分工如下：

| 字段/通道 | shape | 当前分工 |
|---|---|---|
| `pre_post_geometry_target_angstrom` | `[B, 2]` | loss 的监督答案；辅助 forward 不读取 |
| `pre_post_geometry_component_valid_mask` | `[B, 2]` | 上游有效性；默认用途沿用 BASELINE 行为，hidden 用途在 loss 内再次要求 POST valid |
| `pre_post_geometry_component_loss_mask` | `[B, 2]` | 上游请求；hidden 用途复制后仅收紧 POST 列，不原地改写 |
| `pre_post_geometry_predictions_angstrom` | `[N_pair_candidates, 2]` | pair candidate head 的非负预测 |
| `ligand_batch_index` | `[N_ligand]` | hidden 用途必需的独立 ligand 节点归属；一维 `long`，不是 supervision schema/训练特征 |
| `pocket_batch_index` | `[N_pocket]` | hidden 用途必需的独立 pocket 节点归属；一维 `long`，不是 supervision schema/训练特征 |
| `observed_complex_pair_distance_angstrom` | `[B, 1]` | 观测诊断字段；本轮所测辅助 forward/loss 均不直接读取 |
| `ligand_anchor_distance_angstrom` | `[N_ligand, 1]` | role/mask/anchor encoder 的 conditioning；只在 valid、fixed、非-generated 行进入 anchor encoder |

默认用途下，局部 loss 对每个有分量请求的 sample，用
`pair_positive_candidate_index[sample]` 选择预测行，用 `[B,2]` loss mask
选择列；先对该 sample 的已选分量求 Smooth-L1 均值，再对纳入的 sample 求
均值。旧文档中“当前 loss 只依赖上游 mask”的描述只对应 BASELINE/默认用途。

hidden 用途在读取所选 target/prediction 前，先验证 sample/component bool mask、
generation/fixed、long index、offset 覆盖、candidate segment、model-output 与
supervision candidate metadata，以及 positive ligand/pocket flat index。真实 trace
没有独立 ligand/pocket batch index 字段，candidate 自己声明的 sample ID 不能证明
实际节点归属，所以该用途必须由调用者另传两项独立 batch index；当前只有合成
fixture 提供它们。合法缺失的 `pair_valid=false` 哨兵先被排除，不会以 Python
负索引读取最后一行。有效 positive pair 还必须落在同 sample 的独立 ligand/pocket
节点集合中，pocket flat index 必须等于 target reactive anchor，positive ligand
必须是有效 warhead role 且 `generated=true, fixed=false`。

effective mask 从请求 mask 的副本开始，只替换 POST 列；PRE 的选择顺序、
unit-beta Smooth-L1 和“sample 内分量 mean，再对有效 sample mean”的 reduction
保持不变。未选择的 NaN 不会被读取；全部 geometry 关闭时，以空张量切片构造
有限、graph-connected 的零，避免对含 NaN 的完整 prediction 做 `sum()*0`。

pair embedding 的距离输入来自
`(denoised_ligand_xh - clean_centered_pocket_xh) * coordinate_normalization`；
其范数以 angstrom 进入 head。该距离是当前 denoised 模型状态的几何特征，
不是 clean supervision target，也不是 observed diagnostic。

静态读取 FFQ adapter 还确认：当前 FFQ 的 geometry target 全为 NaN，
component valid/loss mask 全为 false；adapter 只运行 raw auxiliary prediction，
不运行 geometry loss。FFQ observed 字段的存在不能自动授权把它复制成 POST
target。Exact16 binder 的成员范围和批准也没有扩展到 FFQ。

## 合成运行结果

原探针及本轮新增测试使用三个不对称 sample，candidate offsets 为 `[0, 4, 9, 12]`，
positive candidate index 为 `[2, 8, 10]`。前两个 sample 请求 POST，第三个
不请求；所有 PRE target 为 NaN，PRE valid/loss 均为 false。

- 默认用途的 POST-only loss 精确选择 candidate 2/8 的 component 1，并与独立写出的
  unit-beta Smooth-L1 和双层 sample reduction 一致。梯度支持仅出现在
  `(candidate 2, POST)` 与 `(candidate 8, POST)`；PRE、non-positive
  candidates 以及被 mask 的第三个 sample 均无该项梯度。
- 固定模型参数、hidden、坐标、role delta、candidate/index 和所有 mask 后，
  只改变 POST target，pair/geometry predictions 按位不变而 geometry loss
  改变；只改变 observed diagnostic，所测 forward predictions 和 geometry
  loss 均按位不变。这一结论只覆盖实际调用的辅助 forward/loss，不能外推为
  上游 hidden/trace 来源的全链 no-leakage 证明。
- `pair_embedding` pre-hook 捕获的最后一列与 denoised ligand 到 conditional
  pocket 的距离乘 `2.5` 完全一致，与二次乘 normalization 不一致。只改一个
  denoised ligand 坐标会改变相应输入距离；共同旋转和平移 ligand/pocket 后，
  距离和 geometry prediction 保持一致。
- 两个明确端点场景的 protein anchor 都作为给定 conditional pocket：Task A
  的 positive warhead ligand 端点为 generated；Task B3 的 positive warhead
  ligand 端点为 fixed。合法合成 POST mask 为 true 时，现有 loss 对两者都
  产生有限 per-sample loss，证明默认行为只依赖传入 mask，没有独立排除已知
  端点。测试内隐藏-POST eligibility 为 `[true, false, false]`；第三个 Task C
  端点虽 generated，但其上游请求为 false，未被自动开启。
- 在固定 prediction=`1.0` 的同一输入上，默认/显式历史用途均纳入 generated
  sample 的 `SmoothL1(1.0, 7.25)=5.75` 与 fixed sample 的
  `SmoothL1(1.0, 0.15)=0.36125`，最终为 `3.055625`、有效 sample 数为 2；hidden
  用途只纳入前者，loss 为 `5.75`、有效 sample 数为 1，梯度也只落在
  `(candidate 2, POST)`。原 request/valid/target 均未被原地修改。
- 独立 false-request 对照同时保持 component valid、准入、pair/condition 和
  generated 端点为 true，仅 request=false，实际 hidden loss 仍为 graph-connected
  零。fixed、both-false、未准入、invalid component/canonical/condition 只关闭
  hidden POST；同 sample 的合法 PRE 继续参与。
- PRE-only、POST-only、PRE+POST 的受控 loss 分别为 `1.5`、`2.5`、`2.0`；
  全部关闭时为有限零。被排除 target/prediction 的 NaN 不污染结果，真正选中的
  NaN 或负距离则 fail closed。负/越界/错 segment、跨样本节点、错 target anchor、
  metadata 不一致、mask/index dtype/shape/device 错误均按统一接口错误拒绝。

BASELINE 前已登记的组合证据为
`covapie_post_distance_supervision_applicability_probe_v1` iteration 1 / output406，
原始摘要 `18 passed in 1.67s`；未登记的旧 5/13 单独结果不在本轮追认。

本任务 `implement_scoped_hidden_post_loss_applicability_v1` iteration 1 的新实现
组合运行（无 `-k`、deselect、skip 或 xfail）为：

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$REPO:$REPO/src" python -B -m pytest -q \
  tests/test_covapie_post_distance_supervision_applicability_v1.py \
  tests/test_covapie_current11_auxiliary_model_and_loss_v1.py \
  tests/test_covapie_ffq_post_conditioning_visibility_v1.py
........................................................................ [ 69%]
................................                                         [100%]
104 passed in 2.51s
```

## 五任务边界与证据类型

运行测试直接核了 canonical registry 精确包含
`warhead_only`、`linker_plus_warhead`、`scaffold_plus_warhead`、
`scaffold_only`、`scaffold_plus_linker_plus_warhead`，没有第六任务；
`scaffold_only` / B3 被保留。

任务 ID 常量和合法 role/endpoint mask 合成覆盖全部五项。A/B/B2/C 的 positive
warhead ligand 端点按各自合法角色配置为 generated，hidden POST 被纳入；B3
保留的 warhead 端点为 fixed，只排除该用途的 POST，而同 sample PRE 仍参与，
B3 整体任务没有被禁用。判断依据是 positive pair 定位后的真实
generation/fixed mask，不是短别名硬编码开关。这些仍是合成角色配置证据，不是
真实样本适用性或 authority。

以下结论来自运行：候选/分量选择、reduction、梯度支持、target/observed
局部消费关系、denoised 距离来源、一次 normalization、刚体不变性和当前
fixed/generated loss 行为。以下来自静态读取：PRE/POST 正式定义、tensorizer
的 mask 合成、FFQ 的 NaN/false 边界、FFQ observed 来源以及 Exact16 binder
的 POST-only 绑定范围。

准确 PRE 不是 V1 全局硬前置；本轮 POST-only 验证没有用 POST 填 PRE，也没有
改变两分量顺序或 head shape。

## 剩余边界与下一步

本轮已完成 scoped `hidden POST loss applicability gate` 的真实函数入口和合成
验证。上游请求仍是必要条件，不能由资格判断自行打开 false mask；
fixed-context 的其他用途必须等独立目标合同后再进入，不能混用这一 gate。

选择 loss 边界而不只改 encoder，是因为 encoder 只构造 conditioning hidden
delta，不决定 geometry target 是否与 head prediction 比较；仅改 encoder
无法阻止 fixed 端点的 POST mask 进入现有 loss。只在 Current11 tensorizer
过滤也不足以形成最终边界，因为 Exact16 binder 会在 tensorize 后复制并打开
POST mask，其他 bridge 或直接构造 supervision 的调用方也可能绕过。

未来若有调用方声明采用 hidden-POST 用途，必须显式传入 purpose 和经语义核验的
既有 `ligand["mask"]` / `pocket["mask"]` 节点归属；本轮没有迁移任何调用方。
生产调用迁移还需逐一核 Current11 training Lightning、mixed-profile bridge、
batch/smoke、Exact16 binder 和 FFQ adapter 的真实字段与 authority，不能从
candidate index 反推 batch index 再当作独立交叉证据。

仍缺的真实 FFQ 授权包括：POST target 的正式来源绑定、逐样本端点/用途批准、
training admission、geometry valid/loss 开启，以及对现有人审排除的保持。
这些授权在关闭前不得开启真实 FFQ geometry loss。正式训练前仍须完成 feature-
semantics audit；Step12D 仅是 smoke legality check，不是最终训练特征合同，
历史 `UNKNOWN_ATOM_FEATURE_POLICY` / `feature_semantics_known=False` 状态必须被
解决或正式审计。本轮不构成 `READY_FOR_TRAINING`，也没有执行扩散模型 forward、
checkpoint load、optimizer step、参数更新、真实训练、commit 或 push。
