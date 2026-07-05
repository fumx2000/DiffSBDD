from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke_v0"

STEP13Z_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke_v0"
)
STEP13Z_MANIFEST_JSON = STEP13Z_ROOT / "loader_shape_dry_run_execution_smoke_manifest.json"
STEP13Z_SAMPLE_AUDIT_CSV = STEP13Z_ROOT / "loader_shape_dry_run_sample_audit.csv"
STEP13Z_SHAPE_OBSERVATION_CSV = STEP13Z_ROOT / "loader_shape_dry_run_shape_observation.csv"
STEP13Z_BATCH_AUDIT_CSV = STEP13Z_ROOT / "loader_shape_dry_run_batch_audit.csv"
STEP13Z_EXECUTION_BOUNDARY_AUDIT_CSV = STEP13Z_ROOT / "loader_shape_dry_run_execution_boundary_audit.csv"
STEP13Z_FEATURE_SEMANTICS_AUDIT_CSV = STEP13Z_ROOT / "loader_shape_dry_run_feature_semantics_audit.csv"

STEP13Y_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate_v0"
)
STEP13Y_INPUT_CONTRACT_CSV = STEP13Y_ROOT / "loader_shape_dry_run_input_contract.csv"
STEP13Y_SHAPE_EXPECTATION_CONTRACT_CSV = STEP13Y_ROOT / "loader_shape_dry_run_shape_expectation_contract.csv"
STEP13Y_EXECUTION_BOUNDARY_CONTRACT_CSV = STEP13Y_ROOT / "loader_shape_dry_run_execution_boundary_contract.csv"
STEP13Y_FEATURE_SEMANTICS_BOUNDARY_CSV = STEP13Y_ROOT / "loader_shape_dry_run_feature_semantics_boundary.csv"

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate_v0"
)
SAMPLE_QA_AUDIT_CSV = OUTPUT_ROOT / "loader_shape_dry_run_sample_qa_audit.csv"
SHAPE_OBSERVATION_QA_AUDIT_CSV = OUTPUT_ROOT / "loader_shape_dry_run_shape_observation_qa_audit.csv"
BATCH_QA_AUDIT_CSV = OUTPUT_ROOT / "loader_shape_dry_run_batch_qa_audit.csv"
EXECUTION_BOUNDARY_QA_AUDIT_CSV = OUTPUT_ROOT / "loader_shape_dry_run_execution_boundary_qa_audit.csv"
FEATURE_SEMANTICS_QA_AUDIT_CSV = OUTPUT_ROOT / "loader_shape_dry_run_feature_semantics_qa_audit.csv"
DEPENDENCY_QA_AUDIT_CSV = OUTPUT_ROOT / "loader_shape_dry_run_dependency_qa_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "loader_shape_dry_run_qa_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "loader_shape_dry_run_qa_manifest.json"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate_v0_summary.md")

EXPECTED_LOADER_SHAPE_DRY_RUN_SAMPLE_IDS = ["LSDR_DESIGN_000001", "LSDR_DESIGN_000002", "LSDR_DESIGN_000003"]
EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS = ["RMI_SMOKE_000001", "RMI_SMOKE_000002", "RMI_SMOKE_000003"]
EXPECTED_SAMPLE_INDEX_ROW_IDS = ["RSIDX_000001", "RSIDX_000002", "RSIDX_000003"]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_ATOM_BOND_COUNTS = {"HR_0002": (33, 35), "HR_0003": (30, 33), "HR_0004": (41, 45)}
V1_TRAIN_READY_SCOPE = "cys_sg_with_known_restoration_template_only"
QA_SCOPE = "current_cys_sg_golden_samples_only"
RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate"
CANONICAL_MASK_TASK_NAMES = [
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
]
CANONICAL_MASK_TASK_ALIASES = ["A", "B", "B2", "B3", "C"]

PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]
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

SAMPLE_QA_COLUMNS = [
    "loader_shape_dry_run_sample_id",
    "model_input_smoke_row_id",
    "sample_index_row_id",
    "review_row_id",
    "pdb_id",
    "sample_audit_row_found",
    "expected_identity_validated",
    "sample_shape_dry_run_passed",
    "dataset_row_found",
    "loader_batch_seen",
    "cys_sg_scope_validated",
    "ligand_counts_validated",
    "endpoint_counts_validated",
    "canonical_masks_validated",
    "transient_tensors_created_in_step13z",
    "tensor_artifact_written",
    "model_forward_called",
    "loss_compute_called",
    "training_ready",
    "sample_qa_passed",
    "blocking_reasons",
]
SHAPE_OBSERVATION_QA_COLUMNS = [
    "loader_shape_dry_run_sample_id",
    "review_row_id",
    "shape_item",
    "expected_rank",
    "observed_rank",
    "expected_first_dimension_source",
    "expected_first_dimension_value",
    "observed_shape",
    "observed_dtype_family",
    "shape_observation_status",
    "tensor_persisted",
    "shape_observation_passed",
    "shape_contract_consistency_validated",
    "shape_qa_passed",
    "blocking_reasons",
]
BATCH_QA_COLUMNS = [
    "batch_index",
    "loader_shape_dry_run_sample_id",
    "model_input_smoke_row_id",
    "batch_size",
    "collate_status",
    "batch_shape_checked",
    "batch_order_validated",
    "model_forward_called",
    "loss_compute_called",
    "backward_called",
    "optimizer_step_called",
    "training_step_called",
    "batch_audit_passed",
    "batch_qa_passed",
    "blocking_reasons",
]
EXECUTION_BOUNDARY_QA_COLUMNS = [
    "boundary_item",
    "observed_current_step_status",
    "boundary_respected",
    "training_forbidden_respected",
    "artifact_forbidden_respected",
    "boundary_audit_passed",
    "boundary_qa_passed",
    "blocking_reasons",
]
FEATURE_SEMANTICS_QA_COLUMNS = [
    "feature_semantics_item",
    "feature_group",
    "current_status",
    "audit_required_before_training",
    "fully_audited_claimed",
    "blocking_for_loader_shape_dry_run_execution_smoke",
    "training_ready",
    "recommended_audit_step",
    "feature_semantics_execution_audit_passed",
    "feature_semantics_qa_passed",
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
    if path.suffix == ".json":
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


def _source_diff_exists() -> bool:
    unstaged = _run_git(["diff", "--quiet", "--", *PROTECTED_SOURCE_PATHS])
    staged = _run_git(["diff", "--cached", "--quiet", "--", *PROTECTED_SOURCE_PATHS])
    return unstaged.returncode != 0 or staged.returncode != 0


def _forbidden_committable_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in FORBIDDEN_COMMITTABLE_SUFFIXES for path in root_path.rglob("*"))


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", "data/raw/covalent_sources"]).stdout.strip())


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", "data/raw/covalent_sources"]).stdout.strip())


