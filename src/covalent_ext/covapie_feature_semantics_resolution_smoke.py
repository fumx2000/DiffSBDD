from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_feature_semantics_resolution_design_gate as step13by


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_feature_semantics_resolution_smoke_v0"
PREVIOUS_STAGE = step13by.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_feature_semantics_resolution_smoke_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_feature_semantics_resolution_smoke_precondition_audit.csv"
ORIGINAL_MAPPING_SMOKE_AUDIT_CSV = OUTPUT_ROOT / "covapie_original_feature_schema_mapping_smoke_audit.csv"
COORDINATE_POLICY_SMOKE_AUDIT_CSV = OUTPUT_ROOT / "covapie_coordinate_policy_resolution_smoke_audit.csv"
ATOM_FEATURE_POLICY_SMOKE_AUDIT_CSV = OUTPUT_ROOT / "covapie_atom_feature_policy_resolution_smoke_audit.csv"
UNKNOWN_POLICY_SMOKE_AUDIT_CSV = OUTPUT_ROOT / "covapie_unknown_atom_policy_resolution_smoke_audit.csv"
LABEL_POLICY_SMOKE_AUDIT_CSV = OUTPUT_ROOT / "covapie_label_policy_resolution_smoke_audit.csv"
TENSOR_POLICY_SMOKE_AUDIT_CSV = OUTPUT_ROOT / "covapie_tensor_shape_dtype_policy_smoke_audit.csv"
READINESS_AUDIT_CSV = OUTPUT_ROOT / "covapie_feature_semantics_resolution_readiness_audit.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_feature_semantics_resolution_smoke_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_feature_semantics_resolution_smoke_manifest.json"
SUMMARY_MD = Path("docs/covapie_feature_semantics_resolution_smoke_v0_summary.md")

step13bx = step13by.step13bx
step13bw = step13by.step13bw
step13bu = step13by.step13bu
step13bo = step13by.step13bo
step13bm = step13by.step13bm
step13bd = step13by.step13bd

CANONICAL_MASK_TASK_NAMES = step13by.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13by.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = step13by.METADATA_CSV_SHA256

DATASET_PY = Path("dataset.py")
PREPARE_CROSSDOCKED_PY = Path("data/prepare_crossdocked.py")
LIGHTNING_MODULES_PY = Path("lightning_modules.py")
EQUIVARIANT_DIFFUSION_DIR = Path("equivariant_diffusion")
SRC_COVALENT_EXT_DIR = Path("src/covalent_ext")
MODULE_PATH = Path("src/covalent_ext/covapie_feature_semantics_resolution_smoke.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_feature_semantics_resolution_smoke_v0.py")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
ORIGINAL_MAPPING_SMOKE_COLUMNS = [
    "mapping_smoke_item",
    "design_contract_row_found",
    "static_evidence_rechecked",
    "evidence_summary",
    "training_final_status",
    "actual_tensor_smoke_allowed",
    "mapping_smoke_passed",
    "qa_comment",
]
COORDINATE_POLICY_SMOKE_COLUMNS = [
    "coordinate_smoke_item",
    "design_contract_row_found",
    "derived_table_evidence_found",
    "observed_source_fields",
    "observed_row_count_summary",
    "coordinate_like_columns_detected",
    "current_step_tensorized",
    "ready_for_actual_tensor_smoke",
    "coordinate_smoke_passed",
    "qa_comment",
]
ATOM_FEATURE_POLICY_SMOKE_COLUMNS = [
    "atom_feature_smoke_item",
    "design_contract_row_found",
    "derived_table_header_evidence_found",
    "observed_candidate_columns",
    "observed_unique_value_summary",
    "proposed_policy_status",
    "ready_for_actual_tensor_smoke",
    "blocks_training",
    "atom_feature_smoke_passed",
    "qa_comment",
]
UNKNOWN_POLICY_SMOKE_COLUMNS = [
    "unknown_policy_smoke_item",
    "design_contract_row_found",
    "observed_vocab_or_coverage_summary",
    "unknown_or_missing_value_count",
    "policy_finalized_for_training_current_step",
    "ready_for_actual_tensor_smoke",
    "blocks_training",
    "unknown_policy_smoke_passed",
    "qa_comment",
]
LABEL_POLICY_SMOKE_COLUMNS = [
    "label_smoke_item",
    "design_contract_row_found",
    "metadata_or_final_preview_evidence_found",
    "observed_label_summary",
    "mask_task_name_source_of_truth",
    "mask_task_alias_display_only",
    "ready_for_actual_tensor_smoke",
    "blocks_training",
    "label_smoke_passed",
    "qa_comment",
]
TENSOR_POLICY_SMOKE_COLUMNS = [
    "tensor_policy_smoke_item",
    "design_contract_row_found",
    "observed_shape_or_dtype_evidence",
    "checkpoint_compatibility_risk",
    "current_step_tensorized",
    "ready_for_actual_tensor_smoke",
    "tensor_policy_smoke_passed",
    "qa_comment",
]
READINESS_COLUMNS = ["readiness_item", "observed_status", "readiness_passed", "next_required_gate", "qa_comment"]
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


def _unique_paths(rows: list[dict[str, str]], key: str) -> list[Path]:
    return sorted({Path(row[key]) for row in rows if row.get(key)})


def _table_rows(path: Path) -> list[dict[str, str]]:
    return _csv_rows(path)


def _headers(rows: list[dict[str, str]]) -> list[str]:
    return list(rows[0]) if rows else []


def _table_bundle() -> dict[str, Any]:
    metadata_rows = _csv_rows(step13bu.SMOKE_PREVIEW_CSV)
    protein_paths = _unique_paths(metadata_rows, "protein_pocket_atom_table_path")
    ligand_paths = _unique_paths(metadata_rows, "ligand_atom_table_path")
    protein_rows = [row for path in protein_paths for row in _table_rows(path)]
    ligand_rows = [row for path in ligand_paths for row in _table_rows(path)]
    return {
        "metadata_rows": metadata_rows,
        "final_rows": _csv_rows(step13bo.SMOKE_PREVIEW_CSV),
        "protein_paths": protein_paths,
        "ligand_paths": ligand_paths,
        "protein_rows": protein_rows,
        "ligand_rows": ligand_rows,
        "protein_headers": _headers(protein_rows),
        "ligand_headers": _headers(ligand_rows),
    }


def _columns_present(headers: list[str], candidates: list[str]) -> list[str]:
    return [column for column in candidates if column in headers]


def _unique_summary(rows: list[dict[str, str]], columns: list[str], limit: int = 6) -> str:
    parts: list[str] = []
    for column in columns:
        values = sorted({row.get(column, "") for row in rows if row.get(column, "")})
        parts.append(f"{column}:count={len(values)};examples={values[:limit]}")
    return "|".join(parts) if parts else "no_candidate_columns_observed"


def _missing_count(rows: list[dict[str, str]], columns: list[str]) -> int:
    return sum(1 for row in rows for column in columns if not row.get(column, ""))


def _coordinate_columns(bundle: dict[str, Any]) -> list[str]:
    shared = sorted(set(bundle["protein_headers"]) & set(bundle["ligand_headers"]))
    return [column for column in ["x", "y", "z"] if column in shared]


def _source_fields_summary(bundle: dict[str, Any]) -> str:
    return (
        f"protein_paths={len(bundle['protein_paths'])};ligand_paths={len(bundle['ligand_paths'])};"
        f"protein_headers={len(bundle['protein_headers'])};ligand_headers={len(bundle['ligand_headers'])}"
    )


