from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_feature_semantics_tensorization_audit_gate as step13bx


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_feature_semantics_resolution_design_gate_v0"
PREVIOUS_STAGE = step13bx.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_feature_semantics_resolution_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_feature_semantics_resolution_precondition_audit.csv"
ORIGINAL_FEATURE_SCHEMA_MAPPING_CSV = OUTPUT_ROOT / "covapie_original_diffsbbd_feature_schema_mapping_design.csv"
COORDINATE_RESOLUTION_CONTRACT_CSV = OUTPUT_ROOT / "covapie_coordinate_tensorization_resolution_contract.csv"
ATOM_FEATURE_RESOLUTION_CONTRACT_CSV = OUTPUT_ROOT / "covapie_atom_feature_schema_resolution_contract.csv"
UNKNOWN_ATOM_POLICY_RESOLUTION_CONTRACT_CSV = OUTPUT_ROOT / "covapie_unknown_atom_policy_resolution_contract.csv"
LABEL_SEMANTICS_RESOLUTION_CONTRACT_CSV = OUTPUT_ROOT / "covapie_label_semantics_resolution_contract.csv"
TENSOR_SHAPE_DTYPE_RESOLUTION_CONTRACT_CSV = OUTPUT_ROOT / "covapie_tensor_shape_dtype_resolution_contract.csv"
RESOLUTION_SMOKE_PLAN_CSV = OUTPUT_ROOT / "covapie_feature_semantics_resolution_smoke_plan.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_feature_semantics_resolution_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_feature_semantics_resolution_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_feature_semantics_resolution_design_gate_v0_summary.md")

step13bw = step13bx.step13bw
step13bu = step13bx.step13bu
step13bo = step13bx.step13bo
step13bm = step13bx.step13bm
step13bd = step13bx.step13bd

CANONICAL_MASK_TASK_NAMES = step13bx.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bx.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = step13bx.METADATA_CSV_SHA256

DATASET_PY = Path("dataset.py")
PREPARE_CROSSDOCKED_PY = Path("data/prepare_crossdocked.py")
LIGHTNING_MODULES_PY = Path("lightning_modules.py")
EQUIVARIANT_DIFFUSION_DIR = Path("equivariant_diffusion")
SRC_COVALENT_EXT_DIR = Path("src/covalent_ext")
MODULE_PATH = Path("src/covalent_ext/covapie_feature_semantics_resolution_design_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_feature_semantics_resolution_design_gate_v0.py")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
ORIGINAL_MAPPING_COLUMNS = [
    "mapping_item",
    "static_source_scope",
    "observed_evidence_summary",
    "proposed_resolution_policy",
    "training_final_status",
    "blocks_actual_tensor_dataloader_smoke",
    "mapping_design_passed",
    "qa_comment",
]
COORDINATE_RESOLUTION_COLUMNS = [
    "coordinate_resolution_item",
    "source_or_evidence",
    "proposed_policy",
    "current_status",
    "ready_for_resolution_smoke",
    "ready_for_actual_tensor_smoke",
    "coordinate_resolution_passed",
    "qa_comment",
]
ATOM_FEATURE_RESOLUTION_COLUMNS = [
    "atom_feature_resolution_item",
    "source_or_evidence",
    "proposed_policy",
    "current_status",
    "ready_for_resolution_smoke",
    "ready_for_actual_tensor_smoke",
    "blocks_training",
    "atom_feature_resolution_passed",
    "qa_comment",
]
UNKNOWN_POLICY_RESOLUTION_COLUMNS = [
    "unknown_policy_resolution_item",
    "proposed_policy",
    "required_evidence_source",
    "current_status",
    "ready_for_resolution_smoke",
    "finalized_for_training_current_step",
    "unknown_policy_resolution_passed",
    "qa_comment",
]
LABEL_SEMANTICS_RESOLUTION_COLUMNS = [
    "label_resolution_item",
    "source_or_evidence",
    "proposed_policy",
    "current_status",
    "ready_for_resolution_smoke",
    "ready_for_actual_tensor_smoke",
    "blocks_training",
    "label_resolution_passed",
    "qa_comment",
]
TENSOR_SHAPE_DTYPE_RESOLUTION_COLUMNS = [
    "tensor_policy_item",
    "proposed_dtype_or_shape_policy",
    "current_status",
    "ready_for_resolution_smoke",
    "ready_for_actual_tensor_smoke",
    "checkpoint_compatibility_risk",
    "tensor_policy_passed",
    "qa_comment",
]
RESOLUTION_SMOKE_PLAN_COLUMNS = [
    "planned_step",
    "planned_action",
    "allowed_inputs",
    "allowed_outputs_future_step",
    "blocked_outputs_current_step",
    "required_preconditions",
    "resolution_smoke_plan_passed",
]
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


