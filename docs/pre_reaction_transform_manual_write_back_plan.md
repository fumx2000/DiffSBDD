# Pre-Reaction Transform Manual Write-Back Plan

This is a write-back plan only.

- It does not write back to decision draft files.
- It does not approve any transform.
- It does not create pre-reaction SDF files.
- It does not modify raw ligand SDF files.
- It does not modify repaired trial SDF files.
- It does not mark samples as training-ready.

| sample_id | proposed_manual_covalent_bond_to_remove | proposed_manual_bond_order_to_restore | proposed_manual_boundary_resolution | write_back_allowed_by_script | explicit_human_approval_required | approval_phrase_required | plan_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | CYS:SG-19 | 18-19:double | reviewed_no_boundary_atoms_transferred_to_pre_reaction_transform_rule_candidate | false | true | APPROVE_PRE_REACTION_WRITE_BACK_STEP_8L | awaiting_explicit_human_approval |
| KRAS_G12C_5F2E | CYS:SG-29 | 8-29:double | reviewed_no_boundary_atoms_transferred_to_pre_reaction_transform_rule_candidate | false | true | APPROVE_PRE_REACTION_WRITE_BACK_STEP_8L | awaiting_explicit_human_approval |
| KRAS_G12C_6OIM | CYS:SG-7 | 6-7:double | reviewed_no_boundary_atoms_transferred_to_pre_reaction_transform_rule_candidate | false | true | APPROVE_PRE_REACTION_WRITE_BACK_STEP_8L | awaiting_explicit_human_approval |

## Global Conclusion

- No decision draft was modified.
- Explicit human approval is required before write-back.
- No pre-reaction SDF was generated.
- No sample is training-ready.
