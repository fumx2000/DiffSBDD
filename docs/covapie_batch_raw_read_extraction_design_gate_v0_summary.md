# CovaPIE Batch Raw Read Extraction Design Gate v0 Summary

Step 13BD is a design gate for a future batch raw read / extraction smoke step.
It designs contracts for reading raw `.cif` files later, extracting event-level records later, and writing atom-level smoke tables later.
It does not read raw file content, parse mmCIF text, scan `atom_site` or `struct_conn`, extract coordinates, write extracted event or atom tables, write sample_index/final_dataset/split/leakage artifacts, or train.
The current step only checks raw file path existence and git tracking/staging status without opening raw files.
The five canonical masks remain unchanged, including `scaffold_only / B3`.
Feature semantics audit and leakage/split design remain required before formal training, fine-tuning, or real parameter updates.
This gate allows `covapie_batch_raw_read_extraction_smoke` next, not extraction QA, not sample_index design, and not training.

source_allowlist_row_count: `4`
batch_raw_read_input_contract_row_count: `4`
raw_file_path_contract_row_count: `4`
raw_file_path_exists_count: `4`
extracted_event_schema_field_count: `31`
extracted_atom_schema_row_count: `46`
raw_read_extraction_smoke_plan_row_count: `13`
raw_file_content_read_current_step: `False`
mmcif_parse_current_step: `False`
atom_site_scan_current_step: `False`
struct_conn_scan_current_step: `False`
coordinate_extraction_current_step: `False`
extracted_event_table_written: `False`
extracted_atom_table_written: `False`
ready_for_covapie_batch_raw_read_extraction_smoke: `True`
ready_for_covapie_extraction_qa_gate: `False`
ready_for_sample_index_design_gate: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_batch_raw_read_extraction_smoke`
blocking_reasons: `[]`
