# Real Covalent Confirmed Candidate Full Atom Extraction Design Gate v0 Summary

Step 13I is a confirmed candidate full atom extraction design gate.
This step read the Step 13H minimal sample records and field audit.
This step read the Step 13F-v1 coordinate pair sanity table.
This step read the Step 13E2 altloc-aware endpoint coordinates and altloc selection audit as provenance.
This step wrote a full atom extraction schema contract with 81 fields.
This step wrote a full atom extraction candidate contract for 3 confirmed candidates.
This step did not read raw `.cif.gz`, did not decompress raw files, did not use gzip.open, and did not parse mmCIF.
This step did not run actual full protein atom extraction or full ligand atom extraction.
This step did not write protein full atom tables, ligand full atom tables, pocket atom tables, or ligand topology tables.
This step did not use Bio.PDB/MMCIFParser/PDBParser/gemmi/RDKit.
This step did not write sample_index, did not write enriched sample_index, did not write final dataset, did not materialize model input, and did not train.
The candidate contract preserves HR_0002 altloc B atom_site 659.
The next step is full atom extraction smoke, not direct training.
