"""Metadata-only ADMIT_011 raw-target relative-path contract design gate.

This module deliberately contains a design oracle, not ``evaluate_admit_011``.
It performs no raw-root, filesystem-provider, network, download, or runtime I/O.
"""
from __future__ import annotations

import csv, ctypes, hashlib, io, json, os, secrets, stat, subprocess
from dataclasses import dataclass, fields
from pathlib import Path, PurePosixPath

PROJECT="CovaPIE"; STAGE="covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1"
EXPECTED_BASE_COMMIT="a8cf1a8dcda6ebcdf1ddaf34233f61475686b417"
EXPECTED_BASE_SUBJECT="add CovaPIE ADMIT_011 evaluator preconditions audit v1"
RULE_ID="ADMIT_011"; RULE_NAME="raw_overwrite_forbidden"; CANDIDATE_FIELD="raw_target_relative_path"
REQUIRED_CONTEXT_ITEMS=("existing_raw_target_relative_paths","raw_target_relative_path_contract")
STANDALONE_CONTEXT_VALIDATION_ORDER=("raw_target_relative_path_contract","existing_raw_target_relative_paths")
# Historical declaration order remains separate from future standalone order.
CONTEXT_ITEMS=REQUIRED_CONTEXT_ITEMS
REPO_ROOT=Path(__file__).resolve().parents[2]; OUTPUT_ROOT=Path("data/derived/covalent_small")/STAGE
CONTRACT_FILE="covapie_admit_011_raw_target_relative_path_contract_schema_matrix.csv"; TRUTH_FILE="covapie_admit_011_raw_target_relative_path_grammar_truth_matrix.csv"; RESPONSIBILITY_FILE="covapie_admit_011_raw_target_context_responsibility_matrix.csv"; OBSERVED_FILE="covapie_admit_011_raw_target_observed_value_coverage_matrix.csv"; ISSUE_FILE="covapie_admit_011_raw_target_issue_readiness_inventory.csv"; BOUNDARY_FILE="covapie_admit_011_raw_target_contract_source_boundary_audit.csv"; MANIFEST_FILE="covapie_admit_011_raw_target_relative_path_contract_manifest.json"
OUTPUT_FILES=(CONTRACT_FILE,TRUTH_FILE,RESPONSIBILITY_FILE,OBSERVED_FILE,ISSUE_FILE,BOUNDARY_FILE,MANIFEST_FILE)
FROZEN_CSV_SHA256={CONTRACT_FILE:"dd5f853c047c7457d110739edf6f2ac3647bc3a9069b2b7a6d15b1470504f13e",TRUTH_FILE:"1b32c3cc658433da18b804336afec8c63a275bcf44f68556faf75804e3b386ca",RESPONSIBILITY_FILE:"0f3772e65db51623fe7ab477e97cc7fc98166755f39d172ef017a87c7ebfba24",OBSERVED_FILE:"c55c48b58a66b44b2f6f0cc7fde27fe22fa317e3502a7eee9ee06c25006b74a2",ISSUE_FILE:"eb36931b833800c4a7c9dffa33a690c4197ba0bb161cfbda742b90c3b3d8d1c0",BOUNDARY_FILE:"e0747e6b3be3a51d1884a76a85f70b05d34d4f687b20e2604f56783db985840f"}
MATERIALIZER_SAFETY_KEYS=("initial_output_preflight_before_source_bytes","no_output_mutation_before_artifacts_built","parent_chain_non_symlink","broken_symlink_rejected","missing_parent_creation_forbidden","root_identity_revalidated_before_write","existing_leaf_identity_revalidated_before_write","directory_fd_pinned","temporary_files_same_directory","temporary_files_exclusive_non_symlink","file_fsync_before_publish","atomic_publish_via_directory_fd","directory_fsync_after_publish","postwrite_inventory_verified","postwrite_bytes_and_sha_verified","temporary_files_cleaned_on_failure","newly_created_root_cleanup_on_failure","materializer_hardening_passed")
MATERIALIZER_SAFETY={key:True for key in MATERIALIZER_SAFETY_KEYS}
CONTRACT_FIELDS=("schema_version","contract_id","canonical_raw_root_identity","candidate_coordinate_system","allowed_namespace_prefixes","path_grammar_version","equality_policy","case_policy","normalization_policy","percent_decoding_policy","unicode_policy","snapshot_phase","occupied_path_policy","evaluator_io_policy","mutation_policy")
SNAPSHOT_FIELDS=("schema_version","canonical_raw_root_identity","candidate_coordinate_system","path_grammar_version","equality_policy","snapshot_phase","snapshot_complete","occupied_relative_paths")
RESULT_FIELDS=("admission_rule_id","outcome","passed","blocks_candidate","reason","canonical_raw_target_relative_path","validated_candidate_fields","consumed_candidate_fields","consumed_context_items","evaluator_io_used")
SCALAR_REASONS=("RAW_TARGET_RELATIVE_PATH_TYPE_INVALID","RAW_TARGET_RELATIVE_PATH_EMPTY","RAW_TARGET_RELATIVE_PATH_NON_ASCII_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_NUL_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_CONTROL_CHARACTER_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_WHITESPACE_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_ABSOLUTE_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_WINDOWS_DRIVE_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_UNC_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_URI_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_PERCENT_ENCODING_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_TILDE_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_ENVIRONMENT_EXPANSION_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_BACKSLASH_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_TRAILING_SEPARATOR","RAW_TARGET_RELATIVE_PATH_REPEATED_SEPARATOR","RAW_TARGET_RELATIVE_PATH_DOT_COMPONENT_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_DOTDOT_COMPONENT_FORBIDDEN","RAW_TARGET_RELATIVE_PATH_NAMESPACE_FORBIDDEN")
CONTRACT_REASONS=("RAW_TARGET_RELATIVE_PATH_CONTRACT_TYPE_INVALID","RAW_TARGET_RELATIVE_PATH_CONTRACT_VALUE_INVALID")
SNAPSHOT_REASONS=("EXISTING_RAW_TARGET_RELATIVE_PATHS_SNAPSHOT_TYPE_INVALID","EXISTING_RAW_TARGET_RELATIVE_PATHS_SNAPSHOT_VALUE_INVALID","RAW_TARGET_CONTEXT_ROOT_IDENTITY_MISMATCH","RAW_TARGET_CONTEXT_COORDINATE_SYSTEM_MISMATCH","RAW_TARGET_CONTEXT_GRAMMAR_MISMATCH","RAW_TARGET_CONTEXT_EQUALITY_POLICY_MISMATCH","RAW_TARGET_CONTEXT_PHASE_MISMATCH")
COLLISION_REASON="RAW_TARGET_RELATIVE_PATH_ALREADY_OCCUPIED"
REASON_VOCABULARY=("",*SCALAR_REASONS,*CONTRACT_REASONS,*SNAPSHOT_REASONS,COLLISION_REASON)
VALIDATION_PRECEDENCE=("scalar_type","scalar_empty","scalar_ascii","scalar_nul","scalar_control","scalar_whitespace","scalar_absolute","scalar_windows_drive","scalar_unc","scalar_uri","scalar_percent","scalar_tilde","scalar_environment","scalar_backslash","scalar_trailing_separator","scalar_repeated_separator","scalar_dot","scalar_dotdot","scalar_namespace","contract_type","contract_value","snapshot_type","snapshot_value","context_root","context_coordinate","context_grammar","context_equality","context_phase","exact_occupied_collision","passed")

