# Real Covalent Pilot Download Integrity Gate v0 Summary

Step 12U is a pilot download integrity gate.

This step performed no network calls, no re-download, no decompression, and no mmCIF parsing.

## Raw Files Rechecked
- 6DI9.cif.gz
- 5F2E.cif.gz
- 6OIM.cif.gz

All raw files exist, are nonempty, have file size values matching Step 12T, have SHA256 values matching Step 12T provenance, have valid gzip magic bytes, live under data/raw, are gitignored, are not staged, are not tracked, and are not allowed to commit.

## Provenance
The provenance cross-check passed. The Step 12T provenance rows match the recomputed raw file size and SHA256 values, and local curated rows remain recorded without NPZ reads.

## Safety Boundary
This step performed no mmCIF parsing, no adapters, no RDKit/UniProt/CD-HIT/geometry, and no training.
It did not write enriched sample_index, split assignments, leakage matrix, checkpoint, model, or tensor dump artifacts.

## Decision
- raw_file_integrity_row_count: 3
- all_raw_file_sizes_match_expected: true
- all_raw_sha256_match_expected: true
- all_raw_gzip_magic_valid: true
- provenance_cross_check_passed: true
- ready_for_minimal_mmcif_parser_design_gate: true
- recommended_next_step: real_covalent_minimal_mmcif_parser_design_gate

The next step is real_covalent_minimal_mmcif_parser_design_gate. That step can start designing a minimal parser/adapter smoke, but still should not begin large-scale parsing.
