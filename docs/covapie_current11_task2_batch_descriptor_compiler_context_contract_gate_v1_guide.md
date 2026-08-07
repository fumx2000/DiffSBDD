# CovaPIE Current11 Task2 Compiler Context Contract Gate V1

This is a contract-only increment for moving verified compiler authority out of the per-batch hot loop. It does not implement a context, fast compiler, cache, shared-kernel refactor, DataLoader integration, model integration, loss integration, or training. It does not modify the existing compiler, runtime observation extractor, or public remap adapter.

## Contract gate API and Exact6

The gate module exports exactly one keyword-only function:

```python
build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, bytes]
```

It validates canonical roots, invokes the existing compiler's private `_authority(repo, state)` exactly once, validates the resulting Source Exact10, 11-sample/22-role provider, and readiness template, and returns this deterministic in-memory Exact6:

1. `current11_task2_batch_descriptor_compiler_context_contract_manifest.json`
2. `current11_task2_batch_descriptor_compiler_context_schema.json`
3. `current11_task2_batch_descriptor_compiler_context_api_and_error_contract.json`
4. `current11_task2_batch_descriptor_compiler_context_reference_vectors.json`
5. `current11_task2_batch_descriptor_compiler_context_acceptance_matrix.json`
6. `current11_task2_batch_descriptor_compiler_context_contract_gate_report.json`

The first five artifacts participate in the stable contract digest. Framing is SHA256 over the domain followed, for each artifact in that exact order, by its UTF-8 name and bytes, each preceded by an unsigned 64-bit big-endian byte length. The report is self-excluded. No artifact is written to the repository or state root.

The compiler product commit and its pre-refactor source SHA256 are predecessor provenance. The source SHA is explicitly not a permanent future checker admission condition because the approved product increment will change private compiler bytes. Repository admission instead requires branch `main`, existence of predecessor commit `463c481b65a68442f19b9f1b417ce2325434785f`, and that commit being an ancestor of or equal to current `HEAD`. Equality between `HEAD`, the base, and `origin/main` is not required.

## Frozen future APIs and placement

The future module is:

```text
src/covalent_ext/covapie_current11_task2_batch_descriptor_compiler_context_v1.py
```

Its `__all__` is exactly:

```python
(
    "build_covapie_current11_task2_batch_descriptor_compiler_context_v1",
    "compile_covapie_current11_task2_batch_descriptor_with_context_v1",
)
```

The keyword-only signatures are:

```python
build_covapie_current11_task2_batch_descriptor_compiler_context_v1(
    *, repo_root: Path, state_root: Path,
) -> object

compile_covapie_current11_task2_batch_descriptor_with_context_v1(
    *, context: object, observation: dict[str, object],
) -> dict[str, object]
```

No context class is public. The existing compiler module continues to export only `compile_covapie_current11_task2_batch_descriptor_v1`, with its existing keyword-only `repo_root`, `state_root`, and `observation` signature and fresh-authority semantics unchanged.

## Option 2 shared-kernel architecture

The contract selects Option 2. The existing compiler will own one private pure batch-local kernel, conceptually `_compile_with_verified_authority_v1(*, authority, observation)`. The current observation validation body, Exact18 construction, `_output` behavior, status precedence, deep-copy behavior, provenance, and readiness remain single-sourced there.

The existing slow API validates roots, invokes fresh `_authority` exactly once, and calls the shared kernel. The context builder validates roots, invokes `_authority` exactly once, deeply freezes the verified snapshot, and seals an opaque context. The fast API performs only O(1) context checks and calls the same kernel.

Production monkeypatching, duplicated observation validation, duplicated Exact18 construction, duplicated output logic, module/global caches, `lru_cache`, and first-call implicit caches are forbidden. The fast path performs no root validation, gate call, adapter call, Git call, filesystem/formal read, state poll, or `_authority` call.

## Immutable context and authority snapshot

The context schema version is `covapie_current11_task2_batch_descriptor_compiler_context_v1`. The preferred representation is a private `@dataclass(frozen=True, slots=True, repr=False)` with private frozen nested records and tuples. An equivalent implementation is allowed only if it provides the same exact-type, deep-immutability, opacity, and representation guarantees. No built-in list or dictionary may be reachable from the context. There is no public constructor, mutation method, or data-rich representation.

Semantic fields include the context schema version; compiler product commit; compiler contract commit and digest; provider digest; formal carrier aggregate and NPZ SHA256; source/remap contract digest; authority snapshot digest; complete Source Exact10; complete 11-sample/22-role provider; and exact compiler readiness template. A module-private construction seal is an integrity field, not semantic identity.

Absolute repository/state paths, `origin/main`, ahead/behind state, device, inode, mtime, formal hidden-object nonce, timestamps, and random nonces are excluded from semantic identity.

