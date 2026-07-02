# Real Covalent Minimal mmCIF Parser Design Gate v0 Summary

Step 12V is a minimal mmCIF parser design gate.

This step does not network, does not download, does not read raw files, does not decompress, and does not parse mmCIF.
It only defines the next parser smoke contract.

## Step 12W Scope
The next step must actually run parser smoke and is limited to these 3 pilot raw files:
- 6DI9.cif.gz
- 5F2E.cif.gz
- 6OIM.cif.gz

Step 12W may use in-memory gzip read and text scan only.
Step 12W forbids Bio.PDB/MMCIFParser/PDBParser/gemmi/RDKit.
Step 12W forbids raw/decompressed mmCIF/PDB/SDF/MOL2 outputs and may only write CSV/JSON/MD summary artifacts.

## Minimal Fields
The parser smoke may extract only minimal metadata fields: entry id/title/entity count/atom_site count/chem_comp ids/struct_conn count/covalent connection candidate count.

## Boundaries
Step 12W does not do geometry, UniProt/CD-HIT, training, or enriched sample_index writing.
This is the last parser-before-smoke design gate; the next step must actually run parser smoke.

## Decision
- parser_contract_row_count: 29
- parser_input_contract_row_count: 3
- parser_policy_row_count: 10
- parser_expected_extraction_contract_row_count: 16
- ready_for_minimal_mmcif_parser_smoke: true
- recommended_next_step: real_covalent_minimal_mmcif_parser_smoke
