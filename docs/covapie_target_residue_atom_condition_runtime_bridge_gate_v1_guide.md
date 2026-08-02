# CovaPIE target-residue atom-condition runtime bridge gate V1

Runtime bridge 是已经进入 `lightning_modules.py` 的传递机制：它把 Current11 的布尔 sidecar 从 collated batch 放进 pocket，也让外部 Python API 可用 Exact6 selector 构造同一 sidecar。Runtime bridge gate 则是独立的 successor 证据层；它冻结、重跑并审计这套机制，但不再实现机制本身。

因此本 gate 不修改 Lightning。它绑定实现提交 `75589a94235dde2d0943606e58a1f2216b31d3b2`、其唯一父提交 `6f3ba8eb0dcb2982a14f5bdc0c7319b0a4e79250`，以及提交中四个 runtime 文件的精确字节。实现提交只需是当前 HEAD 的 ancestor 或等于 HEAD，而不是永久要求 HEAD 等于该提交；这样未来提交本 gate 后仍能执行生命周期检查。

## Current11 runtime 证据

Gate 从四份正式 predecessor bundle 读取 11 个 adapter record、alignment record 和 retained pocket atom table。它重新生成正式 retained 坐标及 10 维 one-hot，以 adapter indicator 构造真实 synthetic collated batch，再调用从当前 Lightning AST 隔离加载的真实 `get_ligand_and_pocket()`。结果必须是 11 个样本、2202 个 pocket node、11 个 true。

每个样本同时验证 local index 和 flat index。local index 证明 true 位于本样本正确的 retained node；flat index 证明 11 个 sample block 拼接后偏移量仍正确。只验证其中一个无法排除样本块长度或拼接顺序发生漂移。每个 true row 还必须在 10 维 one-hot 中只有 feature index 3 为 1，因为这把 indicator 重新连回 checkpoint vocabulary 中的 S，而不是只验证一个抽象布尔位置。

每条 Current11 输出是 Exact20 record，并有排除自身 digest 字段计算的 canonical SHA256。正式 bundle 是 Exact39，也使用相同的内部 digest 规则。整个 JSON 使用 UTF-8、ASCII escaping、排序 key、紧凑 separators、禁止 NaN，且没有末尾换行。

Record self digest 只证明该 record 内部自洽，bundle self digest 也只证明整个 JSON 在重新签名后内部自洽；二者都不能单独证明 lineage 正确。因此 validator 还把 11 条 record 的 sample、PDB ID、adapter record SHA、retained count、local/flat index 和 mask sample ID 投影回正式 adapter lineage，并绑定该 projection 的 canonical SHA256。Flat index 必须由所有前序 record 的 retained count 加当前 local index 推导。即使攻击者在两个 record 之间用 `+1/-1` 补偿 count、让总数仍为 2202，并重算所有 record 与 bundle digest，也会因正式 lineage 不匹配而被拒绝。本次 validator 修订不改变任何正式 record、正式 bundle、runtime 结果或 readiness。

## Legacy、external 和分支边界

字段缺失时，当前和 base commit 的 `get_ligand_and_pocket()` 返回 arity、key 顺序和全部 tensor 必须完全一致，目标 key 必须缺失，不能悄悄增加 all-false tensor。`prepare_pocket()` 分别对 CA 和 full-atom representation 做同样的 base/current parity。

External 路径使用 Exact6：chain、residue number、blank insertion code、CYS、SG、S。Synthetic full-atom 顺序是 `ALA CA, CYS CA, CYS SG, CYS N`，所以 target local index 必须为 2。Gate 验证 repeats=1 和 repeats=3；三次 repeat 的 true index 必须为 2、6、10，且 `mask[indicator]` 必须为 0、1、2。selector 输入保持不变。多余/缺失字段、错误类型或残基/原子/元素、CA selector、目标缺失或重复、disorder、非空 altloc、缺少 S vocabulary，以及非法 repeats 都 fail closed。

Gate 用 fake DDPM branch 调用真实 `generate_ligands()`，不调用真实 model forward。Conditional 和 inpainting 都必须接收 `prepare_pocket()` 返回的同一个 pocket object，sidecar 保持在该对象中；selector 只能进入 `prepare_pocket()`，不能进入 sampler 或 inpaint kwargs。这只证明 sidecar 被携带到分支入口，不证明模型、dynamics 或 loss 已经读取它。

## 为什么冻结旧 gate 而不重跑

Adapter gate、runtime bridge design 和 external-path resolution 是实现前的 source-freeze 合同。授权的 Lightning successor 变更发生后，要求这些旧 evaluator 在当前源码上继续绿色会混淆历史证据与新有效状态。本 gate 只 exact-byte 绑定旧 production、正式 bundle、schema 和 digest，并明确由本 successor 的 runtime 证据取代其源码时点判断；它不会修改或重新解释历史 SHA。

## Checkpoint、caller 和下一步

Gate 绑定原 checkpoint 的 size 与 SHA，冻结 dataset、Conditional DDPM、diffusion、dynamics，以及六个旧 repository caller。AST 差分只允许 `get_ligand_and_pocket`、`prepare_pocket`、`generate_ligands` 和四个 helper 变化；forward、训练/评估方法、其他类、imports、参数、buffer 和 one-hot width 均保持不变。因此 checkpoint compatibility 被保留。

Repository CLI 仍未显式转发 selector，但这不阻断下一步设计：当前 Python API 已有显式 selector 入口，且 gate 已冻结 runtime 传递。下一步 `design_covapie_target_residue_atom_condition_model_consumption_v1` 的含义是先设计模型如何消费 sidecar；本 gate 不实现 consumption，也不授权训练。

Canonical mask 合同仍只有五个语义任务：`warhead_only`、`linker_plus_warhead`、`scaffold_plus_warhead`、`scaffold_only`、`scaffold_plus_linker_plus_warhead`。Runtime sidecar 不增加第六个 mask，`scaffold_only` 也不能被遗漏。

即使 gate 通过，`indicator_consumed_by_model=false`、`indicator_passed_into_dynamics=false` 仍成立。正式训练前仍必须进行 feature-semantics audit：Step12D 只是 smoke legality check，不是最终训练特征合同；历史 `UNKNOWN_ATOM_FEATURE_POLICY` 与 `feature_semantics_known=False` 必须先被正式解决或审计。

Formal materializer 只在输出目录内创建临时文件，以 hard-link publication 实现不覆盖发布。相同 bytes 的既有文件返回 `idempotent_existing`，inode、mtime 和 bytes 不变；不同 bytes、symlink、错误 mode 或多 hard-link 均 fail closed，且临时文件会被清理。
