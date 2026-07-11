from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Any

from covalent_ext.covapie_sample_index_design_gate import SAMPLE_INDEX_FIELDS, CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES

REPO = Path(__file__).resolve().parents[2]
STAGE = "covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0"
ROOT = Path("data/derived/covalent_small") / STAGE
PREVIOUS = "covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke_v0"
PILOT = Path("data/derived/covalent_small/covapie_sample_index_materialization_smoke_v0/sample_index.csv")
PILOT_JSON = PILOT.with_suffix(".json")
EXP = Path("data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_index_materialization_smoke_v0/expansion_batch_sample_index.csv")
EXP_JSON = EXP.with_suffix(".json")
EVIDENCE = Path("data/derived/covalent_small") / PREVIOUS
OUT = {name: ROOT / name for name in [
    "covapie_unified_assignment_merge_precondition_audit.csv", "unified_sample_index.csv", "unified_sample_index.json",
    "covapie_unified_sample_index_schema_validation_audit.csv", "covapie_final_leakage_group_assignment.csv",
    "covapie_final_leakage_group_assignment.json", "covapie_final_leakage_group_inventory.csv",
    "covapie_pairwise_group_assignment_decision_audit.csv", "covapie_unified_sample_index_merge_traceability_audit.csv",
    "covapie_unified_assignment_merge_issue_inventory.csv", "covapie_unified_assignment_merge_safety_audit.csv",
    "covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_manifest.json",
]}
SUMMARY = Path("docs/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0_summary.md")
EXPECTED = [(f"CYS_SG_SAMPLE_INDEX_{i:06d}", p, h) for i, p, h in [
    (1,"6BV6","JUG"),(2,"6BV8","JUG"),(3,"6BV5","JUG"),(4,"1AEC","E64"),(5,"1AIM","ZYA"),(6,"1AU3","PCM"),(7,"1AU4","INP"),(8,"1AYU","INA"),(9,"1AYV","IN6"),(10,"1AYW","IN3"),(11,"1B02","UFP")]]
HASHES = {PILOT:"2733991775edf5e075b461a9ba1872c7e2fe7f61f5d9614a2704b814c3f0e2c5", PILOT_JSON:"8d740458e30cc77bbaa568c615dd10f5df334cd0c46f21433c570c16391b8b38", EXP:"857a0bdb665b49efd5d079a855142fed0985106f844338401f6329aeeae368c7", EXP_JSON:"5f188c9a0ebf5840d1cca7041788a3eca2235f666ab76ab524482c997d186f1b"}
POLICY = "conservative_union_of_ligand_graph_scaffold_and_protein_accession_sequence_clusters_v1"
ASSIGNMENT_FIELDS = [
    "assignment_id", "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "source_index_stage", "ligand_graph_group_id", "ligand_scaffold_group_id",
    "protein_exact_sequence_group_id", "protein_accession_group_id",
    "protein_sequence_cluster_90_id", "protein_sequence_cluster_50_id",
    "direct_must_link_neighbor_count", "final_leakage_group_id",
    "final_leakage_group_member_count", "final_leakage_group_status",
    "assignment_policy", "final_group_assignment_passed",
    "eligible_for_split_materialization_current_step",
    "ready_for_training_current_step",
    "feature_semantics_audit_required_before_training",
    "leakage_split_design_required_before_training", "blocking_reasons",
]
TRACEABILITY_FIELDS = [
    "merge_traceability_id", "sample_index_row_id", "source_index_stage",
    "source_csv_row_found", "source_json_row_found",
    "source_csv_json_consistent", "all_33_fields_preserved",
    "unified_csv_row_found", "unified_json_row_found",
    "unified_csv_json_consistent", "final_group_assignment_row_found",
    "row_order_preserved", "artifact_paths_still_exist",
    "merge_traceability_passed", "blocking_reasons",
]
ASSIGNMENT_INTEGER_FIELDS = {
    "direct_must_link_neighbor_count", "final_leakage_group_member_count",
}
ASSIGNMENT_BOOLEAN_FIELDS = {
    "final_group_assignment_passed",
    "eligible_for_split_materialization_current_step",
    "ready_for_training_current_step",
    "feature_semantics_audit_required_before_training",
    "leakage_split_design_required_before_training",
}
TRACEABILITY_BOOLEAN_FIELDS = set(TRACEABILITY_FIELDS[3:-1])
ARTIFACT_PATH_FIELDS = [
    "protein_atom_table_path", "ligand_atom_table_path", "pocket_atom_table_path",
    "covalent_event_table_path", "ligand_residue_atom_pair_table_path",
    "sample_preparation_audit_path",
]
SAFETY_FIELDS = ["safety_item","required_status","observed_status","safety_passed","blocking_reasons"]
SAFETY_EXPECTED = {
    "network_access_used_current_step":False,
    "download_attempted_current_step":False,
    "raw_entry_files_read_current_step":False,
    "ccd_raw_files_read_current_step":False,
    "raw_files_modified":False,
    "raw_files_tracked":False,
    "raw_files_staged":False,
    "pilot_index_files_unchanged":True,
    "expansion_index_files_unchanged":True,
    "step14ao_artifacts_unchanged":True,
    "step14an_artifacts_unchanged":True,
    "step14am_artifacts_unchanged":True,
    "unified_sample_index_csv_written":True,
    "unified_sample_index_json_written":True,
    "final_group_assignment_csv_written":True,
    "final_group_assignment_json_written":True,
    "group_inventory_csv_written":True,
    "pairwise_assignment_audit_written":True,
    "merge_traceability_csv_written":True,
    "schema_validation_audit_written":True,
    "source_sample_indexes_modified":False,
    "split_assignments_written":False,
    "leakage_matrix_written":False,
    "final_dataset_written":False,
    "actual_dataloader_artifacts_written":False,
    "training_artifacts_written":False,
    "standalone_assignment_qa_gate_created":False,
    "embedded_assignment_qa_performed":True,
    "part_or_tmp_files_remaining":False,
    "forbidden_artifacts_present":False,
    "protected_source_diff_empty":True,
    "original_dataloader_diff_empty":True,
    "unexpected_staged_files_present":False,
    "torch_imported":False,
    "numpy_imported":False,
    "rdkit_used":False,
    "biopython_used":False,
    "gemmi_used":False,
    "requests_used":False,
}
BLOCKED_SAFETY_EXPECTED = {**SAFETY_EXPECTED,"embedded_assignment_qa_performed":False}
ISSUE_FIELDS = ["issue_id","issue_scope","sample_index_row_id","final_leakage_group_id","issue_severity","issue_type","issue_description","issue_status"]
PRECONDITION_FIELDS = ["precondition_item","artifact_or_check","expected_status","observed_status","precondition_passed","blocking_reasons"]
SCHEMA_AUDIT_FIELDS = ["schema_validation_id","sample_index_field","expected_data_type","csv_column_present","json_field_present_all_rows","non_null_rule_passed","data_type_validation_passed","source_field_preservation_passed","semantic_validation_passed","schema_validation_status","blocking_reasons"]
GROUP_INVENTORY_FIELDS = ["final_leakage_group_id","group_order","member_count","member_sample_index_row_ids","member_pdb_het_pairs","source_stage_composition","direct_internal_must_link_edge_count","ligand_axis_internal_edge_count","protein_axis_internal_edge_count","singleton_group","final_leakage_group_status","group_inventory_passed","blocking_reasons"]
PAIR_DECISION_FIELDS = ["source_ligand_evidence_complete","source_protein_evidence_complete","ligand_axis_must_link","protein_axis_must_link","direct_must_link_edge","direct_must_link_reason","pair_assignment_classification","pair_assignment_decision_id","left_sample_index_row_id","right_sample_index_row_id","left_pdb_id","right_pdb_id","left_ligand_comp_id","right_ligand_comp_id","source_combined_evidence_row_found","same_ligand_graph","same_murcko_scaffold","same_protein_accession","same_exact_protein_sequence","same_sequence_cluster_90","same_sequence_cluster_50","same_final_leakage_group_after_transitive_closure","transitive_only_same_group","pair_assignment_passed","blocking_reasons"]
RAW_ROOT = Path("data/raw/covalent_sources")
STEP14AN_ROOT = Path("data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_index_materialization_smoke_v0")
STEP14AM_ROOT = Path("data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0")

@dataclass
class RunActivity:
    read_paths: set[str] = field(default_factory=set)
    written_paths: set[str] = field(default_factory=set)
    network_access_used: bool = False
    download_attempted: bool = False

@dataclass(frozen=True)
class InputPaths:
    pilot_csv: Path
    pilot_json: Path
    expansion_csv: Path
    expansion_json: Path
    step14ao_manifest: Path
    step14ao_issue_inventory: Path
    ligand_evidence: Path
    protein_evidence: Path
    ligand_pairwise: Path
    protein_pairwise: Path
    combined_pairwise: Path
    ligand_group_inventory: Path
    protein_group_inventory: Path

DEFAULT_INPUT_PATHS = InputPaths(
    pilot_csv=PILOT,pilot_json=PILOT_JSON,expansion_csv=EXP,expansion_json=EXP_JSON,
    step14ao_manifest=EVIDENCE/"covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke_manifest.json",
    step14ao_issue_inventory=EVIDENCE/"covapie_independence_evidence_materialization_issue_inventory.csv",
    ligand_evidence=EVIDENCE/"covapie_ligand_graph_scaffold_evidence.csv",
    protein_evidence=EVIDENCE/"covapie_protein_sequence_accession_evidence.csv",
    ligand_pairwise=EVIDENCE/"covapie_ligand_pairwise_similarity_evidence.csv",
    protein_pairwise=EVIDENCE/"covapie_protein_pairwise_sequence_identity_evidence.csv",
    combined_pairwise=EVIDENCE/"covapie_combined_pairwise_independence_evidence.csv",
    ligand_group_inventory=EVIDENCE/"covapie_ligand_graph_scaffold_group_inventory.csv",
    protein_group_inventory=EVIDENCE/"covapie_protein_sequence_cluster_inventory.csv",
)

@dataclass
class LoadedInputs:
    pilot_csv_rows: list[dict[str,str]]
    pilot_json_rows: list[dict[str,Any]]
    expansion_csv_rows: list[dict[str,str]]
    expansion_json_rows: list[dict[str,Any]]
    step14ao_manifest: dict[str,Any]
    step14ao_issue_rows: list[dict[str,str]]
    ligand_evidence_rows: list[dict[str,str]]
    protein_evidence_rows: list[dict[str,str]]
    ligand_pairwise_rows: list[dict[str,str]]
    protein_pairwise_rows: list[dict[str,str]]
    combined_pairwise_rows: list[dict[str,str]]
    ligand_group_inventory_rows: list[dict[str,str]]
    protein_group_inventory_rows: list[dict[str,str]]
    blocking_reasons: list[str]

    @property
    def input_load_passed(self) -> bool: return not self.blocking_reasons

@dataclass
class SemanticValidationResult:
    passed: bool
    blocking_reasons: list[str]
    normalized_pilot_rows: list[dict[str,Any]]
    normalized_expansion_rows: list[dict[str,Any]]
    validated_ligand_evidence_rows: list[dict[str,Any]]
    validated_protein_evidence_rows: list[dict[str,Any]]
    validated_ligand_pairwise_rows: list[dict[str,Any]]
    validated_protein_pairwise_rows: list[dict[str,Any]]
    validated_combined_pairwise_rows: list[dict[str,Any]]

    @property
    def semantic_validation_passed(self) -> bool: return self.passed and not self.blocking_reasons

def parse_strict_bool(value: Any, logical_input: str, row_number: int, field_name: str, blockers: list[str]) -> bool | None:
    if value is True or value is False: return value
    if isinstance(value,str) and value in {"True","False","true","false"}: return value.lower()=="true"
    blockers.append(f"invalid_boolean:{logical_input}:{row_number}:{field_name}:{value}"); return None

def parse_strict_int(value: Any, logical_input: str, row_number: int, field_name: str, blockers: list[str]) -> int | None:
    if isinstance(value,bool): blockers.append(f"invalid_integer:{logical_input}:{row_number}:{field_name}:{value}"); return None
    if isinstance(value,int): return value
    if isinstance(value,str) and value and (value.isdigit() or value[0]=="-" and value[1:].isdigit()): return int(value)
    blockers.append(f"invalid_integer:{logical_input}:{row_number}:{field_name}:{value}"); return None

def parse_strict_float(value: Any, logical_input: str, row_number: int, field_name: str, blockers: list[str]) -> float | None:
    import math
    if isinstance(value,bool): blockers.append(f"invalid_float:{logical_input}:{row_number}:{field_name}:{value}"); return None
    try: parsed=float(value)
    except (TypeError,ValueError): blockers.append(f"invalid_float:{logical_input}:{row_number}:{field_name}:{value}"); return None
    if not math.isfinite(parsed): blockers.append(f"invalid_float:{logical_input}:{row_number}:{field_name}:{value}"); return None
    return parsed

def _activity_path(path: Path | str) -> str:
    resolved=rp(path).resolve()
    try: return str(resolved.relative_to(REPO.resolve()))
    except ValueError: return str(resolved)

def rp(path: Path | str) -> Path:
    path = Path(path); return path if path.is_absolute() else REPO / path
def digest(path: Path | str, activity: RunActivity | None = None) -> str:
    value=hashlib.sha256(rp(path).read_bytes()).hexdigest()
    if activity is not None: activity.read_paths.add(_activity_path(path))
    return value
def read_csv(path: Path | str, activity: RunActivity | None = None) -> list[dict[str,str]]:
    with rp(path).open(newline="",encoding="utf-8") as h: rows=list(csv.DictReader(h))
    if activity is not None: activity.read_paths.add(_activity_path(path))
    return rows