@dataclass(frozen=True)
class RawTargetRelativePathContract:
    schema_version:str; contract_id:str; canonical_raw_root_identity:str; candidate_coordinate_system:str; allowed_namespace_prefixes:tuple; path_grammar_version:str; equality_policy:str; case_policy:str; normalization_policy:str; percent_decoding_policy:str; unicode_policy:str; snapshot_phase:str; occupied_path_policy:str; evaluator_io_policy:str; mutation_policy:str
    def __post_init__(self):
        if type(self) is not RawTargetRelativePathContract or tuple(x.name for x in fields(type(self)))!=CONTRACT_FIELDS: raise TypeError("exact RawTargetRelativePathContract required")
        if any(type(getattr(self,n)) is not str for n in CONTRACT_FIELDS if n!="allowed_namespace_prefixes") or type(self.allowed_namespace_prefixes) is not tuple or any(type(x) is not str for x in self.allowed_namespace_prefixes): raise TypeError("contract requires exact built-ins")
        if "DEFAULT_CONTRACT" in globals() and self!=DEFAULT_CONTRACT: raise ValueError("contract values differ from v1")

@dataclass(frozen=True)
class ExistingRawTargetRelativePathsSnapshot:
    schema_version:str; canonical_raw_root_identity:str; candidate_coordinate_system:str; path_grammar_version:str; equality_policy:str; snapshot_phase:str; snapshot_complete:bool; occupied_relative_paths:tuple
    def __post_init__(self):
        if type(self) is not ExistingRawTargetRelativePathsSnapshot or tuple(x.name for x in fields(type(self)))!=SNAPSHOT_FIELDS: raise TypeError("exact ExistingRawTargetRelativePathsSnapshot required")
        if any(type(getattr(self,n)) is not str for n in SNAPSHOT_FIELDS[:6]) or type(self.snapshot_complete) is not bool or type(self.occupied_relative_paths) is not tuple or any(type(x) is not str for x in self.occupied_relative_paths): raise TypeError("snapshot requires exact built-ins")
        if self.schema_version!="covapie_existing_raw_target_relative_paths_snapshot_v1" or self.snapshot_complete is not True or len(set(self.occupied_relative_paths))!=len(self.occupied_relative_paths) or ("_scalar_reason" in globals() and any(_scalar_reason(member) for member in self.occupied_relative_paths)): raise ValueError("snapshot v1 invariant invalid")

DEFAULT_CONTRACT=RawTargetRelativePathContract("covapie_raw_target_relative_path_contract_v1","covapie_raw_target_relative_path_contract_v1","covapie_repository_raw_root_v1","repository_relative_posix_lexical_path",("data/raw/",),"covapie_posix_relative_path_lexical_v1","exact_canonical_lexical_string_case_sensitive","case_sensitive","already_canonical_no_repair","forbidden","ASCII_only_no_unicode_normalization","pre_download","any_occupied_object_blocks_exact_target","pure_in_memory_no_filesystem_network_or_raw_read","none")

@dataclass(frozen=True)
class Admit011EvaluationResultDesign:
    admission_rule_id:str; outcome:str; passed:bool; blocks_candidate:bool; reason:str; canonical_raw_target_relative_path:str; validated_candidate_fields:tuple; consumed_candidate_fields:tuple; consumed_context_items:tuple; evaluator_io_used:bool
    def __post_init__(self):
        if type(self) is not Admit011EvaluationResultDesign or tuple(x.name for x in fields(type(self)))!=RESULT_FIELDS: raise TypeError("exact result design required")
        if any(type(v) is not str for v in (self.admission_rule_id,self.outcome,self.reason,self.canonical_raw_target_relative_path)): raise TypeError("result string fields require exact built-in str")
        if type(self.passed) is not bool or type(self.blocks_candidate) is not bool or type(self.evaluator_io_used) is not bool: raise TypeError("result booleans require exact built-in bool")
        if any(type(v) is not tuple for v in (self.validated_candidate_fields,self.consumed_candidate_fields,self.consumed_context_items)): raise TypeError("result tuple fields require exact built-in tuple")
        if any(type(pair) is not tuple or len(pair)!=2 or any(type(x) is not str for x in pair) for pair in self.validated_candidate_fields): raise TypeError("validated fields require exact string-pair tuples")
        if any(type(x) is not str for x in self.consumed_candidate_fields+self.consumed_context_items): raise TypeError("consumed fields require exact string tuples")
        if self.admission_rule_id!=RULE_ID or self.outcome not in ("passed","blocked","invalid") or self.passed is not (self.outcome=="passed") or self.blocks_candidate is not (self.outcome!="passed") or self.reason not in REASON_VOCABULARY or (self.reason=="") is not (self.outcome=="passed") or self.evaluator_io_used is not False or self.consumed_candidate_fields!=(CANDIDATE_FIELD,): raise ValueError("result invariant invalid")
        if self.reason==COLLISION_REASON:
            if self.outcome!="blocked": raise ValueError("collision is blocked only")
        elif self.reason!="" and self.outcome!="invalid": raise ValueError("noncollision reason is invalid only")
        expected=() if self.canonical_raw_target_relative_path=="" else ((CANDIDATE_FIELD,self.canonical_raw_target_relative_path),)
        if self.validated_candidate_fields!=expected: raise ValueError("validated candidate fields mismatch canonical state")
        if self.canonical_raw_target_relative_path!="" and not _is_canonical_raw_target_relative_path(self.canonical_raw_target_relative_path): raise ValueError("retained canonical path is not canonical")
        if self.reason in SCALAR_REASONS:
            if self.canonical_raw_target_relative_path!="" or self.consumed_context_items!=(): raise ValueError("scalar invalid consumption mismatch")
        elif self.reason in CONTRACT_REASONS:
            if not self.canonical_raw_target_relative_path or self.consumed_context_items!=(STANDALONE_CONTEXT_VALIDATION_ORDER[0],): raise ValueError("contract invalid consumption mismatch")
        else:
            if not self.canonical_raw_target_relative_path or self.consumed_context_items!=STANDALONE_CONTEXT_VALIDATION_ORDER: raise ValueError("snapshot/passed consumption mismatch")

def _scalar_reason(value:object, contract:RawTargetRelativePathContract=DEFAULT_CONTRACT)->str:
    if type(value) is not str:return SCALAR_REASONS[0]
    if value=="":return SCALAR_REASONS[1]
    if not value.isascii():return SCALAR_REASONS[2]
    if "\0" in value:return SCALAR_REASONS[3]
    if any(ord(x)<32 or ord(x)==127 for x in value):return SCALAR_REASONS[4]
    if any(x.isspace() for x in value):return SCALAR_REASONS[5]
    if value.startswith("/"):return SCALAR_REASONS[6]
    if len(value)>1 and value[1]==":" and value[0].isalpha():return SCALAR_REASONS[7]
    if value.startswith("\\\\"):return SCALAR_REASONS[8]
    if "://" in value:return SCALAR_REASONS[9]
    if "%" in value:return SCALAR_REASONS[10]
    if value.startswith("~"):return SCALAR_REASONS[11]
    if "$" in value:return SCALAR_REASONS[12]
    if "\\" in value:return SCALAR_REASONS[13]
    if value.endswith("/"):return SCALAR_REASONS[14]
    if "//" in value:return SCALAR_REASONS[15]
    parts=value.split("/")
    if "." in parts:return SCALAR_REASONS[16]
    if ".." in parts:return SCALAR_REASONS[17]
    if not any(value.startswith(p) for p in contract.allowed_namespace_prefixes):return SCALAR_REASONS[18]
    return ""

