# CovaPIE unified dispatch runtime with ADMIT_001 to ADMIT_013 v1

This successor implements the formal ADMIT_013 unified adapter and registers
it in a new immutable Exact13 single-rule registry. The frozen base is
`dd17566f1b82eebcaaa49f17172a7b22a83b9c53`
(`add CovaPIE ADMIT_013 unified adapter contract design v1`).

The runtime identity-reexports the shared `UnifiedAdmissionRuleEvaluation`,
`UnifiedAdmissionDispatchError`, schema constants, error constants, and
outcome vocabulary from the committed Exact12 predecessor. Every
ADMIT_001–ADMIT_012 registry value is the identical predecessor handler
object. ADMIT_013 alone is bound to `_evaluate_registered_admit_013`.
The successor dispatcher is a distinct function with the predecessor's exact
signature and uses the local Exact13 registry. ADMIT_014 and ADMIT_015 remain
known but unregistered.

The handler routes in this order: batch must be `None`; evaluation context
must be a `Mapping`; download-result context must be a `Mapping`; stage
authorization must be `None`; candidate must be a `Mapping`; Exact4 required
download observations are read with ordered `__getitem__`; Exact3 optional
integrity-authority values are read with ordered `__getitem__`; the formal
evaluator is called once; its exact standalone result is validated; the
committed independent formal-interface Design oracle is called once; every
Exact12 field is compared for exact type and value; the result is projected
to the unchanged shared Exact13 schema.

A first Exact4 `KeyError` omits that keyword, stops later Exact4 lookups,
skips every authority lookup, and still calls the formal evaluator so its own
private default produces the frozen missing reason. A non-`KeyError` becomes
`ADMIT_013_DOWNLOAD_RESULT_CONTEXT_LOOKUP_FAILED`. After a complete Exact4,
all three optional authority names are attempted. Authority `KeyError`
omits and continues; any other exception becomes
`ADMIT_013_EVALUATION_CONTEXT_LOOKUP_FAILED`. The adapter does not import,
inspect, or pass the standalone private missing sentinel.

Candidate records are envelope-only and receive zero key, iteration, size,
`get`, or containment operations. A non-Mapping candidate returns the fixed
invalid blocking Exact13 result with four empty tuple fields and zero
formal/oracle calls.

The formal source must be the exact `Admit013EvaluationResult` type with
Exact12 dataclass/storage order, exact top-level types, successful
reconstruction, all nested pair/name/reason/outcome invariants, ADMIT_013
identity, and false evaluator I/O. Wrong exact type uses
`ADMIT_013_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID`; every other source, oracle,
equality, or projection drift uses
`ADMIT_013_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID`. Both fail closed with
`UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY` and `adapter_ready=false`.

`normalized_values` contains the canonical Exact4 download observations
followed by provided-valid Exact3 authority pairs. Exact integers become
canonical decimal strings; exact strings remain unchanged.
`validated_candidate_fields` contains download-observation pairs only,
`consumed_candidate_fields` contains download-observation names, and
`consumed_context_items` contains integrity-authority names. The historical
candidate field names do not imply candidate-record sourcing.

The public pure-memory closure contains 11 ordered definitions and ends at the
unique `# === CovaPIE ADMIT_001 TO ADMIT_013 PUBLIC RUNTIME CLOSURE END ===`
marker. It imports only the Exact12 predecessor, the ADMIT_013 standalone
evaluator, and the committed formal-interface oracle as project runtime
dependencies. The unified-adapter Design simulator is not imported or called
by the public closure.

The evidence source boundary is a fixed ordered Exact20 set: six Exact12
runtime authorities, six ADMIT_013 adapter-contract authorities, four
ADMIT_013 standalone authorities, three ADMIT_013 formal-oracle authorities,
and the original shared Exact13 authority. Every source must be tracked in
the current index, be a regular non-symlink base-tree blob with a real parent
chain, and match its frozen base/filesystem SHA through pinned no-follow reads
before output traversal. Revised1 pins the repository root with a no-follow
directory descriptor, traverses every parent component with `dir_fd`, reads
each leaf through its pinned parent, and rechecks the root, every parent, and
the full leaf identity after each read. The independent checker implements
the same contract without importing the production helper.

The Exact6 evidence contains 59 contract rows; 885 truth rows comprising the
committed Exact694 lineage plus structural successor continuity, the
committed ADMIT_013 Exact128 identities (102 normal projections and 26
negative source attestations), all Exact44 routing cases, and 19
dispatcher/identity cases; 39 registry/identity rows; 30 safety rows; the
transitioned Exact23 issue inventory; and one manifest. This does not claim a
new runtime replay of the 694 predecessor inputs. The committed predecessor
truth, frozen predecessor source, shared dispatcher schema, first-12 handler
object identities, successor signature/precedence, and targeted behavior
jointly establish continuity. The 23 inherited ADMIT_013 business cases
remain part of the Exact102 normal set.

Only `UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE` transitions. It stays open
and changes from `ADMIT_013|ADMIT_014|ADMIT_015` to
`ADMIT_014|ADMIT_015`, recording
`unified_dispatch_runtime_with_admit_001_to_013_implemented_v1`.
`UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED` remains open
for ADMIT_001–ADMIT_015, and the other Exact23 issue states do not change.

Canonical artifact building, source snapshots, materialization, and checker
execution require CPython 3.10.4. Import and pure evaluator semantic smoke do
not reject noncanonical Python at module import. Evidence publication uses
exclusive leaves, fsync, pinned directory descriptors,
`renameat2(RENAME_NOREPLACE)`, destination name/inode binding, complete-set
postverification, and inode-preserving identical-set reuse. Revised1 performs
a complete Exact6 full-identity recheck after traversal and revalidates the
parent, destination name, root descriptor, inventory, and every leaf after
the final root fsync for both existing-set and rename-success paths. The
checker rejects duplicate JSON keys and freezes the exact top-level,
readiness, output-SHA, and candidate-attestation key order. Its Exact10
lifecycle gate also requires an exact same-stage top-level/Exact6 inventory,
regular non-symlink leaves no larger than 100 MiB, a single all-untracked or
all-tracked-clean lifecycle, and the frozen base as an ancestor. GPFS
`EINVAL` fails closed without `os.replace` fallback or residue.

The strict semantic combined regression with the original Exact3
stage-local deselections has exactly one expected repository-state failure:
`tests/test_covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1.py::test_no_formal_evaluator_result_adapter_registry_or_exact13_runtime`.
That historical formal-design node asserts that the now-authorized successor
runtime path is absent; it is obsolete for this successor stage, not a
business-semantic regression. Revised1 therefore uses the precise Exact4
stage-local deselection set by adding only that node. The strict Exact3 run
must have no other failure or error, and the successor-authorized Exact4 run
must have zero failures, errors, or skips. This is not a claim that the full
repository pytest suite is green.

This stage does not implement ADMIT_014, ADMIT_015, combined candidate
verdict, cross-rule aggregation, provider mapping, network access, real
download, raw-data access, model/checkpoint/dataloader work, training,
fine-tuning, backward passes, optimizer steps, or parameter updates. Step12D
remains a smoke-legality check, not a final training-feature contract; a
feature-semantics audit is still required before training.

Recommended next step:
`audit_covapie_admit_014_formal_evaluator_interface_preconditions_v1`.
