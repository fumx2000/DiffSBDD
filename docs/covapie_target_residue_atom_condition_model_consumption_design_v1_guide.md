# CovaPIE target-residue atom condition model-consumption design V1

## 1. 本步是什么

本步只回答一个架构问题：已经由 runtime bridge 放进 pocket dictionary 的
`pocket_target_residue_atom_condition_indicator`，未来怎样在不破坏 DiffSBDD
checkpoint 的前提下影响模型 hidden representation。

本步没有实现模型消费，没有改 forward、loss、state dict 或 caller，也没有创建
Parameter、运行模型、训练、反向传播、optimizer step、commit 或 push。

## 2. Runtime bridge 与 model consumption 的区别

Runtime bridge 负责从目标 CYS-SG-S 选择器定位 full-atom pocket node，构建与 pocket
node order 对齐的 bool sidecar，并把它带到 pocket dictionary。正式 gate 已证明
Current11 的 11 个样本共有 2202 个 pocket nodes、11 个 True，而且每个样本恰好一个
True。

Model consumption 是下一层合同：sidecar 必须从 DDPM 顶层入口显式传入 dynamics，并
在 `EGNNDynamics` 中改变目标 node 的 hidden feature。当前代码尚未做这件事，所以
`indicator_consumed_by_model=false`、`indicator_passed_into_dynamics=false`。

## 3. 为什么 sidecar 已进入 pocket，模型仍未使用

`LigandPocketDDPM.get_ligand_and_pocket()` 和 `prepare_pocket()` 会保留 sidecar，但
`ConditionalDDPM`、`EnVariationalDiffusion` 现有的 `self.dynamics(...)` 调用只传
ligand/pocket 的 `xh`、time 和 batch masks。`EGNNDynamics.forward()` 也没有对应参数。
因此 dictionary 中有 key 不等于神经网络已经消费该语义。

## 4. 冻结的 checkpoint 事实

正式 checkpoint 是 `crossdocked_fullatom_cond.ckpt`，实际元数据而不是文件名推断为：

- `mode=pocket_conditioning`
- `pocket_representation=full-atom`
- `joint_nf=32`
- `atom_nf=10`
- `residue_nf=10`
- `condition_time=true`，由默认构造语义和 EGNN 输入宽度 `33=32+1` 共同确认
- state dict 有 122 个 keys，其中 120 个使用 `ddpm.dynamics.` 前缀
- ordered-key manifest SHA256 为
  `3ff753379384502f43a65ea8e9116a47d08a404420966b4fd671c307ad98faaa`
- shape/dtype manifest SHA256 为
  `94e426ea3d114d50dbac63f2f8af7b3f5c14ca97df8a99afebbd3838473c0692`

## 5. 为什么不能 append 到 one-hot

把 indicator append 到 pocket one-hot 会把 `residue_nf` 从 10 改成 11，直接改变
`residue_encoder.0.weight` 的输入 shape。旧 checkpoint 对应 tensor 是 `[20, 10]`，
strict load 将不再兼容。此外，target identity 是静态条件语义，不是需要归一化和加噪
的扩散 feature。

把 indicator append 到 time channel 同样不可行：它会把 EGNN `in_node_nf` 从 33
改成 34，改变第一层 weight shape，并混淆 timestep 与 target identity。

## 6. 选中的架构

选中候选是：

`optional_zero_initialized_target_node_embedding_after_residue_encoder`

冻结合同如下：

- condition representation：`same_name_per_pocket_node_bool_sidecar`
- enable flag：`target_residue_atom_conditioning=false`
- dynamics 参数：`pocket_target_residue_atom_condition_indicator=None`
- injection module：`EGNNDynamics`
- injection point：
  `after_residue_encoder_before_atom_residue_concatenation_and_before_time_concatenation`
- Parameter：`target_residue_atom_condition_embedding`
- shape：`[joint_nf]`，本 checkpoint 中是 `[32]`
- initialization：全零
- coordinates、edges、masks 和 time feature：均不直接注入

未来语义等价于：

```python
h_residues = self.residue_encoder(h_residues)

if pocket_target_residue_atom_condition_indicator is not None:
    h_residues = h_residues + (
        pocket_target_residue_atom_condition_indicator
        .to(device=h_residues.device, dtype=h_residues.dtype)
        .unsqueeze(1)
        * self.target_residue_atom_condition_embedding.unsqueeze(0)
    )
```

这段代码只说明未来语义，不是本步实现授权。

## 7. 为什么在 residue encoder 之后注入

`atom_encoder` 与 `residue_encoder` 已经把两种输入映射到共同的 `joint_nf` 空间。在
residue encoder 之后加一个 `[joint_nf]` 向量，不需要改变 atom/residue one-hot
宽度、encoder weight shape 或 EGNN 输入宽度。注入又发生在 atom/residue 合并和 time
拼接之前，因此只有 pocket hidden rows 接收该条件，time channel 仍保持原义。

