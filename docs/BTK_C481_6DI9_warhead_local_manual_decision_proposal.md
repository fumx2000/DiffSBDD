# BTK_C481_6DI9 Warhead-Local Manual Decision Proposal

This is a proposal for manual review only.

- It does not modify any CSV.
- It does not repair bond orders.
- It does not create pre-reaction graphs.
- It does not modify ligand SDF files.
- Final decisions must be explicitly applied in a later step.

## Inputs Reviewed

- `data/raw/covalent_small/metadata/6DI9_reference/GJJ_warhead_local_manual_decision_draft.csv`
- `data/raw/covalent_small/metadata/6DI9_reference/GJJ_warhead_local_mapping_review_template.csv`
- `data/raw/covalent_small/metadata/6DI9_reference/GJJ_graph_repair_report.csv`
- `docs/warhead_local_mapping_review_summary.md`
- `docs/BTK_C481_6DI9_curation_notes.md`

## Context

The BTK sample uses ligand `GJJ A 701`. The covalent LINK records connect
`CYS A 481 SG` altloc `A/B` to ligand atom `GJJ C33`, which maps to extracted
SDF atom `19`.

The extracted SDF is post-covalent-compatible bound geometry from PDB HETATM
and CONECT records. Its bond order is not reliable. The GJJ ideal reference SDF
contains the more chemically useful graph, but its atom order must not be used
directly for manifest indices.

The draft warhead annotation for this workflow smoke test is:

- warhead atoms: `17,18,19,32`
- linker atoms in this local review: `13,14,15,28,29`
- reactive atom: `19` / PDB atom `C33`

## Proposed Decisions

| extracted_atom_id | extracted_pdb_atom_name | final_role | is_reactive_atom | graph_distance_to_reactive_atom | mapping_confidence | reference_candidate_atom_id | local_review_reason | proposed_manual_decision | proposed_review_status | proposed_manual_reference_atom_id | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 13 | C22 | linker | false | 6 | low | 13 | low_confidence_warhead_or_linker | unresolved | needs_followup |  | Low-confidence linker atom far from reactive atom. Keep unresolved until the linker boundary mapping is manually checked against the reference graph. |
| 14 | C24 | linker | false | 4 | low | 14 | low_confidence_warhead_or_linker | unresolved | needs_followup |  | Low-confidence linker atom outside the immediate warhead core. Candidate is element-matched, but degree mismatch means it should not be accepted automatically. |
| 15 | N26 | linker | false | 3 | low | 15 | within_graph_distance_3;low_confidence_warhead_or_linker | unresolved | needs_followup |  | This linker nitrogen is close to the warhead, but mapping confidence is low. It should be manually checked before any local transfer across the linker-warhead boundary. |
| 17 | C30 | warhead | false | 2 | medium | 17 | warhead_atom;within_graph_distance_3 | accept_candidate | reviewed |  | Warhead atom in the proposed acrylamide/Michael acceptor region. Candidate is non-empty, element-matched, degree-matched, and locally consistent with the C30-C32-C33-O31 warhead description. |
| 18 | C32 | warhead | false | 1 | low | 18 | warhead_atom;within_graph_distance_3;low_confidence_warhead_or_linker | accept_candidate | reviewed |  | Warhead atom adjacent to reactive C33. Although confidence is low due to degree mismatch from degraded extracted bond order, the PDB atom name and position in the C30-C32-C33-O31 warhead support accepting this candidate for manual review. |
| 19 | C33 | warhead | true | 0 | high | 19 | reactive_atom;warhead_atom;within_graph_distance_3 | accept_candidate | reviewed |  | Reactive ligand atom. PDB atom C33 is linked to CYS A 481 SG altloc A/B, maps to extracted SDF atom 19, and has a non-empty element-matched reference candidate. |
| 28 | C23 | linker | false | 5 | low | 28 | low_confidence_warhead_or_linker | unresolved | needs_followup |  | Low-confidence linker atom outside the immediate warhead core. Do not accept without manual confirmation of the reference correspondence. |
| 29 | C25 | linker | false | 5 | low | 29 | low_confidence_warhead_or_linker | unresolved | needs_followup |  | Low-confidence linker atom outside the immediate warhead core. Keep unresolved until linker mapping is manually reviewed. |
| 32 | O31 | warhead | false | 3 | medium | 32 | warhead_atom;within_graph_distance_3 | accept_candidate | reviewed |  | Warhead oxygen in the proposed acrylamide/Michael acceptor region. Candidate is non-empty, element-matched, degree-matched, and consistent with the C30-C32-C33-O31 local warhead description. |

## Summary

- proposed accept_candidate count: `4`
- proposed unresolved count: `5`
- proposed replace_candidate count: `0`
- proposed reviewed rows: `4`
- proposed needs_followup rows: `5`

Warhead atom recommendations:

- atom `17` / `C30`: `accept_candidate`, `reviewed`
- atom `18` / `C32`: `accept_candidate`, `reviewed`
- atom `19` / `C33`: `accept_candidate`, `reviewed`
- atom `32` / `O31`: `accept_candidate`, `reviewed`

Linker atom recommendations:

- atom `13` / `C22`: `unresolved`, `needs_followup`
- atom `14` / `C24`: `unresolved`, `needs_followup`
- atom `15` / `N26`: `unresolved`, `needs_followup`
- atom `28` / `C23`: `unresolved`, `needs_followup`
- atom `29` / `C25`: `unresolved`, `needs_followup`

## Readiness Assessment

BTK_C481_6DI9 is not ready for warhead-local bond-order transfer yet.

Reason: the core warhead atoms have reasonable accept-candidate proposals, but
the linker-side boundary atoms remain unresolved. A later step should either
manually confirm those linker mappings or narrow the trial further to a strictly
warhead-only transfer that does not cross unresolved boundary atoms.

Recommended next action:

1. Apply these decisions only in a separate CSV-editing step after review.
2. Re-run `scripts/check_warhead_local_manual_decision_draft.py`.
3. If unresolved linker rows remain, do not perform local bond-order transfer
   across those atoms.
