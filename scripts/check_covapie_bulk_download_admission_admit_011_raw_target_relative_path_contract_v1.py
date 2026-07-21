#!/usr/bin/env python3
"""Independent, non-executing checker for the ADMIT_011 design outputs."""
from __future__ import annotations
import csv, hashlib, io, json, os, stat, subprocess
from pathlib import Path, PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
BASE="a8cf1a8dcda6ebcdf1ddaf34233f61475686b417"; SUBJECT="add CovaPIE ADMIT_011 evaluator preconditions audit v1"; STAGE="covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1"; EXPECTED_OUTPUT_ROOT=Path("data/derived/covalent_small")/STAGE
FIELD="raw_target_relative_path"; CONTRACT_CONTEXT="raw_target_relative_path_contract"; SNAPSHOT_CONTEXT="existing_raw_target_relative_paths"
FILES=("covapie_admit_011_raw_target_relative_path_contract_schema_matrix.csv","covapie_admit_011_raw_target_relative_path_grammar_truth_matrix.csv","covapie_admit_011_raw_target_context_responsibility_matrix.csv","covapie_admit_011_raw_target_observed_value_coverage_matrix.csv","covapie_admit_011_raw_target_issue_readiness_inventory.csv","covapie_admit_011_raw_target_contract_source_boundary_audit.csv","covapie_admit_011_raw_target_relative_path_contract_manifest.json")
FROZEN_HASHES={"covapie_admit_011_raw_target_context_responsibility_matrix.csv":"0f3772e65db51623fe7ab477e97cc7fc98166755f39d172ef017a87c7ebfba24","covapie_admit_011_raw_target_contract_source_boundary_audit.csv":"e0747e6b3be3a51d1884a76a85f70b05d34d4f687b20e2604f56783db985840f","covapie_admit_011_raw_target_issue_readiness_inventory.csv":"eb36931b833800c4a7c9dffa33a690c4197ba0bb161cfbda742b90c3b3d8d1c0","covapie_admit_011_raw_target_observed_value_coverage_matrix.csv":"c55c48b58a66b44b2f6f0cc7fde27fe22fa317e3502a7eee9ee06c25006b74a2","covapie_admit_011_raw_target_relative_path_contract_manifest.json":"9718090b212e3338bddef1fb7d6fb62e39d95e1911fe5bdd0ff6613b364e8bf4","covapie_admit_011_raw_target_relative_path_contract_schema_matrix.csv":"dd5f853c047c7457d110739edf6f2ac3647bc3a9069b2b7a6d15b1470504f13e","covapie_admit_011_raw_target_relative_path_grammar_truth_matrix.csv":"1b32c3cc658433da18b804336afec8c63a275bcf44f68556faf75804e3b386ca"}
CONTRACT_FIELDS=("schema_version","contract_id","canonical_raw_root_identity","candidate_coordinate_system","allowed_namespace_prefixes","path_grammar_version","equality_policy","case_policy","normalization_policy","percent_decoding_policy","unicode_policy","snapshot_phase","occupied_path_policy","evaluator_io_policy","mutation_policy")
SNAPSHOT_FIELDS=("schema_version","canonical_raw_root_identity","candidate_coordinate_system","path_grammar_version","equality_policy","snapshot_phase","snapshot_complete","occupied_relative_paths")
SCALAR=("RAW_TARGET_RELATIVE_PATH_TYPE_INVALID","RAW_TARGET_RELATIVE_PATH_EMPTY","RAW_TARGET_RELATIVE_PATH_NON_ASCII_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_NUL_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_CONTROL_CHARACTER_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_WHITESPACE_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_ABSOLUTE_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_WINDOWS_DRIVE_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_UNC_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_URI_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_PERCENT_ENCODING_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_TILDE_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_ENVIRONMENT_EXPANSION_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_BACKSLASH_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_TRAILING_SEPARATOR","RAW_TARGET_RELATIVE_PATH_REPEATED_SEPARATOR","RAW_TARGET_RELATIVE_PATH_DOT_COMPONENT_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_DOTDOT_COMPONENT_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_NAMESPACE_FORBIDDEN")
CONTRACT=("RAW_TARGET_RELATIVE_PATH_CONTRACT_TYPE_INVALID","RAW_TARGET_RELATIVE_PATH_CONTRACT_VALUE_INVALID")
SNAPSHOT=("EXISTING_RAW_TARGET_RELATIVE_PATHS_SNAPSHOT_TYPE_INVALID","EXISTING_RAW_TARGET_RELATIVE_PATHS_SNAPSHOT_VALUE_INVALID","RAW_TARGET_CONTEXT_ROOT_IDENTITY_MISMATCH","RAW_TARGET_CONTEXT_COORDINATE_SYSTEM_MISMATCH","RAW_TARGET_CONTEXT_GRAMMAR_MISMATCH","RAW_TARGET_CONTEXT_EQUALITY_POLICY_MISMATCH","RAW_TARGET_CONTEXT_PHASE_MISMATCH")
COLLISION="RAW_TARGET_RELATIVE_PATH_ALREADY_OCCUPIED"; REASONS=("",*SCALAR,*CONTRACT,*SNAPSHOT,COLLISION)
PRECEDENCE=("scalar_type","scalar_empty","scalar_ascii","scalar_nul","scalar_control","scalar_whitespace","scalar_absolute","scalar_windows_drive","scalar_unc","scalar_uri","scalar_percent","scalar_tilde","scalar_environment","scalar_backslash","scalar_trailing_separator","scalar_repeated_separator","scalar_dot","scalar_dotdot","scalar_namespace","contract_type","contract_value","snapshot_type","snapshot_value","context_root","context_coordinate","context_grammar","context_equality","context_phase","exact_occupied_collision","passed")
SCHEMA_HEADER=("order","object","field","exact_type","exact_value","passed")
TRUTH_HEADER=("case_order","case_id","matrix_group","candidate_representation","contract_state","snapshot_state","outcome","passed","blocks_candidate","reason","canonical","validated_candidate_fields","consumed_candidate_fields","consumed_context_items","evaluator_io_used","expected_precedence","case_passed")
BOUNDARY_HEADER=("source_order","source_relative_path","expected_sha256","base_tree_sha256","filesystem_sha256","frozen_snapshot_sha256","git_tracked","base_tree_blob","base_tree_mode","filesystem_regular","non_symlink","parent_chain_non_symlink","safe_descendant","resolved_identity_passed","source_boundary_passed")
MATERIALIZER_SAFETY_KEYS=("initial_output_preflight_before_source_bytes","no_output_mutation_before_artifacts_built","parent_chain_non_symlink","broken_symlink_rejected","missing_parent_creation_forbidden","root_identity_revalidated_before_write","existing_leaf_identity_revalidated_before_write","directory_fd_pinned","temporary_files_same_directory","temporary_files_exclusive_non_symlink","file_fsync_before_publish","atomic_publish_via_directory_fd","directory_fsync_after_publish","postwrite_inventory_verified","postwrite_bytes_and_sha_verified","temporary_files_cleaned_on_failure","newly_created_root_cleanup_on_failure","materializer_hardening_passed")
SOURCE_PATHS=(
"src/covalent_ext/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit.py","data/derived/covalent_small/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_011_formal_evaluator_preconditions_manifest.json","data/derived/covalent_small/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_011_formal_evaluator_precondition_matrix.csv","data/derived/covalent_small/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_011_raw_target_field_occurrence_inventory.csv","data/derived/covalent_small/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_011_raw_target_observed_value_inventory.csv","data/derived/covalent_small/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_011_source_boundary_audit.csv","data/derived/covalent_small/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_011_formal_evaluator_issue_readiness_inventory.csv","data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv","data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_schema_contract.csv","data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_rule_executability_matrix.csv","data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_field_semantics_matrix.csv","data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv","src/covalent_ext/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate.py","src/covalent_ext/covapie_bulk_download_admission_admit_009_rule_logic_interface.py","src/covalent_ext/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate.py","src/covalent_ext/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate.py","src/covalent_ext/covapie_bulk_download_admission_admit_010_rule_logic_interface.py","src/covalent_ext/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate.py","src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010.py","scripts/check_covapie_staged_commit_safety.py","src/covalent_ext/covapie_legacy_pipeline_retirement_policy.py")
SOURCE_SHAS="999a126cab9e189adf5206b1972cd8db0a7ea5de4aefb7182744c5cec108b99a 8e4ebee6b82cb6a63d291e97dd118596d07a254decf6d36803c2e2a9895471b1 3ba029d388bdf860361202de27283abb337b3372cca66b3c9425abaacf8788e7 09a738c169fd3819290060ceb743cef2a9594def200b4625d4d82349eb896af0 2a5caae4ef52400710ddc70cb374f618fccbfdfeb8d2f3e8326586f58ce4b48c 9fe10646888b0197102816fade40b2162a2a375318736207e3d1b655415a257c f59eecc7136ebdd148f2c6c6422b7a2bc0637e340322e09bc005eb00355db03c 9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc 44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710 a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1 1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0 bf20595836e9b178252d37ca72229641a466b97e7510d2ff535e015599110f26 3649971eec020c5981a3ba8bfddeb604797f8557fb6036efd6094a2b0d6ab4e4 9fc1ca277220da3dd982e72c4198e74af911d4cc9d4df39e4864cb8ea0fe1c30 cbff1bd3fe4e6d65c9be33a5efee4d80ea1f9310cb7cb73e45dc4e1055a2de05 05a89049fca65b6f9d9480392eb57b333a1960064fbd6c2c5061efeac3bb9a1c dd2f88da8024d75d9b4fd9f1b8698a402c3395ebbfca6c9f17b0e19b84bb5095 b613321aa1563c7c559208fc08cf82d1e2ccee07cdc6b9c8c338d87b14c78436 055b26efe5d58f4a6f069a6afc506948a1f987547e78fd15e08051c8bfdfc590 2ce3af6de11e1af7965ca7bfa8a65847e8e782882bfe4ac4edcd78547fbb70a8".split()
SOURCE_SHA256=dict(zip(SOURCE_PATHS,SOURCE_SHAS,strict=True)); PATH_LIST_SHA="e18394c632a04531d64ed48a00ff7f90114d409c713b0f1cfa1d6a6224a13cec"; PAIRS_SHA="b1a21c1d48b0a320264801056839d0962ad23c32d1ca5676fb7735ec4859b948"
def _sha(value):return hashlib.sha256(value).hexdigest()
def _run_git(args,*,text=True):return subprocess.run(["git",*args],cwd=ROOT,capture_output=True,text=text,check=False)
def _base(path):
    result=_run_git(["show",f"{BASE}:{path}"],text=False);assert result.returncode==0 and type(result.stdout) is bytes
    return result.stdout
