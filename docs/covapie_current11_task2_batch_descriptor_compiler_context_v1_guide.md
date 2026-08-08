# CovaPIE Current11 Task2 Compiler Context V1

This product builds one private, sealed, deeply immutable authority context per
process and reuses it for batch-local compilation. A DDP job builds one context
independently in each rank's main process. The context is not transported to a
Dataset, a DataLoader worker, another rank, or a checkpoint.

The builder validates both canonical roots, obtains fresh compiler authority
exactly once, verifies the published canonical authority-snapshot digest, and
freezes the source Exact10, identity-provider Exact11, and readiness template.
It has no hidden global, LRU, or first-call cache. The context is deliberately
non-pickleable and exposes no public class or mutation API.

The fast API performs only O(1) fixed-provenance and construction-seal checks.
For each batch it deterministically thaws fresh temporary built-in source,
provider, and readiness objects, then calls the compiler-owned private shared
kernel. This small thaw covers only the fixed Current11 authority. No mutable
authority is stored in the context, and no authority discovery, root check,
gate, Git operation, filesystem/formal read, or adapter call occurs on the fast
path.

The existing public slow compiler API remains unchanged and continues to obtain
fresh authority on every call. Slow and fast compilation produce exactly the
same Output Exact10 and adapter Exact18, including field order, failures,
provenance, and readiness; context reuse adds no output metadata. Context
programming-contract failures use
`COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_V1_ERROR`.

The public remap adapter still rebuilds authority on each call and is the next
hot-loop blocker. Therefore DataLoader, model, loss, and training integration
remain not ready. Step12D was only a smoke legality check: feature semantics and
the historical unknown-atom policy must be re-audited before any training.
