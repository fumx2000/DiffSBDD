"""Read-only ADMIT_012 evaluator-interface precondition audit.

This module audits committed metadata only.  It deliberately defines neither
an ADMIT_012 evaluator nor a result/adapter/runtime contract.
"""
from __future__ import annotations

import ast
import csv
import ctypes
import hashlib
import io
import json
import os
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_COMMIT = "97128a674b9ffc0579c67fd1ed2acf30d4cedfa5"
BASE_SUBJECT = "add CovaPIE unified dispatch runtime with ADMIT_001 to ADMIT_011 v1"
STAGE = "covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1"
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
FIELDS = ("download_result_status", "observed_http_status", "observed_content_length_bytes", "observed_sha256")
EXPECTED_SOURCE_COUNT = 129
EXPECTED_PATH_LIST_SHA256 = "f0ed67bbb346ff5e900c532b2188b90a527291e1f3b704a60454fd33ed938b2b"
EXPECTED_PATH_SHA256_PAIRS_SHA256 = "97a0bbb81314e7213e5999d56278d590d5073b9e1ce0e0a9e03458934aae2fab"
RULE_REGISTRY = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv")
SCHEMA = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_schema_contract.csv")
EXECUTABILITY = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_rule_executability_matrix.csv")
FIELD_MATRIX = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_field_semantics_matrix.csv")
CONTEXT = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv")
RUNTIME_ISSUES = Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1/covapie_admit_001_to_011_runtime_issue_inventory.csv")
REQUIRED_PATHS = (
    Path("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011.py"),
    Path("scripts/check_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1.py"),
    Path("tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1.py"),
    Path("docs/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1_summary.md"),
    Path("src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_design_gate.py"),
    Path("scripts/check_covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1.py"),
    Path("tests/test_covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1.py"),
    Path("docs/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1_summary.md"),
    Path("src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate.py"),
    Path("scripts/check_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1.py"),
    Path("tests/test_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1.py"),
    Path("docs/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1_summary.md"),
    Path("src/covalent_ext/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit.py"),
    Path("scripts/check_covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1.py"),
    Path("tests/test_covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1.py"),
    Path("docs/covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1_summary.md"),
    Path("src/covalent_ext/covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit.py"),
    Path("scripts/check_covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit_v1.py"),
    Path("tests/test_covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit_v1.py"),
    Path("docs/covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit_v1_summary.md"),
    RULE_REGISTRY, SCHEMA, EXECUTABILITY, FIELD_MATRIX, CONTEXT, RUNTIME_ISSUES,
)
FILES = (
    "covapie_admit_012_formal_evaluator_precondition_matrix.csv",
    "covapie_admit_012_field_occurrence_inventory.csv",
    "covapie_admit_012_observed_value_inventory.csv",
    "covapie_admit_012_source_boundary_audit.csv",
    "covapie_admit_012_issue_readiness_inventory.csv",
    "covapie_admit_012_formal_evaluator_preconditions_manifest.json",
)
PRECONDITION, OCCURRENCE, OBSERVED, SOURCE_AUDIT, ISSUE, MANIFEST = FILES
COLUMNS = {
    PRECONDITION: ("precondition_order", "precondition_id", "precondition_group", "precondition_subject", "expected_contract", "observed_evidence", "completeness_status", "implementation_blocking", "blocking_reason", "precondition_passed"),
    OCCURRENCE: ("occurrence_order", "field_name", "relative_path", "file_role", "occurrence_kind", "declaring_or_referencing", "phase_claim", "type_claim", "validation_claim", "source_authority_level", "current_contract_effect", "occurrence_passed"),
    OBSERVED: ("value_order", "field_name", "source_path", "representation", "source_kind", "real_observed_value", "synthetic_example", "placeholder", "schema_only", "produced_by_download_execution", "admissible_as_semantic_evidence", "notes"),
    SOURCE_AUDIT: ("source_order", "source_relative_path", "source_kind", "base_tree_mode", "base_tree_sha256", "filesystem_sha256", "tracked_regular_non_symlink", "parent_chain_verified", "pinned_fd_read", "triple_sha256_passed", "source_boundary_passed"),
}

@dataclass(frozen=True)
class Source:
    path: Path
    content: bytes
    sha256: str
    base_mode: str

