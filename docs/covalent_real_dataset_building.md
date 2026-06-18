# Small Real Covalent Dataset Building

This document defines the first real-data preprocessing path for the covalent
extension. The first version is intentionally small and manual:

```text
raw protein PDB + raw ligand SDF + manual manifest
-> processed covalent JSONL
-> QA checks
-> downstream covalent mask/inpainting workflows
```

The goal is not to download or clean a full covalent-docking database yet. The
goal is to make a stable, inspectable path for a handful of curated examples.

## Why Manual Manifest First

Covalent complexes require annotations that are not reliably recoverable from
structure files alone:

- Which protein residue is reactive.
- Which protein atom is reactive, for example `CYS SG`.
- Which ligand atom forms or would form the covalent bond.
- Which ligand atoms are scaffold, linker, and warhead.
- Which warhead class should be assigned.

Those fields are high-impact labels. A small manual manifest makes them explicit
and easy to audit before any larger semi-automatic pipeline is attempted.

## Required Manifest Columns

Each row in the raw manifest must include:

| Column | Description |
| --- | --- |
| `sample_id` | Stable sample identifier. |
| `protein_pdb_path` | Path to the protein PDB file. |
| `ligand_sdf_path` | Path to the ligand SDF file. |
| `reactive_residue_chain` | Protein chain containing the reactive residue. |
| `reactive_residue_id` | Residue number for the reactive residue. |
| `reactive_residue_type` | Residue type, for example `CYS`. |
| `reactive_atom_name` | Protein atom name, for example `SG`. |
| `ligand_reactive_atom_id` | Zero-based ligand atom index. |
| `warhead_type` | Warhead label. |
| `scaffold_atoms` | Comma- or space-separated zero-based ligand atom indices. |
| `linker_atoms` | Comma- or space-separated zero-based ligand atom indices. |
| `warhead_atoms` | Comma- or space-separated zero-based ligand atom indices. |

## Processed JSONL Fields

The processed file follows `docs/covalent_data_schema.md`. Each line is one JSON
object with:

- `sample_id`
- `protein_pocket`
- `pre_reaction_ligand_graph`
- `post_covalent_ligand_coords`
- `reactive_residue_type`
- `reactive_residue_id`
- `reactive_atom_name`
- `reactive_atom_coord`
- `warhead_type`
- `ligand_reactive_atom_id`
- `covalent_bond_atom_pair`
- `scaffold_atoms`
- `linker_atoms`
- `warhead_atoms`

## Field Sources

Fields read from protein PDB:

- `protein_pocket`
- `reactive_residue_type`
- `reactive_residue_id`
- `reactive_atom_name`
- `reactive_atom_coord`

Fields read from ligand SDF:

- `pre_reaction_ligand_graph.atom_symbols`
- `pre_reaction_ligand_graph.atom_names`
- `pre_reaction_ligand_graph.formal_charges`
- `pre_reaction_ligand_graph.bonds`
- `post_covalent_ligand_coords`

Fields from manual or semi-automatic annotation:

- `sample_id`
- `ligand_reactive_atom_id`
- `warhead_type`
- `scaffold_atoms`
- `linker_atoms`
- `warhead_atoms`
- `covalent_bond_atom_pair`, derived from the annotated protein and ligand
  reactive atoms.

## QA Checks

The QA script should check:

- The processed JSONL has at least one sample.
- Ligand atom count is positive.
- Scaffold, linker, and warhead atom sets are all non-empty.
- Scaffold, linker, and warhead atom sets are disjoint.
- All atom indices are inside the ligand atom range.
- `ligand_reactive_atom_id` is inside `warhead_atoms`.
- `reactive_atom_coord` exists and has three numeric values.
- `covalent_bond_atom_pair` exists.
- A/B/B2/C masks can be generated.

## Current Smoke Test

`data/raw/covalent_small/manifest_example.csv` uses:

- `example/3rfm.pdb`
- `example/3rfm_B_CFF.sdf`

This is a pseudo-real smoke test for the file-processing path. It is not a
validated real covalent complex and should not be used as scientific training
data.
