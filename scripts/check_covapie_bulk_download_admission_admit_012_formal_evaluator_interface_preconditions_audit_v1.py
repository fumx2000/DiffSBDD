#!/usr/bin/env python3
"""Independent semantic checker for the ADMIT_012 precondition audit."""
from __future__ import annotations
import ast, csv, hashlib, io, json, os, stat, subprocess
from pathlib import Path
from typing import Any

REPO_ROOT=Path(__file__).resolve().parents[1]
BASE="97128a674b9ffc0579c67fd1ed2acf30d4cedfa5"
SUBJECT="add CovaPIE unified dispatch runtime with ADMIT_001 to ADMIT_011 v1"
STAGE="covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1"
OUTPUT_ROOT=Path("data/derived/covalent_small")/STAGE
FIELDS=("download_result_status","observed_http_status","observed_content_length_bytes","observed_sha256")
COUNT=129; PATH_SHA="f0ed67bbb346ff5e900c532b2188b90a527291e1f3b704a60454fd33ed938b2b"; PAIR_SHA="97a0bbb81314e7213e5999d56278d590d5073b9e1ce0e0a9e03458934aae2fab"
FILES=("covapie_admit_012_formal_evaluator_precondition_matrix.csv","covapie_admit_012_field_occurrence_inventory.csv","covapie_admit_012_observed_value_inventory.csv","covapie_admit_012_source_boundary_audit.csv","covapie_admit_012_issue_readiness_inventory.csv","covapie_admit_012_formal_evaluator_preconditions_manifest.json")
PRE,OCC,OBS,SRC,ISSUE,MANIFEST=FILES
HEADERS={PRE:("precondition_order","precondition_id","precondition_group","precondition_subject","expected_contract","observed_evidence","completeness_status","implementation_blocking","blocking_reason","precondition_passed"),OCC:("occurrence_order","field_name","relative_path","file_role","occurrence_kind","declaring_or_referencing","phase_claim","type_claim","validation_claim","source_authority_level","current_contract_effect","occurrence_passed"),OBS:("value_order","field_name","source_path","representation","source_kind","real_observed_value","synthetic_example","placeholder","schema_only","produced_by_download_execution","admissible_as_semantic_evidence","notes"),SRC:("source_order","source_relative_path","source_kind","base_tree_mode","base_tree_sha256","filesystem_sha256","tracked_regular_non_symlink","parent_chain_verified","pinned_fd_read","triple_sha256_passed","source_boundary_passed")}
RULE=Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv")
SCHEMA=Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_schema_contract.csv")
EXEC=Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_rule_executability_matrix.csv")
FIELD=Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_field_semantics_matrix.csv")
CTX=Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv")
RUNTIME=Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1/covapie_admit_001_to_011_runtime_issue_inventory.csv")
REQUIRED=tuple(Path(value) for value in (
 "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011.py","scripts/check_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1.py","tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1.py","docs/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1_summary.md",
 "src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_design_gate.py","scripts/check_covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1.py","tests/test_covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1.py","docs/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1_summary.md",
 "src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate.py","scripts/check_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1.py","tests/test_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1.py","docs/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1_summary.md",
 "src/covalent_ext/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit.py","scripts/check_covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1.py","tests/test_covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1.py","docs/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1_summary.md",
 "src/covalent_ext/covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit.py","scripts/check_covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit_v1.py","tests/test_covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit_v1.py","docs/covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit_v1_summary.md",
 RULE.as_posix(),SCHEMA.as_posix(),EXEC.as_posix(),FIELD.as_posix(),CTX.as_posix(),RUNTIME.as_posix()))
FROZEN_SHA={
 PRE:"c667c5f195a1d834672564835380896553339833041d17cc2f689db23f9d319f",
 OCC:"12f09454bc19f37c57101da32c9a349a7fa1deb72b6cc98bbb1199fce5c2712f",
 OBS:"dc47865f2f176b9e37aac0caf71fdacee1275eece19351cb69d31f64ad14104f",
 SRC:"4272d31320a9b32e503d4fda49df5c21778238b46e5f2b51bb1dbbb1a3d5ce5e",
 ISSUE:"5ebe9332137bfa9c7804c82041ff695b3379ba505a5eb006fa5c7798510e8529",
 MANIFEST:"712caa27add06784db5cfe2e59a65952ae4b1c5a369ff43772d8e4f95b18c4de",
}

def git(args, text=True): return subprocess.run(["git",*args],cwd=REPO_ROOT,capture_output=True,text=text,check=False)
def csv_bytes(header, rows):
 s=io.StringIO(newline=""); w=csv.DictWriter(s,fieldnames=header,lineterminator="\n",extrasaction="raise"); w.writeheader();w.writerows(rows);return s.getvalue().encode()
