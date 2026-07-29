# CovaPIE Current11 pre-reaction warhead atom-set and attachment-boundary proposals v1

## Scope

This metadata-only successor materializes reviewable candidate proposals from
the frozen pre-reaction parent graph, the known reactive parent atom, the
radius-1 local reaction-center lower bound, and leaving-group evidence. It does
not generate SMARTS, human decisions, approved warhead atom sets, role
annotations, minimal seeds, canonical masks, tensors, model changes, or
training activity.

`auto_exact_candidate` means only that the graph contract has one candidate.
It never means human-approved or gold. Ambiguous and quarantined records keep
all primary proposal fields empty.

## Deterministic graph method and completeness

For every sample, the implementation validates the SHA-attested connected
parent graph and independently reconstructs the reactive atom, all radius-1
neighbors, reactive-neighbor bonds, and required pre-reaction leaving-group
atoms. Neighbor comparison is a multiset over element, formal charge,
normalized bond order, and retained/leaving disposition; list order is never
used as matching authority.

Every parent-graph bridge is enumerated in canonical bond-ID order. Removing a
bridge partitions the graph, and the connected side containing the reactive
atom is admitted only when it is a proper subset, has exactly one external
bond, contains the complete local reaction center, contains every required
leaving-group atom, and remains connected.

This bridge enumeration is complete for the stated contract: if a connected
warhead-side atom set has exactly one bond to its nonwarhead complement,
removing that unique boundary bond disconnects the parent graph. Therefore the
boundary bond must be a bridge. Enumerating every bridge enumerates every
possible connected exact-one-boundary atom set; this is not heuristic
sampling. No smallest, largest, or first candidate is selected.

## Actual Current11 result

| Sample | PDB | Component | Reactive parent atom | Local center atom count | Leaving-group atom count | Parent bridges | Admitted candidates | Proposal status |
|---|---|---|---|---:|---:|---:|---:|---|
| CYS_SG_SAMPLE_INDEX_000001 | 6BV6 | JUG | CAG | 3 | 0 | 3 | 3 | ambiguous_candidate |
| CYS_SG_SAMPLE_INDEX_000002 | 6BV8 | JUG | CAG | 3 | 0 | 3 | 3 | ambiguous_candidate |
| CYS_SG_SAMPLE_INDEX_000003 | 6BV5 | JUG | CAG | 3 | 0 | 3 | 3 | ambiguous_candidate |
| CYS_SG_SAMPLE_INDEX_000004 | 1AEC | E64 | C2 | 3 | 0 | 24 | 22 | ambiguous_candidate |
| CYS_SG_SAMPLE_INDEX_000005 | 1AIM | ZYA | CM | 3 | 1 | 18 | 16 | ambiguous_candidate |
| CYS_SG_SAMPLE_INDEX_000006 | 1AU3 | PCM | C22 | 4 | 0 | 28 | 27 | ambiguous_candidate |
| CYS_SG_SAMPLE_INDEX_000007 | 1AU4 | INP | C17 | 4 | 0 | 27 | 26 | ambiguous_candidate |
| CYS_SG_SAMPLE_INDEX_000008 | 1AYU | INA | C21 | 4 | 0 | 31 | 28 | ambiguous_candidate |
| CYS_SG_SAMPLE_INDEX_000009 | 1AYV | IN6 | C21 | 4 | 0 | 28 | 25 | ambiguous_candidate |
| CYS_SG_SAMPLE_INDEX_000010 | 1AYW | IN3 | C21 | 4 | 0 | 24 | 21 | ambiguous_candidate |
| CYS_SG_SAMPLE_INDEX_000011 | 1B02 | UFP | C6 | 3 | 0 | 11 | 11 | ambiguous_candidate |

Actual totals are 11 proposal records, 200 bridge-enumeration records, and 185
admitted candidates. Status counts are 0 auto-exact, 11 ambiguous, 0
quarantined, and 0 not-materialized. The three JUG samples have identical
topology enumeration, while retaining sample-specific proposal identities.

All 11 proposal records are ready for real human proposal review because the
candidate alternatives and ambiguity state are fully materialized and hashed.
Complete warhead atom-set authority and exact-one attachment-boundary authority
remain unavailable until that review occurs. Candidate SMARTS materialization,
SMARTS review, roles, masks, model integration, and training therefore remain
closed.

## Transaction and next step

Phase-A or global authority failure makes proposal, bridge-enumeration, and
readiness outputs header-only. Zero bridges, zero admitted candidates, and
multiple admitted candidates are normal per-sample outcomes rather than global
transaction failures. The Exact36 typed mutation matrix verifies fail-closed
behavior.

## Actual and hermetic release lifecycle evidence

The actual repository lifecycle and the shared hermetic Exact4 matrix are
different evidence. The actual lifecycle is derived fail-closed from the
current HEAD, successor parent/message/path/mode identity, branch state, and
the relationship between HEAD and `origin/main`. It is exactly one of
`pre_commit`, `detached_candidate_post_commit`,
`formal_main_post_commit_unpushed`, or `formal_main_post_push`.

The hermetic harness separately proves that all four states are reachable with
the exact successor contract and that its temporary worktrees, refs, and
repositories are cleaned. The checker reports these independently as
`current_lifecycle` and `hermetic_lifecycle`; it never presents the hermetic
four-state list as the current repository state. Consequently, targeted
validation remains runnable at the real pre-commit, formal-main committed but
unpushed, and formal-main pushed stages, as well as in a detached candidate.

Recommended manual action:
`perform_real_human_review_of_materialized_family_topology_and_sample_assignment_packages`.

Recommended engineering next step:
`materialize_covapie_current11_warhead_atom_set_and_attachment_boundary_review_packages_v1`.
