# Warhead-Local Mapping Review Summary

This document is for manual review only.

- It does not repair bond orders.
- It does not create pre-reaction graphs.
- It does not modify ligand SDF files.
- Reference atom order must not be used directly for manifest indices.

## BTK_C481_6DI9

- sample_id: `BTK_C481_6DI9`
- row count: 9
- reactive atom row: 19
- warhead atom rows: 17, 18, 19, 32
- linker rows included by low_confidence_warhead_or_linker: 13, 14, 15, 28, 29
- rows with mapping_confidence=low: 13, 14, 15, 18, 28, 29
- rows with mapping_confidence=medium: 17, 32
- rows with local_review_reason: low_confidence_warhead_or_linker=6, reactive_atom=1, warhead_atom=4, within_graph_distance_3=5
- manual review status: not_reviewed

| extracted_atom_id | extracted_pdb_atom_name | extracted_element | reference_candidate_atom_id | reference_element | graph_distance_to_reactive_atom | final_role | is_reactive_atom | mapping_confidence | local_review_reason | manual_reference_atom_id | manual_decision | manual_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 13 | C22 | C | 13 | C | 6 | linker | false | low | low_confidence_warhead_or_linker |  |  |  |
| 14 | C24 | C | 14 | C | 4 | linker | false | low | low_confidence_warhead_or_linker |  |  |  |
| 15 | N26 | N | 15 | N | 3 | linker | false | low | within_graph_distance_3;low_confidence_warhead_or_linker |  |  |  |
| 17 | C30 | C | 17 | C | 2 | warhead | false | medium | warhead_atom;within_graph_distance_3 |  |  |  |
| 18 | C32 | C | 18 | C | 1 | warhead | false | low | warhead_atom;within_graph_distance_3;low_confidence_warhead_or_linker |  |  |  |
| 19 | C33 | C | 19 | C | 0 | warhead | true | high | reactive_atom;warhead_atom;within_graph_distance_3 |  |  |  |
| 28 | C23 | C | 28 | C | 5 | linker | false | low | low_confidence_warhead_or_linker |  |  |  |
| 29 | C25 | C | 29 | C | 5 | linker | false | low | low_confidence_warhead_or_linker |  |  |  |
| 32 | O31 | O | 32 | O | 3 | warhead | false | medium | warhead_atom;within_graph_distance_3 |  |  |  |

## KRAS_G12C_5F2E

- sample_id: `KRAS_G12C_5F2E`
- row count: 8
- reactive atom row: 29
- warhead atom rows: 8, 27, 28, 29
- linker rows included by low_confidence_warhead_or_linker: 7, 24, 26
- rows with mapping_confidence=low: 7, 8, 24, 26
- rows with mapping_confidence=medium: 25, 27, 28
- rows with local_review_reason: low_confidence_warhead_or_linker=4, reactive_atom=1, warhead_atom=4, within_graph_distance_3=5
- manual review status: not_reviewed

| extracted_atom_id | extracted_pdb_atom_name | extracted_element | reference_candidate_atom_id | reference_element | graph_distance_to_reactive_atom | final_role | is_reactive_atom | mapping_confidence | local_review_reason | manual_reference_atom_id | manual_decision | manual_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | C11 | C | 7 | C | 5 | linker | false | low | low_confidence_warhead_or_linker |  |  |  |
| 8 | C14 | C | 8 | C | 1 | warhead | false | low | warhead_atom;within_graph_distance_3;low_confidence_warhead_or_linker |  |  |  |
| 24 | C16 | C | 24 | C | 4 | linker | false | low | low_confidence_warhead_or_linker |  |  |  |
| 25 | N3 | N | 25 | N | 3 | linker | false | medium | within_graph_distance_3 |  |  |  |
| 26 | C12 | C | 26 | C | 4 | linker | false | low | low_confidence_warhead_or_linker |  |  |  |
| 27 | C13 | C | 27 | C | 2 | warhead | false | medium | warhead_atom;within_graph_distance_3 |  |  |  |
| 28 | O1 | O | 28 | O | 3 | warhead | false | medium | warhead_atom;within_graph_distance_3 |  |  |  |
| 29 | C15 | C | 29 | C | 0 | warhead | true | high | reactive_atom;warhead_atom;within_graph_distance_3 |  |  |  |

## KRAS_G12C_6OIM

- sample_id: `KRAS_G12C_6OIM`
- row count: 10
- reactive atom row: 7
- warhead atom rows: 4, 5, 6, 7
- linker rows included by low_confidence_warhead_or_linker: 0, 1, 2, 8, 9
- rows with mapping_confidence=low: 0, 1, 2, 6, 8, 9
- rows with mapping_confidence=medium: 3, 4, 5
- rows with local_review_reason: low_confidence_warhead_or_linker=6, reactive_atom=1, warhead_atom=4, within_graph_distance_3=5
- manual review status: not_reviewed

| extracted_atom_id | extracted_pdb_atom_name | extracted_element | reference_candidate_atom_id | reference_element | graph_distance_to_reactive_atom | final_role | is_reactive_atom | mapping_confidence | local_review_reason | manual_reference_atom_id | manual_decision | manual_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | C21 | C | 0 | C | 6 | linker | false | low | low_confidence_warhead_or_linker |  |  |  |
| 1 | C20 | C | 1 | C | 5 | linker | false | low | low_confidence_warhead_or_linker |  |  |  |
| 2 | C19 | C | 2 | C | 4 | linker | false | low | low_confidence_warhead_or_linker |  |  |  |
| 3 | N6 | N | 3 | N | 3 | linker | false | medium | within_graph_distance_3 |  |  |  |
| 4 | C23 | C | 4 | C | 2 | warhead | false | medium | warhead_atom;within_graph_distance_3 |  |  |  |
| 5 | O2 | O | 5 | O | 3 | warhead | false | medium | warhead_atom;within_graph_distance_3 |  |  |  |
| 6 | C24 | C | 6 | C | 1 | warhead | false | low | warhead_atom;within_graph_distance_3;low_confidence_warhead_or_linker |  |  |  |
| 7 | C25 | C | 7 | C | 0 | warhead | true | high | reactive_atom;warhead_atom;within_graph_distance_3 |  |  |  |
| 8 | C18 | C | 8 | C | 4 | linker | false | low | low_confidence_warhead_or_linker |  |  |  |
| 9 | C17 | C | 9 | C | 5 | linker | false | low | low_confidence_warhead_or_linker |  |  |  |
