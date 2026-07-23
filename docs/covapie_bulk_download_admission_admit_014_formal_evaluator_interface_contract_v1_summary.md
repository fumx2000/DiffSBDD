# CovaPIE ADMIT_014 formal evaluator interface contract v1

This design-only stage freezes the future public ADMIT_014 evaluator signature
and Exact9 result contract. Its committed base is
`d56140d8558208ee34eb5a43773010a2dc69169b`, with parent
`30bbfaba4df0843d1f028e695d3dc499079a9b36` and tree
`3dbdc1a9723d30e05a1f856cc02ac60af5a25120`.

It does not implement `evaluate_admit_014`, define the formal
`Admit014EvaluationResult`, freeze or implement a unified adapter, register
ADMIT_014, create an Exact14 runtime, implement mandatory pre-download
enforcement, aggregate rules, execute provider/network/download/raw work, or
modify model, checkpoint, dataloader, or training behavior.

## Future public interface

The sole future public call contract is:

```text
evaluate_admit_014(*, stage_authorization_context: object = _MISSING) -> Admit014EvaluationResult
```

There is exactly one keyword-only parameter. Its annotation is `object` and
its default is a private missing singleton so an omitted context produces a
structured blocked result rather than a Python missing-argument `TypeError`.
Positional calls, unknown keywords, `*args`, `**kwargs`, candidate/batch/
evaluation/download-result contexts, provider results, policy mappings, and
fallback envelopes are rejected or absent from the signature.

The module exposes an `inspect.Signature` design and a pure in-memory design
oracle named
`classify_admit_014_formal_evaluator_interface_design`. Neither is the formal
evaluator.

## Exact9 future result

The frozen ordered fields and exact types are:

1. `admission_rule_id`: `str`
2. `outcome`: `str`
3. `passed`: `bool`
4. `blocks_candidate`: `bool`
5. `reason`: `str`
6. `canonical_stage_authorization_record`: `tuple`
7. `validated_stage_authorization_fields`: `tuple`
8. `consumed_stage_authorization_fields`: `tuple`
9. `evaluator_io_used`: `bool`

The future formal result is intended to be a frozen dataclass. This stage
defines only the exact, frozen, non-subclassable
`Admit014EvaluationResultContractDesign`, which validates types, values,
representations, and cross-field invariants fail closed.

`admission_rule_id` is always `ADMIT_014`. Outcomes are exactly `passed` or
`blocked`; there is no `invalid`. `passed` is true exactly for `passed`,
`blocks_candidate` is true exactly for `blocked`, the reason is empty exactly
for a pass, and `evaluator_io_used` is exact `False`. Here,
`blocks_candidate` means blocking later candidate/download-stage progression;
it does not claim that a combined verdict exists.

## Canonical, validated, and consumed representations

The canonical record is an exact tuple. It is either empty or contains one
exact two-item tuple:

```text
()
(("current_stage_download_authorized", False),)
(("current_stage_download_authorized", True),)
```

The key is exact built-in `str`; the retained value is exact built-in `bool`.
Tuple subclasses, pair subclasses, lists, dictionaries, duplicates, extra
pairs, the ADMIT_015 key, and stringified booleans are forbidden.

Validated and consumed fields are each either:

```text
()
("current_stage_download_authorized",)
```

They are exact tuples containing an exact string. Unknown, duplicate, or
ADMIT_015 fields and tuple/container subclasses are forbidden.

The result projections are:

| Input state | Canonical | Validated | Consumed |
|---|---|---|---|
| omitted or `None` | empty | empty | empty |
| non-mapping | empty | empty | empty |
| target `KeyError` | empty | empty | target field |
| other lookup failure | empty | empty | target field |
| target type not exact `bool` | empty | empty | target field |
| exact `False` | retained false pair | target field | target field |
| exact `True` | retained true pair | target field | target field |

## Closed precedence and mapping behavior

The exact first-failure precedence is:

1. omitted or `None`:
   `STAGE_AUTHORIZATION_CONTEXT_REQUIRED`;
