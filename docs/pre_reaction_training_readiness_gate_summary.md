# Pre-Reaction Training-Readiness Gate Summary

This is a readiness gate only.

- It does not train or fine-tune any model.
- It does not modify manifest files.
- It does not modify any SDF files.
- Passing this gate means the derived pre-reaction SDF can enter a dataset assembly candidate pool.
- Passing this gate does not mean the sample is training-ready.

| sample_id | dataset_candidate_gate_status | eligible_for_dataset_assembly_candidate_pool | output_pre_reaction_sdf | qa_status | can_update_manifest_later | training_ready | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | passed_for_dataset_candidate_not_training | true | data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf | generated_pre_reaction_sdf_qa_passed | true | false | build_manifest_staging_plan_not_training |
| KRAS_G12C_5F2E | passed_for_dataset_candidate_not_training | true | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf | generated_pre_reaction_sdf_qa_passed | true | false | build_manifest_staging_plan_not_training |
| KRAS_G12C_6OIM | passed_for_dataset_candidate_not_training | true | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf | generated_pre_reaction_sdf_qa_passed | true | false | build_manifest_staging_plan_not_training |

## Global Conclusion

- All generated pre-reaction SDFs passed the dataset-candidate gate.
- Manifest was not modified.
- No SDF was modified.
- No training was run.
- Next step is manifest staging plan, not training.
