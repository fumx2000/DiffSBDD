# Warhead-Local Manual Decision Summary

This is a summary only.

- It does not repair bond orders.
- It does not create pre-reaction graphs.
- It does not modify ligand SDF files.
- It does not mark samples as training-ready.

| sample_id | rows | accept_candidate_count | unresolved_count | accepted_warhead_rows | unresolved_boundary_rows | local_bond_order_transfer_ready | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | 9 | 4 | 5 | 4 | 5 | false | strictly_warhead_only_trial_or_manual_boundary_review_before_transfer |
| KRAS_G12C_5F2E | 8 | 4 | 4 | 4 | 4 | false | strictly_warhead_only_trial_or_manual_boundary_review_before_transfer |
| KRAS_G12C_6OIM | 10 | 4 | 6 | 4 | 6 | false | strictly_warhead_only_trial_or_manual_boundary_review_before_transfer |

## BTK_C481_6DI9

- Conclusion: not ready for cross-boundary local bond-order transfer. Accepted warhead rows: 4/4; unresolved boundary rows: 5.
- Recommended next action: `strictly_warhead_only_trial_or_manual_boundary_review_before_transfer`

## KRAS_G12C_5F2E

- Conclusion: not ready for cross-boundary local bond-order transfer. Accepted warhead rows: 4/4; unresolved boundary rows: 4.
- Recommended next action: `strictly_warhead_only_trial_or_manual_boundary_review_before_transfer`

## KRAS_G12C_6OIM

- Conclusion: not ready for cross-boundary local bond-order transfer. Accepted warhead rows: 4/4; unresolved boundary rows: 6.
- Recommended next action: `strictly_warhead_only_trial_or_manual_boundary_review_before_transfer`

## Global Conclusion

- All three samples have accepted warhead-core mappings.
- All three samples still have unresolved linker/local boundary atoms.
- No sample is ready for cross-boundary local bond-order transfer.
- The next safe direction is either manual boundary review or a strictly warhead-only, non-destructive trial that does not cross unresolved atoms.
