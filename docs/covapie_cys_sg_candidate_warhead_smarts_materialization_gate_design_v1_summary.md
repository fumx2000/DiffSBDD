# CovaPIE Cys-SG candidate warhead SMARTS materialization gate design V1

## Scope

This metadata-only gate defines what a future candidate ligand-side warhead
SMARTS must prove. It creates no SMARTS, performs no SMARTS match, makes no
human-review decision, and approves no reaction family, rule, gold label, or
training label.

The immutable formal base is
`77e2d11135da4b3f07ee64411ad3c4634ba60693`. All 15 inputs are read from that
commit and verified against frozen SHA256 values.

## Evidence boundary

`canonical_local_graph_rule_json` is a radius-1 reaction-center local
signature. It is evidence for a lower bound on a future warhead atom set. It is
not complete-warhead atom-set authority, boundary authority, an approved
SMARTS, a reaction SMARTS, or a role annotation.

In particular, its local atom order cannot be serialized into SMARTS; a
semantic name cannot be reverse-engineered into SMARTS; one representative
ligand cannot define a class query; and an exact-one local-rule assignment does
not prove an exact-one complete-warhead query match.

## Current readiness

The seven candidate classes cover all 11 samples and nine unique parent
components. Every class has:

- a verified radius-1 local reaction-center rule;
- SHA-verified pre-reaction parent heavy-atom and heavy-bond authority;
- a verified known reactive observed-to-parent atom mapping;
- rule-JSON/CSV-consistent reaction-delta semantics and pre-reaction
  parent-graph leaving-group evidence rebuilt for every supporting sample;
- enough input authority to materialize candidate pre-reaction warhead
  atom-set and attachment-boundary proposals.

Six classes have an exact zero-leaving-group contract. The remaining class,
`COVAPIE_CYS_SG_WARHEAD_TYPE_CLASS_EE022EB419200D14`, reconstructs one
fluorine leaving group for ZYA from reactive parent atom `CM` through the
pre-reaction `CM`–`F1` single bond. This result is derived from the immutable
rule, atom, bond, assignment, and observed-to-parent authorities rather than
being assigned as a readiness constant.

No class currently has:

- complete-warhead atom-set authority;
- exact-one attachment-boundary authority;
- a deterministic atom-map policy;
- frozen bond-order, formal-charge, aromaticity, hydrogen-count, and chirality
  query semantics;
- class-wide exact-one complete-warhead match validation.

Therefore proposal materialization is ready for 7/7 classes, while candidate
SMARTS materialization and SMARTS human review remain ready for 0/7 classes.

## Future candidate contract

A future V1 candidate must be a single connected ligand-side query component,
contain no reaction arrow or protein/CYS-SG component, use the pre-reaction
parent heavy-atom graph, include the known reactive atom and the reviewed
complete warhead atom set, retain pre-reaction leaving-group atoms, and expose
exactly one warhead-to-nonwarhead attachment boundary. Its V1 allowed match
count is one, validation covers every supporting parent graph with RDKit
2022.03.2, and its initial state is only `candidate_not_reviewed`.

The inherited warhead-rule schema remains the exact 12-field
`WARHEAD_RULE_FIELDS` contract. The next proposal schema is frozen as 22 fields
with the closed statuses `not_materialized`, `auto_exact_candidate`,
`ambiguous_candidate`, and `quarantined`; this step materializes zero proposal
records.

Every proposal atom identifier uses the `parent_ccd_atom_id` namespace.
Reaction-center bond identifiers use
`canonical_parent_ccd_endpoint_pair_and_normalized_order_v1`, encoded as
`atom_id_low|atom_id_high|normalized_bond_order` with UTF-8 lexical endpoint
ordering. The Exact22 field-type contract distinguishes exact strings, one
exact non-boolean integer class index, and five exact `list[str]` fields.
Atom/bond lists are sorted and unique and must resolve against parent
authority.

The future `proposal_record_sha256` is lower-case SHA256 over UTF-8 canonical
JSON with sorted keys, compact separators, and ASCII escaping. It includes the
other Exact21 fields and excludes only `proposal_record_sha256` itself.

## Fail-closed state

The design transaction has two phases. Phase A verifies immutable predecessor,
review-package, identity, parent-graph, mapping, and local-rule evidence. Phase
B verifies the Exact16 contract registry, Current7 readiness matrix, Exact49
class-by-gap matrix, no-SMARTS boundary, and closed downstream state. If either
phase fails, the contract, readiness, and gap tables are all header-only.

The Exact32 typed-mutation matrix demonstrates this atomic behavior, including
explicit reaction-delta/rule mismatch and parent leaving-group evidence
mismatch cases. Role
proposal generation, all five canonical mask tasks (including
`scaffold_only` / `B3`), tensorization, model integration, and training remain
closed. Integrated covalent model modules remain 0/5.

Tests and the independent checker both exercise the shared hermetic Git
lifecycle harness across all four states: pre-commit, detached candidate,
formal-main committed but unpushed, and formal-main pushed. These states use
temporary local repositories and a temporary bare remote; cleanup is verified
without changing the real main branch or remote.

## Next steps

The independent manual action remains:
`perform_real_human_review_of_materialized_family_topology_and_sample_assignment_packages`.

The recommended engineering successor is:
`materialize_covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_v1`.
