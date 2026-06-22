from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from init_pre_reaction_transform_rule_template import RULE_COLUMNS, build_template_rows, write_template


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_readiness(path: Path) -> None:
    rows = [
        {
            "sample_id": "BTK_C481_6DI9",
            "qa_total_rows": "35",
            "qa_passed_rows": "35",
            "qa_failed_rows": "0",
            "transferred_count": "2",
            "kept_count": "1",
            "blocked_count": "32",
            "coordinate_hash_same_all": "true",
            "raw_sdf_hash_same_all": "true",
            "blocked_bonds_unchanged": "true",
            "boundary_touches_blocked": "true",
            "manual_accept_candidate_count": "4",
            "manual_unresolved_count": "5",
            "all_warhead_atoms_accepted": "true",
            "has_unresolved_boundary": "true",
            "cross_boundary_transfer_ready": "false",
            "derived_trial_safe": "true",
            "training_ready": "false",
            "pre_reaction_graph_ready": "false",
            "recommended_next_action": "manual_boundary_review_or_pre_reaction_graph_design_before_training_ready",
        },
        {
            "sample_id": "KRAS_G12C_5F2E",
            "qa_total_rows": "33",
            "qa_passed_rows": "33",
            "qa_failed_rows": "0",
            "transferred_count": "2",
            "kept_count": "1",
            "blocked_count": "30",
            "coordinate_hash_same_all": "true",
            "raw_sdf_hash_same_all": "true",
            "blocked_bonds_unchanged": "true",
            "boundary_touches_blocked": "true",
            "manual_accept_candidate_count": "4",
            "manual_unresolved_count": "4",
            "all_warhead_atoms_accepted": "true",
            "has_unresolved_boundary": "true",
            "cross_boundary_transfer_ready": "false",
            "derived_trial_safe": "true",
            "training_ready": "false",
            "pre_reaction_graph_ready": "false",
            "recommended_next_action": "manual_boundary_review_or_pre_reaction_graph_design_before_training_ready",
        },
        {
            "sample_id": "KRAS_G12C_6OIM",
            "qa_total_rows": "45",
            "qa_passed_rows": "45",
            "qa_failed_rows": "0",
            "transferred_count": "1",
            "kept_count": "2",
            "blocked_count": "42",
            "coordinate_hash_same_all": "true",
            "raw_sdf_hash_same_all": "true",
            "blocked_bonds_unchanged": "true",
            "boundary_touches_blocked": "true",
            "manual_accept_candidate_count": "4",
            "manual_unresolved_count": "6",
            "all_warhead_atoms_accepted": "true",
            "has_unresolved_boundary": "true",
            "cross_boundary_transfer_ready": "false",
            "derived_trial_safe": "true",
            "training_ready": "false",
            "pre_reaction_graph_ready": "false",
            "recommended_next_action": "manual_boundary_review_or_pre_reaction_graph_design_before_training_ready",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_pre_reaction_transform_rule_template_has_safe_draft_rows(tmp_path: Path) -> None:
    readiness_csv = tmp_path / "readiness.csv"
    output_csv = tmp_path / "pre_reaction_graph" / "template.csv"
    _write_readiness(readiness_csv)
    readiness_hash = _sha256(readiness_csv)

    rows = build_template_rows(readiness_csv)
    write_template(rows, output_csv)

    assert _sha256(readiness_csv) == readiness_hash
    assert output_csv.exists()
    written_rows = list(csv.DictReader(output_csv.open(newline="", encoding="utf-8")))
    assert written_rows == rows
    assert list(written_rows[0]) == RULE_COLUMNS
    assert {row["sample_id"] for row in written_rows} == {
        "BTK_C481_6DI9",
        "KRAS_G12C_5F2E",
        "KRAS_G12C_6OIM",
    }
    assert {row["requires_manual_review"] for row in written_rows} == {"true"}
    assert {row["confidence_level"] for row in written_rows} == {"draft"}
    assert {row["training_ready_candidate"] for row in written_rows} == {"false"}
    assert {row["pre_reaction_graph_ready"] for row in written_rows} == {"false"}
    assert {row["rule_status"] for row in written_rows} == {"draft_not_reviewed"}
    assert not list(tmp_path.rglob("*.sdf"))
