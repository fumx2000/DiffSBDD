# CovaPIE action-permission bridge in-memory integration smoke V1

This increment connects the committed canonical single-candidate fixture to
the actual stage orchestrator, the actual bulk-download call-site decision
runtime, and the actual action-permission bridge runtime. The public
no-argument API returns a frozen report containing exactly two observations.

The current fixture is used without changing its authorization context. Its
actual chain produces blocked `ADMIT_014`, a blocked combined candidate
verdict, `BULK_DOWNLOAD_CANDIDATE_VERDICT_BLOCKED` at the call site, and
`ACTION_PERMISSION_BRIDGE_ADMIT_014_NOT_PASSED` at the bridge.

The future observation creates a new authorization dictionary from the same
committed fixture and changes only
`current_stage_download_authorized=True`. The original fixture remains
unchanged. Its actual chain produces passed `ADMIT_014`, a passed combined
candidate verdict, `BULK_DOWNLOAD_ACTION_PERMISSION_NOT_GRANTED` at the call
site, and `ACTION_PERMISSION_BRIDGE_TRANSITION_ELIGIBLE` at the bridge.

The smoke stops at `transition_eligible=true`. It does not modify a stage
result, construct an authorized call-site decision, grant action permission,
accept a download callable, execute a permission transition, invoke a
download, or perform bridge, provider, network, filesystem-business, raw-data,
model, or training I/O.

The independent checker executes both actual chains itself and independently
constructs their expected Exact19 values. The resulting evidence contains 38
rows (`2 × 19`), and every row verifies both exact value and exact type.
Fixture provenance contains exactly the `current_blocked` and
`future_eligible` sources. Runtime identity evidence covers the actual
orchestrator, actual call-site runtime, actual bridge runtime, dispatcher,
registry, every registered handler, and aggregator without recording object
representations or memory addresses.

Three public reports, their serialized bytes, three Exact19 matrices, and
consecutive complete evidence builds are deterministic. Success evidence uses
no monkeypatch, injection, registry replacement, forged result, design
classifier, private bridge helper, fallback implementation, permission
transition, or action executor.

The smoke report remains closed:

- `permission_transition_attempted=false`
- `permission_transition_completed=false`
- `transition_eligible_count=1`
- `action_permission_granted_count=0`
- `download_action_count=0`
- `bridge_io_count=0`
- `ready_for_download=false`
- `ready_for_training=false`

The canonical V1 mask contract remains exactly:

1. `warhead_only / A`
2. `linker_plus_warhead / B`
3. `scaffold_plus_warhead / B2`
4. `scaffold_only / B3`
5. `scaffold_plus_linker_plus_warhead / C`

The inherited issue inventory remains byte-identical. The effective-open
issues remain `COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED` and
`REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT`; this increment resolves neither
and adds no issue.

Step12D was a smoke legality check, not a final training-feature contract.
`UNKNOWN_ATOM_FEATURE_POLICY` remains unresolved,
`feature_semantics_known=False`, and a feature-semantics audit remains
mandatory before formal training.

The recommended next step is
`review_covapie_post_admission_control_plane_completion_and_select_next_training_preparation_blocker_v1`.
That review must select between
`COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED` and
`REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT`; it must not add another
permission layer.