def _is_canonical_raw_target_relative_path(value:object)->bool:
    """Design-only predicate; it performs no normalization or filesystem I/O."""
    return type(value) is str and _scalar_reason(value)==""

def classify_admit_011_raw_target_relative_path_design(raw_target_relative_path_object:object, existing_raw_target_relative_paths_snapshot_object:object, raw_target_relative_path_contract_object:object)->Admit011EvaluationResultDesign:
    """Design oracle only; future production evaluator must not call this function."""
    scalar=_scalar_reason(raw_target_relative_path_object)
    if scalar:return Admit011EvaluationResultDesign(RULE_ID,"invalid",False,True,scalar,"",(),(CANDIDATE_FIELD,),(),False)
    canonical=raw_target_relative_path_object
    if type(raw_target_relative_path_contract_object) is not RawTargetRelativePathContract:return Admit011EvaluationResultDesign(RULE_ID,"invalid",False,True,CONTRACT_REASONS[0],canonical,((CANDIDATE_FIELD,canonical),),(CANDIDATE_FIELD,),(STANDALONE_CONTEXT_VALIDATION_ORDER[0],),False)
    try: raw_target_relative_path_contract_object.__post_init__()
    except (TypeError,ValueError): return Admit011EvaluationResultDesign(RULE_ID,"invalid",False,True,CONTRACT_REASONS[1],canonical,((CANDIDATE_FIELD,canonical),),(CANDIDATE_FIELD,),(STANDALONE_CONTEXT_VALIDATION_ORDER[0],),False)
    if type(existing_raw_target_relative_paths_snapshot_object) is not ExistingRawTargetRelativePathsSnapshot:return Admit011EvaluationResultDesign(RULE_ID,"invalid",False,True,SNAPSHOT_REASONS[0],canonical,((CANDIDATE_FIELD,canonical),),(CANDIDATE_FIELD,),STANDALONE_CONTEXT_VALIDATION_ORDER,False)
    try: existing_raw_target_relative_paths_snapshot_object.__post_init__()
    except (TypeError,ValueError): return Admit011EvaluationResultDesign(RULE_ID,"invalid",False,True,SNAPSHOT_REASONS[1],canonical,((CANDIDATE_FIELD,canonical),),(CANDIDATE_FIELD,),STANDALONE_CONTEXT_VALIDATION_ORDER,False)
    s=existing_raw_target_relative_paths_snapshot_object; c=raw_target_relative_path_contract_object
    checks=((s.canonical_raw_root_identity,c.canonical_raw_root_identity,SNAPSHOT_REASONS[2]),(s.candidate_coordinate_system,c.candidate_coordinate_system,SNAPSHOT_REASONS[3]),(s.path_grammar_version,c.path_grammar_version,SNAPSHOT_REASONS[4]),(s.equality_policy,c.equality_policy,SNAPSHOT_REASONS[5]),(s.snapshot_phase,c.snapshot_phase,SNAPSHOT_REASONS[6]))
    for a,b,r in checks:
        if a!=b:return Admit011EvaluationResultDesign(RULE_ID,"invalid",False,True,r,canonical,((CANDIDATE_FIELD,canonical),),(CANDIDATE_FIELD,),STANDALONE_CONTEXT_VALIDATION_ORDER,False)
    if canonical in s.occupied_relative_paths:return Admit011EvaluationResultDesign(RULE_ID,"blocked",False,True,COLLISION_REASON,canonical,((CANDIDATE_FIELD,canonical),),(CANDIDATE_FIELD,),STANDALONE_CONTEXT_VALIDATION_ORDER,False)
    return Admit011EvaluationResultDesign(RULE_ID,"passed",True,False,"",canonical,((CANDIDATE_FIELD,canonical),),(CANDIDATE_FIELD,),STANDALONE_CONTEXT_VALIDATION_ORDER,False)

SOURCE_PATHS=(
"src/covalent_ext/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit.py","data/derived/covalent_small/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_011_formal_evaluator_preconditions_manifest.json","data/derived/covalent_small/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_011_formal_evaluator_precondition_matrix.csv","data/derived/covalent_small/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_011_raw_target_field_occurrence_inventory.csv","data/derived/covalent_small/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_011_raw_target_observed_value_inventory.csv","data/derived/covalent_small/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_011_source_boundary_audit.csv","data/derived/covalent_small/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_011_formal_evaluator_issue_readiness_inventory.csv","data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv","data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_schema_contract.csv","data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_rule_executability_matrix.csv","data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_field_semantics_matrix.csv","data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv","src/covalent_ext/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate.py","src/covalent_ext/covapie_bulk_download_admission_admit_009_rule_logic_interface.py","src/covalent_ext/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate.py","src/covalent_ext/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate.py","src/covalent_ext/covapie_bulk_download_admission_admit_010_rule_logic_interface.py","src/covalent_ext/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate.py","src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010.py","scripts/check_covapie_staged_commit_safety.py","src/covalent_ext/covapie_legacy_pipeline_retirement_policy.py")
SOURCE_SHA256=dict(zip(SOURCE_PATHS,"999a126cab9e189adf5206b1972cd8db0a7ea5de4aefb7182744c5cec108b99a 8e4ebee6b82cb6a63d291e97dd118596d07a254decf6d36803c2e2a9895471b1 3ba029d388bdf860361202de27283abb337b3372cca66b3c9425abaacf8788e7 09a738c169fd3819290060ceb743cef2a9594def200b4625d4d82349eb896af0 2a5caae4ef52400710ddc70cb374f618fccbfdfeb8d2f3e8326586f58ce4b48c 9fe10646888b0197102816fade40b2162a2a375318736207e3d1b655415a257c f59eecc7136ebdd148f2c6c6422b7a2bc0637e340322e09bc005eb00355db03c 9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc 44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710 a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1 1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0 bf20595836e9b178252d37ca72229641a466b97e7510d2ff535e015599110f26 3649971eec020c5981a3ba8bfddeb604797f8557fb6036efd6094a2b0d6ab4e4 9fc1ca277220da3dd982e72c4198e74af911d4cc9d4df39e4864cb8ea0fe1c30 cbff1bd3fe4e6d65c9be33a5efee4d80ea1f9310cb7cb73e45dc4e1055a2de05 05a89049fca65b6f9d9480392eb57b333a1960064fbd6c2c5061efeac3bb9a1c dd2f88da8024d75d9b4fd9f1b8698a402c3395ebbfca6c9f17b0e19b84bb5095 b613321aa1563c7c559208fc08cf82d1e2ccee07cdc6b9c8c338d87b14c78436 055b26efe5d58f4a6f069a6afc506948a1f987547e78fd15e08051c8bfdfc590 2ce3af6de11e1af7965ca7bfa8a65847e8e782882bfe4ac4edcd78547fbb70a8".split(),strict=True))
EXPECTED_SOURCE_COUNT=21
EXPECTED_SOURCE_PATH_LIST_SHA256="e18394c632a04531d64ed48a00ff7f90114d409c713b0f1cfa1d6a6224a13cec"
EXPECTED_SOURCE_PATH_SHA256_PAIRS_SHA256="b1a21c1d48b0a320264801056839d0962ad23c32d1ca5676fb7735ec4859b948"

@dataclass(frozen=True)
class FrozenSourceRecord:
    relative_path:str; expected_sha256:str; base_tree_sha256:str; filesystem_sha256:str; frozen_snapshot_sha256:str; base_tree_mode:str; content:bytes

