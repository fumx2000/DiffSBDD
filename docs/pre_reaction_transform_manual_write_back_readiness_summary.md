# Pre-Reaction Transform Manual Write-Back Readiness Summary

This is a post-write-back readiness checker only.

- It does not generate pre-reaction SDF files.
- It does not modify raw ligand SDF files.
- It does not modify repaired trial SDF files.
- It does not modify manifest files.
- It does not mark samples as training-ready.

| sample_id | post_write_back_check_status | eligible_for_future_transform_dry_run_only | manual_covalent_bond_to_remove | manual_bond_order_to_restore | recommended_next_action |
| --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | eligible_for_future_transform_dry_run_only | true | CYS:SG-19 | 18-19:double | build_pre_reaction_transform_dry_run_next |
| KRAS_G12C_5F2E | eligible_for_future_transform_dry_run_only | true | CYS:SG-29 | 8-29:double | build_pre_reaction_transform_dry_run_next |
| KRAS_G12C_6OIM | eligible_for_future_transform_dry_run_only | true | CYS:SG-7 | 6-7:double | build_pre_reaction_transform_dry_run_next |

## Global Conclusion

- Manual write-back is complete.
- Samples are eligible for future transform dry-run only: true.
- No pre-reaction SDF was generated.
- No sample is training-ready: true.
