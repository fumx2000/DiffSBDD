# CovaPIE Current11 Task2 compiler/remap-context handoff contract gate V1

## Scope

This gate freezes Option B, `additive_compiler_context_successor_from_published_remap_context_v1`. It creates six deterministic contract artifacts in memory and writes none of them to the repository or state root. It does not implement the future bridge, call a remap-context builder, parse stable5, acquire historical compiler authority, access CUDA, integrate a DataLoader, touch model/loss code, read a checkpoint, or train.

The gate source exports exactly:

```python
build_covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, bytes]
```

All ordinary root, identity, schema, source, design-report, or mapping failures close to:

```text
COVAPIE_CURRENT11_TASK2_COMPILER_REMAP_CONTEXT_HANDOFF_CONTRACT_GATE_V1_ERROR
```

`KeyboardInterrupt` and `SystemExit` are not converted into the gate error.

## In-memory Exact6

The returned built-in dictionary has this exact order:

1. `current11_task2_compiler_remap_context_handoff_contract_manifest.json`
2. `current11_task2_compiler_remap_context_handoff_context_schema.json`
3. `current11_task2_compiler_remap_context_handoff_api_and_error_contract.json`
4. `current11_task2_compiler_remap_context_handoff_reference_vectors.json`
5. `current11_task2_compiler_remap_context_handoff_acceptance_matrix.json`
6. `current11_task2_compiler_remap_context_handoff_contract_gate_report.json`

The first five artifacts participate in the domain-separated framed stable digest. The report is self-excluded. Every artifact is canonical UTF-8 JSON with LF endings, one terminal LF, no BOM/NUL/CR, finite built-in JSON types only, and deterministic bytes.

The stable digest and known-vector digest are emitted by the standalone checker. Neither digest depends on timestamps, absolute paths, filesystem devices, inodes, mtimes, working-tree state, or the current HEAD.

The verified precommit candidate values are:

```text
stable_contract_digest=7de09322699eb9529486f49f5e5c1367317d63143e967f6223b010a4ef972c78
known_vector_digest=bae265a068b9c7b3fcedd7edcee5946b881e1000d82b21debb22202332ac0ce5
```

## Frozen predecessors and trusted-owner boundary

The gate verifies the byte identity, Git blob, and last-change commit of the published adapter context, adapter hot-loop gate, historical compiler context, historical compiler-context gate, current compiler shared-kernel source, and runtime observation extractor. It separately verifies the frozen design report as a regular non-symlink file with mode `0644`, 39,895 bytes, 524 LF bytes, and SHA256 `10d5c2245b54665f83cab2782651a18ab7569628d07c07697841887e3e27d47e`.

The adapter context remains public Exact2. Its private trusted-owner helper remains:

```python
_validate_context_and_materialize(
    context: object,
) -> tuple[dict[str, object], list[dict[str, object]], dict[str, object]]
```

Opacity means caller-facing non-inspection and non-mutation. Only the named/versioned future bridge may import the pinned adapter owner and call that helper, exactly once during bridge construction. The helper is not a public accessor and cannot be called per batch. The future bridge may not read `_semantic` or `_seal`, reconstruct the private adapter type, bypass owner validation, monkeypatch the owner, or continue after an owner error.

## Source Exact10 and Provider Exact11

Source Exact10 is frozen in this order:

1. `schema_version`
2. `source_projection_digest`
3. `source_payload_digest`
4. `parser_schema_version`
5. `collate_schema_version`
6. `source_sample_order`
7. `source_pair_values_int64`
8. `source_sample_offsets_int64`
9. `source_entry_validity_bool`
10. `source_sample_validity_bool`

The first, fourth, and fifth values are constants after adapter/compiler equality checks. Projection and payload digests are rename-only values from the sealed remap semantic payload. The five collection fields are deep-copy/rename-only values from the materialized source contract. Runtime observation is never source authority.

The static Source fixture reproduces canonical compact bytes `2735`, SHA256 `21bc3eb8a7b2f4b569f17d102715726eda09aed6467782e5477a7cfa285f98f2`, and source component digest `ffbd6311d0ae44e0729cf6c659493f14945414d7ce6aac3ddea107a321773aba`.

Provider Exact11 is a built-in list of 11 records. Every record contains `sample_identity` then `roles`; sample identity uses the compiler's exact four identity fields, and roles remain ordered `pocket`, `ligand`. Only redundant nested `source_sample_index` is projected out; it remains in Source Exact10. Each complete historical 18-field role record is retained, including the existing `source_to_parser_local` mapping without recomputation, and selected atom identity remains Exact8.

The provider reference freezes canonical compact bytes `23364`, canonical SHA256 `1345c9da88fd516677c1730d129ab8a19f487eb0862fa7b7580481bc15a43bc5`, historical provider digest `a6193bfe7099b9c9436036f75101df31638739a893b598af8ac021bfa46aa186`, and provider component digest `1c06fdec0313c481c60eadb9b6c20d278c682908c3681f99995f8fee5109564a`. The mapping is lossless and has zero missing information.

## Historical readiness and compatibility

The future bridge must preserve the historical compiler Output10 readiness Exact24 in the lexical order produced by parsing the canonical historical manifest. It deliberately preserves these stale values:

```text
runtime_batch_observation_extractor_implemented=false
ready_for_runtime_batch_observation_extractor_design=true
```

The current truthful fact that the extractor is published appears only in this gate's report. Readiness does not control the pure compile kernel. The readiness component digest is `8d6bcae9f365f6c802e9109a8c1e53c1b85c8c8c23f04d005a162c09fcdb6890`.

The historical compiler-authority compatibility digest is `e3c7c14e5a94db2bf59b5195ae6902d7fd7269e58a8690589962548860348d44`. It is not the future bridge construction seal. Acquisition provenance remains separate from compiler authority compatibility.

## Future bridge contract, not implementation

The future module is reserved as:

```text
src/covalent_ext/covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1.py
```

This gate does not create it. Its future public Exact2 is frozen as:

```python
build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
    *, remap_context: object,
) -> object

compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1(
    *, context: object, observation: dict[str, object],
) -> dict[str, object]
```

The future error token is:

```text
COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_FROM_REMAP_CONTEXT_V1_ERROR
```

The builder cannot accept repository/state roots, artifacts, formal paths, or device identity. The future private context is frozen/slotted, caller-opaque, unconstructible through a public class, deeply immutable, uncached, unregistered, and non-pickleable. It retains no remap-context object.

The future logical context is Exact20:

1. `context_schema_version`
2. `context_contract_version`
3. `adapter_context_owner_module`
4. `adapter_context_owner_schema_version`
5. `adapter_context_owner_contract_version`
6. `adapter_context_owner_source_sha256`
7. `adapter_context_private_materializer`
8. `compiler_module`
9. `compiler_product_commit`
10. `compiler_source_sha256`
11. `compiler_private_kernel`
12. `compiler_contract_digest`
13. `source_contract_digest`
14. `provider_digest`
15. `historical_authority_compatibility_digest`
16. `context_freshness_model`
17. `source_exact10`
18. `identity_provider_exact11`
19. `readiness_template`
20. `construction_seal`

Its seal is domain-separated SHA256 over framed canonical compact JSON for the first 19 logical fields. The exact domain is the UTF-8 bytes of `COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_FROM_REMAP_CONTEXT_V1` followed by one terminal NUL byte (`0x00`). Python source represents that byte as `\x00`, and canonical JSON represents it as `\u0000`; it is not the two-byte literal backslash-plus-zero suffix (`\0`). The seal excludes itself and all machine/process/device identities.

## Ownership, fast path, and Output10

The caller builds one remap context. The future bridge consumes that same object, calls the owner materializer exactly once at bridge build, maps and freezes compiler authority once, then discards the remap object. The bridge itself calls the public remap builder zero times and calls historical compiler `_authority`, stable5 parsing, reconciliation, successor, B2/state-mount transition, formal validation, and historical compiler contract construction zero times.

Fast compile validates exact bridge type/version/lineage/seal before observation evaluation, thaws fresh Source Exact10, Provider Exact11, and readiness, then calls only:

```python
_compile_with_verified_authority_v1(
    *,
    authority: tuple[
        dict[str, object],
        list[dict[str, object]],
        dict[str, bool],
    ],
    observation: object,
) -> dict[str, object]
```

