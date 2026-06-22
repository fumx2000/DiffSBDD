#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


REPORT_COLUMNS = [
    "sample_id",
    "eligible_for_future_transform_dry_run_only",
    "manual_covalent_bond_to_remove",
    "covalent_bond_remove_directive_status",
    "ligand_reactive_atom",
    "ligand_reactive_atom_present_in_sdf",
    "manual_bond_order_to_restore",
    "restore_bond_atom_1",
    "restore_bond_atom_2",
    "restore_bond_exists_in_repaired_sdf",
    "current_bond_order_in_repaired_sdf",
    "target_bond_order",
    "bond_order_dry_run_action",
    "manual_boundary_resolution",
    "manual_atoms_requiring_charge_check",
    "manual_atoms_requiring_valence_check",
    "dry_run_preview_status",
    "can_build_future_transform_script",
    "pre_reaction_sdf_generated",
    "raw_ligand_sdf_modified",
    "repaired_trial_sdf_modified",
    "manifest_modified",
    "pre_reaction_transform_ready",
    "training_ready",
    "blocking_reasons",
    "recommended_next_action",
]

TARGET_BOND_ORDER = {
    "single": "1",
    "double": "2",
    "triple": "3",
    "aromatic": "4",
}


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_covalent_bond_remove(value: str) -> int:
    try:
        _, atom_text = value.rsplit("-", 1)
        return int(atom_text)
    except ValueError as exc:
        raise ValueError(f"invalid covalent bond removal directive: {value!r}") from exc


def parse_bond_order_restore(value: str) -> tuple[int, int, str]:
    try:
        pair_text, order_text = value.split(":", 1)
        atom_a_text, atom_b_text = pair_text.split("-", 1)
    except ValueError as exc:
        raise ValueError(f"invalid bond order restore directive: {value!r}") from exc
    if order_text not in TARGET_BOND_ORDER:
        raise ValueError(f"unsupported target bond order {order_text!r} in {value!r}")
    atom_a = int(atom_a_text)
    atom_b = int(atom_b_text)
    return min(atom_a, atom_b), max(atom_a, atom_b), TARGET_BOND_ORDER[order_text]


def parse_v2000_sdf(path: str | Path) -> tuple[int, dict[tuple[int, int], str]]:
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
    bonds: dict[tuple[int, int], str] = {}
    for line in bond_lines:
        if not line.strip():
            continue
        atom_a = int(line[0:3]) - 1
        atom_b = int(line[3:6]) - 1
        order = line[6:9].strip()
        bonds[(min(atom_a, atom_b), max(atom_a, atom_b))] = order
    return atom_count, bonds


def map_sdf_paths_to_samples(sample_ids: set[str], sdf_paths: list[Path]) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for sample_id in sample_ids:
        matches = [path for path in sdf_paths if path.name.startswith(sample_id)]
        if len(matches) != 1:
            raise ValueError(f"expected exactly one SDF path for {sample_id}, found {len(matches)}")
        mapping[sample_id] = matches[0]
    return mapping


def index_by_sample(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["sample_id"]: row for row in rows}


def build_row(
    *,
    decision: dict[str, str],
    readiness: dict[str, str],
    sdf_path: Path,
) -> dict[str, str]:
    blocking_reasons: list[str] = []
    eligible = readiness.get("eligible_for_future_transform_dry_run_only", "") == "true"
    if not eligible:
        blocking_reasons.append("sample_not_eligible_for_future_transform_dry_run_only")

    ligand_reactive_atom = parse_covalent_bond_remove(decision["manual_covalent_bond_to_remove"])
    atom_a, atom_b, target_order = parse_bond_order_restore(decision["manual_bond_order_to_restore"])
    atom_count, bonds = parse_v2000_sdf(sdf_path)
    reactive_present = 0 <= ligand_reactive_atom < atom_count
    if not reactive_present:
        blocking_reasons.append("ligand_reactive_atom_missing_in_sdf")
    restore_bond = (atom_a, atom_b)
    restore_bond_exists = restore_bond in bonds
    current_order = bonds.get(restore_bond, "")
    if not restore_bond_exists:
        blocking_reasons.append("restore_bond_missing_in_repaired_sdf")

    if not restore_bond_exists:
        action = "blocked_missing_restore_bond"
    elif current_order == target_order:
        action = "already_target_order_no_change_needed"
    else:
        action = "would_restore_bond_order_to_target"

    passed = not blocking_reasons
    return {
        "sample_id": decision["sample_id"],
        "eligible_for_future_transform_dry_run_only": str(eligible).lower(),
        "manual_covalent_bond_to_remove": decision["manual_covalent_bond_to_remove"],
        "covalent_bond_remove_directive_status": "protein_ligand_covalent_bond_removal_directive_present",
        "ligand_reactive_atom": str(ligand_reactive_atom),
        "ligand_reactive_atom_present_in_sdf": str(reactive_present).lower(),
        "manual_bond_order_to_restore": decision["manual_bond_order_to_restore"],
        "restore_bond_atom_1": str(atom_a),
        "restore_bond_atom_2": str(atom_b),
        "restore_bond_exists_in_repaired_sdf": str(restore_bond_exists).lower(),
        "current_bond_order_in_repaired_sdf": current_order,
        "target_bond_order": target_order,
        "bond_order_dry_run_action": action,
        "manual_boundary_resolution": decision["manual_boundary_resolution"],
        "manual_atoms_requiring_charge_check": decision["manual_atoms_requiring_charge_check"],
        "manual_atoms_requiring_valence_check": decision["manual_atoms_requiring_valence_check"],
        "dry_run_preview_status": "preview_passed" if passed else "blocked",
        "can_build_future_transform_script": str(passed).lower(),
        "pre_reaction_sdf_generated": "false",
        "raw_ligand_sdf_modified": "false",
        "repaired_trial_sdf_modified": "false",
        "manifest_modified": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": ";".join(blocking_reasons),
        "recommended_next_action": "design_guarded_pre_reaction_transform_script" if passed else "fix_preview_blockers",
    }


