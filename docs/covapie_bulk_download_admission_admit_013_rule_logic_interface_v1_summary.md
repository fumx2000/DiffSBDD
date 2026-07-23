# CovaPIE ADMIT_013 standalone evaluator interface v1

## Scope and lineage

This increment implements the standalone, pure in-memory ADMIT_013 rule logic on
top of commit `79e63dce368722b126ad21208a3de13f7ea4b6df` (`add CovaPIE
ADMIT_013 formal evaluator interface contract v1`). Its exact parent is
`2eea08835c4ef88d5b810509134f8eef94e3e99e`, and its exact tree is
`ac3633abc2cf52a715faf36faea827f76d4236d9`.

The public implementation consists of `evaluate_admit_013` and the frozen
Exact12 `Admit013EvaluationResult`. This stage does not implement an adapter,
change `EVALUATOR_REGISTRY`, register ADMIT_013, create an Exact13 unified
runtime, aggregate rules, produce a combined candidate verdict, connect a
provider, perform a network/download/raw operation, change model/checkpoint or
dataloader code, or perform training or parameter updates.

## Formal evaluator

The exact public signature is:

```python
evaluate_admit_013(
    *,
    download_result_status: object = _MISSING,
    observed_http_status: object = _MISSING,
    observed_content_length_bytes: object = _MISSING,
    observed_sha256: object = _MISSING,
    expected_content_length_bytes: object = _MISSING,
    expected_sha256: object = _MISSING,
    explicit_integrity_verdict: object = _MISSING,
) -> Admit013EvaluationResult
```

All seven parameters are keyword-only and preserve their original exact type
and value. `_MISSING` is a module-private singleton distinct from `None`,
`False`, `0`, and the empty string. The evaluator performs no conversion,
normalization, inference, default filling, file access, hashing, provider call,
or other I/O.

The frozen phase order is `Exact4_presence`, `Exact4_type_value`,
`Exact3_optional_authority_type_value`, `Exact7_business_outcome`, and
`passed`. Required Exact4 presence is completed before Exact4 type/value
validation. Optional Exact3 absence is legal; a present authority is validated
by exact built-in type before range, grammar, or enum value. The first failure
returns immediately.

After structural success, business precedence is:

1. `DOWNLOAD_RESULT_STATUS_FAILURE`
2. `OBSERVED_HTTP_STATUS_NOT_SUCCESS`
3. `OBSERVED_CONTENT_EMPTY`
4. `OBSERVED_SHA256_MISMATCH`
5. `EXPLICIT_INTEGRITY_VERDICT_FAILED`
6. `OBSERVED_CONTENT_LENGTH_MISMATCH`
7. `INTEGRITY_AUTHORITY_MISSING`
8. pass with an empty reason

An exact expected/observed SHA match or explicit `verified` verdict is strong
authority. Expected-length agreement alone is not. Every provided authority
must agree; a mismatch or `failed` verdict cannot be overridden by another
passing authority.

## Exact12 result

`Admit013EvaluationResult` is an exact, frozen dataclass with fields, in order:

1. `admission_rule_id`
2. `outcome`
3. `passed`
4. `blocks_candidate`
5. `reason`
6. `canonical_download_result_record`
7. `canonical_integrity_authority_record`
8. `validated_download_result_fields`
9. `validated_integrity_authority_fields`
10. `consumed_download_result_fields`
11. `consumed_integrity_authority_fields`
12. `evaluator_io_used`

Construction fails closed for subclasses; field-order drift; non-exact
top-level strings, booleans, or tuples; malformed, partial, reordered,
duplicated, or extra canonical pairs; tuple/pair subclasses; sentinel leakage;
noncanonical validated/consumed sequences; unknown outcomes/reasons; and every
reason/phase contradiction. `passed` is true exactly for outcome `passed`,
`blocks_candidate` is true exactly otherwise, the reason is empty exactly when
passed, and `evaluator_io_used` is always exact `False`.

## Evidence and independent checking

The deterministic Exact6 evidence set contains the implementation contract,
Exact128 truth matrix, Exact12 source boundary audit, formal-closure purity
audit, byte-identical inherited Exact23 issue inventory, and manifest. The
truth matrix projects all 102 evaluator/result cases from the committed Design
oracle, including the inherited Exact23 business cases, and records actual
fail-closed rejection for all 26 result-negative cases.

The formal closure ends at the unique marker
`# === ADMIT_013 FORMAL EVALUATOR CLOSURE END ===`. Its ordered definition
list is Exact10: the original nine definitions in their frozen order followed
by the private sentinel class `_MissingAdmit013Value`. The normalized AST
SHA256 values, marker-prefix SHA256, and full production source SHA256 are
frozen in the manifest. The sentinel purity row attests its private-sentinel
definition kind and the absence of forbidden I/O, mutation, and dynamic
dispatch. The complete purity audit proves the reachable closure contains no
file, path, OS I/O, subprocess, socket/network, provider, raw, adapter/runtime,
dynamic import/dispatch, `eval`/`exec`, or global/nonlocal mutation.

Frozen evidence is authoritative only under canonical CPython 3.10.4. Formal
AST attestation, artifact build/materialization, the independent checker, and
frozen-evidence verification fail fast on any other interpreter with the
required and observed runtime identities and an explicit version-sensitivity
message. Importing the production module, constructing the result, and calling
the evaluator remain legal on noncanonical Python solely as non-authoritative
evaluator semantic smoke. In particular, a Python 3.12 smoke run does not
authorize updating any frozen SHA. Moving the evidence runtime to Python 3.12
requires a separate explicit contract-refresh migration stage.

The independent checker does not import the production module. It validates
the canonical runtime, base ancestry, and the frozen committed source boundary
before reading any new output. For each Exact12 source it independently checks
safe relative-path grammar, non-symlink directory ancestry, Git tracking and
base-tree blob mode, a pinned no-follow read, and base/current/frozen SHA
identity. It then statically reconstructs the signature, result storage and
formal closure, recomputes AST hashes, applies an independent Exact7 classifier
to the 102 normal truth rows, validates the Exact23 and Exact26 projections,
and verifies exact CSV semantics and manifest keys/order.

The checker pins the output root with
`O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC`, inventories Exact6 with
`os.listdir(root_fd)`, opens every leaf relative to that directory FD, and
rechecks parent, root-FD, root lexical, inventory, and leaf identities after
all reads. Root/leaf replacement, symlinks, and extra or missing outputs fail
closed. Lifecycle validation additionally applies the narrow
`*admit_013_rule_logic_interface*` glob in `src/covalent_ext`, `scripts`,
`tests`, and `docs`; those four observed files plus Exact6 must equal Exact10.
Unrelated commits and unrelated tracked, staged, untracked, or ignored cache
files do not alter that stage-scoped lifecycle result.

The publisher uses build-before-mutation, exact inventory, non-symlink roots
and leaves, `O_EXCL` staging leaves, leaf and directory fsync,
`RENAME_NOREPLACE`, root `O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC`, leaf reads via
`dir_fd`, identity rechecks, and an inode-preserving byte-identical no-op.
Mismatch and GPFS `EINVAL` fail closed without `os.replace` fallback or staging
residue.

## Readiness

The standalone evaluator, result type, and rule logic are implemented, and the
next authorized step is exactly
`design_covapie_admit_013_unified_adapter_contract_v1`. The unified adapter,
registration, Exact13 runtime, provider mapping/evaluation, real bulk download,
combined verdict, and cross-rule aggregation remain unimplemented.

Training remains blocked. Step12D was a smoke legality check, not a final
training-feature contract. A feature-semantics audit must still resolve or
formally audit the historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False` state before training.