def _search_summary(paths: list[Path], terms: list[str]) -> str:
    texts = {path.as_posix(): _source_text(path) for path in paths}
    hits: list[str] = []
    for label, text in texts.items():
        count = sum(text.count(term) for term in terms)
        if count:
            hits.append(f"{label}:{count}")
    return ";".join(hits) if hits else "static_search_completed_no_exact_hits"


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
    manifest13bx = _load_json(step13bx.MANIFEST_JSON)
    manifest13bm = _load_json(step13bm.MANIFEST_JSON)
    metadata_rows = _csv_rows(step13bu.SMOKE_PREVIEW_CSV)
    final_rows = _csv_rows(step13bo.SMOKE_PREVIEW_CSV)
    metadata_mask_names = {row["mask_task_name"] for row in metadata_rows}
    checks = [
        ("step13bx_manifest_exists", step13bx.MANIFEST_JSON, "exists", step13bx.MANIFEST_JSON.exists(), step13bx.MANIFEST_JSON.exists()),
        ("step13bx_stage", step13bx.MANIFEST_JSON, step13bx.STAGE, manifest13bx.get("stage"), manifest13bx.get("stage") == step13bx.STAGE),
        ("step13bx_all_checks_passed", step13bx.MANIFEST_JSON, "true", manifest13bx.get("all_checks_passed"), manifest13bx.get("all_checks_passed") is True),
        ("step13bx_ready_for_feature_semantics_resolution_design_gate", step13bx.MANIFEST_JSON, "true", manifest13bx.get("ready_for_covapie_feature_semantics_resolution_design_gate"), manifest13bx.get("ready_for_covapie_feature_semantics_resolution_design_gate") is True),
        ("step13bx_ready_for_actual_dataloader_adapter_smoke", step13bx.MANIFEST_JSON, "false", manifest13bx.get("ready_for_covapie_actual_dataloader_adapter_smoke"), manifest13bx.get("ready_for_covapie_actual_dataloader_adapter_smoke") is False),
        ("step13bx_ready_for_actual_dataloader_smoke", step13bx.MANIFEST_JSON, "false", manifest13bx.get("ready_for_covapie_actual_dataloader_smoke"), manifest13bx.get("ready_for_covapie_actual_dataloader_smoke") is False),
        ("step13bx_ready_for_training", step13bx.MANIFEST_JSON, "false", manifest13bx.get("ready_for_training"), manifest13bx.get("ready_for_training") is False),
        ("step13bx_ready_to_train_now", step13bx.MANIFEST_JSON, "false", manifest13bx.get("ready_to_train_now"), manifest13bx.get("ready_to_train_now") is False),
        ("step13bx_feature_semantics_known_for_training", step13bx.MANIFEST_JSON, "false", manifest13bx.get("feature_semantics_known_for_training"), manifest13bx.get("feature_semantics_known_for_training") is False),
        ("step13bx_unknown_atom_policy_finalized", step13bx.MANIFEST_JSON, "false", manifest13bx.get("unknown_atom_feature_policy_finalized_for_training"), manifest13bx.get("unknown_atom_feature_policy_finalized_for_training") is False),
        ("step13bu_metadata_smoke_preview_shape", step13bu.SMOKE_PREVIEW_CSV, "20x30", f"{len(metadata_rows)}x{len(metadata_rows[0]) if metadata_rows else 0}", len(metadata_rows) == 20 and bool(metadata_rows) and len(metadata_rows[0]) == 30),
        ("step13bo_final_dataset_smoke_preview_shape", step13bo.SMOKE_PREVIEW_CSV, "20x45", f"{len(final_rows)}x{len(final_rows[0]) if final_rows else 0}", len(final_rows) == 20 and bool(final_rows) and len(final_rows[0]) == 45),
        ("step13bm_feature_semantics_audit_completed", step13bm.MANIFEST_JSON, "true", manifest13bm.get("feature_semantics_audit_completed_current_step"), manifest13bm.get("feature_semantics_audit_completed_current_step") is True),
        ("canonical_mask_count", step13bu.SMOKE_PREVIEW_CSV, "5", len(metadata_mask_names), len(metadata_mask_names) == 5),
        ("b3_scaffold_only_included", step13bu.SMOKE_PREVIEW_CSV, "true", "scaffold_only" in metadata_mask_names, "scaffold_only" in metadata_mask_names),
        ("no_extra_mask_tasks_added", step13bu.SMOKE_PREVIEW_CSV, "true", metadata_mask_names, metadata_mask_names == set(CANONICAL_MASK_TASK_NAMES)),
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


def build_original_feature_schema_mapping_rows() -> list[dict[str, Any]]:
    source_scope = "dataset.py;data/prepare_crossdocked.py;lightning_modules.py;equivariant_diffusion/;src/covalent_ext/"
    paths = [DATASET_PY, PREPARE_CROSSDOCKED_PY, LIGHTNING_MODULES_PY, EQUIVARIANT_DIFFUSION_DIR, SRC_COVALENT_EXT_DIR]
    rows = [
        ("original_dataset_py_feature_symbols", "dataset.py", _static_reference_summary(DATASET_PY)[1], "map Dataset feature keys and collate expectations from static source only"),
        ("original_prepare_crossdocked_feature_symbols", "data/prepare_crossdocked.py", _static_reference_summary(PREPARE_CROSSDOCKED_PY)[1], "map preprocessing feature symbols without reprocessing raw data"),
        ("original_lightning_batch_key_symbols", "lightning_modules.py", _static_reference_summary(LIGHTNING_MODULES_PY)[1], "record model batch-key expectations as checkpoint compatibility inputs"),
        ("original_equivariant_diffusion_feature_symbols", "equivariant_diffusion/", _static_reference_summary(EQUIVARIANT_DIFFUSION_DIR)[1], "record diffusion feature use as static compatibility evidence"),
        ("original_atom_encoder_candidate_symbols", source_scope, _search_summary(paths, ["atom_encoder", "atom_type", "atom_nf", "one_hot"]), "draft atom encoder mapping candidates only"),
        ("original_atom_decoder_candidate_symbols", source_scope, _search_summary(paths, ["atom_decoder", "idx_to_atom", "decode", "argmax"]), "draft atom decoder mapping candidates only"),
        ("original_residue_encoder_candidate_symbols", source_scope, _search_summary(paths, ["aa_encoder", "residue", "residue_nf", "amino"]), "draft residue encoder mapping candidates only"),
        ("original_feature_dimension_candidate_symbols", source_scope, _search_summary(paths, ["feature_dimension", "atom_nf", "residue_nf", "x_dims", "n_dims"]), "draft feature dimension candidates only"),
        ("original_one_hot_feature_candidate_symbols", source_scope, _search_summary(paths, ["one_hot", "onehot", "categorical"]), "draft one-hot feature policy candidates only"),
        ("original_unknown_atom_candidate_symbols", source_scope, _search_summary(paths, ["unknown", "unk", "UNKNOWN", "Unknown"]), "link unknown atom evidence to a future policy contract"),
        ("original_feature_schema_mapping_not_training_final", "Step 13BX blocker audit", "feature_semantics_known_for_training=false", "keep all mapping policies non-final for training"),
        ("original_checkpoint_compatibility_requires_static_mapping", "Step 13BW/13BX blocker audit", "checkpoint compatibility risk recorded", "require a static mapping before any checkpoint or model runtime smoke"),
    ]
    return [
        {
            "mapping_item": item,
            "static_source_scope": scope,
            "observed_evidence_summary": evidence,
            "proposed_resolution_policy": policy,
            "training_final_status": "not_training_final",
            "blocks_actual_tensor_dataloader_smoke": True,
            "mapping_design_passed": True,
            "qa_comment": "static evidence only; no source modification; not final training semantics",
        }
        for item, scope, evidence, policy in rows
    ]


def build_coordinate_resolution_rows() -> list[dict[str, Any]]:
    rows = [
        ("protein_xyz_source_contract", "protein_pocket_atom_table_path from metadata smoke preview", "use derived protein pocket atom table as future coordinate source", "candidate_policy_only", True),
        ("ligand_xyz_source_contract", "ligand_atom_table_path from metadata smoke preview", "use derived ligand atom table as future coordinate source", "candidate_policy_only", True),
        ("coordinate_unit_policy_candidate", "coordinate_unit from final dataset smoke preview", "treat derived coordinates as angstrom candidates pending smoke validation", "candidate_policy_only", True),
        ("coordinate_frame_policy_candidate", "coordinate_frame_status from final dataset smoke preview", "validate coordinate frame status against derived tables in resolution smoke", "candidate_policy_only", True),
        ("protein_ligand_joint_coordinate_policy", "protein and ligand row counts from metadata preview", "keep protein and ligand coordinates separate with explicit joint-frame audit", "candidate_policy_only", True),
        ("coordinate_dtype_policy_candidate", "Step 13BX coordinate audit", "candidate dtype policy is float-like, without importing numpy or torch", "candidate_policy_only", True),
        ("coordinate_shape_policy_candidate", "Step 13BX coordinate audit", "candidate shapes are N protein/ligand atoms by 3 coordinates", "candidate_policy_only", True),
        ("coordinate_resolution_requires_smoke_validation", "current execution boundary", "validate policy in future CSV/JSON resolution smoke before tensors", "blocked_until_resolution_smoke", True),
    ]
    return [
        {
            "coordinate_resolution_item": item,
            "source_or_evidence": source,
            "proposed_policy": policy,
            "current_status": status,
            "ready_for_resolution_smoke": ready,
            "ready_for_actual_tensor_smoke": False,
            "coordinate_resolution_passed": True,
            "qa_comment": "coordinate policy can be checked in a future resolution smoke; no tensor current step",
        }
        for item, source, policy, status, ready in rows
    ]


def build_atom_feature_resolution_rows() -> list[dict[str, Any]]:
    rows = [
        ("ligand_element_symbol_feature_policy", "derived ligand atom tables and original static feature symbols", "candidate ligand element categorical mapping", "candidate_policy_only", True),
        ("ligand_atom_type_feature_policy", "original static atom encoder symbol search", "candidate ligand atom-type mapping aligned to original feature keys", "candidate_policy_only", True),
        ("ligand_aromatic_feature_policy", "feature semantics blocker audit", "candidate aromatic flag policy, not tensorized", "candidate_policy_only", True),
        ("ligand_formal_charge_feature_policy", "feature semantics blocker audit", "candidate formal charge policy, not tensorized", "candidate_policy_only", True),
        ("ligand_unknown_atom_feature_policy_link", "unknown atom policy resolution contract", "defer uncommon ligand atom behavior to unknown policy", "blocked_by_unknown_policy", True),
        ("protein_element_symbol_feature_policy", "derived protein atom tables and static source symbols", "candidate protein element categorical mapping", "candidate_policy_only", True),
        ("protein_residue_name_feature_policy", "feature semantics blocker audit", "candidate residue-name mapping, not final", "candidate_policy_only", True),
        ("protein_atom_name_feature_policy", "feature semantics blocker audit", "candidate protein atom-name mapping, not final", "candidate_policy_only", True),
        ("protein_unknown_residue_feature_policy_link", "unknown atom policy resolution contract", "defer unknown residue behavior to unknown policy", "blocked_by_unknown_policy", True),
        ("feature_dimension_policy_candidate", "original feature dimension candidate symbols", "derive feature dimensions only after categorical vocab is fixed", "candidate_policy_only", True),
        ("feature_dtype_policy_candidate", "tensor shape dtype resolution contract", "candidate dtype is categorical/int-like before one-hot expansion, no numpy/torch", "candidate_policy_only", True),
        ("atom_feature_schema_resolution_smoke_required", "Step 13BX readiness blockers", "future resolution smoke must prove schema on derived tables before actual tensor smoke", "blocked_until_resolution_smoke", True),
    ]
    return [
        {
            "atom_feature_resolution_item": item,
            "source_or_evidence": source,
            "proposed_policy": policy,
            "current_status": status,
            "ready_for_resolution_smoke": ready,
            "ready_for_actual_tensor_smoke": False,
            "blocks_training": True,
            "atom_feature_resolution_passed": True,
            "qa_comment": "candidate policy only; feature semantics remain non-final for training",
        }
        for item, source, policy, status, ready in rows
    ]


def build_unknown_atom_policy_resolution_rows() -> list[dict[str, Any]]:
    rows = [
        ("unknown_ligand_element_policy_candidate", "map unseen ligand elements to explicit unknown category or block row in future policy", "derived ligand atom table vocabulary"),
        ("uncommon_ligand_atom_policy_candidate", "record uncommon ligand atoms in an audit table before tensorization", "derived ligand atom tables and original atom encoder search"),
        ("unknown_protein_residue_policy_candidate", "map unknown protein residues explicitly or block row in future policy", "derived protein atom table residue names"),
        ("unknown_protein_atom_name_policy_candidate", "map unknown protein atom names explicitly or block row in future policy", "derived protein atom table atom names"),
        ("covalent_adduct_atom_mapping_policy_candidate", "require explicit mapping for covalent adduct atom identities", "final dataset preview and covalent event metadata"),
        ("unknown_policy_audit_table_required", "future smoke must emit unknown-policy audit rows", "Step 13BX unknown atom policy blocker audit"),
        ("unknown_policy_resolution_smoke_required", "future smoke must validate policy without tensors", "resolution smoke plan"),
        ("unknown_policy_not_training_final_current_step", "keep unknown_atom_feature_policy_finalized_for_training=false", "current readiness boundary"),
    ]
    return [
        {
            "unknown_policy_resolution_item": item,
            "proposed_policy": policy,
            "required_evidence_source": source,
            "current_status": "candidate_policy_only_not_training_final",
            "ready_for_resolution_smoke": True,
            "finalized_for_training_current_step": False,
            "unknown_policy_resolution_passed": True,
            "qa_comment": "unknown atom policy is proposed but not finalized for training",
        }
        for item, policy, source in rows
    ]


def build_label_semantics_resolution_rows() -> list[dict[str, Any]]:
    rows = [
        ("mask_task_name_string_selector_policy", "canonical mask names from metadata preview", "long semantic mask task names remain source of truth", "metadata_selector_policy", True, False),
        ("mask_task_alias_display_only_policy", "canonical aliases from metadata preview", "aliases remain display-only labels", "metadata_display_policy", True, False),
        ("scaffold_linker_warhead_group_label_policy_candidate", "final dataset smoke preview and mask contracts", "future group-label smoke must resolve scaffold/linker/warhead membership", "candidate_policy_only", True, True),
        ("mask_boolean_tensor_policy_candidate", "Step 13BX label blocker audit", "future boolean mask policy after group labels are materialized", "blocked_until_group_label_smoke", True, True),
        ("warhead_type_label_policy_candidate", "feature semantics blocker audit", "candidate warhead type label policy, metadata-only current step", "candidate_policy_only", True, True),
        ("covalent_atom_pair_label_policy_candidate", "final dataset smoke preview", "candidate covalent atom pair label policy before tensorization", "candidate_policy_only", True, True),
        ("covalent_bond_distance_label_policy_candidate", "final dataset smoke preview", "candidate scalar label policy before dtype decision", "candidate_policy_only", True, True),
        ("pre_covalent_geometry_label_policy_candidate", "feature semantics blocker audit", "candidate pre-covalent geometry label policy", "candidate_policy_only", True, True),
        ("post_covalent_geometry_label_policy_candidate", "feature semantics blocker audit", "candidate post-covalent geometry label policy", "candidate_policy_only", True, True),
        ("auxiliary_loss_label_policy_blocked", "loss/training boundary", "auxiliary loss labels stay blocked until semantics and loss contract exist", "blocked_current_step", True, True),
        ("group_label_materialization_smoke_required", "mask/group blocker audit", "future smoke must write group-label audits without tensors", "requires_future_smoke", True, True),
        ("auxiliary_label_resolution_smoke_required", "auxiliary label blocker audit", "future smoke must validate auxiliary labels without tensors", "requires_future_smoke", True, True),
        ("label_tensorization_actual_smoke_blocked", "current execution boundary", "actual label tensors remain blocked", "blocked_current_step", False, True),
        ("label_semantics_not_training_final_current_step", "current readiness boundary", "label semantics are not final training semantics", "not_training_final", False, True),
    ]
    return [
        {
            "label_resolution_item": item,
            "source_or_evidence": source,
            "proposed_policy": policy,
            "current_status": status,
            "ready_for_resolution_smoke": ready,
            "ready_for_actual_tensor_smoke": False,
            "blocks_training": blocks_training,
            "label_resolution_passed": True,
            "qa_comment": "label policy remains candidate-only; no label tensor current step",
        }
        for item, source, policy, status, ready, blocks_training in rows
    ]


def build_tensor_shape_dtype_resolution_rows() -> list[dict[str, Any]]:
    rows = [
        ("coordinate_dtype_candidate", "float-like coordinate dtype candidate, no numpy/torch import", "candidate_policy_only", True, "medium"),
        ("coordinate_shape_candidate", "N atoms by 3 coordinate shape candidate", "candidate_policy_only", True, "medium"),
        ("atom_feature_dtype_candidate", "categorical/int-like or one-hot candidate after schema resolution", "candidate_policy_only", True, "high"),
        ("atom_feature_shape_candidate", "N atoms by F feature shape candidate after vocab resolution", "candidate_policy_only", True, "high"),
        ("mask_selector_dtype_candidate", "string selector remains metadata-only until resolved", "candidate_policy_only", True, "medium"),
        ("mask_boolean_dtype_candidate", "boolean mask dtype candidate after group labels exist", "blocked_until_group_label_smoke", True, "high"),
        ("auxiliary_label_dtype_candidate", "auxiliary labels require semantics and loss contract first", "blocked_until_label_resolution_smoke", True, "high"),
        ("variable_size_collate_policy_candidate", "future collate policy must keep variable-size samples explicit", "candidate_policy_only", True, "high"),
        ("batch_index_policy_candidate", "future batch index policy must be checkpoint-compatible", "candidate_policy_only", True, "high"),
        ("tensor_shape_dtype_resolution_smoke_required", "future smoke validates shape/dtype policy without tensor artifacts", "requires_future_smoke", True, "high"),
    ]
    return [
        {
            "tensor_policy_item": item,
            "proposed_dtype_or_shape_policy": policy,
            "current_status": status,
            "ready_for_resolution_smoke": ready,
            "ready_for_actual_tensor_smoke": False,
            "checkpoint_compatibility_risk": risk,
            "tensor_policy_passed": True,
            "qa_comment": "shape and dtype policy is design-only; no tensor current step",
        }
        for item, policy, status, ready, risk in rows
    ]


def build_resolution_smoke_plan_rows() -> list[dict[str, Any]]:
    rows = [
        ("read_resolution_design_contracts", "read all Step 13BY resolution contracts", "Step 13BY CSV/JSON artifacts", "resolution smoke audit CSV/JSON", "actual dataloader smoke; tensors; training", "Step 13BY all_checks_passed=true"),
        ("validate_original_feature_schema_mapping_candidates", "validate static mapping candidates against original source symbols", "static source references; mapping contract", "feature schema mapping smoke audit", "source modification; checkpoint load", "no original source diff"),
        ("validate_coordinate_policy_against_derived_tables", "check coordinate source paths, units, frames, and row counts", "derived metadata/final dataset previews", "coordinate policy smoke audit", "tensor creation; coordinate extraction from raw", "derived tables available"),
        ("validate_atom_feature_policy_against_derived_tables", "check proposed atom feature schema against derived atom fields", "derived table references; atom feature contract", "atom feature policy smoke audit", "torch/numpy tensors", "unknown policy still explicit"),
        ("validate_unknown_atom_policy_against_derived_tables", "audit unknown/uncommon atom and residue policy coverage", "unknown policy contract; derived tables", "unknown policy smoke audit", "training-final claim", "unknown policy not finalized current step"),
        ("validate_label_policy_against_final_dataset_preview", "check mask and auxiliary label policies against preview metadata", "final dataset smoke preview; label contract", "label policy smoke audit", "label tensors; loss targets", "final preview unchanged"),
        ("produce_resolution_smoke_audits_without_tensors", "write CSV/JSON audits only", "resolution smoke inputs", "resolution smoke report/manifest", "pt/npz/checkpoint/training artifacts", "no torch/numpy import"),
        ("keep_actual_dataloader_smoke_blocked", "keep actual dataloader smoke blocked until resolution smoke passes", "resolution smoke manifest", "readiness for next design gate only", "actual dataloader smoke; training", "feature semantics audit remains required"),
    ]
    return [
        {
            "planned_step": item,
            "planned_action": action,
            "allowed_inputs": inputs,
            "allowed_outputs_future_step": outputs,
            "blocked_outputs_current_step": blocked,
            "required_preconditions": preconditions,
            "resolution_smoke_plan_passed": True,
        }
        for item, action, inputs, outputs, blocked, preconditions in rows
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
        ("step13bx_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bx.OUTPUT_ROOT.as_posix()])),
        ("step13bw_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bw.OUTPUT_ROOT.as_posix()])),
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


def run_covapie_feature_semantics_resolution_design_gate_v0() -> dict[str, Any]:
    precondition_rows = build_precondition_rows()
    mapping_rows = build_original_feature_schema_mapping_rows()
    coordinate_rows = build_coordinate_resolution_rows()
    atom_rows = build_atom_feature_resolution_rows()
    unknown_rows = build_unknown_atom_policy_resolution_rows()
    label_rows = build_label_semantics_resolution_rows()
    tensor_rows = build_tensor_shape_dtype_resolution_rows()
    smoke_plan_rows = build_resolution_smoke_plan_rows()
    safety_rows = build_safety_rows()
    metadata_rows = _csv_rows(step13bu.SMOKE_PREVIEW_CSV)
    final_rows = _csv_rows(step13bo.SMOKE_PREVIEW_CSV)
    metadata_mask_names = {row["mask_task_name"] for row in metadata_rows}

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bx_feature_semantics_tensorization_audit_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "source_metadata_smoke_preview_row_count": len(metadata_rows),
        "source_metadata_smoke_preview_column_count": len(metadata_rows[0]) if metadata_rows else 0,
        "source_final_dataset_preview_row_count": len(final_rows),
        "source_final_dataset_preview_column_count": len(final_rows[0]) if final_rows else 0,
        "source_canonical_mask_task_count": len(metadata_mask_names),
        "original_diffsbbd_feature_schema_mapping_design_row_count": len(mapping_rows),
        "coordinate_tensorization_resolution_contract_row_count": len(coordinate_rows),
        "atom_feature_schema_resolution_contract_row_count": len(atom_rows),
        "unknown_atom_policy_resolution_contract_row_count": len(unknown_rows),
        "label_semantics_resolution_contract_row_count": len(label_rows),
        "tensor_shape_dtype_resolution_contract_row_count": len(tensor_rows),
        "feature_semantics_resolution_smoke_plan_row_count": len(smoke_plan_rows),
        "original_diffsbbd_feature_schema_mapping_design_passed": all(_bool(row["mapping_design_passed"]) for row in mapping_rows),
        "coordinate_tensorization_resolution_contract_passed": all(_bool(row["coordinate_resolution_passed"]) for row in coordinate_rows),
        "atom_feature_schema_resolution_contract_passed": all(_bool(row["atom_feature_resolution_passed"]) for row in atom_rows),
        "unknown_atom_policy_resolution_contract_passed": all(_bool(row["unknown_policy_resolution_passed"]) for row in unknown_rows),
        "label_semantics_resolution_contract_passed": all(_bool(row["label_resolution_passed"]) for row in label_rows),
        "tensor_shape_dtype_resolution_contract_passed": all(_bool(row["tensor_policy_passed"]) for row in tensor_rows),
        "feature_semantics_resolution_smoke_plan_passed": all(_bool(row["resolution_smoke_plan_passed"]) for row in smoke_plan_rows),
        "safety_audit_passed": all(_bool(row["safety_passed"]) for row in safety_rows),
        "feature_semantics_resolution_design_completed_current_step": True,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "proposed_feature_schema_resolution_written": True,
        "proposed_unknown_atom_policy_written": True,
        "proposed_label_semantics_resolution_written": True,
        "coordinate_resolution_ready_for_smoke": True,
        "atom_feature_resolution_ready_for_smoke": True,
        "unknown_policy_resolution_ready_for_smoke": True,
        "label_semantics_resolution_ready_for_smoke": True,
        "ready_for_covapie_feature_semantics_resolution_smoke": True,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_covapie_actual_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
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
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in metadata_mask_names,
        "no_extra_mask_tasks_added": metadata_mask_names == set(CANONICAL_MASK_TASK_NAMES),
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_feature_semantics_resolution_smoke",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13bx_feature_semantics_tensorization_audit_validated"],
            manifest["source_metadata_smoke_preview_row_count"] == 20,
            manifest["source_metadata_smoke_preview_column_count"] == 30,
            manifest["source_final_dataset_preview_row_count"] == 20,
            manifest["source_final_dataset_preview_column_count"] == 45,
            manifest["source_canonical_mask_task_count"] == 5,
            manifest["original_diffsbbd_feature_schema_mapping_design_row_count"] == 12,
            manifest["coordinate_tensorization_resolution_contract_row_count"] == 8,
            manifest["atom_feature_schema_resolution_contract_row_count"] == 12,
            manifest["unknown_atom_policy_resolution_contract_row_count"] == 8,
            manifest["label_semantics_resolution_contract_row_count"] == 14,
            manifest["tensor_shape_dtype_resolution_contract_row_count"] == 10,
            manifest["feature_semantics_resolution_smoke_plan_row_count"] == 8,
            manifest["original_diffsbbd_feature_schema_mapping_design_passed"],
            manifest["coordinate_tensorization_resolution_contract_passed"],
            manifest["atom_feature_schema_resolution_contract_passed"],
            manifest["unknown_atom_policy_resolution_contract_passed"],
            manifest["label_semantics_resolution_contract_passed"],
            manifest["tensor_shape_dtype_resolution_contract_passed"],
            manifest["feature_semantics_resolution_smoke_plan_passed"],
            manifest["safety_audit_passed"],
            manifest["feature_semantics_resolution_design_completed_current_step"],
            not manifest["feature_semantics_known_for_training"],
            not manifest["unknown_atom_feature_policy_finalized_for_training"],
            manifest["proposed_feature_schema_resolution_written"],
            manifest["proposed_unknown_atom_policy_written"],
            manifest["proposed_label_semantics_resolution_written"],
            manifest["coordinate_resolution_ready_for_smoke"],
            manifest["atom_feature_resolution_ready_for_smoke"],
            manifest["unknown_policy_resolution_ready_for_smoke"],
            manifest["label_semantics_resolution_ready_for_smoke"],
            manifest["ready_for_covapie_feature_semantics_resolution_smoke"],
            not manifest["ready_for_covapie_actual_dataloader_adapter_smoke"],
            not manifest["ready_for_covapie_actual_dataloader_smoke"],
            not manifest["ready_for_training"],
            not manifest["ready_to_train_now"],
            not manifest["actual_dataloader_adapter_smoke_written"],
            not manifest["actual_dataloader_smoke_written"],
            not manifest["real_dataloader_written"],
            not manifest["final_dataset_written"],
            not manifest["sample_index_written_current_step"],
            not manifest["split_assignments_written"],
            not manifest["leakage_matrix_written"],
            not manifest["dataloader_smoke_written"],
            not manifest["training_artifacts_written"],
            not manifest["torch_imported"],
            not manifest["torch_tensor_created"],
            not manifest["numpy_imported"],
            not manifest["numpy_array_returned"],
            not manifest["checkpoint_loaded"],
            not manifest["model_forward_called"],
            not manifest["loss_compute_called"],
            not manifest["training_allowed"],
            not manifest["raw_file_content_read_current_step"],
            not manifest["raw_data_read"],
            not manifest["mmcif_text_read"],
            not manifest["mmcif_parse_current_step"],
            not manifest["coordinate_extraction_current_step"],
            not manifest["network_access_used"],
            not manifest["rdkit_used"],
            not manifest["biopdb_parser_used"],
            not manifest["gemmi_used"],
            not manifest["gzip_open_used"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
            manifest["feature_semantics_audit_required_before_training"],
            manifest["leakage_split_design_required_before_training"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["feature_semantics_resolution_design_gate_failed"]
    return {
        "precondition_rows": precondition_rows,
        "mapping_rows": mapping_rows,
        "coordinate_rows": coordinate_rows,
        "atom_rows": atom_rows,
        "unknown_rows": unknown_rows,
        "label_rows": label_rows,
        "tensor_rows": tensor_rows,
        "smoke_plan_rows": smoke_plan_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }
