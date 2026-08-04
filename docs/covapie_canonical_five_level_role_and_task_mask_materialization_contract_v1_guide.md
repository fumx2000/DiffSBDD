# CovaPIE canonical five-level role/task-mask materialization contract V1

## Scope and fixed baseline

This increment resolves one semantic blocker only:

```text
authority
  → canonical five-level role/task mask materialization contract  ← this step
  → real role/seed/anchor authority
  → tensor sidecar materialization
  → loader / collate
  → model consumption
  → loss
  → supervised training
```

The gate is bound to `main` at
`540be2e4162b2b6a7f1090d41f852e5ac87be459`, whose subject is
`add CovaPIE five-module training-path completion gap audit v1`.
The contract survives exactly three repository lifecycle profiles:

```text
contract_precommit_candidate
contract_committed_unpushed
contract_published_successor
```

The precommit profile requires `HEAD == origin/main ==` that base, `0/0`, and
exactly nine ordinary-untracked candidate files. The formal contract commit
must have that base as its only parent, add exactly the same nine regular
`100644` blobs, and use this exact subject:

```text
add CovaPIE canonical five-level role and task mask materialization contract v1
```

The committed-unpushed profile requires that commit at `HEAD`, `origin/main`
at the base, `1/0`, and a clean repository. The published profile requires the
same formal commit to be an ancestor of both `HEAD` and `origin/main`, with no
later commit modifying any candidate path. Unrelated future successors are
allowed. For every tracked candidate, the evaluator separately requires the
index blob and the blob hashed from actual worktree bytes to equal the formal
commit blob. Tracked live identity is taken from actual worktree bytes, not
inferred from the index alone; an assume-unchanged-style hidden worktree drift
therefore fails closed. Any other lifecycle fails closed.

The targeted tests independently read live `HEAD`, `origin/main`, divergence,
status, unstaged diff, cached diff, and ordinary-untracked paths, then validate
the matching profile. They also bind formal parent, subject, Exact9 `A` status,
mode, index blob, actual-worktree blob, and candidate-path drift, so the same
suite remains valid before commit, after a clean local commit, and after
publication beneath unrelated successors.

The evaluator is metadata-only and read-only. It does not import Torch, execute a
runtime provider, read a checkpoint or tensor archive, materialize a tensor,
run a runtime smoke, or change a loader, model, forward path, loss, or training
path. `commit_created=false` and `push_performed=false` report that the
evaluator itself performed no repository writes; they do not assert that the
contract can never be committed or published.

## Evidence actually bound by the gate

The source inventory binds 20 immutable `commit:path` blobs. It includes all
four current five-module gap-audit files, the tensor contract source plus its
registry, issue inventory, failure matrix and manifest, the feature-resolution
source and manifest, the Current11 auxiliary-readiness source and guide, the
current mask/schema/dataset/demo runtime, and the role/minimal-seed contract's
manifest, Current11 readiness matrix, and role/seed contract registry. The
registry's `LRMSC_002` row independently freezes a disjoint, exhaustive,
retained-heavy Exact3 partition with no H and all three roles nonempty.

The evaluator also checks the subjects and ancestry of the R1, R2 and R3 mask
migration/retirement commits:

```text
963562e2da9bcc14d67d075a49a7770aecaa2e68
8711c1899759ca4c1f4a24f7ff9782b81a257245
5974ded1dc1aa02a365a23e4a409b9a7fe98a4be
```

Historical evidence remains read-only. The gate never executes a retired
legacy stage and does not reintroduce the legacy four-level API.

## Primary role contract

The primary-role vocabulary is the closed Exact3 set:

| role id | semantic name |
| ---: | --- |
| 0 | `scaffold` |
| 1 | `linker` |
| 2 | `warhead` |

`anchor`, `minimal_seed`, `unknown`, and `padding` are not primary roles.
Minimal seed/anchor is an orthogonal condition flag.

Every admitted sample uses retained-ligand-heavy-atom local identity before
flattening. Scaffold, linker, and warhead atom sets must be duplicate-free,
nonempty, in-range, pairwise disjoint, and exactly exhaustive over the admitted
retained heavy atoms. Explicit H is excluded upstream and cannot enter the role domain.
The source full-atom row space is metadata-only and cannot enter a model or
loss as a retained-heavy index.

The per-atom sidecars are:

