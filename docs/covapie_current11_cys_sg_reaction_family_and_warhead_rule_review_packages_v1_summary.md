# CovaPIE Current11 Cys-SG review packages v1

## Scope

This stage materializes evidence packages and blank record templates for later
review by real human reviewers. It does not execute or simulate human review.
It does not invent a reviewer, rationale, notes, decision, or SMARTS.

The immutable formal base is
`c0de1003ec1de9dd05e3c4204b458d1f3757d95d`. All 12 predecessor sources are
read with `git show BASE:<path>` and checked against frozen SHA256 values.

## Materialized contract

- Seven candidate-class source records use the exact 23-field
  `covapie_cys_sg_class_review_source_record_v1` contract.
- Each class source identity is the SHA256 of exact typed canonical JSON using
  sorted keys, compact separators, ASCII escaping, and UTF-8.
- Seven class review templates use the predecessor exact 19-field schema.
- Eleven sample review templates use the predecessor exact 13-field schema.
- Sample source identity remains the existing `assignment_record_sha256`; no
  second assignment identity is introduced.
- The package index contains 18 ordered rows: class indices 0 through 6,
  followed by sample IDs in ascending order.
- `unreviewed_template_payload_sha256` proves blank-template integrity only. It
  is not copied into `review_record_sha256` and is not a completed human-review
  record identity.

All templates remain `not_reviewed`, all reviewer metadata is exactly empty,
class SMARTS status remains `not_materialized`, candidate SMARTS is exactly
empty, and every `review_record_sha256` is exactly empty.

## Transaction and failure behavior

Phase A verifies the formal base, Exact12 source digests, predecessor
transactions, Exact7/Exact11 identities, links, assignment-record digests, and
the fully blank predecessor review state. Phase B verifies source records,
templates, the package index, ordering, digests, and readiness.

If either phase fails, the package index and both template CSVs are emitted
header-only together. The Exact36 typed mutation matrix verifies this
fail-closed behavior, including schema, exact-type, bool-as-int, ordering,
identity, partial-materialization, lifecycle, and downstream-readiness
boundaries.

## Readiness

The materialized evidence and blank templates make family identity, rule
topology, and sample assignment ready for real human review execution. Complete
human review is not ready because candidate warhead SMARTS has not been
materialized, so SMARTS review remains closed.

Reaction-family approval, warhead-rule approval, gold status, training-label
approval, role and minimal-seed generation, all five canonical masks,
tensorization, model integration, and training remain closed. Integrated
covalent model modules remain 0 of 5.

Recommended manual action:
`perform_real_human_review_of_materialized_family_topology_and_sample_assignment_packages`.

Recommended engineering next step:
`design_covapie_cys_sg_candidate_warhead_smarts_materialization_gate_v1`.
