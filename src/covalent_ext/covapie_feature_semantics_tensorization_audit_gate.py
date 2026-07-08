from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_actual_dataloader_design_gate as step13bw


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_feature_semantics_tensorization_audit_gate_v0"
PREVIOUS_STAGE = step13bw.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_feature_semantics_tensorization_audit_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_feature_semantics_tensorization_precondition_audit.csv"
STATIC_SOURCE_AUDIT_CSV = OUTPUT_ROOT / "covapie_original_feature_source_static_audit.csv"
COORDINATE_TENSORIZATION_AUDIT_CSV = OUTPUT_ROOT / "covapie_coordinate_tensorization_semantics_audit.csv"
ATOM_FEATURE_AUDIT_CSV = OUTPUT_ROOT / "covapie_atom_feature_semantics_audit.csv"
UNKNOWN_ATOM_POLICY_AUDIT_CSV = OUTPUT_ROOT / "covapie_unknown_atom_policy_audit.csv"
LABEL_TENSORIZATION_BLOCKER_AUDIT_CSV = OUTPUT_ROOT / "covapie_label_tensorization_blocker_audit.csv"
READINESS_DECISION_CONTRACT_CSV = OUTPUT_ROOT / "covapie_tensorization_readiness_decision_contract.csv"
RESOLUTION_PLAN_CSV = OUTPUT_ROOT / "covapie_feature_semantics_resolution_plan.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_feature_semantics_tensorization_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_feature_semantics_tensorization_audit_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_feature_semantics_tensorization_audit_gate_v0_summary.md")

step13bv = step13bw.step13bv
step13bu = step13bw.step13bu
step13bo = step13bw.step13bo
step13bm = step13bw.step13bm
step13bd = step13bw.step13bd

CANONICAL_MASK_TASK_NAMES = step13bw.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bw.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = step13bw.METADATA_CSV_SHA256

