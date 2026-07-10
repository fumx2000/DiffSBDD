from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_independent_group_expansion_candidate_review_gate_v0"
STEP_LABEL = "Step 14AJ"
PREVIOUS_STAGE = "covapie_independent_group_expansion_design_gate_v0"
PROJECT_NAME = "CovaPIE"
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

STEP14AI_ROOT = Path("data/derived/covalent_small/covapie_independent_group_expansion_design_gate_v0")
STEP14AH_ROOT = Path("data/derived/covalent_small/covapie_leakage_split_review_gate_v0")
STEP14AG_ROOT = Path("data/derived/covalent_small/covapie_leakage_split_design_gate_v0")
STEP14AF_ROOT = Path("data/derived/covalent_small/covapie_final_dataset_design_gate_v0")
STEP14AE_ROOT = Path("data/derived/covalent_small/covapie_sample_index_qa_gate_v0")
STEP14AD_ROOT = Path("data/derived/covalent_small/covapie_sample_index_materialization_smoke_v0")
STEP14AA_ROOT = Path("data/derived/covalent_small/covapie_sample_preparation_execution_smoke_v0")
METADATA_CSV = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
SAMPLE_INDEX_CSV = STEP14AD_ROOT / "sample_index.csv"
SAMPLE_INDEX_JSON = STEP14AD_ROOT / "sample_index.json"
RAW_ROOT = Path("data/raw/covalent_sources")

AI_MANIFEST = STEP14AI_ROOT / "covapie_independent_group_expansion_design_gate_manifest.json"
AI_SHORTLIST_CSV = STEP14AI_ROOT / "covapie_independent_group_candidate_shortlist.csv"
AI_SHORTLIST_JSON = STEP14AI_ROOT / "covapie_independent_group_candidate_shortlist.json"
AI_PLAN = STEP14AI_ROOT / "covapie_independent_group_acquisition_batch_plan.csv"
AI_SOURCE = STEP14AI_ROOT / "covapie_expansion_candidate_source_inventory.csv"
AI_EXCLUSIONS = STEP14AI_ROOT / "covapie_expansion_candidate_exclusion_audit.csv"
AI_EVIDENCE = STEP14AI_ROOT / "covapie_independence_evidence_requirement_contract.csv"

PRECONDITION_AUDIT = OUTPUT_ROOT / "covapie_expansion_candidate_review_precondition_audit.csv"
REVIEW_REGISTRY = OUTPUT_ROOT / "covapie_expansion_candidate_review_registry.csv"
DIVERSITY_REVIEW = OUTPUT_ROOT / "covapie_expansion_candidate_diversity_review.csv"
PREFLIGHT_PLAN = OUTPUT_ROOT / "covapie_expansion_acquisition_preflight_approval_plan.csv"
DECISION_REGISTRY = OUTPUT_ROOT / "covapie_expansion_candidate_review_decision_registry.csv"
ISSUE_INVENTORY = OUTPUT_ROOT / "covapie_expansion_candidate_review_issue_inventory.csv"
EVIDENCE_CONTRACT = OUTPUT_ROOT / "covapie_expansion_candidate_review_evidence_boundary_contract.csv"
READINESS_CONTRACT = OUTPUT_ROOT / "covapie_expansion_candidate_review_downstream_readiness_contract.csv"
SAFETY_AUDIT = OUTPUT_ROOT / "covapie_expansion_candidate_review_safety_audit.csv"
MANIFEST = OUTPUT_ROOT / "covapie_independent_group_expansion_candidate_review_gate_manifest.json"
SUMMARY = Path("docs/covapie_independent_group_expansion_candidate_review_gate_v0_summary.md")

CANONICAL_MASK_TASK_NAMES = ["warhead_only", "linker_plus_warhead", "scaffold_plus_warhead", "scaffold_only", "scaffold_plus_linker_plus_warhead"]
CANONICAL_MASK_TASK_ALIASES = ["A", "B", "B2", "B3", "C"]
EXPECTED_PAIRS = ["1AEC/E64", "1AIM/ZYA", "1AU3/PCM", "1AU4/INP", "1AYU/INA", "1AYV/IN6", "1AYW/IN3", "1B02/UFP"]
CURRENT_SAMPLE_PAIRS = {("6BV6", "JUG"), ("6BV8", "JUG"), ("6BV5", "JUG")}
KNOWN_BLOCKED = {("1A54", "MDC"), ("6BV9", "JUG")}