def _git(args: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=text, check=False)

def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n", extrasaction="raise")
    writer.writeheader(); writer.writerows(rows)
    return stream.getvalue().encode()

def _safe(path: Path) -> bool:
    return not path.is_absolute() and bool(path.parts) and ".." not in path.parts and path.parts[:2] != ("data", "raw") and path.parts[0] != "checkpoints"

def _kind(path: Path) -> str:
    if path.suffix == ".py": return "python_source"
    if path.suffix == ".csv": return "committed_csv"
    if path.suffix == ".json": return "committed_manifest"
    return "tracked_text"

def _paths() -> tuple[Path, ...]:
    command = ["grep", "-l", "-I"] + sum((["-e", field] for field in FIELDS), []) + [BASE_COMMIT, "--", ":!data/raw/**", ":!checkpoints/**"]
    result = _git(command)
    if result.returncode not in (0, 1): raise ValueError("base occurrence discovery failed")
    prefix = f"{BASE_COMMIT}:"
    discovered = {Path(line.removeprefix(prefix)) for line in result.stdout.splitlines() if line}
    if any(not line.startswith(prefix) for line in result.stdout.splitlines() if line): raise ValueError("unsafe base discovery")
    paths = tuple(sorted(discovered | set(REQUIRED_PATHS), key=lambda p: p.as_posix()))
    serialized=[path.as_posix() for path in paths]
    if not all(_safe(path) and STAGE not in path.as_posix() for path in paths): raise ValueError("unsafe source boundary")
    if len(paths) != EXPECTED_SOURCE_COUNT or hashlib.sha256(json.dumps(serialized, separators=(",", ":")).encode()).hexdigest() != EXPECTED_PATH_LIST_SHA256: raise ValueError("frozen source path boundary mismatch")
    return paths

def _real_repo_root() -> Path:
    item=os.lstat(REPO_ROOT)
    if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode) or REPO_ROOT.resolve(strict=True) != REPO_ROOT: raise ValueError("unsafe repository root")
    return REPO_ROOT

def _parent_chain(path: Path) -> None:
    current=(REPO_ROOT/path).parent
    while current != REPO_ROOT:
        item=os.lstat(current)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode): raise ValueError("unsafe source parent")
        current=current.parent

def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return item.st_dev, item.st_ino, item.st_mode

def _pinned_read(path: Path, expected_identity: tuple[int, int, int] | None = None) -> bytes:
    absolute=REPO_ROOT/path
    _real_repo_root(); _parent_chain(path)
    before=os.lstat(absolute); expected_identity=expected_identity or _identity(before)
    if _identity(before) != expected_identity: raise ValueError("source lexical identity drift before open")
    flags=os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    descriptor=os.open(absolute, flags)
    try:
        if _identity(os.fstat(descriptor)) != expected_identity: raise ValueError("source stat/open race")
        chunks=[]
        while True:
            chunk=os.read(descriptor, 1024 * 1024)
            if not chunk: break
            chunks.append(chunk)
        if _identity(os.fstat(descriptor)) != expected_identity: raise ValueError("source FD identity drift after read")
        if _identity(os.lstat(absolute)) != expected_identity: raise ValueError("source lexical replacement after read")
        _parent_chain(path); _real_repo_root()
        return b"".join(chunks)
    finally:
        os.close(descriptor)

