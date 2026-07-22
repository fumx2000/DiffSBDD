# ADMIT_012 standalone evaluator interface v1

This stage implements the formal, pure in-memory keyword-only
`evaluate_admit_012` interface and its frozen Exact10
`Admit012EvaluationResult` contract. It is based on commit
`3e75daf58475de9deabc1efb55d978a2f458d0d5` (`add CovaPIE ADMIT_012 formal
evaluator interface contract v1`).

The evaluator validates the Exact4 download-result fields in frozen presence
order and then in frozen type/value order. Only after all fields are valid does
it validate the four policy contexts, checking each exact outer tuple type
before exact content. Missing fields return `blocked`; field or context
contract failures return `invalid`; a complete valid input returns `passed`.
The canonical record is empty before field validation completes and is the
complete ordered Exact4 tuple thereafter. Validated fields and consumed fields
or contexts are exact ordered prefixes. The evaluator always reports
`evaluator_io_used=False`.

ADMIT_012 does not judge download success or integrity. Consequently the
frozen `failure` status and legal 4xx or 5xx HTTP values pass when all field and
context contracts are valid. ADMIT_013 is not implemented or invoked here.

The formal closure is the exact eight-definition set
`evaluate_admit_012`, `_record`, `_make_result`, `_context_reason`,
`Admit012EvaluationResult`, `Admit012EvaluationResult.__post_init__`,
`_ordered_pair_prefix_valid`, and `_field_pair_valid`. The checker freezes the
full production SHA256, the unique marker-prefix SHA256, every normalized AST
SHA256, the exact imports and runtime bindings, the frozen result-class
envelope, and a closed-world call/mutation boundary. Formal source is pinned
and attested before lazy import; the imported file, spec, module identity,
constants, defaults, dataclass and regular-expression bindings are then
rechecked without reload.

The Exact6 evidence contains an 18-row signature/result contract, the exact
105 predecessor cases (52 field, 39 context, 6 cross-phase, and 8 negative
result-invariant cases), an ordered Exact18 base-anchored source boundary, a
14-row purity audit, the unchanged Exact16 issue inventory, and one manifest.
Expected truth semantics are independently owned by the checker and decoded
with `ast.literal_eval` plus explicit non-literal tokens; no `eval` is used.
The two open issues remain unified coverage and cross-rule aggregation, and
coverage remains `ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015` until ADMIT_012 is
actually registered in a future Exact12 runtime.

The canonical repository filesystem rejected the single formal set-atomic
publication attempt with `renameat2(RENAME_NOREPLACE)` `EINVAL`. The operation
failed closed without `os.replace`, without a published target, and without a
staging residue. In accordance with the frozen policy, the Exact6 set was then
generated once on a supporting temporary filesystem, verified against a
second in-memory build by byte and SHA256, copied as the controlled generated
set, and verified again byte-for-byte. No retry of formal GPFS publication was
performed.

This stage does not implement an adapter, alter a registry or dispatcher,
modify the Exact11 runtime, register ADMIT_012, implement ADMIT_013, map a
provider, perform a download, read raw data, touch model/checkpoint paths, or
perform training or parameter updates. Feature-semantics audit remains
required before training, and Step12D remains
`smoke_legality_only_not_final_training_feature_contract`.

The only authorized next step is
`design_covapie_admit_012_unified_adapter_contract_v1`; this stage does not
authorize proceeding directly to Exact12 runtime work.