def _canon(value):return json.dumps(value,ensure_ascii=True,separators=(",",":"),sort_keys=False).encode()
def _read_csv(data,header):
    reader=csv.DictReader(io.StringIO(data.decode()));assert tuple(reader.fieldnames or ())==header;return list(reader)
def _safe_source_path(path):
    if type(path) is not str or not path or "\\" in path:return False
    item=PurePosixPath(path)
    return path==item.as_posix() and not item.is_absolute() and bool(item.parts) and "." not in item.parts and ".." not in item.parts and item.parts[0]!="checkpoints" and item.parts[:2]!=("data","raw")
def _live_root():
    metadata=os.lstat(ROOT);assert ROOT.is_absolute() and stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode) and ROOT.resolve(strict=True)==ROOT
    return ROOT
def _validate_live_source_configuration():
    assert len(SOURCE_PATHS)==len(SOURCE_SHA256)==21 and tuple(SOURCE_SHA256)==SOURCE_PATHS and len(set(SOURCE_PATHS))==21
    assert _sha(_canon(list(SOURCE_PATHS)))==PATH_LIST_SHA and _sha(_canon([[p,SOURCE_SHA256[p]] for p in SOURCE_PATHS]))==PAIRS_SHA
    assert all(_safe_source_path(path) and STAGE not in path for path in SOURCE_PATHS)
def _validate_live_base_lineage():
    subject=_run_git(["show","-s","--format=%s",BASE]);ancestor=_run_git(["merge-base","--is-ancestor",BASE,"HEAD"])
    assert subject.returncode==ancestor.returncode==0 and subject.stdout.strip()==SUBJECT
def _live_source_structure(path,root):
    assert _safe_source_path(path)
    absolute=root/path;current=absolute.parent
    while current!=root:
        metadata=os.lstat(current);assert stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
        current=current.parent
    leaf=os.lstat(absolute);assert stat.S_ISREG(leaf.st_mode) and not stat.S_ISLNK(leaf.st_mode)
    tracked=_run_git(["ls-files","--error-unmatch","--",path]);tree=_run_git(["ls-tree",BASE,"--",path])
    lines=tree.stdout.splitlines();entry=lines[0].split("\t",1) if len(lines)==1 else [];metadata=entry[0].split() if entry else []
    assert tracked.returncode==tree.returncode==0 and len(entry)==2 and entry[1]==path and len(metadata)==3 and metadata[0] in ("100644","100755") and metadata[1]=="blob"
    resolved=absolute.resolve(strict=True);assert resolved==absolute and root in (resolved,*resolved.parents)
    return metadata[0]
def _live_boundary_rows():
    root=_live_root();_validate_live_base_lineage();_validate_live_source_configuration()
    modes={path:_live_source_structure(path,root) for path in SOURCE_PATHS}
    rows=[]
    for path in SOURCE_PATHS:
        base=_run_git(["show",f"{BASE}:{path}"],text=False);assert base.returncode==0 and type(base.stdout) is bytes
        current=(root/path).read_bytes();expected=SOURCE_SHA256[path];base_sha=_sha(base.stdout);filesystem_sha=_sha(current)
        assert expected==base_sha==filesystem_sha
        rows.append({"source_order":str(len(rows)+1),"source_relative_path":path,"expected_sha256":expected,"base_tree_sha256":base_sha,"filesystem_sha256":filesystem_sha,"frozen_snapshot_sha256":filesystem_sha,"git_tracked":"true","base_tree_blob":"true","base_tree_mode":modes[path],"filesystem_regular":"true","non_symlink":"true","parent_chain_non_symlink":"true","safe_descendant":"true","resolved_identity_passed":"true","source_boundary_passed":"true"})
    return rows
CHECKER_DIRECTORY_FLAGS=os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC
CHECKER_FILE_FLAGS=os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC
def _identity(item):return (int(item.st_dev),int(item.st_ino),int(item.st_mode))
def _assert_real_parent_chain(parent,anchor):
    current=parent
    while True:
        item=os.lstat(current);assert stat.S_ISDIR(item.st_mode) and not stat.S_ISLNK(item.st_mode)
        if current==anchor:break
        assert current!=current.parent;current=current.parent
    assert parent.resolve(strict=True)==parent
def _require_output_read_capabilities():
    assert all(hasattr(os,name) for name in ("O_DIRECTORY","O_NOFOLLOW","O_CLOEXEC")) and all(fn in os.supports_dir_fd for fn in (os.open,os.stat))
class _PinnedOutputTree:
    __slots__=("root","parent","parent_identity","root_identity","leaf_identities","root_fd")
    def __init__(self,root,parent,parent_identity,root_identity,leaf_identities,root_fd):self.root=root;self.parent=parent;self.parent_identity=parent_identity;self.root_identity=root_identity;self.leaf_identities=leaf_identities;self.root_fd=root_fd
def _open_output_tree_readonly(root):
    _require_output_read_capabilities();candidate=Path(root);relative=not candidate.is_absolute();root=(ROOT/candidate) if relative else candidate;anchor=ROOT if relative else Path(root.anchor);parent=root.parent
    assert root.is_absolute() and root.name and (not relative or ROOT in (parent,*parent.parents));_assert_real_parent_chain(parent,anchor);parent_identity=_identity(os.lstat(parent))
    root_stat=os.lstat(root);assert stat.S_ISDIR(root_stat.st_mode) and not stat.S_ISLNK(root_stat.st_mode) and root.resolve(strict=True)==root
    root_fd=os.open(os.fspath(root),CHECKER_DIRECTORY_FLAGS)
    try:
        root_identity=_identity(root_stat);assert _identity(os.fstat(root_fd))==root_identity and _identity(os.lstat(root))==root_identity
        assert set(os.listdir(root_fd))==set(FILES)
        leaves=[]
        for name in FILES:
            item=os.stat(name,dir_fd=root_fd,follow_symlinks=False);assert stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode)
            file_fd=os.open(name,CHECKER_FILE_FLAGS,dir_fd=root_fd)
            try:assert _identity(os.fstat(file_fd))==_identity(item)
            finally:os.close(file_fd)
            leaves.append((name,_identity(item)))
        return _PinnedOutputTree(root,parent,parent_identity,root_identity,tuple(leaves),root_fd)
    except BaseException:
        os.close(root_fd);raise
