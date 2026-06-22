#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


REVIEW_COLUMNS = [
    "sample_id",
    "ligand_reactive_atom_candidate",
    "accepted_warhead_atoms",
    "candidate_bond_atom_1",
    "candidate_bond_atom_2",
    "candidate_bond",
    "current_bond_order_in_repaired_sdf",
    "proposed_restore_bond_order",
    "candidate_reason",
    "candidate_priority",
    "requires_manual_review",
    "reviewer_decision",
    "reviewer_note",
    "review_status",
    "decision_source",
]

REVIEWER_NOTE = (
    "candidate_only_no_bond_order_restored;"
    "manual_chemistry_review_required;"
    "no_pre_reaction_sdf_generated;"
    "not_training_ready"
)


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_atom_set(value: str) -> set[int]:
    return {int(part) for part in value.split() if part.strip()}


def parse_v2000_bonds(path: str | Path) -> list[tuple[int, int, str]]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    if len(lines) < 4:
        raise ValueError(f"SDF is too short: {path}")
    counts = lines[3]
    try:
        atom_count = int(counts[0:3])
        bond_count = int(counts[3:6])
    except ValueError as exc:
        raise ValueError(f"could not parse V2000 counts line in {path}: {counts!r}") from exc
    bond_start = 4 + atom_count
    bond_lines = lines[bond_start : bond_start + bond_count]
    bonds: list[tuple[int, int, str]] = []
    for line in bond_lines:
        if not line.strip():
            continue
        atom_a = int(line[0:3]) - 1
        atom_b = int(line[3:6]) - 1
        order = line[6:9].strip()
        bonds.append((min(atom_a, atom_b), max(atom_a, atom_b), order))
    return bonds


def map_sdf_paths_to_samples(sample_ids: set[str], sdf_paths: list[Path]) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for sample_id in sample_ids:
        matches = [path for path in sdf_paths if path.name.startswith(sample_id)]
        if len(matches) != 1:
            raise ValueError(f"expected exactly one SDF path for {sample_id}, found {len(matches)}")
        mapping[sample_id] = matches[0]
    return mapping


def build_candidate_rows(*, decision_csv: str | Path, sdf_paths: list[Path]) -> list[dict[str, str]]:
    decision_rows = read_csv(decision_csv)
    sdf_by_sample = map_sdf_paths_to_samples({row["sample_id"] for row in decision_rows}, sdf_paths)
    output_rows: list[dict[str, str]] = []
    for decision in sorted(decision_rows, key=lambda row: row["sample_id"]):
        sample_id = decision["sample_id"]
        reactive_atom = int(decision["ligand_reactive_atom_candidate"])
        accepted_atoms = parse_atom_set(decision["accepted_warhead_atoms"])
        bonds = parse_v2000_bonds(sdf_by_sample[sample_id])
        warhead_bonds = [(a, b, order) for a, b, order in bonds if a in accepted_atoms and b in accepted_atoms]
        reactive_neighbors = {
            b if a == reactive_atom else a
            for a, b, _ in warhead_bonds
            if reactive_atom in {a, b}
        }
        candidate_bonds: list[tuple[int, int, str, str, str]] = []
        for atom_a, atom_b, order in warhead_bonds:
            if reactive_atom in {atom_a, atom_b}:
                candidate_bonds.append(
                    (
                        atom_a,
                        atom_b,
                        order,
                        "touches_ligand_reactive_atom_candidate",
                        "high",
                    )
                )
            elif atom_a in reactive_neighbors or atom_b in reactive_neighbors:
                candidate_bonds.append(
                    (
                        atom_a,
                        atom_b,
                        order,
                        "adjacent_warhead_internal_bond_candidate",
                        "medium",
                    )
                )
        for atom_a, atom_b, order, reason, priority in sorted(candidate_bonds):
            output_rows.append(
                {
                    "sample_id": sample_id,
                    "ligand_reactive_atom_candidate": str(reactive_atom),
                    "accepted_warhead_atoms": decision["accepted_warhead_atoms"],
                    "candidate_bond_atom_1": str(atom_a),
                    "candidate_bond_atom_2": str(atom_b),
                    "candidate_bond": f"{atom_a}-{atom_b}",
                    "current_bond_order_in_repaired_sdf": order,
                    "proposed_restore_bond_order": "double_candidate",
                    "candidate_reason": reason,
                    "candidate_priority": priority,
                    "requires_manual_review": "true",
                    "reviewer_decision": "",
                    "reviewer_note": REVIEWER_NOTE,
                    "review_status": "draft_not_reviewed",
                    "decision_source": "pre_reaction_transform_manual_decision_draft",
                }
            )
    return output_rows


def write_csv(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(rows: list[dict[str, str]]) -> str:
    rows_by_sample: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        rows_by_sample[row["sample_id"]].append(row)
    lines = [
        "# Pre-Reaction Bond-Order Restore Candidate Review",
        "",
        "This is a candidate review only.",
        "",
        "- It does not restore any bond order.",
        "- It does not create pre-reaction SDF files.",
        "- It does not modify raw ligand SDF files.",
        "- It does not modify repaired trial SDF files.",
        "- It does not mark samples as training-ready.",
        "",
    ]
    for sample_id in sorted(rows_by_sample):
        lines.extend(
            [
                f"## {sample_id}",
                "",
                "| sample_id | candidate_bond | current_bond_order_in_repaired_sdf | proposed_restore_bond_order | candidate_reason | candidate_priority | review_status |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for row in rows_by_sample[sample_id]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        row["sample_id"],
                        row["candidate_bond"],
                        row["current_bond_order_in_repaired_sdf"],
                        row["proposed_restore_bond_order"],
                        row["candidate_reason"],
                        row["candidate_priority"],
                        row["review_status"],
                    ]
                )
                + " |"
            )
        lines.append("")
    lines.extend(
        [
            "## Global Conclusion",
            "",
            "- Bond-order restore remains manual-review-only.",
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
    parser = argparse.ArgumentParser(description="Build pre-reaction bond-order restore candidate review.")
    parser.add_argument("--decision_csv", type=Path, required=True)
    parser.add_argument("--sdf_paths", type=Path, nargs="+", required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command builds a candidate review only.")
    print("warning: it does not restore bond order or generate pre-reaction SDF files.")
    rows = build_candidate_rows(decision_csv=args.decision_csv, sdf_paths=args.sdf_paths)
    write_csv(rows, args.output_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote bond-order restore candidate review: {args.output_csv}")
    print(f"wrote bond-order restore candidate Markdown: {args.output_md}")
    rows_by_sample: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        rows_by_sample[row["sample_id"]].append(row["candidate_bond"])
    for sample_id in sorted(rows_by_sample):
        print(f"{sample_id}: candidate_bonds={' '.join(rows_by_sample[sample_id])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
