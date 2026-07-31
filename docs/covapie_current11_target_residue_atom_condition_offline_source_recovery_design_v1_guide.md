# Current11 target-residue atom-condition 离线源恢复设计 V1

## 这一步回答什么问题

正式 source inventory 的 `resolved_unique_sample_count=0/11` 表示：按当时 inventory 能直接看见并验证的字段，没有任何样本已经具备可物化 condition authority 的完整、唯一证据。它不表示 11 个样本都没有蛋白靶原子，也不表示原始结构一定丢失。

每个样本的 21 个未来必需字段中已有 4 个、缺 17 个。这里的“缺”是 schema 和 lineage 层面的结论：字段没有出现在正式 inventory 可验证的位置，或缺少规范化 provenance。已有 locator sidecar、protein atom table 与本地 raw mmCIF 可能仍包含恢复这些字段所需的信息。本设计只读地核查这种可能性。

## 为什么不能给 protein table 改列名

generic protein atom table 有 atom-site ID、元素、原子名、残基、chain、坐标、occupancy、altloc、model 和 raw 文件 locator，适合交叉验证。但它没有完整保留 mmCIF auth/label 字段语义，也没有独立建立 exact raw bytes、目标行和 canonical condition evidence 之间的权威 lineage。把 `atom_name` 改名为 `protein_auth_atom_id` 不会补回缺失的 namespace 或 provenance，因此不能把普通派生表“升级”为 authority。

locator sidecar 提供 sample-preparation/PDB 绑定、raw 相对路径、claimed SHA、`matched_atom_site_id`、auth/label residue locator，以及 struct_conn/atom_site insertion 的原始 token 和一致性状态。它仍不替代 raw `_atom_site` 行：model、component、element、altloc、完整 auth/label crosswalk 必须从 exact raw row 实际观察并与其他来源交叉验证。

Formal source inventory 不只冻结 sample index 和 locator sidecar，也已经为每个样本记录 protein atom table 的 locator、状态和 exact-byte SHA。Offline recovery 必须读取同一路径上的同一份 table bytes；否则可能把旧 formal inventory 与物化后发生变化的新 table 混合，形成错误 provenance。formal artifact record 提供的是跨步骤 snapshot binding；evaluator 在函数结束前重新读取首次看到的 bytes，提供的是调用内不变性。两项检查覆盖不同时间边界，并不重复。raw structure 仍可按 locator sidecar 做离线恢复可行性审计；本 revision 不补 raw 数据，也不创建 evidence 或 authority。

## 为什么回到 exact raw mmCIF

raw 文件是所选 `_atom_site` 行的最接近源证据。设计只接受 locator sidecar 和 protein table 已声明且彼此一致的安全仓库内相对路径；不依据 PDB ID 猜路径，不联网，也不下载。

对 `.gz` 文件，filesystem SHA256 针对磁盘上的 exact compressed bytes。解压后的 mmCIF 内容是解析输入，但不是这个 filesystem SHA 的替代品。解压只在内存中进行，带大小上限；损坏、截断或异常膨胀的 gzip 会 fail closed，且不会写出解压文件。

`matched_atom_site_id` 是唯一 selector。raw `_atom_site.id` 必须恰好匹配一行。零行与多行都阻断恢复。occupancy 只是被交叉验证的数据，不能用于选行；nearest-neighbour、唯一 CYS、atom-name fallback 同样禁止，否则会把猜测伪装成 source evidence。

## auth、label、insertion 与 altloc

mmCIF auth namespace 保留作者使用的 chain、residue sequence 和 atom identity；label namespace 是 mmCIF 的标准化 crosswalk。两者不能互相代替。本设计分别恢复并核对 auth/label chain、component、sequence 和 atom 字段。

`pdbx_PDB_ins_code` 与 `label_alt_id` 的 raw `.` 和 `?` 含义不同，必须保留它们来自哪个列、原始 token 是什么，再按 committed contract 规范化为空字符串。真实 altloc（例如历史样本中的 `B`）必须原样保留。缺列时不能默认空；model 也不能默认成 1。locator sidecar 的 struct_conn insertion 与 raw atom_site insertion 必须明确一致，否则状态为 `blocked_insertion_provenance`。

## 输出边界

reference evaluator 返回纯内存 Exact14 response，每个样本含一个 Exact20 feasibility record。只有 raw bytes SHA、唯一 atom-site 行、sample/locator/protein-table lineage、CYS/SG/S scope 和 insertion provenance 全部通过时，才在内存中构造 proposed canonical condition-evidence record 及其 digest。

proposed evidence 不是 authority。它只是证明未来 compiler 有足够、可重复验证的输入。本步不会创建 enriched source inventory、evidence 文件、condition authority、adapter、label、tensor 或训练输入；不会修改 sample index、locator sidecar、protein table 或 raw structure，也不会进行网络访问。

只有 11/11 都为 `recoverable_offline_unique` 时，下一步才是实现 `implement_covapie_current11_target_residue_atom_condition_source_evidence_compiler_v1`。否则 response 会根据实际主要 blocker 推荐一个独立的修复步骤，但本步不执行该步骤。

## 与训练 readiness 的关系

离线 source recovery 可行，只说明 condition evidence 的来源可以被严格重建，不等于可训练。正式训练或任何参数更新之前仍必须完成 feature-semantics audit，解决历史 `UNKNOWN_ATOM_FEATURE_POLICY` 与 `feature_semantics_known=False` 状态。Step12D 仍只是 smoke legality check，不是最终 training-feature contract。
