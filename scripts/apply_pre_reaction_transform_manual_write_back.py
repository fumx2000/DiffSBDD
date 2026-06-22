#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


APPROVAL_PHRASE = "APPROVE_PRE_REACTION_WRITE_BACK_STEP_8L"
WRITE_BACK_NOTE = (
    "manual_write_back_performed_after_explicit_human_approval;"
    f"approval_phrase={APPROVAL_PHRASE};"
    "no_pre_reaction_sdf_generated;"
    "not_training_ready;"
    "no_raw_or_repaired_sdf_modified"
)

REPORT_COLUMNS = [
    "sample_id",
    "approval_phrase_used",
    "write_back_status",
    "manual_covalent_bond_to_remove",
    "manual_bond_order_to_restore",
    "manual_boundary_resolution",
    "manual_atoms_requiring_charge_check",
    "manual_atoms_requiring_valence_check",
    "reviewer_decision",
    "review_status",
    "requires_manual_review",
    "pre_reaction_transform_ready",
    "training_ready",
    "decision_csv_modified",
    "pre_reaction_sdf_generated",
    "raw_ligand_sdf_modified",
    "repaired_trial_sdf_modified",
    "manifest_modified",
    "reviewer_note",
]


def read_csv(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: str | Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def index_by_sample(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["sample_id"]: row for row in rows}


def validate_approval(approval_phrase: str) -> None:
    if approval_phrase != APPROVAL_PHRASE:
        raise ValueError(f"approval phrase mismatch; expected {APPROVAL_PHRASE}")


def validate_plan_row(plan: dict[str, str]) -> None:
    if plan.get("approval_phrase_required", "") != APPROVAL_PHRASE:
        raise ValueError(f"plan approval phrase mismatch for {plan['sample_id']}")
    if plan.get("plan_status", "") != "awaiting_explicit_human_approval":
        raise ValueError(f"plan is not awaiting explicit approval for {plan['sample_id']}")
    if plan.get("explicit_human_approval_required", "") != "true":
        raise ValueError(f"plan does not require explicit approval for {plan['sample_id']}")
    if plan.get("write_back_allowed_by_script", "") != "false":
        raise ValueError(f"plan unexpectedly allows script write-back for {plan['sample_id']}")
    if plan.get("proposed_pre_reaction_transform_ready", "") != "false":
        raise ValueError(f"plan unexpectedly marks transform ready for {plan['sample_id']}")
    if plan.get("proposed_training_ready", "") != "false":
        raise ValueError(f"plan unexpectedly marks training ready for {plan['sample_id']}")


def append_note(existing_note: str, new_note: str) -> str:
    if not existing_note:
        return new_note
    return f"{existing_note};{new_note}"


def apply_write_back_rows(
    *,
    decision_rows: list[dict[str, str]],
    plan_rows: list[dict[str, str]],
    approval_phrase: str,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    validate_approval(approval_phrase)
    plan_by_sample = index_by_sample(plan_rows)
    updated_rows: list[dict[str, str]] = []
    report_rows: list[dict[str, str]] = []
    for decision in decision_rows:
        sample_id = decision["sample_id"]
        if sample_id not in plan_by_sample:
            raise ValueError(f"missing write-back plan row for {sample_id}")
        plan = plan_by_sample[sample_id]
        validate_plan_row(plan)

        updated = dict(decision)
        updated["manual_covalent_bond_to_remove"] = plan["proposed_manual_covalent_bond_to_remove"]
        updated["manual_bond_order_to_restore"] = plan["proposed_manual_bond_order_to_restore"]
        updated["manual_boundary_resolution"] = plan["proposed_manual_boundary_resolution"]
        updated["manual_atoms_requiring_charge_check"] = plan["proposed_manual_atoms_requiring_charge_check"]
        updated["manual_atoms_requiring_valence_check"] = plan["proposed_manual_atoms_requiring_valence_check"]
        updated["reviewer_decision"] = "approved"
        updated["review_status"] = "reviewed"
        updated["requires_manual_review"] = "false"
        updated["pre_reaction_transform_ready"] = "false"
        updated["training_ready"] = "false"
        updated["reviewer_note"] = append_note(updated.get("reviewer_note", ""), WRITE_BACK_NOTE)
        updated_rows.append(updated)

        report_rows.append(
            {
                "sample_id": sample_id,
                "approval_phrase_used": approval_phrase,
                "write_back_status": "written_after_explicit_human_approval",
                "manual_covalent_bond_to_remove": updated["manual_covalent_bond_to_remove"],
                "manual_bond_order_to_restore": updated["manual_bond_order_to_restore"],
                "manual_boundary_resolution": updated["manual_boundary_resolution"],
                "manual_atoms_requiring_charge_check": updated["manual_atoms_requiring_charge_check"],
                "manual_atoms_requiring_valence_check": updated["manual_atoms_requiring_valence_check"],
                "reviewer_decision": updated["reviewer_decision"],
                "review_status": updated["review_status"],
                "requires_manual_review": updated["requires_manual_review"],
                "pre_reaction_transform_ready": updated["pre_reaction_transform_ready"],
                "training_ready": updated["training_ready"],
                "decision_csv_modified": "true",
                "pre_reaction_sdf_generated": "false",
                "raw_ligand_sdf_modified": "false",
                "repaired_trial_sdf_modified": "false",
                "manifest_modified": "false",
                "reviewer_note": WRITE_BACK_NOTE,
            }
        )
    return updated_rows, report_rows


def write_report(rows: list[dict[str, str]], output_report_csv: str | Path) -> None:
    write_csv(output_report_csv, REPORT_COLUMNS, rows)


def build_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Pre-Reaction Transform Manual Write-Back Summary",
        "",
        "This write-back was performed only after explicit human approval.",
        "",
        f"- Approval phrase: {APPROVAL_PHRASE}",
        "- It updated only the manual decision draft CSV.",
        "- It did not create pre-reaction SDF files.",
        "- It did not modify raw ligand SDF files.",
        "- It did not modify repaired trial SDF files.",
        "- It did not modify manifest files.",
        "- It did not mark samples as training-ready.",
        "- It did not run training or fine-tuning.",
        "",
        "| sample_id | manual_covalent_bond_to_remove | manual_bond_order_to_restore | manual_boundary_resolution | reviewer_decision | review_status | requires_manual_review | pre_reaction_transform_ready | training_ready | write_back_status |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["sample_id"],
                    row["manual_covalent_bond_to_remove"],
                    row["manual_bond_order_to_restore"],
                    row["manual_boundary_resolution"],
                    row["reviewer_decision"],
                    row["review_status"],
                    row["requires_manual_review"],
                    row["pre_reaction_transform_ready"],
                    row["training_ready"],
                    row["write_back_status"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- Manual decision draft was updated.",
            "- No pre-reaction SDF was generated.",
            "- No sample is pre-reaction-transform-ready yet.",
            "- No sample is training-ready.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def apply_write_back(
    *,
    decision_csv: str | Path,
    plan_csv: str | Path,
    approval_phrase: str,
    output_report_csv: str | Path,
    output_md: str | Path,
) -> list[dict[str, str]]:
    decision_fields, decision_rows = read_csv(decision_csv)
    _, plan_rows = read_csv(plan_csv)
    updated_rows, report_rows = apply_write_back_rows(
        decision_rows=decision_rows,
        plan_rows=plan_rows,
        approval_phrase=approval_phrase,
    )
    write_csv(decision_csv, decision_fields, updated_rows)
    write_report(report_rows, output_report_csv)
    write_markdown(build_markdown(report_rows), output_md)
    return report_rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply pre-reaction transform manual write-back after approval.")
    parser.add_argument("--decision_csv", type=Path, required=True)
    parser.add_argument("--plan_csv", type=Path, required=True)
    parser.add_argument("--approval_phrase", required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command writes back only to the manual decision draft CSV.")
    print("warning: it does not generate pre-reaction SDF files.")
    print("warning: it does not modify raw or repaired trial SDF files.")
    report_rows = apply_write_back(
        decision_csv=args.decision_csv,
        plan_csv=args.plan_csv,
        approval_phrase=args.approval_phrase,
        output_report_csv=args.output_report_csv,
        output_md=args.output_md,
    )
    print(f"wrote manual write-back report: {args.output_report_csv}")
    print(f"wrote manual write-back summary: {args.output_md}")
    for row in report_rows:
        print(
            f"{row['sample_id']}: "
            f"manual_covalent_bond_to_remove={row['manual_covalent_bond_to_remove']} "
            f"manual_bond_order_to_restore={row['manual_bond_order_to_restore']} "
            f"reviewer_decision={row['reviewer_decision']} "
            f"pre_reaction_transform_ready={row['pre_reaction_transform_ready']} "
            f"training_ready={row['training_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