def safe(p): return not p.is_absolute() and bool(p.parts) and ".." not in p.parts and p.parts[:2]!=("data","raw") and p.parts[0]!="checkpoints"
def kind(p): return "python_source" if p.suffix==".py" else "committed_csv" if p.suffix==".csv" else "committed_manifest" if p.suffix==".json" else "tracked_text"
def paths():
 r=git(["grep","-l","-I",*sum((["-e",f] for f in FIELDS),[]),BASE,"--",":!data/raw/**",":!checkpoints/**"]); prefix=BASE+":"
 assert r.returncode in (0,1) and all(line.startswith(prefix) for line in r.stdout.splitlines() if line)
 values=tuple(sorted({Path(x.removeprefix(prefix)) for x in r.stdout.splitlines() if x}|set(REQUIRED),key=lambda x:x.as_posix()))
 assert len(values)==COUNT and all(safe(p) and STAGE not in p.as_posix() for p in values)
 assert hashlib.sha256(json.dumps([p.as_posix() for p in values],separators=(",",":")).encode()).hexdigest()==PATH_SHA
 return values
def pinned(p):
 a=REPO_ROOT/p; before=os.lstat(a); fd=os.open(a,os.O_RDONLY|getattr(os,"O_NOFOLLOW",0)|getattr(os,"O_CLOEXEC",0))
 try:
  one=os.fstat(fd); data=b""
  while True:
   chunk=os.read(fd,1048576)
   if not chunk: break
   data+=chunk
  two=os.fstat(fd); after=os.lstat(a)
 finally: os.close(fd)
 assert (before.st_dev,before.st_ino,before.st_mode)==(one.st_dev,one.st_ino,one.st_mode)==(two.st_dev,two.st_ino,two.st_mode)==(after.st_dev,after.st_ino,after.st_mode)
 return data
def snapshot():
 root=os.lstat(REPO_ROOT); assert stat.S_ISDIR(root.st_mode) and not stat.S_ISLNK(root.st_mode) and REPO_ROOT.resolve()==REPO_ROOT
 s=git(["show","-s","--format=%s",BASE]); assert s.returncode==0 and s.stdout.strip()==SUBJECT
 a=git(["merge-base","--is-ancestor",BASE,"HEAD"]); assert a.returncode==0
 records=[]
 for p in paths():
  a=REPO_ROOT/p; cur=a.parent
  while cur!=REPO_ROOT:
   item=os.lstat(cur); assert stat.S_ISDIR(item.st_mode) and not stat.S_ISLNK(item.st_mode);cur=cur.parent
  leaf=os.lstat(a); t=git(["ls-tree",BASE,"--",p.as_posix()]); l=git(["ls-files","--error-unmatch","--",p.as_posix()]); head,sep,name=t.stdout.partition("\t"); bits=head.split()
  assert l.returncode==t.returncode==0 and l.stdout.splitlines()==[p.as_posix()] and sep and name.strip()==p.as_posix() and len(bits)==3 and bits[0] in {"100644","100755"} and bits[1]=="blob" and stat.S_ISREG(leaf.st_mode) and not stat.S_ISLNK(leaf.st_mode) and a.resolve()==a
  records.append((p,bits[0]))
 out=[];pairs=[]
 for p,mode in records:
  base=git(["show",f"{BASE}:{p.as_posix()}"],False); data=pinned(p); digest=hashlib.sha256(data).hexdigest();assert base.returncode==0 and hashlib.sha256(base.stdout).hexdigest()==digest;pairs.append([p.as_posix(),digest]);out.append((p,data,digest,mode))
 assert hashlib.sha256(json.dumps(pairs,separators=(",",":")).encode()).hexdigest()==PAIR_SHA
 return out
def get(records,p): return next(x for x in records if x[0]==p)
def rows(records,p): return list(csv.DictReader(io.StringIO(get(records,p)[1].decode(),newline="")))
def preconditions():
 specs=(("identity","rule identity","ADMIT_012 exact","registry exact",1,""),("identity","phase","post_download","registry exact",1,""),("identity","required status","exact status","registry exact",1,""),("identity","blocking reason","exact blocker","registry exact",1,""),("field","Exact4 identity/order","frozen ordered fields","Step14AU-A exact",1,""),("routing","future result producer","download execution result","field matrix exact",1,""),("routing","candidate versus result envelope","future consumer envelope frozen","candidate false but envelope allocation absent",0,"ADMIT_012_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED"),("type","download_result_status type","exact built-in str","no exact type contract",0,"DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED"),("type","download_result_status vocabulary","allowed vocabulary","context exact=false",0,"DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED"),("type","observed_http_status type/range","exact int, bool rejection, range","no exact contract",0,"DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED"),("type","content length type/range","exact int, bool rejection, range","no exact contract",0,"DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED"),("type","SHA256 grammar/case","exact grammar and case policy","no exact contract",0,"DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED"),("validation","presence semantics","defined key/value/type meaning","no exact contract",0,"ADMIT_012_PRESENCE_SEMANTICS_UNRESOLVED"),("validation","multi-invalid precedence","deterministic reason order","no exact contract",0,"ADMIT_012_MULTI_INVALID_PRECEDENCE_UNRESOLVED"),("interface","public standalone signature","scalar/object/mapping resolved","routing/validation unresolved",0,"ADMIT_012_STANDALONE_SIGNATURE_UNRESOLVED"),("interface","Exact10 result contract","result object/shape resolved","not designed",0,"ADMIT_012_RESULT_CONTRACT_UNRESOLVED"),("purity","pure in-memory","possible","Step14AU-A exact",1,""),("purity","no network/filesystem/raw","forbidden inside evaluator","network/filesystem false",1,""),("boundary","ADMIT_012/013 responsibility","presence versus fail-closed outcome","separate registry rules",1,""),("boundary","provider mapping required","not required inside evaluator","pure interface evidence",1,""),("authorization","real provider mapping","not validated","not authorized",1,""),("authorization","real download evaluation","not authorized","not authorized",1,""),("authorization","runtime integration","not authorized","Exact11 unchanged",1,""),("training","feature audit","still required before training","historical readiness",1,""))
 return [{"precondition_order":str(n),"precondition_id":f"PRE_{n:03d}","precondition_group":g,"precondition_subject":s,"expected_contract":e,"observed_evidence":o,"completeness_status":"complete" if ok else "incomplete","implementation_blocking":"false" if ok else "true","blocking_reason":b,"precondition_passed":str(bool(ok)).lower()} for n,(g,s,e,o,ok,b) in enumerate(specs,1)]
def role(p):
 x=p.as_posix()
 return "production_source" if x.startswith("src/") else "tests" if x.startswith("tests/") else "checker" if x.startswith("scripts/") else "docs" if x.startswith("docs/") else "manifest" if p.suffix==".json" else "candidate_schema" if "schema" in p.name else "runtime_envelope" if "runtime" in p.name else "derived_csv"
PRIMARY=frozenset((RULE,SCHEMA,EXEC,FIELD,CTX))
def occurrence(records):
 out=[]
 for p,data,digest,mode in records:
  for line in data.decode().splitlines():
   for field in FIELDS:
    if field in line:
     auth="primary_committed_contract" if p in PRIMARY else "historical_or_reference"; exact=line.startswith(field+",") or (field in line and "("+repr(field) in line); declares=auth=="primary_committed_contract" and exact
     out.append({"occurrence_order":str(len(out)+1),"field_name":field,"relative_path":p.as_posix(),"file_role":role(p),"occurrence_kind":"field_declaration" if declares else "field_reference","declaring_or_referencing":"declaring" if declares else "referencing","phase_claim":"post_download" if auth=="primary_committed_contract" and "post_download" in line else "unspecified_or_non_authoritative","type_claim":"not_exactly_defined","validation_claim":"incomplete" if auth=="primary_committed_contract" and ("false" in line.lower() or "UNRESOLVED" in line) else "reference_only","source_authority_level":auth,"current_contract_effect":"field_identity_or_lifecycle_authority" if auth=="primary_committed_contract" else "non_promoted_reference","occurrence_passed":"true"})
 return out
def walk_json(value, loc="$"):
 if isinstance(value,dict):
  for k,v in value.items():
   child=f"{loc}.{k}";
   if k in FIELDS: yield k,child,v
   yield from walk_json(v,child)
 elif isinstance(value,list):
  for i,v in enumerate(value): yield from walk_json(v,f"{loc}[{i}]")
def observed(records):
 out=[{"value_order":str(i),"field_name":f,"source_path":SCHEMA.as_posix(),"representation":"schema_field_declaration","source_kind":"schema_only","real_observed_value":"false","synthetic_example":"false","placeholder":"true","schema_only":"true","produced_by_download_execution":"false","admissible_as_semantic_evidence":"false","notes":"field identity only; no observed download result"} for i,f in enumerate(FIELDS,1)]
 for p,data,digest,mode in records:
  values=[]
  if p.suffix==".json": values=list(walk_json(json.loads(data.decode())))
  elif p.suffix==".csv":
   for n,row in enumerate(rows(records,p),1): values += [(f,f"row:{n}.{f}",row[f]) for f in FIELDS if f in row]
  elif p.suffix==".py":
   for node in ast.walk(ast.parse(data.decode())):
    if isinstance(node,ast.Dict):
     for k,v in zip(node.keys,node.values):
      if isinstance(k,ast.Constant) and k.value in FIELDS and isinstance(v,ast.Constant): values.append((k.value,f"ast:{node.lineno}",v.value))
  if p.parts[0]=="tests":
   present={f for f,_,_ in values}; values += [(f,"static_test_field_literal",f) for f in FIELDS if f in data.decode() and f not in present]
  for f,loc,v in values:
   test=p.parts[0]=="tests"; historic="real_covalent_pilot_download_integrity_gate" in p.as_posix(); attestation=f=="observed_sha256" and not test and not historic
   sk="test_fixture" if test else "historical_non_admit012_integrity_observation" if historic else "unrelated_source_attestation_hash" if attestation else "historical_non_admit012_integrity_observation"
   out.append({"value_order":str(len(out)+1),"field_name":f,"source_path":p.as_posix(),"representation":f"static_literal_or_value:{loc}","source_kind":sk,"real_observed_value":str(attestation).lower(),"synthetic_example":str(test).lower(),"placeholder":str(not test and not attestation and not historic).lower(),"schema_only":"false","produced_by_download_execution":"false","admissible_as_semantic_evidence":"false","notes":"static Python/test fixture; not production semantics" if test else "historical source-attestation digest, not download-result semantics" if attestation else "historical non-ADMIT_012 integrity evidence" if historic else "historical/reference value; not authorized ADMIT_012 execution"})
 return out
def source_rows(records): return [{"source_order":str(n),"source_relative_path":p.as_posix(),"source_kind":kind(p),"base_tree_mode":mode,"base_tree_sha256":d,"filesystem_sha256":d,"tracked_regular_non_symlink":"true","parent_chain_verified":"true","pinned_fd_read":"true","triple_sha256_passed":"true","source_boundary_passed":"true"} for n,(p,data,d,mode) in enumerate(records,1)]
def issues(records):
 out=rows(records,RUNTIME); header=tuple(out[0]); extra=(("ADMIT_012_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED","|".join(FIELDS)),("ADMIT_012_PRESENCE_SEMANTICS_UNRESOLVED","|".join(FIELDS)),("ADMIT_012_MULTI_INVALID_PRECEDENCE_UNRESOLVED","|".join(FIELDS)),("ADMIT_012_STANDALONE_SIGNATURE_UNRESOLVED",""),("ADMIT_012_RESULT_CONTRACT_UNRESOLVED",""))
 for issue,fields in extra: out.append({k:{"issue_id":issue,"issue_type":"implementation_semantics_gap","affected_fields":fields,"affected_rules":"ADMIT_012","severity":"blocking","status":"open","blocking_scope":"admission_evaluator_rule_logic","blocking_reason":issue,"issue_origin":STAGE,"integration_transition":"new_open","issue_count":"1"}.get(k,"") for k in header})
 return out
def readiness(): return {"unified_dispatch_runtime_with_admit_001_to_011_implemented":True,"admit_011_registered_in_engine":True,"admit_012_preconditions_audited":True,"feature_semantics_audit_required_before_training":True,"step12d_is_final_training_feature_contract":False,"admit_012_rule_logic_implemented":False,"evaluate_admit_012_implemented":False,"Admit012EvaluationResult_implemented":False,"admit_012_unified_adapter_contract_frozen":False,"admit_012_unified_adapter_implemented":False,"admit_012_registered_in_engine":False,"unified_dispatch_runtime_with_admit_001_to_012_implemented":False,"provider_mapping_validated":False,"real_provider_evaluation_ready":False,"ready_for_bulk_download_now":False,"combined_candidate_verdict_implemented":False,"ready_for_training":False,"admit_012_field_semantics_complete":False,"admit_012_routing_responsibility_resolved":False,"admit_012_validation_precedence_resolved":False,"ready_for_admit_012_standalone_evaluator_interface_implementation":False}
def expected():
 records=snapshot(); pc=preconditions();oc=occurrence(records);ob=observed(records);sr=source_rows(records);ir=issues(records); payload={PRE:csv_bytes(HEADERS[PRE],pc),OCC:csv_bytes(HEADERS[OCC],oc),OBS:csv_bytes(HEADERS[OBS],ob),SRC:csv_bytes(HEADERS[SRC],sr),ISSUE:csv_bytes(tuple(ir[0]),ir)}; hashes={n:hashlib.sha256(v).hexdigest() for n,v in payload.items()}; ready=readiness()
 manifest={"project":"CovaPIE","stage":STAGE,"base_commit":BASE,"base_subject":SUBJECT,"admission_rule_id":"ADMIT_012","admission_rule_name":"future_download_integrity_fields_required","evidence_source":"future_download_result","evaluation_phase":"post_download","required_status":"download_status_http_status_content_length_and_sha256_present","blocking_reason":"download_integrity_fields_missing","exact4_fields":list(FIELDS),"field_semantics":"incomplete","routing_responsibility":"unresolved","presence_semantics":"unresolved","multi_invalid_precedence":"unresolved","future_evaluator_pure_in_memory":True,"network_required_inside_evaluator":False,"raw_structure_required_inside_evaluator":False,"renameat2_policy":"RENAME_NOREPLACE_required;_EINVAL_fails_closed_without_os.replace_fallback","admit_012_013_boundary":"ADMIT_012_requires_integrity_field_contract;_ADMIT_013_retains_download_failure_fail_closed","source_count":COUNT,"source_path_list_sha256":PATH_SHA,"source_path_sha256_pairs_sha256":PAIR_SHA,"occurrence_row_count":len(oc),"occurrence_authority_counts":{k:sum(r["source_authority_level"]==k for r in oc) for k in ("primary_committed_contract","historical_or_reference")},"observed_value_row_count":len(ob),"observed_value_source_kind_counts":{k:sum(r["source_kind"]==k for r in ob) for k in sorted({r["source_kind"] for r in ob})},"authorized_admit_012_download_execution_count":0,"real_provider_mapping_validated":False,"recommended_next_step":"design_covapie_admit_012_download_integrity_field_contract_v1","step12d_status":"smoke_legality_only_not_final_training_feature_contract","readiness":ready,"safety":{"network":False,"filesystem":False,"raw":False,"provider_mapping":False,"real_download":False,"runtime_change":False,"training":False},"output_sha256":hashes,"all_checks_passed":True};manifest.update(ready);payload[MANIFEST]=(json.dumps(manifest,indent=2,sort_keys=True)+"\n").encode();return payload
def _identity(item): return item.st_dev,item.st_ino,item.st_mode
def _pinned_outputs(root):
 parent=root.parent; parent_identity=_identity(os.lstat(parent)); root_identity=_identity(os.lstat(root))
 assert root.is_dir() and not root.is_symlink() and {p.name for p in root.iterdir()}==set(FILES)
 root_fd=os.open(root,os.O_RDONLY|getattr(os,"O_DIRECTORY",0)|getattr(os,"O_NOFOLLOW",0)|getattr(os,"O_CLOEXEC",0))
 try:
  assert _identity(os.fstat(root_fd))==root_identity; result={}; frozen={}
  for name in FILES:
   leaf=os.lstat(root/name); assert stat.S_ISREG(leaf.st_mode) and not stat.S_ISLNK(leaf.st_mode); identity=_identity(leaf); frozen[name]=identity
   fd=os.open(name,os.O_RDONLY|getattr(os,"O_NOFOLLOW",0)|getattr(os,"O_CLOEXEC",0),dir_fd=root_fd)
   try:
    assert _identity(os.fstat(fd))==identity; data=b""
    while True:
     chunk=os.read(fd,1048576)
     if not chunk: break
     data+=chunk
    assert _identity(os.fstat(fd))==identity; result[name]=data
   finally: os.close(fd)
  assert _identity(os.lstat(parent))==parent_identity and _identity(os.fstat(root_fd))==root_identity and _identity(os.lstat(root))==root_identity and {p.name for p in root.iterdir()}==set(FILES)
  assert all(_identity(os.lstat(root/name))==frozen[name] for name in FILES)
  return result
 finally: os.close(root_fd)
def validate(root=REPO_ROOT/OUTPUT_ROOT,enforce_frozen_hashes=True):
 want=expected(); got=_pinned_outputs(root); assert got==want
 if enforce_frozen_hashes: assert FROZEN_SHA and {n:hashlib.sha256(got[n]).hexdigest() for n in FILES}==FROZEN_SHA
def main(): validate(); print(json.dumps({"stage":STAGE,"status":"passed","output_sha256":FROZEN_SHA},sort_keys=True))
if __name__=="__main__": main()
