# CovaPIE external-pocket runtime bridge path coverage V1

## What this step resolves

DiffSBDD's main public inference route accepts an external PDB and calls
`LigandPocketDDPM.generate_ligands`. That method selects a pocket, calls
`prepare_pocket`, and then sends the resulting pocket dictionary to either
`ConditionalDDPM.sample_given_pocket` or `EnVariationalDiffusion.inpaint`.
It does not load a collated dataset batch and therefore bypasses
`LigandPocketDDPM.get_ligand_and_pocket`.

The predecessor design covered the collated training and evaluation routes,
but correctly left this external-PDB route blocked. This V1 resolution freezes
how the missing route will carry the target identity. It is still a design:
the runtime bridge is not implemented and the model does not consume the
indicator.

## Explicit target selector

The future Python argument is exactly
`target_residue_atom_condition_spec`. It will be an explicit parameter of both
`generate_ligands` and `prepare_pocket`; it must not disappear into `**kwargs`
and must not be forwarded as a DDPM or inpainting option.

The selector has exactly six semantic fields:

| Field | V1 meaning |
| --- | --- |
| `chain_id` | Non-empty string, matched exactly to the Biopython chain ID |
| `residue_sequence_number` | Integer, but never a boolean |
| `residue_insertion_code` | Exactly one character; V1 supports only the blank code `" "` |
| `residue_name` | Exactly `CYS` |
| `atom_name` | Exactly `SG` |
| `element` | Exactly `S` |

The external PDB model is model index 0 and the standard protein-residue
hetflag is the blank string `" "`. V1 is deliberately restricted to Cys-SG-S:
it solves the current CovaPIE target semantics without inventing a broader
residue or atom-selection language.

An explicit selector is necessary because residue number alone is ambiguous
between chains, and “find the unique cysteine” is not stable under a different
pocket or structure. The design also rejects nearest-coordinate, nearest
reference-ligand, PDB atom-serial, and user-provided local-index selection.
Coordinates can move during centering and normalization and are not an atom's
identity; atom serials and local indices are representations rather than the
canonical chain/residue/atom identity.

## Full-atom pocket and membership

When the selector is present, `pocket_representation` must be `full-atom`.
The CA representation has no SG atom node, so V1 fails closed instead of
fabricating an SG indicator on a CA node. With no selector, the existing CA
route remains unchanged.

The target must already belong to the selected pocket for both selection
routes:

- an explicit `pocket_ids` list; and
- a pocket derived from `ref_ligand`.

It must occur in the selected `biopython_residues` and in the final
`pocket_atoms` sequence. Missing and duplicate matches both fail closed. V1
does not append a residue, enlarge the radius, alter `pocket_ids`, alter the
reference-ligand selection, or reorder atoms. Automatic append would silently
change pocket composition and the distribution seen by the checkpoint.

Disordered target residues, disordered target atoms, and implicit altloc child
selection are rejected. Biopython's selected child is not a sufficiently
explicit identity contract. A future step may define disordered/altloc
semantics; this V1 records that work as deferred.

## Binding to the real node order

The target is matched inside the exact `pocket_atoms` list that
`prepare_pocket` already uses to construct `pocket_coord` and
`pocket_one_hot`. The identity comes from the atom's parent residue and chain,
the residue hetflag/sequence/insertion tuple, residue name, atom name, and
element. Exactly one match is required, and sulfur must be representable by
the checkpoint's 10-dimensional pocket vocabulary.

The base indicator is created before repetition:

```python
base_indicator = [False] * len(pocket_atoms)
base_indicator[target_local_index] = True
```

The runtime implementation will use `torch.bool`. For `n_samples`, it repeats
the complete base block in the same order as `pocket_coord.repeat(n_samples,
1)` and `pocket_one_hot.repeat(n_samples, 1)`. Thus every sample block has one
true node, the total true count is `n_samples`, and the decisive alignment
check is equivalent to:

```python
pocket["mask"][indicator] == torch.arange(n_samples)
```

This base-order-first rule prevents interleaved or per-atom repeat layouts
from silently disagreeing with the existing pocket tensors.

## Sidecar and both diffusion branches

With a selector, the prepared pocket gains exactly this same-name sidecar:

```text
pocket_target_residue_atom_condition_indicator
```

It is a per-pocket-node `torch.bool` tensor on the same device and with the
same length and node order as `x`, `one_hot`, and `mask`. The conditional and
inpainting branches receive the same prepared pocket dictionary and therefore
the same sidecar. With no selector, the key is absent; an all-false placeholder
would confuse “legacy field absent” with an asserted covalent condition and is
forbidden.

Carrying the sidecar through both branches is only path coverage. This step
does not append it to `pocket_one_hot`, pass it into dynamics, change EGNN,
change a loss, or design model consumption. Consequently atom/residue/joint
feature widths, state-dict keys, and checkpoint tensor shapes remain unchanged.

## Repository callers

The audit covers all current direct generation callers:

- `generate_ligands.py` public CLI;
- `test.py` batch CLI; and
- `colab/DiffSBDD.ipynb` interactive generation cell.

It also covers every current direct pocket-preparation caller:

- `LigandPocketDDPM.generate_ligands`;
- `optimize.py`;
- `inpaint.py`; and
- `scripts/covalent_inpaint_demo.py`.

Each has a frozen future forwarding surface. CLI or notebook callers must
build an Exact6 selector explicitly; the batch CLI needs a per-complex selector
manifest. Direct `prepare_pocket` wrappers must accept and forward the named
selector. Omitting it preserves their current behavior. This design step does
not add those CLI options.

## Compatibility, masks, and next boundary

The canonical mask contract remains exactly five tasks:

1. `warhead_only`
2. `linker_plus_warhead`
3. `scaffold_plus_warhead`
4. `scaffold_only`
5. `scaffold_plus_linker_plus_warhead`

No sixth mask is introduced. The Current11 collated path is unchanged.

The next authorized implementation is expected to remain within the three
Lightning method boundaries `get_ligand_and_pocket`, `prepare_pocket`, and
explicit forwarding in `generate_ligands`, plus isolated helpers, tests, a
checker, and documentation. This guide does not authorize that implementation.

Finally, runtime path coverage is not training readiness. Step12D was a smoke
legality check, not a final training-feature contract. Before formal training
or any parameter update, CovaPIE still requires a feature-semantics audit and
must resolve or formally audit the historical
`UNKNOWN_ATOM_FEATURE_POLICY` / `feature_semantics_known=False` state.

## Why the validator freezes semantics as well as the digest

The response's self digest proves that its bytes are internally consistent; it
does not by itself prove that the represented policy is the approved policy.
Erroneous code—or an attacker able to alter a response—could change a nested
value and compute a new, valid digest for the changed semantics.

For that reason, the Exact36 validator independently binds the formal lineage
and the complete nested contracts. It freezes the selector and validation
rules, full-atom and membership policies, actual `pocket_atoms` order,
sample-block repetition, same-name sidecar, legacy behavior, both diffusion
branches, runtime source audit, current interfaces, every caller forwarding
surface, all candidate decisions, and checkpoint compatibility. It also
derives implementation readiness only after all of those contracts match.
Tests and the checker deliberately modify validly shaped nested fields,
recompute the response digest, and require the real validator to reject them.

This semantic-validator revision does not alter the public builder's formal
Exact36 response, its response SHA, the external-pocket design, or the
`ready_for_runtime_bridge_implementation=true` conclusion. It only closes the
re-signed semantic-drift validation gap; no runtime bridge or model consumption
is implemented here.