def build_preview_rows(
    *,
    decision_csv: str | Path,
    readiness_csv: str | Path,
    sdf_paths: list[Path],
) -> list[dict[str, str]]:
    decisions = read_csv(decision_csv)
    readiness_by_sample = index_by_sample(read_csv(readiness_csv))
    sdf_by_sample = map_sdf_paths_to_samples({row["sample_id"] for row in decisions}, sdf_paths)
    rows: list[dict[str, str]] = []
    for decision in sorted(decisions, key=lambda row: row["sample_id"]):
        sample_id = decision["sample_id"]
        if sample_id not in readiness_by_sample:
            raise ValueError(f"missing readiness row for {sample_id}")
        rows.append(
            build_row(
                decision=decision,
                readiness=readiness_by_sample[sample_id],
                sdf_path=sdf_by_sample[sample_id],
            )
        )
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
        "# Pre-Reaction Transform Dry-Run Preview Summary",
        "",
        "This is a dry-run preview only.",
        "",
        "- It does not create pre-reaction SDF files.",
        "- It does not modify raw ligand SDF files.",
        "- It does not modify repaired trial SDF files.",
        "- It does not modify manifest files.",
        "- It does not mark samples as training-ready.",
        "",
        "| sample_id | dry_run_preview_status | manual_covalent_bond_to_remove | manual_bond_order_to_restore | current_bond_order_in_repaired_sdf | target_bond_order | bond_order_dry_run_action | can_build_future_transform_script |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["sample_id"],
                    row["dry_run_preview_status"],
                    row["manual_covalent_bond_to_remove"],
                    row["manual_bond_order_to_restore"],
                    row["current_bond_order_in_repaired_sdf"],
                    row["target_bond_order"],
                    row["bond_order_dry_run_action"],
                    row["can_build_future_transform_script"],
                ]
            )
            + " |"
        )
    all_passed = all(row["dry_run_preview_status"] == "preview_passed" for row in rows)
    any_training_ready = any(row["training_ready"] == "true" for row in rows)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            f"- Dry-run preview passed for all eligible samples: {str(all_passed).lower()}.",
            "- No pre-reaction SDF was generated.",
            f"- No sample is training-ready: {str(not any_training_ready).lower()}.",
            "- Next step is to design a guarded transform script, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build pre-reaction transform dry-run preview.")
    parser.add_argument("--decision_csv", type=Path, required=True)
    parser.add_argument("--readiness_csv", type=Path, required=True)
    parser.add_argument("--sdf_paths", type=Path, nargs="+", required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command builds a dry-run preview only.")
    print("warning: it does not generate pre-reaction SDF files.")
    print("warning: it does not modify raw or repaired trial SDF files.")
    rows = build_preview_rows(
        decision_csv=args.decision_csv,
        readiness_csv=args.readiness_csv,
        sdf_paths=args.sdf_paths,
    )
    write_csv(rows, args.output_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote dry-run preview report: {args.output_csv}")
    print(f"wrote dry-run preview summary: {args.output_md}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"dry_run_preview_status={row['dry_run_preview_status']} "
            f"current_bond_order={row['current_bond_order_in_repaired_sdf']} "
            f"target_bond_order={row['target_bond_order']} "
            f"action={row['bond_order_dry_run_action']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
