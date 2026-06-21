# Bond-Order Repair and Pre-Reaction Graph Plan

## Scope

Step 6a is a planning-only step. It does not implement repair scripts, update
manifests, modify ligand SDF files, change model code, train, or fine-tune.

The current small real covalent dataset is a workflow smoke test. The samples
prove that the manifest, processed JSONL builder, QA checks, and four-level mask
logic can run on real PDB-derived covalent complexes. They are not yet final
scientific training samples.

## Current Problem

The current ligand SDF files were extracted from PDB HETATM and CONECT records.
This preserves useful bound-pose 3D coordinates from the experimental complex,
but the chemical graph is incomplete for model training:

- PDB extracted SDF files contain real post-covalent bound-pose coordinates.
- PDB CONECT records do not reliably encode bond order, aromaticity, or double
  bonds.
- CCD ideal SDF files usually provide a more reliable ligand chemical graph,
  including bond order, aromaticity, and double-bond information.
- CCD ideal SDF coordinates are idealized coordinates, not the crystallographic
  bound pose.
- CCD ideal SDF atom order may differ from the extracted ligand SDF atom order.
  It must not be used directly for manifest atom indices.
- Covalent ligands need an additional distinction between the post-covalent
  graph observed in the complex and the pre-reaction ligand graph needed for
  generation or training.

The desired final representation should keep the experimentally aligned 3D
geometry while repairing the ligand graph using a trusted reference source.

## Repair Strategy

The future repair workflow should keep geometry and chemistry as separate
curation objects:

1. Keep the extracted ligand SDF as the bound-pose coordinate source.
2. Load the CCD or ideal SDF as the reference chemical graph source.
3. Build an atom mapping from extracted atom order to reference atom order.
4. Validate the mapping using element identity, graph neighborhood, PDB atom
   names, reactive atom identity, and warhead annotations.
5. Transfer reference bond order, aromaticity, and formal graph information onto
   the extracted atom order.
6. Preserve the extracted 3D coordinates after graph repair.
7. Preserve ligand reactive atom, covalent bond atom pair, scaffold/linker/
   warhead annotation, and mask-compatible atom indices in the extracted atom
   order.
8. Apply warhead-specific logic to derive or annotate the pre-reaction form.
9. Write repaired outputs to new files, never overwriting the original extracted
   ligand SDF.

The repaired output may be a repaired SDF, a JSON ligand graph, or both. The
important invariant is that final manifest atom indices must always refer to the
chosen ligand file or graph used by the processed dataset.

## Atom Mapping Requirements

Atom mapping is the key risk in bond-order repair. A future implementation
should record:

- extracted SDF atom index
- extracted PDB atom name
- reference atom index
- reference atom name if available
- element match
- local neighbor match
- reactive atom match
- mapping confidence
- unresolved or ambiguous atoms

If the extracted and reference graphs cannot be mapped reliably, the sample
should remain non-training-ready. The workflow should not silently guess atom
correspondence.

## Pre-Reaction Graph Curation

For covalent ligands, the post-covalent ligand in the PDB may differ from the
pre-reaction ligand that should be generated. The future workflow should decide
per warhead type how to represent the pre-reaction graph.

Examples of decisions that need explicit curation:

- Whether the protein-ligand covalent bond is absent from the ligand-only
  pre-reaction graph.
- Whether the reactive ligand atom participates in a Michael acceptor,
  acrylamide, acryloyl, chloroacetamide, sulfonyl fluoride, or another warhead.
- Which double bonds or leaving groups should be restored.
- Whether the post-covalent bound geometry is still usable as a coordinate
  target for the pre-reaction ligand graph.
- Whether the sample should be excluded until a high-confidence pre-reaction
  ligand structure is available.

Pre-reaction graph repair should be implemented as an explicit curation stage,
not as a side effect of reading the manifest.

## Proposed Sample State Fields

Future manifests or processed JSONL records should include sample status fields
that make training readiness explicit:

- `geometry_state`: coordinate source and meaning.
- `bond_order_state`: whether bond orders are trusted, repaired, or unreliable.
- `graph_state`: whether the ligand graph is extracted, repaired, or needs
  repair.
- `curation_status`: current curation maturity.
- `training_ready`: whether the sample should be used for training.
- `pre_reaction_graph_ready`: whether a curated pre-reaction graph is available.

Suggested controlled values:

- `geometry_state`: `post_covalent_bound`, `idealized`, `unknown`
- `bond_order_state`: `pdb_conect_unreliable`, `ccd_transferred`,
  `manual_curated`, `unknown`
- `graph_state`: `needs_repair`, `post_covalent_repaired`,
  `pre_reaction_curated`, `excluded`
- `curation_status`: `workflow_smoke_test`, `draft_manual_annotation`,
  `reviewed`, `training_ready`, `excluded`
- `training_ready`: `true` or `false`
- `pre_reaction_graph_ready`: `true` or `false`

## Current Sample Status

The current three samples should be treated as workflow smoke tests:

| sample_id | geometry_state | bond_order_state | graph_state | curation_status | training_ready | pre_reaction_graph_ready |
| --- | --- | --- | --- | --- | --- | --- |
| KRAS_G12C_5F2E | post_covalent_bound | pdb_conect_unreliable | needs_repair | workflow_smoke_test | false | false |
| KRAS_G12C_6OIM | post_covalent_bound | pdb_conect_unreliable | needs_repair | workflow_smoke_test | false | false |
| BTK_C481_6DI9 | post_covalent_bound | pdb_conect_unreliable | needs_repair | workflow_smoke_test | false | false |

These status values should remain conservative until repaired chemical graphs
and pre-reaction ligand graphs are explicitly curated.

## Expected Future Outputs

A future repair step should write new files such as:

- `*_repaired.sdf`: extracted coordinates with repaired bond order in extracted
  atom order.
- `*_pre_reaction.sdf`: curated pre-reaction ligand graph if an SDF
  representation is appropriate.
- `*_graph_repair_report.csv`: atom mapping, transferred bonds, warnings, and
  confidence information.
- `*_pre_reaction_graph.json`: explicit graph representation for downstream
  processing if SDF is insufficient.

The original extracted SDF files should remain immutable provenance artifacts.

## Step 6 Boundaries

Step 6 should be split into small, reviewable stages:

- Step 6a: write this design document only.
- Future steps: implement mapping reports, then repaired graph outputs, then
  pre-reaction graph curation.

Step 6a specifically does not:

- write repair scripts
- modify `manifest_real_small.csv`
- modify existing ligand SDF files
- overwrite extracted coordinates
- alter scaffold/linker/warhead annotations
- modify DiffSBDD model code
- modify `equivariant_diffusion/`
- train or fine-tune any model
