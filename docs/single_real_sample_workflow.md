# Single Real Covalent Sample Workflow

This workflow is for adding one manually curated real covalent complex to the
small real covalent dataset. It does not train or fine-tune any model.

## Steps

1. Choose a real covalent complex from a trusted source such as CovPDB,
   CovBinder, PDB, or a covalent inhibitor paper.
2. Save the protein PDB to:

   ```text
   data/raw/covalent_small/proteins/
   ```

3. Save the ligand SDF to:

   ```text
   data/raw/covalent_small/ligands/
   ```

4. Inspect the ligand SDF atom order:

   ```bash
   /home/fmx_25111030037/bin/micromamba run -r /home/fmx_25111030037/micromamba -n covdiff python scripts/print_ligand_atom_indices.py --ligand_sdf data/raw/covalent_small/ligands/<sample_id>.sdf
   ```

5. Confirm the reactive residue chain, residue id, and residue type in the PDB.
6. Inspect the reactive residue atoms:

   ```bash
   /home/fmx_25111030037/bin/micromamba run -r /home/fmx_25111030037/micromamba -n covdiff python scripts/print_pdb_residue_atoms.py --protein_pdb data/raw/covalent_small/proteins/<sample_id>.pdb --chain <chain> --residue_id <residue_id>
   ```

7. Confirm the protein reactive atom, for example `CYS SG`.
8. Confirm the ligand reactive atom index in the SDF atom order.
9. Annotate `scaffold_atoms`, `linker_atoms`, and `warhead_atoms` using
   zero-based ligand atom indices.
10. Fill one row in:

    ```text
    data/raw/covalent_small/manifests/manifest_real_small.csv
    ```

11. Record source, rationale, and uncertainties in:

    ```text
    data/raw/covalent_small/metadata/curation_log.md
    ```

12. Run the manifest checker:

    ```bash
    /home/fmx_25111030037/bin/micromamba run -r /home/fmx_25111030037/micromamba -n covdiff python scripts/check_manifest_real_small.py --manifest data/raw/covalent_small/manifests/manifest_real_small.csv
    ```

13. Build processed JSONL:

    ```bash
    /home/fmx_25111030037/bin/micromamba run -r /home/fmx_25111030037/micromamba -n covdiff python scripts/build_covalent_real_small.py --manifest data/raw/covalent_small/manifests/manifest_real_small.csv --output data/processed/covalent_real_small.jsonl
    ```

14. Run processed-data QA:

    ```bash
    /home/fmx_25111030037/bin/micromamba run -r /home/fmx_25111030037/micromamba -n covdiff python scripts/check_covalent_real_small.py --input data/processed/covalent_real_small.jsonl
    ```

## Notes

- Do not add pseudo-real smoke-test rows as real data.
- Do not describe `example/3rfm.pdb` or `example/3rfm_B_CFF.sdf` as real
  covalent samples.
- Keep the first real batch small and auditable.
