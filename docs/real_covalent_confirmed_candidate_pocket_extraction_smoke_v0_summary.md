# Real Covalent Confirmed Candidate Pocket Extraction Smoke v0 Summary

Step 13L is a pocket extraction smoke.
This step read the Step 13K pocket contract and the Step 13J full atom tables.
This step calculated protein atom distances to ligand heavy atoms using the extracted CSV coordinates.
This step wrote pocket_atom_table with 741 protein pocket atom rows.
This step wrote pocket extraction audit with 3 rows.
HR_0002 altloc B atom_site 659 is present in the pocket table.
This step did not read raw `.cif.gz`, did not use gzip_open_used, did not decompress raw files, and did not parse mmCIF.
This step did not run an atom_site text scan and did not use Bio.PDB/MMCIFParser/PDBParser/gemmi/RDKit.
This step did not write ligand_topology_table.
This step did not write sample_index, enriched_sample_index, final_dataset, split assignments, leakage matrix, or model input.
This step did not run forward, loss, backward, optimizer, trainer, checkpoint, model save, or tensor dump.
This step did not train and does not claim training-ready samples.
Feature semantics audit is still required before formal training.
The next step is ligand topology design gate, not training.
