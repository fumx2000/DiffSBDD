# CovaPIE Ligand Role and Minimal Seed Annotation Contract Design V1

## Outcome and boundary

This metadata-only step freezes an Exact3 per-heavy-atom role contract
(`scaffold`, `linker`, `warhead`), a scaffold exit-vector minimal-seed
contract, ambiguity quarantine, current11 input-readiness auditing, and a
future human gold-review interface.

The outcome is `designed_contract_with_input_authority_gaps`. No current11
role or minimal-seed atom sets are generated. No mask, schema, dataloader,
model, forward, or loss code is changed. No raw data, NPZ, LMDB, archive, or
checkpoint is read. No RDKit current11 segmentation, image/structure output,
tensor materialization, training, backward pass, or optimizer step occurs.

## Exact3 roles and preserved Exact5 masks

The role vocabulary is exactly `scaffold`, `linker`, and `warhead`. The three
sets must be pairwise disjoint, exhaustive over retained ligand heavy atoms,
hydrogen-free, and individually nonempty. `scaffold_core` is proposal
metadata. `minimal_seed` is a scaffold-subset context override, not a fourth
role.

The existing Exact5 masks remain unchanged. In particular, B3 targets
`scaffold` with `linker+warhead` context. C targets the whole Exact3 ligand,
while the validated minimal seed is retained as context override. No sixth
mask is admitted.

## Canonical proposal order

The frozen order is: known ligand reactive atom; approved reaction-family
rule; exact warhead proposal; Murcko scaffold-core proposal; BRICS supporting
evidence; connectivity-derived linker proposal; scaffold remainder;
exit-vector seed proposal; partition gate; ambiguity quarantine; current11
human gold review.

Distance to Cys alone and model predictions are never V1 label authority.
Murcko and BRICS are proposal/supporting evidence, never direct final labels.

## Warhead and scaffold contracts

An approved warhead rule carries a stable family/version, residue scope,
reactive residue atom, mapped SMARTS, reactive/warhead/attachment map numbers,
expected pre-reaction bond orders, allowed charge pattern, allowed match
count, and priority. A match must use pre-reaction topology, include the known
ligand reactive atom, yield one nonempty deduplicated atom set, and expose one
attachment boundary. Unknown families and competing distinct sets are
quarantined.

Scaffold-core proposal priority is curated authority, Murcko proposal,
BRICS-supported rigid-core proposal, then a deterministic ringless fallback.
Ringless and incomparable alternatives require review. Input atom order is not
a permitted tie-break.

## Linker, scaffold remainder, and direct attachment

After removing accepted warhead and scaffold-core atoms, a unique residual
component touching both sides is the linker candidate. A component touching
only the core joins the scaffold role. A warhead-only-side component requires
reaction-family explanation. Disconnected residual components and multiple
bridge paths are blocked.

The final scaffold role is the retained-heavy remainder after warhead and
linker assignment, and it must contain the accepted scaffold core. V1 requires
nonempty scaffold, linker, and warhead. Direct scaffold-warhead attachment
without a linker is quarantined as
`direct_attachment_no_linker_v1_quarantine`.

## Minimal seed and review

The seed is the scaffold-side exit-vector context: primary boundary atom
`s0`, a stable deterministic scaffold neighbor `s1`, and optional plane anchor
`s2`. It is a connected scaffold subset of size two or three, contains `s0`,
does not overlap linker or warhead, and is independent of input atom numbering.
Non-unique boundaries or canonical-rank ties are blocked.

Annotation status is a closed vocabulary:
`proposal_only`, `auto_exact`, `gold_curated`, and `ambiguous_blocked`.
Current11 training authority requires `gold_curated`; `auto_exact` is only a
future proposal status. The future review package records atom identity,
reactive atom, rule identity, role/core proposals, both boundary bonds, seed
anchors, partition result, ambiguity reasons, and reviewer decision.

## Exact types and status hardening

Every `AnnotationScenario` boolean uses exact `bool`, while every boundary,
bridge, match, and seed-size count uses an exact nonnegative `int`. Python
booleans and numeric-equal floats cannot impersonate count value `1`.
`annotation_status` is an exact string, and `canonical_masks` is an exact
tuple of exact strings. Type validation runs before business comparisons.

`gold_curated` always means human review is complete. An annotation can be
training eligible only when it is `gold_curated` and human review is complete.
`proposal_only`, `auto_exact`, and `ambiguous_blocked` are never training
eligible; `auto_exact` remains proposal-level authority.

A ringless fallback cannot be marked `auto_exact`, even when the fallback is
deterministic and its review flag is complete. Human review may promote it to
`gold_curated`, revise it, or quarantine it.

The public partition, graph-component, and minimal-seed helpers accept only
stable ordered `tuple`, `list`, or `range` atom-index inputs containing unique,
nonnegative exact integers. They reject booleans, floats, duplicate indices,
unordered or single-pass containers, and malformed graph edges.

The failure matrix contains Exact42 distinct state mutations. Each mutation
has a unique signature and explicit expected reasons that are checked against
recomputed scenario observations.

## Current11 authority audit

Committed BASE evidence verifies retained-heavy projection and exact ligand
and residue reactive-atom mappings for 11/11 samples. CCD SMILES, graph hashes,
atom inventories, and Murcko scaffold evidence are useful supporting evidence.
They do not freeze an atom-indexed pre-reaction connectivity/bond-order table
mapped into the retained-heavy index space. Historical topology-restoration
policy evidence covers a separate three-candidate design and explicitly wrote
no topology table.

No current11 reaction-family labels or approved warhead SMARTS rule registry
are committed. Therefore all 11 rows remain false for role proposal
generation, minimal-seed proposal generation, and human gold review.

The next step is
`resolve_covapie_role_annotation_input_authority_gaps_v1`, not proposal
generation or training. The planned/integrated covalent module count remains
5/0, and existing condition/task-mask and geometry/auxiliary-label blockers
remain open.
