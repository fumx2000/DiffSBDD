#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

from rdkit import Chem


REPORT_COLUMNS = [
    "sample_id",
    "output_sdf_path",
    "source_ligand_sdf_path",
    "bond_endpoint_a",
    "bond_endpoint_b",
    "old_bond_type",
    "new_bond_type",
    "action_applied",
    "safety_decision",
    "touched_unresolved_boundary",
    "coordinate_hash_before",
    "coordinate_hash_after",
    "coordinate_hash_same",
    "raw_sdf_hash_before",
    "raw_sdf_hash_after",
    "raw_sdf_hash_same",
    "rationale",
]

ALLOWED_ACTIONS = {"transferred", "kept", "blocked"}


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


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def coordinate_hash(mol: Chem.Mol) -> str:
    if mol.GetNumConformers() == 0:
        return "no_conformer"
    conf = mol.GetConformer()
    parts: list[str] = []
    for atom_idx in range(mol.GetNumAtoms()):
        pos = conf.GetAtomPosition(atom_idx)
        parts.append(f"{atom_idx}:{pos.x:.8f}:{pos.y:.8f}:{pos.z:.8f}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def bond_type_name(bond: Chem.Bond | None) -> str:
    if bond is None:
        return ""
    return str(bond.GetBondType()).lower()


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def bond_type_from_name(name: str) -> Chem.BondType:
    mapping = {
        "single": Chem.BondType.SINGLE,
        "double": Chem.BondType.DOUBLE,
        "triple": Chem.BondType.TRIPLE,
        "aromatic": Chem.BondType.AROMATIC,
    }
    try:
        return mapping[name]
    except KeyError as exc:
        raise ValueError(f"unsupported bond type for local trial: {name!r}") from exc


def validate_dry_run_rows(rows: list[dict[str, str]]) -> None:
    for row in rows:
        if parse_bool(row.get("touches_unresolved_boundary", "")) and row.get("safety_decision", "") == "eligible":
            raise ValueError("unsafe dry-run row: touches unresolved boundary but safety_decision=eligible")
        if row.get("proposed_action", "") == "would_transfer_in_warhead_only_scope":
            if row.get("safety_decision", "") != "eligible":
                raise ValueError("would_transfer row must have safety_decision=eligible")
            if parse_bool(row.get("touches_unresolved_boundary", "")):
                raise ValueError("would_transfer row touches unresolved boundary")
            if not parse_bool(row.get("both_atoms_accepted_warhead", "")):
                raise ValueError("would_transfer row is not both_atoms_accepted_warhead=true")
            if not row.get("reference_candidate_bond_type", ""):
                raise ValueError("would_transfer row missing reference_candidate_bond_type")


def action_for_row(row: dict[str, str]) -> str:
    proposed_action = row.get("proposed_action", "")
    safety_decision = row.get("safety_decision", "")
    if safety_decision == "blocked":
        return "blocked"
    if safety_decision == "eligible" and proposed_action == "keep":
        return "kept"
    if safety_decision == "eligible" and proposed_action == "would_transfer_in_warhead_only_scope":
        return "transferred"
    return "blocked"


def write_sdf(mol: Chem.Mol, output_path: str | Path) -> None:
    writer = Chem.SDWriter(str(output_path))
    writer.write(mol)
    writer.close()


def apply_trial(
    *,
    manifest_csv: str | Path,
    dry_run_csv: str | Path,
    output_sdf_dir: str | Path,
) -> list[dict[str, str]]:
    manifest = load_manifest(manifest_csv)
    dry_rows = read_csv(dry_run_csv)
    validate_dry_run_rows(dry_rows)
    rows_by_sample: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in dry_rows:
        rows_by_sample[row["sample_id"]].append(row)

    output_dir = Path(output_sdf_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_rows: list[dict[str, str]] = []

    for sample_id in sorted(rows_by_sample):
        if sample_id not in manifest:
            raise ValueError(f"sample_id missing from manifest: {sample_id}")
        source_path = Path(manifest[sample_id]["ligand_sdf_path"])
        raw_hash_before = sha256_file(source_path)
        mol = load_mol(source_path)
        editable = Chem.RWMol(mol)
        coord_hash_before = coordinate_hash(mol)
        output_path = output_dir / f"{sample_id}_warhead_only_repaired_trial.sdf"

        per_sample_rows: list[dict[str, str]] = []
        for dry_row in rows_by_sample[sample_id]:
            atom_a = int(dry_row["bond_endpoint_a"])
            atom_b = int(dry_row["bond_endpoint_b"])
            bond = editable.GetBondBetweenAtoms(atom_a, atom_b)
            if bond is None:
                raise ValueError(f"bond missing in source ligand for {sample_id}: {atom_a}-{atom_b}")

            old_bond_type = bond_type_name(bond)
            action = action_for_row(dry_row)
            if action == "transferred":
                new_bond_type = dry_row["reference_candidate_bond_type"]
                bond.SetBondType(bond_type_from_name(new_bond_type))
            else:
                new_bond_type = old_bond_type

            if action not in ALLOWED_ACTIONS:
                raise AssertionError(f"invalid action_applied: {action}")

            per_sample_rows.append(
                {
                    "sample_id": sample_id,
                    "output_sdf_path": str(output_path),
                    "source_ligand_sdf_path": str(source_path),
                    "bond_endpoint_a": str(atom_a),
                    "bond_endpoint_b": str(atom_b),
                    "old_bond_type": old_bond_type,
                    "new_bond_type": new_bond_type,
                    "action_applied": action,
                    "safety_decision": dry_row["safety_decision"],
                    "touched_unresolved_boundary": dry_row["touches_unresolved_boundary"],
                    "coordinate_hash_before": coord_hash_before,
                    "coordinate_hash_after": "",
                    "coordinate_hash_same": "",
                    "raw_sdf_hash_before": raw_hash_before,
                    "raw_sdf_hash_after": "",
                    "raw_sdf_hash_same": "",
                    "rationale": dry_row.get("rationale", ""),
                }
            )

        repaired = editable.GetMol()
        coord_hash_after = coordinate_hash(repaired)
        write_sdf(repaired, output_path)
        raw_hash_after = sha256_file(source_path)
        for row in per_sample_rows:
            row["coordinate_hash_after"] = coord_hash_after
            row["coordinate_hash_same"] = str(coord_hash_before == coord_hash_after).lower()
            row["raw_sdf_hash_after"] = raw_hash_after
            row["raw_sdf_hash_same"] = str(raw_hash_before == raw_hash_after).lower()
        report_rows.extend(per_sample_rows)
    return report_rows


def write_report(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    with Path(output_csv).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def summarize_rows(rows: list[dict[str, str]]) -> dict[str, Counter[str]]:
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        counters[row["sample_id"]][row["action_applied"]] += 1
        counters[row["sample_id"]][f"coordinate_hash_same={row['coordinate_hash_same']}"] += 1
        counters[row["sample_id"]][f"raw_sdf_hash_same={row['raw_sdf_hash_same']}"] += 1
    return dict(counters)


def build_markdown(rows: list[dict[str, str]]) -> str:
    counters = summarize_rows(rows)
    output_paths = {row["sample_id"]: row["output_sdf_path"] for row in rows}
    lines = [
        "# Warhead-Only Bond-Order Trial Summary",
        "",
        "This is a non-destructive repaired-SDF trial only.",
        "",
        "- It does not modify raw ligand SDF files.",
        "- It does not create pre-reaction graphs.",
        "- It does not modify manifest files.",
        "- It does not mark samples as training-ready.",
        "",
        "| sample_id | transferred_count | kept_count | blocked_count | coordinate_hash_same | raw_sdf_hash_same | output_sdf_path |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for sample_id in sorted(counters):
        counter = counters[sample_id]
        total = counter.get("transferred", 0) + counter.get("kept", 0) + counter.get("blocked", 0)
        coordinate_same = counter.get("coordinate_hash_same=true", 0) == total
        raw_same = counter.get("raw_sdf_hash_same=true", 0) == total
        lines.append(
            "| "
            + " | ".join(
                [
                    sample_id,
                    str(counter.get("transferred", 0)),
                    str(counter.get("kept", 0)),
                    str(counter.get("blocked", 0)),
                    str(coordinate_same).lower(),
                    str(raw_same).lower(),
                    output_paths[sample_id],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- Repaired trial SDF files are derived curation artifacts only.",
            "- They are not training-ready.",
            "- No raw ligand SDF was modified.",
            "- No pre-reaction SDF was generated.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    Path(output_md).write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply a strictly warhead-only non-destructive bond-order trial.")
    parser.add_argument("--manifest_csv", type=Path, required=True)
    parser.add_argument("--dry_run_csv", type=Path, required=True)
    parser.add_argument("--output_sdf_dir", type=Path, required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this is a non-destructive repaired-SDF trial only.")
    print("warning: this command does not modify raw ligand SDF files.")
    print("warning: this command does not create pre-reaction graphs.")
    rows = apply_trial(
        manifest_csv=args.manifest_csv,
        dry_run_csv=args.dry_run_csv,
        output_sdf_dir=args.output_sdf_dir,
    )
    args.output_report_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    write_report(rows, args.output_report_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote trial report: {args.output_report_csv}")
    print(f"wrote trial Markdown summary: {args.output_md}")
    for sample_id, counter in sorted(summarize_rows(rows).items()):
        print(
            f"{sample_id}: "
            f"transferred={counter.get('transferred', 0)} "
            f"kept={counter.get('kept', 0)} "
            f"blocked={counter.get('blocked', 0)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
