# Pre-Reaction Transform Execution Plan

This is an execution plan only.

- It does not create pre-reaction SDF files.
- It does not modify raw ligand SDF files.
- It does not modify repaired trial SDF files.
- It does not modify manifest files.
- It does not mark samples as training-ready.
- SDF generation requires explicit future approval.

| sample_id | source_repaired_sdf | planned_output_pre_reaction_sdf | planned_bond_order_operation | execution_plan_status | write_sdf_allowed_by_plan | approval_phrase_required |
| --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | data/derived/covalent_small/ligands_warhead_only_repaired/BTK_C481_6DI9_warhead_only_repaired_trial.sdf | data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf | validate_existing_target_bond_order_and_copy_if_future_approved | ready_for_guarded_transform_script_design | false | APPROVE_PRE_REACTION_TRANSFORM_SDF_STEP_8P |
| KRAS_G12C_5F2E | data/derived/covalent_small/ligands_warhead_only_repaired/KRAS_G12C_5F2E_warhead_only_repaired_trial.sdf | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf | validate_existing_target_bond_order_and_copy_if_future_approved | ready_for_guarded_transform_script_design | false | APPROVE_PRE_REACTION_TRANSFORM_SDF_STEP_8P |
| KRAS_G12C_6OIM | data/derived/covalent_small/ligands_warhead_only_repaired/KRAS_G12C_6OIM_warhead_only_repaired_trial.sdf | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf | set_bond_order_to_target_if_future_approved | ready_for_guarded_transform_script_design | false | APPROVE_PRE_REACTION_TRANSFORM_SDF_STEP_8P |

## Global Conclusion

- Execution plan is ready for guarded transform script design: true.
- No pre-reaction SDF was generated.
- No sample is training-ready.
- Future SDF generation requires explicit approval phrase APPROVE_PRE_REACTION_TRANSFORM_SDF_STEP_8P.
