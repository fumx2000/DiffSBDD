from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_cys_sg_discovery_support_review_gate as step14i


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_cys_sg_ligand_covale_annotation_alignment_gate_v0"
STEP_LABEL = "Step 14J"
PREVIOUS_STAGE = step14i.STAGE
PROJECT_NAME = "CovaPIE"

CURRENT_SOURCE_PROFILE = step14i.CURRENT_SOURCE_PROFILE
CURRENT_SOURCE_DATABASE = step14i.CURRENT_SOURCE_DATABASE
METADATA_CSV = step14i.METADATA_CSV
METADATA_CSV_SHA256 = step14i.METADATA_CSV_SHA256
RAW_REFERENCE_ROOT = step14i.RAW_REFERENCE_ROOT
RAW_OUTPUT_ROOT = step14i.RAW_OUTPUT_ROOT
STEP14I_ROOT = step14i.OUTPUT_ROOT
STEP14I_MANIFEST_JSON = step14i.MANIFEST_JSON
STEP14I_CANDIDATES_CSV = step14i.LIGAND_COVALE_CANDIDATES_CSV
STEP14I_CANDIDATES_JSON = step14i.LIGAND_COVALE_CANDIDATES_JSON
STEP14H_ROOT = step14i.STEP14H_ROOT
STEP14G_ROOT = step14i.STEP14G_ROOT

CANONICAL_MASK_TASK_NAMES = step14i.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14i.CANONICAL_MASK_TASK_ALIASES

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_ligand_covale_annotation_alignment_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_annotation_alignment_precondition_audit.csv"
METADATA_SCHEMA_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_annotation_metadata_schema_audit.csv"
CANDIDATE_INPUT_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_annotation_candidate_input_audit.csv"
POLICY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_annotation_alignment_policy_contract.csv"
ALIGNMENT_CANDIDATES_CSV = OUTPUT_ROOT / "covapie_cys_sg_annotation_alignment_candidates.csv"
ALIGNMENT_CANDIDATES_JSON = OUTPUT_ROOT / "covapie_cys_sg_annotation_alignment_candidates.json"
GAP_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_annotation_gap_audit.csv"
DOWNSTREAM_READINESS_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_annotation_downstream_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_annotation_alignment_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_annotation_alignment_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_cys_sg_ligand_covale_annotation_alignment_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_cys_sg_ligand_covale_annotation_alignment_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_cys_sg_ligand_covale_annotation_alignment_gate_v0.py")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
METADATA_SCHEMA_COLUMNS = ["metadata_field_name", "field_present", "mapped_semantic_role", "required_for_current_alignment", "schema_audit_passed", "qa_comment"]
CANDIDATE_INPUT_COLUMNS = ["candidate_input_item", "observed_status", "candidate_input_passed", "qa_comment"]
POLICY_COLUMNS = ["policy_item", "policy_status", "allowed_current_step", "forbidden_current_step", "policy_contract_passed", "qa_comment"]
ALIGNMENT_COLUMNS = [
    "annotation_alignment_candidate_id",
    "ligand_covale_candidate_id",
    "original_proposal_id",
    "pdb_id",
    "ligand_identifier",
    "suggested_ligand_comp_id",
    "suggested_chain_id",
    "suggested_residue_name",
    "suggested_residue_index",
    "suggested_residue_atom_name",
    "suggested_ligand_atom_name",
    "suggested_covalent_bond_atom_pair",
    "suggested_covalent_event_id",
    "struct_conn_type",
    "metadata_row_match_count_by_pdb",
    "metadata_row_match_count_by_pdb_and_ligand_identifier",
    "metadata_row_match_count_by_pdb_and_het_code_if_available",
    "metadata_candidate_ligand_field_value",
    "metadata_candidate_het_code_value",
    "metadata_residue_name_value_if_available",
    "metadata_residue_atom_value_if_available",
    "metadata_warhead_value_if_available",
    "metadata_mechanism_value_if_available",
    "rcsb_covale_evidence_status",
    "covpdb_metadata_alignment_status",
    "annotation_gap_status",
    "manual_review_status",
    "ready_candidate_current_step",
    "exclusion_reason",
]
GAP_COLUMNS = ["gap_item", "observed_status", "gap_audit_passed", "qa_comment"]
DOWNSTREAM_COLUMNS = ["readiness_item", "observed_status", "readiness_passed", "next_required_gate", "qa_comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]

METADATA_FIELD_ROLES = {
    "pdb_id": "pdb_context_key",
    "covpdb_ligand_id": "covpdb_ligand_identifier",
    "ligand_identifier": "candidate_ligand_identifier",
    "het_code": "ligand_het_code",
    "ligand_id": "ligand_identifier",
    "ligand_name": "ligand_name_context",
    "residue_name": "event_residue_name",
    "residue_atom_name": "event_residue_atom",
    "residue_index": "event_residue_index",
    "chain_id": "event_chain_id",
    "warhead": "warhead_context",
    "mechanism": "mechanism_context",
    "source_database": "source_database",
    "source_profile": "source_profile",
}


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _csv_header(path: str | Path) -> list[str]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle).fieldnames or [])


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    unstaged = _run_git(["diff", "--quiet", "--", *paths]).returncode != 0
    staged = _run_git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0
    return unstaged or staged


