# CovaPIE unified dispatch runtime with ADMIT_001–ADMIT_010 v1

## Baseline and scope

- Baseline commit: `73aa9b4e91e3f80da47da2909eb2702dc04e15c9`
- Baseline subject: `add CovaPIE ADMIT_010 unified adapter contract design v1`
- Runtime stage: `covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1`
- Manifest schema: `covapie_unified_dispatch_runtime_with_admit_001_to_010_manifest_v1`
- The Exact9 runtime and all committed ADMIT_010 standalone, adapter-design, and provenance sources remain unchanged.

## Runtime result

The successor exports the Exact9 `UnifiedAdmissionRuleEvaluation`,
`UnifiedAdmissionDispatchError`, and five public schema/vocabulary constants by
object identity. Its public `evaluate_admission_rule` is a new function object
with the Exact9 signature and is bound to the successor-local immutable Exact10
registry.

The registry contains ADMIT_001–ADMIT_010 in canonical order. The first nine
handlers are reused from Exact9 by object identity. ADMIT_010 is registered as
the sole new handler, `_evaluate_registered_admit_010`, with rule name
`leakage_group_assignment_before_split` and adapter ID
`covapie_admit_010_unified_adapter_v1`. ADMIT_011–ADMIT_015 remain known but not
registered.

ADMIT_010 enforces the frozen order: batch exact-`None`; evaluation `Mapping`;
one direct provenance lookup; download exact-`None`; stage exact-`None`;
candidate `Mapping`; one direct scalar lookup; one positional formal call;
exact-type and full Exact10 source validation; one independent-oracle call;
full Exact10 equality; and Exact13 projection. Only `KeyError` denotes a missing
mapping key. No adapter-side normalization, provider mapping, or context
injection into scalar-short results occurs.

## Evidence

- Fixed committed source boundary: Exact18, in the task-defined order, with
  tracked/base-blob/regular/non-symlink/resolved-descendant and triple-SHA
  verification.
- Runtime contract: 80/80 passing rows.
- Runtime truth matrix: 407/407 passing rows across eight natural groups:
  predecessor Exact9 (289), global dispatch (9), predecessor identities (9),
  ADMIT_010 context (7), mapping semantics (5), candidate envelope (8),
  standalone Exact71 (71), and source failures (9).
- Registry audit: 15/15 passing rows.
- Safety audit: 20/20 passing rows.
- Issue inventory: 11 rows. Only
  `UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE.affected_rules` and
  `.integration_transition` changed; coverage is now ADMIT_011–ADMIT_015 and
  remains open.
- Readiness: 24 true and 12 false values, mirrored at manifest top level.
- Manifest: 147 top-level keys.

Frozen output SHA256 values:

- `covapie_admit_001_to_010_runtime_contract.csv`:
  `da2ccbeef748a9ff503ff1e993bcdfb05ae436f92dcd4d46544c424f4f841874`
- `covapie_admit_001_to_010_runtime_truth_matrix.csv`:
  `2d087ef178cd7402fa3d0d40a8a22d2b0a726ed0f49ff2549f6893db15cb20ee`
- `covapie_admit_001_to_010_registry_routing_and_oracle_audit.csv`:
  `c797c6aad1a9951c61c85379fc2f633aa528bc593dd6f923de9416b7f07ccdbc`
- `covapie_admit_001_to_010_runtime_safety_audit.csv`:
  `2c2ae91713cbd05361db3b0a1e74045cc9b810e06133caceff53e8daf0b5786b`
- `covapie_admit_001_to_010_runtime_issue_inventory.csv`:
  `f59eecc7136ebdd148f2c6c6422b7a2bc0637e340322e09bc005eb00355db03c`
- `covapie_admit_001_to_010_runtime_manifest.json`:
  `46dcef1d5e62c5a8904e9ff66b145b6ee9dae88fc406e42d669a8a7002285198`

## Safety and stop boundary

Output authorization is checked before source reads. Relative output must
resolve within the real repository root; absolute temporary output may not use
parent symlink indirection. Existing entries must be allowlisted regular
non-symlinks. Writes use same-directory `.tmp` files, `fdopen("wb")`, flush,
`fsync`, `os.replace`, cleanup, and post-write Exact6 revalidation.

Provider mapping and real-provider export remain unvalidated and unexecuted.
ADMIT_011 has not started. `evaluate_all_rules`, combined candidate verdict,
cross-rule precedence, real candidate evaluation, raw/network download,
split/reassignment, checkpoint access, model forward/loss, and training are out
of scope and remain forbidden. Formal training still requires an independent
feature-semantics audit; Step12D remains a smoke-legality check only.

Recommended next step (not started):
`audit_covapie_admit_011_formal_evaluator_interface_preconditions_v1`.

## Revised1 closure

The output preflight is now completely non-mutating. When the authorized root
does not exist, preflight returns the resolved target and a creation decision
without creating files or directories. The runner validates sources, builds
runtime state, and constructs every payload before creating that root. A
dedicated prewrite gate then revalidates containment, directory identity, and
inventory immediately before the first atomic write.

Consequently, source validation failure leaves a missing output root absent
and leaves an existing safe output root byte- and metadata-identical. It emits
no output, `.tmp`, or `.part` file and does not reach `_atomic_write`.

The independent checker now owns literal, complete, ordered Exact10
`RULE_NAMES` and `ADAPTER_IDS` mappings. Expected registry rows and manifest
mapping values are built only from those checker-owned literals. Synchronized
runtime, registry-output, and manifest-output mapping drift therefore cannot
cause checker expectations to follow the tamper.

This revised1 closure does not alter the dispatcher, ADMIT_010 handler,
Exact10 registry or first-nine handler identities, routing and lookup
semantics, candidate envelope, formal/source/oracle behavior, projection,
issue transition, readiness, Exact18 boundary, or any of the six frozen output
files.
