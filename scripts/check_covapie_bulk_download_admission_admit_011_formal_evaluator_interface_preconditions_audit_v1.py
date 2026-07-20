#!/usr/bin/env python3
"""Independent, base-anchored checker for the ADMIT_011 precondition audit."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "ce5323d6fce27e42cfdfa5faad198dbf0f719d19"
BASE_SUBJECT = "add CovaPIE unified admission runtime for ADMIT_001 to ADMIT_010 v1"
STAGE = "covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1"
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
FILES = (
    "covapie_admit_011_formal_evaluator_precondition_matrix.csv",
    "covapie_admit_011_raw_target_field_occurrence_inventory.csv",
    "covapie_admit_011_raw_target_observed_value_inventory.csv",
    "covapie_admit_011_source_boundary_audit.csv",
    "covapie_admit_011_formal_evaluator_issue_readiness_inventory.csv",
    "covapie_admit_011_formal_evaluator_preconditions_manifest.json",
)
PRECONDITION, OCCURRENCE, OBSERVED, SOURCE_AUDIT, ISSUE, MANIFEST = FILES
EXPECTED_OUTPUT_ROOT = OUTPUT_ROOT
EXPECTED_FILES = FILES
CSV_COLUMNS = {
    PRECONDITION: ("precondition_id", "semantic_area", "verified", "evidence", "blocker_id", "implementation_disposition"),
    OCCURRENCE: ("occurrence_order", "source_relative_path", "source_sha256", "source_kind", "line_number", "occurrence_class", "text"),
    OBSERVED: ("value_order", "source_relative_path", "source_sha256", "container_kind", "field_location", "observed_value", "value_state", "grammar_promoted", "evaluator_usable"),
    SOURCE_AUDIT: ("source_order", "source_relative_path", "source_kind", "base_tree_sha256", "filesystem_sha256", "tracked_regular_non_symlink", "source_boundary_passed"),
}
SOURCE_COUNT = 99
PATH_LIST_SHA256 = "5bcdf682ac5a536c28fe8b6bd4f11421d80a3647e14e3464f7558806b2a85922"
PATH_SHA256_PAIRS_SHA256 = "750f995b01ff3bd93ab0dc4fe3683b280e7a94175487b9992fd81a9c803404ee"
PRECONDITION_ROWS_SHA256 = "cd9c7d0a6216ce7cf1490d530f01aeb4cdd823509b4f4e82b262d061d2af4233"
OCCURRENCE_ROWS_SHA256 = "ed8a909f3729d0e73281e234b124fd8e86e06500fc6726827462d508f9dcb034"
OBSERVED_ROWS_SHA256 = "cd6949d681479ae4743ff72ea7333923baa876923dfb4b997b0855278ffdac73"
SOURCE_ROWS_SHA256 = "5bbb7c70a6875f1880fe947113e8b32593dab6783d3ad5add9ad8e8504b9e9ea"
ISSUE_SHA256 = "f59eecc7136ebdd148f2c6c6422b7a2bc0637e340322e09bc005eb00355db03c"
EXPECTED_OUTPUT_SHA256 = {
    PRECONDITION: "3ba029d388bdf860361202de27283abb337b3372cca66b3c9425abaacf8788e7",
    OCCURRENCE: "09a738c169fd3819290060ceb743cef2a9594def200b4625d4d82349eb896af0",
    OBSERVED: "2a5caae4ef52400710ddc70cb374f618fccbfdfeb8d2f3e8326586f58ce4b48c",
    SOURCE_AUDIT: "9fe10646888b0197102816fade40b2162a2a375318736207e3d1b655415a257c",
    ISSUE: ISSUE_SHA256,
    MANIFEST: "8e4ebee6b82cb6a63d291e97dd118596d07a254decf6d36803c2e2a9895471b1",
}
PRIMARY_BLOCKER = "RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED"
RECOMMENDED_NEXT_STEP = "design_covapie_admit_011_raw_target_relative_path_contract_v1"
RULE_REGISTRY_PATH = "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv"
SCHEMA_PATH = "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_schema_contract.csv"
EXECUTABILITY_PATH = "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_rule_executability_matrix.csv"
FIELD_SEMANTICS_PATH = "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_field_semantics_matrix.csv"
CONTEXT_PATH = "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv"
IMPLEMENTATION_ISSUE_PATH = "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_implementation_issue_inventory.csv"
RUNTIME_ISSUE_PATH = "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1/covapie_admit_001_to_010_runtime_issue_inventory.csv"
REQUIRED_PATHS = frozenset((RULE_REGISTRY_PATH, SCHEMA_PATH, EXECUTABILITY_PATH, FIELD_SEMANTICS_PATH, CONTEXT_PATH, IMPLEMENTATION_ISSUE_PATH, RUNTIME_ISSUE_PATH))


@dataclass(frozen=True)
class Source:
    path: str
    content: bytes
    sha256: str


def _git(args: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=text, check=False)


def _canon(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=False).encode("utf-8")


def _contained(path: Path, root: Path) -> bool:
    return path.is_relative_to(root)


def _real_repo_root() -> Path:
    assert REPO_ROOT.is_absolute()
    metadata = os.lstat(REPO_ROOT)
    assert stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    assert REPO_ROOT.resolve(strict=True) == REPO_ROOT
    return REPO_ROOT


def _output_preflight(root: Path) -> Path:
    repo = _real_repo_root()
    candidate = root if root.is_absolute() else repo / root
    if not root.is_absolute():
        assert _contained(candidate.resolve(strict=False), repo)
    parent = candidate.parent
    assert parent.exists()
    anchor = Path(candidate.anchor) if candidate.is_absolute() else repo
    current = parent
    while True:
        metadata = os.lstat(current)
        assert stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
        if current == anchor:
            break
        assert current.parent != current
        current = current.parent
    candidate = parent.resolve(strict=True) / candidate.name
    if not root.is_absolute():
        assert _contained(candidate, repo)
    metadata = os.lstat(candidate)
    assert stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    assert candidate.resolve(strict=True) == candidate
    entries = tuple(candidate.iterdir())
    assert {item.name for item in entries} == set(FILES)
    for item in entries:
        metadata = os.lstat(item)
        assert stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
        assert item.resolve(strict=True) == item
    return candidate


def _safe_source_path(path: str) -> bool:
    item = Path(path)
    return not item.is_absolute() and bool(item.parts) and ".." not in item.parts and item.parts[:2] != ("data", "raw") and item.parts[0] != "checkpoints"


def _base_paths() -> tuple[str, ...]:
    result = _git(["grep", "-l", "-I", "raw_target_relative_path", BASE_COMMIT, "--", ":!data/raw/**", ":!checkpoints/**"])
    assert result.returncode in (0, 1)
    prefix = f"{BASE_COMMIT}:"
    lines = [line for line in result.stdout.splitlines() if line]
    assert all(line.startswith(prefix) for line in lines)
    paths = tuple(sorted({line.removeprefix(prefix) for line in lines} | REQUIRED_PATHS))
    assert len(paths) == SOURCE_COUNT == len(set(paths))
    assert set(REQUIRED_PATHS) <= set(paths) and all(_safe_source_path(path) and STAGE not in path for path in paths)
    assert hashlib.sha256(_canon(list(paths))).hexdigest() == PATH_LIST_SHA256
    return paths


def _structure(path: str, repo: Path) -> None:
    absolute = repo / path
    metadata = os.lstat(absolute)
    tracked = _git(["ls-files", "--error-unmatch", "--", path])
    tree = _git(["ls-tree", BASE_COMMIT, "--", path])
    fields = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
    assert tracked.returncode == tree.returncode == 0 and len(fields) == 3 and fields[0] in {"100644", "100755"} and fields[1] == "blob"
    assert stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    current = absolute.parent
    while current != repo:
        item = os.lstat(current)
        assert stat.S_ISDIR(item.st_mode) and not stat.S_ISLNK(item.st_mode)
        current = current.parent
    assert absolute.resolve(strict=True) == absolute and _contained(absolute, repo)


def _snapshot() -> tuple[Source, ...]:
    repo = _real_repo_root()
    subject = _git(["show", "-s", "--format=%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    assert subject.returncode == ancestor.returncode == 0 and subject.stdout.strip() == BASE_SUBJECT
    paths = _base_paths()
    for path in paths:
        _structure(path, repo)
    result: list[Source] = []
    pairs: list[list[str]] = []
    for path in paths:
        base = _git(["show", f"{BASE_COMMIT}:{path}"], text=False)
        current = (repo / path).read_bytes()
        assert base.returncode == 0 and type(base.stdout) is bytes
        digest = hashlib.sha256(base.stdout).hexdigest()
        assert digest == hashlib.sha256(current).hexdigest()
        pairs.append([path, digest])
        result.append(Source(path, current, digest))
    assert hashlib.sha256(_canon(pairs)).hexdigest() == PATH_SHA256_PAIRS_SHA256
    return tuple(result)


def _source(snapshot: tuple[Source, ...], path: str) -> Source:
    return next(item for item in snapshot if item.path == path)


def _csv(snapshot: tuple[Source, ...], path: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(_source(snapshot, path).content.decode("utf-8"), newline="")))


def _kind(path: str) -> str:
    if path.endswith(".py"):
        return "python_source"
    if path.endswith(".json"):
        return "committed_manifest"
    if path.endswith(".csv"):
        return "committed_schema_or_evidence_csv"
    return "tracked_text_source"


def _precondition_rows() -> list[dict[str, str]]:
    specs = (
        ("canonical_identity", True, "registry fixes ADMIT_011/raw_overwrite_forbidden/pre_download", ""), ("candidate_field", True, "schema and Step14AU-A fix raw_target_relative_path", ""),
        ("historical_vocabulary", True, "registry fixes target_does_not_overwrite_existing_raw/raw_target_overwrite_forbidden", ""), ("required_context_shape", True, "existing_raw_target_relative_paths plus raw_target_relative_path_contract are named", ""),
        ("issue_and_coverage", True, "Exact10 preserves blocker open and coverage ADMIT_011–ADMIT_015", ""), ("all_tracked_occurrences", True, "all tracked non-raw field occurrences are frozen and inventoried", ""),
        ("observed_values_and_missing_states", True, "CSV/manifest direct values are recorded without grammar promotion", ""), ("pure_memory_interface_feasibility", True, "Step14AU-A declares filesystem/network false and pure interface possible", ""),
        ("relative_path_grammar", False, "absolute, traversal, empty segment, dot, separator, Windows, NUL and non-ASCII policy is not formally defined", PRIMARY_BLOCKER), ("lexical_vs_resolved_boundary", False, "no canonical lexical/resolved path boundary", PRIMARY_BLOCKER),
        ("root_identity_and_allowlist", False, "no canonical raw-root identity or allowlisted target root", PRIMARY_BLOCKER), ("target_object_semantics", False, "existing target, overwrite, symlink, directory, FIFO and device semantics are not frozen", PRIMARY_BLOCKER),
        ("context_responsibility", False, "candidate, batch snapshot, download and stage ownership is not fully allocated", PRIMARY_BLOCKER), ("provider_mapping", False, "candidate_metadata_provider is only a scope label; mapping remains unverified", PRIMARY_BLOCKER),
        ("admit_012_013_boundary", True, "ADMIT_011 is pre_download target admission; ADMIT_012/013 are post_download result contracts", ""),
    )
    rows = [{"precondition_id": f"PRE_{index:03d}", "semantic_area": area, "verified": str(verified).lower(), "evidence": evidence, "blocker_id": blocker, "implementation_disposition": "retain_as_unverified_precondition" if not verified else "interface_evidence_only"} for index, (area, verified, evidence, blocker) in enumerate(specs, 1)]
    assert hashlib.sha256(_canon(rows)).hexdigest() == PRECONDITION_ROWS_SHA256
    return rows


def _occurrence_rows(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source in snapshot:
        for line_number, line in enumerate(source.content.decode("utf-8").splitlines(), 1):
            if "raw_target_relative_path" in line:
                classification = "schema_or_contract" if any(token in Path(source.path).name for token in ("schema", "contract", "matrix", "manifest")) else "source_or_historical_evidence"
                if "unresolved" in line.lower():
                    classification = "open_blocker_evidence"
                rows.append({"occurrence_order": str(len(rows) + 1), "source_relative_path": source.path, "source_sha256": source.sha256, "source_kind": _kind(source.path), "line_number": str(line_number), "occurrence_class": classification, "text": line})
    assert len(rows) == 172 and hashlib.sha256(_canon(rows)).hexdigest() == OCCURRENCE_ROWS_SHA256
    return rows


def _walk_json(value: Any, location: str = "$") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key in sorted(value):
            child = f"{location}.{key}"
            if key == "raw_target_relative_path":
                yield child, value[key]
            yield from _walk_json(value[key], child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_json(item, f"{location}[{index}]")


def _observed_rows(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source in snapshot:
        values: list[tuple[str, Any]] = []
        if source.path.endswith(".csv"):
            for index, row in enumerate(_csv(snapshot, source.path), 1):
                if "raw_target_relative_path" in row:
                    values.append((f"row:{index}", row["raw_target_relative_path"]))
        elif source.path.endswith(".json"):
            values.extend(_walk_json(json.loads(source.content.decode("utf-8"))))
        for location, value in values:
            observed = value if isinstance(value, str) else json.dumps(value, sort_keys=True)
            value_state = "missing_empty" if observed == "" else "missing_null_like" if observed.lower() in {"null", "none", "n/a", "na"} else "present_historical_or_fixture_value"
            rows.append({"value_order": str(len(rows) + 1), "source_relative_path": source.path, "source_sha256": source.sha256, "container_kind": _kind(source.path), "field_location": location, "observed_value": observed, "value_state": value_state, "grammar_promoted": "false", "evaluator_usable": "false"})
    assert len(rows) == 47 and hashlib.sha256(_canon(rows)).hexdigest() == OBSERVED_ROWS_SHA256
    return rows


def _source_rows(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    rows = [{"source_order": str(index), "source_relative_path": source.path, "source_kind": _kind(source.path), "base_tree_sha256": source.sha256, "filesystem_sha256": source.sha256, "tracked_regular_non_symlink": "true", "source_boundary_passed": "true"} for index, source in enumerate(snapshot, 1)]
    assert hashlib.sha256(_canon(rows)).hexdigest() == SOURCE_ROWS_SHA256
    return rows


def _verify_contract(snapshot: tuple[Source, ...]) -> bytes:
    rule = next(row for row in _csv(snapshot, RULE_REGISTRY_PATH) if row["admission_rule_id"] == "ADMIT_011")
    executable = next(row for row in _csv(snapshot, EXECUTABILITY_PATH) if row["admission_rule_id"] == "ADMIT_011")
    contexts = [row for row in _csv(snapshot, CONTEXT_PATH) if row["required_by_rules"] == "ADMIT_011"]
    issue = _source(snapshot, RUNTIME_ISSUE_PATH).content
    rows = list(csv.DictReader(issue.decode("utf-8").splitlines()))
    blocker = next(row for row in rows if row["issue_id"] == PRIMARY_BLOCKER)
    coverage = next(row for row in rows if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert rule["admission_rule_name"] == "raw_overwrite_forbidden" and rule["evaluation_phase"] == "pre_download" and rule["required_status"] == "target_does_not_overwrite_existing_raw" and rule["blocking_reason"] == "raw_target_overwrite_forbidden"
    assert executable["candidate_field_dependencies"] == "raw_target_relative_path" and executable["evaluation_context_dependencies"] == "existing_raw_target_relative_paths|raw_target_relative_path_contract" and executable["external_filesystem_required"] == executable["network_required"] == "false" and executable["pure_in_memory_interface_possible"] == "true"
    assert {(row["context_item"], row["context_scope"], row["exact_contract_defined"]) for row in contexts} == {("existing_raw_target_relative_paths", "batch_external_state_snapshot", "true"), ("raw_target_relative_path_contract", "evaluation_policy", "false")}
    assert hashlib.sha256(issue).hexdigest() == ISSUE_SHA256 and blocker["status"] == "open" and blocker["affected_fields"] == "raw_target_relative_path" and blocker["affected_rules"] == "ADMIT_011"
    assert coverage["affected_rules"] == "ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"
    return issue


def _readiness() -> dict[str, bool]:
    return {"admit_011_precondition_audit_complete": True, "admit_011_canonical_identity_verified": True, "admit_011_field_occurrences_audited": True, "admit_011_pure_in_memory_interface_feasible": True, "ready_for_admit_011_raw_target_relative_path_contract_design": True, "ready_for_admit_011_standalone_evaluator_interface_implementation": False, "raw_target_relative_path_contract_frozen": False, "admit_011_rule_logic_implemented": False, "admit_011_adapter_implemented": False, "admit_011_registered_in_engine": False, "unified_dispatch_runtime_with_admit_001_to_011_implemented": False, "real_provider_evaluation_ready": False, "provider_mapping_validated": False, "evaluate_all_rules_implemented": False, "combined_candidate_verdict_implemented": False, "ready_for_bulk_download_now": False, "ready_for_training": False, "feature_semantics_audit_required_before_training": True}


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _expected_payloads() -> dict[str, bytes]:
    snapshot = _snapshot()
    preconditions, occurrences, observed, sources, issue = _precondition_rows(), _occurrence_rows(snapshot), _observed_rows(snapshot), _source_rows(snapshot), _verify_contract(snapshot)
    payloads = {PRECONDITION: _csv_bytes(CSV_COLUMNS[PRECONDITION], preconditions), OCCURRENCE: _csv_bytes(CSV_COLUMNS[OCCURRENCE], occurrences), OBSERVED: _csv_bytes(CSV_COLUMNS[OBSERVED], observed), SOURCE_AUDIT: _csv_bytes(CSV_COLUMNS[SOURCE_AUDIT], sources), ISSUE: issue}
    output_hashes = {name: hashlib.sha256(value).hexdigest() for name, value in payloads.items()}
    readiness = _readiness()
    manifest: dict[str, Any] = {"project": "CovaPIE", "stage": STAGE, "step": "ADMIT_011 formal evaluator interface preconditions audit v1", "base_commit": BASE_COMMIT, "base_subject": BASE_SUBJECT, "admission_rule_id": "ADMIT_011", "admission_rule_name": "raw_overwrite_forbidden", "evaluation_phase": "pre_download", "candidate_field": "raw_target_relative_path", "required_context": ["existing_raw_target_relative_paths", "raw_target_relative_path_contract"], "required_status": "target_does_not_overwrite_existing_raw", "historical_blocking_reason": "raw_target_overwrite_forbidden", "primary_unresolved_blocker": PRIMARY_BLOCKER, "primary_blocker_status": "open", "source_count": SOURCE_COUNT, "source_path_list_sha256": PATH_LIST_SHA256, "source_path_sha256_pairs_sha256": PATH_SHA256_PAIRS_SHA256, "occurrence_row_count": 172, "observed_value_row_count": 47, "observed_value_state_counts": {"present_historical_or_fixture_value": 47, "missing_empty": 0, "missing_null_like": 0}, "issue_inventory_byte_identical_to_exact10": True, "admit_012_013_boundary": "post_download_download_result_contract_not_evaluated_here", "readiness": readiness, "safety": {"raw_read": False, "filesystem_target_probe": False, "network_or_download": False, "real_candidate_evaluation": False, "evaluate_all_rules": False, "combined_verdict": False, "training": False, "runtime_change": False}, "recommended_next_step": RECOMMENDED_NEXT_STEP, "output_sha256": output_hashes, "all_checks_passed": True}
    manifest.update(readiness)
    payloads[MANIFEST] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    assert {name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()} == EXPECTED_OUTPUT_SHA256
    return payloads


def _validate_output_tree(root: Path = REPO_ROOT / OUTPUT_ROOT, *, enforce_frozen_hashes: bool = True) -> None:
    checked = _output_preflight(root)
    expected = _expected_payloads()
    for name, value in expected.items():
        assert (checked / name).read_bytes() == value
    if enforce_frozen_hashes:
        assert {name: hashlib.sha256((checked / name).read_bytes()).hexdigest() for name in FILES} == EXPECTED_OUTPUT_SHA256


def main() -> int:
    _validate_output_tree()
    print(json.dumps({"output_sha256": EXPECTED_OUTPUT_SHA256, "stage": STAGE, "status": "passed"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