def _canonical_json(value):return json.dumps(value,ensure_ascii=True,separators=(",",":"),sort_keys=False).encode("utf-8")
def _git(args,*,text=True):return subprocess.run(["git",*args],cwd=REPO_ROOT,capture_output=True,text=text,check=False)
def _safe_source_path(raw):
    if type(raw) is not str or not raw or "\\" in raw:return False
    path=PurePosixPath(raw)
    return raw==path.as_posix() and not path.is_absolute() and bool(path.parts) and "." not in path.parts and ".." not in path.parts and path.parts[0]!="checkpoints" and path.parts[:2]!=("data","raw")
def _validate_source_configuration():
    successor_source=Path(__file__).resolve().relative_to(REPO_ROOT).as_posix();successor_output=OUTPUT_ROOT.as_posix()+"/"
    if len(SOURCE_PATHS)!=EXPECTED_SOURCE_COUNT or len(set(SOURCE_PATHS))!=EXPECTED_SOURCE_COUNT or len(SOURCE_SHA256)!=EXPECTED_SOURCE_COUNT or tuple(SOURCE_SHA256)!=SOURCE_PATHS or not all(_safe_source_path(raw) and raw!=successor_source and not raw.startswith(successor_output) for raw in SOURCE_PATHS):raise ValueError("source configuration invalid")
    paths=list(SOURCE_PATHS);pairs=[[raw,SOURCE_SHA256[raw]] for raw in SOURCE_PATHS]
    if hashlib.sha256(_canonical_json(paths)).hexdigest()!=EXPECTED_SOURCE_PATH_LIST_SHA256 or hashlib.sha256(_canonical_json(pairs)).hexdigest()!=EXPECTED_SOURCE_PATH_SHA256_PAIRS_SHA256:raise ValueError("source digest configuration invalid")
def _real_repo_root():
    root=REPO_ROOT
    try:metadata=os.lstat(root);resolved=root.resolve(strict=True)
    except OSError as exc:raise ValueError("repository root invalid") from exc
    if not root.is_absolute() or not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode) or resolved!=root:raise ValueError("repository root invalid")
    return resolved
def _validate_base_lineage():
    subject=_git(["show","-s","--format=%s",EXPECTED_BASE_COMMIT]);ancestor=_git(["merge-base","--is-ancestor",EXPECTED_BASE_COMMIT,"HEAD"])
    if subject.returncode or ancestor.returncode or subject.stdout.strip()!=EXPECTED_BASE_SUBJECT:raise ValueError("base lineage invalid")
def _source_structure(raw,repo):
    if not _safe_source_path(raw):raise ValueError("unsafe source path")
    absolute=repo/raw;current=absolute.parent
    while current!=repo:
        try:item=os.lstat(current)
        except OSError as exc:raise ValueError("source parent invalid") from exc
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):raise ValueError("source parent invalid")
        current=current.parent
    try:leaf=os.lstat(absolute)
    except OSError as exc:raise ValueError("source leaf invalid") from exc
    tracked=_git(["ls-files","--error-unmatch","--",raw]);tree=_git(["ls-tree",EXPECTED_BASE_COMMIT,"--",raw])
    line=tree.stdout.strip().splitlines();fields=line[0].split("\t",1) if len(line)==1 else []
    meta=fields[0].split() if fields else []
    if not stat.S_ISREG(leaf.st_mode) or stat.S_ISLNK(leaf.st_mode) or tracked.returncode or tree.returncode or len(meta)!=3 or meta[0] not in ("100644","100755") or meta[1]!="blob" or len(fields)!=2 or fields[1]!=raw:raise ValueError("source tree structure invalid")
    try:resolved=absolute.resolve(strict=True)
    except OSError as exc:raise ValueError("source resolved identity invalid") from exc
    if resolved!=absolute or repo not in (resolved,*resolved.parents):raise ValueError("source resolved identity invalid")
    return meta[0]
def _frozen_csv_rows(content,header,label):
    reader=csv.DictReader(io.StringIO(content.decode("utf-8")))
    if tuple(reader.fieldnames or ())!=header:raise ValueError(f"{label} header invalid")
    return list(reader)
def _predecessor_attestation(records):
    index={record.relative_path:record for record in records}
    manifest=json.loads(index[SOURCE_PATHS[1]].content.decode("utf-8"));required={"source_count":99,"occurrence_row_count":172,"observed_value_row_count":47,"primary_unresolved_blocker":"RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED","ready_for_admit_011_raw_target_relative_path_contract_design":True,"ready_for_admit_011_standalone_evaluator_interface_implementation":False,"feature_semantics_audit_required_before_training":True,"recommended_next_step":"design_covapie_admit_011_raw_target_relative_path_contract_v1"}
    if any(manifest.get(key)!=value for key,value in required.items()):raise ValueError("predecessor manifest attestation invalid")
    occurrence=_frozen_csv_rows(index[SOURCE_PATHS[3]].content,("occurrence_order","source_relative_path","source_sha256","source_kind","line_number","occurrence_class","text"),"predecessor occurrence")
    observed=_frozen_csv_rows(index[SOURCE_PATHS[4]].content,("value_order","source_relative_path","source_sha256","container_kind","field_location","observed_value","value_state","grammar_promoted","evaluator_usable"),"predecessor observed")
    boundary=_frozen_csv_rows(index[SOURCE_PATHS[5]].content,("source_order","source_relative_path","source_kind","base_tree_sha256","filesystem_sha256","tracked_regular_non_symlink","source_boundary_passed"),"predecessor boundary")
    issues=_frozen_csv_rows(index[SOURCE_PATHS[6]].content,("issue_id","issue_type","affected_fields","affected_rules","severity","status","blocking_scope","blocking_reason","issue_origin","integration_transition","issue_count"),"predecessor issue")
    if len(occurrence)!=172 or [row["occurrence_order"] for row in occurrence]!=[str(i) for i in range(1,173)] or len(observed)!=47 or [row["value_order"] for row in observed]!=[str(i) for i in range(1,48)] or len(boundary)!=99 or [row["source_order"] for row in boundary]!=[str(i) for i in range(1,100)] or len(issues)!=11:raise ValueError("predecessor cardinality attestation invalid")
    if any(row["source_boundary_passed"]!="true" or row["tracked_regular_non_symlink"]!="true" or row["base_tree_sha256"]!=row["filesystem_sha256"] for row in boundary) or len({row["source_relative_path"] for row in boundary})!=99:raise ValueError("predecessor boundary attestation invalid")
    states={key:sum(row["value_state"]==key for row in observed) for key in ("present_historical_or_fixture_value","missing_empty","missing_null_like")}
    if states!=manifest["observed_value_state_counts"]:raise ValueError("predecessor observed attestation invalid")
    return observed,issues,{"predecessor_source_boundary_count":99,"predecessor_occurrence_count":172,"predecessor_observed_value_count":47,"predecessor_issue_count":11,"predecessor_observed_value_state_counts":states}
def _snapshot_sources():
    repo=_real_repo_root();_validate_base_lineage();_validate_source_configuration()
    modes={raw:_source_structure(raw,repo) for raw in SOURCE_PATHS}
    records=[]
    for raw in SOURCE_PATHS:
        base=_git(["show",f"{EXPECTED_BASE_COMMIT}:{raw}"],text=False)
        if base.returncode or type(base.stdout) is not bytes:raise ValueError("base source read failed")
        current=(repo/raw).read_bytes();base_sha=hashlib.sha256(base.stdout).hexdigest();filesystem_sha=hashlib.sha256(current).hexdigest();frozen_sha=hashlib.sha256(current).hexdigest()
        if base_sha!=SOURCE_SHA256[raw] or filesystem_sha!=SOURCE_SHA256[raw] or frozen_sha!=SOURCE_SHA256[raw]:raise ValueError("frozen source drift")
        records.append(FrozenSourceRecord(raw,SOURCE_SHA256[raw],base_sha,filesystem_sha,frozen_sha,modes[raw],current))
    observed,issues,attestation=_predecessor_attestation(tuple(records))
    return tuple(records),observed,issues,attestation
