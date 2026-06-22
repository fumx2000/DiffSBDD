#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


REPORT_COLUMNS = [
    "sample_id",
    "source_repaired_sdf",
    "output_pre_reaction_sdf",
    "source_repaired_sdf_exists",
    "output_pre_reaction_sdf_exists",
    "source_repaired_sdf_sha256_matches_report",
    "output_pre_reaction_sdf_sha256_matches_report",
    "atom_count_source",
    "atom_count_output",
    "bond_count_source",
    "bond_count_output",
    "atom_block_identical",
    "coordinate_block_identical",
    "bond_block_change_count",
    "allowed_bond_order_change_only",
    "restore_bond_atom_1",
    "restore_bond_atom_2",
    "source_restore_bond_order",
    "output_restore_bond_order",
    "target_bond_order",
    "planned_bond_order_operation",
    "expected_change_description",
    "qa_status",
    "pre_reaction_transform_ready",
    "training_ready",
    "blocking_reasons",
    "recommended_next_action",
]


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def index_by_sample(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["sample_id"]: row for row in rows}


def parse_v2000_sdf(path: str | Path) -> dict[str, object]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    if len(lines) < 4:
        raise ValueError(f"SDF is too short: {path}")
    counts = lines[3]
    try:
        atom_count = int(counts[0:3])
        bond_count = int(counts[3:6])
    except ValueError as exc:
        raise ValueError(f"could not parse V2000 counts line in {path}: {counts!r}") from exc
    atom_start = 4
    atom_end = atom_start + atom_count
    bond_start = atom_end
    bond_end = bond_start + bond_count
    atom_block = lines[atom_start:atom_end]
    bond_block = lines[bond_start:bond_end]
    bonds: dict[tuple[int, int], str] = {}
    for line in bond_block:
        if not line.strip():
            continue
        atom_a = int(line[0:3]) - 1
        atom_b = int(line[3:6]) - 1
        order = line[6:9].strip()
        bonds[(min(atom_a, atom_b), max(atom_a, atom_b))] = order
    return {
        "atom_count": atom_count,
        "bond_count": bond_count,
        "atom_block": atom_block,
        "coordinate_block": [line[:30] for line in atom_block],
        "bond_block": bond_block,
        "bonds": bonds,
    }


def bond_block_differences(source_block: list[str], output_block: list[str]) -> list[tuple[int, str, str]]:
    max_len = max(len(source_block), len(output_block))
    diffs: list[tuple[int, str, str]] = []
    for index in range(max_len):
        left = source_block[index] if index < len(source_block) else ""
        right = output_block[index] if index < len(output_block) else ""
        if left != right:
            diffs.append((index, left, right))
    return diffs


def diff_is_only_restore_bond_order(
    diff: tuple[int, str, str],
    restore_a: int,
    restore_b: int,
    target_order: str,
) -> bool:
    _, source_line, output_line = diff
    if len(source_line) < 9 or len(output_line) < 9:
        return False
    source_atoms = sorted((int(source_line[0:3]) - 1, int(source_line[3:6]) - 1))
    output_atoms = sorted((int(output_line[0:3]) - 1, int(output_line[3:6]) - 1))
    restore_atoms = sorted((restore_a, restore_b))
    return (
        source_atoms == restore_atoms
        and output_atoms == restore_atoms
        and source_line[:6] == output_line[:6]
        and output_line[6:9].strip() == target_order
        and source_line[9:] == output_line[9:]
    )


def expected_change_description(operation: str) -> str:
    if operation == "validate_existing_target_bond_order_and_copy_if_future_approved":
        return "source_copied_because_target_bond_order_already_present"
    if operation == "set_bond_order_to_target_if_future_approved":
        return "only_restore_bond_order_changed_to_target"
    return "unsupported_operation"


