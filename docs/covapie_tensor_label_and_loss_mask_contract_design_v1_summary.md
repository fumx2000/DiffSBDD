# CovaPIE Tensor, Label, and Loss-Mask Contract Design V1

## Scope and outcome

This step is a BASE-bound, metadata-only contract design. It materializes no
training tensor or NPZ, reads no raw structure or checkpoint, and changes no
dataloader, model, forward path, loss, or training code.

The decision is `designed_with_blockers`. The pair candidate, positive-label,
deterministic-negative, and pair-loss-mask policy is frozen. The complete
condition/task-mask contract remains blocked because the current 11 committed
samples contain no per-atom scaffold/linker/warhead assignments and no
minimal-seed/anchor locator. The geometry/auxiliary-label contract remains
blocked because the current 11 contain no warhead-type labels and expose only
post-covalent bond distance, not a complete pre/post/delta geometry authority.

## Checkpoint and sidecar boundary

The existing checkpoint input remains:

- ligand categorical `float32 [N_ligand,10]`;
- pocket categorical `float32 [N_pocket,10]`;
- ligand coordinates `float32 [N_ligand,3]`;
- pocket coordinates `float32 [N_pocket,3]`;
- ligand batch membership `int64 [N_ligand]`;
- pocket batch membership `int64 [N_pocket]`.

All newly designed covalent tensors are sidecars. They are not concatenated to
the checkpoint 10D categorical features. A future adapter is required.

## Exact index spaces and flattening

The Exact6 spaces are:

1. `source_full_atom_row_index_0based`
2. `retained_heavy_local_index_0based`
3. `flattened_ligand_index_0based`
4. `flattened_pocket_index_0based`
5. `pair_candidate_index_0based`
6. `batch_sample_index_0based`

`ligand_node_offsets`, `pocket_node_offsets`, and
`pair_candidate_offsets` are `int64 [B+1]`. They start at zero, are monotone
nondecreasing, and terminate at the corresponding flattened node or global
pair-candidate count. For each sample:

```text
pair_candidate_offsets[b+1] - pair_candidate_offsets[b] =
retained_ligand_count[b] *
target_residue_retained_heavy_count[b]
```

The BASE-derived current11 arrays are:

```text
ligand_node_offsets =
[0,13,26,39,64,92,135,177,219,262,302,323]

pocket_node_offsets =
[0,66,170,266,474,662,940,1207,1464,1713,1974,2202]

pair_candidate_offsets =
[0,78,156,234,384,552,810,1062,1314,1572,1812,1938]
```

```text
flattened_ligand_index =
ligand_node_offsets[batch] + retained_ligand_local_index

flattened_pocket_index =
pocket_node_offsets[batch] + retained_pocket_local_index
```

Source full-table indices may be used only by the metadata projection and may
not enter a model or loss. Every per-atom field uses the same post-H-filter
source-to-retained-heavy map. Sentinel `-1` requires a separate boolean
validity mask; zero is always a valid zero-based index and never means missing.

## Exact5 canonical task IDs

| ID | Long semantic name | Display alias | Target role regions | Context role regions |
|---:|---|---|---|---|
| 0 | `warhead_only` | A | warhead | scaffold, linker |
| 1 | `linker_plus_warhead` | B | linker, warhead | scaffold |
| 2 | `scaffold_plus_warhead` | B2 | scaffold, warhead | linker |
| 3 | `scaffold_only` | B3 | scaffold | linker, warhead |
| 4 | `scaffold_plus_linker_plus_warhead` | C | scaffold, linker, warhead | minimal seed/anchor override |

The dynamically frozen role vocabulary order is
`0=scaffold, 1=linker, 2=warhead`, derived from the committed long-form mask
helper signature. Long semantic names are authoritative; aliases are display
only.

For every admitted sample, `generation_mask == target_mask`,
`fixed_mask == context_mask`, and target/context must be disjoint and
exhaustive over retained ligand heavy atoms. In task C, a committed minimal
seed/anchor must remain context. Because current11 has neither per-atom role
assignments nor a minimal-seed/anchor authority, these mask tensors are
`designed_with_blocker` rather than fabricated.

## Condition sidecars

The target-residue sidecars are:

- `target_residue_membership_mask: bool [N_pocket,1]`;
- `target_residue_reactive_atom_mask: bool [N_pocket,1]`;
- reactive local and flattened indices `int64 [B]`;
- `target_residue_condition_valid: bool [B]`.

For the current 11 samples, each target residue is CYS with six retained heavy
atoms and its remapped SG is exact-one, retained, and inside the membership
mask.

`ligand_anchor_distance_angstrom: float32 [N_ligand,1]` is the Euclidean
distance, after H filtering, from each retained ligand heavy atom to the
target-residue reactive atom. It is in angstrom, invariant to joint centering,
and paired with `ligand_anchor_distance_valid`.

## Pair candidate, positive, and negative policy

Within each sample, the candidate domain is:

```text
all retained ligand heavy atoms
×
all retained heavy atoms of the specified target residue
```

Enumeration is deterministic: sample order, then ligand retained-heavy local
index ascending, then target-residue pocket-local retained-heavy index
ascending. The current11 metadata yields 1,938 candidates. All 11 samples have
exactly one remapped positive pair and at least one negative.

`pair_candidate_residue_local_index` is the pocket retained-heavy local index
within the whole sample. It is not the `0..R_b-1` ordinal of an atom inside
the target-residue membership list. That target-residue member ordinal is used
only to determine enumeration position; it is not a model tensor and does not
create a seventh formal index space.

