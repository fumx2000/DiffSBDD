# CovaPIE ADMIT_005 standalone evaluator interface v1

This increment implements only the pure, in-memory `evaluate_admit_005(residue_name, atom_name)` scalar evaluator and its frozen `Admit005EvaluationResult`. It does not accept a candidate mapping or context and does not alter or register with the Phase 4 unified runtime.

The evaluator validates residue name first, then atom name, then classifies the CYS/SG scope. Residue names must be exact nonempty ASCII strings matching `[A-Za-z0-9]{1,32}` and are canonicalized to uppercase. Atom names must be exact nonempty ASCII strings without whitespace and cannot be `.` or `?`; valid generic atom names are preserved exactly. Only canonical residue `CYS` with exact atom `SG` passes. Other valid pairs are rejected with `ADMIT_005_CYS_SG_SCOPE_REJECTED`; lexical failures are invalid with the frozen field-specific reason.

The frozen result dataclass validates semantic state as well as field shape. A passed result is bound to the empty reason and exact canonical CYS/SG pair; a rejected result is bound to the scope-rejection reason and a valid non-CYS/SG canonical pair; an invalid result is bound to either a residue-invalid reason with no canonical fields or an atom-invalid reason with only a valid uppercase canonical residue. Malformed direct construction fails closed. These revised direct-construction invariants do not change any normal formal-evaluator result: the Exact22 truth cases remain byte-equivalent.

The deterministic evidence set contains 22 synthetic evaluator cases, 24 non-duplicate contract rows, a 12-source boundary audit, the unchanged Phase 4 Exact11 issue inventory, a safety audit, and a manifest. Tests and the checker independently combine the frozen `classify_admit_004_admit_005_atom_scope_design` and `validate_generic_covalent_residue_atom_name` helpers as the semantic oracle. The production evaluator neither imports nor calls those helpers.

Candidate projection and context routing contracts are not frozen. The unified adapter is not implemented, ADMIT_005 is not registered, and ADMIT_006 through ADMIT_015 remain unregistered. Combined candidate verdict and cross-rule precedence are not implemented. No real candidate or Exact11 evaluation, provider/parser execution, raw read, network access, download, checkpoint access, model execution, or training occurred.

Bulk download and training remain prohibited. Before any formal training or training-preparation work, a feature-semantics audit remains required; the historical Step12D result was a smoke legality check, not a final training-feature contract, and the historical `UNKNOWN_ATOM_FEATURE_POLICY` / `feature_semantics_known=False` state must be resolved or formally audited.

The recommended next step is `design_covapie_admit_005_unified_adapter_contract_v1`.
