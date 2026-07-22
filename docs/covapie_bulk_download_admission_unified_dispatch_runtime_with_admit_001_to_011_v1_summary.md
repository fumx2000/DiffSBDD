# CovaPIE unified dispatch runtime with ADMIT_001–ADMIT_011 v1

## Baseline and scope

- Baseline commit: `fab48133058b826f5e9387c06d3cb0024657aec9`
- Baseline subject: `add CovaPIE ADMIT_011 unified adapter contract design v1`
- Runtime stage: `covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1`
- Manifest schema: `covapie_unified_dispatch_runtime_with_admit_001_to_011_manifest_v1`
- The Exact10 runtime and all committed ADMIT_011 standalone, precondition,
  path-contract, adapter-contract, and oracle sources remain unchanged.

## Runtime result

The successor exports the Exact10 `UnifiedAdmissionRuleEvaluation`,
`UnifiedAdmissionDispatchError`, and five public schema/vocabulary constants by
object identity. Its public `evaluate_admission_rule` is a new function object
with the Exact10 signature and is bound to the successor-local immutable
Exact11 registry.

The registry contains ADMIT_001–ADMIT_011 in canonical order. The first ten
handlers are reused from Exact10 by object identity. ADMIT_011 is the sole new
handler, `_evaluate_registered_admit_011`, with rule name
`raw_overwrite_forbidden` and adapter ID
`covapie_admit_011_unified_adapter_v1`. ADMIT_012–ADMIT_015 remain known but
unregistered.

ADMIT_011 enforces the frozen thirteen-step route: batch exact-`None`;
evaluation `Mapping`; one direct contract lookup; one direct snapshot lookup;
download exact-`None`; stage exact-`None`; candidate `Mapping`; one direct
scalar lookup; one positional formal call; exact-type and full Exact10 source
validation; one independent-oracle call; exact-type and full-value oracle
equality; and Exact13 projection. Only `KeyError` denotes a missing mapping
key. Candidate values and both context objects are forwarded by identity.
Formal exceptions propagate; source-shape and oracle failures fail closed under
the frozen unified adapter error contract.

## Evidence

- Fixed committed source boundary: Exact23 in task-defined order, with baseline
  subject/ancestry, tracked/base-blob/tree-mode, real-parent-chain,
  regular/non-symlink/resolved-descendant, pinned-descriptor, and base/filesystem
  triple-SHA verification before project import or source consumption.
- Runtime contract: 36/36 passing rows.
- Runtime truth matrix: 534/534 passing rows across predecessor Exact10 (407),
  global dispatch (9), first-ten handler identity and parity (10), ADMIT_011
  context routing (7), mapping semantics (3), candidate envelope (2),
  standalone Exact84 including historical Exact47 (84), and source/oracle
  failures (12).
- Registry audit: 15/15 passing rows.
- Safety audit: 35/35 passing rows.
- Issue inventory: 11 rows. Only
  `UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE.affected_rules` and
  `.integration_transition` changed; coverage is now ADMIT_012–ADMIT_015 and
  remains open.
- Readiness: 18 true and 12 false values, mirrored at manifest top level.
- Manifest: 143 top-level keys.

Frozen output SHA256 values:

- `covapie_admit_001_to_011_runtime_contract.csv`:
  `9616573151091786f07b3c4d1b6c8343a1ceb796f439e495023abd2f3ad37626`
- `covapie_admit_001_to_011_runtime_truth_matrix.csv`:
  `c6d543b9c1ad6760e202074b981659ca34155c16ec0435b1cec3035c93d90901`
- `covapie_admit_001_to_011_registry_routing_and_oracle_audit.csv`:
  `0ceb3aa607fb9a539a3d5a6fd519a685693d765b3606e52be9d3316ce476c752`
- `covapie_admit_001_to_011_runtime_safety_audit.csv`:
  `3ec709b1e9cfd82e2fa17bd05013e7a392bf709de85f4f00e37886577a749dd1`