def _read_pinned_output_bytes(tree):
    assert _identity(os.lstat(tree.parent))==tree.parent_identity and _identity(os.fstat(tree.root_fd))==tree.root_identity and _identity(os.lstat(tree.root))==tree.root_identity and tree.root.resolve(strict=True)==tree.root and set(os.listdir(tree.root_fd))==set(FILES)
    content={}
    for name,identity in tree.leaf_identities:
        item=os.stat(name,dir_fd=tree.root_fd,follow_symlinks=False);assert _identity(item)==identity and stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode)
        file_fd=os.open(name,CHECKER_FILE_FLAGS,dir_fd=tree.root_fd)
        try:
            assert _identity(os.fstat(file_fd))==identity;chunks=[]
            while True:
                chunk=os.read(file_fd,65536)
                if not chunk:break
                chunks.append(chunk)
            assert _identity(os.fstat(file_fd))==identity and _identity(os.stat(name,dir_fd=tree.root_fd,follow_symlinks=False))==identity
            content[name]=b"".join(chunks)
        finally:os.close(file_fd)
    assert _identity(os.lstat(tree.parent))==tree.parent_identity and _identity(os.fstat(tree.root_fd))==tree.root_identity and _identity(os.lstat(tree.root))==tree.root_identity
    return content
def _schema_rows():
    values=("covapie_raw_target_relative_path_contract_v1","covapie_raw_target_relative_path_contract_v1","covapie_repository_raw_root_v1","repository_relative_posix_lexical_path","('data/raw/',)","covapie_posix_relative_path_lexical_v1","exact_canonical_lexical_string_case_sensitive","case_sensitive","already_canonical_no_repair","forbidden","ASCII_only_no_unicode_normalization","pre_download","any_occupied_object_blocks_exact_target","pure_in_memory_no_filesystem_network_or_raw_read","none","covapie_existing_raw_target_relative_paths_snapshot_v1","covapie_repository_raw_root_v1","repository_relative_posix_lexical_path","covapie_posix_relative_path_lexical_v1","exact_canonical_lexical_string_case_sensitive","pre_download","True","()")
    rows=[]
    for field,value in zip((*CONTRACT_FIELDS,*SNAPSHOT_FIELDS),values,strict=True):
        obj="RawTargetRelativePathContract" if len(rows)<15 else "ExistingRawTargetRelativePathsSnapshot"; typ="exact built-in bool" if field=="snapshot_complete" else "exact built-in tuple" if field in ("allowed_namespace_prefixes","occupied_relative_paths") else "exact built-in str"
        rows.append({"order":str(len(rows)+1),"object":obj,"field":field,"exact_type":typ,"exact_value":value,"passed":"true"})
    return rows
def _row(order,case_id,group,candidate,contract_state,snapshot_state,reason,precedence):
    canonical="" if reason in SCALAR else candidate
    outcome="passed" if reason=="" else "blocked" if reason==COLLISION else "invalid"
    contexts=[] if reason in SCALAR else [CONTRACT_CONTEXT] if reason in CONTRACT else [CONTRACT_CONTEXT,SNAPSHOT_CONTEXT]
    return {"case_order":str(order),"case_id":case_id,"matrix_group":group,"candidate_representation":repr(candidate),"contract_state":contract_state,"snapshot_state":snapshot_state,"outcome":outcome,"passed":str(outcome=="passed").lower(),"blocks_candidate":str(outcome!="passed").lower(),"reason":reason,"canonical":canonical,"validated_candidate_fields":json.dumps((),separators=(",",":")) if not canonical else json.dumps(((FIELD,canonical),),separators=(",",":")),"consumed_candidate_fields":json.dumps((FIELD,),separators=(",",":")),"consumed_context_items":json.dumps(tuple(contexts),separators=(",",":")),"evaluator_io_used":"false","expected_precedence":precedence,"case_passed":"true"}
