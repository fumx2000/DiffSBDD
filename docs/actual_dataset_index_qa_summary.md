# Actual Dataset Index QA Summary

This is actual dataset index QA only.
It reads the review-only dataset index and dataset manifest.
It does not modify the index CSV.
It does not modify the dataset manifest JSON.
It does not modify manifest files.
It does not modify source or packaged PDB/SDF/JSON files.
It does not copy files.
It does not create package archives.
It does not generate real training tensor datasets.
It does not train or fine-tune any model.
Passing this QA still does not mean the samples are training-ready.

## Index/Manifest Contents

- index CSV path: `data/derived/covalent_small/dataset_index_review_only/covalent_small_pre_reaction_review_only_index.csv`
- dataset manifest JSON path: `data/derived/covalent_small/dataset_index_review_only/covalent_small_pre_reaction_review_only_manifest.json`
- index row count: 3
- manifest row count: 3
- package file counts: 3 PDB, 3 SDF, 3 metadata JSON

## Sample QA

| candidate_id | source_sample_id | index_row_fields_match_gate_plan | index_row_hashes_match_current_files | dataset_manifest_hashes_match_current_files | mask_levels_valid | auxiliary_labels_valid | actual_dataset_index_qa_status | real_dataset_generated | training_ready | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9_pre_reaction | BTK_C481_6DI9 | true | true | true | true | true | actual_dataset_index_qa_passed | false | false | prepare_read_only_dataset_loader_dry_run_gate_not_training |
| KRAS_G12C_5F2E_pre_reaction | KRAS_G12C_5F2E | true | true | true | true | true | actual_dataset_index_qa_passed | false | false | prepare_read_only_dataset_loader_dry_run_gate_not_training |
| KRAS_G12C_6OIM_pre_reaction | KRAS_G12C_6OIM | true | true | true | true | true | actual_dataset_index_qa_passed | false | false | prepare_read_only_dataset_loader_dry_run_gate_not_training |

## Global Conclusion

- all three samples passed actual dataset index QA
- index CSV contains exactly 3 rows: true
- dataset manifest row_count is 3: true
- no index/manifest/package/source/raw manifest files were modified by QA
- no archive was created
- no training tensor dataset was generated
- no training was run
- next step is read-only dataset loader dry-run gate, not training
