# CovaPIE Cys-SG reaction-family and warhead-rule registry design v1

## Scope

This Exact10 design successor freezes a CYS/SG-only reaction-family registry,
an exact local-parent-graph warhead-rule registry, and exact-one Current11
candidate assignments. It also defines the candidate warhead-type vocabulary
and the downstream interfaces for later role, minimal-seed, and mask work.

This step does not claim a reaction mechanism, approve SMARTS, materialize a
formal reaction-family label, approve a warhead rule, assign ligand roles,
propose a minimal seed, materialize any of the five canonical masks, create a
tensor, modify a dataloader or model, add a head or loss, access a checkpoint,
train, fine-tune, or update parameters.

## Formal BASE and evidence boundary

The formal BASE is
`68c5ca5cf1ce5b20be5db9ce0b37e10830c09288`, with parent
`34ff4dbb94a5caf4f8b393152e9694e5a8d7c2ce` and tree
`971c5c6360854ae705056c99dda04e96e07fd779`. All 21 predecessor sources are
read with `git show BASE:<path>` and checked against frozen SHA256 values before
interpretation.

The source inventory contains the predecessor production contract, its four
mapping/bond/readiness/manifest authorities, two Exact9 parent-graph tables,
the reaction-delta evidence, canonical atom-pair validation, the Current11
final index, and 11 per-sample ligand atom tables. It records each source path,
BASE SHA256, row count, Current11 coverage, fields actually used, and authority
class.

## Reaction-center result

- Current11 coverage: 11/11 samples and 9 unique ligand components.
- Target condition: CYS SG in 11/11.
- Exact-one reactive ligand atom: 11/11; every center element is carbon.
- Component parent-graph and observed-graph SHA agreement: 11/11.
- Formed bond design condition: ligand reactive atom to CYS SG, single.
- The only parent/observed atom loss is ZYA/F1. BASE evidence classifies it as
  `covalent_leaving_group_loss`, names F1 as the leaving group, and verifies
  the missing parent endpoint. The other ten samples use
  `intact_parent_atom_inventory_match`.

No SMILES atom order, RDKit index, canonical rank, coordinate/distance guess,
component name as warhead type, or hand-authored eleven-label table is used.

## Canonical local signatures and selected radius

For radius 0, 1, and 2, each sample has a canonical provenance signature that
contains the reactive parent CCD atom ID, element and charge; stable local atom
and bond records; retained/leaving-group disposition; the CYS SG target
condition; and reaction delta. Canonical JSON uses sorted keys and stable atom
and bond ordering. Reversing input rows does not change the result.

The provenance signatures preserve CCD atom IDs for traceability. A separate
canonical rule projection removes PDB and component identity while retaining
the exact local graph attributes needed for matching. This prevents component
names from becoming auxiliary warhead labels.

| Radius | Unique provenance signatures | Unique rule projections |
|---:|---:|---:|
| 0 | 7 | 2 |
| 1 | 9 | 7 |
| 2 | 9 | 7 |

Radius 0 omits direct bond-order and leaving-group context. Radius 1 is the
minimal complete first shell and yields exact-one candidate assignments for
all 11 samples. Radius 2 adds distal evidence but no Current11 rule-projection
group, so the selected formal radius is 1. Repeated JUG samples have identical
signatures. Two radius-1 rules each span two different components, showing
that grouping is not a component-ID lookup.

## Registries and candidate assignments

The design contains seven reaction families and seven
`canonical_local_graph_exact_match_v1` warhead rules. Their long semantic names
describe CYS-SG single-bond formation, center charge/element, exact first-shell
bond/element/disposition terms, and a signature digest. IDs and groupings are
derived from canonical evidence signatures; neither component ID nor PDB ID is
an input.

All families use
`topology_defined_mechanism_not_claimed`. The topology is not called Michael
addition, SN2, ring opening, acyl substitution, or any other specific
mechanism. All rules have an empty `approved_warhead_smarts`,
`SMARTS_status=not_materialized_in_design_stage`,
`human_gold_review_completed=false`, and `approved=false`.

The design matrix has exactly one row per Current11 sample. Candidate
reaction-family and warhead-rule assignment is exact-one for 11/11, with zero
absent and zero ambiguous assignments. These are design candidates, not formal
labels or approved rules:

- `reaction_family_label_available=false`
- `approved_warhead_rule_available=false`
- `human_gold_review_completed=false`
- role proposal, minimal-seed proposal, mask, tensor, model integration, and
  training readiness all remain false.

## Auxiliary-label and model boundary

The seven candidate warhead types define a candidate auxiliary-label
vocabulary and Current11 sample-to-candidate-class mapping. No output head,
logits, cross-entropy loss, class weights, dataloader field, or label tensor is
created. The manifest records:

- `warhead_type_auxiliary_label_contract_designed=true`
- `warhead_type_model_head_integrated=false`
- `warhead_type_loss_integrated=false`
- planned/integrated covalent model modules: 5/0
- `ready_for_training=false`

## Fail-closed transaction and lifecycle

Phase A validates all BASE sources, Current11 identity, CYS SG target evidence,
reactive atoms, and graph SHAs. Phase B validates all three-radius signatures,
minimal radius, family/rule grouping, and exact-one assignments. Unless both
phases pass, the family registry, rule registry, and Current11 design matrix
are all header-only; partial sample materialization is forbidden.

The failure matrix contains 25 unique exact typed dataclass mutations covering
the requested source, target, reactive-atom, graph, determinism, ID,
assignment, rule-consistency, mechanism, SMARTS, transaction, and execution
boundaries. Every case hits its expected reason, fails closed, and keeps model,
loss, mask, and training readiness false.

Production, tests, and the independent checker support exactly
`pre_commit`, `detached_candidate_post_commit`,
`formal_main_post_commit_unpushed`, and `formal_main_post_push`. An exact
successor must have BASE as its sole parent, the frozen subject, an empty body,
the exact ten paths, and ten `100644` modes. The shared hermetic lifecycle
harness verifies all four states.

## Independent assignment-identity hardening

The independent checker does not stop at testing whether assigned IDs happen
to exist in a registry. For each Current11 sample it now independently
reconstructs the radius-1 rule JSON and digest, resolves that digest to exactly
one canonical rule-registry row, and requires the assigned rule ID and
candidate warhead semantic name to match that row exactly.

From the independently reconstructed rule JSON, the checker also rebuilds the
formal family signature and digest, verifies the rule-to-family link, and
requires the design-matrix family ID and semantic name to match the resulting
family-registry row. It independently recomputes per-rule and per-family
sample counts, unique-component counts, family rule counts, and the
corresponding manifest count maps.

In-memory negative tests demonstrate fail-closed rejection of assignment-ID
swaps, semantic-name corruption, rule and family JSON/SHA corruption,
rule-to-family link corruption, registry count corruption, an absent rule, and
an ambiguous duplicate rule digest. These checks do not change any design
result, readiness value, or recommended next step.

## Recommended next step

Because Current11 candidate family/rule assignment is exact-one for 11/11, the
evidence-driven next step is
`materialize_covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1`.
That future step must preserve the design-versus-human-approval distinction and
must not infer model or training readiness.
