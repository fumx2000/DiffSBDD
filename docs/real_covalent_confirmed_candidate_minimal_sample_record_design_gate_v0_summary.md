# Real Covalent Confirmed Candidate Minimal Sample Record Design Gate v0 Summary

Step 13G is a minimal sample record design gate.
This step read the Step 13F-v1 pair sanity table.
This step converts 3 confirmed covalent candidates that passed altloc-aware pair sanity into a future minimal sample record contract.
This step did not read raw `.cif.gz`, did not decompress raw files, did not use gzip.open, and did not parse mmCIF.
This step did not recompute geometry distance.
This step did not use Bio.PDB/MMCIFParser/PDBParser/gemmi/RDKit.
This step did not write sample_index, did not write final dataset, and did not train.
This step wrote a schema contract and a candidate contract.
The candidate contract keeps training_ready=false.
Future steps still require full protein atom extraction, full ligand atom extraction, pocket definition, ligand bond topology, feature semantics audit, and split/leakage check.
HR_0002 altloc B atom_site 659 was preserved.
The next step is minimal sample record write smoke, not direct training.
