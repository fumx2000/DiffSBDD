# CovaPIE Current11 warhead/boundary review ingestion gate design v1

This step freezes the future ingestion contract for the 11 materialized
warhead atom-set and attachment-boundary review packages. It does not perform
human review and does not create submitted review records, ingestion
envelopes, ingestion results, or authority records.

The current evidence remains:

- 11 review packages and 11 blank `not_reviewed` templates;
- 200 review options, of which 185 are review-eligible and 15 are ineligible;
- zero completed reviews, envelopes, ingestion results, authorities, or
  quarantined samples;
- zero candidate SMARTS, approvals, gold labels, or training labels.

The inherited review record remains Exact26. The future ingestion envelope is
Exact9, the future authority/disposition record is Exact27, and the future
ingestion result is Exact18. Their hashes use UTF-8 canonical JSON with sorted
keys, compact separators, and ASCII escaping. The submitted-record payload
digest includes all typed Exact26 fields, including the populated review
record digest. The envelope digest, authority digest, and result digest each
exclude only their own digest field.

Every ingestion call now requires a frozen in-memory authority context. Its
Exact4 record binds the context version, formal BASE commit, ordered Exact13
source-path/SHA pairs, and canonical context digest. The context carries the
exact `git show BASE:path` bytes and is revalidated on every use. Package
identity, options, proposals, assignments, and parent graphs are rebuilt only
after all 13 paths, bytes, hashes, ordering, and the context digest pass.
Caller-supplied authority maps are not part of the public interface.

Every completed decision performs an Exact14 identity join against that
validated BASE context before decision-specific validation. The join covers
version, unit, sample, PDB, ligand, class index and ID, family, rule,
proposal/assignment/candidate-set lineage, and both candidate counts.
Recomputing review, envelope, or forged-context digests cannot substitute
for the formal BASE bytes. Select options must be an exact-one eligible formal
option; revise uses the formal proposal and connected parent graph; quarantine
has no identity-validation shortcut.

Human provenance requires an explicit true attestation, a meaningful human
attestor identifier, and a meaningful source label. This is a provenance
declaration, not cryptographic identity verification. Automated reviewer and
attestor identifiers remain forbidden.

Future batches may contain 1–11 distinct samples and may be partial. Sample
identities and review-record digests must be unique within a batch. The batch
must also have exactly one meaningful `submission_batch_id`; mixed IDs fail
the entire batch before record validation. The batch is atomic: one invalid or
blocking item prevents every new authority effect.
Quarantine is a valid passed disposition. Exact replay of the same review is
idempotent only after the existing authority passes Exact27 schema/hash,
unique-sample, package-lineage, reviewer, decision-evidence, and
submitted-review semantic-equivalence validation. Existing select evidence
must match an exact-one eligible option; revise evidence must satisfy the
formal graph invariants; quarantine evidence must remain empty. Invalid
existing-authority sets fail closed before replay or conflict evaluation. A
different review for a sample with existing active or quarantined authority
is blocked. V1 has no supersession or silent overwrite.

Ingestion results expose only the frozen 31-code public reason vocabulary.
Internal exception details, field names, `KeyError` text, and Python
representations never become public reasons. Batch size, mixed batch ID,
duplicate sample, duplicate review digest, authority-context validation,
existing-authority validation, record validation, conflict, and atomic
rollback use a frozen Exact10 deterministic precedence and preserve input
result order. The reason/effect contract independently freezes valid passed,
blocked, and invalid combinations, including replay, conflict, consumption,
decision disposition, and authority SHA effects.

The design transaction emits a 20-row ingestion contract registry, a four-row
decision-effect matrix, an 11-row Current11 readiness matrix, and 51 frozen
typed fail-closed mutations. If either design phase fails, all three core
tables are header-only.

Design readiness and execution readiness are intentionally distinct:

- `review_ingestion_gate_design_completed=true`
- `ready_for_review_ingestion_interface_implementation=true`
- `ready_for_review_ingestion_execution=false`

Execution remains blocked because completed human review records and their
human-provenance envelopes do not exist. Review-package materialization is not
human-review completion; review completion is not admission; admission is not
authority materialization; authority materialization is not family, rule,
SMARTS, gold, or training approval.

The canonical mask contract remains exactly:

1. `warhead_only`
2. `linker_plus_warhead`
3. `scaffold_plus_warhead`
4. `scaffold_only`
5. `scaffold_plus_linker_plus_warhead`

No role, minimal seed, mask, tensor, model, or training artifact is created.
The planned/integrated covalent model module count remains 5/0. Formal
training still requires a feature-semantics audit, and Step12D remains only a
smoke legality check.

The recommended primary manual action is
`perform_real_human_review_of_current11_warhead_atom_set_and_attachment_boundary_review_packages`.
The parallel manual action remains
`perform_real_human_review_of_materialized_family_topology_and_sample_assignment_packages`.
The next engineering step is
`implement_covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1`.
