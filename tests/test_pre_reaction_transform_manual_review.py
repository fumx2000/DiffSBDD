from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from init_pre_reaction_transform_manual_review import REVIEW_COLUMNS, build_review_rows, write_review


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_template(path: Path) -> None:
    rows = []
    for sample_id, warhead_type in [
        ("BTK_C481_6DI9", "btk_c481_inhibitor_like_michael_acceptor_draft"),
        ("KRAS_G12C_5F2E", "kras_g12c_inhibitor_like_michael_acceptor_draft"),
        ("KRAS_G12C_6OIM", "kras_g12c_inhibitor_like_michael_acceptor_draft"),
    ]:
        rows.append(
            {
                "sample_id": sample_id,
                "warhead_type": warhead_type,
                "residue_name": "CYS",
                "residue_atom": "SG",
                "ligand_reactive_atom": "",
                "covalent_bond_to_remove": "",
                "bond_order_to_restore": "",
                "atoms_requiring_charge_check": "",
                "atoms_requiring_valence_check": "",
                "protonation_note": "requires_manual_review",
                "geometry_note": "post_covalent_bound_pose_coordinates_do_not_claim_free_ligand_conformer",
                "confidence_level": "draft",
                "requires_manual_review": "true",
                "rule_status": "draft_not_reviewed",
                "rule_source": "pre_reaction_graph_design_plan",
                "training_ready_candidate": "false",
                "pre_reaction_graph_ready": "false",
                "curator_note": "template_only_no_transform_performed",
            }
        )
    _write_csv(path, rows)


def _decision_row(
    sample_id: str,
    atom_id: str,
    final_role: str,
    is_reactive_atom: str,
    manual_decision: str,
    local_review_reason: str = "",
) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "extracted_atom_id": atom_id,
        "extracted_element": "C",
        "extracted_pdb_atom_name": f"C{atom_id}",
        "reference_candidate_atom_id": atom_id,
        "reference_element": "C",
        "graph_distance_to_reactive_atom": "1",
        "final_role": final_role,
        "is_reactive_atom": is_reactive_atom,
        "mapping_confidence": "medium",
        "mapping_warning": "",
        "local_review_reason": local_review_reason,
        "manual_reference_atom_id": "",
        "manual_decision": manual_decision,
        "manual_note": "",
        "review_status": "reviewed" if manual_decision == "accept_candidate" else "needs_followup",
        "decision_source": "test",
        "decision_warning": "test",
    }


def _write_decision_drafts(tmp_path: Path) -> list[Path]:
    sample_specs = {
        "BTK_C481_6DI9": {
            "reactive": "19",
            "warheads": ["17", "18", "19", "32"],
            "boundary": ["13", "14", "15", "28", "29"],
        },
        "KRAS_G12C_5F2E": {
            "reactive": "29",
            "warheads": ["8", "27", "28", "29"],
            "boundary": ["7", "24", "25", "26"],
        },
        "KRAS_G12C_6OIM": {
            "reactive": "7",
            "warheads": ["4", "5", "6", "7"],
            "boundary": ["0", "1", "2", "3", "8", "9"],
        },
    }
    paths: list[Path] = []
    for sample_id, spec in sample_specs.items():
        rows = []
        for atom_id in spec["warheads"]:
            rows.append(
                _decision_row(
                    sample_id=sample_id,
                    atom_id=atom_id,
                    final_role="warhead",
                    is_reactive_atom=str(atom_id == spec["reactive"]).lower(),
                    manual_decision="accept_candidate",
                    local_review_reason="warhead_atom",
                )
            )
        for atom_id in spec["boundary"]:
            rows.append(
                _decision_row(
                    sample_id=sample_id,
                    atom_id=atom_id,
                    final_role="linker",
                    is_reactive_atom="false",
                    manual_decision="unresolved",
                    local_review_reason="low_confidence_warhead_or_linker",
                )
            )
        path = tmp_path / f"{sample_id}.csv"
        _write_csv(path, rows)
        paths.append(path)
    return paths


def test_pre_reaction_transform_manual_review_draft(tmp_path: Path) -> None:
    template_csv = tmp_path / "template.csv"
    output_csv = tmp_path / "review.csv"
    _write_template(template_csv)
    decision_paths = _write_decision_drafts(tmp_path)
    input_hashes = {path: _sha256(path) for path in [template_csv, *decision_paths]}

    rows = build_review_rows(rule_template_csv=template_csv, manual_decision_drafts=decision_paths)
    write_review(rows, output_csv)

    assert output_csv.exists()
    written_rows = list(csv.DictReader(output_csv.open(newline="", encoding="utf-8")))
    assert list(written_rows[0]) == REVIEW_COLUMNS
    assert {row["sample_id"] for row in written_rows} == {
        "BTK_C481_6DI9",
        "KRAS_G12C_5F2E",
        "KRAS_G12C_6OIM",
    }
    by_sample = {row["sample_id"]: row for row in written_rows}
    assert by_sample["BTK_C481_6DI9"]["ligand_reactive_atom_candidate"] == "19"
    assert by_sample["KRAS_G12C_5F2E"]["ligand_reactive_atom_candidate"] == "29"
    assert by_sample["KRAS_G12C_6OIM"]["ligand_reactive_atom_candidate"] == "7"
    assert by_sample["BTK_C481_6DI9"]["accepted_warhead_atoms"] == "17 18 19 32"
    assert by_sample["KRAS_G12C_5F2E"]["accepted_warhead_atoms"] == "8 27 28 29"
    assert by_sample["KRAS_G12C_6OIM"]["accepted_warhead_atoms"] == "4 5 6 7"
    assert by_sample["BTK_C481_6DI9"]["unresolved_boundary_atoms"] == "13 14 15 28 29"
    assert by_sample["KRAS_G12C_5F2E"]["unresolved_boundary_atoms"] == "7 24 25 26"
    assert by_sample["KRAS_G12C_6OIM"]["unresolved_boundary_atoms"] == "0 1 2 3 8 9"
    assert {row["requires_manual_review"] for row in written_rows} == {"true"}
    assert {row["review_status"] for row in written_rows} == {"draft_not_reviewed"}
    assert {row["training_ready_candidate"] for row in written_rows} == {"false"}
    assert {row["pre_reaction_graph_ready"] for row in written_rows} == {"false"}
    for row in written_rows:
        assert "template_only_no_transform_performed" in row["reviewer_note"]
        assert "no_pre_reaction_sdf_generated" in row["reviewer_note"]
        assert "unresolved_boundary_present" in row["reviewer_note"]
        assert "requires_manual_review_before_transform" in row["reviewer_note"]
    assert {path: _sha256(path) for path in [template_csv, *decision_paths]} == input_hashes
    assert not list(tmp_path.rglob("*.sdf"))
