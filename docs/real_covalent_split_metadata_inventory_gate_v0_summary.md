# Real Covalent Split Metadata Inventory Gate v0 Summary

Step 12N is a split metadata inventory gate, not enrichment, not split implementation, not training.
Step 12M leakage-aware split design gate was verified: true.

## Current Sample Index
- current_sample_count: 3 samples.
- sample_index_observed_field_count: 14.
- sample_index_observed_fields: sample_id, source_sample_id, split, npz_path, npz_sha256, ligand_atom_count, ligand_bond_count, protein_atom_count, protein_residue_count, scaffold_atom_count, linker_atom_count, warhead_atom_count, ligand_reactive_atom_index, materialization_status.
- No NPZ contents read.
- npz_files_loaded: false.
- npz_contents_read: false.

## Required Metadata Coverage
- Step 12M required split metadata field count: 38.
- exact present required fields: sample_id, ligand_reactive_atom_index.
- missing required metadata count: 36.
- metadata completeness: 2/38.
- metadata_complete_for_final_split: false.

## Useful Non-Required Fields
- Useful but non-required sample_index fields include atom counts, materialization_status, npz_path, npz_sha256, source_sample_id, and split.
- split field is not final leakage-aware split and must not be used for paper claim.

## Candidate Enrichment Plan
- Candidate derivation plan is defined.
- Candidate metadata parsed from sample_id or source_sample_id is not authoritative.
- ligand identity requires RDKit/ligand structure.
- protein identity requires sequence/UniProt/CD-HIT.
- geometry requires coordinate calculation.

## Output Boundary
- No enriched sample_index written.
- No split assignments written.
- No leakage matrix written.
- No forward, no loss compute, no backward, no optimizer creation, no parameter update, no training loop call, no checkpoint/model/tensor dump.

## Decision
- metadata gap level: severe.
- metadata_enrichment_required: true.
- final_train_valid_test_split_allowed: false.
- real_covalent_split_metadata_inventory_gate_passed: true.
- recommended_next_step: real_covalent_split_metadata_enrichment_design_gate