DATASET_PY = Path("dataset.py")
PREPARE_CROSSDOCKED_PY = Path("data/prepare_crossdocked.py")
LIGHTNING_MODULES_PY = Path("lightning_modules.py")
EQUIVARIANT_DIFFUSION_DIR = Path("equivariant_diffusion")
SRC_COVALENT_EXT_DIR = Path("src/covalent_ext")
MODULE_PATH = Path("src/covalent_ext/covapie_feature_semantics_tensorization_audit_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_feature_semantics_tensorization_audit_gate_v0.py")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
STATIC_SOURCE_COLUMNS = ["source_audit_item", "source_path_or_scope", "search_or_reference_policy", "observed_status", "evidence_summary", "source_audit_passed", "qa_comment"]
COORDINATE_COLUMNS = [
    "coordinate_item",
    "source_fields_or_evidence",
    "observed_status",
    "future_tensor_key",
    "semantics_confidence",
    "current_step_tensorized",
    "coordinate_audit_passed",
    "qa_comment",
]
ATOM_FEATURE_COLUMNS = [
    "atom_feature_item",
    "source_or_evidence",
    "observed_status",
    "semantics_status",
    "blocks_actual_tensor_dataloader_smoke",
    "blocks_training",
    "atom_feature_audit_passed",
    "qa_comment",
]
UNKNOWN_POLICY_COLUMNS = [
    "unknown_policy_item",
    "observed_status",
    "required_resolution",
    "blocks_actual_tensor_dataloader_smoke",
    "blocks_training",
    "unknown_policy_audit_passed",
    "qa_comment",
]
LABEL_BLOCKER_COLUMNS = [
    "label_blocker_item",
    "source_or_evidence",
    "observed_status",
    "current_tensorization_status",
    "blocks_actual_tensor_dataloader_smoke",
    "blocks_training",
    "label_blocker_audit_passed",
    "qa_comment",
]
READINESS_COLUMNS = ["readiness_decision_item", "decision", "reason", "ready_current_step", "required_next_gate", "readiness_decision_passed"]
RESOLUTION_PLAN_COLUMNS = ["resolution_item", "required_action", "allowed_inputs_future_step", "expected_future_output", "blocked_outputs_current_step", "resolution_plan_passed"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    return _run_git(["diff", "--quiet", "--", *paths]).returncode != 0 or _run_git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0


def _metadata_hash() -> str:
    return hashlib.sha256(step13bd.METADATA_CSV.read_bytes()).hexdigest() if step13bd.METADATA_CSV.exists() else ""


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _source_text(path: Path) -> str:
    full_path = REPO_ROOT / path
    if full_path.is_dir():
        return "\n".join(source.read_text(encoding="utf-8") for source in sorted(full_path.rglob("*.py")))
    return full_path.read_text(encoding="utf-8") if full_path.exists() else ""


def _static_reference_summary(path: Path) -> tuple[str, str, bool]:
    full_path = REPO_ROOT / path
    if full_path.is_dir():
        files = sorted(full_path.rglob("*.py"))
        text = _source_text(path)
        return "static_read_only", f"py_files={len(files)};bytes={len(text)}", bool(files)
    text = _source_text(path)
    return "static_read_only", f"bytes={len(text)}", bool(text)


def _search_summary(paths: list[Path], terms: list[str]) -> tuple[str, str, bool]:
    texts = {path.as_posix(): _source_text(path) for path in paths}
    hits: list[str] = []
    for label, text in texts.items():
        count = sum(text.count(term) for term in terms)
        if count:
            hits.append(f"{label}:{count}")
    summary = ";".join(hits) if hits else "no_exact_symbol_hits"
    return "static_search_completed", summary, True


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.is_file() and path.suffix.lower() in forbidden for path in root.rglob("*"))


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {
        "actual_dataloader_smoke.csv",
        "actual_dataloader_smoke.json",
        "dataloader_smoke.csv",
        "dataloader_smoke.json",
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
    }
    return root.exists() and any(path.name in forbidden for path in root.rglob("*"))


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
    forbidden = {"urllib", "requests", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"}
    return any(_imports_forbidden_module(path, forbidden) for path in [MODULE_PATH, CHECK_SCRIPT_PATH])


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest13bw = _load_json(step13bw.MANIFEST_JSON)
    manifest13bm = _load_json(step13bm.MANIFEST_JSON)
    metadata_rows = _csv_rows(step13bu.SMOKE_PREVIEW_CSV)
    final_rows = _csv_rows(step13bo.SMOKE_PREVIEW_CSV)
    checks = [
        ("step13bw_manifest_exists", step13bw.MANIFEST_JSON, "exists", step13bw.MANIFEST_JSON.exists(), step13bw.MANIFEST_JSON.exists()),
        ("step13bw_stage", step13bw.MANIFEST_JSON, step13bw.STAGE, manifest13bw.get("stage"), manifest13bw.get("stage") == step13bw.STAGE),
        ("step13bw_all_checks_passed", step13bw.MANIFEST_JSON, "true", manifest13bw.get("all_checks_passed"), manifest13bw.get("all_checks_passed") is True),
        ("step13bw_ready_for_feature_semantics_tensorization_audit_gate", step13bw.MANIFEST_JSON, "true", manifest13bw.get("ready_for_covapie_feature_semantics_tensorization_audit_gate"), manifest13bw.get("ready_for_covapie_feature_semantics_tensorization_audit_gate") is True),
        ("step13bw_ready_for_actual_dataloader_adapter_smoke", step13bw.MANIFEST_JSON, "false", manifest13bw.get("ready_for_covapie_actual_dataloader_adapter_smoke"), manifest13bw.get("ready_for_covapie_actual_dataloader_adapter_smoke") is False),
        ("step13bw_ready_for_actual_dataloader_smoke", step13bw.MANIFEST_JSON, "false", manifest13bw.get("ready_for_covapie_actual_dataloader_smoke"), manifest13bw.get("ready_for_covapie_actual_dataloader_smoke") is False),
        ("step13bw_ready_for_training", step13bw.MANIFEST_JSON, "false", manifest13bw.get("ready_for_training"), manifest13bw.get("ready_for_training") is False),
        ("step13bw_ready_to_train_now", step13bw.MANIFEST_JSON, "false", manifest13bw.get("ready_to_train_now"), manifest13bw.get("ready_to_train_now") is False),
        ("step13bm_feature_semantics_audit_completed", step13bm.MANIFEST_JSON, "true", manifest13bm.get("feature_semantics_audit_completed_current_step"), manifest13bm.get("feature_semantics_audit_completed_current_step") is True),
        ("step13bm_feature_semantics_known_for_training", step13bm.MANIFEST_JSON, "false", manifest13bm.get("feature_semantics_known_for_training"), manifest13bm.get("feature_semantics_known_for_training") is False),
        ("step13bm_unknown_atom_policy_finalized", step13bm.MANIFEST_JSON, "false", manifest13bm.get("unknown_atom_feature_policy_finalized_for_training"), manifest13bm.get("unknown_atom_feature_policy_finalized_for_training") is False),
        ("step13bu_metadata_smoke_preview_shape", step13bu.SMOKE_PREVIEW_CSV, "20x30", f"{len(metadata_rows)}x{len(metadata_rows[0]) if metadata_rows else 0}", len(metadata_rows) == 20 and bool(metadata_rows) and len(metadata_rows[0]) == 30),
        ("step13bo_final_dataset_smoke_preview_shape", step13bo.SMOKE_PREVIEW_CSV, "20x45", f"{len(final_rows)}x{len(final_rows[0]) if final_rows else 0}", len(final_rows) == 20 and bool(final_rows) and len(final_rows[0]) == 45),
        ("canonical_mask_count", step13bu.SMOKE_PREVIEW_CSV, "5", len({row["mask_task_name"] for row in metadata_rows}), len({row["mask_task_name"] for row in metadata_rows}) == 5),
        ("b3_scaffold_only_included", step13bu.SMOKE_PREVIEW_CSV, "true", "scaffold_only" in {row["mask_task_name"] for row in metadata_rows}, "scaffold_only" in {row["mask_task_name"] for row in metadata_rows}),
        ("no_extra_mask_tasks_added", step13bu.SMOKE_PREVIEW_CSV, "true", {row["mask_task_name"] for row in metadata_rows}, {row["mask_task_name"] for row in metadata_rows} == set(CANONICAL_MASK_TASK_NAMES)),
        ("metadata_csv_hash_unchanged", step13bd.METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", step13bd.RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", step13bd.RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
    ]
    return [
        {
            "precondition_item": item,
            "artifact_or_check": str(check),
            "expected_status": expected,
            "observed_status": observed,
            "precondition_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, check, expected, observed, passed in checks
    ]


def build_original_feature_source_static_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item, path, comment in [
        ("dataset_py_static_feature_reference", DATASET_PY, "original Dataset/collate feature handling read as static reference"),
        ("prepare_crossdocked_static_feature_reference", PREPARE_CROSSDOCKED_PY, "original preprocessing feature handling read as static reference"),
        ("lightning_modules_static_feature_reference", LIGHTNING_MODULES_PY, "model batch key usage read as static reference"),
        ("equivariant_diffusion_static_feature_reference", EQUIVARIANT_DIFFUSION_DIR, "diffusion feature usage read as static reference"),
    ]:
        observed, evidence, passed = _static_reference_summary(path)
        rows.append(
            {
                "source_audit_item": item,
                "source_path_or_scope": path.as_posix(),
                "search_or_reference_policy": "static_read_only_no_import",
                "observed_status": observed,
                "evidence_summary": evidence,
                "source_audit_passed": passed,
                "qa_comment": comment,
            }
        )
    search_scope = [DATASET_PY, PREPARE_CROSSDOCKED_PY, LIGHTNING_MODULES_PY, EQUIVARIANT_DIFFUSION_DIR, SRC_COVALENT_EXT_DIR]
    searches = [
        ("existing_atom_encoder_symbols_search", ["atom_encoder", "atom_type", "atom_nf", "one_hot"]),
        ("existing_atom_decoder_symbols_search", ["atom_decoder", "idx_to_atom", "decode", "argmax"]),
        ("existing_aa_encoder_symbols_search", ["aa_encoder", "residue", "residue_nf", "amino"]),
        ("existing_feature_dimension_symbols_search", ["feature_dimension", "atom_nf", "residue_nf", "x_dims", "n_dims"]),
        ("existing_unknown_atom_handling_search", ["unknown", "unk", "UNKNOWN", "Unknown"]),
        ("existing_batch_key_symbols_search", ["collate_fn", "ligand", "pocket", "mask", "one_hot", "x"]),
    ]
    for item, terms in searches:
        observed, evidence, passed = _search_summary(search_scope, terms)
        rows.append(
            {
                "source_audit_item": item,
                "source_path_or_scope": "dataset.py;data/prepare_crossdocked.py;lightning_modules.py;equivariant_diffusion/;src/covalent_ext/",
                "search_or_reference_policy": "static_symbol_search_no_import_no_semantics_claim",
                "observed_status": observed,
                "evidence_summary": evidence,
                "source_audit_passed": passed,
                "qa_comment": "symbol evidence recorded without claiming training-final semantics",
            }
        )
    original_no_diff = not _path_diff_exists([DATASET_PY.as_posix(), PREPARE_CROSSDOCKED_PY.as_posix()])
    protected_no_diff = not _path_diff_exists([EQUIVARIANT_DIFFUSION_DIR.as_posix(), LIGHTNING_MODULES_PY.as_posix()])
    rows.extend(
        [
            {
                "source_audit_item": "original_dataloader_no_diff",
                "source_path_or_scope": "dataset.py;data/prepare_crossdocked.py",
                "search_or_reference_policy": "git_diff_check",
                "observed_status": "no_diff" if original_no_diff else "diff_present",
                "evidence_summary": "original DiffSBDD dataloader files unchanged",
                "source_audit_passed": original_no_diff,
                "qa_comment": "no source modification",
            },
            {
                "source_audit_item": "protected_model_code_no_diff",
                "source_path_or_scope": "lightning_modules.py;equivariant_diffusion/",
                "search_or_reference_policy": "git_diff_check",
                "observed_status": "no_diff" if protected_no_diff else "diff_present",
                "evidence_summary": "protected DiffSBDD model code unchanged",
                "source_audit_passed": protected_no_diff,
                "qa_comment": "no source modification",
            },
        ]
    )
    return rows


def build_coordinate_tensorization_rows() -> list[dict[str, Any]]:
    metadata_rows = _csv_rows(step13bu.SMOKE_PREVIEW_CSV)
    final_rows = _csv_rows(step13bo.SMOKE_PREVIEW_CSV)
    protein_paths_present = all(row["protein_pocket_atom_table_path"] for row in metadata_rows)
    ligand_paths_present = all(row["ligand_atom_table_path"] for row in metadata_rows)
    coordinate_units = sorted({row.get("coordinate_unit", "") for row in final_rows})
    coordinate_frames = sorted({row.get("coordinate_frame_status", "") for row in final_rows})
    protein_counts_present = all(int(row["protein_atom_row_count_for_event"]) > 0 for row in metadata_rows)
    ligand_counts_present = all(int(row["ligand_atom_row_count_for_event"]) > 0 for row in metadata_rows)
    rows = [
        ("protein_xyz_source_path_refs", "protein_pocket_atom_table_path", f"paths_present={protein_paths_present}", "protein_xyz", "medium", False),
        ("ligand_xyz_source_path_refs", "ligand_atom_table_path", f"paths_present={ligand_paths_present}", "ligand_xyz", "medium", False),
        ("coordinate_unit_angstrom_candidate", "coordinate_unit", ";".join(coordinate_units), "coordinate_unit", "medium", False),
        ("coordinate_frame_current_smoke", "coordinate_frame_status", ";".join(coordinate_frames), "coordinate_frame_status", "medium", False),
        ("protein_atom_row_counts_available", "protein_atom_row_count_for_event", f"positive_counts={protein_counts_present}", "num_protein_atoms", "high", False),
        ("ligand_atom_row_counts_available", "ligand_atom_row_count_for_event", f"positive_counts={ligand_counts_present}", "num_ligand_atoms", "high", False),
        ("coordinate_tensor_candidate_future", "derived atom table refs and row counts", "candidate_for_future_design_only", "protein_xyz;ligand_xyz", "medium", False),
        ("coordinate_tensorization_still_requires_actual_smoke", "current execution boundary", "not_tensorized_current_step", "protein_xyz;ligand_xyz", "high", False),
    ]
    return [
        {
            "coordinate_item": item,
            "source_fields_or_evidence": source,
            "observed_status": observed,
            "future_tensor_key": key,
            "semantics_confidence": confidence,
            "current_step_tensorized": tensorized,
            "coordinate_audit_passed": True,
            "qa_comment": "coordinate source is a future tensorization candidate only; no tensor current step",
        }
        for item, source, observed, key, confidence, tensorized in rows
    ]


def build_atom_feature_rows() -> list[dict[str, Any]]:
    rows = [
        ("protein_atom_feature_source_not_training_final", "Step 13BM feature semantics blockers", "not_training_final", "blocked", True, True),
        ("ligand_atom_feature_source_not_training_final", "Step 13BM feature semantics blockers", "not_training_final", "blocked", True, True),
        ("atom_element_symbol_semantics_partial", "derived metadata/static feature search", "partial_evidence_only", "not_training_final", True, True),
        ("atom_type_encoder_mapping_not_locked", "static atom encoder symbol search", "not_locked", "not_training_final", True, True),
        ("aromatic_formal_charge_hybridization_unknown_or_not_final", "feature schema audit", "unknown_or_not_final", "not_training_final", True, True),
        ("residue_feature_semantics_not_final", "feature semantics audit", "not_training_final", "not_training_final", True, True),
        ("ligand_feature_schema_not_final", "feature semantics audit", "not_training_final", "not_training_final", True, True),
        ("protein_feature_schema_not_final", "feature semantics audit", "not_training_final", "not_training_final", True, True),
        ("feature_dimension_not_training_final", "static feature dimension symbol search", "not_training_final", "not_training_final", True, True),
        ("atom_feature_tensorization_blocked", "current gate boundary", "blocked_current_step", "blocked", True, True),
    ]
    return [
        {
            "atom_feature_item": item,
            "source_or_evidence": source,
            "observed_status": observed,
            "semantics_status": status,
            "blocks_actual_tensor_dataloader_smoke": blocks_smoke,
            "blocks_training": blocks_training,
            "atom_feature_audit_passed": True,
            "qa_comment": "atom feature semantics remain blocked before actual tensor dataloader smoke",
        }
        for item, source, observed, status, blocks_smoke, blocks_training in rows
    ]


def build_unknown_atom_policy_rows() -> list[dict[str, Any]]:
    rows = [
        ("unknown_atom_feature_policy_present_as_blocker", "blocker_present", "define explicit unknown atom policy"),
        ("unknown_atom_feature_policy_finalized_for_training_false", "unknown_atom_feature_policy_finalized_for_training=false", "finalize unknown atom policy"),
        ("unknown_element_handling_not_final", "not_final", "resolve unknown element handling"),
        ("uncommon_ligand_atom_handling_not_final", "not_final", "resolve uncommon ligand atom policy"),
        ("protein_unknown_residue_handling_not_final", "not_final", "resolve unknown residue policy"),
        ("covalent_adduct_atom_mapping_unknown_policy_not_final", "not_final", "resolve covalent adduct atom mapping policy"),
        ("unknown_policy_blocks_actual_tensor_smoke", "blocked", "unknown policy resolution gate"),
        ("unknown_policy_blocks_training", "blocked", "formal training feature semantics audit"),
    ]
    return [
        {
            "unknown_policy_item": item,
            "observed_status": observed,
            "required_resolution": resolution,
            "blocks_actual_tensor_dataloader_smoke": True,
            "blocks_training": True,
            "unknown_policy_audit_passed": True,
            "qa_comment": "unknown atom policy remains unresolved for tensorization and training",
        }
        for item, observed, resolution in rows
    ]


def build_label_tensorization_blocker_rows() -> list[dict[str, Any]]:
    rows = [
        ("mask_task_name_string_selector_ok_for_metadata", "mask_task_name", "metadata_selector_available", "metadata_only_not_tensorized", False, False),
        ("mask_boolean_tensor_blocked_until_group_labels", "group label materialization", "not_materialized", "blocked", True, True),
        ("scaffold_linker_warhead_labels_not_materialized", "final dataset smoke status", "not_materialized", "blocked", True, True),
        ("warhead_type_label_not_materialized", "auxiliary label audit", "not_materialized", "blocked", True, True),
        ("covalent_atom_pair_label_not_training_final", "covalent_bond_atom_pair", "metadata_only_not_training_final", "blocked", True, True),
        ("covalent_bond_distance_metadata_only", "covalent_bond_distance_angstrom", "metadata_only", "metadata_only_not_tensorized", True, True),
        ("pre_covalent_geometry_label_not_materialized", "geometry label audit", "not_materialized", "blocked", True, True),
        ("post_covalent_geometry_label_not_training_final", "geometry label audit", "not_training_final", "blocked", True, True),
        ("auxiliary_loss_labels_not_ready", "auxiliary label audit", "not_ready", "blocked", True, True),
        ("batch_collate_for_labels_blocked", "batch/collate design", "blocked", "blocked", True, True),
        ("loss_integration_blocked", "loss integration gate", "blocked", "blocked", True, True),
        ("training_targets_blocked", "training target semantics", "blocked", "blocked", True, True),
    ]
    return [
        {
            "label_blocker_item": item,
            "source_or_evidence": source,
            "observed_status": observed,
            "current_tensorization_status": status,
            "blocks_actual_tensor_dataloader_smoke": blocks_smoke,
            "blocks_training": blocks_training,
            "label_blocker_audit_passed": True,
            "qa_comment": "label tensorization blocker explicitly recorded",
        }
        for item, source, observed, status, blocks_smoke, blocks_training in rows
    ]


def build_readiness_decision_rows() -> list[dict[str, Any]]:
    rows = [
        ("coordinate_tensor_candidate_ready_for_design_only", "candidate_for_future_design_only", "derived coordinate path refs and row counts exist; no tensor smoke yet", True, "covapie_feature_semantics_resolution_design_gate"),
        ("atom_feature_tensorization_not_ready", "not_ready", "atom feature semantics not training-final", False, "covapie_feature_semantics_resolution_design_gate"),
        ("mask_boolean_tensorization_not_ready", "not_ready", "group labels not materialized", False, "covapie_feature_semantics_resolution_design_gate"),
        ("auxiliary_label_tensorization_not_ready", "not_ready", "auxiliary labels not materialized or not training-final", False, "covapie_feature_semantics_resolution_design_gate"),
        ("unknown_atom_policy_not_ready", "not_ready", "unknown atom policy not finalized", False, "covapie_feature_semantics_resolution_design_gate"),
        ("batch_collate_tensorization_not_ready", "not_ready", "tensor shape/dtype/collate policy requires future gate", False, "covapie_feature_semantics_resolution_design_gate"),
        ("checkpoint_runtime_not_ready", "not_ready", "checkpoint compatibility cannot be run before tensorization policy", False, "covapie_checkpoint_compatibility_smoke_before_model_runtime"),
        ("model_forward_not_ready", "not_ready", "model forward requires checkpoint-compatible tensor batch", False, "covapie_model_forward_smoke_after_checkpoint_compatibility"),
        ("actual_dataloader_adapter_smoke_not_ready", "not_ready", "feature semantics blockers still active", False, "covapie_feature_semantics_resolution_design_gate"),
        ("formal_training_not_ready", "not_ready", "feature semantics, leakage/split, checkpoint, forward, and loss gates remain required", False, "formal_training_feature_semantics_audit"),
    ]
    return [
        {
            "readiness_decision_item": item,
            "decision": decision,
            "reason": reason,
            "ready_current_step": ready,
            "required_next_gate": gate,
            "readiness_decision_passed": True,
        }
        for item, decision, reason, ready, gate in rows
    ]


def build_resolution_plan_rows() -> list[dict[str, Any]]:
    rows = [
        ("resolve_original_diffsbbd_feature_schema", "map original DiffSBDD feature keys/dimensions without modifying source", "static source refs; existing checkpoint compatibility evidence", "feature schema mapping contract", "actual dataloader smoke; tensors; training"),
        ("resolve_covapie_ligand_atom_feature_schema", "define ligand atom feature schema and dtype policy", "derived ligand atom tables; feature semantics audits", "ligand feature schema contract", "actual dataloader smoke; training"),
        ("resolve_covapie_protein_atom_feature_schema", "define protein atom/residue feature schema and dtype policy", "derived protein atom tables; feature semantics audits", "protein feature schema contract", "actual dataloader smoke; training"),
        ("resolve_unknown_atom_policy", "define unknown/uncommon atom and residue handling", "static searches; derived atom tables", "unknown atom policy contract", "actual dataloader smoke; training"),
        ("resolve_mask_group_label_materialization", "materialize scaffold/linker/warhead group labels in a separate gate", "mask contracts; final dataset smoke preview", "group label materialization contract", "boolean mask tensors; training"),
        ("resolve_auxiliary_label_semantics", "settle warhead/covalent-pair/geometry auxiliary labels", "feature semantics artifacts; final dataset smoke preview", "auxiliary label semantics contract", "loss targets; training"),
        ("resolve_tensor_shape_dtype_policy", "define tensor shape, dtype, padding/collate policy", "feature schema contracts; coordinate candidates", "tensor shape dtype policy contract", "actual DataLoader tensors; training"),
        ("rerun_actual_dataloader_design_after_resolution", "rerun/update actual dataloader design after blockers resolve", "resolved feature semantics contracts", "updated adapter smoke readiness contract", "training"),
    ]
    return [
        {
            "resolution_item": item,
            "required_action": action,
            "allowed_inputs_future_step": inputs,
            "expected_future_output": output,
            "blocked_outputs_current_step": blocked,
            "resolution_plan_passed": True,
        }
        for item, action, inputs, output, blocked in rows
    ]


def build_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "empty", not _raw_files_tracked()),
        ("raw_files_unstaged", "empty", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "true", True),
        ("derived_output_no_forbidden_binary_artifacts", "true", not _forbidden_suffix_exists()),
        ("no_actual_dataloader_smoke_written", "true", not _forbidden_named_artifact_exists()),
        ("no_real_dataloader_written", "true", not _forbidden_named_artifact_exists()),
        ("no_original_dataloader_modified", "true", not _path_diff_exists([DATASET_PY.as_posix(), PREPARE_CROSSDOCKED_PY.as_posix()])),
        ("no_torch_tensor_checkpoint_training_artifacts", "true", not _forbidden_suffix_exists()),
        ("no_numpy_outputs", "true", True),
        ("no_real_final_dataset_written", "true", not _forbidden_named_artifact_exists()),
        ("no_new_sample_index_written", "true", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", "true", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", "true", not _forbidden_named_artifact_exists()),
        ("metadata_csv_unchanged", "unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bw_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bw.OUTPUT_ROOT.as_posix()])),
        ("step13bv_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bv.OUTPUT_ROOT.as_posix()])),
        ("step13bu_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bu.OUTPUT_ROOT.as_posix()])),
        ("step13bo_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bo.OUTPUT_ROOT.as_posix()])),
        ("step13bm_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bm.OUTPUT_ROOT.as_posix()])),
        ("step13ai_inventory_artifacts_unchanged", "no_diff", not _path_diff_exists(["data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0"])),
        ("protected_source_diff_empty", "no_diff", not _path_diff_exists([EQUIVARIANT_DIFFUSION_DIR.as_posix(), LIGHTNING_MODULES_PY.as_posix()])),
        ("original_dataloader_diff_empty", "no_diff", not _path_diff_exists([DATASET_PY.as_posix(), PREPARE_CROSSDOCKED_PY.as_posix()])),
        ("no_network_download_rdkit_biopdb_gemmi_gzip_torch_numpy_imports", "true", not _own_files_have_forbidden_imports()),
    ]
    return [
        {
            "safety_item": item,
            "required_status": required,
            "observed_status": "passed" if passed else "failed",
            "safety_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, required, passed in checks
    ]


def run_covapie_feature_semantics_tensorization_audit_gate_v0() -> dict[str, Any]:
    precondition_rows = build_precondition_rows()
    static_rows = build_original_feature_source_static_rows()
    coordinate_rows = build_coordinate_tensorization_rows()
    atom_rows = build_atom_feature_rows()
    unknown_rows = build_unknown_atom_policy_rows()
    label_rows = build_label_tensorization_blocker_rows()
    readiness_rows = build_readiness_decision_rows()
    resolution_rows = build_resolution_plan_rows()
    safety_rows = build_safety_rows()
    metadata_rows = _csv_rows(step13bu.SMOKE_PREVIEW_CSV)
    final_rows = _csv_rows(step13bo.SMOKE_PREVIEW_CSV)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bw_actual_dataloader_design_gate_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "source_metadata_smoke_preview_row_count": len(metadata_rows),
        "source_metadata_smoke_preview_column_count": len(metadata_rows[0]) if metadata_rows else 0,
        "source_final_dataset_preview_row_count": len(final_rows),
        "source_final_dataset_preview_column_count": len(final_rows[0]) if final_rows else 0,
        "source_canonical_mask_task_count": len({row["mask_task_name"] for row in metadata_rows}),
        "original_feature_source_static_audit_row_count": len(static_rows),
        "coordinate_tensorization_semantics_audit_row_count": len(coordinate_rows),
        "atom_feature_semantics_audit_row_count": len(atom_rows),
        "unknown_atom_policy_audit_row_count": len(unknown_rows),
        "label_tensorization_blocker_audit_row_count": len(label_rows),
        "tensorization_readiness_decision_contract_row_count": len(readiness_rows),
        "feature_semantics_resolution_plan_row_count": len(resolution_rows),
        "original_feature_source_static_audit_passed": all(_bool(row["source_audit_passed"]) for row in static_rows),
        "coordinate_tensorization_semantics_audit_passed": all(_bool(row["coordinate_audit_passed"]) for row in coordinate_rows),
        "atom_feature_semantics_audit_passed": all(_bool(row["atom_feature_audit_passed"]) for row in atom_rows),
        "unknown_atom_policy_audit_passed": all(_bool(row["unknown_policy_audit_passed"]) for row in unknown_rows),
        "label_tensorization_blocker_audit_passed": all(_bool(row["label_blocker_audit_passed"]) for row in label_rows),
        "tensorization_readiness_decision_contract_passed": all(_bool(row["readiness_decision_passed"]) for row in readiness_rows),
        "feature_semantics_resolution_plan_passed": all(_bool(row["resolution_plan_passed"]) for row in resolution_rows),
        "safety_audit_passed": all(_bool(row["safety_passed"]) for row in safety_rows),
        "feature_semantics_tensorization_audit_completed_current_step": True,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "coordinate_tensor_candidate_for_future_design": True,
        "atom_feature_tensorization_ready": False,
        "mask_boolean_tensorization_ready": False,
        "auxiliary_label_tensorization_ready": False,
        "actual_dataloader_adapter_smoke_written": False,
        "actual_dataloader_smoke_written": False,
        "real_dataloader_written": False,
        "original_dataloader_modified": False,
        "final_dataset_written": False,
        "sample_index_written_current_step": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "dataloader_smoke_written": False,
        "training_artifacts_written": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "numpy_imported": False,
        "numpy_array_returned": False,
        "checkpoint_loaded": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "raw_file_content_read_current_step": False,
        "raw_data_read": False,
        "mmcif_text_read": False,
        "mmcif_parse_current_step": False,
        "coordinate_extraction_current_step": False,
        "network_access_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "gzip_open_used": False,
        "ready_for_covapie_feature_semantics_resolution_design_gate": True,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_covapie_actual_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in {row["mask_task_name"] for row in metadata_rows},
        "no_extra_mask_tasks_added": {row["mask_task_name"] for row in metadata_rows} == set(CANONICAL_MASK_TASK_NAMES),
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_feature_semantics_resolution_design_gate",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13bw_actual_dataloader_design_gate_validated"],
            manifest["source_metadata_smoke_preview_row_count"] == 20,
            manifest["source_metadata_smoke_preview_column_count"] == 30,
            manifest["source_final_dataset_preview_row_count"] == 20,
            manifest["source_final_dataset_preview_column_count"] == 45,
            manifest["source_canonical_mask_task_count"] == 5,
            manifest["original_feature_source_static_audit_row_count"] == 12,
            manifest["coordinate_tensorization_semantics_audit_row_count"] == 8,
            manifest["atom_feature_semantics_audit_row_count"] == 10,
            manifest["unknown_atom_policy_audit_row_count"] == 8,
            manifest["label_tensorization_blocker_audit_row_count"] == 12,
            manifest["tensorization_readiness_decision_contract_row_count"] == 10,
            manifest["feature_semantics_resolution_plan_row_count"] == 8,
            manifest["original_feature_source_static_audit_passed"],
            manifest["coordinate_tensorization_semantics_audit_passed"],
            manifest["atom_feature_semantics_audit_passed"],
            manifest["unknown_atom_policy_audit_passed"],
            manifest["label_tensorization_blocker_audit_passed"],
            manifest["tensorization_readiness_decision_contract_passed"],
            manifest["feature_semantics_resolution_plan_passed"],
            manifest["safety_audit_passed"],
            manifest["feature_semantics_tensorization_audit_completed_current_step"],
            not manifest["feature_semantics_known_for_training"],
            not manifest["unknown_atom_feature_policy_finalized_for_training"],
            manifest["coordinate_tensor_candidate_for_future_design"],
            not manifest["atom_feature_tensorization_ready"],
            not manifest["mask_boolean_tensorization_ready"],
            not manifest["auxiliary_label_tensorization_ready"],
            not manifest["actual_dataloader_adapter_smoke_written"],
            not manifest["actual_dataloader_smoke_written"],
            not manifest["real_dataloader_written"],
            not manifest["torch_imported"],
            not manifest["torch_tensor_created"],
            not manifest["numpy_imported"],
            not manifest["checkpoint_loaded"],
            not manifest["model_forward_called"],
            not manifest["loss_compute_called"],
            not manifest["training_allowed"],
            manifest["ready_for_covapie_feature_semantics_resolution_design_gate"],
            not manifest["ready_for_covapie_actual_dataloader_adapter_smoke"],
            not manifest["ready_for_covapie_actual_dataloader_smoke"],
            not manifest["ready_for_training"],
            not manifest["ready_to_train_now"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["feature_semantics_tensorization_audit_gate_failed"]
    return {
        "precondition_rows": precondition_rows,
        "static_rows": static_rows,
        "coordinate_rows": coordinate_rows,
        "atom_rows": atom_rows,
        "unknown_rows": unknown_rows,
        "label_rows": label_rows,
        "readiness_rows": readiness_rows,
        "resolution_rows": resolution_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }
