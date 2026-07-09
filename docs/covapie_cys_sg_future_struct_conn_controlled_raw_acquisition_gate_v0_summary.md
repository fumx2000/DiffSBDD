# CovaPIE CYS/SG Future Struct Conn Controlled Raw Acquisition Gate v0 Summary

Step 14S performs controlled raw mmCIF acquisition for the five Step 14R PDB IDs. It downloads missing files or reuses existing raw files, then records byte-level availability and integrity metadata.

This step does not parse struct_conn, does not create ready candidates, does not write sample/final/split/leakage/training artifacts, and does not train. Raw `.cif` files are written only under `data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0/` and must remain untracked and unstaged.

raw_mmcif_expected_count: `5`
raw_mmcif_available_count: `5`
raw_mmcif_integrity_passed_count: `5`
raw_acquisition_success_count: `5`
raw_downloaded_current_run_count: `0`
raw_reused_existing_count: `5`
accepted_pdb_het_pairs: `1A54/MDC, 6BV6/JUG, 6BV9/JUG, 6BV8/JUG, 6BV5/JUG`
struct_conn_parsed_current_step: `False`
ready_for_covapie_cys_sg_future_struct_conn_crosscheck_execution_gate: `True`
ready_for_training: `False`
recommended_next_step: `covapie_cys_sg_future_struct_conn_crosscheck_execution_gate`

Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.
