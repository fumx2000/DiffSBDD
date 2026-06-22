# Pre-Reaction Transform Readiness Summary

This is a readiness summary only.

- It does not create pre-reaction SDF files.
- It does not modify raw ligand SDF files.
- It does not modify repaired trial SDF files.
- It does not modify manifest files.
- It does not mark samples as training-ready.

| sample_id | pre_reaction_transform_ready | training_ready | can_attempt_transform | dry_run_status | recommended_next_action |
| --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | false | false | false | blocked | manual_review_required_before_pre_reaction_transform;add_covalent_bond_to_remove_candidate_after_manual_review;add_bond_order_to_restore_candidate_after_manual_review;resolve_boundary_atoms_before_transform |
| KRAS_G12C_5F2E | false | false | false | blocked | manual_review_required_before_pre_reaction_transform;add_covalent_bond_to_remove_candidate_after_manual_review;add_bond_order_to_restore_candidate_after_manual_review;resolve_boundary_atoms_before_transform |
| KRAS_G12C_6OIM | false | false | false | blocked | manual_review_required_before_pre_reaction_transform;add_covalent_bond_to_remove_candidate_after_manual_review;add_bond_order_to_restore_candidate_after_manual_review;resolve_boundary_atoms_before_transform |

## Global Conclusion

- All current samples remain blocked: true.
- No sample is training-ready: true.
- No pre-reaction SDF was generated.
- Manual review is required before any transform.
