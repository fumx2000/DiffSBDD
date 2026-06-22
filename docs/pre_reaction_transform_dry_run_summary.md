# Pre-Reaction Transform Dry-Run Summary

This is a dry-run checker only.

- It does not create pre-reaction SDF files.
- It does not modify raw ligand SDF files.
- It does not modify repaired trial SDF files.
- It does not modify manifest files.
- It does not mark samples as training-ready.

| sample_id | can_attempt_transform | dry_run_status | proposed_action | blocking_reasons |
| --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | false | blocked | blocked_missing_required_transform_rule | requires_manual_review_true;review_status_not_reviewed;reviewer_decision_missing;covalent_bond_to_remove_candidate_missing;bond_order_to_restore_candidate_missing;unresolved_boundary_atoms_present |
| KRAS_G12C_5F2E | false | blocked | blocked_missing_required_transform_rule | requires_manual_review_true;review_status_not_reviewed;reviewer_decision_missing;covalent_bond_to_remove_candidate_missing;bond_order_to_restore_candidate_missing;unresolved_boundary_atoms_present |
| KRAS_G12C_6OIM | false | blocked | blocked_missing_required_transform_rule | requires_manual_review_true;review_status_not_reviewed;reviewer_decision_missing;covalent_bond_to_remove_candidate_missing;bond_order_to_restore_candidate_missing;unresolved_boundary_atoms_present |

## Global Conclusion

- No pre-reaction SDF was generated.
- All current samples remain blocked: true.
- Manual review is required before transform.
- Do not use any sample for training yet.
