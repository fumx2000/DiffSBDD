# CovaPIE ADMIT_015 standalone evaluator interface v1

## Scope and lineage

This increment implements only the standalone ADMIT_015 rule evaluator on
committed base `809ec4f8c9494db893d2d66b7551856b2ead4401`
(`add CovaPIE ADMIT_015 formal evaluator interface contract v1`). The base
parent is `a7800cfad9f55809d6161c2db12f49c8312165fb` and the base tree is
`0a047613fed8bd6094675c8d4bc799284e53c43e`.

The implementation does not add a unified adapter or handler, modify the
registry, create an Exact15 runtime, change the Exact14 runtime, implement
mandatory training authorization enforcement, aggregate rules, or form a
combined candidate verdict. It does not instantiate a dataloader, load a
checkpoint, create a model, run forward/loss/backward/optimizer/scheduler
operations, update parameters, write a training checkpoint, or perform
provider/network/download/raw operations.

## Public evaluator and Exact9 result

The real Python signature is:

```python
evaluate_admit_015(
    *,
    stage_authorization_context: object = _MISSING,
) -> Admit015EvaluationResult
```

The only parameter is keyword-only, annotated with built-in `object`, and
defaults by identity to the module-private singleton `_MISSING`. Positional
and unknown-keyword calls are rejected by Python.

`Admit015EvaluationResult` is a frozen dataclass with these Exact9 ordered
fields and built-in annotations:

1. `admission_rule_id: str`
2. `outcome: str`
3. `passed: bool`
4. `blocks_candidate: bool`
5. `reason: str`
6. `canonical_stage_authorization_record: tuple`
7. `validated_stage_authorization_fields: tuple`
8. `consumed_stage_authorization_fields: tuple`
9. `evaluator_io_used: bool`

Subclass definition is rejected. Direct construction validates exact
built-in scalar and tuple types, exact tuple pairs and keys, exact bool
permission values, the closed outcome and six-blocker reason vocabularies,
all flag relationships, and the complete canonical/validated/consumed
projection. `evaluator_io_used` must be exact `False`.

## Frozen rule and consumption behavior

The evaluator applies this fail-closed precedence:

1. omitted or explicit `None`:
   `STAGE_AUTHORIZATION_CONTEXT_REQUIRED`;
2. non-`Mapping`:
   `STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID`;
3. target lookup `KeyError`:
   `CURRENT_STAGE_TRAINING_AUTHORIZED_MISSING`;
4. any other target lookup exception:
   `STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED`;
5. target value whose type is not exact built-in `bool`:
   `CURRENT_STAGE_TRAINING_AUTHORIZED_TYPE_INVALID`;
6. exact `False`: `TRAINING_NOT_AUTHORIZED`;
7. exact `True`: rule-level pass with an empty reason.

For a mapping, the evaluator performs exactly one direct lookup of
`stage_authorization_context["current_stage_training_authorized"]`. It never
iterates, calls `len`, `.get`, containment, truthiness, or `bool(value)`.
Extra keys are allowed. `current_stage_download_authorized` may coexist but
is never accessed. Inputs are not modified and repeated invocations retain no
state.

The formal closure ends at the unique
`# === ADMIT_015 FORMAL EVALUATOR CLOSURE END ===` marker. Static AST and
reachable-call auditing show that the closure cannot reach filesystem,
environment, subprocess, network/provider, raw data, manifest, checkpoint,
dataloader, model, training, registry, adapter, or artifact materialization
behavior. The committed design classifier is not called by the production
rule logic.

## Independent truth and evidence

The checker independently computes all 37 executable business/projection
oracles and compares every Exact9 value and exact runtime type with the
production evaluator. It also executes all 24 malformed-result cases against
the real constructor. Together with the eight real signature checks, this
preserves the committed formal Exact69 case identity, order, precedence, and
projection semantics. The derived truth artifact follows the ADMIT_014
standalone precedent and contains the non-signature Exact61.

The deterministic Exact6 consists of:

1. standalone evaluator contract;
2. Exact61 truth matrix;
3. ordered Exact15 committed-source boundary audit;
4. formal closure purity audit;
5. byte-identical Exact30 issue inventory;
6. closed manifest.

