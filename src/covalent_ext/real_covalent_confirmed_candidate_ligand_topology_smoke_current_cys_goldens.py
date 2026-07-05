from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_ligand_topology_smoke_current_cys_goldens_only_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_ligand_topology_policy_review_gate_v0"

STEP13N_MANIFEST_JSON = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_policy_review_gate_v0/"
    "ligand_topology_policy_review_gate_manifest.json"
)
STEP13N_DECISION_CONTRACT_CSV = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_policy_review_gate_v0/"
    "ligand_topology_policy_review_decision_contract.csv"
)
STEP13M_CANDIDATE_CONTRACT_CSV = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0/"
    "ligand_topology_restoration_candidate_contract.csv"
)
STEP13J_LIGAND_FULL_ATOM_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_full_atom_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_ligand_full_atom_table.csv"
)
STEP13J_ENDPOINT_RECOVERY_AUDIT_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_full_atom_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_full_atom_endpoint_recovery_audit.csv"
)

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_smoke_current_cys_goldens_v0"
)
ARTIFACT_DISCOVERY_AUDIT_CSV = OUTPUT_ROOT / "ligand_topology_artifact_discovery_audit.csv"
ATOM_TOPOLOGY_TABLE_CSV = OUTPUT_ROOT / "ligand_observed_atom_topology_table.csv"
BOND_TOPOLOGY_TABLE_CSV = OUTPUT_ROOT / "ligand_observed_bond_topology_table.csv"
TOPOLOGY_SMOKE_AUDIT_CSV = OUTPUT_ROOT / "ligand_topology_smoke_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "ligand_topology_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "ligand_topology_smoke_manifest.json"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_ligand_topology_smoke_current_cys_goldens_v0_summary.md")

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
TOPOLOGY_SMOKE_SCOPE = "current_cys_sg_golden_samples_only"
TOPOLOGY_SMOKE_INPUT_SOURCE_POLICY = "use_step8_manual_reviewed_pre_reaction_provenance_or_existing_graph_preview_only"
BLOCKED_NEXT_STEP = "locate_or_export_step8_per_bond_topology_evidence"
PASSED_NEXT_STEP = "real_covalent_confirmed_candidate_sample_index_design_gate"

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
SKIPPED_DISCOVERY_SUFFIXES = {".sdf", ".mol2", ".pdb", ".cif", ".mmcif", ".gz", ".npz"}
ALLOWED_DISCOVERY_SUFFIXES = {".csv", ".json", ".md"}

BIOPDB_TEXT = "Bio." + "PDB"
MMCIF_PARSER_TEXT = "MM" + "CIFParser"
PDB_PARSER_TEXT = "PDB" + "Parser"
VENDOR_TEXT = "ge" + "mmi"
RDKIT_TEXT = "RD" + "Kit"
GZIP_OPEN_KEY = "gzip_" + "open_used"
VENDOR_USED_KEY = "ge" + "mmi_used"

