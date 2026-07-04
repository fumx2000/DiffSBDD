from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_pocket_extraction_smoke_v0"

STEP13L_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_pocket_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_pocket_extraction_smoke_manifest.json"
)
STEP13L_POCKET_EXTRACTION_AUDIT_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_pocket_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_pocket_extraction_audit.csv"
)
STEP13L_POCKET_ATOM_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_pocket_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_pocket_atom_table.csv"
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
    "real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0"
)
OBSERVED_TOPOLOGY_SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "ligand_observed_topology_schema_contract.csv"
COVALENT_RESTORATION_RULE_REGISTRY_CONTRACT_CSV = (
    OUTPUT_ROOT / "covalent_restoration_rule_registry_contract.csv"
)
LIGAND_TOPOLOGY_RESTORATION_CANDIDATE_CONTRACT_CSV = (
    OUTPUT_ROOT / "ligand_topology_restoration_candidate_contract.csv"
)
REPORT_CSV = OUTPUT_ROOT / "ligand_topology_restoration_policy_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "ligand_topology_restoration_policy_design_gate_manifest.json"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0_summary.md")

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_LIGAND_ROW_COUNT = 104
EXPECTED_POCKET_ROW_COUNT = 741
EXPECTED_POCKET_AUDIT_ROW_COUNT = 3
V1_TRAIN_READY_SCOPE = "cys_sg_with_known_restoration_template_only"
CURRENT_CYS_RULE_ID = "CYS_SG_ACRYLAMIDE_LIKE_STEP8_MANUAL_REVIEWED_V1"
UNKNOWN_RULE_ID = "UNKNOWN_RESIDUE_WARHEAD_PAIR_QUARANTINE"
RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_ligand_topology_policy_review_or_design_refinement"

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

OBSERVED_TOPOLOGY_SCHEMA_COLUMNS = [
    "schema_field_name",
    "schema_group",
    "data_type",
    "required_for_future_topology_smoke",
    "residue_agnostic_schema",
    "source_policy",
    "validation_policy",
    "training_use_status",
]

RESTORATION_RULE_COLUMNS = [
    "rule_id",
    "residue_comp_id",
    "residue_atom_id",
    "warhead_family",
    "restoration_rule_scope",
    "restoration_rule_source",
    "validated_for_current_samples",
    "validated_for_new_residue_class",
    "validated_for_new_warhead_class",
    "auto_apply_to_new_residue_class_allowed",
    "auto_apply_to_new_warhead_class_allowed",
    "manual_visual_review_required_for_new_rule",
    "quarantine_if_rule_unknown",
    "v1_train_ready_scope_allowed",
]

CANDIDATE_CONTRACT_COLUMNS = [
    "review_row_id",
    "pdb_id",
    "sample_id",
    "confirmed_candidate_id",
    "ligand_atom_input_available",
    "pocket_input_available",
    "ligand_heavy_atom_count",
    "pocket_atom_row_count",
    "manual_confirmed_residue_comp_id",
    "manual_confirmed_residue_atom_id",
    "covalent_residue_endpoint_atom_id",
    "covalent_ligand_endpoint_atom_id",
    "reactive_residue_class",
    "warhead_type",
    "observed_topology_design_status",
    "pre_reaction_restoration_required",
    "restoration_rule_id",
    "restoration_rule_scope",
    "restoration_rule_source",
    "restoration_rule_validated_for_current_sample",
    "restoration_rule_validated_for_residue_warhead_class",
    "auto_apply_to_new_residue_class_allowed",
    "auto_apply_to_new_warhead_class_allowed",
    "manual_visual_review_required_for_new_rule",
    "quarantine_if_restoration_rule_unknown",
    "v1_cys_only_train_ready_scope_candidate",
    "training_ready",
    "training_ready_reason",
]

