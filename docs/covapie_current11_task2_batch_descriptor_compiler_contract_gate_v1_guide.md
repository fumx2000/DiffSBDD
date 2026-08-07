# CovaPIE Current11 Task 2 batch descriptor compiler contract gate V1

This gate freezes the pure, JSON-safe boundary between a future Current11 runtime batch observation compiler and the published Task 2 batch-index remap adapter. It does not implement the compiler, a runtime observation extractor, dataloader integration, model integration, a head, a loss, or training.

## Public API

`build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1(*, repo_root: Path, state_root: Path) -> dict[str, bytes]`

The function is keyword-only, deterministic, silent, read-only, and in-memory. It returns six artifacts in fixed order: a contract manifest, input schema, output schema, closed status vocabulary, reference vectors, and a self-excluded gate report. The stable digest frames only the first five artifacts with the `COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTRACT_GATE_V1` domain.

## Frozen boundary

The input has exactly 14 fields: ten required fields describing runtime schema, exact sample keys, role lengths, membership, joint layout, and virtual-node policy; plus four optional consistency/debug transport fields. Caller-provided source lineage, offsets, atom identity tables, provider overrides, inferred identity, model values, candidate labels, masks, and warhead inference fail closed.

Successful contract-level evaluation produces an Exact10 output containing a complete adapter-input Exact18. Source fields 1–10 are copied only from the published remap contract. Sample identity is expanded by exact Current11 row ID. Atom identity tables come only from the pinned Exact22 provider. Role offsets are computed as exclusive prefix sums. Hard failures always set the Exact18 value to null.

Gate readiness is system-level evidence and is independent of whether one reference observation is admitted. Every reference output therefore carries the same verified gate readiness. A rejected observation remains unambiguously rejected through its hard `compiler_status`, identical `failure_reason`, and null Exact18; it does not falsely revoke the already verified formal carrier, source contract, provider, or gate implementation readiness.

The source Exact10 validator requires an exact built-in dictionary, exact schema and lineage values, the frozen ordered Current11 identities, exact integer pair and offset containers, and exact boolean validity containers. Boolean values cannot masquerade as integers, floating-point values cannot masquerade as indices, sample identities must be complete nonempty trimmed strings, and row IDs must remain unique. The builder and private evaluator use this same validator so their source-drift semantics cannot diverge.

Debug dictionaries are transport-only and never identity authority. Recursive dictionaries, non-JSON-safe objects, encoding failures, and other supported JSON serialization failures are converted into `BATCH_OBSERVATION_SCHEMA_MISMATCH` with a null Exact18 rather than escaping from the private evaluator.

The closed vocabulary contains 15 statuses. `COMPILED_EXACT` is the only overall success. A null joint layout records `JOINT_LAYOUT_UNAVAILABLE` as a component status while preserving overall success. The reference matrix includes canonical, reverse, mixed, subset, no-joint, and empty successful batches plus fail-closed cases for schema, key, provider, role, length, membership, virtual-node, source override, and joint-layout failures.

## Authority and readiness

The gate independently verifies the published remap contract, the public adapter, the runtime carrier contract, and the formal runtime carrier Exact4. Stable artifacts bind the carrier canonical relative path, formal aggregate, Exact4 byte identities, names semantic digest, runtime schema, role-order schema, and no-virtual-node policy. They never bind the formal object's random nonce, inode, mtime, absolute path, or Git lifecycle state.

All six successful reference cases are submitted to the public adapter. This includes the empty batch and no-joint cases. Failure cases are not submitted. The design Markdown is non-runtime lineage only and is never read to build contract authority.

Tests snapshot raw `git status --short` bytes, the complete formal carrier alias/object/leaves, and the formal routing alias/object/leaves around an independent API build. They require byte-identical Git state and identical state metadata and content afterward. Import analysis handles `import` and `from ... import ...` separately so forbidden `ImportFrom` module roots cannot evade the stdlib/local-only guard.

Passing this gate makes the pure in-memory compiler implementation the next authorized increment. It does not authorize dataloader, model, forward, backbone, head, loss, checkpoint, or training changes. Step12D remains only a smoke legality check; a feature-semantics re-audit and resolution of the historical unknown-atom-feature policy remain mandatory before training.

## Checker

Run the checker with both roots:

```text
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python scripts/check_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1.py --repo-root /absolute/repository/path --state-root /absolute/covapie-state/path
```

Success prints one compact canonical JSON report line to stdout and nothing to stderr. Failure prints only `COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTRACT_GATE_V1_ERROR` to stderr and exits with status 1. The checker has no write, materialize, compiler, runtime-input, tensor, NumPy, dataloader, model, head, loss, or training options.
