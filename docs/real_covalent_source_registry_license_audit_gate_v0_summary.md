# Real Covalent Source Registry License Audit Gate v0 Summary

Step 12Q is a source registry license audit gate, not downloading, not adapter implementation, not enrichment, not split, not training.

This step uses manual web-audit seed information to generate a small source registry license audit table.

## Planned Sources
- CovPDB
- CovBinderInPDB
- CovalentInDB
- PDB/mmCIF direct
- local curated

## License Audit
PDB/mmCIF direct has PDB archive license status verified CC0.
Local curated is local project controlled.
CovPDB / CovBinderInPDB / CovalentInDB require manual license review.
Publication found is not license clearance.
Free web access is not bulk download permission.
All bulk downloads disabled.

## Pilot Decision
Pilot candidates after audit are PDB/mmCIF direct and local curated.
Pilot download is still not allowed in this step; the next step must create a pilot download manifest.

## Safety Boundary
No data download/network/raw dirs/raw files/adapters occurred.
No RDKit/UniProt/CD-HIT/geometry/NPZ/training occurred.
No enriched sample_index, split assignments, leakage matrix, final split, checkpoint, model, or tensor dump was written.

## Decision
- source_registry_audit_record_count: 5
- sources_requiring_manual_license_review_count: 3
- ready_to_create_pilot_download_manifest: true
- ready_to_download_large_scale_data_now: false
- recommended_next_step: real_covalent_pilot_download_manifest_gate
