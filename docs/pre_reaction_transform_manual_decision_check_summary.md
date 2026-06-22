# Pre-Reaction Transform Manual Decision Check Summary

This is a manual decision checker only.

- It does not create pre-reaction SDF files.
- It does not modify raw ligand SDF files.
- It does not modify repaired trial SDF files.
- It does not modify manifest files.
- It does not mark samples as training-ready.

| sample_id | decision_check_status | can_approve_for_future_transform | blocking_reasons | recommended_next_action |
| --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | blocked | false | requires_manual_review_true;review_status_not_reviewed;reviewer_decision_missing;manual_covalent_bond_to_remove_missing;manual_bond_order_to_restore_missing;manual_boundary_resolution_missing;proposed_bond_order_to_restore_candidate_missing | fill_manual_transform_decision_fields_before_transform |
| KRAS_G12C_5F2E | blocked | false | requires_manual_review_true;review_status_not_reviewed;reviewer_decision_missing;manual_covalent_bond_to_remove_missing;manual_bond_order_to_restore_missing;manual_boundary_resolution_missing;proposed_bond_order_to_restore_candidate_missing | fill_manual_transform_decision_fields_before_transform |
| KRAS_G12C_6OIM | blocked | false | requires_manual_review_true;review_status_not_reviewed;reviewer_decision_missing;manual_covalent_bond_to_remove_missing;manual_bond_order_to_restore_missing;manual_boundary_resolution_missing;proposed_bond_order_to_restore_candidate_missing | fill_manual_transform_decision_fields_before_transform |

## Global Conclusion

- All current samples remain blocked: true.
- No sample is approved for transform: true.
- No sample is training-ready: true.
- No pre-reaction SDF was generated.