2. non-mapping:
   `STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID`;
3. target lookup `KeyError`:
   `CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING`;
4. target lookup non-`KeyError`:
   `STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED`;
5. target value not exact `bool`:
   `CURRENT_STAGE_DOWNLOAD_AUTHORIZED_TYPE_INVALID`;
6. exact `False`:
   `BULK_DOWNLOAD_NOT_AUTHORIZED`;
7. exact `True`: passed with an empty reason.

The design oracle performs only:

```text
stage_authorization_context["current_stage_download_authorized"]
```

The target is accessed at most once. It never iterates, calls `len`, `.get`,
or containment. Extra keys are allowed. The canonical ADMIT_015
`current_stage_training_authorized` key may coexist but is never accessed.

## Evidence, transitions, and readiness

The ordered Exact11 source boundary contains the predecessor authorization
production and Exact6, the Exact51 precondition matrix, the Step14AU-A context
contract, and the Exact13 production and manifest. Each is a current-index
stage-0 tracked base-tree blob whose current, base, and frozen bytes match.
Pinned no-follow traversal verifies full device/inode/mode/size/mtime/ctime
identity before and after reading.

The deterministic Exact6 comprises an interface/result contract, an eight-row
routing projection, a 69-row truth matrix, an Exact11 source audit, the
inherited Exact30 issue inventory, and a manifest. The truth matrix includes
45 signature/context/lookup/type/business/mapping/projection cases and 24
negative result-contract cases.

The signature Exact8 is produced by real, case-specific evidence rather than
by an omitted-context business classification. The first six rows directly
inspect the frozen `inspect.Signature`, parameter, private missing default,
return annotation, and absence of varargs/varkw; their truth-matrix meta
outcome is `verified` with an empty meta reason. The positional and unknown
keyword rows execute both `Signature.bind` and the design-oracle invocation;
both paths must raise `TypeError`, so those rows record the meta outcome
`rejected` and meta reason `TypeError`. `verified` and `rejected` are evidence
outcomes only. They are not formal evaluator outcomes, whose vocabulary
remains exactly `passed | blocked`.

The Exact30 issue identity and order are preserved. The standalone-signature
and result-contract issues transition through
`resolved_by_successor_formal_interface_contract_design`; all seven
ADMIT_014-specific issues are now effectively resolved. The four known global
issues remain open, and unified coverage remains `ADMIT_014|ADMIT_015`
because ADMIT_014 is not implemented or registered.

Exact51 preconditions advance from 46 complete / 5 incomplete to 49 complete /
2 incomplete. This stage resolves `PRE_039`, `PRE_040`, and `PRE_041`.
`PRE_048` (adapter/Exact13 projection boundary) and `PRE_049`
(registration/runtime boundary) remain open and implementation-blocking.

Current permission and `ready_for_bulk_download_now` remain false. The formal
evaluator/result, adapter, registry, Exact14 runtime, mandatory enforcement,
provider mapping, combined verdict, aggregation, and training readiness remain
unimplemented or false.

Canonical artifact building and checking require CPython 3.10.4. A different
Python may be used only for evaluator semantic smoke; frozen AST, artifact
build, and checker evidence require explicit contract refresh.

Materialization builds all bytes before mutation, uses exclusive leaves,
directory and leaf fsync, pinned parent/root descriptors, and
`RENAME_NOREPLACE`. A byte-identical set is an inode-preserving no-op.
Mismatch and GPFS `EINVAL` fail closed; no `os.replace` fallback exists.
The independent checker output traversal is exercised with real temporary
filesystem races: same-byte replacement of an already-read leaf, same-byte
replacement of the whole output root, addition of a seventh leaf after leaf
reads, and removal of a leaf after leaf reads. Each race fails closed, while a
normal copied Exact6 reads successfully; the committed Exact6 is never
mutated by those tests.

Step12D remains a smoke-legality check, not a final training-feature contract.
The historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=false` state still require a feature-semantics audit
before training.

Recommended next step:
`implement_covapie_admit_014_standalone_evaluator_interface_v1`.
