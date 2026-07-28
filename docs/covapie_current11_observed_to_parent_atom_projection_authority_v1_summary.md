# CovaPIE Current11 observed-to-parent atom projection authority v1

## Scope

This Exact10 successor projects Current11 post-covalent retained-heavy ligand
atoms onto the committed Exact9 CCD parent graph authority. It materializes
case-sensitive observed atom-name mappings, source full-atom row indices,
sample-local retained-heavy indices, sample-expanded parent bonds, observed
projected graphs, and deterministic observed graph SHA256 values.

It does not label reaction families, approve warhead SMARTS, assign
scaffold/linker/warhead roles, propose minimal seeds, materialize masks or
tensors, change model code, load checkpoints, train, fine-tune, or update
parameters.

## Formal BASE and source authority

The formal BASE is
`34ff4dbb94a5caf4f8b393152e9694e5a8d7c2ce`, with tree
`e0276fd276cea27ddb617f5fa28dfd71ad35c9ba`. Every checked source is read
through `git show BASE:<path>` and verified against its frozen SHA256 before it
is interpreted.

The formal observed row authority is a lossless BASE-tracked join:

1. `covapie_heavy_atom_disposition_and_index_projection_matrix.csv` supplies
   the exact Current11 sample identity, SHA-attested source table path,
   source full-atom row index, retained-heavy disposition, and sample-local
   retained-heavy index.
2. The 11 referenced BASE-tracked per-sample `ligand_atom_table.csv` files
   supply the row-level `atom_name`, `type_symbol`, and covalent reactive-atom
   flag.
3. The join is exact on sample identity, source path/SHA, and zero-based source
   row index. No SMILES order, RDKit index, canonical rank, element/degree
   heuristic, coordinate matching, fuzzy alias, case folding, CCD loop-order
   alignment, or hand-authored 323-row mapping is used.

The source inventory contains all 21 checked BASE candidates. It distinguishes
the 11 full-atom row-level atom-name sources from count-, index-, parent-graph-,
and supporting-only evidence.

## Execution lifecycle boundary

The production boundary accepts exactly four lifecycle classifications:
`pre_commit`, `detached_candidate_post_commit`,
`formal_main_post_commit_unpushed`, and `formal_main_post_push`.

At pre-commit, `HEAD` is the formal BASE. After commit, `HEAD` must be the
BASE's exact single-parent successor with the frozen subject, an empty body,
exactly the ten Exact10 paths, and mode `100644` for every path. Detached
candidate, formal-main unpushed, and formal-main pushed states are classified
explicitly. A merge, wrong parent or subject, nonempty body, missing or extra
path, wrong mode, non-main formal branch, or second-generation descendant fails
closed.

Both pre-commit and the exact successor continue to read all 21 predecessor
sources exclusively with `git show BASE:<path>` and verify their frozen SHA256
values. No lifecycle skip environment variable or production bypass switch is
used; the nested-test environment marker prevents test recursion only.

## Materialized result

- Current11 samples: 11
- Unique parent components: 9
- Sample-expanded parent-heavy atoms: 324
- Observed retained-heavy atoms: 323
- Case-sensitive exact atom-name mappings: 323/323
- Exact element matches: 323/323
- Unique source full-row indices: 323/323 within sample
- Unique continuous retained-heavy local indices: 323/323 within sample
- Exact-one reactive ligand atom: 11/11
- Sample-expanded parent bonds: 337
- Projected retained-observed bonds: 336
- Verified leaving-group endpoint-missing bonds: 1
- Connected deterministic observed graphs: 11/11

The sole parent/observed atom delta is
`CYS_SG_SAMPLE_INDEX_000005` / `ZYA` / `F1`. BASE evidence identifies it as
`covalent_leaving_group_loss`, names `F1` as the leaving group, verifies the
parent leaving-group bond, and the Exact9 parent bond authority contains the
F1 bond. The endpoint partner is read from that authority rather than
hard-coded. There are no unexpected observed atoms and no unexplained missing
parent atoms.

Observed graph SHA256 serializes sorted atom triples
`(observed_atom_name, parent-matched element, formal charge)` and sorted
undirected bond triples
`(min_atom_name, max_atom_name, normalized_bond_order)`. Reversing atom or bond
input order leaves the SHA unchanged.

## Transaction and failure closure

Phase A verifies the formal BASE, all frozen sources, exact Current11 identity,
all 323 retained source rows, per-sample uniqueness and continuity, and all 11
reactive rows. Phase B verifies 323 exact parent mappings, element agreement,
the sole ZYA/F1 delta, all 337 parent-bond projections, graph validity, and
graph SHA determinism.

Nonempty mapping and bond tables are emitted only when both phases pass. Any
failure emits header-only mapping and bond tables, blocked readiness, and a
manifest reason. Partial sample materialization is not allowed.

The failure matrix contains 24 explicit typed dataclass mutations. Every
mutation differs from the clean baseline, has a unique canonical signature,
hits its expected reason, fails closed, and keeps role, mask, model, and
training readiness false.

## Readiness boundary

Parent component graphs, exact observed atom projection, observed projected
graphs, parent graph validity, observed graph validity, pre-reaction
connectivity, and pre-reaction bond order are available for 11/11 samples.

Reaction-family labels, approved warhead rules, role proposals, minimal-seed
proposals, and human gold review remain 0/11. Planned/integrated covalent model
modules remain 5/0. Mask materialization, tensorization, model integration, and
training readiness remain false.

The evidence-driven next step is
`design_covapie_cys_sg_reaction_family_and_warhead_rule_registry_v1`.
