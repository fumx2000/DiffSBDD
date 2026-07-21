from __future__ import annotations
import csv, hashlib, importlib.util, json, os, shutil, stat, subprocess, sys
from dataclasses import fields
from pathlib import Path
from types import SimpleNamespace
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"src"))
from covalent_ext import covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate as gate
spec=importlib.util.spec_from_file_location("check011",ROOT/"scripts/check_covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1.py");checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
def snap():return gate.ExistingRawTargetRelativePathsSnapshot("covapie_existing_raw_target_relative_paths_snapshot_v1","covapie_repository_raw_root_v1","repository_relative_posix_lexical_path","covapie_posix_relative_path_lexical_v1","exact_canonical_lexical_string_case_sensitive","pre_download",True,())
def test_exact_design_object_identities_and_namespace():
    assert tuple(f.name for f in fields(gate.RawTargetRelativePathContract))==gate.CONTRACT_FIELDS
    assert tuple(f.name for f in fields(gate.ExistingRawTargetRelativePathsSnapshot))==gate.SNAPSHOT_FIELDS
    assert gate.DEFAULT_CONTRACT.allowed_namespace_prefixes==("data/raw/",)
    child=type("X",(gate.RawTargetRelativePathContract,),{})
    with pytest.raises(TypeError):child(*tuple(getattr(gate.DEFAULT_CONTRACT,x) for x in gate.CONTRACT_FIELDS))
def test_historical_47_and_exact11_overlay():
    records,observed,issues,attestation=gate._snapshot_sources();assert len(records)==21 and len(observed)==47 and len(issues)==11 and attestation["predecessor_occurrence_count"]==172
    files=gate.build_artifacts(records,observed,issues,attestation);assert len(list(csv.DictReader(files[gate.OBSERVED_FILE].decode().splitlines())))==47
    rows=list(csv.DictReader(files[gate.ISSUE_FILE].decode().splitlines()));assert len(rows)==11 and next(x for x in rows if x["issue_id"]=="RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED")["status"]=="resolved";assert "ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015" in next(x for x in rows if x["issue_id"]=="UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")["affected_rules"]
def test_fixed_source_boundary_and_predecessor_attestation():
    records,observed,issues,attestation=gate._snapshot_sources()
    assert len(records)==gate.EXPECTED_SOURCE_COUNT==21 and tuple(gate.SOURCE_SHA256)==gate.SOURCE_PATHS and len(set(gate.SOURCE_PATHS))==21
    assert hashlib.sha256(gate._canonical_json(list(gate.SOURCE_PATHS))).hexdigest()==gate.EXPECTED_SOURCE_PATH_LIST_SHA256
    assert hashlib.sha256(gate._canonical_json([[p,gate.SOURCE_SHA256[p]] for p in gate.SOURCE_PATHS])).hexdigest()==gate.EXPECTED_SOURCE_PATH_SHA256_PAIRS_SHA256
    assert all(r.expected_sha256==r.base_tree_sha256==r.filesystem_sha256==r.frozen_snapshot_sha256 and r.base_tree_mode in ("100644","100755") for r in records)
    assert attestation=={"predecessor_source_boundary_count":99,"predecessor_occurrence_count":172,"predecessor_observed_value_count":47,"predecessor_issue_count":11,"predecessor_observed_value_state_counts":{"present_historical_or_fixture_value":47,"missing_empty":0,"missing_null_like":0}}
def test_base_subject_and_ancestor_are_frozen():
    assert gate.EXPECTED_BASE_SUBJECT=="add CovaPIE ADMIT_011 evaluator preconditions audit v1"
    gate._validate_base_lineage()
def test_source_structure_failure_precedes_all_byte_reads(monkeypatch):
    called=False
    def bomb(self):
        nonlocal called;called=True;raise AssertionError("byte read")
    monkeypatch.setattr(Path,"read_bytes",bomb);monkeypatch.setattr(gate,"_source_structure",lambda *a,**k:(_ for _ in ()).throw(ValueError("structural")))
    with pytest.raises(ValueError,match="structural"):gate._snapshot_sources()
    assert called is False
def _fake_source_structure_git(monkeypatch,raw,*,tree_kind="blob",tree_mode="100644",tracked=True):
    def fake(args,*,text=True):
        if args[0]=="ls-files":return subprocess.CompletedProcess(args,0 if tracked else 1,"" if text else b"","")
        if args[0]=="ls-tree":return subprocess.CompletedProcess(args,0,f"{tree_mode} {tree_kind} {'a'*40}\t{raw}\n" if text else b"","")
        raise AssertionError(args)
    monkeypatch.setattr(gate,"_git",fake)
def test_source_structure_rejects_nonblob_mode_and_untracked(monkeypatch,tmp_path):
    repo=tmp_path/"repo";leaf=repo/"safe"/"source.txt";leaf.parent.mkdir(parents=True);leaf.write_text("source")
    for kind,mode,tracked in (("tree","040000",True),("blob","100000",True),("blob","100644",False)):
        _fake_source_structure_git(monkeypatch,"safe/source.txt",tree_kind=kind,tree_mode=mode,tracked=tracked)
        with pytest.raises(ValueError):gate._source_structure("safe/source.txt",repo)
def test_source_structure_rejects_leaf_parent_and_resolved_escape(monkeypatch,tmp_path):
    repo=tmp_path/"repo";repo.mkdir();outside=tmp_path/"outside";outside.write_text("outside")
    leaf=repo/"safe"/"source.txt";leaf.parent.mkdir();leaf.symlink_to(outside)
    with pytest.raises(ValueError):gate._source_structure("safe/source.txt",repo)
    leaf.unlink();(repo/"linked").symlink_to(tmp_path,target_is_directory=True)
    with pytest.raises(ValueError):gate._source_structure("linked/outside",repo)
    regular=repo/"safe"/"regular.txt";regular.write_text("regular");_fake_source_structure_git(monkeypatch,"safe/regular.txt")
    original_resolve=Path.resolve
    def escaped(self,strict=False):return outside if self==regular else original_resolve(self,strict=strict)
    monkeypatch.setattr(Path,"resolve",escaped)
    with pytest.raises(ValueError,match="resolved identity"):gate._source_structure("safe/regular.txt",repo)
