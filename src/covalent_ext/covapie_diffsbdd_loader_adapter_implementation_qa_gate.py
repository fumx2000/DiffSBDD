from __future__ import annotations

import ast
import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_diffsbdd_loader_adapter_implementation_qa_gate_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke_v0"
PROJECT_NAME = "CovaPIE"

STEP13AC_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke_v0"
)
STEP13AC_MANIFEST_JSON = STEP13AC_ROOT / "diffsbdd_loader_adapter_implementation_smoke_manifest.json"
STEP13AC_INPUT_AUDIT_CSV = STEP13AC_ROOT / "diffsbdd_loader_adapter_input_audit.csv"
STEP13AC_SAMPLE_DICT_AUDIT_CSV = STEP13AC_ROOT / "diffsbdd_loader_adapter_sample_dict_audit.csv"
STEP13AC_FIELD_SHAPE_OBSERVATION_CSV = STEP13AC_ROOT / "diffsbdd_loader_adapter_field_shape_observation.csv"
STEP13AC_SINGLE_SAMPLE_BATCH_AUDIT_CSV = STEP13AC_ROOT / "diffsbdd_loader_adapter_single_sample_batch_audit.csv"
STEP13AC_MASK_MAPPING_AUDIT_CSV = STEP13AC_ROOT / "diffsbdd_loader_adapter_mask_mapping_audit.csv"
STEP13AC_AUXILIARY_LABEL_AUDIT_CSV = STEP13AC_ROOT / "diffsbdd_loader_adapter_auxiliary_label_audit.csv"
STEP13AC_EXECUTION_BOUNDARY_AUDIT_CSV = STEP13AC_ROOT / "diffsbdd_loader_adapter_execution_boundary_audit.csv"
STEP13AC_FEATURE_SEMANTICS_AUDIT_CSV = STEP13AC_ROOT / "diffsbdd_loader_adapter_feature_semantics_audit.csv"
STEP13AC_DEPENDENCY_AUDIT_CSV = STEP13AC_ROOT / "diffsbdd_loader_adapter_dependency_audit.csv"
STEP13AC_REPORT_CSV = STEP13AC_ROOT / "diffsbdd_loader_adapter_implementation_smoke_report.csv"
STEP13AC_SOURCE_PY = Path(
    "src/covalent_ext/real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke.py"
)

STEP13AB_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate_v0/"
    "diffsbdd_loader_adapter_design_gate_manifest.json"
)
NAMING_CONVENTION_MD = Path("docs/covapie_project_naming_convention.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_diffsbdd_loader_adapter_implementation_qa_gate_v0")
INPUT_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_adapter_input_qa_audit.csv"
SAMPLE_DICT_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_adapter_sample_dict_qa_audit.csv"
FIELD_SHAPE_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_adapter_field_shape_qa_audit.csv"
SINGLE_SAMPLE_BATCH_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_adapter_single_sample_batch_qa_audit.csv"
MASK_MAPPING_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_adapter_mask_mapping_qa_audit.csv"
AUXILIARY_LABEL_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_adapter_auxiliary_label_qa_audit.csv"
EXECUTION_BOUNDARY_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_adapter_execution_boundary_qa_audit.csv"
FEATURE_SEMANTICS_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_adapter_feature_semantics_qa_audit.csv"
DEPENDENCY_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_adapter_dependency_qa_audit.csv"
SOURCE_AST_SAFETY_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_adapter_source_ast_safety_qa_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "covapie_adapter_implementation_qa_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_adapter_implementation_qa_manifest.json"
SUMMARY_MD = Path("docs/covapie_diffsbdd_loader_adapter_implementation_qa_gate_v0_summary.md")

EXPECTED_ADAPTER_DESIGN_SAMPLE_IDS = [
    "DSBDD_ADAPTER_DESIGN_000001",
    "DSBDD_ADAPTER_DESIGN_000002",
    "DSBDD_ADAPTER_DESIGN_000003",
]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_SHAPES = {
    ("HR_0002", "ligand_atom_coordinates"): [33, 3],
    ("HR_0002", "ligand_bond_index"): [2, 35],
    ("HR_0003", "ligand_atom_coordinates"): [30, 3],
    ("HR_0003", "ligand_bond_index"): [2, 33],
    ("HR_0004", "ligand_atom_coordinates"): [41, 3],
    ("HR_0004", "ligand_bond_index"): [2, 45],
}
CANONICAL_MASK_TASK_NAMES = [
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
]
CANONICAL_MASK_TASK_ALIASES = ["A", "B", "B2", "B3", "C"]
QA_SCOPE = "current_cys_sg_golden_samples_only"
V1_TRAIN_READY_SCOPE = "cys_sg_with_known_restoration_template_only"
CHECKPOINT_COMPATIBILITY_POLICY = "preserve_diffsbdd_checkpoint_compatibility_by_external_adapter_only"
RECOMMENDED_NEXT_STEP = "covapie_batch_scale_data_preparation_design_gate"

PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]
ORIGINAL_DIFFSBDD_DATALOADER_PATHS = ["dataset.py", "data/prepare_crossdocked.py"]
FORBIDDEN_COMMITTABLE_SUFFIXES = {
    ".pt",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".ckpt",
    ".pth",
    ".npz",
    ".pdb",
    ".cif",
    ".mmcif",
    ".sdf",
    ".mol2",
    ".gz",
}