def safe_read_csv(path: Path | str, required_columns: list[str] | None = None, activity: RunActivity | None = None) -> tuple[list[dict[str,str]], list[str], list[str]]:
    try:
        with rp(path).open(newline="",encoding="utf-8") as handle:
            reader=csv.DictReader(handle); rows=list(reader); fields=list(reader.fieldnames or [])
        if activity is not None: activity.read_paths.add(_activity_path(path))
    except (OSError, csv.Error, UnicodeError): return [],[],[f"unreadable_csv:{path}"]
    missing=[c for c in required_columns or [] if c not in fields]
    return rows,fields,[f"missing_csv_column:{path}:{c}" for c in missing]
def safe_read_json(path: Path | str, activity: RunActivity | None = None) -> tuple[Any, list[str]]:
    try:
        value=json.loads(rp(path).read_text(encoding="utf-8"))
        if activity is not None: activity.read_paths.add(_activity_path(path))
        return value,[]
    except (OSError, UnicodeError, json.JSONDecodeError): return None,[f"unreadable_json:{path}"]
def safe_digest(path: Path | str, activity: RunActivity | None = None) -> tuple[str,list[str]]:
    try: return digest(path,activity),[]
    except OSError: return "",[f"unreadable_digest:{path}"]

CSV_REQUIRED = {
    "step14ao_issue_inventory":["issue_id","issue_status","issue_type","issue_description"],
    "ligand_evidence":["sample_index_row_id","pdb_id","ligand_comp_id","ligand_graph_group_id","ligand_scaffold_group_id","ligand_graph_evidence_passed","blocking_reasons"],
    "protein_evidence":["sample_index_row_id","pdb_id","ligand_comp_id","protein_exact_sequence_group_id","protein_accession_group_id","protein_sequence_cluster_90_id","protein_sequence_cluster_50_id","protein_sequence_evidence_passed","blocking_reasons"],
    "ligand_pairwise":["ligand_pairwise_evidence_id","left_sample_index_row_id","right_sample_index_row_id","same_ligand_graph","same_murcko_scaffold","ligand_tanimoto_radius2_2048","ligand_pairwise_evidence_passed","blocking_reasons"],
    "protein_pairwise":["protein_pairwise_evidence_id","left_sample_index_row_id","right_sample_index_row_id","same_protein_accession","same_exact_protein_sequence","same_sequence_cluster_90","same_sequence_cluster_50","protein_sequence_identity","protein_pairwise_evidence_passed","blocking_reasons"],
    "combined_pairwise":["pairwise_evidence_id","left_sample_index_row_id","right_sample_index_row_id","left_pdb_id","right_pdb_id","left_ligand_comp_id","right_ligand_comp_id","same_ligand_graph","same_murcko_scaffold","same_protein_accession","same_exact_protein_sequence","same_sequence_cluster_90","same_sequence_cluster_50","protein_sequence_identity","combined_pairwise_independence_evidence_classification","blocking_reasons"],
    "ligand_group_inventory":["group_id","member_count","member_sample_index_row_ids","group_inventory_passed"],
    "protein_group_inventory":["group_id","member_count","member_sample_index_row_ids","group_inventory_passed"],
}
LOGICAL_INPUT_NAMES = ["pilot_csv","pilot_json","expansion_csv","expansion_json","step14ao_manifest","step14ao_issue_inventory","ligand_evidence","protein_evidence","ligand_pairwise","protein_pairwise","combined_pairwise","ligand_group_inventory","protein_group_inventory"]

def load_inputs_safely(input_paths: InputPaths, activity: RunActivity) -> LoadedInputs:
    blockers=[]; csv_values={}
    for name in ["pilot_csv","expansion_csv",*CSV_REQUIRED]:
        path=getattr(input_paths,name); required=SAMPLE_INDEX_FIELDS if name in {"pilot_csv","expansion_csv"} else CSV_REQUIRED[name]
        rows,fields,errors=safe_read_csv(path,required,activity)
        if errors:
            for error in errors:
                column=error.rsplit(":",1)[-1] if error.startswith("missing_csv_column:") else ""
                blockers.append(f"missing_csv_column:{name}:{column}" if column else f"unreadable_csv:{name}")
        if not fields: blockers.append(f"empty_csv:{name}")
        elif name in {"pilot_csv","expansion_csv"} and fields!=SAMPLE_INDEX_FIELDS: blockers.append(f"invalid_csv_field_order:{name}")
        if not rows: blockers.append(f"header_only_csv:{name}")
        csv_values[name]=rows
    json_values={}
    for name,label in [("pilot_json","pilot_index"),("expansion_json","expansion_index")]:
        value,errors=safe_read_json(getattr(input_paths,name),activity)
        if errors: blockers.append(f"unreadable_json:{label}"); value=[]
        if not isinstance(value,list): blockers.append(f"invalid_json_root_type:{label}"); value=[]
        valid_rows=[]
        for index,row in enumerate(value,1):
            if not isinstance(row,dict): blockers.append(f"invalid_json_row_type:{label}:{index}")
            elif set(row)!=set(SAMPLE_INDEX_FIELDS): blockers.append(f"invalid_json_field_set:{label}:{index}")
            else: valid_rows.append(row)
        json_values[name]=valid_rows
    manifest,errors=safe_read_json(input_paths.step14ao_manifest,activity)
    if errors: blockers.append("unreadable_json:step14ao_manifest"); manifest={}
    if not isinstance(manifest,dict): blockers.append("invalid_json_root_type:step14ao_manifest"); manifest={}
    for field_name in ["stage","all_checks_passed","blocking_reasons","ready_for_covapie_unified_independence_group_assignment_and_sample_index_merge_smoke"]:
        if field_name not in manifest: blockers.append(f"missing_manifest_field:step14ao_manifest:{field_name}")
    for path,expected in HASHES.items():
        logical="pilot_csv" if path==PILOT else "pilot_json" if path==PILOT_JSON else "expansion_csv" if path==EXP else "expansion_json"
        actual,errors=safe_digest(getattr(input_paths,logical),activity)
        if errors: blockers.append(f"unreadable_digest:{logical}")
        elif input_paths==DEFAULT_INPUT_PATHS and actual!=expected: blockers.append(f"source_index_hash_mismatch:{logical}")
    return LoadedInputs(
        pilot_csv_rows=csv_values["pilot_csv"],pilot_json_rows=json_values["pilot_json"],
        expansion_csv_rows=csv_values["expansion_csv"],expansion_json_rows=json_values["expansion_json"],
        step14ao_manifest=manifest,step14ao_issue_rows=csv_values["step14ao_issue_inventory"],
        ligand_evidence_rows=csv_values["ligand_evidence"],protein_evidence_rows=csv_values["protein_evidence"],
        ligand_pairwise_rows=csv_values["ligand_pairwise"],protein_pairwise_rows=csv_values["protein_pairwise"],
        combined_pairwise_rows=csv_values["combined_pairwise"],ligand_group_inventory_rows=csv_values["ligand_group_inventory"],protein_group_inventory_rows=csv_values["protein_group_inventory"],
        blocking_reasons=sorted(set(blockers)),
    )

def _normalize_sample_rows(rows: list[dict[str,Any]], logical: str, blockers: list[str]) -> list[dict[str,Any]]:
    integers={"protein_atom_count","ligand_atom_count","pocket_atom_count","covalent_event_count","ligand_residue_atom_pair_count"}; booleans={"eligible_for_final_dataset_design","ready_for_training_current_step","feature_semantics_audit_required_before_training","leakage_split_design_required_before_training"}; out=[]
    for n,row in enumerate(rows,1):
        normalized={}
        for field_name in SAMPLE_INDEX_FIELDS:
            value=row.get(field_name)
            normalized[field_name]=parse_strict_int(value,logical,n,field_name,blockers) if field_name in integers else parse_strict_float(value,logical,n,field_name,blockers) if field_name=="bond_distance_angstrom" else parse_strict_bool(value,logical,n,field_name,blockers) if field_name in booleans else value if isinstance(value,str) else str(value) if value is not None else ""
        out.append(normalized)
    return out

def _validate_pair_structure(rows: list[dict[str,Any]], table: str, id_field: str, prefix: str, expected_pairs: list[tuple[str,str]], blockers: list[str]) -> dict[tuple[str,str],dict[str,Any]]:
    if len(rows)!=55: blockers.append(f"pairwise_row_count_mismatch:{table}")
    seen_pairs=Counter(); seen_ids=Counter(); result={}; expected_set=set(expected_pairs); order={sample:i for i,sample in enumerate([row[0] for row in EXPECTED])}
    for n,row in enumerate(rows,1):
        left,right=row.get("left_sample_index_row_id",""),row.get("right_sample_index_row_id",""); pair=(left,right); seen_pairs[pair]+=1; seen_ids[row.get(id_field,"")]+=1
        if pair not in expected_set: blockers.append(f"unexpected_pair:{table}:{left}:{right}")
        if left in order and right in order and order[left]>=order[right]: blockers.append(f"reversed_pair:{table}:{left}:{right}")
        if n<=len(expected_pairs) and pair!=expected_pairs[n-1]: blockers.append(f"pair_order_mismatch:{table}:{n}")
        if row.get(id_field)!=f"{prefix}_{n:06d}": blockers.append(f"pair_id_mismatch:{table}:{n}")
        result[pair]=row
    blockers.extend(f"duplicate_pair:{table}:{left}:{right}" for (left,right),count in seen_pairs.items() if count>1)
    blockers.extend(f"duplicate_pair_id:{table}:{identifier}" for identifier,count in seen_ids.items() if count>1)
    blockers.extend(f"missing_pair:{table}:{left}:{right}" for left,right in expected_pairs if (left,right) not in seen_pairs)
    return result

def _combined_classification(ligand_class: str, protein_class: str) -> str:
    protein_related=protein_class in {"same_exact_sequence","same_accession_nonidentical_sequence","same_sequence_cluster_90","same_sequence_cluster_50"}; ligand_related=ligand_class in {"same_exact_graph","different_graph_same_scaffold"}
    if protein_related and ligand_related: return "strong_same_group_evidence"
    if protein_related: return "protein_related_ligand_distinct"
    if ligand_related: return "ligand_related_protein_distinct"
    return "provisional_distinct_both_axes"

def _classification_protein_from_flags(same_exact: bool, same_accession: bool, same_cluster_90: bool, same_cluster_50: bool) -> str:
    if same_exact: return "same_exact_sequence"
    if same_accession: return "same_accession_nonidentical_sequence"
    if same_cluster_90: return "same_sequence_cluster_90"
    if same_cluster_50: return "same_sequence_cluster_50"
    return "sequence_below_50_identity"

