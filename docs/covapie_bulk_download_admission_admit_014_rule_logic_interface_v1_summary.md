# CovaPIE ADMIT_014 standalone evaluator interface v1

## Scope and lineage

This increment implements the standalone, pure in-memory ADMIT_014 rule logic
on top of commit `0ec764f03bd3fe227a1e346380f1cdf31837f023`
(`add CovaPIE ADMIT_014 formal evaluator interface contract v1`). Its exact
parent is `d56140d8558208ee34eb5a43773010a2dc69169b`, and its exact tree is
`13c3d43310ec6eaa53004f92550e7184d1f67229`.

The implementation defines only `evaluate_admit_014` and the frozen Exact9
`Admit014EvaluationResult`. It does not define a unified adapter or
`_evaluate_registered_admit_014`, change `EVALUATOR_REGISTRY`, register
ADMIT_014, create an Exact14 runtime, implement mandatory pre-download
enforcement, map a provider, aggregate rules, form a combined candidate
verdict, perform network/download/raw operations, change model/checkpoint or
dataloader code, or perform training or parameter updates.

## Formal evaluator and result

The exact public signature is:

```python
evaluate_admit_014(
    *,
    stage_authorization_context: object = _MISSING,
) -> Admit014EvaluationResult
```

The sole parameter is keyword-only and uses a private singleton default.
Omission and explicit `None` therefore return a structured blocked result.
Positional calls and unknown keywords are rejected by Python.

The frozen Exact9 result fields are, in order:

1. `admission_rule_id`
2. `outcome`
3. `passed`
4. `blocks_candidate`
5. `reason`
6. `canonical_stage_authorization_record`
7. `validated_stage_authorization_fields`
8. `consumed_stage_authorization_fields`
9. `evaluator_io_used`

Direct construction rejects subclasses, field-order drift, non-exact built-in
string/boolean/tuple types, malformed canonical pairs, unknown or duplicate
validated/consumed fields, unknown outcomes or reasons, and all cross-field
contradictions. Outcomes are exactly `passed | blocked`; there is no
`invalid`. `evaluator_io_used` is always exact `False`.

## Frozen precedence and access behavior

The evaluator applies this first-failure order:

1. omitted or `None`: `STAGE_AUTHORIZATION_CONTEXT_REQUIRED`;
2. non-`Mapping`: `STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID`;
3. target `KeyError`: `CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING`;
4. other target lookup exception:
   `STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED`;
5. target value whose type is not exact `bool`:
   `CURRENT_STAGE_DOWNLOAD_AUTHORIZED_TYPE_INVALID`;
6. exact `False`: `BULK_DOWNLOAD_NOT_AUTHORIZED`;
7. exact `True`: pass with an empty reason.

For a mapping, the evaluator performs exactly one direct
`stage_authorization_context["current_stage_download_authorized"]` lookup. It
does not iterate, call `len`, `.get`, containment, or `bool(value)`. Extra keys
are allowed. The ADMIT_015 `current_stage_training_authorized` key may coexist
but is never accessed.

## Evidence and purity

The deterministic Exact6 contains the implementation contract, ordered
Exact61 truth matrix, Exact12 committed-source audit, formal purity audit,
byte-identical inherited Exact30 issue inventory, and manifest. The truth
matrix excludes the predecessor signature Exact8 and preserves the remaining
case identity/order: Exact37 evaluator-executable cases compare every Exact9
field and exact type against one committed Design-oracle execution, while
Exact24 malformed constructions are executed against the actual result class
and rejected.

The formal closure ends at the unique marker
`# === ADMIT_014 FORMAL EVALUATOR CLOSURE END ===`. Its Exact7 identity is the
private sentinel, two validation helpers, frozen result class, result
`__post_init__`, result factory, and evaluator. Per-definition CPython 3.10.4
normalized AST SHA256, marker-prefix SHA256, full production SHA256, reachable
bindings, permitted calls, and absence of I/O, mutation, and dynamic dispatch
are frozen.

The closure cannot reach filesystem, environment, subprocess, importlib,
network, provider, downloader, raw data, evidence materialization, registry,
dispatcher, model, or training behavior. Evidence imports and materialization
exist only after the marker.

The source boundary is ordered Exact12 and pins the committed formal production
and Exact6, authorization truth/manifest, ADMIT_013 production/manifest, and
Exact13 runtime production/manifest. Each source is a current-index stage-0
base-tree blob with frozen/current/base SHA equality and pinned no-follow
identity checks. The source audit records each real 40-character lowercase
base-tree blob ID and mode; the independent checker recomputes both from
`git ls-tree` and `git ls-files --stage` and requires exact row and manifest
agreement.

Canonical artifact construction and checking require CPython 3.10.4.
Noncanonical Python is limited to evaluator-only semantic smoke; changing the
canonical runtime requires an explicit contract refresh.

Materialization builds all bytes before mutation and pins the output parent
and staging directory with no-follow directory descriptors. Every leaf is
created exclusively relative to the staging descriptor and fsynced.
`RENAME_NOREPLACE` binds both names to the same parent descriptor; after
publication, the destination name must identify the still-open staging
inode both before and after the parent fsync. A complete pinned Exact6 read
then rechecks both inventories, all leaf descriptors and names, the root
descriptor and name, and the parent descriptor and name. An already
byte-identical Exact6 is an inode-preserving no-op; mismatch, concurrent
nonidentical publication, and GPFS `EINVAL` fail closed with no `os.replace`
fallback.

The independent checker uses the same pinned, no-follow traversal principle
for every committed source and output. Its manifest parser rejects duplicate,
missing, extra, or reordered top-level and nested fields, including readiness,
safety, materialization policy, source entries, output hashes, preconditions,
mapping consumption, AST evidence, and row counts. Deterministic race tests
replace or mutate real temporary files and directories at stat/open,
post-read, inventory, rename, and fsync boundaries; lifecycle tests also
reject tracked-but-ignored candidates and `check-ignore` errors.

## Readiness

The standalone evaluator, Exact9 result, and ADMIT_014 rule logic are
implemented. The Exact30 issue inventory remains byte-identical to the formal
contract: all seven ADMIT_014-specific issues remain effectively resolved,
the four global issues remain open, and coverage remains
`ADMIT_014|ADMIT_015`. Preconditions remain 49 complete and 2 incomplete;
`PRE_048` and `PRE_049` stay open because adapter projection and
registration/runtime are not part of this stage.

Current permission remains false and the authorized ADMIT_014 download
execution count remains zero. Mandatory enforcement, provider mapping,
network/download/raw execution, combined verdict, aggregation, and training
readiness remain false or unimplemented.

Step12D remains a smoke-legality check, not a final training-feature contract.
The historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False` state still require a feature-semantics audit
before training.

Recommended next step:
`design_covapie_admit_014_unified_adapter_contract_v1`.
