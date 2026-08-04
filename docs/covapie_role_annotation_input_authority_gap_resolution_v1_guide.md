# CovaPIE role annotation input authority gap resolution V1

This increment is a metadata-only, read-only Current11 authority audit. It does
not generate scaffold/linker/warhead roles or minimal seeds. It does not create
review packages, tensors, sidecars, loader data, or training inputs.

The only public API is keyword-only:

```python
evaluate_covapie_role_annotation_input_authority_gap_resolution_v1(
    *, repo_root: Path
) -> dict[str, object]
```

## Authority result

The nine proposal-input dimensions use the closed statuses
`authoritative_resolved`, `candidate_only`, `missing`, `conflicted`, and
`not_applicable`. The Current11 audit resolves retained-heavy mapping, both
reactive atoms, pre-reaction connectivity, pre-reaction bond orders, and the
Murcko/BRICS method inputs for all 11 samples.

Reaction-family and warhead-rule IDs exist for all samples, but their committed
source explicitly calls them machine-derived, unreviewed candidates. The rule
registry also says `approved=false` and that approved SMARTS were not
materialized. Both dimensions therefore remain `candidate_only`; candidate IDs
are retained for lineage but do not count as ready authority.

The pre-reaction graph is the connected ligand-internal graph projected to
`retained_heavy_local_index_0based`. Every projected edge has committed
normalized bond-order evidence using the actual per-sample subset of
`single`, `double`, `triple`, and `aromatic`. Connectivity and bond-order
readiness are validated independently.

## Review boundary

The SHA-bound unified effective authority view proves 11/11 completed and active
warhead atom-set/attachment-boundary reviews (six legacy exact-one plus five
multi-boundary exact-two). This is not role/minimal-seed gold review. Role/seed
gold review remains 0/11 and is not a proposal input, although it is required
later for `gold_curated`, mask materialization, and training authority.

Murcko and BRICS are not executed. Their 11/11 method-input readiness means only
that the authoritative atom-indexed graph, bond orders, mapping, and legal
component are available. Murcko remains proposal-only and BRICS remains
supporting-only under the frozen predecessor contract.

## Readiness and next increment

Because two of the seven core dimensions remain candidate-only, role-proposal
input readiness and minimal-seed input readiness are both 0/11. No proposal,
role, seed, tensor, or review package is generated. The fail-closed next step is:

```text
bind_covapie_current11_reaction_family_and_approved_warhead_rule_authority_v1
```

That future step must separately approve sample-level reaction families and
fully specified warhead rules; it must not promote the current candidate table
by renaming statuses.

## Safety and lifecycle

The gate reads committed text blobs and two formal state JSON files whose
transport SHA256 values are bound by committed source. It does not access raw
structures, the network, RDKit, topology restoration, Murcko, BRICS,
checkpoints, model forward paths, training, reward, or RL. It supports exactly
`authority_precommit_candidate`, `authority_committed_unpushed`, and
`authority_published_successor`, including separate index and actual-worktree
blob verification. Both the checker and the complete targeted test suite accept
all three profiles. The live-tree test independently reads HEAD, origin/main,
ahead/behind, tracked and staged diffs, ordinary untracked files, and porcelain
status. After the formal commit exists it also verifies its subject, single
BASE parent, Exact9 added paths, `100644` modes, and equality of commit, index,
and actual-worktree blobs. A published authority commit may remain valid below
future unrelated successors of HEAD and origin/main.

## Fail-closed validation

The 36-row failure matrix is bound to a data-driven mutation registry. Every
X01--X36 case has a unique mutation signature, one of the `matrix`, `response`,
`lifecycle`, or `execution_boundary` validator targets, and a real pytest
parameter node. The evaluator and tests validate each clean baseline, apply the
registered mutation in memory, prove that its canonical bytes changed, and
require the shared error contract. Case coverage therefore comes from executed
semantic mutations, not from test-node names alone.

The matrix validator checks Exact11 ordered sample identity, all nine authority
status fields, mapping and reactive-atom identities, retained-index graph
semantics, connectivity and bond-order separation, candidate family/rule
pairing, Murcko/BRICS input readiness, the separation of warhead review from
role/seed gold review, core-gap readiness closure, and the absence of proposal
or materialization overclaim. Graph mutation cases additionally validate
explicit in-memory endpoints for self-loops, duplicate edges, index range, edge
count, and connectedness.

The response validator recomputes matrix coverage, review and readiness counts,
Murcko/BRICS counts, unresolved core dimensions, and completion state. It also
cross-validates Exact3 lifecycle fields, Exact36 failure evidence, Exact5
generated evidence paths, the next-increment recommendation, all execution and
training safety booleans, fixed field order and scalar types, and the SHA256 of
the unsigned canonical response. Its Exact8 lifecycle projection is additionally
bound to an external witness built from the evaluator's Git-derived origin,
ahead/behind counts, and formal lifecycle result before the response exists. A
syntactically valid replacement authority SHA, origin SHA, or divergence count
is rejected even after recomputing the response digest. Recomputing a digest
after changing any other critical field likewise does not make the response
valid.

Formal training still requires the feature-semantics audit. Step12D was a smoke
legality check, not a final training-feature contract; historical unknown-atom
semantics must remain formally audited before training.