It performs no filesystem, Git, subprocess, report, artifact-write, rebuild, materializer, or global-cache operation. No benchmark or millisecond SLA is part of this contract.

Output10 remains whole-dictionary deep exact with the historical compiler context. Success parity IDs are `canonical`, `reversed`, `subset_10_4_0`, and `singleton_10`. Frozen hard failures are:

- `source_contract_override` → `SOURCE_CONTRACT_MISMATCH`
- `duplicate_runtime_key` → `BATCH_SAMPLE_KEY_DUPLICATED`
- `wrong_ligand_length` → `ROLE_LENGTH_MISMATCH`
- `wrong_ligand_membership` → `MEMBERSHIP_MASK_MISMATCH`
- `unknown_joint_descriptor` → `BATCH_OBSERVATION_SCHEMA_MISMATCH`

Programming-invalid bridge contexts fail to the future bridge error before observation evaluation. A valid bridge context plus malformed observation continues returning the historical compiler hard-failure Output10. No bridge metadata is added.

## Device risk and readiness

The historical risk is the old compiler authority chain reaching a routing projection identity pinned to `st_dev=49` while current authorized state is on `st_dev=50`. The successor-backed adapter context already consumes the authorized transition. This gate defines the proof obligations that remove the old chain, so `device_identity_risk_resolution_contract_defined=true`; because no bridge exists yet, `device_identity_risk_resolution_runtime_proven=false`.

Readiness has two deliberately separate layers. The stable manifest's semantic
readiness keeps
`ready_for_compiler_remap_context_handoff_implementation=false`: the contract
artifact itself does not implement the bridge product. The self-excluded report
adds repository-lifecycle readiness: a clean tracked successor authorizes the
next bridge implementation increment without claiming that the bridge already
exists.

### `precommit-untracked`

```text
gate_status=PASS_COMPILER_REMAP_CONTEXT_HANDOFF_CONTRACT_PRECOMMIT_CANDIDATE_ONLY
ready_for_compiler_remap_context_handoff_contract_gate_commit_review=true
ready_for_compiler_remap_context_handoff_contract_gate_publication=false
ready_for_compiler_remap_context_handoff_implementation=false
compiler_remap_context_handoff_implementation_blocker=handoff_contract_gate_not_published
device_identity_risk_resolution_runtime_proven=false
ready_for_dataloader_integration=false
ready_for_model_integration=false
ready_for_loss_integration=false
feature_semantics_reaudit_required_before_training=true
ready_for_training=false
```

### `clean-tracked-successor`

```text
gate_status=PASS_COMPILER_REMAP_CONTEXT_HANDOFF_CONTRACT_CLEAN_TRACKED_SUCCESSOR
ready_for_compiler_remap_context_handoff_contract_gate_commit_review=false
ready_for_compiler_remap_context_handoff_contract_gate_publication=true
ready_for_compiler_remap_context_handoff_implementation=true
compiler_remap_context_handoff_implementation_blocker=NONE
device_identity_risk_resolution_runtime_proven=false
ready_for_dataloader_integration=false
ready_for_model_integration=false
ready_for_loss_integration=false
feature_semantics_reaudit_required_before_training=true
ready_for_training=false
```

The clean state means only that publication authorizes an implementation
candidate. It does not mean handoff implementation, device-risk runtime proof,
DataLoader/model/loss integration, or training has completed.

Step12D remains a smoke legality check, not a final training-feature contract. The historical `UNKNOWN_ATOM_FEATURE_POLICY` and `feature_semantics_known=False` condition still requires a feature-semantics audit before training.

The canonical masks remain exactly `warhead_only/A`, `linker_plus_warhead/B`, `scaffold_plus_warhead/B2`, `scaffold_only/B3`, and `scaffold_plus_linker_plus_warhead/C`. No sixth mask is permitted, and the engineering bridge is not named `B3`.

## Check command

```bash
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 python -B \
  scripts/check_covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1.py \
  --repo-root /cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/DiffSBDD-base \
  --state-root /cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/covapie-state
```

Success emits one compact canonical JSON line on stdout and nothing on stderr. Invalid CLI or root input emits only the gate error token on stderr and exits with status 1.