def build_frozen_source_snapshot() -> tuple[Source, ...]:
    _real_repo_root()
    subject = _git(["show", "-s", "--format=%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    if subject.returncode or ancestor.returncode or subject.stdout.strip() != BASE_SUBJECT: raise ValueError("base lineage unavailable")
    paths = _paths()
    structures=[]
    for path in paths:
        absolute = REPO_ROOT / path
        _parent_chain(path); item = os.lstat(absolute); tree = _git(["ls-tree", BASE_COMMIT, "--", path.as_posix()])
        tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()])
        head, sep, tree_path=tree.stdout.partition("\t"); fields=head.split() if tree.returncode == 0 else []
        if tracked.returncode or tracked.stdout.splitlines() != [path.as_posix()] or tree.returncode or not sep or tree_path.strip() != path.as_posix() or len(fields) != 3 or fields[0] not in {"100644", "100755"} or fields[1] != "blob" or stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode) or absolute.resolve(strict=True) != absolute: raise ValueError(f"unsafe source: {path}")
        structures.append((path, fields[0], _identity(item)))
    records = []
    pairs=[]
    for path, mode, expected_identity in structures:
        base = _git(["show", f"{BASE_COMMIT}:{path.as_posix()}"], text=False); current = _pinned_read(path, expected_identity)
        if base.returncode or not isinstance(base.stdout, bytes) or hashlib.sha256(base.stdout).digest() != hashlib.sha256(current).digest(): raise ValueError(f"source drift: {path}")
        digest=hashlib.sha256(current).hexdigest(); pairs.append([path.as_posix(),digest]); records.append(Source(path, current, digest, mode))
    if hashlib.sha256(json.dumps(pairs, separators=(",", ":")).encode()).hexdigest() != EXPECTED_PATH_SHA256_PAIRS_SHA256: raise ValueError("frozen source SHA boundary mismatch")
    return tuple(records)

def _record(snapshot: tuple[Source, ...], path: Path) -> Source:
    return next(source for source in snapshot if source.path == path)

def _rows(snapshot: tuple[Source, ...], path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(_record(snapshot, path).content.decode(), newline="")))

def _contracts(snapshot: tuple[Source, ...]) -> None:
    rule = next(row for row in _rows(snapshot, RULE_REGISTRY) if row["admission_rule_id"] == "ADMIT_012")
    executable = next(row for row in _rows(snapshot, EXECUTABILITY) if row["admission_rule_id"] == "ADMIT_012")
    field_rows = [row for row in _rows(snapshot, FIELD_MATRIX) if row["field_name"] in FIELDS]
    contexts = [row for row in _rows(snapshot, CONTEXT) if row["required_by_rules"] == "ADMIT_012|ADMIT_013"]
    issues = _rows(snapshot, RUNTIME_ISSUES)
    if not (rule["admission_rule_name"] == "future_download_integrity_fields_required" and rule["evidence_source"] == "future_download_result" and rule["required_status"] == "download_status_http_status_content_length_and_sha256_present" and rule["blocking_reason"] == "download_integrity_fields_missing" and rule["evaluation_phase"] == "post_download" and executable["candidate_field_dependencies"].split("|") == list(FIELDS) and executable["batch_context_dependencies"] == "" and executable["download_execution_result_required"] == "true" and executable["pure_in_memory_interface_possible"] == "true" and executable["semantics_complete"] == executable["deterministic_evaluation_possible_now"] == "false" and executable["deterministic_evaluation_possible_after_contract_freeze"] == "true" and executable["implementation_disposition"] == "interface_only_pending_semantics" and all(row["candidate_record_field"] == "false" and row["producer_scope"] == "download_execution_result" and row["implementation_semantics_complete"] == "false" for row in field_rows) and len(contexts) == 4 and all(row["exact_contract_defined"] == "false" for row in contexts) and {row["issue_id"] for row in issues} >= {"DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED", "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED", "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE", "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"}): raise ValueError("ADMIT_012 contract evidence failed")

