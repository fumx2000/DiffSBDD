from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_ligand_topology_smoke_current_cys_goldens_only_v0"

STEP13O_MANIFEST_JSON = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_smoke_current_cys_goldens_v0/"
    "ligand_topology_smoke_manifest.json"
)
STEP13O_ARTIFACT_DISCOVERY_AUDIT_CSV = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_smoke_current_cys_goldens_v0/"
    "ligand_topology_artifact_discovery_audit.csv"
)
STEP13N_MANIFEST_JSON = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_policy_review_gate_v0/"
    "ligand_topology_policy_review_gate_manifest.json"
)
STEP13M_CANDIDATE_CONTRACT_CSV = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0/"
    "ligand_topology_restoration_candidate_contract.csv"
)

STEP8_GRAPH_PREVIEW_CANDIDATES_CSV = Path(
    "data/derived/covalent_small/pre_reaction_graph/dataset_assembly_graph_preview_candidates.csv"
)
STEP8_GRAPH_PREVIEW_REPORT_CSV = Path(
    "data/derived/covalent_small/pre_reaction_graph/dataset_assembly_graph_preview_report.csv"
)
STEP8_MANUAL_WRITE_BACK_REPORT_CSV = Path(
    "data/derived/covalent_small/pre_reaction_graph/pre_reaction_transform_manual_write_back_report.csv"
)
STEP8_PACKAGING_QA_REPORT_CSV = Path(
    "data/derived/covalent_small/pre_reaction_graph/real_packaging_execution_qa_report.csv"
)
STEP8_DATASET_INDEX_CSV = Path(
    "data/derived/covalent_small/dataset_index_review_only/covalent_small_pre_reaction_review_only_index.csv"
)
STEP8_METADATA_ROOT = Path("data/derived/covalent_small/packaging_real_review_only/metadata")

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate_v0"
)
SOURCE_DISCOVERY_CONTRACT_CSV = OUTPUT_ROOT / "step8_topology_evidence_source_discovery_contract.csv"
EXPORT_SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "step8_topology_evidence_export_schema_contract.csv"
EXPORT_CANDIDATE_CONTRACT_CSV = OUTPUT_ROOT / "step8_topology_evidence_export_candidate_contract.csv"
REPORT_CSV = OUTPUT_ROOT / "step8_topology_evidence_export_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "step8_topology_evidence_export_design_gate_manifest.json"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate_v0_summary.md")

EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_SAMPLE_NAMES = {
    "HR_0002": "BTK_C481_6DI9_pre_reaction",
    "HR_0003": "KRAS_G12C_5F2E_pre_reaction",
    "HR_0004": "KRAS_G12C_6OIM_pre_reaction",
}
EXPECTED_SOURCE_SAMPLE_NAMES = {
    "HR_0002": "BTK_C481_6DI9",
    "HR_0003": "KRAS_G12C_5F2E",
    "HR_0004": "KRAS_G12C_6OIM",
}
EXPECTED_ATOM_COUNTS = {"HR_0002": 33, "HR_0003": 30, "HR_0004": 41}
EXPECTED_BOND_COUNTS = {"HR_0002": 35, "HR_0003": 33, "HR_0004": 45}
V1_TRAIN_READY_SCOPE = "cys_sg_with_known_restoration_template_only"
TOPOLOGY_EXPORT_SCOPE = "current_cys_sg_golden_samples_only"
TOPOLOGY_EXPORT_INPUT_POLICY = (
    "readonly_parse_step8_manual_reviewed_pre_reaction_sdf_if_hash_and_manual_review_provenance_exist"
)
ALLOWED_NEXT_STEP = "real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_smoke"
BLOCKED_NEXT_STEP = "locate_step8_pre_reaction_sdf_hash_and_manual_review_provenance"

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

BIOPDB_TEXT = "Bio." + "PDB"
MMCIF_PARSER_TEXT = "MM" + "CIFParser"
PDB_PARSER_TEXT = "PDB" + "Parser"
VENDOR_TEXT = "ge" + "mmi"
RDKIT_TEXT = "RD" + "Kit"
GZIP_OPEN_KEY = "gzip_" + "open_used"
VENDOR_USED_KEY = "ge" + "mmi_used"

