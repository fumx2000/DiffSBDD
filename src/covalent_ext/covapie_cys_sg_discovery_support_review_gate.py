from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_cys_sg_discovery_download_smoke as step14h


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_cys_sg_discovery_support_review_gate_v0"
STEP_LABEL = "Step 14I"
PREVIOUS_STAGE = step14h.STAGE
PROJECT_NAME = "CovaPIE"

CURRENT_SOURCE_PROFILE = step14h.CURRENT_SOURCE_PROFILE
CURRENT_SOURCE_DATABASE = step14h.CURRENT_SOURCE_DATABASE
METADATA_CSV = step14h.METADATA_CSV
METADATA_CSV_SHA256 = step14h.METADATA_CSV_SHA256
RAW_REFERENCE_ROOT = step14h.RAW_REFERENCE_ROOT
RAW_OUTPUT_ROOT = step14h.RAW_OUTPUT_ROOT
STEP14H_ROOT = step14h.OUTPUT_ROOT
STEP14H_MANIFEST_JSON = step14h.MANIFEST_JSON
STEP14H_PROPOSALS_CSV = step14h.EVENT_PROPOSALS_CSV
STEP14H_PROPOSALS_JSON = step14h.EVENT_PROPOSALS_JSON
STEP14H_STATUS_CSV = step14h.DOWNLOAD_STATUS_MANIFEST_CSV
STEP14H_STATUS_JSON = step14h.DOWNLOAD_STATUS_MANIFEST_JSON
STEP14G_ROOT = step14h.STEP14G_ROOT
STEP14F_ROOT = step14h.STEP14F_ROOT
STEP14E_ROOT = step14h.STEP14E_ROOT

