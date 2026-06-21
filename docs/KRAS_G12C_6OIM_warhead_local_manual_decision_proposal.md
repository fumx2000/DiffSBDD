# KRAS_G12C_6OIM Warhead-Local Manual Decision Proposal

This is a proposal for manual review only.

- It does not modify any CSV.
- It does not repair bond orders.
- It does not create pre-reaction graphs.
- It does not modify ligand SDF files.
- Final decisions must be explicitly applied in a later step.

## Inputs Reviewed

- `data/raw/covalent_small/metadata/6OIM_reference/MOV_warhead_local_manual_decision_draft.csv`
- `data/raw/covalent_small/metadata/6OIM_reference/MOV_warhead_local_mapping_review_template.csv`
- `data/raw/covalent_small/metadata/6OIM_reference/MOV_graph_repair_report.csv`
- `docs/warhead_local_mapping_review_summary.md`
- `docs/KRAS_G12C_6OIM_curation_notes.md`

## Context

The KRAS sample uses ligand `MOV A 303`. The covalent LINK record connects
`CYS A 12 SG` to ligand atom `MOV C25`, which maps to extracted SDF atom `7`.

The extracted SDF is post-covalent-compatible bound geometry from PDB HETATM
and CONECT records. Its bond order is not reliable. The MOV ideal reference SDF
can help review the warhead chemistry, but its atom order must not be used
directly for manifest indices.

The draft warhead annotation for this workflow smoke test is:

- warhead atoms: `4,5,6,7`
- linker/local boundary atoms in this review: `0,1,2,3,8,9`
- reactive atom: `7` / PDB atom `C25`

## Proposed Decisions

| extracted_atom_id | extracted_pdb_atom_name | final_role | is_reactive_atom | graph_distance_to_reactive_atom | mapping_confidence | reference_candidate_atom_id | local_review_reason | proposed_manual_decision | proposed_review_status | proposed_manual_reference_atom_id | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | C21 | linker | false | 6 | low | 0 | low_confidence_warhead_or_linker | unresolved | needs_followup |  | Low-confidence linker-side boundary atom. It is outside the immediate warhead core and should not be accepted without manual confirmation. |
| 1 | C20 | linker | false | 5 | low | 1 | low_confidence_warhead_or_linker | unresolved | needs_followup |  | Low-confidence linker-side boundary atom. Candidate is element-matched, but degree mismatch means it should not be accepted automatically. |
| 2 | C19 | linker | false | 4 | low | 2 | low_confidence_warhead_or_linker | unresolved | needs_followup |  | Low-confidence linker-side boundary atom. Keep unresolved until the linker-warhead boundary mapping is manually checked. |
| 3 | N6 | linker | false | 3 | medium | 3 | within_graph_distance_3 | unresolved | needs_followup |  | Local linker atom near the warhead. Even with medium confidence, it is a boundary atom and should be manually confirmed before transfer across this atom. |
| 4 | C23 | warhead | false | 2 | medium | 4 | warhead_atom;within_graph_distance_3 | accept_candidate | reviewed |  | Warhead atom in the proposed acrylamide/Michael acceptor region. Candidate is non-empty, element-matched, degree-matched, and locally consistent with C23-C24-C25-O2. |
| 5 | O2 | warhead | false | 3 | medium | 5 | warhead_atom;within_graph_distance_3 | accept_candidate | reviewed |  | Warhead oxygen in the proposed acrylamide/Michael acceptor region. Candidate is non-empty, element-matched, degree-matched, and consistent with the C23-C24-C25-O2 local warhead description. |
| 6 | C24 | warhead | false | 1 | low | 6 | warhead_atom;within_graph_distance_3;low_confidence_warhead_or_linker | accept_candidate | reviewed |  | Warhead atom adjacent to reactive C25. Although confidence is low due to degree mismatch from degraded extracted bond order, the PDB atom name and C23-C24-C25-O2 warhead context support accepting this candidate for manual review. |
| 7 | C25 | warhead | true | 0 | high | 7 | reactive_atom;warhead_atom;within_graph_distance_3 | accept_candidate | reviewed |  | Reactive ligand atom. PDB atom C25 is linked to CYS A 12 SG, maps to extracted SDF atom 7, and has a non-empty element-matched reference candidate. |
| 8 | C18 | linker | false | 4 | low | 8 | low_confidence_warhead_or_linker | unresolved | needs_followup |  | Low-confidence linker-side boundary atom. Do not accept automatically without manual reference graph confirmation. |
| 9 | C17 | linker | false | 5 | low | 9 | low_confidence_warhead_or_linker | unresolved | needs_followup |  | Low-confidence linker-side boundary atom outside the immediate warhead core. Keep unresolved until linker mapping is manually reviewed. |

## Summary

- proposed accept_candidate count: `4`
- proposed unresolved count: `6`
- proposed replace_candidate count: `0`
- proposed reviewed rows: `4`
- proposed needs_followup rows: `6`

Warhead atom recommendations:

- atom `4` / `C23`: `accept_candidate`, `reviewed`
- atom `5` / `O2`: `accept_candidate`, `reviewed`
- atom `6` / `C24`: `accept_candidate`, `reviewed`
- atom `7` / `C25`: `accept_candidate`, `reviewed`

Linker/local boundary atom recommendations:

- atom `0` / `C21`: `unresolved`, `needs_followup`
- atom `1` / `C20`: `unresolved`, `needs_followup`
- atom `2` / `C19`: `unresolved`, `needs_followup`
- atom `3` / `N6`: `unresolved`, `needs_followup`
- atom `8` / `C18`: `unresolved`, `needs_followup`
- atom `9` / `C17`: `unresolved`, `needs_followup`

## Readiness Assessment

KRAS_G12C_6OIM is not ready for warhead-local bond-order transfer yet.

Reason: the core warhead atoms have reasonable accept-candidate proposals, but
the linker/local boundary atoms remain unresolved. A later step should either
manually confirm those boundary mappings or narrow any trial to a strictly
warhead-only transfer that does not cross unresolved atoms.

Recommended next action:

1. Apply these decisions only in a separate CSV-editing step after review.
2. Re-run `scripts/check_warhead_local_manual_decision_draft.py`.
3. If unresolved linker/local boundary rows remain, do not perform local
   bond-order transfer across those atoms.
