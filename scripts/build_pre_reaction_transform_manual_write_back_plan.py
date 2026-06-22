#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


TARGET_DECISION_CSV = "data/derived/covalent_small/pre_reaction_graph/pre_reaction_transform_manual_decision_draft.csv"
APPROVAL_PHRASE = "APPROVE_PRE_REACTION_WRITE_BACK_STEP_8L"
DECISION_SOURCE = "pre_reaction_transform_manual_decision_proposal_check"
PLAN_STATUS = "awaiting_explicit_human_approval"
REVIEWER_NOTE = (
    "plan_only_no_write_back_performed;"
    "explicit_human_approval_required;"
    "no_pre_reaction_sdf_generated;"
    "not_training_ready;"
    "no_raw_or_repaired_sdf_modified"
)

PLAN_COLUMNS = [
    "sample_id",
    "proposal_check_status",
    "can_consider_manual_write_back",
    "target_decision_csv",
    "proposed_manual_covalent_bond_to_remove",
    "proposed_manual_bond_order_to_restore",
    "proposed_manual_boundary_resolution",
    "proposed_manual_atoms_requiring_charge_check",
    "proposed_manual_atoms_requiring_valence_check",
    "proposed_reviewer_decision",
    "proposed_review_status",
    "proposed_requires_manual_review",
    "proposed_pre_reaction_transform_ready",
    "proposed_training_ready",
    "write_back_allowed_by_script",
    "explicit_human_approval_required",
    "approval_phrase_required",
    "plan_status",
    "blocking_reasons",
    "reviewer_note",
    "decision_source",
]


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def index_by_sample(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["sample_id"]: row for row in rows}


def can_use_check_row(check_row: dict[str, str]) -> bool:
    return (
        check_row.get("proposal_check_status", "") == "consistent_proposal_only"
        and check_row.get("can_consider_manual_write_back", "") == "true"
    )


def build_blocking_reasons(proposal: dict[str, str], check_row: dict[str, str] | None, decision_row: dict[str, str] | None) -> list[str]:
    reasons: list[str] = []
    if check_row is None:
        reasons.append("proposal_check_row_missing")
    elif not can_use_check_row(check_row):
        if check_row.get("proposal_check_status", "") != "consistent_proposal_only":
            reasons.append("proposal_check_status_not_consistent")
        if check_row.get("can_consider_manual_write_back", "") != "true":
            reasons.append("can_consider_manual_write_back_not_true")
        if check_row.get("blocking_reasons", ""):
            reasons.append(check_row["blocking_reasons"])
    if decision_row is None:
        reasons.append("decision_draft_row_missing")
    if not proposal.get("proposed_manual_covalent_bond_to_remove", ""):
        reasons.append("proposed_manual_covalent_bond_to_remove_missing")
    if not proposal.get("proposed_manual_bond_order_to_restore", ""):
        reasons.append("proposed_manual_bond_order_to_restore_missing")
    if not proposal.get("proposed_manual_boundary_resolution", ""):
        reasons.append("proposed_manual_boundary_resolution_missing")
    return reasons