```text
ligand_role_id:    int64 [N_ligand]
ligand_role_valid: bool  [N_ligand]
```

The pair contract is exact: `valid=true` iff the role ID is `0`, `1`, or `2`;
`valid=false` iff the role ID is the `-1` sentinel. Booleans are never accepted
as IDs, lengths must match, and any other negative or greater-than-two ID fails
closed. Base generation/fixed masks are derived only when every row is valid;
no mask or loss atom can be created from an invalid row. For an admitted
role-authority sample every retained ligand heavy atom has one valid Exact3 role.
A warhead complement does not separate scaffold from linker,
and a ligand-internal attachment boundary is not a complete role partition.
Heuristic or RDKit partitions can only become future candidate evidence.

## Exact5 base task truth table

Long semantic names are the only semantic authority. Aliases are display-only
and remain invalid as runtime inputs.

| task id | semantic name | alias | generated primary roles | fixed primary roles |
| ---: | --- | --- | --- | --- |
| 0 | `warhead_only` | A | warhead | scaffold + linker |
| 1 | `linker_plus_warhead` | B | linker + warhead | scaffold |
| 2 | `scaffold_plus_warhead` | B2 | scaffold + warhead | linker |
| 3 | `scaffold_only` | B3 | scaffold | linker + warhead |
| 4 | `scaffold_plus_linker_plus_warhead` | C | scaffold + linker + warhead | empty |

B2 and B3 are different contracts. B3 is mandatory. A sixth or seventh task
is forbidden. The evaluator parses the committed runtime AST and requires this
truth table to match `CANONICAL_MASK_SEMANTICS`,
`CANONICAL_MASK_SEMANTIC_TO_LEVEL`, and `LONG_FORM_MASK_COMPONENTS`.

## Task C resolution: base mask plus orthogonal condition

The ambiguity in the predecessor metadata contract is resolved as two layers:

```text
Task C base generation = scaffold + linker + warhead
Task C base fixed      = empty

Task C minimal seed/anchor = separate conditioning sidecar
```

The seed/anchor flag does not remove an atom from base generation, add an atom
to base fixed/context, alter current `lig_fixed`, become a fourth role, become
a sixth task, or redefine `LONG_FORM_MASK_COMPONENTS`. It also does not remove
the conditioned atom from active diffusion loss. A future loss exception would
require its own explicit contract.

The condition fields are:

```text
ligand_minimal_seed_or_anchor_mask:  bool [N_ligand,1]
ligand_minimal_seed_or_anchor_valid: bool [B]
```

Only Task C can use them. A/B/B2/B3 require an all-false mask and `valid=false`.
For Task C, `valid=true` requires at least one retained ligand heavy atom and
`valid=false` requires the all-false mask. The final bundle validator checks
these relations independently, and seed selection cannot affect base masks or
active loss.
Primary roles are unchanged by seed selection. Without formal Current11
authority these fields remain unmaterialized and invalid for training use.

## Base masks and active diffusion loss

The canonical fields are:

```text
canonical_task_id:                  int64 [B]
canonical_task_valid:               bool  [B]
ligand_base_generation_mask:        bool  [N_ligand,1]
ligand_base_fixed_mask:             bool  [N_ligand,1]
ligand_base_target_mask:            bool  [N_ligand,1]
ligand_base_context_mask:           bool  [N_ligand,1]
ligand_active_diffusion_loss_mask:   bool  [N_ligand,1]
sample_training_admitted:            bool  [B]
```

Polarity is explicit: generation/target true means generated active base
region; fixed/context true means preserved base context. For every valid task:

```text
generation == target
fixed == base_context
generation ∩ fixed = empty
generation ∪ fixed = every retained ligand heavy atom
target ∩ base_context = empty
target ∪ base_context = every retained ligand heavy atom
```

The existing runtime uses rank-one integer `lig_fixed` with `1=fixed` and
`0=generated`. A future adapter must explicitly apply:

```text
lig_fixed = ligand_base_fixed_mask.squeeze(-1).cast(int64)
```

This step records but does not implement that adapter.

Generation is not an unconditional loss mask. V1 freezes:

```text
ligand_active_diffusion_loss_mask
  = ligand_base_generation_mask
    AND ligand_role_valid
    AND canonical_task_valid
    AND sample_training_admitted
```

Fixed atoms and invalid samples cannot contribute. Padding is false but padding
is not label availability. The current flattened contract admits no padding
rows.

