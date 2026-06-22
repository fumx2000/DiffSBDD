# Pre-Reaction Graph Design Plan

This is a design plan only.

- It does not create pre-reaction SDF files.
- It does not modify raw ligand SDF files.
- It does not modify repaired trial SDF files.
- It does not modify manifest files.
- It does not mark samples as training-ready.
- It does not change model code.

## Why Pre-Reaction Graphs Are Needed

The current small real covalent samples are useful workflow smoke tests, but
they still mix several different scientific objects:

- The post-covalent bound ligand contains covalent-adduct chemistry from the
  protein-ligand complex.
- Model training needs a consistent ligand graph representation, not an
  accidental graph implied by PDB `CONECT` records.
- A pre-reaction ligand graph is needed to represent the free ligand before
  covalent bond formation.
- The post-covalent 3D pose can still be useful as bound-pose geometry
  supervision, especially for pocket-conditioned generation and inpainting.
- The pre-reaction graph should be generated non-destructively as derived data,
  never by overwriting the extracted ligand files.

This means chemistry and geometry should stay explicitly separated until a QA
gate proves that a sample is ready for downstream use.

## Three Data Objects

### `raw_extracted_post_covalent_sdf`

The raw extracted SDF is the provenance-preserving coordinate source. It is
built from PDB HETATM/CONECT records and keeps the bound-pose ligand atom order
used by the current manifest annotations.

Rules:

- Do not overwrite it.
- Treat its coordinates as the current post-covalent bound-pose geometry.
- Treat its bond order as unreliable unless separately validated.
- Use its atom order for current scaffold/linker/warhead annotations.

### `warhead_only_repaired_trial_sdf`

The warhead-only repaired trial SDF is the current derived curation artifact
from Step 7. It only transfers bond order for accepted warhead-internal bonds
that passed dry-run and QA checks.

Rules:

- It lives under `data/derived/`.
- It is non-destructive.
- It only repairs accepted warhead-internal bond order.
- It does not cross unresolved linker/local boundaries.
- It is not training-ready.
- It is not a pre-reaction ligand graph.

### `future_pre_reaction_graph_sdf`

The future pre-reaction graph SDF is a possible derived object for training
candidate data. It should represent the ligand graph before covalent bond
formation, while retaining explicit provenance back to the coordinate source
and transform rule.

Rules:

- It must be written only under `data/derived/`.
- It must pass a dedicated pre-reaction QA gate before being considered for any
  training manifest.
- It must record source file paths, hashes, coordinates, transform rules, and
  QA status.
- It must not be used as training-ready data merely because it exists.

## Safety Principles

Future pre-reaction graph work must follow these invariants:

- Do not modify raw SDF files.
- Do not modify repaired trial SDF files.
- Write outputs only under `data/derived/`.
- Do not change atom coordinates, unless a later explicit design introduces a
  separate 2D or graph-only output.
- Do not perform bond transfer across unresolved boundaries.
- Do not automatically mark `training_ready=true`.
- Record `source_sdf_path`.
- Record `source_hash`.
- Record `coordinate_hash`.
- Record `warhead_rule`.
- Record `bond_break_rule`.
- Record `charge_rule`.
- Record `qa_status`.

## Strategy A: Graph-Only Pre-Reaction Representation

Strategy A generates an explicit molecular graph and labels without claiming
that the ligand has a realistic free-ligand 3D pose.

Properties:

- Generates graph objects rather than a chemically asserted 3D SDF.
- Keeps post-covalent bound coordinates as geometry context.
- Stores atom symbols, bonds, bond orders, formal charges, reactive atom id,
  and scaffold/linker/warhead roles.
- Avoids implying that bound-pose coordinates are the free ligand conformation.
- Is better suited for early training experiments and label engineering.
- Can be represented as JSON, NPZ, or a graph section inside processed sample
  metadata.

This is the safer first scientific representation because it separates the
chemical target graph from uncertain free-ligand geometry.

## Strategy B: Pre-Reaction-Like 3D SDF

Strategy B creates a derived SDF whose atom coordinates remain close to the
post-covalent bound pose, but whose graph is transformed toward the pre-reaction
ligand state.

Properties:

- Removes or omits the protein-ligand covalent bond from the ligand graph.
- Restores warhead electrophile bond order when a rule supports it.
- May need formal charge, valence, and protonation corrections.
- Keeps coordinates near the bound pose, so it is not a true free-ligand
  conformer.
- Requires stricter QA than graph-only output.
- Must not be treated as training-ready until QA and curation status explicitly
  allow it.

This strategy may become useful after transform rules are reviewed, but it is
riskier than graph-only output because SDF sanitization can silently expose
valence/protonation assumptions.

## Warhead and Reaction Template Placeholders

No transform templates are implemented in this step. Future rules should begin
as reviewed data records, not hidden script logic.

### Acrylamide / Michael Acceptor-Like Warhead

Fields needed:

- ligand reactive atom
- beta carbon / electrophilic carbon assignment
- carbonyl carbon and oxygen assignment
- alkene bond to restore
- protein residue and reactive atom
- covalent bond to remove or ignore
- atoms requiring valence and charge checks
- protonation assumptions
- confidence level and manual review flag

QA needed:

- restored double bond is within accepted warhead atoms
- carbonyl bond order is correct
- reactive atom valence is valid
- no unresolved boundary atom is modified

### Covalent KRAS G12C Inhibitor-Like Warhead

Fields needed:

- `CYS` residue identity
- protein `SG` reactive atom
- ligand reactive atom mapped from PDB atom name
- accepted warhead atom set
- acryloyl/acrylamide-like bond order restoration rule
- post-covalent bound geometry source
- unresolved linker/local boundary atoms

QA needed:

- ligand reactive atom remains in `warhead_atoms`
- restored warhead bonds are internal to accepted warhead atoms
- no linker/local boundary bond is transferred without manual review
- output remains non-training-ready until pre-reaction graph QA passes

### Covalent BTK C481 Inhibitor-Like Warhead

Fields needed:

- `CYS` residue identity
- protein `SG` reactive atom, including altloc notes when present
- ligand reactive atom mapped from PDB atom name
- accepted acrylamide/Michael acceptor warhead atoms
- unresolved linker/local boundary atoms
- charge and valence checks around the warhead carbonyl and alkene

QA needed:

- altloc provenance remains documented
- ligand reactive atom is accepted and retained
- warhead-only transfer does not cross into unresolved linker atoms
- any future pre-reaction output records the specific rule and confidence

## Future Transform Rule Table

A future transform rule template should contain at least these fields:

| field | purpose |
| --- | --- |
| `warhead_type` | Warhead or reaction class label. |
| `residue_name` | Reactive residue name, for example `CYS`. |
| `residue_atom` | Reactive protein atom, for example `SG`. |
| `ligand_reactive_atom` | Ligand atom index in the selected ligand graph atom order. |
| `covalent_bond_to_remove` | Protein-ligand covalent bond descriptor or ligand-side adduct bond if represented. |
| `bond_order_to_restore` | Ligand-internal bond order changes needed for the pre-reaction graph. |
| `atoms_requiring_charge_check` | Atom indices needing formal charge review. |
| `atoms_requiring_valence_check` | Atom indices needing valence review. |
| `protonation_note` | Curator note for protonation assumptions. |
| `geometry_note` | Statement of whether coordinates are bound-pose, graph-only, or otherwise derived. |
| `confidence_level` | Controlled value such as `draft`, `reviewed`, or `high_confidence`. |
| `requires_manual_review` | Boolean gate preventing automatic use before review. |

The table should be sample-specific until repeated patterns are sufficiently
validated to become reusable templates.

## Future Pre-Reaction QA Report

A future pre-reaction QA report should include at least these fields:

| field | purpose |
| --- | --- |
| `sample_id` | Sample identifier. |
| `source_sdf_path` | Raw or derived source graph/coordinate file. |
| `output_pre_reaction_sdf_path` | Derived pre-reaction output path, if an SDF is produced. |
| `warhead_type` | Warhead rule label used for transformation. |
| `covalent_bond_removed` | Whether the specified covalent bond was removed or excluded. |
| `restored_bond_order` | Bond order restoration summary. |
| `valence_check_passed` | Whether valence checks passed. |
| `charge_check_passed` | Whether charge checks passed. |
| `sanitization_passed` | Whether RDKit or equivalent sanitization passed, if applicable. |
| `coordinate_hash_same` | Whether coordinates stayed unchanged. |
| `source_hash_same` | Whether the source file stayed unchanged. |
| `unresolved_boundary_touched` | Whether any unresolved boundary atom was touched. |
| `training_ready_candidate` | Candidate flag only; not final training status. |
| `qa_status` | `passed` or `failed`. |
| `qa_error` | Error or warning details. |

`training_ready_candidate=true` must not automatically imply
`training_ready=true`. A separate dataset-level gate is still required.

## Current Sample Status

| sample_id | derived_trial_safe | training_ready | pre_reaction_graph_ready | recommended next action |
| --- | --- | --- | --- | --- |
| `BTK_C481_6DI9` | true | false | false | design transform rules before generating any pre-reaction SDF |
| `KRAS_G12C_5F2E` | true | false | false | design transform rules before generating any pre-reaction SDF |
| `KRAS_G12C_6OIM` | true | false | false | design transform rules before generating any pre-reaction SDF |

The Step 7 repaired trial SDFs are safe derived curation artifacts, but they
are not pre-reaction graphs and must not be added to a training manifest.

## Recommended Next Steps

1. Step 8b: create a pre-reaction transform rule template CSV. It may remain
   empty or contain draft rows, but it should not generate SDF files.
2. Step 8c: generate manual review drafts for the three current samples.
3. Step 8d: implement a dry-run transform checker that reports proposed graph
   changes without writing pre-reaction SDF files.
4. Keep all samples out of training until a pre-reaction QA gate passes.

No training, fine-tuning, manifest promotion, or model-code modification should
occur before those gates are explicit and reviewable.
