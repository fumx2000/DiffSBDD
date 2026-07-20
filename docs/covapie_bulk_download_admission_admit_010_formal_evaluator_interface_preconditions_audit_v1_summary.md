# CovaPIE ADMIT_010 formal evaluator interface preconditions audit v1

This read-only audit establishes that the repository contains enough committed evidence to begin design of `leakage_group_assignment_provenance_contract`, but not enough to freeze that contract, define the general `leakage_group_id` grammar, validate provider mapping, or implement ADMIT_010.

## Audited interface identity

- Rule: `ADMIT_010` / `leakage_group_assignment_before_split`
- Evaluation phase: `pre_final_split`
- Future candidate field: `leakage_group_id`
- Future caller context: `leakage_group_assignment_provenance_contract`
- Historical success/failure vocabulary: `leakage_group_assigned` / `leakage_group_unassigned`
- Primary blocker: `LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED`, still `open`

The canonical implementation-precondition contract says the future caller supplies the provenance context and that the evaluator itself needs neither filesystem nor network access. A future standalone evaluator can therefore remain pure in memory: it should validate the caller-provided candidate value and context, not run a grouping algorithm, inspect split files, or derive provenance from filesystem state.

## Field and provenance findings

`leakage_group_id` is the canonical admission field. The historical Step14AP, Step14AQ, and Step14AR artifacts predominantly use `final_leakage_group_id`. No committed contract in the fixed source boundary formally maps those two names, so the mapping remains `unverified`. The five values observed in the current 11-sample smoke artifacts are historical evidence only and do not define a general grammar.

`assignment_id` is an assignment-row identifier, not a group identifier. `group_split_assignment_id` and `sample_split_assignment_id` likewise identify split-assignment records. `duplicate_identity_key`, ligand graph/scaffold groups, and protein accession/exact-sequence/sequence-cluster groups are semantically distinct and cannot substitute for a final leakage group. Similar names or equal observed values do not prove equivalent provenance.

The historical assignment rows provide a policy string whose value ends in `_v1`, plus assignment status, sample membership, group membership, and group status. There is no standalone `policy_version` field and no frozen provenance contract. Design must explicitly decide how policy identity/version, assignment identity/status, membership evidence, and field mapping are represented.

## Stage ordering evidence

The committed boundaries establish this order:

1. Step14AP materializes unified group assignment and membership, reports `split_assignments_written=false`, and makes Step14AQ ready.
2. Step14AQ names Step14AP as its previous/source stage, SHA-binds the Step14AP assignment inputs, then executes the smoke split over `final_leakage_group_id`.
3. Step14AR names Step14AQ as its previous stage and consumes its group/sample split assignments to materialize final membership.

This is affirmative pre-split ordering evidence. A split assignment alone is not accepted as reverse proof that a valid provenance-bearing group assignment already existed.

## Deterministic outputs

The audit emits exactly six regular, non-symlink outputs: a natural 21-row precondition matrix, 401-row term occurrence inventory, 197-row deduplicated observed-value inventory, exact 32-source boundary, the byte-identical 11-row Exact9 issue inventory, and a timestamp-free manifest. Production and checker independently freeze the same ordered source paths and committed SHA256 values.

The issue inventory is unchanged byte-for-byte from Exact9. It keeps ADMIT_010 through ADMIT_015 in open coverage and makes no issue transition.

## Output materialization safety revised1

Before its first output write, the production materializer now validates the complete output-root inventory and applies `os.lstat` to the root and every existing entry. The root must be a real directory, its inventory may contain only the six authorized names, and every existing authorized entry must be a regular non-symlink file. Unexpected entries, directories, FIFOs, sockets, devices, and symlinks fail closed; unsafe state is neither cleaned automatically nor partially overwritten.

Each authorized payload is written to a `tempfile.mkstemp` file in the destination directory, flushed, synchronized with `os.fsync`, and installed with `os.replace`. A `finally` path removes any residual temporary file. The completed inventory is then revalidated as exactly six regular non-symlink files. Symlink rejection occurs before any write, so an external symlink target remains unchanged.

This revised output path changes no ADMIT_010 audit semantics and no output payload bytes. The provenance contract remains unfrozen, the primary blocker remains open, and evaluator/result/oracle/adapter/runtime implementation remains absent.

## Stop and readiness boundary

`ready_for_admit_010_leakage_group_assignment_provenance_contract_design=true` is supported because rule identity, field/context dependencies, historical membership/provenance evidence, stage ordering, and pure-memory feasibility are all auditable. The next step is `design_covapie_admit_010_leakage_group_assignment_provenance_contract_v1`.

All implementation and operational readiness remains false: the contract and grammar are not frozen; provider mapping is not validated; `evaluate_admit_010` and `Admit010EvaluationResult` do not exist; no oracle, adapter, registration, Exact10 runtime, combined verdict, real evaluation, split execution, reassignment, download, raw access, or training was performed. Formal training still requires a feature-semantics audit; Step12D remains a smoke-legality check, not a final training-feature contract.
