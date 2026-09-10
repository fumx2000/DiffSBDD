# CovaPIE FFQ POST conditioning visibility 限定验证与最小生产修复 V1

## 结论

历史 baseline `023bd309492115a33249fb9b4ae2b0aed7e1890b` 的 output 388
证明旧生产方法会让原始 valid 的 generated clean-anchor distance 进入真实辅助
encoder。当前未提交四文件候选已在同一真实
`CovapieCurrent11AuxiliaryModelV1.encode_role_mask_anchor_v1` 内实施最小修复：仅有
`original_valid & fixed & ~generation` 的行可见。generated 行的有限扰动、NaN、
Inf、负值均不会进入 anchor encoder；合法 fixed/context 距离仍保持敏感。

这只关闭 clean-anchor distance 这一条字段通道。默认零初始化仍只是一项 control；
本修复不构成全部 conditioning、最终扩散预测或训练 loss 的 no-leakage proof。

## 真实数据流定位

- `src/covalent_ext/covapie_ffq_supervised_forward_adapter_v1.py` 的
  `_assemble_supervision_v1`（约 381–412 行）从 clean ligand/pocket 坐标计算每个
  ligand 节点到目标 pocket anchor 的距离，并把对应 valid 全部置 true；同一函数
  另把正例观测距离写入 diagnostic 字段（约 466–470 行）。
- `src/covalent_ext/covapie_current11_auxiliary_model_and_loss_v1.py` 的构造器
  （约 121–150 行）把 role/task/generation/seed embedding 和 anchor encoder 最后一层
  零初始化。baseline 的 `encode_role_mask_anchor_v1` 只 gather 原始 valid anchor 行；
  当前未提交实现先核验 valid/fixed/generation 的 bool、严格 `[L,1]` shape、device 与
  fixed/generation 不重叠，再核验 distance 为同设备浮点 `[L,1]` tensor，派生 effective
  行后才检查选中距离有限且非负并执行 `log1p` 和真实 `anchor_distance_encoder`。
- FFQ 专用 `_run_loss_free_forward_v1`（约 698–708 行）调用该 encoder，并要求本次
  初始 delta exact-zero，否则抛
  `ZERO_INITIAL_ROLE_ENCODING_DELTA_DRIFT`。这个 guard 只约束当前 FFQ adapter 的
  零初始化运行；本轮没有执行该 adapter，也没有把非零探针冒充 adapter 成功运行。
- 共享训练模块的 `forward`（
  `src/covalent_ext/covapie_current11_training_lightning_module_v1.py`，约 817–883 行）
  依次 tensorize、调用同一 encoder、进入扩散 hidden 路径、辅助 head 和 loss。这里
  没有 FFQ 专用的 exact-zero guard。baseline 中一旦 encoder 权重非零，generated
  clean anchor 可成为共享预测路径的条件输入；当前所有调用这一共享方法的路径都会
  继承本次 anchor 限制，因此并非只影响 FFQ。本轮没有端到端执行全部调用方，也没有
  执行该共享 training forward。
- 常规 tensorizer 也从 admitted model-index-space clean ligand/pocket 坐标构造
  anchor 距离及 valid（
  `src/covalent_ext/covapie_current11_training_tensorizer_v1.py`，约 892–905、
  1058–1059 行）。本轮只静态读取该实现，没有调用真实 tensorizer。

## 历史基线合成数值对照（output 388）

output 388 在 baseline 上为 `5 passed in 1.43s`。全部推理均在
`torch.no_grad()` 下完成；`sample_training_admitted=false`，所有 loss mask=false，
geometry target 全为 NaN 且 valid=false。未发生参数变化，所有参数 gradient 均为
`None`。output 389 是文件 mode 检查的真实 FAIL，output 390 是仅修复 mode 后的恢复
闭环；两条历史记录均保留，未复制或改判。

- A，zero-initialization control：generated 节点距离从 1 Å 改为 3 Å 前后，完整
  `8 × 4` hidden delta 均为 exact-zero。
- B，固定非零权重敏感性：真实 encoder 对该节点的四个 delta 分量从
  `0.46209812` 变为 `1.10903549`；每分量变化 `0.64693737`，L2 变化约
  `1.29387474`。其余节点 exact-unchanged，另一独立样本的最大变化为 0。这一正向
  对照证明 anchor 字段能够影响真实辅助编码，但未量化扩散预测或 loss。
- C，测试内候选视图使用
  `original_anchor_valid & fixed_mask & ~generation_mask`。对两个样本的全部四个
  generated 节点分别施加有限值扰动和 hidden-row NaN 后，完整 delta 均
  exact-unchanged 且全有限，generated 行 delta 为 exact-zero。这也验证 invalid
  NaN 行没有通过 `NaN * 0` 进入数值 encoder。
- D，在同一候选视图中把一个可见 fixed-context 节点从 4 Å 改为 8 Å，其四个
  delta 分量从 `1.34119826` 变为 `1.97750212`；每分量变化 `0.63630386`，L2
  变化约 `1.27260772`。其余节点及另一独立样本 exact-unchanged，说明结果不是
  通过关闭整个 encoder 得到。