def _preconditions() -> list[dict[str, str]]:
    specs = (
        ("identity", "rule identity", "ADMIT_012 exact", "registry exact", True, ""), ("identity", "phase", "post_download", "registry exact", True, ""), ("identity", "required status", "exact status", "registry exact", True, ""), ("identity", "blocking reason", "exact blocker", "registry exact", True, ""),
        ("field", "Exact4 identity/order", "frozen ordered fields", "Step14AU-A exact", True, ""), ("routing", "future result producer", "download execution result", "field matrix exact", True, ""), ("routing", "candidate versus result envelope", "future consumer envelope frozen", "candidate false but envelope allocation absent", False, "ADMIT_012_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED"),
        ("type", "download_result_status type", "exact built-in str", "no exact type contract", False, "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED"), ("type", "download_result_status vocabulary", "allowed vocabulary", "context exact=false", False, "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED"), ("type", "observed_http_status type/range", "exact int, bool rejection, range", "no exact contract", False, "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED"),
        ("type", "content length type/range", "exact int, bool rejection, range", "no exact contract", False, "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED"), ("type", "SHA256 grammar/case", "exact grammar and case policy", "no exact contract", False, "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED"), ("validation", "presence semantics", "defined key/value/type meaning", "no exact contract", False, "ADMIT_012_PRESENCE_SEMANTICS_UNRESOLVED"), ("validation", "multi-invalid precedence", "deterministic reason order", "no exact contract", False, "ADMIT_012_MULTI_INVALID_PRECEDENCE_UNRESOLVED"),
        ("interface", "public standalone signature", "scalar/object/mapping resolved", "routing/validation unresolved", False, "ADMIT_012_STANDALONE_SIGNATURE_UNRESOLVED"), ("interface", "Exact10 result contract", "result object/shape resolved", "not designed", False, "ADMIT_012_RESULT_CONTRACT_UNRESOLVED"), ("purity", "pure in-memory", "possible", "Step14AU-A exact", True, ""), ("purity", "no network/filesystem/raw", "forbidden inside evaluator", "network/filesystem false", True, ""),
        ("boundary", "ADMIT_012/013 responsibility", "presence versus fail-closed outcome", "separate registry rules", True, ""), ("boundary", "provider mapping required", "not required inside evaluator", "pure interface evidence", True, ""), ("authorization", "real provider mapping", "not validated", "not authorized", True, ""), ("authorization", "real download evaluation", "not authorized", "not authorized", True, ""), ("authorization", "runtime integration", "not authorized", "Exact11 unchanged", True, ""), ("training", "feature audit", "still required before training", "historical readiness", True, ""),
    )
    rows=[]
    for number, (group, subject, expected, evidence, complete, blocker) in enumerate(specs, 1): rows.append({"precondition_order":str(number), "precondition_id":f"PRE_{number:03d}", "precondition_group":group, "precondition_subject":subject, "expected_contract":expected, "observed_evidence":evidence, "completeness_status":"complete" if complete else "incomplete", "implementation_blocking":"false" if complete else "true", "blocking_reason":blocker, "precondition_passed":str(complete).lower()})
    return rows

def _role(path: Path) -> str:
    value=path.as_posix()
    if value.startswith("src/"): return "production_source"
    if value.startswith("tests/"): return "tests"
    if value.startswith("scripts/"): return "checker"
    if value.startswith("docs/"): return "docs"
    if path.suffix == ".json": return "manifest"
    if "schema" in path.name: return "candidate_schema"
    if "runtime" in path.name: return "runtime_envelope"
    return "derived_csv"

PRIMARY_CONTRACT_PATHS=frozenset((RULE_REGISTRY, SCHEMA, EXECUTABILITY, FIELD_MATRIX, CONTEXT))

def _occurrences(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    rows=[]
    for source in snapshot:
        for line_number, line in enumerate(source.content.decode(errors="strict").splitlines(), 1):
            for field in FIELDS:
                if field in line:
                    authority="primary_committed_contract" if source.path in PRIMARY_CONTRACT_PATHS else "historical_or_reference"
                    exact_field_cell=line.startswith(field+",") or (field in line and "("+repr(field) in line)
                    declares=authority == "primary_committed_contract" and exact_field_cell
                    phase="post_download" if authority == "primary_committed_contract" and "post_download" in line else "unspecified_or_non_authoritative"
                    rows.append({"occurrence_order":str(len(rows)+1), "field_name":field, "relative_path":source.path.as_posix(), "file_role":_role(source.path), "occurrence_kind":"field_declaration" if declares else "field_reference", "declaring_or_referencing":"declaring" if declares else "referencing", "phase_claim":phase, "type_claim":"not_exactly_defined", "validation_claim":"incomplete" if authority == "primary_committed_contract" and ("false" in line.lower() or "UNRESOLVED" in line) else "reference_only", "source_authority_level":authority, "current_contract_effect":"field_identity_or_lifecycle_authority" if authority == "primary_committed_contract" else "non_promoted_reference", "occurrence_passed":"true"})
    return rows

def _walk_json(value: Any, location: str = "$"):
    if isinstance(value, dict):
        for key, child in value.items():
            loc=f"{location}.{key}"
            if key in FIELDS: yield key, loc, child
            yield from _walk_json(child, loc)
    elif isinstance(value, list):
        for index, child in enumerate(value): yield from _walk_json(child, f"{location}[{index}]")

def _python_literals(source: Source):
    tree=ast.parse(source.content.decode(), filename=source.path.as_posix())
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value in FIELDS and isinstance(value, ast.Constant):
                    yield key.value, f"ast:{node.lineno}", value.value

def _observed_kind(source: Source, field: str) -> tuple[str, bool, bool, bool, str]:
    path=source.path.as_posix()
    if path.startswith("tests/"): return "test_fixture", False, True, False, "static Python/test fixture; not production semantics"
    if "real_covalent_pilot_download_integrity_gate" in path: return "historical_non_admit012_integrity_observation", False, False, False, "historical non-ADMIT_012 integrity evidence"
    if field == "observed_sha256": return "unrelated_source_attestation_hash", True, False, False, "historical source-attestation digest, not download-result semantics"
    return "historical_non_admit012_integrity_observation", False, False, True, "historical/reference value; not authorized ADMIT_012 execution"

def _observed(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    rows=[]
    for field in FIELDS:
        rows.append({"value_order":str(len(rows)+1), "field_name":field, "source_path":SCHEMA.as_posix(), "representation":"schema_field_declaration", "source_kind":"schema_only", "real_observed_value":"false", "synthetic_example":"false", "placeholder":"true", "schema_only":"true", "produced_by_download_execution":"false", "admissible_as_semantic_evidence":"false", "notes":"field identity only; no observed download result"})
    for source in snapshot:
        values=[]
        if source.path.suffix == ".json": values=list(_walk_json(json.loads(source.content.decode())))
        elif source.path.suffix == ".csv":
            for number, row in enumerate(_rows(snapshot, source.path), 1):
                values.extend((field, f"row:{number}.{field}", row[field]) for field in FIELDS if field in row)
        elif source.path.suffix == ".py": values=list(_python_literals(source))
        if source.path.parts[0] == "tests":
            present={field for field, _, _ in values}
            values.extend((field, "static_test_field_literal", field) for field in FIELDS if field in source.content.decode() and field not in present)
        for field, location, value in values:
            kind, real, synthetic, placeholder, note=_observed_kind(source, field)
            rows.append({"value_order":str(len(rows)+1), "field_name":field, "source_path":source.path.as_posix(), "representation":f"static_literal_or_value:{location}", "source_kind":kind, "real_observed_value":str(real).lower(), "synthetic_example":str(synthetic).lower(), "placeholder":str(placeholder).lower(), "schema_only":"false", "produced_by_download_execution":"false", "admissible_as_semantic_evidence":"false", "notes":note})
    return rows

def _source_rows(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    return [{"source_order":str(index), "source_relative_path":source.path.as_posix(), "source_kind":_kind(source.path), "base_tree_mode":source.base_mode, "base_tree_sha256":source.sha256, "filesystem_sha256":source.sha256, "tracked_regular_non_symlink":"true", "parent_chain_verified":"true", "pinned_fd_read":"true", "triple_sha256_passed":"true", "source_boundary_passed":"true"} for index, source in enumerate(snapshot, 1)]

def _issue_rows(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    inherited=_rows(snapshot, RUNTIME_ISSUES)
    columns=tuple(inherited[0])
    additions=(
        ("ADMIT_012_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED", "download_result_status|observed_http_status|observed_content_length_bytes|observed_sha256"), ("ADMIT_012_PRESENCE_SEMANTICS_UNRESOLVED", "download_result_status|observed_http_status|observed_content_length_bytes|observed_sha256"), ("ADMIT_012_MULTI_INVALID_PRECEDENCE_UNRESOLVED", "download_result_status|observed_http_status|observed_content_length_bytes|observed_sha256"), ("ADMIT_012_STANDALONE_SIGNATURE_UNRESOLVED", ""), ("ADMIT_012_RESULT_CONTRACT_UNRESOLVED", ""),
    )
    for issue, fields in additions:
        inherited.append({column: {"issue_id":issue, "issue_type":"implementation_semantics_gap", "affected_fields":fields, "affected_rules":"ADMIT_012", "severity":"blocking", "status":"open", "blocking_scope":"admission_evaluator_rule_logic", "blocking_reason":issue, "issue_origin":STAGE, "integration_transition":"new_open", "issue_count":"1"}.get(column, "") for column in columns})
    return inherited

def _readiness() -> dict[str, bool]:
    return {"unified_dispatch_runtime_with_admit_001_to_011_implemented":True, "admit_011_registered_in_engine":True, "admit_012_preconditions_audited":True, "feature_semantics_audit_required_before_training":True, "step12d_is_final_training_feature_contract":False, "admit_012_rule_logic_implemented":False, "evaluate_admit_012_implemented":False, "Admit012EvaluationResult_implemented":False, "admit_012_unified_adapter_contract_frozen":False, "admit_012_unified_adapter_implemented":False, "admit_012_registered_in_engine":False, "unified_dispatch_runtime_with_admit_001_to_012_implemented":False, "provider_mapping_validated":False, "real_provider_evaluation_ready":False, "ready_for_bulk_download_now":False, "combined_candidate_verdict_implemented":False, "ready_for_training":False, "admit_012_field_semantics_complete":False, "admit_012_routing_responsibility_resolved":False, "admit_012_validation_precedence_resolved":False, "ready_for_admit_012_standalone_evaluator_interface_implementation":False}

def _payloads(snapshot: tuple[Source, ...]) -> dict[str, bytes]:
    _contracts(snapshot)
    payloads={PRECONDITION:_csv_bytes(COLUMNS[PRECONDITION], _preconditions()), OCCURRENCE:_csv_bytes(COLUMNS[OCCURRENCE], _occurrences(snapshot)), OBSERVED:_csv_bytes(COLUMNS[OBSERVED], _observed(snapshot)), SOURCE_AUDIT:_csv_bytes(COLUMNS[SOURCE_AUDIT], _source_rows(snapshot))}
    issues=_issue_rows(snapshot); payloads[ISSUE]=_csv_bytes(tuple(issues[0]), issues)
    hashes={name:hashlib.sha256(data).hexdigest() for name,data in payloads.items()}
    readiness=_readiness()
    occurrence_rows=_occurrences(snapshot); observed_rows=_observed(snapshot)
    manifest={"project":"CovaPIE", "stage":STAGE, "base_commit":BASE_COMMIT, "base_subject":BASE_SUBJECT, "admission_rule_id":"ADMIT_012", "admission_rule_name":"future_download_integrity_fields_required", "evidence_source":"future_download_result", "evaluation_phase":"post_download", "required_status":"download_status_http_status_content_length_and_sha256_present", "blocking_reason":"download_integrity_fields_missing", "exact4_fields":list(FIELDS), "field_semantics":"incomplete", "routing_responsibility":"unresolved", "presence_semantics":"unresolved", "multi_invalid_precedence":"unresolved", "future_evaluator_pure_in_memory":True, "network_required_inside_evaluator":False, "raw_structure_required_inside_evaluator":False, "renameat2_policy":"RENAME_NOREPLACE_required;_EINVAL_fails_closed_without_os.replace_fallback", "admit_012_013_boundary":"ADMIT_012_requires_integrity_field_contract;_ADMIT_013_retains_download_failure_fail_closed", "source_count":EXPECTED_SOURCE_COUNT, "source_path_list_sha256":EXPECTED_PATH_LIST_SHA256, "source_path_sha256_pairs_sha256":EXPECTED_PATH_SHA256_PAIRS_SHA256, "occurrence_row_count":len(occurrence_rows), "occurrence_authority_counts":{key:sum(row["source_authority_level"]==key for row in occurrence_rows) for key in ("primary_committed_contract","historical_or_reference")}, "observed_value_row_count":len(observed_rows), "observed_value_source_kind_counts":{key:sum(row["source_kind"]==key for row in observed_rows) for key in sorted({row["source_kind"] for row in observed_rows})}, "authorized_admit_012_download_execution_count":0, "real_provider_mapping_validated":False, "recommended_next_step":"design_covapie_admit_012_download_integrity_field_contract_v1", "step12d_status":"smoke_legality_only_not_final_training_feature_contract", "readiness":readiness, "safety":{"network":False,"filesystem":False,"raw":False,"provider_mapping":False,"real_download":False,"runtime_change":False,"training":False}, "output_sha256":hashes, "all_checks_passed":True}
    manifest.update(readiness); payloads[MANIFEST]=(json.dumps(manifest, indent=2, sort_keys=True)+"\n").encode()
    return payloads

def _rename_noreplace(source: Path, destination: Path) -> None:
    # Linux renameat2(RENAME_NOREPLACE); EINVAL is deliberately not downgraded.
    if os.uname().machine not in {"x86_64", "amd64"}: raise ValueError("renameat2 syscall number unavailable")
    result=ctypes.CDLL(None, use_errno=True).syscall(316, -100, os.fsencode(source), -100, os.fsencode(destination), 1)
    if result != 0:
        error=ctypes.get_errno()
        raise OSError(error, os.strerror(error), destination)

def _fsync_directory(path: Path) -> None:
    descriptor=os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0))
    try: os.fsync(descriptor)
    finally: os.close(descriptor)

def _write_staged_leaf(path: Path, data: bytes) -> None:
    descriptor=os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0), 0o644)
    try:
        view=memoryview(data)
        while view: view=view[os.write(descriptor, view):]
        os.fsync(descriptor)
    finally: os.close(descriptor)