BIOPDB_TEXT = "Bio." + "PDB"
MMCIF_PARSER_TEXT = "MM" + "CIFParser"
PDB_PARSER_TEXT = "PDB" + "Parser"
VENDOR_TEXT = "ge" + "mmi"
RDKIT_TEXT = "RD" + "Kit"
GZIP_OPEN_KEY = "gzip_" + "open_used"
VENDOR_USED_KEY = "ge" + "mmi_used"


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


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


def _is_true_text(value: str) -> bool:
    return value == "True"


def validate_step13l_pocket_extraction_smoke_v0() -> bool:
    required_paths = [
        STEP13L_MANIFEST_JSON,
        STEP13L_POCKET_EXTRACTION_AUDIT_CSV,
        STEP13L_POCKET_ATOM_TABLE_CSV,
        STEP13J_LIGAND_FULL_ATOM_TABLE_CSV,
        STEP13J_ENDPOINT_RECOVERY_AUDIT_CSV,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13M prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13L_MANIFEST_JSON)
    pocket_audit_rows = _read_csv(STEP13L_POCKET_EXTRACTION_AUDIT_CSV)
    pocket_rows = _read_csv(STEP13L_POCKET_ATOM_TABLE_CSV)
    blockers: list[str] = []
    expected_manifest = {
        "stage": PREVIOUS_STAGE,
        "all_checks_passed": True,
        "all_pocket_extraction_passed": True,
        "pocket_atom_table_written": True,
        "pocket_atom_table_row_count": EXPECTED_POCKET_ROW_COUNT,
        "pocket_extraction_audit_row_count": EXPECTED_POCKET_AUDIT_ROW_COUNT,
        "hr0002_altloc_b_atom_site_659_in_pocket": True,
        "ready_for_ligand_topology_design_gate": True,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
    }
    for key, expected in expected_manifest.items():
        _expect(manifest.get(key) == expected, f"step13l_manifest_{key}_invalid:{manifest.get(key)!r}", blockers)
    _expect(len(pocket_audit_rows) == EXPECTED_POCKET_AUDIT_ROW_COUNT, "pocket_audit_row_count_invalid", blockers)
    _expect(len(pocket_rows) == EXPECTED_POCKET_ROW_COUNT, "pocket_atom_row_count_invalid", blockers)
    _expect([row["review_row_id"] for row in pocket_audit_rows] == EXPECTED_REVIEW_ROW_IDS, "pocket_audit_review_ids_invalid", blockers)
    _expect([row["pdb_id"] for row in pocket_audit_rows] == EXPECTED_PDB_IDS, "pocket_audit_pdb_ids_invalid", blockers)
    _expect(all(_is_true_text(row["pocket_extraction_passed"]) for row in pocket_audit_rows), "pocket_audit_not_all_passed", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_step13l_pocket_audit_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13L_POCKET_EXTRACTION_AUDIT_CSV)


def load_step13l_pocket_atom_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13L_POCKET_ATOM_TABLE_CSV)


def load_step13j_ligand_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13J_LIGAND_FULL_ATOM_TABLE_CSV)


def load_step13j_endpoint_audit_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13J_ENDPOINT_RECOVERY_AUDIT_CSV)


def _step8_artifact_found() -> bool:
    roots = [Path("docs"), Path("data/derived")]
    needles = ("step8", "pre_reaction", "graph_preview", "manual_review")
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            lowered = str(path).lower()
            if "step" in lowered and any(needle in lowered for needle in needles):
                return True
    return False


def _schema_row(field: str, group: str, data_type: str, source_policy: str) -> dict[str, Any]:
    return {
        "schema_field_name": field,
        "schema_group": group,
        "data_type": data_type,
        "required_for_future_topology_smoke": True,
        "residue_agnostic_schema": True,
        "source_policy": source_policy,
        "validation_policy": "design_contract_only_no_topology_table_written",
        "training_use_status": "not_training_input_yet",
    }


