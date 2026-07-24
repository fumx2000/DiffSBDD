# CovaPIE ADMIT_015 training authorization contract v1

This metadata-only stage freezes the training-authorization contract for
`ADMIT_015` (`current_gate_grants_no_training_permission`) against committed
base `4fb86e7d6b8cd27258362cae34eec196b117c265`, parent
`f54c0efabfb695653c9e55b3a53bda8cf200f353`, and tree
`2a447517ce601e9440a7c1523866d459b192870c`.

It does not implement `evaluate_admit_015`, a final evaluator signature, a
final result dataclass, an independent oracle, a standalone evaluator, an
adapter or handler, a registry entry, Exact15 runtime, mandatory training
enforcement, combined verdict, or cross-rule aggregation.

## Authority, type, and trust

The only authoritative path is
`stage_authorization_context.current_stage_training_authorized`. The context
scope is `stage`; its trusted producer boundary is
`trusted_future_stage_orchestrator`. Trust belongs to the caller boundary, not
to a string stored in the mapping. The caller must reconstruct an
invocation-local context for every invocation. Previous-invocation, artifact,
cache, and raw replay are forbidden. Cryptographic authentication remains
outside the future evaluator.

The value contract is exact: `type(value) is bool`, with the closed vocabulary
`False | True`. Normalization, `bool(value)`, integer/string/NumPy coercion,
truthiness, defaults, fallback, aliases, OR, and AND-as-a-single-permission are
forbidden. The deterministic design classifier performs one target
`__getitem__` and does not iterate the mapping or call `len`, `.get`, or
containment.

Candidate, batch, evaluation, and download-result envelopes cannot authorize
training. Neither can provider results, candidate self-report, environment
variables, filesystem markers, raw files, artifact or Git hashes, manifest
self-report, fixtures, checkpoint metadata, training configuration, CLI flags,
model state, dataloader state, or ADMIT_014 download permission.

## Download/training isolation

`current_stage_download_authorized=True` does not authorize training, and
`current_stage_training_authorized=True` does not authorize download. The keys
cannot substitute for, alias, OR with, or collapse by AND into one another.
When the training key is missing, the design classifier does not read the
download key. Combined permission semantics remain undefined and cross-rule
aggregation remains unimplemented.

## Outcome and precedence

The exact outcomes are `passed` and `blocked`. Failure precedence is:

1. missing envelope: `STAGE_AUTHORIZATION_CONTEXT_REQUIRED`;
2. non-mapping envelope: `STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID`;
3. target lookup `KeyError`: `CURRENT_STAGE_TRAINING_AUTHORIZED_MISSING`;
4. other target lookup exception:
   `STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED`;
5. non-exact-bool target:
   `CURRENT_STAGE_TRAINING_AUTHORIZED_TYPE_INVALID`;
6. exact `False`: `TRAINING_NOT_AUTHORIZED`;
7. exact `True`: passed with an empty reason.

The Exact40 truth matrix preserves the ADMIT_014 case order, 16-column schema,
and group counts: context structure 7, exact bool 2, non-exact bool 12,
mapping behavior 10, forbidden pseudo-authority 6, and current/future 3. All
40 design cases pass and forbidden-envelope access totals zero.

The literal case IDs and order are inherited unchanged from the committed
ADMIT_014 Exact40 precedent, including `ADMIT015_PLUS_TRUE` and
`ADMIT015_PLUS_FALSE`. Their payloads have been switched to ADMIT_015
semantics: `current_stage_training_authorized` is the target key and
`current_stage_download_authorized` is only the isolated coexistence key.

Synthetic `True` is only a future-rule design case. It does not change current
permission, authorize an actual training invocation, or imply training
readiness. Current permission is false and authorized ADMIT_015 training
execution count is zero.

## Future mandatory responsibility

A future training-stage global guard must evaluate ADMIT_015 once per real
training invocation and block continuation before dataloader instantiation,
checkpoint loading, model initialization or forward, loss, backward,
optimizer/scheduler creation, parameter update, checkpoint write, or training
result materialization. A combined verdict must not override a blocked result.

This stage freezes that responsibility boundary only. The enforcement API is
not frozen and enforcement is not implemented. Every blocked protected-action
count remains zero, so `PRE_034` remains open.

## Evidence, transitions, and readiness

The ordered Exact18 committed source boundary contains the seven ADMIT_015
preconditions artifacts, Step14AT registry, Step14AU-A context contract, three
ADMIT_014 authorization artifacts, Exact14 runtime production/manifest/issues,
canonical QA manifest, feature-semantics manifest, and Step12D manifest.
Sources require base/index stage-0 identity, byte equality, frozen SHA256,
pinned no-follow traversal, and retained final-leaf descriptors.

Exactly these preconditions transition to complete:
`PRE_007`–`PRE_012`, `PRE_016`–`PRE_018`, and `PRE_025`–`PRE_027`. The final
counts are 31 complete, zero supported-but-not-frozen, 14 incomplete, and 14
implementation-blocking. Open IDs are `PRE_019`–`PRE_024`, `PRE_031`–`PRE_036`,
`PRE_038`, and `PRE_042`.

The Exact30 issue inventory remains byte-identical with zero issue transitions.
Coverage remains ADMIT_015 and its coverage issue remains open.

The canonical V1 mask contract remains exactly:

1. `warhead_only` / `A`
2. `linker_plus_warhead` / `B`
3. `scaffold_plus_warhead` / `B2`
4. `scaffold_only` / `B3`
5. `scaffold_plus_linker_plus_warhead` / `C`

Feature-semantics audit is still incomplete. Step12D remains a smoke-legality
check rather than a final training-feature contract. No dataloader,
checkpoint, model, provider, network, download, raw-data, or training action
is performed.

The deterministic Exact6 consists of the authorization contract, Exact40 truth
matrix, value/trust contract, safety boundary, byte-identical Exact30 issue
inventory, and manifest. Materialization reuses the predecessor hardened
build-before-mutation, exact-no-op, `RENAME_NOREPLACE`, fail-closed retained
staging, and bounded lifecycle contract.

The revised1 checker independently rebuilds every field of Contract Exact40,
Truth Exact40, Value/trust Exact26, Safety Exact31, the Exact45 precondition
transition and its hash, and the complete 81-key manifest. It rejects
duplicate, missing, extra, reordered, and exact-type-invalid manifest values.
Synchronized tamper tests update payload hashes, recompute the manifest hash,
and bypass the frozen-SHA layer before confirming rejection by independent
semantics. The checker also restores the committed recursive bounded,
no-follow stage-family lifecycle scan for ignored, nested, tracked-extra,
sibling-root, symlink, forbidden-suffix, oversized, staged, mixed, dirty, and
missing artifacts.

The revised2 checker restores final binding checks for every held parent FD
and its lexical name before rechecking the repository root and source leaf.
Real intermediate- and upper-parent rename/recreate tests prove that the
checker rejects a path whose held parent still exposes the old bytes while
the lexical path exposes replacement bytes. The
`covapie_admit_015_issue_readiness_inventory` token is now included in the
recursive stage-family lifecycle, including ignored, nested, tracked,
symlink, and forbidden-suffix negative cases. Production and all Exact6 bytes
remain unchanged, and no authorization business semantics are changed.

Recommended next step:
`design_covapie_admit_015_formal_evaluator_interface_contract_v1`.
