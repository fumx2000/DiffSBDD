# Pre-Reaction Actual Manifest Update QA Summary

This QA validates the actual manifest update after Step 8V.

- It does not modify manifest files.
- It does not modify or generate SDF files.
- It does not train or fine-tune any model.
- Passing this QA means the actual manifest update can be committed.
- Passing this QA does not mean the samples are training-ready.

| proposed_manifest_sample_id | source_sample_id | actual_manifest_update_qa_status | proposed_ligand_sdf_path | existing_rows_preserved | appended_rows_match_proposed_rows | training_ready | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9_pre_reaction | BTK_C481_6DI9 | actual_manifest_update_qa_passed | data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf | true | true | false | commit_actual_manifest_update_after_qa_not_training |
| KRAS_G12C_5F2E_pre_reaction | KRAS_G12C_5F2E | actual_manifest_update_qa_passed | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf | true | true | false | commit_actual_manifest_update_after_qa_not_training |
| KRAS_G12C_6OIM_pre_reaction | KRAS_G12C_6OIM | actual_manifest_update_qa_passed | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf | true | true | false | commit_actual_manifest_update_after_qa_not_training |

## Global Conclusion

- Actual manifest update QA passed for all three rows.
- Backup matches manifest before update.
- Current manifest equals backup plus exactly 3 proposed rows.
- No existing manifest rows were modified.
- No SDF files were modified or generated.
- No training was run.
- Next step is commit actual manifest update and QA files.
