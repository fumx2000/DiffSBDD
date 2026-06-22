#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


REPORT_COLUMNS = [
    "sample_id",
    "proposed_manual_covalent_bond_to_remove",
    "selected_bond_order_candidate",
    "proposed_manual_bond_order_to_restore",
    "high_priority_candidate_count",
    "proposal_status",
    "can_write_back_to_decision_draft",
    "requires_manual_review",
    "pre_reaction_transform_ready",
    "training_ready",
    "proposal_check_status",
    "proposal_consistent_with_decision_draft",
    "proposal_consistent_with_bond_candidate_review",
    "can_consider_manual_write_back",
    "blocking_reasons",
    "recommended_next_action",
]

CONSISTENT_STATUS = "consistent_proposal_only"
BLOCKED_STATUS = "blocked"
NEXT_ACTION_CONSISTENT = "manual_confirmation_required_before_write_back"
NEXT_ACTION_BLOCKED = "fix_proposal_consistency_before_manual_write_back"


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def bool_str(value: bool) -> str:
    return str(value).lower()


def index_by_sample(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["sample_id"]: row for row in rows}


def index_candidates(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["sample_id"], row["candidate_bond"]): row for row in rows}


def decision_consistency_reasons(
    proposal: dict[str, str],
    decision_by_sample: dict[str, dict[str, str]],
) -> list[str]:
    decision = decision_by_sample.get(proposal["sample_id"])
    if decision is None:
        return ["proposal_decision_draft_mismatch"]
    checks = [
        (
            proposal.get("proposed_manual_covalent_bond_to_remove", ""),
            decision.get("proposed_covalent_bond_to_remove_candidate", ""),
        ),
        (
            proposal.get("ligand_reactive_atom_candidate", ""),
            decision.get("ligand_reactive_atom_candidate", ""),
        ),
        (
            proposal.get("accepted_warhead_atoms", ""),
            decision.get("accepted_warhead_atoms", ""),
        ),
        (
            proposal.get("unresolved_boundary_atoms", ""),
            decision.get("unresolved_boundary_atoms", ""),
        ),
    ]
    if any(left != right for left, right in checks):
        return ["proposal_decision_draft_mismatch"]
    return []


def candidate_consistency_reasons(
    proposal: dict[str, str],
    candidate_by_key: dict[tuple[str, str], dict[str, str]],
) -> list[str]:
    reasons: list[str] = []
    selected_bond = proposal.get("selected_bond_order_candidate", "")
    candidate = candidate_by_key.get((proposal["sample_id"], selected_bond))
    if candidate is None:
        reasons.append("selected_bond_order_candidate_not_found")
    else:
        if candidate.get("candidate_priority", "") != "high":
            reasons.append("selected_candidate_not_high_priority")
        if candidate.get("candidate_reason", "") != "touches_ligand_reactive_atom_candidate":
            reasons.append("selected_candidate_not_touching_reactive_atom")
        if candidate.get("proposed_restore_bond_order", "") != "double_candidate":
            reasons.append("proposed_restore_not_double_candidate")
    if proposal.get("proposed_manual_bond_order_to_restore", "") != f"{selected_bond}:double":
        reasons.append("proposed_restore_not_double_candidate")
    if proposal.get("high_priority_candidate_count", "") != "1":
        reasons.append("high_priority_candidate_count_not_one")
    return reasons


def proposal_state_reasons(proposal: dict[str, str]) -> list[str]:
    reasons: list[str] = []
    if proposal.get("proposal_status", "") != "proposal_only_not_approved":
        reasons.append("proposal_status_not_proposal_only")
    if proposal.get("can_write_back_to_decision_draft", "") != "false":
        reasons.append("can_write_back_not_false")
    if proposal.get("requires_manual_review", "") != "true":
        reasons.append("requires_manual_review_not_true")
    if proposal.get("pre_reaction_transform_ready", "") != "false":
        reasons.append("pre_reaction_transform_ready_not_false")
    if proposal.get("training_ready", "") != "false":
        reasons.append("training_ready_not_false")
    return reasons