def validate_step13z_precondition_v0() -> bool:
    required_paths = [
        STEP13Z_MANIFEST_JSON,
        STEP13Z_SAMPLE_AUDIT_CSV,
        STEP13Z_SHAPE_OBSERVATION_CSV,
        STEP13Z_BATCH_AUDIT_CSV,
        STEP13Z_EXECUTION_BOUNDARY_AUDIT_CSV,
        STEP13Z_FEATURE_SEMANTICS_AUDIT_CSV,
        STEP13Y_INPUT_CONTRACT_CSV,
        STEP13Y_SHAPE_EXPECTATION_CONTRACT_CSV,
        STEP13Y_EXECUTION_BOUNDARY_CONTRACT_CSV,
        STEP13Y_FEATURE_SEMANTICS_BOUNDARY_CSV,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13AA prerequisite outputs are missing: {missing}")

    manifest = _load_json(STEP13Z_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "all_checks_passed": True,
        "step13y_loader_shape_dry_run_design_gate_validated": True,
        "loader_shape_dry_run_execution_scope": QA_SCOPE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "loader_shape_dry_run_sample_audit_written": True,
        "loader_shape_dry_run_sample_audit_row_count": 3,
        "loader_shape_dry_run_shape_observation_written": True,
        "loader_shape_dry_run_shape_observation_row_count": 42,
        "loader_shape_dry_run_batch_audit_written": True,
        "loader_shape_dry_run_batch_audit_row_count": 3,
        "loader_shape_dry_run_execution_boundary_audit_written": True,
        "loader_shape_dry_run_execution_boundary_audit_row_count": 14,
        "loader_shape_dry_run_feature_semantics_audit_written": True,
        "loader_shape_dry_run_feature_semantics_audit_row_count": 12,
        "canonical_mask_task_count": 5,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "smoke_dataset_instantiated": True,
        "loader_instantiated": True,
        "loader_batch_size": 1,
        "loader_batch_count": 3,
        "torch_imported": True,
        "torch_tensor_created": True,
        "transient_tensor_shape_inspection_performed": True,
        "all_loader_batches_seen": True,
        "all_sample_shape_dry_run_passed": True,
        "all_shape_observations_passed": True,
        "all_batch_audits_passed": True,
        "all_execution_boundaries_respected": True,
        "all_feature_semantics_audit_required_before_training": True,
        "no_feature_semantics_claimed_fully_audited": True,
        "loader_shape_dry_run_execution_smoke_passed": True,
        "tensor_artifact_written": False,
        "npz_created": False,
        "pt_created": False,
        "dataloader_modified": False,
        "forward_modified": False,
        "loss_modified": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "ready_for_loader_shape_dry_run_qa_gate": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": "real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate",
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("canonical_mask_task_names") != CANONICAL_MASK_TASK_NAMES:
        blockers.append("canonical_mask_task_names")
    if manifest.get("canonical_mask_task_aliases") != CANONICAL_MASK_TASK_ALIASES:
        blockers.append("canonical_mask_task_aliases")
    if blockers:
        raise ValueError("Step 13Z precondition failed: " + ";".join(blockers))
    return True


def build_sample_qa_rows_v0(sample_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    expected = zip(
        EXPECTED_LOADER_SHAPE_DRY_RUN_SAMPLE_IDS,
        EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS,
        EXPECTED_SAMPLE_INDEX_ROW_IDS,
        EXPECTED_REVIEW_ROW_IDS,
        EXPECTED_PDB_IDS,
        strict=True,
    )
    by_id = {row["loader_shape_dry_run_sample_id"]: row for row in sample_rows}
    for sample_id, model_input_id, sample_index_id, review_id, pdb_id in expected:
        row = by_id.get(sample_id, {})
        found = bool(row)
        identity = (
            found
            and row.get("model_input_smoke_row_id") == model_input_id
            and row.get("sample_index_row_id") == sample_index_id
            and row.get("review_row_id") == review_id
            and row.get("pdb_id") == pdb_id
        )
        true_checks = {
            key: _as_bool(row.get(key, False))
            for key in [
                "sample_shape_dry_run_passed",
                "dataset_row_found",
                "loader_batch_seen",
                "cys_sg_scope_validated",
                "ligand_counts_validated",
                "endpoint_counts_validated",
                "canonical_masks_validated",
                "transient_tensors_created",
            ]
        }
        false_checks = {
            key: not _as_bool(row.get(key, True))
            for key in ["tensor_artifact_written", "model_forward_called", "loss_compute_called", "training_ready"]
        }
        passed = found and identity and all(true_checks.values()) and all(false_checks.values()) and not row.get("blocking_reasons")
        rows.append(
            {
                "loader_shape_dry_run_sample_id": sample_id,
                "model_input_smoke_row_id": model_input_id,
                "sample_index_row_id": sample_index_id,
                "review_row_id": review_id,
                "pdb_id": pdb_id,
                "sample_audit_row_found": found,
                "expected_identity_validated": identity,
                "sample_shape_dry_run_passed": true_checks["sample_shape_dry_run_passed"],
                "dataset_row_found": true_checks["dataset_row_found"],
                "loader_batch_seen": true_checks["loader_batch_seen"],
                "cys_sg_scope_validated": true_checks["cys_sg_scope_validated"],
                "ligand_counts_validated": true_checks["ligand_counts_validated"],
                "endpoint_counts_validated": true_checks["endpoint_counts_validated"],
                "canonical_masks_validated": true_checks["canonical_masks_validated"],
                "transient_tensors_created_in_step13z": true_checks["transient_tensors_created"],
                "tensor_artifact_written": False,
                "model_forward_called": False,
                "loss_compute_called": False,
                "training_ready": False,
                "sample_qa_passed": passed,
                "blocking_reasons": "" if passed else "sample_qa_failed",
            }
        )
    return rows


def build_shape_observation_qa_rows_v0(
    shape_rows: list[dict[str, str]], shape_contract_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    contract_by_item = {row["shape_item"]: row for row in shape_contract_rows}
    seen: set[tuple[str, str]] = set()
    rows = []
    for row in shape_rows:
        key = (row["loader_shape_dry_run_sample_id"], row["shape_item"])
        duplicate = key in seen
        seen.add(key)
        contract = contract_by_item.get(row["shape_item"], {})
        expected_rank = contract.get("expected_rank", row["expected_rank"])
        expected_source = contract.get("expected_first_dimension_source", row["expected_first_dimension_source"])
        expected_value = contract.get("expected_first_dimension_value", row["expected_first_dimension_value"])
        contract_consistent = (
            str(row["expected_rank"]) == str(expected_rank)
            and row["expected_first_dimension_source"] == expected_source
            and row["expected_first_dimension_value"] == expected_value
        )
        shape_passed = (
            not duplicate
            and row["shape_item"] in contract_by_item
            and _as_bool(row["shape_observation_passed"])
            and not _as_bool(row["tensor_persisted"])
            and row["shape_observation_status"] == "observed_in_transient_shape_smoke"
            and contract_consistent
            and not row.get("blocking_reasons")
        )
        rows.append(
            {
                "loader_shape_dry_run_sample_id": row["loader_shape_dry_run_sample_id"],
                "review_row_id": row["review_row_id"],
                "shape_item": row["shape_item"],
                "expected_rank": expected_rank,
                "observed_rank": row["observed_rank"],
                "expected_first_dimension_source": expected_source,
                "expected_first_dimension_value": expected_value,
                "observed_shape": row["observed_shape"],
                "observed_dtype_family": row["observed_dtype_family"],
                "shape_observation_status": row["shape_observation_status"],
                "tensor_persisted": False,
                "shape_observation_passed": _as_bool(row["shape_observation_passed"]),
                "shape_contract_consistency_validated": contract_consistent,
                "shape_qa_passed": shape_passed,
                "blocking_reasons": "" if shape_passed else "shape_observation_qa_failed",
            }
        )
    return rows


def build_batch_qa_rows_v0(batch_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(batch_rows):
        batch_passed = (
            int(row["batch_index"]) == index
            and row["loader_shape_dry_run_sample_id"] == EXPECTED_LOADER_SHAPE_DRY_RUN_SAMPLE_IDS[index]
            and row["model_input_smoke_row_id"] == EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS[index]
            and int(row["batch_size"]) == 1
            and row["collate_status"] == "single_sample_collate_no_padding_no_training"
            and _as_bool(row["batch_shape_checked"])
            and _as_bool(row["batch_order_validated"])
            and _as_bool(row["batch_audit_passed"])
            and not any(
                _as_bool(row[key])
                for key in [
                    "model_forward_called",
                    "loss_compute_called",
                    "backward_called",
                    "optimizer_step_called",
                    "training_step_called",
                ]
            )
            and not row.get("blocking_reasons")
        )
        rows.append(
            {
                "batch_index": row["batch_index"],
                "loader_shape_dry_run_sample_id": row["loader_shape_dry_run_sample_id"],
                "model_input_smoke_row_id": row["model_input_smoke_row_id"],
                "batch_size": row["batch_size"],
                "collate_status": row["collate_status"],
                "batch_shape_checked": _as_bool(row["batch_shape_checked"]),
                "batch_order_validated": _as_bool(row["batch_order_validated"]),
                "model_forward_called": False,
                "loss_compute_called": False,
                "backward_called": False,
                "optimizer_step_called": False,
                "training_step_called": False,
                "batch_audit_passed": _as_bool(row["batch_audit_passed"]),
                "batch_qa_passed": batch_passed,
                "blocking_reasons": "" if batch_passed else "batch_qa_failed",
            }
        )
    return rows


def build_execution_boundary_qa_rows_v0(boundary_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    expected_status = {
        "loader_instantiation": "executed_allowed_for_shape_inspection",
        "torch_tensor_creation": "executed_transient_in_memory_for_shape_inspection",
        "feature_semantics_audit": "required_before_training_not_completed",
    }
    rows = []
    for row in boundary_rows:
        item = row["boundary_item"]
        expected = expected_status.get(item, "not_executed_or_not_allowed")
        passed = (
            row["observed_current_step_status"] == expected
            and _as_bool(row["boundary_respected"])
            and _as_bool(row["boundary_audit_passed"])
            and _as_bool(row["training_forbidden_respected"])
            and _as_bool(row["artifact_forbidden_respected"])
            and not row.get("blocking_reasons")
        )
        rows.append(
            {
                "boundary_item": item,
                "observed_current_step_status": row["observed_current_step_status"],
                "boundary_respected": _as_bool(row["boundary_respected"]),
                "training_forbidden_respected": _as_bool(row["training_forbidden_respected"]),
                "artifact_forbidden_respected": _as_bool(row["artifact_forbidden_respected"]),
                "boundary_audit_passed": _as_bool(row["boundary_audit_passed"]),
                "boundary_qa_passed": passed,
                "blocking_reasons": "" if passed else "execution_boundary_qa_failed",
            }
        )
    return rows


def build_feature_semantics_qa_rows_v0(feature_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for row in feature_rows:
        passed = (
            _as_bool(row["audit_required_before_training"])
            and not _as_bool(row["fully_audited_claimed"])
            and not _as_bool(row["blocking_for_loader_shape_dry_run_execution_smoke"])
            and not _as_bool(row["training_ready"])
            and bool(row["recommended_audit_step"])
            and _as_bool(row["feature_semantics_execution_audit_passed"])
            and not row.get("blocking_reasons")
        )
        rows.append(
            {
                "feature_semantics_item": row["feature_semantics_item"],
                "feature_group": row["feature_group"],
                "current_status": row["current_status"],
                "audit_required_before_training": _as_bool(row["audit_required_before_training"]),
                "fully_audited_claimed": _as_bool(row["fully_audited_claimed"]),
                "blocking_for_loader_shape_dry_run_execution_smoke": _as_bool(
                    row["blocking_for_loader_shape_dry_run_execution_smoke"]
                ),
                "training_ready": _as_bool(row["training_ready"]),
                "recommended_audit_step": row["recommended_audit_step"],
                "feature_semantics_execution_audit_passed": _as_bool(row["feature_semantics_execution_audit_passed"]),
                "feature_semantics_qa_passed": passed,
                "blocking_reasons": "" if passed else "feature_semantics_qa_failed",
            }
        )
    return rows


def build_dependency_qa_rows_v0() -> list[dict[str, Any]]:
    dependencies = [
        ("step13z_manifest", STEP13Z_MANIFEST_JSON, 1),
        ("step13z_sample_audit", STEP13Z_SAMPLE_AUDIT_CSV, 3),
        ("step13z_shape_observation", STEP13Z_SHAPE_OBSERVATION_CSV, 42),
        ("step13z_batch_audit", STEP13Z_BATCH_AUDIT_CSV, 3),
        ("step13z_execution_boundary_audit", STEP13Z_EXECUTION_BOUNDARY_AUDIT_CSV, 14),
        ("step13z_feature_semantics_audit", STEP13Z_FEATURE_SEMANTICS_AUDIT_CSV, 12),
        ("step13y_input_contract", STEP13Y_INPUT_CONTRACT_CSV, 3),
        ("step13y_shape_expectation_contract", STEP13Y_SHAPE_EXPECTATION_CONTRACT_CSV, 14),
        ("step13y_execution_boundary_contract", STEP13Y_EXECUTION_BOUNDARY_CONTRACT_CSV, 14),
        ("step13y_feature_semantics_boundary", STEP13Y_FEATURE_SEMANTICS_BOUNDARY_CSV, 12),
    ]
    rows = []
    for name, path, expected_count in dependencies:
        exists = path.is_file()
        count = _row_count(path)
        count_validated = exists and count == expected_count
        passed = exists and count_validated
        rows.append(
            {
                "dependency_name": name,
                "dependency_artifact_path": str(path),
                "dependency_exists": exists,
                "dependency_row_count": count,
                "dependency_expected_row_count": expected_count,
                "dependency_count_validated": count_validated,
                "dependency_qa_passed": passed,
                "blocking_reasons": "" if passed else "dependency_qa_failed",
            }
        )
    return rows


def run_loader_shape_dry_run_qa_gate_v0() -> dict[str, Any]:
    validate_step13z_precondition_v0()
    step13z_manifest = _load_json(STEP13Z_MANIFEST_JSON)
    sample_rows = _read_csv(STEP13Z_SAMPLE_AUDIT_CSV)
    shape_rows = _read_csv(STEP13Z_SHAPE_OBSERVATION_CSV)
    batch_rows = _read_csv(STEP13Z_BATCH_AUDIT_CSV)
    boundary_rows = _read_csv(STEP13Z_EXECUTION_BOUNDARY_AUDIT_CSV)
    feature_rows = _read_csv(STEP13Z_FEATURE_SEMANTICS_AUDIT_CSV)
    shape_contract_rows = _read_csv(STEP13Y_SHAPE_EXPECTATION_CONTRACT_CSV)

    sample_qa_rows = build_sample_qa_rows_v0(sample_rows)
    shape_observation_qa_rows = build_shape_observation_qa_rows_v0(shape_rows, shape_contract_rows)
    batch_qa_rows = build_batch_qa_rows_v0(batch_rows)
    execution_boundary_qa_rows = build_execution_boundary_qa_rows_v0(boundary_rows)
    feature_semantics_qa_rows = build_feature_semantics_qa_rows_v0(feature_rows)
    dependency_qa_rows = build_dependency_qa_rows_v0()

    shape_counts_by_sample: dict[str, int] = {}
    for row in shape_observation_qa_rows:
        shape_counts_by_sample[row["loader_shape_dry_run_sample_id"]] = (
            shape_counts_by_sample.get(row["loader_shape_dry_run_sample_id"], 0) + 1
        )

    all_sample_qa_passed = len(sample_qa_rows) == 3 and all(_as_bool(row["sample_qa_passed"]) for row in sample_qa_rows)
    all_shape_observation_qa_passed = (
        len(shape_observation_qa_rows) == 42
        and set(shape_counts_by_sample.values()) == {14}
        and len({(row["loader_shape_dry_run_sample_id"], row["shape_item"]) for row in shape_observation_qa_rows}) == 42
        and all(_as_bool(row["shape_qa_passed"]) for row in shape_observation_qa_rows)
    )
    all_batch_qa_passed = len(batch_qa_rows) == 3 and all(_as_bool(row["batch_qa_passed"]) for row in batch_qa_rows)
    all_execution_boundary_qa_passed = len(execution_boundary_qa_rows) == 14 and all(
        _as_bool(row["boundary_qa_passed"]) for row in execution_boundary_qa_rows
    )
    all_feature_semantics_qa_passed = len(feature_semantics_qa_rows) == 12 and all(
        _as_bool(row["feature_semantics_qa_passed"]) for row in feature_semantics_qa_rows
    )
    all_dependency_artifacts_exist = all(_as_bool(row["dependency_exists"]) for row in dependency_qa_rows)
    all_dependency_counts_validated = all(_as_bool(row["dependency_count_validated"]) for row in dependency_qa_rows)
    all_feature_semantics_audit_required_before_training = all(
        _as_bool(row["audit_required_before_training"]) for row in feature_semantics_qa_rows
    )
    no_feature_semantics_claimed_fully_audited = all(
        not _as_bool(row["fully_audited_claimed"]) for row in feature_semantics_qa_rows
    )
    loader_shape_dry_run_qa_gate_passed = all(
        [
            all_sample_qa_passed,
            all_shape_observation_qa_passed,
            all_batch_qa_passed,
            all_execution_boundary_qa_passed,
            all_feature_semantics_qa_passed,
            all_dependency_artifacts_exist,
            all_dependency_counts_validated,
            all_feature_semantics_audit_required_before_training,
            no_feature_semantics_claimed_fully_audited,
        ]
    )
    safety_ok = not any(
        [
            _source_diff_exists(),
            _forbidden_committable_artifacts_created(),
            _raw_files_staged(),
            _raw_files_tracked(),
        ]
    )
    all_checks_passed = loader_shape_dry_run_qa_gate_passed and safety_ok
    blocking_reasons = []
    if not loader_shape_dry_run_qa_gate_passed:
        blocking_reasons.append("loader_shape_dry_run_qa_gate_failed")
    if not safety_ok:
        blocking_reasons.append("repository_or_output_safety_check_failed")

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13z_loader_shape_dry_run_execution_smoke_validated": True,
        "loader_shape_dry_run_qa_scope": QA_SCOPE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "loader_shape_dry_run_sample_qa_audit_written": True,
        "loader_shape_dry_run_sample_qa_audit_row_count": len(sample_qa_rows),
        "loader_shape_dry_run_shape_observation_qa_audit_written": True,
        "loader_shape_dry_run_shape_observation_qa_audit_row_count": len(shape_observation_qa_rows),
        "loader_shape_dry_run_batch_qa_audit_written": True,
        "loader_shape_dry_run_batch_qa_audit_row_count": len(batch_qa_rows),
        "loader_shape_dry_run_execution_boundary_qa_audit_written": True,
        "loader_shape_dry_run_execution_boundary_qa_audit_row_count": len(execution_boundary_qa_rows),
        "loader_shape_dry_run_feature_semantics_qa_audit_written": True,
        "loader_shape_dry_run_feature_semantics_qa_audit_row_count": len(feature_semantics_qa_rows),
        "loader_shape_dry_run_dependency_qa_audit_written": True,
        "loader_shape_dry_run_dependency_qa_audit_row_count": len(dependency_qa_rows),
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_sample_qa_passed": all_sample_qa_passed,
        "all_shape_observation_qa_passed": all_shape_observation_qa_passed,
        "all_batch_qa_passed": all_batch_qa_passed,
        "all_execution_boundary_qa_passed": all_execution_boundary_qa_passed,
        "all_feature_semantics_qa_passed": all_feature_semantics_qa_passed,
        "all_dependency_artifacts_exist": all_dependency_artifacts_exist,
        "all_dependency_counts_validated": all_dependency_counts_validated,
        "all_feature_semantics_audit_required_before_training": all_feature_semantics_audit_required_before_training,
        "no_feature_semantics_claimed_fully_audited": no_feature_semantics_claimed_fully_audited,
        "loader_shape_dry_run_qa_gate_passed": loader_shape_dry_run_qa_gate_passed,
        "smoke_dataset_instantiated_in_step13z": step13z_manifest["smoke_dataset_instantiated"],
        "loader_instantiated_in_step13z": step13z_manifest["loader_instantiated"],
        "torch_tensor_created_in_step13z": step13z_manifest["torch_tensor_created"],
        "transient_tensor_shape_inspection_performed_in_step13z": step13z_manifest[
            "transient_tensor_shape_inspection_performed"
        ],
        "all_loader_batches_seen_in_step13z": step13z_manifest["all_loader_batches_seen"],
        "all_shape_observations_passed_in_step13z": step13z_manifest["all_shape_observations_passed"],
        "loader_shape_dry_run_execution_smoke_passed": step13z_manifest[
            "loader_shape_dry_run_execution_smoke_passed"
        ],
        "smoke_dataset_instantiated": False,
        "loader_instantiated": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "transient_tensor_shape_inspection_performed": False,
        "sample_index_written": False,
        "sample_index_modified": False,
        "enriched_sample_index_written": False,
        "final_dataset_written": False,
        "model_input_smoke_modified": False,
        "model_input_materialized": False,
        "model_input_written": False,
        "tensor_artifact_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "training_ready_samples_claimed": False,
        "training_allowed": False,
        "finetune_allowed": False,
        "parameter_update_allowed": False,
        "dataloader_modified": False,
        "forward_modified": False,
        "loss_modified": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "pt_created": False,
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
        "original_diffsbdd_source_modified": _source_diff_exists(),
        "forbidden_committable_artifacts_created": _forbidden_committable_artifacts_created(),
        "raw_files_staged": _raw_files_staged(),
        "raw_files_tracked": _raw_files_tracked(),
        "ready_for_diffsbdd_loader_adapter_design_gate": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blocking_reasons,
    }
    report_sections = {
        "step13z_precondition": {"validated": True, "execution_smoke_passed": True},
        "sample_qa": {"row_count": len(sample_qa_rows), "all_sample_qa_passed": all_sample_qa_passed},
        "shape_observation_qa": {
            "row_count": len(shape_observation_qa_rows),
            "all_shape_observation_qa_passed": all_shape_observation_qa_passed,
        },
        "batch_qa": {"row_count": len(batch_qa_rows), "all_batch_qa_passed": all_batch_qa_passed},
        "execution_boundary_qa": {
            "row_count": len(execution_boundary_qa_rows),
            "all_execution_boundary_qa_passed": all_execution_boundary_qa_passed,
        },
        "feature_semantics_qa": {
            "row_count": len(feature_semantics_qa_rows),
            "all_feature_semantics_qa_passed": all_feature_semantics_qa_passed,
        },
        "dependency_qa": {
            "row_count": len(dependency_qa_rows),
            "all_dependency_artifacts_exist": all_dependency_artifacts_exist,
            "all_dependency_counts_validated": all_dependency_counts_validated,
        },
        "readiness_boundary": {
            "ready_for_diffsbdd_loader_adapter_design_gate": True,
            "ready_for_training": False,
        },
    }
    return {
        "sample_qa_rows": sample_qa_rows,
        "shape_observation_qa_rows": shape_observation_qa_rows,
        "batch_qa_rows": batch_qa_rows,
        "execution_boundary_qa_rows": execution_boundary_qa_rows,
        "feature_semantics_qa_rows": feature_semantics_qa_rows,
        "dependency_qa_rows": dependency_qa_rows,
        "manifest": manifest,
        "report_sections": report_sections,
    }
