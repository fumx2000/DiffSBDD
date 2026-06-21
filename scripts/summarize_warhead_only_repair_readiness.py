#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


SUMMARY_COLUMNS = [
    "sample_id",
    "qa_total_rows",
    "qa_passed_rows",
    "qa_failed_rows",
    "transferred_count",
    "kept_count",
    "blocked_count",
    "coordinate_hash_same_all",
    "raw_sdf_hash_same_all",
    "blocked_bonds_unchanged",
    "boundary_touches_blocked",
    "manual_accept_candidate_count",
    "manual_unresolved_count",
    "all_warhead_atoms_accepted",
    "has_unresolved_boundary",
    "cross_boundary_transfer_ready",
    "derived_trial_safe",
    "training_ready",
    "pre_reaction_graph_ready",
    "recommended_next_action",
]

NEXT_ACTION = "manual_boundary_review_or_pre_reaction_graph_design_before_training_ready"


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_manual_summary(path: str | Path) -> dict[str, dict[str, str]]:
    return {row["sample_id"]: row for row in read_csv(path)}


def summarize_qa_rows(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["sample_id"]].append(row)

    summaries: dict[str, dict[str, str]] = {}
    for sample_id, sample_rows in sorted(grouped.items()):
        counts = Counter(row["action_applied"] for row in sample_rows)
        status_counts = Counter(row["qa_status"] for row in sample_rows)
        blocked_rows = [row for row in sample_rows if row["action_applied"] == "blocked"]
        boundary_rows = [row for row in sample_rows if parse_bool(row["touched_unresolved_boundary"])]
        coordinate_hash_same_all = all(parse_bool(row["coordinate_hash_same"]) for row in sample_rows)
        raw_sdf_hash_same_all = all(parse_bool(row["raw_sdf_hash_same"]) for row in sample_rows)
        blocked_bonds_unchanged = all(
            row["raw_current_bond_type"] == row["repaired_current_bond_type"] for row in blocked_rows
        )
        boundary_touches_blocked = all(row["action_applied"] == "blocked" for row in boundary_rows)
        summaries[sample_id] = {
            "sample_id": sample_id,
            "qa_total_rows": str(len(sample_rows)),
            "qa_passed_rows": str(status_counts.get("passed", 0)),
            "qa_failed_rows": str(status_counts.get("failed", 0)),
            "transferred_count": str(counts.get("transferred", 0)),
            "kept_count": str(counts.get("kept", 0)),
            "blocked_count": str(counts.get("blocked", 0)),
            "coordinate_hash_same_all": str(coordinate_hash_same_all).lower(),
            "raw_sdf_hash_same_all": str(raw_sdf_hash_same_all).lower(),
            "blocked_bonds_unchanged": str(blocked_bonds_unchanged).lower(),
            "boundary_touches_blocked": str(boundary_touches_blocked).lower(),
        }
    return summaries


def build_readiness_rows(
    *,
    qa_csv: str | Path,
    manual_decision_summary_csv: str | Path,
) -> list[dict[str, str]]:
    qa_summaries = summarize_qa_rows(read_csv(qa_csv))
    manual_summaries = load_manual_summary(manual_decision_summary_csv)
    rows: list[dict[str, str]] = []
    for sample_id in sorted(qa_summaries):
        if sample_id not in manual_summaries:
            raise ValueError(f"sample_id missing from manual decision summary: {sample_id}")
        qa = qa_summaries[sample_id]
        manual = manual_summaries[sample_id]
        qa_failed_rows = int(qa["qa_failed_rows"])
        all_warhead_atoms_accepted = parse_bool(manual["all_warhead_atoms_accepted"])
        has_unresolved_boundary = parse_bool(manual["has_unresolved_boundary"])
        cross_boundary_transfer_ready = all_warhead_atoms_accepted and not has_unresolved_boundary
        derived_trial_safe = (
            qa_failed_rows == 0
            and parse_bool(qa["coordinate_hash_same_all"])
            and parse_bool(qa["raw_sdf_hash_same_all"])
            and parse_bool(qa["blocked_bonds_unchanged"])
            and parse_bool(qa["boundary_touches_blocked"])
        )
        rows.append(
            {
                **qa,
                "manual_accept_candidate_count": manual["accept_candidate_count"],
                "manual_unresolved_count": manual["unresolved_count"],
                "all_warhead_atoms_accepted": manual["all_warhead_atoms_accepted"],
                "has_unresolved_boundary": manual["has_unresolved_boundary"],
                "cross_boundary_transfer_ready": str(cross_boundary_transfer_ready).lower(),
                "derived_trial_safe": str(derived_trial_safe).lower(),
                "training_ready": "false",
                "pre_reaction_graph_ready": "false",
                "recommended_next_action": NEXT_ACTION,
            }
        )
    return rows


def write_csv(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Warhead-Only Repair Readiness Summary",
        "",
        "This is a readiness summary only.",
        "",
        "- It does not modify raw ligand SDF files.",
        "- It does not modify repaired trial SDF files.",
        "- It does not create pre-reaction graphs.",
        "- It does not modify manifest files.",
        "- It does not mark samples as training-ready.",
        "",
        "| sample_id | derived_trial_safe | training_ready | pre_reaction_graph_ready | qa_passed_rows | qa_failed_rows | manual_unresolved_count | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["sample_id"],
                    row["derived_trial_safe"],
                    row["training_ready"],
                    row["pre_reaction_graph_ready"],
                    row["qa_passed_rows"],
                    row["qa_failed_rows"],
                    row["manual_unresolved_count"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    lines.append("")

    for row in rows:
        reason = (
            "has unresolved linker/local boundary atoms; cross-boundary transfer is not ready; "
            "pre-reaction graph is not ready"
        )
        lines.extend(
            [
                f"## {row['sample_id']}",
                "",
                f"- derived_trial_safe: {row['derived_trial_safe']}",
                f"- training_ready: {row['training_ready']}",
                f"- reason not training-ready: {reason}.",
                f"- recommended_next_action: `{row['recommended_next_action']}`",
                "",
            ]
        )

    all_safe = all(parse_bool(row["derived_trial_safe"]) for row in rows)
    any_training_ready = any(parse_bool(row["training_ready"]) for row in rows)
    lines.extend(
        [
            "## Global Conclusion",
            "",
            f"- All three repaired trial SDFs are safe derived curation artifacts: {str(all_safe).lower()}.",
            f"- No sample is training-ready: {str(not any_training_ready).lower()}.",
            "- The next safe direction is manual boundary review and/or pre-reaction graph design.",
            "- Do not use these derived SDFs for model training yet.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize warhead-only repair readiness.")
    parser.add_argument("--qa_csv", type=Path, required=True)
    parser.add_argument("--manual_decision_summary_csv", type=Path, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this is a readiness summary only.")
    print("warning: this command does not modify raw or repaired trial SDF files.")
    print("warning: this command does not create pre-reaction graphs.")
    rows = build_readiness_rows(
        qa_csv=args.qa_csv,
        manual_decision_summary_csv=args.manual_decision_summary_csv,
    )
    write_csv(rows, args.output_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote readiness CSV: {args.output_csv}")
    print(f"wrote readiness Markdown: {args.output_md}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"derived_trial_safe={row['derived_trial_safe']} "
            f"training_ready={row['training_ready']} "
            f"pre_reaction_graph_ready={row['pre_reaction_graph_ready']} "
            f"next={row['recommended_next_action']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