def check_proposal_row(
    proposal: dict[str, str],
    decision_by_sample: dict[str, dict[str, str]],
    candidate_by_key: dict[tuple[str, str], dict[str, str]],
) -> dict[str, str]:
    decision_reasons = decision_consistency_reasons(proposal, decision_by_sample)
    candidate_reasons = candidate_consistency_reasons(proposal, candidate_by_key)
    state_reasons = proposal_state_reasons(proposal)
    decision_consistent = not decision_reasons
    candidate_consistent = not candidate_reasons
    blocking_reasons = decision_reasons + candidate_reasons + state_reasons
    can_consider_write_back = not blocking_reasons
    return {
        "sample_id": proposal["sample_id"],
        "proposed_manual_covalent_bond_to_remove": proposal["proposed_manual_covalent_bond_to_remove"],
        "selected_bond_order_candidate": proposal["selected_bond_order_candidate"],
        "proposed_manual_bond_order_to_restore": proposal["proposed_manual_bond_order_to_restore"],
        "high_priority_candidate_count": proposal["high_priority_candidate_count"],
        "proposal_status": proposal["proposal_status"],
        "can_write_back_to_decision_draft": proposal["can_write_back_to_decision_draft"],
        "requires_manual_review": proposal["requires_manual_review"],
        "pre_reaction_transform_ready": proposal["pre_reaction_transform_ready"],
        "training_ready": proposal["training_ready"],
        "proposal_check_status": CONSISTENT_STATUS if can_consider_write_back else BLOCKED_STATUS,
        "proposal_consistent_with_decision_draft": bool_str(decision_consistent),
        "proposal_consistent_with_bond_candidate_review": bool_str(candidate_consistent),
        "can_consider_manual_write_back": bool_str(can_consider_write_back),
        "blocking_reasons": ";".join(blocking_reasons),
        "recommended_next_action": NEXT_ACTION_CONSISTENT if can_consider_write_back else NEXT_ACTION_BLOCKED,
    }


def build_report_rows(
    *,
    proposal_csv: str | Path,
    decision_csv: str | Path,
    bond_candidate_csv: str | Path,
) -> list[dict[str, str]]:
    proposal_rows = read_csv(proposal_csv)
    decision_by_sample = index_by_sample(read_csv(decision_csv))
    candidate_by_key = index_candidates(read_csv(bond_candidate_csv))
    return [
        check_proposal_row(proposal, decision_by_sample, candidate_by_key)
        for proposal in sorted(proposal_rows, key=lambda row: row["sample_id"])
    ]


def write_csv(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Pre-Reaction Transform Manual Decision Proposal Check Summary",
        "",
        "This is a proposal consistency checker only.",
        "",
        "- It does not write back to decision draft files.",
        "- It does not approve any transform.",
        "- It does not create pre-reaction SDF files.",
        "- It does not modify raw ligand SDF files.",
        "- It does not modify repaired trial SDF files.",
        "- It does not mark samples as training-ready.",
        "",
        "| sample_id | proposal_check_status | proposal_consistent_with_decision_draft | proposal_consistent_with_bond_candidate_review | can_consider_manual_write_back | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["sample_id"],
                    row["proposal_check_status"],
                    row["proposal_consistent_with_decision_draft"],
                    row["proposal_consistent_with_bond_candidate_review"],
                    row["can_consider_manual_write_back"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- All proposals are consistency-checked only.",
            "- No decision draft was modified.",
            "- No sample is approved for transform.",
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
    parser = argparse.ArgumentParser(description="Check pre-reaction transform manual decision proposal.")
    parser.add_argument("--proposal_csv", type=Path, required=True)
    parser.add_argument("--decision_csv", type=Path, required=True)
    parser.add_argument("--bond_candidate_csv", type=Path, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command checks proposal consistency only.")
    print("warning: it does not write back to decision draft files.")
    print("warning: it does not generate pre-reaction SDF files.")
    rows = build_report_rows(
        proposal_csv=args.proposal_csv,
        decision_csv=args.decision_csv,
        bond_candidate_csv=args.bond_candidate_csv,
    )
    write_csv(rows, args.output_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote proposal check report: {args.output_csv}")
    print(f"wrote proposal check summary: {args.output_md}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"proposal_check_status={row['proposal_check_status']} "
            f"can_consider_manual_write_back={row['can_consider_manual_write_back']} "
            f"blocking_reasons={row['blocking_reasons']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