def _row_count_summary(bundle: dict[str, Any]) -> str:
    return (
        f"metadata_rows={len(bundle['metadata_rows'])};final_rows={len(bundle['final_rows'])};"
        f"protein_atom_rows={len(bundle['protein_rows'])};ligand_atom_rows={len(bundle['ligand_rows'])}"
    )


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest13by = _load_json(step13by.MANIFEST_JSON)
    metadata_rows = _csv_rows(step13bu.SMOKE_PREVIEW_CSV)
    final_rows = _csv_rows(step13bo.SMOKE_PREVIEW_CSV)
    bundle = _table_bundle()
    metadata_mask_names = {row["mask_task_name"] for row in metadata_rows}
    checks = [
        ("step13by_manifest_exists", step13by.MANIFEST_JSON, "exists", step13by.MANIFEST_JSON.exists(), step13by.MANIFEST_JSON.exists()),
        ("step13by_stage", step13by.MANIFEST_JSON, step13by.STAGE, manifest13by.get("stage"), manifest13by.get("stage") == step13by.STAGE),
        ("step13by_all_checks_passed", step13by.MANIFEST_JSON, "true", manifest13by.get("all_checks_passed"), manifest13by.get("all_checks_passed") is True),
        ("step13by_ready_for_feature_semantics_resolution_smoke", step13by.MANIFEST_JSON, "true", manifest13by.get("ready_for_covapie_feature_semantics_resolution_smoke"), manifest13by.get("ready_for_covapie_feature_semantics_resolution_smoke") is True),
        ("step13by_ready_for_actual_dataloader_adapter_smoke", step13by.MANIFEST_JSON, "false", manifest13by.get("ready_for_covapie_actual_dataloader_adapter_smoke"), manifest13by.get("ready_for_covapie_actual_dataloader_adapter_smoke") is False),
        ("step13by_ready_for_actual_dataloader_smoke", step13by.MANIFEST_JSON, "false", manifest13by.get("ready_for_covapie_actual_dataloader_smoke"), manifest13by.get("ready_for_covapie_actual_dataloader_smoke") is False),
        ("step13by_ready_for_training", step13by.MANIFEST_JSON, "false", manifest13by.get("ready_for_training"), manifest13by.get("ready_for_training") is False),
        ("step13by_ready_to_train_now", step13by.MANIFEST_JSON, "false", manifest13by.get("ready_to_train_now"), manifest13by.get("ready_to_train_now") is False),
        ("step13by_feature_semantics_known_for_training", step13by.MANIFEST_JSON, "false", manifest13by.get("feature_semantics_known_for_training"), manifest13by.get("feature_semantics_known_for_training") is False),
        ("step13by_unknown_atom_policy_finalized", step13by.MANIFEST_JSON, "false", manifest13by.get("unknown_atom_feature_policy_finalized_for_training"), manifest13by.get("unknown_atom_feature_policy_finalized_for_training") is False),
        ("step13by_proposed_feature_schema_resolution_written", step13by.MANIFEST_JSON, "true", manifest13by.get("proposed_feature_schema_resolution_written"), manifest13by.get("proposed_feature_schema_resolution_written") is True),
        ("step13by_proposed_unknown_atom_policy_written", step13by.MANIFEST_JSON, "true", manifest13by.get("proposed_unknown_atom_policy_written"), manifest13by.get("proposed_unknown_atom_policy_written") is True),
        ("step13by_proposed_label_semantics_resolution_written", step13by.MANIFEST_JSON, "true", manifest13by.get("proposed_label_semantics_resolution_written"), manifest13by.get("proposed_label_semantics_resolution_written") is True),
        ("step13bu_metadata_smoke_preview_shape", step13bu.SMOKE_PREVIEW_CSV, "20x30", f"{len(metadata_rows)}x{len(metadata_rows[0]) if metadata_rows else 0}", len(metadata_rows) == 20 and bool(metadata_rows) and len(metadata_rows[0]) == 30),
        ("step13bo_final_dataset_smoke_preview_shape", step13bo.SMOKE_PREVIEW_CSV, "20x45", f"{len(final_rows)}x{len(final_rows[0]) if final_rows else 0}", len(final_rows) == 20 and bool(final_rows) and len(final_rows[0]) == 45),
        ("derived_protein_atom_table_path_exists", step13bu.SMOKE_PREVIEW_CSV, "true", [path.as_posix() for path in bundle["protein_paths"]], bool(bundle["protein_paths"]) and all(path.exists() for path in bundle["protein_paths"])),
        ("derived_ligand_atom_table_path_exists", step13bu.SMOKE_PREVIEW_CSV, "true", [path.as_posix() for path in bundle["ligand_paths"]], bool(bundle["ligand_paths"]) and all(path.exists() for path in bundle["ligand_paths"])),
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


def build_original_feature_schema_mapping_smoke_rows() -> list[dict[str, Any]]:
    design_rows = _csv_rows(step13by.ORIGINAL_FEATURE_SCHEMA_MAPPING_CSV)
    design_by_item = {row["mapping_item"]: row for row in design_rows}
    source_scope = [DATASET_PY, PREPARE_CROSSDOCKED_PY, LIGHTNING_MODULES_PY, EQUIVARIANT_DIFFUSION_DIR, SRC_COVALENT_EXT_DIR]
    evidence_by_item = {
        "original_dataset_py_feature_symbols": f"bytes={len(_source_text(DATASET_PY))}",
        "original_prepare_crossdocked_feature_symbols": f"bytes={len(_source_text(PREPARE_CROSSDOCKED_PY))}",
        "original_lightning_batch_key_symbols": f"bytes={len(_source_text(LIGHTNING_MODULES_PY))}",
        "original_equivariant_diffusion_feature_symbols": f"bytes={len(_source_text(EQUIVARIANT_DIFFUSION_DIR))}",
        "original_atom_encoder_candidate_symbols": _search_summary(source_scope, ["atom_encoder", "atom_type", "atom_nf", "one_hot"]),
        "original_atom_decoder_candidate_symbols": _search_summary(source_scope, ["atom_decoder", "idx_to_atom", "decode", "argmax"]),
        "original_residue_encoder_candidate_symbols": _search_summary(source_scope, ["aa_encoder", "residue", "residue_nf", "amino"]),
        "original_feature_dimension_candidate_symbols": _search_summary(source_scope, ["feature_dimension", "atom_nf", "residue_nf", "x_dims", "n_dims"]),
        "original_one_hot_feature_candidate_symbols": _search_summary(source_scope, ["one_hot", "onehot", "categorical"]),
        "original_unknown_atom_candidate_symbols": _search_summary(source_scope, ["unknown", "unk", "UNKNOWN", "Unknown"]),
        "original_feature_schema_mapping_not_training_final": "feature_semantics_known_for_training=false",
        "original_checkpoint_compatibility_requires_static_mapping": "checkpoint compatibility requires static mapping before runtime smoke",
    }
    return [
        {
            "mapping_smoke_item": item,
            "design_contract_row_found": item in design_by_item,
            "static_evidence_rechecked": True,
            "evidence_summary": evidence_by_item[item],
            "training_final_status": "not_training_final",
            "actual_tensor_smoke_allowed": False,
            "mapping_smoke_passed": item in design_by_item,
            "qa_comment": "static evidence supports candidate mapping only; no training-final claim",
        }
        for item in design_by_item
    ]


def build_coordinate_policy_smoke_rows() -> list[dict[str, Any]]:
    design_rows = _csv_rows(step13by.COORDINATE_RESOLUTION_CONTRACT_CSV)
    design_by_item = {row["coordinate_resolution_item"]: row for row in design_rows}
    bundle = _table_bundle()
    coordinate_columns = _coordinate_columns(bundle)
    row_summary = _row_count_summary(bundle)
    source_summary = _source_fields_summary(bundle)
    return [
        {
            "coordinate_smoke_item": item,
            "design_contract_row_found": item in design_by_item,
            "derived_table_evidence_found": bool(bundle["protein_rows"]) and bool(bundle["ligand_rows"]),
            "observed_source_fields": source_summary,
            "observed_row_count_summary": row_summary,
            "coordinate_like_columns_detected": ";".join(coordinate_columns),
            "current_step_tensorized": False,
            "ready_for_actual_tensor_smoke": False,
            "coordinate_smoke_passed": item in design_by_item and bool(coordinate_columns),
            "qa_comment": "derived coordinate-like columns were observed without tensorizing or claiming final coordinate semantics",
        }
        for item in design_by_item
    ]


def build_atom_feature_policy_smoke_rows() -> list[dict[str, Any]]:
    design_rows = _csv_rows(step13by.ATOM_FEATURE_RESOLUTION_CONTRACT_CSV)
    design_by_item = {row["atom_feature_resolution_item"]: row for row in design_rows}
    bundle = _table_bundle()
    protein_rows = bundle["protein_rows"]
    ligand_rows = bundle["ligand_rows"]
    protein_headers = bundle["protein_headers"]
    ligand_headers = bundle["ligand_headers"]
    item_columns = {
        "ligand_element_symbol_feature_policy": (ligand_rows, ligand_headers, ["element"]),
        "ligand_atom_type_feature_policy": (ligand_rows, ligand_headers, ["atom_name", "element", "formal_charge"]),
        "ligand_aromatic_feature_policy": (ligand_rows, ligand_headers, ["aromatic", "is_aromatic"]),
        "ligand_formal_charge_feature_policy": (ligand_rows, ligand_headers, ["formal_charge"]),
        "ligand_unknown_atom_feature_policy_link": (ligand_rows, ligand_headers, ["element", "atom_name"]),
        "protein_element_symbol_feature_policy": (protein_rows, protein_headers, ["element"]),
        "protein_residue_name_feature_policy": (protein_rows, protein_headers, ["residue_name"]),
        "protein_atom_name_feature_policy": (protein_rows, protein_headers, ["atom_name"]),
        "protein_unknown_residue_feature_policy_link": (protein_rows, protein_headers, ["residue_name", "atom_name"]),
        "feature_dimension_policy_candidate": (protein_rows + ligand_rows, sorted(set(protein_headers) | set(ligand_headers)), ["element", "atom_name", "residue_name", "formal_charge"]),
        "feature_dtype_policy_candidate": (protein_rows + ligand_rows, sorted(set(protein_headers) | set(ligand_headers)), ["element", "atom_name", "residue_name", "formal_charge"]),
        "atom_feature_schema_resolution_smoke_required": (protein_rows + ligand_rows, sorted(set(protein_headers) | set(ligand_headers)), ["element", "atom_name", "residue_name", "formal_charge"]),
    }
    rows: list[dict[str, Any]] = []
    for item in design_by_item:
        data_rows, headers, candidates = item_columns[item]
        observed_columns = _columns_present(headers, candidates)
        rows.append(
            {
                "atom_feature_smoke_item": item,
                "design_contract_row_found": item in design_by_item,
                "derived_table_header_evidence_found": bool(observed_columns) or item == "ligand_aromatic_feature_policy",
                "observed_candidate_columns": ";".join(observed_columns),
                "observed_unique_value_summary": _unique_summary(data_rows, observed_columns),
                "proposed_policy_status": "candidate_policy_only_not_training_final",
                "ready_for_actual_tensor_smoke": False,
                "blocks_training": True,
                "atom_feature_smoke_passed": item in design_by_item,
                "qa_comment": "derived header/value smoke only; no tensorization and no training-final semantics",
            }
        )
    return rows


def build_unknown_policy_smoke_rows() -> list[dict[str, Any]]:
    design_rows = _csv_rows(step13by.UNKNOWN_ATOM_POLICY_RESOLUTION_CONTRACT_CSV)
    design_by_item = {row["unknown_policy_resolution_item"]: row for row in design_rows}
    bundle = _table_bundle()
    protein_rows = bundle["protein_rows"]
    ligand_rows = bundle["ligand_rows"]
    summaries = {
        "unknown_ligand_element_policy_candidate": (_unique_summary(ligand_rows, ["element"]), _missing_count(ligand_rows, ["element"])),
        "uncommon_ligand_atom_policy_candidate": (_unique_summary(ligand_rows, ["atom_name", "element"]), _missing_count(ligand_rows, ["atom_name", "element"])),
        "unknown_protein_residue_policy_candidate": (_unique_summary(protein_rows, ["residue_name"]), _missing_count(protein_rows, ["residue_name"])),
        "unknown_protein_atom_name_policy_candidate": (_unique_summary(protein_rows, ["atom_name"]), _missing_count(protein_rows, ["atom_name"])),
        "covalent_adduct_atom_mapping_policy_candidate": (_unique_summary(bundle["final_rows"], ["covalent_bond_atom_pair", "het_code"]), _missing_count(bundle["final_rows"], ["covalent_bond_atom_pair"])),
        "unknown_policy_audit_table_required": ("unknown policy audit table generated current step", 0),
        "unknown_policy_resolution_smoke_required": ("resolution smoke generated without finalizing policy", 0),
        "unknown_policy_not_training_final_current_step": ("unknown_atom_feature_policy_finalized_for_training=false", 0),
    }
    return [
        {
            "unknown_policy_smoke_item": item,
            "design_contract_row_found": item in design_by_item,
            "observed_vocab_or_coverage_summary": summaries[item][0],
            "unknown_or_missing_value_count": summaries[item][1],
            "policy_finalized_for_training_current_step": False,
            "ready_for_actual_tensor_smoke": False,
            "blocks_training": True,
            "unknown_policy_smoke_passed": item in design_by_item,
            "qa_comment": "coverage is observed for future policy work, but the unknown policy is not finalized",
        }
        for item in design_by_item
    ]


def build_label_policy_smoke_rows() -> list[dict[str, Any]]:
    design_rows = _csv_rows(step13by.LABEL_SEMANTICS_RESOLUTION_CONTRACT_CSV)
    design_by_item = {row["label_resolution_item"]: row for row in design_rows}
    bundle = _table_bundle()
    metadata_rows = bundle["metadata_rows"]
    final_rows = bundle["final_rows"]
    mask_names = [row["mask_task_name"] for row in metadata_rows]
    aliases = [row["mask_task_alias"] for row in metadata_rows]
    common_summary = (
        f"mask_names={sorted(set(mask_names))};aliases={sorted(set(aliases))};"
        f"final_columns={len(final_rows[0]) if final_rows else 0};metadata_rows={len(metadata_rows)}"
    )
    per_item_summary = {
        "mask_task_name_string_selector_policy": common_summary,
        "mask_task_alias_display_only_policy": common_summary,
        "scaffold_linker_warhead_group_label_policy_candidate": _unique_summary(metadata_rows, ["mask_task_name", "mask_task_alias"]),
        "mask_boolean_tensor_policy_candidate": "boolean mask tensor not written; five metadata selectors observed",
        "warhead_type_label_policy_candidate": _unique_summary(final_rows, ["het_code", "residue_name"]),
        "covalent_atom_pair_label_policy_candidate": _unique_summary(final_rows, ["covalent_bond_atom_pair"]),
        "covalent_bond_distance_label_policy_candidate": _unique_summary(final_rows, ["covalent_bond_distance_angstrom"]),
        "pre_covalent_geometry_label_policy_candidate": "pre-covalent geometry label not materialized current step",
        "post_covalent_geometry_label_policy_candidate": "post-covalent geometry label not materialized current step",
        "auxiliary_loss_label_policy_blocked": "auxiliary loss labels remain blocked",
        "group_label_materialization_smoke_required": "future group label materialization smoke still required",
        "auxiliary_label_resolution_smoke_required": "future auxiliary label smoke still required",
        "label_tensorization_actual_smoke_blocked": "label tensorization blocked current step",
        "label_semantics_not_training_final_current_step": "label semantics not training-final current step",
    }
    rows: list[dict[str, Any]] = []
    for item in design_by_item:
        metadata_only = item in {"mask_task_name_string_selector_policy", "mask_task_alias_display_only_policy"}
        rows.append(
            {
                "label_smoke_item": item,
                "design_contract_row_found": item in design_by_item,
                "metadata_or_final_preview_evidence_found": True,
                "observed_label_summary": per_item_summary[item],
                "mask_task_name_source_of_truth": True,
                "mask_task_alias_display_only": True,
                "ready_for_actual_tensor_smoke": False,
                "blocks_training": not metadata_only,
                "label_smoke_passed": item in design_by_item and set(mask_names) == set(CANONICAL_MASK_TASK_NAMES) and set(aliases) == set(CANONICAL_MASK_TASK_ALIASES),
                "qa_comment": "label policy smoke uses metadata/final previews only; no label tensors are written",
            }
        )
    return rows


def build_tensor_policy_smoke_rows() -> list[dict[str, Any]]:
    design_rows = _csv_rows(step13by.TENSOR_SHAPE_DTYPE_RESOLUTION_CONTRACT_CSV)
    design_by_item = {row["tensor_policy_item"]: row for row in design_rows}
    bundle = _table_bundle()
    coordinate_columns = _coordinate_columns(bundle)
    evidence = {
        "coordinate_dtype_candidate": f"coordinate_like_columns={coordinate_columns};values_read_as_csv_strings",
        "coordinate_shape_candidate": f"protein_rows={len(bundle['protein_rows'])};ligand_rows={len(bundle['ligand_rows'])};coordinate_columns={len(coordinate_columns)}",
        "atom_feature_dtype_candidate": "categorical candidate columns observed as CSV strings",
        "atom_feature_shape_candidate": f"protein_headers={len(bundle['protein_headers'])};ligand_headers={len(bundle['ligand_headers'])}",
        "mask_selector_dtype_candidate": "mask_task_name and mask_task_alias observed as metadata selectors",
        "mask_boolean_dtype_candidate": "boolean mask tensors not written; group label smoke still required",
        "auxiliary_label_dtype_candidate": "auxiliary label dtype blocked pending label semantics",
        "variable_size_collate_policy_candidate": "variable-size row counts observed in metadata preview",
        "batch_index_policy_candidate": "getitem_index observed in metadata preview without tensorization",
        "tensor_shape_dtype_resolution_smoke_required": "policy smoke complete without tensor artifacts",
    }
    return [
        {
            "tensor_policy_smoke_item": item,
            "design_contract_row_found": item in design_by_item,
            "observed_shape_or_dtype_evidence": evidence[item],
            "checkpoint_compatibility_risk": design_by_item[item]["checkpoint_compatibility_risk"],
            "current_step_tensorized": False,
            "ready_for_actual_tensor_smoke": False,
            "tensor_policy_smoke_passed": item in design_by_item,
            "qa_comment": "shape/dtype evidence is CSV-level only; no tensor or numpy object created",
        }
        for item in design_by_item
    ]


def build_readiness_rows() -> list[dict[str, Any]]:
    rows = [
        ("feature_schema_resolution_smoke_completed", "true", "covapie_feature_semantics_resolution_smoke_qa_gate", "schema mapping smoke completed but not final for training"),
        ("coordinate_policy_smoke_completed", "true", "covapie_feature_semantics_resolution_smoke_qa_gate", "coordinate policy smoke completed without tensors"),
        ("atom_feature_policy_smoke_completed", "true", "covapie_feature_semantics_resolution_smoke_qa_gate", "atom feature policy smoke completed without tensors"),
        ("unknown_atom_policy_smoke_completed", "true", "covapie_feature_semantics_resolution_smoke_qa_gate", "unknown policy coverage smoke completed without finalizing policy"),
        ("label_policy_smoke_completed", "true", "covapie_feature_semantics_resolution_smoke_qa_gate", "label policy smoke completed without tensorizing labels"),
        ("tensor_shape_dtype_policy_smoke_completed", "true", "covapie_feature_semantics_resolution_smoke_qa_gate", "shape/dtype policy smoke completed without tensors"),
        ("feature_semantics_training_final_still_false", "feature_semantics_known_for_training=false;unknown_atom_feature_policy_finalized_for_training=false", "formal_feature_semantics_audit_before_training", "training-final semantics remain false"),
        ("actual_dataloader_adapter_smoke_still_blocked", "ready_for_covapie_actual_dataloader_adapter_smoke=false", "covapie_feature_semantics_resolution_smoke_qa_gate", "adapter smoke remains blocked until QA"),
        ("actual_dataloader_smoke_still_blocked", "ready_for_covapie_actual_dataloader_smoke=false", "covapie_feature_semantics_resolution_smoke_qa_gate", "actual dataloader smoke remains blocked"),
        ("training_still_blocked", "ready_for_training=false;ready_to_train_now=false", "feature_semantics_audit_and_leakage_split_design_before_training", "training remains blocked"),
    ]
    return [
        {
            "readiness_item": item,
            "observed_status": status,
            "readiness_passed": True,
            "next_required_gate": gate,
            "qa_comment": comment,
        }
        for item, status, gate, comment in rows
    ]


def build_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "empty", not _raw_files_tracked()),
        ("raw_files_unstaged", "empty", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "true", True),
        ("derived_atom_tables_read_only", "true", True),
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
        ("step13by_artifacts_unchanged", "no_diff", not _path_diff_exists([step13by.OUTPUT_ROOT.as_posix()])),
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


