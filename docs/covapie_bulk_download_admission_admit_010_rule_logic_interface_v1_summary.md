# CovaPIE ADMIT_010 standalone evaluator interface v1

This increment implements the standalone, pure in-memory ADMIT_010 evaluator and stops before unified-adapter design or runtime registration.

## Public contract

`evaluate_admit_010(leakage_group_id, leakage_group_assignment_provenance_contract) -> Admit010EvaluationResult` has exactly two required positional-or-keyword parameters, no defaults, and no variadic arguments. It does not copy, normalize, repair, sort, deduplicate, mutate, group, split, or perform I/O.

`Admit010EvaluationResult` is a frozen dataclass without slots. Its Exact10 field order is:

1. `admission_rule_id`
2. `outcome`
3. `passed`
4. `blocks_candidate`
5. `reason`
6. `canonical_leakage_group_id`
7. `validated_candidate_fields`
8. `consumed_candidate_fields`
9. `consumed_context_items`
10. `evaluator_io_used`

Construction validates all exact built-in types before value comparison, membership, or cross-field validation. Result subclasses, string and tuple subclasses, coercions, hostile comparators, invalid tuple shapes, and inconsistent states fail closed.

The evaluator directly reuses the committed `LeakageGroupAssignmentProvenanceContractV1` class identity and frozen ADMIT_010 constants. It independently implements the committed 21-level validation precedence. The committed design classifier is absent from the formal evaluator call graph and is used only by tests, the checker, and metadata parity materialization.

## Deterministic evidence

The formal truth matrix contains the committed natural Exact71 corpus in its exact case order and ten frozen groups. Every row records all Exact10 fields and passes full 10/10 equality against the committed design oracle. The evidence contains:

- interface contract: 41/41 rows
- formal/design truth matrix: 71/71 rows
- fixed source boundary: 13/13 rows
- safety audit: 35/35 rows
- authoritative issue inventory: 11/11 rows
- manifest: one deterministic JSON document with 31 readiness values

The authoritative issue inventory is byte-identical to the committed predecessor and retains SHA256 `779932531b630072ff33721e689a2865defdad477df8335a9950c8e4537476bd`. The provenance blocker remains resolved. Unified admission coverage remains open for ADMIT_010 through ADMIT_015; no issue transition occurs in this step.

The materializer completes source and output preflight before its first write, accepts only the exact output-name allowlist, rejects non-regular or symlink entries, writes through same-directory `.tmp` files with flush/fsync/atomic replace/final cleanup, and revalidates the exact six-file inventory after writing.

## Readiness and stop boundary

The standalone evaluator, Exact10 result contract, exact-type and cross-field invariants, runtime precedence, design-oracle independence, and full Exact71 parity are implemented. The next authorized design step is `design_covapie_admit_010_unified_adapter_contract_v1`, but it is not started here.

Provider mapping remains unvalidated with zero real-provider leakage-group identifiers. No unified adapter was designed or implemented, ADMIT_010 was not registered, the Exact10 unified runtime was not created, and ADMIT_011 was not started. There was no real candidate evaluation, raw or checkpoint access, network or download activity, split or reassignment, model execution, training, fine-tuning, optimizer step, staging, commit, or push.

Formal training remains prohibited until a separate feature-semantics audit resolves or formally audits the historical unknown atom-feature policy. Step12D remains only a smoke-legality check, not a final training-feature contract.

## Revised1 evidence and output containment closure

The revised1 closure validates resolved output containment before source reads, payload construction, or writes. Relative output roots must resolve beneath the real, non-symlink repository root. Absolute temporary output roots remain supported only when their lexical absolute parent and target exactly match their strict resolved paths, so parent-directory symlink indirection is rejected. Unsafe targets fail closed without calling `build_interface_state`, changing external-directory contents, creating partial outputs, or leaving `.tmp` files.

The independent checker now constructs and compares the complete Exact102 manifest, including every scalar, nested dictionary, ordered list, all 13 source-verification records, readiness values and mirrors, output hashes, materialization contract, stop boundaries, and validation markers. It also independently constructs and compares every field of all Exact41 contract rows in exact order. Semantic tampering remains rejected with frozen-output-hash enforcement disabled.

This revision does not change the formal evaluator five-function closure, public API, Exact10 result contract, Exact19 identity, 21-level precedence, Exact71 corpus or parity, issue inventory, readiness, recommended next step, or any of the six deterministic output bytes.