For every candidate:

```text
pair_candidate_pocket_flat_index =
pocket_node_offsets[batch] + pair_candidate_residue_local_index
```

For the unique positive in sample `b`:

```text
pair_positive_candidate_index[b] =
pair_candidate_offsets[b] +
positive_ligand_local_index[b] * R_b +
positive_target_residue_member_ordinal[b]
```

The metadata-only builder reconstructs and validates all 1,938 records, both
local-to-flat relations, Exact11 positive global indices, and Exact11
positive/negative counts.

Pair-head candidate construction also permits the degenerate but valid domain
with exactly one positive candidate and zero negatives. The positive remains
valid and eligible for pair-head supervision; only
`pair_contrastive_sample_loss_mask` becomes false. A zero-negative sample is
not rejected by the pair projection builder.

Pair positive and negative counts require exact Python `int` values and must
be nonnegative. A negative positive count reports
`positive_pair_count_negative`; a negative negative count reports
`negative_pair_count_negative`. A negative count is invalid regardless of
whether the contrastive sample loss mask is enabled. Zero negatives remain
legal when contrastive supervision is disabled, while enabling contrastive
supervision with zero negatives only disables that contrastive sample mask.

Every same-sample non-positive candidate is a negative. Cross-sample
negatives, random subsampling, hard-negative mining, full-pocket candidates,
H, padding, and rejected samples are forbidden.

Canonical generation masks, pair-label availability, pair-head candidate loss
masks, and pair-contrastive sample loss masks are distinct contracts. The
contrastive sample mask is true only when the sample is admitted, has exactly
one positive, has at least one negative, and all indices are valid.

## Executable fail-closed scenarios

The 40-row failure matrix is produced from explicit dataclass state mutations.
Each case replaces one or more fields on a common baseline scenario, runs the
lower checkpoint/sidecar, task-mask, target-residue, pair-policy, geometry,
and auxiliary-label validators, and records its distinct mutation signature,
expected primary reason, and observed reasons.

The scenario dataclass has no `failure_case` field. No validator receives a
case-name string and no string-driven fallback returns `invalid`. Every row
must observe `invalid`, detect its expected reason, keep all readiness flags
false, and fail closed.

The separate 16-row pair-policy matrix is likewise built from an explicit
`PairCandidatePolicyScenario` baseline plus state mutations. Valid positive
and negative candidates remain allowed; invalid domains, indices, counts,
ordering, or negative policies are rejected from their actual state.

All Python integer indices and counts in `PairCandidateSampleSpec`, the
top-level contract scenario, and the pair-policy scenario require exact
`int` values. Because Python `bool` is an `int` subclass, ordinary
`isinstance(value, int)` is insufficient here: `True` and `False` are
explicitly rejected and cannot stand in for index/count values 1 and 0.
Likewise, every boolean contract field requires exact `bool`, target-residue
membership must be a tuple, and every membership element must be an exact
`int`. Failure and pair-policy mutation registries are audited against their
baseline dataclass fields and exact scalar types before mutations execute.

The exact-int policy also covers every public index/count/task helper:
`validate_offsets_v1`, `flatten_local_index_v1`,
`validate_sentinel_with_validity_v1`, `canonical_task_regions_v1`, and
`validate_pair_candidate_sample_spec_exact_types_v1`. Python booleans and
numeric-equal floats cannot serve as an offset terminal, offset element,
batch/local index, sentinel index, or canonical task ID. Malformed offsets
fail closed without leaking `TypeError` or `IndexError`, while the legitimate
zero index and the Exact5 task order, including `scaffold_only`/B3 at ID 3,
remain valid.

An offset container must be an ordered, repeatably readable `Sequence`.
Tuples, lists, ranges, and other stable ordered Sequence implementations are
accepted when their elements satisfy the exact-int offset rules. Dictionaries,
sets, iterators, generators, and binary containers (`bytes`, `bytearray`, and
`memoryview`) are rejected before conversion and cannot be normalized into a
valid offset sequence. `flatten_local_index_v1` applies the same container
rule before reading an offset and reports `offset contract invalid` for every
unordered or single-pass container.

## Warhead and geometry boundaries

The legacy schema names a `warhead_type` field, but no current11 committed
table carries a warhead-type value. Therefore the vocabulary is empty and
unfrozen, `warhead_type_id` uses `-1` only with
`warhead_type_label_valid=false`, and current valid coverage is 0/11. It is an
auxiliary task boundary, not a sixth covalent model module.

Geometry component 0 is
`post_covalent_positive_pair_bond_distance_angstrom`. It is a nonperiodic
scalar in angstrom with canonical range `[0,+inf)`, tied to the remapped
positive pair, and valid for 11/11 samples. Missing components must be masked,
never zero-filled into loss. No committed current11 authority freezes
pre-covalent geometry, geometry deltas, angles, or dihedrals, so the unified
geometry contract remains blocked.

## Issue result and next step

The three appended design issues are:

- condition/task-mask tensor contract: `open`;
- pair label/negative policy: `resolved`;
- geometry/auxiliary label contract: `open`.

Consequently:

```text
ready_for_tensor_materialization_smoke=false
ready_for_tensorization=false
ready_for_model_integration=false
ready_for_training=false
integrated_covalent_model_module_count=0
planned_covalent_model_module_count=5
```

The fail-closed next step is
`resolve_covapie_condition_and_task_mask_tensor_contract_gaps_v1`.