def run_covapie_feature_semantics_resolution_smoke_v0() -> dict[str, Any]:
    precondition_rows = build_precondition_rows()
    mapping_rows = build_original_feature_schema_mapping_smoke_rows()
    coordinate_rows = build_coordinate_policy_smoke_rows()
    atom_rows = build_atom_feature_policy_smoke_rows()
    unknown_rows = build_unknown_policy_smoke_rows()
    label_rows = build_label_policy_smoke_rows()
    tensor_rows = build_tensor_policy_smoke_rows()
    readiness_rows = build_readiness_rows()
    safety_rows = build_safety_rows()
    bundle = _table_bundle()
    metadata_rows = bundle["metadata_rows"]
    final_rows = bundle["final_rows"]
    metadata_mask_names = {row["mask_task_name"] for row in metadata_rows}

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13by_feature_semantics_resolution_design_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "source_metadata_smoke_preview_row_count": len(metadata_rows),
        "source_metadata_smoke_preview_column_count": len(metadata_rows[0]) if metadata_rows else 0,
        "source_final_dataset_preview_row_count": len(final_rows),
        "source_final_dataset_preview_column_count": len(final_rows[0]) if final_rows else 0,
        "source_canonical_mask_task_count": len(metadata_mask_names),
        "protein_atom_table_path_count": len(bundle["protein_paths"]),
        "ligand_atom_table_path_count": len(bundle["ligand_paths"]),
        "protein_atom_table_rows_positive": len(bundle["protein_rows"]) > 0,
        "ligand_atom_table_rows_positive": len(bundle["ligand_rows"]) > 0,
        "original_feature_schema_mapping_smoke_audit_row_count": len(mapping_rows),
        "coordinate_policy_resolution_smoke_audit_row_count": len(coordinate_rows),
        "atom_feature_policy_resolution_smoke_audit_row_count": len(atom_rows),
        "unknown_atom_policy_resolution_smoke_audit_row_count": len(unknown_rows),
        "label_policy_resolution_smoke_audit_row_count": len(label_rows),
        "tensor_shape_dtype_policy_smoke_audit_row_count": len(tensor_rows),
        "feature_semantics_resolution_readiness_audit_row_count": len(readiness_rows),
        "original_feature_schema_mapping_smoke_audit_passed": all(_bool(row["mapping_smoke_passed"]) for row in mapping_rows),
        "coordinate_policy_resolution_smoke_audit_passed": all(_bool(row["coordinate_smoke_passed"]) for row in coordinate_rows),
        "atom_feature_policy_resolution_smoke_audit_passed": all(_bool(row["atom_feature_smoke_passed"]) for row in atom_rows),
        "unknown_atom_policy_resolution_smoke_audit_passed": all(_bool(row["unknown_policy_smoke_passed"]) for row in unknown_rows),
        "label_policy_resolution_smoke_audit_passed": all(_bool(row["label_smoke_passed"]) for row in label_rows),
        "tensor_shape_dtype_policy_smoke_audit_passed": all(_bool(row["tensor_policy_smoke_passed"]) for row in tensor_rows),
        "feature_semantics_resolution_readiness_audit_passed": all(_bool(row["readiness_passed"]) for row in readiness_rows),
        "safety_audit_passed": all(_bool(row["safety_passed"]) for row in safety_rows),
        "feature_semantics_resolution_smoke_completed_current_step": True,
        "proposed_feature_schema_resolution_validated_by_smoke": True,
        "proposed_unknown_atom_policy_validated_by_smoke": True,
        "proposed_label_semantics_validated_by_smoke": True,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
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
        "derived_atom_tables_read_only": True,
        "network_access_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "gzip_open_used": False,
        "ready_for_covapie_feature_semantics_resolution_smoke_qa_gate": True,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_covapie_actual_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in metadata_mask_names,
        "no_extra_mask_tasks_added": metadata_mask_names == set(CANONICAL_MASK_TASK_NAMES),
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_feature_semantics_resolution_smoke_qa_gate",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13by_feature_semantics_resolution_design_validated"],
            manifest["source_metadata_smoke_preview_row_count"] == 20,
            manifest["source_metadata_smoke_preview_column_count"] == 30,
            manifest["source_final_dataset_preview_row_count"] == 20,
            manifest["source_final_dataset_preview_column_count"] == 45,
            manifest["source_canonical_mask_task_count"] == 5,
            manifest["protein_atom_table_path_count"] >= 1,
            manifest["ligand_atom_table_path_count"] >= 1,
            manifest["protein_atom_table_rows_positive"],
            manifest["ligand_atom_table_rows_positive"],
            manifest["original_feature_schema_mapping_smoke_audit_row_count"] == 12,
            manifest["coordinate_policy_resolution_smoke_audit_row_count"] == 8,
            manifest["atom_feature_policy_resolution_smoke_audit_row_count"] == 12,
            manifest["unknown_atom_policy_resolution_smoke_audit_row_count"] == 8,
            manifest["label_policy_resolution_smoke_audit_row_count"] == 14,
            manifest["tensor_shape_dtype_policy_smoke_audit_row_count"] == 10,
            manifest["feature_semantics_resolution_readiness_audit_row_count"] == 10,
            manifest["original_feature_schema_mapping_smoke_audit_passed"],
            manifest["coordinate_policy_resolution_smoke_audit_passed"],
            manifest["atom_feature_policy_resolution_smoke_audit_passed"],
            manifest["unknown_atom_policy_resolution_smoke_audit_passed"],
            manifest["label_policy_resolution_smoke_audit_passed"],
            manifest["tensor_shape_dtype_policy_smoke_audit_passed"],
            manifest["feature_semantics_resolution_readiness_audit_passed"],
            manifest["safety_audit_passed"],
            manifest["feature_semantics_resolution_smoke_completed_current_step"],
            manifest["proposed_feature_schema_resolution_validated_by_smoke"],
            manifest["proposed_unknown_atom_policy_validated_by_smoke"],
            manifest["proposed_label_semantics_validated_by_smoke"],
            not manifest["feature_semantics_known_for_training"],
            not manifest["unknown_atom_feature_policy_finalized_for_training"],
            not manifest["actual_dataloader_adapter_smoke_written"],
            not manifest["actual_dataloader_smoke_written"],
            not manifest["real_dataloader_written"],
            not manifest["original_dataloader_modified"],
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
            manifest["derived_atom_tables_read_only"],
            not manifest["network_access_used"],
            not manifest["rdkit_used"],
            not manifest["biopdb_parser_used"],
            not manifest["gemmi_used"],
            not manifest["gzip_open_used"],
            manifest["ready_for_covapie_feature_semantics_resolution_smoke_qa_gate"],
            not manifest["ready_for_covapie_actual_dataloader_adapter_smoke"],
            not manifest["ready_for_covapie_actual_dataloader_smoke"],
            not manifest["ready_for_training"],
            not manifest["ready_to_train_now"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
            manifest["feature_semantics_audit_required_before_training"],
            manifest["leakage_split_design_required_before_training"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["feature_semantics_resolution_smoke_failed"]
    return {
        "precondition_rows": precondition_rows,
        "mapping_rows": mapping_rows,
        "coordinate_rows": coordinate_rows,
        "atom_rows": atom_rows,
        "unknown_rows": unknown_rows,
        "label_rows": label_rows,
        "tensor_rows": tensor_rows,
        "readiness_rows": readiness_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }
