# CovaPIE Current11 Cys-SG candidate assignments V1

This stage materializes a stable seven-class candidate warhead-type vocabulary
and exact-one candidate reaction-family/rule assignments for all eleven
Current11 samples.

The class authority is the ascending full 64-character
`canonical_local_graph_rule_sha256`. Class indices are exactly `0..6`; each
stable class ID is `COVAPIE_CYS_SG_WARHEAD_TYPE_CLASS_` followed by the
upper-case first sixteen SHA characters. Sample frequency, component, PDB,
semantic name, registry row order, and unordered sets are not ordering
authorities.

Every sample record is a machine-derived candidate assignment with
`review_status=not_reviewed` and
`training_label_status=not_approved_for_training`. Its canonical record SHA
covers sample, CYS-SG target, reactive ligand atom, parent/observed graph,
radius-1 signature, candidate family/rule/class identity, and all three
statuses. It does not include its own digest.

All eleven review packages are ready for human assignment review. No formal or
gold reaction-family label, approved warhead rule, approved SMARTS, training
label, role annotation, seed, mask, tensor, model head, loss, or model
integration is materialized. The downstream role contract requires approved
reaction-family/warhead-rule authority, so role proposal generation remains
closed.

The transaction is fail-closed. Phase A validates the immutable BASE sources,
their SHA256 values, predecessor transactions, Current11 identity, reactive
atoms, and graph SHA values. Phase B validates the deterministic vocabulary,
exact-one joins, record hashes, and review readiness. If either phase fails,
the vocabulary, assignment authority, and readiness matrix are all
header-only. The Exact27 typed-mutation matrix demonstrates this closed
behavior.

The recommended next step is
`design_covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_v1`.