def _truth_rows():
    observed=_read_csv(_base("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_011_raw_target_observed_value_inventory.csv"),("value_order","source_relative_path","source_sha256","container_kind","field_location","observed_value","value_state","grammar_promoted","evaluator_usable"));assert len(observed)==47
    rows=[]
    for item in observed:rows.append(_row(len(rows)+1,f"HIST_{len(rows)+1:03d}","historical_observed",item["observed_value"],"valid_contract","valid_snapshot","","passed"))
    scalar_values=(None,"","data/raw/café","data/raw/a\0","data/raw/a\x01","data/raw/a b","/data/raw/../a","C:\\data/raw/a","\\\\srv\\x","https://x//y","data/raw/%2e%2e","~/data/raw/a","$ROOT/data/raw/a","data/raw\\a","data/raw/a/","data/raw//a","data/raw/./a","data/raw/../a","docs/a")
    for value,reason,precedence in zip(scalar_values,SCALAR,PRECEDENCE[:19],strict=True):rows.append(_row(len(rows)+1,f"SCALAR_{len(rows)-46:03d}","scalar_reason",value,"valid_contract","valid_snapshot",reason,precedence))
    fixed=(("CONTRACT_TYPE","contract_reason","data/raw/a.cif","type_invalid","not_consumed",CONTRACT[0],"contract_type"),("CONTRACT_VALUE","contract_reason","data/raw/a.cif","value_invalid","not_consumed",CONTRACT[1],"contract_value"),("SNAPSHOT_TYPE","snapshot_reason","data/raw/a.cif","valid_contract","type_invalid",SNAPSHOT[0],"snapshot_type"),("SNAPSHOT_VALUE","snapshot_reason","data/raw/a.cif","valid_contract","value_invalid",SNAPSHOT[1],"snapshot_value"))
    for case in fixed:rows.append(_row(len(rows)+1,*case))
    for case_id,state,reason,precedence in (("MISMATCH_001","canonical_raw_root_identity",SNAPSHOT[2],"context_root"),("MISMATCH_002","candidate_coordinate_system",SNAPSHOT[3],"context_coordinate"),("MISMATCH_003","path_grammar_version",SNAPSHOT[4],"context_grammar"),("MISMATCH_004","equality_policy",SNAPSHOT[5],"context_equality"),("MISMATCH_005","snapshot_phase",SNAPSHOT[6],"context_phase")):rows.append(_row(len(rows)+1,case_id,"cross_context_mismatch","data/raw/a.cif","valid_contract",state,reason,precedence))
    rest=(("COLLISION","collision","data/raw/a.cif","valid_contract","occupied",COLLISION,"exact_occupied_collision"),("PASSED","passed","data/raw/a.cif","valid_contract","empty","","passed"),("MULTI_NONASCII_WHITESPACE","multi_invalid","data/raw/café x","valid_contract","valid_snapshot",SCALAR[2],"scalar_ascii"),("MULTI_ABSOLUTE_DOTDOT","multi_invalid","/data/raw/../a","valid_contract","valid_snapshot",SCALAR[6],"scalar_absolute"),("MULTI_WINDOWS_BACKSLASH","multi_invalid","C:\\data/raw\\a","valid_contract","valid_snapshot",SCALAR[7],"scalar_windows_drive"),("MULTI_URI_REPEATED","multi_invalid","https://x//y","valid_contract","valid_snapshot",SCALAR[9],"scalar_uri"),("MULTI_PERCENT_TRAVERSAL","multi_invalid","data/raw/%2e%2e/a","valid_contract","valid_snapshot",SCALAR[10],"scalar_percent"),("MULTI_SCALAR_CONTRACT","multi_invalid","docs/a","type_invalid","not_consumed",SCALAR[18],"scalar_namespace"),("MULTI_CONTRACT_SNAPSHOT","multi_invalid","data/raw/a.cif","type_invalid","type_invalid",CONTRACT[0],"contract_type"))
    for case in rest:rows.append(_row(len(rows)+1,*case))
    assert len(rows)==84 and {r["reason"] for r in rows}==set(REASONS) and {r["expected_precedence"] for r in rows}==set(PRECEDENCE)
    return rows,observed
