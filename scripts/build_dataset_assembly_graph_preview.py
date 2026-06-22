#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

try:
    from rdkit import Chem
except ImportError:  # pragma: no cover - exercised only in environments without RDKit.
    Chem = None


TARGETS = {
    "BTK_C481_6DI9_pre_reaction": "BTK_C481_6DI9",
    "KRAS_G12C_5F2E_pre_reaction": "KRAS_G12C_5F2E",
    "KRAS_G12C_6OIM_pre_reaction": "KRAS_G12C_6OIM",
}

PREVIEW_CANDIDATE_COLUMNS = [
    "graph_preview_candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "protein_pdb_path",
    "protein_pdb_sha256",
    "ligand_sdf_path",
    "ligand_sdf_sha256",
    "ligand_atom_count",
    "ligand_heavy_atom_count",
    "ligand_bond_count",
    "ligand_element_set",
    "protein_atom_count",
    "protein_residue_count",
    "reactive_residue_chain",
    "reactive_residue_id",
    "reactive_residue_type",
    "reactive_atom_name",
    "reactive_residue_found",
    "reactive_atom_found",
    "ligand_reactive_atom_id",
    "scaffold_atoms",
    "linker_atoms",
    "warhead_atoms",
    "scaffold_atom_count",
    "linker_atom_count",
    "warhead_atom_count",
    "candidate_type",
    "dataset_assembly_stage",
    "schema_validation_stage",
    "file_hash_gate_stage",
    "graph_preview_stage",
    "training_ready",
]

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "hash_locked_candidates_csv",
    "file_hash_report_csv",
    "candidate_row_found_once",
    "file_hash_gate_passed",
    "hash_locked_candidate_written_confirmed",
    "file_hash_report_real_dataset_generated_false",
    "file_hash_report_training_ready_false",
    "protein_pdb_path",
    "protein_pdb_exists",
    "protein_pdb_size_matches_hash_locked",
    "protein_pdb_sha256_matches_hash_locked",
    "ligand_sdf_path",
    "ligand_sdf_exists",
    "ligand_sdf_size_matches_hash_locked",
    "ligand_sdf_sha256_matches_hash_locked",
    "ligand_rdkit_parseable",
    "ligand_atom_count",
    "ligand_heavy_atom_count",
    "ligand_bond_count",
    "ligand_element_set",
    "scaffold_atoms_parseable",
    "linker_atoms_parseable",
    "warhead_atoms_parseable",
    "atom_groups_non_overlapping",
    "atom_indices_within_ligand_range",
    "ligand_reactive_atom_id_is_integer",
    "ligand_reactive_atom_in_range",
    "warhead_contains_ligand_reactive_atom",
    "protein_atom_count",
    "protein_residue_count",
    "reactive_residue_found",
    "reactive_atom_found",
    "graph_preview_candidate_written",
    "graph_preview_status",
    "manifest_modified",
    "sdf_modified",
    "sdf_generated",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
    "blocking_reasons",
    "recommended_next_action",
]


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def index_many(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    indexed: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        indexed.setdefault(row.get(key, ""), []).append(row)
    return indexed


def index_one(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows if row.get(key)}


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def path_size(path_value: str) -> str:
    if not path_value or not Path(path_value).exists():
        return ""
    return str(Path(path_value).stat().st_size)


def path_sha256(path_value: str) -> str:
    if not path_value or not Path(path_value).exists():
        return ""
    return sha256_file(path_value)


def parse_atom_list(value: str) -> tuple[list[int], bool]:
    try:
        if not value.strip():
            return [], True
        return [int(part) for part in value.split()], True
    except ValueError:
        return [], False


def parse_int(value: str) -> tuple[int | None, bool]:
    try:
        return int(value), True
    except (TypeError, ValueError):
        return None, False


def preview_ligand(path_value: str) -> dict[str, str]:
    if Chem is None or not path_value or not Path(path_value).exists():
        return {
            "ligand_rdkit_parseable": "false",
            "ligand_atom_count": "0",
            "ligand_heavy_atom_count": "0",
            "ligand_bond_count": "0",
            "ligand_element_set": "",
        }
    supplier = Chem.SDMolSupplier(str(path_value), sanitize=False, removeHs=False)
    mol = supplier[0] if supplier and len(supplier) else None
    if mol is None:
        return {
            "ligand_rdkit_parseable": "false",
            "ligand_atom_count": "0",
            "ligand_heavy_atom_count": "0",
            "ligand_bond_count": "0",
            "ligand_element_set": "",
        }
    elements = sorted({atom.GetSymbol() for atom in mol.GetAtoms()})
    heavy_count = sum(1 for atom in mol.GetAtoms() if atom.GetAtomicNum() > 1)
    return {
        "ligand_rdkit_parseable": "true",
        "ligand_atom_count": str(mol.GetNumAtoms()),
        "ligand_heavy_atom_count": str(heavy_count),
        "ligand_bond_count": str(mol.GetNumBonds()),
        "ligand_element_set": ";".join(elements),
    }


def preview_protein(
    path_value: str,
    reactive_chain: str,
    reactive_residue_id: str,
    reactive_residue_type: str,
    reactive_atom_name: str,
) -> dict[str, str]:
    atom_count = 0
    residues: set[tuple[str, str, str]] = set()
    reactive_residue_found = False
    reactive_atom_found = False
    if path_value and Path(path_value).exists():
        with Path(path_value).open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not (line.startswith("ATOM") or line.startswith("HETATM")):
                    continue
                atom_count += 1
                atom_name = line[12:16].strip()
                resname = line[17:20].strip()
                chain = line[21].strip()
                resseq = line[22:26].strip()
                residues.add((chain, resseq, resname))
                if chain == reactive_chain and resseq == reactive_residue_id and resname == reactive_residue_type:
                    reactive_residue_found = True
                    if atom_name == reactive_atom_name:
                        reactive_atom_found = True
    return {
        "protein_atom_count": str(atom_count),
        "protein_residue_count": str(len(residues)),
        "reactive_residue_found": str(reactive_residue_found).lower(),
        "reactive_atom_found": str(reactive_atom_found).lower(),
    }


def build_preview_candidate(row: dict[str, str], report: dict[str, str]) -> dict[str, str]:
    return {
        "graph_preview_candidate_id": row["hash_locked_candidate_id"],
        "source_sample_id": row["source_sample_id"],
        "pre_reaction_sample_id": row["pre_reaction_sample_id"],
        "protein_pdb_path": row["protein_pdb_path"],
        "protein_pdb_sha256": row["protein_pdb_sha256"],
        "ligand_sdf_path": row["ligand_sdf_path"],
        "ligand_sdf_sha256": row["ligand_sdf_sha256"],
        "ligand_atom_count": report["ligand_atom_count"],
        "ligand_heavy_atom_count": report["ligand_heavy_atom_count"],
        "ligand_bond_count": report["ligand_bond_count"],
        "ligand_element_set": report["ligand_element_set"],
        "protein_atom_count": report["protein_atom_count"],
        "protein_residue_count": report["protein_residue_count"],
        "reactive_residue_chain": row["reactive_residue_chain"],
        "reactive_residue_id": row["reactive_residue_id"],
        "reactive_residue_type": row["reactive_residue_type"],
        "reactive_atom_name": row["reactive_atom_name"],
        "reactive_residue_found": report["reactive_residue_found"],
        "reactive_atom_found": report["reactive_atom_found"],
        "ligand_reactive_atom_id": row["ligand_reactive_atom_id"],
        "scaffold_atoms": row["scaffold_atoms"],
        "linker_atoms": row["linker_atoms"],
        "warhead_atoms": row["warhead_atoms"],
        "scaffold_atom_count": row["scaffold_atom_count"],
        "linker_atom_count": row["linker_atom_count"],
        "warhead_atom_count": row["warhead_atom_count"],
        "candidate_type": row["candidate_type"],
        "dataset_assembly_stage": row["dataset_assembly_stage"],
        "schema_validation_stage": row["schema_validation_stage"],
        "file_hash_gate_stage": row["file_hash_gate_stage"],
        "graph_preview_stage": "graph_preview_candidate_only_not_training",
        "training_ready": "false",
    }


def evaluate_candidate(
    *,
    candidate_id: str,
    locked_rows_by_id: dict[str, list[dict[str, str]]],
    hash_report_by_id: dict[str, dict[str, str]],
    hash_locked_candidates_csv: Path,
    file_hash_report_csv: Path,
) -> tuple[dict[str, str], dict[str, str] | None]:
    expected_source = TARGETS[candidate_id]
    matching_rows = locked_rows_by_id.get(candidate_id, [])
    row = matching_rows[0] if len(matching_rows) == 1 else {}
    hash_report = hash_report_by_id.get(candidate_id, {})
    protein_path = row.get("protein_pdb_path", "")
    ligand_path = row.get("ligand_sdf_path", "")
    protein_exists = bool(protein_path) and Path(protein_path).exists()
    ligand_exists = bool(ligand_path) and Path(ligand_path).exists()
    protein_size_matches = protein_exists and path_size(protein_path) == row.get("protein_pdb_size_bytes", "")
    ligand_size_matches = ligand_exists and path_size(ligand_path) == row.get("ligand_sdf_size_bytes", "")
    protein_hash_matches = protein_exists and path_sha256(protein_path) == row.get("protein_pdb_sha256", "")
    ligand_hash_matches = ligand_exists and path_sha256(ligand_path) == row.get("ligand_sdf_sha256", "")
    ligand_preview = preview_ligand(ligand_path)
    atom_count, atom_count_ok = parse_int(ligand_preview["ligand_atom_count"])
    bond_count, bond_count_ok = parse_int(ligand_preview["ligand_bond_count"])
    scaffold_atoms, scaffold_ok = parse_atom_list(row.get("scaffold_atoms", ""))
    linker_atoms, linker_ok = parse_atom_list(row.get("linker_atoms", ""))
    warhead_atoms, warhead_ok = parse_atom_list(row.get("warhead_atoms", ""))
    atom_groups = [set(scaffold_atoms), set(linker_atoms), set(warhead_atoms)]
    atom_groups_non_overlapping = (
        scaffold_ok
        and linker_ok
        and warhead_ok
        and not (atom_groups[0] & atom_groups[1])
        and not (atom_groups[0] & atom_groups[2])
        and not (atom_groups[1] & atom_groups[2])
    )
    all_group_atoms = scaffold_atoms + linker_atoms + warhead_atoms
    atom_indices_within_range = (
        atom_count_ok
        and atom_count is not None
        and all(index >= 0 and index < atom_count for index in all_group_atoms)
    )
    reactive_atom_id, reactive_atom_ok = parse_int(row.get("ligand_reactive_atom_id", ""))
    reactive_atom_in_range = reactive_atom_ok and atom_count is not None and reactive_atom_id is not None and 0 <= reactive_atom_id < atom_count
    warhead_contains_reactive = reactive_atom_ok and reactive_atom_id in set(warhead_atoms)
    protein_preview = preview_protein(
        protein_path,
        row.get("reactive_residue_chain", ""),
        row.get("reactive_residue_id", ""),
        row.get("reactive_residue_type", ""),
        row.get("reactive_atom_name", ""),
    )
    protein_atom_count, protein_atom_count_ok = parse_int(protein_preview["protein_atom_count"])
    protein_residue_count, protein_residue_count_ok = parse_int(protein_preview["protein_residue_count"])

    checks = [
        ("candidate_row_not_found_once", len(matching_rows) == 1),
        ("candidate_id_not_target", candidate_id in TARGETS),
        ("source_mapping_invalid", row.get("source_sample_id", "") == expected_source),
        ("pre_reaction_sample_id_mismatch", row.get("pre_reaction_sample_id", "") == candidate_id),
        ("training_ready_not_false", row.get("training_ready", "") == "false"),
        (
            "file_hash_gate_stage_invalid",
            row.get("file_hash_gate_stage", "") == "file_existence_and_hash_locked_candidate_only_not_training",
        ),
        ("protein_pdb_missing", protein_exists),
        ("protein_pdb_size_mismatch", protein_size_matches),
        ("protein_pdb_sha256_mismatch", protein_hash_matches),
        ("ligand_sdf_missing", ligand_exists),
        ("ligand_sdf_size_mismatch", ligand_size_matches),
        ("ligand_sdf_sha256_mismatch", ligand_hash_matches),
        (
            "file_hash_gate_not_passed",
            hash_report.get("file_existence_and_hash_gate_status", "") == "file_existence_and_hash_gate_passed",
        ),
        (
            "hash_locked_candidate_written_not_true",
            hash_report.get("hash_locked_candidate_written", "") == "true",
        ),
        (
            "file_hash_report_real_dataset_generated_not_false",
            hash_report.get("real_dataset_generated", "") == "false",
        ),
        ("file_hash_report_training_ready_not_false", hash_report.get("training_ready", "") == "false"),
        ("ligand_rdkit_not_parseable", ligand_preview["ligand_rdkit_parseable"] == "true"),
        ("ligand_atom_count_not_positive", atom_count_ok and atom_count is not None and atom_count > 0),
        ("ligand_bond_count_not_positive", bond_count_ok and bond_count is not None and bond_count > 0),
        ("scaffold_atoms_not_parseable", scaffold_ok),
        ("linker_atoms_not_parseable", linker_ok),
        ("warhead_atoms_not_parseable", warhead_ok),
        ("atom_groups_overlap", atom_groups_non_overlapping),
        ("atom_index_out_of_ligand_range", atom_indices_within_range),
        ("ligand_reactive_atom_id_not_integer", reactive_atom_ok),
        ("ligand_reactive_atom_out_of_range", reactive_atom_in_range),
        ("warhead_missing_ligand_reactive_atom", warhead_contains_reactive),
        ("protein_atom_count_not_positive", protein_atom_count_ok and protein_atom_count is not None and protein_atom_count > 0),
        ("protein_residue_count_not_positive", protein_residue_count_ok and protein_residue_count is not None and protein_residue_count > 0),
        ("reactive_residue_chain_empty", bool(row.get("reactive_residue_chain", ""))),
        ("reactive_residue_id_not_integer", parse_int(row.get("reactive_residue_id", ""))[1]),
        ("reactive_residue_type_not_cys", row.get("reactive_residue_type", "") == "CYS"),
        ("reactive_atom_name_not_sg", row.get("reactive_atom_name", "") == "SG"),
        ("reactive_residue_not_found", protein_preview["reactive_residue_found"] == "true"),
        ("reactive_atom_not_found", protein_preview["reactive_atom_found"] == "true"),
    ]
    reasons = [reason for reason, passed in checks if not passed]
    passed = not reasons
    report = {
        "candidate_id": candidate_id,
        "source_sample_id": row.get("source_sample_id", expected_source),
        "pre_reaction_sample_id": row.get("pre_reaction_sample_id", candidate_id),
        "hash_locked_candidates_csv": str(hash_locked_candidates_csv),
        "file_hash_report_csv": str(file_hash_report_csv),
        "candidate_row_found_once": str(len(matching_rows) == 1).lower(),
        "file_hash_gate_passed": str(hash_report.get("file_existence_and_hash_gate_status", "") == "file_existence_and_hash_gate_passed").lower(),
        "hash_locked_candidate_written_confirmed": str(hash_report.get("hash_locked_candidate_written", "") == "true").lower(),
        "file_hash_report_real_dataset_generated_false": str(hash_report.get("real_dataset_generated", "") == "false").lower(),
        "file_hash_report_training_ready_false": str(hash_report.get("training_ready", "") == "false").lower(),
        "protein_pdb_path": protein_path,
        "protein_pdb_exists": str(protein_exists).lower(),
        "protein_pdb_size_matches_hash_locked": str(protein_size_matches).lower(),
        "protein_pdb_sha256_matches_hash_locked": str(protein_hash_matches).lower(),
        "ligand_sdf_path": ligand_path,
        "ligand_sdf_exists": str(ligand_exists).lower(),
        "ligand_sdf_size_matches_hash_locked": str(ligand_size_matches).lower(),
        "ligand_sdf_sha256_matches_hash_locked": str(ligand_hash_matches).lower(),
        **ligand_preview,
        "scaffold_atoms_parseable": str(scaffold_ok).lower(),
        "linker_atoms_parseable": str(linker_ok).lower(),
        "warhead_atoms_parseable": str(warhead_ok).lower(),
        "atom_groups_non_overlapping": str(atom_groups_non_overlapping).lower(),
        "atom_indices_within_ligand_range": str(atom_indices_within_range).lower(),
        "ligand_reactive_atom_id_is_integer": str(reactive_atom_ok).lower(),
        "ligand_reactive_atom_in_range": str(reactive_atom_in_range).lower(),
        "warhead_contains_ligand_reactive_atom": str(warhead_contains_reactive).lower(),
        **protein_preview,
        "graph_preview_candidate_written": str(passed).lower(),
        "graph_preview_status": "dataset_assembly_graph_preview_passed" if passed else "blocked",
        "manifest_modified": "false",
        "sdf_modified": "false",
        "sdf_generated": "false",
        "real_dataset_generated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": ";".join(reasons),
        "recommended_next_action": (
            "build_dataset_assembly_final_readiness_gate_not_training"
            if passed
            else "fix_dataset_assembly_graph_preview_blockers"
        ),
    }
    return report, build_preview_candidate(row, report) if passed else None


def build_preview(
    *,
    hash_locked_candidates_csv: str | Path,
    file_hash_report_csv: str | Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    hash_locked_path = Path(hash_locked_candidates_csv)
    file_hash_report_path = Path(file_hash_report_csv)
    locked_rows = read_csv(hash_locked_path)
    file_hash_rows = read_csv(file_hash_report_path)
    locked_rows_by_id = index_many(locked_rows, "hash_locked_candidate_id")
    file_hash_report_by_id = index_one(file_hash_rows, "candidate_id")
    reports = []
    preview_candidates = []
    for candidate_id in sorted(TARGETS):
        report, preview_candidate = evaluate_candidate(
            candidate_id=candidate_id,
            locked_rows_by_id=locked_rows_by_id,
            hash_report_by_id=file_hash_report_by_id,
            hash_locked_candidates_csv=hash_locked_path,
            file_hash_report_csv=file_hash_report_path,
        )
        reports.append(report)
        if preview_candidate is not None:
            preview_candidates.append(preview_candidate)
    return reports, preview_candidates


def write_csv(rows: list[dict[str, str]], output_csv: str | Path, fieldnames: list[str]) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(reports: list[dict[str, str]], preview_candidates: list[dict[str, str]]) -> str:
    lines = [
        "# Dataset Assembly Graph Preview Summary",
        "",
        "This is graph preview only.",
        "",
        "- It reads hash-locked candidates.",
        "- It does not modify manifest files.",
        "- It does not modify or generate SDF files.",
        "- It does not generate real training datasets.",
        "- It does not train or fine-tune any model.",
        "- Passing this preview means candidates can enter final readiness gate.",
        "- Passing this preview does not mean the samples are training-ready.",
        "",
        "| candidate_id | ligand_atom_count | ligand_heavy_atom_count | ligand_bond_count | protein_atom_count | protein_residue_count | reactive_residue_found | reactive_atom_found | graph_preview_status | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in reports:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["candidate_id"],
                    row["ligand_atom_count"],
                    row["ligand_heavy_atom_count"],
                    row["ligand_bond_count"],
                    row["protein_atom_count"],
                    row["protein_residue_count"],
                    row["reactive_residue_found"],
                    row["reactive_atom_found"],
                    row["graph_preview_status"],
                    row["training_ready"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    all_passed = all(row["graph_preview_status"] == "dataset_assembly_graph_preview_passed" for row in reports)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            (
                "- All three candidates passed graph preview."
                if all_passed
                else "- One or more candidates are blocked by graph preview."
            ),
            f"- Graph preview candidates CSV contains exactly 3 rows: {str(len(preview_candidates) == 3).lower()}.",
            "- Manifest was not modified.",
            "- No SDF files were modified or generated.",
            "- No real dataset was generated.",
            "- No training was run.",
            "- Next step is final readiness gate, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build dataset assembly graph preview reports.")
    parser.add_argument("--hash_locked_candidates_csv", type=Path, required=True)
    parser.add_argument("--file_hash_report_csv", type=Path, required=True)
    parser.add_argument("--output_preview_candidates_csv", type=Path, required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command performs graph preview only.")
    print("warning: it does not modify manifest or SDF files.")
    print("warning: it does not generate real training datasets.")
    reports, preview_candidates = build_preview(
        hash_locked_candidates_csv=args.hash_locked_candidates_csv,
        file_hash_report_csv=args.file_hash_report_csv,
    )
    write_csv(preview_candidates, args.output_preview_candidates_csv, PREVIEW_CANDIDATE_COLUMNS)
    write_csv(reports, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(build_markdown(reports, preview_candidates), args.output_md)
    print(f"wrote graph preview candidates: {args.output_preview_candidates_csv}")
    print(f"wrote graph preview report: {args.output_report_csv}")
    print(f"wrote graph preview summary: {args.output_md}")
    for row in reports:
        print(
            f"{row['candidate_id']}: "
            f"graph_preview_status={row['graph_preview_status']} "
            f"training_ready={row['training_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
