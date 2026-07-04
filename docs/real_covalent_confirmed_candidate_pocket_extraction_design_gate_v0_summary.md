# Real Covalent Confirmed Candidate Pocket Extraction Design Gate v0 Summary

Step 13K is a pocket extraction design gate.
This step read the Step 13J protein full atom table, ligand full atom table, and endpoint recovery audit.
This step inherited 4600 protein atom rows, 104 ligand atom rows, and 3 endpoint audit rows.
This step did not read raw `.cif.gz`, did not use gzip_open_used, did not decompress raw files, and did not parse mmCIF.
This step did not calculate distances or a protein-ligand distance matrix.
This step did not write pocket_atom_table or ligand_topology_table.
This step did not write sample_index, enriched_sample_index, final_dataset, split assignments, leakage matrix, or model input.
This step did not use Bio.PDB/MMCIFParser/PDBParser/gemmi/RDKit.
This step did not train and did not save checkpoint, model, or tensor dump.
Feature semantics audit is still required before formal training.
The next step is pocket extraction smoke, not training.