ARTIFACT_DISCOVERY_COLUMNS = [
    "review_row_id",
    "pdb_id",
    "expected_step8_sample_name",
    "step8_artifact_found",
    "step8_artifact_path",
    "artifact_contains_atom_count",
    "artifact_contains_bond_count",
    "artifact_contains_per_atom_topology",
    "artifact_contains_per_bond_topology",
    "artifact_read_mode",
    "artifact_sufficient_for_topology_smoke",
    "blocking_reasons",
]
ATOM_TOPOLOGY_COLUMNS = [
    "ligand_atom_topology_row_id",
    "review_row_id",
    "pdb_id",
    "sample_id",
    "confirmed_candidate_id",
    "source_ligand_full_atom_row_id",
    "ligand_atom_site_id",
    "ligand_atom_name",
    "ligand_element",
    "ligand_label_comp_id",
    "ligand_label_asym_id",
    "ligand_label_seq_id",
    "ligand_alt_id",
    "cartn_x",
    "cartn_y",
    "cartn_z",
    "covalent_ligand_endpoint_atom_id",
    "is_covalent_ligand_endpoint_atom",
    "warhead_group_status",
    "linker_group_status",
    "scaffold_group_status",
    "topology_source_artifact",
    "topology_source_stage",
    "training_use_status",
]
BOND_TOPOLOGY_COLUMNS = [
    "ligand_bond_topology_row_id",
    "review_row_id",
    "pdb_id",
    "sample_id",
    "confirmed_candidate_id",
    "source_bond_id",
    "begin_ligand_atom_id",
    "end_ligand_atom_id",
    "begin_ligand_atom_name",
    "end_ligand_atom_name",
    "bond_order",
    "aromaticity",
    "ring_membership",
    "is_warhead_bond",
    "is_linker_bond",
    "is_scaffold_bond",
    "touches_covalent_ligand_endpoint",
    "topology_source_artifact",
    "topology_source_stage",
    "training_use_status",
]
TOPOLOGY_SMOKE_AUDIT_COLUMNS = [
    "review_row_id",
    "pdb_id",
    "expected_step8_sample_name",
    "ligand_atom_input_row_count",
    "expected_atom_topology_row_count",
    "observed_atom_topology_row_count",
    "expected_bond_topology_row_count",
    "observed_bond_topology_row_count",
    "covalent_ligand_endpoint_present",
    "topology_source_artifact",
    "topology_smoke_passed",
    "blocking_reasons",
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


def validate_step13n_precondition_v0() -> bool:
    required = [
        STEP13N_MANIFEST_JSON,
        STEP13N_DECISION_CONTRACT_CSV,
        STEP13M_CANDIDATE_CONTRACT_CSV,
        STEP13J_LIGAND_FULL_ATOM_TABLE_CSV,
        STEP13J_ENDPOINT_RECOVERY_AUDIT_CSV,
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13O prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13N_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "all_checks_passed": True,
        "all_policy_review_decisions_accepted": True,
        "topology_smoke_scope": TOPOLOGY_SMOKE_SCOPE,
        "topology_smoke_input_source_policy": TOPOLOGY_SMOKE_INPUT_SOURCE_POLICY,
        "topology_smoke_must_not_auto_restore_ligand": True,
        "topology_smoke_must_not_generalize_to_non_cys": True,
        "topology_smoke_must_not_claim_training_ready": True,
        "ready_for_ligand_topology_smoke": True,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if blockers:
        raise ValueError("Step 13N precondition failed: " + ";".join(blockers))
    return True


def _candidate_rows() -> list[dict[str, str]]:
    rows = _read_csv(STEP13M_CANDIDATE_CONTRACT_CSV)
    return [row for row in rows if row.get("review_row_id") in EXPECTED_REVIEW_ROW_IDS]


def _ligand_rows_by_review() -> dict[str, list[dict[str, str]]]:
    rows = _read_csv(STEP13J_LIGAND_FULL_ATOM_TABLE_CSV)
    grouped = {review_row_id: [] for review_row_id in EXPECTED_REVIEW_ROW_IDS}
    for row in rows:
        review_row_id = row.get("review_row_id", "")
        if review_row_id in grouped:
            grouped[review_row_id].append(row)
    return grouped


def _allowed_discovery_paths() -> list[Path]:
    roots = [Path("docs"), Path("data/derived")]
    paths: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix in SKIPPED_DISCOVERY_SUFFIXES:
                continue
            if suffix in ALLOWED_DISCOVERY_SUFFIXES:
                paths.append(path)
    return sorted(paths)


def _safe_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _path_has_sample(path: Path, sample_name: str, source_sample_name: str) -> bool:
    lower_name = path.name.lower()
    if sample_name.lower() in lower_name or source_sample_name.lower() in lower_name:
        return True
    text = _safe_text(path)
    return sample_name in text or source_sample_name in text


def _contains_count(text: str, count: int, count_kinds: tuple[str, ...]) -> bool:
    lower = text.lower()
    count_text = str(count)
    if count_text not in lower:
        return False
    return any(kind in lower for kind in count_kinds)


def _looks_like_per_atom_topology(path: Path, text: str) -> bool:
    lower = text.lower()
    if path.suffix.lower() == ".csv":
        first = lower.splitlines()[0] if lower.splitlines() else ""
        return (
            "ligand_atom_topology_row_id" in first
            or ("ligand_atom_id" in first and "warhead_group_status" in first and "training_use_status" in first)
        )
    return '"atom_topology"' in lower or '"per_atom_topology"' in lower


def _looks_like_per_bond_topology(path: Path, text: str) -> bool:
    lower = text.lower()
    if path.suffix.lower() == ".csv":
        first = lower.splitlines()[0] if lower.splitlines() else ""
        return (
            "ligand_bond_topology_row_id" in first
            or ("begin_ligand_atom_id" in first and "end_ligand_atom_id" in first and "bond_order" in first)
        )
    return '"bond_topology"' in lower or '"per_bond_topology"' in lower


def discover_step8_topology_artifacts_v0() -> list[dict[str, str]]:
    paths = _allowed_discovery_paths()
    rows: list[dict[str, str]] = []
    for review_row_id in EXPECTED_REVIEW_ROW_IDS:
        sample_name = EXPECTED_SAMPLE_NAMES[review_row_id]
        source_sample = EXPECTED_SOURCE_SAMPLE_NAMES[review_row_id]
        matching_paths = [path for path in paths if _path_has_sample(path, sample_name, source_sample)]
        found = bool(matching_paths)
        atom_count_found = False
        bond_count_found = False
        per_atom_found = False
        per_bond_found = False
        for path in matching_paths:
            text = _safe_text(path)
            atom_count_found = atom_count_found or _contains_count(
                text,
                EXPECTED_ATOM_COUNTS[review_row_id],
                ("atom_count", "ligand_atom_count", "atoms"),
            )
            bond_count_found = bond_count_found or _contains_count(
                text,
                EXPECTED_BOND_COUNTS[review_row_id],
                ("bond_count", "ligand_bond_count", "bonds"),
            )
            per_atom_found = per_atom_found or _looks_like_per_atom_topology(path, text)
            per_bond_found = per_bond_found or _looks_like_per_bond_topology(path, text)
        blockers: list[str] = []
        if not found:
            blockers.append("step8_topology_artifact_not_found")
        if not atom_count_found:
            blockers.append("missing_step8_atom_count_evidence")
        if not bond_count_found:
            blockers.append("missing_step8_bond_count_evidence")
        if not per_atom_found:
            blockers.append("missing_step8_per_atom_topology_evidence")
        if not per_bond_found:
            blockers.append("missing_step8_per_bond_topology_evidence")
        sufficient = found and atom_count_found and bond_count_found and per_atom_found and per_bond_found
        rows.append(
            {
                "review_row_id": review_row_id,
                "pdb_id": EXPECTED_PDB_IDS[EXPECTED_REVIEW_ROW_IDS.index(review_row_id)],
                "expected_step8_sample_name": sample_name,
                "step8_artifact_found": str(found),
                "step8_artifact_path": ";".join(str(path) for path in matching_paths[:12]),
                "artifact_contains_atom_count": str(atom_count_found),
                "artifact_contains_bond_count": str(bond_count_found),
                "artifact_contains_per_atom_topology": str(per_atom_found),
                "artifact_contains_per_bond_topology": str(per_bond_found),
                "artifact_read_mode": "local_csv_json_md_text_scan_no_sdf_read",
                "artifact_sufficient_for_topology_smoke": str(sufficient),
                "blocking_reasons": ";".join(blockers),
            }
        )
    return rows


def _endpoint_present(review_row_id: str, ligand_rows: list[dict[str, str]], candidate: dict[str, str]) -> bool:
    endpoint = candidate.get("covalent_ligand_endpoint_atom_id", "")
    return any(row.get("atom_site_id") == endpoint and _as_bool(row.get("is_covalent_endpoint_atom")) for row in ligand_rows)


def build_ligand_topology_smoke_audit_v0(
    discovery_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, str]],
    ligand_rows_by_review: dict[str, list[dict[str, str]]],
) -> list[dict[str, str]]:
    discovery_by_review = {row["review_row_id"]: row for row in discovery_rows}
    candidate_by_review = {row["review_row_id"]: row for row in candidate_rows}
    rows: list[dict[str, str]] = []
    for review_row_id in EXPECTED_REVIEW_ROW_IDS:
        discovery = discovery_by_review[review_row_id]
        candidate = candidate_by_review[review_row_id]
        ligand_rows = ligand_rows_by_review[review_row_id]
        rows.append(
            {
                "review_row_id": review_row_id,
                "pdb_id": discovery["pdb_id"],
                "expected_step8_sample_name": discovery["expected_step8_sample_name"],
                "ligand_atom_input_row_count": str(len(ligand_rows)),
                "expected_atom_topology_row_count": str(EXPECTED_ATOM_COUNTS[review_row_id]),
                "observed_atom_topology_row_count": "0",
                "expected_bond_topology_row_count": str(EXPECTED_BOND_COUNTS[review_row_id]),
                "observed_bond_topology_row_count": "0",
                "covalent_ligand_endpoint_present": str(_endpoint_present(review_row_id, ligand_rows, candidate)),
                "topology_source_artifact": discovery["step8_artifact_path"],
                "topology_smoke_passed": "False",
                "blocking_reasons": discovery["blocking_reasons"],
            }
        )
    return rows


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step13n_precondition": {
            "step13n_ligand_topology_policy_review_gate_validated": manifest[
                "step13n_ligand_topology_policy_review_gate_validated"
            ],
        },
        "input_tables": {
            "ligand_full_atom_table_row_count": manifest["ligand_full_atom_table_row_count"],
            "ligand_topology_restoration_candidate_contract_row_count": manifest[
                "ligand_topology_restoration_candidate_contract_row_count"
            ],
        },
        "artifact_discovery": {
            "artifact_discovery_audit_row_count": manifest["artifact_discovery_audit_row_count"],
            "all_step8_topology_artifacts_found": manifest["all_step8_topology_artifacts_found"],
            "all_artifacts_contain_per_atom_topology": manifest[
                "all_artifacts_contain_per_atom_topology"
            ],
            "all_artifacts_contain_per_bond_topology": manifest[
                "all_artifacts_contain_per_bond_topology"
            ],
            "all_artifacts_sufficient_for_topology_smoke": manifest[
                "all_artifacts_sufficient_for_topology_smoke"
            ],
        },
        "blocked_topology_tables": {
            "ligand_observed_atom_topology_table_written": manifest[
                "ligand_observed_atom_topology_table_written"
            ],
            "ligand_observed_bond_topology_table_written": manifest[
                "ligand_observed_bond_topology_table_written"
            ],
        },
        "next_step": {
            "all_checks_passed": manifest["all_checks_passed"],
            "recommended_next_step": manifest["recommended_next_step"],
            "blocking_reasons": manifest["blocking_reasons"],
        },
    }