The ordered Exact15 source boundary pins the ADMIT_015 formal production and
formal Exact6, training authorization manifest, precondition inventory and
manifest, committed ADMIT_014 standalone production and manifest, Exact14
runtime manifest, feature-semantics manifest, and Step12D manifest. Every
source is required to be the same regular stage-0 blob in the base tree,
index, and filesystem, with frozen SHA256 and pinned no-follow reads.
Source readers retain the leaf descriptor through both leaf checks, every
parent descriptor/lexical check, and the repository-root descriptor/lexical
checks. A second leaf descriptor/lexical check therefore rejects a real
late same-name replacement that occurs after the first post-read leaf check.

Artifact construction is deterministic and build-before-mutation. It uses
exclusive staging leaves, descriptor-relative operations, fsync,
`RENAME_NOREPLACE`, and complete pinned post-publication reads. A pre-existing
byte-identical Exact6 is an inode-preserving no-op. GPFS `EINVAL`, concurrent
publication, and identity drift fail closed with no `os.replace` fallback.
Failure staging is retained without unlink/rmdir cleanup; bounded tests
verify the retained inventory and foreign-object non-destruction.
Exact6 readers retain all leaf descriptors and perform a second inventory,
leaf descriptor/lexical, and root/parent descriptor/lexical verification
before returning. The materializer verifies that the staging lexical name is
still bound to its open staging descriptor after open, around every leaf
write, after staging fsync and parent refresh, before rename, and again
inside `_rename_noreplace` before the syscall. Real staging replacement is
rejected without publishing or deleting either the owned-away or foreign
tree.

The independent checker reconstructs the complete manifest and recursively
compares exact Python types, dictionary key order, list order and length, and
every scalar value; bool/int equivalence is rejected. Synchronized output
and manifest SHA changes cannot bypass the independent semantic checks.
The revised2 audit also found that the earlier CSV checks were aggregate-only:
they did not reconstruct every non-pass field. The checker now independently
rebuilds and compares all fields of Contract Exact37×10, Truth Exact61×12,
and Purity Exact16×13. Contract rows come from checker-local frozen interface,
closure, AST, and safety contracts. Truth rows are reconstructed from the
committed formal case identity plus real evaluator/result execution and the
independent Exact9 oracle. Purity rows are reconstructed from checker-local
closure reachability, AST, permitted binding/call, absence, and metadata
contracts. Synchronized CSV and Manifest SHA changes therefore cannot bypass
any semantic column. This revision leaves Production, every Exact6 byte, and
the evaluator business semantics unchanged.
Lifecycle inspection uses a bounded recursive no-follow scan of
`src/covalent_ext`, `scripts`, `tests`, and `docs`, plus matching first-level
stage-family roots under `data/derived/covalent_small`. Every discovered
stage-family path is checked against Git ignore rules and the filesystem
allowlist is exactly Exact10 plus the single Exact6 root, so nested, ignored,
tracked, sibling-root, forbidden-suffix, oversized, symlink, and seventh-file
artifacts fail closed.

## Readiness

The formal `evaluate_admit_015`, `Admit015EvaluationResult`, standalone
signature, Exact9 representation, and ADMIT_015 rule logic are implemented.
The checker/test oracle is evidence only, so production runtime independent
oracle remains false.

Preconditions remain exactly 37 complete, 0 supported-but-not-frozen, and
8 incomplete/implementation-blocking. The remaining identifiers are
`PRE_031`, `PRE_032`, `PRE_033`, `PRE_034`, `PRE_035`, `PRE_036`, `PRE_038`,
and `PRE_042`. The Exact30 issue inventory remains byte-identical, with zero
issue transitions and open coverage limited to ADMIT_015.

Current project permission remains false and authorized real ADMIT_015
training execution count remains zero. Mandatory enforcement, unified
adapter, registry entry, Exact15 runtime, combined verdict, cross-rule
aggregation, real training readiness, and training readiness remain false or
unimplemented. A synthetic exact `True` produces only a rule-level pass and
does not authorize or start real training.

The canonical V1 masks remain exactly:

1. `warhead_only` / `A`
2. `linker_plus_warhead` / `B`
3. `scaffold_plus_warhead` / `B2`
4. `scaffold_only` / `B3`
5. `scaffold_plus_linker_plus_warhead` / `C`

Feature-semantics audit completion, historical unknown-atom-policy
resolution, and historical feature-semantics knowledge remain false.
Step12D remains a smoke-legality check, not the final training-feature
contract. A feature-semantics audit is still required before training.

Recommended next step:
`design_covapie_admit_015_unified_adapter_contract_v1`.