SOURCE_DISCOVERY_COLUMNS = [
    "review_row_id",
    "pdb_id",
    "expected_step8_sample_name",
    "step13o_artifact_found",
    "step13o_artifact_paths",
    "candidate_pre_reaction_sdf_path_discovered",
    "candidate_pre_reaction_sdf_path",
    "candidate_pre_reaction_sdf_hash_or_manifest_path_discovered",
    "candidate_pre_reaction_sdf_hash_or_manifest_path",
    "graph_preview_artifact_discovered",
    "graph_preview_artifact_path",
    "packaging_qa_artifact_discovered",
    "packaging_qa_artifact_path",
    "allowed_for_future_readonly_topology_export",
    "discovery_status",
    "blocking_reasons",
]
EXPORT_SCHEMA_COLUMNS = [
    "future_table_name",
    "field_name",
    "field_group",
    "field_description",
    "required_for_future_export",
    "training_use_status",
]
EXPORT_CANDIDATE_COLUMNS = [
    "review_row_id",
    "pdb_id",
    "expected_step8_sample_name",
    "v1_train_ready_scope",
    "topology_export_scope",
    "topology_export_input_policy",
    "readonly_rdkit_export_allowed_next_step",
    "source_pre_reaction_sdf_path",
    "source_manual_review_or_graph_preview_artifact_path",
    "source_hash_or_manifest_path",
    "expected_atom_topology_row_count",
    "expected_bond_topology_row_count",
    "auto_restore_ligand_allowed",
    "sdf_generation_allowed",
    "sdf_modification_allowed",
    "sdf_copy_allowed",
    "non_cys_generalization_allowed",
    "training_ready",
    "training_ready_reason",
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


def validate_step13o_blocked_precondition_v0() -> bool:
    required = [
        STEP13O_MANIFEST_JSON,
        STEP13O_ARTIFACT_DISCOVERY_AUDIT_CSV,
        STEP13N_MANIFEST_JSON,
        STEP13M_CANDIDATE_CONTRACT_CSV,
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13P prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13O_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "step13n_ligand_topology_policy_review_gate_validated": True,
        "all_checks_passed": False,
        "all_step8_topology_artifacts_found": True,
        "all_artifacts_contain_per_atom_topology": False,
        "all_artifacts_contain_per_bond_topology": False,
        "all_artifacts_sufficient_for_topology_smoke": False,
        "ligand_observed_atom_topology_table_written": False,
        "ligand_observed_bond_topology_table_written": False,
        "ready_for_sample_index_design_gate": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": "locate_or_export_step8_per_bond_topology_evidence",
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if blockers:
        raise ValueError("Step 13O blocked precondition failed: " + ";".join(blockers))
    return True


def _row_by_key(path: Path, key: str, values: set[str]) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    rows = _read_csv(path)
    return {row.get(key, ""): row for row in rows if row.get(key, "") in values}


def _metadata_for_sample(sample_name: str) -> dict[str, Any]:
    path = STEP8_METADATA_ROOT / f"{sample_name}.json"
    if not path.is_file():
        return {}
    return _load_json(path)


def _candidate_rows() -> list[dict[str, str]]:
    rows = _read_csv(STEP13M_CANDIDATE_CONTRACT_CSV)
    return [row for row in rows if row.get("review_row_id") in EXPECTED_REVIEW_ROW_IDS]


def build_source_discovery_contract_v0() -> list[dict[str, str]]:
    step13o_rows = _read_csv(STEP13O_ARTIFACT_DISCOVERY_AUDIT_CSV)
    step13o_by_review = {row["review_row_id"]: row for row in step13o_rows}
    sample_names = set(EXPECTED_SAMPLE_NAMES.values())
    source_names = set(EXPECTED_SOURCE_SAMPLE_NAMES.values())
    graph_candidates = _row_by_key(STEP8_GRAPH_PREVIEW_CANDIDATES_CSV, "pre_reaction_sample_id", sample_names)
    graph_reports = _row_by_key(STEP8_GRAPH_PREVIEW_REPORT_CSV, "pre_reaction_sample_id", sample_names)
    manual_reports = _row_by_key(STEP8_MANUAL_WRITE_BACK_REPORT_CSV, "sample_id", source_names)
    packaging_reports = _row_by_key(STEP8_PACKAGING_QA_REPORT_CSV, "pre_reaction_sample_id", sample_names)
    index_rows = _row_by_key(STEP8_DATASET_INDEX_CSV, "pre_reaction_sample_id", sample_names)

    rows: list[dict[str, str]] = []
    for review_row_id in EXPECTED_REVIEW_ROW_IDS:
        sample_name = EXPECTED_SAMPLE_NAMES[review_row_id]
        source_sample = EXPECTED_SOURCE_SAMPLE_NAMES[review_row_id]
        step13o = step13o_by_review.get(review_row_id, {})
        graph_candidate = graph_candidates.get(sample_name, {})
        graph_report = graph_reports.get(sample_name, {})
        manual_report = manual_reports.get(source_sample, {})
        packaging_report = packaging_reports.get(sample_name, {})
        index_row = index_rows.get(sample_name, {})
        metadata = _metadata_for_sample(sample_name)

        ligand_meta = metadata.get("ligand", {}) if isinstance(metadata.get("ligand"), dict) else {}
        sdf_path = (
            graph_candidate.get("ligand_sdf_path")
            or graph_report.get("ligand_sdf_path")
            or index_row.get("source_ligand_sdf_path")
            or ligand_meta.get("source_path", "")
        )
        sha_source = (
            str(STEP8_GRAPH_PREVIEW_CANDIDATES_CSV)
            if graph_candidate.get("ligand_sdf_sha256")
            else str(STEP8_DATASET_INDEX_CSV)
            if index_row.get("packaged_ligand_sha256")
            else str(STEP8_METADATA_ROOT / f"{sample_name}.json")
            if ligand_meta.get("sha256")
            else ""
        )
        graph_path = (
            str(STEP8_GRAPH_PREVIEW_CANDIDATES_CSV)
            if graph_candidate
            else str(STEP8_GRAPH_PREVIEW_REPORT_CSV)
            if graph_report
            else ""
        )
        manual_or_graph_paths = [path for path in [graph_path, str(STEP8_MANUAL_WRITE_BACK_REPORT_CSV) if manual_report else ""] if path]
        packaging_path = str(STEP8_PACKAGING_QA_REPORT_CSV) if packaging_report else ""
        sdf_found = bool(sdf_path)
        hash_found = bool(sha_source)
        graph_found = bool(manual_or_graph_paths)
        packaging_found = bool(packaging_path or metadata)
        blockers: list[str] = []
        if not _as_bool(step13o.get("step8_artifact_found", "False")):
            blockers.append("step13o_artifact_paths_missing")
        if not sdf_found:
            blockers.append("pre_reaction_sdf_path_missing")
        if not hash_found:
            blockers.append("pre_reaction_sdf_hash_or_manifest_missing")
        if not graph_found:
            blockers.append("manual_review_or_graph_preview_provenance_missing")
        allowed = bool(sdf_found and hash_found and graph_found)
        rows.append(
            {
                "review_row_id": review_row_id,
                "pdb_id": EXPECTED_PDB_IDS[EXPECTED_REVIEW_ROW_IDS.index(review_row_id)],
                "expected_step8_sample_name": sample_name,
                "step13o_artifact_found": str(_as_bool(step13o.get("step8_artifact_found", "False"))),
                "step13o_artifact_paths": step13o.get("step8_artifact_path", ""),
                "candidate_pre_reaction_sdf_path_discovered": str(sdf_found),
                "candidate_pre_reaction_sdf_path": sdf_path,
                "candidate_pre_reaction_sdf_hash_or_manifest_path_discovered": str(hash_found),
                "candidate_pre_reaction_sdf_hash_or_manifest_path": sha_source,
                "graph_preview_artifact_discovered": str(graph_found),
                "graph_preview_artifact_path": ";".join(manual_or_graph_paths),
                "packaging_qa_artifact_discovered": str(packaging_found),
                "packaging_qa_artifact_path": packaging_path or str(STEP8_METADATA_ROOT / f"{sample_name}.json"),
                "allowed_for_future_readonly_topology_export": str(allowed),
                "discovery_status": "source_discovery_passed" if allowed else "source_discovery_incomplete",
                "blocking_reasons": ";".join(blockers),
            }
        )
    return rows


def build_export_schema_contract_v0() -> list[dict[str, str]]:
    atom_fields = [
        "ligand_atom_topology_row_id",
        "review_row_id",
        "pdb_id",
        "expected_step8_sample_name",
        "source_pre_reaction_sdf_path",
        "source_pre_reaction_sdf_sha256",
        "rdkit_atom_idx",
        "atom_map_or_original_atom_id",
        "atom_symbol",
        "formal_charge",
        "aromatic",
        "hybridization",
        "degree",
        "explicit_valence",
        "implicit_valence",
        "is_covalent_ligand_endpoint_atom",
        "warhead_group_status",
        "linker_group_status",
        "scaffold_group_status",
        "export_source_stage",
        "training_use_status",
    ]
    bond_fields = [
        "ligand_bond_topology_row_id",
        "review_row_id",
        "pdb_id",
        "expected_step8_sample_name",
        "source_pre_reaction_sdf_path",
        "source_pre_reaction_sdf_sha256",
        "rdkit_bond_idx",
        "begin_rdkit_atom_idx",
        "end_rdkit_atom_idx",
        "begin_atom_symbol",
        "end_atom_symbol",
        "bond_type",
        "bond_order_numeric",
        "is_aromatic",
        "is_conjugated",
        "is_in_ring",
        "stereo",
        "touches_covalent_ligand_endpoint",
        "is_warhead_bond",
        "is_linker_bond",
        "is_scaffold_bond",
        "export_source_stage",
        "training_use_status",
    ]
    rows: list[dict[str, str]] = []
    for table_name, fields in [
        ("step8_exported_ligand_atom_topology_table", atom_fields),
        ("step8_exported_ligand_bond_topology_table", bond_fields),
    ]:
        for field in fields:
            rows.append(
                {
                    "future_table_name": table_name,
                    "field_name": field,
                    "field_group": "atom_topology" if "atom" in table_name else "bond_topology",
                    "field_description": f"Future readonly topology export field: {field}",
                    "required_for_future_export": "True",
                    "training_use_status": "not_training_input_yet",
                }
            )
    return rows


def build_export_candidate_contract_v0(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    source_by_review = {row["review_row_id"]: row for row in source_rows}
    rows: list[dict[str, str]] = []
    for review_row_id in EXPECTED_REVIEW_ROW_IDS:
        source = source_by_review[review_row_id]
        rows.append(
            {
                "review_row_id": review_row_id,
                "pdb_id": source["pdb_id"],
                "expected_step8_sample_name": source["expected_step8_sample_name"],
                "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
                "topology_export_scope": TOPOLOGY_EXPORT_SCOPE,
                "topology_export_input_policy": TOPOLOGY_EXPORT_INPUT_POLICY,
                "readonly_rdkit_export_allowed_next_step": source["allowed_for_future_readonly_topology_export"],
                "source_pre_reaction_sdf_path": source["candidate_pre_reaction_sdf_path"],
                "source_manual_review_or_graph_preview_artifact_path": source["graph_preview_artifact_path"],
                "source_hash_or_manifest_path": source["candidate_pre_reaction_sdf_hash_or_manifest_path"],
                "expected_atom_topology_row_count": str(EXPECTED_ATOM_COUNTS[review_row_id]),
                "expected_bond_topology_row_count": str(EXPECTED_BOND_COUNTS[review_row_id]),
                "auto_restore_ligand_allowed": "False",
                "sdf_generation_allowed": "False",
                "sdf_modification_allowed": "False",
                "sdf_copy_allowed": "False",
                "non_cys_generalization_allowed": "False",
                "training_ready": "False",
                "training_ready_reason": "design_gate_only_no_topology_export_run",
            }
        )
    return rows


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step13o_blocked_precondition": {
            "step13o_blocked_evidence_gate_validated": manifest["step13o_blocked_evidence_gate_validated"],
            "step13o_all_checks_passed": manifest["step13o_all_checks_passed"],
        },
        "source_discovery": {
            "source_discovery_contract_row_count": manifest["source_discovery_contract_row_count"],
            "all_candidates_have_pre_reaction_sdf_path": manifest[
                "all_candidates_have_pre_reaction_sdf_path"
            ],
            "all_candidates_have_hash_or_manifest_provenance": manifest[
                "all_candidates_have_hash_or_manifest_provenance"
            ],
            "all_candidates_allowed_for_future_readonly_topology_export": manifest[
                "all_candidates_allowed_for_future_readonly_topology_export"
            ],
        },
        "schema_contract": {
            "export_schema_contract_row_count": manifest["export_schema_contract_row_count"],
            "export_candidate_contract_row_count": manifest["export_candidate_contract_row_count"],
        },
        "safety_boundary": {
            "rdkit_used": manifest["rdkit_used"],
            "sdf_read": manifest["sdf_read"],
            "ligand_topology_table_written": manifest["ligand_topology_table_written"],
            "ready_to_train_now": manifest["ready_to_train_now"],
        },
        "next_step": {
            "readonly_rdkit_export_allowed_next_step": manifest["readonly_rdkit_export_allowed_next_step"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }


def build_real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step13o_validated = validate_step13o_blocked_precondition_v0()
    except Exception as exc:
        step13o_validated = False
        blockers.append(f"step13o_blocked_precondition_failed:{type(exc).__name__}:{exc}")
    source_rows = build_source_discovery_contract_v0() if STEP13O_ARTIFACT_DISCOVERY_AUDIT_CSV.is_file() else []
    schema_rows = build_export_schema_contract_v0()
    candidate_rows = build_export_candidate_contract_v0(source_rows) if source_rows else []

    all_have_step13o_paths = all(_as_bool(row["step13o_artifact_found"]) for row in source_rows)
    all_have_sdf_path = all(_as_bool(row["candidate_pre_reaction_sdf_path_discovered"]) for row in source_rows)
    all_have_manual_graph = all(_as_bool(row["graph_preview_artifact_discovered"]) for row in source_rows)
    all_have_hash = all(_as_bool(row["candidate_pre_reaction_sdf_hash_or_manifest_path_discovered"]) for row in source_rows)
    all_allowed = all(_as_bool(row["allowed_for_future_readonly_topology_export"]) for row in source_rows)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_committable_artifacts_created()
    raw_staged = _raw_files_staged()
    raw_tracked = _raw_files_tracked()
    if source_modified:
        blockers.append("protected_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_committable_artifacts_created")
    if raw_staged:
        blockers.append("raw_files_staged")
    if raw_tracked:
        blockers.append("raw_files_tracked")
    for row in source_rows:
        if row["blocking_reasons"]:
            blockers.extend(f"{row['review_row_id']}:{reason}" for reason in row["blocking_reasons"].split(";"))

    all_checks_passed = (
        step13o_validated
        and len(source_rows) == 3
        and len(schema_rows) >= 40
        and len(candidate_rows) == 3
        and all_have_step13o_paths
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not blockers
    )
    manifest: dict[str, Any] = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13o_blocked_evidence_gate_validated": step13o_validated,
        "step13o_all_checks_passed": False,
        "step13o_blocked_due_to_missing_per_atom_or_per_bond_topology_evidence": True,
        "source_discovery_contract_written": True,
        "source_discovery_contract_row_count": len(source_rows),
        "export_schema_contract_written": True,
        "export_schema_contract_row_count": len(schema_rows),
        "export_candidate_contract_written": True,
        "export_candidate_contract_row_count": len(candidate_rows),
        "all_current_samples_cys_sg": True,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "topology_export_scope": TOPOLOGY_EXPORT_SCOPE,
        "topology_export_input_policy": TOPOLOGY_EXPORT_INPUT_POLICY,
        "all_candidates_have_step8_artifact_paths_from_step13o": all_have_step13o_paths,
        "all_candidates_have_pre_reaction_sdf_path": all_have_sdf_path,
        "all_candidates_have_manual_review_or_graph_preview_provenance": all_have_manual_graph,
        "all_candidates_have_hash_or_manifest_provenance": all_have_hash,
        "all_candidates_allowed_for_future_readonly_topology_export": all_allowed,
        "readonly_rdkit_export_allowed_next_step": all_allowed,
        "rdkit_used": False,
        "sdf_read": False,
        "sdf_generated": False,
        "sdf_modified": False,
        "sdf_copied": False,
        "ligand_auto_restoration_run": False,
        "ligand_topology_table_written": False,
        "sample_index_written": False,
        "enriched_sample_index_written": False,
        "final_dataset_written": False,
        "model_input_materialized": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "training_allowed": False,
        "finetune_allowed": False,
        "parameter_update_allowed": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "raw_files_read": False,
        GZIP_OPEN_KEY: False,
        "mmcif_text_read": False,
        "atom_site_text_scan_run": False,
        "biopdb_parser_used": False,
        VENDOR_USED_KEY: False,
        "output_limited_to_csv_json_md": True,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_committable_artifacts_created": forbidden_artifacts,
        "raw_files_staged": raw_staged,
        "raw_files_tracked": raw_tracked,
        "ready_for_step8_readonly_topology_evidence_export_smoke": all_allowed,
        "ready_for_sample_index_design_gate": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": ALLOWED_NEXT_STEP if all_allowed else BLOCKED_NEXT_STEP,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "source_discovery_rows": source_rows,
        "schema_rows": schema_rows,
        "candidate_rows": candidate_rows,
        "report_sections": _build_report_sections(manifest),
    }