def validate_loaded_inputs_semantically(loaded: LoadedInputs) -> SemanticValidationResult:
    blockers=[]
    pilot_csv=_normalize_sample_rows(loaded.pilot_csv_rows,"pilot_csv",blockers); pilot_json=_normalize_sample_rows(loaded.pilot_json_rows,"pilot_json",blockers); expansion_csv=_normalize_sample_rows(loaded.expansion_csv_rows,"expansion_csv",blockers); expansion_json=_normalize_sample_rows(loaded.expansion_json_rows,"expansion_json",blockers)
    if len(pilot_csv)!=3 or len(pilot_json)!=3: blockers.append("sample_index_row_count_mismatch:pilot")
    if len(expansion_csv)!=8 or len(expansion_json)!=8: blockers.append("sample_index_row_count_mismatch:expansion")
    for csv_rows,json_rows in [(pilot_csv,pilot_json),(expansion_csv,expansion_json)]:
        for n in range(min(len(csv_rows),len(json_rows))):
            sid=csv_rows[n].get("sample_index_row_id",f"row_{n+1}")
            for field_name in SAMPLE_INDEX_FIELDS:
                if csv_rows[n].get(field_name)!=json_rows[n].get(field_name): blockers.append(f"sample_index_csv_json_mismatch:{sid}:{field_name}")
    samples=pilot_csv+expansion_csv; sample_ids=[row.get("sample_index_row_id","") for row in samples]; expected_ids=[row[0] for row in EXPECTED]
    if len(samples)!=11 or sample_ids!=expected_ids: blockers.append("sample_index_order_mismatch")
    blockers.extend(f"duplicate_sample_index_row_id:{sid}" for sid,count in Counter(sample_ids).items() if count>1)
    pairs=[(row.get("pdb_id",""),row.get("ligand_comp_id","")) for row in samples]; blockers.extend(f"duplicate_pdb_ligand_pair:{pdb}/{lig}" for (pdb,lig),count in Counter(pairs).items() if count>1)
    for row in samples:
        sid=row.get("sample_index_row_id","")
        for field_name in ["protein_atom_count","ligand_atom_count","pocket_atom_count"]:
            if not isinstance(row.get(field_name),int) or isinstance(row.get(field_name),bool) or row[field_name]<=0: blockers.append(f"invalid_positive_integer:{sid}:{field_name}")
        for field_name in ["covalent_event_count","ligand_residue_atom_pair_count"]:
            if row.get(field_name)!=1: blockers.append(f"invalid_positive_integer:{sid}:{field_name}")
        if not isinstance(row.get("bond_distance_angstrom"),(int,float)) or row.get("bond_distance_angstrom",0)<=0: blockers.append(f"invalid_bond_distance:{sid}")
        if not row.get("pdb_id") or not row.get("ligand_comp_id"): blockers.append(f"sample_identity_missing:{sid}")
        if row.get("expected_het_id")!=row.get("ligand_comp_id"): blockers.append(f"expected_het_ligand_mismatch:{sid}")
        if row.get("covalent_residue_name")!="CYS" or row.get("covalent_residue_atom_name")!="SG": blockers.append(f"non_cys_sg_scope:{sid}")
        if row.get("covalent_bond_atom_pair")!=f"{row.get('covalent_residue_atom_name')}--{row.get('ligand_covalent_atom_name')}": blockers.append(f"covalent_atom_pair_mismatch:{sid}")
        if row.get("eligible_for_final_dataset_design") is not False or row.get("ready_for_training_current_step") is not False or row.get("feature_semantics_audit_required_before_training") is not True or row.get("leakage_split_design_required_before_training") is not True: blockers.append(f"sample_readiness_boundary_mismatch:{sid}")
        for field_name in ARTIFACT_PATH_FIELDS:
            if not row.get(field_name) or not rp(row[field_name]).exists(): blockers.append(f"sample_artifact_path_missing:{sid}:{field_name}")
    sample_by={row.get("sample_index_row_id"):row for row in samples}
    manifest=loaded.step14ao_manifest
    for condition,reason in [(manifest.get("stage")!=PREVIOUS,"step14ao_manifest_stage_mismatch"),(manifest.get("all_checks_passed") is not True,"step14ao_manifest_not_passed"),(manifest.get("blocking_reasons")!=[],"step14ao_manifest_has_blockers"),(manifest.get("materialization_issue_count")!=0,"step14ao_materialization_issue_count_nonzero"),(manifest.get("ready_for_covapie_unified_independence_group_assignment_and_sample_index_merge_smoke") is not True,"step14ao_not_ready_for_step14ap"),(manifest.get("ready_for_training") is not False,"step14ao_training_boundary_invalid"),(manifest.get("feature_semantics_known_for_training") is not False or manifest.get("feature_semantics_audit_required_before_training") is not True,"step14ao_feature_semantics_boundary_invalid")]:
        if condition: blockers.append(reason)
    issue=loaded.step14ao_issue_rows
    if len(issue)!=1 or issue[0].get("issue_id")!="NO_INDEPENDENCE_EVIDENCE_MATERIALIZATION_ISSUES" or issue[0].get("issue_status")!="passed" or issue[0].get("issue_type")!="no_issues" or any(row.get("issue_status")=="failed" for row in issue): blockers.append("step14ao_issue_sentinel_invalid")
    ligand=[]; lig_multi=defaultdict(list)
    for n,source in enumerate(loaded.ligand_evidence_rows,1):
        row=dict(source); sid=row.get("sample_index_row_id",""); row["ligand_graph_evidence_passed"]=parse_strict_bool(row.get("ligand_graph_evidence_passed"),"ligand_evidence",n,"ligand_graph_evidence_passed",blockers); ligand.append(row); lig_multi[sid].append(row)
    if len(ligand)!=11: blockers.append("ligand_evidence_row_count_mismatch")
    protein=[]; prot_multi=defaultdict(list)
    for n,source in enumerate(loaded.protein_evidence_rows,1):
        row=dict(source); sid=row.get("sample_index_row_id",""); row["protein_sequence_evidence_passed"]=parse_strict_bool(row.get("protein_sequence_evidence_passed"),"protein_evidence",n,"protein_sequence_evidence_passed",blockers); protein.append(row); prot_multi[sid].append(row)
    if len(protein)!=11: blockers.append("protein_evidence_row_count_mismatch")
    for sid in expected_ids:
        for namespace,multi,prefix,passed_field,group_fields in [("ligand",lig_multi,"ligand", "ligand_graph_evidence_passed",["ligand_graph_group_id","ligand_scaffold_group_id"]),("protein",prot_multi,"protein","protein_sequence_evidence_passed",["protein_exact_sequence_group_id","protein_accession_group_id","protein_sequence_cluster_90_id","protein_sequence_cluster_50_id"])]:
            found=multi.get(sid,[])
            if not found: blockers.append(f"missing_{prefix}_evidence_row:{sid}"); continue
            if len(found)>1: blockers.append(f"duplicate_{prefix}_evidence_row:{sid}"); continue
            row=found[0]; sample=sample_by.get(sid,{})
            if row.get("pdb_id")!=sample.get("pdb_id"): blockers.append(f"{prefix}_evidence_pdb_mismatch:{sid}")
            if row.get("ligand_comp_id")!=sample.get("ligand_comp_id"): blockers.append(f"{prefix}_evidence_ligand_mismatch:{sid}")
            if row.get(passed_field) is not True: blockers.append(f"{prefix}_evidence_not_passed:{sid}")
            if row.get("blocking_reasons"): blockers.append(f"{prefix}_evidence_has_blocker:{sid}")
            for field_name in group_fields:
                if not row.get(field_name): blockers.append(f"{field_name}_missing:{sid}")
    def validate_group_inventory(rows: list[dict[str,str]], evidence: list[dict[str,Any]], mapping: dict[str,str], prefix: str) -> None:
        inventory={}; evidence_groups=defaultdict(list)
        for field_name,group_type in mapping.items():
            for row in evidence:
                if row.get(field_name): evidence_groups[(group_type,row[field_name])].append(row.get("sample_index_row_id"))
        for n,row in enumerate(rows,1):
            group_type,gid=row.get("group_type",""),row.get("group_id",""); key=(group_type,gid); members=row.get("member_sample_index_row_ids","").split(";") if row.get("member_sample_index_row_ids") else []; count=parse_strict_int(row.get("member_count"),f"{prefix}_group_inventory",n,"member_count",blockers); passed=parse_strict_bool(row.get("group_inventory_passed"),f"{prefix}_group_inventory",n,"group_inventory_passed",blockers)
            if not gid or key in inventory: blockers.append(f"{prefix}_group_inventory_not_passed:{gid}")
            inventory[key]=members
            if passed is not True: blockers.append(f"{prefix}_group_inventory_not_passed:{gid}")
            if count is None or count<=0 or count!=len(members) or members!=sorted(members) or len(members)!=len(set(members)): blockers.append(f"{prefix}_group_member_count_mismatch:{gid}")
            blockers.extend(f"unknown_inventory_sample:{gid}:{sid}" for sid in members if sid not in sample_by)
        for key,members in evidence_groups.items():
            if set(inventory.get(key,[]))!=set(members): blockers.append(f"{prefix}_group_membership_mismatch:{key[1]}")
        blockers.extend(f"unexpected_{prefix}_group_inventory_group:{group_type}:{group_id}" for group_type,group_id in sorted(set(inventory)-set(evidence_groups)))
    validate_group_inventory(loaded.ligand_group_inventory_rows,ligand,{"ligand_graph_group_id":"ligand_exact_graph","ligand_scaffold_group_id":"ligand_murcko_scaffold"},"ligand")
    validate_group_inventory(loaded.protein_group_inventory_rows,protein,{"protein_exact_sequence_group_id":"protein_exact_sequence","protein_accession_group_id":"protein_accession","protein_sequence_cluster_90_id":"protein_sequence_cluster_90","protein_sequence_cluster_50_id":"protein_sequence_cluster_50"},"protein")
    expected_pairs=list(combinations(expected_ids,2))
    ligand_rows=[]
    for n,source in enumerate(loaded.ligand_pairwise_rows,1):
        row=dict(source)
        for field_name in ["same_ligand_graph","same_murcko_scaffold","ligand_pairwise_evidence_passed"]: row[field_name]=parse_strict_bool(row.get(field_name),"ligand_pairwise",n,field_name,blockers)
        row["ligand_tanimoto_radius2_2048"]=parse_strict_float(row.get("ligand_tanimoto_radius2_2048"),"ligand_pairwise",n,"ligand_tanimoto_radius2_2048",blockers); ligand_rows.append(row)
    protein_rows=[]
    for n,source in enumerate(loaded.protein_pairwise_rows,1):
        row=dict(source)
        for field_name in ["same_protein_accession","same_exact_protein_sequence","same_sequence_cluster_90","same_sequence_cluster_50","protein_pairwise_evidence_passed"]: row[field_name]=parse_strict_bool(row.get(field_name),"protein_pairwise",n,field_name,blockers)
        row["protein_sequence_identity"]=parse_strict_float(row.get("protein_sequence_identity"),"protein_pairwise",n,"protein_sequence_identity",blockers); protein_rows.append(row)
    combined_rows=[]
    for n,source in enumerate(loaded.combined_pairwise_rows,1):
        row=dict(source)
        for field_name in ["same_ligand_graph","same_murcko_scaffold","same_protein_accession","same_exact_protein_sequence","same_sequence_cluster_90","same_sequence_cluster_50"]: row[field_name]=parse_strict_bool(row.get(field_name),"combined_pairwise",n,field_name,blockers)
        row["protein_sequence_identity"]=parse_strict_float(row.get("protein_sequence_identity"),"combined_pairwise",n,"protein_sequence_identity",blockers); combined_rows.append(row)
    ligand_map=_validate_pair_structure(ligand_rows,"ligand_pairwise","ligand_pairwise_evidence_id","COVAPIE_LIGAND_PAIRWISE",expected_pairs,blockers); protein_map=_validate_pair_structure(protein_rows,"protein_pairwise","protein_pairwise_evidence_id","COVAPIE_PROTEIN_PAIRWISE",expected_pairs,blockers); combined_map=_validate_pair_structure(combined_rows,"combined_pairwise","pairwise_evidence_id","COVAPIE_COMBINED_PAIRWISE",expected_pairs,blockers)
    lig_by={sid:rows[0] for sid,rows in lig_multi.items() if len(rows)==1}; prot_by={sid:rows[0] for sid,rows in prot_multi.items() if len(rows)==1}
    classes=Counter()
    for left,right in expected_pairs:
        lr,pr,cr=ligand_map.get((left,right),{}),protein_map.get((left,right),{}),combined_map.get((left,right),{}); ls,rs=sample_by.get(left,{}),sample_by.get(right,{})
        if lr:
            expected_graph=lig_by.get(left,{}).get("ligand_graph_group_id")==lig_by.get(right,{}).get("ligand_graph_group_id"); expected_scaffold=lig_by.get(left,{}).get("ligand_scaffold_group_id")==lig_by.get(right,{}).get("ligand_scaffold_group_id")
            if lr.get("same_ligand_graph")!=expected_graph: blockers.append(f"ligand_pair_graph_flag_mismatch:{left}:{right}")
            if lr.get("same_murcko_scaffold")!=expected_scaffold: blockers.append(f"ligand_pair_scaffold_flag_mismatch:{left}:{right}")
            if lr.get("ligand_tanimoto_radius2_2048") is None or not 0<=lr["ligand_tanimoto_radius2_2048"]<=1: blockers.append(f"invalid_ligand_similarity:{left}:{right}")
            if lr.get("ligand_pairwise_evidence_passed") is not True: blockers.append(f"ligand_pair_not_passed:{left}:{right}")
            if lr.get("blocking_reasons"): blockers.append(f"ligand_pair_has_blocker:{left}:{right}")
        if pr:
            expected_flags={"same_protein_accession":"protein_accession_group_id","same_exact_protein_sequence":"protein_exact_sequence_group_id","same_sequence_cluster_90":"protein_sequence_cluster_90_id","same_sequence_cluster_50":"protein_sequence_cluster_50_id"}
            labels={"same_protein_accession":"accession","same_exact_protein_sequence":"exact","same_sequence_cluster_90":"cluster90","same_sequence_cluster_50":"cluster50"}
            for field_name,group_field in expected_flags.items():
                expected_value=prot_by.get(left,{}).get(group_field)==prot_by.get(right,{}).get(group_field)
                if pr.get(field_name)!=expected_value: blockers.append(f"protein_pair_{labels[field_name]}_flag_mismatch:{left}:{right}")
            if pr.get("same_exact_protein_sequence") and not pr.get("same_sequence_cluster_90") or pr.get("same_sequence_cluster_90") and not pr.get("same_sequence_cluster_50"): blockers.append(f"protein_cluster_hierarchy_violation:{left}:{right}")
            if pr.get("protein_sequence_identity") is None or not 0<=pr["protein_sequence_identity"]<=1: blockers.append(f"invalid_protein_sequence_identity:{left}:{right}")
            if pr.get("protein_pairwise_evidence_passed") is not True: blockers.append(f"protein_pair_not_passed:{left}:{right}")
            if pr.get("blocking_reasons"): blockers.append(f"protein_pair_has_blocker:{left}:{right}")
        if cr and lr and pr:
            if cr.get("left_pdb_id")!=ls.get("pdb_id") or cr.get("right_pdb_id")!=rs.get("pdb_id"): blockers.append(f"combined_pdb_mismatch:{left}:{right}")
            if cr.get("left_ligand_comp_id")!=ls.get("ligand_comp_id") or cr.get("right_ligand_comp_id")!=rs.get("ligand_comp_id"): blockers.append(f"combined_ligand_mismatch:{left}:{right}")
            for field_name in ["same_ligand_graph","same_murcko_scaffold"]:
                if cr.get(field_name)!=lr.get(field_name): blockers.append(f"combined_ligand_flag_mismatch:{left}:{right}:{field_name}")
            for field_name in ["same_protein_accession","same_exact_protein_sequence","same_sequence_cluster_90","same_sequence_cluster_50"]:
                if cr.get(field_name)!=pr.get(field_name): blockers.append(f"combined_protein_flag_mismatch:{left}:{right}:{field_name}")
            if cr.get("protein_sequence_identity") is None or pr.get("protein_sequence_identity") is None or abs(cr["protein_sequence_identity"]-pr["protein_sequence_identity"])>1e-12: blockers.append(f"combined_identity_mismatch:{left}:{right}")
            if cr.get("blocking_reasons"): blockers.append(f"combined_pair_has_blocker:{left}:{right}")
            ligand_class="same_exact_graph" if lr.get("same_ligand_graph") else "different_graph_same_scaffold" if lr.get("same_murcko_scaffold") else "different_scaffold"
            protein_class=_classification_protein_from_flags(bool(pr.get("same_exact_protein_sequence")),bool(pr.get("same_protein_accession")),bool(pr.get("same_sequence_cluster_90")),bool(pr.get("same_sequence_cluster_50")))
            recomputed=_combined_classification(ligand_class,protein_class); stored=cr.get("combined_pairwise_independence_evidence_classification",""); classes[stored]+=1
            if stored not in {"strong_same_group_evidence","protein_related_ligand_distinct","ligand_related_protein_distinct","provisional_distinct_both_axes","evidence_incomplete"}: blockers.append(f"unknown_combined_classification:{left}:{right}:{stored}")
            if stored=="evidence_incomplete": blockers.append(f"evidence_incomplete:{left}:{right}")
            if stored!=recomputed: blockers.append(f"combined_classification_mismatch:{left}:{right}")
    if classes!={"strong_same_group_evidence":3,"protein_related_ligand_distinct":10,"provisional_distinct_both_axes":42}: blockers.append("combined_classification_count_mismatch")
    blockers=sorted(set(blockers))
    return SemanticValidationResult(not blockers,blockers,pilot_csv,expansion_csv,ligand,protein,ligand_rows,protein_rows,combined_rows)
def strict_bool(value: Any) -> bool:
    if value is True or value is False: return value
    if isinstance(value,str) and value in {"True","False","true","false"}: return value.lower()=="true"
    raise ValueError("invalid_boolean")
def normalize_assignment_csv_row(row: dict[str,Any]) -> dict[str,Any]:
    return {
        field: int(row[field]) if field in ASSIGNMENT_INTEGER_FIELDS
        else strict_bool(row[field]) if field in ASSIGNMENT_BOOLEAN_FIELDS
        else row[field]
        for field in ASSIGNMENT_FIELDS
    }
def validate_written_assignment(expected_validated_assignment_rows: list[dict[str,Any]], csv_path: Path | str, json_path: Path | str, activity: RunActivity | None = None) -> dict[str,Any]:
    reasons=[]
    try:
        csv_rows=read_csv(csv_path,activity)
        csv_typed=[normalize_assignment_csv_row(row) for row in csv_rows]
    except (OSError,csv.Error,UnicodeError,KeyError,TypeError,ValueError):
        csv_rows=[]; csv_typed=[]; reasons.append("assignment_csv_unreadable_or_invalid")
    try:
        json_rows=json.loads(rp(json_path).read_text(encoding="utf-8"))
        if activity is not None: activity.read_paths.add(_activity_path(json_path))
        if not isinstance(json_rows,list): raise ValueError("assignment_json_not_list")
    except (OSError,UnicodeError,json.JSONDecodeError,ValueError):
        json_rows=[]; reasons.append("assignment_json_unreadable_or_invalid")
    csv_count=len(csv_rows)==11; json_count=len(json_rows)==11
    csv_fields=bool(csv_rows) and list(csv_rows[0])==ASSIGNMENT_FIELDS and all(list(row)==ASSIGNMENT_FIELDS for row in csv_rows)
    json_fields=len(json_rows)==11 and all(isinstance(row,dict) and set(row)==set(ASSIGNMENT_FIELDS) for row in json_rows)
    json_types=json_fields and all(
        all(isinstance(row[field],int) and not isinstance(row[field],bool) for field in ASSIGNMENT_INTEGER_FIELDS)
        and all(isinstance(row[field],bool) for field in ASSIGNMENT_BOOLEAN_FIELDS)
        and all(isinstance(row[field],str) for field in set(ASSIGNMENT_FIELDS)-ASSIGNMENT_INTEGER_FIELDS-ASSIGNMENT_BOOLEAN_FIELDS)
        for row in json_rows
    )
    expected_ids=[f"COVAPIE_ASSIGNMENT_{i:06d}" for i in range(1,12)]
    expected_samples=[row[0] for row in EXPECTED]
    row_order=csv_count and json_count and [row.get("assignment_id") for row in csv_rows]==expected_ids and [row.get("assignment_id") for row in json_rows]==expected_ids and [row.get("sample_index_row_id") for row in csv_rows]==expected_samples and [row.get("sample_index_row_id") for row in json_rows]==expected_samples
    consistent=csv_count and json_count and csv_fields and json_fields and json_types and csv_typed==json_rows
    preserved=consistent and csv_typed==expected_validated_assignment_rows and all(row.get("final_group_assignment_passed") is True for row in json_rows)
    checks={
        "assignment_csv_row_count_passed":csv_count,
        "assignment_json_row_count_passed":json_count,
        "assignment_csv_field_order_passed":csv_fields,
        "assignment_json_field_set_passed":json_fields and json_types,
        "assignment_csv_json_consistent":consistent,
        "assignment_source_preservation_passed":preserved,
        "assignment_row_order_passed":row_order,
    }
    reasons.extend(name for name,value in checks.items() if not value)
    checks["assignment_write_validation_passed"]=all(checks.values())
    checks.update({"disk_assignment_csv_rows":csv_rows,"disk_assignment_csv_typed_rows":csv_typed,"disk_assignment_json_rows":json_rows,"blocking_reasons":";".join(sorted(set(reasons)))})
    return checks

def _multi_map(rows: list[dict[str,Any]]) -> dict[str,list[tuple[int,dict[str,Any]]]]:
    result=defaultdict(list)
    for index,row in enumerate(rows): result[row.get("sample_index_row_id","")].append((index,row))
    return result

def build_merge_traceability_rows(source_csv_rows: list[dict[str,Any]], source_json_rows: list[dict[str,Any]], disk_unified_csv_rows: list[dict[str,Any]], disk_unified_json_rows: list[dict[str,Any]], disk_assignment_csv_rows: list[dict[str,Any]], disk_assignment_json_rows: list[dict[str,Any]]) -> list[dict[str,Any]]:
    try: source_csv_typed=[typed(row) for row in source_csv_rows]
    except (TypeError,ValueError): source_csv_typed=[]
    maps=[_multi_map(rows) for rows in [source_csv_typed,source_json_rows,disk_unified_csv_rows,disk_unified_json_rows,disk_assignment_csv_rows,disk_assignment_json_rows]]
    out=[]
    for n,(sid,_,_) in enumerate(EXPECTED,1):
        source_csv,source_json,unified_csv,unified_json,assignment_csv,assignment_json=[mapping.get(sid,[]) for mapping in maps]
        reasons=[]
        def exactly_one(found:list[Any], missing:str, duplicate:str)->bool:
            if not found: reasons.append(f"{missing}:{sid}")
            elif len(found)>1: reasons.append(f"{duplicate}:{sid}")
            return len(found)==1
        source_csv_found=exactly_one(source_csv,"source_csv_row_missing","source_csv_row_duplicate")
        source_json_found=exactly_one(source_json,"source_json_row_missing","source_json_row_duplicate")
        unified_csv_found=exactly_one(unified_csv,"unified_csv_row_missing","unified_csv_row_duplicate")
        unified_json_found=exactly_one(unified_json,"unified_json_row_missing","unified_json_row_duplicate")
        assignment_csv_found=exactly_one(assignment_csv,"assignment_csv_row_missing","assignment_csv_row_duplicate")
        assignment_json_found=exactly_one(assignment_json,"assignment_json_row_missing","assignment_json_row_duplicate")
        source_consistent=source_csv_found and source_json_found and source_csv[0][1]==source_json[0][1]
        if not source_consistent: reasons.append(f"source_csv_json_mismatch:{sid}")
        unified_consistent=unified_csv_found and unified_json_found and unified_csv[0][1]==unified_json[0][1]
        if not unified_consistent: reasons.append(f"unified_csv_json_mismatch:{sid}")
        preserved=source_consistent and unified_consistent and source_csv[0][1]==unified_csv[0][1]
        if not preserved: reasons.append(f"canonical_fields_not_preserved:{sid}")
        assignment_consistent=assignment_csv_found and assignment_json_found and assignment_csv[0][1]==assignment_json[0][1] and assignment_csv[0][1].get("sample_index_row_id")==sid
        if not assignment_consistent: reasons.append(f"assignment_csv_json_mismatch:{sid}")
        ordered=all(len(found)==1 and found[0][0]==n-1 for found in [source_csv,source_json,unified_csv,unified_json,assignment_csv,assignment_json])
        if not ordered: reasons.append(f"row_order_mismatch:{sid}")
        artifact_source=unified_json[0][1] if unified_json_found else {}
        missing_paths=[field for field in ARTIFACT_PATH_FIELDS if not artifact_source.get(field) or not rp(artifact_source.get(field,"")).exists()]
        reasons.extend(f"artifact_path_missing:{sid}:{field}" for field in missing_paths)
        row={"merge_traceability_id":f"COVAPIE_MERGE_TRACE_{n:06d}","sample_index_row_id":sid,"source_index_stage":"pilot" if n<=3 else "expansion","source_csv_row_found":source_csv_found,"source_json_row_found":source_json_found,"source_csv_json_consistent":source_consistent,"all_33_fields_preserved":preserved,"unified_csv_row_found":unified_csv_found,"unified_json_row_found":unified_json_found,"unified_csv_json_consistent":unified_consistent,"final_group_assignment_row_found":assignment_consistent,"row_order_preserved":ordered,"artifact_paths_still_exist":not missing_paths,"merge_traceability_passed":not reasons,"blocking_reasons":";".join(sorted(set(reasons)))}
        out.append(row)
    return out

def normalize_traceability_csv_row(row: dict[str,Any]) -> dict[str,Any]:
    return {field:strict_bool(row[field]) if field in TRACEABILITY_BOOLEAN_FIELDS else row[field] for field in TRACEABILITY_FIELDS}
def validate_written_traceability(expected_trace_rows: list[dict[str,Any]], trace_path: Path | str, activity: RunActivity | None = None) -> dict[str,Any]:
    reasons=[]
    try:
        rows=read_csv(trace_path,activity); typed_rows=[normalize_traceability_csv_row(row) for row in rows]
    except (OSError,csv.Error,UnicodeError,KeyError,TypeError,ValueError):
        rows=[]; typed_rows=[]; reasons.append("traceability_csv_unreadable_or_invalid")
    count=len(rows)==11
    fields=bool(rows) and list(rows[0])==TRACEABILITY_FIELDS and all(list(row)==TRACEABILITY_FIELDS for row in rows)
    ids=[row.get("merge_traceability_id") for row in rows]==[f"COVAPIE_MERGE_TRACE_{i:06d}" for i in range(1,12)]
    samples=[row.get("sample_index_row_id") for row in rows]==[row[0] for row in EXPECTED]
    preserved=count and fields and ids and samples and typed_rows==expected_trace_rows
    checks={"traceability_row_count_passed":count,"traceability_field_order_passed":fields,"traceability_id_order_passed":ids,"traceability_sample_order_passed":samples,"traceability_source_preservation_passed":preserved}
    reasons.extend(name for name,value in checks.items() if not value)
    checks["traceability_written_validation_passed"]=all(checks.values())
    checks.update({"disk_traceability_rows":rows,"disk_traceability_typed_rows":typed_rows,"blocking_reasons":";".join(sorted(set(reasons)))})
    return checks

def safe_git_stdout(args: list[str]) -> tuple[str,bool]:
    result=subprocess.run(["git",*args],cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    return result.stdout.strip(),result.returncode==0

def _git_paths_clean(paths: list[Path | str]) -> bool:
    names=[str(path) for path in paths]
    working,working_ok=safe_git_stdout(["diff","--name-only","--",*names])
    staged,staged_ok=safe_git_stdout(["diff","--cached","--name-only","--",*names])
    return working_ok and staged_ok and not working and not staged

def _scan_files(roots: list[Path | str]) -> list[Path]:
    files=[]
    for root in roots:
        path=rp(root)
        if path.is_file(): files.append(path)
        elif path.is_dir(): files.extend(item for item in path.rglob("*") if item.is_file())
    return files

def _is_under(path: Path | str, root: Path | str) -> bool:
    try: rp(path).resolve().relative_to(rp(root).resolve()); return True
    except ValueError: return False

def build_safety_observations(*, read_paths: set[str], written_paths: set[str], embedded_assignment_qa_passed: bool, embedded_schema_qa_passed: bool, embedded_traceability_qa_passed: bool, network_access_used: bool = False, download_attempted: bool = False, scan_roots: list[Path | str] | None = None, output_paths: dict[str,Path | str] | None = None, module_path: Path | str | None = None) -> dict[str,bool]:
    scan_files=_scan_files(scan_roots or [ROOT,Path(__file__),Path("scripts/check_covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0.py"),SUMMARY,Path("tests/test_covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0.py")])
    output_paths=output_paths or {
        "unified_sample_index_csv_written":OUT["unified_sample_index.csv"],
        "unified_sample_index_json_written":OUT["unified_sample_index.json"],
        "final_group_assignment_csv_written":OUT["covapie_final_leakage_group_assignment.csv"],
        "final_group_assignment_json_written":OUT["covapie_final_leakage_group_assignment.json"],
        "group_inventory_csv_written":OUT["covapie_final_leakage_group_inventory.csv"],
        "pairwise_assignment_audit_written":OUT["covapie_pairwise_group_assignment_decision_audit.csv"],
        "merge_traceability_csv_written":OUT["covapie_unified_sample_index_merge_traceability_audit.csv"],
        "schema_validation_audit_written":OUT["covapie_unified_sample_index_schema_validation_audit.csv"],
    }
    output_exists={key:rp(path).is_file() and rp(path).stat().st_size>0 for key,path in output_paths.items()}
    raw_tracked,raw_tracked_ok=safe_git_stdout(["ls-files","--",str(RAW_ROOT)])
    raw_staged,raw_staged_ok=safe_git_stdout(["diff","--cached","--name-only","--",str(RAW_ROOT)])
    raw_working,raw_working_ok=safe_git_stdout(["diff","--name-only","--",str(RAW_ROOT)])
    staged_all,staged_all_ok=safe_git_stdout(["diff","--cached","--name-only"])
    pilot_clean=_git_paths_clean([PILOT,PILOT_JSON])
    expansion_clean=_git_paths_clean([EXP,EXP_JSON])
    try:
        pilot_hashes=all(digest(path)==value for path,value in HASHES.items() if path in {PILOT,PILOT_JSON})
        expansion_hashes=all(digest(path)==value for path,value in HASHES.items() if path in {EXP,EXP_JSON})
    except OSError:
        pilot_hashes=False; expansion_hashes=False
    pilot_unchanged=pilot_hashes and pilot_clean; expansion_unchanged=expansion_hashes and expansion_clean
    lower_names=[path.name.lower() for path in scan_files]
    part_tmp=any(path.suffix.lower() in {".tmp",".part"} for path in scan_files)
    forbidden_suffixes={".pt",".ckpt",".pth",".pkl",".npz",".lmdb",".cif",".pdb",".mmcif",".sdf",".mol2",".gz",".html",".tar",".zip",".tgz"}
    forbidden=any(path.suffix.lower() in forbidden_suffixes for path in scan_files)
    split_written=any("split_assignment" in name or "split_assignments" in name or name in {"train.csv","validation.csv","test.csv"} for name in lower_names)
    leakage_written=any("leakage_matrix" in name or "pairwise_leakage_matrix" in name for name in lower_names)
    final_written=any("final_dataset" in name or "dataset_manifest" in name for name in lower_names)
    dataloader_written=any("dataloader" in name or path.suffix.lower() in {".pt",".npz"} or "tensor_cache" in name for path,name in zip(scan_files,lower_names))
    training_written=any(path.suffix.lower() in {".ckpt",".pth"} or any(token in name for token in ["training_log","optimizer_state","scheduler_state"]) for path,name in zip(scan_files,lower_names))
    standalone_paths=[Path("data/derived/covalent_small/covapie_unified_independence_group_assignment_qa_gate_v0"),Path("src/covalent_ext/covapie_unified_independence_group_assignment_qa_gate.py"),Path("scripts/check_covapie_unified_independence_group_assignment_qa_gate_v0.py"),Path("tests/test_covapie_unified_independence_group_assignment_qa_gate_v0.py")]
    imports=set()
    try:
        tree=ast.parse(rp(module_path or Path(__file__)).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node,ast.Import): imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module: imports.add(node.module.split(".")[0])
    except (OSError,UnicodeError,SyntaxError):
        imports={"torch","numpy","rdkit","Bio","gemmi","requests"}
    raw_reads=[path for path in read_paths if _is_under(path,RAW_ROOT)]
    ccd_reads=[path for path in raw_reads if _is_under(path,RAW_ROOT/"ccd")]
    raw_writes=[path for path in written_paths if _is_under(path,RAW_ROOT)]
    observations={
        "network_access_used_current_step":network_access_used,
        "download_attempted_current_step":download_attempted,
        "raw_entry_files_read_current_step":bool([path for path in raw_reads if path not in ccd_reads]),
        "ccd_raw_files_read_current_step":bool(ccd_reads),
        "raw_files_modified":bool(raw_writes) or not raw_working_ok or bool(raw_working) or not raw_staged_ok or bool(raw_staged),
        "raw_files_tracked":not raw_tracked_ok or bool(raw_tracked),
        "raw_files_staged":not raw_staged_ok or bool(raw_staged),
        "pilot_index_files_unchanged":pilot_unchanged,
        "expansion_index_files_unchanged":expansion_unchanged,
        "step14ao_artifacts_unchanged":_git_paths_clean([EVIDENCE]),
        "step14an_artifacts_unchanged":_git_paths_clean([STEP14AN_ROOT]),
        "step14am_artifacts_unchanged":_git_paths_clean([STEP14AM_ROOT]),
        **output_exists,
        "source_sample_indexes_modified":not (pilot_unchanged and expansion_unchanged),
        "split_assignments_written":split_written,
        "leakage_matrix_written":leakage_written,
        "final_dataset_written":final_written,
        "actual_dataloader_artifacts_written":dataloader_written,
        "training_artifacts_written":training_written,
        "standalone_assignment_qa_gate_created":any(rp(path).exists() for path in standalone_paths),
        "embedded_assignment_qa_performed":embedded_assignment_qa_passed and embedded_schema_qa_passed and embedded_traceability_qa_passed,
        "part_or_tmp_files_remaining":part_tmp,
        "forbidden_artifacts_present":forbidden,
        "protected_source_diff_empty":_git_paths_clean(["equivariant_diffusion/","lightning_modules.py"]),
        "original_dataloader_diff_empty":_git_paths_clean(["dataset.py","data/prepare_crossdocked.py"]),
        "unexpected_staged_files_present":not staged_all_ok or bool(staged_all),
        "torch_imported":"torch" in imports,
        "numpy_imported":"numpy" in imports,
        "rdkit_used":"rdkit" in imports,
        "biopython_used":"Bio" in imports,
        "gemmi_used":"gemmi" in imports,
        "requests_used":"requests" in imports,
    }
    return observations

def build_safety_rows(observations: dict[str,bool], expected: dict[str,bool] | None = None) -> list[dict[str,Any]]:
    expected=expected or SAFETY_EXPECTED
    if set(observations)!=set(expected): raise ValueError("safety_observation_contract_mismatch")
    rows=[]
    for item,required in expected.items():
        observed=observations[item]; passed=observed==required
        rows.append({"safety_item":item,"required_status":required,"observed_status":observed,"safety_passed":passed,"blocking_reasons":"" if passed else f"safety_mismatch:{item}:expected={str(required).lower()}:observed={str(observed).lower()}"})
    return rows

def build_issue_rows(blocking_reasons: list[str]) -> tuple[list[dict[str,Any]],list[str]]:
    blockers=sorted(set(reason for reason in blocking_reasons if reason))
    if not blockers:
        return [{"issue_id":"NO_UNIFIED_ASSIGNMENT_OR_SAMPLE_INDEX_MERGE_ISSUES","issue_scope":"unified_11_sample_assignment_merge_v0","sample_index_row_id":"","final_leakage_group_id":"","issue_severity":"none","issue_type":"no_issues","issue_description":"No unified independence-group assignment or sample-index merge issues detected.","issue_status":"passed"}],[]
    return [{"issue_id":f"COVAPIE_ASSIGNMENT_ISSUE_{i:06d}","issue_scope":"assignment","sample_index_row_id":"","final_leakage_group_id":"","issue_severity":"blocking","issue_type":"validation","issue_description":reason,"issue_status":"failed"} for i,reason in enumerate(blockers,1)],blockers
def validate_written_unified(source: list[dict[str,Any]], activity: RunActivity | None = None) -> tuple[list[dict[str,Any]],list[dict[str,Any]],bool]:
    csv_rows=read_csv(OUT["unified_sample_index.csv"],activity); json_rows=json.loads(rp(OUT["unified_sample_index.json"]).read_text(encoding="utf-8"))
    if activity is not None: activity.read_paths.add(_activity_path(OUT["unified_sample_index.json"]))
    try: csv_typed=[typed(r) for r in csv_rows]
    except (ValueError, TypeError): csv_typed=[]
    valid=len(csv_rows)==len(json_rows)==len(source)==11 and bool(csv_rows) and list(csv_rows[0])==SAMPLE_INDEX_FIELDS and all(isinstance(r,dict) and set(r)==set(SAMPLE_INDEX_FIELDS) for r in json_rows) and csv_typed==json_rows==source
    return csv_typed,json_rows,valid
def schema_rows_from_disk(source: list[dict[str,Any]], csv_rows: list[dict[str,str]], json_rows: list[dict[str,Any]]) -> list[dict[str,Any]]:
    ints={"protein_atom_count","ligand_atom_count","pocket_atom_count","covalent_event_count","ligand_residue_atom_pair_count"}; bools={"eligible_for_final_dataset_design","ready_for_training_current_step","feature_semantics_audit_required_before_training","leakage_split_design_required_before_training"}; out=[]
    for n,f in enumerate(SAMPLE_INDEX_FIELDS,1):
        vals=[r.get(f) for r in csv_rows]; jvals=[r.get(f) for r in json_rows]; column=bool(csv_rows) and f in csv_rows[0]; jsonpresent=len(json_rows)==11 and all(f in r for r in json_rows); nonnull=all(v is not None for v in vals+jvals)
        try:
            typeok=all((int(v) or True) for v in vals) and all(isinstance(v,int) and not isinstance(v,bool) for v in jvals) if f in ints else all((float(v) or True) for v in vals) and all(isinstance(v,(int,float)) and not isinstance(v,bool) for v in jvals) if f=="bond_distance_angstrom" else all(str(v).lower() in {"true","false"} for v in vals) and all(isinstance(v,bool) for v in jvals) if f in bools else all(isinstance(v,str) for v in jvals)
        except (ValueError,TypeError): typeok=False
        preserve=[str(v).lower() if f in bools else str(v) for v in vals]==[("true" if r[f] else "false") if f in bools else str(r[f]) for r in source] and jvals==[r[f] for r in source]
        semantic=all(r["covalent_residue_name"]=="CYS" and r["covalent_residue_atom_name"]=="SG" and r["covalent_event_count"]==1 and r["ligand_residue_atom_pair_count"]==1 and r["ready_for_training_current_step"] is False and r["feature_semantics_audit_required_before_training"] is True and r["leakage_split_design_required_before_training"] is True for r in json_rows)
        passed=column and jsonpresent and nonnull and typeok and preserve and semantic; out.append({"schema_validation_id":f"COVAPIE_SCHEMA_{n:06d}","sample_index_field":f,"expected_data_type":"integer" if f in ints else "boolean" if f in bools else "number" if f=="bond_distance_angstrom" else "string","csv_column_present":column,"json_field_present_all_rows":jsonpresent,"non_null_rule_passed":nonnull,"data_type_validation_passed":typeok,"source_field_preservation_passed":preserve,"semantic_validation_passed":semantic,"schema_validation_status":"passed" if passed else "failed","blocking_reasons":"" if passed else f"schema_validation_failed:{f}"})
    return out
def atomic(path: Path, text: str, activity: RunActivity | None = None) -> None:
    target=rp(path); target.parent.mkdir(parents=True,exist_ok=True); tmp=target.with_name(target.name+".tmp")
    try:
        tmp.write_text(text,encoding="utf-8"); os.replace(tmp,target)
        if activity is not None: activity.written_paths.add(_activity_path(path))
    finally:
        if tmp.exists(): tmp.unlink()
def write_csv(path: Path, rows: list[dict[str,Any]], fields: list[str], activity: RunActivity | None = None) -> None:
    import io
    h=io.StringIO(); w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); [w.writerow({f:r.get(f,"") for f in fields}) for r in rows]; atomic(path,h.getvalue(),activity)
def write_json(path: Path, value: Any, activity: RunActivity | None = None) -> None: atomic(path,json.dumps(value,indent=2,sort_keys=True)+"\n",activity)
def truth(v: Any) -> bool: return v is True or str(v).lower()=="true"
def typed(row: dict[str,str]) -> dict[str,Any]:
    ints={"protein_atom_count","ligand_atom_count","pocket_atom_count","covalent_event_count","ligand_residue_atom_pair_count"}; bools={"eligible_for_final_dataset_design","ready_for_training_current_step","feature_semantics_audit_required_before_training","leakage_split_design_required_before_training"}
    return {k:(int(v) if k in ints else float(v) if k=="bond_distance_angstrom" else truth(v) if k in bools else v) for k,v in row.items()}
class UF:
    def __init__(self, ids:list[str]): self.p={x:x for x in ids}
    def find(self,x:str)->str:
        while self.p[x]!=x: self.p[x]=self.p[self.p[x]]; x=self.p[x]
        return x
    def union(self,a:str,b:str)->None:
        a,b=self.find(a),self.find(b)
        if a!=b:self.p[max(a,b)]=min(a,b)
def decide_pair(row:dict[str,str], ligand_complete: bool = True, protein_complete: bool = True)->dict[str,Any]:
    ligand=truth(row["same_ligand_graph"]) or truth(row["same_murcko_scaffold"])
    protein=any(truth(row[k]) for k in ["same_protein_accession","same_exact_protein_sequence","same_sequence_cluster_90","same_sequence_cluster_50"])
    complete=ligand_complete and protein_complete and row["combined_pairwise_independence_evidence_classification"]!="evidence_incomplete" and not row.get("blocking_reasons","")
    edge=complete and (ligand or protein)
    classification="blocked_evidence_incomplete" if not complete else "must_link_both_axes" if ligand and protein else "must_link_ligand_axis_only" if ligand else "must_link_protein_axis_only" if protein else "no_direct_must_link_provisional_distinct"
    reasons=[]
    for key,name in [("same_ligand_graph","ligand_graph"),("same_murcko_scaffold","ligand_scaffold"),("same_protein_accession","protein_accession"),("same_exact_protein_sequence","protein_exact_sequence"),("same_sequence_cluster_90","protein_sequence_cluster_90"),("same_sequence_cluster_50","protein_sequence_cluster_50")]:
        if truth(row.get(key,"False")): reasons.append(name)
    return {"source_ligand_evidence_complete":ligand_complete,"source_protein_evidence_complete":protein_complete,"ligand_axis_must_link":ligand,"protein_axis_must_link":protein,"direct_must_link_edge":edge,"direct_must_link_reason":";".join(sorted(reasons)) if edge else "none","pair_assignment_classification":classification}
def groups(ids:list[str], decisions:list[dict[str,Any]])->dict[str,str]:
    uf=UF(ids)
    for r in decisions:
        if r["direct_must_link_edge"]: uf.union(r["left_sample_index_row_id"],r["right_sample_index_row_id"])
    buckets=defaultdict(list)
    for i in ids:buckets[uf.find(i)].append(i)
    comps=sorted((sorted(v) for v in buckets.values()),key=lambda v:v[0])
    return {sid:f"COVAPIE_LEAKAGE_GROUP_{n:06d}" for n,comp in enumerate(comps,1) for sid in comp}

def build_candidate_assignment_rows(unified_rows:list[dict[str,Any]], decisions:list[dict[str,Any]], ligand_rows:list[dict[str,Any]], protein_rows:list[dict[str,Any]], final_assignment:dict[str,str], group_members:dict[str,list[str]])->list[dict[str,Any]]:
    by_lig={r.get("sample_index_row_id"):r for r in ligand_rows if r.get("sample_index_row_id")}
    by_prot={r.get("sample_index_row_id"):r for r in protein_rows if r.get("sample_index_row_id")}
    out=[]
    for n,row in enumerate(unified_rows,1):
        sid=row.get("sample_index_row_id",""); g=final_assignment.get(sid,""); members=sorted(group_members.get(g,[])); lr=by_lig.get(sid,{}); pr=by_prot.get(sid,{})
        out.append({"assignment_id":f"COVAPIE_ASSIGNMENT_{n:06d}","sample_index_row_id":sid,"pdb_id":row.get("pdb_id",""),"ligand_comp_id":row.get("ligand_comp_id",""),"source_index_stage":"pilot" if n<=3 else "expansion","ligand_graph_group_id":lr.get("ligand_graph_group_id",""),"ligand_scaffold_group_id":lr.get("ligand_scaffold_group_id",""),"protein_exact_sequence_group_id":pr.get("protein_exact_sequence_group_id",""),"protein_accession_group_id":pr.get("protein_accession_group_id",""),"protein_sequence_cluster_90_id":pr.get("protein_sequence_cluster_90_id",""),"protein_sequence_cluster_50_id":pr.get("protein_sequence_cluster_50_id",""),"direct_must_link_neighbor_count":sum(bool(d.get("direct_must_link_edge")) and sid in {d.get("left_sample_index_row_id"),d.get("right_sample_index_row_id")} for d in decisions),"final_leakage_group_id":g,"final_leakage_group_member_count":len(members),"final_leakage_group_status":"confirmed_nonindependent_group_within_current_11_sample_set" if len(members)>1 else "provisional_independent_singleton_within_current_11_sample_set","assignment_policy":POLICY,"eligible_for_split_materialization_current_step":True,"ready_for_training_current_step":False,"feature_semantics_audit_required_before_training":True,"leakage_split_design_required_before_training":True})
    return out

def validate_assignment_rows(candidate_rows:list[dict[str,Any]], unified_rows:list[dict[str,Any]], decisions:list[dict[str,Any]], ligand_evidence_rows:list[dict[str,Any]], protein_evidence_rows:list[dict[str,Any]], final_assignment_by_sample:dict[str,str], group_members:dict[str,list[str]])->list[dict[str,Any]]:
    unified={r.get("sample_index_row_id"):r for r in unified_rows}; lig=defaultdict(list); prot=defaultdict(list)
    for r in ligand_evidence_rows: lig[r.get("sample_index_row_id","")].append(r)
    for r in protein_evidence_rows: prot[r.get("sample_index_row_id","")].append(r)
    ids=[r.get("assignment_id","") for r in candidate_rows]; samples=[r.get("sample_index_row_id","") for r in candidate_rows]; out=[]
    expected_ids=[f"COVAPIE_ASSIGNMENT_{i:06d}" for i in range(1,len(candidate_rows)+1)]
    for n,row in enumerate(candidate_rows,1):
        r=dict(row); sid=r.get("sample_index_row_id",""); reasons=[]; src=unified.get(sid)
        if len(set(ids))!=len(ids): reasons.append("duplicate_assignment_id")
        if ids!=expected_ids: reasons.append("assignment_id_not_contiguous")
        if len(set(samples))!=len(samples): reasons.append("duplicate_assignment_sample_id")
        if not src: reasons.append(f"missing_unified_sample_row:{sid}")
        elif r.get("pdb_id")!=src.get("pdb_id"): reasons.append(f"assignment_pdb_mismatch:{sid}")
        if src and r.get("ligand_comp_id")!=src.get("ligand_comp_id"): reasons.append(f"assignment_ligand_mismatch:{sid}")
        expected_stage="pilot" if sid in [x[0] for x in EXPECTED[:3]] else "expansion"
        if r.get("source_index_stage")!=expected_stage: reasons.append(f"source_index_stage_mismatch:{sid}")
        if len(lig[sid])==0: reasons.append(f"missing_ligand_evidence_row:{sid}")
        elif len(lig[sid])>1: reasons.append(f"duplicate_ligand_evidence_row:{sid}")
        elif not truth(lig[sid][0].get("ligand_graph_evidence_passed")) or lig[sid][0].get("blocking_reasons"): reasons.append(f"failed_ligand_evidence_row:{sid}")
        if len(prot[sid])==0: reasons.append(f"missing_protein_evidence_row:{sid}")
        elif len(prot[sid])>1: reasons.append(f"duplicate_protein_evidence_row:{sid}")
        elif not truth(prot[sid][0].get("protein_sequence_evidence_passed")) or prot[sid][0].get("blocking_reasons"): reasons.append(f"failed_protein_evidence_row:{sid}")
        for f in ["ligand_graph_group_id","ligand_scaffold_group_id"]:
            if not r.get(f) or (len(lig[sid])==1 and r.get(f)!=lig[sid][0].get(f)): reasons.append(f"ligand_group_id_mismatch:{sid}:{f}")
        for f in ["protein_exact_sequence_group_id","protein_accession_group_id","protein_sequence_cluster_90_id","protein_sequence_cluster_50_id"]:
            if not r.get(f) or (len(prot[sid])==1 and r.get(f)!=prot[sid][0].get(f)): reasons.append(f"protein_group_id_mismatch:{sid}:{f}")
        neighbors=sum(bool(d.get("direct_must_link_edge")) and sid in {d.get("left_sample_index_row_id"),d.get("right_sample_index_row_id")} for d in decisions)
        if int(r.get("direct_must_link_neighbor_count",-1))!=neighbors: reasons.append(f"direct_neighbor_count_mismatch:{sid}")
        gid=final_assignment_by_sample.get(sid,""); members=group_members.get(gid,[])
        if r.get("final_leakage_group_id")!=gid: reasons.append(f"final_group_id_mismatch:{sid}")
        if int(r.get("final_leakage_group_member_count",-1))!=len(members): reasons.append(f"final_group_member_count_mismatch:{sid}")
        status="confirmed_nonindependent_group_within_current_11_sample_set" if len(members)>1 else "provisional_independent_singleton_within_current_11_sample_set"
        if r.get("final_leakage_group_status")!=status: reasons.append(f"final_group_status_mismatch:{sid}")
        if r.get("assignment_policy")!=POLICY: reasons.append(f"assignment_policy_mismatch:{sid}")
        if not truth(r.get("eligible_for_split_materialization_current_step")) or truth(r.get("ready_for_training_current_step")) or not truth(r.get("feature_semantics_audit_required_before_training")) or not truth(r.get("leakage_split_design_required_before_training")): reasons.append(f"assignment_readiness_boundary_mismatch:{sid}")
        r["final_group_assignment_passed"]=not reasons; r["blocking_reasons"]=";".join(sorted(set(reasons))); out.append(r)
    return out

def build_candidate_group_inventory_rows(group_members:dict[str,list[str]], decisions:list[dict[str,Any]], unified_rows:list[dict[str,Any]])->list[dict[str,Any]]:
    by={r.get("sample_index_row_id"):r for r in unified_rows}; ids=[r.get("sample_index_row_id") for r in unified_rows]; out=[]
    for n,(gid,members) in enumerate(sorted(group_members.items()),1):
        members=sorted(members); internal=[d for d in decisions if d.get("direct_must_link_edge") and d.get("left_sample_index_row_id") in members and d.get("right_sample_index_row_id") in members]; stages=["pilot" if s in ids[:3] else "expansion" for s in members]; composition="pilot" if set(stages)=={"pilot"} else "expansion" if set(stages)=={"expansion"} else "pilot;expansion"
        out.append({"final_leakage_group_id":gid,"group_order":n,"member_count":len(members),"member_sample_index_row_ids":";".join(members),"member_pdb_het_pairs":";".join(f"{by.get(s,{}).get('pdb_id','')}/{by.get(s,{}).get('ligand_comp_id','')}" for s in members),"source_stage_composition":composition,"direct_internal_must_link_edge_count":len(internal),"ligand_axis_internal_edge_count":sum(bool(d.get("ligand_axis_must_link")) for d in internal),"protein_axis_internal_edge_count":sum(bool(d.get("protein_axis_must_link")) for d in internal),"singleton_group":len(members)==1,"final_leakage_group_status":"confirmed_nonindependent_group_within_current_11_sample_set" if len(members)>1 else "provisional_independent_singleton_within_current_11_sample_set"})
    return out

def validate_group_inventory_rows(candidate_rows:list[dict[str,Any]], validated_assignment_rows:list[dict[str,Any]], decisions:list[dict[str,Any]], unified_rows:list[dict[str,Any]])->list[dict[str,Any]]:
    unified={r.get("sample_index_row_id"):r for r in unified_rows}; assigned=defaultdict(list)
    for r in validated_assignment_rows: assigned[r.get("final_leakage_group_id","")].append(r.get("sample_index_row_id",""))
    gids=[r.get("final_leakage_group_id","") for r in candidate_rows]; all_members=[]; out=[]
    for n,row in enumerate(candidate_rows,1):
        r=dict(row); gid=r.get("final_leakage_group_id",""); raw=r.get("member_sample_index_row_ids",""); members=raw.split(";") if raw else []; reasons=[]; all_members.extend(members)
        if len(candidate_rows)!=5: reasons.append("group_inventory_row_count_mismatch")
        if len(set(gids))!=len(gids): reasons.append("duplicate_final_group_id")
        if gids!=[f"COVAPIE_LEAKAGE_GROUP_{i:06d}" for i in range(1,len(gids)+1)]: reasons.append("final_group_id_not_contiguous")
        if [int(x.get("group_order",-1)) for x in candidate_rows]!=list(range(1,len(candidate_rows)+1)): reasons.append("group_order_not_contiguous")
        if not members: reasons.append(f"empty_group_member_list:{gid}")
        if members!=sorted(members): reasons.append(f"unsorted_group_member_list:{gid}")
        if len(members)!=len(set(members)): reasons.append(f"duplicate_group_member:{gid}")
        if int(r.get("member_count",-1))!=len(members): reasons.append(f"group_member_count_mismatch:{gid}")
        if set(members)!=set(assigned.get(gid,[])): reasons.append(f"assignment_inventory_membership_mismatch:{gid}")
        expected_pairs=";".join(f"{unified[s]['pdb_id']}/{unified[s]['ligand_comp_id']}" for s in members if s in unified)
        if r.get("member_pdb_het_pairs")!=expected_pairs: reasons.append(f"pdb_het_pair_mismatch:{gid}")
        stages=["pilot" if s in [x[0] for x in EXPECTED[:3]] else "expansion" for s in members]; composition="pilot" if set(stages)=={"pilot"} else "expansion" if set(stages)=={"expansion"} else "pilot;expansion"
        if r.get("source_stage_composition")!=composition: reasons.append(f"source_stage_composition_mismatch:{gid}")
        internal=[d for d in decisions if d.get("direct_must_link_edge") and d.get("left_sample_index_row_id") in members and d.get("right_sample_index_row_id") in members]
        for field,value,label in [("direct_internal_must_link_edge_count",len(internal),"direct_internal_edge_count_mismatch"),("ligand_axis_internal_edge_count",sum(bool(d.get("ligand_axis_must_link")) for d in internal),"ligand_internal_edge_count_mismatch"),("protein_axis_internal_edge_count",sum(bool(d.get("protein_axis_must_link")) for d in internal),"protein_internal_edge_count_mismatch")]:
            if int(r.get(field,-1))!=value: reasons.append(f"{label}:{gid}")
        singleton=len(members)==1
        if truth(r.get("singleton_group"))!=singleton: reasons.append(f"singleton_flag_mismatch:{gid}")
        status="provisional_independent_singleton_within_current_11_sample_set" if singleton else "confirmed_nonindependent_group_within_current_11_sample_set"
        if r.get("final_leakage_group_status")!=status: reasons.append(f"group_status_mismatch:{gid}")
        r["group_inventory_passed"]=not reasons; r["blocking_reasons"]=";".join(sorted(set(reasons))); out.append(r)
    counts=Counter(all_members)
    global_reasons=[f"sample_missing_from_inventory:{sid}" for sid in unified if counts[sid]==0]+[f"sample_in_multiple_inventory_groups:{sid}" for sid,c in counts.items() if c>1]
    group_for={sid:r.get("final_leakage_group_id") for r in candidate_rows for sid in str(r.get("member_sample_index_row_ids","")).split(";") if sid}
    global_reasons += [f"cross_group_direct_edge:{d.get('left_sample_index_row_id')}:{d.get('right_sample_index_row_id')}" for d in decisions if d.get("direct_must_link_edge") and group_for.get(d.get("left_sample_index_row_id"))!=group_for.get(d.get("right_sample_index_row_id"))]
    if global_reasons:
        for r in out: r["group_inventory_passed"]=False; r["blocking_reasons"]=";".join(sorted(set(filter(None,[r["blocking_reasons"],*global_reasons]))))
    return out

def _blocked_schema_rows(block_scope: str) -> list[dict[str,Any]]:
    if block_scope not in {"input_loading","semantic_validation"}: raise ValueError("invalid_premerge_block_scope")
    blocking_reason="input_loading_failed_before_schema_validation" if block_scope=="input_loading" else "semantic_validation_failed_before_schema_validation"
    integer_fields={"protein_atom_count","ligand_atom_count","pocket_atom_count","covalent_event_count","ligand_residue_atom_pair_count"}; boolean_fields={"eligible_for_final_dataset_design","ready_for_training_current_step","feature_semantics_audit_required_before_training","leakage_split_design_required_before_training"}
    return [{"schema_validation_id":f"COVAPIE_SCHEMA_{n:06d}","sample_index_field":name,"expected_data_type":"integer" if name in integer_fields else "boolean" if name in boolean_fields else "number" if name=="bond_distance_angstrom" else "string","csv_column_present":False,"json_field_present_all_rows":False,"non_null_rule_passed":False,"data_type_validation_passed":False,"source_field_preservation_passed":False,"semantic_validation_passed":False,"schema_validation_status":"failed","blocking_reasons":blocking_reason} for n,name in enumerate(SAMPLE_INDEX_FIELDS,1)]

def write_premerge_blocked_outputs(*, loaded: LoadedInputs, activity: RunActivity, block_scope: str, blocking_reasons: list[str]) -> dict[str,Any]:
    if block_scope not in {"input_loading","semantic_validation"}: raise ValueError("invalid_premerge_block_scope")
    schema=_blocked_schema_rows(block_scope)
    aliases={"pilot_json":"pilot_index","expansion_json":"expansion_index"}
    pre=[]
    for name in LOGICAL_INPUT_NAMES:
        tokens={name,aliases.get(name,name)}
        related=[reason for reason in loaded.blocking_reasons if any(token in reason for token in tokens)]
        pre.append({"precondition_item":f"{name}_load","artifact_or_check":"input_loading","expected_status":True,"observed_status":not related,"precondition_passed":not related,"blocking_reasons":";".join(related)})
    if block_scope=="semantic_validation": pre.append({"precondition_item":"semantic_validation","artifact_or_check":"semantic_validation","expected_status":True,"observed_status":False,"precondition_passed":False,"blocking_reasons":";".join(sorted(set(blocking_reasons)))})
    write_csv(OUT["unified_sample_index.csv"],[],SAMPLE_INDEX_FIELDS,activity); write_json(OUT["unified_sample_index.json"],[],activity)
    write_csv(OUT["covapie_unified_sample_index_schema_validation_audit.csv"],schema,SCHEMA_AUDIT_FIELDS,activity)
    write_csv(OUT["covapie_final_leakage_group_assignment.csv"],[],ASSIGNMENT_FIELDS,activity); write_json(OUT["covapie_final_leakage_group_assignment.json"],[],activity)
    write_csv(OUT["covapie_final_leakage_group_inventory.csv"],[],GROUP_INVENTORY_FIELDS,activity)
    write_csv(OUT["covapie_pairwise_group_assignment_decision_audit.csv"],[],PAIR_DECISION_FIELDS,activity)
    write_csv(OUT["covapie_unified_sample_index_merge_traceability_audit.csv"],[],TRACEABILITY_FIELDS,activity)
    observations=build_safety_observations(read_paths=activity.read_paths,written_paths=activity.written_paths,embedded_assignment_qa_passed=False,embedded_schema_qa_passed=False,embedded_traceability_qa_passed=False,network_access_used=activity.network_access_used,download_attempted=activity.download_attempted)
    safety=build_safety_rows(observations,BLOCKED_SAFETY_EXPECTED)
    scope_blocker="input_loading_failed_before_schema_validation" if block_scope=="input_loading" else "semantic_validation_failed_before_schema_validation"
    blockers=list(blocking_reasons)+[row["blocking_reasons"] for row in safety if not row["safety_passed"]]+[scope_blocker]
    issues,blockers=build_issue_rows(blockers)
    write_csv(OUT["covapie_unified_assignment_merge_precondition_audit.csv"],pre,PRECONDITION_FIELDS,activity)
    write_csv(OUT["covapie_unified_assignment_merge_safety_audit.csv"],safety,SAFETY_FIELDS,activity)
    write_csv(OUT["covapie_unified_assignment_merge_issue_inventory.csv"],issues,ISSUE_FIELDS,activity)
    all_safety=len(safety)==39 and all(row["safety_passed"] for row in safety)
    manifest={"stage":STAGE,"step_label":"Step 14AP","previous_stage":PREVIOUS,"project_name":"CovaPIE","input_load_passed":loaded.input_load_passed,"input_load_blocking_reason_count":len(loaded.blocking_reasons),"semantic_validation_passed":False,"semantic_validation_blocking_reason_count":len(blocking_reasons) if block_scope=="semantic_validation" else 0,"input_blocked_output_contract_written":block_scope=="input_loading","premerge_blocked_output_contract_written":True,"blocked_before_unified_merge":True,"blocked_before_group_assignment":True,"premerge_block_scope":block_scope,"unified_sample_index_row_count":0,"unified_sample_index_schema_field_count":33,"unified_sample_index_written":False,"unified_sample_index_blocked_contract_artifact_written":True,"final_group_assignment_row_count":0,"final_independence_group_assignment_written":False,"pairwise_assignment_decision_count":0,"direct_must_link_edge_count":0,"no_direct_must_link_pair_count":0,"final_leakage_group_count":0,"final_leakage_group_sizes":[],"confirmed_new_independent_group_count_current_step":0,"split_assignments_written":False,"leakage_matrix_written":False,"final_dataset_written":False,"actual_dataloader_artifacts_written":False,"training_artifacts_written":False,"all_preconditions_passed":False,"all_schema_checks_passed":False,"all_pairwise_assignment_checks_passed":False,"all_group_assignment_checks_passed":False,"all_merge_traceability_checks_passed":False,"all_safety_checks_passed":all_safety,"issue_inventory_row_count":len(issues),"blocking_issue_count":len(issues),"issue_inventory_clear":False,"all_checks_passed":False,"ready_for_covapie_unified_leakage_split_materialization_smoke":False,"ready_for_covapie_final_dataset_materialization_smoke":False,"ready_for_training":False,"ready_to_train_now":False,"feature_semantics_known_for_training":False,"unknown_atom_feature_policy_finalized_for_training":False,"feature_semantics_audit_required_before_training":True,"leakage_split_design_required_before_training":True,"canonical_mask_task_names":CANONICAL_MASK_TASK_NAMES,"canonical_mask_task_aliases":CANONICAL_MASK_TASK_ALIASES,"b3_scaffold_only_included":True,"no_extra_mask_tasks_added":True,"recommended_next_step":"resolve_covapie_unified_assignment_merge_issues","blocking_reasons":blockers}
    write_json(OUT["covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_manifest.json"],manifest,activity)
    atomic(SUMMARY,f"# CovaPIE unified independence group assignment and sample-index merge smoke v0\n\nStep 14AP was blocked during {block_scope}. Header-only contract artifacts were written; no merge, group assignment, split, final dataset, dataloader artifact, or training output was produced.\n",activity)
    return {"manifest":manifest,"decisions":[],"assignment":[],"inventory":[],"traceability":[],"safety_observations":observations,"safety_rows":safety,"issue_rows":issues,"loaded_inputs":loaded}

def run(input_paths: InputPaths = DEFAULT_INPUT_PATHS)->dict[str,Any]:
    activity=RunActivity()
    loaded=load_inputs_safely(input_paths,activity)
    if not loaded.input_load_passed: return write_premerge_blocked_outputs(loaded=loaded,activity=activity,block_scope="input_loading",blocking_reasons=loaded.blocking_reasons)
    semantic=validate_loaded_inputs_semantically(loaded)
    if not semantic.semantic_validation_passed: return write_premerge_blocked_outputs(loaded=loaded,activity=activity,block_scope="semantic_validation",blocking_reasons=semantic.blocking_reasons)
    pilot,exp=semantic.normalized_pilot_rows,semantic.normalized_expansion_rows
    pjson,ejson=loaded.pilot_json_rows,loaded.expansion_json_rows
    rows=pilot+exp; source_json_rows=pjson+ejson; ids=[r["sample_index_row_id"] for r in rows]; issues=[]
    if len(pilot)!=3 or len(exp)!=8 or any(list(r)!=SAMPLE_INDEX_FIELDS for r in rows): issues.append("source_index_schema_or_count")
    if pjson!=[typed(r) for r in pilot] or ejson!=[typed(r) for r in exp]: issues.append("source_csv_json_inconsistent")
    if [(r["sample_index_row_id"],r["pdb_id"],r["ligand_comp_id"]) for r in rows]!=EXPECTED or len(ids)!=len(set(ids)) or len({(r["pdb_id"],r["ligand_comp_id"]) for r in rows})!=11: issues.append("source_identity_or_order")
    manifest=loaded.step14ao_manifest
    if not(manifest.get("stage")==PREVIOUS and manifest.get("all_checks_passed") and manifest.get("ready_for_covapie_unified_independence_group_assignment_and_sample_index_merge_smoke")): issues.append("step14ao_precondition")
    combined,lpair,ppair,lig,prot=semantic.validated_combined_pairwise_rows,semantic.validated_ligand_pairwise_rows,semantic.validated_protein_pairwise_rows,semantic.validated_ligand_evidence_rows,semantic.validated_protein_evidence_rows
    if len(combined)!=55 or any(r["combined_pairwise_independence_evidence_classification"]=="evidence_incomplete" for r in combined): issues.append("combined_evidence_incomplete")
    pairkey=lambda r:(r.get("left_sample_index_row_id",""),r.get("right_sample_index_row_id",""))
    lmap={pairkey(r):r for r in lpair}; pmap={pairkey(r):r for r in ppair}
    if len(lpair)!=55 or len(ppair)!=55 or len(lmap)!=55 or len(pmap)!=55 or set(lmap)!=set(pmap) or set(lmap)!={pairkey(r) for r in combined}: issues.append("pairwise_source_table_inconsistent")
    decisions=[]
    for n,r in enumerate(combined,1):
        l,rr=r["left_sample_index_row_id"],r["right_sample_index_row_id"]; lr,pr=lmap.get((l,rr),{}),pmap.get((l,rr),{}); lc=bool(lr) and truth(lr.get("ligand_pairwise_evidence_passed")) and not lr.get("blocking_reasons",""); pc=bool(pr) and truth(pr.get("protein_pairwise_evidence_passed")) and not pr.get("blocking_reasons",""); d=decide_pair(r,lc,pc); d.update({"pair_assignment_decision_id":f"COVAPIE_PAIR_ASSIGNMENT_{n:06d}","left_sample_index_row_id":l,"right_sample_index_row_id":rr,"left_pdb_id":r["left_pdb_id"],"right_pdb_id":r["right_pdb_id"],"left_ligand_comp_id":r["left_ligand_comp_id"],"right_ligand_comp_id":r["right_ligand_comp_id"],"source_combined_evidence_row_found":True,"same_ligand_graph":r["same_ligand_graph"],"same_murcko_scaffold":r["same_murcko_scaffold"],"same_protein_accession":r["same_protein_accession"],"same_exact_protein_sequence":r["same_exact_protein_sequence"],"same_sequence_cluster_90":r["same_sequence_cluster_90"],"same_sequence_cluster_50":r["same_sequence_cluster_50"]}); decisions.append(d)
    assignment=groups(ids,decisions); members=defaultdict(list)
    for sid,g in assignment.items(): members[g].append(sid)
    for d in decisions:
        same=assignment[d["left_sample_index_row_id"]]==assignment[d["right_sample_index_row_id"]]; pair_passed=d["source_ligand_evidence_complete"] and d["source_protein_evidence_complete"] and d["pair_assignment_classification"]!="blocked_evidence_incomplete"; d.update({"same_final_leakage_group_after_transitive_closure":same,"transitive_only_same_group":same and not d["direct_must_link_edge"],"pair_assignment_passed":pair_passed,"blocking_reasons":"" if pair_passed else "pairwise_evidence_incomplete"})
    if len(members)!=5 or sum(d["direct_must_link_edge"] for d in decisions)!=13: issues.append("unexpected_group_assignment")

    unified_json=[typed(r) for r in rows]
    write_csv(OUT["unified_sample_index.csv"],rows,SAMPLE_INDEX_FIELDS,activity); write_json(OUT["unified_sample_index.json"],unified_json,activity)
    disk_unified_csv,disk_unified_json,csv_json_ok=validate_written_unified(unified_json,activity)
    if not csv_json_ok: issues.append("unified_post_write_validation_failed")
    schema=schema_rows_from_disk(unified_json,read_csv(OUT["unified_sample_index.csv"],activity),disk_unified_json)

    candidate_assignment=build_candidate_assignment_rows(rows,decisions,lig,prot,assignment,members)
    assignment_rows=validate_assignment_rows(candidate_assignment,rows,decisions,lig,prot,assignment,members)
    write_csv(OUT["covapie_final_leakage_group_assignment.csv"],assignment_rows,ASSIGNMENT_FIELDS,activity)
    write_json(OUT["covapie_final_leakage_group_assignment.json"],assignment_rows,activity)
    assignment_write=validate_written_assignment(assignment_rows,OUT["covapie_final_leakage_group_assignment.csv"],OUT["covapie_final_leakage_group_assignment.json"],activity)
    if not assignment_write["assignment_write_validation_passed"]: issues.append(assignment_write["blocking_reasons"] or "assignment_write_validation_failed")

    candidate_inventory=build_candidate_group_inventory_rows(members,decisions,rows)
    inventory=validate_group_inventory_rows(candidate_inventory,assignment_rows,decisions,rows)
    trace=build_merge_traceability_rows(rows,source_json_rows,disk_unified_csv,disk_unified_json,assignment_write["disk_assignment_csv_typed_rows"],assignment_write["disk_assignment_json_rows"])
    write_csv(OUT["covapie_unified_sample_index_merge_traceability_audit.csv"],trace,TRACEABILITY_FIELDS,activity)
    trace_write=validate_written_traceability(trace,OUT["covapie_unified_sample_index_merge_traceability_audit.csv"],activity)
    issues.extend(row["blocking_reasons"] for row in trace if not row["merge_traceability_passed"])
    if not trace_write["traceability_written_validation_passed"]: issues.append(trace_write["blocking_reasons"] or "traceability_written_validation_failed")
    write_csv(OUT["covapie_unified_sample_index_schema_validation_audit.csv"],schema,list(schema[0]),activity)
    write_csv(OUT["covapie_final_leakage_group_inventory.csv"],inventory,list(inventory[0]),activity)
    write_csv(OUT["covapie_pairwise_group_assignment_decision_audit.csv"],decisions,list(decisions[0]),activity)
    embedded_assignment=len(assignment_rows)==11 and all(row["final_group_assignment_passed"] for row in assignment_rows) and len(inventory)==5 and all(row["group_inventory_passed"] for row in inventory) and assignment_write["assignment_write_validation_passed"] and csv_json_ok
    embedded_schema=len(schema)==33 and all(row["schema_validation_status"]=="passed" for row in schema)
    embedded_trace=len(trace)==11 and all(row["merge_traceability_passed"] for row in trace) and trace_write["traceability_written_validation_passed"]
    observations=build_safety_observations(read_paths=activity.read_paths,written_paths=activity.written_paths,embedded_assignment_qa_passed=embedded_assignment,embedded_schema_qa_passed=embedded_schema,embedded_traceability_qa_passed=embedded_trace,network_access_used=activity.network_access_used,download_attempted=activity.download_attempted)
    safe_rows=build_safety_rows(observations)
    issues.extend(row["blocking_reasons"] for row in safe_rows if not row["safety_passed"])
    issues.extend(row["blocking_reasons"] for row in decisions if not row["pair_assignment_passed"])
    issues.extend(row["blocking_reasons"] for row in assignment_rows if not row["final_group_assignment_passed"])
    issues.extend(row["blocking_reasons"] for row in inventory if not row["group_inventory_passed"])
    issue14ao=loaded.step14ao_issue_rows
    gcheck=lambda *args: not bool(subprocess.run(["git",*args],cwd=REPO,text=True,stdout=subprocess.PIPE,check=False).stdout.strip())
    checks={"step14ao_manifest_exists":rp(input_paths.step14ao_manifest).is_file(),"step14ao_manifest_stage":manifest.get("stage")==PREVIOUS,"step14ao_all_checks_passed":manifest.get("all_checks_passed") is True,"step14ao_blocking_reasons_clear":manifest.get("blocking_reasons")==[],"step14ao_ready_for_current_step":manifest.get("ready_for_covapie_unified_independence_group_assignment_and_sample_index_merge_smoke") is True,"step14ao_issue_count_zero":manifest.get("materialization_issue_count")==0,"step14ao_issue_sentinel":len(issue14ao)==1 and issue14ao[0].get("issue_status")=="passed","step14ao_ligand_evidence_11":len(lig)==11 and all(truth(r.get("ligand_graph_evidence_passed")) for r in lig),"step14ao_protein_evidence_11":len(prot)==11 and all(truth(r.get("protein_sequence_evidence_passed")) for r in prot),"step14ao_ligand_pairwise_55":len(lpair)==55 and all(truth(r.get("ligand_pairwise_evidence_passed")) for r in lpair),"step14ao_protein_pairwise_55":len(ppair)==55 and all(truth(r.get("protein_pairwise_evidence_passed")) for r in ppair),"step14ao_combined_pairwise_55":len(combined)==55,"step14ao_classifications_3_10_42":Counter(r.get("combined_pairwise_independence_evidence_classification") for r in combined)=={"strong_same_group_evidence":3,"protein_related_ligand_distinct":10,"provisional_distinct_both_axes":42},"step14ao_evidence_incomplete_zero":not any(r.get("combined_pairwise_independence_evidence_classification")=="evidence_incomplete" for r in combined),"pilot_csv_json_exists":rp(input_paths.pilot_csv).is_file() and rp(input_paths.pilot_json).is_file(),"pilot_hashes_unchanged":observations["pilot_index_files_unchanged"],"pilot_csv_json_typed_consistent":pjson==[typed(r) for r in pilot],"expansion_csv_json_exists":rp(input_paths.expansion_csv).is_file() and rp(input_paths.expansion_json).is_file(),"expansion_hashes_unchanged":observations["expansion_index_files_unchanged"],"expansion_csv_json_typed_consistent":ejson==[typed(r) for r in exp],"canonical_schema_33":len(SAMPLE_INDEX_FIELDS)==33,"unified_ids_exact":[(r["sample_index_row_id"],r["pdb_id"],r["ligand_comp_id"]) for r in rows]==EXPECTED,"no_duplicate_row_id":len(ids)==len(set(ids)),"no_duplicate_pdb_het":len({(r["pdb_id"],r["ligand_comp_id"]) for r in rows})==11,"step14ao_artifacts_unchanged":gcheck("diff","--",str(EVIDENCE)),"step14an_artifacts_unchanged":gcheck("diff","--","data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_index_materialization_smoke_v0"),"step14am_artifacts_unchanged":gcheck("diff","--","data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0"),"staged_files_empty":gcheck("diff","--cached","--name-only"),"protected_model_dataloader_diff_empty":gcheck("diff","--","equivariant_diffusion/","lightning_modules.py","dataset.py","data/prepare_crossdocked.py"),"canonical_masks_preserved":CANONICAL_MASK_TASK_ALIASES==["A","B","B2","B3","C"]}
    pre=[{"precondition_item":k,"artifact_or_check":"input_or_evidence_validation","expected_status":True,"observed_status":v,"precondition_passed":v,"blocking_reasons":"" if v else k} for k,v in checks.items()]
    issues.extend(row["blocking_reasons"] for row in pre if not row["precondition_passed"])
    issues.extend(row["blocking_reasons"] for row in schema if row["schema_validation_status"]!="passed")
    issue_rows,issues=build_issue_rows(issues)
    write_csv(OUT["covapie_unified_assignment_merge_issue_inventory.csv"],issue_rows,ISSUE_FIELDS,activity)
    write_csv(OUT["covapie_unified_assignment_merge_safety_audit.csv"],safe_rows,SAFETY_FIELDS,activity)
    write_csv(OUT["covapie_unified_assignment_merge_precondition_audit.csv"],pre,list(pre[0]),activity)
    all_pre=all(row["precondition_passed"] for row in pre); all_schema=len(schema)==33 and all(row["schema_validation_status"]=="passed" for row in schema); all_pair=len(decisions)==55 and all(row["pair_assignment_passed"] for row in decisions); all_safety=len(safe_rows)==39 and all(row["safety_passed"] for row in safe_rows); all_groups=len(assignment_rows)==11 and all(row["final_group_assignment_passed"] for row in assignment_rows) and len(inventory)==5 and all(row["group_inventory_passed"] for row in inventory) and assignment_write["assignment_write_validation_passed"] and assignment_write["assignment_csv_json_consistent"]; all_trace=len(trace)==11 and all(row["merge_traceability_passed"] for row in trace) and trace_write["traceability_written_validation_passed"]
    blocking_issue_count=sum(row["issue_status"]=="failed" for row in issue_rows); issue_clear=blocking_issue_count==0 and len(issue_rows)==1 and issue_rows[0]["issue_id"]=="NO_UNIFIED_ASSIGNMENT_OR_SAMPLE_INDEX_MERGE_ISSUES" and issue_rows[0]["issue_status"]=="passed"
    passed=all([all_pre,all_schema,all_pair,all_groups,all_trace,all_safety,issue_clear,csv_json_ok,assignment_write["assignment_write_validation_passed"],trace_write["traceability_written_validation_passed"]])
    man={"stage":STAGE,"step_label":"Step 14AP","previous_stage":PREVIOUS,"project_name":"CovaPIE","pilot_sample_count":3,"expansion_sample_count":8,"unified_sample_index_row_count":11,"unified_sample_index_schema_field_count":33,"unified_sample_index_csv_json_consistent":csv_json_ok,"unified_sample_index_csv_sha256":digest(OUT['unified_sample_index.csv']),"unified_sample_index_json_sha256":digest(OUT['unified_sample_index.json']),"final_group_assignment_row_count":11,"final_group_assignment_csv_json_consistent":assignment_write["assignment_csv_json_consistent"],"final_group_assignment_source_preservation_passed":assignment_write["assignment_source_preservation_passed"],"final_group_assignment_row_order_passed":assignment_write["assignment_row_order_passed"],"final_group_assignment_write_validation_passed":assignment_write["assignment_write_validation_passed"],"final_group_assignment_csv_sha256":digest(OUT["covapie_final_leakage_group_assignment.csv"]),"final_group_assignment_json_sha256":digest(OUT["covapie_final_leakage_group_assignment.json"]),"merge_traceability_row_count":len(trace),"merge_traceability_written_validation_passed":trace_write["traceability_written_validation_passed"],"merge_traceability_csv_sha256":digest(OUT["covapie_unified_sample_index_merge_traceability_audit.csv"]),"issue_inventory_row_count":len(issue_rows),"blocking_issue_count":blocking_issue_count,"issue_inventory_clear":issue_clear,"safety_observation_key_count":len(observations),"safety_audit_row_count":len(safe_rows),"pairwise_assignment_decision_count":55,"direct_must_link_edge_count":sum(d['direct_must_link_edge'] for d in decisions),"no_direct_must_link_pair_count":sum(not d['direct_must_link_edge'] for d in decisions),"final_leakage_group_count":len(members),"final_leakage_group_sizes":[len(v) for _,v in sorted(members.items())],"pilot_baseline_group_count":1,"confirmed_new_independent_group_count_current_step":4,"final_leakage_group_ids":sorted(members),"group_assignment_policy":POLICY,"source_indexes_modified":False,"final_independence_group_assignment_written":True,"unified_sample_index_written":True,"split_assignments_written":False,"leakage_matrix_written":False,"final_dataset_written":False,"actual_dataloader_artifacts_written":False,"training_artifacts_written":False,"all_preconditions_passed":passed,"all_schema_checks_passed":passed,"all_merge_traceability_checks_passed":passed,"all_pairwise_assignment_checks_passed":passed,"all_group_assignment_checks_passed":passed,"all_safety_checks_passed":passed,"ready_for_covapie_unified_leakage_split_materialization_smoke":passed,"ready_for_covapie_final_dataset_materialization_smoke":False,"ready_for_training":False,"ready_to_train_now":False,"feature_semantics_known_for_training":False,"unknown_atom_feature_policy_finalized_for_training":False,"feature_semantics_audit_required_before_training":True,"leakage_split_design_required_before_training":True,"canonical_mask_task_names":CANONICAL_MASK_TASK_NAMES,"canonical_mask_task_aliases":CANONICAL_MASK_TASK_ALIASES,"b3_scaffold_only_included":True,"no_extra_mask_tasks_added":True,"recommended_next_step":"covapie_unified_leakage_split_materialization_smoke" if passed else "resolve_covapie_unified_assignment_merge_issues","all_checks_passed":passed,"blocking_reasons":issues}
    man.update({"input_load_passed":True,"semantic_validation_passed":True,"semantic_validation_blocking_reason_count":0,"blocked_before_unified_merge":False,"blocked_before_group_assignment":False,"premerge_block_scope":"none","all_preconditions_passed":all_pre,"all_schema_checks_passed":all_schema,"all_merge_traceability_checks_passed":all_trace,"all_pairwise_assignment_checks_passed":all_pair,"all_group_assignment_checks_passed":all_groups,"all_safety_checks_passed":all_safety,"new_leakage_split_unit_count_current_step":4,"independence_claim_scope":"current_11_sample_conservative_v1_policy_only","singleton_independence_status":"provisional_not_absolute_independence","confirmed_new_independent_group_count_semantics":"four_new_leakage_split_units_relative_to_the_single_pilot_baseline_group_under_current_v1_policy"})
    write_json(OUT["covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_manifest.json"],man,activity); atomic(SUMMARY,"# CovaPIE unified independence group assignment and sample-index merge smoke v0\n\nStep 14AP writes a canonical 11-row unified index and separate conservative leakage-group assignments. It performs embedded post-write assignment, traceability, and explicit safety validation. It does not write a split, final dataset, dataloader artifact, or training output.\n",activity)
    return {"manifest":man,"decisions":decisions,"assignment":assignment_rows,"inventory":inventory,"traceability":trace,"assignment_write_validation":assignment_write,"traceability_write_validation":trace_write,"safety_observations":observations,"safety_rows":safe_rows,"issue_rows":issue_rows}
