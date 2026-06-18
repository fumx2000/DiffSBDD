# KRAS_G12C_6OIM Initial Inspection

This is an initial inspection note for preparing `KRAS_G12C_6OIM` as the next
small real covalent workflow sample. No ligand SDF has been extracted yet, and
`manifest_real_small.csv` has not been updated.

## Structure

- PDB ID: `6OIM`
- Protein PDB path:
  `data/raw/covalent_small/proteins/KRAS_G12C_6OIM.pdb`
- Target context: KRAS G12C covalent complex candidate

## Reactive Residue Check

Chain `A` residue `12` exists and is `CYS`.

Residue atoms from `print_pdb_residue_atoms.py`:

- `N`: `-3.6520 -5.0930 2.8750`
- `CA`: `-4.5140 -4.0220 2.3980`
- `C`: `-5.3300 -3.4490 3.5570`
- `O`: `-5.9260 -4.1970 4.3370`
- `CB`: `-5.4320 -4.5450 1.2880`
- `SG`: `-6.3440 -3.2600 0.4090`

CYS12 `SG` is present in chain `A`.

## HETATM Ligand-Like Residues

Detected non-water HETATM residues:

- `MG A:301`, atom count `1`
- `GDP A:302`, atom count `28`
- `MOV A:303`, atom count `41`

`MOV A:303` is the covalent ligand candidate for the next SDF extraction step.

## LINK / CONECT Evidence

The PDB contains a covalent LINK involving CYS12:

```text
LINK         SG  CYS A  12                 C25 MOV A 303     1555   1555  1.81
```

This indicates:

- Protein reactive atom candidate: `CYS A 12 SG`
- Ligand residue candidate: `MOV A 303`
- PDB ligand reactive atom candidate: `C25`
- LINK distance: `1.81`

The raw PDB also contains numeric CONECT records consistent with this link:

```text
CONECT   93 1374
CONECT 1374   93 1373
```

Here atom serial `93` is `CYS A 12 SG`, and atom serial `1374` is
`MOV A 303 C25`.

## Suitability for Next Step

`KRAS_G12C_6OIM` is suitable for the next workflow step:

1. Extract `MOV A 303` to SDF.
2. Generate the PDB atom name to SDF atom index mapping.
3. Confirm where `MOV C25` maps in the extracted SDF.
4. Download/check reference CCD files for `MOV` before assigning final
   scaffold/linker/warhead roles.

Do not fill `manifest_real_small.csv` yet. The sample still needs ligand SDF
extraction, atom mapping, annotation template generation, reference graph
checks, and draft role curation.