def build_plan_rows(
    *,
    proposal_csv: str | Path,
    proposal_check_csv: str | Path,
    decision_csv: str | Path,
) -> list[dict[str, str]]:
    proposal_rows = read_csv(proposal_csv)
    check_by_sample = index_by_sample(read_csv(proposal_check_csv))
    decision_by_sample = index_by_sample(read_csv(decision_csv))

    rows: list[dict[str, str]] = []
    for proposal in sorted(proposal_rows, key=lambda row: row["sample_id"]):
        sample_id = proposal["sample_id"]
        check_row = check_by_sample.get(sample_id)
        decision_row = decision_by_sample.get(sample_id)
        reasons = build_blocking_reasons(proposal, check_row, decision_row)
        plan_can_propose = not reasons

        rows.append(
            {
                "sample_id": sample_id,
                "proposal_check_status": check_row.get("proposal_check_status", "") if check_row else "",
                "can_consider_manual_write_back": check_row.get("can_consider_manual_write_back", "") if check_row else "false",
                "target_decision_csv": TARGET_DECISION_CSV,
                "proposed_manual_covalent_bond_to_remove": proposal["proposed_manual_covalent_bond_to_remove"]
                if plan_can_propose
                else "",
                "proposed_manual_bond_order_to_restore": proposal["proposed_manual_bond_order_to_restore"]
                if plan_can_propose
                else "",
                "proposed_manual_boundary_resolution": proposal["proposed_manual_boundary_resolution"] if plan_can_propose else "",
                "proposed_manual_atoms_requiring_charge_check": proposal["ligand_reactive_atom_candidate"]
                if plan_can_propose
                else "",
                "proposed_manual_atoms_requiring_valence_check": proposal["accepted_warhead_atoms"] if plan_can_propose else "",
                "proposed_reviewer_decision": "approved_candidate_after_manual_confirmation" if plan_can_propose else "",
                "proposed_review_status": "reviewed_after_manual_confirmation" if plan_can_propose else "",
                "proposed_requires_manual_review": "false_after_manual_confirmation" if plan_can_propose else "",
                "proposed_pre_reaction_transform_ready": "false",
                "proposed_training_ready": "false",
                "write_back_allowed_by_script": "false",
                "explicit_human_approval_required": "true",
                "approval_phrase_required": APPROVAL_PHRASE,
                "plan_status": PLAN_STATUS if plan_can_propose else "blocked",
                "blocking_reasons": ";".join(reasons),
                "reviewer_note": REVIEWER_NOTE,
                "decision_source": DECISION_SOURCE,
            }
        )
    return rows


def write_csv(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PLAN_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Pre-Reaction Transform Manual Write-Back Plan",
        "",
        "This is a write-back plan only.",
        "",
        "- It does not write back to decision draft files.",
        "- It does not approve any transform.",
        "- It does not create pre-reaction SDF files.",
        "- It does not modify raw ligand SDF files.",
        "- It does not modify repaired trial SDF files.",
        "- It does not mark samples as training-ready.",
        "",
        "| sample_id | proposed_manual_covalent_bond_to_remove | proposed_manual_bond_order_to_restore | proposed_manual_boundary_resolution | write_back_allowed_by_script | explicit_human_approval_required | approval_phrase_required | plan_status |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["sample_id"],
                    row["proposed_manual_covalent_bond_to_remove"],
                    row["proposed_manual_bond_order_to_restore"],
                    row["proposed_manual_boundary_resolution"],
                    row["write_back_allowed_by_script"],
                    row["explicit_human_approval_required"],
                    row["approval_phrase_required"],
                    row["plan_status"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- No decision draft was modified.",
            "- Explicit human approval is required before write-back.",
            "- No pre-reaction SDF was generated.",
            "- No sample is training-ready.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build pre-reaction transform manual write-back plan.")
    parser.add_argument("--proposal_csv", type=Path, required=True)
    parser.add_argument("--proposal_check_csv", type=Path, required=True)
    parser.add_argument("--decision_csv", type=Path, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command writes a plan only.")
    print("warning: it does not write back to decision draft files.")
    print("warning: it does not generate pre-reaction SDF files.")
    rows = build_plan_rows(
        proposal_csv=args.proposal_csv,
        proposal_check_csv=args.proposal_check_csv,
        decision_csv=args.decision_csv,
    )
    write_csv(rows, args.output_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote pre-reaction transform manual write-back plan CSV: {args.output_csv}")
    print(f"wrote pre-reaction transform manual write-back plan Markdown: {args.output_md}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"proposed_manual_covalent_bond_to_remove={row['proposed_manual_covalent_bond_to_remove']} "
            f"proposed_manual_bond_order_to_restore={row['proposed_manual_bond_order_to_restore']} "
            f"write_back_allowed_by_script={row['write_back_allowed_by_script']} "
            f"plan_status={row['plan_status']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
