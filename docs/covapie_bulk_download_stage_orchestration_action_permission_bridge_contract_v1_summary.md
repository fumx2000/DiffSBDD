# CovaPIE bulk-download orchestration action-permission bridge contract v1

This stage freezes a deterministic, pure in-memory, fail-closed classifier for
the eligibility of a future action-permission state transition. It does not
implement the future runtime
`evaluate_bulk_download_stage_orchestration_action_permission_bridge`, grant
permission, invoke download, or perform I/O.

The public design API accepts exactly one exact
`StageAdmissionOrchestrationResult` and the exact shared call-site decision
that corresponds to it. It validates the StageResult Exact12 deep contract,
the call-site decision Exact15 deep contract, download scope, zero
orchestration I/O, the pre-transition permission state, source lineage,
candidate diagnostics, and ADMIT_014 authority semantics. The frozen Exact19
decision outcomes are `eligible`, `blocked`, and `invalid`, with the 13
reasons frozen in the public evidence.

Source lineage is exact: all 14 call-site projection fields must equal the
projection independently derived from the StageResult. The former
`authorized / ""` exception has been removed, so a structurally valid
authorized decision paired with an all-passed, permission-false StageResult
is `invalid / ACTION_PERMISSION_BRIDGE_SOURCE_LINEAGE_MISMATCH`. The
`ACTION_PERMISSION_BRIDGE_CALL_SITE_DECISION_NOT_PERMISSION_PENDING` reason
remains reserved in the Exact13 vocabulary but is currently unreachable.
The design implements its own StageResult/Candidate deep validation and calls
no private helper from the predecessor call-site contract.

The committed canonical authorization-false fixture produces
`ADMIT_014=blocked` and bridge reason
`ACTION_PERMISSION_BRIDGE_ADMIT_014_NOT_PASSED`. A new in-memory authorization
context with only `current_stage_download_authorized=True` produces an actual
all-passed orchestration result and an actual permission-pending call-site
decision. That pair reaches `transition_eligible=true`, while
`action_permission_granted=false`, `download_action_invoked=false`, and
`bridge_io_used=false` remain mandatory.

The executable evidence contains 50 truth rows in 7 groups, 23
source-lineage/invariant rows, 19 public-contract rows, 23 safety rows, and a
byte-identical 30-row inherited issue inventory. Every truth row compares all
19 expected and observed fields with exact types, storage order, tuple-element
types, and zero-action invariants. Every invariant projection is a byte-equal
complete Exact19 canonical JSON object. Effective-open issues remain
exactly `COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED` and
`REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT`; no issue or PRE transition is
introduced.

The canonical five-mask contract remains
`warhead_only/A`, `linker_plus_warhead/B`,
`scaffold_plus_warhead/B2`, `scaffold_only/B3`, and
`scaffold_plus_linker_plus_warhead/C`.

Step12D remains only a smoke legality check, not a final training-feature
contract. `UNKNOWN_ATOM_FEATURE_POLICY` remains unresolved,
`feature_semantics_known=False`, and a feature-semantics audit is required
before any formal training.

The recommended next step is
`implement_covapie_bulk_download_stage_orchestration_action_permission_bridge_v1`.
That step may implement only the pure bridge decision runtime and still may
not execute a real download.
