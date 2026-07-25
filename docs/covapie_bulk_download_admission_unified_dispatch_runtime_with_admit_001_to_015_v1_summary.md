# CovaPIE unified dispatch runtime with ADMIT_001–015 v1

## Scope

This successor implements the `ADMIT_015` in-memory unified adapter, adds it
to an immutable Exact15 registry, and closes the ADMIT_001–ADMIT_015
single-rule dispatcher. It preserves the committed Exact14 runtime and all
other predecessor files unchanged.

The step does not implement mandatory training-authorization enforcement,
combined candidate verdicts, cross-rule aggregation, provider mapping,
network or download operations, feature-semantics resolution, training,
optimizer steps, or parameter updates.

The public runtime closure ends at:

```text
# === CovaPIE ADMIT_001 TO ADMIT_015 PUBLIC RUNTIME CLOSURE END ===
```

Before this marker the module depends only on the committed Exact14 runtime,
the committed ADMIT_015 standalone evaluator, the committed independent
formal-interface oracle, and Python in-memory type helpers. The adapter design
simulator is evidence-only and imported after the marker.

## Revised1 infrastructure hardening

The pre-commit `revised1` audit found three real post-traversal gaps without
changing any public runtime semantics. The production and checker source
readers checked the final leaf and then returned without one last
parent/root lexical and FD binding pass. The checker Exact6 reader likewise
had no final inventory or root/parent pass after its final leaf traversal.
Real root and parent replacement therefore let the old readers return bytes
from held old descriptors, and adding a seventh output during the last leaf
traversal escaped the old Exact6 inventory checks.

The revised source sequence is now read/leaf verification, complete
parent/root verification, final leaf verification, and final complete
parent/root verification, with every descriptor retained and six-field
identities used throughout. The checker Exact6 reader retains all six leaf
descriptors and performs initial, second, and final inventories plus final
root/parent binding after its final leaf pass.

The previous lifecycle check scanned only the immediate `src`, `scripts`,
`tests`, and `docs` children. A nested ignored same-stage file was absent from
Git's nonignored inventory and from that top-level scan. The replacement is a
bounded recursive `lstat`/`scandir` scanner that never follows symlinks,
rejects nested ignored or tracked stage-family paths, enforces the recursive
Exact10 allowlist, and inspects only matching first-level derived roots.

Finally, the checker now independently reconstructs the complete Manifest and
recursively compares exact Python types, dict key order, list order, nested
objects, and scalar values. Synchronized Manifest/SHA changes can no longer
bypass partial semantic checks. The Manifest records the source-read,
output-read, and recursive-lifecycle policies. Contract, Truth, Registry,
Safety, Issue, public marker, public Exact11 AST, handler, registry, dispatcher,
PRE transition, and coverage transition remain unchanged.

## Runtime closure

- The shared Exact13 result type, dispatch error type, field tuples, error
  codes, and outcome vocabulary are direct predecessor object re-exports.
- The first fourteen registry handler values preserve exact object identity.
- `EVALUATOR_REGISTRY`, `RULE_NAMES`, and `ADAPTER_IDS` are immutable
  `MappingProxyType` objects ordered from `ADMIT_001` through `ADMIT_015`.
- The registry contains exactly fifteen rules, with no duplicate and no
  `ADMIT_016`; there is currently no known-but-unregistered canonical rule.
- The dispatcher preserves its predecessor signature and error precedence and
  evaluates exactly one selected rule.
- The legacy `NOT_REGISTERED` and `ADAPTER_NOT_READY` error paths remain in
  the shared dispatcher contract but are unreachable for the canonical
  Exact15 set.

The formal ADMIT_015 handler:

1. rejects forbidden batch, evaluation, and download-result contexts before
   inspecting the candidate;
2. validates the standalone Exact9 source;
3. calls the independent oracle exactly once only after source validation;
4. requires exact field type and value equality across the full formal and
   oracle Exact9 results; and
5. projects the validated Exact9 value to the shared Exact13 result.

A valid candidate mapping is not accessed. The identical stage context is
forwarded to the formal evaluator and oracle. Stage booleans project to the
lowercase strings `"false"` and `"true"`, and stage fields never leak into
candidate fields.

## Evidence

The ordered Exact20 source boundary is verified against the frozen base Git
tree, current stage-0 index, Git blob bytes, pinned filesystem bytes, and
frozen SHA256 values before candidate or output evidence is accepted.

The Exact6 evidence is:

| File | Rows | SHA256 |
| --- | ---: | --- |
| `covapie_admit_001_to_015_runtime_contract.csv` | 45 | `b6606d4111b7493e4b8cd531fb88c5281b5a685369788b85742b5e85d721a465` |
| `covapie_admit_001_to_015_dispatch_truth_matrix.csv` | 79 | `f93a43cfa560d495ea7e14fca26a957c6eb087907cbfde91d7456d1a55440abb` |
| `covapie_admit_001_to_015_registry_and_identity_audit.csv` | 27 | `eac4ea16fbd2193c3b53f8d6bdf11728f086a499390bba7c33e1e3d2e61cc75e` |
| `covapie_admit_001_to_015_runtime_safety_audit.csv` | 32 | `50db14b8d823c162e694a74abaa5a9189006f54d6cb6716d6ad9406f509a05b2` |
| `covapie_admit_001_to_015_runtime_issue_readiness_inventory.csv` | 30 | `c8ea16e335e43ed781bb5177e1aba0247a55714f55eeb5caf8bed23a539f431d` |
| `covapie_admit_001_to_015_runtime_manifest.json` | n/a | `0fbd5999977d025a44b4bef854d9edfda5ea0e5ed79a7d5ff7b17cef7b6186d3` |

