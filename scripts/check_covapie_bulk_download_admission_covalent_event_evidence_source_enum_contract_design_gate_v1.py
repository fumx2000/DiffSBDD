#!/usr/bin/env python3
"""Independently verify the V1 covalent evidence enum design outputs."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate as gate,
)


FROZEN_OUTPUT_SHA256 = {
    "covapie_covalent_event_evidence_source_enum_source_boundary_audit.csv": "0b3098ceccb954fb0fb3f3d562011ff19a3fbb3f20dd3078a8b76200dff96da2",
    "covapie_covalent_event_evidence_source_enum_registry.csv": "7a4c3e2b7be8a097be521d98cd3a9d8003c766cc95a1d41a4b68198f6e6729a7",
    "covapie_covalent_event_evidence_source_enum_validation_truth_matrix.csv": "d332ca526fd0ec05be5ab2edee87daa6d93adcd51515bacec1f1caee814f7507",
    "covapie_admit_006_admit_007_evidence_responsibility_matrix.csv": "41f7b53ccee575d098379ff6722639a53583c6b4097be7708483ed9f651ae284",
    "covapie_covalent_event_evidence_source_enum_issue_readiness_inventory.csv": "d3333fd74af79b065eb136d830e730c3a636e0d632bcb735b3e841a29d548c79",
    "covapie_covalent_event_evidence_source_enum_contract_manifest.json": "91b98e2a10a20a8f8b07708ec77af947c29e94c33ce73bcf7528f1d8a8abbf20",
}

INDEPENDENT_CANONICAL_ENUM_MEMBERS = (
    "explicit_structure_bond_record",
    "explicit_curated_covalent_annotation",
    "distance_only_inference",
)
INDEPENDENT_ALLOWED_CONTEXT = INDEPENDENT_CANONICAL_ENUM_MEMBERS[:2]
INDEPENDENT_SCALAR_SYNTAX = r"[a-z][a-z0-9_]{0,63}"
INDEPENDENT_SCALAR_VALIDATION_PRECEDENCE = (
    "exact_type", "nonempty", "ascii", "syntax", "membership",
)
INDEPENDENT_TRUTH_MATRIX_COLUMNS = (
    "case_id", "case_group", "scalar_input_kind", "scalar_input_display",
    "context_input_kind", "expected_scalar_classification", "expected_canonical_value",
    "expected_scalar_reason", "expected_context_valid", "expected_context_reason",
    "expected_admit_006_outcome", "expected_admit_006_reason",
    "expected_admit_007_outcome", "expected_admit_007_reason",
    "normative_not_observed", "case_passed",
)
INDEPENDENT_TRUTH_GROUP_COUNTS = (
    ("canonical", 3),
    ("scalar_type", 6),
    ("empty_syntax", 11),
    ("unknown", 5),
    ("context", 12),
)
INDEPENDENT_SCALAR_REASONS = {
    "type": "COVALENT_EVENT_EVIDENCE_SOURCE_TYPE_INVALID",
    "empty": "COVALENT_EVENT_EVIDENCE_SOURCE_EMPTY",
    "non_ascii": "COVALENT_EVENT_EVIDENCE_SOURCE_NON_ASCII",
    "syntax": "COVALENT_EVENT_EVIDENCE_SOURCE_SYNTAX_INVALID",
    "unknown": "COVALENT_EVENT_EVIDENCE_SOURCE_UNKNOWN",
}
INDEPENDENT_CONTEXT_REASONS = {
    "type": "ALLOWED_COVALENT_EVIDENCE_CLASSES_TYPE_INVALID",
    "content": "ALLOWED_COVALENT_EVIDENCE_CLASSES_CONTENT_INVALID",
}
INDEPENDENT_ADMIT_006_MAPPING = {
    "explicit_structure_bond_record": ("passed", ""),
    "explicit_curated_covalent_annotation": ("passed", ""),
    "distance_only_inference": ("blocked", "COVALENT_EVENT_EVIDENCE_NOT_EXPLICIT"),
}
INDEPENDENT_ADMIT_007_MAPPING = {
    "explicit_structure_bond_record": ("passed", ""),
    "explicit_curated_covalent_annotation": ("passed", ""),
    "distance_only_inference": ("blocked", "DISTANCE_ONLY_INFERENCE_NOT_ADMISSIBLE"),
}


class IndependentOracleResult(NamedTuple):
    scalar_classification: str
    canonical_value: str
    scalar_reason: str
    context_valid: bool
    context_reason: str
    admit_006_outcome: str
    admit_006_reason: str
    admit_007_outcome: str
    admit_007_reason: str


class IndependentTruthCase(NamedTuple):
    case_name: str
    case_group: str
    scalar_input: object
    scalar_input_kind: str
    scalar_input_display: str
    context_input_kind: str
    context_input: object


class _CheckerStringSubclass(str):
    pass


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        return tuple(reader.fieldnames), list(reader)


def _assert_raises(callable_object: object, *args: object, **kwargs: object) -> None:
    try:
        callable_object(*args, **kwargs)  # type: ignore[operator]
    except (AssertionError, OSError, RuntimeError, ValueError):
        return
    raise AssertionError("negative path did not fail closed")


def _runtime_contract() -> tuple[str, ...]:
    snapshot = gate.build_frozen_source_snapshot()
    tree = gate._ast_document(snapshot, gate.RUNTIME_SOURCE_PATH)
    functions = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    keys = gate._registry_keys(tree)
    assert keys == tuple(f"ADMIT_{index:03d}" for index in range(1, 6))
    assert "evaluate_admit_006" not in functions
    assert "evaluate_admit_007" not in functions
    assert "evaluate_all_rules" not in functions
    return keys


def _independent_oracle(scalar: object, context: object) -> IndependentOracleResult:
    if type(scalar) is not str:
        scalar_class, canonical, scalar_reason = "invalid", "", INDEPENDENT_SCALAR_REASONS["type"]
    elif not scalar:
        scalar_class, canonical, scalar_reason = "invalid", "", INDEPENDENT_SCALAR_REASONS["empty"]
    elif not scalar.isascii():
        scalar_class, canonical, scalar_reason = "invalid", "", INDEPENDENT_SCALAR_REASONS["non_ascii"]
    elif re.fullmatch(INDEPENDENT_SCALAR_SYNTAX, scalar, flags=re.ASCII) is None:
        scalar_class, canonical, scalar_reason = "invalid", "", INDEPENDENT_SCALAR_REASONS["syntax"]
    elif scalar not in INDEPENDENT_CANONICAL_ENUM_MEMBERS:
        scalar_class, canonical, scalar_reason = "unknown", "", INDEPENDENT_SCALAR_REASONS["unknown"]
    else:
        scalar_class, canonical, scalar_reason = "canonical", scalar, ""
    if type(context) is not tuple:
        context_valid, context_reason = False, INDEPENDENT_CONTEXT_REASONS["type"]
    elif any(type(member) is not str for member in context) or context != INDEPENDENT_ALLOWED_CONTEXT:
        context_valid, context_reason = False, INDEPENDENT_CONTEXT_REASONS["content"]
    else:
        context_valid, context_reason = True, ""
    if scalar_class != "canonical":
        admit006 = admit007 = ("invalid", scalar_reason)
    elif not context_valid:
        admit006 = admit007 = ("invalid", context_reason)
    else:
        admit006 = INDEPENDENT_ADMIT_006_MAPPING[canonical]
        admit007 = INDEPENDENT_ADMIT_007_MAPPING[canonical]
    return IndependentOracleResult(
        scalar_classification=scalar_class,
        canonical_value=canonical,
        scalar_reason=scalar_reason,
        context_valid=context_valid,
        context_reason=context_reason,
        admit_006_outcome=admit006[0],
        admit_006_reason=admit006[1],
        admit_007_outcome=admit007[0],
        admit_007_reason=admit007[1],
    )


def _independent_display(value: object) -> str:
    if type(value) is str:
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, _CheckerStringSubclass):
        return f"str_subclass:{json.dumps(str(value))}"
    return f"{type(value).__name__}:{repr(value)}"


def _independent_truth_cases() -> tuple[IndependentTruthCase, ...]:
    exact = INDEPENDENT_ALLOWED_CONTEXT
    scalar_definitions: tuple[tuple[str, str, object, str | None], ...] = (
        ("canonical_structure_bond", "canonical", INDEPENDENT_CANONICAL_ENUM_MEMBERS[0], None),
        ("canonical_curated_annotation", "canonical", INDEPENDENT_CANONICAL_ENUM_MEMBERS[1], None),
        ("canonical_distance_only", "canonical", INDEPENDENT_CANONICAL_ENUM_MEMBERS[2], None),
        ("type_none", "scalar_type", None, None),
        ("type_int", "scalar_type", 7, None),
        ("type_bool", "scalar_type", True, None),
        ("type_str_subclass", "scalar_type", _CheckerStringSubclass(INDEPENDENT_CANONICAL_ENUM_MEMBERS[0]), "_StringSubclass"),
        ("type_list", "scalar_type", [INDEPENDENT_CANONICAL_ENUM_MEMBERS[0]], None),
        ("type_mapping", "scalar_type", {"value": INDEPENDENT_CANONICAL_ENUM_MEMBERS[0]}, None),
        ("empty", "empty_syntax", "", None),
        ("whitespace_only", "empty_syntax", " ", None),
        ("leading_whitespace", "empty_syntax", " explicit_structure_bond_record", None),
        ("trailing_whitespace", "empty_syntax", "explicit_structure_bond_record ", None),
        ("uppercase", "empty_syntax", "Explicit_structure_bond_record", None),
        ("hyphen", "empty_syntax", "explicit-structure-bond-record", None),
        ("dot", "empty_syntax", "explicit.structure", None),
        ("slash", "empty_syntax", "explicit/structure", None),
        ("non_ascii", "empty_syntax", "explicit_évidence", None),
        ("over_length", "empty_syntax", "a" * 65, None),
        ("leading_digit", "empty_syntax", "1explicit", None),
        ("unknown_valid", "unknown", "unregistered_value", None),
        ("unknown_explicit_looking", "unknown", "explicit_database_bond", None),
        ("unknown_manual_review", "unknown", "manual_review", None),
        ("unknown_other", "unknown", "other", None),
        ("unknown_unknown", "unknown", "unknown", None),
    )
    cases = [
        IndependentTruthCase(
            name, group, scalar, kind or type(scalar).__name__,
            _independent_display(scalar), "exact_tuple", exact,
        )
        for name, group, scalar, kind in scalar_definitions
    ]
    context_definitions: tuple[tuple[str, object], ...] = (
        ("context_exact_tuple", exact),
        ("context_none", None),
        ("context_list", list(exact)),
        ("context_set", set(exact)),
        ("context_frozenset", frozenset(exact)),
        ("context_wrong_order", tuple(reversed(exact))),
        ("context_missing_member", exact[:1]),
        ("context_duplicate", (exact[0], exact[0])),
        ("context_distance_only", (*exact, INDEPENDENT_CANONICAL_ENUM_MEMBERS[2])),
        ("context_unknown", (*exact, "unknown")),
        ("context_str_subclass", (_CheckerStringSubclass(exact[0]), exact[1])),
        ("context_extra_member", (*exact, "explicit_database_bond")),
    )
    cases.extend(
        IndependentTruthCase(
            name, "context", INDEPENDENT_CANONICAL_ENUM_MEMBERS[0], "str",
            json.dumps(INDEPENDENT_CANONICAL_ENUM_MEMBERS[0]),
            name.removeprefix("context_"), context,
        )
        for name, context in context_definitions
    )
    assert len(cases) == 37
    assert tuple(
        (group, sum(case.case_group == group for case in cases))
        for group, _ in INDEPENDENT_TRUTH_GROUP_COUNTS
    ) == INDEPENDENT_TRUTH_GROUP_COUNTS
    return tuple(cases)


def _independent_truth_rows() -> tuple[dict[str, str], ...]:
    rows = []
    for index, case in enumerate(_independent_truth_cases(), 1):
        result = _independent_oracle(case.scalar_input, case.context_input)
        rows.append({
            "case_id": f"CASE_{index:03d}_{case.case_name}",
            "case_group": case.case_group,
            "scalar_input_kind": case.scalar_input_kind,
            "scalar_input_display": case.scalar_input_display,
            "context_input_kind": case.context_input_kind,
            "expected_scalar_classification": result.scalar_classification,
            "expected_canonical_value": result.canonical_value,
            "expected_scalar_reason": result.scalar_reason,
            "expected_context_valid": "true" if result.context_valid else "false",
            "expected_context_reason": result.context_reason,
            "expected_admit_006_outcome": result.admit_006_outcome,
            "expected_admit_006_reason": result.admit_006_reason,
            "expected_admit_007_outcome": result.admit_007_outcome,
            "expected_admit_007_reason": result.admit_007_reason,
            "normative_not_observed": "true",
            "case_passed": "true",
        })
    return tuple(rows)


def _validate_independent_ast() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    protected_names = {
        "_independent_oracle",
        "_independent_display",
        "_independent_truth_cases",
        "_independent_truth_rows",
    }
    protected = {
        node.name: node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in protected_names
    }
    assert set(protected) == protected_names
    forbidden_bare_names = {
        "CANONICAL_ENUM_MEMBERS",
        "ALLOWED_COVALENT_EVIDENCE_CLASSES",
        "SCALAR_REASONS",
        "CONTEXT_REASONS",
        "validate_covalent_event_evidence_source_design",
        "validate_allowed_covalent_evidence_classes_design",
        "classify_admit_006_admit_007_evidence_design",
        "_truth_definitions",
        "_truth_matrix_rows",
    }
    for node in protected.values():
        referenced_names = {
            child.id for child in ast.walk(node) if isinstance(child, ast.Name)
        }
        assert "gate" not in referenced_names
        assert forbidden_bare_names.isdisjoint(referenced_names)


def _validate_oracles(disk_truth: list[dict[str, str]] | None = None) -> None:
    cases = _independent_truth_cases()
    expected_results = tuple(
        _independent_oracle(case.scalar_input, case.context_input) for case in cases
    )
    expected_rows = _independent_truth_rows()
    if disk_truth is not None:
        assert len(disk_truth) == len(cases) == 37
    assert gate.CANONICAL_ENUM_MEMBERS == INDEPENDENT_CANONICAL_ENUM_MEMBERS
    assert gate.ALLOWED_COVALENT_EVIDENCE_CLASSES == INDEPENDENT_ALLOWED_CONTEXT
    assert gate.CANONICAL_SYNTAX == INDEPENDENT_SCALAR_SYNTAX
    assert gate.TRUTH_MATRIX_COLUMNS == INDEPENDENT_TRUTH_MATRIX_COLUMNS
    assert gate.SCALAR_REASONS == tuple(INDEPENDENT_SCALAR_REASONS.values())
    assert gate.CONTEXT_REASONS == tuple(INDEPENDENT_CONTEXT_REASONS.values())
    for index, (case, expected, expected_row) in enumerate(
        zip(cases, expected_results, expected_rows, strict=True)
    ):
        scalar = gate.validate_covalent_event_evidence_source_design(case.scalar_input)
        context = gate.validate_allowed_covalent_evidence_classes_design(case.context_input)
        classification = gate.classify_admit_006_admit_007_evidence_design(
            case.scalar_input, case.context_input
        )
        assert (scalar.classification, scalar.canonical_value, scalar.reason) == (
            expected.scalar_classification, expected.canonical_value, expected.scalar_reason,
        )
        assert (context.valid, context.reason) == (expected.context_valid, expected.context_reason)
        assert (
            classification.scalar.classification,
            classification.scalar.canonical_value,
            classification.scalar.reason,
        ) == (
            expected.scalar_classification,
            expected.canonical_value,
            expected.scalar_reason,
        )
        assert (classification.context.valid, classification.context.reason) == (
            expected.context_valid,
            expected.context_reason,
        )
        assert (classification.admit_006.outcome, classification.admit_006.reason) == (
            expected.admit_006_outcome, expected.admit_006_reason,
        )
        assert (classification.admit_007.outcome, classification.admit_007.reason) == (
            expected.admit_007_outcome, expected.admit_007_reason,
        )
        if disk_truth is not None:
            assert disk_truth[index] == expected_row


def _validate_disk(root: Path, *, enforce_frozen_hashes: bool = True) -> dict[str, object]:
    expected = set(gate.OUTPUT_FILES)
    assert root.is_dir() and not root.is_symlink()
    assert {entry.name for entry in root.iterdir()} == expected
    assert all((root / name).is_file() and not (root / name).is_symlink() for name in expected)
    hashes = {name: _sha(root / name) for name in gate.OUTPUT_FILES}
    if enforce_frozen_hashes:
        assert hashes == FROZEN_OUTPUT_SHA256

    boundary_header, boundary = _csv(root / gate.SOURCE_BOUNDARY_FILENAME)
    enum_header, enum_rows = _csv(root / gate.ENUM_REGISTRY_FILENAME)
    truth_header, truth = _csv(root / gate.TRUTH_MATRIX_FILENAME)
    responsibility_header, responsibility = _csv(root / gate.RESPONSIBILITY_FILENAME)
    issue_header, issues = _csv(root / gate.ISSUE_FILENAME)
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert type(manifest) is dict

    assert boundary_header == gate.SOURCE_BOUNDARY_COLUMNS and len(boundary) == 12
    assert tuple(row["source_relative_path"] for row in boundary) == tuple(path.as_posix() for path in gate.SOURCE_PATHS)
    assert tuple(row["expected_sha256"] for row in boundary) == tuple(gate.SOURCE_SHA256.values())
    assert all(row["source_boundary_passed"] == "true" for row in boundary)

    assert enum_header == gate.ENUM_REGISTRY_COLUMNS and len(enum_rows) == 3
    assert tuple(row["canonical_value"] for row in enum_rows) == INDEPENDENT_CANONICAL_ENUM_MEMBERS
    assert [row["enum_order"] for row in enum_rows] == ["1", "2", "3"]
    assert all(row["normative_contract_member"] == "true" for row in enum_rows)
    assert all(row["observed_in_committed_metadata"] == "false" for row in enum_rows)
    assert [row["explicit_covalent_evidence"] for row in enum_rows] == ["true", "true", "false"]
    assert [row["distance_only"] for row in enum_rows] == ["false", "false", "true"]
    assert [row["allowed_by_admit_006"] for row in enum_rows] == ["true", "true", "false"]
    assert [row["allowed_by_admit_007"] for row in enum_rows] == ["true", "true", "false"]
    assert all(row["alias_allowed"] == "false" for row in enum_rows)
    forbidden_members = {"unknown", "unspecified", "other", "none", "null", "manual_review", "manual_review_confirmed", "inferred", "predicted"}
    assert not forbidden_members.intersection(row["canonical_value"] for row in enum_rows)

    assert truth_header == INDEPENDENT_TRUTH_MATRIX_COLUMNS
    _validate_independent_ast()
    _validate_oracles(truth)

    assert responsibility_header == gate.RESPONSIBILITY_COLUMNS and len(responsibility) == 3
    assert [row["contract_subject"] for row in responsibility] == [
        "shared_enum_validator", "positive_explicit_evidence_permission", "negative_distance_only_prohibition"
    ]
    assert [row["rule_id"] for row in responsibility] == ["SHARED", "ADMIT_006", "ADMIT_007"]
    assert responsibility[1]["blocked_reason"] == "COVALENT_EVENT_EVIDENCE_NOT_EXPLICIT"
    assert responsibility[2]["blocked_reason"] == "DISTANCE_ONLY_INFERENCE_NOT_ADMISSIBLE"
    assert all(row["responsibility_passed"] == "true" for row in responsibility)

    assert issue_header == gate.ISSUE_COLUMNS and len(issues) == 11
    predecessor = gate._csv_document(gate.build_frozen_source_snapshot(), gate.AUDIT_ISSUE_PATH).rows
    changed = []
    for old, new in zip(predecessor, issues, strict=True):
        differences = {key for key in old if old[key] != new[key]}
        if differences:
            changed.append((new["issue_id"], differences))
    assert changed == [("COVALENT_EVIDENCE_ENUM_UNRESOLVED", {"status", "integration_transition"})]
    enum_issue = next(row for row in issues if row["issue_id"] == "COVALENT_EVIDENCE_ENUM_UNRESOLVED")
    assert enum_issue == {
        **next(row for row in predecessor if row["issue_id"] == "COVALENT_EVIDENCE_ENUM_UNRESOLVED"),
        "status": "resolved",
        "integration_transition": "covalent_event_evidence_source_enum_contract_frozen_v1",
    }
    assert sum(row["status"] == "open" for row in issues) == 10
    coverage = next(row for row in issues if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert "ADMIT_006" in coverage["affected_rules"].split("|")

    assert manifest["expected_base_commit"] == gate.EXPECTED_BASE_COMMIT
    assert manifest["source_input_paths"] == [path.as_posix() for path in gate.SOURCE_PATHS]
    assert manifest["source_input_sha256"] == {path.as_posix(): gate.SOURCE_SHA256[path] for path in gate.SOURCE_PATHS}
    assert manifest["output_files"] == list(gate.OUTPUT_FILES) and manifest["output_file_count"] == 6
    assert manifest["output_sha256"] == {name: hashes[name] for name in gate.CSV_OUTPUTS}
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert manifest["normative_enum_member_count"] == 3
    assert manifest["observed_evidence_value_count"] == 0
    assert manifest["normative_enum_values_are_not_observed_values"] is True
    assert manifest["normative_enum_members"] == list(INDEPENDENT_CANONICAL_ENUM_MEMBERS)
    assert manifest["allowed_covalent_evidence_classes"] == list(INDEPENDENT_ALLOWED_CONTEXT)
    assert manifest["scalar_validation_precedence"] == list(INDEPENDENT_SCALAR_VALIDATION_PRECEDENCE)
    assert manifest["manual_review_member_included"] is False
    assert manifest["catch_all_member_included"] is False
    assert manifest["alias_support"] is False and manifest["scalar_normalization_applied"] is False
    assert manifest["enum_issue_status"] == "resolved" and manifest["active_open_issue_count"] == 10
    assert manifest["current_registered_rule_count"] == 5
    assert manifest["admit_006_registered"] is False and manifest["admit_007_registered"] is False
    assert all(manifest[key] is True for key in gate.TRUE_READINESS)
    assert all(manifest[key] is False for key in gate.FALSE_READINESS)
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    assert manifest["all_checks_passed"] is True
    serialized = json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in serialized.lower() and "/home/" not in serialized
    assert _runtime_contract() == tuple(f"ADMIT_{index:03d}" for index in range(1, 6))
    return manifest


def _negative_source_checks(snapshot: gate.FrozenSourceSnapshot) -> None:
    records = list(snapshot.records)
    first = records[0]
    records[0] = gate.FrozenSourceRecord(first.relative_path, first.expected_sha256, first.base_tree_sha256, "0" * 64, first.content_bytes)
    assert not gate.validate_frozen_source_snapshot(gate.FrozenSourceSnapshot(tuple(records)))
    original_git = gate._git
    try:
        def non_descendant(arguments: object, repo_root: Path, *, text: bool = True) -> subprocess.CompletedProcess[object]:
            if list(arguments)[:2] == ["merge-base", "--is-ancestor"]:
                return subprocess.CompletedProcess([], 1, "" if text else b"", "" if text else b"")
            return original_git(arguments, repo_root, text=text)  # type: ignore[arg-type]
        gate._git = non_descendant  # type: ignore[assignment]
        _assert_raises(gate._validate_expected_base_lineage, REPO_ROOT)
    finally:
        gate._git = original_git  # type: ignore[assignment]


def _negative_output_checks(root: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="covapie_enum_checker_") as temporary:
        temp = Path(temporary)
        for label, mutation in (("missing", "missing"), ("extra", "extra"), ("tamper", "tamper"), ("hash", "hash"), ("overclaim", "overclaim")):
            copied = temp / label
            shutil.copytree(root, copied)
            if mutation == "missing":
                (copied / gate.ENUM_REGISTRY_FILENAME).unlink()
            elif mutation == "extra":
                (copied / "unexpected.txt").write_text("unexpected", encoding="utf-8")
            elif mutation == "tamper":
                with (copied / gate.TRUTH_MATRIX_FILENAME).open("ab") as handle:
                    handle.write(b"tamper")
            elif mutation == "hash":
                with (copied / gate.ENUM_REGISTRY_FILENAME).open("ab") as handle:
                    handle.write(b"hash-mismatch")
                _assert_raises(_validate_disk, copied, enforce_frozen_hashes=True)
                continue
            else:
                manifest_path = copied / gate.MANIFEST_FILENAME
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["ready_for_bulk_download_now"] = True
                manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            _assert_raises(_validate_disk, copied, enforce_frozen_hashes=False)
        unsafe = temp / "unsafe"
        unsafe.mkdir()
        victim = temp / "victim.txt"
        victim.write_text("unchanged", encoding="utf-8")
        (unsafe / gate.SOURCE_BOUNDARY_FILENAME).symlink_to(victim)
        _assert_raises(gate.run_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1, unsafe)
        assert victim.read_text(encoding="utf-8") == "unchanged"


def main() -> int:
    root = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    first = gate.run_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1(root)
    first_bytes = {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    second = gate.run_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1(root)
    second_bytes = {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    assert first["manifest"] == second["manifest"] and first_bytes == second_bytes
    manifest = _validate_disk(root)
    snapshot = gate.build_frozen_source_snapshot()
    _negative_source_checks(snapshot)
    _negative_output_checks(root)
    assert manifest["normative_enum_member_count"] == 3
    assert manifest["observed_evidence_value_count"] == 0
    assert manifest["active_open_issue_count"] == 10
    assert manifest["ready_for_admit_006_standalone_evaluator_interface_implementation"] is True
    assert manifest["real_provider_enum_mapping_validated"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    print(f"stage={gate.STAGE}")
    print("all_checks_passed=true")
    print("source_boundary_exact12=true")
    print("normative_enum_member_count=3")
    print("observed_evidence_value_count=0")
    print("allowed_explicit_member_count=2")
    print("distance_only_member_count=1")
    print("manual_review_member_included=false")
    print("alias_support=false")
    print("enum_issue_status=resolved")
    print("active_open_issue_count=10")
    print("current_registered_rule_count=5")
    print("ready_for_admit_006_standalone_evaluator_interface_implementation=true")
    print("real_provider_enum_mapping_validated=false")
    print("frozen_output_sha=6/6")
    print("ready_for_bulk_download_now=false")
    print("ready_for_training=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
