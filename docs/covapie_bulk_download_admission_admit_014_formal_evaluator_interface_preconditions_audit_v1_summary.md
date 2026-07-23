# CovaPIE ADMIT_014 formal evaluator interface preconditions audit v1

This read-only design audit freezes the historical identity of ADMIT_014:

- rule ID: `ADMIT_014`
- rule name: `current_gate_grants_no_download_permission`
- evidence source: `current_design_gate`
- required status: `bulk_download_not_authorized_now`
- severity and reason: `blocking` / `bulk_download_not_authorized`
- evaluation phase: `current_step`
- network required: `false`
- raw structure required: `false`
- ready for future implementation: `true`

The final flag means only that contract design may continue. It does not
authorize a download, registration, provider execution, raw write, or
training.

## Current committed fact and future evaluator boundary

The committed Step14AT gate explicitly grants no download permission.
Step14AT, Step14AU-A, the current Exact13 runtime, and canonical final-dataset
QA all report `ready_for_bulk_download_now=false`. The audited current step
used no network, download queue, download manifest, or raw write.

That current fact is distinct from a future ADMIT_014 evaluator contract.
Committed Step14AU-A evidence selects
`future_explicit_authorization_context`, with context item
`current_stage_download_authorized`, scope `stage`, and a future caller as
provider. Candidate-record, batch-context, and download-result authorization
sourcing are forbidden. The evaluator therefore has no ADMIT_001..013
rule-result dependency and can remain pure in memory with no filesystem or
network access. The alternative `current_stage_constant_guard` is explicitly
rejected. Neither that selection nor the available context contract grants
download permission now.

The exact successor envelope ownership (`evaluation_context` versus
`stage_authorization_context`), built-in type, closed value vocabulary,
normalization/coercion, trusted producer, provenance, freshness/replay,
missing/invalid/contradiction behavior, false-to-true transition semantics,
outcome/reason vocabularies, precedence, signature, result, normalized
representation, adapter projection, registration, caller-level enforcement,
aggregation relationship, and provider/download boundary remain open
implementation-blocking preconditions.

## Current unified runtime boundary

ADMIT_001 through ADMIT_013 are registered in the current immutable
single-rule dispatcher. ADMIT_014 and ADMIT_015 are known but not registered.
The dispatcher signature contains `stage_authorization_context`, but the
current runtime gives that envelope no ADMIT_014 semantics and contains no
ADMIT_014 handler.

The runtime does not implement a combined candidate verdict, cross-rule
aggregation, provider mapping, network access, download execution, or a
caller-level mandatory ADMIT_014 guard. This audit does not add any of those
capabilities.

## Evidence

The deterministic Exact6 evidence contains:

- a 51-row ordered precondition matrix across identity, current committed
  state, authority/evidence, scope/routing, outcome/interface, and
  integration/enforcement;
- a 20-row authorization-evidence and routing-responsibility matrix;
- a 13-row current-gate observed-state inventory, including the authoritative
  Step14AU-A context contract;
- a fixed 15-source boundary audit;
- the inherited Exact23 issue inventory followed by Exact7 new open blocking
  ADMIT_014 issues, producing Exact30;
- one manifest with schemas, row/group counts, readiness, safety, source
  identities, output hashes, and the training boundary.

There are 25 complete preconditions and 26 incomplete implementation-blocking
preconditions. An incomplete implementation precondition does not fail this
audit: the audit passes because it reports the committed facts and open gaps
truthfully. Audit success is not implementation readiness.

The source boundary is a small explicit set: four Step14AT authorities, four
Step14AU-A authorities, five current Exact13 runtime authorities, and two
canonical QA safety/training authorities. Every source is a current-index
tracked regular base-tree blob with a frozen SHA256, read through pinned
no-follow descriptors with post-read identity verification. No `data/raw` or
checkpoint path is included.

## Issues and readiness

The Exact7 new issues are:

1. `ADMIT_014_AUTHORIZATION_EVIDENCE_SOURCE_UNRESOLVED`
2. `ADMIT_014_STAGE_AUTHORIZATION_ROUTING_RESPONSIBILITY_UNRESOLVED`
3. `ADMIT_014_PERMISSION_VALUE_VOCABULARY_UNRESOLVED`
4. `ADMIT_014_PERMISSION_TRANSITION_AND_PRECEDENCE_UNRESOLVED`
5. `ADMIT_014_STANDALONE_SIGNATURE_UNRESOLVED`
6. `ADMIT_014_RESULT_CONTRACT_UNRESOLVED`
7. `ADMIT_014_RUNTIME_ENFORCEMENT_WITHOUT_AGGREGATION_UNRESOLVED`

All are blocking and open; no resolution transition is claimed. The inherited
coverage issue still affects `ADMIT_014|ADMIT_015`.

The audit, rule identity, explicit-context model selection, authorization-field
identity, stage-global scope, forbidden candidate/batch/download-result
sourcing, current no-download/no-network facts, pure-memory possibility,
readiness for the next contract-design step, current Exact13 runtime, and
training feature-semantics prerequisite are true. Trusted producer/provenance,
exact successor routing, vocabulary/transition/precedence/signature/result
readiness, adapter, registry, Exact14 runtime, provider/download readiness,
combined verdict, aggregation, and training readiness are false.

## Safety and publication

Canonical evidence building and checking require CPython 3.10.4. Noncanonical
Python may be used only for evaluator-semantic smoke; artifact building,
checking, and frozen AST evidence require an explicit contract refresh.

Source reads pin the repository root and every parent directory, open leaves
relative to pinned descriptors with `O_NOFOLLOW`, and verify full
device/inode/mode/size/mtime/ctime identity before and after each read.
Current-index stage, mode, and blob identity are verified before any output is
read. Checker output traversal similarly pins the output parent and root,
holds all Exact6 leaf descriptors until a single post-traversal inventory and
identity verification, and rejects non-regular, symlinked, or oversized
evidence. Real race tests cover extra or missing leaves both during traversal
and immediately before the unified post-traversal check, as well as
existing-set root and same-byte leaf replacement.

Lifecycle validation applies `git check-ignore --no-index` to every Exact10
path, so an ignored tracked post-commit candidate is rejected just like an
ignored untracked pre-commit candidate. Return codes other than the exact
not-ignored result also fail closed. These checks do not change the production
audit module or any Exact6 business-evidence byte.

Materialization builds all bytes before mutation, uses a pinned parent,
Exact6 allowlisted staging root, exclusive leaves, leaf/staging/parent fsync,
and `RENAME_NOREPLACE`. It verifies the destination directory-entry/FD
binding immediately after publication, after parent fsync, and through a full
pinned Exact6 post-read. Existing byte-identical output is an inode-preserving
no-op. A mismatch or GPFS `EINVAL` fails closed, with no `os.replace`
fallback and no owned staging residue.

No evaluator, `Admit014EvaluationResult`, adapter, handler, registry entry,
provider, network/download/raw operation, model/checkpoint/dataloader change,
combined verdict, aggregation, training, backward pass, optimizer step, or
parameter update is implemented or executed.

Step12D remains a smoke-legality check, not a final training-feature contract.
The historical unknown-atom feature policy and
`feature_semantics_known=false` state require an explicit feature-semantics
audit before training.

Recommended next step:
`design_covapie_admit_014_download_authorization_contract_v1`.