- `covapie_admit_001_to_011_runtime_issue_inventory.csv`:
  `976e3b195d20cacaf0658b38fb88f922479bc9e4ac29e8834933cc734fe8935b`
- `covapie_admit_001_to_011_runtime_manifest.json`:
  `9895bf9b82eb9ca0f9c90ef8012af644a2b325dd971c3e6655b361fc8ff83011`

## Verification result

The revised1 targeted module contains 63 test functions, 19 parameterized
decorators, and 95 parameterized cases; all 139 collected cases passed. The new
independent checker passed twice with byte-identical 758-byte stdout; stdout
SHA256 is
`96c6de2fd8a727139a97cc6682e74ef0d8eb88bc67fa30fab2149dadda3a55e6`.

Required historical regressions produced the frozen results:

- ADMIT_011 adapter contract: 116 passed; checker passed.
- ADMIT_011 standalone: 262 passed; checker passed.
- ADMIT_011 path contract and formal preconditions: 101 and 24 passed;
  both checkers passed.
- ADMIT_009/010 adapters: 52 and 62 passed; both checkers passed.
- ADMIT_009/010 standalone evaluators: 61 and 77 passed; both checkers passed.
- Exact10 runtime: 67 passed and exactly one expected fixed-AST-hash failure,
  `test_runtime_business_function_ast_sha256_is_unchanged`; its independent
  checker passed. The predecessor source and historical test were not edited.
- Direct dispatcher identity/first-ten parity and Exact10-to-Exact13 checks
  passed. Compilation, production/checker silent imports, and `git diff
  --check` passed.

## Revised1 pre-commit hardening

The checker now attests the untracked successor before any project import or
execution. It verifies the real repository and parent chain, regular
non-symlink lexical leaf, containment, pre-open identity, no-follow descriptor
identity, post-read descriptor and lexical identity, and pinned-byte SHA256.
The successor AST is parsed only from those attested bytes. Immediately before
and after import, the checker repeats lexical/inode/pinned-byte validation and
requires `module.__file__` and `module.__spec__.origin` to equal the attested
path. The imported successor and its three project dependencies must be the
exact `sys.modules` objects at their Exact23-attested source paths. The unsafe
in-process reload was removed; silent/no-side-effect import is checked in an
isolated subprocess that first verifies the frozen source SHA.

The public runtime closure is a checker-owned closed world of exactly ten
module-level definitions. Their normalized AST SHA256 values are:

- `evaluate_admission_rule`: `11740861a0117d11a4fc64f9ead737a39010fdd957dbae2c2cf92e594c157548`
- `_raise_dispatch_error`: `adb1d13a5bea21730e5d56742c1ba46faa30b5c31d80f827a892de73cc6e1356`
- `_admit011_context_failure`: `b8f79418a5c7ac9c0ab746ccbcfdd2db09dd5fd88164f0379cd7990715eec237`
- `_admit011_adapter_failure`: `f5e0ffb443aa5213f02e976e10da2f900e46e1634299a30d16bcbcb294a97a8a`
- `_admit011_candidate_invalid`: `ccdb8c278eb486cf47dc09b41cdc91baf2df29a6e144d2871af77c55df752067`
- `_prevalidate_admit011_source`: `3255e9a9603226375049d0b35abd0028c5ec67b12fe524595a50cabd9bb59da5`
- `_expected_admit011_from_oracle`: `2b946d1772083ff244a9ea3d97be660048c48cee1ea06e0f1d7290b993af55a6`
- `_validate_admit011_oracle_equivalence`: `3f75097ae9292f582d68d3f5ad33c275ff2f02e852bcd7f95b424fbfa104567c`
- `_project_admit011_exact13`: `80d92d3210ddfb7483660aa360678b376450be4e12c9e8987aa4b4aff1b525ef`
- `_evaluate_registered_admit_011`: `1f56e6b007f7c33e480e9b720a97db8236fa7bb6de7cb6b78b16a8d0bf94cbd4`