def _csv(rows,cols):
    out=io.StringIO(newline=""); w=csv.DictWriter(out,fieldnames=cols,lineterminator="\n"); w.writeheader();w.writerows(rows);return out.getvalue().encode()
def _json(v):return (json.dumps(v,sort_keys=False,indent=2)+"\n").encode()
def _sha(v):return hashlib.sha256(v).hexdigest()
CANONICAL_EMPTY_SNAPSHOT_VALUES=("covapie_existing_raw_target_relative_paths_snapshot_v1","covapie_repository_raw_root_v1","repository_relative_posix_lexical_path","covapie_posix_relative_path_lexical_v1","exact_canonical_lexical_string_case_sensitive","pre_download",True,())
def _empty_snapshot():return ExistingRawTargetRelativePathsSnapshot(*CANONICAL_EMPTY_SNAPSHOT_VALUES)
def _unsafe_contract():
    value=object.__new__(RawTargetRelativePathContract)
    for name in CONTRACT_FIELDS:object.__setattr__(value,name,getattr(DEFAULT_CONTRACT,name))
    object.__setattr__(value,"contract_id","invalid")
    return value
def _unsafe_snapshot(**changes):
    value=object.__new__(ExistingRawTargetRelativePathsSnapshot)
    for name,item in zip(SNAPSHOT_FIELDS,CANONICAL_EMPTY_SNAPSHOT_VALUES,strict=True):object.__setattr__(value,name,item)
    for name,item in changes.items():object.__setattr__(value,name,item)
    return value
def _schema_rows():
    rows=[]
    for field_name in CONTRACT_FIELDS:
        value=getattr(DEFAULT_CONTRACT,field_name); rows.append({"order":str(len(rows)+1),"object":"RawTargetRelativePathContract","field":field_name,"exact_type":"exact built-in tuple" if field_name=="allowed_namespace_prefixes" else "exact built-in str","exact_value":"('data/raw/',)" if field_name=="allowed_namespace_prefixes" else value,"passed":"true"})
    for field_name,value in zip(SNAPSHOT_FIELDS,CANONICAL_EMPTY_SNAPSHOT_VALUES,strict=True):
        exact_type="exact built-in bool" if field_name=="snapshot_complete" else "exact built-in tuple" if field_name=="occupied_relative_paths" else "exact built-in str"
        exact_value="True" if field_name=="snapshot_complete" else "()" if field_name=="occupied_relative_paths" else value
        rows.append({"order":str(len(rows)+1),"object":"ExistingRawTargetRelativePathsSnapshot","field":field_name,"exact_type":exact_type,"exact_value":exact_value,"passed":"true"})
    assert [row["order"] for row in rows]==[str(i) for i in range(1,24)]
    return rows
def _result_row(case_order,case_id,matrix_group,candidate,contract_state,snapshot_state,result,precedence):
    return {"case_order":str(case_order),"case_id":case_id,"matrix_group":matrix_group,"candidate_representation":repr(candidate),"contract_state":contract_state,"snapshot_state":snapshot_state,"outcome":result.outcome,"passed":str(result.passed).lower(),"blocks_candidate":str(result.blocks_candidate).lower(),"reason":result.reason,"canonical":result.canonical_raw_target_relative_path,"validated_candidate_fields":json.dumps(result.validated_candidate_fields,separators=(",",":")),"consumed_candidate_fields":json.dumps(result.consumed_candidate_fields,separators=(",",":")),"consumed_context_items":json.dumps(result.consumed_context_items,separators=(",",":")),"evaluator_io_used":str(result.evaluator_io_used).lower(),"expected_precedence":precedence,"case_passed":"true"}
def _truth_rows(observed):
    cases=[]; empty=_empty_snapshot()
    for index,row in enumerate(observed,1):cases.append((f"HIST_{index:03d}","historical_observed",row["observed_value"],DEFAULT_CONTRACT,empty,"valid_contract","valid_snapshot","passed"))
    scalar_cases=((None,SCALAR_REASONS[0]),("",SCALAR_REASONS[1]),("data/raw/café",SCALAR_REASONS[2]),("data/raw/a\0",SCALAR_REASONS[3]),("data/raw/a\x01",SCALAR_REASONS[4]),("data/raw/a b",SCALAR_REASONS[5]),("/data/raw/../a",SCALAR_REASONS[6]),("C:\\data/raw/a",SCALAR_REASONS[7]),("\\\\srv\\x",SCALAR_REASONS[8]),("https://x//y",SCALAR_REASONS[9]),("data/raw/%2e%2e",SCALAR_REASONS[10]),("~/data/raw/a",SCALAR_REASONS[11]),("$ROOT/data/raw/a",SCALAR_REASONS[12]),("data/raw\\a",SCALAR_REASONS[13]),("data/raw/a/",SCALAR_REASONS[14]),("data/raw//a",SCALAR_REASONS[15]),("data/raw/./a",SCALAR_REASONS[16]),("data/raw/../a",SCALAR_REASONS[17]),("docs/a",SCALAR_REASONS[18]))
    for index,(value,reason) in enumerate(scalar_cases,1):cases.append((f"SCALAR_{index:03d}","scalar_reason",value,DEFAULT_CONTRACT,empty,"valid_contract","valid_snapshot",VALIDATION_PRECEDENCE[SCALAR_REASONS.index(reason)]))
    cases.extend((("CONTRACT_TYPE","contract_reason","data/raw/a.cif",object(),empty,"type_invalid","not_consumed","contract_type"),("CONTRACT_VALUE","contract_reason","data/raw/a.cif",_unsafe_contract(),empty,"value_invalid","not_consumed","contract_value"),("SNAPSHOT_TYPE","snapshot_reason","data/raw/a.cif",DEFAULT_CONTRACT,object(),"valid_contract","type_invalid","snapshot_type"),("SNAPSHOT_VALUE","snapshot_reason","data/raw/a.cif",DEFAULT_CONTRACT,_unsafe_snapshot(snapshot_complete=False),"valid_contract","value_invalid","snapshot_value")))
    for index,(field_name,reason,precedence) in enumerate((("canonical_raw_root_identity",SNAPSHOT_REASONS[2],"context_root"),("candidate_coordinate_system",SNAPSHOT_REASONS[3],"context_coordinate"),("path_grammar_version",SNAPSHOT_REASONS[4],"context_grammar"),("equality_policy",SNAPSHOT_REASONS[5],"context_equality"),("snapshot_phase",SNAPSHOT_REASONS[6],"context_phase")),1):cases.append((f"MISMATCH_{index:03d}","cross_context_mismatch","data/raw/a.cif",DEFAULT_CONTRACT,_unsafe_snapshot(**{field_name:"wrong"}),"valid_contract",field_name,precedence))
    cases.extend((("COLLISION","collision","data/raw/a.cif",DEFAULT_CONTRACT,ExistingRawTargetRelativePathsSnapshot(*CANONICAL_EMPTY_SNAPSHOT_VALUES[:-1],("data/raw/a.cif",)),"valid_contract","occupied","exact_occupied_collision"),("PASSED","passed","data/raw/a.cif",DEFAULT_CONTRACT,empty,"valid_contract","empty","passed"),("MULTI_NONASCII_WHITESPACE","multi_invalid","data/raw/café x",DEFAULT_CONTRACT,empty,"valid_contract","valid_snapshot","scalar_ascii"),("MULTI_ABSOLUTE_DOTDOT","multi_invalid","/data/raw/../a",DEFAULT_CONTRACT,empty,"valid_contract","valid_snapshot","scalar_absolute"),("MULTI_WINDOWS_BACKSLASH","multi_invalid","C:\\data/raw\\a",DEFAULT_CONTRACT,empty,"valid_contract","valid_snapshot","scalar_windows_drive"),("MULTI_URI_REPEATED","multi_invalid","https://x//y",DEFAULT_CONTRACT,empty,"valid_contract","valid_snapshot","scalar_uri"),("MULTI_PERCENT_TRAVERSAL","multi_invalid","data/raw/%2e%2e/a",DEFAULT_CONTRACT,empty,"valid_contract","valid_snapshot","scalar_percent"),("MULTI_SCALAR_CONTRACT","multi_invalid","docs/a",object(),empty,"type_invalid","not_consumed","scalar_namespace"),("MULTI_CONTRACT_SNAPSHOT","multi_invalid","data/raw/a.cif",object(),object(),"type_invalid","type_invalid","contract_type")))
    rows=[]
    for index,(case_id,group,candidate,contract,snapshot,cstate,sstate,precedence) in enumerate(cases,1):
        result=classify_admit_011_raw_target_relative_path_design(candidate,snapshot,contract)
        if group=="historical_observed":assert result.outcome=="passed" and result.reason=="" and result.canonical_raw_target_relative_path==candidate
        rows.append(_result_row(index,case_id,group,candidate,cstate,sstate,result,precedence))
    assert {row["reason"] for row in rows}==set(REASON_VOCABULARY)
    assert len([row for row in rows if row["matrix_group"]=="historical_observed"])==47
    return rows
