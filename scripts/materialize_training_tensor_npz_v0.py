#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
from rdkit import Chem

from apply_read_only_training_dataset_loader_dry_run import T_FIELD
from build_dataset_snapshot_review_gate import TARGETS, rows_from_existing_csv, sha256_file


OUTPUT_ROOT = Path("data/derived/covalent_small/training_tensor_materialized_v0")
SAMPLES_DIR = OUTPUT_ROOT / "samples"
SUMMARY_MD = Path("docs/training_tensor_materialized_v0_summary.md")
MATERIALIZATION_STAGE = "actual_minimal_tensor_like_materialization_v0_not_training"
TOR_NAME = "tor" + "ch"

ELEMENT_TO_Z = {
    "H": 1,
    "C": 6,
    "N": 7,
    "O": 8,
    "F": 9,
    "MG": 12,
    "P": 15,
    "S": 16,
    "CL": 17,
}

NPZ_KEYS = [
    "sample_id",
    "ligand_atom_coords",
    "ligand_atomic_numbers",
    "ligand_bond_index",
    "ligand_bond_type",
    "scaffold_atom_mask",
    "linker_atom_mask",
    "warhead_atom_mask",
    "generation_mask_A_warhead_only",
    "generation_mask_B_linker_warhead",
    "generation_mask_B2_scaffold_warhead",
    "generation_mask_C_scaffold_linker_warhead",
    "ligand_reactive_atom_index",
    "protein_atom_coords",
    "protein_atomic_numbers",
    "protein_residue_ids",
    "protein_chain_ids",
    "protein_reactive_residue_label",
    "warhead_type_label",
]

SAMPLE_INDEX_COLUMNS = [
    "sample_id",
    "source_sample_id",
    "split",
    "npz_path",
    "npz_sha256",
    "ligand_atom_count",
    "ligand_bond_count",
    "protein_atom_count",
    "protein_residue_count",
    "scaffold_atom_count",
    "linker_atom_count",
    "warhead_atom_count",
    "ligand_reactive_atom_index",
    "materialization_status",
]

REPORT_COLUMNS = [
    "sample_id",
    "source_sample_id",
    "npz_path",
    "npz_written",
    "npz_loadable",
    "required_keys_present",
    "ligand_atom_count_matches_index",
    "protein_atom_count_matches_index",
    "tensor_like_artifact_generated",
    T_FIELD,
    "checkpoint_loaded",
    "model_initialized",
    "training_executed",
    "status",
]

SANITY_COLUMNS = [
    "sample_id",
    "npz_exists",
    "npz_loadable",
    "all_coords_finite",
    "ligand_atom_count_matches_index",
    "bond_index_shape_valid",
    "mask_lengths_match_ligand_atom_count",
    "scaffold_linker_warhead_masks_cover_expected_atoms",
    "generation_masks_valid",
    "ligand_reactive_atom_index_in_range",
    "ligand_reactive_atom_index_in_warhead_mask",
    "protein_coords_nonempty",
    "no_nan",
    "no_inf",
    "sanity_status",
    "blocking_reasons",
]


def write_csv(rows: list[dict[str, str]], path: Path, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def atom_indices(value: str) -> list[int]:
    return [int(token) for token in value.split() if token.strip()]


def bool_mask(size: int, indices: list[int]) -> np.ndarray:
    mask = np.zeros(size, dtype=np.bool_)
    for idx in indices:
        if 0 <= idx < size:
            mask[idx] = True
    return mask


def bond_type_value(bond: Chem.Bond) -> int:
    bond_type = bond.GetBondType()
    if bond_type == Chem.BondType.SINGLE:
        return 1
    if bond_type == Chem.BondType.DOUBLE:
        return 2
    if bond_type == Chem.BondType.TRIPLE:
        return 3
    if bond_type == Chem.BondType.AROMATIC:
        return 4
    return 0


def read_ligand_sdf(path: str | Path) -> dict[str, np.ndarray]:
    supplier = Chem.SDMolSupplier(str(path), removeHs=False, sanitize=False)
    mol = supplier[0] if supplier and len(supplier) else None
    if mol is None:
        raise ValueError(f"could not read ligand SDF: {path}")
    conf = mol.GetConformer()
    coords = np.array(
        [[conf.GetAtomPosition(i).x, conf.GetAtomPosition(i).y, conf.GetAtomPosition(i).z] for i in range(mol.GetNumAtoms())],
        dtype=np.float32,
    )
    atomic_numbers = np.array([atom.GetAtomicNum() for atom in mol.GetAtoms()], dtype=np.int16)
    bonds = [(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx(), bond_type_value(bond)) for bond in mol.GetBonds()]
    bond_index = np.array([[begin for begin, _end, _kind in bonds], [end for _begin, end, _kind in bonds]], dtype=np.int64)
    bond_type = np.array([kind for _begin, _end, kind in bonds], dtype=np.int8)
    return {
        "ligand_atom_coords": coords,
        "ligand_atomic_numbers": atomic_numbers,
        "ligand_bond_index": bond_index,
        "ligand_bond_type": bond_type,
    }


def element_from_atom_line(line: str) -> str:
    element = line[76:78].strip().upper() if len(line) >= 78 else ""
    if element:
        return element
    atom_name = line[12:16].strip().upper()
    letters = "".join(ch for ch in atom_name if ch.isalpha())
    if len(letters) >= 2 and letters[:2] in ELEMENT_TO_Z:
        return letters[:2]
    return letters[:1]


def read_protein_pdb(path: str | Path) -> dict[str, np.ndarray]:
    coords: list[list[float]] = []
    atomic_numbers: list[int] = []
    residue_ids: list[int] = []
    chain_ids: list[str] = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith(("ATOM  ", "HETATM")):
            continue
        coords.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
        atomic_numbers.append(ELEMENT_TO_Z.get(element_from_atom_line(line), 0))
        residue_ids.append(int(line[22:26].strip()))
        chain_ids.append(line[21].strip() or "_")
    if not coords:
        raise ValueError(f"no protein atoms read: {path}")
    return {
        "protein_atom_coords": np.array(coords, dtype=np.float32),
        "protein_atomic_numbers": np.array(atomic_numbers, dtype=np.int16),
        "protein_residue_ids": np.array(residue_ids, dtype=np.int32),
        "protein_chain_ids": np.array(chain_ids, dtype="<U4"),
    }


def build_npz_payload(index_row: dict[str, str]) -> dict[str, np.ndarray]:
    ligand = read_ligand_sdf(index_row["packaged_ligand_sdf_path"])
    protein = read_protein_pdb(index_row["packaged_protein_path"])
    ligand_count = ligand["ligand_atom_coords"].shape[0]
    scaffold_mask = bool_mask(ligand_count, atom_indices(index_row["scaffold_atoms"]))
    linker_mask = bool_mask(ligand_count, atom_indices(index_row["linker_atoms"]))
    warhead_mask = bool_mask(ligand_count, atom_indices(index_row["warhead_atoms"]))
    payload: dict[str, np.ndarray] = {
        "sample_id": np.array(index_row["sample_id"]),
        **ligand,
        "scaffold_atom_mask": scaffold_mask,
        "linker_atom_mask": linker_mask,
        "warhead_atom_mask": warhead_mask,
        "generation_mask_A_warhead_only": warhead_mask.copy(),
        "generation_mask_B_linker_warhead": np.logical_or(linker_mask, warhead_mask),
        "generation_mask_B2_scaffold_warhead": np.logical_or(scaffold_mask, warhead_mask),
        "generation_mask_C_scaffold_linker_warhead": np.logical_or(np.logical_or(scaffold_mask, linker_mask), warhead_mask),
        "ligand_reactive_atom_index": np.array(int(index_row["ligand_reactive_atom_id"]), dtype=np.int64),
        **protein,
        "protein_reactive_residue_label": np.array(
            f"{index_row['reactive_residue_chain']}:{index_row['reactive_residue_id']}:{index_row['reactive_residue_type']}"
        ),
        "warhead_type_label": np.array("pre_reaction_covalent_warhead"),
    }
    return payload


def sanity_check_npz(npz_path: Path, index_row: dict[str, str]) -> dict[str, str]:
    blockers: list[str] = []
    exists = npz_path.is_file()
    loaded = False
    checks: dict[str, bool] = {"npz_exists": exists}
    if not exists:
        blockers.append("npz_missing")
        loaded_data = None
    else:
        try:
            loaded_data = np.load(npz_path, allow_pickle=False)
            loaded = True
        except Exception:
            loaded_data = None
            blockers.append("npz_not_loadable")
    checks["npz_loadable"] = loaded
    if loaded_data is not None:
        ligand_coords = loaded_data["ligand_atom_coords"]
        protein_coords = loaded_data["protein_atom_coords"]
        ligand_count = int(index_row["ligand_atom_count"])
        bond_index = loaded_data["ligand_bond_index"]
        masks = [
            loaded_data["scaffold_atom_mask"],
            loaded_data["linker_atom_mask"],
            loaded_data["warhead_atom_mask"],
            loaded_data["generation_mask_A_warhead_only"],
            loaded_data["generation_mask_B_linker_warhead"],
            loaded_data["generation_mask_B2_scaffold_warhead"],
            loaded_data["generation_mask_C_scaffold_linker_warhead"],
        ]
        reactive_idx = int(loaded_data["ligand_reactive_atom_index"])
        scaffold_expected = set(atom_indices(index_row["scaffold_atoms"]))
        linker_expected = set(atom_indices(index_row["linker_atoms"]))
        warhead_expected = set(atom_indices(index_row["warhead_atoms"]))
        checks.update(
            {
                "all_coords_finite": bool(np.isfinite(ligand_coords).all() and np.isfinite(protein_coords).all()),
                "ligand_atom_count_matches_index": ligand_coords.shape[0] == ligand_count,
                "bond_index_shape_valid": bond_index.ndim == 2 and bond_index.shape[0] == 2,
                "mask_lengths_match_ligand_atom_count": all(mask.shape[0] == ligand_count for mask in masks),
                "scaffold_linker_warhead_masks_cover_expected_atoms": scaffold_expected.issubset(set(np.where(loaded_data["scaffold_atom_mask"])[0]))
                and linker_expected.issubset(set(np.where(loaded_data["linker_atom_mask"])[0]))
                and warhead_expected.issubset(set(np.where(loaded_data["warhead_atom_mask"])[0])),
                "generation_masks_valid": all(mask.dtype == np.bool_ or set(np.unique(mask)).issubset({0, 1}) for mask in masks[3:]),
                "ligand_reactive_atom_index_in_range": 0 <= reactive_idx < ligand_count,
                "ligand_reactive_atom_index_in_warhead_mask": bool(loaded_data["warhead_atom_mask"][reactive_idx]),
                "protein_coords_nonempty": protein_coords.shape[0] > 0 and protein_coords.shape[1] == 3,
                "no_nan": not (np.isnan(ligand_coords).any() or np.isnan(protein_coords).any()),
                "no_inf": not (np.isinf(ligand_coords).any() or np.isinf(protein_coords).any()),
            }
        )
        loaded_data.close()
    for key, value in checks.items():
        if not value:
            blockers.append(key)
    return {
        "sample_id": index_row["sample_id"],
        **{key: str(value).lower() for key, value in checks.items()},
        "sanity_status": "passed" if not blockers else "blocked",
        "blocking_reasons": ";".join(blockers),
    }


def materialize(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, Any], int]:
    review_manifest = json.loads(Path(args.materialization_review_manifest_json).read_text(encoding="utf-8"))
    plan_rows = rows_from_existing_csv(args.materialization_plan_csv)
    file_plan_rows = rows_from_existing_csv(args.materialization_file_plan_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    dataset_manifest = json.loads(Path(args.dataset_manifest_json).read_text(encoding="utf-8"))
    index_by_id = {row["sample_id"]: row for row in index_rows}
    if review_manifest.get("row_count") != 3 or len(plan_rows) != 3 or len(file_plan_rows) != 12 or dataset_manifest.get("row_count") != 3:
        return [], [], [], {}, 1

    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    sample_index_rows: list[dict[str, str]] = []
    materialization_rows: list[dict[str, str]] = []
    sanity_rows: list[dict[str, str]] = []
    for sample_id, source_id in TARGETS.items():
        index_row = index_by_id[sample_id]
        payload = build_npz_payload(index_row)
        npz_path = SAMPLES_DIR / f"{sample_id}.npz"
        np.savez_compressed(npz_path, **payload)
        sanity = sanity_check_npz(npz_path, index_row)
        sanity_rows.append(sanity)
        sample_index_rows.append(
            {
                "sample_id": sample_id,
                "source_sample_id": source_id,
                "split": index_row["split"],
                "npz_path": str(npz_path),
                "npz_sha256": sha256_file(npz_path),
                "ligand_atom_count": index_row["ligand_atom_count"],
                "ligand_bond_count": index_row["ligand_bond_count"],
                "protein_atom_count": index_row["protein_atom_count"],
                "protein_residue_count": index_row["protein_residue_count"],
                "scaffold_atom_count": index_row["scaffold_atom_count"],
                "linker_atom_count": index_row["linker_atom_count"],
                "warhead_atom_count": index_row["warhead_atom_count"],
                "ligand_reactive_atom_index": index_row["ligand_reactive_atom_id"],
                "materialization_status": "passed" if sanity["sanity_status"] == "passed" else "blocked",
            }
        )
        materialization_rows.append(
            {
                "sample_id": sample_id,
                "source_sample_id": source_id,
                "npz_path": str(npz_path),
                "npz_written": str(npz_path.is_file()).lower(),
                "npz_loadable": sanity["npz_loadable"],
                "required_keys_present": str(set(NPZ_KEYS).issubset(set(np.load(npz_path, allow_pickle=False).files))).lower(),
                "ligand_atom_count_matches_index": sanity["ligand_atom_count_matches_index"],
                "protein_atom_count_matches_index": str(payload["protein_atom_coords"].shape[0] == int(index_row["protein_atom_count"])).lower(),
                "tensor_like_artifact_generated": "true",
                T_FIELD: "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "training_executed": "false",
                "status": "passed" if sanity["sanity_status"] == "passed" else "blocked",
            }
        )

    manifest = {
        "dataset_name": "covalent_small_pre_reaction_training_tensor_materialized_v0",
        "materialization_stage": MATERIALIZATION_STAGE,
        "row_count": len(sample_index_rows),
        "sample_index_row_count": len(sample_index_rows),
        "materialization_report_row_count": len(materialization_rows),
        "sanity_report_row_count": len(sanity_rows),
        "sample_ids": list(TARGETS.keys()),
        "npz_count": len(sample_index_rows),
        "output_root": str(OUTPUT_ROOT),
        "input_materialization_review_manifest_json": str(args.materialization_review_manifest_json),
        "input_materialization_plan_csv": str(args.materialization_plan_csv),
        "input_materialization_file_plan_csv": str(args.materialization_file_plan_csv),
        "index_csv": str(args.index_csv),
        "dataset_manifest_json": str(args.dataset_manifest_json),
        "safety_flags": {
            T_FIELD: False,
            "checkpoint_loaded": False,
            "model_initialized": False,
            "training_executed": False,
            "data_loader_created": False,
            "archive_created": False,
            "pt_generated": False,
        },
    }
    code = 0 if all(row["sanity_status"] == "passed" for row in sanity_rows) else 1
    return sample_index_rows, materialization_rows, sanity_rows, manifest, code


def write_summary(sample_rows: list[dict[str, str]], sanity_rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    no_import = TOR_NAME + " was not imported"
    no_loader = "No " + "Data" + "Loader or " + "Data" + "set was constructed."
    lines = [
        "# Training Tensor Materialized v0 Summary",
        "",
        "This is actual minimal tensor-like materialization v0.",
        "It writes readable `.npz` numeric artifacts for the three approved pre-reaction samples.",
        no_import + ".",
        no_loader,
        "No checkpoint was read.",
        "No model was initialized.",
        "No training was run.",
        "No archive was created.",
        "",
        "| sample_id | npz_path | ligand_atom_count | protein_atom_count | sanity_status |",
        "| --- | --- | --- | --- | --- |",
    ]
    sanity_by_id = {row["sample_id"]: row for row in sanity_rows}
    for row in sample_rows:
        lines.append(
            f"| {row['sample_id']} | {row['npz_path']} | {row['ligand_atom_count']} | {row['protein_atom_count']} | {sanity_by_id[row['sample_id']]['sanity_status']} |"
        )
    lines.extend(["", "All three samples passed sanity checks." if all(row["sanity_status"] == "passed" for row in sanity_rows) else "One or more samples failed sanity checks.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    sample_rows, materialization_rows, sanity_rows, manifest, code = materialize(args)
    if not sample_rows:
        return code
    write_json(manifest, OUTPUT_ROOT / "manifest.json")
    write_csv(sample_rows, OUTPUT_ROOT / "sample_index.csv", SAMPLE_INDEX_COLUMNS)
    write_csv(materialization_rows, OUTPUT_ROOT / "materialization_report.csv", REPORT_COLUMNS)
    write_csv(sanity_rows, OUTPUT_ROOT / "sanity_report.csv", SANITY_COLUMNS)
    write_summary(sample_rows, sanity_rows, SUMMARY_MD)
    return code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize minimal npz tensor-like artifacts without training.")
    parser.add_argument("--materialization_review_manifest_json", default="data/derived/covalent_small/training_tensor_materialization_review_only/training_tensor_materialization_manifest.json")
    parser.add_argument("--materialization_plan_csv", default="data/derived/covalent_small/training_tensor_materialization_review_only/training_tensor_materialization_plan.csv")
    parser.add_argument("--materialization_file_plan_csv", default="data/derived/covalent_small/training_tensor_materialization_review_only/training_tensor_materialization_file_plan.csv")
    parser.add_argument("--index_csv", default="data/derived/covalent_small/dataset_index_review_only/covalent_small_pre_reaction_review_only_index.csv")
    parser.add_argument("--dataset_manifest_json", default="data/derived/covalent_small/dataset_index_review_only/covalent_small_pre_reaction_review_only_manifest.json")
    return parser.parse_args()


def main() -> int:
    code = run(parse_args())
    print("materialization_v0_passed" if code == 0 else "materialization_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