- E，保持 anchor 输入不变，仅把 observed-distance diagnostic 从 `(1.5, 2.5)`
  改为 `(999, 777)`，encoder delta exact-unchanged。按当前函数真实行为，
  `encode_role_mask_anchor_v1` 不直接消费该 diagnostic 字段。

## 当前未提交修复与回归

- output 391 / task iteration 1：在生产代码未修改时，新的直接生产回归传入原始
  `valid=全 true`，generated NaN 进入旧 encoder 数值检查，pytest 真实结果为
  `1 failed`、rc=1。这是目标缺陷复现，不是 fixture/import 错误。
- output 392 / iteration 2：只修改生产方法后原样重跑同一节点，结果为
  `1 passed`、rc=0；测试端没有预过滤 valid，也没有调用候选 adapter/helper。
- output 393 / iteration 3：扩展 visibility/fail-closed 矩阵与保留的梯度节点共
  `27 passed`、rc=0。
- output 394 / iteration 4：要求的两份完整测试文件组合命令结果为
  `39 passed in 1.90s`、rc=0，无 `-k`、deselect、skip 或 xfail。

当前回归还证明：original-valid=false 的 fixed 行与 fixed/generation 均 false 的行
不可见；fixed/generation 重叠、非 bool、错误 shape/device 及非法 distance tensor
均 fail closed；全 generated 时没有调用 anchor encoder，但非零 role/task/generation
embedding 贡献仍保留；observed-distance diagnostic 不直接影响此 encoder。五个
canonical task ID 均遵守同一规则，包括 `scaffold_only` / B3，没有新增第六任务。

旧梯度测试只把合法可见 anchor 移到既有 fixed 第 4 行（零基索引 4），同时保留第
0 行 generated 且 original-valid=true。hook 继续执行真实 encoder，并观察到仅
`log1p(2 Å)` 进入；backward 后 hidden generated/invalid distance 梯度为零，合法 fixed
distance 与 encoder 参数的梯度通路仍存在。完整旧辅助测试还实际执行了小型合成
auxiliary forward、loss 与 autograd，但没有真实训练数据、optimizer 或参数更新。

构造器、网络层、参数注册和 state_dict key/shape 均未修改。baseline 与当前合成构造
模型的 18 项 state_dict key/shape/dtype 清单完全一致，两份清单 SHA256 均为
`90cfda732577873f35def3296437e850e7a1d7a223f6ef2fa3d95c722b0a8706`；本轮未保存
权重文件、未加载 checkpoint。这项结构兼容不表示任意历史非零权重的预测不变：切断
generated clean-anchor 影响正是本次预期语义变化。

## 语义边界与最小后续建议

需要分别处理四类几何：待生成区域的 clean 最终距离可能是答案侧通道；本来可见的
fixed/context 几何可以是合法条件；从当前 noisy/denoised 状态计算的几何不是同一条
clean ground-truth 通道；外部明确指定的设计约束只有在另行授权和定义后才能作为
条件。本轮没有新的设计约束授权，不能把隐藏的最终答案改名为“条件”。

若 `scaffold_only` / B3 等任务保留反应端点，其距离可能属于可见上下文，但这并不
自动授权把它计作独立 POST 预测监督；loss/applicability 仍需后续单独审计。本轮
保持 canonical 五任务不变：`warhead_only`、`linker_plus_warhead`、
`scaffold_plus_warhead`、`scaffold_only`、
`scaffold_plus_linker_plus_warhead`，没有新增 mask/task。

本次实际实施的最小生产修改只位于 `encode_role_mask_anchor_v1`：用现有字段派生
`original_valid & fixed & ~generation` 并只编码这些行，没有改变 checkpoint key、
tensor shape、10D 通道或模型结构。其他 conditioning 通道和外部设计约束语义仍需
后续审计；本轮不能据此宣称 clean 坐标、其他观测字段、hidden state 或
denoised-state 通道安全。

## 本轮状态

`PRODUCTION_CODE_MODIFIED=true`（仅当前未提交 working tree）；
`SYNTHETIC_AUXILIARY_FORWARD_EXECUTED=true`；
`SYNTHETIC_AUXILIARY_LOSS_EXECUTED=true`；`SYNTHETIC_AUTOGRAD_EXECUTED=true`；
`REAL_FFQ_TRAINING_TARGETS_CREATED=false`；
`REAL_SAMPLE_LOSS_MASKS_ENABLED=false`；`DIFFUSION_MODEL_FORWARD_EXECUTED=false`；
`CHECKPOINT_LOADED=false`；`OPTIMIZER_STEP_EXECUTED=false`；
`PARAMETER_UPDATE_PERFORMED=false`；`GLOBAL_TRAINING_AUDIT_CLOSED=false`；
`READY_FOR_TRAINING=false`；`TRAINING_STARTED=false`；`COMMIT_PERFORMED=false`；
`PUSH_PERFORMED=false`。

这是 feature-semantics audit 的限定可执行补充。Step12D 仍只代表 smoke legality；
准确 PRE 不是 V1 全局硬前置，历史 `UNKNOWN_ATOM_FEATURE_POLICY` /
`feature_semantics_known=False` 等全局训练前置并未由本轮关闭。
