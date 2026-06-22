# Guarded Pre-Reaction Transform Write-SDF Summary

This write_sdf run was performed only after explicit human approval.

- Approval phrase: APPROVE_PRE_REACTION_TRANSFORM_SDF_STEP_8P
- It created only derived pre-reaction SDF files.
- It did not modify raw ligand SDF files.
- It did not modify repaired trial SDF files.
- It did not modify manifest files.
- It did not mark samples as training-ready.
- Generated SDFs still require QA before any training use.

| sample_id | output_pre_reaction_sdf | planned_bond_order_operation | original_bond_order_in_source_sdf | target_bond_order | final_bond_order_in_output_sdf | write_sdf_status | training_ready |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf | validate_existing_target_bond_order_and_copy_if_future_approved | 2 | 2 | 2 | written_after_explicit_human_approval | false |
| KRAS_G12C_5F2E | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf | validate_existing_target_bond_order_and_copy_if_future_approved | 2 | 2 | 2 | written_after_explicit_human_approval | false |
| KRAS_G12C_6OIM | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf | set_bond_order_to_target_if_future_approved | 1 | 2 | 2 | written_after_explicit_human_approval | false |

## Global Conclusion

- 3 pre-reaction SDF files were generated as derived artifacts.
- No raw ligand SDF was modified.
- No repaired trial SDF was modified.
- No manifest was modified.
- No sample is training-ready.
- Next step is generated pre-reaction SDF QA.
