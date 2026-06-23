# Actual Dataset Index Build Summary

This is actual dataset index build for review-only artifacts.

- Explicit approval token was required and provided.
- It wrote a review-only dataset index CSV.
- It wrote a review-only dataset manifest JSON.
- It did not modify manifest files.
- It did not modify source or packaged PDB/SDF/JSON files.
- It did not copy files.
- It did not create package archives.
- It did not generate real training tensor datasets.
- It did not train or fine-tune any model.
- Passing this step still does not mean the samples are training-ready.

## Output Files

- index CSV path: `data/derived/covalent_small/dataset_index_review_only/covalent_small_pre_reaction_review_only_index.csv`
- dataset manifest JSON path: `data/derived/covalent_small/dataset_index_review_only/covalent_small_pre_reaction_review_only_manifest.json`
- index row count: 3
- manifest row count: 3

| candidate_id | source_sample_id | index_row_found_once | index_row_fields_match_gate_plan | index_row_hashes_match_files | index_row_safety_flags_valid | actual_dataset_index_build_status | real_dataset_generated | training_ready | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9_pre_reaction | BTK_C481_6DI9 | true | true | true | true | actual_dataset_index_build_passed | false | false | build_actual_dataset_index_qa_not_training |
| KRAS_G12C_5F2E_pre_reaction | KRAS_G12C_5F2E | true | true | true | true | actual_dataset_index_build_passed | false | false | build_actual_dataset_index_qa_not_training |
| KRAS_G12C_6OIM_pre_reaction | KRAS_G12C_6OIM | true | true | true | true | actual_dataset_index_build_passed | false | false | build_actual_dataset_index_qa_not_training |

## Global Conclusion

- All three samples passed actual dataset index build.
- Index CSV contains exactly 3 rows: true.
- Dataset manifest JSON row_count is 3: true.
- No package files were copied.
- No source or packaged PDB/SDF/JSON files were modified.
- No archive was created.
- No training tensor dataset was generated.
- No training was run.
- Next step is actual dataset index QA, not training.
