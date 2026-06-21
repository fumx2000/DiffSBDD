# Warhead-Only Bond-Order Dry-Run Summary

This is a dry-run report only.

- It does not repair bond orders.
- It does not create repaired SDF files.
- It does not create pre-reaction graphs.
- It does not modify ligand SDF files.
- It does not mark samples as training-ready.

| sample_id | total_bonds_reported | eligible_keep_count | eligible_would_transfer_count | blocked_touches_unresolved_boundary_count | blocked_missing_reference_bond_count | blocked_atom_not_accepted_count |
| --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | 35 | 1 | 2 | 7 | 0 | 25 |
| KRAS_G12C_5F2E | 33 | 1 | 2 | 6 | 0 | 24 |
| KRAS_G12C_6OIM | 45 | 2 | 1 | 8 | 0 | 34 |

## Global Conclusion

- No repaired SDF was generated.
- Only eligible rows fully inside accepted warhead atoms may be considered later.
- Any row touching unresolved boundary remains blocked.
