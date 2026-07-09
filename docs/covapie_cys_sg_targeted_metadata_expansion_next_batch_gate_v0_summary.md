# CovaPIE CYS/SG Targeted Metadata Expansion Next Batch Gate v0 Summary

Step 14M plans the next batch of CYS/SG ligand covalent metadata acquisition. It reads Step 14L/14K/14J artifacts only, writes design contracts and a future acquisition manifest, and does not use network access, download files, read raw CIF content, write raw files, create ready candidates, create sample/final/split/leakage artifacts, instantiate dataloaders, or train.

current_candidate_count: `9`
total_candidate_target: `20`
additional_candidate_needed_count: `11`
next_batch_source_strategy_row_count: `12`
next_batch_acquisition_manifest_row_count: `5`
ready_for_covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke: `True`
ready_for_training: `False`
recommended_next_step: `covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke`

The existing nine candidates remain pending manual review and are not ready candidates. Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.