## Anchor-distance reference

The existing production field is not renamed in this step:

```text
ligand_anchor_distance_angstrom: float32 [N_ligand,1]
ligand_anchor_distance_valid:    bool    [N_ligand,1]
```

Its canonical interpretation is
`ligand_to_target_reactive_atom_distance_angstrom`: Euclidean distance from
each retained ligand heavy atom to the target residue reactive atom. The unit
is angstrom and the frame is centering-invariant Euclidean distance. Validity
depends on target reactive atom availability.

It is not a distance to a ligand seed atom, scaffold anchor, or ligand-internal
boundary, and it is not a seed/anchor locator.

## Evidence-derived Current11 authority and readiness

Coverage is calculated from committed formal evidence, not treated as a task
prompt constant:

| authority | coverage | interpretation |
| --- | ---: | --- |
| warhead atom set | 11/11 | authority ready |
| ligand-internal warhead boundary | 11/11 | authority ready; not a ligand-protein pair |
| complete primary role assignment | 0/11 | incomplete |
| minimal seed/anchor | 0/11 | incomplete |

The role/minimal-seed manifest and all 11 readiness rows report no completed
Current11 role proposal plus human gold review and no completed minimal-seed
proposal plus human gold review. Therefore:

```text
role_task_mask_contract_resolved = true
primary_role_authority_complete = false
minimal_seed_anchor_authority_complete = false
base_task_masks_derivable = false                 # for real Current11 rows
synthetic_base_task_masks_derivable = true        # contract truth-table proof
real_role_task_mask_materialization_ready = false
canonical_mask_tensors_materialized = false
ready_for_tensor_materialization_smoke = false
ready_for_model_integration = false
ready_for_training = false
```

Contract resolution does not imply real tensor materialization.

## Checkpoint and feature-semantics boundary

The checkpoint categorical width remains 10 with the existing order:

```text
C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9
```

All new role/task/seed tensors are sidecars. They are not concatenated into the
10D atom feature. No model state dict changes and no checkpoint migration is
required by this contract.

The historical feature audit and unknown-atom policy resolution are complete.
Explicit H is excluded before the retained-heavy projection; unsupported
non-H atoms reject the sample fail closed; silent zero-vector fallback remains
forbidden. Runtime enforcement is not fully integrated, and final training
feature-semantics revalidation remains required after future loader/model
integration. Step12D was a smoke legality check, not a final training-feature
contract.

## API, artifacts, and fail-closed matrix

The only public evaluator is:

```python
evaluate_covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1(
    *, repo_root: Path,
) -> dict[str, object]
```

Imports are silent. The response has a fixed field order; its last field is the
SHA256 of canonical JSON for every preceding field. Two evaluations must be
byte-identical. All invalid states use one error contract:

```text
COVAPIE_CANONICAL_FIVE_LEVEL_ROLE_AND_TASK_MASK_MATERIALIZATION_CONTRACT_INVALID
```

Five evidence files are emitted as ordinary deterministic text: source
inventory, task truth table, field registry, 34-case failure matrix, and a
manifest. The manifest records SHA256 for the other four files and never its
own hash. It contains no timestamp or absolute path.

The failure matrix covers Exact5/B3/B2-vs-B3, aliases, fourth roles, partition
overlap/gaps/indices/H, index spaces and bool IDs, base-mask partition errors,
Task C base-fixed drift, seed-as-role/task or hidden `lig_fixed` override,
non-C seed use, authority overclaim, anchor-distance reinterpretation, active
loss violations, checkpoint-width concatenation, protected runtime changes,
execution-boundary crossing, and response integrity/determinism.
The final four cases additionally bind nonempty primary-role regions, exact
role-ID/validity sentinel pairs, independent seed-bundle validation, and a
commit-survivable Exact3 lifecycle. Response-integrity tests mutate critical
fields and recompute the digest; semantic cross-field validation still rejects
the tampered response.

## Next increment

The predecessor role/seed manifest explicitly reports both Current11 proposal
readiness values false, zero ready rows, and unresolved graph, bond-order,
reaction-family, approved-rule, gold-review, tensor-contract, and geometry
contract blockers. Therefore the next bounded direction is:

```text
resolve_covapie_role_annotation_input_authority_gaps_v1
```

This evaluator creates no commit and performs no push. In the current precommit
profile, the candidate stops for human commit review.
