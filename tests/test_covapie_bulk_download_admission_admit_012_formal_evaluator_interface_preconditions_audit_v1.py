from __future__ import annotations
import ast, hashlib, importlib.util, json, os, shutil, stat, sys
from pathlib import Path
import pytest
REPO_ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(REPO_ROOT/"src"))
from covalent_ext import covapie_bulk_download_admission_admit_012_formal_evaluator_interface_preconditions_audit as gate
SPEC=importlib.util.spec_from_file_location("admit012_checker",REPO_ROOT/"scripts/check_covapie_bulk_download_admission_admit_012_formal_evaluator_interface_preconditions_audit_v1.py"); assert SPEC and SPEC.loader
checker=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(checker)
ROOT=REPO_ROOT/checker.OUTPUT_ROOT
def copied(tmp_path): tmp_path.mkdir(parents=True,exist_ok=True); target=tmp_path/"out"; shutil.copytree(ROOT,target); return target
def resync(root):
 path=root/checker.MANIFEST; value=json.loads(path.read_text()); value["output_sha256"]={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in checker.FILES[:-1]}; path.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")
def reject(root):
 with pytest.raises(AssertionError): checker.validate(root,enforce_frozen_hashes=False)

def test_exact24_full_matrix_and_fail_closed_rows():
 rows=gate._preconditions(); assert rows==checker.preconditions() and len(rows)==24 and [row["precondition_id"] for row in rows]==[f"PRE_{n:03d}" for n in range(1,25)]
 assert {row["precondition_id"] for row in rows if row["precondition_passed"]=="false"}=={f"PRE_{n:03d}" for n in range(7,17)}
def test_exact16_issues_and_origin_count():
 rows=gate._issue_rows(gate.build_frozen_source_snapshot()); assert len(rows)==16 and all(row["issue_origin"]==gate.STAGE and row["issue_count"]=="1" for row in rows[-5:])
 assert rows[-5:]==checker.issues(checker.snapshot())[-5:]
def test_source_boundary_exact129_digests_and_pinned_rows():
 snapshot=gate.build_frozen_source_snapshot(); rows=gate._source_rows(snapshot)
 assert len(snapshot)==len(rows)==129 and all(row["pinned_fd_read"]==row["triple_sha256_passed"]=="true" for row in rows)
 assert hashlib.sha256(json.dumps([s.path.as_posix() for s in snapshot],separators=(",",":")).encode()).hexdigest()==gate.EXPECTED_PATH_LIST_SHA256
def test_occurrence_classification_is_deterministic_and_nonpromoting():
 rows=gate._occurrences(gate.build_frozen_source_snapshot()); assert rows==checker.occurrence(checker.snapshot())
 assert all(row["phase_claim"]=="unspecified_or_non_authoritative" for row in rows if row["source_authority_level"]=="historical_or_reference")
def test_observed_static_classifications_and_zero_authorized_execution():
 rows=gate._observed(gate.build_frozen_source_snapshot()); kinds={row["source_kind"] for row in rows}
 assert {"schema_only","test_fixture","unrelated_source_attestation_hash","historical_non_admit012_integrity_observation"}<=kinds
 assert all(row["produced_by_download_execution"]==row["admissible_as_semantic_evidence"]=="false" for row in rows)
def test_materializer_exact_set_noop_and_mismatch_fail_closed(tmp_path):
 root=tmp_path/"generated"; gate.materialize_audit(root); before={p.name:(p.stat().st_ino,p.read_bytes()) for p in root.iterdir()}; gate.materialize_audit(root)
 assert before=={p.name:(p.stat().st_ino,p.read_bytes()) for p in root.iterdir()}; (root/gate.PRECONDITION).write_bytes(b"broken")
 with pytest.raises(ValueError,match="mismatch"): gate.materialize_audit(root)
def test_materializer_gpfs_einval_fails_closed(tmp_path,monkeypatch):
 root=tmp_path/"target"; monkeypatch.setattr(gate,"_rename_noreplace",lambda a,b:(_ for _ in ()).throw(OSError(22,"EINVAL")))
 with pytest.raises(OSError): gate.materialize_audit(root)
 assert not root.exists() and not list(tmp_path.glob("*.staging"))
def test_source_and_output_symlink_fail_closed(tmp_path):
 link=tmp_path/"link"; link.symlink_to(tmp_path, target_is_directory=True)
 with pytest.raises((ValueError,OSError)): gate.materialize_audit(link/"out")
def test_synchronized_csv_semantic_tamper_is_rejected(tmp_path):
 root=copied(tmp_path); path=root/checker.OCC; text=path.read_text(); assert "historical_or_reference" in text; path.write_text(text.replace("historical_or_reference","primary_committed_contract",1)); resync(root); reject(root)
def test_synchronized_observed_source_issue_and_manifest_tampers_are_rejected(tmp_path):
 for filename,needle,replacement in ((checker.OBS,"schema_only","test_fixture"),(checker.SRC,"pinned_fd_read","pinned_fd_READ"),(checker.ISSUE,"issue_count","issue_COUNT")):
  root=copied(tmp_path/filename); path=root/filename; text=path.read_text(); assert needle in text; path.write_text(text.replace(needle,replacement,1)); resync(root); reject(root)
 root=copied(tmp_path/"manifest"); path=root/checker.MANIFEST; value=json.loads(path.read_text()); value["source_count"]=128; path.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n"); reject(root)
def test_shape_reorder_duplicate_extra_missing_and_unknown_key_fail_closed(tmp_path):
 root=copied(tmp_path); path=root/checker.PRE; lines=path.read_text().splitlines(); path.write_text("\n".join([lines[0],lines[2],lines[1],*lines[3:]])+"\n"); resync(root); reject(root)
 root=copied(tmp_path/"unknown"); path=root/checker.MANIFEST; value=json.loads(path.read_text()); value["unknown_key"]=True; path.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n"); reject(root)
def test_no_evaluator_result_adapter_registry_dispatcher_or_forbidden_artifacts():
 text=(REPO_ROOT/"src/covalent_ext/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_preconditions_audit.py").read_text()
 assert "def evaluate_admit_012" not in text and "class Admit012EvaluationResult" not in text and "def register_" not in text
 assert all(path.suffix not in {".pt",".ckpt",".pth",".pkl",".lmdb",".tar",".zip",".tgz",".npz"} for path in ROOT.iterdir())
def test_checker_regular_outputs_and_silent_import(): checker.validate(ROOT)
def test_production_has_no_chained_identity_not_equal_comparison():
 tree=ast.parse((REPO_ROOT/"src/covalent_ext/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_preconditions_audit.py").read_text())
 assert not [node for node in ast.walk(tree) if isinstance(node,ast.Compare) and sum(isinstance(op,ast.NotEq) for op in node.ops)>=2]
def test_checker_rejects_base_ancestry_before_output_read(monkeypatch):
 original=checker.git
 def fake(args,text=True):
  if args[:2]==["merge-base","--is-ancestor"]: return type("R",(),{"returncode":1,"stdout":""})()
  return original(args,text)
 monkeypatch.setattr(checker,"git",fake)
 with pytest.raises(AssertionError): checker.snapshot()