def build_artifacts(records,observed,issues,attestation):
    contract=_schema_rows()
    ccols=("order","object","field","exact_type","exact_value","passed")
    coverage=[{"coverage_order":str(i),"source_relative_path":r["source_relative_path"],"source_sha256":r["source_sha256"],"source_occurrence":r["field_location"],"observed_value":r["observed_value"],"accepted":"true","expected_canonical_value":r["observed_value"],"coverage_passed":"true"} for i,r in enumerate(observed,1)]
    ocols=("coverage_order","source_relative_path","source_sha256","source_occurrence","observed_value","accepted","expected_canonical_value","coverage_passed")
    truth=_truth_rows(observed)
    tcols=("case_order","case_id","matrix_group","candidate_representation","contract_state","snapshot_state","outcome","passed","blocks_candidate","reason","canonical","validated_candidate_fields","consumed_candidate_fields","consumed_context_items","evaluator_io_used","expected_precedence","case_passed")
    resp=[{"role_order":str(i),"role":a,"boundary":b,"implemented":"false"} for i,(a,b) in enumerate((("standalone_evaluator","scalar + two exact context objects only"),("future_unified_adapter","candidate/evaluation/batch envelope and identity routing"),("snapshot_provider","filesystem namespace enumeration before call"),("ADMIT_012_013","post-download result/integrity"),("stage_authorization","separate authority")),1)]
    rcols=("role_order","role","boundary","implemented")
    for row in issues:
        if row["issue_id"]=="RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED":row["status"]="resolved";row["integration_transition"]="resolved_by_raw_target_relative_path_contract_v1"
    icols=("issue_id","issue_type","affected_fields","affected_rules","severity","status","blocking_scope","blocking_reason","issue_origin","integration_transition","issue_count")
    boundary=[{"source_order":str(i),"source_relative_path":r.relative_path,"expected_sha256":r.expected_sha256,"base_tree_sha256":r.base_tree_sha256,"filesystem_sha256":r.filesystem_sha256,"frozen_snapshot_sha256":r.frozen_snapshot_sha256,"git_tracked":"true","base_tree_blob":"true","base_tree_mode":r.base_tree_mode,"filesystem_regular":"true","non_symlink":"true","parent_chain_non_symlink":"true","safe_descendant":"true","resolved_identity_passed":"true","source_boundary_passed":"true"} for i,r in enumerate(records,1)]; bcols=("source_order","source_relative_path","expected_sha256","base_tree_sha256","filesystem_sha256","frozen_snapshot_sha256","git_tracked","base_tree_blob","base_tree_mode","filesystem_regular","non_symlink","parent_chain_non_symlink","safe_descendant","resolved_identity_passed","source_boundary_passed")
    files={CONTRACT_FILE:_csv(contract,ccols),OBSERVED_FILE:_csv(coverage,ocols),TRUTH_FILE:_csv(truth,tcols),RESPONSIBILITY_FILE:_csv(resp,rcols),ISSUE_FILE:_csv(issues,icols),BOUNDARY_FILE:_csv(boundary,bcols)}
    readiness={k:True for k in ("raw_target_relative_path_contract_frozen","relative_path_grammar_frozen","lexical_resolved_boundary_frozen","raw_root_identity_contract_frozen","raw_namespace_allowlist_frozen","occupied_snapshot_contract_frozen","exact_context_object_schemas_frozen","standalone_scalar_context_boundary_frozen","reason_vocabulary_and_precedence_frozen","context_responsibility_frozen","ready_for_admit_011_standalone_evaluator_interface_implementation")};readiness.update({k:False for k in ("admit_011_rule_logic_implemented","admit_011_adapter_implemented","admit_011_registered_in_engine","unified_dispatch_runtime_with_admit_001_to_011_implemented","provider_mapping_validated","real_provider_evaluation_ready","combined_candidate_verdict_implemented","ready_for_bulk_download_now","checkpoint_compatibility_validated","full_repository_canonical_validated","ready_for_training")})
    manifest={"manifest_schema_version":"covapie_admit_011_raw_target_relative_path_contract_manifest_v4","stage":STAGE,"base_commit":EXPECTED_BASE_COMMIT,"base_subject":EXPECTED_BASE_SUBJECT,"admission_rule_id":RULE_ID,"admission_rule_name":RULE_NAME,"source_input_count":len(records),"source_path_list_sha256":EXPECTED_SOURCE_PATH_LIST_SHA256,"source_path_sha256_pairs_sha256":EXPECTED_SOURCE_PATH_SHA256_PAIRS_SHA256,"source_paths_sha256":{r.relative_path:r.expected_sha256 for r in records},**attestation,"source_structure_checks_completed_before_byte_read":True,"all_source_base_tree_blob_verified":True,"all_source_parent_chains_non_symlink":True,"all_source_resolved_identity_verified":True,"source_boundary_output_sha256":_sha(files[BOUNDARY_FILE]),"source_attestation_passed":True,"output_files":list(OUTPUT_FILES),"output_file_count":len(OUTPUT_FILES),"row_counts":{"schema":len(contract),"truth":len(truth),"truth_historical":47,"observed_coverage":len(coverage),"issue":len(issues),"responsibility":len(resp),"source_boundary":len(boundary)},"contract_class":"RawTargetRelativePathContract","contract_fields":list(CONTRACT_FIELDS),"snapshot_class":"ExistingRawTargetRelativePathsSnapshot","snapshot_fields":list(SNAPSHOT_FIELDS),"coordinate_system":DEFAULT_CONTRACT.candidate_coordinate_system,"allowed_namespace_prefixes":list(DEFAULT_CONTRACT.allowed_namespace_prefixes),"reason_vocabulary":list(REASON_VOCABULARY),"validation_precedence":list(VALIDATION_PRECEDENCE),"issue_inventory_count":len(issues),"issue_inventory_sha256":_sha(files[ISSUE_FILE]),"coverage_affected_rules":"ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015","feature_semantics_audit_required_before_training":True,"step12d_is_final_training_feature_contract":False,"step12d_status":"smoke_legality_only_not_final_training_feature_contract","readiness":readiness,"safety":{"filesystem_used":False,"network_used":False,"raw_read":False,"mutation":False},"materializer_safety":dict(MATERIALIZER_SAFETY),"recommended_next_step":"implement_covapie_admit_011_standalone_evaluator_interface_v1","all_checks_passed":True,"validation_failures":[],"output_sha256":{n:_sha(x) for n,x in files.items()}}
    files[MANIFEST_FILE]=_json(manifest);return {name:files[name] for name in OUTPUT_FILES}

