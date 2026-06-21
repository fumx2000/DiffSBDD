# Strictly Warhead-Only Bond-Order Trial Plan

This is a design plan only.

- It does not repair bond orders.
- It does not create repaired SDF files.
- It does not create pre-reaction graphs.
- It does not modify ligand SDF files.
- It does not mark samples as training-ready.
- It does not change model code.

## Rationale

The three curated workflow-smoke-test samples now have accepted warhead-core
manual mappings, but each still has unresolved linker/local boundary atoms. The
current conservative path is therefore not cross-boundary bond-order transfer.

The only safe next trial to design is a strictly warhead-only, non-destructive
dry run. It may inspect whether reference bond-order information could be
transferred inside the accepted warhead core, but it must block any bond that
touches unresolved boundary atoms.

## Strictly Warhead-Only Scope

The strictly warhead-only scope is intentionally narrow:

- Only atoms with `manual_decision=accept_candidate` and `final_role=warhead`
  are eligible.
- Only ligand-internal bonds whose two endpoints are both accepted warhead atoms
  are eligible for consideration.
- Any bond with one or both endpoints outside accepted warhead atoms is blocked.
- Any bond connected to an unresolved linker/local boundary atom is blocked.
- No cross-boundary bond may be created or modified.
- No new bond may be created across a warhead/linker boundary.
- Atom coordinates must not be modified.
- Raw extracted SDF files must not be overwritten.
- `manifest_real_small.csv` must not be modified.
- No sample may be marked training-ready.
- Any future output must be written under `data/derived/`, not under raw data.

This means a future trial can only inspect or transfer bond order for bonds
fully contained inside the accepted warhead atom set.

## Current Eligible Warhead Atoms

| sample_id | eligible accepted warhead atoms |
| --- | --- |
| BTK_C481_6DI9 | `17,18,19,32` |
| KRAS_G12C_5F2E | `8,27,28,29` |
| KRAS_G12C_6OIM | `4,5,6,7` |

## Current Unresolved Boundary Atoms

| sample_id | unresolved linker/local boundary atoms |
| --- | --- |
| BTK_C481_6DI9 | `13,14,15,28,29` |
| KRAS_G12C_5F2E | `7,24,25,26` |
| KRAS_G12C_6OIM | `0,1,2,3,8,9` |

These unresolved atoms are the reason no sample is ready for cross-boundary
local bond-order transfer.

## Step 7b Dry-Run Report

Step 7b should implement a dry-run report only. It should not write repaired
SDF files and should not change any input files.

The dry-run report should contain one row per relevant ligand-internal bond and
should include at least these fields:

- `sample_id`
- `bond_endpoint_a`
- `bond_endpoint_b`
- `extracted_old_bond_type`
- `reference_candidate_bond_type`
- `both_atoms_accepted_warhead`
- `touches_unresolved_boundary`
- `proposed_action`
- `safety_decision`
- `rationale`

Allowed `proposed_action` values:

- `keep`
- `would_transfer_in_warhead_only_scope`
- `blocked_touches_unresolved_boundary`
- `blocked_missing_reference_bond`
- `blocked_atom_not_accepted`

Allowed `safety_decision` values:

- `eligible`
- `blocked`

Dry-run rows should use conservative logic:

- If both endpoints are accepted warhead atoms and a reference candidate bond is
  available, the row can be `would_transfer_in_warhead_only_scope` and
  `eligible`.
- If either endpoint touches an unresolved boundary atom, the row must be
  `blocked_touches_unresolved_boundary` and `blocked`.
- If either endpoint is not an accepted warhead atom, the row must be
  `blocked_atom_not_accepted` and `blocked`.
- If no reference candidate bond can be identified, the row must be
  `blocked_missing_reference_bond` and `blocked`.
- If the extracted and reference bond types already match, the row can be
  `keep`, but only when it is still inside accepted warhead-only scope.

## Future Step 7c Non-Destructive Output Locations

Step 7a does not generate these files or directories. A future non-destructive
trial may use:

- `data/derived/covalent_small/warhead_only_repair_reports/`
- `data/derived/covalent_small/ligands_warhead_only_repaired/`

The derived location is mandatory. Future repaired outputs must not overwrite
raw extracted ligand SDF files.

## Recommended Route

1. Implement Step 7b as a dry-run report only.
2. Inspect whether every `would_transfer_in_warhead_only_scope` bond is fully
   contained inside accepted warhead atoms.
3. Confirm no `would-transfer` row touches unresolved boundary atoms.
4. Only then consider Step 7c as a non-destructive repaired-SDF trial under
   `data/derived/`.
5. Treat any future repaired SDF as a curation artifact, not as training-ready
   data.
6. Marking `training_ready=true` must wait for a later explicit QA gate.

## Current Readiness

| sample_id | accepted warhead mappings | unresolved boundary atoms | cross-boundary transfer ready | strictly warhead-only dry run |
| --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | yes | yes | no | allowed as dry run only |
| KRAS_G12C_5F2E | yes | yes | no | allowed as dry run only |
| KRAS_G12C_6OIM | yes | yes | no | allowed as dry run only |

All three samples are candidates for a strictly warhead-only dry-run report.
None is ready for cross-boundary local bond-order transfer, and none is
training-ready.
