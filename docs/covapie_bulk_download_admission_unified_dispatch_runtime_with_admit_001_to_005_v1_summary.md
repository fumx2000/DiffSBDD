# CovaPIE ADMIT_001–005 unified dispatch runtime v1

This successor single-rule runtime preserves the committed Phase 4 runtime and
reuses its ADMIT_001–004 handler objects by identity. It registers one new
handler for ADMIT_005; ADMIT_006–015 remain known but unregistered and fail
closed.

The ADMIT_005 path enforces None-only contexts in batch, evaluation, download
result, and stage authorization order before candidate access. It projects only
`covalent_residue_name` and `covalent_residue_atom_name`, calls the standalone
evaluator once with the original scalar objects, validates its exact result type
and Exact10 invariants before oracle access, calls both independent semantic
oracle helpers once, requires Exact10 equality, and then projects Exact10 to the
shared Exact13 result. Passed, rejected, and invalid outcomes are preserved;
rejected is not remapped.

Deterministic evidence comprises 35 non-duplicate contract rows, 71 non-padding
truth rows in eight groups, 15 registry audit rows, a safety audit, the updated
Exact11 issue inventory, and a manifest. Only the coverage issue changes: its
open scope now begins at ADMIT_006. The provider blocker and cross-rule
aggregation blocker remain open.

This increment does not implement `evaluate_all_rules`, a combined verdict,
cross-rule aggregation, ADMIT_006, real candidate or Exact11 evaluation, raw or
provider execution, downloads, checkpoint use, model changes, or training.
Bulk-download and training readiness remain false. A feature-semantics audit is
still mandatory before any formal training work.
