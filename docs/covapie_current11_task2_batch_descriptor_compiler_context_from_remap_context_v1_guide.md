# CovaPIE Current11 Task2 compiler context from remap context V1

## Scope

This additive bridge implements the published compiler/remap-context handoff contract with stable digest `7de09322699eb9529486f49f5e5c1367317d63143e967f6223b010a4ef972c78`. It does not replace or modify the published remap context, the historical compiler context, the compiler, the observation extractor, a DataLoader, model/head/forward/loss code, or checkpoint state.

The production module exports exactly:

```python
build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
    *, remap_context: object,
) -> object

compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1(
    *, context: object, observation: dict[str, object],
) -> dict[str, object]
```

Programming-invalid remap or bridge contexts fail closed with:

```text
COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_FROM_REMAP_CONTEXT_V1_ERROR
```

A valid context plus a malformed observation returns the historical compiler hard-failure Output10 instead of converting that runtime result into a bridge error.

## Build ownership

The builder accepts no repository or state root. The caller first builds one published remap context and passes that same object to the bridge. During bridge construction, the bridge:

1. reads and verifies the already-imported adapter-context and compiler owner sources as regular, non-symlink, mode-`0644` files with pinned byte, LF, and SHA256 identities;
2. verifies the adapter public Exact2, adapter context schema/contract versions, compiler contract/source/provider digests, and the two trusted private callables;
3. calls the adapter owner's `_validate_context_and_materialize` exactly once;
4. maps, validates, and deep-freezes compiler authority; and
5. discards the caller's remap-context object.

The adapter owner source is 43,578 bytes, 1,211 LF bytes, and SHA256 `1eb764aa4425ad857d59daa625e610a5e015a0a272594f332254998bed8191e6`. The compiler owner source is 31,298 bytes, 687 LF bytes, and SHA256 `a7a232a4f344e5cbac152ae8cc51921f4d9bf07deaaab0d55f1ce950e67b524a`.

The production bridge imports only those two CovaPIE owners plus the Python standard library. It does not import a checker, handoff gate, historical compiler context/gate, reconciliation, successor, B2, slow adapter, DataLoader, model, or loss owner. It calls no Git command.

## Private immutable Exact20

The bridge context is private, frozen, slotted, opaque, uncached, and non-pickleable. It exposes no public context class or constructor and contains no reachable built-in mutable dictionary or list. `copy.copy`, `copy.deepcopy`, pickle reduction, and explicit reduction all fail closed. A module-private construction token rejects reconstructed objects, and the context retains no reference to the original remap context.

Its logical fields are exactly:

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

The schema version is `covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1`, the context version is the published handoff digest, and freshness is `explicit_rebuild_from_caller_owned_remap_context`.

The construction seal is lowercase SHA256 over the canonical compact JSON bytes of fields 1–19. Framing is `domain || uint64be(payload length) || payload`. The runtime domain ends in one real NUL byte (`0x00`) after `COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_FROM_REMAP_CONTEXT_V1`; the source contains an escape sequence, never a raw NUL or a literal backslash-plus-zero suffix. The seal excludes itself, the remap-context object, absolute paths, timestamps, device identity, and process identity.

## Mapped compiler authority

Source Exact10 is mapped only from the owner-materialized source contract and sealed adapter semantic values. It is never inferred from an observation or reparsed from stable5. Its canonical compact identity is 2,735 bytes with SHA256 `21bc3eb8a7b2f4b569f17d102715726eda09aed6467782e5477a7cfa285f98f2`; its source component digest is `ffbd6311d0ae44e0729cf6c659493f14945414d7ce6aac3ddea107a321773aba`.

Provider Exact11 retains all eleven samples. Each provider identity projects the exact compiler identity4 while checking the source ordinal. Role order remains `pocket`, `ligand`, and each role preserves all 18 existing fields, including extra metadata, selected atom identity, and the existing `source_to_parser_local` value without recomputation. Its canonical compact identity is 23,364 bytes with SHA256 `1345c9da88fd516677c1730d129ab8a19f487eb0862fa7b7580481bc15a43bc5`; the historical provider digest is `a6193bfe7099b9c9436036f75101df31638739a893b598af8ac021bfa46aa186`.

Historical readiness remains Exact24 in lexical manifest-parse order. It intentionally keeps `runtime_batch_observation_extractor_implemented=false` and `ready_for_runtime_batch_observation_extractor_design=true` for whole Output10 parity. Its component digest is `8d6bcae9f365f6c802e9109a8c1e53c1b85c8c8c23f04d005a162c09fcdb6890`. These readiness fields are parity metadata, not compiler branch conditions.

The independently cross-checked historical authority compatibility digest is `e3c7c14e5a94db2bf59b5195ae6902d7fd7269e58a8690589962548860348d44`. It is stored as compatibility metadata and is not the bridge construction seal.

## Fast compile and Output10

Every fast call validates the exact private type, construction token, frozen graph, fixed lineage, Exact10/Exact11/Exact24 goldens, compatibility value, and recomputed seal. It materializes fresh built-in authority and calls the compiler-owned `_compile_with_verified_authority_v1` exactly once.

The fast path performs no remap materialization, public remap build or fast call, old compiler `_authority`, stable5 parsing, reconciliation, successor, B2, formal validation, historical contract build, source read, filesystem/Git/subprocess operation, report generation, artifact write, context rebuild, or cache access.

Output10 is the historical whole built-in dictionary with exact field order, readiness, statuses, failure reasons, outcomes, provenance, and no bridge metadata. The success parity cases are `canonical`, `reversed`, `subset_10_4_0`, and `singleton_10`. The five frozen hard failures are source-contract override, duplicate runtime key, wrong ligand length, wrong ligand membership, and unknown joint descriptor.

## Precommit and future clean proof

While this Exact4 is untracked, the published public remap-context builder correctly fails its clean lifecycle. Precommit validation therefore imports the existing adapter-context checker, obtains verified reconciliation/successor artifacts through `_acquire_predecessor_fixture`, and passes those artifacts to the adapter owner's private verified-predecessor fixture builder. This is test/checker-only lifecycle patching; restoration is verified, production is not monkeypatched, and `real_public_remap_context_build_performed=false`.

After publication in a clean tracked tree, the same checker switches to `_acquire_clean_public_context`. That path must delegate the real public remap build and prove reconciliation/successor/B2/formal counts `1/1/1/2`, then pass the same real remap object to the bridge. Only that clean live proof may set `device_identity_risk_resolution_runtime_proven=true` and `ready_for_bridge_publication=true`.

For this precommit candidate, device-risk resolution is contract-defined but not runtime-proven. `ready_for_bridge_commit_review=true`, while publication, DataLoader, model, loss, and training readiness remain false.

## Training and masks

Step12D remains only a smoke legality check, not a final training-feature contract. The historical `UNKNOWN_ATOM_FEATURE_POLICY` and `feature_semantics_known=False` state still require a feature-semantics audit before training.

The canonical V1 masks remain exactly `warhead_only/A`, `linker_plus_warhead/B`, `scaffold_plus_warhead/B2`, `scaffold_only/B3`, and `scaffold_plus_linker_plus_warhead/C`. `B3` always means `scaffold_only`; no sixth mask is introduced.

## Check command

```bash
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 python -B \
  scripts/check_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1.py \
  --repo-root /cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/DiffSBDD-base \
  --state-root /cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/covapie-state
```

Success prints one compact canonical JSON line and nothing on stderr. Invalid CLI or root input exits with status 1 and prints only `COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_FROM_REMAP_CONTEXT_V1_CHECK_ERROR` on stderr.
