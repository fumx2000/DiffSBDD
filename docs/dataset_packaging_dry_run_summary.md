# Dataset Packaging Dry-Run Summary

This is packaging dry-run only.

- It reads final readiness candidates.
- It does not modify manifest files.
- It does not modify or generate SDF files.
- It does not copy protein or ligand files.
- It does not create package archives.
- It does not generate real training datasets.
- It does not train or fine-tune any model.
- Passing this dry-run means candidates can enter packaging dry-run QA.
- Passing this dry-run still does not mean the samples are training-ready.

| candidate_id | source_sample_id | protein_pdb_path | ligand_sdf_path | packaging_dry_run_status | packaging_plan_row_written | ready_for_real_packaging_later | real_dataset_generated | training_ready | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9_pre_reaction | BTK_C481_6DI9 | data/raw/covalent_small/proteins/BTK_C481_6DI9.pdb | data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf | dataset_packaging_dry_run_passed | true | true | false | false | build_dataset_packaging_dry_run_qa_not_training |
| KRAS_G12C_5F2E_pre_reaction | KRAS_G12C_5F2E | data/raw/covalent_small/proteins/KRAS_G12C_5F2E.pdb | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf | dataset_packaging_dry_run_passed | true | true | false | false | build_dataset_packaging_dry_run_qa_not_training |
| KRAS_G12C_6OIM_pre_reaction | KRAS_G12C_6OIM | data/raw/covalent_small/proteins/KRAS_G12C_6OIM.pdb | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf | dataset_packaging_dry_run_passed | true | true | false | false | build_dataset_packaging_dry_run_qa_not_training |

## Global Conclusion

- All three candidates passed packaging dry-run.
- Packaging dry-run plan CSV contains exactly 3 rows: true.
- No files were copied.
- No package archive was created.
- Manifest was not modified.
- No SDF files were modified or generated.
- No real dataset was generated.
- No training was run.
- Next step is packaging dry-run QA, not training.
