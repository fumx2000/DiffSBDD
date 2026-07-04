# Real Covalent Confirmed Candidate Coordinate Pair Sanity Gate v1 Altloc Aware Summary

Step 13F-v1 is an altloc-aware coordinate pair sanity gate.
This step read the Step 13E2 altloc-aware corrected endpoint coordinates.
This step did not read raw `.cif.gz`, did not decompress raw files, did not use gzip.open, and did not parse mmCIF.
This step paired 6 corrected endpoint rows into 3 protein-ligand coordinate pairs.
This step calculated 3 corrected protein SG to ligand atom distances.
HR_0002 preserved CYS481 SG altloc B atom_site id 659.
HR_0002 distance now agrees with struct_conn reported distance.
All 3 pairs are within the 1.4-2.2 A covalent sanity range.
All 3 pairs agree with Step 13C struct_conn pdbx_dist_value within 0.05 A.
This step did not use Bio.PDB/MMCIFParser/PDBParser/gemmi/RDKit.
This step did not write sample_index, did not write final dataset, and did not train.
coordinate pair sanity passed, but training_ready=false remains enforced.
The next step is minimal sample record design gate, not direct training.
