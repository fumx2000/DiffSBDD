# CovaPIE Current11 warhead/boundary review-ingestion interface V1

## Scope

This increment implements a stable, pure in-memory interface over the
committed Current11 review-ingestion gate design. The committed design module
remains the sole authority for authority-context reconstruction, package and
graph validation, replay/conflict semantics, public reasons, batch atomicity,
and Exact18/Exact27 record semantics.

The interface adds:

- a fresh authority-context builder that reads the frozen design BASE Git
  objects directly and revalidates the resulting design context;
- a read-only public runtime repository guard that accepts the interface BASE
  and every descendant of that BASE;
- a frozen imported-design source guard that requires the worktree source and
  current HEAD blob to be byte-identical at the committed SHA256;
- an evaluator-local runtime attestation that infers the repository root from
  the imported interface module and repeats repository/design integrity checks
  before inspecting inputs or delegating ingestion;
- a keyword-only batch evaluator;
- a deterministic, self-excluding Exact6 response hash;
- independent response-level order, atomicity, replay, authority-linkage, and
  count validation;
- canonical deep input snapshots and post-call immutability checks.

Artifact construction remains strict to the four interface lifecycles:
`pre_commit`, `detached_candidate_post_commit`,
`formal_main_post_commit_unpushed`, and `formal_main_post_push`. It operates
directly from the current repository root. Public builder/evaluator runtime is
separately compatible with the interface BASE and all downstream descendants
whose imported design source remains frozen. It requires neither an exact
interface artifact lifecycle nor a second worktree pinned to the design or
interface BASE. Downstream callers must not use the lifecycle-strict interface
`build_result`. The lifecycle-bound design builder and design `build_result`
entry points are not called; the minimal synthetic evidence needed by this
interface is recovered internally from the validated committed-design context.

Both public entry points are protected. A context built while the source is
valid cannot be saved and later passed directly to the evaluator after either
committed or uncommitted design-source drift. The evaluator performs its
read-only attestation before input snapshots and before the single
`design.ingest_review_batch` delegation, so a failed attestation produces no
authority effect.

No external file path, caller-supplied authority map, raw payload, package map,
option map, proposal map, parent graph map, or valid-sample map is accepted by
the evaluator.

## Evidence

The interface transaction is grounded in Exact6 sources read from commit
`7e0f63d043b546480f66215c69af37253506c08a` through `git show`. Its evidence
contains Exact12 interface contracts, an ordered Exact18 synthetic truth
matrix, Exact11 Current11 readiness rows, and Exact35 frozen typed fail-closed
mutations.

The public runtime matrix verifies first- and second-level downstream
descendants in one worktree, including a valid quarantine submission with an
unchanged input snapshot, one new authority in memory, and zero filesystem
side effects. Unrelated history, committed or uncommitted design-source drift,
non-root repository paths, and missing required commit objects fail closed.

Review, envelope, result, and authority business payloads remain purely
in-memory. Runtime integrity is allowed to perform read-only Git ancestry,
HEAD-blob, and imported-source checks; it does not read review data or permit
filesystem persistence.

The synthetic truth outcomes are:

- passed: 4;
- blocked: 3;
- invalid: 11.

Synthetic review-shaped records, provenance envelopes, ingestion results, and
authority records remain in memory and are never written as lifecycle
artifacts.

## Current readiness boundary

Interface implementation is complete and synthetic interface evaluation is
ready. Real review ingestion execution remains closed because completed human
review records and human provenance envelopes do not exist, and real ingestion
has not been executed.

Actual lifecycle counts remain zero for completed reviews, provenance
envelopes, ingestion results, and authority records. Complete warhead atom-set
authority, exact-one attachment-boundary authority, quarantine state, candidate
SMARTS, family/rule/SMARTS approval, human gold, and training labels all remain
absent.

Role, minimal-seed, mask, tensor, model-integration, and training readiness
remain false. The canonical mask inventory remains exactly:

1. `warhead_only`
2. `linker_plus_warhead`
3. `scaffold_plus_warhead`
4. `scaffold_only`
5. `scaffold_plus_linker_plus_warhead`

Integrated/planned covalent model modules remain `0/5`.

Formal training still requires a feature-semantics audit. Step12D remains a
smoke legality check only and is not a final training-feature contract.

## Next actions

Primary manual action:
`perform_real_human_review_of_current11_warhead_atom_set_and_attachment_boundary_review_packages`.

Parallel manual action:
`perform_real_human_review_of_materialized_family_topology_and_sample_assignment_packages`.

Recommended engineering next step:
`design_covapie_current11_warhead_atom_set_and_attachment_boundary_review_submission_adapter_v1`.
