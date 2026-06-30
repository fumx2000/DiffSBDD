# Real Covalent Multi-Source Dataset Ingestion Design Gate v0 Summary

Step 12P is a multi-source dataset ingestion design gate, not downloading, not enrichment, not split, not training.

## Scope
This step defines the pre-download engineering contract for covalent dataset ingestion. It does not write real source URLs, does not verify current URLs, and does not verify license terms. Source URL placeholders and usage notes must be resolved in the source registry license audit.

## Planned Sources
- CovPDB
- CovBinderInPDB
- CovalentInDB
- PDB/mmCIF direct
- local curated

## Adapter Contract
Different datasets must enter through source-specific adapters. Each adapter must output canonical raw covalent records.
Different sources cannot one-pot merge before normalization.
The canonical raw covalent record schema is required before metadata enrichment.

## Raw Storage
Raw storage design is data/raw/covalent_sources/{source_name}/... with downloads, structures, tables, manifests, logs, and checksums subdirectories.
This step created no raw dirs and wrote no raw files.

## Download Controls
Download manifest, checksum, resume, and provenance records are required before any download job.
Raw downloads and large binary structures cannot commit to git.
Small pilot scope is 1-3 records per source after license audit.

## Safety Boundary
No data download/network/source registry/raw dirs/adapters occurred.
No RDKit/UniProt/CD-HIT/geometry/NPZ/training occurred.
No enriched sample_index, split assignments, leakage matrix, final split, checkpoint, model, or tensor dump was written.

## Decision
- source_registry_entry_count: 5
- ready_to_create_source_registry_license_audit: true
- ready_to_download_large_scale_data_now: false
- recommended_next_step: real_covalent_source_registry_license_audit_gate