def test_snapshot_rejects_git_show_failure_before_filesystem_read(monkeypatch):
    original_git=gate._git;called=False
    def fake(args,*,text=True):
        if args[0]=="show" and text is False:return subprocess.CompletedProcess(args,1,b"",b"failed")
        return original_git(args,text=text)
    def bomb(self):
        nonlocal called;called=True;raise AssertionError("filesystem byte read")
    monkeypatch.setattr(gate,"_git",fake);monkeypatch.setattr(Path,"read_bytes",bomb)
    with pytest.raises(ValueError,match="base source read failed"):gate._snapshot_sources()
    assert called is False
def test_snapshot_rejects_filesystem_base_sha_drift(monkeypatch):
    raw=gate.SOURCE_PATHS[0];expected=gate.SOURCE_SHA256[raw]
    monkeypatch.setattr(gate,"SOURCE_PATHS",(raw,));monkeypatch.setattr(gate,"SOURCE_SHA256",{raw:expected})
    monkeypatch.setattr(gate,"_validate_source_configuration",lambda:None);monkeypatch.setattr(gate,"_validate_base_lineage",lambda:None);monkeypatch.setattr(gate,"_source_structure",lambda *args:"100644")
    monkeypatch.setattr(gate,"_git",lambda args,*,text=True:subprocess.CompletedProcess(args,0,b"base-drift" if not text else "",b""))
    with pytest.raises(ValueError,match="frozen source drift"):gate._snapshot_sources()
def test_source_boundary_has_exact_21_attested_rows_and_revised2a_hashes():
    records,observed,issues,attestation=gate._snapshot_sources();files=gate.build_artifacts(records,observed,issues,attestation)
    boundary=list(csv.DictReader(files[gate.BOUNDARY_FILE].decode().splitlines()))
    assert tuple(boundary[0])==("source_order","source_relative_path","expected_sha256","base_tree_sha256","filesystem_sha256","frozen_snapshot_sha256","git_tracked","base_tree_blob","base_tree_mode","filesystem_regular","non_symlink","parent_chain_non_symlink","safe_descendant","resolved_identity_passed","source_boundary_passed")
    assert len(boundary)==21 and [row["source_relative_path"] for row in boundary]==list(gate.SOURCE_PATHS)
    assert all(row["expected_sha256"]==row["base_tree_sha256"]==row["filesystem_sha256"]==row["frozen_snapshot_sha256"] and all(row[key]=="true" for key in ("git_tracked","base_tree_blob","filesystem_regular","non_symlink","parent_chain_non_symlink","safe_descendant","resolved_identity_passed","source_boundary_passed")) for row in boundary)
    expected={gate.CONTRACT_FILE:"dd5f853c047c7457d110739edf6f2ac3647bc3a9069b2b7a6d15b1470504f13e",gate.TRUTH_FILE:"1b32c3cc658433da18b804336afec8c63a275bcf44f68556faf75804e3b386ca",gate.RESPONSIBILITY_FILE:"0f3772e65db51623fe7ab477e97cc7fc98166755f39d172ef017a87c7ebfba24",gate.OBSERVED_FILE:"c55c48b58a66b44b2f6f0cc7fde27fe22fa317e3502a7eee9ee06c25006b74a2",gate.ISSUE_FILE:"eb36931b833800c4a7c9dffa33a690c4197ba0bb161cfbda742b90c3b3d8d1c0"}
    assert {name:hashlib.sha256(files[name]).hexdigest() for name in expected}==expected
def test_schema_matrix_has_exact_23_ordered_rows_and_snapshot_fixture():
    records,observed,issues,attestation=gate._snapshot_sources();rows=list(csv.DictReader(gate.build_artifacts(records,observed,issues,attestation)[gate.CONTRACT_FILE].decode().splitlines()))
    assert [r["order"] for r in rows]==[str(i) for i in range(1,24)]
    assert [r["field"] for r in rows[:15]]==list(gate.CONTRACT_FIELDS) and [r["field"] for r in rows[15:]]==list(gate.SNAPSHOT_FIELDS)
    assert [(r["field"],r["exact_type"],r["exact_value"]) for r in rows[-2:]]==[("snapshot_complete","exact built-in bool","True"),("occupied_relative_paths","exact built-in tuple","()")]
def test_result_design_type_state_and_projection_invariants():
    passed=gate.classify_admit_011_raw_target_relative_path_design("data/raw/a",snap(),gate.DEFAULT_CONTRACT);assert passed.outcome=="passed" and passed.validated_candidate_fields==((gate.CANDIDATE_FIELD,"data/raw/a"),) and passed.consumed_context_items==gate.STANDALONE_CONTEXT_VALIDATION_ORDER
    with pytest.raises(ValueError):gate.Admit011EvaluationResultDesign(gate.RULE_ID,"passed",False,False,"","data/raw/a",((gate.CANDIDATE_FIELD,"data/raw/a"),),(gate.CANDIDATE_FIELD,),gate.STANDALONE_CONTEXT_VALIDATION_ORDER,False)
    with pytest.raises(TypeError):gate.Admit011EvaluationResultDesign(gate.RULE_ID,"passed",True,False,"","data/raw/a",[],(gate.CANDIDATE_FIELD,),gate.STANDALONE_CONTEXT_VALIDATION_ORDER,False)
