# Warhead-Only Repair Readiness Summary

This is a readiness summary only.

- It does not modify raw ligand SDF files.
- It does not modify repaired trial SDF files.
- It does not create pre-reaction graphs.
- It does not modify manifest files.
- It does not mark samples as training-ready.

| sample_id | derived_trial_safe | training_ready | pre_reaction_graph_ready | qa_passed_rows | qa_failed_rows | manual_unresolved_count | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | true | false | false | 35 | 0 | 5 | manual_boundary_review_or_pre_reaction_graph_design_before_training_ready |
| KRAS_G12C_5F2E | true | false | false | 33 | 0 | 4 | manual_boundary_review_or_pre_reaction_graph_design_before_training_ready |
| KRAS_G12C_6OIM | true | false | false | 45 | 0 | 6 | manual_boundary_review_or_pre_reaction_graph_design_before_training_ready |

## BTK_C481_6DI9

- derived_trial_safe: true
- training_ready: false
- reason not training-ready: has unresolved linker/local boundary atoms; cross-boundary transfer is not ready; pre-reaction graph is not ready.
- recommended_next_action: `manual_boundary_review_or_pre_reaction_graph_design_before_training_ready`

## KRAS_G12C_5F2E

- derived_trial_safe: true
- training_ready: false
- reason not training-ready: has unresolved linker/local boundary atoms; cross-boundary transfer is not ready; pre-reaction graph is not ready.
- recommended_next_action: `manual_boundary_review_or_pre_reaction_graph_design_before_training_ready`

## KRAS_G12C_6OIM

- derived_trial_safe: true
- training_ready: false
- reason not training-ready: has unresolved linker/local boundary atoms; cross-boundary transfer is not ready; pre-reaction graph is not ready.
- recommended_next_action: `manual_boundary_review_or_pre_reaction_graph_design_before_training_ready`

## Global Conclusion

- All three repaired trial SDFs are safe derived curation artifacts: true.
- No sample is training-ready: true.
- The next safe direction is manual boundary review and/or pre-reaction graph design.
- Do not use these derived SDFs for model training yet.
