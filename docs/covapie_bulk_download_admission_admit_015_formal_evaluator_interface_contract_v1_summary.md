# CovaPIE ADMIT_015 formal evaluator interface contract v1

This metadata-only design stage freezes the future ADMIT_015 public evaluator
interface and Exact9 result contract. It does not implement the formal
evaluator, the formal result type, a production runtime oracle, standalone
evaluator, adapter, registry entry, Exact15 runtime, combined verdict,
cross-rule aggregation, or mandatory training enforcement.

## Frozen base and source boundary

The committed base is
`a7800cfad9f55809d6161c2db12f49c8312165fb`, with parent
`4fb86e7d6b8cd27258362cae34eec196b117c265`, tree
`7f74b75e63e2f949a5ed73b7f7df6aa921235132`, and subject
`add CovaPIE ADMIT_015 training authorization contract v1`.

Evidence generation requires CPython 3.10.4. The ordered Exact18 source
boundary pins the committed ADMIT_015 authorization contract, its five
non-manifest artifacts and manifest, the ADMIT_015 precondition inventory and
manifest, the ADMIT_014 formal-interface production precedent and five
artifacts, the Exact14 runtime manifest, the feature-semantics audit manifest,
and the Step12D manifest. Every source is checked against base tree, index
stage 0, filesystem bytes, SHA256, no-follow FD traversal, post-read identity,
and final-leaf identity.

## Revised1 verification hardening

The source readers retain the opened leaf FD through the first lexical-leaf
check and every held parent/root FD and lexical binding check. They then repeat
both the leaf FD identity check and lexical-leaf identity check before closing
the leaf and directory descriptors. Real rename-and-recreate tests replace the
lexical leaf only after the first post-read lexical stat has obtained the old
identity; both the production reader and the independent checker fail closed
on the final lexical check.

The independent checker rebuilds the Exact22 contract, Exact8 routing,
Exact69 truth, Exact18 source audit, Exact30 byte inheritance, and PRE
transition before independently constructing the complete expected manifest.
Manifest verification is recursive and exact for dictionary key set and
order, list length and order, scalar value, and Python type, including strict
separation of booleans and integers. Synchronized tamper tests update the
affected manifest output SHA, recompute the manifest SHA, and replace the
checker frozen SHA map; the independent semantic layer still rejects every
contract, routing, truth, source, issue, and nested manifest mutation.

Lifecycle inventory uses a bounded recursive no-follow scan of
`src/covalent_ext`, `scripts`, `tests`, and `docs`. Under
`data/derived/covalent_small`, only matching first-level stage-family roots are
entered, then their contents are scanned recursively. Every discovered
stage-family path is checked independently of Git ignore visibility and must
match the Exact10 plus the one Exact6 parent root. Nested ignored, unignored,
tracked, symlink, forbidden-suffix, oversized, sibling-root, and seventh-output
artifacts all fail closed.

## Future public interface

The future formal public symbol is not defined in this stage. Its exact frozen
signature is:

```python
evaluate_admit_015(
    *,
    stage_authorization_context: object = _MISSING,
) -> Admit015EvaluationResult
```

There is exactly one keyword-only parameter. The default is the private
`_MISSING` singleton. Positional calls, `*args`, `**kwargs`, unknown keywords,
and extra parameters are forbidden.

The metadata-only design oracle is
`classify_admit_015_formal_evaluator_interface_design`. Its design-only frozen
result is `Admit015EvaluationResultContractDesign`; neither name is the future
formal runtime implementation.

## Exact9 result contract

The future `Admit015EvaluationResult` is frozen as a non-subclassable frozen
dataclass with these exact fields, types, and order:

1. `admission_rule_id: str`
2. `outcome: str`
3. `passed: bool`
4. `blocks_candidate: bool`
5. `reason: str`
6. `canonical_stage_authorization_record: tuple`
7. `validated_stage_authorization_fields: tuple`
8. `consumed_stage_authorization_fields: tuple`
9. `evaluator_io_used: bool`

The canonical record is exactly `()`,
`(('current_stage_training_authorized', False),)`, or
`(('current_stage_training_authorized', True),)`. Validated and consumed
fields are exactly `()` or
`('current_stage_training_authorized',)`. Tuple, pair, string, and boolean
representations require exact built-in types.

The result invariants require `admission_rule_id == "ADMIT_015"`, exact
outcome/flag agreement, empty reason iff passed, one of six closed blocker
reasons iff blocked, and exact `evaluator_io_used is False`.

## Exact8 routing

The ordered routes are `OMITTED`, `EXPLICIT_NONE`, `NON_MAPPING`,
`TARGET_KEYERROR`, `TARGET_NONKEYERROR`, `INVALID_TYPE`, `EXACT_FALSE`, and
`EXACT_TRUE`.

Omitted and explicit `None` produce
`STAGE_AUTHORIZATION_CONTEXT_REQUIRED`. A non-mapping produces
`STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID`. Target `KeyError` produces
`CURRENT_STAGE_TRAINING_AUTHORIZED_MISSING`; another lookup exception produces
`STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED`. A non-exact bool produces
`CURRENT_STAGE_TRAINING_AUTHORIZED_TYPE_INVALID`. Exact `False` produces
`TRAINING_NOT_AUTHORIZED`; exact `True` passes with an empty reason.

Only the target key is accessed, at most once. Mapping iteration, `len`, `get`,
and membership checks are forbidden. The coexistence key
`current_stage_download_authorized` is never consumed.

## Exact69 truth and preconditions

The 17-column truth matrix retains the ADMIT_014 literal case IDs and order:
8 signature, 8 context-structure, 3 lookup, 11 invalid-exact-type, 2 business,
7 mapping-behavior, 6 projection, and 24 negative-result-contract rows. All
69 cases pass. Six signature rows report metadata outcome `verified`; two
real bind/invocation rejection rows report metadata outcome `rejected` with
`TypeError`. These metadata outcomes are not formal evaluator outcomes.

The Exact45 precondition inventory is independently rebuilt. Only PRE_019
through PRE_024 become complete in this stage, after retaining the twelve
authorization-contract transitions. Final counts are 37 complete, 0
supported-but-not-frozen, 8 incomplete, and 8 implementation-blocking.
Remaining open IDs are PRE_031, PRE_032, PRE_033, PRE_034, PRE_035, PRE_036,
PRE_038, and PRE_042.

The inherited Exact30 issue inventory is byte-identical. Its transition count
is zero, ADMIT_015 coverage remains open, and no issue is added.

## Safety and readiness

Current permission remains false and the authorized ADMIT_015 training
execution count remains zero. A synthetic exact-True design case does not
authorize real training.

The canonical masks remain exactly:

1. `warhead_only / A`
2. `linker_plus_warhead / B`
3. `scaffold_plus_warhead / B2`
4. `scaffold_only / B3`
5. `scaffold_plus_linker_plus_warhead / C`

The historical unknown-atom feature policy and training feature semantics
remain unresolved. Step12D remains
`smoke_legality_only_not_final_training_feature_contract`. No provider,
network, download, raw-data, dataloader, checkpoint, model, forward, loss,
backward, optimizer, scheduler, parameter-update, or training action is part
of this stage.

The recommended next step is exactly
`implement_covapie_admit_015_standalone_evaluator_interface_v1`.
