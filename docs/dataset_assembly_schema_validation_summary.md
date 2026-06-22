# Dataset Assembly Schema Validation Summary

This is schema validation only.

- It reads the post-manifest dry-run candidate list.
- It does not modify manifest files.
- It does not modify or generate SDF files.
- It does not generate real training datasets.
- It does not train or fine-tune any model.
- Passing this validation means candidates can enter file existence and hash gate.
- Passing this validation does not mean the samples are training-ready.

| candidate_id | source_sample_id | ligand_sdf_path | protein_pdb_path | schema_validation_status | schema_valid_candidate_written | training_ready | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9_pre_reaction | BTK_C481_6DI9 | data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf | data/raw/covalent_small/proteins/BTK_C481_6DI9.pdb | dataset_assembly_schema_validation_passed | true | false | build_dataset_assembly_file_existence_and_hash_gate_not_training |
| KRAS_G12C_5F2E_pre_reaction | KRAS_G12C_5F2E | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf | data/raw/covalent_small/proteins/KRAS_G12C_5F2E.pdb | dataset_assembly_schema_validation_passed | true | false | build_dataset_assembly_file_existence_and_hash_gate_not_training |
| KRAS_G12C_6OIM_pre_reaction | KRAS_G12C_6OIM | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf | data/raw/covalent_small/proteins/KRAS_G12C_6OIM.pdb | dataset_assembly_schema_validation_passed | true | false | build_dataset_assembly_file_existence_and_hash_gate_not_training |

## Global Conclusion

- All three candidates passed schema validation.
- Valid candidates CSV contains exactly 3 rows: true.
- Manifest was not modified.
- No SDF files were modified or generated.
- No real dataset was generated.
- No training was run.
- Next step is file existence and hash gate, not training.
