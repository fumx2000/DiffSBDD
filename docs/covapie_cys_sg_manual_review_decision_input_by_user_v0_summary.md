# CovaPIE CYS/SG Manual Review Decision Input By User v0 Summary

Step 14P records user-supplied manual review decision input. It copies the Step 14O decision template into a new decision input artifact and marks only the five user-selected Step 14N rows as `accept_for_future_struct_conn_crosscheck`.

This step does not modify Step 14O artifacts, does not create ready candidates, does not run raw/mmCIF struct_conn cross-check, does not use network access, does not write sample/final/split/leakage artifacts, and does not train.

input_manual_review_candidate_count: `25`
accepted_for_future_struct_conn_crosscheck_count: `5`
pending_manual_review_count: `20`
rejected_candidate_count_current_step: `0`
needs_more_evidence_count_current_step: `0`
ready_candidate_count_current_step: `0`
accepted_pdb_het_pairs: `1A54/MDC, 6BV6/JUG, 6BV9/JUG, 6BV8/JUG, 6BV5/JUG`
ready_for_covapie_cys_sg_manual_review_decision_application_gate: `True`
ready_for_training: `False`
recommended_next_step: `covapie_cys_sg_manual_review_decision_application_gate`

Accepted for future struct_conn cross-check is not a ready-candidate label. Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.
