# Guarded Pre-Reaction Transform Dry-Run Summary

This is a dry-run of the guarded transform script only.

- It does not create pre-reaction SDF files.
- It does not create the ligands_pre_reaction directory.
- It does not modify raw ligand SDF files.
- It does not modify repaired trial SDF files.
- It does not modify manifest files.
- It does not mark samples as training-ready.
- Future write_sdf mode requires explicit approval phrase APPROVE_PRE_REACTION_TRANSFORM_SDF_STEP_8P.

| sample_id | dry_run_status | source_repaired_sdf_sha256_matches | planned_bond_order_operation | planned_output_pre_reaction_sdf | can_attempt_future_write_sdf_after_explicit_approval |
| --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | dry_run_passed_no_files_written | true | validate_existing_target_bond_order_and_copy_if_future_approved | data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf | true |
| KRAS_G12C_5F2E | dry_run_passed_no_files_written | true | validate_existing_target_bond_order_and_copy_if_future_approved | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf | true |
| KRAS_G12C_6OIM | dry_run_passed_no_files_written | true | set_bond_order_to_target_if_future_approved | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf | true |

## Global Conclusion

- Guarded transform dry-run passed: true.
- No pre-reaction SDF was generated.
- No output directory was created.
- No sample is training-ready.
- Wait for explicit human approval before write_sdf.