def qa_row(write_report: dict[str, str], execution_plan: dict[str, str]) -> dict[str, str]:
    reasons: list[str] = []
    source_path = Path(write_report["source_repaired_sdf"])
    output_path = Path(write_report["output_pre_reaction_sdf"])
    source_exists = source_path.exists()
    output_exists = output_path.exists()
    if not source_exists:
        reasons.append("source_repaired_sdf_missing")
    if not output_exists:
        reasons.append("output_pre_reaction_sdf_missing")

    source_hash_match = False
    output_hash_match = False
    source_info: dict[str, object] | None = None
    output_info: dict[str, object] | None = None
    source_restore_order = ""
    output_restore_order = ""
    atom_count_source = atom_count_output = bond_count_source = bond_count_output = ""
    atom_block_identical = coordinate_block_identical = False
    diff_count = ""
    allowed_change = False
    operation = write_report["planned_bond_order_operation"]
    restore_a = int(write_report["restore_bond_atom_1"])
    restore_b = int(write_report["restore_bond_atom_2"])
    restore_key = tuple(sorted((restore_a, restore_b)))
    target_order = write_report["target_bond_order"]

    if source_exists:
        source_hash_match = sha256_file(source_path) == write_report["source_repaired_sdf_sha256_after"]
        if not source_hash_match:
            reasons.append("source_repaired_sdf_sha256_mismatch")
        source_info = parse_v2000_sdf(source_path)
    if output_exists:
        output_hash_match = sha256_file(output_path) == write_report["output_pre_reaction_sdf_sha256"]
        if not output_hash_match:
            reasons.append("output_pre_reaction_sdf_sha256_mismatch")
        output_info = parse_v2000_sdf(output_path)

    if source_info and output_info:
        atom_count_source = str(source_info["atom_count"])
        atom_count_output = str(output_info["atom_count"])
        bond_count_source = str(source_info["bond_count"])
        bond_count_output = str(output_info["bond_count"])
        if source_info["atom_count"] != output_info["atom_count"]:
            reasons.append("atom_count_mismatch")
        if source_info["bond_count"] != output_info["bond_count"]:
            reasons.append("bond_count_mismatch")
        atom_block_identical = source_info["atom_block"] == output_info["atom_block"]
        coordinate_block_identical = source_info["coordinate_block"] == output_info["coordinate_block"]
        if not atom_block_identical:
            reasons.append("atom_block_changed")
        if not coordinate_block_identical:
            reasons.append("coordinate_block_changed")
        source_bonds = source_info["bonds"]
        output_bonds = output_info["bonds"]
        if restore_key not in source_bonds or restore_key not in output_bonds:
            reasons.append("restore_bond_missing")
        else:
            source_restore_order = source_bonds[restore_key]
            output_restore_order = output_bonds[restore_key]
            if output_restore_order != target_order:
                reasons.append("output_restore_bond_order_not_target")
        diffs = bond_block_differences(source_info["bond_block"], output_info["bond_block"])
        diff_count = str(len(diffs))
        if operation == "validate_existing_target_bond_order_and_copy_if_future_approved":
            allowed_change = len(diffs) == 0
            if source_restore_order != target_order:
                reasons.append("source_restore_bond_order_not_target")
            if len(diffs) != 0:
                reasons.append("bond_block_changed_for_copy_operation")
        elif operation == "set_bond_order_to_target_if_future_approved":
            allowed_change = (
                len(diffs) == 1 and diff_is_only_restore_bond_order(diffs[0], restore_a, restore_b, target_order)
            )
            if not allowed_change:
                reasons.append("bond_block_change_not_limited_to_restore_bond_order")
        else:
            reasons.append("unsupported_planned_bond_order_operation")

    if write_report.get("pre_reaction_transform_ready", "") != "false":
        reasons.append("pre_reaction_transform_ready_not_false")
    if write_report.get("training_ready", "") != "false":
        reasons.append("training_ready_not_false")
    if execution_plan.get("sample_id", "") != write_report["sample_id"]:
        reasons.append("execution_plan_sample_mismatch")

    passed = not reasons
    return {
        "sample_id": write_report["sample_id"],
        "source_repaired_sdf": str(source_path),
        "output_pre_reaction_sdf": str(output_path),
        "source_repaired_sdf_exists": str(source_exists).lower(),
        "output_pre_reaction_sdf_exists": str(output_exists).lower(),
        "source_repaired_sdf_sha256_matches_report": str(source_hash_match).lower(),
        "output_pre_reaction_sdf_sha256_matches_report": str(output_hash_match).lower(),
        "atom_count_source": atom_count_source,
        "atom_count_output": atom_count_output,
        "bond_count_source": bond_count_source,
        "bond_count_output": bond_count_output,
        "atom_block_identical": str(atom_block_identical).lower(),
        "coordinate_block_identical": str(coordinate_block_identical).lower(),
        "bond_block_change_count": diff_count,
        "allowed_bond_order_change_only": str(allowed_change).lower(),
        "restore_bond_atom_1": str(restore_a),
        "restore_bond_atom_2": str(restore_b),
        "source_restore_bond_order": source_restore_order,
        "output_restore_bond_order": output_restore_order,
        "target_bond_order": target_order,
        "planned_bond_order_operation": operation,
        "expected_change_description": expected_change_description(operation),
        "qa_status": "generated_pre_reaction_sdf_qa_passed" if passed else "blocked",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": ";".join(reasons),
        "recommended_next_action": (
            "build_pre_reaction_training_readiness_gate"
            if passed
            else "fix_generated_pre_reaction_sdf_before_readiness"
        ),
    }


