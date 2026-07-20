"""Read-only ADMIT_011 formal-evaluator interface precondition audit v1.

This audit is anchored to the Exact10 base tree.  It never follows a raw
artifact reference, probes a candidate target, or implements an evaluator.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import stat
import subprocess
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STEP = "ADMIT_011 formal evaluator interface preconditions audit v1"
STAGE = "covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1"
EXPECTED_BASE_COMMIT = "ce5323d6fce27e42cfdfa5faad198dbf0f719d19"
EXPECTED_BASE_SUBJECT = "add CovaPIE unified admission runtime for ADMIT_001 to ADMIT_010 v1"
EXPECTED_SOURCE_COUNT = 99
EXPECTED_PATH_LIST_SHA256 = "5bcdf682ac5a536c28fe8b6bd4f11421d80a3647e14e3464f7558806b2a85922"
EXPECTED_PATH_SHA256_PAIRS_SHA256 = "750f995b01ff3bd93ab0dc4fe3683b280e7a94175487b9992fd81a9c803404ee"
PRIMARY_BLOCKER = "RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED"
RECOMMENDED_NEXT_STEP = "design_covapie_admit_011_raw_target_relative_path_contract_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

RULE_REGISTRY_PATH = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv")
SCHEMA_PATH = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_schema_contract.csv")
EXECUTABILITY_PATH = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_rule_executability_matrix.csv")
FIELD_SEMANTICS_PATH = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_field_semantics_matrix.csv")
CONTEXT_PATH = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv")
IMPLEMENTATION_ISSUE_PATH = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_implementation_issue_inventory.csv")
RUNTIME_ISSUE_PATH = Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1/covapie_admit_001_to_010_runtime_issue_inventory.csv")
REQUIRED_CANONICAL_PATHS = frozenset((RULE_REGISTRY_PATH, SCHEMA_PATH, EXECUTABILITY_PATH, FIELD_SEMANTICS_PATH, CONTEXT_PATH, IMPLEMENTATION_ISSUE_PATH, RUNTIME_ISSUE_PATH))

PRECONDITION_FILENAME = "covapie_admit_011_formal_evaluator_precondition_matrix.csv"
OCCURRENCE_FILENAME = "covapie_admit_011_raw_target_field_occurrence_inventory.csv"
OBSERVED_FILENAME = "covapie_admit_011_raw_target_observed_value_inventory.csv"
SOURCE_BOUNDARY_FILENAME = "covapie_admit_011_source_boundary_audit.csv"
ISSUE_FILENAME = "covapie_admit_011_formal_evaluator_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_011_formal_evaluator_preconditions_manifest.json"
OUTPUT_FILES = (PRECONDITION_FILENAME, OCCURRENCE_FILENAME, OBSERVED_FILENAME, SOURCE_BOUNDARY_FILENAME, ISSUE_FILENAME, MANIFEST_FILENAME)
CSV_COLUMNS = {
    PRECONDITION_FILENAME: ("precondition_id", "semantic_area", "verified", "evidence", "blocker_id", "implementation_disposition"),
    OCCURRENCE_FILENAME: ("occurrence_order", "source_relative_path", "source_sha256", "source_kind", "line_number", "occurrence_class", "text"),
    OBSERVED_FILENAME: ("value_order", "source_relative_path", "source_sha256", "container_kind", "field_location", "observed_value", "value_state", "grammar_promoted", "evaluator_usable"),
    SOURCE_BOUNDARY_FILENAME: ("source_order", "source_relative_path", "source_kind", "base_tree_sha256", "filesystem_sha256", "tracked_regular_non_symlink", "source_boundary_passed"),
}


@dataclass(frozen=True)
class FrozenSource:
    path: Path
    content: bytes
    sha256: str


def _git(args: list[str], repo_root: Path, *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=text, check=False)


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=False).encode("utf-8")


def _resolved_real_directory(path: Path, *, label: str) -> Path:
    if not path.is_absolute():
        raise ValueError(f"{label} must be absolute")
    metadata = os.lstat(path)
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise ValueError(f"{label} must be a real non-symlink directory")
    resolved = path.resolve(strict=True)
    if resolved != path:
        raise ValueError(f"{label} must equal its resolved path")
    return resolved


def _is_contained(path: Path, root: Path) -> bool:
    return path.is_relative_to(root)


def _assert_real_parent_chain(parent: Path, *, anchor: Path) -> None:
    current = parent
    while True:
        metadata = os.lstat(current)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise ValueError("output parent component is unsafe")
        if current == anchor:
            return
        if current.parent == current:
            raise ValueError("output parent escaped containment anchor")
        current = current.parent


def _resolved_output_preflight(output_root: Path, repo_root: Path = REPO_ROOT) -> tuple[Path, bool]:
    """Purely inspect an output location before source/state work begins."""
    resolved_repo = _resolved_real_directory(repo_root, label="repo root")
    if output_root.is_absolute():
        root = output_root
        parent_anchor = Path(root.anchor)
    else:
        root = resolved_repo / output_root
        parent_anchor = resolved_repo
        if not _is_contained(root.resolve(strict=False), resolved_repo):
            raise ValueError("relative output root escapes repository")
    parent = root.parent
    if not parent.exists():
        raise ValueError("output parent must already exist")
    _assert_real_parent_chain(parent, anchor=parent_anchor)
    resolved_parent = parent.resolve(strict=True)
    candidate = resolved_parent / root.name
    if not output_root.is_absolute() and not _is_contained(candidate, resolved_repo):
        raise ValueError("relative output root escapes repository")
    try:
        metadata = os.lstat(candidate)
    except FileNotFoundError:
        return candidate, True
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("output root must be a real non-symlink directory")
    if candidate.resolve(strict=True) != candidate:
        raise ValueError("output root must equal its resolved path")
    entries = tuple(candidate.iterdir())
    if {entry.name for entry in entries} - set(OUTPUT_FILES):
        raise ValueError("output root contains an unexpected entry")
    for entry in entries:
        item = os.lstat(entry)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
            raise ValueError("existing output entry must be regular and non-symlink")
        if entry.resolve(strict=True) != entry:
            raise ValueError("output entry resolved containment failed")
    return candidate, False


def _validate_prewrite_output_root(
    root: Path,
    repo_root: Path,
    *,
    output_root_was_relative: bool,
    newly_created: bool,
) -> None:
    """Revalidate containment and inventory immediately before the first write."""
    checked_root, create_root = _resolved_output_preflight(root, repo_root)
    if checked_root != root or create_root:
        raise ValueError("prewrite output containment revalidation failed")
    resolved_repo = _resolved_real_directory(repo_root, label="repo root")
    if output_root_was_relative and not _is_contained(root, resolved_repo):
        raise ValueError("relative output root escaped repository before write")
    entries = tuple(root.iterdir())
    if newly_created and entries:
        raise ValueError("newly-created output root must remain empty before first write")


def _safe_source_path(path: Path) -> bool:
    return not path.is_absolute() and bool(path.parts) and ".." not in path.parts and path.parts[:2] != ("data", "raw") and path.parts[0] != "checkpoints"


def _base_source_paths(repo_root: Path = REPO_ROOT) -> tuple[Path, ...]:
    result = _git(["grep", "-l", "-I", "raw_target_relative_path", EXPECTED_BASE_COMMIT, "--", ":!data/raw/**", ":!checkpoints/**"], repo_root)
    if result.returncode not in (0, 1):
        raise ValueError("base-tree source discovery failed")
    prefix = f"{EXPECTED_BASE_COMMIT}:"
    discovered = {Path(value.removeprefix(prefix)) for value in result.stdout.splitlines() if value.startswith(prefix)}
    if len(discovered) != len([value for value in result.stdout.splitlines() if value]):
        raise ValueError("base-tree source discovery returned an unsafe path")
    paths = tuple(sorted(discovered | REQUIRED_CANONICAL_PATHS, key=lambda item: item.as_posix()))
    serialized_paths = [path.as_posix() for path in paths]
    if len(paths) != EXPECTED_SOURCE_COUNT or len(paths) != len(set(paths)) or not all(_safe_source_path(path) for path in paths):
        raise ValueError("Exact99 source boundary shape invalid")
    if not REQUIRED_CANONICAL_PATHS <= set(paths):
        raise ValueError("canonical source path missing")
    if hashlib.sha256(_canonical_json(serialized_paths)).hexdigest() != EXPECTED_PATH_LIST_SHA256:
        raise ValueError("Exact99 path-list digest mismatch")
    if any(STAGE in path.as_posix() for path in paths):
        raise ValueError("successor ADMIT_011 stage contaminated base source boundary")
    return paths


def _source_structure(path: Path, repo_root: Path, resolved_repo: Path) -> None:
    if not _safe_source_path(path):
        raise ValueError("unsafe source path")
    absolute = repo_root / path
    metadata = os.lstat(absolute)
    tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
    tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", path.as_posix()], repo_root)
    fields = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
    if tracked.returncode or tree.returncode or len(fields) != 3 or fields[0] not in {"100644", "100755"} or fields[1] != "blob":
        raise ValueError(f"source tree metadata invalid: {path}")
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"source leaf is unsafe: {path}")
    # Resolve each parent explicitly: a source parent may not be a symlink.
    current = absolute.parent
    while current != repo_root:
        item = os.lstat(current)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode):
            raise ValueError(f"source parent is unsafe: {path}")
        current = current.parent
    resolved = absolute.resolve(strict=True)
    if resolved != absolute or not _is_contained(resolved, resolved_repo):
        raise ValueError(f"source resolved containment failed: {path}")


def build_frozen_source_snapshot(repo_root: Path = REPO_ROOT) -> tuple[FrozenSource, ...]:
    """Complete all Exact99 structural checks before reading any source bytes."""
    resolved_repo = _resolved_real_directory(repo_root, label="repo root")
    subject = _git(["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT], repo_root)
    ancestor = _git(["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, "HEAD"], repo_root)
    if subject.returncode or ancestor.returncode or subject.stdout.strip() != EXPECTED_BASE_SUBJECT:
        raise ValueError("expected base lineage is unavailable")
    paths = _base_source_paths(repo_root)
    for path in paths:
        _source_structure(path, repo_root, resolved_repo)
    records: list[FrozenSource] = []
    pairs: list[list[str]] = []
    for path in paths:
        base = _git(["show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"], repo_root, text=False)
        current = (repo_root / path).read_bytes()
        if base.returncode or type(base.stdout) is not bytes:
            raise ValueError(f"base blob unavailable: {path}")
        base_sha = hashlib.sha256(base.stdout).hexdigest()
        current_sha = hashlib.sha256(current).hexdigest()
        if base_sha != current_sha:
            raise ValueError(f"source byte mismatch: {path}")
        pairs.append([path.as_posix(), base_sha])
        records.append(FrozenSource(path, current, base_sha))
    if hashlib.sha256(_canonical_json(pairs)).hexdigest() != EXPECTED_PATH_SHA256_PAIRS_SHA256:
        raise ValueError("Exact99 path/SHA digest mismatch")
    return tuple(records)


def _record(snapshot: tuple[FrozenSource, ...], path: Path) -> FrozenSource:
    record = next((item for item in snapshot if item.path == path), None)
    if record is None:
        raise ValueError(f"missing frozen source: {path}")
    return record


def _csv(snapshot: tuple[FrozenSource, ...], path: Path) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(_record(snapshot, path).content.decode("utf-8"), newline=""))
    if not reader.fieldnames:
        raise ValueError(f"invalid CSV source: {path}")
    return [dict(row) for row in reader]


def _source_kind(path: Path) -> str:
    if path.suffix == ".py":
        return "python_source"
    if path.suffix == ".json":
        return "committed_manifest"
    if path.suffix == ".csv":
        return "committed_schema_or_evidence_csv"
    return "tracked_text_source"


def _authoritative_contract(snapshot: tuple[FrozenSource, ...]) -> dict[str, Any]:
    rule = next(row for row in _csv(snapshot, RULE_REGISTRY_PATH) if row["admission_rule_id"] == "ADMIT_011")
    schema = next(row for row in _csv(snapshot, SCHEMA_PATH) if row["admission_field_name"] == "raw_target_relative_path")
    executable = next(row for row in _csv(snapshot, EXECUTABILITY_PATH) if row["admission_rule_id"] == "ADMIT_011")
    field = next(row for row in _csv(snapshot, FIELD_SEMANTICS_PATH) if row["field_name"] == "raw_target_relative_path")
    contexts = [row for row in _csv(snapshot, CONTEXT_PATH) if row["required_by_rules"] == "ADMIT_011"]
    issue = next(row for row in _csv(snapshot, IMPLEMENTATION_ISSUE_PATH) if row["issue_id"] == PRIMARY_BLOCKER)
    runtime_issue = next(row for row in _csv(snapshot, RUNTIME_ISSUE_PATH) if row["issue_id"] == PRIMARY_BLOCKER)
    coverage = next(row for row in _csv(snapshot, RUNTIME_ISSUE_PATH) if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    if not (
        rule["admission_rule_name"] == "raw_overwrite_forbidden" and rule["evaluation_phase"] == "pre_download" and rule["required_status"] == "target_does_not_overwrite_existing_raw" and rule["blocking_reason"] == "raw_target_overwrite_forbidden"
        and schema["requirement_phase"] == "pre_download" and schema["required_at_phase"] == "true"
        and executable["candidate_field_dependencies"] == "raw_target_relative_path" and executable["evaluation_context_dependencies"] == "existing_raw_target_relative_paths|raw_target_relative_path_contract" and executable["external_filesystem_required"] == executable["network_required"] == "false" and executable["pure_in_memory_interface_possible"] == "true"
        and field["producer_scope"] == "candidate_metadata_provider" and field["implementation_semantics_complete"] == "false" and field["blocking_reasons"] == PRIMARY_BLOCKER
        and {(row["context_item"], row["context_scope"], row["exact_contract_defined"]) for row in contexts} == {("existing_raw_target_relative_paths", "batch_external_state_snapshot", "true"), ("raw_target_relative_path_contract", "evaluation_policy", "false")}
        and issue["status"] == runtime_issue["status"] == "open" and issue["affected_fields"] == runtime_issue["affected_fields"] == "raw_target_relative_path" and issue["affected_rules"] == runtime_issue["affected_rules"] == "ADMIT_011"
        and coverage["affected_rules"] == "ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"
    ):
        raise ValueError("canonical ADMIT_011 contract evidence failed")
    return {"rule": rule, "schema": schema, "executable": executable, "field": field, "contexts": contexts, "issue": issue, "runtime_issue": runtime_issue, "coverage": coverage}


def _occurrences(snapshot: tuple[FrozenSource, ...]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for record in snapshot:
        for line_number, line in enumerate(record.content.decode("utf-8").splitlines(), 1):
            if "raw_target_relative_path" in line:
                classification = "schema_or_contract" if any(token in record.path.name for token in ("schema", "contract", "matrix", "manifest")) else "source_or_historical_evidence"
                if "unresolved" in line.lower():
                    classification = "open_blocker_evidence"
                rows.append({"occurrence_order": str(len(rows) + 1), "source_relative_path": record.path.as_posix(), "source_sha256": record.sha256, "source_kind": _source_kind(record.path), "line_number": str(line_number), "occurrence_class": classification, "text": line})
    if len(rows) != 172:
        raise ValueError("Exact172 occurrence inventory mismatch")
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


def _observed_values(snapshot: tuple[FrozenSource, ...]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for record in snapshot:
        values: list[tuple[str, Any]] = []
        if record.path.suffix == ".csv":
            for index, source_row in enumerate(_csv(snapshot, record.path), 1):
                if "raw_target_relative_path" in source_row:
                    values.append((f"row:{index}", source_row["raw_target_relative_path"]))
        elif record.path.suffix == ".json":
            values.extend(_walk_json(json.loads(record.content.decode("utf-8"))))
        for location, value in values:
            observed = value if isinstance(value, str) else json.dumps(value, sort_keys=True)
            state = "missing_empty" if observed == "" else "missing_null_like" if observed.lower() in {"null", "none", "n/a", "na"} else "present_historical_or_fixture_value"
            rows.append({"value_order": str(len(rows) + 1), "source_relative_path": record.path.as_posix(), "source_sha256": record.sha256, "container_kind": _source_kind(record.path), "field_location": location, "observed_value": observed, "value_state": state, "grammar_promoted": "false", "evaluator_usable": "false"})
    if len(rows) != 47:
        raise ValueError("Exact47 observed-value inventory mismatch")
    return rows


def _preconditions() -> list[dict[str, str]]:
    specs = (
        ("canonical_identity", True, "registry fixes ADMIT_011/raw_overwrite_forbidden/pre_download", ""),
        ("candidate_field", True, "schema and Step14AU-A fix raw_target_relative_path", ""),
        ("historical_vocabulary", True, "registry fixes target_does_not_overwrite_existing_raw/raw_target_overwrite_forbidden", ""),
        ("required_context_shape", True, "existing_raw_target_relative_paths plus raw_target_relative_path_contract are named", ""),
        ("issue_and_coverage", True, "Exact10 preserves blocker open and coverage ADMIT_011–ADMIT_015", ""),
        ("all_tracked_occurrences", True, "all tracked non-raw field occurrences are frozen and inventoried", ""),
        ("observed_values_and_missing_states", True, "CSV/manifest direct values are recorded without grammar promotion", ""),
        ("pure_memory_interface_feasibility", True, "Step14AU-A declares filesystem/network false and pure interface possible", ""),
        ("relative_path_grammar", False, "absolute, traversal, empty segment, dot, separator, Windows, NUL and non-ASCII policy is not formally defined", PRIMARY_BLOCKER),
        ("lexical_vs_resolved_boundary", False, "no canonical lexical/resolved path boundary", PRIMARY_BLOCKER),
        ("root_identity_and_allowlist", False, "no canonical raw-root identity or allowlisted target root", PRIMARY_BLOCKER),
        ("target_object_semantics", False, "existing target, overwrite, symlink, directory, FIFO and device semantics are not frozen", PRIMARY_BLOCKER),
        ("context_responsibility", False, "candidate, batch snapshot, download and stage ownership is not fully allocated", PRIMARY_BLOCKER),
        ("provider_mapping", False, "candidate_metadata_provider is only a scope label; mapping remains unverified", PRIMARY_BLOCKER),
        ("admit_012_013_boundary", True, "ADMIT_011 is pre_download target admission; ADMIT_012/013 are post_download result contracts", ""),
    )
    return [{"precondition_id": f"PRE_{index:03d}", "semantic_area": area, "verified": str(verified).lower(), "evidence": evidence, "blocker_id": blocker, "implementation_disposition": "retain_as_unverified_precondition" if not verified else "interface_evidence_only"} for index, (area, verified, evidence, blocker) in enumerate(specs, 1)]


def _source_rows(snapshot: tuple[FrozenSource, ...]) -> list[dict[str, str]]:
    return [{"source_order": str(index), "source_relative_path": item.path.as_posix(), "source_kind": _source_kind(item.path), "base_tree_sha256": item.sha256, "filesystem_sha256": item.sha256, "tracked_regular_non_symlink": "true", "source_boundary_passed": "true"} for index, item in enumerate(snapshot, 1)]


def build_audit_state(snapshot: tuple[FrozenSource, ...] | None = None) -> dict[str, Any]:
    snapshot = snapshot or build_frozen_source_snapshot()
    contracts = _authoritative_contract(snapshot)
    issue_bytes = _record(snapshot, RUNTIME_ISSUE_PATH).content
    readiness = {
        "admit_011_precondition_audit_complete": True,
        "admit_011_canonical_identity_verified": True,
        "admit_011_field_occurrences_audited": True,
        "admit_011_pure_in_memory_interface_feasible": True,
        "ready_for_admit_011_raw_target_relative_path_contract_design": True,
        "ready_for_admit_011_standalone_evaluator_interface_implementation": False,
        "raw_target_relative_path_contract_frozen": False,
        "admit_011_rule_logic_implemented": False,
        "admit_011_adapter_implemented": False,
        "admit_011_registered_in_engine": False,
        "unified_dispatch_runtime_with_admit_001_to_011_implemented": False,
        "real_provider_evaluation_ready": False,
        "provider_mapping_validated": False,
        "evaluate_all_rules_implemented": False,
        "combined_candidate_verdict_implemented": False,
        "ready_for_bulk_download_now": False,
        "ready_for_training": False,
        "feature_semantics_audit_required_before_training": True,
    }
    safety = {"raw_read": False, "filesystem_target_probe": False, "network_or_download": False, "real_candidate_evaluation": False, "evaluate_all_rules": False, "combined_verdict": False, "training": False, "runtime_change": False}
    return {"snapshot": snapshot, "contracts": contracts, "precondition_rows": _preconditions(), "occurrence_rows": _occurrences(snapshot), "observed_rows": _observed_values(snapshot), "source_rows": _source_rows(snapshot), "issue_bytes": issue_bytes, "readiness": readiness, "safety": safety}


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        if tuple(row) != columns:
            raise ValueError("output schema mismatch")
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _manifest(state: dict[str, Any], output_hashes: dict[str, str]) -> dict[str, Any]:
    state_counts = {name: sum(row["value_state"] == name for row in state["observed_rows"]) for name in ("present_historical_or_fixture_value", "missing_empty", "missing_null_like")}
    manifest: dict[str, Any] = {
        "project": PROJECT, "stage": STAGE, "step": STEP, "base_commit": EXPECTED_BASE_COMMIT, "base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": "ADMIT_011", "admission_rule_name": "raw_overwrite_forbidden", "evaluation_phase": "pre_download", "candidate_field": "raw_target_relative_path",
        "required_context": ["existing_raw_target_relative_paths", "raw_target_relative_path_contract"], "required_status": "target_does_not_overwrite_existing_raw", "historical_blocking_reason": "raw_target_overwrite_forbidden",
        "primary_unresolved_blocker": PRIMARY_BLOCKER, "primary_blocker_status": "open", "source_count": EXPECTED_SOURCE_COUNT, "source_path_list_sha256": EXPECTED_PATH_LIST_SHA256, "source_path_sha256_pairs_sha256": EXPECTED_PATH_SHA256_PAIRS_SHA256,
        "occurrence_row_count": len(state["occurrence_rows"]), "observed_value_row_count": len(state["observed_rows"]), "observed_value_state_counts": state_counts,
        "issue_inventory_byte_identical_to_exact10": hashlib.sha256(state["issue_bytes"]).hexdigest() == output_hashes[ISSUE_FILENAME], "admit_012_013_boundary": "post_download_download_result_contract_not_evaluated_here",
        "readiness": state["readiness"], "safety": state["safety"], "recommended_next_step": RECOMMENDED_NEXT_STEP, "output_sha256": output_hashes, "all_checks_passed": True,
    }
    manifest.update(state["readiness"])
    return manifest


def materialize_audit(output_root: Path | None = None) -> dict[str, Any]:
    requested_root = output_root if output_root is not None else REPO_ROOT / DEFAULT_OUTPUT_ROOT
    output_root_was_relative = output_root is None or not requested_root.is_absolute()
    root, create_root = _resolved_output_preflight(requested_root)
    snapshot = build_frozen_source_snapshot()
    state = build_audit_state(snapshot)
    payloads = {
        PRECONDITION_FILENAME: _csv_bytes(CSV_COLUMNS[PRECONDITION_FILENAME], state["precondition_rows"]),
        OCCURRENCE_FILENAME: _csv_bytes(CSV_COLUMNS[OCCURRENCE_FILENAME], state["occurrence_rows"]),
        OBSERVED_FILENAME: _csv_bytes(CSV_COLUMNS[OBSERVED_FILENAME], state["observed_rows"]),
        SOURCE_BOUNDARY_FILENAME: _csv_bytes(CSV_COLUMNS[SOURCE_BOUNDARY_FILENAME], state["source_rows"]),
        ISSUE_FILENAME: state["issue_bytes"],
    }
    output_hashes = {name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()}
    payloads[MANIFEST_FILENAME] = (json.dumps(_manifest(state, output_hashes), indent=2, sort_keys=True) + "\n").encode("utf-8")
    if create_root:
        root.mkdir(exist_ok=False)
    _validate_prewrite_output_root(
        root, REPO_ROOT, output_root_was_relative=output_root_was_relative, newly_created=create_root
    )
    for name in OUTPUT_FILES:
        _atomic_write(root / name, payloads[name])
    checked_root, checked_create = _resolved_output_preflight(root)
    if checked_root != root or checked_create or {item.name for item in root.iterdir()} != set(OUTPUT_FILES):
        raise ValueError("postwrite output validation failed")
    return {"output_root": root, "manifest": _manifest(state, output_hashes), "output_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()}}


def run_covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1(output_root: Path | None = None) -> dict[str, Any]:
    return materialize_audit(output_root)


if __name__ == "__main__":
    materialize_audit()
