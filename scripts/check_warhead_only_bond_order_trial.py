#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from rdkit import Chem


QA_COLUMNS = [
    "sample_id",
    "output_sdf_path",
    "source_ligand_sdf_path",
    "bond_endpoint_a",
    "bond_endpoint_b",
    "action_applied",
    "expected_old_bond_type",
    "expected_new_bond_type",
    "raw_current_bond_type",
    "repaired_current_bond_type",
    "bond_change_matches_action",
    "coordinate_hash_same",
    "raw_sdf_hash_same",
    "touched_unresolved_boundary",
    "qa_status",
    "qa_error",
]

VALID_ACTIONS = {"transferred", "kept", "blocked"}


def resolve_manifest_path(path: Path) -> Path:
    if path.exists():
        return path
    fallback = path.parent / "manifests" / path.name
    if fallback.exists():
        print(f"warning: manifest not found at {path}; using {fallback}")
        return fallback
    raise FileNotFoundError(f"manifest_csv not found: {path}")


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_manifest(path: str | Path) -> dict[str, dict[str, str]]:
    resolved = resolve_manifest_path(Path(path))
    return {row["sample_id"]: row for row in read_csv(resolved)}


def load_mol(path: str | Path) -> Chem.Mol:
    supplier = Chem.SDMolSupplier(str(path), removeHs=False, sanitize=False)
    mol = supplier[0] if supplier and len(supplier) else None
    if mol is None:
        raise ValueError(f"could not read SDF: {path}")
    return mol


def bond_type_name(mol: Chem.Mol, atom_a: int, atom_b: int) -> str:
    bond = mol.GetBondBetweenAtoms(atom_a, atom_b)
    if bond is None:
        return ""
    return str(bond.GetBondType()).lower()


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def _append_error(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def check_row(row: dict[str, str], manifest: dict[str, dict[str, str]]) -> dict[str, str]:
    sample_id = row["sample_id"]
    atom_a = int(row["bond_endpoint_a"])
    atom_b = int(row["bond_endpoint_b"])
    action = row["action_applied"]
    expected_old = row["old_bond_type"]
    expected_new = row["new_bond_type"]
    source_path = Path(row["source_ligand_sdf_path"])
    output_path = Path(row["output_sdf_path"])

    raw_mol = load_mol(source_path)
    repaired_mol = load_mol(output_path)
    raw_current = bond_type_name(raw_mol, atom_a, atom_b)
    repaired_current = bond_type_name(repaired_mol, atom_a, atom_b)
    touched_boundary = parse_bool(row["touched_unresolved_boundary"])
    coordinate_same = parse_bool(row["coordinate_hash_same"])
    raw_hash_same = parse_bool(row["raw_sdf_hash_same"])

    errors: list[str] = []
    _append_error(errors, action in VALID_ACTIONS, f"invalid action_applied={action}")
    _append_error(errors, sample_id in manifest, "sample_id missing from manifest")
    if sample_id in manifest:
        manifest_source = Path(manifest[sample_id].get("ligand_sdf_path", ""))
        _append_error(errors, manifest_source == source_path, "source_ligand_sdf_path does not match manifest")
    _append_error(errors, coordinate_same, "coordinate_hash_same is not true")
    _append_error(errors, raw_hash_same, "raw_sdf_hash_same is not true")

    if action == "transferred":
        _append_error(errors, raw_current == expected_old, "raw_current_bond_type does not match expected_old_bond_type")
        _append_error(
            errors,
            repaired_current == expected_new,
            "repaired_current_bond_type does not match expected_new_bond_type",
        )
        _append_error(errors, expected_old != expected_new, "transferred row expected old/new bond types to differ")
        _append_error(errors, not touched_boundary, "transferred row touches unresolved boundary")
        bond_matches = raw_current == expected_old and repaired_current == expected_new and expected_old != expected_new
    elif action == "kept":
        _append_error(errors, raw_current == repaired_current, "kept row changed bond type")
        _append_error(
            errors,
            repaired_current in {expected_old, expected_new},
            "kept row repaired bond type does not match expected old/new",
        )
        bond_matches = raw_current == repaired_current and repaired_current in {expected_old, expected_new}
    elif action == "blocked":
        _append_error(errors, raw_current == repaired_current, "blocked row changed bond type")
        bond_matches = raw_current == repaired_current
    else:
        bond_matches = False

    if touched_boundary:
        _append_error(errors, action == "blocked", "boundary-touching row is not blocked")
        _append_error(errors, raw_current == repaired_current, "boundary-touching row changed bond type")

    return {
        "sample_id": sample_id,
        "output_sdf_path": str(output_path),
        "source_ligand_sdf_path": str(source_path),
        "bond_endpoint_a": str(atom_a),
        "bond_endpoint_b": str(atom_b),
        "action_applied": action,
        "expected_old_bond_type": expected_old,
        "expected_new_bond_type": expected_new,
        "raw_current_bond_type": raw_current,
        "repaired_current_bond_type": repaired_current,
        "bond_change_matches_action": str(bond_matches and not errors).lower(),
        "coordinate_hash_same": row["coordinate_hash_same"],
        "raw_sdf_hash_same": row["raw_sdf_hash_same"],
        "touched_unresolved_boundary": row["touched_unresolved_boundary"],
        "qa_status": "passed" if not errors else "failed",
        "qa_error": "; ".join(errors),
    }


def run_qa(*, manifest_csv: str | Path, trial_report_csv: str | Path) -> list[dict[str, str]]:
    manifest = load_manifest(manifest_csv)
    trial_rows = read_csv(trial_report_csv)
    return [check_row(row, manifest) for row in trial_rows]


def write_qa_csv(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QA_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, str]]) -> dict[str, Counter[str]]:
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        sample_id = row["sample_id"]
        counters[sample_id]["total"] += 1
        counters[sample_id][row["qa_status"]] += 1
        counters[sample_id][row["action_applied"]] += 1
        counters[sample_id][f"coordinate_hash_same={row['coordinate_hash_same']}"] += 1
        counters[sample_id][f"raw_sdf_hash_same={row['raw_sdf_hash_same']}"] += 1
        if row["action_applied"] == "blocked" and row["raw_current_bond_type"] == row["repaired_current_bond_type"]:
            counters[sample_id]["blocked_unchanged"] += 1
        if parse_bool(row["touched_unresolved_boundary"]) and row["action_applied"] == "blocked":
            counters[sample_id]["boundary_touches_blocked"] += 1
        if parse_bool(row["touched_unresolved_boundary"]):
            counters[sample_id]["boundary_touches"] += 1
    return dict(counters)


