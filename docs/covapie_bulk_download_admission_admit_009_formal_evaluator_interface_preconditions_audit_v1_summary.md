# CovaPIE ADMIT_009 formal evaluator interface preconditions audit v1

This read-only, metadata-only audit confirms the high-level identity `ADMIT_009 / duplicate_identity_precheck`, its `pre_download` phase, candidate field `duplicate_identity_key`, batch dependency `batch_duplicate_identity_keys`, evaluation-policy dependency `duplicate_identity_key_contract`, and the feasibility of a future pure-in-memory interface.

All Exact24 audit rows pass as audit assertions. Six interface-identity or feasibility semantics are complete and eighteen formal duplicate-key, batch-membership, result-state, oracle, provider, or implementation semantics are incomplete. A passed audit row does not claim that its required semantic contract exists.

The 24-row vocabulary inventory keeps candidate, sample, assignment, ligand, residue, atom-pair, protein-group, leakage-group, split, and materialization identities distinct. `candidate_record_id` is explicitly not `duplicate_identity_key`; ligand graph/scaffold groups and the conservative multi-relation leakage group are not promoted to exact-duplicate equivalence or duplicate-key components.

The fixed Exact17 source boundary uses tracked regular non-symlink blobs from commit `8215c99edc93b4dcf50da87139917fae9ec46cc5`. It reads only frozen committed snapshot bytes, does not recursively open artifact references, and contains no raw or checkpoint source. Historical grouping evidence exists, but the canonical duplicate-key provider mapping is unvalidated and the real provider duplicate-key count is zero.

The Exact11 runtime issue inventory is byte-identical to its Exact8 predecessor. `DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED` remains open for `duplicate_identity_key / ADMIT_009`, and unified coverage still begins with ADMIT_009.

`ready_for_admit_009_standalone_evaluator_interface_implementation` is false. `ready_for_admit_009_duplicate_identity_key_contract_design` is true. The sole recommended next step is `design_covapie_admit_009_duplicate_identity_key_contract_v1`.

No duplicate key, component set, separator, hash, batch container, self-exclusion policy, evaluator, result class, adapter, Exact9 runtime entry, provider mapping, real candidate evaluation, raw/network/download operation, or training action is created by this audit. A feature-semantics audit remains mandatory before any formal training; Step12D was only a smoke legality check.
