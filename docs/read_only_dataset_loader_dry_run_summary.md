# Read-only Dataset Loader Dry-run Summary

This is read-only dataset loader dry-run only.
Explicit approval token was required and provided.
It read the review-only dataset index and dataset manifest.
It read packaged PDB/SDF/metadata files in read-only mode.
It constructed in-memory dry-run records.
It did not import torch.
It did not load checkpoints.
It did not initialize a model.
It did not generate dataloader tensors.
It did not modify the index CSV.
It did not modify the dataset manifest JSON.
It did not modify manifest files.
It did not modify source or packaged PDB/SDF/JSON files.
It did not copy files.
It did not create package archives.
It did not train or fine-tune any model.
Passing this dry-run still does not mean the samples are training-ready.

## Output Files

- dry-run report CSV path: `data/derived/covalent_small/loader_dry_run_review_only/read_only_dataset_loader_dry_run_report.csv`

## Sample Dry-run

| candidate_id | source_sample_id | packaged_metadata_json_parseable | packaged_protein_readable | packaged_ligand_sdf_readable | dry_run_record_constructed | loader_dry_run_executed | torch_imported | dataloader_tensor_generated | read_only_dataset_loader_dry_run_status | real_dataset_generated | training_ready | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9_pre_reaction | BTK_C481_6DI9 | true | true | true | true | true | false | false | read_only_dataset_loader_dry_run_passed | false | false | build_read_only_dataset_loader_dry_run_qa_not_training |
| KRAS_G12C_5F2E_pre_reaction | KRAS_G12C_5F2E | true | true | true | true | true | false | false | read_only_dataset_loader_dry_run_passed | false | false | build_read_only_dataset_loader_dry_run_qa_not_training |
| KRAS_G12C_6OIM_pre_reaction | KRAS_G12C_6OIM | true | true | true | true | true | false | false | read_only_dataset_loader_dry_run_passed | false | false | build_read_only_dataset_loader_dry_run_qa_not_training |

## Global Conclusion

- all three samples passed read-only dataset loader dry-run
- loader dry-run was executed in read-only mode
- torch was not imported
- no checkpoint was loaded
- no model was initialized
- no dataloader tensor was generated
- no files were copied
- no archive was created
- no training tensor dataset was generated
- no training was run
- next step is read-only dataset loader dry-run QA, not training
