"""Step 14AN: isolated eight-row CovaPIE expansion sample-index smoke."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext.covapie_sample_index_design_gate import (
    CANONICAL_MASK_TASK_ALIASES,
    CANONICAL_MASK_TASK_NAMES,
    SAMPLE_INDEX_FIELDS,
)

REPO = Path(__file__).resolve().parents[2]
STAGE = "covapie_independent_group_expansion_batch_sample_index_materialization_smoke_v0"
OUT = Path("data/derived/covalent_small") / STAGE
AM = Path("data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0")
AL = Path("data/derived/covalent_small/covapie_independent_group_expansion_struct_conn_crosscheck_smoke_v0")
AK = Path("data/derived/covalent_small/covapie_independent_group_expansion_acquisition_execution_smoke_v0")
EXISTING_CSV = Path("data/derived/covalent_small/covapie_sample_index_materialization_smoke_v0/sample_index.csv")
EXISTING_JSON = Path("data/derived/covalent_small/covapie_sample_index_materialization_smoke_v0/sample_index.json")
META = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
RAW = Path("data/raw/covalent_sources/covpdb/independent_group_expansion_batch_000001")
PRE = OUT / "covapie_expansion_batch_sample_index_precondition_audit.csv"
INDEX_CSV = OUT / "expansion_batch_sample_index.csv"
INDEX_JSON = OUT / "expansion_batch_sample_index.json"
SCHEMA = OUT / "covapie_expansion_batch_sample_index_schema_validation_audit.csv"
TRACE = OUT / "covapie_expansion_batch_sample_index_row_traceability_audit.csv"
COLLISION = OUT / "covapie_expansion_batch_sample_index_collision_audit.csv"
ISSUES = OUT / "covapie_expansion_batch_sample_index_materialization_issue_inventory.csv"
SAFETY = OUT / "covapie_expansion_batch_sample_index_safety_audit.csv"
MANIFEST = OUT / "covapie_independent_group_expansion_batch_sample_index_materialization_smoke_manifest.json"

PAIRS = [("1AEC", "E64", "C2"), ("1AIM", "ZYA", "CM"), ("1AU3", "PCM", "C22"), ("1AU4", "INP", "C17"), ("1AYU", "INA", "C21"), ("1AYV", "IN6", "C21"), ("1AYW", "IN3", "C21"), ("1B02", "UFP", "C6")]
EXISTING_HASHES = {EXISTING_CSV: "2733991775edf5e075b461a9ba1872c7e2fe7f61f5d9614a2704b814c3f0e2c5", EXISTING_JSON: "8d740458e30cc77bbaa568c615dd10f5df334cd0c46f21433c570c16391b8b38"}
PRE_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SCHEMA_COLUMNS = ["schema_validation_id", "sample_index_field", "expected_data_type", "csv_column_present", "json_field_present_all_rows", "non_null_rule_passed", "data_type_validation_passed", "semantic_validation_passed", "schema_validation_status", "blocking_reasons"]
TRACE_COLUMNS = ["row_traceability_id", "sample_index_row_id", "sample_preparation_input_id", "sample_execution_id", "sample_qa_id", "pdb_id", "expected_het_id", "execution_manifest_row_found", "sample_inventory_row_found", "traceability_source_row_found", "quality_source_row_found", "all_six_artifact_paths_exist", "actual_table_counts_match_index", "execution_counts_match_index", "event_table_single_row", "pair_table_single_row", "event_identity_matches_index", "pair_identity_matches_index", "event_pair_dynamic_atom_names_consistent", "bond_distance_matches_pair_table", "embedded_sample_audit_13_of_13_passed", "row_traceability_status", "blocking_reasons"]
COLLISION_COLUMNS = ["collision_audit_id", "sample_index_row_id", "pdb_id", "expected_het_id", "row_id_collision_with_existing_index", "pdb_het_collision_with_existing_index", "duplicate_row_id_within_expansion_batch", "duplicate_pdb_het_within_expansion_batch", "namespace_continuity_passed", "collision_audit_passed", "blocking_reasons"]
ISSUE_COLUMNS = ["issue_id", "issue_scope", "sample_index_row_id", "pdb_id", "expected_het_id", "issue_severity", "issue_type", "issue_description", "issue_status"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]
BOOL_FIELDS = {"eligible_for_final_dataset_design", "ready_for_training_current_step", "feature_semantics_audit_required_before_training", "leakage_split_design_required_before_training"}
INT_FIELDS = {"protein_atom_count", "ligand_atom_count", "pocket_atom_count", "covalent_event_count", "ligand_residue_atom_pair_count"}
SAFETY_EXPECTED = {"network_access_used_current_step": False, "download_attempted_current_step": False, "raw_mmcif_read_current_step": False, "struct_conn_parsed_current_step": False, "atom_site_parsed_current_step": False, "raw_files_modified": False, "raw_files_tracked": False, "raw_files_staged": False, "step14am_artifacts_unchanged": True, "step14al_artifacts_unchanged": True, "step14ak_artifacts_unchanged": True, "existing_sample_index_files_unchanged": True, "metadata_csv_unchanged": True, "expansion_batch_sample_index_csv_written": True, "expansion_batch_sample_index_json_written": True, "existing_sample_index_modified": False, "combined_sample_index_written": False, "standalone_sample_index_qa_gate_created": False, "embedded_sample_index_qa_performed": True, "split_assignments_written": False, "leakage_matrix_written": False, "final_dataset_written": False, "actual_dataloader_artifacts_written": False, "training_artifacts_written": False, "part_or_tmp_files_remaining": False, "protected_source_diff_empty": True, "original_dataloader_diff_empty": True, "torch_imported": False, "numpy_imported": False, "rdkit_used": False, "biopython_used": False, "gemmi_used": False, "requests_used": False}


def _csv(path: Path) -> list[dict[str, str]]:
    with (REPO / path).open(newline="", encoding="utf-8") as handle: return list(csv.DictReader(handle))
def _json(path: Path) -> Any: return json.loads((REPO / path).read_text(encoding="utf-8"))
def _sha(path: Path) -> str: return hashlib.sha256((REPO / path).read_bytes()).hexdigest()
def _bool(value: Any) -> bool: return value is True or str(value).lower() == "true"
def _git(args: list[str]) -> subprocess.CompletedProcess[str]: return subprocess.run(["git", *args], cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
def _changed(paths: list[str]) -> bool: return _git(["diff", "--quiet", "--", *paths]).returncode != 0 or _git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0
def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    target=REPO/path; target.parent.mkdir(parents=True,exist_ok=True); tmp=target.with_name(target.name+".tmp")
    with tmp.open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction="ignore"); writer.writeheader(); writer.writerows(rows)
    os.replace(tmp,target)
def _write_json(path: Path, value: Any, *, sort_keys: bool = True) -> None:
    target=REPO/path; target.parent.mkdir(parents=True,exist_ok=True); tmp=target.with_name(target.name+".tmp"); tmp.write_text(json.dumps(value,indent=2,sort_keys=sort_keys)+"\n",encoding="utf-8"); os.replace(tmp,target)
def _actual_rows(path: str) -> list[dict[str, str]]: return _csv(Path(path))
def _paths(root: str) -> dict[str, str]:
    base=Path(root); return {"protein_atom_table_path":(base/"protein_atom_table.csv").as_posix(),"ligand_atom_table_path":(base/"ligand_atom_table.csv").as_posix(),"pocket_atom_table_path":(base/"pocket_atom_table.csv").as_posix(),"covalent_event_table_path":(base/"covalent_event_table.csv").as_posix(),"ligand_residue_atom_pair_table_path":(base/"ligand_residue_atom_pair_table.csv").as_posix(),"sample_preparation_audit_path":(base/"sample_preparation_audit.csv").as_posix()}


def _preconditions(am_manifest: dict[str, Any], execution: list[dict[str, str]], inventory: list[dict[str, str]], trace: list[dict[str, str]], quality: list[dict[str, str]], failures: list[dict[str, str]], existing: list[dict[str, str]]) -> list[dict[str, Any]]:
    am_json=_json(AM/"covapie_batch_sample_preparation_execution_manifest.json"); inv_json=_json(AM/"covapie_batch_sample_preparation_sample_inventory.json")
    expected_ids=[f"CYS_SG_SAMPLE_INDEX_{i:06d}" for i in range(1,4)]
    checks={
      "step14am_manifest_valid":am_manifest.get("stage")=="covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0" and all(am_manifest.get(k) is True for k in ["all_checks_passed","all_preconditions_passed","all_samples_passed","all_safety_passed"]),
      "step14am_execution_results":(am_manifest.get("sample_execution_count"),am_manifest.get("sample_preparation_passed_count"),am_manifest.get("sample_preparation_failed_count"),am_manifest.get("embedded_qa_passed_count"),am_manifest.get("embedded_qa_failed_count"),am_manifest.get("batch_failure_count"))==(8,8,0,8,0,0),
      "failure_sentinel":len(failures)==1 and failures[0].get("failure_id")=="NO_BATCH_SAMPLE_PREPARATION_FAILURES",
      "execution_csv_json_consistent":len(execution)==len(am_json)==8 and [r["sample_execution_id"] for r in execution]==[r["sample_execution_id"] for r in am_json],
      "inventory_csv_json_consistent":len(inventory)==len(inv_json)==8 and [r["sample_execution_id"] for r in inventory]==[r["sample_execution_id"] for r in inv_json],
      "traceability_and_quality_passed":len(trace)==len(quality)==8 and all(r["traceability_audit_passed"]=="True" for r in trace) and all(r["quality_audit_passed"]=="True" for r in quality),
      "sample_roots_and_tables_exist":len(execution)==8 and all(all((REPO/p).is_file() for p in _paths(r["sample_artifact_root"]).values()) for r in execution),
      "existing_index_schema_and_namespace":len(existing)==3 and list(existing[0])==SAMPLE_INDEX_FIELDS and [r["sample_index_row_id"] for r in existing]==expected_ids,
      "existing_index_hashes_unchanged":all(_sha(p)==h for p,h in EXISTING_HASHES.items()),
      "metadata_hash_unchanged":_sha(META)=="c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365" and not _changed([str(META)]),
      "prior_artifacts_unchanged":not _changed([str(AM),str(AL),str(AK),str(EXISTING_CSV),str(EXISTING_JSON)]),
      "raw_untracked_unstaged":not _git(["ls-files",str(RAW)]).stdout.strip() and not _git(["diff","--cached","--name-only","--",str(RAW)]).stdout.strip(),
      "protected_sources_clean":not _changed(["equivariant_diffusion/","lightning_modules.py","dataset.py","data/prepare_crossdocked.py"]),
      "staged_empty":not _git(["diff","--cached","--name-only"]).stdout.strip(),
      "canonical_masks_preserved":CANONICAL_MASK_TASK_NAMES==["warhead_only","linker_plus_warhead","scaffold_plus_warhead","scaffold_only","scaffold_plus_linker_plus_warhead"] and CANONICAL_MASK_TASK_ALIASES==["A","B","B2","B3","C"],
    }
    return [{"precondition_item":k,"artifact_or_check":"embedded_read_only_check","expected_status":True,"observed_status":v,"precondition_passed":v,"blocking_reasons":"" if v else k} for k,v in checks.items()]


def _materialize(execution: list[dict[str,str]], inventory: list[dict[str,str]]) -> tuple[list[dict[str,Any]],list[dict[str,Any]],list[str]]:
    inv={(r["pdb_id"],r["expected_het_id"]):r for r in inventory}; index=[]; details=[]
    blockers=[]
    for rank,(pdb,het,atom) in enumerate(PAIRS,4):
        source=next((r for r in execution if (r["pdb_id"],r["expected_het_id"])==(pdb,het)),None)
        if source is None:
            blockers.append(f"{pdb}/{het}:missing_execution_source_row"); continue
        if (pdb,het) not in inv:
            blockers.append(f"{pdb}/{het}:missing_inventory_source_row"); continue
        paths=_paths(source["sample_artifact_root"])
        missing=[path for path in paths.values() if not (REPO/path).is_file()]
        if missing:
            blockers.extend(f"{pdb}/{het}:missing_source_table:{path}" for path in missing); continue
        tables={key:_actual_rows(path) for key,path in paths.items()}
        event=tables["covalent_event_table_path"][0] if len(tables["covalent_event_table_path"])==1 else {}; pair=tables["ligand_residue_atom_pair_table_path"][0] if len(tables["ligand_residue_atom_pair_table_path"])==1 else {}
        counts={"protein_atom_count":len(tables["protein_atom_table_path"]),"ligand_atom_count":len(tables["ligand_atom_table_path"]),"pocket_atom_count":len(tables["pocket_atom_table_path"]),"covalent_event_count":len(tables["covalent_event_table_path"]),"ligand_residue_atom_pair_count":len(tables["ligand_residue_atom_pair_table_path"])}
        row={"sample_index_row_id":f"CYS_SG_SAMPLE_INDEX_{rank:06d}","sample_preparation_input_id":source["sample_preparation_input_id"],"sample_execution_id":source["sample_execution_id"],"sample_qa_id":f"CYS_SG_EXPANSION_EMBEDDED_QA_{rank-3:06d}","pdb_id":pdb,"expected_het_id":het,"sample_artifact_root":source["sample_artifact_root"],**paths,**counts,"covalent_residue_name":event.get("residue_comp_id",""),"covalent_residue_chain_id":event.get("residue_auth_asym_id","") or event.get("residue_label_asym_id",""),"covalent_residue_index":event.get("residue_auth_seq_id","") or event.get("residue_label_seq_id",""),"covalent_residue_atom_name":event.get("residue_atom_name",""),"ligand_comp_id":event.get("ligand_comp_id",""),"ligand_covalent_atom_name":event.get("ligand_atom_name",""),"covalent_bond_atom_pair":event.get("covalent_bond_atom_pair",""),"conn_id":event.get("conn_id",""),"conn_type_id":event.get("conn_type_id",""),"bond_distance_angstrom":float(pair.get("bond_distance_angstrom","0") or 0),"sample_index_status":"sample_index_materialized_from_qa_passed_sample","eligible_for_final_dataset_design":False,"ready_for_training_current_step":False,"feature_semantics_audit_required_before_training":True,"leakage_split_design_required_before_training":True}
        index.append(row); details.append({"source":source,"inventory":inv[(pdb,het)],"tables":tables,"event":event,"pair":pair,"expected_atom":atom})
    return index,details,blockers


def _json_rows(rows: list[dict[str,Any]]) -> list[dict[str,Any]]: return [{field:row[field] for field in SAMPLE_INDEX_FIELDS} for row in rows]
def normalize_csv_index_rows_for_json_comparison(rows: list[dict[str,str]]) -> list[dict[str,Any]]:
    """Convert CSV strings into the canonical JSON value types before comparison."""
    normalized=[]
    for row in rows:
        normalized.append({field:(int(row[field]) if field in INT_FIELDS else float(row[field]) if field=="bond_distance_angstrom" else _bool(row[field]) if field in BOOL_FIELDS else row[field]) for field in SAMPLE_INDEX_FIELDS})
    return normalized
def _schema_rows(rows: list[dict[str,Any]], csv_columns: list[str], json_rows: list[dict[str,Any]]) -> list[dict[str,Any]]:
    checks=[]
    for number,field in enumerate(SAMPLE_INDEX_FIELDS,1):
        kind="boolean" if field in BOOL_FIELDS else "integer" if field in INT_FIELDS else "number" if field=="bond_distance_angstrom" else "string"
        csv_present=field in csv_columns; json_present=bool(json_rows) and all(field in r for r in json_rows); non_null=bool(rows) and all(r[field] not in ("",None) for r in rows)
        typed=bool(rows) and all(isinstance(r[field],bool) if kind=="boolean" else isinstance(r[field],int) and not isinstance(r[field],bool) if kind=="integer" else isinstance(r[field],float) if kind=="number" else isinstance(r[field],str) for r in rows)
        semantic=len(rows)==8
        if field=="sample_index_row_id": semantic=[r[field] for r in rows]==[f"CYS_SG_SAMPLE_INDEX_{i:06d}" for i in range(4,12)]
        elif field in INT_FIELDS: semantic=all(r[field]>0 if field not in {"covalent_event_count","ligand_residue_atom_pair_count"} else r[field]==1 for r in rows)
        elif field=="covalent_residue_name": semantic=all(r[field]=="CYS" for r in rows)
        elif field in {"covalent_residue_chain_id","covalent_residue_index","conn_id","ligand_covalent_atom_name"}: semantic=all(r[field] not in ("",None) for r in rows)
        elif field=="ligand_comp_id": semantic=all(r[field]==r["expected_het_id"] for r in rows)
        elif field=="covalent_residue_atom_name": semantic=all(r[field]=="SG" for r in rows)
        elif field=="covalent_bond_atom_pair": semantic=all(r[field]=="SG--"+r["ligand_covalent_atom_name"] for r in rows)
        elif field=="conn_type_id": semantic=all(r[field]=="covale" for r in rows)
        elif field=="bond_distance_angstrom": semantic=all(0<r[field]<=3 for r in rows)
        elif field=="sample_index_status": semantic=all(r[field]=="sample_index_materialized_from_qa_passed_sample" for r in rows)
        elif field=="sample_qa_id": semantic=[r[field] for r in rows]==[f"CYS_SG_EXPANSION_EMBEDDED_QA_{i:06d}" for i in range(1,9)]
        elif field in {"pdb_id","expected_het_id"}: semantic=[(r["pdb_id"],r["expected_het_id"]) for r in rows]==[(p,h) for p,h,_ in PAIRS]
        elif field in BOOL_FIELDS: semantic=all(r[field] is (field in {"feature_semantics_audit_required_before_training","leakage_split_design_required_before_training"}) for r in rows)
        elif field.endswith("_path"): semantic=all((REPO/r[field]).is_file() for r in rows)
        passed=csv_present and json_present and non_null and typed and semantic
        checks.append({"schema_validation_id":f"SCHEMA_{number:06d}","sample_index_field":field,"expected_data_type":kind,"csv_column_present":csv_present,"json_field_present_all_rows":json_present,"non_null_rule_passed":non_null,"data_type_validation_passed":typed,"semantic_validation_passed":semantic,"schema_validation_status":"passed" if passed else "failed","blocking_reasons":"" if passed else field})
    return checks


def _trace_rows(rows: list[dict[str,Any]], details: list[dict[str,Any]], execution: list[dict[str,str]], inventory: list[dict[str,str]], trace: list[dict[str,str]], quality: list[dict[str,str]]) -> list[dict[str,Any]]:
    result=[]
    for number,(row,detail) in enumerate(zip(rows,details),1):
        source,tables,event,pair=detail["source"],detail["tables"],detail["event"],detail["pair"]
        actual={"protein_atom_count":len(tables["protein_atom_table_path"]),"ligand_atom_count":len(tables["ligand_atom_table_path"]),"pocket_atom_count":len(tables["pocket_atom_table_path"]),"covalent_event_count":len(tables["covalent_event_table_path"]),"ligand_residue_atom_pair_count":len(tables["ligand_residue_atom_pair_table_path"])}
        audit=tables["sample_preparation_audit_path"]
        checks={"execution_manifest_row_found":any(r["sample_execution_id"]==row["sample_execution_id"] for r in execution),"sample_inventory_row_found":any((r["pdb_id"],r["expected_het_id"])==(row["pdb_id"],row["expected_het_id"]) for r in inventory),"traceability_source_row_found":any(r["sample_execution_id"]==row["sample_execution_id"] and r["traceability_audit_passed"]=="True" for r in trace),"quality_source_row_found":any(r["sample_execution_id"]==row["sample_execution_id"] and r["quality_audit_passed"]=="True" for r in quality),"all_six_artifact_paths_exist":all((REPO/row[field]).is_file() for field in rpath_fields()),"actual_table_counts_match_index":all(row[k]==v for k,v in actual.items()),"execution_counts_match_index":all(int(source[k])==row[k] for k in actual),"event_table_single_row":len(tables["covalent_event_table_path"])==1,"pair_table_single_row":len(tables["ligand_residue_atom_pair_table_path"])==1,"event_identity_matches_index":event.get("conn_id")==row["conn_id"] and event.get("ligand_comp_id")==row["ligand_comp_id"],"pair_identity_matches_index":pair.get("ligand_atom_name")==row["ligand_covalent_atom_name"],"event_pair_dynamic_atom_names_consistent":event.get("ligand_atom_name")==pair.get("ligand_atom_name")==detail["expected_atom"] and event.get("covalent_bond_atom_pair")==pair.get("covalent_bond_atom_pair")==row["covalent_bond_atom_pair"],"bond_distance_matches_pair_table":str(row["bond_distance_angstrom"])==str(float(pair.get("bond_distance_angstrom","0") or 0)),"embedded_sample_audit_13_of_13_passed":len(audit)==13 and all(r["audit_passed"]=="True" for r in audit)}
        passed=all(checks.values()); result.append({"row_traceability_id":f"TRACE_{number:06d}","sample_index_row_id":row["sample_index_row_id"],"sample_preparation_input_id":row["sample_preparation_input_id"],"sample_execution_id":row["sample_execution_id"],"sample_qa_id":row["sample_qa_id"],"pdb_id":row["pdb_id"],"expected_het_id":row["expected_het_id"],**checks,"row_traceability_status":"passed" if passed else "failed","blocking_reasons":"" if passed else ";".join(k for k,v in checks.items() if not v)})
    return result


def rpath_fields() -> list[str]: return [f for f in SAMPLE_INDEX_FIELDS if f.endswith("_path")]
def _collision_rows(rows: list[dict[str,Any]], existing: list[dict[str,str]]) -> list[dict[str,Any]]:
    existing_ids={r["sample_index_row_id"] for r in existing}; existing_pairs={(r["pdb_id"],r["expected_het_id"]) for r in existing}; ids=[r["sample_index_row_id"] for r in rows]; pairs=[(r["pdb_id"],r["expected_het_id"]) for r in rows]; result=[]
    for number,row in enumerate(rows,1):
        checks={"row_id_collision_with_existing_index":row["sample_index_row_id"] in existing_ids,"pdb_het_collision_with_existing_index":(row["pdb_id"],row["expected_het_id"]) in existing_pairs,"duplicate_row_id_within_expansion_batch":ids.count(row["sample_index_row_id"])>1,"duplicate_pdb_het_within_expansion_batch":pairs.count((row["pdb_id"],row["expected_het_id"]))>1,"namespace_continuity_passed":row["sample_index_row_id"]==f"CYS_SG_SAMPLE_INDEX_{number+3:06d}"}
        passed=not any(checks[k] for k in checks if k!="namespace_continuity_passed") and checks["namespace_continuity_passed"]
        result.append({"collision_audit_id":f"COLLISION_{number:06d}","sample_index_row_id":row["sample_index_row_id"],"pdb_id":row["pdb_id"],"expected_het_id":row["expected_het_id"],**checks,"collision_audit_passed":passed,"blocking_reasons":"" if passed else ";".join(k for k,v in checks.items() if (not v if k=="namespace_continuity_passed" else v))})
    return result


def _safety_rows(observed: dict[str,bool]) -> list[dict[str,Any]]:
    if set(observed)!=set(SAFETY_EXPECTED): raise ValueError("safety observation mapping differs from expected mapping")
    return [{"safety_item":k,"required_status":v,"observed_status":observed[k],"safety_passed":observed[k]==v,"blocking_reasons":"" if observed[k]==v else k} for k,v in SAFETY_EXPECTED.items()]
def _ready(pre:bool, rows:bool, schema:bool, trace:bool, collision:bool, issues:bool, safety:bool) -> bool: return all((pre,rows,schema,trace,collision,issues,safety))


def run() -> dict[str,Any]:
    am_manifest=_json(AM/"covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_manifest.json")
    execution=_csv(AM/"covapie_batch_sample_preparation_execution_manifest.csv"); inventory=_csv(AM/"covapie_batch_sample_preparation_sample_inventory.csv"); source_trace=_csv(AM/"covapie_batch_sample_preparation_traceability_audit.csv"); quality=_csv(AM/"covapie_batch_sample_preparation_quality_audit.csv"); failures=_csv(AM/"covapie_batch_sample_preparation_failure_inventory.csv"); existing=_csv(EXISTING_CSV)
    pre=_preconditions(am_manifest,execution,inventory,source_trace,quality,failures,existing); rows,details,source_blockers=_materialize(execution,inventory)
    _write_csv(INDEX_CSV,SAMPLE_INDEX_FIELDS,rows); _write_json(INDEX_JSON,_json_rows(rows),sort_keys=False)
    with (REPO/INDEX_CSV).open(newline="",encoding="utf-8") as handle: csv_reader=csv.DictReader(handle); csv_columns=csv_reader.fieldnames or []; written_csv=list(csv_reader)
    written_json=_json(INDEX_JSON); csv_json_consistent=normalize_csv_index_rows_for_json_comparison(written_csv)==written_json
    schema=_schema_rows(rows,csv_columns,written_json); trace=_trace_rows(rows,details,execution,inventory,source_trace,quality) if len(rows)==8 else [] ; collision=_collision_rows(rows,existing)
    issues=[]
    all_pre=all(_bool(r["precondition_passed"]) for r in pre); all_rows=len(rows)==8; all_schema=all(r["schema_validation_status"]=="passed" for r in schema); all_trace=all(r["row_traceability_status"]=="passed" for r in trace); all_collision=all(_bool(r["collision_audit_passed"]) for r in collision)
    if source_blockers or not (all_rows and all_schema and all_trace and all_collision and csv_json_consistent):
        issues=[{"issue_id":"EXPANSION_BATCH_SAMPLE_INDEX_MATERIALIZATION_ISSUE","issue_scope":"expansion_batch_000001","sample_index_row_id":"","pdb_id":"","expected_het_id":"","issue_severity":"blocking","issue_type":"embedded_validation_failed","issue_description":"One or more embedded index validations failed.","issue_status":"blocked"}]
    else: issues=[{"issue_id":"NO_EXPANSION_BATCH_SAMPLE_INDEX_MATERIALIZATION_ISSUES","issue_scope":"expansion_batch_000001","sample_index_row_id":"","pdb_id":"","expected_het_id":"","issue_severity":"none","issue_type":"no_issues","issue_description":"No expansion batch sample-index materialization issues detected.","issue_status":"passed"}]
    output_files=[p for p in (REPO/OUT).rglob("*") if p.is_file()]
    observed={"network_access_used_current_step":False,"download_attempted_current_step":False,"raw_mmcif_read_current_step":False,"struct_conn_parsed_current_step":False,"atom_site_parsed_current_step":False,"raw_files_modified":False,"raw_files_tracked":bool(_git(["ls-files",str(RAW)]).stdout.strip()),"raw_files_staged":bool(_git(["diff","--cached","--name-only","--",str(RAW)]).stdout.strip()),"step14am_artifacts_unchanged":not _changed([str(AM)]),"step14al_artifacts_unchanged":not _changed([str(AL)]),"step14ak_artifacts_unchanged":not _changed([str(AK)]),"existing_sample_index_files_unchanged":not _changed([str(EXISTING_CSV),str(EXISTING_JSON)]) and all(_sha(p)==h for p,h in EXISTING_HASHES.items()),"metadata_csv_unchanged":not _changed([str(META)]),"expansion_batch_sample_index_csv_written":(REPO/INDEX_CSV).is_file(),"expansion_batch_sample_index_json_written":(REPO/INDEX_JSON).is_file(),"existing_sample_index_modified":_changed([str(EXISTING_CSV),str(EXISTING_JSON)]) or any(_sha(p)!=h for p,h in EXISTING_HASHES.items()),"combined_sample_index_written":any("combined" in p.name.lower() or "merged" in p.name.lower() for p in output_files),"standalone_sample_index_qa_gate_created":any("standalone" in p.name.lower() and "qa" in p.name.lower() for p in output_files),"embedded_sample_index_qa_performed":True,"split_assignments_written":False,"leakage_matrix_written":False,"final_dataset_written":False,"actual_dataloader_artifacts_written":False,"training_artifacts_written":False,"part_or_tmp_files_remaining":any(p.suffix in {".tmp",".part"} for p in output_files),"protected_source_diff_empty":not _changed(["equivariant_diffusion/","lightning_modules.py"]),"original_dataloader_diff_empty":not _changed(["dataset.py","data/prepare_crossdocked.py"]),"torch_imported":False,"numpy_imported":False,"rdkit_used":False,"biopython_used":False,"gemmi_used":False,"requests_used":False}
    safety=_safety_rows(observed); all_safety=all(_bool(r["safety_passed"]) for r in safety); ready=_ready(all_pre,all_rows and csv_json_consistent,all_schema,all_trace,all_collision,len(issues)==1 and issues[0]["issue_status"]=="passed",all_safety)
    blockers=[r["precondition_item"] for r in pre if not _bool(r["precondition_passed"])]+source_blockers+(["csv_json_consistency_failed"] if not csv_json_consistent else [])+[r["sample_index_field"] for r in schema if r["schema_validation_status"]!="passed"]+[r["sample_index_row_id"] for r in trace if r["row_traceability_status"]!="passed"]+[r["sample_index_row_id"] for r in collision if not _bool(r["collision_audit_passed"])]+[r["issue_id"] for r in issues if r["issue_status"]!="passed"]+[r["safety_item"] for r in safety if not _bool(r["safety_passed"])]
    blockers=list(dict.fromkeys(blockers))
    manifest={"stage":STAGE,"step_label":"Step 14AN","previous_stage":"covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0","project_name":"CovaPIE","input_sample_count":8,"input_embedded_qa_passed_count":8,"input_batch_failure_count":0,"existing_sample_index_row_count":len(existing),"existing_sample_index_schema_field_count":len(SAMPLE_INDEX_FIELDS),"expansion_batch_sample_index_row_count":len(rows),"expansion_batch_sample_index_schema_field_count":len(SAMPLE_INDEX_FIELDS),"future_combined_sample_count":len(existing)+len(rows),"expansion_batch_sample_index_csv_json_consistent":csv_json_consistent,"expansion_batch_sample_index_written_current_step":True,"expansion_batch_sample_index_csv_written":observed["expansion_batch_sample_index_csv_written"],"expansion_batch_sample_index_json_written":observed["expansion_batch_sample_index_json_written"],"expansion_batch_sample_index_row_ids":[r["sample_index_row_id"] for r in rows],"accepted_pdb_het_pairs":[f"{p}/{h}" for p,h,_ in PAIRS],"covalent_bond_atom_pairs":list(dict.fromkeys(r["covalent_bond_atom_pair"] for r in rows)),"schema_validation_count":len(schema),"schema_validation_passed_count":sum(r["schema_validation_status"]=="passed" for r in schema),"row_traceability_count":len(trace),"row_traceability_passed_count":sum(r["row_traceability_status"]=="passed" for r in trace),"collision_audit_count":len(collision),"collision_audit_passed_count":sum(_bool(r["collision_audit_passed"]) for r in collision),"materialization_issue_count":0 if issues[0]["issue_status"]=="passed" else len(issues),"embedded_index_qa_count":len(rows),"embedded_index_qa_passed_count":sum(r["row_traceability_status"]=="passed" for r in trace),"expansion_batch_sample_index_csv_sha256":_sha(INDEX_CSV),"expansion_batch_sample_index_json_sha256":_sha(INDEX_JSON),"existing_sample_index_csv_sha256":_sha(EXISTING_CSV),"existing_sample_index_json_sha256":_sha(EXISTING_JSON),"confirmed_new_independent_group_count_current_step":0,"ligand_graph_independence_status":"pending_canonical_graph_hash_and_scaffold_review","protein_sequence_independence_status":"pending_accession_and_sequence_cluster","eligible_for_final_dataset_design_count_current_step":0,"ready_for_training_candidate_count_current_step":0,**observed,"ready_for_covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke":ready,"ready_for_covapie_unified_sample_index_merge_smoke":False,"ready_for_covapie_split_materialization_smoke":False,"ready_for_covapie_final_dataset_materialization_smoke":False,"ready_for_training":False,"ready_to_train_now":False,"feature_semantics_known_for_training":False,"unknown_atom_feature_policy_finalized_for_training":False,"feature_semantics_audit_required_before_training":True,"leakage_split_design_required_before_training":True,"canonical_mask_task_names":CANONICAL_MASK_TASK_NAMES,"canonical_mask_task_aliases":CANONICAL_MASK_TASK_ALIASES,"b3_scaffold_only_included":True,"no_extra_mask_tasks_added":True,"all_preconditions_passed":all_pre,"all_rows_passed":all_rows and csv_json_consistent,"all_schema_checks_passed":all_schema,"all_traceability_checks_passed":all_trace,"all_collision_checks_passed":all_collision,"all_safety_checks_passed":all_safety,"recommended_next_step":"covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke" if ready else "covapie_independent_group_expansion_batch_sample_index_materialization_issue_resolution","all_checks_passed":ready,"blocking_reasons":blockers}
    _write_csv(PRE,PRE_COLUMNS,pre); _write_csv(SCHEMA,SCHEMA_COLUMNS,schema); _write_csv(TRACE,TRACE_COLUMNS,trace); _write_csv(COLLISION,COLLISION_COLUMNS,collision); _write_csv(ISSUES,ISSUE_COLUMNS,issues); _write_csv(SAFETY,SAFETY_COLUMNS,safety); _write_json(MANIFEST,manifest)
    return {"manifest":manifest,"index_rows":rows,"schema":schema,"trace":trace,"collision":collision,"safety":safety}