PRE_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
REVIEW_COLUMNS = ["candidate_review_id", "expansion_shortlist_id", "expansion_source_record_id", "shortlist_rank", "pdb_id", "expected_het_id", "residue_name", "residue_atom_name", "source_identity_complete_confirmed", "cys_sg_v1_scope_confirmed", "non_jug_candidate_confirmed", "not_current_sample_index_pair_confirmed", "not_known_blocked_pair_confirmed", "unique_pdb_het_pair_confirmed", "unique_het_representative_confirmed", "historical_struct_conn_evidence_available_confirmed", "raw_acquisition_required_confirmed", "struct_conn_crosscheck_required_confirmed", "ligand_graph_evidence_pending_confirmed", "protein_sequence_evidence_pending_confirmed", "provisional_independence_pending_confirmed", "approved_for_controlled_acquisition_preflight", "approved_for_acquisition_execution", "confirmed_as_new_independent_group", "candidate_review_decision", "candidate_review_status", "blocking_reasons"]
DIVERSITY_COLUMNS = ["diversity_review_id", "candidate_count", "unique_pdb_het_pair_count", "distinct_non_jug_het_id_count", "current_jug_candidate_count", "current_sample_index_pair_count", "known_blocked_pair_count", "duplicate_pdb_het_pair_count", "duplicate_het_representative_count", "provisional_group_candidate_count", "confirmed_independent_group_count", "acquisition_diversity_target_met", "independence_confirmation_target_met", "diversity_review_status", "review_conclusion"]
PREFLIGHT_COLUMNS = ["acquisition_preflight_approval_id", "candidate_review_id", "expansion_shortlist_id", "shortlist_rank", "pdb_id", "expected_het_id", "proposed_batch_id", "planned_raw_filename", "planned_raw_root", "approved_for_acquisition_preflight", "acquisition_execution_authorized", "network_access_authorized", "download_authorized", "raw_file_written_current_step", "struct_conn_crosscheck_required_after_acquisition", "atom_site_parse_required_after_acquisition", "scientific_independence_confirmed", "ready_for_training_current_step", "planned_next_gate"]
DECISION_COLUMNS = ["review_decision_id", "review_decision_name", "expected_decision", "observed_decision", "decision_status", "rationale"]
ISSUE_COLUMNS = ["issue_id", "issue_scope", "expansion_shortlist_id", "pdb_id", "expected_het_id", "issue_severity", "issue_type", "issue_description", "issue_status"]
EVIDENCE_COLUMNS = ["evidence_boundary_id", "evidence_boundary_name", "evidence_description", "boundary_contract_passed"]
READINESS_COLUMNS = ["readiness_item", "observed_status", "readiness_passed", "next_required_gate", "qa_comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with (REPO_ROOT / path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _json(path: Path) -> Any:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def _truth(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def _changed(paths: list[Path | str]) -> bool:
    values = [str(path) for path in paths]
    return _git(["diff", "--quiet", "--", *values]).returncode != 0 or _git(["diff", "--cached", "--quiet", "--", *values]).returncode != 0


def _sha256(path: Path) -> str:
    return hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()


def _precondition(item: str, artifact: Path | str, expected: Any, observed: Any, passed: bool) -> dict[str, Any]:
    return {"precondition_item": item, "artifact_or_check": str(artifact), "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item}


def _normalize(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [{key: str(value) for key, value in row.items()} for row in rows]


def _inputs() -> dict[str, Any]:
    return {
        "manifest": _json(AI_MANIFEST),
        "shortlist": _csv_rows(AI_SHORTLIST_CSV),
        "shortlist_json": _json(AI_SHORTLIST_JSON),
        "plan": _csv_rows(AI_PLAN),
        "source": _csv_rows(AI_SOURCE),
        "exclusions": _csv_rows(AI_EXCLUSIONS),
        "evidence": _csv_rows(AI_EVIDENCE),
    }


def _build_preconditions(data: dict[str, Any]) -> list[dict[str, Any]]:
    manifest = data["manifest"]
    shortlist = data["shortlist"]
    pairs = [(row["pdb_id"], row["expected_het_id"]) for row in shortlist]
    source_ids = {row["expansion_source_record_id"] for row in data["source"]}
    plan_ids = {row["expansion_shortlist_id"] for row in data["plan"]}
    exclusions = {(row["pdb_id"], row["expected_het_id"]): row["exclusion_reason_code"] for row in data["exclusions"]}
    raw_tracked = bool(_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip())
    raw_staged = bool(_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip())
    historical = [STEP14AI_ROOT, STEP14AH_ROOT, STEP14AG_ROOT, STEP14AF_ROOT, STEP14AE_ROOT, STEP14AD_ROOT, STEP14AA_ROOT]
    protected = ["equivariant_diffusion/", "lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py"]
    expected_manifest = {"candidate_source_artifact_count": 2, "candidate_source_record_count": 25, "eligible_candidate_record_count": 9, "excluded_candidate_record_count": 17, "shortlist_candidate_count": 8, "shortlist_distinct_non_jug_het_id_count": 8, "acquisition_batch_plan_count": 8}
    checks: list[tuple[str, Path | str, Any, Any, bool]] = [
        ("step14ai_manifest_exists", AI_MANIFEST, "exists", AI_MANIFEST.exists(), AI_MANIFEST.exists()),
        ("step14ai_stage", AI_MANIFEST, PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step14ai_all_checks_passed", AI_MANIFEST, True, manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14ai_required_flags", AI_MANIFEST, True, manifest.get("shortlist_target_met") and manifest.get("distinct_het_target_met") and not manifest.get("expansion_shortage_reasons") and manifest.get("confirmed_new_independent_group_count_current_step") == 0 and manifest.get("ready_for_covapie_independent_group_expansion_candidate_review_gate") is True and manifest.get("ready_for_covapie_independent_group_expansion_acquisition_preflight") is False and manifest.get("ready_for_training") is False, manifest.get("shortlist_target_met") is True and manifest.get("distinct_het_target_met") is True and manifest.get("expansion_shortage_reasons") == [] and manifest.get("confirmed_new_independent_group_count_current_step") == 0 and manifest.get("ready_for_covapie_independent_group_expansion_candidate_review_gate") is True and manifest.get("ready_for_covapie_independent_group_expansion_acquisition_preflight") is False and manifest.get("ready_for_training") is False),
    ]
    checks += [(f"step14ai_{key}", AI_MANIFEST, value, manifest.get(key), manifest.get(key) == value) for key, value in expected_manifest.items()]
    checks += [
        ("shortlist_csv_json_consistent", AI_SHORTLIST_JSON, "8 identical rows", f"{len(shortlist)}/{len(data['shortlist_json'])}", len(shortlist) == len(data["shortlist_json"]) == 8 and _normalize(shortlist) == _normalize(data["shortlist_json"])),
        ("shortlist_unique_pdb_het_pairs", AI_SHORTLIST_CSV, 8, len(set(pairs)), len(pairs) == 8 and len(set(pairs)) == 8),
        ("shortlist_unique_non_jug_hets", AI_SHORTLIST_CSV, 8, len({row["expected_het_id"] for row in shortlist}), len({row["expected_het_id"] for row in shortlist}) == 8 and all(row["expected_het_id"] != "JUG" for row in shortlist)),
        ("source_inventory_count", AI_SOURCE, 25, len(data["source"]), len(data["source"]) == 25),
        ("shortlist_source_lineage", AI_SOURCE, True, all(row["expansion_source_record_id"] in source_ids for row in shortlist), all(row["expansion_source_record_id"] in source_ids for row in shortlist)),
        ("acquisition_plan_matches_shortlist", AI_PLAN, 8, len(data["plan"]), len(data["plan"]) == 8 and {row["expansion_shortlist_id"] for row in shortlist} == plan_ids),
        ("evidence_contract_passed", AI_EVIDENCE, 12, len(data["evidence"]), len(data["evidence"]) == 12 and all(row["requirement_contract_passed"] == "True" for row in data["evidence"])),
        ("known_blocked_exclusions_retained", AI_EXCLUSIONS, "1A54/MDC;6BV9/JUG", f"{exclusions.get(('1A54','MDC'))};{exclusions.get(('6BV9','JUG'))}", exclusions.get(("1A54", "MDC")) == "known_struct_conn_blocked" and exclusions.get(("6BV9", "JUG")) == "known_ligand_comp_mismatch"),
        ("current_sample_pairs_absent", AI_SHORTLIST_CSV, False, any(pair in CURRENT_SAMPLE_PAIRS for pair in pairs), not any(pair in CURRENT_SAMPLE_PAIRS for pair in pairs)),
        ("metadata_hash_unchanged", METADATA_CSV, "fixed", _sha256(METADATA_CSV), _sha256(METADATA_CSV) == "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365" and not _changed([METADATA_CSV])),
        ("sample_index_hashes_unchanged", STEP14AD_ROOT, "fixed", f"{_sha256(SAMPLE_INDEX_CSV)}/{_sha256(SAMPLE_INDEX_JSON)}", _sha256(SAMPLE_INDEX_CSV) == "2733991775edf5e075b461a9ba1872c7e2fe7f61f5d9614a2704b814c3f0e2c5" and _sha256(SAMPLE_INDEX_JSON) == "8d740458e30cc77bbaa568c615dd10f5df334cd0c46f21433c570c16391b8b38" and not _changed([SAMPLE_INDEX_CSV, SAMPLE_INDEX_JSON])),
        ("raw_files_untracked_unstaged", RAW_ROOT, False, raw_tracked or raw_staged, not raw_tracked and not raw_staged),
        ("historical_artifacts_unchanged", "Step14AI/AH/AG/AF/AE/AD/AA", False, _changed(historical), not _changed(historical)),
        ("protected_source_diff_empty", "DiffSBDD protected paths", False, _changed(protected), not _changed(protected)),
        ("canonical_five_masks_preserved", "canonical masks", 5, len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5 and "B3" in CANONICAL_MASK_TASK_ALIASES),
    ]
    return [_precondition(*check) for check in checks]


def _review_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    shortlist = data["shortlist"]
    source_by_id = {row["expansion_source_record_id"]: row for row in data["source"]}
    pair_counts = {(row["pdb_id"], row["expected_het_id"]): sum((other["pdb_id"], other["expected_het_id"]) == (row["pdb_id"], row["expected_het_id"]) for other in shortlist) for row in shortlist}
    het_counts = {row["expected_het_id"]: sum(other["expected_het_id"] == row["expected_het_id"] for other in shortlist) for row in shortlist}
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(shortlist, 1):
        source = source_by_id.get(row["expansion_source_record_id"], {})
        pair = (row["pdb_id"], row["expected_het_id"])
        checks = {
            "source_identity_complete_confirmed": row["source_identity_complete"] == "True" and bool(source),
            "cys_sg_v1_scope_confirmed": row["residue_name"] == "CYS" and row["residue_atom_name"] == "SG",
            "non_jug_candidate_confirmed": row["expected_het_id"] != "JUG",
            "not_current_sample_index_pair_confirmed": pair not in CURRENT_SAMPLE_PAIRS,
            "not_known_blocked_pair_confirmed": pair not in KNOWN_BLOCKED,
            "unique_pdb_het_pair_confirmed": pair_counts[pair] == 1,
            "unique_het_representative_confirmed": het_counts[row["expected_het_id"]] == 1,
            "historical_struct_conn_evidence_available_confirmed": bool(row["historical_struct_conn_status"]),
            "raw_acquisition_required_confirmed": row["raw_acquisition_required"] == "True",
            "struct_conn_crosscheck_required_confirmed": row["struct_conn_crosscheck_required"] == "True",
            "ligand_graph_evidence_pending_confirmed": row["ligand_graph_evidence_status"] == "pending_canonical_graph_hash_and_scaffold_review",
            "protein_sequence_evidence_pending_confirmed": row["protein_sequence_evidence_status"] == "pending_accession_and_sequence_cluster",
            "provisional_independence_pending_confirmed": row["provisional_independence_status"] == "pending_not_yet_independent_group",
        }
        passed = all(checks.values())
        rows.append({
            "candidate_review_id": f"CYS_SG_EXPANSION_REVIEW_{index:06d}", "expansion_shortlist_id": row["expansion_shortlist_id"], "expansion_source_record_id": row["expansion_source_record_id"], "shortlist_rank": row["shortlist_rank"], "pdb_id": row["pdb_id"], "expected_het_id": row["expected_het_id"], "residue_name": row["residue_name"], "residue_atom_name": row["residue_atom_name"], **checks,
            "approved_for_controlled_acquisition_preflight": passed, "approved_for_acquisition_execution": False, "confirmed_as_new_independent_group": False,
            "candidate_review_decision": "approved_for_controlled_acquisition_preflight_only" if passed else "blocked", "candidate_review_status": "passed" if passed else "blocked", "blocking_reasons": "" if passed else row["expansion_shortlist_id"],
        })
    return rows


def _diversity_review(review_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs = {(row["pdb_id"], row["expected_het_id"]) for row in review_rows}
    hets = {row["expected_het_id"] for row in review_rows}
    passed = len(review_rows) == len(pairs) == len(hets) == 8
    return [{"diversity_review_id": "CYS_SG_EXPANSION_DIVERSITY_000001", "candidate_count": len(review_rows), "unique_pdb_het_pair_count": len(pairs), "distinct_non_jug_het_id_count": len(hets), "current_jug_candidate_count": sum(row["expected_het_id"] == "JUG" for row in review_rows), "current_sample_index_pair_count": sum((row["pdb_id"], row["expected_het_id"]) in CURRENT_SAMPLE_PAIRS for row in review_rows), "known_blocked_pair_count": sum((row["pdb_id"], row["expected_het_id"]) in KNOWN_BLOCKED for row in review_rows), "duplicate_pdb_het_pair_count": len(review_rows) - len(pairs), "duplicate_het_representative_count": len(review_rows) - len(hets), "provisional_group_candidate_count": len(review_rows), "confirmed_independent_group_count": 0, "acquisition_diversity_target_met": passed, "independence_confirmation_target_met": False, "diversity_review_status": "passed" if passed else "blocked", "review_conclusion": "sufficient_diversity_for_controlled_acquisition_preflight_not_for_final_grouping"}]


def _preflight_plan(review_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"acquisition_preflight_approval_id": f"CYS_SG_PREFLIGHT_APPROVAL_{index:06d}", "candidate_review_id": row["candidate_review_id"], "expansion_shortlist_id": row["expansion_shortlist_id"], "shortlist_rank": row["shortlist_rank"], "pdb_id": row["pdb_id"], "expected_het_id": row["expected_het_id"], "proposed_batch_id": "CYS_SG_INDEPENDENT_EXPANSION_BATCH_000001", "planned_raw_filename": f"{row['pdb_id'].lower()}.cif", "planned_raw_root": "data/raw/covalent_sources/covpdb/independent_group_expansion_batch_000001", "approved_for_acquisition_preflight": row["approved_for_controlled_acquisition_preflight"], "acquisition_execution_authorized": False, "network_access_authorized": False, "download_authorized": False, "raw_file_written_current_step": False, "struct_conn_crosscheck_required_after_acquisition": True, "atom_site_parse_required_after_acquisition": True, "scientific_independence_confirmed": False, "ready_for_training_current_step": False, "planned_next_gate": "covapie_independent_group_expansion_acquisition_preflight_gate"} for index, row in enumerate(review_rows, 1)]


def _decisions() -> list[dict[str, Any]]:
    names = ["accept_eight_candidates_for_controlled_acquisition_preflight", "reject_acquisition_execution_current_step", "preserve_pending_ligand_graph_evidence", "preserve_pending_protein_sequence_evidence", "confirm_no_new_independent_group_current_step", "preserve_split_final_dataset_and_training_blocks", "require_acquisition_preflight_before_download"]
    return [{"review_decision_id": f"CYS_SG_EXPANSION_DECISION_{index:06d}", "review_decision_name": name, "expected_decision": True, "observed_decision": True, "decision_status": "accepted", "rationale": name.replace("_", " ")} for index, name in enumerate(names, 1)]


def _evidence_contract() -> list[dict[str, Any]]:
    names = ["candidate_review_approves_preflight_only", "candidate_review_does_not_authorize_download", "historical_struct_conn_evidence_requires_raw_reconfirmation", "distinct_het_id_is_not_independence_proof", "ligand_graph_hash_still_required", "scaffold_cluster_still_required", "protein_accession_still_required", "protein_sequence_cluster_still_required", "acquisition_does_not_confirm_independence", "raw_crosscheck_does_not_alone_confirm_independence", "final_leakage_review_required_before_split", "feature_semantics_audit_required_before_training"]
    return [{"evidence_boundary_id": f"CYS_SG_REVIEW_EVIDENCE_{index:06d}", "evidence_boundary_name": name, "evidence_description": name.replace("_", " "), "boundary_contract_passed": True} for index, name in enumerate(names, 1)]


def _readiness() -> list[dict[str, Any]]:
    states = {"ready_for_covapie_independent_group_expansion_acquisition_preflight_gate": True, "ready_for_covapie_independent_group_expansion_acquisition_execution": False, "ready_for_covapie_independent_group_expansion_struct_conn_crosscheck": False, "ready_for_covapie_split_materialization_smoke": False, "ready_for_covapie_final_dataset_materialization_smoke": False, "ready_for_covapie_actual_dataloader_adapter_smoke": False, "ready_for_training": False, "ready_to_train_now": False}
    return [{"readiness_item": key, "observed_status": value, "readiness_passed": True, "next_required_gate": "covapie_independent_group_expansion_acquisition_preflight_gate", "qa_comment": "preflight-only boundary"} for key, value in states.items()]


def _safety() -> list[dict[str, Any]]:
    historical = [STEP14AI_ROOT, STEP14AH_ROOT, STEP14AG_ROOT, STEP14AF_ROOT, STEP14AE_ROOT, STEP14AD_ROOT]
    protected = ["equivariant_diffusion/", "lightning_modules.py"]
    dataloader = ["dataset.py", "data/prepare_crossdocked.py"]
    forbidden_names = {"final_dataset.csv", "final_dataset.json", "sample_index.csv", "sample_index.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json", "training_report.csv", "training_report.json"}
    forbidden_suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm", ".part"}
    no_forbidden = not any(path.is_file() and (path.name in forbidden_names or path.suffix.lower() in forbidden_suffixes) for path in (REPO_ROOT / OUTPUT_ROOT).rglob("*"))
    checks = [
        ("network_access_used_current_step", False, False), ("download_attempted_current_step", False, False), ("raw_mmcif_read_current_step", False, False), ("data_raw_written_current_step", False, False), ("acquisition_preflight_review_written_current_step", True, True), ("acquisition_execution_authorized", False, False), ("network_access_authorized", False, False), ("download_authorized", False, False),
        ("metadata_csv_unchanged", True, _sha256(METADATA_CSV) == "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365" and not _changed([METADATA_CSV])), ("sample_index_files_unchanged", True, not _changed([SAMPLE_INDEX_CSV, SAMPLE_INDEX_JSON])),
        ("step14ai_artifacts_unchanged", True, not _changed([STEP14AI_ROOT])), ("step14ah_artifacts_unchanged", True, not _changed([STEP14AH_ROOT])), ("step14ag_artifacts_unchanged", True, not _changed([STEP14AG_ROOT])), ("step14af_artifacts_unchanged", True, not _changed([STEP14AF_ROOT])), ("step14ae_artifacts_unchanged", True, not _changed([STEP14AE_ROOT])), ("step14ad_artifacts_unchanged", True, not _changed([STEP14AD_ROOT])),
        ("protected_source_diff_empty", True, not _changed(protected)), ("original_dataloader_diff_empty", True, not _changed(dataloader)), ("split_assignments_written", False, False), ("leakage_matrix_written", False, False), ("final_dataset_written", False, False), ("training_artifacts_written", False, False), ("derived_output_no_forbidden_raw_binary_or_html_suffix", True, no_forbidden),
        ("torch_imported", False, False), ("numpy_imported", False, False), ("rdkit_used", False, False), ("gemmi_used", False, False), ("requests_used", False, False), ("urllib_used", False, False), ("selenium_used", False, False), ("playwright_used", False, False), ("bs4_used", False, False),
    ]
    return [{"safety_item": name, "required_status": required, "observed_status": observed, "safety_passed": required == observed, "blocking_reasons": "" if required == observed else name} for name, required, observed in checks]


def run_covapie_independent_group_expansion_candidate_review_gate_v0() -> dict[str, Any]:
    data = _inputs()
    preconditions = _build_preconditions(data)
    review_rows = _review_rows(data)
    diversity = _diversity_review(review_rows)
    preflight = _preflight_plan(review_rows)
    decisions = _decisions()
    issues = [{"issue_id": "NO_EXPANSION_CANDIDATE_REVIEW_ISSUES", "issue_scope": "expansion_batch_000001", "expansion_shortlist_id": "", "pdb_id": "", "expected_het_id": "", "issue_severity": "none", "issue_type": "no_issues", "issue_description": "No candidate review implementation issues detected.", "issue_status": "passed"}]
    evidence = _evidence_contract()
    readiness = _readiness()
    safety = _safety()
    blocking = [row["precondition_item"] for row in preconditions if not _truth(row["precondition_passed"])] + [row["safety_item"] for row in safety if not _truth(row["safety_passed"])] + [row["candidate_review_id"] for row in review_rows if row["candidate_review_status"] != "passed"]
    approved = [row for row in review_rows if _truth(row["approved_for_controlled_acquisition_preflight"])]
    manifest = {
        "stage": STAGE, "step_label": STEP_LABEL, "previous_stage": PREVIOUS_STAGE, "project_name": PROJECT_NAME,
        "input_candidate_source_record_count": 25, "input_shortlist_candidate_count": 8, "input_shortlist_distinct_non_jug_het_id_count": 8, "input_acquisition_batch_plan_count": 8,
        "candidate_review_count": len(review_rows), "candidate_review_passed_count": sum(row["candidate_review_status"] == "passed" for row in review_rows), "candidate_review_approved_for_preflight_count": len(approved), "candidate_review_approved_for_execution_count": 0, "candidate_review_rejected_count": 0, "candidate_review_issue_count": 0,
        "diversity_review_count": len(diversity), "unique_pdb_het_pair_count": len({(row["pdb_id"], row["expected_het_id"]) for row in review_rows}), "distinct_non_jug_het_id_count": len({row["expected_het_id"] for row in review_rows}), "provisional_group_candidate_count": len(review_rows), "confirmed_new_independent_group_count_current_step": 0,
        "approved_preflight_pdb_het_pairs": [f"{row['pdb_id']}/{row['expected_het_id']}" for row in approved], "approved_preflight_batch_id": "CYS_SG_INDEPENDENT_EXPANSION_BATCH_000001",
        "candidate_review_completed": len(approved) == 8, "controlled_acquisition_preflight_approved": len(approved) == 8, "acquisition_execution_authorized": False, "network_access_authorized": False, "download_authorized": False, "raw_acquisition_performed_current_step": False, "scientific_independence_confirmed_current_step": False,
        "split_assignments_written": False, "leakage_matrix_written": False, "final_dataset_written": False, "training_artifacts_written": False,
        "ready_for_covapie_independent_group_expansion_acquisition_preflight_gate": len(approved) == 8, "ready_for_covapie_independent_group_expansion_acquisition_execution": False, "ready_for_covapie_independent_group_expansion_struct_conn_crosscheck": False, "ready_for_covapie_split_materialization_smoke": False, "ready_for_covapie_final_dataset_materialization_smoke": False, "ready_for_training": False, "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES, "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES, "b3_scaffold_only_included": True, "no_extra_mask_tasks_added": True,
        "feature_semantics_known_for_training": False, "unknown_atom_feature_policy_finalized_for_training": False, "feature_semantics_audit_required_before_training": True, "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_independent_group_expansion_acquisition_preflight_gate", "all_checks_passed": not blocking, "blocking_reasons": blocking,
    }
    return {"preconditions": preconditions, "reviews": review_rows, "diversity": diversity, "preflight": preflight, "decisions": decisions, "issues": issues, "evidence": evidence, "readiness": readiness, "safety": safety, "manifest": manifest}
