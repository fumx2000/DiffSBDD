# CovaPIE Current11 Task2 Compiler Shared-Kernel Refactor V1

This increment only separates fresh authority acquisition from the existing
batch-local compiler semantics. The public slow API and its sole `__all__`
entry are unchanged. Each slow call still validates both roots, obtains fresh
`_authority` exactly once, and then calls the compiler-owned private kernel:

```python
_compile_with_verified_authority_v1(*, authority, observation)
```

The observation validation, Exact18 construction, Output Exact10 construction,
status and failure precedence, field order, provenance, readiness, debug and
joint handling, and deep-copy behavior were moved into that kernel without a
semantic rewrite. The kernel does not accept roots and performs no root
validation, authority discovery, gate or adapter call, Git operation,
filesystem access, formal-state poll, or input mutation. Fixture-only checks
prove exact slow/direct equality for four success cases and five representative
hard failures, deterministic repeated direct calls, and fresh built-in outputs.

No context module, context builder, context class, or fast public compiler API
is implemented here. No module cache, `lru_cache`, or first-call implicit cache
was added. The next authorized increment is the separate context module, which
will use this same private kernel.

Passing this increment makes the repository ready for context-module
implementation only. DataLoader integration remains not ready, and the public
remap adapter still requires its own hot-loop audit before that integration.
Model and loss integration remain not ready. Step12D remains a smoke legality
check rather than a final training-feature contract; feature semantics and the
historical unknown-atom policy must be re-audited before training, so
`ready_for_training=false`.