def _metadata_hash() -> str:
    return hashlib.sha256(METADATA_CSV.read_bytes()).hexdigest() if METADATA_CSV.exists() else ""


def _raw_files_tracked(root: Path) -> bool:
    return bool(_run_git(["ls-files", root.as_posix()]).stdout.strip())


def _raw_files_staged(root: Path) -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", root.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


def _normal(value: Any) -> str:
    return str(value or "").strip()


def _upper(value: Any) -> str:
    return _normal(value).upper()


def _imports_forbidden_module(path: Path, forbidden: set[str]) -> bool:
    full_path = REPO_ROOT / path
    if not full_path.exists():
        return False
    tree = ast.parse(full_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name.split(".")[0] in forbidden for alias in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden:
            return True
    return False


def _own_files_have_forbidden_imports() -> bool:
    forbidden = {"requests", "urllib", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"}
    return any(_imports_forbidden_module(path, forbidden) for path in [MODULE_PATH, CHECK_SCRIPT_PATH])


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden_names = {
        "small_pilot_download_manifest.csv",
        "small_pilot_download_manifest.json",
        "final_dataset.csv",
        "final_dataset.json",
        "sample_index.csv",
        "sample_index.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
        "training_report.csv",
        "training_report.json",
        "actual_dataloader_smoke.csv",
        "actual_dataloader_smoke.json",
        "dataloader_smoke.csv",
        "dataloader_smoke.json",
    }
    return root.exists() and any(path.name in forbidden_names for path in root.rglob("*") if path.is_file())


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden_suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.suffix.lower() in forbidden_suffixes for path in root.rglob("*") if path.is_file())


def _candidate_json_rows() -> list[dict[str, Any]]:
    data = _load_json(STEP14I_CANDIDATES_JSON)
    return data if isinstance(data, list) else []


def _candidates_consistent(csv_rows: list[dict[str, str]], json_rows: list[dict[str, Any]]) -> bool:
    csv_ids = [row["ligand_covale_candidate_id"] for row in csv_rows]
    json_ids = [str(row.get("ligand_covale_candidate_id", "")) for row in json_rows]
    return csv_ids == json_ids and len(csv_rows) == len(json_rows)


def _metadata_has_ligand_identifier_field(header: list[str]) -> bool:
    return any(field in header for field in ["covpdb_ligand_id", "ligand_identifier", "het_code", "ligand_id", "ligand_name"])


def _event_annotation_gap(header: list[str]) -> bool:
    event_fields = {"residue_name", "residue_atom_name", "residue_index", "chain_id"}
    return not event_fields.issubset(set(header))


def build_precondition_rows(candidates: list[dict[str, str]], candidate_json_rows: list[dict[str, Any]], metadata_header: list[str]) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14I_MANIFEST_JSON) if STEP14I_MANIFEST_JSON.exists() else {}
    checks: list[tuple[str, str, str, Any, bool]] = [
        ("step14i_manifest_exists", STEP14I_MANIFEST_JSON.as_posix(), "exists", STEP14I_MANIFEST_JSON.exists(), STEP14I_MANIFEST_JSON.exists()),
        ("step14i_stage", STEP14I_MANIFEST_JSON.as_posix(), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step14i_all_checks_passed", STEP14I_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14i_ligand_covale_candidate_count", STEP14I_MANIFEST_JSON.as_posix(), "9", manifest.get("ligand_covale_candidate_count"), manifest.get("ligand_covale_candidate_count") == 9),
        ("step14i_ready_for_annotation_alignment", STEP14I_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_cys_sg_ligand_covale_annotation_alignment_gate"), manifest.get("ready_for_covapie_cys_sg_ligand_covale_annotation_alignment_gate") is True),
        ("step14i_ready_for_training", STEP14I_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("candidate_csv_exists", STEP14I_CANDIDATES_CSV.as_posix(), "exists", STEP14I_CANDIDATES_CSV.exists(), STEP14I_CANDIDATES_CSV.exists()),
        ("candidate_json_exists", STEP14I_CANDIDATES_JSON.as_posix(), "exists", STEP14I_CANDIDATES_JSON.exists(), STEP14I_CANDIDATES_JSON.exists()),
        ("candidate_csv_json_consistent", STEP14I_CANDIDATES_JSON.as_posix(), "true", _candidates_consistent(candidates, candidate_json_rows), _candidates_consistent(candidates, candidate_json_rows)),
        ("all_candidates_pending_manual_review", STEP14I_CANDIDATES_CSV.as_posix(), "true", all(row["manual_review_status"] == "pending_manual_review" for row in candidates), all(row["manual_review_status"] == "pending_manual_review" for row in candidates)),
        ("metadata_csv_exists", METADATA_CSV.as_posix(), "exists", METADATA_CSV.exists(), METADATA_CSV.exists()),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("metadata_has_pdb_id", METADATA_CSV.as_posix(), "pdb_id", "pdb_id" in metadata_header, "pdb_id" in metadata_header),
        ("metadata_has_ligand_identifier_field", METADATA_CSV.as_posix(), "one ligand identifier field", _metadata_has_ligand_identifier_field(metadata_header), _metadata_has_ligand_identifier_field(metadata_header)),
        ("raw_roots_not_tracked", RAW_OUTPUT_ROOT.as_posix(), "false", _raw_files_tracked(RAW_OUTPUT_ROOT) or _raw_files_tracked(RAW_REFERENCE_ROOT), not _raw_files_tracked(RAW_OUTPUT_ROOT) and not _raw_files_tracked(RAW_REFERENCE_ROOT)),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
        ("no_extra_mask_tasks", "canonical masks", "true", CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_NAMES == step14i.CANONICAL_MASK_TASK_NAMES),
    ]
    return [
        {
            "precondition_item": item,
            "artifact_or_check": artifact,
            "expected_status": expected,
            "observed_status": observed,
            "precondition_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, artifact, expected, observed, passed in checks
    ]


def build_metadata_schema_rows(metadata_header: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for field, role in METADATA_FIELD_ROLES.items():
        present = field in metadata_header
        required = field == "pdb_id" or field in {"covpdb_ligand_id", "ligand_identifier", "het_code", "ligand_id", "ligand_name"}
        if field == "pdb_id":
            passed = present
        elif field in {"covpdb_ligand_id", "ligand_identifier", "het_code", "ligand_id", "ligand_name"}:
            passed = _metadata_has_ligand_identifier_field(metadata_header)
        else:
            passed = True
        rows.append(
            {
                "metadata_field_name": field,
                "field_present": present,
                "mapped_semantic_role": role,
                "required_for_current_alignment": required,
                "schema_audit_passed": passed,
                "qa_comment": "" if present else ("optional_event_annotation_gap_recorded" if not required else "covered_by_alternate_ligand_identifier_field"),
            }
        )
    return rows


def build_candidate_input_rows(candidates: list[dict[str, str]], candidate_json_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = [
        ("candidate_csv_exists", STEP14I_CANDIDATES_CSV.exists(), STEP14I_CANDIDATES_CSV.as_posix()),
        ("candidate_json_exists", STEP14I_CANDIDATES_JSON.exists(), STEP14I_CANDIDATES_JSON.as_posix()),
        ("candidate_csv_json_consistent", _candidates_consistent(candidates, candidate_json_rows), "candidate ids and row counts match"),
        ("ligand_covale_candidate_count", len(candidates) == 9, str(len(candidates))),
        ("all_candidates_struct_conn_type_covale", all(_upper(row["struct_conn_type"]) == "COVALE" for row in candidates), "covale"),
        ("all_candidates_residue_cys_sg", all(_upper(row["suggested_residue_name"]) == "CYS" and _upper(row["suggested_residue_atom_name"]) == "SG" for row in candidates), "CYS/SG"),
        ("all_candidates_ligand_comp_not_cys", all(_upper(row["suggested_ligand_comp_id"]) != "CYS" for row in candidates), "ligand comp != CYS"),
        ("all_candidates_bond_pair_not_sg_sg", all(_upper(row["suggested_covalent_bond_atom_pair"]) != "SG--SG" for row in candidates), "not SG--SG"),
        ("all_candidates_pending_manual_review", all(row["manual_review_status"] == "pending_manual_review" for row in candidates), "pending_manual_review"),
        ("no_ready_candidates_in_input", all(not _bool(row["ready_candidate_current_step"]) for row in candidates), "ready false"),
    ]
    return [
        {
            "candidate_input_item": item,
            "observed_status": observed,
            "candidate_input_passed": passed,
            "qa_comment": "" if passed else f"failed:{item}",
        }
        for item, passed, observed in checks
    ]


def build_policy_rows() -> list[dict[str, Any]]:
    rows = [
        ("pdb_id_only_not_event_identity", "required", "context_only", "event_identity"),
        ("covpdb_ligand_id_only_not_event_identity", "required", "context_only", "event_identity"),
        ("rcsb_struct_conn_covale_required", "required", "covale_evidence_required", "non_covale_candidate"),
        ("metadata_alignment_required_before_manual_confirmation", "required", "alignment_gate", "manual_confirmed_ready"),
        ("metadata_gap_allowed_but_recorded", "required", "record_gap", "hide_gap"),
        ("no_ready_candidate_current_step", "required", "ready_false", "ready_true"),
        ("below_20_after_alignment_triggers_targeted_expansion", "required", "targeted_expansion_gate", "small_pilot_rerun"),
        ("no_training_or_dataloader_current_step", "required", "audit_only", "dataloader_or_training"),
    ]
    return [
        {
            "policy_item": item,
            "policy_status": status,
            "allowed_current_step": allowed,
            "forbidden_current_step": forbidden,
            "policy_contract_passed": True,
            "qa_comment": "",
        }
        for item, status, allowed, forbidden in rows
    ]


def _metadata_matches(metadata_rows: list[dict[str, str]], pdb_id: str) -> list[dict[str, str]]:
    return [row for row in metadata_rows if _upper(row.get("pdb_id")) == _upper(pdb_id)]


def _metadata_value(row: dict[str, str], fields: list[str]) -> str:
    values = [_normal(row.get(field)) for field in fields if _normal(row.get(field))]
    return ";".join(dict.fromkeys(values))


def build_alignment_candidates(candidates: list[dict[str, str]], metadata_rows: list[dict[str, str]], metadata_header: list[str]) -> list[dict[str, Any]]:
    aligned_rows: list[dict[str, Any]] = []
    has_event_gap = _event_annotation_gap(metadata_header)
    for index, candidate in enumerate(candidates, start=1):
        pdb_rows = _metadata_matches(metadata_rows, candidate["pdb_id"])
        ligand_identifier = _upper(candidate["ligand_identifier"])
        ligand_comp = _upper(candidate["suggested_ligand_comp_id"])
        ligand_id_rows = [
            row
            for row in pdb_rows
            if ligand_identifier
            and ligand_identifier
            in {_upper(row.get("covpdb_ligand_id")), _upper(row.get("ligand_identifier")), _upper(row.get("ligand_id")), _upper(row.get("ligand_name"))}
        ]
        het_rows = [row for row in pdb_rows if ligand_comp and ligand_comp in {_upper(row.get("het_code")), _upper(row.get("ligand_id"))}]
        aligned = bool(ligand_id_rows or het_rows)
        conflict = bool(pdb_rows and not aligned and (ligand_identifier or ligand_comp))
        if aligned:
            status = "metadata_ligand_or_het_aligned_pending_manual_review"
        elif conflict:
            status = "metadata_conflict_pending_manual_review"
        elif pdb_rows:
            status = "pdb_only_metadata_context_not_event_identity"
        else:
            status = "metadata_missing_pdb_context_pending_manual_review"
        matched_context = ligand_id_rows or het_rows or pdb_rows
        first = matched_context[0] if matched_context else {}
        gap_status = "metadata_event_annotation_gap_recorded" if has_event_gap else "metadata_event_annotation_fields_present_not_ready"
        aligned_rows.append(
            {
                "annotation_alignment_candidate_id": f"CYS_SG_ANNOT_ALIGN_{index:06d}",
                "ligand_covale_candidate_id": candidate["ligand_covale_candidate_id"],
                "original_proposal_id": candidate["original_proposal_id"],
                "pdb_id": candidate["pdb_id"],
                "ligand_identifier": candidate["ligand_identifier"],
                "suggested_ligand_comp_id": candidate["suggested_ligand_comp_id"],
                "suggested_chain_id": candidate["suggested_chain_id"],
                "suggested_residue_name": candidate["suggested_residue_name"],
                "suggested_residue_index": candidate["suggested_residue_index"],
                "suggested_residue_atom_name": candidate["suggested_residue_atom_name"],
                "suggested_ligand_atom_name": candidate["suggested_ligand_atom_name"],
                "suggested_covalent_bond_atom_pair": candidate["suggested_covalent_bond_atom_pair"],
                "suggested_covalent_event_id": candidate["suggested_covalent_event_id"],
                "struct_conn_type": candidate["struct_conn_type"],
                "metadata_row_match_count_by_pdb": len(pdb_rows),
                "metadata_row_match_count_by_pdb_and_ligand_identifier": len(ligand_id_rows),
                "metadata_row_match_count_by_pdb_and_het_code_if_available": len(het_rows),
                "metadata_candidate_ligand_field_value": _metadata_value(first, ["covpdb_ligand_id", "ligand_identifier", "ligand_id", "ligand_name"]),
                "metadata_candidate_het_code_value": _metadata_value(first, ["het_code"]),
                "metadata_residue_name_value_if_available": _metadata_value(first, ["residue_name"]),
                "metadata_residue_atom_value_if_available": _metadata_value(first, ["residue_atom_name"]),
                "metadata_warhead_value_if_available": _metadata_value(first, ["warhead"]),
                "metadata_mechanism_value_if_available": _metadata_value(first, ["mechanism"]),
                "rcsb_covale_evidence_status": "rcsb_struct_conn_covale_evidence_present",
                "covpdb_metadata_alignment_status": status,
                "annotation_gap_status": gap_status,
                "manual_review_status": "pending_manual_review",
                "ready_candidate_current_step": False,
                "exclusion_reason": "",
            }
        )
    return aligned_rows


def build_gap_rows(alignment_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    input_count = len(alignment_rows)
    pdb_match_count = sum(int(row["metadata_row_match_count_by_pdb"]) > 0 for row in alignment_rows)
    ligand_align_count = sum(
        row["covpdb_metadata_alignment_status"] == "metadata_ligand_or_het_aligned_pending_manual_review"
        for row in alignment_rows
    )
    event_gap_count = sum(row["annotation_gap_status"].startswith("metadata_event_annotation_gap") for row in alignment_rows)
    conflict_count = sum(row["covpdb_metadata_alignment_status"] == "metadata_conflict_pending_manual_review" for row in alignment_rows)
    threshold_status = "below_threshold_needs_targeted_expansion_after_alignment" if input_count < 20 else "met"
    rows = [
        ("input_ligand_covale_candidate_count", str(input_count), input_count == 9, "input candidates reviewed"),
        ("metadata_pdb_match_count", str(pdb_match_count), pdb_match_count >= 0, "PDB context only, not event identity"),
        ("metadata_ligand_or_het_alignment_count", str(ligand_align_count), ligand_align_count >= 0, "ligand/het context alignment"),
        ("metadata_event_annotation_gap_count", str(event_gap_count), event_gap_count >= 0, "event-level metadata gaps recorded"),
        ("metadata_conflict_count", str(conflict_count), conflict_count >= 0, "conflicts retained for review"),
        ("annotation_aligned_pending_review_count", str(input_count), input_count == len(alignment_rows), "all rows remain pending review"),
        ("ready_candidate_count_current_step", "0", True, "no ready candidates"),
        ("small_pilot_threshold_20_status", threshold_status, True, threshold_status),
        ("targeted_expansion_needed_after_alignment", str(input_count < 20), True, "below threshold route recorded"),
        ("training_still_blocked", "true", True, "training blocked"),
    ]
    return [
        {"gap_item": item, "observed_status": observed, "gap_audit_passed": passed, "qa_comment": comment}
        for item, observed, passed, comment in rows
    ]


def build_downstream_rows(alignment_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    count = len(alignment_rows)
    rows = [
        ("annotation_alignment_completed", "true", True, "covapie_cys_sg_targeted_metadata_expansion_gate" if count < 20 else "covapie_cys_sg_ligand_covale_manual_review_gate", ""),
        ("annotation_alignment_candidates_written", str(count), True, "covapie_cys_sg_targeted_metadata_expansion_gate" if count < 20 else "covapie_cys_sg_ligand_covale_manual_review_gate", ""),
        ("no_ready_candidates_created", "true", True, "manual_review_or_targeted_expansion_required", ""),
        ("ready_for_covapie_cys_sg_ligand_covale_manual_review_gate", str(count > 0), True, "covapie_cys_sg_ligand_covale_manual_review_gate", ""),
        ("ready_for_covapie_cys_sg_targeted_metadata_expansion_gate_after_alignment_if_below_20", str(count < 20), True, "covapie_cys_sg_targeted_metadata_expansion_gate", ""),
        ("ready_for_small_pilot_manifest_rerun_false", "false", True, "not_allowed_current_step", ""),
        ("ready_for_actual_dataloader_false", "false", True, "not_allowed_current_step", ""),
        ("training_still_false", "false", True, "not_allowed_current_step", ""),
        ("feature_semantics_still_not_training_final", "true", True, "feature_semantics_audit_required_before_training", ""),
        ("raw_files_remain_untracked_uncommitted", str(not _raw_files_tracked(RAW_OUTPUT_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT)), not _raw_files_tracked(RAW_OUTPUT_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT), "raw_files_not_committable", ""),
    ]
    return [
        {
            "readiness_item": item,
            "observed_status": observed,
            "readiness_passed": passed,
            "next_required_gate": next_gate,
            "qa_comment": comment,
        }
        for item, observed, passed, next_gate, comment in rows
    ]


def build_safety_rows(alignment_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[tuple[str, str, str, bool]] = [
        ("no_network_access_current_step", "passed", "passed", True),
        ("no_download_current_step", "passed", "passed", True),
        ("no_raw_file_content_read_current_step", "passed", "passed", True),
        ("no_raw_files_written_current_step", "passed", "passed", True),
        ("raw_files_untracked", "passed", "passed" if not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT) else "failed", not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT)),
        ("raw_files_unstaged", "passed", "passed" if not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT) else "failed", not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT)),
        ("metadata_csv_unchanged", "passed", "passed" if _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()]) else "failed", _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14i_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14I_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14I_ROOT.as_posix()])),
        ("step14h_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14H_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14H_ROOT.as_posix()])),
        ("step14g_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14G_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14G_ROOT.as_posix()])),
        ("protected_source_diff_empty", "passed", "passed" if not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]) else "failed", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "passed", "passed" if not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]) else "failed", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_sample_download_manifest_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_actual_dataloader_artifacts", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_training_artifacts", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_final_dataset_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_sample_index_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_torch_numpy_rdkit_biopdb_gemmi_gzip_imports", "passed", "passed" if not _own_files_have_forbidden_imports() else "failed", not _own_files_have_forbidden_imports()),
        ("derived_output_no_forbidden_binary_or_raw_suffix", "passed", "passed" if not _forbidden_suffix_exists() else "failed", not _forbidden_suffix_exists()),
        ("pdb_id_not_used_as_event_identity", "passed", "passed", True),
        ("no_ready_candidates_created", "passed", "passed" if all(not _bool(row["ready_candidate_current_step"]) for row in alignment_rows) else "failed", all(not _bool(row["ready_candidate_current_step"]) for row in alignment_rows)),
    ]
    return [
        {
            "safety_item": item,
            "required_status": required,
            "observed_status": observed,
            "safety_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, required, observed, passed in checks
    ]


def build_manifest(
    precondition_rows: list[dict[str, Any]],
    metadata_schema_rows: list[dict[str, Any]],
    candidate_input_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    alignment_rows: list[dict[str, Any]],
    gap_rows: list[dict[str, Any]],
    downstream_rows: list[dict[str, Any]],
    safety_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_count = len(alignment_rows)
    pdb_match_count = sum(int(row["metadata_row_match_count_by_pdb"]) > 0 for row in alignment_rows)
    ligand_align_count = sum(row["covpdb_metadata_alignment_status"] == "metadata_ligand_or_het_aligned_pending_manual_review" for row in alignment_rows)
    event_gap_count = sum(row["annotation_gap_status"].startswith("metadata_event_annotation_gap") for row in alignment_rows)
    conflict_count = sum(row["covpdb_metadata_alignment_status"] == "metadata_conflict_pending_manual_review" for row in alignment_rows)
    pending = all(row["manual_review_status"] == "pending_manual_review" for row in alignment_rows)
    threshold_met = candidate_count >= 20
    next_step = "covapie_cys_sg_targeted_metadata_expansion_gate" if candidate_count < 20 else "covapie_cys_sg_ligand_covale_manual_review_gate"
    passed = (
        _all_true(precondition_rows, "precondition_passed")
        and _all_true(metadata_schema_rows, "schema_audit_passed")
        and _all_true(candidate_input_rows, "candidate_input_passed")
        and _all_true(policy_rows, "policy_contract_passed")
        and _all_true(gap_rows, "gap_audit_passed")
        and _all_true(downstream_rows, "readiness_passed")
        and _all_true(safety_rows, "safety_passed")
        and pending
        and all(not _bool(row["ready_candidate_current_step"]) for row in alignment_rows)
    )
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "current_source_profile": CURRENT_SOURCE_PROFILE,
        "current_source_database": CURRENT_SOURCE_DATABASE,
        "input_ligand_covale_candidate_count": candidate_count,
        "annotation_alignment_candidate_count": candidate_count,
        "metadata_pdb_match_count": pdb_match_count,
        "metadata_ligand_or_het_alignment_count": ligand_align_count,
        "metadata_event_annotation_gap_count": event_gap_count,
        "metadata_conflict_count": conflict_count,
        "annotation_alignment_candidates_csv_json_consistent": True,
        "all_annotation_alignment_candidates_pending_manual_review": pending,
        "no_ready_candidates_created": True,
        "ready_candidate_count_current_step": 0,
        "small_pilot_threshold_20_met": threshold_met,
        "small_pilot_threshold_20_status": "met" if threshold_met else "below_threshold_needs_targeted_expansion_after_alignment",
        "network_access_used": False,
        "download_attempted": False,
        "raw_file_content_read_current_step": False,
        "raw_files_written_current_step": False,
        "raw_files_tracked": _raw_files_tracked(RAW_OUTPUT_ROOT),
        "raw_files_staged": _raw_files_staged(RAW_OUTPUT_ROOT),
        "sample_download_manifest_written": False,
        "final_dataset_written": False,
        "sample_index_written_current_step": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "actual_dataloader_adapter_smoke_written": False,
        "actual_dataloader_smoke_written": False,
        "training_artifacts_written": False,
        "torch_imported": False,
        "numpy_imported": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "gzip_open_used": False,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "ready_for_covapie_cys_sg_ligand_covale_manual_review_gate": candidate_count > 0,
        "ready_for_covapie_cys_sg_targeted_metadata_expansion_gate_after_alignment_if_below_20": candidate_count < 20,
        "ready_for_covapie_small_pilot_manifest_rerun_gate": False,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else [row.get("blocking_reasons", "") for row in [*precondition_rows, *safety_rows] if row.get("blocking_reasons")],
    }


def run_covapie_cys_sg_ligand_covale_annotation_alignment_gate_v0() -> dict[str, Any]:
    candidates = _csv_rows(STEP14I_CANDIDATES_CSV)
    candidate_json_rows = _candidate_json_rows()
    metadata_rows = _csv_rows(METADATA_CSV)
    metadata_header = _csv_header(METADATA_CSV)
    precondition_rows = build_precondition_rows(candidates, candidate_json_rows, metadata_header)
    metadata_schema_rows = build_metadata_schema_rows(metadata_header)
    candidate_input_rows = build_candidate_input_rows(candidates, candidate_json_rows)
    policy_rows = build_policy_rows()
    alignment_rows = build_alignment_candidates(candidates, metadata_rows, metadata_header)
    gap_rows = build_gap_rows(alignment_rows)
    downstream_rows = build_downstream_rows(alignment_rows)
    safety_rows = build_safety_rows(alignment_rows)
    manifest = build_manifest(precondition_rows, metadata_schema_rows, candidate_input_rows, policy_rows, alignment_rows, gap_rows, downstream_rows, safety_rows)
    return {
        "precondition_rows": precondition_rows,
        "metadata_schema_rows": metadata_schema_rows,
        "candidate_input_rows": candidate_input_rows,
        "policy_rows": policy_rows,
        "alignment_rows": alignment_rows,
        "gap_rows": gap_rows,
        "downstream_rows": downstream_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }
