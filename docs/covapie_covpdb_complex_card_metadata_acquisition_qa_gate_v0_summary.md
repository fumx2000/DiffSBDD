# CovaPIE CovPDB Complex Card Metadata Acquisition QA Gate v0 Summary

This is a read-only QA gate for the Step 13AS complex-card metadata acquisition smoke artifacts.
It does not access the network.
It does not rerun the Step 13AS live acquisition check script.
It does not fetch complex cards.
It does not download raw structures, ligand SDF, ZIP/GZ, PDB, CIF, or mmCIF.
It does not save full HTML.
It does not modify the Step 13AS artifacts or parser.
It does not materialize candidate metadata or candidate allowlists.
It does not write sample_index, final_dataset, split assignments, or leakage matrix.
It does not import torch, create tensors, load checkpoints, call model forward, compute loss, backward, optimizer, trainer.fit, or train.

Step 13AS showed that five allowed CovPDB complex-card HTML pages were fetched successfully.
The current text parser did not resolve chain/residue/reactive atom/covalent bond atom pair fields.
Candidate metadata, allowlist materialization, raw-read smoke, and training therefore remain blocked.
The recommended next step is a sanitized CovPDB complex-card HTML structure probe design gate, not raw download or training.

attempted_card_count: `5`
fetch_succeeded_count: `5`
fetch_failed_count: `0`
minimal_event_key_resolved_card_count: `0`
preferred_event_key_resolved_card_count: `0`
partial_event_key_card_count: `0`
unresolved_card_count: `5`
future_candidate_metadata_possible_count: `0`
future_automatic_allowlist_possible_count: `0`
ready_for_covapie_covpdb_complex_card_html_structure_probe_design_gate: `True`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `covapie_covpdb_complex_card_html_structure_probe_design_gate`
blocking_reasons: `[]`
