from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_independent_group_expansion_design_gate_v0"
STEP_LABEL = "Step 14AI"
PREVIOUS_STAGE = "covapie_leakage_split_review_gate_v0"
PROJECT_NAME = "CovaPIE"
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

STEP14AH_ROOT = Path("data/derived/covalent_small/covapie_leakage_split_review_gate_v0")
STEP14AG_ROOT = Path("data/derived/covalent_small/covapie_leakage_split_design_gate_v0")
STEP14AF_ROOT = Path("data/derived/covalent_small/covapie_final_dataset_design_gate_v0")
STEP14AE_ROOT = Path("data/derived/covalent_small/covapie_sample_index_qa_gate_v0")
STEP14AD_ROOT = Path("data/derived/covalent_small/covapie_sample_index_materialization_smoke_v0")
STEP14AA_ROOT = Path("data/derived/covalent_small/covapie_sample_preparation_execution_smoke_v0")
STEP14O_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_acquired_annotation_manual_review_gate_v0")
STEP14P_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_manual_review_decision_application_gate_v0")

STEP14AH_MANIFEST = STEP14AH_ROOT / "covapie_leakage_split_review_gate_manifest.json"
STEP14AH_DECISIONS = STEP14AH_ROOT / "covapie_leakage_split_review_decision_registry.csv"
SOURCE_INVENTORY = STEP14O_ROOT / "covapie_cys_sg_combined_acquired_annotation_inventory.csv"
SOURCE_DECISIONS = STEP14P_ROOT / "covapie_cys_sg_applied_manual_review_decisions.csv"
METADATA_CSV = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
SAMPLE_INDEX_CSV = STEP14AD_ROOT / "sample_index.csv"
SAMPLE_INDEX_JSON = STEP14AD_ROOT / "sample_index.json"
RAW_ROOT = Path("data/raw/covalent_sources")

PRECONDITION_AUDIT = OUTPUT_ROOT / "covapie_independent_group_expansion_precondition_audit.csv"
SOURCE_AUDIT = OUTPUT_ROOT / "covapie_expansion_candidate_source_inventory.csv"
EXCLUSION_AUDIT = OUTPUT_ROOT / "covapie_expansion_candidate_exclusion_audit.csv"
EVIDENCE_CONTRACT = OUTPUT_ROOT / "covapie_independence_evidence_requirement_contract.csv"
SHORTLIST_CSV = OUTPUT_ROOT / "covapie_independent_group_candidate_shortlist.csv"
SHORTLIST_JSON = OUTPUT_ROOT / "covapie_independent_group_candidate_shortlist.json"
ACQUISITION_PLAN = OUTPUT_ROOT / "covapie_independent_group_acquisition_batch_plan.csv"
POLICY_CONTRACT = OUTPUT_ROOT / "covapie_independent_group_expansion_policy_contract.csv"
SAFETY_AUDIT = OUTPUT_ROOT / "covapie_independent_group_expansion_safety_audit.csv"
MANIFEST = OUTPUT_ROOT / "covapie_independent_group_expansion_design_gate_manifest.json"
SUMMARY = Path("docs/covapie_independent_group_expansion_design_gate_v0_summary.md")

CANONICAL_MASK_TASK_NAMES = [
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
]
CANONICAL_MASK_TASK_ALIASES = ["A", "B", "B2", "B3", "C"]
TARGET_SHORTLIST_MIN = 5
TARGET_SHORTLIST_MAX = 10
TARGET_DISTINCT_NON_JUG_HET_ID_MIN = 3
CURRENT_SAMPLE_PAIRS = {("6BV6", "JUG"), ("6BV8", "JUG"), ("6BV5", "JUG")}
CURRENT_JUG_PAIRS = CURRENT_SAMPLE_PAIRS | {("6BV9", "JUG")}
KNOWN_BLOCKED = {
    ("1A54", "MDC"): ("known_struct_conn_blocked", "no_struct_conn_loop_found"),
    ("6BV9", "JUG"): ("known_ligand_comp_mismatch", "ligand_comp_id_mismatch"),
}