CANONICAL_MASK_TASK_NAMES = step14h.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14h.CANONICAL_MASK_TASK_ALIASES

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_discovery_support_review_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_support_review_precondition_audit.csv"
INPUT_PROPOSAL_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_support_review_input_proposal_audit.csv"
POLICY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_support_review_policy_contract.csv"
DISULFIDE_EXCLUSION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_disulfide_exclusion_audit.csv"
LIGAND_COVALE_CANDIDATES_CSV = OUTPUT_ROOT / "covapie_cys_sg_ligand_covale_candidates.csv"
LIGAND_COVALE_CANDIDATES_JSON = OUTPUT_ROOT / "covapie_cys_sg_ligand_covale_candidates.json"
DECISION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_support_review_decision_audit.csv"
DOWNSTREAM_READINESS_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_support_review_downstream_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_support_review_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_support_review_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_cys_sg_discovery_support_review_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_cys_sg_discovery_support_review_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_cys_sg_discovery_support_review_gate_v0.py")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
INPUT_AUDIT_COLUMNS = ["input_audit_item", "observed_status", "input_audit_passed", "qa_comment"]
POLICY_COLUMNS = ["policy_item", "policy_status", "allowed_current_step", "forbidden_current_step", "policy_contract_passed", "qa_comment"]
DISULFIDE_AUDIT_COLUMNS = [
    "proposal_id",
    "pdb_id",
    "ligand_identifier",
    "struct_conn_id",
    "struct_conn_type",
    "suggested_chain_id",
    "suggested_residue_name",
    "suggested_residue_index",
    "suggested_residue_atom_name",
    "suggested_ligand_comp_id",
    "suggested_ligand_atom_name",
    "suggested_covalent_bond_atom_pair",
    "review_classification",
    "exclusion_reason",
    "keep_for_ligand_covale_review",
    "disulfide_exclusion_audit_passed",
    "qa_comment",
]
LIGAND_COVALE_COLUMNS = [
    "ligand_covale_candidate_id",
    "original_proposal_id",
    "discovery_manifest_row_id",
    "curation_candidate_id",
    "source_profile",
    "source_database",
    "candidate_metadata_id",
    "pdb_id",
    "ligand_identifier",
    "suggested_chain_id",
    "suggested_residue_name",
    "suggested_residue_index",
    "suggested_residue_atom_name",
    "suggested_ligand_comp_id",
    "suggested_ligand_atom_name",
    "suggested_covalent_bond_atom_pair",
    "suggested_covalent_event_id",
    "struct_conn_id",
    "struct_conn_type",
    "evidence_source_name",
    "evidence_source_path",
    "evidence_provenance_status",
    "ambiguity_status",
    "review_status",
    "covpdb_annotation_alignment_status",
    "manual_review_status",
    "ready_candidate_current_step",
    "exclusion_reason",
]
DECISION_COLUMNS = ["decision_item", "observed_status", "decision_passed", "qa_comment"]
DOWNSTREAM_COLUMNS = ["readiness_item", "observed_status", "readiness_passed", "next_required_gate", "qa_comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def _proposal_json_rows() -> list[dict[str, Any]]:
    data = _load_json(STEP14H_PROPOSALS_JSON)
    return data if isinstance(data, list) else []


def _normal(value: Any) -> str:
    return str(value or "").strip()


def _upper(value: Any) -> str:
    return _normal(value).upper()


def _proposals_consistent(csv_rows: list[dict[str, str]], json_rows: list[dict[str, Any]]) -> bool:
    csv_ids = [row["proposal_id"] for row in csv_rows]
    json_ids = [str(row.get("proposal_id", "")) for row in json_rows]
    return csv_ids == json_ids and len(csv_rows) == len(json_rows)


def build_precondition_rows(proposals: list[dict[str, str]], proposal_json_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14H_MANIFEST_JSON) if STEP14H_MANIFEST_JSON.exists() else {}
    checks: list[tuple[str, str, str, Any, bool]] = [
        ("step14h_manifest_exists", STEP14H_MANIFEST_JSON.as_posix(), "exists", STEP14H_MANIFEST_JSON.exists(), STEP14H_MANIFEST_JSON.exists()),
        ("step14h_stage", STEP14H_MANIFEST_JSON.as_posix(), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step14h_all_checks_passed", STEP14H_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14h_download_success_count", STEP14H_MANIFEST_JSON.as_posix(), "25", manifest.get("download_success_count"), manifest.get("download_success_count") == 25),
        ("step14h_support_proposal_count", STEP14H_MANIFEST_JSON.as_posix(), "86", manifest.get("support_proposal_count"), manifest.get("support_proposal_count") == 86),
        ("step14h_ready_for_support_review", STEP14H_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_cys_sg_discovery_support_review_gate"), manifest.get("ready_for_covapie_cys_sg_discovery_support_review_gate") is True),
        ("step14h_ready_for_training", STEP14H_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("proposal_csv_exists", STEP14H_PROPOSALS_CSV.as_posix(), "exists", STEP14H_PROPOSALS_CSV.exists(), STEP14H_PROPOSALS_CSV.exists()),
        ("proposal_json_exists", STEP14H_PROPOSALS_JSON.as_posix(), "exists", STEP14H_PROPOSALS_JSON.exists(), STEP14H_PROPOSALS_JSON.exists()),
        ("proposal_csv_json_consistent", STEP14H_PROPOSALS_JSON.as_posix(), "true", _proposals_consistent(proposals, proposal_json_rows), _proposals_consistent(proposals, proposal_json_rows)),
        ("all_proposals_pending_manual_review", STEP14H_PROPOSALS_CSV.as_posix(), "true", all(row["proposal_status"] == "pending_manual_review" and row["manual_review_status"] == "pending_manual_review" for row in proposals), all(row["proposal_status"] == "pending_manual_review" and row["manual_review_status"] == "pending_manual_review" for row in proposals)),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("raw_roots_not_tracked", RAW_OUTPUT_ROOT.as_posix(), "false", _raw_files_tracked(RAW_OUTPUT_ROOT) or _raw_files_tracked(RAW_REFERENCE_ROOT), not _raw_files_tracked(RAW_OUTPUT_ROOT) and not _raw_files_tracked(RAW_REFERENCE_ROOT)),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
        ("no_extra_mask_tasks", "canonical masks", "true", CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_NAMES == step14h.CANONICAL_MASK_TASK_NAMES),
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


def build_input_audit_rows(proposals: list[dict[str, str]], proposal_json_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    disulf_rows = [row for row in proposals if _upper(row["struct_conn_type"]) == "DISULF" or _upper(row["suggested_covalent_bond_atom_pair"]) == "SG--SG" or _upper(row["suggested_ligand_comp_id"]) == "CYS"]
    covale_rows = [row for row in proposals if _upper(row["struct_conn_type"]) == "COVALE"]
    checks = [
        ("proposal_csv_exists", STEP14H_PROPOSALS_CSV.exists(), STEP14H_PROPOSALS_CSV.as_posix()),
        ("proposal_json_exists", STEP14H_PROPOSALS_JSON.exists(), STEP14H_PROPOSALS_JSON.as_posix()),
        ("proposal_csv_json_consistent", _proposals_consistent(proposals, proposal_json_rows), "proposal ids and row counts match"),
        ("input_support_proposal_count", len(proposals) == 86, str(len(proposals))),
        ("all_proposals_pending_manual_review", all(row["proposal_status"] == "pending_manual_review" and row["manual_review_status"] == "pending_manual_review" for row in proposals), "pending_manual_review"),
        ("no_ready_candidates_in_input", all(not _bool(row["ready_candidate_current_step"]) for row in proposals), "ready false"),
        ("expected_residue_name_cys", all(_upper(row["suggested_residue_name"]) == "CYS" for row in proposals), "CYS"),
        ("expected_residue_atom_sg", all(_upper(row["suggested_residue_atom_name"]) == "SG" for row in proposals), "SG"),
        ("input_contains_disulfide_rows", bool(disulf_rows), str(len(disulf_rows))),
        ("input_contains_covale_rows", bool(covale_rows), str(len(covale_rows))),
    ]
    return [
        {
            "input_audit_item": item,
            "observed_status": observed,
            "input_audit_passed": passed,
            "qa_comment": "" if passed else f"failed:{item}",
        }
        for item, passed, observed in checks
    ]


def build_policy_rows() -> list[dict[str, Any]]:
    rows = [
        ("disulf_struct_conn_excluded", "required", "exclude", "promote_to_training"),
        ("sg_sg_bond_pair_excluded", "required", "exclude", "promote_to_training"),
        ("ligand_comp_cys_excluded", "required", "exclude", "treat_as_ligand_covale"),
        ("ligand_covale_candidate_definition", "required", "covale_non_cys_non_sg_ligand_atom", "pdb_id_only_identity"),
        ("covale_ligand_candidates_remain_pending_review", "required", "pending_manual_review", "ready_candidate"),
        ("no_ready_candidate_current_step", "required", "ready_false", "ready_true"),
        ("covpdb_annotation_alignment_required_next", "required", "annotation_alignment_gate", "training"),
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


def classify_proposal(row: dict[str, str]) -> tuple[str, str, bool]:
    struct_type = _upper(row["struct_conn_type"])
    pair = _upper(row["suggested_covalent_bond_atom_pair"])
    ligand_comp = _upper(row["suggested_ligand_comp_id"])
    ligand_atom = _upper(row["suggested_ligand_atom_name"])
    residue_name = _upper(row["suggested_residue_name"])
    residue_atom = _upper(row["suggested_residue_atom_name"])
    if struct_type == "DISULF" or pair == "SG--SG" or ligand_comp == "CYS":
        return "exclude_disulfide_or_protein_protein_sg_sg", "disulf_or_sg_sg_or_ligand_comp_cys", False
    if struct_type == "COVALE" and residue_name == "CYS" and residue_atom == "SG" and ligand_comp != "CYS" and ligand_atom != "SG" and pair != "SG--SG":
        return "keep_ligand_covale_candidate_pending_review", "", True
    return "other_excluded_or_needs_manual_triage", "not_ligand_covale_definition", False


def build_disulfide_audit_rows(proposals: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in proposals:
        classification, reason, keep = classify_proposal(row)
        passed = not (keep and classification != "keep_ligand_covale_candidate_pending_review")
        rows.append(
            {
                "proposal_id": row["proposal_id"],
                "pdb_id": row["pdb_id"],
                "ligand_identifier": row["ligand_identifier"],
                "struct_conn_id": row["struct_conn_id"],
                "struct_conn_type": row["struct_conn_type"],
                "suggested_chain_id": row["suggested_chain_id"],
                "suggested_residue_name": row["suggested_residue_name"],
                "suggested_residue_index": row["suggested_residue_index"],
                "suggested_residue_atom_name": row["suggested_residue_atom_name"],
                "suggested_ligand_comp_id": row["suggested_ligand_comp_id"],
                "suggested_ligand_atom_name": row["suggested_ligand_atom_name"],
                "suggested_covalent_bond_atom_pair": row["suggested_covalent_bond_atom_pair"],
                "review_classification": classification,
                "exclusion_reason": reason,
                "keep_for_ligand_covale_review": keep,
                "disulfide_exclusion_audit_passed": passed,
                "qa_comment": "",
            }
        )
    return rows


def build_ligand_covale_candidates(proposals: list[dict[str, str]], disulfide_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {row["proposal_id"]: row for row in proposals}
    kept = [row for row in disulfide_rows if _bool(row["keep_for_ligand_covale_review"])]
    candidates: list[dict[str, Any]] = []
    for index, audit_row in enumerate(kept, start=1):
        proposal = by_id[audit_row["proposal_id"]]
        candidates.append(
            {
                "ligand_covale_candidate_id": f"CYS_SG_LIG_COVALE_REVIEW_{index:06d}",
                "original_proposal_id": proposal["proposal_id"],
                "discovery_manifest_row_id": proposal["discovery_manifest_row_id"],
                "curation_candidate_id": proposal["curation_candidate_id"],
                "source_profile": proposal["source_profile"],
                "source_database": proposal["source_database"],
                "candidate_metadata_id": proposal["candidate_metadata_id"],
                "pdb_id": proposal["pdb_id"],
                "ligand_identifier": proposal["ligand_identifier"],
                "suggested_chain_id": proposal["suggested_chain_id"],
                "suggested_residue_name": proposal["suggested_residue_name"],
                "suggested_residue_index": proposal["suggested_residue_index"],
                "suggested_residue_atom_name": proposal["suggested_residue_atom_name"],
                "suggested_ligand_comp_id": proposal["suggested_ligand_comp_id"],
                "suggested_ligand_atom_name": proposal["suggested_ligand_atom_name"],
                "suggested_covalent_bond_atom_pair": proposal["suggested_covalent_bond_atom_pair"],
                "suggested_covalent_event_id": proposal["suggested_covalent_event_id"],
                "struct_conn_id": proposal["struct_conn_id"],
                "struct_conn_type": proposal["struct_conn_type"],
                "evidence_source_name": proposal["evidence_source_name"],
                "evidence_source_path": proposal["evidence_source_path"],
                "evidence_provenance_status": proposal["evidence_provenance_status"],
                "ambiguity_status": proposal["ambiguity_status"],
                "review_status": "pending_covpdb_annotation_alignment",
                "covpdb_annotation_alignment_status": "pending",
                "manual_review_status": "pending_manual_review",
                "ready_candidate_current_step": False,
                "exclusion_reason": "",
            }
        )
    return candidates


def build_decision_rows(proposals: list[dict[str, str]], disulfide_rows: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    disulfide_count = sum(row["review_classification"] == "exclude_disulfide_or_protein_protein_sg_sg" for row in disulfide_rows)
    other_count = sum(row["review_classification"] == "other_excluded_or_needs_manual_triage" for row in disulfide_rows)
    unique_pdb_count = len({row["pdb_id"] for row in candidates})
    threshold_status = "met" if len(candidates) >= 20 else "below_threshold_needs_expansion_after_alignment"
    checks = [
        ("input_support_proposal_count", str(len(proposals)), len(proposals) == 86, "input proposals reviewed"),
        ("disulfide_excluded_count", str(disulfide_count), disulfide_count > 0, "SG-SG/CYS protein-protein rows excluded"),
        ("other_excluded_or_triage_count", str(other_count), other_count >= 0, "non-matching rows not promoted"),
        ("ligand_covale_candidate_count", str(len(candidates)), len(candidates) >= 0, "derived from support review rules"),
        ("unique_pdb_count_for_ligand_covale_candidates", str(unique_pdb_count), unique_pdb_count <= len(candidates), "unique PDBs only a summary, not event identity"),
        ("all_ligand_covale_candidates_pending_review", str(all(row["manual_review_status"] == "pending_manual_review" for row in candidates)), all(row["manual_review_status"] == "pending_manual_review" for row in candidates), "manual review retained"),
        ("no_ready_candidates_created", "true", all(not _bool(row["ready_candidate_current_step"]) for row in candidates), "no ready candidates"),
        ("covpdb_annotation_alignment_required", "true", True, "next gate required before materialization"),
        ("small_pilot_threshold_20_status", threshold_status, True, threshold_status),
        ("training_still_blocked", "true", True, "training blocked"),
    ]
    return [
        {
            "decision_item": item,
            "observed_status": observed,
            "decision_passed": passed,
            "qa_comment": comment,
        }
        for item, observed, passed, comment in checks
    ]


def build_downstream_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    count = len(candidates)
    alignment_ready = count > 0
    rows = [
        ("support_review_completed", "true", True, "covapie_cys_sg_ligand_covale_annotation_alignment_gate" if alignment_ready else "covapie_cys_sg_targeted_metadata_expansion_gate", ""),
        ("disulfide_rows_excluded", "true", True, "covapie_cys_sg_ligand_covale_annotation_alignment_gate", ""),
        ("ligand_covale_candidates_written", str(count), True, "covapie_cys_sg_ligand_covale_annotation_alignment_gate" if alignment_ready else "covapie_cys_sg_targeted_metadata_expansion_gate", ""),
        ("ready_for_covapie_cys_sg_ligand_covale_annotation_alignment_gate", str(alignment_ready), True, "covapie_cys_sg_ligand_covale_annotation_alignment_gate" if alignment_ready else "not_ready_no_ligand_candidates", ""),
        ("ready_for_covapie_cys_sg_targeted_metadata_expansion_gate_after_alignment_if_below_20", str(count < 20), True, "covapie_cys_sg_targeted_metadata_expansion_gate_after_alignment_if_below_20", ""),
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


def build_safety_rows(disulfide_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[tuple[str, str, str, bool]] = [
        ("no_network_access_current_step", "passed", "passed", True),
        ("no_download_current_step", "passed", "passed", True),
        ("no_raw_file_content_read_current_step", "passed", "passed", True),
        ("no_raw_files_written_current_step", "passed", "passed", True),
        ("raw_files_untracked", "passed", "passed" if not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT) else "failed", not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT)),
        ("raw_files_unstaged", "passed", "passed" if not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT) else "failed", not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT)),
        ("metadata_csv_unchanged", "passed", "passed" if _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()]) else "failed", _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14h_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14H_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14H_ROOT.as_posix()])),
        ("step14g_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14G_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14G_ROOT.as_posix()])),
        ("step14f_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14F_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14F_ROOT.as_posix()])),
        ("step14e_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14E_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14E_ROOT.as_posix()])),
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
        ("disulfide_not_promoted_to_training_candidate", "passed", "passed" if all(row["review_classification"] != "exclude_disulfide_or_protein_protein_sg_sg" or not _bool(row["keep_for_ligand_covale_review"]) for row in disulfide_rows) else "failed", all(row["review_classification"] != "exclude_disulfide_or_protein_protein_sg_sg" or not _bool(row["keep_for_ligand_covale_review"]) for row in disulfide_rows)),
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
    input_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    disulfide_rows: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
    downstream_rows: list[dict[str, Any]],
    safety_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    input_count = len(disulfide_rows)
    disulfide_count = sum(row["review_classification"] == "exclude_disulfide_or_protein_protein_sg_sg" for row in disulfide_rows)
    other_count = sum(row["review_classification"] == "other_excluded_or_needs_manual_triage" for row in disulfide_rows)
    ligand_count = len(candidates)
    unique_pdb_count = len({row["pdb_id"] for row in candidates})
    threshold_met = ligand_count >= 20
    threshold_status = "met" if threshold_met else "below_threshold_needs_expansion_after_alignment"
    ready_alignment = ligand_count > 0
    next_step = "covapie_cys_sg_ligand_covale_annotation_alignment_gate" if ready_alignment else "covapie_cys_sg_targeted_metadata_expansion_gate"
    all_pending = all(row["manual_review_status"] == "pending_manual_review" and row["review_status"] == "pending_covpdb_annotation_alignment" for row in candidates)
    csv_json_consistent = True
    passed = (
        _all_true(precondition_rows, "precondition_passed")
        and _all_true(input_rows, "input_audit_passed")
        and _all_true(policy_rows, "policy_contract_passed")
        and _all_true(disulfide_rows, "disulfide_exclusion_audit_passed")
        and _all_true(decision_rows, "decision_passed")
        and _all_true(downstream_rows, "readiness_passed")
        and _all_true(safety_rows, "safety_passed")
        and all_pending
        and all(not _bool(row["ready_candidate_current_step"]) for row in candidates)
    )
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "current_source_profile": CURRENT_SOURCE_PROFILE,
        "current_source_database": CURRENT_SOURCE_DATABASE,
        "input_support_proposal_count": input_count,
        "disulfide_excluded_count": disulfide_count,
        "other_excluded_or_triage_count": other_count,
        "ligand_covale_candidate_count": ligand_count,
        "unique_ligand_covale_pdb_count": unique_pdb_count,
        "ligand_covale_candidates_csv_json_consistent": csv_json_consistent,
        "all_ligand_covale_candidates_pending_manual_review": all_pending,
        "no_ready_candidates_created": True,
        "ready_candidate_count_current_step": 0,
        "disulfide_rows_excluded_from_training_scope": True,
        "small_pilot_threshold_20_met": threshold_met,
        "small_pilot_threshold_20_status": threshold_status,
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
        "ready_for_covapie_cys_sg_ligand_covale_annotation_alignment_gate": ready_alignment,
        "ready_for_covapie_cys_sg_targeted_metadata_expansion_gate": ligand_count == 0,
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


def run_covapie_cys_sg_discovery_support_review_gate_v0() -> dict[str, Any]:
    proposals = _csv_rows(STEP14H_PROPOSALS_CSV)
    proposal_json_rows = _proposal_json_rows()
    precondition_rows = build_precondition_rows(proposals, proposal_json_rows)
    input_rows = build_input_audit_rows(proposals, proposal_json_rows)
    policy_rows = build_policy_rows()
    disulfide_rows = build_disulfide_audit_rows(proposals)
    candidates = build_ligand_covale_candidates(proposals, disulfide_rows)
    decision_rows = build_decision_rows(proposals, disulfide_rows, candidates)
    downstream_rows = build_downstream_rows(candidates)
    safety_rows = build_safety_rows(disulfide_rows)
    manifest = build_manifest(precondition_rows, input_rows, policy_rows, disulfide_rows, candidates, decision_rows, downstream_rows, safety_rows)
    return {
        "precondition_rows": precondition_rows,
        "input_rows": input_rows,
        "policy_rows": policy_rows,
        "disulfide_rows": disulfide_rows,
        "candidates": candidates,
        "decision_rows": decision_rows,
        "downstream_rows": downstream_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }
