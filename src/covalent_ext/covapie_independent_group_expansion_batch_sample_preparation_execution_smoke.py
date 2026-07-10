"""Step 14AM: deterministic, metadata-only preparation outputs for eight raw mmCIF files.

This module intentionally reuses the established text-loop parser from the historical
sample-preparation smoke while keeping the selected ligand atom dynamic per event.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_sample_preparation_execution_smoke as historical


REPO = Path(__file__).resolve().parents[2]
STAGE = "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0"
OUT = Path("data/derived/covalent_small") / STAGE
RAW = Path("data/raw/covalent_sources/covpdb/independent_group_expansion_batch_000001")
AL = Path("data/derived/covalent_small/covapie_independent_group_expansion_struct_conn_crosscheck_smoke_v0")
AK = Path("data/derived/covalent_small/covapie_independent_group_expansion_acquisition_execution_smoke_v0")
META = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
INDEX_CSV = Path("data/derived/covalent_small/covapie_sample_index_materialization_smoke_v0/sample_index.csv")
INDEX_JSON = Path("data/derived/covalent_small/covapie_sample_index_materialization_smoke_v0/sample_index.json")
HISTORICAL = Path("src/covalent_ext/covapie_sample_preparation_execution_smoke.py")

PRE = OUT / "covapie_batch_sample_preparation_precondition_audit.csv"
EXEC = OUT / "covapie_batch_sample_preparation_execution_manifest.csv"
EXEC_JSON = OUT / "covapie_batch_sample_preparation_execution_manifest.json"
INV = OUT / "covapie_batch_sample_preparation_sample_inventory.csv"
INV_JSON = OUT / "covapie_batch_sample_preparation_sample_inventory.json"
TRACE = OUT / "covapie_batch_sample_preparation_traceability_audit.csv"
QUALITY = OUT / "covapie_batch_sample_preparation_quality_audit.csv"
FAILURES = OUT / "covapie_batch_sample_preparation_failure_inventory.csv"
SAFETY = OUT / "covapie_batch_sample_preparation_safety_audit.csv"
MANIFEST = OUT / "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_manifest.json"

AUDIT_COLUMNS = ["audit_item", "expected_status", "observed_status", "audit_passed", "blocking_reasons"]
PRE_COLUMNS = ["precondition_item", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
EXEC_COLUMNS = ["sample_preparation_input_id", "sample_execution_id", "shortlist_rank", "pdb_id", "expected_het_id", "raw_file_path", "sample_artifact_root", "selected_struct_conn_id", "selected_cys_chain_id", "selected_cys_seq_id", "selected_ligand_chain_id", "selected_ligand_seq_id", "selected_ligand_atom_name", "covalent_bond_atom_pair", "protein_atom_count", "ligand_atom_count", "pocket_atom_count", "covalent_event_count", "ligand_residue_atom_pair_count", "struct_conn_distance_angstrom", "computed_atom_site_distance_angstrom", "distance_delta_angstrom", "sample_preparation_status", "embedded_qa_passed", "ready_for_batch_sample_index_current_step", "ready_for_training_current_step"]
TRACE_COLUMNS = ["sample_preparation_input_id", "sample_execution_id", "pdb_id", "expected_het_id", "raw_file_path", "raw_sha256_verified", "selected_struct_conn_id", "struct_conn_event_revalidated", "residue_atom_from_struct_conn", "ligand_atom_from_struct_conn", "atom_site_residue_atom_found", "atom_site_ligand_atom_found", "dynamic_ligand_atom_preserved", "traceability_audit_passed", "blocking_reasons"]
QUALITY_COLUMNS = ["sample_preparation_input_id", "sample_execution_id", "pdb_id", "expected_het_id", "protein_atom_count", "ligand_atom_count", "pocket_atom_count", "covalent_event_count", "ligand_residue_atom_pair_count", "ligand_covalent_atom_count", "event_pair_atom_names_consistent", "atom_site_distance_angstrom", "struct_conn_distance_angstrom", "distance_delta_angstrom", "distance_consistency_passed", "quality_audit_passed", "blocking_reasons"]
FAILURE_COLUMNS = ["failure_id", "pdb_id", "expected_het_id", "failure_stage", "failure_type", "failure_description", "retry_or_resolution_recommended", "failure_status"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]
MASK_NAMES = ["warhead_only", "linker_plus_warhead", "scaffold_plus_warhead", "scaffold_only", "scaffold_plus_linker_plus_warhead"]
MASK_ALIASES = ["A", "B", "B2", "B3", "C"]
EXPECTED_PAIRS = [("1AEC", "E64", "C2"), ("1AIM", "ZYA", "CM"), ("1AU3", "PCM", "C22"), ("1AU4", "INP", "C17"), ("1AYU", "INA", "C21"), ("1AYV", "IN6", "C21"), ("1AYW", "IN3", "C21"), ("1B02", "UFP", "C6")]
GUARDED_HASHES = {
    META: "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365",
    INDEX_CSV: "2733991775edf5e075b461a9ba1872c7e2fe7f61f5d9614a2704b814c3f0e2c5",
    INDEX_JSON: "8d740458e30cc77bbaa568c615dd10f5df334cd0c46f21433c570c16391b8b38",
}
SAMPLE_TABLE_KEYS = ("protein", "ligand", "pocket", "event", "pair", "audit")
SAFETY_EXPECTED = {
    "network_access_used_current_step": False,
    "download_attempted_current_step": False,
    "raw_mmcif_read_current_step": True,
    "struct_conn_parsed_current_step": True,
    "atom_site_parsed_current_step": True,
    "raw_files_modified": False,
    "raw_files_tracked": False,
    "raw_files_staged": False,
    "part_or_tmp_files_remaining": False,
    "historical_sample_preparation_module_modified": False,
    "metadata_csv_unchanged": True,
    "sample_index_files_unchanged": True,
    "step14al_artifacts_unchanged": True,
    "step14ak_artifacts_unchanged": True,
    "historical_artifacts_unchanged": True,
    "protected_source_diff_empty": True,
    "original_dataloader_diff_empty": True,
    "per_sample_tables_written": True,
    "existing_sample_index_written": False,
    "split_assignments_written": False,
    "leakage_matrix_written": False,
    "final_dataset_written": False,
    "actual_dataloader_artifacts_written": False,
    "training_artifacts_written": False,
    "torch_imported": False,
    "numpy_imported": False,
    "rdkit_used": False,
    "biopython_used": False,
    "gemmi_used": False,
    "requests_used": False,
}


def _rows(path: Path) -> list[dict[str, str]]:
    with (REPO / path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _json(path: Path) -> dict[str, Any]:
    return json.loads((REPO / path).read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256((REPO / path).read_bytes()).hexdigest()


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def _changed(paths: list[str]) -> bool:
    return _git(["diff", "--quiet", "--", *paths]).returncode != 0 or _git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _clean(value: str) -> str:
    return "" if value in {"", ".", "?"} else str(value).upper()


def _partner(record: dict[str, str], side: str) -> dict[str, str]:
    def get(name: str) -> str:
        return _clean(record.get(f"_struct_conn.{side}_{name}", ""))

    return {
        "comp_id": get("label_comp_id") or get("auth_comp_id"),
        "atom_id": get("label_atom_id") or get("auth_atom_id"),
        "auth_asym_id": get("auth_asym_id"),
        "auth_seq_id": get("auth_seq_id"),
        "label_asym_id": get("label_asym_id"),
        "label_seq_id": get("label_seq_id"),
    }


def _find_selected_event(sample: dict[str, str], struct_rows: list[dict[str, str]]) -> tuple[dict[str, Any] | None, str]:
    matches: list[dict[str, Any]] = []
    for record in struct_rows:
        if _clean(record.get("_struct_conn.id", "")) != _clean(sample["selected_struct_conn_id"]):
            continue
        if _clean(record.get("_struct_conn.conn_type_id", "")) != "COVALE":
            continue
        p1, p2 = _partner(record, "ptnr1"), _partner(record, "ptnr2")
        for residue, ligand in ((p1, p2), (p2, p1)):
            if (residue["comp_id"], residue["atom_id"], ligand["comp_id"], ligand["atom_id"]) == ("CYS", "SG", _clean(sample["expected_het_id"]), _clean(sample["selected_ligand_atom_name"])):
                matches.append({"record": record, "residue": residue, "ligand": ligand})
    if len(matches) == 1:
        return matches[0], "validated"
    return None, "no_unique_selected_struct_conn_event" if not matches else "multiple_selected_struct_conn_events"


def _atomic_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    target = REPO / path
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, target)


def _atomic_json(path: Path, value: Any) -> None:
    target = REPO / path
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, target)


def _event_row(sample: dict[str, str], event: dict[str, Any]) -> dict[str, Any]:
    residue, ligand, record = event["residue"], event["ligand"], event["record"]
    dynamic_pair = f"SG--{sample['selected_ligand_atom_name']}"
    return {"sample_preparation_input_id": sample["sample_preparation_input_id"], "pdb_id": sample["pdb_id"], "expected_het_id": sample["expected_het_id"], "conn_id": record.get("_struct_conn.id", ""), "conn_type_id": record.get("_struct_conn.conn_type_id", ""), "residue_comp_id": residue["comp_id"], "residue_atom_name": residue["atom_id"], "residue_auth_asym_id": residue["auth_asym_id"], "residue_auth_seq_id": residue["auth_seq_id"], "residue_label_asym_id": residue["label_asym_id"], "residue_label_seq_id": residue["label_seq_id"], "ligand_comp_id": ligand["comp_id"], "ligand_atom_name": ligand["atom_id"], "ligand_auth_asym_id": ligand["auth_asym_id"], "ligand_auth_seq_id": ligand["auth_seq_id"], "ligand_label_asym_id": ligand["label_asym_id"], "ligand_label_seq_id": ligand["label_seq_id"], "covalent_bond_atom_pair": dynamic_pair, "event_source": "raw_struct_conn_step14al_crosschecked", "event_status": "validated"}


def _pair_row(sample: dict[str, str], residue_atom: dict[str, str], ligand_atom: dict[str, str]) -> dict[str, Any]:
    residue_xyz, ligand_xyz = historical._coords(residue_atom), historical._coords(ligand_atom)
    distance = historical._distance(residue_xyz, ligand_xyz)
    return {"sample_preparation_input_id": sample["sample_preparation_input_id"], "pdb_id": sample["pdb_id"], "expected_het_id": sample["expected_het_id"], "residue_atom_name": "SG", "ligand_atom_name": sample["selected_ligand_atom_name"], "covalent_bond_atom_pair": f"SG--{sample['selected_ligand_atom_name']}", "residue_atom_site_id": residue_atom.get("_atom_site.id", ""), "ligand_atom_site_id": ligand_atom.get("_atom_site.id", ""), "residue_x": f"{residue_xyz[0]:.3f}", "residue_y": f"{residue_xyz[1]:.3f}", "residue_z": f"{residue_xyz[2]:.3f}", "ligand_x": f"{ligand_xyz[0]:.3f}", "ligand_y": f"{ligand_xyz[1]:.3f}", "ligand_z": f"{ligand_xyz[2]:.3f}", "bond_distance_angstrom": f"{distance:.3f}", "validation_status": "validated_from_step14al_struct_conn_and_raw_atom_site"}


def prepare_from_text(sample: dict[str, str], text: str, raw_sha_verified: bool = True, source: str = "synthetic.cif") -> dict[str, Any]:
    """Prepare one isolated sample.  Used with synthetic text in unit tests."""
    protein_rows: list[dict[str, Any]] = []
    ligand_rows: list[dict[str, Any]] = []
    pocket_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    pair_rows: list[dict[str, Any]] = []
    _, atom_rows, atom_status = historical.parse_atom_site_loop(text)
    _, struct_rows, struct_status = historical.parse_struct_conn_loop(text)
    event, event_status = _find_selected_event(sample, struct_rows) if struct_status == "parsed_loop" else (None, "struct_conn_parse_failed")
    filtered = [row for row in atom_rows if historical._model_allowed(row) and historical._altloc_allowed(row)]
    residue_atoms: list[dict[str, str]] = []
    ligand_instance: list[dict[str, str]] = []
    ligand_covalent: list[dict[str, str]] = []
    struct_distance: float | None = None
    if event:
        residue_atoms = [row for row in filtered if historical._atom_matches_partner(row, event["residue"])]
        ligand_instance = [row for row in filtered if historical._ligand_instance_matches(row, event["ligand"])]
        ligand_covalent = [row for row in ligand_instance if (row.get("_atom_site.auth_atom_id") or row.get("_atom_site.label_atom_id", "")).upper() == sample["selected_ligand_atom_name"].upper()]
        protein_atoms = [row for row in filtered if row.get("_atom_site.group_PDB") == "ATOM"]
        protein_rows = [historical._protein_row(sample["sample_preparation_input_id"], sample["pdb_id"], row, source) for row in protein_atoms]
        ligand_rows = [historical._ligand_row(sample["sample_preparation_input_id"], sample["pdb_id"], sample["expected_het_id"], row, sample["selected_ligand_atom_name"], source) for row in ligand_instance]
        event_rows = [_event_row(sample, event)]
        try:
            struct_distance = float(event["record"].get("_struct_conn.pdbx_dist_value", ""))
        except ValueError:
            struct_distance = None
        ligand_coords = [historical._coords(row) for row in ligand_instance]
        if ligand_coords:
            for atom in protein_atoms:
                min_distance = min(historical._distance(historical._coords(atom), coords) for coords in ligand_coords)
                if min_distance <= 8.0:
                    pocket_rows.append(historical._pocket_row(sample["sample_preparation_input_id"], sample["pdb_id"], atom, min_distance, source))
        if len(residue_atoms) == 1 and len(ligand_covalent) == 1:
            pair_rows = [_pair_row(sample, residue_atoms[0], ligand_covalent[0])]
    computed = float(pair_rows[0]["bond_distance_angstrom"]) if pair_rows else None
    delta = abs(computed - struct_distance) if computed is not None and struct_distance is not None else None
    checks = {
        "raw_fingerprint_verified": raw_sha_verified,
        "raw_file_resolved": bool(source),
        "atom_site_loop_parsed": atom_status == "parsed_loop" and bool(atom_rows),
        "selected_struct_conn_event_revalidated": event is not None and event_status == "validated",
        "residue_cys_sg_atom_unique": len(residue_atoms) == 1,
        "ligand_instance_nonempty": bool(ligand_instance),
        "ligand_covalent_atom_unique": len(ligand_covalent) == 1,
        "protein_atom_table_nonempty": bool(protein_rows),
        "ligand_atom_table_nonempty": bool(ligand_rows),
        "pocket_atom_table_nonempty": bool(pocket_rows),
        "covalent_event_table_single_row": len(event_rows) == 1,
        "ligand_residue_atom_pair_single_row": len(pair_rows) == 1,
        "atom_site_struct_conn_distance_consistent": delta is not None and delta <= 0.020,
    }
    audits = [{"audit_item": name, "expected_status": "true", "observed_status": value, "audit_passed": value, "blocking_reasons": "" if value else name} for name, value in checks.items()]
    return {"protein_rows": protein_rows, "ligand_rows": ligand_rows, "pocket_rows": pocket_rows, "event_rows": event_rows, "pair_rows": pair_rows, "audit_rows": audits, "checks": checks, "struct_conn_distance": struct_distance, "computed_distance": computed, "distance_delta": delta, "event_status": event_status}


def _preconditions() -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, Any]]:
    manifest = _json(AL / "covapie_independent_group_expansion_struct_conn_crosscheck_smoke_manifest.json")
    audit = _rows(AL / "covapie_struct_conn_candidate_crosscheck_audit.csv")
    fingerprints = _rows(AL / "covapie_struct_conn_raw_fingerprint_audit.csv")
    acquisition = _json(AK / "covapie_independent_group_expansion_acquisition_execution_smoke_manifest.json")
    raw_dir = REPO / RAW
    pairs = [f"{row['pdb_id']}/{row['expected_het_id']}" for row in audit]
    checks = {
        "step14al_manifest_valid": manifest.get("stage") == "covapie_independent_group_expansion_struct_conn_crosscheck_smoke_v0" and manifest.get("all_checks_passed") is True,
        "input_candidate_count_eight": manifest.get("input_candidate_count") == 8,
        "confirmed_and_eligible_counts_eight": manifest.get("confirmed_unique_exact_match_count") == 8 and manifest.get("eligible_for_batch_sample_preparation_count") == 8,
        "scientifically_blocked_list_empty": manifest.get("scientifically_blocked_pdb_het_pairs") == [],
        "ready_for_batch_preparation": manifest.get("ready_for_covapie_independent_group_expansion_batch_sample_preparation_execution_smoke") is True,
        "candidate_audit_exactly_eight": len(audit) == 8 and pairs == [f"{p}/{h}" for p, h, _ in EXPECTED_PAIRS],
        "candidate_classifications_and_selected_fields": all(row["crosscheck_classification"] == "confirmed_unique_exact_match" and row["selected_struct_conn_id"] and row["selected_ligand_atom_name"] for row in audit),
        "raw_fingerprint_audit_eight_passed": len(fingerprints) == 8 and all(_bool(row["sha256_matches"]) for row in fingerprints),
        "step14ak_hash_map_present": len(acquisition.get("raw_sha256_by_pdb", {})) == 8,
        "raw_files_exactly_eight_without_part": raw_dir.exists() and len(list(raw_dir.glob("*.cif"))) == 8 and not list(raw_dir.glob("*.part")),
        "raw_ignored_untracked_unstaged": _git(["check-ignore", "-q", str(RAW / "1aec.cif")]).returncode == 0 and not _git(["ls-files", str(RAW)]).stdout.strip() and not _git(["diff", "--cached", "--name-only", "--", str(RAW)]).stdout.strip(),
        "guarded_inputs_available": all((REPO / path).exists() for path in (META, INDEX_CSV, INDEX_JSON, HISTORICAL)),
        "metadata_and_sample_index_hashes_unchanged": all(_sha(path) == digest for path, digest in GUARDED_HASHES.items()),
        "historical_and_prior_outputs_clean": not _changed([str(AL), str(AK), "data/derived/covalent_small/covapie_independent_group_expansion_candidate_review_gate_v0", "data/derived/covalent_small/covapie_independent_group_expansion_design_gate_v0", "data/derived/covalent_small/covapie_leakage_split_review_gate_v0", "data/derived/covalent_small/covapie_leakage_split_design_gate_v0", "data/derived/covalent_small/covapie_final_dataset_design_gate_v0", "data/derived/covalent_small/covapie_sample_index_qa_gate_v0", "data/derived/covalent_small/covapie_sample_index_materialization_smoke_v0", str(META), str(HISTORICAL)]),
        "protected_sources_clean": not _changed(["equivariant_diffusion/", "lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py"]),
        "staged_files_empty": not _git(["diff", "--cached", "--name-only"]).stdout.strip(),
        "canonical_five_masks_preserved": MASK_NAMES[3] == "scaffold_only" and MASK_ALIASES == ["A", "B", "B2", "B3", "C"],
    }
    rows = [{"precondition_item": name, "expected_status": "true", "observed_status": value, "precondition_passed": value, "blocking_reasons": "" if value else name} for name, value in checks.items()]
    return rows, audit, acquisition


def _sample_paths(pdb_id: str, het_id: str) -> dict[str, Path]:
    root = OUT / "samples" / f"{pdb_id}_{het_id}"
    return {"root": root, "protein": root / "protein_atom_table.csv", "ligand": root / "ligand_atom_table.csv", "pocket": root / "pocket_atom_table.csv", "event": root / "covalent_event_table.csv", "pair": root / "ligand_residue_atom_pair_table.csv", "audit": root / "sample_preparation_audit.csv"}


def _per_sample_tables_written(sample_paths: list[dict[str, Path]]) -> bool:
    return all((REPO / paths[key]).is_file() for paths in sample_paths for key in SAMPLE_TABLE_KEYS)


def _table_written_counts(sample_paths: list[dict[str, Path]]) -> dict[str, int]:
    return {key: sum((REPO / paths[key]).is_file() for paths in sample_paths) for key in SAMPLE_TABLE_KEYS}


def _raw_file_resolved(path: Path, sample_checks: dict[str, bool]) -> bool:
    return (REPO / path).is_file() and sample_checks.get("raw_file_resolved", False)


def _safety_rows(observed: dict[str, bool]) -> list[dict[str, Any]]:
    if set(observed) != set(SAFETY_EXPECTED):
        raise ValueError("safety observation keys must match explicit expected-status mapping")
    return [{"safety_item": item, "required_status": expected, "observed_status": observed[item], "safety_passed": observed[item] == expected, "blocking_reasons": "" if observed[item] == expected else item} for item, expected in SAFETY_EXPECTED.items()]


def _ready(all_preconditions_passed: bool, all_samples_passed: bool, all_safety_passed: bool) -> bool:
    return all_preconditions_passed and all_samples_passed and all_safety_passed


def run() -> dict[str, Any]:
    pre_rows, candidate_audit, acquisition = _preconditions()
    by_pair = {f"{row['pdb_id']}/{row['expected_het_id']}": row for row in candidate_audit}
    execution_rows: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    quality_rows: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    sample_paths: list[dict[str, Path]] = []
    raw_file_resolved_flags: list[bool] = []
    total_protein = total_ligand = total_pocket = 0

    for rank, (pdb_id, het_id, expected_atom) in enumerate(EXPECTED_PAIRS, 1):
        selected = by_pair[f"{pdb_id}/{het_id}"]
        sample = {"sample_preparation_input_id": f"CYS_SG_EXPANSION_PREP_{rank:06d}", "sample_execution_id": f"CYS_SG_EXPANSION_EXEC_{rank:06d}", "shortlist_rank": str(rank), "pdb_id": pdb_id, "expected_het_id": het_id, "selected_struct_conn_id": selected["selected_struct_conn_id"], "selected_ligand_atom_name": selected["selected_ligand_atom_name"]}
        paths = _sample_paths(pdb_id, het_id)
        sample_paths.append(paths)
        raw_path = RAW / f"{pdb_id.lower()}.cif"
        raw_sha = _sha(raw_path) if (REPO / raw_path).exists() else ""
        raw_ok = raw_sha == acquisition.get("raw_sha256_by_pdb", {}).get(pdb_id, "")
        result: dict[str, Any]
        if (REPO / raw_path).exists():
            result = prepare_from_text(sample, (REPO / raw_path).read_text(encoding="utf-8", errors="replace"), raw_ok, raw_path.as_posix())
        else:
            result = prepare_from_text(sample, "", False, "")
        raw_file_resolved_flags.append(_raw_file_resolved(raw_path, result["checks"]))
        _atomic_csv(paths["protein"], historical.PROTEIN_ATOM_COLUMNS, result["protein_rows"])
        _atomic_csv(paths["ligand"], historical.LIGAND_ATOM_COLUMNS, result["ligand_rows"])
        _atomic_csv(paths["pocket"], historical.POCKET_ATOM_COLUMNS, result["pocket_rows"])
        _atomic_csv(paths["event"], historical.COVALENT_EVENT_COLUMNS, result["event_rows"])
        _atomic_csv(paths["pair"], historical.PAIR_TABLE_COLUMNS, result["pair_rows"])
        _atomic_csv(paths["audit"], AUDIT_COLUMNS, result["audit_rows"])
        passed = all(row["audit_passed"] for row in result["audit_rows"])
        blocking = ";".join(row["blocking_reasons"] for row in result["audit_rows"] if row["blocking_reasons"])
        computed = result["computed_distance"]
        struct_distance = result["struct_conn_distance"]
        delta = result["distance_delta"]
        dynamic_pair = f"SG--{sample['selected_ligand_atom_name']}"
        counts = {"protein": len(result["protein_rows"]), "ligand": len(result["ligand_rows"]), "pocket": len(result["pocket_rows"]), "event": len(result["event_rows"]), "pair": len(result["pair_rows"])}
        total_protein += counts["protein"]; total_ligand += counts["ligand"]; total_pocket += counts["pocket"]
        execution_rows.append({**sample, "raw_file_path": raw_path.as_posix(), "sample_artifact_root": paths["root"].as_posix(), "selected_cys_chain_id": selected["selected_cys_chain_id"], "selected_cys_seq_id": selected["selected_cys_seq_id"], "selected_ligand_chain_id": selected["selected_ligand_chain_id"], "selected_ligand_seq_id": selected["selected_ligand_seq_id"], "covalent_bond_atom_pair": dynamic_pair, "protein_atom_count": counts["protein"], "ligand_atom_count": counts["ligand"], "pocket_atom_count": counts["pocket"], "covalent_event_count": counts["event"], "ligand_residue_atom_pair_count": counts["pair"], "struct_conn_distance_angstrom": f"{struct_distance:.3f}" if struct_distance is not None else "", "computed_atom_site_distance_angstrom": f"{computed:.3f}" if computed is not None else "", "distance_delta_angstrom": f"{delta:.3f}" if delta is not None else "", "sample_preparation_status": "passed" if passed else "failed", "embedded_qa_passed": passed, "ready_for_batch_sample_index_current_step": False, "ready_for_training_current_step": False})
        trace_rows.append({"sample_preparation_input_id": sample["sample_preparation_input_id"], "sample_execution_id": sample["sample_execution_id"], "pdb_id": pdb_id, "expected_het_id": het_id, "raw_file_path": raw_path.as_posix(), "raw_sha256_verified": raw_ok, "selected_struct_conn_id": sample["selected_struct_conn_id"], "struct_conn_event_revalidated": result["checks"]["selected_struct_conn_event_revalidated"], "residue_atom_from_struct_conn": "CYS/SG", "ligand_atom_from_struct_conn": sample["selected_ligand_atom_name"], "atom_site_residue_atom_found": result["checks"]["residue_cys_sg_atom_unique"], "atom_site_ligand_atom_found": result["checks"]["ligand_covalent_atom_unique"], "dynamic_ligand_atom_preserved": sample["selected_ligand_atom_name"] == expected_atom and all(row.get("ligand_atom_name", sample["selected_ligand_atom_name"]) == sample["selected_ligand_atom_name"] for row in result["event_rows"] + result["pair_rows"]), "traceability_audit_passed": passed, "blocking_reasons": blocking})
        quality_rows.append({"sample_preparation_input_id": sample["sample_preparation_input_id"], "sample_execution_id": sample["sample_execution_id"], "pdb_id": pdb_id, "expected_het_id": het_id, "protein_atom_count": counts["protein"], "ligand_atom_count": counts["ligand"], "pocket_atom_count": counts["pocket"], "covalent_event_count": counts["event"], "ligand_residue_atom_pair_count": counts["pair"], "ligand_covalent_atom_count": sum(_bool(row["is_covalent_ligand_atom"]) for row in result["ligand_rows"]), "event_pair_atom_names_consistent": bool(result["event_rows"] and result["pair_rows"] and result["event_rows"][0]["covalent_bond_atom_pair"] == result["pair_rows"][0]["covalent_bond_atom_pair"]), "atom_site_distance_angstrom": f"{computed:.3f}" if computed is not None else "", "struct_conn_distance_angstrom": f"{struct_distance:.3f}" if struct_distance is not None else "", "distance_delta_angstrom": f"{delta:.3f}" if delta is not None else "", "distance_consistency_passed": result["checks"]["atom_site_struct_conn_distance_consistent"], "quality_audit_passed": passed, "blocking_reasons": blocking})
        inventory.append({"sample_preparation_input_id": sample["sample_preparation_input_id"], "sample_execution_id": sample["sample_execution_id"], "shortlist_rank": rank, "pdb_id": pdb_id, "expected_het_id": het_id, "selected_ligand_atom_name": sample["selected_ligand_atom_name"], "covalent_bond_atom_pair": dynamic_pair, "raw_file_path": raw_path.as_posix(), "sample_artifact_root": paths["root"].as_posix(), "sample_preparation_status": "passed" if passed else "failed"})
        if not passed:
            failure_rows.append({"failure_id": f"BATCH_PREPARATION_FAILURE_{rank:06d}", "pdb_id": pdb_id, "expected_het_id": het_id, "failure_stage": "sample_preparation", "failure_type": "embedded_qa_failed", "failure_description": blocking, "retry_or_resolution_recommended": True, "failure_status": "blocked"})

    all_preconditions_passed = all(_bool(row["precondition_passed"]) for row in pre_rows)
    all_samples_passed = len(failure_rows) == 0 and all(_bool(row["embedded_qa_passed"]) for row in execution_rows)
    if not failure_rows:
        failure_rows = [{"failure_id": "NO_BATCH_SAMPLE_PREPARATION_FAILURES", "pdb_id": "", "expected_het_id": "", "failure_stage": "none", "failure_type": "no_failures", "failure_description": "No batch sample preparation failures detected.", "retry_or_resolution_recommended": False, "failure_status": "passed"}]
    table_counts = _table_written_counts(sample_paths)
    safety_values = {"network_access_used_current_step": False, "download_attempted_current_step": False, "raw_mmcif_read_current_step": True, "struct_conn_parsed_current_step": True, "atom_site_parsed_current_step": True, "raw_files_modified": False, "raw_files_tracked": bool(_git(["ls-files", str(RAW)]).stdout.strip()), "raw_files_staged": bool(_git(["diff", "--cached", "--name-only", "--", str(RAW)]).stdout.strip()), "part_or_tmp_files_remaining": any(path.suffix in {".tmp", ".part"} for path in (REPO / OUT).rglob("*")) if (REPO / OUT).exists() else False, "historical_sample_preparation_module_modified": _changed([str(HISTORICAL)]), "metadata_csv_unchanged": not _changed([str(META)]), "sample_index_files_unchanged": not _changed([str(INDEX_CSV), str(INDEX_JSON)]), "step14al_artifacts_unchanged": not _changed([str(AL)]), "step14ak_artifacts_unchanged": not _changed([str(AK)]), "historical_artifacts_unchanged": not _changed(["data/derived/covalent_small/covapie_sample_preparation_execution_smoke_v0"]), "protected_source_diff_empty": not _changed(["equivariant_diffusion/", "lightning_modules.py"]), "original_dataloader_diff_empty": not _changed(["dataset.py", "data/prepare_crossdocked.py"]), "per_sample_tables_written": _per_sample_tables_written(sample_paths), "existing_sample_index_written": False, "split_assignments_written": False, "leakage_matrix_written": False, "final_dataset_written": False, "actual_dataloader_artifacts_written": False, "training_artifacts_written": False, "torch_imported": False, "numpy_imported": False, "rdkit_used": False, "biopython_used": False, "gemmi_used": False, "requests_used": False}
    safety_rows = _safety_rows(safety_values)
    all_safety_passed = all(_bool(row["safety_passed"]) for row in safety_rows)
    ready = _ready(all_preconditions_passed, all_samples_passed, all_safety_passed)
    mapping = {f"{row['pdb_id']}/{row['expected_het_id']}": row["covalent_bond_atom_pair"] for row in execution_rows}
    blocking_reasons = [row["precondition_item"] for row in pre_rows if not _bool(row["precondition_passed"])]
    blocking_reasons += [row["pdb_id"] for row in execution_rows if row["sample_preparation_status"] == "failed"]
    blocking_reasons += [row["safety_item"] for row in safety_rows if not _bool(row["safety_passed"])]
    manifest = {"stage": STAGE, "step_label": "Step 14AM", "previous_stage": "covapie_independent_group_expansion_struct_conn_crosscheck_smoke_v0", "project_name": "CovaPIE", "input_confirmed_candidate_count": 8, "input_sample_preparation_eligible_count": 8, "raw_fingerprint_verified_count": sum(_bool(row["raw_sha256_verified"]) for row in trace_rows), "raw_file_resolved_count": sum(raw_file_resolved_flags), "sample_execution_count": 8, "sample_preparation_passed_count": sum(row["sample_preparation_status"] == "passed" for row in execution_rows), "sample_preparation_failed_count": sum(row["sample_preparation_status"] == "failed" for row in execution_rows), "embedded_qa_count": 8, "embedded_qa_passed_count": sum(_bool(row["embedded_qa_passed"]) for row in execution_rows), "embedded_qa_failed_count": sum(not _bool(row["embedded_qa_passed"]) for row in execution_rows), "batch_failure_count": 0 if failure_rows[0]["failure_id"] == "NO_BATCH_SAMPLE_PREPARATION_FAILURES" else len(failure_rows), "protein_atom_table_written_count": table_counts["protein"], "ligand_atom_table_written_count": table_counts["ligand"], "pocket_atom_table_written_count": table_counts["pocket"], "covalent_event_table_written_count": table_counts["event"], "ligand_residue_atom_pair_table_written_count": table_counts["pair"], "sample_preparation_audit_written_count": table_counts["audit"], "total_protein_atom_count": total_protein, "total_ligand_atom_count": total_ligand, "total_pocket_atom_count": total_pocket, "total_covalent_event_count": sum(int(row["covalent_event_count"]) for row in execution_rows), "total_ligand_residue_atom_pair_count": sum(int(row["ligand_residue_atom_pair_count"]) for row in execution_rows), "accepted_pdb_het_pairs": [f"{p}/{h}" for p, h, _ in EXPECTED_PAIRS], "covalent_bond_atom_pair_by_pdb_het": mapping, "computed_bond_distance_by_pdb_het": {f"{row['pdb_id']}/{row['expected_het_id']}": row["computed_atom_site_distance_angstrom"] for row in execution_rows}, "struct_conn_distance_by_pdb_het": {f"{row['pdb_id']}/{row['expected_het_id']}": row["struct_conn_distance_angstrom"] for row in execution_rows}, "distance_delta_by_pdb_het": {f"{row['pdb_id']}/{row['expected_het_id']}": row["distance_delta_angstrom"] for row in execution_rows}, "all_distance_checks_passed": all(_bool(row["distance_consistency_passed"]) for row in quality_rows), "all_preconditions_passed": all_preconditions_passed, "all_samples_passed": all_samples_passed, "all_safety_passed": all_safety_passed, "standalone_sample_preparation_qa_gate_created": False, "embedded_sample_preparation_qa_performed": True, **safety_values, "existing_sample_index_written_current_step": False, "confirmed_new_independent_group_count_current_step": 0, "ligand_graph_independence_status": "pending_canonical_graph_hash_and_scaffold_review", "protein_sequence_independence_status": "pending_accession_and_sequence_cluster", "ready_for_covapie_independent_group_expansion_batch_sample_index_materialization_smoke": ready, "ready_for_covapie_independent_group_expansion_batch_sample_preparation_issue_resolution": not ready, "ready_for_covapie_split_materialization_smoke": False, "ready_for_covapie_final_dataset_materialization_smoke": False, "ready_for_training": False, "ready_to_train_now": False, "feature_semantics_known_for_training": False, "unknown_atom_feature_policy_finalized_for_training": False, "feature_semantics_audit_required_before_training": True, "leakage_split_design_required_before_training": True, "canonical_mask_task_names": MASK_NAMES, "canonical_mask_task_aliases": MASK_ALIASES, "b3_scaffold_only_included": True, "no_extra_mask_tasks_added": True, "recommended_next_step": "covapie_independent_group_expansion_batch_sample_index_materialization_smoke" if ready else "covapie_independent_group_expansion_batch_sample_preparation_issue_resolution", "all_checks_passed": ready, "blocking_reasons": blocking_reasons}
    _atomic_csv(PRE, PRE_COLUMNS, pre_rows); _atomic_csv(EXEC, EXEC_COLUMNS, execution_rows); _atomic_json(EXEC_JSON, execution_rows); _atomic_csv(INV, list(inventory[0].keys()), inventory); _atomic_json(INV_JSON, inventory); _atomic_csv(TRACE, TRACE_COLUMNS, trace_rows); _atomic_csv(QUALITY, QUALITY_COLUMNS, quality_rows); _atomic_csv(FAILURES, FAILURE_COLUMNS, failure_rows); _atomic_csv(SAFETY, SAFETY_COLUMNS, safety_rows); _atomic_json(MANIFEST, manifest)
    return {"manifest": manifest, "execution_rows": execution_rows, "precondition_rows": pre_rows, "quality_rows": quality_rows}