## 8. 为什么只加到目标 pocket node

indicator 是逐 pocket node、与 node order 对齐的 bool tensor。乘法只选择 True 所在
的 hidden row：目标 row 加 embedding，非目标 pocket rows 在注入点不变，ligand rows
不直接添加 embedding。随后现有 EGNN edges 和 message passing 可以把目标信息传播到
ligand 与其他 pocket nodes。

## 9. 为什么保持 E(3) 等变性

indicator 是旋转和平移不变的标量标签，embedding 只进入 scalar hidden features；它
不进入坐标、不改变距离、不重建 edges，也不改变 coordinate-update mask。平移或旋转
坐标不会改变注入值；同步置换 pocket nodes、pocket mask 和 indicator 时，注入 row 也
随置换。因此 translation、rotation 与 node-permutation equivariance 保持，reflection
policy 与原模型一致。

当前 checkpoint 的 `reflection_equivariant=False` 是原模型事实；本设计不扩大或缩小
该 policy。

## 10. 为什么 condition 不做 normalization 或 diffusion noise

Target indicator 是静态离散语义，不是 `xh_pocket` 的一部分。它不 normalized、noised、
centered、rotated、decoded，也不贡献 reconstruction loss。`normalize()` 可以继续让
pocket dictionary 保留这个 key，但不得修改它的 bool dtype 或值。同一 tensor 在每个
denoising timestep 重复使用。

## 11. 为什么 zero initialization 保证初始 parity

当 embedding 为零时，`indicator * embedding` 对每个 row 都为零。因此：

- disabled + absent 与 base 模型完全一致，state key 也完全一致；
- enabled + absent 不执行注入，输出与 base 一致；
- enabled + present + zero embedding 的注入仍为零，输出与 base 一致；
- enabled + present + nonzero embedding 才在注入点改变目标 row。

代数 Jacobian 对目标 row 是 identity、对非目标 row 是 zero，所以未来训练时梯度路径
可以到达该 Parameter；本设计只用 synthetic algebra oracle 证明这一点，没有运行真实
模型或反向传播。

## 12. Disabled checkpoint profile

`target_residue_atom_conditioning=false` 时，推荐使用：

```python
self.register_parameter("target_residue_atom_condition_embedding", None)
```

于是新名称不出现在 state dict，现有 key 集合和 tensor shapes 完全不变，旧 checkpoint
继续 `strict=True` 加载，missing/unexpected keys 都为空。默认 flag 必须是 false，确保旧
checkpoint 的 hyperparameters 中没有该字段时仍走 legacy profile。

## 13. Base checkpoint 到 conditioned model 的迁移 profile

启用 flag 后，完整新 key 必须是：

`ddpm.dynamics.target_residue_atom_condition_embedding`

迁移步骤必须严格限定为：把旧 checkpoint 读入内存副本；构建 conditioned model；比较
共享 keys 和 shapes；确认旧 checkpoint 只缺这个精确 key；用当前模型中全零初始化的
tensor 填入；最后执行 `load_state_dict(..., strict=True)`，并要求最终 missing/unexpected
均为空。磁盘 checkpoint 不得修改，也不得自动 reshape 旧 tensor。

## 14. Conditioned checkpoint strict profile

含新 key 的未来 conditioned checkpoint 必须以
`target_residue_atom_conditioning=true` 构造，并严格加载。不能退回宽松加载。

Blanket `strict=False` 会掩盖拼写错误、遗漏传播、unexpected keys 和其他 architecture
drift，无法证明“只新增一个 key”。仓库中历史 pretrained smoke 的局部 `strict=False`
只属于旧 smoke，不得复用于本迁移。

## 15. Condition 存在性与验证边界

采用 `top_level_validate_once_then_thread_static_tensor`：

- legacy absent：key 缺失，flag 可 false 或 true，不添加 embedding；
- covalent present：必须是 `torch.bool`、1D、长度等于 pocket node 数、每个 sample
  恰好一个 True，并要求 flag=true；
- present + flag=false：fail closed，不能静默忽略；
- present all-false：拒绝，语义暂缓；
- mixed covalent/noncovalent same batch：暂缓，因为尚无正式 per-sample presence mask。

完整 cardinality 扫描只在 DDPM 顶层入口做一次。`EGNNDynamics.forward()` 仅做轻量
防御检查：None，或 bool/1D/长度等于 `len(xh_residues)`；它不重新猜测 sample
cardinality。

## 16. Conditional 训练、评估与采样路径

当前 `ConditionalDDPM` 的四个直接 dynamics 位置全部审计：

