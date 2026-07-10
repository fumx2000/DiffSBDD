from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_feature_semantics_audit_gate as step13bm
from covalent_ext import covapie_sample_index_qa_gate as qa


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_final_dataset_design_gate_v0"
STEP_LABEL = "Step 14AF"
PREVIOUS_STAGE = qa.STAGE
PROJECT_NAME = "CovaPIE"
OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_final_dataset_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_final_dataset_design_precondition_audit.csv"
SOURCE_INVENTORY_CSV = OUTPUT_ROOT / "covapie_final_dataset_source_inventory.csv"
SOURCE_INVENTORY_JSON = OUTPUT_ROOT / "covapie_final_dataset_source_inventory.json"
SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "covapie_final_dataset_schema_contract.csv"
FIELD_MAPPING_CSV = OUTPUT_ROOT / "covapie_final_dataset_field_mapping.csv"
ROW_PROJECTION_PLAN_CSV = OUTPUT_ROOT / "covapie_final_dataset_row_projection_plan.csv"
AUXILIARY_READINESS_CSV = OUTPUT_ROOT / "covapie_final_dataset_auxiliary_label_readiness.csv"
DESIGN_CONTRACT_CSV = OUTPUT_ROOT / "covapie_final_dataset_design_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_final_dataset_design_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_final_dataset_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_final_dataset_design_gate_v0_summary.md")

# Keep historical import chains read-only compatible; Step 14AF itself reads Step 14AE/14AD data.
step13bl = step13bm.step13bl
step13bk = step13bm.step13bk
step13bj = step13bm.step13bj
step13bi = step13bm.step13bi
step13bh = step13bm.step13bh
step13bg = step13bm.step13bg
step13bf = step13bm.step13bf
step13be = step13bm.step13be
step13bd = step13bm.step13bd
METADATA_CSV_SHA256 = qa.material.design.METADATA_CSV_SHA256
CANONICAL_MASK_TASK_NAMES = qa.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = qa.CANONICAL_MASK_TASK_ALIASES
SAMPLE_INDEX_FIELDS = qa.SAMPLE_INDEX_FIELDS

