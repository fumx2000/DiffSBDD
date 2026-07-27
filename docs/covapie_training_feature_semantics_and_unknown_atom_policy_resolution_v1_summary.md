# CovaPIE training feature semantics and unknown-atom policy resolution V1

## Scope and BASE

This metadata-only successor is bound to commit
`5b2013281b03d7bd3e0c59b9985e52494263c69f` (`add CovaPIE final training
feature-semantics audit v1`). It resolves only
`UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED`. It does not modify atom tables, the
final dataset, NPZ data, dataloaders, model architecture, forward paths, losses,
or checkpoints, and it does not create tensors or perform training.

## Frozen categorical lineages

The checkpoint training config selects `dataset='crossdock'`, a
`processed_crossdock_noH_full` datadir, full-atom pocket representation, and
normalization factors `[1,4]`. The checkpoint-compatible categorical interface
therefore remains exactly:

```text
C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9
```

The 11-channel
`C|N|O|S|B|Br|Cl|P|I|F|others` adapter is frozen as preview/intermediate
evidence only and has no checkpoint-input authority. The historical Step12D
helper's silent all-zero row for unsupported atomic numbers is recorded as
observed smoke behavior, not as an allowed final-training policy.

## Resolved policy

Protein/pocket and ligand use the same high-level policy:
`fail_closed_rejection_required_for_checkpoint_compatibility`.

- An explicit `H` is excluded before the checkpoint model-bound node set is
  formed.
- A supported non-hydrogen is retained in source order and mapped to its exact
  checkpoint channel.
- An unsupported non-hydrogen rejects the complete sample.
- A missing, empty, non-string, or syntactically invalid `type_symbol` rejects
  the complete sample.
- Silent zero-vector fallback, the preview `others` channel as checkpoint input,
  and a new eleventh checkpoint channel are forbidden.

Classification reads only the explicit `type_symbol`. Atom names, residue names,
and atom-name prefixes have no element-inference authority.

## Projection order

The contract freezes this order:

```text
read type_symbol
→ validate presence, non-emptiness, and legal type
→ classify supported heavy / explicit H / unsupported non-H
→ exclude explicit H
→ reject the sample if unsupported non-H exists
→ build source-row → retained-heavy-row indices
→ project every future per-atom array and mask with the same keep mask
→ remap covalent atom-pair indices
→ compute the retained ligand+pocket heavy-atom joint centroid
→ create the 10-channel categorical feature
→ enter the future tensor contract
```

Thus hydrogen filtering precedes coordinate centering, node counts, batch
membership, every mask projection, and atom-pair index projection. Computing a
centroid over all atoms and deleting H afterward is not compatible with the
frozen `noH` training distribution.

All future per-atom tensors, role labels, canonical task masks,
target/context/generation/fixed masks, auxiliary labels, and covalent pair
indices must share one retained-heavy keep mask and one source-to-projected
index map. This V1 does not materialize any of those tensors.

## Current canonical evidence

The 22 BASE-bound atom tables contain 2870 rows:

| Domain | Source | Explicit H excluded | Supported heavy retained |
|---|---:|---:|---:|
| Protein/pocket | 2531 | 329 | 2202 |
| Ligand | 339 | 16 | 323 |
| Total | 2870 | 345 | 2525 |

There are zero unsupported non-hydrogen rows and zero missing or invalid
symbols. Retained indices start at zero, are contiguous within each
sample/domain, preserve source order, and have exact channels 0–9. Excluded H
rows have neither a projected index nor a channel and do not reject a sample.

All 11 samples retain nonempty ligand and pocket heavy-atom sets. All 11
covalent residue atoms and all 11 ligand atoms remain supported heavy atoms;
their source indices are independently remapped to retained-heavy indices with
exact-one evidence.

## Masks, issue transition, and readiness

The canonical mask contract remains exactly:

```text
warhead_only / A
linker_plus_warhead / B
scaffold_plus_warhead / B2
scaffold_only / B3
scaffold_plus_linker_plus_warhead / C
```

The predecessor's first 32 issue identities and order are retained. Only the
four successor-transition fields of
`UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED` change, resolving it with the 2870-row
classification, 345-row H exclusion, 2525-row heavy retention, and 11/11 pair
remap evidence. The effective open issue set is now empty.

Consequently, `feature_semantics_known=true`,
`unknown_atom_feature_policy_resolved=true`, and
`ready_for_tensor_label_loss_mask_contract_design=true`.

Runtime enforcement is deliberately not integrated:
`unknown_atom_runtime_enforcement_integrated=false`. Tensorization, model
integration, and training readiness all remain false. The five planned
covalent model modules remain 0/5 integrated.

The next authorized step is:

```text
design_covapie_tensor_label_and_loss_mask_contract_v1
```