def build_report_rows(
    *,
    write_sdf_report_csv: str | Path,
    execution_plan_csv: str | Path,
) -> list[dict[str, str]]:
    execution_by_sample = index_by_sample(read_csv(execution_plan_csv))
    rows: list[dict[str, str]] = []
    for write_report in sorted(read_csv(write_sdf_report_csv), key=lambda row: row["sample_id"]):
        sample_id = write_report["sample_id"]
        if sample_id not in execution_by_sample:
            raise ValueError(f"missing execution plan row for {sample_id}")
        rows.append(qa_row(write_report, execution_by_sample[sample_id]))
    return rows


def write_csv(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Generated Pre-Reaction SDF QA Summary",
        "",
        "This QA checks generated pre-reaction SDF files only.",
        "",
        "- It does not modify any SDF files.",
        "- It does not modify raw ligand SDF files.",
        "- It does not modify repaired trial SDF files.",
        "- It does not modify manifest files.",
        "- It does not mark samples as training-ready.",
        "",
        "| sample_id | qa_status | source_restore_bond_order | output_restore_bond_order | target_bond_order | bond_block_change_count | allowed_bond_order_change_only | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["sample_id"],
                    row["qa_status"],
                    row["source_restore_bond_order"],
                    row["output_restore_bond_order"],
                    row["target_bond_order"],
                    row["bond_block_change_count"],
                    row["allowed_bond_order_change_only"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    all_passed = all(row["qa_status"] == "generated_pre_reaction_sdf_qa_passed" for row in rows)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            f"- Generated pre-reaction SDF QA passed for all samples: {str(all_passed).lower()}.",
            "- No SDF files were modified during QA.",
            "- No manifest was modified.",
            "- No sample is training-ready.",
            "- Next step is a separate training-readiness gate, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="QA generated pre-reaction SDF files.")
    parser.add_argument("--write_sdf_report_csv", type=Path, required=True)
    parser.add_argument("--execution_plan_csv", type=Path, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command reads generated pre-reaction SDF files for QA only.")
    print("warning: it does not modify SDF files or mark samples training-ready.")
    rows = build_report_rows(
        write_sdf_report_csv=args.write_sdf_report_csv,
        execution_plan_csv=args.execution_plan_csv,
    )
    write_csv(rows, args.output_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote generated pre-reaction SDF QA report: {args.output_csv}")
    print(f"wrote generated pre-reaction SDF QA summary: {args.output_md}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"qa_status={row['qa_status']} "
            f"source_order={row['source_restore_bond_order']} "
            f"output_order={row['output_restore_bond_order']} "
            f"bond_block_change_count={row['bond_block_change_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
