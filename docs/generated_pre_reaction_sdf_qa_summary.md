# Generated Pre-Reaction SDF QA Summary

This QA checks generated pre-reaction SDF files only.

- It does not modify any SDF files.
- It does not modify raw ligand SDF files.
- It does not modify repaired trial SDF files.
- It does not modify manifest files.
- It does not mark samples as training-ready.

| sample_id | qa_status | source_restore_bond_order | output_restore_bond_order | target_bond_order | bond_block_change_count | allowed_bond_order_change_only | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | generated_pre_reaction_sdf_qa_passed | 2 | 2 | 2 | 0 | true | build_pre_reaction_training_readiness_gate |
| KRAS_G12C_5F2E | generated_pre_reaction_sdf_qa_passed | 2 | 2 | 2 | 0 | true | build_pre_reaction_training_readiness_gate |
| KRAS_G12C_6OIM | generated_pre_reaction_sdf_qa_passed | 1 | 2 | 2 | 1 | true | build_pre_reaction_training_readiness_gate |

## Global Conclusion

- Generated pre-reaction SDF QA passed for all samples: true.
- No SDF files were modified during QA.
- No manifest was modified.
- No sample is training-ready.
- Next step is a separate training-readiness gate, not training.