def test_result_design_rejects_every_noncanonical_retained_value():
    values=(("passed",True,False,"",("raw_target_relative_path_contract","existing_raw_target_relative_paths")),("blocked",False,True,gate.COLLISION_REASON,("raw_target_relative_path_contract","existing_raw_target_relative_paths")),("invalid",False,True,gate.CONTRACT_REASONS[0],("raw_target_relative_path_contract",)))
    for outcome,passed,blocks,reason,contexts in values:
        with pytest.raises(ValueError):gate.Admit011EvaluationResultDesign(gate.RULE_ID,outcome,passed,blocks,reason,"docs/a",((gate.CANDIDATE_FIELD,"docs/a"),),(gate.CANDIDATE_FIELD,),contexts,False)
    with pytest.raises(ValueError):gate.Admit011EvaluationResultDesign(gate.RULE_ID,"passed",True,False,"","data/rawness/a",((gate.CANDIDATE_FIELD,"data/rawness/a"),),(gate.CANDIDATE_FIELD,),gate.STANDALONE_CONTEXT_VALIDATION_ORDER,False)
    class StrChild(str):pass
    with pytest.raises(TypeError):gate.Admit011EvaluationResultDesign(gate.RULE_ID,"passed",True,False,"",StrChild("data/raw/a"),((gate.CANDIDATE_FIELD,"data/raw/a"),),(gate.CANDIDATE_FIELD,),gate.STANDALONE_CONTEXT_VALIDATION_ORDER,False)
def test_contract_snapshot_and_mismatch_consumption_order():
    contract_bad=gate.classify_admit_011_raw_target_relative_path_design("data/raw/a",snap(),object());assert contract_bad.reason==gate.CONTRACT_REASONS[0] and contract_bad.consumed_context_items==("raw_target_relative_path_contract",)
    snapshot_bad=gate.classify_admit_011_raw_target_relative_path_design("data/raw/a",object(),gate.DEFAULT_CONTRACT);assert snapshot_bad.reason==gate.SNAPSHOT_REASONS[0] and snapshot_bad.consumed_context_items==gate.STANDALONE_CONTEXT_VALIDATION_ORDER
    for field,reason in zip(("canonical_raw_root_identity","candidate_coordinate_system","path_grammar_version","equality_policy","snapshot_phase"),gate.SNAPSHOT_REASONS[2:],strict=True):
        assert gate.classify_admit_011_raw_target_relative_path_design("data/raw/a",gate._unsafe_snapshot(**{field:"wrong"}),gate.DEFAULT_CONTRACT).reason==reason
def test_complete_truth_matrix_calls_oracle_and_covers_every_reason():
    records,observed,issues,attestation=gate._snapshot_sources();truth=list(csv.DictReader(gate.build_artifacts(records,observed,issues,attestation)[gate.TRUTH_FILE].decode().splitlines()))
    assert len(truth)==84 and len([r for r in truth if r["matrix_group"]=="historical_observed"])==47 and {r["reason"] for r in truth}==set(gate.REASON_VOCABULARY)
    assert {r["expected_precedence"] for r in truth}==set(gate.VALIDATION_PRECEDENCE) and all(r["evaluator_io_used"]=="false" for r in truth)
@pytest.mark.parametrize("value,reason",[(None,"RAW_TARGET_RELATIVE_PATH_TYPE_INVALID"),("docs/a","RAW_TARGET_RELATIVE_PATH_NAMESPACE_FORBIDDEN"),("data/rawness/a","RAW_TARGET_RELATIVE_PATH_NAMESPACE_FORBIDDEN"),("data/raw//a","RAW_TARGET_RELATIVE_PATH_REPEATED_SEPARATOR"),("C:\\a","RAW_TARGET_RELATIVE_PATH_WINDOWS_DRIVE_FORBIDDEN"),("\\\\s\\x","RAW_TARGET_RELATIVE_PATH_UNC_FORBIDDEN"),("https://x//y","RAW_TARGET_RELATIVE_PATH_URI_FORBIDDEN"),("%2e%2e/x","RAW_TARGET_RELATIVE_PATH_PERCENT_ENCODING_FORBIDDEN"),("café x","RAW_TARGET_RELATIVE_PATH_NON_ASCII_FORBIDDEN"),("/../x","RAW_TARGET_RELATIVE_PATH_ABSOLUTE_FORBIDDEN")])
def test_grammar_precedence(value,reason):assert gate.classify_admit_011_raw_target_relative_path_design(value,snap(),gate.DEFAULT_CONTRACT).reason==reason
def test_scalar_context_and_collision_projection():
    scalar=gate.classify_admit_011_raw_target_relative_path_design("docs/a",object(),object());assert scalar.canonical_raw_target_relative_path=="" and scalar.consumed_context_items==()
    colliding=gate.ExistingRawTargetRelativePathsSnapshot("covapie_existing_raw_target_relative_paths_snapshot_v1","covapie_repository_raw_root_v1","repository_relative_posix_lexical_path","covapie_posix_relative_path_lexical_v1","exact_canonical_lexical_string_case_sensitive","pre_download",True,("data/raw/x.cif",)); result=gate.classify_admit_011_raw_target_relative_path_design("data/raw/x.cif",colliding,gate.DEFAULT_CONTRACT);assert (result.outcome,result.reason,result.evaluator_io_used)==("blocked",gate.COLLISION_REASON,False)
def test_snapshot_invariants_and_context_mismatch():
    with pytest.raises(ValueError):gate.ExistingRawTargetRelativePathsSnapshot("covapie_existing_raw_target_relative_paths_snapshot_v1","covapie_repository_raw_root_v1","repository_relative_posix_lexical_path","covapie_posix_relative_path_lexical_v1","exact_canonical_lexical_string_case_sensitive","pre_download",True,("data/raw/a","data/raw/a"))
    bad=gate.ExistingRawTargetRelativePathsSnapshot("covapie_existing_raw_target_relative_paths_snapshot_v1","wrong","repository_relative_posix_lexical_path","covapie_posix_relative_path_lexical_v1","exact_canonical_lexical_string_case_sensitive","pre_download",True,());assert gate.classify_admit_011_raw_target_relative_path_design("data/raw/a",bad,gate.DEFAULT_CONTRACT).reason=="RAW_TARGET_CONTEXT_ROOT_IDENTITY_MISMATCH"
def test_atomic_absolute_tmp_determinism_checker_and_real_hash_tamper(tmp_path):
    root=tmp_path/"out";a=gate.materialize_contract(root);before=_output_state(root);b=gate.materialize_contract(root);assert a==b and _output_state(root)==before;checker._validate_output_tree(root)
    truth=root/gate.TRUTH_FILE;truth.write_text(truth.read_text().replace("RAW_TARGET_RELATIVE_PATH_ALREADY_OCCUPIED","TAMPERED",1));m=json.loads((root/gate.MANIFEST_FILE).read_text());m["output_sha256"][gate.TRUTH_FILE]=hashlib.sha256(truth.read_bytes()).hexdigest();(root/gate.MANIFEST_FILE).write_text(json.dumps(m,sort_keys=True)+"\n")
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
def test_checker_rejects_schema_and_consumption_semantic_tamper_without_hashes(tmp_path):
    root=tmp_path/"out";gate.materialize_contract(root)
    schema=root/gate.CONTRACT_FILE;schema.write_text(schema.read_text().replace("covapie_existing_raw_target_relative_paths_snapshot_v1","wrong",1));
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
def test_checker_rejects_manifest_key_and_readiness_tamper_without_hashes(tmp_path):
    root=tmp_path/"out";gate.materialize_contract(root);manifest=root/gate.MANIFEST_FILE;value=json.loads(manifest.read_text());value["unexpected"]=True;manifest.write_text(json.dumps(value,sort_keys=True)+"\n")
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
    root=tmp_path/"second";gate.materialize_contract(root);manifest=root/gate.MANIFEST_FILE;value=json.loads(manifest.read_text());value["readiness"]["ready_for_admit_011_standalone_evaluator_interface_implementation"]=False;manifest.write_text(json.dumps(value,sort_keys=True)+"\n")
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
def test_checker_rejects_manifest_safety_precedence_and_row_count_tampers(tmp_path):
    for index,mutate in enumerate((lambda x:x["safety"].__setitem__("raw_read",True),lambda x:x.__setitem__("validation_precedence",list(reversed(x["validation_precedence"]))),lambda x:x["row_counts"].__setitem__("truth",83))):
        root=tmp_path/f"out-{index}";gate.materialize_contract(root);manifest=root/gate.MANIFEST_FILE;value=json.loads(manifest.read_text());mutate(value);manifest.write_text(json.dumps(value,sort_keys=True)+"\n")
        with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
def test_checker_rejects_manifest_issue_inventory_count_tamper(tmp_path):
    root=tmp_path/"out";gate.materialize_contract(root);manifest=root/gate.MANIFEST_FILE;value=json.loads(manifest.read_text());value["issue_inventory_count"]=12;manifest.write_text(json.dumps(value,sort_keys=True)+"\n")
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
def _sync_output_hash(root,filename):
    manifest=root/gate.MANIFEST_FILE;value=json.loads(manifest.read_text());value["output_sha256"][filename]=hashlib.sha256((root/filename).read_bytes()).hexdigest();manifest.write_text(json.dumps(value,sort_keys=True)+"\n")
def _sync_boundary_hashes(root):
    manifest=root/gate.MANIFEST_FILE;value=json.loads(manifest.read_text());digest=hashlib.sha256((root/gate.BOUNDARY_FILE).read_bytes()).hexdigest();value["output_sha256"][gate.BOUNDARY_FILE]=digest;value["source_boundary_output_sha256"]=digest;manifest.write_text(json.dumps(value,sort_keys=True)+"\n")
def test_checker_never_executes_malicious_candidate_representation(tmp_path):
    root=tmp_path/"out";gate.materialize_contract(root);truth=root/gate.TRUTH_FILE;rows=list(csv.DictReader(truth.read_text().splitlines()));rows[0]["candidate_representation"]=f"__import__('pathlib').Path({str(tmp_path/'marker')!r}).write_text('executed')";out=__import__('io').StringIO(newline="");writer=csv.DictWriter(out,fieldnames=rows[0].keys(),lineterminator="\n");writer.writeheader();writer.writerows(rows);truth.write_text(out.getvalue());_sync_output_hash(root,gate.TRUTH_FILE)
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
    assert not (tmp_path/"marker").exists() and "eval(" not in (ROOT/"scripts/check_covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1.py").read_text()
