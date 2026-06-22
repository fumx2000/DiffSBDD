# Pre-Reaction Manifest Update Dry-Run Summary

This is a manifest update dry-run only.

- It does not modify manifest_real_small.csv.
- It does not create a new full manifest file.
- It only writes a proposed rows preview.
- It does not modify any SDF files.
- It does not train or fine-tune any model.
- Passing this dry-run does not mean the samples are training-ready.

| sample_id | proposed_manifest_sample_id | proposed_ligand_sdf_path | manifest_update_dry_run_status | would_add_manifest_row_later | manifest_updated | new_manifest_created | training_ready | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | BTK_C481_6DI9_pre_reaction | data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf | passed_manifest_update_dry_run_not_written | true | false | false | false | manual_review_manifest_update_dry_run_before_approval |
| KRAS_G12C_5F2E | KRAS_G12C_5F2E_pre_reaction | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf | passed_manifest_update_dry_run_not_written | true | false | false | false | manual_review_manifest_update_dry_run_before_approval |
| KRAS_G12C_6OIM | KRAS_G12C_6OIM_pre_reaction | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf | passed_manifest_update_dry_run_not_written | true | false | false | false | manual_review_manifest_update_dry_run_before_approval |

## Global Conclusion

- All three proposed manifest rows passed dry-run.
- manifest_real_small.csv was not modified.
- No new full manifest was created.
- Proposed rows preview was written.
- No SDF was modified.
- No training was run.
- Next step is manual review and explicit approval before actual manifest update.