def _read_exact_output_set(root: Path, payloads: dict[str, bytes]) -> bool:
    item=os.lstat(root)
    if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode) or root.resolve(strict=True) != root: raise ValueError("unsafe output root")
    entries={entry.name:entry for entry in root.iterdir()}
    if set(entries) != set(FILES): return False
    for name, expected in payloads.items():
        leaf=entries[name]; before=os.lstat(leaf)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode): raise ValueError("unsafe output leaf")
        descriptor=os.open(leaf, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0))
        try:
            expected_identity=_identity(before)
            if _identity(os.fstat(descriptor)) != expected_identity: raise ValueError("output leaf stat/open race")
            data=b""
            while True:
                chunk=os.read(descriptor, 1024*1024)
                if not chunk: break
                data+=chunk
            if _identity(os.fstat(descriptor)) != expected_identity: raise ValueError("output leaf FD identity drift after read")
        finally: os.close(descriptor)
        if _identity(os.lstat(leaf)) != expected_identity: raise ValueError("output leaf lexical replacement")
        if data != expected: return False
    return True

def _cleanup_owned_staging(staging: Path, owned: set[str]) -> None:
    if not staging.exists(): return
    entries={item.name:item for item in staging.iterdir()}
    if set(entries) - owned: return
    for name in owned:
        item=entries.get(name)
        if item is not None and stat.S_ISREG(os.lstat(item).st_mode) and not item.is_symlink(): item.unlink()
    try: staging.rmdir()
    except OSError: pass

