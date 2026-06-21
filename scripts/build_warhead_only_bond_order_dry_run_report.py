#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from rdkit import Chem


REPORT_COLUMNS = [
    "sample_id",
    "bond_endpoint_a",
    "bond_endpoint_b",
    "extracted_old_bond_type",
    "reference_candidate_bond_type",
    "both_atoms_accepted_warhead",
    "touches_unresolved_boundary",
    "proposed_action",
    "safety_decision",
    "rationale",
]

ALLOWED_ACTIONS = {
    "keep",
    "would_transfer_in_warhead_only_scope",
    "blocked_touches_unresolved_boundary",
    "blocked_missing_reference_bond",
    "blocked_atom_not_accepted",
}

ALLOWED_SAFETY_DECISIONS = {"eligible", "blocked"}


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


def load_mol(path: str | Path, *, sanitize: bool) -> Chem.Mol:
    supplier = Chem.SDMolSupplier(str(path), removeHs=False, sanitize=sanitize)
    mol = supplier[0] if supplier and len(supplier) else None
    if mol is None and sanitize:
        print(f"warning: sanitized read failed for {path}; retrying sanitize=False")
        return load_mol(path, sanitize=False)
    if mol is None:
        raise ValueError(f"could not read SDF: {path}")
    if not sanitize:
        try:
            Chem.SanitizeMol(mol)
        except Exception as exc:  # noqa: BLE001 - dry-run should remain report-only and permissive.
            print(f"warning: RDKit sanitize failed for {path}: {exc}")
    return mol


def bond_type_name(bond: Chem.Bond | None) -> str:
    if bond is None:
        return ""
    return str(bond.GetBondType()).lower()


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def load_decision_drafts(paths: list[Path]) -> dict[str, list[dict[str, str]]]:
    rows_by_sample: dict[str, list[dict[str, str]]] = defaultdict(list)
    for path in paths:
        for row in read_csv(path):
            rows_by_sample[row["sample_id"]].append(row)
    return dict(rows_by_sample)


def accepted_warhead_atoms(rows: list[dict[str, str]]) -> set[int]:
    return {
        int(row["extracted_atom_id"])
        for row in rows
        if row.get("manual_decision", "") == "accept_candidate" and row.get("final_role", "") == "warhead"
    }


def unresolved_boundary_atoms(rows: list[dict[str, str]]) -> set[int]:
    atoms: set[int] = set()
    for row in rows:
        manual_decision = row.get("manual_decision", "")
        final_role = row.get("final_role", "")
        reason = row.get("local_review_reason", "")
        if manual_decision == "unresolved" and final_role in {"linker", "boundary"}:
            atoms.add(int(row["extracted_atom_id"]))
        elif "low_confidence_warhead_or_linker" in reason and final_role in {"linker", "boundary"}:
            atoms.add(int(row["extracted_atom_id"]))
    return atoms


def reference_mapping(rows: list[dict[str, str]]) -> dict[int, int]:
    mapping: dict[int, int] = {}
    for row in rows:
        raw_extracted = row.get("extracted_atom_id", "")
        raw_reference = row.get("reference_candidate_atom_id", "")
        if not raw_extracted or not raw_reference:
            continue
        if " " in raw_reference:
            continue
        try:
            mapping[int(raw_extracted)] = int(raw_reference)
        except ValueError:
            continue
    return mapping


def sample_reference_sdf(sample_id: str, manifest_row: dict[str, str]) -> Path:
    base = Path("data/raw/covalent_small/metadata")
    pdb_id = sample_id.split("_")[-1]
    reference_dir = base / f"{pdb_id}_reference"
    candidates = sorted(reference_dir.glob("*_ideal.sdf"))
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        ligand_stem = Path(manifest_row["ligand_sdf_path"]).stem.upper()
        matched = [path for path in candidates if path.stem.split("_")[0].upper() in ligand_stem]
        if len(matched) == 1:
            return matched[0]
    raise FileNotFoundError(f"could not resolve unique ideal/reference SDF for sample {sample_id}")


def build_bond_row(
    *,
    sample_id: str,
    bond: Chem.Bond,
    reference_mol: Chem.Mol,
    accepted_atoms: set[int],
    unresolved_atoms: set[int],
    mapping: dict[int, int],
) -> dict[str, str]:
    atom_a = bond.GetBeginAtomIdx()
    atom_b = bond.GetEndAtomIdx()
    extracted_old_bond_type = bond_type_name(bond)
    both_accepted = atom_a in accepted_atoms and atom_b in accepted_atoms
    touches_unresolved = atom_a in unresolved_atoms or atom_b in unresolved_atoms
    reference_candidate_bond_type = ""

    if touches_unresolved:
        proposed_action = "blocked_touches_unresolved_boundary"
        safety_decision = "blocked"
        rationale = "at least one endpoint is an unresolved linker/local boundary atom"
    elif both_accepted:
        reference_a = mapping.get(atom_a)
        reference_b = mapping.get(atom_b)
        if reference_a is None or reference_b is None:
            proposed_action = "blocked_missing_reference_bond"
            safety_decision = "blocked"
            rationale = "accepted warhead endpoint lacks a unique reference candidate atom"
        else:
            reference_bond = reference_mol.GetBondBetweenAtoms(reference_a, reference_b)
            reference_candidate_bond_type = bond_type_name(reference_bond)
            if reference_bond is None:
                proposed_action = "blocked_missing_reference_bond"
                safety_decision = "blocked"
                rationale = "both endpoints are accepted warhead atoms but no reference candidate bond exists"
            elif extracted_old_bond_type == reference_candidate_bond_type:
                proposed_action = "keep"
                safety_decision = "eligible"
                rationale = "bond is inside accepted warhead-only scope and bond type already matches reference"
            else:
                proposed_action = "would_transfer_in_warhead_only_scope"
                safety_decision = "eligible"
                rationale = "bond is inside accepted warhead-only scope and reference bond type differs"
    else:
        proposed_action = "blocked_atom_not_accepted"
        safety_decision = "blocked"
        rationale = "one or both endpoints are not accepted warhead atoms"

    if proposed_action not in ALLOWED_ACTIONS:
        raise AssertionError(f"invalid proposed_action: {proposed_action}")
    if safety_decision not in ALLOWED_SAFETY_DECISIONS:
        raise AssertionError(f"invalid safety_decision: {safety_decision}")
    if touches_unresolved and safety_decision != "blocked":
        raise AssertionError("touches_unresolved_boundary row must be blocked")

    return {
        "sample_id": sample_id,
        "bond_endpoint_a": str(atom_a),
        "bond_endpoint_b": str(atom_b),
        "extracted_old_bond_type": extracted_old_bond_type,
        "reference_candidate_bond_type": reference_candidate_bond_type,
        "both_atoms_accepted_warhead": str(both_accepted).lower(),
        "touches_unresolved_boundary": str(touches_unresolved).lower(),
        "proposed_action": proposed_action,
        "safety_decision": safety_decision,
        "rationale": rationale,
    }


