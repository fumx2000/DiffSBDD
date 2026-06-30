# Real Covalent Split Metadata Enrichment Design Gate v0 Summary

Step 12O is a metadata enrichment design gate, not actual enrichment, not downloading, not split, not training.

## Definition
Metadata enrichment converts a thin materialization index to authoritative leakage-aware split metadata.
Current sample_index metadata completeness is 2/38, so enrichment is required before final split or training.

## Multi-Source Architecture
Different datasets can enter via source-specific adapters, then normalize into a canonical raw covalent record schema.
They cannot one-pot merge before normalization.
Required source-specific adapters: CovPDB, CovBinderInPDB, CovalentInDB, PDB/mmCIF direct, local curated.
The common enrichment pipeline includes ligand identity enrichment, protein identity enrichment, covalent identity enrichment, geometry/diversity enrichment, quality control enrichment, and leakage metadata enrichment.

## Enrichment Methods
Ligand identity requires RDKit.
Protein identity requires UniProt and CD-HIT-compatible sequence clustering.
Geometry/diversity requires coordinate geometry calculation.
Warhead and reaction metadata require a SMARTS library, reaction family classifier, and reconstruction template registry.

## Quality Policy
Heuristic metadata may be used for inventory only.
Authoritative metadata missing blocks final split and training.
Low-confidence, ambiguous covalent bond, ligand sanitization fail, protein mapping fail, duplicate, and non-Cys records are deferred or flagged according to the policy.

## Data Transition
ready_to_design_multi_source_ingestion=true.
ready_to_download_large_scale_data_now=false.
Raw downloads and large binary structures cannot be committed.
Allowed git outputs for this design stage: csv, json, md, py.

## Safety Boundary
No data download/network/RDKit/UniProt/CD-HIT/geometry run occurred.
No NPZ contents were read.
No enriched sample_index, split assignments, leakage matrix, or final split were written.
No forward, loss compute, backward, optimizer creation, parameter update, training loop call, checkpoint/model/tensor dump occurred.

## Decision
- real_covalent_split_metadata_enrichment_design_gate_passed: true
- metadata_enrichment_design_contract_defined: true
- recommended_next_step: real_covalent_multi_source_dataset_ingestion_design_gate