def materialize_audit(output_root: Path | None = None) -> dict[str, Any]:
    root=REPO_ROOT / DEFAULT_OUTPUT_ROOT if output_root is None else Path(output_root)
    parent=root.parent
    parent_item=os.lstat(parent)
    if root.is_absolute() and parent.resolve(strict=True) != parent or stat.S_ISLNK(parent_item.st_mode) or not stat.S_ISDIR(parent_item.st_mode): raise ValueError("unsafe output parent")
    # This preflight intentionally mutates nothing and existing output sets are never repaired.
    root_exists=root.exists()
    snapshot=build_frozen_source_snapshot(); payloads=_payloads(snapshot)
    if root_exists:
        if _read_exact_output_set(root, payloads): return json.loads(payloads[MANIFEST])
        raise ValueError("existing output set mismatch")
    staging=Path(tempfile.mkdtemp(prefix=f".{root.name}.", suffix=".staging", dir=parent))
    owned=set(FILES)
    try:
        for name, data in payloads.items():
            _write_staged_leaf(staging/name, data)
        _fsync_directory(staging)
        _rename_noreplace(staging, root)
        _fsync_directory(parent)
        if not _read_exact_output_set(root, payloads): raise ValueError("published output postverify failed")
    except BaseException:
        _cleanup_owned_staging(staging, owned)
        raise
    return json.loads(payloads[MANIFEST])

def run_covapie_bulk_download_admission_admit_012_formal_evaluator_interface_preconditions_audit_v1(output_root: Path | None = None) -> dict[str, Any]:
    return materialize_audit(output_root)
