# CovaPIE Step14AU-E1-E1 summary

This successor design gate freezes the ADMIT_004 generic atom identity and
identity-evidence-context reconciliation contract. It does not change the E1-D
effective rule, field, or context matrices.

## Historical conflict

The frozen exact16 evidence directly shows that E1-D describes ADMIT_004 as
`rule_logic_ready`, gives it nine candidate dependencies, and gives it only the
`covalent_residue_identity_contract` evaluation context. The shared
`covalent_residue_atom_name` field still says `must be SG for v1 Cys scope` and
is used by both ADMIT_004 and ADMIT_005. E1-A implements that leakage by
accepting only exact `SG` in `validate_covalent_residue_atom_name` and calling
that helper from the ADMIT_004 identity evidence design.

P4 independently defines `matched_residue_atom_name` as an exact-preserved
ASCII identifier without an SG requirement. Step14AT identifies ADMIT_004 as
residue identity and ADMIT_005 as `cys_sg_scope_only_v1`. E1-E1 therefore
retains the historical E1-D claim as read-only evidence while recording the
new blocking reconciliation issue.

## Frozen generic atom and scope contracts

`validate_generic_covalent_residue_atom_name` accepts only exact `str` values,
rejects subclasses, empty values, non-ASCII values, whitespace at any position,
and complete `.` or `?` markers. It performs no trim, coercion, case conversion,
Unicode normalization, canonical rewrite, or semantic maximum-length check.
Successful values are preserved exactly. Examples include `SG`, `CA`, `ca`,
`N1`, `OXT`, `C1'`, `A.B`, and `+`.

`classify_admit_004_admit_005_atom_scope_design` freezes the responsibility
split without implementing an admission evaluator. A grammar-valid residue and
generic atom pass the atom portion of ADMIT_004. ADMIT_005 passes only when the
canonical residue is `CYS` and the exact atom is `SG`; otherwise valid inputs are
rejected by ADMIT_005. Malformed residue or atom inputs are invalid for both.
ADMIT_004 never returns `rejected` from this design helper.

E1-E1 reuses the committed E1-C insertion present-value grammar character for
character. `/` remains valid, while `\\` and `=` remain invalid; this gate must
neither expand nor narrow the frozen E1-C character set.

## Frozen evidence-context contract

The future interface remains conceptually:

```text
evaluate_admit_004(candidate_record: Mapping[str, object],
                   evaluation_context: Mapping[str, object])
```

E1-E1 does not implement that function. It freezes a pure design classifier.
The top-level context accepts `Mapping` implementations and unrelated unified
engine keys, but requires `covalent_residue_identity_evidence_context`. The
nested mapping has exactly six keys:

1. `schema_version`
2. `attested_candidate_fields`
3. `provider_evidence_outcome`
4. `provider_evidence_reason`
5. `four_way_present_value_exact_equality_attested`
6. `present_value_quote_class_roundtrip_verified`

The schema version is
`covapie_covalent_residue_identity_evidence_context_v1`. The attestation mapping
contains exactly the nine ADMIT_004 dependencies in their E1-D order and binds
each exact string to the raw candidate field value before any canonicalization:

1. `covalent_residue_name`
2. `covalent_residue_chain_id`
3. `covalent_residue_index`
4. `covalent_residue_atom_name`
5. `covalent_residue_locator_namespace`
6. `covalent_residue_insertion_code_state`
7. `covalent_residue_insertion_code`
8. `covalent_residue_locator_provenance_source_id`
9. `covalent_residue_locator_provenance_sha256`

The provider outcome is exact `passed`, `blocked`, or `invalid`. A passed
outcome requires an empty exact-string reason; blocked and invalid require a
nonempty ASCII exact-string reason. Both attestation flags require exact bools.
For present insertion values, false four-way equality or quote-class roundtrip
blocks. These flags do not promote absent or unknown states to present.

A completely missing evidence-context key is blocked with
`ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_MISSING`. Any malformed top-level or nested
context, schema, key set, attested field set/value, binding, provider
outcome/reason, or bool is invalid. The frozen precedence is
`invalid > blocked > passed`; malformed context therefore remains invalid even
for an unknown candidate. Among valid blocked conditions, unknown provenance
comes before missing context, provider blocking, present four-way attestation,
and present quote-class verification.

## Evidence and readiness

The truth matrix contains exactly 36 passing rows: 8 generic valid, 8 generic
invalid, 8 ADMIT_004/ADMIT_005 scope, and 12 evidence-context binding cases. The
nine E1-D issues are copied byte-for-field and in the same order, followed by
one new blocking issue:
`ADMIT_004_GENERIC_ATOM_AND_EVIDENCE_CONTEXT_SEMANTICS_UNRESOLVED`. The real
provider blocker remains open with count 11, and Exact11 remains 11/11 blocked.

The design is ready only for
`integrate_covapie_admit_004_generic_atom_identity_evidence_context_reconciliation_v1`.
The reconciled interface is not implementation-ready; the effective context has
not gained a row; no evaluator, unified rule engine, candidate/admission record,
parser/provider execution, provenance dereference, raw read, network/download,
checkpoint access, model execution, or training occurs. Quote-class roundtrip
and real-provider present-value readiness remain false. Candidate evaluation,
bulk download, and training remain disallowed. A feature-semantics audit is
still required before formal training; Step12D was a smoke legality check, not a
final training-feature contract, and the historical unknown feature-semantics
state remains a training prerequisite.
