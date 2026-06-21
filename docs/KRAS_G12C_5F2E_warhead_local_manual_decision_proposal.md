# KRAS_G12C_5F2E Warhead-Local Manual Decision Proposal

This is a proposal for manual review only.

- It does not modify any CSV.
- It does not repair bond orders.
- It does not create pre-reaction graphs.
- It does not modify ligand SDF files.
- Final decisions must be explicitly applied in a later step.

## Inputs Reviewed

- `data/raw/covalent_small/metadata/5F2E_reference/5UT_warhead_local_manual_decision_draft.csv`
- `data/raw/covalent_small/metadata/5F2E_reference/5UT_warhead_local_mapping_review_template.csv`
- `data/raw/covalent_small/metadata/5F2E_reference/5UT_graph_repair_report.csv`
- `docs/warhead_local_mapping_review_summary.md`
- `docs/KRAS_G12C_5F2E_curation_notes.md`

## Context

The KRAS sample uses ligand `5UT A 204`. The covalent LINK record connects
`CYS A 12 SG` to ligand atom `5UT C15`, which maps to extracted SDF atom `29`.

The extracted SDF is post-covalent-compatible bound geometry from PDB HETATM
and CONECT records. Its bond order is not reliable. The 5UT ideal reference SDF
can help review the warhead chemistry, but its atom order must not be used
directly for manifest indices.

The draft warhead annotation for this workflow smoke test is:

- warhead atoms: `8,27,28,29`
- linker/local boundary atoms in this review: `7,24,25,26`
- reactive atom: `29` / PDB atom `C15`

## Proposed Decisions

| extracted_atom_id | extracted_pdb_atom_name | final_role | is_reactive_atom | graph_distance_to_reactive_atom | mapping_confidence | reference_candidate_atom_id | local_review_reason | proposed_manual_decision | proposed_review_status | proposed_manual_reference_atom_id | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | C11 | linker | false | 5 | low | 7 | low_confidence_warhead_or_linker | unresolved | needs_followup |  | Low-confidence linker-side boundary atom. It is outside the immediate warhead core and should not be accepted without manual confirmation. |
| 8 | C14 | warhead | false | 1 | low | 8 | warhead_atom;within_graph_distance_3;low_confidence_warhead_or_linker | accept_candidate | reviewed |  | Warhead atom adjacent to reactive C15. Although confidence is low due to degraded extracted bond order, the PDB atom name and C13-C14-C15-O1 warhead context support accepting this candidate for manual review. |
| 24 | C16 | linker | false | 4 | low | 24 | low_confidence_warhead_or_linker | unresolved | needs_followup |  | Low-confidence linker-side boundary atom. Keep unresolved until the linker-warhead boundary mapping is manually checked. |
| 25 | N3 | linker | false | 3 | medium | 25 | within_graph_distance_3 | unresolved | needs_followup |  | Local linker atom near the warhead. Even with medium confidence, it is a boundary atom and should be manually confirmed before transfer across this atom. |
| 26 | C12 | linker | false | 4 | low | 26 | low_confidence_warhead_or_linker | unresolved | needs_followup |  | Low-confidence linker-side boundary atom. Do not accept automatically without manual reference graph confirmation. |
| 27 | C13 | warhead | false | 2 | medium | 27 | warhead_atom;within_graph_distance_3 | accept_candidate | reviewed |  | Warhead atom in the proposed acryloyl/Michael acceptor region. Candidate is non-empty, element-matched, degree-matched, and locally consistent with C13-C14-C15-O1. |
| 28 | O1 | warhead | false | 3 | medium | 28 | warhead_atom;within_graph_distance_3 | accept_candidate | reviewed |  | Warhead oxygen in the proposed acryloyl/Michael acceptor region. Candidate is non-empty, element-matched, degree-matched, and consistent with the C13-C14-C15-O1 local warhead description. |
| 29 | C15 | warhead | true | 0 | high | 29 | reactive_atom;warhead_atom;within_graph_distance_3 | accept_candidate | reviewed |  | Reactive ligand atom. PDB atom C15 is linked to CYS A 12 SG, maps to extracted SDF atom 29, and has a non-empty element-matched reference candidate. |

## Summary

- proposed accept_candidate count: `4`
- proposed unresolved count: `4`
- proposed replace_candidate count: `0`
- proposed reviewed rows: `4`
- proposed needs_followup rows: `4`

Warhead atom recommendations:

- atom `8` / `C14`: `accept_candidate`, `reviewed`
- atom `27` / `C13`: `accept_candidate`, `reviewed`
- atom `28` / `O1`: `accept_candidate`, `reviewed`
- atom `29` / `C15`: `accept_candidate`, `reviewed`

Linker/local boundary atom recommendations:

- atom `7` / `C11`: `unresolved`, `needs_followup`
- atom `24` / `C16`: `unresolved`, `needs_followup`
- atom `25` / `N3`: `unresolved`, `needs_followup`
- atom `26` / `C12`: `unresolved`, `needs_followup`

## Readiness Assessment

KRAS_G12C_5F2E is not ready for warhead-local bond-order transfer yet.

Reason: the core warhead atoms have reasonable accept-candidate proposals, but
the linker/local boundary atoms remain unresolved. A later step should either
manually confirm those boundary mappings or narrow any trial to a strictly
warhead-only transfer that does not cross unresolved atoms.

Recommended next action:

1. Apply these decisions only in a separate CSV-editing step after review.
2. Re-run `scripts/check_warhead_local_manual_decision_draft.py`.
3. If unresolved linker/local boundary rows remain, do not perform local
   bond-order transfer across those atoms.
