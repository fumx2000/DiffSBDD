# CovaPIE combined permission semantics contract v1

This design-only stage freezes exactly four phase-scoped admission-layer
permission scopes. It does not implement a production cross-rule aggregator,
a combined candidate verdict, dispatcher call order, runtime short-circuiting,
or training-orchestrator integration.

## Frozen scopes

1. `download_execution_permission` requires, in order, ADMIT_001–009,
   ADMIT_011, and ADMIT_014 (Exact11).
2. `post_download_acceptance_permission` requires, in order, ADMIT_001–009,
   ADMIT_011–014 (Exact13).
3. `pre_final_split_acceptance_permission` requires, in order,
   ADMIT_001–014 (Exact14).
4. `training_execution_admission_permission` requires, in order,
   ADMIT_001–015 (Exact15).

ADMIT_010 is isolated to the pre-final-split and later admission scopes.
ADMIT_012 and ADMIT_013 are unavailable in the pre-download scope.
ADMIT_015 appears only in the training admission scope. ADMIT_014 is required
from the download scope onward.

## Frozen combination semantics

Rule states and combined outcomes both use the exact vocabulary `passed`,
`blocked`, and `invalid`. Collection, schema, membership, or order failure is
`invalid`; otherwise any required `invalid` wins, then any required `blocked`,
and only an all-`passed` vector passes. Thus the deterministic fail-closed
precedence is `invalid > blocked > passed`.

The combination is a monotone conjunction. OR, majority vote, weighting,
fallback, latest-pass behavior, omission-as-pass, extra-as-ignore, and
scope-external substitution are forbidden. ADMIT_014 and ADMIT_015 are each
necessary in the scopes that require them but are never sufficient alone and
cannot override another required rule's `blocked` or `invalid` state.

The immutable simulator is evidence-only and pure in memory. Its result is not
the future production aggregation-result contract. The deterministic truth
matrix contains 163 rows in 17 groups, including every required rule singly
blocked and singly invalid, structural failures, phase-isolation cases,
non-override cases, invalid-over-blocked precedence, and a synthetic pass that
does not mutate permission or execution counts. The safety audit contains 30
passing rows.

## Readiness boundary

This stage resolves only PRE_035. The resulting Exact45 overlay is
complete/supported/incomplete/implementation-blocking = `42/0/3/3`.
PRE_036 (aggregation implementation), PRE_038 (feature semantics), and PRE_042
(real training readiness) remain open.

Exactly one Existing Exact30 issue transitions:
`UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED` becomes
resolved because the Exact4 scope membership, fail-closed precedence,
monotone conjunction, and ADMIT_014/015 non-override semantics are frozen.
Aggregation implementation remains false. The genuinely open issues
`COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED` and
`REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT` remain open.

`current_permission` remains false and
`authorized_admit_015_training_execution_count` remains zero. Passing all
rules in the training admission scope means only that all required
admission-layer permissions are satisfied. It does not establish feature
semantics, checkpoint compatibility, final dataset QA, provider readiness,
or real training readiness.

Step12D remains a smoke legality check, not the final training-feature
contract. A feature-semantics audit is mandatory before training; historical
`UNKNOWN_ATOM_FEATURE_POLICY` and `feature_semantics_known=False` remain
unresolved. The canonical V1 mask set remains Exact5 and includes
`scaffold_only` / `B3`.

Recommended next step:
`design_covapie_combined_candidate_verdict_and_cross_rule_aggregation_contract_v1`.

## Revised1 infrastructure closure

The Revised1 repair changes infrastructure only. Exact4 scope membership,
combined-permission semantics, simulator results, PRE and issue transitions,
and all five CSV byte streams remain unchanged.

The former checker lifecycle used a simplified Git inventory and did not
inherit the committed predecessor's four-root FD-pinned recursive scanner.
The former source readers checked the held leaf but lacked a final lexical
parent/root binding, and the former Exact6 reader lacked a set-level lexical
parent/root binding. Production and checker now independently hold and
reverse-validate the complete no-follow parent chain, bind strict initial and
final `HEAD^{commit}`, and hold all six output leaf FDs through final Exact6
inventory and parent/root checks. The checker lifecycle scans
`src/covalent_ext`, `scripts`, `tests`, and `docs`, enters only matching
current-stage derived roots, rejects generic symlinks before name filtering,
and snapshots the full `git ls-files --stage -z` bytes without `git
write-tree`.

Materialization now authenticates an existing byte-identical root before
treating it as a no-op, keeps the staging FD held, reauthenticates the parent
and staging identities immediately before `RENAME_NOREPLACE`, and binds the
published directory identity before an independent final Exact6 read. A
pre-publication failure reports a retained staging path only when its frozen,
held-FD, and lexical identities still agree; no destructive cleanup or
overwrite fallback is introduced.

This repair does not implement an aggregator or combined candidate verdict,
does not integrate an orchestrator, and does not resolve feature semantics.
`ready_for_training` remains false.

## Revised2 final lifecycle closure

Revised2 leaves Production and all five CSV byte streams unchanged and
preserves every Revised1 reader, Exact6, materializer, and recursive-scanner
repair. It changes checker orchestration only: a complete recursive lifecycle
runs before candidate validation and a second complete recursive lifecycle
runs after every candidate import, source snapshot, artifact build, and
comparison. The prefinal simplified snapshot remains an additional
HEAD/index/status/identity comparison, but it is no longer used as a
substitute for the final four-root scanner. The final complete lifecycle is
the checker's last Git or filesystem validation; only an in-memory report is
constructed afterward.

The checker now also exposes an internal exact observed-artifact verifier.
Synchronized Precedence, Membership, or Truth CSV plus canonical Manifest and
derived-SHA tampering is passed to that verifier and must raise, rather than
being demonstrated only with an inequality assertion.

This closure still does not implement an aggregator or combined candidate
verdict, does not integrate an orchestrator, and does not resolve feature
semantics. `ready_for_training` remains false.

## Revised3 generator and Manifest unification

Revised2's final lifecycle ordering and both complete recursive lifecycle
runs remain unchanged. Revised2 initially kept Production byte-identical and
therefore added its lifecycle declaration through a checker-owned in-memory
Manifest overlay. That temporary compatibility mechanism left the Production
artifact generator unable to reproduce the formal on-disk Manifest directly.

Revised3 moves the deterministic Revised2 closure metadata into Production's
canonical Manifest generator. The checker now has one local expected Exact6:
there is no `include_revised2` branch, second Production expected, or
checker-owned overlay. Production output, checker-local expected, the formal
disk Exact6, and a newly materialized Exact6 are required to be byte-for-byte
equal. Existing formal materialization and the formal run entry are
inode-preserving no-ops.

All five CSV byte streams and all combined-permission business semantics
remain unchanged. This revision still does not implement an aggregator or
combined candidate verdict, does not integrate an orchestrator, and does not
resolve feature semantics. `ready_for_training` remains false.
