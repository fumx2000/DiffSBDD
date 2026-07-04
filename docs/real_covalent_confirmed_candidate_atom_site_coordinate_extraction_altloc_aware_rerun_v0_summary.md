# Real Covalent Confirmed Candidate Atom Site Coordinate Extraction Altloc Aware Rerun v0 Summary

Step 13E2 is an altloc-aware rerun of confirmed candidate atom_site coordinate extraction.
This step was added after Step 13F debug found the HR_0002 altloc mismatch.
This step first cleaned the uncommitted blocked Step 13F untracked files.
This step read the Step 13D contract and Step 13C struct_conn reported distance.
This step actually read 3 raw `.cif.gz` files, decompressed only in memory, and wrote no decompressed mmCIF.
This step only scanned the `_atom_site` loop.
This step did not use Bio.PDB/MMCIFParser/PDBParser/gemmi/RDKit.
This step evaluated endpoint candidate pairs and selected altloc by struct_conn reported distance agreement.
HR_0002 corrected CYS481 SG from altloc A to altloc B.
HR_0002 selected protein atom_site id 659, altloc B, selected pair distance approximately 1.8053 A.
6 endpoint coordinates were written.
3 altloc selection audit rows were written.
This step did not write sample_index, did not write final dataset, and did not train.
The next step is altloc-aware coordinate pair sanity gate, not sample_index and not training.
