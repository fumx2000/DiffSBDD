# Pre-Reaction Manifest Staging Plan

This is a manifest staging plan only.

- It does not modify manifest_real_small.csv.
- It does not create a new manifest file.
- It does not modify any SDF files.
- It does not train or fine-tune any model.
- Passing this plan means proposed manifest rows may be built in a later dry-run step.
- Passing this plan does not mean the sample is training-ready.

| sample_id | proposed_manifest_sample_id | proposed_ligand_sdf_path | can_stage_manifest_row | manifest_row_should_be_added_later | manifest_updated | training_ready | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | BTK_C481_6DI9_pre_reaction | data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf | true | true | false | false | build_manifest_update_dry_run_not_training |
| KRAS_G12C_5F2E | KRAS_G12C_5F2E_pre_reaction | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf | true | true | false | false | build_manifest_update_dry_run_not_training |
| KRAS_G12C_6OIM | KRAS_G12C_6OIM_pre_reaction | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf | true | true | false | false | build_manifest_update_dry_run_not_training |

## Global Conclusion

- All three pre-reaction artifacts can be staged for future manifest update dry-run.
- manifest_real_small.csv was not modified.
- No new manifest was created.
- No SDF was modified.
- No training was run.
- Next step is manifest update dry-run, not training.