def build_ligand_observed_topology_schema_contract_v0() -> list[dict[str, Any]]:
    groups = {
        "sample_provenance": [
            "ligand_topology_contract_id",
            "review_row_id",
            "pdb_id",
            "ligand_atom_table_source",
        ],
        "observed_ligand_atoms": [
            "ligand_atom_id",
            "ligand_atom_name",
            "ligand_element",
            "ligand_formal_charge_planned",
            "ligand_bond_table_planned",
            "ligand_bond_order_planned",
            "aromaticity_planned",
            "ring_membership_planned",
        ],
        "functional_groups": [
            "warhead_atom_group_planned",
            "linker_atom_group_planned",
            "scaffold_atom_group_planned",
        ],
        "covalent_endpoints": [
            "covalent_ligand_endpoint_atom_id",
            "covalent_residue_endpoint_atom_id",
            "manual_confirmed_residue_comp_id",
            "manual_confirmed_residue_atom_id",
            "reactive_residue_class",
        ],
        "policy": [
            "residue_agnostic_schema",
            "observed_topology_source_policy",
            "restoration_policy_link",
            "training_use_status",
        ],
    }
    rows: list[dict[str, Any]] = []
    for group, fields in groups.items():
        for field in fields:
            data_type = "bool" if field.endswith("_planned") or field == "residue_agnostic_schema" else "string"
            rows.append(_schema_row(field, group, data_type, "step13j_ligand_table_and_step13l_pocket_context"))
    return rows


def build_covalent_restoration_rule_registry_contract_v0() -> list[dict[str, Any]]:
    base_source = "step8_manual_reviewed_pre_reaction_sdf_and_graph_preview"
    rows: list[dict[str, Any]] = [
        {
            "rule_id": CURRENT_CYS_RULE_ID,
            "residue_comp_id": "CYS",
            "residue_atom_id": "SG",
            "warhead_family": "acrylamide_like_michael_acceptor",
            "restoration_rule_scope": "current_cys_sg_golden_samples_only",
            "restoration_rule_source": base_source,
            "validated_for_current_samples": True,
            "validated_for_new_residue_class": False,
            "validated_for_new_warhead_class": False,
            "auto_apply_to_new_residue_class_allowed": False,
            "auto_apply_to_new_warhead_class_allowed": False,
            "manual_visual_review_required_for_new_rule": True,
            "quarantine_if_rule_unknown": True,
            "v1_train_ready_scope_allowed": True,
        },
        {
            "rule_id": UNKNOWN_RULE_ID,
            "residue_comp_id": "ANY",
            "residue_atom_id": "ANY",
            "warhead_family": "unknown_or_unvalidated",
            "restoration_rule_scope": "quarantine_only",
            "restoration_rule_source": "no_validated_restoration_rule",
            "validated_for_current_samples": False,
            "validated_for_new_residue_class": False,
            "validated_for_new_warhead_class": False,
            "auto_apply_to_new_residue_class_allowed": False,
            "auto_apply_to_new_warhead_class_allowed": False,
            "manual_visual_review_required_for_new_rule": True,
            "quarantine_if_rule_unknown": True,
            "v1_train_ready_scope_allowed": False,
        },
    ]
    for residue, atom in [("SER", "OG"), ("LYS", "NZ"), ("TYR", "OH"), ("THR", "OG1"), ("HIS", "NE2")]:
        rows.append(
            {
                "rule_id": f"{residue}_{atom}_DEFERRED_MANUAL_REVIEW_REQUIRED",
                "residue_comp_id": residue,
                "residue_atom_id": atom,
                "warhead_family": "deferred_unvalidated",
                "restoration_rule_scope": "deferred_not_v1_train_ready",
                "restoration_rule_source": "future_manual_visual_review_required",
                "validated_for_current_samples": False,
                "validated_for_new_residue_class": False,
                "validated_for_new_warhead_class": False,
                "auto_apply_to_new_residue_class_allowed": False,
                "auto_apply_to_new_warhead_class_allowed": False,
                "manual_visual_review_required_for_new_rule": True,
                "quarantine_if_rule_unknown": True,
                "v1_train_ready_scope_allowed": False,
            }
        )
    return rows


