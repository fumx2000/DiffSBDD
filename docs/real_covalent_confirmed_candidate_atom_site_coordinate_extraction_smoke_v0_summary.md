# Real Covalent Confirmed Candidate Atom Site Coordinate Extraction Smoke v0 Summary

Step 13E is an actual confirmed candidate atom_site coordinate extraction smoke.
This step read the Step 13D coordinate extraction contract.
This step actually performed raw `.cif.gz` read for 3 local files.
This step only decompressed raw mmCIF text in memory and did not write decompressed mmCIF.
This step only scanned the `_atom_site` loop.
This step did not use Bio.PDB/MMCIFParser/PDBParser/gemmi/RDKit.

Endpoint coordinates extracted: 6.
matched_endpoint_row_count=6.
unmatched_endpoint_row_count=0.

This step did not calculate endpoint distance, did not run geometry sanity, did not write sample_index, did not write final dataset, and did not train.
The next step is coordinate pair sanity gate, not sample_index and not training.
