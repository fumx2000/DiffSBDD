# CovaPIE Current11 warhead atom-set and attachment-boundary review packages v1

This successor packages the immutable Current11 proposal evidence for later,
real human review. It does not perform review and does not select a primary
candidate.

The materialized evidence contains 11 sample-specific candidate-set
identities, all 200 source bridge candidates as review options (185 eligible
and 15 ineligible), 11 blank `not_reviewed` review-record templates, and 11
package-index rows with contiguous option spans. Candidate-set identities bind
the sample and proposal identities to ordered full and admitted candidate SHA
lists. They do not replace bridge-candidate identities.

The human review-record contract supports `not_reviewed`,
`select_admitted_candidate`, `revise_atom_set_and_boundary`, and `quarantine`.
Only synthetic test records exercise completed decisions. Formal templates
contain no selection, reviewed atoms, boundary values, reviewer, rationale,
notes, or human review-record SHA. The package index records a separate
unreviewed-template payload SHA solely for template-integrity checking.

The transaction fails closed: any global input, identity, ordering, graph,
review-dependency, or downstream-readiness failure leaves the options,
templates, and package-index tables header-only. The Exact38 mutation matrix
exercises that behavior.

No complete warhead atom-set authority or exact-one attachment-boundary
authority is established. SMARTS, approvals, role annotations, minimal seed,
the five canonical masks, tensorization, model integration, and training
remain closed. Planned/integrated covalent modules remain 5/0.

The primary next manual action is real human review of these warhead
atom-set/attachment-boundary packages. In parallel, the already-materialized
family-topology and sample-assignment packages still require real human
review. The recommended engineering successor is
`design_covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_v1`.

Formal training remains blocked on a separate feature-semantics audit.
Step12D was a smoke legality check, not a final training-feature contract.