def _issue_rows():
    path="data/derived/covalent_small/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_011_formal_evaluator_issue_readiness_inventory.csv"; raw=_base(path);rows=_read_csv(raw,("issue_id","issue_type","affected_fields","affected_rules","severity","status","blocking_scope","blocking_reason","issue_origin","integration_transition","issue_count"))
    for row in rows:
        if row["issue_id"]=="RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED":row["status"]="resolved";row["integration_transition"]="resolved_by_raw_target_relative_path_contract_v1"
    return rows,raw
def _coverage_rows(observed):return [{"coverage_order":str(i),"source_relative_path":r["source_relative_path"],"source_sha256":r["source_sha256"],"source_occurrence":r["field_location"],"observed_value":r["observed_value"],"accepted":"true","expected_canonical_value":r["observed_value"],"coverage_passed":"true"} for i,r in enumerate(observed,1)]
def _responsibility_rows():return [{"role_order":str(i),"role":a,"boundary":b,"implemented":"false"} for i,(a,b) in enumerate((("standalone_evaluator","scalar + two exact context objects only"),("future_unified_adapter","candidate/evaluation/batch envelope and identity routing"),("snapshot_provider","filesystem namespace enumeration before call"),("ADMIT_012_013","post-download result/integrity"),("stage_authorization","separate authority")),1)]
def _validate_output_tree(root=ROOT/EXPECTED_OUTPUT_ROOT,*,enforce_frozen_hashes=True):
    tree=_open_output_tree_readonly(root)
    try:
        boundary=_live_boundary_rows()
        content=_read_pinned_output_bytes(tree)
    finally:os.close(tree.root_fd)
    for name in FILES:
        if enforce_frozen_hashes:assert _sha(content[name])==FROZEN_HASHES[name]
    truth,observed=_truth_rows();assert _read_csv(content[FILES[1]],TRUTH_HEADER)==truth
    assert _read_csv(content[FILES[0]],SCHEMA_HEADER)==_schema_rows()
    coverage_header=("coverage_order","source_relative_path","source_sha256","source_occurrence","observed_value","accepted","expected_canonical_value","coverage_passed");assert _read_csv(content[FILES[3]],coverage_header)==_coverage_rows(observed)
    issue,raw=_issue_rows();assert _read_csv(content[FILES[4]],tuple(issue[0]))==issue
    responsibility_header=("role_order","role","boundary","implemented");assert _read_csv(content[FILES[2]],responsibility_header)==_responsibility_rows()
    assert _read_csv(content[FILES[5]],BOUNDARY_HEADER)==boundary
    m=json.loads(content[FILES[6]]);keys={"manifest_schema_version","stage","base_commit","base_subject","admission_rule_id","admission_rule_name","source_input_count","source_path_list_sha256","source_path_sha256_pairs_sha256","source_paths_sha256","predecessor_source_boundary_count","predecessor_occurrence_count","predecessor_observed_value_count","predecessor_issue_count","predecessor_observed_value_state_counts","source_structure_checks_completed_before_byte_read","all_source_base_tree_blob_verified","all_source_parent_chains_non_symlink","all_source_resolved_identity_verified","source_boundary_output_sha256","source_attestation_passed","output_files","output_file_count","row_counts","contract_class","contract_fields","snapshot_class","snapshot_fields","coordinate_system","allowed_namespace_prefixes","reason_vocabulary","validation_precedence","issue_inventory_count","issue_inventory_sha256","coverage_affected_rules","feature_semantics_audit_required_before_training","step12d_is_final_training_feature_contract","step12d_status","readiness","safety","materializer_safety","recommended_next_step","all_checks_passed","validation_failures","output_sha256"};assert set(m)==keys
    true_keys={"raw_target_relative_path_contract_frozen","relative_path_grammar_frozen","lexical_resolved_boundary_frozen","raw_root_identity_contract_frozen","raw_namespace_allowlist_frozen","occupied_snapshot_contract_frozen","exact_context_object_schemas_frozen","standalone_scalar_context_boundary_frozen","reason_vocabulary_and_precedence_frozen","context_responsibility_frozen","ready_for_admit_011_standalone_evaluator_interface_implementation"};false_keys={"admit_011_rule_logic_implemented","admit_011_adapter_implemented","admit_011_registered_in_engine","unified_dispatch_runtime_with_admit_001_to_011_implemented","provider_mapping_validated","real_provider_evaluation_ready","combined_candidate_verdict_implemented","ready_for_bulk_download_now","checkpoint_compatibility_validated","full_repository_canonical_validated","ready_for_training"};assert set(m["readiness"])==true_keys|false_keys and all(m["readiness"][x] is True for x in true_keys) and all(m["readiness"][x] is False for x in false_keys)
    assert m["manifest_schema_version"]=="covapie_admit_011_raw_target_relative_path_contract_manifest_v4" and m["stage"]==STAGE and m["base_commit"]==BASE and m["base_subject"]==SUBJECT and m["admission_rule_id"]=="ADMIT_011" and m["admission_rule_name"]=="raw_overwrite_forbidden" and m["contract_class"]=="RawTargetRelativePathContract" and m["contract_fields"]==list(CONTRACT_FIELDS) and m["snapshot_class"]=="ExistingRawTargetRelativePathsSnapshot" and m["snapshot_fields"]==list(SNAPSHOT_FIELDS) and m["coordinate_system"]=="repository_relative_posix_lexical_path" and m["allowed_namespace_prefixes"]==["data/raw/"] and m["coverage_affected_rules"]=="ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015" and m["recommended_next_step"]=="implement_covapie_admit_011_standalone_evaluator_interface_v1"
    assert set(m["safety"])=={"filesystem_used","network_used","raw_read","mutation"} and all(v is False for v in m["safety"].values()) and m["row_counts"]=={"schema":23,"truth":84,"truth_historical":47,"observed_coverage":47,"issue":11,"responsibility":5,"source_boundary":21} and m["validation_precedence"]==list(PRECEDENCE) and m["reason_vocabulary"]==list(REASONS) and m["source_input_count"]==21 and m["output_files"]==list(FILES) and m["output_file_count"]==7 and m["issue_inventory_count"]==11 and m["validation_failures"]==[] and m["all_checks_passed"] is True and m["feature_semantics_audit_required_before_training"] is True and m["step12d_is_final_training_feature_contract"] is False and m["step12d_status"]=="smoke_legality_only_not_final_training_feature_contract"
    assert m["source_path_list_sha256"]==PATH_LIST_SHA and m["source_path_sha256_pairs_sha256"]==PAIRS_SHA and tuple(m["source_paths_sha256"])==SOURCE_PATHS and m["source_paths_sha256"]==SOURCE_SHA256 and m["predecessor_source_boundary_count"]==99 and m["predecessor_occurrence_count"]==172 and m["predecessor_observed_value_count"]==47 and m["predecessor_issue_count"]==11 and m["predecessor_observed_value_state_counts"]=={"present_historical_or_fixture_value":47,"missing_empty":0,"missing_null_like":0} and all(m[x] is True for x in ("source_structure_checks_completed_before_byte_read","all_source_base_tree_blob_verified","all_source_parent_chains_non_symlink","all_source_resolved_identity_verified","source_attestation_passed")) and m["source_boundary_output_sha256"]==_sha(content[FILES[5]]) and m["issue_inventory_sha256"]==_sha(content[FILES[4]])
    assert set(m["materializer_safety"])==set(MATERIALIZER_SAFETY_KEYS) and all(m["materializer_safety"][key] is True for key in MATERIALIZER_SAFETY_KEYS)
    assert m["output_sha256"]=={name:_sha(content[name]) for name in FILES[:-1]}
    print(json.dumps({"checked":True,"output_sha256":{name:_sha(content[name]) for name in FILES}},sort_keys=True))
if __name__=="__main__":_validate_output_tree()