def build_dry_run_rows(
    *,
    manifest_csv: str | Path,
    decision_drafts: list[Path],
) -> list[dict[str, str]]:
    manifest = load_manifest(manifest_csv)
    drafts_by_sample = load_decision_drafts(decision_drafts)
    rows: list[dict[str, str]] = []
    for sample_id in sorted(drafts_by_sample):
        if sample_id not in manifest:
            raise ValueError(f"sample_id from decision draft missing in manifest: {sample_id}")
        manifest_row = manifest[sample_id]
        extracted_mol = load_mol(manifest_row["ligand_sdf_path"], sanitize=False)
        reference_mol = load_mol(sample_reference_sdf(sample_id, manifest_row), sanitize=True)
        draft_rows = drafts_by_sample[sample_id]
        accepted_atoms = accepted_warhead_atoms(draft_rows)
        unresolved_atoms = unresolved_boundary_atoms(draft_rows)
        mapping = reference_mapping(draft_rows)

        for bond in extracted_mol.GetBonds():
            rows.append(
                build_bond_row(
                    sample_id=sample_id,
                    bond=bond,
                    reference_mol=reference_mol,
                    accepted_atoms=accepted_atoms,
                    unresolved_atoms=unresolved_atoms,
                    mapping=mapping,
                )
            )
    return rows


def write_report(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    with Path(output_csv).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def summarize_rows(rows: list[dict[str, str]]) -> dict[str, Counter[str]]:
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        counters[row["sample_id"]][row["proposed_action"]] += 1
    return dict(counters)


def build_markdown(rows: list[dict[str, str]]) -> str:
    counters = summarize_rows(rows)
    lines = [
        "# Warhead-Only Bond-Order Dry-Run Summary",
        "",
        "This is a dry-run report only.",
        "",
        "- It does not repair bond orders.",
        "- It does not create repaired SDF files.",
        "- It does not create pre-reaction graphs.",
        "- It does not modify ligand SDF files.",
        "- It does not mark samples as training-ready.",
        "",
        "| sample_id | total_bonds_reported | eligible_keep_count | eligible_would_transfer_count | blocked_touches_unresolved_boundary_count | blocked_missing_reference_bond_count | blocked_atom_not_accepted_count |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for sample_id in sorted(counters):
        counter = counters[sample_id]
        total = sum(counter.values())
        lines.append(
            "| "
            + " | ".join(
                [
                    sample_id,
                    str(total),
                    str(counter.get("keep", 0)),
                    str(counter.get("would_transfer_in_warhead_only_scope", 0)),
                    str(counter.get("blocked_touches_unresolved_boundary", 0)),
                    str(counter.get("blocked_missing_reference_bond", 0)),
                    str(counter.get("blocked_atom_not_accepted", 0)),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- No repaired SDF was generated.",
            "- Only eligible rows fully inside accepted warhead atoms may be considered later.",
            "- Any row touching unresolved boundary remains blocked.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    Path(output_md).write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a strictly warhead-only bond-order dry-run report.")
    parser.add_argument("--manifest_csv", type=Path, required=True)
    parser.add_argument("--decision_drafts", type=Path, nargs="+", required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this is a dry-run report only.")
    print("warning: this command does not repair bond orders.")
    print("warning: this command does not create repaired SDF files.")
    print("warning: this command does not create pre-reaction graphs.")
    rows = build_dry_run_rows(manifest_csv=args.manifest_csv, decision_drafts=args.decision_drafts)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    write_report(rows, args.output_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote dry-run CSV report: {args.output_csv}")
    print(f"wrote dry-run Markdown summary: {args.output_md}")
    for sample_id, counter in sorted(summarize_rows(rows).items()):
        print(
            f"{sample_id}: "
            f"keep={counter.get('keep', 0)} "
            f"would_transfer={counter.get('would_transfer_in_warhead_only_scope', 0)} "
            f"blocked_boundary={counter.get('blocked_touches_unresolved_boundary', 0)} "
            f"blocked_missing_reference={counter.get('blocked_missing_reference_bond', 0)} "
            f"blocked_not_accepted={counter.get('blocked_atom_not_accepted', 0)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
