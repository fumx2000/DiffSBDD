# BTK_C481_6DI9 Initial Inspection

This is an initial inspection note for preparing `BTK_C481_6DI9` as a small
real covalent workflow sample. No ligand SDF has been extracted yet, and
`manifest_real_small.csv` has not been updated.

## Structure

- PDB ID: `6DI9`
- Protein PDB path:
  `data/raw/covalent_small/proteins/BTK_C481_6DI9.pdb`
- Target context: BTK C481 covalent inhibitor complex candidate

## Reactive Residue Check

Chain `A` residue `481` exists and is `CYS`.

Residue atoms from `print_pdb_residue_atoms.py`:

- `N`: `-20.7630 10.8580 2.1190`
- `CA`: `-20.5230 12.1110 1.3970`
- `C`: `-20.2280 13.2610 2.3530`
- `O`: `-20.7670 13.4210 3.4430`
- `CB`: `-21.6210 12.5040 0.4180`
- `SG`: `-23.0970 13.0730 1.1790`

CYS481 `SG` is present in chain `A`. The raw PDB contains alternate `SG`
positions:

```text
ATOM    658  SG ACYS A 481     -23.097  13.073   1.179  0.50 10.10           S
ATOM    659  SG BCYS A 481     -22.309  13.806   0.067  0.50 11.56           S
```

## HETATM Ligand-Like Residues

Detected non-water HETATM residues:

- `GJJ A:701`, atom count `33`
- `DMS A:702`, atom count `4`

`GJJ A:701` is the covalent ligand candidate for the next SDF extraction step.
`DMS A:702` is a solvent/additive-like HETATM residue and is not the primary
covalent ligand candidate.

## LINK / CONECT Evidence

The PDB contains covalent LINK records involving CYS481:

```text
LINK         SG ACYS A 481                 C33 GJJ A 701     1555   1555  1.87
LINK         SG BCYS A 481                 C33 GJJ A 701     1555   1555  1.81
```

This indicates:

- Protein reactive atom candidate: `CYS A 481 SG`
- Ligand residue candidate: `GJJ A 701`
- PDB ligand reactive atom candidate: `C33`
- LINK distance: `1.87` for altloc `A`, `1.81` for altloc `B`

The raw PDB also contains numeric CONECT records consistent with these links:

```text
CONECT  658 2071
CONECT  659 2071
CONECT 2071  658  659 2070
```

Here atom serial `658` is `CYS A 481 SG` altloc `A`, atom serial `659` is
`CYS A 481 SG` altloc `B`, and atom serial `2071` is `GJJ A 701 C33`.

## Suitability for Next Step

`BTK_C481_6DI9` is suitable for the next workflow step:

1. Extract `GJJ A 701` to SDF.
2. Generate the PDB atom name to SDF atom index mapping.
3. Confirm where `GJJ C33` maps in the extracted SDF.
4. Download/check reference CCD files for `GJJ` before assigning final
   scaffold/linker/warhead roles.

Do not fill `manifest_real_small.csv` yet. The sample still needs ligand SDF
extraction, atom mapping, annotation template generation, reference graph
checks, and draft role curation.