| 当前位置 | 用途 | 未来来源 |
|---|---|---|
| `conditional_model.py:253` | forward 主 timestep，训练与评估 | forward 顶层一次验证 |
| `conditional_model.py:306` | 评估额外 t=0 | 与主 timestep 同一静态 tensor |
| `conditional_model.py:445` | 每个反向采样 timestep | sample/diversify/inpaint 顶层 tensor |
| `conditional_model.py:119` | 最终 `p(x,h|z0)` | 与迭代采样同一 tensor |

`sample_given_pocket()`、`diversify()` 和 conditional `inpaint()` 都必须显式把同名可选
参数传到 `sample_p_zs_given_zt()` 与 `sample_p_xh_given_z0()`；不能把 indicator 放进
`**kwargs`、global、hook 或 module mutable current-mask state。

## 17. Joint training 与 inpainting 路径

`EnVariationalDiffusion` 的四个直接位置也全部审计：

| 当前位置 | 用途 |
|---|---|
| `en_diffusion.py:378` | joint forward 主 timestep |
| `en_diffusion.py:436` | joint 评估 t=0 |
| `en_diffusion.py:516` | joint sample/inpaint 迭代 timestep |
| `en_diffusion.py:270` | joint sample/inpaint 最终 `p(x,h|z0)` |

Joint forward 和 joint inpaint 能从输入 pocket dictionary 获得 sidecar，并在顶层验证
一次。Unconditional joint `sample()` 自己生成 pocket，没有输入 target identity；它保持
absent profile，不凭空猜目标 node。

## 18. SimpleConditionalDDPM 的处理

`SimpleConditionalDDPM.forward()` 和 `sample_given_pocket()` 是实际 override，未来都必须
在 signature 中增加同名可选参数，并显式传给 `super()`，不能假设继承自动覆盖。
Conditional `inpaint()` 被继承，可使用同一顶层合同。

当前 `LigandPocketDDPM.generate_ligands()` 的 exact-type branch 不支持
`SimpleConditionalDDPM`，会进入 `NotImplementedError`。这个既有 profile 是明确
fail closed，不会静默丢 condition，因此不阻断模型消费实现设计；它也不授权本步修改
caller。

## 19. CLI selector forwarding 与五级 mask

Repository CLI 尚未把 target selector 全面 forward，这由 runtime gate 明确记录为
false。CLI selector forwarding 是独立后续边界，不阻断本次 architecture design，也不在
本步修改任何 caller。

Ligand mask 语义保持精确五级：

1. `warhead_only` / A
2. `linker_plus_warhead` / B
3. `scaffold_plus_warhead` / B2
4. `scaffold_only` / B3
5. `scaffold_plus_linker_plus_warhead` / C

Target pocket condition 不会新增第六种 mask，也不会省略 `scaffold_only`。

## 20. Runtime bridge gate commit 的 post-commit 生命周期

`148689cc0716a56f3eb991f762af0010c5849f3a` 是本设计绑定的 runtime bridge gate
冻结祖先，不是永久要求的当前 branch tip。设计 API 必须支持三个正常状态：设计文件仍
未提交时，HEAD 和 `origin/main` 都可等于 gate commit；设计提交但尚未 push 时，HEAD
可以位于 successor commit 而 `origin/main` 仍位于 gate commit；提交并 push 后，HEAD
和 `origin/main` 都可以位于 successor commit。

因此 post-commit 校验使用 `git merge-base --is-ancestor`，分别要求 gate commit 是
`HEAD` 和 `origin/main` 的祖先或与其相等，而不再要求两个 refs 精确等于 gate commit，
也不要求 API 运行时 HEAD 必须始终等于 `origin/main`。Gate commit 的唯一 parent、gate
production 在该 commit 中的 bytes、当前 working-tree bytes 与冻结 SHA 仍继续精确
绑定，lineage 强度没有降低。

这次生命周期修订不改变 model-consumption 架构、Exact47、checkpoint 审计、response
SHA、readiness 或 recommended next step。

## 21. 下一步实现范围与训练边界

审计无未解决 blocker，因此设计结论是：

- `ready_for_model_consumption_implementation=true`
- `recommended_next_step=implement_covapie_target_residue_atom_condition_model_consumption_v1`

未来实现预计修改 `lightning_modules.py`、`equivariant_diffusion/dynamics.py`、
`equivariant_diffusion/conditional_model.py` 和 `equivariant_diffusion/en_diffusion.py`。
源码证据支持 `equivariant_diffusion/egnn_new.py` 保持不变；`dataset.py`、collate、runtime
bridge gate、正式 bundles 与 checkpoint 也保持不变。

实现 model consumption 仍不等于可以训练。Step12D 只是 smoke legality check，不是最终
training-feature contract。正式训练、fine-tuning、backward、optimizer step 或任何参数
更新之前，仍必须完成 feature-semantics audit，并正式解决或审计历史
`UNKNOWN_ATOM_FEATURE_POLICY` 与 `feature_semantics_known=False` 状态。
