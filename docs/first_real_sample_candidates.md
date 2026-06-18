# First Real Covalent Sample Candidates

This document tracks the first 3-5 candidate real covalent complexes for manual
curation. These are candidates only. A sample should not be added to
`manifest_real_small.csv` until both the protein PDB and ligand SDF have been
curated and atom annotations have been checked.

| sample_id | PDB ID | target | reactive residue | protein reactive atom | expected warhead / ligand class | source link or note | why suitable for first batch | curation risks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `KRAS_G12C_5F2E` | 5F2E | KRAS G12C | CYS12 | SG | KRAS G12C covalent inhibitor, electrophilic acrylamide-like class expected | RCSB PDB entry 5F2E; candidate from KRAS G12C covalent inhibitor structures | Small, well-known covalent target; CYS12 is the intended reactive residue; useful first single-sample workflow target | Ligand SDF must be exported separately; confirm chain, ligand identity, covalent atom pair, and SDF atom order before manifest entry |
| `KRAS_G12C_6OIM` | 6OIM | KRAS G12C | CYS12 | SG | KRAS G12C covalent inhibitor, electrophilic warhead expected | RCSB PDB entry 6OIM; candidate KRAS G12C covalent complex | Same reactive residue family as 5F2E, useful for checking consistency across KRAS examples | Ligand naming and SDF atom order must be verified; avoid mixing PDB ligand atom order with exported SDF atom order |
| `BTK_C481_6DI9` | 6DI9 | BTK | CYS481 | SG | BTK covalent inhibitor, acrylamide-like kinase inhibitor class expected | RCSB PDB entry 6DI9; candidate BTK covalent complex | Adds a kinase target and a different CYS covalent system to the first batch | Confirm biological chain and residue numbering; exported ligand SDF atom order must drive all ligand atom annotations |

## Ligand SDF Requirement

For these candidates, the protein PDB can be downloaded from RCSB one entry at a
time. The ligand SDF should be prepared separately from RCSB ligand export,
CovPDB/CovBinder, or a manual export workflow.

The SDF atom order is the only atom order that should be used for:

- `ligand_reactive_atom_id`
- `scaffold_atoms`
- `linker_atoms`
- `warhead_atoms`

Do not mix PDB ligand atom order with SDF atom order. If the ligand is exported
again, re-run `scripts/print_ligand_atom_indices.py` and re-check all atom
annotations.

## Current 5F2E Status

For `KRAS_G12C_5F2E`, this step downloads only:

```text
data/raw/covalent_small/proteins/KRAS_G12C_5F2E.pdb
```

The ligand SDF is intentionally not generated automatically in this step. The
manifest should remain unchanged until the ligand SDF and atom annotations are
curated manually.