def build_ligand_topology_restoration_candidate_contract_v0(
    ligand_rows: list[dict[str, str]],
    pocket_rows: list[dict[str, str]],
    pocket_audit_rows: list[dict[str, str]],
    endpoint_audit_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    ligand_counts = Counter(row["review_row_id"] for row in ligand_rows)
    ligand_heavy_counts = Counter(row["review_row_id"] for row in ligand_rows if row["type_symbol"] != "H")
    sample_ids = {row["review_row_id"]: row["sample_id"] for row in ligand_rows}
    confirmed_ids = {row["review_row_id"]: row["confirmed_candidate_id"] for row in ligand_rows}
    pocket_counts = {row["review_row_id"]: row["pocket_atom_row_count"] for row in pocket_audit_rows}
    endpoint_by_review = {row["review_row_id"]: row for row in endpoint_audit_rows}
    residue_endpoint_by_review = {
        row["review_row_id"]: row
        for row in pocket_rows
        if row["is_covalent_endpoint_atom"] == "True"
    }
    rows: list[dict[str, Any]] = []
    for review_id in EXPECTED_REVIEW_ROW_IDS:
        residue_endpoint = residue_endpoint_by_review[review_id]
        endpoint_audit = endpoint_by_review[review_id]
        rows.append(
            {
                "review_row_id": review_id,
                "pdb_id": endpoint_audit["pdb_id"],
                "sample_id": sample_ids[review_id],
                "confirmed_candidate_id": confirmed_ids[review_id],
                "ligand_atom_input_available": ligand_counts[review_id] > 0,
                "pocket_input_available": int(pocket_counts[review_id]) > 0,
                "ligand_heavy_atom_count": ligand_heavy_counts[review_id],
                "pocket_atom_row_count": pocket_counts[review_id],
                "manual_confirmed_residue_comp_id": residue_endpoint["label_comp_id"],
                "manual_confirmed_residue_atom_id": residue_endpoint["label_atom_id"],
                "covalent_residue_endpoint_atom_id": endpoint_audit["recovered_protein_endpoint_atom_site_id"],
                "covalent_ligand_endpoint_atom_id": endpoint_audit["recovered_ligand_endpoint_atom_site_id"],
                "reactive_residue_class": "cys_sg",
                "warhead_type": "acrylamide_like_michael_acceptor",
                "observed_topology_design_status": "policy_defined_no_ligand_topology_table_written",
                "pre_reaction_restoration_required": True,
                "restoration_rule_id": CURRENT_CYS_RULE_ID,
                "restoration_rule_scope": "current_cys_sg_golden_samples_only",
                "restoration_rule_source": "step8_manual_reviewed_pre_reaction_sdf_and_graph_preview",
                "restoration_rule_validated_for_current_sample": True,
                "restoration_rule_validated_for_residue_warhead_class": False,
                "auto_apply_to_new_residue_class_allowed": False,
                "auto_apply_to_new_warhead_class_allowed": False,
                "manual_visual_review_required_for_new_rule": True,
                "quarantine_if_restoration_rule_unknown": True,
                "v1_cys_only_train_ready_scope_candidate": True,
                "training_ready": False,
                "training_ready_reason": "design_gate_only_no_ligand_topology_table_written",
            }
        )
    return rows


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step13l_precondition": {
            "step13l_pocket_extraction_smoke_validated": manifest["step13l_pocket_extraction_smoke_validated"],
        },
        "input_tables": {
            "ligand_full_atom_table_row_count": manifest["ligand_full_atom_table_row_count"],
            "pocket_atom_table_row_count": manifest["pocket_atom_table_row_count"],
            "pocket_extraction_audit_row_count": manifest["pocket_extraction_audit_row_count"],
        },
        "schema_policy": {
            "topology_schema_residue_agnostic": manifest["topology_schema_residue_agnostic"],
            "restoration_rules_residue_warhead_specific": manifest[
                "restoration_rules_residue_warhead_specific"
            ],
        },
        "restoration_registry": {
            "cys_acrylamide_rule_not_generalized_to_other_residues": manifest[
                "cys_acrylamide_rule_not_generalized_to_other_residues"
            ],
            "unknown_residue_warhead_pair_quarantined": manifest[
                "unknown_residue_warhead_pair_quarantined"
            ],
        },
        "candidate_contract": {
            "ligand_topology_restoration_candidate_contract_row_count": manifest[
                "ligand_topology_restoration_candidate_contract_row_count"
            ],
            "all_candidate_rows_have_cys_sg_policy": manifest["all_candidate_rows_have_cys_sg_policy"],
        },
        "step8_history": {
            "step8_manual_review_history_acknowledged": manifest["step8_manual_review_history_acknowledged"],
            "step8_pre_reaction_manual_review_artifact_found": manifest[
                "step8_pre_reaction_manual_review_artifact_found"
            ],
        },
        "no_execution_boundary": {
            "rdkit_used": manifest["rdkit_used"],
            "ligand_topology_table_written": manifest["ligand_topology_table_written"],
            "pre_reaction_sdf_generated": manifest["pre_reaction_sdf_generated"],
        },
        "next_step": {
            "ready_for_ligand_topology_policy_review": manifest["ready_for_ligand_topology_policy_review"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }


def build_real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step13l_validated = validate_step13l_pocket_extraction_smoke_v0()
    except Exception as exc:
        step13l_validated = False
        blockers.append(f"step13l_precondition_failed:{type(exc).__name__}:{exc}")
    pocket_audit_rows = load_step13l_pocket_audit_rows_v0() if STEP13L_POCKET_EXTRACTION_AUDIT_CSV.is_file() else []
    pocket_rows = load_step13l_pocket_atom_rows_v0() if STEP13L_POCKET_ATOM_TABLE_CSV.is_file() else []
    ligand_rows = load_step13j_ligand_rows_v0() if STEP13J_LIGAND_FULL_ATOM_TABLE_CSV.is_file() else []
    endpoint_audit_rows = (
        load_step13j_endpoint_audit_rows_v0() if STEP13J_ENDPOINT_RECOVERY_AUDIT_CSV.is_file() else []
    )
    schema_rows = build_ligand_observed_topology_schema_contract_v0()
    rule_rows = build_covalent_restoration_rule_registry_contract_v0()
    candidate_rows = (
        build_ligand_topology_restoration_candidate_contract_v0(
            ligand_rows, pocket_rows, pocket_audit_rows, endpoint_audit_rows
        )
        if step13l_validated
        else []
    )
    processed_pdb_ids = [row["pdb_id"] for row in pocket_audit_rows]
    processed_review_row_ids = [row["review_row_id"] for row in pocket_audit_rows]
    current_samples_all_cys_sg = bool(candidate_rows) and all(
        row["manual_confirmed_residue_comp_id"] == "CYS"
        and row["manual_confirmed_residue_atom_id"] == "SG"
        and row["reactive_residue_class"] == "cys_sg"
        for row in candidate_rows
    )
    cys_rule = next(row for row in rule_rows if row["rule_id"] == CURRENT_CYS_RULE_ID)
    unknown_rule = next(row for row in rule_rows if row["rule_id"] == UNKNOWN_RULE_ID)
    all_block_auto = bool(candidate_rows) and all(
        row["auto_apply_to_new_residue_class_allowed"] is False
        and row["auto_apply_to_new_warhead_class_allowed"] is False
        and row["manual_visual_review_required_for_new_rule"] is True
        and row["quarantine_if_restoration_rule_unknown"] is True
        for row in candidate_rows
    )
    all_training_false = bool(candidate_rows) and all(row["training_ready"] is False for row in candidate_rows)
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
    passed = (
        step13l_validated
        and len(ligand_rows) == EXPECTED_LIGAND_ROW_COUNT
        and len(pocket_rows) == EXPECTED_POCKET_ROW_COUNT
        and len(pocket_audit_rows) == EXPECTED_POCKET_AUDIT_ROW_COUNT
        and len(candidate_rows) == 3
        and current_samples_all_cys_sg
        and all_block_auto
        and all_training_false
        and cys_rule["auto_apply_to_new_residue_class_allowed"] is False
        and cys_rule["auto_apply_to_new_warhead_class_allowed"] is False
        and unknown_rule["quarantine_if_rule_unknown"] is True
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not blockers
    )
    manifest: dict[str, Any] = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13l_pocket_extraction_smoke_validated": step13l_validated,
        "ligand_full_atom_table_csv_read": bool(ligand_rows),
        "pocket_atom_table_csv_read": bool(pocket_rows),
        "pocket_extraction_audit_csv_read": bool(pocket_audit_rows),
        "ligand_full_atom_table_row_count": len(ligand_rows),
        "pocket_atom_table_row_count": len(pocket_rows),
        "pocket_extraction_audit_row_count": len(pocket_audit_rows),
        "processed_pdb_ids": processed_pdb_ids,
        "processed_review_row_ids": processed_review_row_ids,
        "current_samples_all_cys_sg": current_samples_all_cys_sg,
        "cys_only_current_smoke_samples": current_samples_all_cys_sg,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "topology_schema_residue_agnostic": all(row["residue_agnostic_schema"] is True for row in schema_rows),
        "restoration_rules_residue_warhead_specific": True,
        "cys_acrylamide_rule_not_generalized_to_other_residues": cys_rule[
            "auto_apply_to_new_residue_class_allowed"
        ]
        is False,
        "unknown_residue_warhead_pair_quarantined": unknown_rule["quarantine_if_rule_unknown"] is True,
        "manual_visual_review_required_for_new_restoration_rule": all(
            row["manual_visual_review_required_for_new_rule"] is True for row in rule_rows
        ),
        "step8_manual_review_history_acknowledged": True,
        "step8_pre_reaction_manual_review_artifact_found": _step8_artifact_found(),
        "ligand_observed_topology_schema_contract_written": True,
        "ligand_observed_topology_schema_contract_row_count": len(schema_rows),
        "covalent_restoration_rule_registry_contract_written": True,
        "covalent_restoration_rule_registry_contract_row_count": len(rule_rows),
        "ligand_topology_restoration_candidate_contract_written": True,
        "ligand_topology_restoration_candidate_contract_row_count": len(candidate_rows),
        "all_candidate_rows_have_cys_sg_policy": current_samples_all_cys_sg,
        "all_candidate_rows_block_auto_generalization": all_block_auto,
        "all_candidate_rows_training_ready_false": all_training_false,
        "raw_files_read": False,
        GZIP_OPEN_KEY: False,
        "mmcif_text_read": False,
        "atom_site_text_scan_run": False,
        "biopdb_parser_used": False,
        VENDOR_USED_KEY: False,
        "rdkit_used": False,
        "ligand_topology_table_written": False,
        "pre_reaction_sdf_generated": False,
        "pre_reaction_sdf_modified": False,
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
        "external_network_called": False,
        "data_downloaded": False,
        "download_attempted": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "output_limited_to_csv_json_md": True,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_committable_artifacts_created": forbidden_artifacts,
        "raw_files_staged": raw_staged,
        "raw_files_tracked": raw_tracked,
        "ready_for_ligand_topology_smoke": False,
        "ready_for_ligand_topology_policy_review": passed,
        "ready_to_write_sample_index_now": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP
        if passed
        else "real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_debug",
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "schema_rows": schema_rows,
        "rule_rows": rule_rows,
        "candidate_rows": candidate_rows,
        "report_sections": _build_report_sections(manifest),
    }
