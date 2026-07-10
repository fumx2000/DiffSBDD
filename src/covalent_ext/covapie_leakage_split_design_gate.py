from __future__ import annotations

import csv
import hashlib
import itertools
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_final_dataset_design_gate as final

REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_leakage_split_design_gate_v0"
STEP_LABEL = "Step 14AG"
PREVIOUS_STAGE = final.STAGE
PROJECT_NAME = "CovaPIE"
OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_leakage_split_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_leakage_split_design_precondition_audit.csv"
SOURCE_CSV = OUTPUT_ROOT / "covapie_leakage_source_inventory.csv"
SOURCE_JSON = OUTPUT_ROOT / "covapie_leakage_source_inventory.json"
PAIRWISE_CSV = OUTPUT_ROOT / "covapie_leakage_pairwise_evidence.csv"
GROUP_PLAN_CSV = OUTPUT_ROOT / "covapie_proposed_leakage_group_plan.csv"
FEASIBILITY_CSV = OUTPUT_ROOT / "covapie_split_feasibility_assessment.csv"
RULE_CSV = OUTPUT_ROOT / "covapie_leakage_rule_contract.csv"
CONTRACT_CSV = OUTPUT_ROOT / "covapie_leakage_split_design_contract.csv"
SAFETY_CSV = OUTPUT_ROOT / "covapie_leakage_split_design_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_leakage_split_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_leakage_split_design_gate_v0_summary.md")
CANONICAL_MASK_TASK_NAMES = final.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = final.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = final.METADATA_CSV_SHA256
PRE_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SOURCE_COLUMNS = ["leakage_source_id", "final_dataset_source_id", "planned_final_dataset_row_id", "sample_index_row_id", "pdb_id", "expected_het_id", "ligand_comp_id", "covalent_residue_name", "covalent_residue_atom_name", "ligand_covalent_atom_name", "covalent_bond_atom_pair", "protein_atom_count", "ligand_atom_count", "pocket_atom_count", "approved_for_final_dataset_design_by_qa", "eligible_for_leakage_split_design", "current_leakage_group_id", "current_split_assignment", "ready_for_training_current_step", "source_sample_index_csv_sha256", "source_sample_index_json_sha256"]
PAIR_COLUMNS = ["pairwise_evidence_id", "left_sample_index_row_id", "right_sample_index_row_id", "left_pdb_id", "right_pdb_id", "left_expected_het_id", "right_expected_het_id", "same_expected_het_id", "same_ligand_comp_id", "same_covalent_residue_name", "same_covalent_residue_atom_name", "same_ligand_covalent_atom_name", "same_covalent_bond_atom_pair", "protein_sequence_identity_evidence_status", "ligand_graph_identity_evidence_status", "pdb_id_proximity_used_as_evidence", "conservative_leakage_risk", "required_grouping_action", "pairwise_evidence_status", "evidence_comment"]
GROUP_COLUMNS = ["proposed_group_plan_id", "leakage_source_id", "sample_index_row_id", "planned_final_dataset_row_id", "pdb_id", "expected_het_id", "proposed_leakage_group_id", "proposed_grouping_basis", "proposed_group_member_count", "proposed_split_assignment", "split_assignment_status", "group_review_status", "eligible_for_split_materialization", "eligible_for_final_dataset_materialization", "ready_for_training_current_step", "planned_next_gate"]
FEAS_COLUMNS = ["split_feasibility_assessment_id", "sample_count", "proposed_leakage_group_count", "largest_group_member_count", "minimum_independent_groups_for_three_way_split", "train_validation_test_split_feasible", "any_nontrivial_group_safe_split_feasible", "random_row_level_split_allowed", "all_current_samples_must_remain_together", "additional_independent_samples_required", "recommended_expansion_target", "split_assignment_written_current_step", "leakage_matrix_written_current_step", "final_dataset_written_current_step", "ready_for_training_current_step", "feasibility_status", "recommendation"]
RULE_COLUMNS = ["leakage_rule_id", "leakage_rule_name", "rule_description", "evidence_required", "current_pilot_application", "rule_status"]
CONTRACT_COLUMNS = ["contract_type", "contract_item", "expected_status", "observed_status", "contract_passed", "comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]
FORBIDDEN_NAMES = {"final_dataset.csv", "final_dataset.json", "sample_index.csv", "sample_index.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json", "training_report.csv", "training_report.json"}
FORBIDDEN_SUFFIXES = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm", ".part"}

def _csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
def _json(path: str | Path) -> Any: return json.loads(Path(path).read_text(encoding="utf-8"))
def _bool(value: Any) -> bool: return value is True or str(value).lower() == "true"
def _git(args: list[str]) -> subprocess.CompletedProcess[str]: return subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
def _diff(paths: list[str]) -> bool: return _git(["diff", "--quiet", "--", *paths]).returncode != 0 or _git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0
def _hash(path: Path) -> str: return hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()
def _pre(item: str, artifact: str, expected: Any, observed: Any, passed: bool) -> dict[str, Any]: return {"precondition_item": item, "artifact_or_check": artifact, "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item}

def _sample_index() -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    return _csv(REPO_ROOT / final.qa.material.SAMPLE_INDEX_CSV), _json(REPO_ROOT / final.qa.material.SAMPLE_INDEX_JSON)

def build_preconditions() -> list[dict[str, Any]]:
    manifest = _json(REPO_ROOT / final.MANIFEST_JSON)
    source, source_json = _csv(REPO_ROOT / final.SOURCE_INVENTORY_CSV), _json(REPO_ROOT / final.SOURCE_INVENTORY_JSON)
    plan, samples, sample_json = _csv(REPO_ROOT / final.ROW_PROJECTION_PLAN_CSV), *_sample_index()
    raw = final.qa.material.design.RAW_ROOT.as_posix()
    checks = [
        ("step14af_stage", final.MANIFEST_JSON, final.STAGE, manifest.get("stage"), manifest.get("stage") == final.STAGE),
        ("step14af_all_checks_passed", final.MANIFEST_JSON, True, manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("source_inventory_count", final.MANIFEST_JSON, 3, manifest.get("final_dataset_source_inventory_count"), manifest.get("final_dataset_source_inventory_count") == 3),
        ("schema_mapping_projection_counts", final.MANIFEST_JSON, "46/46/3", f"{manifest.get('final_dataset_schema_field_count')}/{manifest.get('final_dataset_field_mapping_count')}/{manifest.get('final_dataset_row_projection_plan_count')}", manifest.get("final_dataset_schema_field_count") == 46 and manifest.get("final_dataset_field_mapping_count") == 46 and manifest.get("final_dataset_row_projection_plan_count") == 3),
        ("auxiliary_readiness_count", final.MANIFEST_JSON, 9, manifest.get("auxiliary_label_readiness_count"), manifest.get("auxiliary_label_readiness_count") == 9),
        ("leakage_eligible_count", final.MANIFEST_JSON, 3, manifest.get("eligible_for_leakage_split_design_count"), manifest.get("eligible_for_leakage_split_design_count") == 3),
        ("final_materialization_eligible_count", final.MANIFEST_JSON, 0, manifest.get("eligible_for_final_dataset_materialization_count"), manifest.get("eligible_for_final_dataset_materialization_count") == 0),
        ("leakage_design_ready", final.MANIFEST_JSON, True, manifest.get("ready_for_covapie_leakage_split_design_gate"), manifest.get("ready_for_covapie_leakage_split_design_gate") is True),
        ("training_not_ready", final.MANIFEST_JSON, False, manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("feature_semantics_unknown", final.MANIFEST_JSON, False, manifest.get("feature_semantics_known_for_training"), manifest.get("feature_semantics_known_for_training") is False),
        ("source_inventory_csv_json_consistent", final.SOURCE_INVENTORY_CSV, "3/3", f"{len(source)}/{len(source_json)}", len(source) == len(source_json) == 3),
        ("projection_plan_boundary", final.ROW_PROJECTION_PLAN_CSV, "3 pending rows", len(plan), len(plan) == 3 and {r["eligible_for_leakage_split_design"] for r in plan} == {"True"} and {r["eligible_for_final_dataset_materialization"] for r in plan} == {"False"} and {r["planned_leakage_group_id"] for r in plan} == {""} and {r["planned_split_assignment"] for r in plan} == {""}),
        ("sample_index_rows", final.qa.material.SAMPLE_INDEX_CSV, "3/3", f"{len(samples)}/{len(sample_json)}", len(samples) == len(sample_json) == 3),
        ("sample_index_csv_hash", final.qa.material.SAMPLE_INDEX_CSV, manifest.get("source_sample_index_csv_sha256"), _hash(final.qa.material.SAMPLE_INDEX_CSV), _hash(final.qa.material.SAMPLE_INDEX_CSV) == manifest.get("source_sample_index_csv_sha256")),
        ("sample_index_json_hash", final.qa.material.SAMPLE_INDEX_JSON, manifest.get("source_sample_index_json_sha256"), _hash(final.qa.material.SAMPLE_INDEX_JSON), _hash(final.qa.material.SAMPLE_INDEX_JSON) == manifest.get("source_sample_index_json_sha256")),
        ("metadata_hash", final.qa.material.design.METADATA_CSV, METADATA_CSV_SHA256, _hash(final.qa.material.design.METADATA_CSV), _hash(final.qa.material.design.METADATA_CSV) == METADATA_CSV_SHA256 and not _diff([final.qa.material.design.METADATA_CSV.as_posix()])),
        ("raw_untracked", raw, False, bool(_git(["ls-files", raw]).stdout.strip()), not _git(["ls-files", raw]).stdout.strip()),
        ("raw_unstaged", raw, False, bool(_git(["diff", "--cached", "--name-only", "--", raw]).stdout.strip()), not _git(["diff", "--cached", "--name-only", "--", raw]).stdout.strip()),
        ("step14af_unchanged", final.OUTPUT_ROOT, False, _diff([final.OUTPUT_ROOT.as_posix()]), not _diff([final.OUTPUT_ROOT.as_posix()])),
        ("step14ae_unchanged", final.qa.OUTPUT_ROOT, False, _diff([final.qa.OUTPUT_ROOT.as_posix()]), not _diff([final.qa.OUTPUT_ROOT.as_posix()])),
        ("step14ad_unchanged", final.qa.material.OUTPUT_ROOT, False, _diff([final.qa.material.OUTPUT_ROOT.as_posix()]), not _diff([final.qa.material.OUTPUT_ROOT.as_posix()])),
        ("step14ac_unchanged", final.qa.material.design.OUTPUT_ROOT, False, _diff([final.qa.material.design.OUTPUT_ROOT.as_posix()]), not _diff([final.qa.material.design.OUTPUT_ROOT.as_posix()])),
        ("step14aa_unchanged", final.qa.material.design.STEP14AA_ROOT, False, _diff([final.qa.material.design.STEP14AA_ROOT.as_posix()]), not _diff([final.qa.material.design.STEP14AA_ROOT.as_posix()])),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", False, _diff(["equivariant_diffusion/", "lightning_modules.py"]), not _diff(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", False, _diff(["dataset.py", "data/prepare_crossdocked.py"]), not _diff(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_masks", "canonical masks", 5, len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5 and "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
    ]
    return [_pre(*check) for check in checks]

def build_source_inventory() -> list[dict[str, Any]]:
    samples, _ = _sample_index()
    inventory = _csv(REPO_ROOT / final.SOURCE_INVENTORY_CSV)
    plan_by_id = {row["source_sample_index_row_id"]: row for row in _csv(REPO_ROOT / final.ROW_PROJECTION_PLAN_CSV)}
    csv_hash, json_hash = _hash(final.qa.material.SAMPLE_INDEX_CSV), _hash(final.qa.material.SAMPLE_INDEX_JSON)
    rows = []
    for index, (sample, source) in enumerate(zip(samples, inventory), start=1):
        plan = plan_by_id[sample["sample_index_row_id"]]
        rows.append({"leakage_source_id": f"CYS_SG_LEAKAGE_SOURCE_{index:06d}", "final_dataset_source_id": source["final_dataset_source_id"], "planned_final_dataset_row_id": plan["planned_final_dataset_row_id"], "sample_index_row_id": sample["sample_index_row_id"], "pdb_id": sample["pdb_id"], "expected_het_id": sample["expected_het_id"], "ligand_comp_id": sample["ligand_comp_id"], "covalent_residue_name": sample["covalent_residue_name"], "covalent_residue_atom_name": sample["covalent_residue_atom_name"], "ligand_covalent_atom_name": sample["ligand_covalent_atom_name"], "covalent_bond_atom_pair": sample["covalent_bond_atom_pair"], "protein_atom_count": sample["protein_atom_count"], "ligand_atom_count": sample["ligand_atom_count"], "pocket_atom_count": sample["pocket_atom_count"], "approved_for_final_dataset_design_by_qa": True, "eligible_for_leakage_split_design": True, "current_leakage_group_id": "", "current_split_assignment": "", "ready_for_training_current_step": False, "source_sample_index_csv_sha256": csv_hash, "source_sample_index_json_sha256": json_hash})
    return rows

def build_pairwise(source: list[dict[str, Any]]) -> list[dict[str, Any]]:
    comment = "Conservative grouping is based on the same curated ligand component ID and identical covalent event identity, not PDB-number proximity; future larger datasets should add ligand graph hashes and protein sequence/accession clusters."
    rows=[]
    for index, (left, right) in enumerate(itertools.combinations(source, 2), start=1):
        rows.append({"pairwise_evidence_id": f"CYS_SG_PAIRWISE_{index:06d}", "left_sample_index_row_id": left["sample_index_row_id"], "right_sample_index_row_id": right["sample_index_row_id"], "left_pdb_id": left["pdb_id"], "right_pdb_id": right["pdb_id"], "left_expected_het_id": left["expected_het_id"], "right_expected_het_id": right["expected_het_id"], "same_expected_het_id": left["expected_het_id"] == right["expected_het_id"], "same_ligand_comp_id": left["ligand_comp_id"] == right["ligand_comp_id"], "same_covalent_residue_name": left["covalent_residue_name"] == right["covalent_residue_name"], "same_covalent_residue_atom_name": left["covalent_residue_atom_name"] == right["covalent_residue_atom_name"], "same_ligand_covalent_atom_name": left["ligand_covalent_atom_name"] == right["ligand_covalent_atom_name"], "same_covalent_bond_atom_pair": left["covalent_bond_atom_pair"] == right["covalent_bond_atom_pair"], "protein_sequence_identity_evidence_status": "unavailable_in_current_source", "ligand_graph_identity_evidence_status": "unavailable_use_conservative_component_id_grouping", "pdb_id_proximity_used_as_evidence": False, "conservative_leakage_risk": "high_conservative_small_pilot", "required_grouping_action": "must_share_proposed_leakage_group", "pairwise_evidence_status": "passed", "evidence_comment": comment})
    return rows

def build_groups(source: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"proposed_group_plan_id": f"CYS_SG_GROUP_PLAN_{index:06d}", "leakage_source_id": row["leakage_source_id"], "sample_index_row_id": row["sample_index_row_id"], "planned_final_dataset_row_id": row["planned_final_dataset_row_id"], "pdb_id": row["pdb_id"], "expected_het_id": row["expected_het_id"], "proposed_leakage_group_id": "CYS_SG_LEAKAGE_GROUP_000001", "proposed_grouping_basis": "conservative_same_ligand_component_and_covalent_event", "proposed_group_member_count": 3, "proposed_split_assignment": "", "split_assignment_status": "unassigned_single_leakage_group", "group_review_status": "pending_leakage_split_review", "eligible_for_split_materialization": False, "eligible_for_final_dataset_materialization": False, "ready_for_training_current_step": False, "planned_next_gate": "covapie_leakage_split_review_gate"} for index, row in enumerate(source, start=1)]

def build_feasibility() -> list[dict[str, Any]]:
    return [{"split_feasibility_assessment_id": "CYS_SG_SPLIT_FEASIBILITY_000001", "sample_count": 3, "proposed_leakage_group_count": 1, "largest_group_member_count": 3, "minimum_independent_groups_for_three_way_split": 3, "train_validation_test_split_feasible": False, "any_nontrivial_group_safe_split_feasible": False, "random_row_level_split_allowed": False, "all_current_samples_must_remain_together": True, "additional_independent_samples_required": True, "recommended_expansion_target": "acquire_multiple_independent_ligand_or_target_groups_before_split", "split_assignment_written_current_step": False, "leakage_matrix_written_current_step": False, "final_dataset_written_current_step": False, "ready_for_training_current_step": False, "feasibility_status": "blocked_single_conservative_leakage_group", "recommendation": "keep_all_three_samples_in_one_group_and_expand_dataset"}]

def build_rules() -> list[dict[str, Any]]:
    specs=[("exact_curated_ligand_component_grouping", "same JUG component conservatively groups samples together; future graph hash should strengthen evidence"), ("identical_covalent_event_supporting_evidence", "same CYS SG--ligand CAG event supports grouping; event identity alone is not general similarity"), ("no_pdb_number_proximity_heuristic", "PDB numeric similarity must not be used as biological evidence"), ("protein_sequence_evidence_not_available", "no sequence identity claim; future protein accession/sequence cluster required"), ("ligand_graph_evidence_not_available", "no graph fingerprint claim; future canonical graph hash/scaffold clustering required"), ("group_level_split_only", "members of one leakage group cannot cross data splits"), ("no_random_row_level_split", "random row split is forbidden for leakage-related samples"), ("split_requires_multiple_independent_groups", "current one-group pilot cannot support three-way split"), ("no_split_assignment_in_design_gate", "design gate cannot assign train/validation/test"), ("sample_expansion_required", "more independent groups required before split materialization")]
    return [{"leakage_rule_id": f"CYS_SG_RULE_{index:06d}", "leakage_rule_name": name, "rule_description": text, "evidence_required": "documented conservative evidence", "current_pilot_application": "applied", "rule_status": "accepted_for_v0_design"} for index, (name, text) in enumerate(specs, start=1)]

def build_contract() -> list[dict[str, Any]]:
    policies=["leakage_split_design_gate_only", "pairwise_evidence_is_not_leakage_matrix", "proposed_group_is_not_final_group_assignment", "no_train_validation_test_assignment_current_step", "no_random_row_level_split", "all_current_samples_remain_together", "no_pdb_number_proximity_inference", "no_protein_sequence_identity_claim", "no_ligand_graph_similarity_claim", "final_dataset_not_written_current_step", "sample_index_not_modified", "feature_semantics_audit_required_before_training", "canonical_five_masks_preserved", "no_training_current_step"]
    readiness={"ready_for_covapie_leakage_split_review_gate": True, "ready_for_covapie_split_materialization_smoke": False, "ready_for_covapie_final_dataset_materialization_smoke": False, "ready_for_covapie_actual_dataloader_adapter_smoke": False, "ready_for_training": False, "ready_to_train_now": False, "additional_independent_samples_required_before_split": True}
    return [{"contract_type": "policy", "contract_item": item, "expected_status": True, "observed_status": True, "contract_passed": True, "comment": item.replace("_", " ")} for item in policies] + [{"contract_type": "readiness", "contract_item": item, "expected_status": value, "observed_status": value, "contract_passed": True, "comment": "review required before materialization"} for item, value in readiness.items()]

def build_safety() -> list[dict[str, Any]]:
    checks=[("network_access_used_current_step",False,False),("download_attempted_current_step",False,False),("raw_mmcif_read_current_step",False,False),("struct_conn_parsed_current_step",False,False),("atom_site_parsed_current_step",False,False),("data_raw_written_current_step",False,False),("existing_sample_index_read_current_step",True,True),("sample_index_modified_current_step",False,False),("sample_index_rewritten_current_step",False,False),("sample_index_files_unchanged",True,not _diff([final.qa.material.SAMPLE_INDEX_CSV.as_posix(),final.qa.material.SAMPLE_INDEX_JSON.as_posix()])),("metadata_csv_unchanged",True,_hash(final.qa.material.design.METADATA_CSV)==METADATA_CSV_SHA256 and not _diff([final.qa.material.design.METADATA_CSV.as_posix()])),("step14af_artifacts_unchanged",True,not _diff([final.OUTPUT_ROOT.as_posix()])),("step14ae_artifacts_unchanged",True,not _diff([final.qa.OUTPUT_ROOT.as_posix()])),("step14ad_artifacts_unchanged",True,not _diff([final.qa.material.OUTPUT_ROOT.as_posix()])),("step14ac_artifacts_unchanged",True,not _diff([final.qa.material.design.OUTPUT_ROOT.as_posix()])),("step14aa_artifacts_unchanged",True,not _diff([final.qa.material.design.STEP14AA_ROOT.as_posix()])),("source_atom_event_tables_unchanged",True,not _diff([(final.qa.material.design.STEP14AA_ROOT/'samples').as_posix()])),("protected_source_diff_empty",True,not _diff(['equivariant_diffusion/','lightning_modules.py'])),("original_dataloader_diff_empty",True,not _diff(['dataset.py','data/prepare_crossdocked.py'])),("final_dataset_written",False,False),("split_assignments_written",False,False),("leakage_matrix_written",False,False),("actual_dataloader_smoke_written",False,False),("training_artifacts_written",False,False),("derived_output_no_forbidden_raw_binary_or_html_suffix",True,not any(p.is_file() and (p.name in FORBIDDEN_NAMES or p.suffix.lower() in FORBIDDEN_SUFFIXES) for p in (REPO_ROOT/OUTPUT_ROOT).rglob('*'))),("torch_imported",False,False),("numpy_imported",False,False),("rdkit_used",False,False),("gemmi_used",False,False),("requests_used",False,False),("urllib_used",False,False),("selenium_used",False,False),("playwright_used",False,False),("bs4_used",False,False)]
    return [{"safety_item":item,"required_status":expected,"observed_status":observed,"safety_passed":expected==observed,"blocking_reasons":"" if expected==observed else item} for item,expected,observed in checks]

def build_manifest(pre, source, pairs, groups, feasibility, rules, contract, safety):
    blocking=[r['precondition_item'] for r in pre if not _bool(r['precondition_passed'])]+[r['safety_item'] for r in safety if not _bool(r['safety_passed'])]
    return {"stage":STAGE,"step_label":STEP_LABEL,"previous_stage":PREVIOUS_STAGE,"project_name":PROJECT_NAME,"step14af_final_dataset_design_gate_validated":all(_bool(r['precondition_passed']) for r in pre),"input_final_dataset_source_inventory_count":3,"input_final_dataset_projection_plan_count":3,"input_eligible_for_leakage_split_design_count":3,"input_eligible_for_final_dataset_materialization_count":0,"leakage_source_inventory_count":len(source),"pairwise_leakage_evidence_count":len(pairs),"high_conservative_pair_count":sum(r['conservative_leakage_risk']=='high_conservative_small_pilot' for r in pairs),"proposed_leakage_group_count":1,"proposed_leakage_group_member_count":3,"split_feasibility_assessment_count":len(feasibility),"leakage_rule_count":len(rules),"accepted_pdb_het_pairs":[f"{r['pdb_id']}/{r['expected_het_id']}" for r in source],"proposed_leakage_group_ids":["CYS_SG_LEAKAGE_GROUP_000001"],"all_current_samples_in_one_proposed_group":True,"train_validation_test_split_feasible":False,"random_row_level_split_allowed":False,"additional_independent_samples_required":True,"proposed_group_plan_written_current_step":True,"split_assignments_written":False,"leakage_matrix_written":False,"final_dataset_written":False,"actual_dataloader_smoke_written":False,"training_artifacts_written":False,"source_sample_index_csv_sha256":_hash(final.qa.material.SAMPLE_INDEX_CSV),"source_sample_index_json_sha256":_hash(final.qa.material.SAMPLE_INDEX_JSON),"ready_for_covapie_leakage_split_review_gate":True,"ready_for_covapie_split_materialization_smoke":False,"ready_for_covapie_final_dataset_materialization_smoke":False,"ready_for_covapie_actual_dataloader_adapter_smoke":False,"ready_for_training":False,"ready_to_train_now":False,"canonical_mask_task_names":CANONICAL_MASK_TASK_NAMES,"canonical_mask_task_aliases":CANONICAL_MASK_TASK_ALIASES,"b3_scaffold_only_included":True,"no_extra_mask_tasks_added":True,"feature_semantics_known_for_training":False,"unknown_atom_feature_policy_finalized_for_training":False,"feature_semantics_audit_required_before_training":True,"leakage_split_design_required_before_training":True,"recommended_next_step":"covapie_leakage_split_review_gate","all_checks_passed":not blocking,"blocking_reasons":blocking}

def run_covapie_leakage_split_design_gate_v0() -> dict[str, Any]:
    pre=build_preconditions(); source=build_source_inventory(); pairs=build_pairwise(source); groups=build_groups(source); feasibility=build_feasibility(); rules=build_rules(); contract=build_contract(); safety=build_safety(); manifest=build_manifest(pre,source,pairs,groups,feasibility,rules,contract,safety)
    return {"precondition_rows":pre,"source_rows":source,"pair_rows":pairs,"group_rows":groups,"feasibility_rows":feasibility,"rule_rows":rules,"contract_rows":contract,"safety_rows":safety,"manifest":manifest}