@dataclass(frozen=True)
class OutputMaterializationPlan:
    root:Path; parent:Path; anchor:Path; root_name:str; relative_to_repo:bool; parent_identity:tuple; root_identity:tuple|None; leaf_identities:tuple

DIRECTORY_FLAGS=os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC
READ_FILE_FLAGS=os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC
WRITE_FILE_FLAGS=os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC
try:
    _RENAMEAT2=ctypes.CDLL(None,use_errno=True).renameat2
    _RENAMEAT2.argtypes=(ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint)
    _RENAMEAT2.restype=ctypes.c_int
except AttributeError:_RENAMEAT2=None
DIRECTORY_FD_CAPABILITIES=all(fn in os.supports_dir_fd for fn in (os.open,os.stat,os.mkdir,os.unlink,os.rmdir)) and _RENAMEAT2 is not None
RENAME_NOREPLACE=1

def _identity(item):return (int(item.st_dev),int(item.st_ino),int(item.st_mode))
def _same_identity(item,identity):return _identity(item)==identity
def _require_materializer_capabilities():
    if not all(hasattr(os,name) for name in ("O_DIRECTORY","O_NOFOLLOW","O_CLOEXEC")) or not DIRECTORY_FD_CAPABILITIES:raise ValueError("required directory-fd safety unavailable")
def _assert_real_parent_chain(parent,anchor):
    current=parent
    while True:
        item=os.lstat(current)
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):raise ValueError("output parent chain unsafe")
        if current==anchor:break
        if current==current.parent:raise ValueError("output parent anchor escaped")
        current=current.parent
    if parent.resolve(strict=True)!=parent:raise ValueError("output parent identity unsafe")
def _output_target_path(output_root):
    candidate=Path(output_root)
    if candidate.is_absolute():
        root=candidate;relative=False;anchor=Path(root.anchor)
    else:
        if ".." in candidate.parts or candidate.is_absolute():raise ValueError("relative output escape")
        root=REPO_ROOT/candidate;relative=True;anchor=REPO_ROOT
    if not root.is_absolute() or not root.name:raise ValueError("output root invalid")
    return root,relative,anchor
def _inspect_output_target_read_only(output_root):
    _require_materializer_capabilities();root,relative,anchor=_output_target_path(output_root);parent=root.parent
    _assert_real_parent_chain(parent,anchor)
    if relative and REPO_ROOT not in (parent,*parent.parents):raise ValueError("relative output containment")
    parent_identity=_identity(os.lstat(parent))
    try:root_stat=os.lstat(root)
    except FileNotFoundError:return OutputMaterializationPlan(root,parent,anchor,root.name,relative,parent_identity,None,())
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):raise ValueError("output root unsafe")
    if root.resolve(strict=True)!=root:raise ValueError("output root identity unsafe")
    names=tuple(os.listdir(root))
    if set(names)!=set(OUTPUT_FILES) or len(names)!=len(OUTPUT_FILES):raise ValueError("unsafe output inventory")
    leaves=[]
    for name in OUTPUT_FILES:
        leaf=root/name;item=os.lstat(leaf)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode) or leaf.resolve(strict=True)!=leaf:raise ValueError("unsafe output leaf")
        leaves.append((name,_identity(item)))
    return OutputMaterializationPlan(root,parent,anchor,root.name,relative,parent_identity,_identity(root_stat),tuple(leaves))
def _validate_payloads(files):
    if tuple(files)!=OUTPUT_FILES or set(files)!=set(OUTPUT_FILES) or any(type(data) is not bytes for data in files.values()):raise ValueError("output payload inventory invalid")
    if any(_sha(files[name])!=digest for name,digest in FROZEN_CSV_SHA256.items()):raise ValueError("frozen CSV payload changed")
def _assert_parent_revalidated(plan,parent_fd):
    if not _same_identity(os.fstat(parent_fd),plan.parent_identity) or not _same_identity(os.lstat(plan.parent),plan.parent_identity):raise ValueError("output parent replaced")
    _assert_real_parent_chain(plan.parent,plan.anchor)
def _assert_lexical_identity(path,identity):
    item=os.lstat(path)
    if not _same_identity(item,identity) or stat.S_ISLNK(item.st_mode) or path.resolve(strict=True)!=path:raise ValueError("output lexical identity replaced")
def _stat_at(directory_fd,name):return os.stat(name,dir_fd=directory_fd,follow_symlinks=False)
def _listdir_fd(directory_fd):return tuple(os.listdir(directory_fd))
def _rename_noreplace_at(parent_fd,source,target):
    if _RENAMEAT2 is None:raise ValueError("required atomic no-replace rename unavailable")
    if _RENAMEAT2(parent_fd,os.fsencode(source),parent_fd,os.fsencode(target),RENAME_NOREPLACE)!=0:
        code=ctypes.get_errno();raise OSError(code,os.strerror(code),f"{source}->{target}")
def _assert_existing_inventory(plan,root_fd):
    expected=set(OUTPUT_FILES)
    names=set(_listdir_fd(root_fd))
    if names!=expected:raise ValueError("output inventory changed")
    for name,identity in plan.leaf_identities:
        item=_stat_at(root_fd,name)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode) or not _same_identity(item,identity):raise ValueError("output leaf replaced")
def _open_prewrite_root(plan):
    parent_fd=os.open(os.fspath(plan.parent),DIRECTORY_FLAGS);root_fd=None;staging_name=None
    try:
        _assert_parent_revalidated(plan,parent_fd)
        if plan.root_identity is None:
            try:_stat_at(parent_fd,plan.root_name)
            except FileNotFoundError:pass
            else:raise ValueError("missing output target occupied")
            for _ in range(64):
                candidate=f".admit011-stage-{secrets.token_hex(16)}"
                try:os.mkdir(candidate,0o700,dir_fd=parent_fd);staging_name=candidate;break
                except FileExistsError:continue
            else:raise ValueError("staging directory name collision")
            root_fd=os.open(staging_name,DIRECTORY_FLAGS,dir_fd=parent_fd);root_identity=_identity(os.fstat(root_fd))
            if not stat.S_ISDIR(root_identity[2]) or _listdir_fd(root_fd):raise ValueError("new staging directory invalid")
            if not _same_identity(_stat_at(parent_fd,staging_name),root_identity):raise ValueError("staging directory replaced")
        else:
            item=_stat_at(parent_fd,plan.root_name)
            if not _same_identity(item,plan.root_identity) or stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode):raise ValueError("output root replaced")
            root_fd=os.open(plan.root_name,DIRECTORY_FLAGS,dir_fd=parent_fd);root_identity=_identity(os.fstat(root_fd))
            if root_identity!=plan.root_identity:raise ValueError("output root descriptor replaced")
            _assert_lexical_identity(plan.root,root_identity);_assert_existing_inventory(plan,root_fd)
        return parent_fd,root_fd,root_identity,staging_name
    except BaseException:
        if root_fd is not None:
            try:os.close(root_fd)
            except OSError:pass
        if staging_name is not None:
            try:os.rmdir(staging_name,dir_fd=parent_fd)
            except OSError:pass
        try:os.close(parent_fd)
        except OSError:pass
        raise