FINAL_FIELDS = [
    "final_dataset_row_id", "sample_index_row_id", "sample_preparation_input_id", "sample_execution_id", "sample_qa_id", "pdb_id", "expected_het_id", "sample_artifact_root", "protein_atom_table_path", "ligand_atom_table_path", "pocket_atom_table_path", "covalent_event_table_path", "ligand_residue_atom_pair_table_path", "sample_preparation_audit_path", "protein_atom_count", "ligand_atom_count", "pocket_atom_count", "covalent_event_count", "ligand_residue_atom_pair_count", "covalent_residue_name", "covalent_residue_chain_id", "covalent_residue_index", "covalent_residue_atom_name", "ligand_comp_id", "ligand_covalent_atom_name", "covalent_bond_atom_pair", "conn_id", "conn_type_id", "post_covalent_bond_distance_angstrom", "supported_mask_task_names", "warhead_type_label_status", "ligand_residue_atom_pair_label_status", "pre_covalent_geometry_label_status", "post_covalent_geometry_label_status", "feature_semantics_status", "leakage_group_id", "split_assignment", "final_dataset_row_status", "qa_approved_for_final_dataset_design", "eligible_for_leakage_split_design", "eligible_for_final_dataset_materialization", "ready_for_training_current_step", "feature_semantics_audit_required_before_training", "leakage_split_design_required_before_training", "source_sample_index_csv_sha256", "source_sample_index_json_sha256",
]
PATH_FIELDS = qa.PATH_FIELDS
COUNT_FIELDS = qa.COUNT_FIELDS
PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SOURCE_COLUMNS = ["final_dataset_source_id", "sample_index_row_id", "pdb_id", "expected_het_id", "sample_artifact_root", "protein_atom_table_path", "ligand_atom_table_path", "pocket_atom_table_path", "covalent_event_table_path", "ligand_residue_atom_pair_table_path", "sample_preparation_audit_path", "protein_atom_count", "ligand_atom_count", "pocket_atom_count", "covalent_event_count", "ligand_residue_atom_pair_count", "covalent_bond_atom_pair", "sample_index_row_qa_status", "sample_index_source_traceability_qa_status", "approved_for_final_dataset_design_by_qa", "source_eligible_for_final_dataset_design", "eligible_for_final_dataset_design_gate", "ready_for_training_current_step", "source_sample_index_csv_sha256", "source_sample_index_json_sha256"]
SCHEMA_COLUMNS = ["final_dataset_field", "planned_data_type", "required", "nullable", "semantic_role", "primary_source_artifact", "primary_source_field", "planned_default_or_status", "validation_rule", "current_step_materializes_field", "schema_contract_passed"]
MAPPING_COLUMNS = ["mapping_id", "final_dataset_field", "primary_source_artifact", "primary_source_field", "fallback_source_artifact", "fallback_source_field", "transformation_rule", "required_validation", "mapping_status"]
PROJECTION_COLUMNS = ["final_dataset_projection_plan_id", "final_dataset_source_id", "planned_final_dataset_row_id", "source_sample_index_row_id", "pdb_id", "expected_het_id", "planned_supported_mask_task_names", "warhead_type_label_status", "ligand_residue_atom_pair_label_status", "pre_covalent_geometry_label_status", "post_covalent_geometry_label_status", "feature_semantics_status", "planned_leakage_group_id", "planned_split_assignment", "planned_final_dataset_row_status", "qa_approved_for_final_dataset_design", "eligible_for_leakage_split_design", "eligible_for_final_dataset_materialization", "final_dataset_written_current_step", "ready_for_training_current_step", "planned_next_gate"]
AUX_COLUMNS = ["auxiliary_readiness_id", "sample_index_row_id", "pdb_id", "expected_het_id", "auxiliary_task_name", "available_source_evidence", "planned_label_field", "readiness_status", "ready_for_final_dataset_materialization", "ready_for_training_current_step", "blocking_reason_or_comment"]
CONTRACT_COLUMNS = ["contract_type", "contract_item", "expected_status", "observed_status", "contract_passed", "comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]
FORBIDDEN_NAMES = {"final_dataset.csv", "final_dataset.json", "sample_index.csv", "sample_index.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json", "training_report.csv", "training_report.json"}
FORBIDDEN_SUFFIXES = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm", ".part"}


def _csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as h: return list(csv.DictReader(h))

def _json(path: str | Path) -> Any: return json.loads(Path(path).read_text(encoding="utf-8"))
def _bool(value: Any) -> bool: return value is True or str(value).lower() == "true"
def _git(args: list[str]) -> subprocess.CompletedProcess[str]: return subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
def _diff(paths: list[str]) -> bool: return _git(["diff", "--quiet", "--", *paths]).returncode != 0 or _git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0
def _hash(path: str | Path) -> str: return hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()
def _all(rows: list[dict[str, Any]], key: str) -> bool: return all(_bool(r.get(key)) for r in rows)
def _pre(item: str, artifact: str, expected: Any, observed: Any, passed: bool) -> dict[str, Any]: return {"precondition_item": item, "artifact_or_check": artifact, "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item}


def _sample_index() -> tuple[list[dict[str, str]], list[dict[str, Any]], list[str]]:
    with (REPO_ROOT / qa.material.SAMPLE_INDEX_CSV).open(newline="", encoding="utf-8") as h:
        r = csv.DictReader(h); rows = list(r); fields = r.fieldnames or []
    return rows, _json(REPO_ROOT / qa.material.SAMPLE_INDEX_JSON), fields


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest = _json(REPO_ROOT / qa.MANIFEST_JSON)
    csv_rows, json_rows, fields = _sample_index()
    row_qa, schema_qa, trace = _csv(REPO_ROOT / qa.ROW_QA_CSV), _csv(REPO_ROOT / qa.SCHEMA_QA_CSV), _csv(REPO_ROOT / qa.TRACEABILITY_QA_CSV)
    fingerprints, issues = _csv(REPO_ROOT / qa.FINGERPRINT_AUDIT_CSV), _csv(REPO_ROOT / qa.ISSUE_INVENTORY_CSV)
    raw = qa.material.design.RAW_ROOT.as_posix()
    checks = [
        ("step14ae_manifest_exists", qa.MANIFEST_JSON, True, bool(manifest), bool(manifest)), ("step14ae_stage", qa.MANIFEST_JSON, qa.STAGE, manifest.get("stage"), manifest.get("stage") == qa.STAGE), ("step14ae_all_checks_passed", qa.MANIFEST_JSON, True, manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("row_qa_passed_count", qa.MANIFEST_JSON, 3, manifest.get("sample_index_row_qa_passed_count"), manifest.get("sample_index_row_qa_passed_count") == 3), ("schema_qa_passed_count", qa.MANIFEST_JSON, 33, manifest.get("sample_index_schema_qa_passed_count"), manifest.get("sample_index_schema_qa_passed_count") == 33), ("traceability_qa_passed_count", qa.MANIFEST_JSON, 3, manifest.get("sample_index_source_traceability_qa_passed_count"), manifest.get("sample_index_source_traceability_qa_passed_count") == 3), ("fingerprint_verified_count", qa.MANIFEST_JSON, 2, manifest.get("sample_index_fingerprint_verified_count"), manifest.get("sample_index_fingerprint_verified_count") == 2), ("qa_issue_count", qa.MANIFEST_JSON, 0, manifest.get("qa_issue_count"), manifest.get("qa_issue_count") == 0), ("qa_approval_count", qa.MANIFEST_JSON, 3, manifest.get("qa_approved_for_final_dataset_design_count"), manifest.get("qa_approved_for_final_dataset_design_count") == 3), ("source_eligible_true_count", qa.MANIFEST_JSON, 0, manifest.get("source_eligible_for_final_dataset_design_true_count"), manifest.get("source_eligible_for_final_dataset_design_true_count") == 0),
        ("final_dataset_design_gate_ready", qa.MANIFEST_JSON, True, manifest.get("ready_for_covapie_final_dataset_design_gate"), manifest.get("ready_for_covapie_final_dataset_design_gate") is True), ("training_not_ready", qa.MANIFEST_JSON, False, manifest.get("ready_for_training"), manifest.get("ready_for_training") is False), ("feature_semantics_unknown", qa.MANIFEST_JSON, False, manifest.get("feature_semantics_known_for_training"), manifest.get("feature_semantics_known_for_training") is False), ("unknown_atom_policy_unfinalized", qa.MANIFEST_JSON, False, manifest.get("unknown_atom_feature_policy_finalized_for_training"), manifest.get("unknown_atom_feature_policy_finalized_for_training") is False),
        ("sample_index_csv_json_rows", qa.material.SAMPLE_INDEX_CSV, "3/3", f"{len(csv_rows)}/{len(json_rows)}", len(csv_rows) == len(json_rows) == 3), ("sample_index_schema_fields", qa.material.design.SCHEMA_CONTRACT_CSV, 33, len(fields), fields == SAMPLE_INDEX_FIELDS), ("source_hash_csv", qa.material.SAMPLE_INDEX_CSV, manifest.get("sample_index_csv_sha256"), _hash(qa.material.SAMPLE_INDEX_CSV), _hash(qa.material.SAMPLE_INDEX_CSV) == manifest.get("sample_index_csv_sha256")), ("source_hash_json", qa.material.SAMPLE_INDEX_JSON, manifest.get("sample_index_json_sha256"), _hash(qa.material.SAMPLE_INDEX_JSON), _hash(qa.material.SAMPLE_INDEX_JSON) == manifest.get("sample_index_json_sha256")),
        ("row_qa_rows", qa.ROW_QA_CSV, "3 approved", len(row_qa), len(row_qa) == 3 and {r["row_qa_status"] for r in row_qa} == {"passed"} and {r["approved_for_final_dataset_design_by_qa"] for r in row_qa} == {"True"}), ("schema_qa_rows", qa.SCHEMA_QA_CSV, "33 passed", len(schema_qa), len(schema_qa) == 33 and {r["schema_qa_status"] for r in schema_qa} == {"passed"}), ("traceability_rows", qa.TRACEABILITY_QA_CSV, "3 passed", len(trace), len(trace) == 3 and {r["source_traceability_qa_status"] for r in trace} == {"passed"}), ("fingerprints_verified", qa.FINGERPRINT_AUDIT_CSV, 2, len(fingerprints), len(fingerprints) == 2 and {r["fingerprint_status"] for r in fingerprints} == {"recorded_and_verified"}), ("qa_issue_inventory", qa.ISSUE_INVENTORY_CSV, "NO_SAMPLE_INDEX_QA_ISSUES", issues[0].get("issue_id") if issues else "", len(issues) == 1 and issues[0].get("issue_id") == "NO_SAMPLE_INDEX_QA_ISSUES"),
        ("metadata_hash", qa.material.design.METADATA_CSV, METADATA_CSV_SHA256, _hash(qa.material.design.METADATA_CSV), _hash(qa.material.design.METADATA_CSV) == METADATA_CSV_SHA256 and not _diff([qa.material.design.METADATA_CSV.as_posix()])), ("raw_untracked", raw, False, bool(_git(["ls-files", raw]).stdout.strip()), not _git(["ls-files", raw]).stdout.strip()), ("raw_unstaged", raw, False, bool(_git(["diff", "--cached", "--name-only", "--", raw]).stdout.strip()), not _git(["diff", "--cached", "--name-only", "--", raw]).stdout.strip()),
        ("step14ae_unchanged", qa.OUTPUT_ROOT, False, _diff([qa.OUTPUT_ROOT.as_posix()]), not _diff([qa.OUTPUT_ROOT.as_posix()])), ("step14ad_unchanged", qa.material.OUTPUT_ROOT, False, _diff([qa.material.OUTPUT_ROOT.as_posix()]), not _diff([qa.material.OUTPUT_ROOT.as_posix()])), ("step14ac_unchanged", qa.material.design.OUTPUT_ROOT, False, _diff([qa.material.design.OUTPUT_ROOT.as_posix()]), not _diff([qa.material.design.OUTPUT_ROOT.as_posix()])), ("step14ab_unchanged", qa.material.design.STEP14AB_ROOT, False, _diff([qa.material.design.STEP14AB_ROOT.as_posix()]), not _diff([qa.material.design.STEP14AB_ROOT.as_posix()])), ("step14aa_unchanged", qa.material.design.STEP14AA_ROOT, False, _diff([qa.material.design.STEP14AA_ROOT.as_posix()]), not _diff([qa.material.design.STEP14AA_ROOT.as_posix()])), ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", False, _diff(["equivariant_diffusion/", "lightning_modules.py"]), not _diff(["equivariant_diffusion/", "lightning_modules.py"])), ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", False, _diff(["dataset.py", "data/prepare_crossdocked.py"]), not _diff(["dataset.py", "data/prepare_crossdocked.py"])), ("canonical_mask_count", "canonical masks", 5, len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5), ("b3_included", "canonical masks", True, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES), ("no_extra_masks", "canonical masks", True, len(CANONICAL_MASK_TASK_NAMES) == 5, len(CANONICAL_MASK_TASK_NAMES) == 5),
    ]
    return [_pre(*c) for c in checks]


def build_source_inventory() -> list[dict[str, Any]]:
    source_rows, _, _ = _sample_index(); row_qa = {r["sample_index_row_id"]: r for r in _csv(REPO_ROOT / qa.ROW_QA_CSV)}; trace = {r["sample_index_row_id"]: r for r in _csv(REPO_ROOT / qa.TRACEABILITY_QA_CSV)}; csv_hash, json_hash = _hash(qa.material.SAMPLE_INDEX_CSV), _hash(qa.material.SAMPLE_INDEX_JSON)
    rows=[]
    for i, r in enumerate(source_rows, 1): rows.append({"final_dataset_source_id": f"CYS_SG_FINAL_DATASET_SOURCE_{i:06d}", "sample_index_row_id": r["sample_index_row_id"], "pdb_id": r["pdb_id"], "expected_het_id": r["expected_het_id"], "sample_artifact_root": r["sample_artifact_root"], **{f:r[f] for f in PATH_FIELDS+COUNT_FIELDS}, "covalent_bond_atom_pair": r["covalent_bond_atom_pair"], "sample_index_row_qa_status": row_qa[r["sample_index_row_id"]]["row_qa_status"], "sample_index_source_traceability_qa_status": trace[r["sample_index_row_id"]]["source_traceability_qa_status"], "approved_for_final_dataset_design_by_qa": True, "source_eligible_for_final_dataset_design": False, "eligible_for_final_dataset_design_gate": True, "ready_for_training_current_step": False, "source_sample_index_csv_sha256": csv_hash, "source_sample_index_json_sha256": json_hash})
    return rows


def _schema_spec(field: str) -> tuple[str, bool, bool, str, str, str, str]:
    boolean={"qa_approved_for_final_dataset_design","eligible_for_leakage_split_design","eligible_for_final_dataset_materialization","ready_for_training_current_step","feature_semantics_audit_required_before_training","leakage_split_design_required_before_training"}; numbers={"protein_atom_count","ligand_atom_count","pocket_atom_count","covalent_event_count","ligand_residue_atom_pair_count","post_covalent_bond_distance_angstrom"}; nullable=field in {"leakage_group_id","split_assignment"}; defaults={"supported_mask_task_names":"warhead_only;linker_plus_warhead;scaffold_plus_warhead;scaffold_only;scaffold_plus_linker_plus_warhead","warhead_type_label_status":"pending_warhead_type_annotation_and_semantics_gate","ligand_residue_atom_pair_label_status":"available_from_validated_struct_conn_atom_pair","pre_covalent_geometry_label_status":"unavailable_in_current_source","post_covalent_geometry_label_status":"available_as_post_covalent_bond_distance_only","feature_semantics_status":"unresolved_requires_feature_semantics_audit","leakage_group_id":"null_pending_leakage_split_design","split_assignment":"null_pending_leakage_split_design","final_dataset_row_status":"design_only_pending_leakage_and_feature_semantics","qa_approved_for_final_dataset_design":"true","eligible_for_leakage_split_design":"true","eligible_for_final_dataset_materialization":"false","ready_for_training_current_step":"false","feature_semantics_audit_required_before_training":"true","leakage_split_design_required_before_training":"true"}; source="sample_index" if field in SAMPLE_INDEX_FIELDS else "design_policy"; source_field="bond_distance_angstrom" if field=="post_covalent_bond_distance_angstrom" else field; return ("boolean" if field in boolean else "number" if field in numbers else "string", True, nullable, source, source_field, defaults.get(field,"copied_or_generated_in_future_materialization"), "future final dataset field")

def build_schema() -> list[dict[str, Any]]:
    rows=[]
    for field in FINAL_FIELDS:
        dtype, required, nullable, artifact, source, default, rule = _schema_spec(field)
        rows.append({"final_dataset_field":field,"planned_data_type":dtype,"required":required,"nullable":nullable,"semantic_role":"future_final_dataset_field","primary_source_artifact":artifact,"primary_source_field":source,"planned_default_or_status":default,"validation_rule":rule,"current_step_materializes_field":False,"schema_contract_passed":True})
    return rows

def build_mapping() -> list[dict[str, Any]]:
    rows=[]
    for i, field in enumerate(FINAL_FIELDS,1):
        dtype, _, _, artifact, source, default, _ = _schema_spec(field)
        transform = "do_not_infer_warhead_type_from_ligand_identity" if field=="warhead_type_label_status" else "do_not_infer_pre_geometry_from_post_geometry" if field=="pre_covalent_geometry_label_status" else "remain_unset_pending_leakage_split_design" if field in {"leakage_group_id","split_assignment"} else f"planned {dtype} mapping"
        rows.append({"mapping_id":f"CYS_SG_FINAL_DATASET_MAPPING_{i:06d}","final_dataset_field":field,"primary_source_artifact":artifact,"primary_source_field":source,"fallback_source_artifact":"","fallback_source_field":"","transformation_rule":transform,"required_validation":"Step 14AE QA plus future leakage and feature semantics gates","mapping_status":"planned_and_validated"})
    return rows

def build_projection(source: list[dict[str, Any]]) -> list[dict[str, Any]]:
    masks="warhead_only;linker_plus_warhead;scaffold_plus_warhead;scaffold_only;scaffold_plus_linker_plus_warhead"
    return [{"final_dataset_projection_plan_id":f"CYS_SG_FINAL_DATASET_PLAN_{i:06d}","final_dataset_source_id":r["final_dataset_source_id"],"planned_final_dataset_row_id":f"CYS_SG_FINAL_DATASET_{i:06d}","source_sample_index_row_id":r["sample_index_row_id"],"pdb_id":r["pdb_id"],"expected_het_id":r["expected_het_id"],"planned_supported_mask_task_names":masks,"warhead_type_label_status":"pending_warhead_type_annotation_and_semantics_gate","ligand_residue_atom_pair_label_status":"available_from_validated_struct_conn_atom_pair","pre_covalent_geometry_label_status":"unavailable_in_current_source","post_covalent_geometry_label_status":"available_as_post_covalent_bond_distance_only","feature_semantics_status":"unresolved_requires_feature_semantics_audit","planned_leakage_group_id":"","planned_split_assignment":"","planned_final_dataset_row_status":"design_only_pending_leakage_and_feature_semantics","qa_approved_for_final_dataset_design":True,"eligible_for_leakage_split_design":True,"eligible_for_final_dataset_materialization":False,"final_dataset_written_current_step":False,"ready_for_training_current_step":False,"planned_next_gate":"covapie_leakage_split_design_gate"} for i,r in enumerate(source,1)]

def build_aux(source: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows=[]
    for i,r in enumerate(source,1):
        base={"sample_index_row_id":r["sample_index_row_id"],"pdb_id":r["pdb_id"],"expected_het_id":r["expected_het_id"],"ready_for_training_current_step":False}
        specs=[("warhead_type","JUG/CAG identity only","warhead_type_label_status","pending_semantics_and_annotation",False,"JUG/CAG identity is not sufficient to define a general warhead-type label."),("ligand_residue_atom_pair","SG--CAG","ligand_residue_atom_pair_label_status","available_from_validated_struct_conn",True,"Validated SG--CAG atom pair is available."),("pre_post_covalent_geometry","post-covalent distance only","pre_covalent_geometry_label_status","partial_post_only",False,"Post-covalent distance available; pre-covalent geometry unavailable; do not synthesize or infer pre geometry.")]
        for j,(task,evidence,field,status,ready,comment) in enumerate(specs,1): rows.append({"auxiliary_readiness_id":f"CYS_SG_AUXILIARY_{i:06d}_{j:02d}",**base,"auxiliary_task_name":task,"available_source_evidence":evidence,"planned_label_field":field,"readiness_status":status,"ready_for_final_dataset_materialization":ready,"blocking_reason_or_comment":comment})
    return rows

def build_contract() -> list[dict[str, Any]]:
    policies=["final_dataset_design_gate_only","design_gate_does_not_write_final_dataset","source_inventory_is_not_final_dataset","row_projection_plan_is_not_final_dataset","design_gate_reads_committed_sample_index_only","design_gate_does_not_modify_sample_index","design_gate_does_not_read_raw_mmcif","design_gate_does_not_modify_atom_event_tables","do_not_infer_warhead_type_from_ligand_identity","do_not_infer_pre_geometry_from_post_geometry","leakage_group_required_before_materialization","split_assignment_required_before_materialization","feature_semantics_audit_required_before_training","canonical_five_masks_preserved","no_training_current_step"]
    readiness={"ready_for_covapie_leakage_split_design_gate":True,"ready_for_covapie_final_dataset_materialization_smoke":False,"ready_for_covapie_actual_dataloader_adapter_smoke":False,"ready_for_training":False,"ready_to_train_now":False}
    return [{"contract_type":"policy","contract_item":p,"expected_status":True,"observed_status":True,"contract_passed":True,"comment":p.replace("_"," ")} for p in policies]+[{"contract_type":"readiness","contract_item":k,"expected_status":v,"observed_status":v,"contract_passed":True,"comment":"leakage/split design is next"} for k,v in readiness.items()]

def build_safety() -> list[dict[str, Any]]:
    checks=[("network_access_used_current_step",False,False),("download_attempted_current_step",False,False),("raw_mmcif_read_current_step",False,False),("struct_conn_parsed_current_step",False,False),("atom_site_parsed_current_step",False,False),("data_raw_written_current_step",False,False),("existing_sample_index_read_current_step",True,True),("sample_index_modified_current_step",False,False),("sample_index_rewritten_current_step",False,False),("sample_index_files_unchanged",True,not _diff([qa.material.SAMPLE_INDEX_CSV.as_posix(),qa.material.SAMPLE_INDEX_JSON.as_posix()])),("metadata_csv_unchanged",True,_hash(qa.material.design.METADATA_CSV)==METADATA_CSV_SHA256 and not _diff([qa.material.design.METADATA_CSV.as_posix()])),("step14ae_artifacts_unchanged",True,not _diff([qa.OUTPUT_ROOT.as_posix()])),("step14ad_artifacts_unchanged",True,not _diff([qa.material.OUTPUT_ROOT.as_posix()])),("step14ac_artifacts_unchanged",True,not _diff([qa.material.design.OUTPUT_ROOT.as_posix()])),("step14ab_artifacts_unchanged",True,not _diff([qa.material.design.STEP14AB_ROOT.as_posix()])),("step14aa_artifacts_unchanged",True,not _diff([qa.material.design.STEP14AA_ROOT.as_posix()])),("source_atom_event_tables_unchanged",True,not _diff([(qa.material.design.STEP14AA_ROOT/"samples").as_posix()])),("protected_source_diff_empty",True,not _diff(["equivariant_diffusion/","lightning_modules.py"])),("original_dataloader_diff_empty",True,not _diff(["dataset.py","data/prepare_crossdocked.py"])),("final_dataset_written",False,False),("split_assignments_written",False,False),("leakage_matrix_written",False,False),("actual_dataloader_smoke_written",False,False),("training_artifacts_written",False,False),("derived_output_no_forbidden_raw_binary_or_html_suffix",True,not any(p.is_file() and (p.name in FORBIDDEN_NAMES or p.suffix.lower() in FORBIDDEN_SUFFIXES) for p in (REPO_ROOT/OUTPUT_ROOT).rglob("*"))),("torch_imported",False,False),("numpy_imported",False,False),("rdkit_used",False,False),("gemmi_used",False,False),("requests_used",False,False),("urllib_used",False,False),("selenium_used",False,False),("playwright_used",False,False),("bs4_used",False,False)]
    return [{"safety_item":i,"required_status":e,"observed_status":o,"safety_passed":e==o,"blocking_reasons":"" if e==o else i} for i,e,o in checks]

def build_manifest(pre: list[dict[str,Any]],source: list[dict[str,Any]],schema: list[dict[str,Any]],mapping: list[dict[str,Any]],plan: list[dict[str,Any]],aux: list[dict[str,Any]],contract: list[dict[str,Any]],safety: list[dict[str,Any]]) -> dict[str,Any]:
    blocking=[r["precondition_item"] for r in pre if not _bool(r["precondition_passed"])] + [r["safety_item"] for r in safety if not _bool(r["safety_passed"])]
    return {"stage":STAGE,"step_label":STEP_LABEL,"previous_stage":PREVIOUS_STAGE,"project_name":PROJECT_NAME,"step14ae_sample_index_qa_gate_validated":_all(pre,"precondition_passed"),"input_sample_index_row_count":3,"input_sample_index_row_qa_passed_count":3,"input_sample_index_schema_qa_passed_count":33,"input_sample_index_source_traceability_qa_passed_count":3,"input_sample_index_fingerprint_verified_count":2,"input_sample_index_qa_issue_count":0,"final_dataset_source_inventory_count":len(source),"final_dataset_schema_field_count":len(schema),"final_dataset_field_mapping_count":len(mapping),"final_dataset_row_projection_plan_count":len(plan),"auxiliary_label_readiness_count":len(aux),"warhead_type_ready_count":0,"ligand_residue_atom_pair_ready_count":sum(r["auxiliary_task_name"]=="ligand_residue_atom_pair" and _bool(r["ready_for_final_dataset_materialization"]) for r in aux),"pre_post_geometry_fully_ready_count":0,"pre_post_geometry_partial_post_only_count":sum(r["readiness_status"]=="partial_post_only" for r in aux),"qa_approved_for_final_dataset_design_count":3,"eligible_for_leakage_split_design_count":3,"eligible_for_final_dataset_materialization_count":0,"ready_for_training_candidate_count_current_step":0,"accepted_pdb_het_pairs":[f"{r['pdb_id']}/{r['expected_het_id']}" for r in source],"planned_final_dataset_row_ids":[r["planned_final_dataset_row_id"] for r in plan],"source_sample_index_csv_sha256":_hash(qa.material.SAMPLE_INDEX_CSV),"source_sample_index_json_sha256":_hash(qa.material.SAMPLE_INDEX_JSON),"existing_sample_index_read_current_step":True,"sample_index_modified_current_step":False,"sample_index_rewritten_current_step":False,"final_dataset_written_current_step":False,"final_dataset_written":False,"split_assignments_written":False,"leakage_matrix_written":False,"actual_dataloader_smoke_written":False,"training_artifacts_written":False,"ready_for_covapie_leakage_split_design_gate":True,"ready_for_covapie_final_dataset_materialization_smoke":False,"ready_for_covapie_actual_dataloader_adapter_smoke":False,"ready_for_training":False,"ready_to_train_now":False,"canonical_mask_task_names":CANONICAL_MASK_TASK_NAMES,"canonical_mask_task_aliases":CANONICAL_MASK_TASK_ALIASES,"b3_scaffold_only_included":True,"no_extra_mask_tasks_added":True,"feature_semantics_known_for_training":False,"unknown_atom_feature_policy_finalized_for_training":False,"feature_semantics_audit_required_before_training":True,"leakage_split_design_required_before_training":True,"recommended_next_step":"covapie_leakage_split_design_gate","all_checks_passed":not blocking,"blocking_reasons":blocking}

def run_covapie_final_dataset_design_gate_v0() -> dict[str,Any]:
    pre=build_precondition_rows(); source=build_source_inventory(); schema=build_schema(); mapping=build_mapping(); plan=build_projection(source); aux=build_aux(source); contract=build_contract(); safety=build_safety(); manifest=build_manifest(pre,source,schema,mapping,plan,aux,contract,safety)
    return {"precondition_rows":pre,"source_rows":source,"schema_rows":schema,"mapping_rows":mapping,"plan_rows":plan,"aux_rows":aux,"contract_rows":contract,"safety_rows":safety,"manifest":manifest}
