# CovaPIE Step14AU-A Admission Executability Preconditions

Step14AU-A is a read-only audit of the six committed Step14AT admission-design
outputs. It preserves their SHA256 values, does not follow artifact references,
and never reads raw data, accesses a network, or materializes a candidate.

The audit separates dependency-contract correctness from rule-logic readiness.
All 15 canonical rule IDs, phases, candidate fields, batch contexts, and
explicit evaluation contexts are mapped deterministically. That means a future
pure evaluator interface can be shaped without filesystem or network access.
It does not mean the present rules can be executed truthfully.

Both dependency directions are audited: every rule dependency must resolve to
the canonical field/context contract, and every context's `required_by_rules`
must exactly match its actual consumers. Rule blockers are the sorted union of
all dependent field, batch-context, and evaluation-context blockers. The
field matrix also records the reverse `dependent_rules` mapping. The frozen
rule set does not state a consumer for `covalent_bond_atom_pair`; its encoding
gap therefore remains a field-level issue with no inferred rule consumer.

The Step14AT source contract leaves formats, normalization, enums, result
statuses, and several evaluation-policy contracts unresolved. Step14AU-A
records every affected rule and field blocker in deterministic sorted order.
Consequently, interface implementation readiness may be true while rule-logic
readiness and real candidate evaluation remain false.

The five canonical masks remain `warhead_only`/`A`,
`linker_plus_warhead`/`B`, `scaffold_plus_warhead`/`B2`,
`scaffold_only`/`B3`, and `scaffold_plus_linker_plus_warhead`/`C`.
Bulk download, training, fine-tuning, and parameter updates remain forbidden;
feature semantics audit remains required before training.
