# CovaPIE bulk-download orchestration fail-closed call-site contract v1

## Executable-evidence hardening v2

The design classifier and its business control flow remain byte-identical at
SHA256
`96c93e727cbd8f127311969788b08c39f34735f1c5423952e24399d2d3e04c35`.
This revision changes only the checker, tests, summary, truth and invariant
evidence, and manifest.

Every truth case now carries independent expected and actually observed values
for all Decision Exact15 fields. A row passes only when the result has the
exact decision class, every field has the exact expected type and value,
candidate diagnostic tuples match in type, order, and content, and both the
download-action and call-site-I/O fields are false. Expected projections use
an independent frozen dataclass and named reason constants; they are not
derived from classifier output or the design `_decision()` helper.

The `cross_phase_precedence` group executes nine mixed-conflict probes covering
cardinality over type, stage invariant over all later phases, scope over I/O
and permission, I/O over permission and candidate outcomes, action permission
over candidate outcomes, invalid over blocked, blocked over
permission-not-granted, all-passed with permission false, and a legal
success-shaped orchestration error.

Candidate first, middle, last, multiple, and mixed diagnostics are checked in
full. All committed Exact8 error codes are checked against the complete
fail-closed projection. The invariant matrix is no longer static
`verified/verified` evidence: every row links to a unique executable truth
case and records the mutation or positive probe plus complete expected and
observed projections.

No authorized or download branch is reachable in this revision.

## Frozen call-site design

This design step freezes how a future bulk-download call site consumes exactly
one `StageAdmissionOrchestrationResult` or
`StageAdmissionOrchestrationError`. It does not implement the future runtime
`evaluate_bulk_download_stage_orchestration_call_site`, accept a download
callable, or perform provider, network, filesystem, raw-data, model, or
training work.

The public pure classifier is
`classify_bulk_download_stage_orchestration_call_site_contract_design`.
Both source parameters are required keyword-only parameters. The returned
frozen Exact15 decision uses the outcomes `authorized`, `blocked`, and
`invalid`, but the current V1 classifier can never return `authorized`.
Every decision records `download_action_invoked=false` and
`call_site_io_used=false`.

The classifier validates exact source class identity, storage and dataclass
field order, exact field types, reconstruction, committed scope and rule
membership, call cardinalities, Unified and Combined result invariants,
stage-global identity reuse, retained-vector identity, and the canonical
rejected-vector branch. Only `download_execution_permission` is accepted.
Malformed input, orchestration errors, wrong scope, orchestration I/O, and an
unauthorized `action_permission_granted=true` transition all fail closed.
Candidate `invalid` precedes candidate `blocked`; candidate `blocked` precedes
permission-not-granted.

The committed current path is one download-scope candidate with ADMIT_001–013
passed where applicable, ADMIT_014 blocked, and
`action_permission_granted=false`. Its call-site projection is candidate 0
blocked with `BULK_DOWNLOAD_CANDIDATE_VERDICT_BLOCKED`.

The issue inventory is inherited byte-for-byte. Effective-open issues remain
`COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED` and
`REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT`. PRE continuity remains 45 total,
43 complete, two incomplete and implementation-blocking, no transition, with
`PRE_038` and `PRE_042` remaining.

This step does not establish download or training readiness. Step12D remains
only a smoke legality check, `UNKNOWN_ATOM_FEATURE_POLICY` remains unresolved,
and `feature_semantics_known=False`. A feature-semantics audit is required
before formal training.

Recommended next step:
`implement_covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1`.
That step must still remain a pure decision runtime and must not perform a real
download.