The authority digest uses UTF-8 canonical compact JSON with `sort_keys=True`, `ensure_ascii=True`, `allow_nan=False`, and separators `(',', ':')`. Framing is:

```text
SHA256(
  COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_AUTHORITY_SNAPSHOT_V1\0
  || uint64be(payload_bytes)
  || payload
)
```

The artifacts record the digest, domain in escaped and hexadecimal forms, complete canonical semantic snapshot, explicit schema/field orders, and separate provenance, source, provider, and readiness component digests. Python `repr`, pickle bytes, and `hash()` are not digest framing.

## Freshness, integrity, and process semantics

A context means “the immutable authority snapshot verified at builder time.” External repository or formal-state drift after building does not alter or invalidate that already-built snapshot during fast use. A caller requiring fresh disk authority explicitly rebuilds the context. The existing slow API continues to rediscover drift on its next call. No mtime/inode poll or silent authority switch occurs per batch.

Fast validation checks the exact private type, exact schema version, fixed compiler/contract/provider/formal/source digests, stored authority digest, and module-private construction seal in O(1). It does not rehash the provider or recanonicalize the snapshot. This is a programming-contract integrity boundary, not a cryptographic boundary against hostile code in the same process; reflection and `object.__setattr__` are outside the promise.

V1 is explicitly non-pickleable: `__reduce__` and `__reduce_ex__` fail. Every process and every DDP rank explicitly builds once after process initialization. Contexts are not shared across ranks, sent through collectives, stored in checkpoints, passed into Dataset or DataLoader workers, or built inside workers. The rank/main-process flow is `batch -> extractor -> fast compiler(context)`.

## Output and error contract

For the same valid authority and observation, slow and fast outputs are exactly deep-equal built-in structures. This includes Output Exact10 and Exact18 field order and values, statuses, failure reasons, sample outcomes, source/provider data, lengths, offsets, memberships, joint/debug values, provenance, and readiness. Compiler output is not changed to advertise context reuse; reuse evidence belongs only to the context checker/report.

The future fixed token is:

```text
COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_V1_ERROR
```

The existing slow API retains `COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_V1_ERROR`. Builder root/authority/gate/formal/provider failures raise the context token and retain the compiler-token exception as `__cause__`. Wrong-type, wrong-schema, wrong-digest, wrong-provider, unsealed, or reconstructed contexts raise the context token before evaluating observations. A valid context plus malformed observation returns the existing compiler hard-failure Exact10 and does not raise the context token. Unexpected fast shared-kernel invariants use the context token; the slow path retains the compiler token.

The reference vectors freeze complete existing slow outputs and domain-separated output digests for `canonical`, `reversed`, `subset_10_4_0`, and `singleton_10`. They also freeze exact hard-failure outputs for `source_contract_override`, `duplicate_runtime_key`, `wrong_ligand_length`, `wrong_ligand_membership`, and `unknown_joint_descriptor`, plus five invalid-context expectations. The gate uses the already-published pure compiler contract evaluator and compiler `_output`; it does not call the slow public compiler repeatedly or call the adapter.

## Performance acceptance and readiness

There is no absolute latency SLA. The design audit's single-shot `[10,4,0]` timings are directional evidence only. Acceptance is structural: builder `_authority` count one; fast `_authority`, gate, adapter, Git, filesystem, and formal-read counts zero; and exact slow/fast parity across the frozen cases. The Exact16 acceptance matrix also freezes hard-failure parity, drift failure, deep immutability, non-pickleability, no hidden cache, and no checkpoint/model/DataLoader interaction.

Passing this gate means `ready_for_compiler_hot_loop_authority_context_implementation=true`. It does not implement the context or shared kernel. `ready_for_dataloader_integration=false`, and the public remap adapter's own hot-loop audit remains required before that integration. Model/loss integration remains false. Feature semantics must be re-audited before training; Step12D remains a smoke legality check rather than the final training-feature contract. `ready_for_training=false`, with no checkpoint bytes read and no checkpoint/model shape change required.

## Checker

Run exactly once for live authority grounding:

```bash
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 \
python scripts/check_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1.py \
  --repo-root /absolute/path/to/DiffSBDD-base \
  --state-root /absolute/path/to/covapie-state
```

The checker accepts only `--repo-root` and `--state-root`, calls the public gate exactly once, validates the Exact6 and both digests directly, and proves repository plus formal carrier/routing state are unchanged. Success writes one compact JSON line to stdout with `status=PASS_CONTRACT_ONLY`; failure writes only the fixed contract-gate token to stderr and exits 1.

Fast unit tests replace compiler `_authority` with a deterministic in-memory fixture. They do not execute the live predecessor chain. The standalone checker is the unique live path for this increment.
