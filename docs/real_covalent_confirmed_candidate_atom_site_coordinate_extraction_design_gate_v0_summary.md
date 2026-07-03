# Real Covalent Confirmed Candidate Atom Site Coordinate Extraction Design Gate v0 Summary

Step 13D is a confirmed candidate atom_site coordinate extraction design gate.
This step read the Step 13C confirmed candidate table.

This step did not read raw `.cif.gz`, did not decompress raw files, and did not parse mmCIF.
This step did not use Bio.PDB/MMCIFParser/PDBParser/gemmi/RDKit.
This step did not extract coordinates, did not calculate distance, did not write sample_index, and did not train.

Confirmed candidates used: 3.
Atom endpoint coordinate extraction contract rows written: 6.
Each confirmed candidate has one protein_residue endpoint and one ligand endpoint.
Endpoint role comes from manual review fields, not inference.
The contract records label/auth atom_site lookup keys and required `_atom_site` columns.
Expected raw paths are recorded for the next smoke but not read in this design gate.

coordinate_extraction_ready=true but coordinates_extracted=false and training_ready=false.
The next step is actual atom_site coordinate extraction smoke, not sample_index and not training.
