from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from apply_pre_reaction_transform_manual_write_back import APPROVAL_PHRASE, apply_write_back


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _decision_row(sample_id: str, reactive_atom: str, accepted: str, covalent: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "warhead_type": "toy",
        "ligand_reactive_atom_candidate": reactive_atom,
        "accepted_warhead_atoms": accepted,
        "unresolved_boundary_atoms": "boundary",
        "proposed_covalent_bond_to_remove_candidate": covalent,
        "proposed_bond_order_to_restore_candidate": "",
        "proposed_atoms_requiring_charge_check": reactive_atom,
        "proposed_atoms_requiring_valence_check": accepted,
        "boundary_resolution_required": "true",
        "manual_covalent_bond_to_remove": "",
        "manual_bond_order_to_restore": "",
        "manual_atoms_requiring_charge_check": "",
        "manual_atoms_requiring_valence_check": "",
        "manual_boundary_resolution": "",
        "reviewer_decision": "",
        "reviewer_note": "initial_note",
        "review_status": "draft_not_reviewed",
        "requires_manual_review": "true",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "decision_source": "test",
    }


def _plan_row(sample_id: str, covalent: str, restore: str, charge: str, valence: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "proposal_check_status": "consistent_proposal_only",
        "can_consider_manual_write_back": "true",
        "target_decision_csv": "data/derived/covalent_small/pre_reaction_graph/pre_reaction_transform_manual_decision_draft.csv",
        "proposed_manual_covalent_bond_to_remove": covalent,
        "proposed_manual_bond_order_to_restore": restore,
        "proposed_manual_boundary_resolution": "reviewed_no_boundary_atoms_transferred_to_pre_reaction_transform_rule_candidate",
        "proposed_manual_atoms_requiring_charge_check": charge,
        "proposed_manual_atoms_requiring_valence_check": valence,
        "proposed_reviewer_decision": "approved_candidate_after_manual_confirmation",
        "proposed_review_status": "reviewed_after_manual_confirmation",
        "proposed_requires_manual_review": "false_after_manual_confirmation",
        "proposed_pre_reaction_transform_ready": "false",
        "proposed_training_ready": "false",
        "write_back_allowed_by_script": "false",
        "explicit_human_approval_required": "true",
        "approval_phrase_required": APPROVAL_PHRASE,
        "plan_status": "awaiting_explicit_human_approval",
        "blocking_reasons": "",
        "reviewer_note": "plan_only_no_write_back_performed",
        "decision_source": "test",
    }


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    decision_csv = tmp_path / "decision.csv"
    plan_csv = tmp_path / "plan.csv"
    _write_csv(
        decision_csv,
        [
            _decision_row("BTK_C481_6DI9", "19", "17 18 19 32", "CYS:SG-19"),
            _decision_row("KRAS_G12C_5F2E", "29", "8 27 28 29", "CYS:SG-29"),
            _decision_row("KRAS_G12C_6OIM", "7", "4 5 6 7", "CYS:SG-7"),
        ],
    )
    _write_csv(
        plan_csv,
        [
            _plan_row("BTK_C481_6DI9", "CYS:SG-19", "18-19:double", "19", "17 18 19 32"),
            _plan_row("KRAS_G12C_5F2E", "CYS:SG-29", "8-29:double", "29", "8 27 28 29"),
            _plan_row("KRAS_G12C_6OIM", "CYS:SG-7", "6-7:double", "7", "4 5 6 7"),
        ],
    )
    return decision_csv, plan_csv


def test_bad_approval_phrase_fails_without_modifying_decision_csv(tmp_path: Path) -> None:
    decision_csv, plan_csv = _write_inputs(tmp_path)
    report_csv = tmp_path / "report.csv"
    output_md = tmp_path / "summary.md"
    decision_hash = _sha256(decision_csv)

    with pytest.raises(ValueError):
        apply_write_back(
            decision_csv=decision_csv,
            plan_csv=plan_csv,
            approval_phrase="WRONG",
            output_report_csv=report_csv,
            output_md=output_md,
        )

    assert _sha256(decision_csv) == decision_hash
    assert not report_csv.exists()
    assert not output_md.exists()
    assert not list(tmp_path.rglob("*.sdf"))


def test_good_approval_phrase_writes_manual_decisions_and_report(tmp_path: Path) -> None:
    decision_csv, plan_csv = _write_inputs(tmp_path)
    report_csv = tmp_path / "report.csv"
    output_md = tmp_path / "summary.md"
    plan_hash = _sha256(plan_csv)

    report_rows = apply_write_back(
        decision_csv=decision_csv,
        plan_csv=plan_csv,
        approval_phrase=APPROVAL_PHRASE,
        output_report_csv=report_csv,
        output_md=output_md,
    )

    by_sample = {row["sample_id"]: row for row in _read_csv(decision_csv)}
    assert by_sample["BTK_C481_6DI9"]["manual_covalent_bond_to_remove"] == "CYS:SG-19"
    assert by_sample["BTK_C481_6DI9"]["manual_bond_order_to_restore"] == "18-19:double"
    assert by_sample["KRAS_G12C_5F2E"]["manual_covalent_bond_to_remove"] == "CYS:SG-29"
    assert by_sample["KRAS_G12C_5F2E"]["manual_bond_order_to_restore"] == "8-29:double"
    assert by_sample["KRAS_G12C_6OIM"]["manual_covalent_bond_to_remove"] == "CYS:SG-7"
    assert by_sample["KRAS_G12C_6OIM"]["manual_bond_order_to_restore"] == "6-7:double"
    assert {row["manual_boundary_resolution"] for row in by_sample.values()} == {
        "reviewed_no_boundary_atoms_transferred_to_pre_reaction_transform_rule_candidate"
    }
    assert {row["reviewer_decision"] for row in by_sample.values()} == {"approved"}
    assert {row["review_status"] for row in by_sample.values()} == {"reviewed"}
    assert {row["requires_manual_review"] for row in by_sample.values()} == {"false"}
    assert {row["pre_reaction_transform_ready"] for row in by_sample.values()} == {"false"}
    assert {row["training_ready"] for row in by_sample.values()} == {"false"}
    assert len(report_rows) == 3
    assert report_csv.exists()
    assert output_md.exists()
    assert {row["write_back_status"] for row in _read_csv(report_csv)} == {
        "written_after_explicit_human_approval"
    }
    assert {row["decision_csv_modified"] for row in _read_csv(report_csv)} == {"true"}
    assert {row["pre_reaction_sdf_generated"] for row in _read_csv(report_csv)} == {"false"}
    assert _sha256(plan_csv) == plan_hash
    assert not list(tmp_path.rglob("*.sdf"))
