# ADMIT_011 standalone evaluator interface v1

This successor implements only the formal, pure in-memory evaluator
`evaluate_admit_011(raw_target_relative_path,
existing_raw_target_relative_paths, raw_target_relative_path_contract)` and
its exact-ten-field `Admit011EvaluationResult` return contract.

Validation consumes the candidate scalar first, then the contract, then the
immutable occupied-path snapshot. The public declaration preserves the frozen
candidate-plus-historical-context order. Scalar failures consume no context;
contract failures consume only `raw_target_relative_path_contract`; snapshot
failures, mismatches, collisions, and passes consume contract then snapshot.
The exact lexical, case-sensitive collision policy is unchanged.

The successor evidence records formal output for all 84 committed design-truth
rows (including all 47 historical values), an AST/reachability purity audit,
an ordered fixed source boundary rooted at commit
`3c53da1e80d04ad68e5d1e9760b5a5bcdb1005b3`, and the Exact11 issue inventory.
The evaluator does not inspect a filesystem, raw data, checkpoints, providers,
or the design classifier. The source-boundary/materialization code is not
reachable from the evaluator.

This does not implement an ADMIT_011 adapter, runtime registration, provider
mapping, real provider evaluation, a combined verdict, raw download, model or
checkpoint work, or training. Feature-semantics audit remains required before
training; Step12D remains smoke legality only, not a final training-feature
contract. The next authorized step is
`design_covapie_admit_011_unified_adapter_contract_v1`.

## revised1A set-atomic evidence materializer hardening

The six frozen evidence files are unchanged. Only the metadata-only
materializer was hardened: it now completes a read-only `lstat` preflight,
builds and hash-verifies all payloads before any output mutation, pins parent,
root, staging, and leaf identities with directory file descriptors, and uses
descriptor-relative `renameat2(RENAME_NOREPLACE)` to publish a complete sibling
staging directory as one set. An exact existing set is an inode-preserving
no-op; any mismatch fails closed without repair. Capability absence, symlink,
identity, inventory, write, fsync, verification, and race failures fail closed.

This revised1A change does not alter evaluator semantics, output bytes,
checker semantics, source-boundary schema, purity schema, or manifest content.
The later revised1B work (transitive AST closure, fixed source boundary,
manifest exact-value checking, and independent semantic checking) remains out
of scope and pending.

## revised1B1 transitive closure and semantic evidence checks

The checker now starts only at `evaluate_admit_011` and recursively derives
the module-local AST closure. The frozen closure is exactly the public
evaluator, its five pure helper functions, `Admit011EvaluationResult`, and
`Admit011EvaluationResult.__post_init__`. The checker rejects direct or
indirect filesystem, process, dynamic-execution, design-oracle, metadata, and
materializer access, including aliases and newly reachable local helpers.

It independently verifies the Exact10 contract CSV, all 84 successor truth
rows against the committed design truth and the public evaluator, the Exact11
issue inventory against the committed path-contract inventory, and the purity
CSV against the computed closure. Synchronized-SHA tamper tests include every
truth-field class, contract/issue/purity changes, and a malicious candidate
representation that is rejected with `ast.literal_eval` without execution.

Production source and all six derived evidence outputs remain byte-identical.
Source-boundary hardening, full manifest exact-value checking, and pinned-FD
checker output-tree traversal remain explicitly pending revised1B2; this does
not claim final standalone-checker completion.

## revised1B1-fix1 closed-world purity analysis

The transitive closure discovery remains rooted only at
`evaluate_admit_011`, but purity validation is now closed-world rather than a
module denylist. Every reachable function or method is scope-aware checked:
only the frozen global/imported symbols, pure built-ins, call shapes, and data
attributes used by the real closure are permitted. Unknown globals, local or
reachable imports, module aliases, dynamic callables, dunder attributes,
network/process/serialization modules, and non-frozen AST structures fail
closed.

The reachable result class is now checked as an exact envelope: one literal
`@dataclass(frozen=True)` decorator resolving to `dataclasses.dataclass`, no
bases/metaclass, the ordered Exact10 object fields, and only
`__post_init__`. Tests mutate temporary copies of the real production source
to prove rejection of direct/local/aliased socket access, network clients,
dynamic import/execution and callable shapes, dunder escalation, and class
decorator/body bypasses. The production bytes and evidence outputs remain
unchanged; revised1B2 is still pending.

## revised1B1-fix2 runtime binding and exact AST freeze

Formal checker execution now first freezes the complete production source
bytes (`848e79085a28e17df09c1197a2474c64975e361252063155cb8633d7de52a316`),
the unique evaluator-closure marker, and the marker-prefix bytes
(`dd5ea58fa4d1fa229a596723ae2c1abefe9fa092246097da43f6d012cdc2e251`), before
reading any derived business evidence. It separately verifies provenance and
single-binding status for every evaluator runtime dependency: the seven local
definitions, `dataclass`/`fields`, every ADMIT_011 design-gate import, and the
three frozen evaluator module constants. The checker owns the exact imported
module/original-name map and constant values; it does not learn those expected
values from the imported production module at validation time.

Each of the Exact8 reachable definitions is additionally pinned by a
checker-owned normalized AST SHA256. Reachable attribute/subscript writes or
deletes, reflective mutation, and non-frozen local binding shapes fail closed;
the AST digests freeze statement order, guards, operators, literals, returns,
and result-class logic. Real-source temporary-copy tests cover post-marker and
pre-marker rebinding, `fields`/`dataclass`/constant rebinding, duplicate
imports, alias/deletion/comprehension/exception binding, marker drift, and
approved-method-before-type-guard or apparently pure semantic changes.

No production source, materializer, source-boundary logic, manifest, or six
derived outputs changed. revised1B2 remains pending; this still implements no
adapter, unified runtime, provider mapping or evaluation, download, model,
checkpoint, or training work.

## revised1B2 fixed evidence chain and pinned checker traversal

The production metadata path now owns the fixed, ordered Exact11 predecessor
source path/SHA mapping. Before it reads any of those source bytes, it verifies
repository identity and base lineage, every parent chain and leaf identity,
tracked/base-tree blob/mode status for all eleven sources, and the fixed source
configuration. Only then does it attest frozen SHA = base-tree SHA = current
filesystem SHA and construct the unchanged eleven-row source-boundary CSV.

The independent checker now imports only standard-library modules at import
time. Its formal successor source and all Exact11 inputs are structurally
attested before formal/design modules are lazily imported; their imported
`__file__` identities and runtime bindings are then checked against the
attested source. The checker opens an output root only through pinned
directory/file descriptors, validates identities and exact inventory before
and after reads, and gives semantic validators only pinned content bytes.

Manifest validation is now checker-owned and exact for every top-level,
nested-readiness, row-count, reason, precedence, safety, source/output, and
output-hash field. The six formal evidence outputs remain byte-identical.
This completes revised1B2 evidence-chain hardening, but does not authorize or
implement an adapter, unified runtime registration, provider mapping or real
provider evaluation, downloads, model/checkpoint work, or training.
