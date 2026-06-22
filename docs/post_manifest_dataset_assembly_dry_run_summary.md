# Post-Manifest Dataset Assembly Dry-Run Summary

This is a dataset assembly dry-run only.

- It reads the updated manifest after actual manifest update QA.
- It does not modify manifest files.
- It does not modify or generate SDF files.
- It does not generate real training datasets.
- It does not train or fine-tune any model.
- Passing this dry-run means the rows can enter schema validation.
- Passing this dry-run does not mean the samples are training-ready.

| pre_reaction_sample_id | source_sample_id | ligand_sdf_path | protein_pdb_path | dataset_assembly_dry_run_status | candidate_written_to_dry_run_list | training_ready | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9_pre_reaction | BTK_C481_6DI9 | data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf | data/raw/covalent_small/proteins/BTK_C481_6DI9.pdb | post_manifest_dataset_assembly_dry_run_passed | true | false | build_dataset_assembly_schema_validation_not_training |
| KRAS_G12C_5F2E_pre_reaction | KRAS_G12C_5F2E | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf | data/raw/covalent_small/proteins/KRAS_G12C_5F2E.pdb | post_manifest_dataset_assembly_dry_run_passed | true | false | build_dataset_assembly_schema_validation_not_training |
| KRAS_G12C_6OIM_pre_reaction | KRAS_G12C_6OIM | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf | data/raw/covalent_small/proteins/KRAS_G12C_6OIM.pdb | post_manifest_dataset_assembly_dry_run_passed | true | false | build_dataset_assembly_schema_validation_not_training |

## Global Conclusion

- All three pre-reaction manifest rows passed post-manifest dataset assembly dry-run.
- Candidates CSV contains exactly 3 rows: true.
- Manifest was not modified.
- No SDF files were modified or generated.
- No real dataset was generated.
- No training was run.
- Next step is dataset assembly schema validation, not training.
