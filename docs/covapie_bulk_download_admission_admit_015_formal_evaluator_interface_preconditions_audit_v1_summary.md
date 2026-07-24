# CovaPIE ADMIT_015 formal-evaluator interface preconditions audit v1

This is a metadata-only, fail-closed audit based on committed Git tree
`f54c0efabfb695653c9e55b3a53bda8cf200f353`. It does not implement or
authorize an evaluator, result type, adapter, registry entry, Exact15 runtime,
mandatory training guard, provider action, download, raw-data access, or
training.

The final pre-commit `revised3` hardening keeps every business conclusion and
every Exact45/Exact16/Exact23/Exact20/Exact30 byte stable. It retains the
independent evidence, final-leaf, final-set, row-specific provenance, and JSON
exact-type guarantees from the earlier revisions. It replaces destructive
failure cleanup with whole-directory retention and makes the non-Git
stage-family scan recursively bounded.

## Revised3 non-destructive failure contract

The stage explicitly recognizes the ordinary Linux interface boundary: even
after pinning an owned FD, moving a leaf to a random quarantine name, and
checking its lexical identity, another process can replace that name before
`unlink`. Adding more `stat` calls, a longer random name, or another
compare-then-unlink sequence cannot provide an atomic
“unlink only if this name still identifies this inode” operation.

Production therefore never calls `unlink` or `rmdir` on a failure path. It
does not delete individual staging leaves at all. If publication fails before
the staging directory becomes the destination, production verifies the
staging FD/lexical binding and attempts one parent-relative NOREPLACE rename
of the complete staging directory to an unpredictable retained name. If that
rename cannot be verified or completed, the original staging lexical path is
left in place. The FD is closed and the operation fails with an exception
that identifies the retained path. Foreign, owned, partial, and
identity-uncertain bytes are never deleted.

Only two normal paths are residue-free:

1. A byte-identical destination exists before materialization starts. It is
   returned as an inode-preserving no-op before staging is created.
2. A newly built staging directory is atomically published as the
   destination. The staging name disappears as part of that successful rename
   and no cleanup runs.

Concurrent `EEXIST` is deliberately different from a pre-existing exact
destination. If the initial check saw no destination but publication races
with another creator, the materializer fails closed even when the concurrent
destination is byte-identical. It leaves that destination untouched and
retains its own complete staging directory. GPFS `EINVAL`, destination
mismatch, staging mismatch, and other pre-publication failures use the same
non-destructive retention contract.

The independent manifest parser now requires exact built-in Boolean values
for every formal-interface, readiness, safety, and materialization member.
JSON integers `0` and `1` cannot impersonate `false` and `true`; Boolean
values likewise cannot impersonate count, order, or stage integers. Output
hash values, ID and forbidden-source lists, source items, and canonical-mask
fields also have independently checked exact types.

Lifecycle validation recursively scans `src/covalent_ext`, `scripts`,
`tests`, and `docs` without following symlink directories. A stage-family
token in either a basename or relative path is audited even when every parent
directory has an unrelated name. `data/derived/covalent_small` remains
bounded: only first-level matching stage roots are selected, then those roots
are recursively scanned. Ignored, nonignored, or tracked nested artifacts,
hidden files, stage-family directories, symlinks, forbidden suffixes,
oversized files, seventh Exact6 members, and sibling derived roots are
rejected. The scan never enters `data/raw`. All five business CSV files remain
byte-identical.

## Frozen current identity and state

- Rule: `ADMIT_015` / `current_gate_grants_no_training_permission`
- Evidence/status/reason:
  `current_design_gate` / `training_not_authorized_now` /
  `training_not_authorized`
- Current permission: `false`
- Authorized ADMIT_015 training executions: `0`
- Runtime state: known, not registered, callable not discovered, adapter not
  ready
- Exact14 open runtime coverage: `ADMIT_015`
- Exact30 issue inventory: inherited byte-for-byte with zero transitions

## Candidate responsibility audit

The committed ADMIT_014 chain supplies a structural precedent for an
invocation-local `stage_authorization_context`, an exact built-in Boolean,
no coercion, and a trusted future stage orchestrator. Step14AU-A also commits
the coexistence names `current_stage_download_authorized` and
`current_stage_training_authorized`.

For ADMIT_015, the recommended authority path is therefore
`stage_authorization_context.current_stage_training_authorized`, pending a
separate formal authorization contract. This audit does not freeze that
contract. Candidate record, batch/evaluation/download-result context,
provider result, environment, filesystem, artifact or Git SHA, checkpoint
metadata, training config, CLI flag, model state, and dataloader state are
forbidden authority sources.

The download and training keys are strictly isolated: neither implies the
other, neither may fall back to or alias the other, and they may not be
combined with OR or AND as one permission. Combined-permission semantics
remain undefined.

Responsibility rows 6 and 7 are classified as
`supported_but_admit015_contract_not_frozen`. Exact14 proves only its own
download-key consumption and the current runtime proves ADMIT_015 remains
known but unregistered. Step14AU-A freezes the two coexistence names; it does
not commit the future ADMIT_015 evaluator or authorization contract.

## Open implementation preconditions

The training authorization contract, evaluator signature, result class and
field order, outcome/reason vocabulary, normalized projection, independent
oracle, adapter contract and implementation, registry and Exact15 runtime,
mandatory training enforcement, and cross-rule aggregation remain open.

The historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False` state still requires the explicit
feature-semantics audit before training. Step12D remains a smoke-legality
check, not a final training-feature contract. Training readiness is false.

## Canonical mask boundary

The audit preserves exactly five long-name-first V1 masks:

1. `warhead_only` / `A`
2. `linker_plus_warhead` / `B`
3. `scaffold_plus_warhead` / `B2`
4. `scaffold_only` / `B3`
5. `scaffold_plus_linker_plus_warhead` / `C`

No mask, feature, loss, training data, model, checkpoint, dataloader, or
training code is changed.

## Evidence and next step

The Exact6 derived set contains an ordered precondition inventory,
responsibility matrix, pinned source-boundary audit, safety/training audit,
byte-identical Exact30 issue inventory, and manifest. The source boundary
attests 23 committed sources across Step14AT, Step14AU-A, Exact14, the complete
ADMIT_014 design/implementation lineage, canonical QA, feature-semantics
evidence, and Step12D.

The independent checker freezes the ordered Exact23 path/SHA list without
importing production constants, independently reconstructs all Exact45,
Exact16, Exact23, Exact20, and Exact30 rows, and parses the manifest with
duplicate rejection plus exact top-level and nested key/order/type schemas.
Synchronized CSV/manifest/output-SHA tampering therefore remains rejectable
even if candidate output SHA constants are replaced together.

The only recommended next step is:
`design_covapie_admit_015_training_authorization_contract_v1`.
