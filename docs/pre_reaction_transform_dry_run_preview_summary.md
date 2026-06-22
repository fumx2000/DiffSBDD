# Pre-Reaction Transform Dry-Run Preview Summary

This is a dry-run preview only.

- It does not create pre-reaction SDF files.
- It does not modify raw ligand SDF files.
- It does not modify repaired trial SDF files.
- It does not modify manifest files.
- It does not mark samples as training-ready.

| sample_id | dry_run_preview_status | manual_covalent_bond_to_remove | manual_bond_order_to_restore | current_bond_order_in_repaired_sdf | target_bond_order | bond_order_dry_run_action | can_build_future_transform_script |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | preview_passed | CYS:SG-19 | 18-19:double | 2 | 2 | already_target_order_no_change_needed | true |
| KRAS_G12C_5F2E | preview_passed | CYS:SG-29 | 8-29:double | 2 | 2 | already_target_order_no_change_needed | true |
| KRAS_G12C_6OIM | preview_passed | CYS:SG-7 | 6-7:double | 1 | 2 | would_restore_bond_order_to_target | true |

## Global Conclusion

- Dry-run preview passed for all eligible samples: true.
- No pre-reaction SDF was generated.
- No sample is training-ready: true.
- Next step is to design a guarded transform script, not training.