def build_markdown(rows: list[dict[str, str]]) -> str:
    counters = summarize(rows)
    all_passed = all(row["qa_status"] == "passed" for row in rows)
    lines = [
        "# Warhead-Only Bond-Order Trial QA Summary",
        "",
        "This is a QA report only.",
        "",
        "- It does not modify raw ligand SDF files.",
        "- It does not modify repaired trial SDF files.",
        "- It does not create pre-reaction graphs.",
        "- It does not modify manifest files.",
        "- It does not mark samples as training-ready.",
        "",
        "| sample_id | total_rows | passed_rows | failed_rows | transferred_rows | kept_rows | blocked_rows | coordinate_hash_same_all | raw_sdf_hash_same_all | blocked_bonds_unchanged | boundary_touches_blocked |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for sample_id in sorted(counters):
        counter = counters[sample_id]
        total = counter["total"]
        blocked = counter["blocked"]
        boundary_touches = counter["boundary_touches"]
        lines.append(
            "| "
            + " | ".join(
                [
                    sample_id,
                    str(total),
                    str(counter["passed"]),
                    str(counter["failed"]),
                    str(counter["transferred"]),
                    str(counter["kept"]),
                    str(blocked),
                    str(counter[f"coordinate_hash_same=true"] == total).lower(),
                    str(counter[f"raw_sdf_hash_same=true"] == total).lower(),
                    str(counter["blocked_unchanged"] == blocked).lower(),
                    str(counter["boundary_touches_blocked"] == boundary_touches).lower(),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            f"- All QA passed: {str(all_passed).lower()}.",
            "- Repaired trial SDF files remain derived curation artifacts only.",
            "- No sample is training-ready yet.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="QA a strictly warhead-only bond-order repaired SDF trial.")
    parser.add_argument("--manifest_csv", type=Path, required=True)
    parser.add_argument("--trial_report_csv", type=Path, required=True)
    parser.add_argument("--output_qa_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this is a QA report only.")
    print("warning: this command does not modify raw or repaired trial SDF files.")
    print("warning: this command does not create pre-reaction graphs.")
    rows = run_qa(manifest_csv=args.manifest_csv, trial_report_csv=args.trial_report_csv)
    write_qa_csv(rows, args.output_qa_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote QA report: {args.output_qa_csv}")
    print(f"wrote QA Markdown summary: {args.output_md}")
    for sample_id, counter in sorted(summarize(rows).items()):
        print(
            f"{sample_id}: total={counter['total']} passed={counter['passed']} "
            f"failed={counter['failed']} transferred={counter['transferred']} "
            f"kept={counter['kept']} blocked={counter['blocked']}"
        )
    return 0 if all(row["qa_status"] == "passed" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