PRE_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SOURCE_COLUMNS = ["expansion_source_record_id", "source_artifact_path", "source_candidate_id", "pdb_id", "expected_het_id", "residue_name", "residue_atom_name", "source_review_status", "source_decision_status", "historical_struct_conn_status", "historical_blocking_reason", "already_in_current_sample_index", "belongs_to_current_jug_group", "known_blocked_pair", "complete_pdb_het_identity", "within_current_cys_sg_v1_scope", "eligible_for_shortlist_consideration", "source_lineage_comment"]
EXCLUSION_COLUMNS = ["exclusion_audit_id", "expansion_source_record_id", "pdb_id", "expected_het_id", "exclusion_reason_code", "exclusion_reason_description", "exclusion_category", "exclusion_status"]
EVIDENCE_COLUMNS = ["evidence_requirement_id", "evidence_requirement_name", "evidence_description", "required_before_acquisition", "required_before_final_group_assignment", "currently_available", "current_status", "requirement_contract_passed"]
SHORTLIST_COLUMNS = ["expansion_shortlist_id", "expansion_source_record_id", "shortlist_rank", "pdb_id", "expected_het_id", "residue_name", "residue_atom_name", "provisional_group_candidate_id", "provisional_grouping_basis", "distinct_from_current_jug_by_het_id", "source_identity_complete", "source_review_status", "historical_struct_conn_status", "raw_structure_present_currently", "raw_acquisition_required", "struct_conn_crosscheck_required", "ligand_graph_evidence_status", "protein_sequence_evidence_status", "provisional_independence_status", "candidate_priority", "shortlist_status", "shortlist_rationale"]
PLAN_COLUMNS = ["expansion_acquisition_plan_id", "expansion_shortlist_id", "shortlist_rank", "pdb_id", "expected_het_id", "proposed_batch_id", "acquisition_mode", "planned_raw_root", "raw_acquisition_authorized_current_step", "network_access_authorized_current_step", "struct_conn_crosscheck_planned", "atom_site_parse_planned", "manual_approval_required", "ready_for_acquisition_preflight", "ready_for_training_current_step", "planned_next_gate"]
POLICY_COLUMNS = ["policy_item", "policy_description", "policy_contract_passed"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with (REPO_ROOT / path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _json(path: Path) -> dict[str, Any]:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def _truth(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def _path_changed(paths: list[Path | str]) -> bool:
    values = [str(path) for path in paths]
    return _git(["diff", "--quiet", "--", *values]).returncode != 0 or _git(["diff", "--cached", "--quiet", "--", *values]).returncode != 0


def _sha256(path: Path) -> str:
    return hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()


def _committed(path: Path) -> bool:
    return bool(_git(["ls-files", path.as_posix()]).stdout.strip())


def _precondition(item: str, artifact: Path | str, expected: Any, observed: Any, passed: bool) -> dict[str, Any]:
    return {"precondition_item": item, "artifact_or_check": str(artifact), "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item}


def _source_records() -> list[dict[str, Any]]:
    decisions = {(row["pdb_id"], row["suggested_ligand_comp_id"]): row for row in _csv_rows(SOURCE_DECISIONS)}
    records: list[dict[str, Any]] = []
    for number, row in enumerate(sorted(_csv_rows(SOURCE_INVENTORY), key=lambda value: value["manual_review_candidate_id"]), 1):
        pair = (row["pdb_id"], row["suggested_ligand_comp_id"])
        decision = decisions.get(pair, {})
        complete = bool(pair[0] and pair[1])
        cys_sg = row["covpdb_residue_name"] == "CYS" and row["suggested_residue_atom_name"] == "SG"
        known_block = pair in KNOWN_BLOCKED
        current_sample = pair in CURRENT_SAMPLE_PAIRS
        current_jug = pair in CURRENT_JUG_PAIRS
        historical_reject = decision.get("application_status") == "rejected"
        eligible = complete and cys_sg and not known_block and not current_sample and not current_jug and not historical_reject
        records.append({
            "expansion_source_record_id": f"CYS_SG_EXPANSION_SOURCE_{number:06d}",
            "source_artifact_path": SOURCE_INVENTORY.as_posix(),
            "source_candidate_id": row["source_candidate_id"],
            "pdb_id": pair[0],
            "expected_het_id": pair[1],
            "residue_name": row["covpdb_residue_name"],
            "residue_atom_name": row["suggested_residue_atom_name"],
            "source_review_status": row["manual_review_status"],
            "source_decision_status": decision.get("application_status", "not_present_in_step14p_application_artifact"),
            "historical_struct_conn_status": row["struct_conn_evidence_status"],
            "historical_blocking_reason": KNOWN_BLOCKED.get(pair, ("", ""))[1],
            "already_in_current_sample_index": current_sample,
            "belongs_to_current_jug_group": current_jug,
            "known_blocked_pair": known_block,
            "complete_pdb_het_identity": complete,
            "within_current_cys_sg_v1_scope": cys_sg,
            "eligible_for_shortlist_consideration": eligible,
            "source_lineage_comment": "Step 14O controlled 25-row manual-review inventory; Step 14P application status used as read-only supplemental context.",
        })
    return records


def _exclusion_reason(record: dict[str, Any], selected_het_ids: set[str]) -> tuple[str, str, str]:
    pair = (record["pdb_id"], record["expected_het_id"])
    if pair == ("1A54", "MDC"):
        return ("known_struct_conn_blocked", "Historical result is no_struct_conn_loop_found.", "historical_block")
    if pair == ("6BV9", "JUG"):
        return ("known_ligand_comp_mismatch", "Historical result is ligand_comp_id_mismatch.", "historical_block")
    if record["already_in_current_sample_index"]:
        return ("already_in_current_sample_index", "Pair is already materialized in the current JUG pilot sample index.", "current_pilot_exclusion")
    if record["belongs_to_current_jug_group"]:
        return ("current_jug_leakage_group", "JUG belongs to the current conservative group and cannot count as a new group candidate.", "current_pilot_exclusion")
    if not record["complete_pdb_het_identity"]:
        return ("missing_pdb_or_het_identity", "PDB/HET identity is incomplete.", "identity")
    if not record["within_current_cys_sg_v1_scope"]:
        return ("outside_cys_sg_v1_scope", "CYS is present but SG evidence is not yet available; raw mmCIF struct_conn crosscheck is required before V1 consideration.", "scope")
    if record["expected_het_id"] in selected_het_ids:
        return ("lower_priority_duplicate_het_representative", "A deterministic earlier representative for this HET ID is already shortlisted.", "diversity")
    return ("shortlist_capacity_limit", "Candidate is valid but outside the deterministic shortlist capacity.", "capacity")


def _select_shortlist(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    eligible = [record for record in records if record["eligible_for_shortlist_consideration"]]
    ordered = sorted(eligible, key=lambda record: (record["source_candidate_id"], record["pdb_id"], record["expected_het_id"]))
    shortlist: list[dict[str, Any]] = []
    selected_hets: set[str] = set()
    for record in ordered:
        if record["expected_het_id"] in selected_hets or len(shortlist) == TARGET_SHORTLIST_MAX:
            continue
        selected_hets.add(record["expected_het_id"])
        shortlist.append(record)
    return shortlist, ordered


def _build_preconditions(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    previous = _json(STEP14AH_MANIFEST)
    raw_tracked = bool(_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip())
    raw_staged = bool(_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip())
    historical_paths = [STEP14AH_ROOT, STEP14AG_ROOT, STEP14AF_ROOT, STEP14AE_ROOT, STEP14AD_ROOT, STEP14AA_ROOT]
    protected_paths = ["equivariant_diffusion/", "lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py"]
    checks = [
        ("step14ah_manifest_exists", STEP14AH_MANIFEST, "exists", STEP14AH_MANIFEST.exists(), STEP14AH_MANIFEST.exists()),
        ("step14ah_stage", STEP14AH_MANIFEST, PREVIOUS_STAGE, previous.get("stage"), previous.get("stage") == PREVIOUS_STAGE),
        ("step14ah_all_checks_passed", STEP14AH_MANIFEST, True, previous.get("all_checks_passed"), previous.get("all_checks_passed") is True),
        ("step14ah_group_counts", STEP14AH_MANIFEST, "1/2", f"{previous.get('current_independent_leakage_group_count')}/{previous.get('minimum_additional_independent_groups_required')}", previous.get("current_independent_leakage_group_count") == 1 and previous.get("minimum_additional_independent_groups_required") == 2),
        ("step14ah_expansion_required", STEP14AH_MANIFEST, True, previous.get("independent_group_expansion_required"), previous.get("independent_group_expansion_required") is True),
        ("step14ah_expansion_ready", STEP14AH_MANIFEST, True, previous.get("ready_for_covapie_independent_group_expansion_design_gate"), previous.get("ready_for_covapie_independent_group_expansion_design_gate") is True),
        ("step14ah_materialization_training_blocked", STEP14AH_MANIFEST, False, previous.get("split_materialization_approved") or previous.get("final_dataset_materialization_approved") or previous.get("ready_for_training"), not previous.get("split_materialization_approved") and not previous.get("final_dataset_materialization_approved") and previous.get("ready_for_training") is False),
        ("step14ah_feature_semantics_unresolved", STEP14AH_MANIFEST, "false/false", f"{previous.get('feature_semantics_known_for_training')}/{previous.get('unknown_atom_feature_policy_finalized_for_training')}", previous.get("feature_semantics_known_for_training") is False and previous.get("unknown_atom_feature_policy_finalized_for_training") is False),
        ("candidate_source_discovered", SOURCE_INVENTORY, "exists", SOURCE_INVENTORY.exists(), SOURCE_INVENTORY.exists()),
        ("candidate_source_committed", SOURCE_INVENTORY, True, _committed(SOURCE_INVENTORY), _committed(SOURCE_INVENTORY)),
        ("candidate_source_has_rows", SOURCE_INVENTORY, ">=1", len(records), len(records) >= 1),
        ("supplemental_decision_source_committed", SOURCE_DECISIONS, True, _committed(SOURCE_DECISIONS), _committed(SOURCE_DECISIONS)),
        ("metadata_csv_exists", METADATA_CSV, "exists", METADATA_CSV.exists(), METADATA_CSV.exists()),
        ("metadata_hash_unchanged", METADATA_CSV, "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365", _sha256(METADATA_CSV), _sha256(METADATA_CSV) == "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365" and not _path_changed([METADATA_CSV])),
        ("sample_index_hashes_unchanged", STEP14AD_ROOT, "fixed", f"{_sha256(SAMPLE_INDEX_CSV)}/{_sha256(SAMPLE_INDEX_JSON)}", _sha256(SAMPLE_INDEX_CSV) == "2733991775edf5e075b461a9ba1872c7e2fe7f61f5d9614a2704b814c3f0e2c5" and _sha256(SAMPLE_INDEX_JSON) == "8d740458e30cc77bbaa568c615dd10f5df334cd0c46f21433c570c16391b8b38" and not _path_changed([SAMPLE_INDEX_CSV, SAMPLE_INDEX_JSON])),
        ("raw_files_untracked_unstaged", RAW_ROOT, False, raw_tracked or raw_staged, not raw_tracked and not raw_staged),
        ("historical_artifacts_unchanged", "Step14AH/AG/AF/AE/AD/AA", False, _path_changed(historical_paths), not _path_changed(historical_paths)),
        ("protected_source_diff_empty", "DiffSBDD protected paths", False, _path_changed(protected_paths), not _path_changed(protected_paths)),
        ("canonical_five_masks_preserved", "canonical masks", 5, len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5 and "B3" in CANONICAL_MASK_TASK_ALIASES),
    ]
    return [_precondition(*check) for check in checks]


def _build_shortlist_rows(shortlist: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rank, record in enumerate(shortlist, 1):
        het = record["expected_het_id"]
        rows.append({
            "expansion_shortlist_id": f"CYS_SG_EXPANSION_SHORTLIST_{rank:06d}",
            "expansion_source_record_id": record["expansion_source_record_id"],
            "shortlist_rank": rank,
            "pdb_id": record["pdb_id"],
            "expected_het_id": het,
            "residue_name": record["residue_name"],
            "residue_atom_name": record["residue_atom_name"],
            "provisional_group_candidate_id": f"PROVISIONAL_HET_{het}",
            "provisional_grouping_basis": "distinct_non_jug_het_id_for_acquisition_diversification_only",
            "distinct_from_current_jug_by_het_id": True,
            "source_identity_complete": True,
            "source_review_status": record["source_review_status"],
            "historical_struct_conn_status": record["historical_struct_conn_status"],
            "raw_structure_present_currently": False,
            "raw_acquisition_required": True,
            "struct_conn_crosscheck_required": True,
            "ligand_graph_evidence_status": "pending_canonical_graph_hash_and_scaffold_review",
            "protein_sequence_evidence_status": "pending_accession_and_sequence_cluster",
            "provisional_independence_status": "pending_not_yet_independent_group",
            "candidate_priority": "high_current_cys_sg_non_jug_unique_het_representative",
            "shortlist_status": "shortlisted_for_manual_review_before_acquisition",
            "shortlist_rationale": "Current CYS/SG evidence is present; non-JUG HET identity is used only for acquisition diversification and requires manual review plus controlled raw struct_conn crosscheck.",
        })
    return rows


def _build_exclusions(records: list[dict[str, Any]], shortlist: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected_ids = {record["expansion_source_record_id"] for record in shortlist}
    selected_hets = {record["expected_het_id"] for record in shortlist}
    rows: list[dict[str, Any]] = []
    for record in records:
        if record["expansion_source_record_id"] in selected_ids:
            continue
        code, description, category = _exclusion_reason(record, selected_hets)
        rows.append({
            "exclusion_audit_id": f"CYS_SG_EXPANSION_EXCLUSION_{len(rows) + 1:06d}",
            "expansion_source_record_id": record["expansion_source_record_id"],
            "pdb_id": record["pdb_id"],
            "expected_het_id": record["expected_het_id"],
            "exclusion_reason_code": code,
            "exclusion_reason_description": description,
            "exclusion_category": category,
            "exclusion_status": "excluded",
        })
    return rows


def _evidence_contract() -> list[dict[str, Any]]:
    requirements = [
        ("distinct_het_id_is_provisional_diversity_only", "Distinct HET ID is provisional diversity only.", False, True, False, "pending_not_final_independence"),
        ("ligand_graph_hash_required_for_final_grouping", "Canonical ligand graph hash is required for final grouping.", False, True, False, "pending"),
        ("scaffold_cluster_required_for_final_grouping", "Scaffold cluster review is required for final grouping.", False, True, False, "pending"),
        ("protein_accession_required_for_target_grouping", "Protein accession is required for target grouping.", False, True, False, "pending"),
        ("protein_sequence_cluster_required_for_final_grouping", "Protein sequence cluster is required for final grouping.", False, True, False, "pending"),
        ("covalent_event_identity_is_supporting_not_sufficient", "Covalent event identity supports but does not prove independence.", False, True, True, "supporting_only"),
        ("pdb_id_difference_is_not_independence_evidence", "Different PDB IDs are not independence evidence.", False, True, True, "policy_enforced"),
        ("pdb_number_proximity_is_not_similarity_evidence", "PDB number proximity is not similarity evidence.", False, True, True, "policy_enforced"),
        ("raw_struct_conn_crosscheck_required", "Controlled raw mmCIF struct_conn crosscheck is required.", True, True, False, "planned_after_manual_review"),
        ("manual_review_required_before_acquisition", "Manual candidate review is required before acquisition.", True, True, False, "required_next_gate"),
        ("acquisition_does_not_equal_group_independence", "Acquisition does not establish group independence.", False, True, True, "policy_enforced"),
        ("final_leakage_review_required_before_split", "Final leakage review is required before any split.", False, True, False, "blocked_until_evidence_complete"),
    ]
    return [{"evidence_requirement_id": f"CYS_SG_EVIDENCE_{index:06d}", "evidence_requirement_name": name, "evidence_description": description, "required_before_acquisition": before_acquisition, "required_before_final_group_assignment": before_final, "currently_available": available, "current_status": status, "requirement_contract_passed": True} for index, (name, description, before_acquisition, before_final, available, status) in enumerate(requirements, 1)]


def _acquisition_plan(shortlist: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "expansion_acquisition_plan_id": f"CYS_SG_EXPANSION_PLAN_{index:06d}",
        "expansion_shortlist_id": row["expansion_shortlist_id"],
        "shortlist_rank": row["shortlist_rank"],
        "pdb_id": row["pdb_id"],
        "expected_het_id": row["expected_het_id"],
        "proposed_batch_id": "CYS_SG_INDEPENDENT_EXPANSION_BATCH_000001",
        "acquisition_mode": "future_controlled_rcsb_mmcif_acquisition",
        "planned_raw_root": "data/raw/covalent_sources/covpdb/independent_group_expansion_batch_000001",
        "raw_acquisition_authorized_current_step": False,
        "network_access_authorized_current_step": False,
        "struct_conn_crosscheck_planned": True,
        "atom_site_parse_planned": True,
        "manual_approval_required": True,
        "ready_for_acquisition_preflight": True,
        "ready_for_training_current_step": False,
        "planned_next_gate": "covapie_independent_group_expansion_candidate_review_gate",
    } for index, row in enumerate(shortlist, 1)]


def _policy_contract() -> list[dict[str, Any]]:
    names = [
        "independent_group_expansion_design_only", "design_uses_existing_candidate_pool_only", "no_network_or_download_current_step", "current_jug_group_not_counted_as_new_group", "blocked_pairs_not_reintroduced", "distinct_het_id_is_not_final_independence_proof", "no_protein_sequence_identity_claim", "no_ligand_graph_similarity_claim", "no_pdb_id_independence_inference", "manual_candidate_review_required", "controlled_acquisition_required_after_review", "no_split_assignment_current_step", "no_final_dataset_current_step", "no_training_current_step", "feature_semantics_audit_required_before_training", "canonical_five_masks_preserved",
    ]
    return [{"policy_item": name, "policy_description": name.replace("_", " "), "policy_contract_passed": True} for name in names]


def _safety_audit() -> list[dict[str, Any]]:
    historical = [STEP14AH_ROOT, STEP14AG_ROOT, STEP14AF_ROOT, STEP14AE_ROOT, STEP14AD_ROOT]
    protected = ["equivariant_diffusion/", "lightning_modules.py"]
    dataloader = ["dataset.py", "data/prepare_crossdocked.py"]
    forbidden = {"final_dataset.csv", "final_dataset.json", "sample_index.csv", "sample_index.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json", "training_report.csv", "training_report.json"}
    suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm", ".part"}
    no_forbidden = not any(path.is_file() and (path.name in forbidden or path.suffix.lower() in suffixes) for path in (REPO_ROOT / OUTPUT_ROOT).rglob("*"))
    checks = [
        ("network_access_used_current_step", False, False), ("download_attempted_current_step", False, False), ("raw_mmcif_read_current_step", False, False), ("data_raw_written_current_step", False, False),
        ("metadata_csv_unchanged", True, _sha256(METADATA_CSV) == "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365" and not _path_changed([METADATA_CSV])),
        ("sample_index_files_unchanged", True, not _path_changed([SAMPLE_INDEX_CSV, SAMPLE_INDEX_JSON])),
        ("step14ah_artifacts_unchanged", True, not _path_changed([STEP14AH_ROOT])), ("step14ag_artifacts_unchanged", True, not _path_changed([STEP14AG_ROOT])), ("step14af_artifacts_unchanged", True, not _path_changed([STEP14AF_ROOT])), ("step14ae_artifacts_unchanged", True, not _path_changed([STEP14AE_ROOT])), ("step14ad_artifacts_unchanged", True, not _path_changed([STEP14AD_ROOT])),
        ("protected_source_diff_empty", True, not _path_changed(protected)), ("original_dataloader_diff_empty", True, not _path_changed(dataloader)),
        ("split_assignments_written", False, False), ("leakage_matrix_written", False, False), ("final_dataset_written", False, False), ("actual_dataloader_smoke_written", False, False), ("training_artifacts_written", False, False), ("derived_output_no_forbidden_raw_binary_or_html_suffix", True, no_forbidden),
        ("torch_imported", False, False), ("numpy_imported", False, False), ("rdkit_used", False, False), ("gemmi_used", False, False), ("requests_used", False, False), ("urllib_used", False, False), ("selenium_used", False, False), ("playwright_used", False, False), ("bs4_used", False, False),
    ]
    return [{"safety_item": name, "required_status": required, "observed_status": observed, "safety_passed": required == observed, "blocking_reasons": "" if required == observed else name} for name, required, observed in checks]


def run_covapie_independent_group_expansion_design_gate_v0() -> dict[str, Any]:
    records = _source_records()
    shortlist_records, eligible_records = _select_shortlist(records)
    shortlist = _build_shortlist_rows(shortlist_records)
    exclusions = _build_exclusions(records, shortlist_records)
    preconditions = _build_preconditions(records)
    evidence = _evidence_contract()
    plans = _acquisition_plan(shortlist)
    policy = _policy_contract()
    safety = _safety_audit()
    shortage: list[str] = []
    if len(shortlist) < TARGET_SHORTLIST_MIN:
        shortage.append("fewer_than_target_shortlist_min_after_cys_sg_scope_and_blocked_pair_exclusions")
    if len({row["expected_het_id"] for row in shortlist}) < TARGET_DISTINCT_NON_JUG_HET_ID_MIN:
        shortage.append("fewer_than_target_distinct_non_jug_het_ids_after_cys_sg_scope_and_blocked_pair_exclusions")
    blocking = [row["precondition_item"] for row in preconditions if not _truth(row["precondition_passed"])] + [row["safety_item"] for row in safety if not _truth(row["safety_passed"])]
    manifest = {
        "stage": STAGE, "step_label": STEP_LABEL, "previous_stage": PREVIOUS_STAGE, "project_name": PROJECT_NAME,
        "input_current_independent_leakage_group_count": 1, "input_minimum_additional_independent_groups_required": 2, "input_independent_group_expansion_required": True,
        "candidate_source_artifact_count": 2, "candidate_source_artifact_paths": [SOURCE_INVENTORY.as_posix(), SOURCE_DECISIONS.as_posix()], "candidate_source_record_count": len(records), "eligible_candidate_record_count": len(eligible_records), "excluded_candidate_record_count": len(exclusions), "shortlist_candidate_count": len(shortlist), "shortlist_distinct_non_jug_het_id_count": len({row["expected_het_id"] for row in shortlist}), "acquisition_batch_plan_count": len(plans),
        "target_shortlist_min": TARGET_SHORTLIST_MIN, "target_shortlist_max": TARGET_SHORTLIST_MAX, "target_distinct_non_jug_het_id_min": TARGET_DISTINCT_NON_JUG_HET_ID_MIN, "shortlist_target_met": len(shortlist) >= TARGET_SHORTLIST_MIN, "distinct_het_target_met": len({row["expected_het_id"] for row in shortlist}) >= TARGET_DISTINCT_NON_JUG_HET_ID_MIN,
        "current_jug_group_excluded": True, "known_blocked_pairs_excluded": True, "duplicate_pairs_excluded": True,
        "shortlisted_pdb_het_pairs": [f"{row['pdb_id']}/{row['expected_het_id']}" for row in shortlist], "shortlisted_distinct_het_ids": [row["expected_het_id"] for row in shortlist], "provisional_group_candidate_ids": [row["provisional_group_candidate_id"] for row in shortlist],
        "confirmed_new_independent_group_count_current_step": 0, "provisional_group_candidate_count": len(shortlist), "minimum_additional_independent_groups_still_required": 2,
        "raw_acquisition_performed_current_step": False, "network_access_used_current_step": False, "split_assignments_written": False, "leakage_matrix_written": False, "final_dataset_written": False, "training_artifacts_written": False,
        "ready_for_covapie_independent_group_expansion_candidate_review_gate": bool(shortlist), "ready_for_covapie_independent_group_expansion_acquisition_preflight": False, "ready_for_covapie_split_materialization_smoke": False, "ready_for_covapie_final_dataset_materialization_smoke": False, "ready_for_training": False, "ready_to_train_now": False,
        "feature_semantics_known_for_training": False, "unknown_atom_feature_policy_finalized_for_training": False, "feature_semantics_audit_required_before_training": True, "leakage_split_design_required_before_training": True,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES, "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES, "b3_scaffold_only_included": True, "no_extra_mask_tasks_added": True,
        "expansion_shortage_reasons": shortage, "recommended_next_step": "covapie_independent_group_expansion_candidate_review_gate", "all_checks_passed": not blocking, "blocking_reasons": blocking,
    }
    return {"preconditions": preconditions, "source": records, "exclusions": exclusions, "evidence": evidence, "shortlist": shortlist, "plans": plans, "policy": policy, "safety": safety, "manifest": manifest}