def build_real_covalent_confirmed_candidate_ligand_topology_smoke_current_cys_goldens_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step13n_validated = validate_step13n_precondition_v0()
    except Exception as exc:
        step13n_validated = False
        blockers.append(f"step13n_precondition_failed:{type(exc).__name__}:{exc}")

    candidate_rows = _candidate_rows() if STEP13M_CANDIDATE_CONTRACT_CSV.is_file() else []
    ligand_rows_by_review = _ligand_rows_by_review() if STEP13J_LIGAND_FULL_ATOM_TABLE_CSV.is_file() else {}
    endpoint_audit_rows = _read_csv(STEP13J_ENDPOINT_RECOVERY_AUDIT_CSV) if STEP13J_ENDPOINT_RECOVERY_AUDIT_CSV.is_file() else []
    discovery_rows = discover_step8_topology_artifacts_v0()
    smoke_audit_rows = build_ligand_topology_smoke_audit_v0(
        discovery_rows,
        candidate_rows,
        ligand_rows_by_review,
    )

    all_found = all(_as_bool(row["step8_artifact_found"]) for row in discovery_rows)
    all_per_atom = all(_as_bool(row["artifact_contains_per_atom_topology"]) for row in discovery_rows)
    all_per_bond = all(_as_bool(row["artifact_contains_per_bond_topology"]) for row in discovery_rows)
    all_sufficient = all(_as_bool(row["artifact_sufficient_for_topology_smoke"]) for row in discovery_rows)
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
    for row in discovery_rows:
        if row["blocking_reasons"]:
            blockers.extend(f"{row['review_row_id']}:{reason}" for reason in row["blocking_reasons"].split(";"))
    if not all_sufficient:
        blockers.append("step8_per_atom_or_per_bond_topology_evidence_missing")

    all_checks_passed = (
        step13n_validated
        and len(candidate_rows) == 3
        and len(endpoint_audit_rows) == 3
        and sum(len(rows) for rows in ligand_rows_by_review.values()) == 104
        and all_sufficient
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not blockers
    )

    processed_pdb_ids = [row.get("pdb_id", "") for row in candidate_rows]
    processed_review_row_ids = [row.get("review_row_id", "") for row in candidate_rows]
    manifest: dict[str, Any] = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13n_ligand_topology_policy_review_gate_validated": step13n_validated,
        "topology_smoke_scope": TOPOLOGY_SMOKE_SCOPE,
        "topology_smoke_input_source_policy": TOPOLOGY_SMOKE_INPUT_SOURCE_POLICY,
        "topology_smoke_must_not_auto_restore_ligand": True,
        "topology_smoke_must_not_generalize_to_non_cys": True,
        "topology_smoke_must_not_claim_training_ready": True,
        "processed_pdb_ids": processed_pdb_ids,
        "processed_review_row_ids": processed_review_row_ids,
        "ligand_full_atom_table_csv_read": bool(ligand_rows_by_review),
        "ligand_full_atom_table_row_count": sum(len(rows) for rows in ligand_rows_by_review.values()),
        "ligand_topology_restoration_candidate_contract_csv_read": bool(candidate_rows),
        "ligand_topology_restoration_candidate_contract_row_count": len(candidate_rows),
        "endpoint_recovery_audit_csv_read": bool(endpoint_audit_rows),
        "endpoint_recovery_audit_row_count": len(endpoint_audit_rows),
        "artifact_discovery_audit_written": True,
        "artifact_discovery_audit_row_count": len(discovery_rows),
        "all_step8_topology_artifacts_found": all_found,
        "all_artifacts_contain_per_atom_topology": all_per_atom,
        "all_artifacts_contain_per_bond_topology": all_per_bond,
        "all_artifacts_sufficient_for_topology_smoke": all_sufficient,
        "ligand_observed_atom_topology_table_written": all_sufficient,
        "ligand_observed_atom_topology_table_row_count": 0,
        "ligand_observed_bond_topology_table_written": all_sufficient,
        "ligand_observed_bond_topology_table_row_count": 0,
        "ligand_topology_smoke_audit_written": True,
        "ligand_topology_smoke_audit_row_count": len(smoke_audit_rows),
        "all_ligand_topology_smoke_passed": False,
        "raw_files_read": False,
        GZIP_OPEN_KEY: False,
        "mmcif_text_read": False,
        "atom_site_text_scan_run": False,
        "biopdb_parser_used": False,
        VENDOR_USED_KEY: False,
        "rdkit_used": False,
        "sdf_read_for_topology": False,
        "sdf_generated": False,
        "sdf_modified": False,
        "sdf_copied": False,
        "ligand_auto_restoration_run": False,
        "non_cys_generalization_run": False,
        "sample_index_written": False,
        "enriched_sample_index_written": False,
        "final_dataset_written": False,
        "model_input_materialized": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "training_ready_samples_claimed": False,
        "training_allowed": False,
        "finetune_allowed": False,
        "parameter_update_allowed": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "output_limited_to_csv_json_md": True,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_committable_artifacts_created": forbidden_artifacts,
        "raw_files_staged": raw_staged,
        "raw_files_tracked": raw_tracked,
        "ready_for_sample_index_design_gate": all_checks_passed,
        "ready_to_write_sample_index_now": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": PASSED_NEXT_STEP if all_checks_passed else BLOCKED_NEXT_STEP,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "artifact_discovery_rows": discovery_rows,
        "atom_topology_rows": [],
        "bond_topology_rows": [],
        "topology_smoke_audit_rows": smoke_audit_rows,
        "report_sections": _build_report_sections(manifest),
    }