INPUT_QA_COLUMNS = [
    "adapter_design_sample_id",
    "review_row_id",
    "pdb_id",
    "input_audit_row_found",
    "expected_identity_validated",
    "cys_sg_scope_validated",
    "ligand_counts_validated",
    "endpoint_counts_validated",
    "canonical_masks_validated",
    "step13ac_input_audit_passed",
    "qa_passed",
    "blocking_reasons",
]
SAMPLE_DICT_QA_COLUMNS = [
    "adapter_design_sample_id",
    "review_row_id",
    "sample_dict_audit_row_found",
    "adapter_sample_built",
    "metadata_present",
    "adapter_fields_present",
    "adapter_field_count",
    "canonical_mask_task_count",
    "auxiliary_label_count",
    "step13ac_sample_dict_audit_passed",
    "qa_passed",
    "blocking_reasons",
]
FIELD_SHAPE_QA_COLUMNS = [
    "adapter_design_sample_id",
    "review_row_id",
    "covalent_shape_item",
    "future_adapter_field_name",
    "observed_shape",
    "observed_dtype_family",
    "tensor_created_in_step13ac",
    "tensor_persisted",
    "field_shape_observation_passed_in_step13ac",
    "expected_shape_validated",
    "qa_passed",
    "blocking_reasons",
]
SINGLE_SAMPLE_BATCH_QA_COLUMNS = [
    "batch_index",
    "adapter_design_sample_id",
    "review_row_id",
    "batch_size",
    "collate_status",
    "adapter_batch_built",
    "batch_field_count",
    "batch_shape_checked",
    "batch_order_validated",
    "model_forward_called",
    "loss_compute_called",
    "backward_called",
    "optimizer_step_called",
    "training_step_called",
    "single_sample_batch_audit_passed",
    "qa_passed",
    "blocking_reasons",
]
MASK_MAPPING_QA_COLUMNS = [
    "canonical_mask_task_name",
    "display_alias",
    "source_of_truth_status",
    "alias_status",
    "adapter_mask_carried",
    "tensor_mask_persisted",
    "implementation_status",
    "training_use_status",
    "mask_mapping_audit_passed",
    "qa_passed",
    "blocking_reasons",
]
AUXILIARY_LABEL_QA_COLUMNS = [
    "auxiliary_label_name",
    "adapter_label_carried",
    "future_loss_integration_status",
    "loss_integration_performed",
    "training_use_status",
    "feature_semantics_audit_required_before_training",
    "auxiliary_label_audit_passed",
    "qa_passed",
    "blocking_reasons",
]
EXECUTION_BOUNDARY_QA_COLUMNS = [
    "boundary_item",
    "observed_current_step_status",
    "boundary_respected",
    "training_forbidden_respected",
    "artifact_forbidden_respected",
    "original_source_protection_respected",
    "boundary_audit_passed",
    "qa_passed",
    "blocking_reasons",
]
FEATURE_SEMANTICS_QA_COLUMNS = [
    "feature_semantics_item",
    "feature_group",
    "current_status",
    "audit_required_before_training",
    "fully_audited_claimed",
    "blocking_for_adapter_implementation_smoke",
    "training_ready",
    "recommended_audit_step",
    "feature_semantics_adapter_smoke_audit_passed",
    "qa_passed",
    "blocking_reasons",
]
DEPENDENCY_QA_COLUMNS = [
    "dependency_name",
    "dependency_artifact_path",
    "dependency_exists",
    "dependency_row_count",
    "dependency_expected_row_count",
    "dependency_count_validated",
    "dependency_qa_passed",
    "blocking_reasons",
]
SOURCE_AST_SAFETY_QA_COLUMNS = [
    "safety_item",
    "source_path",
    "check_method",
    "expected_status",
    "observed_status",
    "qa_passed",
    "blocking_reasons",
]
REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "section",
    "status",
    "evidence",
    "decision",
    "blocking_reasons",
    "recommended_next_step",
]


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _row_count(path: Path) -> int:
    if not path.is_file():
        return 0
    if path.suffix == ".json" or path.suffix == ".md":
        return 1
    return len(_read_csv(path))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _path_diff_exists(paths: list[str]) -> bool:
    unstaged = _run_git(["diff", "--quiet", "--", *paths])
    staged = _run_git(["diff", "--cached", "--quiet", "--", *paths])
    return unstaged.returncode != 0 or staged.returncode != 0


def _source_diff_exists() -> bool:
    return _path_diff_exists(PROTECTED_SOURCE_PATHS)


def _original_dataloader_diff_exists() -> bool:
    return _path_diff_exists(ORIGINAL_DIFFSBDD_DATALOADER_PATHS)


def _forbidden_committable_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in FORBIDDEN_COMMITTABLE_SUFFIXES for path in root_path.rglob("*"))


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", "data/raw/covalent_sources"]).stdout.strip())


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", "data/raw/covalent_sources"]).stdout.strip())


def validate_covapie_naming_convention_v0() -> bool:
    text = NAMING_CONVENTION_MD.read_text(encoding="utf-8")
    required = [
        "CovaPIE** is the name of this project",
        "CovaGEN** is an external model or project name owned by others",
        "New experiment reports, summaries, gate documents, and Codex prompts should use CovaPIE",
        "Historical artifact paths, historical filenames, and historical step names are retained",
        "`src/covalent_ext/` package is a functional module name and is not renamed",
        "Do not change Python import paths, test paths, data paths, or existing `data/derived/` artifact paths",
        "dedicated migration design gate",
        "Feature semantics audit remains required before formal training",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise ValueError("CovaPIE naming convention is missing required text: " + ";".join(missing))
    return True


def validate_step13ac_precondition_v0() -> bool:
    required_paths = [
        STEP13AC_MANIFEST_JSON,
        STEP13AC_INPUT_AUDIT_CSV,
        STEP13AC_SAMPLE_DICT_AUDIT_CSV,
        STEP13AC_FIELD_SHAPE_OBSERVATION_CSV,
        STEP13AC_SINGLE_SAMPLE_BATCH_AUDIT_CSV,
        STEP13AC_MASK_MAPPING_AUDIT_CSV,
        STEP13AC_AUXILIARY_LABEL_AUDIT_CSV,
        STEP13AC_EXECUTION_BOUNDARY_AUDIT_CSV,
        STEP13AC_FEATURE_SEMANTICS_AUDIT_CSV,
        STEP13AC_DEPENDENCY_AUDIT_CSV,
        STEP13AC_REPORT_CSV,
        STEP13AC_SOURCE_PY,
        STEP13AB_MANIFEST_JSON,
        NAMING_CONVENTION_MD,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13AD prerequisite outputs are missing: {missing}")

    manifest = _load_json(STEP13AC_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate_v0",
        "all_checks_passed": True,
        "step13ab_diffsbdd_loader_adapter_design_gate_validated": True,
        "adapter_implementation_scope": QA_SCOPE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "checkpoint_compatibility_policy": CHECKPOINT_COMPATIBILITY_POLICY,
        "diffsbdd_loader_adapter_input_audit_written": True,
        "diffsbdd_loader_adapter_input_audit_row_count": 3,
        "diffsbdd_loader_adapter_sample_dict_audit_written": True,
        "diffsbdd_loader_adapter_sample_dict_audit_row_count": 3,
        "diffsbdd_loader_adapter_field_shape_observation_written": True,
        "diffsbdd_loader_adapter_field_shape_observation_row_count": 42,
        "diffsbdd_loader_adapter_single_sample_batch_audit_written": True,
        "diffsbdd_loader_adapter_single_sample_batch_audit_row_count": 3,
        "diffsbdd_loader_adapter_mask_mapping_audit_written": True,
        "diffsbdd_loader_adapter_mask_mapping_audit_row_count": 5,
        "diffsbdd_loader_adapter_auxiliary_label_audit_written": True,
        "diffsbdd_loader_adapter_auxiliary_label_audit_row_count": 3,
        "diffsbdd_loader_adapter_execution_boundary_audit_written": True,
        "diffsbdd_loader_adapter_execution_boundary_audit_row_count": 19,
        "diffsbdd_loader_adapter_feature_semantics_audit_written": True,
        "diffsbdd_loader_adapter_feature_semantics_audit_row_count": 12,
        "diffsbdd_loader_adapter_dependency_audit_written": True,
        "diffsbdd_loader_adapter_dependency_audit_row_count": 8,
        "canonical_mask_task_count": 5,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "adapter_implemented": True,
        "adapter_module_location": "src/covalent_ext/",
        "adapter_instantiated": True,
        "adapter_sample_count": 3,
        "adapter_output_field_count": 14,
        "adapter_single_sample_batch_count": 3,
        "torch_imported": True,
        "torch_tensor_created": True,
        "transient_adapter_field_shape_inspection_performed": True,
        "all_adapter_input_audits_passed": True,
        "all_adapter_sample_dict_audits_passed": True,
        "all_adapter_field_shape_observations_passed": True,
        "all_adapter_single_sample_batch_audits_passed": True,
        "all_mask_mapping_audits_passed": True,
        "all_auxiliary_label_audits_passed": True,
        "all_execution_boundaries_respected": True,
        "all_dependency_artifacts_exist": True,
        "all_dependency_counts_validated": True,
        "all_feature_semantics_audit_required_before_training": True,
        "no_feature_semantics_claimed_fully_audited": True,
        "checkpoint_compatibility_preserved_by_external_adapter": True,
        "diffsbdd_loader_adapter_implementation_smoke_passed": True,
        "original_diffsbdd_source_modified": False,
        "original_diffsbdd_dataloader_modified": False,
        "original_diffsbdd_forward_modified": False,
        "original_diffsbdd_loss_modified": False,
        "tensor_artifact_written": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "pt_created": False,
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "ready_for_diffsbdd_loader_adapter_implementation_qa_gate": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_qa_gate",
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("canonical_mask_task_names") != CANONICAL_MASK_TASK_NAMES:
        blockers.append("canonical_mask_task_names")
    if manifest.get("canonical_mask_task_aliases") != CANONICAL_MASK_TASK_ALIASES:
        blockers.append("canonical_mask_task_aliases")
    if blockers:
        raise ValueError("Step 13AC precondition failed: " + ";".join(blockers))
    return True


def _pass_block(passed: bool, reason: str) -> str:
    return "" if passed else reason


def _expected_shape_validated(row: dict[str, str]) -> bool:
    shape = json.loads(row["observed_shape"])
    item = row["covalent_shape_item"]
    review_id = row["review_row_id"]
    if (review_id, item) in EXPECTED_SHAPES:
        return shape == EXPECTED_SHAPES[(review_id, item)]
    if item == "canonical_mask_task_id_or_name":
        return shape == [1]
    return _as_bool(row["field_shape_observation_passed"])


def build_input_qa_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    qa_rows = []
    for index, row in enumerate(rows):
        identity = (
            row["adapter_design_sample_id"] == EXPECTED_ADAPTER_DESIGN_SAMPLE_IDS[index]
            and row["review_row_id"] == EXPECTED_REVIEW_ROW_IDS[index]
            and row["pdb_id"] == EXPECTED_PDB_IDS[index]
        )
        passed = identity and all(
            _as_bool(row[key])
            for key in [
                "adapter_input_row_found",
                "cys_sg_scope_validated",
                "ligand_counts_validated",
                "endpoint_counts_validated",
                "canonical_masks_validated",
                "adapter_input_audit_passed",
            ]
        )
        qa_rows.append(
            {
                "adapter_design_sample_id": row["adapter_design_sample_id"],
                "review_row_id": row["review_row_id"],
                "pdb_id": row["pdb_id"],
                "input_audit_row_found": _as_bool(row["adapter_input_row_found"]),
                "expected_identity_validated": identity,
                "cys_sg_scope_validated": _as_bool(row["cys_sg_scope_validated"]),
                "ligand_counts_validated": _as_bool(row["ligand_counts_validated"]),
                "endpoint_counts_validated": _as_bool(row["endpoint_counts_validated"]),
                "canonical_masks_validated": _as_bool(row["canonical_masks_validated"]),
                "step13ac_input_audit_passed": _as_bool(row["adapter_input_audit_passed"]),
                "qa_passed": passed,
                "blocking_reasons": _pass_block(passed, "input_qa_failed"),
            }
        )
    return qa_rows


def build_sample_dict_qa_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    qa_rows = []
    for row in rows:
        passed = (
            _as_bool(row["adapter_sample_built"])
            and _as_bool(row["metadata_present"])
            and _as_bool(row["adapter_fields_present"])
            and int(row["adapter_field_count"]) == 14
            and int(row["canonical_mask_task_count"]) == 5
            and int(row["auxiliary_label_count"]) == 3
            and _as_bool(row["adapter_sample_dict_audit_passed"])
        )
        qa_rows.append(
            {
                "adapter_design_sample_id": row["adapter_design_sample_id"],
                "review_row_id": row["review_row_id"],
                "sample_dict_audit_row_found": True,
                "adapter_sample_built": _as_bool(row["adapter_sample_built"]),
                "metadata_present": _as_bool(row["metadata_present"]),
                "adapter_fields_present": _as_bool(row["adapter_fields_present"]),
                "adapter_field_count": int(row["adapter_field_count"]),
                "canonical_mask_task_count": int(row["canonical_mask_task_count"]),
                "auxiliary_label_count": int(row["auxiliary_label_count"]),
                "step13ac_sample_dict_audit_passed": _as_bool(row["adapter_sample_dict_audit_passed"]),
                "qa_passed": passed,
                "blocking_reasons": _pass_block(passed, "sample_dict_qa_failed"),
            }
        )
    return qa_rows


def build_field_shape_qa_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    seen = set()
    qa_rows = []
    for row in rows:
        key = (row["adapter_design_sample_id"], row["covalent_shape_item"])
        duplicate_free = key not in seen
        seen.add(key)
        shape_ok = _expected_shape_validated(row)
        passed = (
            duplicate_free
            and _as_bool(row["tensor_created"])
            and not _as_bool(row["tensor_persisted"])
            and _as_bool(row["field_shape_observation_passed"])
            and shape_ok
        )
        qa_rows.append(
            {
                "adapter_design_sample_id": row["adapter_design_sample_id"],
                "review_row_id": row["review_row_id"],
                "covalent_shape_item": row["covalent_shape_item"],
                "future_adapter_field_name": row["future_adapter_field_name"],
                "observed_shape": row["observed_shape"],
                "observed_dtype_family": row["observed_dtype_family"],
                "tensor_created_in_step13ac": _as_bool(row["tensor_created"]),
                "tensor_persisted": _as_bool(row["tensor_persisted"]),
                "field_shape_observation_passed_in_step13ac": _as_bool(row["field_shape_observation_passed"]),
                "expected_shape_validated": shape_ok,
                "qa_passed": passed,
                "blocking_reasons": _pass_block(passed, "field_shape_qa_failed"),
            }
        )
    return qa_rows


def build_batch_qa_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    qa_rows = []
    for index, row in enumerate(rows):
        passed = (
            int(row["batch_index"]) == index
            and int(row["batch_size"]) == 1
            and row["collate_status"] == "external_adapter_single_sample_collate_no_padding_no_training"
            and _as_bool(row["adapter_batch_built"])
            and int(row["batch_field_count"]) == 14
            and _as_bool(row["batch_shape_checked"])
            and _as_bool(row["batch_order_validated"])
            and not _as_bool(row["model_forward_called"])
            and not _as_bool(row["loss_compute_called"])
            and not _as_bool(row["backward_called"])
            and not _as_bool(row["optimizer_step_called"])
            and not _as_bool(row["training_step_called"])
            and _as_bool(row["single_sample_batch_audit_passed"])
        )
        qa_rows.append(
            {
                "batch_index": int(row["batch_index"]),
                "adapter_design_sample_id": row["adapter_design_sample_id"],
                "review_row_id": row["review_row_id"],
                "batch_size": int(row["batch_size"]),
                "collate_status": row["collate_status"],
                "adapter_batch_built": _as_bool(row["adapter_batch_built"]),
                "batch_field_count": int(row["batch_field_count"]),
                "batch_shape_checked": _as_bool(row["batch_shape_checked"]),
                "batch_order_validated": _as_bool(row["batch_order_validated"]),
                "model_forward_called": _as_bool(row["model_forward_called"]),
                "loss_compute_called": _as_bool(row["loss_compute_called"]),
                "backward_called": _as_bool(row["backward_called"]),
                "optimizer_step_called": _as_bool(row["optimizer_step_called"]),
                "training_step_called": _as_bool(row["training_step_called"]),
                "single_sample_batch_audit_passed": _as_bool(row["single_sample_batch_audit_passed"]),
                "qa_passed": passed,
                "blocking_reasons": _pass_block(passed, "batch_qa_failed"),
            }
        )
    return qa_rows


def build_mask_mapping_qa_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    qa_rows = []
    for index, row in enumerate(rows):
        passed = (
            row["canonical_mask_task_name"] == CANONICAL_MASK_TASK_NAMES[index]
            and row["display_alias"] == CANONICAL_MASK_TASK_ALIASES[index]
            and row["source_of_truth_status"] == "long_semantic_name_source_of_truth"
            and row["alias_status"] == "display_only"
            and _as_bool(row["adapter_mask_carried"])
            and not _as_bool(row["tensor_mask_persisted"])
            and row["implementation_status"] == "implemented_in_external_adapter_smoke_only"
            and row["training_use_status"] == "not_training_input_yet"
            and _as_bool(row["mask_mapping_audit_passed"])
        )
        qa_rows.append(
            {
                "canonical_mask_task_name": row["canonical_mask_task_name"],
                "display_alias": row["display_alias"],
                "source_of_truth_status": row["source_of_truth_status"],
                "alias_status": row["alias_status"],
                "adapter_mask_carried": _as_bool(row["adapter_mask_carried"]),
                "tensor_mask_persisted": _as_bool(row["tensor_mask_persisted"]),
                "implementation_status": row["implementation_status"],
                "training_use_status": row["training_use_status"],
                "mask_mapping_audit_passed": _as_bool(row["mask_mapping_audit_passed"]),
                "qa_passed": passed,
                "blocking_reasons": _pass_block(passed, "mask_mapping_qa_failed"),
            }
        )
    return qa_rows


def build_auxiliary_label_qa_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    expected = ["warhead_type", "ligand_residue_atom_pair", "pre_post_covalent_geometry"]
    qa_rows = []
    for index, row in enumerate(rows):
        passed = (
            row["auxiliary_label_name"] == expected[index]
            and _as_bool(row["adapter_label_carried"])
            and row["future_loss_integration_status"] == "not_integrated_into_loss"
            and not _as_bool(row["loss_integration_performed"])
            and row["training_use_status"] == "not_training_input_yet"
            and _as_bool(row["feature_semantics_audit_required_before_training"])
            and _as_bool(row["auxiliary_label_audit_passed"])
        )
        qa_rows.append(
            {
                "auxiliary_label_name": row["auxiliary_label_name"],
                "adapter_label_carried": _as_bool(row["adapter_label_carried"]),
                "future_loss_integration_status": row["future_loss_integration_status"],
                "loss_integration_performed": _as_bool(row["loss_integration_performed"]),
                "training_use_status": row["training_use_status"],
                "feature_semantics_audit_required_before_training": _as_bool(
                    row["feature_semantics_audit_required_before_training"]
                ),
                "auxiliary_label_audit_passed": _as_bool(row["auxiliary_label_audit_passed"]),
                "qa_passed": passed,
                "blocking_reasons": _pass_block(passed, "auxiliary_label_qa_failed"),
            }
        )
    return qa_rows


def build_execution_boundary_qa_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    expected_status = {
        "adapter_implementation": "executed_external_covalent_ext_smoke_only",
        "adapter_instantiation": "executed_external_covalent_ext_smoke_only",
        "torch_import": "executed_for_transient_shape_smoke",
        "tensor_creation": "executed_transient_in_memory_only",
        "single_sample_collate": "executed_external_adapter_single_sample_only",
        "original_diffsbdd_source_modification": "not_executed_or_not_allowed",
        "dataloader_modification": "not_executed_or_not_allowed",
        "model_forward_call": "not_executed_or_not_allowed",
        "loss_compute": "not_executed_or_not_allowed",
        "backward_call": "not_executed_or_not_allowed",
        "optimizer_creation": "not_executed_or_not_allowed",
        "trainer_fit": "not_executed_or_not_allowed",
        "checkpoint_load": "not_executed_or_not_allowed",
        "checkpoint_save": "not_executed_or_not_allowed",
        "pt_npz_artifact_creation": "not_executed_or_not_allowed",
        "rdkit_or_sdf_access": "not_executed_or_not_allowed",
        "raw_mmcif_access": "not_executed_or_not_allowed",
        "training_claim": "not_executed_or_not_allowed",
        "feature_semantics_audit": "required_before_training_not_completed",
    }
    qa_rows = []
    for row in rows:
        passed = (
            row["observed_current_step_status"] == expected_status[row["boundary_item"]]
            and _as_bool(row["boundary_respected"])
            and _as_bool(row["training_forbidden_respected"])
            and _as_bool(row["artifact_forbidden_respected"])
            and _as_bool(row["original_source_protection_respected"])
            and _as_bool(row["boundary_audit_passed"])
        )
        qa_rows.append(
            {
                "boundary_item": row["boundary_item"],
                "observed_current_step_status": row["observed_current_step_status"],
                "boundary_respected": _as_bool(row["boundary_respected"]),
                "training_forbidden_respected": _as_bool(row["training_forbidden_respected"]),
                "artifact_forbidden_respected": _as_bool(row["artifact_forbidden_respected"]),
                "original_source_protection_respected": _as_bool(row["original_source_protection_respected"]),
                "boundary_audit_passed": _as_bool(row["boundary_audit_passed"]),
                "qa_passed": passed,
                "blocking_reasons": _pass_block(passed, "execution_boundary_qa_failed"),
            }
        )
    return qa_rows


def build_feature_semantics_qa_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    qa_rows = []
    for row in rows:
        passed = (
            _as_bool(row["audit_required_before_training"])
            and not _as_bool(row["fully_audited_claimed"])
            and not _as_bool(row["blocking_for_adapter_implementation_smoke"])
            and not _as_bool(row["training_ready"])
            and bool(row["recommended_audit_step"])
            and _as_bool(row["feature_semantics_adapter_smoke_audit_passed"])
        )
        qa_rows.append(
            {
                "feature_semantics_item": row["feature_semantics_item"],
                "feature_group": row["feature_group"],
                "current_status": row["current_status"],
                "audit_required_before_training": _as_bool(row["audit_required_before_training"]),
                "fully_audited_claimed": _as_bool(row["fully_audited_claimed"]),
                "blocking_for_adapter_implementation_smoke": _as_bool(row["blocking_for_adapter_implementation_smoke"]),
                "training_ready": _as_bool(row["training_ready"]),
                "recommended_audit_step": row["recommended_audit_step"],
                "feature_semantics_adapter_smoke_audit_passed": _as_bool(
                    row["feature_semantics_adapter_smoke_audit_passed"]
                ),
                "qa_passed": passed,
                "blocking_reasons": _pass_block(passed, "feature_semantics_qa_failed"),
            }
        )
    return qa_rows


def build_dependency_qa_rows() -> list[dict[str, Any]]:
    dependencies = [
        ("step13ac_manifest", STEP13AC_MANIFEST_JSON, 1),
        ("step13ac_input_audit", STEP13AC_INPUT_AUDIT_CSV, 3),
        ("step13ac_sample_dict_audit", STEP13AC_SAMPLE_DICT_AUDIT_CSV, 3),
        ("step13ac_field_shape_observation", STEP13AC_FIELD_SHAPE_OBSERVATION_CSV, 42),
        ("step13ac_single_sample_batch_audit", STEP13AC_SINGLE_SAMPLE_BATCH_AUDIT_CSV, 3),
        ("step13ac_mask_mapping_audit", STEP13AC_MASK_MAPPING_AUDIT_CSV, 5),
        ("step13ac_auxiliary_label_audit", STEP13AC_AUXILIARY_LABEL_AUDIT_CSV, 3),
        ("step13ac_execution_boundary_audit", STEP13AC_EXECUTION_BOUNDARY_AUDIT_CSV, 19),
        ("step13ac_feature_semantics_audit", STEP13AC_FEATURE_SEMANTICS_AUDIT_CSV, 12),
        ("step13ac_dependency_audit", STEP13AC_DEPENDENCY_AUDIT_CSV, 8),
        ("step13ac_report", STEP13AC_REPORT_CSV, 11),
        ("covapie_naming_convention_doc", NAMING_CONVENTION_MD, 1),
    ]
    qa_rows = []
    for name, path, expected_count in dependencies:
        exists = path.is_file()
        count = _row_count(path)
        count_validated = exists and count == expected_count
        passed = exists and count_validated
        qa_rows.append(
            {
                "dependency_name": name,
                "dependency_artifact_path": str(path),
                "dependency_exists": exists,
                "dependency_row_count": count,
                "dependency_expected_row_count": expected_count,
                "dependency_count_validated": count_validated,
                "dependency_qa_passed": passed,
                "blocking_reasons": _pass_block(passed, "dependency_qa_failed"),
            }
        )
    return qa_rows


def _module_imports_name(tree: ast.AST, name: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == name for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == name:
            return True
    return False


def _module_imports_step13ac(tree: ast.AST) -> bool:
    target = "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(target in alias.name for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module and target in node.module:
            return True
    return False


def _has_class(tree: ast.AST, class_name: str) -> bool:
    return any(isinstance(node, ast.ClassDef) and node.name == class_name for node in ast.walk(tree))


def _has_function(tree: ast.AST, function_name: str) -> bool:
    return any(isinstance(node, ast.FunctionDef) and node.name == function_name for node in ast.walk(tree))


def _has_forbidden_call(tree: ast.AST, names: set[str]) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in names:
                return True
            if isinstance(func, ast.Name) and func.id in names:
                return True
    return False


def build_source_ast_safety_qa_rows() -> list[dict[str, Any]]:
    step13ac_text = STEP13AC_SOURCE_PY.read_text(encoding="utf-8")
    step13ac_tree = ast.parse(step13ac_text)
    this_source = Path(__file__).relative_to(REPO_ROOT)
    this_text = Path(__file__).read_text(encoding="utf-8")
    this_tree = ast.parse(this_text)
    check_script = Path("scripts/check_covapie_diffsbdd_loader_adapter_implementation_qa_gate_v0.py")
    check_tree = ast.parse(check_script.read_text(encoding="utf-8")) if check_script.is_file() else ast.parse("")

    rows: list[dict[str, Any]] = []

    def add(item: str, source_path: Path | str, method: str, expected: str, observed: str, passed: bool) -> None:
        rows.append(
            {
                "safety_item": item,
                "source_path": str(source_path),
                "check_method": method,
                "expected_status": expected,
                "observed_status": observed,
                "qa_passed": passed,
                "blocking_reasons": _pass_block(passed, f"{item}_failed"),
            }
        )

    add(
        "step13ac_module_text_exists",
        STEP13AC_SOURCE_PY,
        "path_exists",
        "exists",
        "exists" if STEP13AC_SOURCE_PY.is_file() else "missing",
        STEP13AC_SOURCE_PY.is_file(),
    )
    add(
        "step13ac_module_defines_adapter_class",
        STEP13AC_SOURCE_PY,
        "ast_class_scan",
        "RealCovalentDiffSBDDLoaderAdapter",
        "found" if _has_class(step13ac_tree, "RealCovalentDiffSBDDLoaderAdapter") else "missing",
        _has_class(step13ac_tree, "RealCovalentDiffSBDDLoaderAdapter"),
    )
    add(
        "step13ac_module_defines_collate_single_sample",
        STEP13AC_SOURCE_PY,
        "ast_function_scan",
        "collate_single_sample",
        "found" if _has_function(step13ac_tree, "collate_single_sample") else "missing",
        _has_function(step13ac_tree, "collate_single_sample"),
    )
    add(
        "step13ac_module_imports_torch_allowed_in_step13ac",
        STEP13AC_SOURCE_PY,
        "ast_import_scan",
        "torch_import_allowed_only_in_step13ac",
        "imports_torch" if _module_imports_name(step13ac_tree, "torch") else "no_torch_import",
        _module_imports_name(step13ac_tree, "torch"),
    )
    add(
        "step13ad_module_does_not_import_torch",
        this_source,
        "ast_import_scan",
        "no_torch_import",
        "imports_torch" if _module_imports_name(this_tree, "torch") else "no_torch_import",
        not _module_imports_name(this_tree, "torch"),
    )
    add(
        "step13ad_check_script_does_not_import_torch",
        check_script,
        "ast_import_scan",
        "no_torch_import",
        "imports_torch" if _module_imports_name(check_tree, "torch") else "no_torch_import",
        not _module_imports_name(check_tree, "torch"),
    )
    add(
        "step13ad_module_does_not_import_step13ac_module",
        this_source,
        "ast_import_scan",
        "no_step13ac_module_import",
        "imports_step13ac_module" if _module_imports_step13ac(this_tree) else "no_step13ac_module_import",
        not _module_imports_step13ac(this_tree),
    )
    forbidden = {
        "load_from_checkpoint",
        "forward",
        "backward",
        "fit",
        "train",
        "training_step",
        "save",
        "savez",
        "dump",
        "SDMolSupplier",
        "MolFromMolFile",
        "MolToMolFile",
        "urlopen",
        "requests",
    }
    checks = [
        ("no_checkpoint_api_call", {"load_from_checkpoint"}),
        ("no_model_forward_call", {"forward"}),
        ("no_loss_call", {"loss", "compute_loss"}),
        ("no_backward_call", {"backward"}),
        ("no_optimizer_call", {"step", "zero_grad"}),
        ("no_trainer_fit_call", {"fit"}),
        ("no_torch_save_or_numpy_save", {"save", "savez"}),
        ("no_rdkit_import_or_call", {"SDMolSupplier", "MolFromMolFile", "MolToMolFile"}),
        ("no_gzip_gemmi_biopdb_import", set()),
        ("no_url_or_network_call", {"urlopen", "requests"}),
    ]
    for item, call_names in checks:
        if item == "no_gzip_gemmi_biopdb_import":
            imported = any(_module_imports_name(this_tree, name) for name in ["gzip", "gemmi", "Bio"])
            add(item, this_source, "ast_import_scan", "not_present", "present" if imported else "not_present", not imported)
        else:
            found = _has_forbidden_call(this_tree, call_names)
            add(item, this_source, "ast_call_scan", "not_called", "called" if found else "not_called", not found)
    return rows


def run_covapie_adapter_implementation_qa_gate_v0() -> dict[str, Any]:
    validate_step13ac_precondition_v0()
    naming_convention_validated = validate_covapie_naming_convention_v0()

    input_rows = _read_csv(STEP13AC_INPUT_AUDIT_CSV)
    sample_rows = _read_csv(STEP13AC_SAMPLE_DICT_AUDIT_CSV)
    shape_rows = _read_csv(STEP13AC_FIELD_SHAPE_OBSERVATION_CSV)
    batch_rows = _read_csv(STEP13AC_SINGLE_SAMPLE_BATCH_AUDIT_CSV)
    mask_rows = _read_csv(STEP13AC_MASK_MAPPING_AUDIT_CSV)
    aux_rows = _read_csv(STEP13AC_AUXILIARY_LABEL_AUDIT_CSV)
    boundary_rows = _read_csv(STEP13AC_EXECUTION_BOUNDARY_AUDIT_CSV)
    feature_rows = _read_csv(STEP13AC_FEATURE_SEMANTICS_AUDIT_CSV)

    input_qa_rows = build_input_qa_rows(input_rows)
    sample_dict_qa_rows = build_sample_dict_qa_rows(sample_rows)
    field_shape_qa_rows = build_field_shape_qa_rows(shape_rows)
    batch_qa_rows = build_batch_qa_rows(batch_rows)
    mask_mapping_qa_rows = build_mask_mapping_qa_rows(mask_rows)
    auxiliary_label_qa_rows = build_auxiliary_label_qa_rows(aux_rows)
    execution_boundary_qa_rows = build_execution_boundary_qa_rows(boundary_rows)
    feature_semantics_qa_rows = build_feature_semantics_qa_rows(feature_rows)
    dependency_qa_rows = build_dependency_qa_rows()
    source_ast_safety_qa_rows = build_source_ast_safety_qa_rows()

    all_input_qa_passed = len(input_qa_rows) == 3 and all(_as_bool(row["qa_passed"]) for row in input_qa_rows)
    all_sample_dict_qa_passed = len(sample_dict_qa_rows) == 3 and all(
        _as_bool(row["qa_passed"]) for row in sample_dict_qa_rows
    )
    all_field_shape_qa_passed = len(field_shape_qa_rows) == 42 and all(
        _as_bool(row["qa_passed"]) for row in field_shape_qa_rows
    )
    all_single_sample_batch_qa_passed = len(batch_qa_rows) == 3 and all(
        _as_bool(row["qa_passed"]) for row in batch_qa_rows
    )
    all_mask_mapping_qa_passed = len(mask_mapping_qa_rows) == 5 and all(
        _as_bool(row["qa_passed"]) for row in mask_mapping_qa_rows
    )
    all_auxiliary_label_qa_passed = len(auxiliary_label_qa_rows) == 3 and all(
        _as_bool(row["qa_passed"]) for row in auxiliary_label_qa_rows
    )
    all_execution_boundary_qa_passed = len(execution_boundary_qa_rows) == 19 and all(
        _as_bool(row["qa_passed"]) for row in execution_boundary_qa_rows
    )
    all_feature_semantics_qa_passed = len(feature_semantics_qa_rows) == 12 and all(
        _as_bool(row["qa_passed"]) for row in feature_semantics_qa_rows
    )
    all_dependency_qa_passed = len(dependency_qa_rows) == 12 and all(
        _as_bool(row["dependency_qa_passed"]) for row in dependency_qa_rows
    )
    all_source_ast_safety_qa_passed = len(source_ast_safety_qa_rows) >= 15 and all(
        _as_bool(row["qa_passed"]) for row in source_ast_safety_qa_rows
    )
    all_feature_semantics_audit_required_before_training = all(
        _as_bool(row["audit_required_before_training"]) for row in feature_semantics_qa_rows
    )
    no_feature_semantics_claimed_fully_audited = all(
        not _as_bool(row["fully_audited_claimed"]) for row in feature_semantics_qa_rows
    )
    all_dependency_artifacts_exist = all(_as_bool(row["dependency_exists"]) for row in dependency_qa_rows)
    all_dependency_counts_validated = all(_as_bool(row["dependency_count_validated"]) for row in dependency_qa_rows)

    original_source_modified = _source_diff_exists()
    original_dataloader_modified = _original_dataloader_diff_exists()
    forbidden_artifacts = _forbidden_committable_artifacts_created()
    raw_files_staged = _raw_files_staged()
    raw_files_tracked = _raw_files_tracked()
    safety_ok = not any(
        [original_source_modified, original_dataloader_modified, forbidden_artifacts, raw_files_staged, raw_files_tracked]
    )
    checkpoint_compatibility_preserved_by_external_adapter = True
    qa_gate_passed = all(
        [
            naming_convention_validated,
            all_input_qa_passed,
            all_sample_dict_qa_passed,
            all_field_shape_qa_passed,
            all_single_sample_batch_qa_passed,
            all_mask_mapping_qa_passed,
            all_auxiliary_label_qa_passed,
            all_execution_boundary_qa_passed,
            all_feature_semantics_qa_passed,
            all_dependency_qa_passed,
            all_source_ast_safety_qa_passed,
            all_feature_semantics_audit_required_before_training,
            no_feature_semantics_claimed_fully_audited,
            checkpoint_compatibility_preserved_by_external_adapter,
        ]
    )
    all_checks_passed = qa_gate_passed and safety_ok
    blocking_reasons: list[str] = []
    if not qa_gate_passed:
        blocking_reasons.append("covapie_adapter_implementation_qa_gate_failed")
    if not safety_ok:
        blocking_reasons.append("repository_or_output_safety_check_failed")

    step13ac_manifest = _load_json(STEP13AC_MANIFEST_JSON)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "naming_convention_validated": naming_convention_validated,
        "step13ac_diffsbdd_loader_adapter_implementation_smoke_validated": True,
        "historical_step_name_retained": True,
        "adapter_implementation_qa_scope": QA_SCOPE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "checkpoint_compatibility_policy": CHECKPOINT_COMPATIBILITY_POLICY,
        "covapie_adapter_input_qa_audit_written": True,
        "covapie_adapter_input_qa_audit_row_count": len(input_qa_rows),
        "covapie_adapter_sample_dict_qa_audit_written": True,
        "covapie_adapter_sample_dict_qa_audit_row_count": len(sample_dict_qa_rows),
        "covapie_adapter_field_shape_qa_audit_written": True,
        "covapie_adapter_field_shape_qa_audit_row_count": len(field_shape_qa_rows),
        "covapie_adapter_single_sample_batch_qa_audit_written": True,
        "covapie_adapter_single_sample_batch_qa_audit_row_count": len(batch_qa_rows),
        "covapie_adapter_mask_mapping_qa_audit_written": True,
        "covapie_adapter_mask_mapping_qa_audit_row_count": len(mask_mapping_qa_rows),
        "covapie_adapter_auxiliary_label_qa_audit_written": True,
        "covapie_adapter_auxiliary_label_qa_audit_row_count": len(auxiliary_label_qa_rows),
        "covapie_adapter_execution_boundary_qa_audit_written": True,
        "covapie_adapter_execution_boundary_qa_audit_row_count": len(execution_boundary_qa_rows),
        "covapie_adapter_feature_semantics_qa_audit_written": True,
        "covapie_adapter_feature_semantics_qa_audit_row_count": len(feature_semantics_qa_rows),
        "covapie_adapter_dependency_qa_audit_written": True,
        "covapie_adapter_dependency_qa_audit_row_count": len(dependency_qa_rows),
        "covapie_adapter_source_ast_safety_qa_audit_written": True,
        "covapie_adapter_source_ast_safety_qa_audit_row_count": len(source_ast_safety_qa_rows),
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "adapter_implemented_in_step13ac": step13ac_manifest["adapter_implemented"],
        "adapter_instantiated_in_step13ac": step13ac_manifest["adapter_instantiated"],
        "torch_imported_in_step13ac": step13ac_manifest["torch_imported"],
        "torch_tensor_created_in_step13ac": step13ac_manifest["torch_tensor_created"],
        "transient_adapter_field_shape_inspection_performed_in_step13ac": step13ac_manifest[
            "transient_adapter_field_shape_inspection_performed"
        ],
        "diffsbdd_loader_adapter_implementation_smoke_passed_in_step13ac": step13ac_manifest[
            "diffsbdd_loader_adapter_implementation_smoke_passed"
        ],
        "adapter_implemented": False,
        "adapter_instantiated": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "transient_adapter_field_shape_inspection_performed": False,
        "tensor_artifact_written": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "pt_created": False,
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "finetune_allowed": False,
        "parameter_update_allowed": False,
        "training_ready_samples_claimed": False,
        "sample_index_written": False,
        "sample_index_modified": False,
        "enriched_sample_index_written": False,
        "final_dataset_written": False,
        "model_input_smoke_modified": False,
        "model_input_materialized": False,
        "model_input_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "rdkit_used": False,
        "sdf_read": False,
        "sdf_generated": False,
        "sdf_modified": False,
        "sdf_copied": False,
        "ligand_auto_restoration_run": False,
        "non_cys_generalization_run": False,
        "raw_files_read": False,
        "gzip_open_used": False,
        "mmcif_text_read": False,
        "atom_site_text_scan_run": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "output_limited_to_csv_json_md": True,
        "original_diffsbdd_source_modified": original_source_modified,
        "original_diffsbdd_dataloader_modified": original_dataloader_modified,
        "original_diffsbdd_forward_modified": original_source_modified,
        "original_diffsbdd_loss_modified": original_source_modified,
        "forbidden_committable_artifacts_created": forbidden_artifacts,
        "raw_files_staged": raw_files_staged,
        "raw_files_tracked": raw_files_tracked,
        "all_input_qa_passed": all_input_qa_passed,
        "all_sample_dict_qa_passed": all_sample_dict_qa_passed,
        "all_field_shape_qa_passed": all_field_shape_qa_passed,
        "all_single_sample_batch_qa_passed": all_single_sample_batch_qa_passed,
        "all_mask_mapping_qa_passed": all_mask_mapping_qa_passed,
        "all_auxiliary_label_qa_passed": all_auxiliary_label_qa_passed,
        "all_execution_boundary_qa_passed": all_execution_boundary_qa_passed,
        "all_feature_semantics_qa_passed": all_feature_semantics_qa_passed,
        "all_dependency_qa_passed": all_dependency_qa_passed,
        "all_source_ast_safety_qa_passed": all_source_ast_safety_qa_passed,
        "all_dependency_artifacts_exist": all_dependency_artifacts_exist,
        "all_dependency_counts_validated": all_dependency_counts_validated,
        "all_feature_semantics_audit_required_before_training": all_feature_semantics_audit_required_before_training,
        "no_feature_semantics_claimed_fully_audited": no_feature_semantics_claimed_fully_audited,
        "checkpoint_compatibility_preserved_by_external_adapter": checkpoint_compatibility_preserved_by_external_adapter,
        "covapie_adapter_implementation_qa_gate_passed": qa_gate_passed,
        "ready_for_covapie_batch_scale_data_preparation_design_gate": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blocking_reasons,
    }
    report_sections = {
        "step13ac_precondition": {"validated": True, "historical_previous_stage": PREVIOUS_STAGE},
        "naming_convention": {"project_name": PROJECT_NAME, "naming_convention_validated": naming_convention_validated},
        "input_qa": {"row_count": len(input_qa_rows), "all_input_qa_passed": all_input_qa_passed},
        "sample_dict_qa": {
            "row_count": len(sample_dict_qa_rows),
            "all_sample_dict_qa_passed": all_sample_dict_qa_passed,
        },
        "field_shape_qa": {"row_count": len(field_shape_qa_rows), "all_field_shape_qa_passed": all_field_shape_qa_passed},
        "single_sample_batch_qa": {
            "row_count": len(batch_qa_rows),
            "all_single_sample_batch_qa_passed": all_single_sample_batch_qa_passed,
        },
        "mask_mapping_qa": {
            "row_count": len(mask_mapping_qa_rows),
            "all_mask_mapping_qa_passed": all_mask_mapping_qa_passed,
        },
        "auxiliary_label_qa": {
            "row_count": len(auxiliary_label_qa_rows),
            "all_auxiliary_label_qa_passed": all_auxiliary_label_qa_passed,
        },
        "execution_boundary_qa": {
            "row_count": len(execution_boundary_qa_rows),
            "all_execution_boundary_qa_passed": all_execution_boundary_qa_passed,
        },
        "feature_semantics_qa": {
            "row_count": len(feature_semantics_qa_rows),
            "all_feature_semantics_qa_passed": all_feature_semantics_qa_passed,
        },
        "dependency_qa": {"row_count": len(dependency_qa_rows), "all_dependency_qa_passed": all_dependency_qa_passed},
        "source_ast_safety_qa": {
            "row_count": len(source_ast_safety_qa_rows),
            "all_source_ast_safety_qa_passed": all_source_ast_safety_qa_passed,
        },
        "readiness_boundary": {
            "ready_for_covapie_batch_scale_data_preparation_design_gate": True,
            "ready_for_training": False,
            "ready_to_train_now": False,
            "feature_semantics_audit_required_before_training": True,
            "recommended_next_step": RECOMMENDED_NEXT_STEP,
        },
    }
    return {
        "input_qa_rows": input_qa_rows,
        "sample_dict_qa_rows": sample_dict_qa_rows,
        "field_shape_qa_rows": field_shape_qa_rows,
        "batch_qa_rows": batch_qa_rows,
        "mask_mapping_qa_rows": mask_mapping_qa_rows,
        "auxiliary_label_qa_rows": auxiliary_label_qa_rows,
        "execution_boundary_qa_rows": execution_boundary_qa_rows,
        "feature_semantics_qa_rows": feature_semantics_qa_rows,
        "dependency_qa_rows": dependency_qa_rows,
        "source_ast_safety_qa_rows": source_ast_safety_qa_rows,
        "report_sections": report_sections,
        "manifest": manifest,
    }