def test_checker_rejects_synced_collision_pass_projection_and_responsibility_tampers(tmp_path):
    def mutate_truth(index,mutator):
        root=tmp_path/f"truth-{index}";gate.materialize_contract(root)
        truth=root/gate.TRUTH_FILE;rows=list(csv.DictReader(truth.read_text().splitlines()));mutator(rows);out=__import__('io').StringIO(newline="");w=csv.DictWriter(out,fieldnames=rows[0].keys(),lineterminator="\n");w.writeheader();w.writerows(rows);truth.write_text(out.getvalue());_sync_output_hash(root,gate.TRUTH_FILE)
        with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
    mutate_truth(1,lambda rows:rows.__getitem__(next(i for i,r in enumerate(rows) if r["case_id"]=="COLLISION")).update(outcome="passed",passed="true",blocks_candidate="false"))
    mutate_truth(2,lambda rows:rows.__getitem__(next(i for i,r in enumerate(rows) if r["case_id"]=="PASSED")).update(blocks_candidate="true"))
    mutate_truth(3,lambda rows:rows.__getitem__(next(i for i,r in enumerate(rows) if r["case_id"]=="PASSED")).update(canonical="data/raw/b",validated_candidate_fields='[["raw_target_relative_path","data/raw/b"]]'))
    root=tmp_path/"responsibility";gate.materialize_contract(root);responsibility=root/gate.RESPONSIBILITY_FILE;rows=list(csv.DictReader(responsibility.read_text().splitlines()));rows[0]["boundary"]="tampered";out=__import__('io').StringIO(newline="");w=csv.DictWriter(out,fieldnames=rows[0].keys(),lineterminator="\n");w.writeheader();w.writerows(rows);responsibility.write_text(out.getvalue());_sync_output_hash(root,gate.RESPONSIBILITY_FILE)
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
@pytest.mark.parametrize("mutate",[
    lambda rows:rows[0].__setitem__("source_relative_path","src/tampered.py"),
    lambda rows:rows.__setitem__(slice(0,2),[rows[1],rows[0]]),
    lambda rows:[row.__setitem__(key,"0"*64) for row in rows[:1] for key in ("expected_sha256","base_tree_sha256","filesystem_sha256","frozen_snapshot_sha256")],
    lambda rows:rows[0].__setitem__("base_tree_mode","100000"),
    lambda rows:rows[0].__setitem__("source_boundary_passed","false"),
])
def test_checker_rejects_synced_boundary_attestation_tampers(tmp_path,mutate):
    root=tmp_path/"out";gate.materialize_contract(root);boundary=root/gate.BOUNDARY_FILE;rows=list(csv.DictReader(boundary.read_text().splitlines()));mutate(rows);out=__import__('io').StringIO(newline="");w=csv.DictWriter(out,fieldnames=rows[0].keys(),lineterminator="\n");w.writeheader();w.writerows(rows);boundary.write_text(out.getvalue());_sync_boundary_hashes(root)
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
def test_checker_rejects_synchronized_boundary_and_manifest_source_map_tamper(tmp_path):
    root=tmp_path/"out";gate.materialize_contract(root);boundary=root/gate.BOUNDARY_FILE;rows=list(csv.DictReader(boundary.read_text().splitlines()));path=rows[0]["source_relative_path"]
    for key in ("expected_sha256","base_tree_sha256","filesystem_sha256","frozen_snapshot_sha256"):rows[0][key]="0"*64
    out=__import__('io').StringIO(newline="");w=csv.DictWriter(out,fieldnames=rows[0].keys(),lineterminator="\n");w.writeheader();w.writerows(rows);boundary.write_text(out.getvalue());_sync_boundary_hashes(root)
    manifest=root/gate.MANIFEST_FILE;value=json.loads(manifest.read_text());value["source_paths_sha256"][path]="0"*64;manifest.write_text(json.dumps(value,sort_keys=True)+"\n")
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
@pytest.mark.parametrize("mutate",[
    lambda value:value.__setitem__("stage","wrong"),
    lambda value:value.__setitem__("base_commit","0"*40),
    lambda value:value.__setitem__("admission_rule_id","ADMIT_999"),
    lambda value:value.__setitem__("contract_class","WrongContract"),
    lambda value:value.__setitem__("snapshot_fields",list(reversed(value["snapshot_fields"]))),
    lambda value:value.__setitem__("coordinate_system","wrong"),
    lambda value:value.__setitem__("allowed_namespace_prefixes",["data/other/"]),
    lambda value:value.__setitem__("issue_inventory_sha256","0"*64),
    lambda value:value.__setitem__("coverage_affected_rules","ADMIT_011"),
    lambda value:value.__setitem__("recommended_next_step","wrong"),
])
def test_checker_rejects_all_manifest_identity_tampers(tmp_path,mutate):
    root=tmp_path/"out";gate.materialize_contract(root);manifest=root/gate.MANIFEST_FILE;value=json.loads(manifest.read_text());mutate(value);manifest.write_text(json.dumps(value,sort_keys=True)+"\n")
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
def test_checker_rejects_manifest_source_path_reorder(tmp_path):
    root=tmp_path/"out";gate.materialize_contract(root);manifest=root/gate.MANIFEST_FILE;value=json.loads(manifest.read_text());value["source_paths_sha256"]={key:value["source_paths_sha256"][key] for key in reversed(value["source_paths_sha256"])};manifest.write_text(json.dumps(value,sort_keys=False)+"\n")
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
@pytest.mark.parametrize("field",("predecessor_source_boundary_count","predecessor_occurrence_count","predecessor_observed_value_count"))
def test_checker_rejects_predecessor_exact_count_tampers(tmp_path,field):
    root=tmp_path/"out";gate.materialize_contract(root);manifest=root/gate.MANIFEST_FILE;value=json.loads(manifest.read_text());value[field]-=1;manifest.write_text(json.dumps(value,sort_keys=True)+"\n")
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
def _checker_output_root(tmp_path):
    root=tmp_path/"out";gate.materialize_contract(root);return root
def _checker_git_failure(monkeypatch,predicate,*,returncode=1,stdout="",stderr=""):
    original=checker._run_git
    def fake(args,*,text=True):
        if predicate(args,text):return subprocess.CompletedProcess(args,returncode,stdout if text else stdout.encode(),stderr if text else stderr.encode())
        return original(args,text=text)
    monkeypatch.setattr(checker,"_run_git",fake)
def test_checker_live_source_attestation_exact21_and_deterministic(tmp_path,capsys):
    root=_checker_output_root(tmp_path);rows=checker._live_boundary_rows()
    assert len(rows)==21 and [row["source_relative_path"] for row in rows]==list(checker.SOURCE_PATHS)
    checker._validate_output_tree(root);first=capsys.readouterr().out;checker._validate_output_tree(root);second=capsys.readouterr().out
    assert first==second
def test_checker_rejects_live_source_sha_drift_before_output_read(tmp_path,monkeypatch):
    root=_checker_output_root(tmp_path);source=checker.ROOT/checker.SOURCE_PATHS[0];original=Path.read_bytes;output_read=False
    def fake(self):
        nonlocal output_read
        if self==source:return b"current-filesystem-drift"
        if self.parent==root:output_read=True;raise AssertionError("output byte read")
        return original(self)
    monkeypatch.setattr(Path,"read_bytes",fake)
    def output_bomb(*args):
        nonlocal output_read;output_read=True;raise AssertionError("output fd read")
    monkeypatch.setattr(checker,"_read_pinned_output_bytes",output_bomb)
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
    assert output_read is False
@pytest.mark.parametrize("kind",("leaf","parent"))
def test_checker_rejects_live_source_symlink_before_any_byte_read(tmp_path,monkeypatch,kind):
    root=_checker_output_root(tmp_path);source=checker.ROOT/checker.SOURCE_PATHS[0];target=source if kind=="leaf" else source.parent;original_lstat=checker.os.lstat;called=False
    def fake_lstat(path):return SimpleNamespace(st_mode=stat.S_IFLNK) if Path(path)==target else original_lstat(path)
    def bomb(self):
        nonlocal called;called=True;raise AssertionError("byte read")
    monkeypatch.setattr(checker.os,"lstat",fake_lstat);monkeypatch.setattr(Path,"read_bytes",bomb)
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
    assert called is False
def test_checker_rejects_live_source_untracked(tmp_path,monkeypatch):
    root=_checker_output_root(tmp_path)
    _checker_git_failure(monkeypatch,lambda args,text:args[0]=="ls-files")
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
def test_checker_rejects_live_base_subject_and_ancestor_mismatch(tmp_path,monkeypatch):
    root=_checker_output_root(tmp_path)
    _checker_git_failure(monkeypatch,lambda args,text:args[:3]==["show","-s","--format=%s"],returncode=0,stdout="wrong subject")
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
    monkeypatch.undo();_checker_git_failure(monkeypatch,lambda args,text:args[:2]==["merge-base","--is-ancestor"])
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
def test_checker_rejects_live_git_show_failure_before_any_byte_read(tmp_path,monkeypatch):
    root=_checker_output_root(tmp_path);called=False
    _checker_git_failure(monkeypatch,lambda args,text:args[0]=="show" and len(args)==2 and args[1].startswith(f"{checker.BASE}:"))
    def bomb(self):
        nonlocal called;called=True;raise AssertionError("byte read")
    monkeypatch.setattr(Path,"read_bytes",bomb)
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
    assert called is False
def _safe_materialized_root(tmp_path):
    root=tmp_path/"out";gate.materialize_contract(root);return root
def _output_bytes(root):return {name:(root/name).read_bytes() for name in gate.OUTPUT_FILES}
def _output_state(root):return {name:(gate._identity(os.lstat(root/name)),(root/name).read_bytes()) for name in gate.OUTPUT_FILES}
def _staging_entries(parent):return tuple(parent.glob(".admit011-stage-*"))
def _no_temporary_entries(root):return not root.exists() or not any(item.name.endswith((".tmp",".part")) or item.name.startswith(".admit011-stage-") for item in root.iterdir())
@pytest.mark.parametrize("kind",("relative_escape","missing_parent","root_symlink_inside","root_symlink_outside","broken_root_symlink","root_file","root_fifo"))
def test_materializer_initial_output_preflight_rejects_unsafe_targets(tmp_path,kind):
    parent=tmp_path/"parent";parent.mkdir();root=parent/"out"
    if kind=="relative_escape":
        with pytest.raises(ValueError):gate._inspect_output_target_read_only(Path("..")/"escape")
        return
    if kind=="missing_parent":root=tmp_path/"missing"/"out"
    elif kind=="root_symlink_inside":root.symlink_to(parent,target_is_directory=True)
    elif kind=="root_symlink_outside":root.symlink_to(tmp_path.parent,target_is_directory=True)
    elif kind=="broken_root_symlink":root.symlink_to(tmp_path/"absent")
    elif kind=="root_file":root.write_text("not a directory")
    elif kind=="root_fifo":os.mkfifo(root)
    with pytest.raises((ValueError,OSError)):gate._inspect_output_target_read_only(root)
@pytest.mark.parametrize("kind",("parent_symlink","unexpected","leaf_symlink","leaf_directory","leaf_fifo"))
def test_materializer_initial_preflight_rejects_unsafe_existing_inventory(tmp_path,kind):
    if kind=="parent_symlink":
        real=tmp_path/"real";real.mkdir();link=tmp_path/"link";link.symlink_to(real,target_is_directory=True)
        with pytest.raises((ValueError,OSError)):gate._inspect_output_target_read_only(link/"out")
        return
    root=_safe_materialized_root(tmp_path)
    if kind=="unexpected":(root/"unexpected").write_text("x")
    else:
        leaf=root/gate.CONTRACT_FILE;leaf.unlink()
        if kind=="leaf_symlink":leaf.symlink_to(root/gate.TRUTH_FILE)
        elif kind=="leaf_directory":leaf.mkdir()
        else:os.mkfifo(leaf)
    with pytest.raises((ValueError,OSError)):gate._inspect_output_target_read_only(root)
def test_materializer_unsafe_preflight_precedes_source_read(tmp_path,monkeypatch):
    root=tmp_path/"out";root.symlink_to(tmp_path,target_is_directory=True);called=False
    def bomb():
        nonlocal called;called=True;raise AssertionError("source read")
    monkeypatch.setattr(gate,"_snapshot_sources",bomb)
    with pytest.raises((ValueError,OSError)):gate.materialize_contract(root)
    assert called is False
def test_materializer_source_and_build_failure_leave_outputs_unmodified(tmp_path,monkeypatch):
    missing=tmp_path/"missing";monkeypatch.setattr(gate,"_snapshot_sources",lambda:(_ for _ in ()).throw(ValueError("snapshot")))
    with pytest.raises(ValueError):gate.materialize_contract(missing)
    assert not missing.exists()
    monkeypatch.undo();missing_build=tmp_path/"missing-build";monkeypatch.setattr(gate,"build_artifacts",lambda *args:(_ for _ in ()).throw(ValueError("build")))
    with pytest.raises(ValueError):gate.materialize_contract(missing_build)
    assert not missing_build.exists()
    monkeypatch.undo();root=_safe_materialized_root(tmp_path);before=_output_bytes(root);monkeypatch.setattr(gate,"_snapshot_sources",lambda:(_ for _ in ()).throw(ValueError("snapshot")))
    with pytest.raises(ValueError):gate.materialize_contract(root)
    assert _output_bytes(root)==before and _no_temporary_entries(root)
    monkeypatch.undo();monkeypatch.setattr(gate,"build_artifacts",lambda *args:(_ for _ in ()).throw(ValueError("build")))
    with pytest.raises(ValueError):gate.materialize_contract(root)
    assert _output_bytes(root)==before and _no_temporary_entries(root)
def _prewrite_race(monkeypatch,action):
    original=gate._open_prewrite_root
    def raced(plan):action(plan);return original(plan)
    monkeypatch.setattr(gate,"_open_prewrite_root",raced)
def test_materializer_prewrite_missing_target_and_parent_races_fail_closed(tmp_path,monkeypatch):
    root=tmp_path/"out";_prewrite_race(monkeypatch,lambda plan:plan.root.mkdir())
    with pytest.raises(ValueError):gate.materialize_contract(root)
    monkeypatch.undo();root=tmp_path/"broken";_prewrite_race(monkeypatch,lambda plan:plan.root.symlink_to(tmp_path/"absent"))
    with pytest.raises(ValueError):gate.materialize_contract(root)
    monkeypatch.undo();parent=tmp_path/"parent";parent.mkdir();root=parent/"out"
    def replace_parent(plan):plan.parent.rename(tmp_path/"old-parent");plan.parent.mkdir()
    _prewrite_race(monkeypatch,replace_parent)
    with pytest.raises((ValueError,OSError)):gate.materialize_contract(root)
def test_materializer_prewrite_existing_root_leaf_and_unknown_races_fail_closed(tmp_path,monkeypatch):
    first=tmp_path/"first";first.mkdir();root=_safe_materialized_root(first);old=first/"old-root"
    def replace_root(plan):plan.root.rename(old);plan.root.mkdir()
    _prewrite_race(monkeypatch,replace_root)
    with pytest.raises((ValueError,OSError)):gate.materialize_contract(root)
    monkeypatch.undo();second=tmp_path/"second";second.mkdir();root=_safe_materialized_root(second)
    def replace_leaf(plan):
        leaf=plan.root/gate.CONTRACT_FILE;data=leaf.read_bytes();leaf.unlink();leaf.write_bytes(data)
    _prewrite_race(monkeypatch,replace_leaf)
    with pytest.raises((ValueError,OSError)):gate.materialize_contract(root)
    monkeypatch.undo();third=tmp_path/"third";third.mkdir();root=_safe_materialized_root(third);_prewrite_race(monkeypatch,lambda plan:(plan.root/"unknown").write_text("race"))
    with pytest.raises((ValueError,OSError)):gate.materialize_contract(root)
def test_materializer_existing_root_mismatch_fails_closed_without_replace(tmp_path,monkeypatch):
    root=_safe_materialized_root(tmp_path);leaf=root/gate.CONTRACT_FILE;leaf.write_bytes(b"different");before=_output_state(root)
    monkeypatch.setattr(gate.os,"replace",lambda *args,**kwargs:(_ for _ in ()).throw(AssertionError("replace must be unreachable")),raising=False)
    with pytest.raises(ValueError,match="existing output payload differs"):gate.materialize_contract(root)
    assert _output_state(root)==before and not _staging_entries(tmp_path)
def test_materializer_existing_exact_root_is_noop_without_replace(tmp_path,monkeypatch):
    root=_safe_materialized_root(tmp_path);before=_output_state(root)
    monkeypatch.setattr(gate.os,"replace",lambda *args,**kwargs:(_ for _ in ()).throw(AssertionError("replace must be unreachable")),raising=False)
    gate.materialize_contract(root)
    assert _output_state(root)==before and not _staging_entries(tmp_path)
@pytest.mark.parametrize("failure_index",range(1,len(gate.OUTPUT_FILES)+1))
def test_materializer_staging_write_failures_leave_final_root_absent(tmp_path,monkeypatch,failure_index):
    root=tmp_path/"out";original=gate._write_all;count=0
    def fail_at(file_fd,data):
        nonlocal count;count+=1
        if count==failure_index:raise OSError(f"write {failure_index}")
        return original(file_fd,data)
    monkeypatch.setattr(gate,"_write_all",fail_at)
    with pytest.raises(OSError,match=f"write {failure_index}"):gate.materialize_contract(root)
    assert not root.exists() and not _staging_entries(tmp_path)
def test_materializer_staging_directory_fsync_and_rename_failures_leave_final_root_absent(tmp_path,monkeypatch):
    root=tmp_path/"fsync";original=gate.os.fsync;count=0
    def fail_staging_fsync(fd):
        nonlocal count;count+=1
        if count==len(gate.OUTPUT_FILES)+1:raise OSError("staging fsync")
        return original(fd)
    monkeypatch.setattr(gate.os,"fsync",fail_staging_fsync)
    with pytest.raises(OSError,match="staging fsync"):gate.materialize_contract(root)
    assert not root.exists() and not _staging_entries(tmp_path)
    monkeypatch.undo();root=tmp_path/"rename";monkeypatch.setattr(gate,"_rename_noreplace_at",lambda *args,**kwargs:(_ for _ in ()).throw(OSError("rename")))
    with pytest.raises(OSError,match="rename"):gate.materialize_contract(root)
    assert not root.exists() and not _staging_entries(tmp_path)
def test_materializer_parent_fsync_failure_leaves_only_complete_published_set(tmp_path,monkeypatch):
    root=tmp_path/"out";original=gate.os.fsync;count=0
    def fail_parent_fsync(fd):
        nonlocal count;count+=1
        if count==len(gate.OUTPUT_FILES)+2:raise OSError("parent fsync")
        return original(fd)
    monkeypatch.setattr(gate.os,"fsync",fail_parent_fsync)
    with pytest.raises(OSError,match="parent fsync"):gate.materialize_contract(root)
    assert set(item.name for item in root.iterdir())==set(gate.OUTPUT_FILES) and not _staging_entries(tmp_path)
def test_materializer_final_root_race_is_rejected_without_overwrite(tmp_path,monkeypatch):
    root=tmp_path/"out";original=gate._publish_staging_directory
    def raced(plan,*args):
        root.mkdir();return original(plan,*args)
    monkeypatch.setattr(gate,"_publish_staging_directory",raced)
    with pytest.raises(ValueError,match="new output target race"):gate.materialize_contract(root)
    assert root.is_dir() and not tuple(root.iterdir()) and not _staging_entries(tmp_path)
def test_materializer_atomic_rename_rejects_postcheck_root_occupant(tmp_path,monkeypatch):
    root=tmp_path/"out";original=gate._rename_noreplace_at
    def raced(parent_fd,source,target):
        root.mkdir();return original(parent_fd,source,target)
    monkeypatch.setattr(gate,"_rename_noreplace_at",raced)
    with pytest.raises(OSError):gate.materialize_contract(root)
    assert root.is_dir() and not tuple(root.iterdir()) and not _staging_entries(tmp_path)
def test_materializer_missing_root_rename_publishes_only_complete_set(tmp_path,monkeypatch):
    root=tmp_path/"out";original=gate._rename_noreplace_at
    def checked_rename(parent_fd,source,target):
        staging=tmp_path/source
        assert not root.exists() and set(item.name for item in staging.iterdir())==set(gate.OUTPUT_FILES)
        return original(parent_fd,source,target)
    monkeypatch.setattr(gate,"_rename_noreplace_at",checked_rename)
    gate.materialize_contract(root)
    assert set(item.name for item in root.iterdir())==set(gate.OUTPUT_FILES) and not _staging_entries(tmp_path)
def test_materializer_unknown_entry_is_not_cleanup_deleted(tmp_path,monkeypatch):
    root=tmp_path/"out"
    def fail_with_unknown(root_fd,files,staged):
        fd=os.open("unknown",os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600,dir_fd=root_fd);os.close(fd);raise OSError("staging")
    monkeypatch.setattr(gate,"_stage_payloads",fail_with_unknown)
    with pytest.raises(OSError):gate.materialize_contract(root)
    stages=_staging_entries(tmp_path)
    assert not root.exists() and len(stages)==1 and (stages[0]/"unknown").is_file()
def test_materializer_rejects_root_swap_after_directory_fd_open(tmp_path,monkeypatch):
    root=tmp_path/"out";old=tmp_path/"old";outside=tmp_path/"outside";outside.mkdir();original=gate._stage_payloads
    def swapped(root_fd,files,staged):
        stage=next(iter(_staging_entries(tmp_path)));stage.rename(old);stage.symlink_to(outside,target_is_directory=True);return original(root_fd,files,staged)
    monkeypatch.setattr(gate,"_stage_payloads",swapped)
    with pytest.raises((ValueError,OSError)):gate.materialize_contract(root)
    assert not root.exists() and len(_staging_entries(tmp_path))==1 and old.is_dir() and _no_temporary_entries(old)
def test_materializer_default_relative_synthetic_repo_and_v4_determinism(tmp_path,monkeypatch):
    records,observed,issues,attestation=gate._snapshot_sources();repo=tmp_path/"repo";(repo/"data/derived/covalent_small").mkdir(parents=True)
    monkeypatch.setattr(gate,"REPO_ROOT",repo);monkeypatch.setattr(gate,"OUTPUT_ROOT",Path("data/derived/covalent_small")/gate.STAGE);monkeypatch.setattr(gate,"_snapshot_sources",lambda:(records,observed,issues,attestation))
    first=gate.materialize_contract();root=repo/gate.OUTPUT_ROOT;second=gate.materialize_contract();manifest=json.loads((root/gate.MANIFEST_FILE).read_text())
    assert first==second and manifest["manifest_schema_version"].endswith("_v4") and set(manifest["materializer_safety"])==set(gate.MATERIALIZER_SAFETY_KEYS) and all(manifest["materializer_safety"].values())
    assert {name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in gate.FROZEN_CSV_SHA256}==gate.FROZEN_CSV_SHA256
def test_checker_rejects_output_parent_root_and_broken_symlink(tmp_path):
    root=_safe_materialized_root(tmp_path);link=tmp_path/"link";link.symlink_to(root,target_is_directory=True)
    with pytest.raises(AssertionError):checker._validate_output_tree(link,enforce_frozen_hashes=False)
    broken=tmp_path/"broken";broken.symlink_to(tmp_path/"absent")
    with pytest.raises(AssertionError):checker._validate_output_tree(broken,enforce_frozen_hashes=False)
    parent=tmp_path/"parent";parent.mkdir();nested=_safe_materialized_root(parent);parent_link=tmp_path/"parent-link";parent_link.symlink_to(parent,target_is_directory=True)
    with pytest.raises(AssertionError):checker._validate_output_tree(parent_link/"out",enforce_frozen_hashes=False)
def test_checker_rejects_output_root_swap_after_pinning(tmp_path,monkeypatch):
    root=_safe_materialized_root(tmp_path);old=tmp_path/"old";original=checker._live_boundary_rows
    def swapped():root.rename(old);root.symlink_to(tmp_path,target_is_directory=True);return original()
    monkeypatch.setattr(checker,"_live_boundary_rows",swapped)
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
@pytest.mark.parametrize("mutate",(
    lambda value:value["materializer_safety"].pop(next(iter(value["materializer_safety"]))),
    lambda value:value["materializer_safety"].__setitem__("unknown",True),
    lambda value:value["materializer_safety"].__setitem__(next(iter(value["materializer_safety"])),False),
    lambda value:value.__setitem__("manifest_schema_version","covapie_admit_011_raw_target_relative_path_contract_manifest_v3"),
))
def test_checker_rejects_materializer_safety_manifest_tamper(tmp_path,mutate):
    root=_safe_materialized_root(tmp_path);manifest=root/gate.MANIFEST_FILE;value=json.loads(manifest.read_text());mutate(value);manifest.write_text(json.dumps(value,sort_keys=True)+"\n")
    with pytest.raises(AssertionError):checker._validate_output_tree(root,enforce_frozen_hashes=False)
def test_output_symlink_and_pre_read_failure(tmp_path,monkeypatch):
    outside=tmp_path/"outside";outside.mkdir();link=tmp_path/"link";link.symlink_to(outside,target_is_directory=True)
    called=False
    def bomb():
        nonlocal called;called=True;raise AssertionError
    monkeypatch.setattr(gate,"_snapshot_sources",bomb)
    with pytest.raises(ValueError):gate.materialize_contract(link)
    assert called is False