All reachable local calls must resolve inside that set; imported calls and
pure built-ins use exact allowlists. Lambda/call-returned/dynamic attribute
callables, arbitrary subscript callables, dunder discovery, dynamic import,
mutation, local imports, `with`/filesystem access, and unknown helpers are
rejected. The sole subscript-call form is the exact AST-frozen local registry
dispatch already required by the frozen dispatcher. The complete runtime
import inventory and 34 protected bindings are checker-owned and frozen by
origin and normalized binding-statement SHA, preventing late module rebinding,
alias replacement, additional definitions, decorators, and import-time
expressions.

Negative tests prove that the superseded direct-name denylist would accept an
indirect `_evil_helper` and late candidate-invalid rebinding, while revised1
rejects both without creating their marker. Two-level open/socket/subprocess
helpers, protected module aliases, local imports, decorator side effects,
subscript calls, dunder discovery, dynamic calls, and state mutation are also
rejected before successor execution. SHA drift, source/parent symlinks,
attestation-to-import replacement, post-import replacement, and wrong imported
module paths all fail closed.

Checker output traversal now completes parent/root/Exact6 leaf structural
preflight before reading any byte, freezes every identity, pins the root and
each leaf with directory-relative no-follow descriptors, and repeats the full
parent/root/inventory/leaf identity check after all reads. Tests cover parent,
root, broken symlink, regular file, FIFO, unexpected/missing inventory,
leaf symlink/directory/FIFO, root replacement, stat-to-open replacement,
mid-read leaf replacement, parent inode replacement, post-read inventory race,
normal pinned reading, and non-mutation.

Revised1 changes only the checker, targeted tests, and this summary. The
runtime SHA remains
`ca8e64897b30f961d999d37ce8af5eb985ddf34f332af40c29bf2142bad6e2c8`;
the Exact23 boundary, all runtime behavior and bindings, six derived files and
their hashes, 36/534/15/35/11 evidence rows, and 143-key manifest are unchanged.

## Set-atomic publication and workspace capability

The production publisher constructs and verifies the complete Exact6 payload
before mutation, creates a same-parent staging directory and all leaves with
exclusive/no-follow descriptors, flushes and fsyncs every file and directory,
publishes with `renameat2(RENAME_NOREPLACE)`, fsyncs the parent, and revalidates
the complete set. Existing identical output is an inode-preserving no-op;
mismatch repair, symlink traversal, unknown inventory, races, partial sets, and
unsafe cleanup all fail closed.

The workspace GPFS returned `EINVAL` for the required no-replace rename during
the one attempted publication into the repository filesystem. The attempt
failed closed before target publication and left no staging residue; no weaker
rename fallback was enabled. The exact payload set was then generated once by
the same production materializer on a filesystem supporting the required
primitive, copied into this candidate through the controlled patch path, and
verified byte-for-byte against all six frozen hashes. The checker subsequently
performed two deterministic materializations plus an inode-preserving no-op
and validated equality with the candidate set. This filesystem limitation does
not weaken the production contract, but repository-local first publication by
that runtime remains unavailable on this GPFS mount.

## Safety and stop boundary

Provider mapping and real-provider export remain unvalidated and unexecuted.
ADMIT_012 has not started. `evaluate_all_rules`, combined candidate verdict,
cross-rule precedence, real candidate evaluation, raw/network download,
split/reassignment, checkpoint access, model forward/loss, backward passes,
optimizer updates, and training are out of scope and remain forbidden.

Formal training still requires an independent feature-semantics audit. The
historical `UNKNOWN_ATOM_FEATURE_POLICY` and `feature_semantics_known=False`
state remains a readiness blocker, and Step12D remains a smoke-legality check,
not a final training-feature contract.

Recommended next step (not started):
`audit_covapie_admit_012_formal_evaluator_interface_preconditions_v1`.
