# Real Covalent Confirmed Candidate Full Atom Extraction Smoke v0 Summary

Step 13J is a minimal full atom extraction smoke for 3 confirmed covalent candidates.
This step read the Step 13I candidate contract.
This step read exactly the 3 local raw `.cif.gz` files referenced by the contract.
This step used standard-library gzip text streaming and a custom `_atom_site` text scan.
This step wrote a protein full atom table with 4600 rows.
This step wrote a ligand full atom table with 104 rows.
This step wrote 3 endpoint recovery audit rows, all passing.
HR_0002 preserved protein atom_site 659 with altloc B.
This step did not write decompressed mmCIF/PDB/SDF/MOL2 files.
This step did not use Bio.PDB/MMCIFParser/PDBParser/gemmi/RDKit.
This step did not define pockets and did not extract ligand topology.
This step did not write sample_index, enriched sample_index, final dataset, split assignments, leakage matrix, or model input.
This step did not run forward, loss, backward, optimizer, trainer, checkpoint, model save, or tensor dump.
This step is not training preparation completion and does not claim training-ready samples.
Feature semantics audit is still required before any training.
The next step is pocket or topology design gate, not training.