The Exact79 truth matrix contains exactly:

- 42 inherited adapter runtime cases;
- 11 standalone-source negative cases;
- 8 independent-oracle negative cases;
- 4 public-dispatch cases; and
- 14 representative predecessor dispatches.

All observations are produced by executing the real runtime. The checker owns
independent expected scenarios and semantics, reconstructs Exact45, Exact79,
Exact27, Exact32, and Exact30 after frozen SHA verification, and rejects
synchronized candidate/output/Manifest tampering.

## Preconditions and issue transition

Only `PRE_032` and `PRE_033` are resolved. The successor precondition state is
40 complete, 0 supported-but-not-frozen, 5 incomplete, and 5
implementation-blocking. The remaining open IDs are:

```text
PRE_034 PRE_035 PRE_036 PRE_038 PRE_042
```

The inherited `UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE` row keeps its
historical identity and inherited status `open`, while the successor
effective status becomes `resolved`. Its successor `affected_fields` and
`affected_rules` are empty, with transition action
`admit_015_removed_from_open_unified_runtime_coverage` and evidence
`Exact15_registry_and_unified_single_rule_dispatch`. No other issue row is
changed.

## Materialization and lifecycle

Evidence is fully built before mutation. Publication uses exclusive leaf
creation, leaf and directory `fsync`, pinned descriptors, double inventory,
double all-leaf traversal, parent/root/staging lexical binding checks, and
`RENAME_NOREPLACE`.

`EINVAL` and `EEXIST` fail closed. Before publication, a failure retains the
owned staging set and reports an authenticated retained path only if both the
parent and staging lexical bindings still match their frozen full identities.
If either binding is lost, the last-known staging name is explicitly not
treated as authority. The failure path performs no `unlink`, `rmdir`,
`os.replace`, or recursive cleanup and never deletes a foreign object. An
existing exact set is an inode-preserving no-op.

### Revised2 generic-symlink lifecycle hardening

1. Revised1 still skipped generic symlinks whose names contained no
   stage-family token.
2. Real tracked and ignored generic symlinks both bypassed that lifecycle
   scan.
3. The cause was applying the name filter before symlink rejection.
4. The revised scanner now performs a no-follow stat and rejects every
   symlink entry before applying the name filter.
5. It does not follow or read the symlink target.
6. Production and the complete Exact6 remain byte-identical.
7. Public runtime business semantics are unchanged.

### Revised3 pinned-recursion lifecycle hardening

1. Revised2 closed only the pre-existing generic-symlink case.
2. A TOCTOU window remained between no-follow stat and path-based recursion.
3. A real directory-to-symlink replacement made the old scanner follow the
   external target.
4. The old lifecycle still returned `pre_commit` after that replacement.
5. The revised scanner opens from a pinned repository-root FD and uses
   `O_NOFOLLOW` for every directory component.
6. Recursive traversal uses only held child directory FDs.
7. Directory inventory plus lexical and FD identities are revalidated after
   recursion.
8. Lifecycle completion revalidates Exact10 full identities and Git
   inventory.
9. This does not claim an atomic whole-repository snapshot.
10. Production, Exact6, Manifest, and public runtime semantics remain
    byte-identical.

### Revised4 HEAD-snapshot lifecycle hardening

1. Revised3 closed the FD-recursion and directory-replacement races.
2. The initial and final lifecycle states still omitted the HEAD commit.
3. A real allow-empty commit changes HEAD without changing the tree, index,
   Exact10 identities, untracked inventory, or clean working-tree state.
4. The old lifecycle therefore still returned `pre_commit` or `post_commit`
   after that HEAD drift.
5. The revised lifecycle freezes the initial HEAD commit and compares it
   exactly with the final HEAD commit.
6. BASE ancestry is checked against both the initial and final HEAD commits.
7. HEAD need not equal BASE, preserving stable descendant-base `pre_commit`
   states and detached-candidate `post_commit` states.
8. This does not claim an atomic Git or whole-repository snapshot.
9. Production, Exact6, Manifest, and public runtime business semantics remain
   byte-identical.

## Safety and readiness boundary

`current_permission` is false and the authorized ADMIT_015 training execution
count is zero. Unified single-rule runtime coverage is complete, and the
successor is ready only for design of the mandatory training-authorization
enforcement contract. It is not ready for bulk download, real provider
evaluation, training, or real parameter updates.

The canonical V1 masks remain exactly:

1. `warhead_only` / `A`
2. `linker_plus_warhead` / `B`
3. `scaffold_plus_warhead` / `B2`
4. `scaffold_only` / `B3`
5. `scaffold_plus_linker_plus_warhead` / `C`

A feature-semantics audit is still mandatory before training. Step12D was a
smoke legality check, not the final training-feature contract; historical
`UNKNOWN_ATOM_FEATURE_POLICY` and `feature_semantics_known=False` remain
unresolved.

Recommended next step:

```text
design_covapie_admit_015_mandatory_training_authorization_enforcement_contract_v1
```