def _write_all(file_fd,data):
    offset=0
    while offset<len(data):
        count=os.write(file_fd,data[offset:])
        if type(count) is not int or count<=0:raise OSError("temporary write failed")
        offset+=count
def _read_at(directory_fd,name,expected_identity):
    item=_stat_at(directory_fd,name)
    if not _same_identity(item,expected_identity) or stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):raise ValueError("pinned leaf changed")
    file_fd=os.open(name,READ_FILE_FLAGS,dir_fd=directory_fd)
    try:
        if not _same_identity(os.fstat(file_fd),expected_identity):raise ValueError("pinned leaf descriptor changed")
        chunks=[]
        while True:
            chunk=os.read(file_fd,65536)
            if not chunk:break
            chunks.append(chunk)
        if not _same_identity(os.fstat(file_fd),expected_identity) or not _same_identity(_stat_at(directory_fd,name),expected_identity):raise ValueError("pinned leaf changed during read")
        return b"".join(chunks)
    finally:os.close(file_fd)
def _stage_payloads(staging_fd,files,staged):
    for name,data in files.items():
        file_fd=os.open(name,WRITE_FILE_FLAGS,0o600,dir_fd=staging_fd)
        try:
            identity=_identity(os.fstat(file_fd));staged[name]=identity
            _write_all(file_fd,data);os.fsync(file_fd)
        finally:os.close(file_fd)
        if _read_at(staging_fd,name,identity)!=data:raise ValueError("staged payload hash mismatch")
    if set(_listdir_fd(staging_fd))!=set(OUTPUT_FILES):raise ValueError("staging inventory invalid")
    for name,data in files.items():
        item=_stat_at(staging_fd,name)
        if not _same_identity(item,staged[name]) or stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode) or _read_at(staging_fd,name,staged[name])!=data or _sha(_read_at(staging_fd,name,staged[name]))!=_sha(data):raise ValueError("staged payload verification failed")
    os.fsync(staging_fd)
    return staged
def _assert_staging_publish_state(plan,parent_fd,staging_fd,staging_identity,staging_name,staged):
    _assert_parent_revalidated(plan,parent_fd)
    if not _same_identity(os.fstat(staging_fd),staging_identity) or not _same_identity(_stat_at(parent_fd,staging_name),staging_identity):raise ValueError("pinned staging directory changed")
    try:_stat_at(parent_fd,plan.root_name)
    except FileNotFoundError:pass
    else:raise ValueError("new output target race")
    if set(_listdir_fd(staging_fd))!=set(OUTPUT_FILES):raise ValueError("staging inventory changed")
    for name,identity in staged.items():
        item=_stat_at(staging_fd,name)
        if not _same_identity(item,identity) or stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):raise ValueError("staged output replaced")
def _publish_staging_directory(plan,parent_fd,staging_fd,staging_identity,staging_name,staged):
    _assert_staging_publish_state(plan,parent_fd,staging_fd,staging_identity,staging_name,staged)
    _rename_noreplace_at(parent_fd,staging_name,plan.root_name)
    if not _same_identity(_stat_at(parent_fd,plan.root_name),staging_identity):raise ValueError("published output root changed")
def _assert_existing_payloads_identical(plan,parent_fd,root_fd,root_identity,files):
    _assert_parent_revalidated(plan,parent_fd)
    if not _same_identity(os.fstat(root_fd),root_identity):raise ValueError("pinned output root changed")
    _assert_lexical_identity(plan.root,root_identity);_assert_existing_inventory(plan,root_fd)
    for name,data in files.items():
        identity=dict(plan.leaf_identities)[name]
        if _read_at(root_fd,name,identity)!=data:raise ValueError("existing output payload differs")
def _postwrite_verify(plan,parent_fd,root_fd,root_identity,files):
    _assert_parent_revalidated(plan,parent_fd)
    if not _same_identity(os.fstat(root_fd),root_identity):raise ValueError("output root changed after publish")
    _assert_lexical_identity(plan.root,root_identity)
    if set(_listdir_fd(root_fd))!=set(OUTPUT_FILES):raise ValueError("postwrite inventory invalid")
    if plan.root_identity is not None:_assert_existing_inventory(plan,root_fd)
    for name,data in files.items():
        item=_stat_at(root_fd,name)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):raise ValueError("postwrite leaf invalid")
        if _read_at(root_fd,name,_identity(item))!=data or _sha(_read_at(root_fd,name,_identity(item)))!=_sha(data):raise ValueError("postwrite payload mismatch")
    os.fsync(root_fd)
def _cleanup_staging(parent_fd,staging_fd,staging_name,staging_identity,staged,files):
    if parent_fd is None or staging_fd is None or staging_name is None:return staging_fd
    try:
        if not _same_identity(os.fstat(staging_fd),staging_identity) or not _same_identity(_stat_at(parent_fd,staging_name),staging_identity):return staging_fd
        if set(_listdir_fd(staging_fd))!=set(staged):return staging_fd
        for name,identity in staged.items():
            item=_stat_at(staging_fd,name)
            if not _same_identity(item,identity) or stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):return staging_fd
        for name,identity in staged.items():
            item=_stat_at(staging_fd,name)
            if not _same_identity(item,identity):return staging_fd
            os.unlink(name,dir_fd=staging_fd)
        if _listdir_fd(staging_fd):return staging_fd
        os.close(staging_fd);staging_fd=None
        os.rmdir(staging_name,dir_fd=parent_fd)
    except BaseException:pass
    return staging_fd
def materialize_contract(output_root=None):
    plan=_inspect_output_target_read_only(OUTPUT_ROOT if output_root is None else output_root)
    parent_fd=root_fd=None;root_identity=None;staging_name=None;staged={};files={}
    try:
        records,observed,issues,attestation=_snapshot_sources();files=build_artifacts(records,observed,issues,attestation);_validate_payloads(files)
        parent_fd,root_fd,root_identity,staging_name=_open_prewrite_root(plan)
        if staging_name is None:
            _assert_existing_payloads_identical(plan,parent_fd,root_fd,root_identity,files);_postwrite_verify(plan,parent_fd,root_fd,root_identity,files)
        else:
            _stage_payloads(root_fd,files,staged);_publish_staging_directory(plan,parent_fd,root_fd,root_identity,staging_name,staged);staging_name=None
            os.fsync(parent_fd);_postwrite_verify(plan,parent_fd,root_fd,root_identity,files)
        return {"output_sha256":{name:_sha(data) for name,data in files.items()}}
    except BaseException:
        root_fd=_cleanup_staging(parent_fd,root_fd,staging_name,root_identity,staged,files)
        raise
    finally:
        if root_fd is not None:
            try:os.close(root_fd)
            except OSError:pass
        if parent_fd is not None:
            try:os.close(parent_fd)
            except OSError:pass
if __name__=="__main__":print(json.dumps(materialize_contract(),sort_keys=True))
