from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate as gate,
)


class StringSubclass(str):
    pass


class TupleSubclass(tuple):
    pass


def _load_checker() -> object:
    path = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1.py"
    spec = importlib.util.spec_from_file_location("admit008_enum_checker", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _hashes(root: Path) -> dict[str, str]:
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in root.iterdir()}


def _refresh_manifest_hash(root: Path, name: str) -> None:
    path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["output_sha256"][name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _rewrite_csv(root: Path, name: str, mutate: object) -> None:
    path = root / name
    reader = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline=""))
    assert reader.fieldnames is not None
    rows = [dict(row) for row in reader]
    result = mutate(rows)  # type: ignore[operator]
    rows = rows if result is None else result
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=reader.fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(stream.getvalue(), encoding="utf-8")
    _refresh_manifest_hash(root, name)


def _rewrite_manifest(root: Path, mutate: object) -> None:
    path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    mutate(manifest)  # type: ignore[operator]
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_production_and_checker_imports_are_silent_and_side_effect_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    importlib.reload(gate)
    _load_checker()
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""
    assert not (tmp_path / gate.DEFAULT_OUTPUT_ROOT).exists()


def test_exact_six_outputs_are_byte_deterministic(tmp_path: Path) -> None:
    first = gate.run_covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1(tmp_path)
    first_hashes = _hashes(tmp_path)
    second = gate.run_covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1(tmp_path)
    assert first["manifest"] == second["manifest"]
    assert first_hashes == _hashes(tmp_path)
    assert tuple(sorted(first_hashes)) == tuple(sorted(gate.OUTPUT_FILES))


def test_exact15_source_boundary_is_ordered_tracked_and_sha_frozen() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert len(snapshot.records) == 15
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert tuple(gate.SOURCE_SHA256) == gate.SOURCE_PATHS


def test_all_structural_checks_precede_first_explicit_content_read(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    original_structure = gate._structural_source_check
    original_git = gate._git
    original_read = Path.read_bytes

    def structure(path: Path, root: Path) -> bool:
        events.append(f"structure:{path}")
        return original_structure(path, root)

    def git(arguments: object, root: Path, *, text: bool = True) -> subprocess.CompletedProcess[object]:
        if list(arguments)[:1] == ["show"] and len(list(arguments)) == 2:
            events.append("content:git_show")
        return original_git(arguments, root, text=text)  # type: ignore[arg-type]

    def read(path: Path) -> bytes:
        if path in tuple(REPO_ROOT / item for item in gate.SOURCE_PATHS):
            events.append("content:filesystem")
        return original_read(path)

    monkeypatch.setattr(gate, "_structural_source_check", structure)
    monkeypatch.setattr(gate, "_git", git)
    monkeypatch.setattr(Path, "read_bytes", read)
    gate.build_frozen_source_snapshot()
    first_content = next(index for index, event in enumerate(events) if event.startswith("content:"))
    assert events[:first_content] == [f"structure:{path}" for path in gate.SOURCE_PATHS]


@pytest.mark.parametrize("bad", [Path("data/raw/forbidden.cif"), Path("checkpoints/forbidden.ckpt"), Path("../escape")])
def test_raw_checkpoint_and_non_descendant_sources_are_rejected(bad: Path) -> None:
    assert gate._safe_relative_path(bad) is False


def test_source_symlink_fails_before_byte_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = gate.SOURCE_PATHS[0]
    full = tmp_path / target
    full.parent.mkdir(parents=True)
    victim = tmp_path / "victim"
    victim.write_text("victim", encoding="utf-8")
    full.symlink_to(victim)
    monkeypatch.setattr(gate, "_validate_expected_base_lineage", lambda *args, **kwargs: None)
    monkeypatch.setattr(gate, "_structural_source_check", lambda path, root: path != target)
    called = False

    def forbidden(*args: object, **kwargs: object) -> bytes:
        nonlocal called
        called = True
        raise AssertionError("content read forbidden")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    with pytest.raises(ValueError, match="structural"):
        gate.build_frozen_source_snapshot(tmp_path)
    assert called is False


def test_exact4_registry_and_exact2_context_are_frozen() -> None:
    rows = gate._enum_registry_rows()
    assert tuple(row["canonical_value"] for row in rows) == gate.CANONICAL_ENUM_MEMBERS
    assert gate.CANONICAL_ENUM_MEMBERS == (
        "approved_restoration_template", "explicit_manual_review_approved",
        "manual_review_required", "quarantine_required",
    )
    assert type(gate.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS) is tuple
    assert gate.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS == gate.CANONICAL_ENUM_MEMBERS[:2]
    assert [row["passed_by_admit_008"] for row in rows] == ["true", "true", "false", "false"]
    assert [row["included_in_allowed_context"] for row in rows] == ["true", "true", "false", "false"]
    assert all(row["provider_mapping_required"] == "true" and row["alias_allowed"] == "false" for row in rows)


@pytest.mark.parametrize(
    ("value", "classification", "reason"),
    [
        (None, "invalid", gate.SCALAR_REASONS[0]),
        (StringSubclass(""), "invalid", gate.SCALAR_REASONS[0]),
        ("", "invalid", gate.SCALAR_REASONS[1]),
        ("réview", "invalid", gate.SCALAR_REASONS[2]),
        ("Manual_review_required", "invalid", gate.SCALAR_REASONS[3]),
        ("unknown", "unknown", gate.SCALAR_REASONS[4]),
        ("approved_restoration_template", "canonical", ""),
    ],
)
def test_scalar_validation_exact_type_and_precedence(value: object, classification: str, reason: str) -> None:
    result = gate.validate_topology_restoration_disposition_design(value)
    assert result.classification == classification and result.reason == reason
    if classification != "canonical":
        assert result.canonical_value == "" and result.validated_candidate_fields == ()


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        (None, gate.CONTEXT_REASONS[0]), (list(gate.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS), gate.CONTEXT_REASONS[0]),
        (TupleSubclass(gate.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS), gate.CONTEXT_REASONS[0]),
        (tuple(reversed(gate.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS)), gate.CONTEXT_REASONS[1]),
        ((StringSubclass(gate.CANONICAL_ENUM_MEMBERS[0]), gate.CANONICAL_ENUM_MEMBERS[1]), gate.CONTEXT_REASONS[1]),
    ],
)
def test_context_validation_exact_tuple_and_member_types(value: object, reason: str) -> None:
    result = gate.validate_allowed_topology_restoration_dispositions_design(value)
    assert result.valid is False and result.reason == reason


def test_oracle_outcomes_reasons_and_canonical_state() -> None:
    exact = gate.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS
    passed = gate.classify_admit_008_topology_restoration_disposition_design(gate.CANONICAL_ENUM_MEMBERS[0], exact)
    manual = gate.classify_admit_008_topology_restoration_disposition_design(gate.CANONICAL_ENUM_MEMBERS[2], exact)
    quarantine = gate.classify_admit_008_topology_restoration_disposition_design(gate.CANONICAL_ENUM_MEMBERS[3], exact)
    context_invalid = gate.classify_admit_008_topology_restoration_disposition_design(gate.CANONICAL_ENUM_MEMBERS[0], tuple(reversed(exact)))
    scalar_invalid = gate.classify_admit_008_topology_restoration_disposition_design(None, None)
    assert (passed.admit_008.outcome, passed.admit_008.passed, passed.admit_008.blocks_candidate, passed.admit_008.reason) == ("passed", True, False, "")
    assert manual.admit_008.reason == "TOPOLOGY_RESTORATION_MANUAL_REVIEW_REQUIRED"
    assert quarantine.admit_008.reason == "TOPOLOGY_RESTORATION_QUARANTINE_REQUIRED"
    assert manual.admit_008.reason != quarantine.admit_008.reason
    assert manual.admit_008.canonical_value == gate.CANONICAL_ENUM_MEMBERS[2]
    assert manual.admit_008.validated_candidate_fields == ((gate.CANDIDATE_FIELDS[0], gate.CANONICAL_ENUM_MEMBERS[2]),)
    assert context_invalid.admit_008.outcome == "invalid"
    assert context_invalid.admit_008.canonical_value == gate.CANONICAL_ENUM_MEMBERS[0]
    assert context_invalid.admit_008.validated_candidate_fields
    assert scalar_invalid.admit_008.reason == gate.SCALAR_REASONS[0]
    assert scalar_invalid.admit_008.canonical_value == "" and scalar_invalid.admit_008.validated_candidate_fields == ()


def test_exact38_truth_has_natural_groups_and_fail_closed_state() -> None:
    rows = gate._truth_matrix_rows()
    assert len(rows) == 38 and all(row["case_passed"] == "true" for row in rows)
    counts = {group: sum(row["case_group"] == group for row in rows) for group in ("canonical", "scalar_type", "empty_syntax", "unknown", "context")}
    assert counts == {"canonical": 4, "scalar_type": 6, "empty_syntax": 11, "unknown": 5, "context": 12}
    assert all(row["scalar_failure_precedence"] == "true" for row in rows)
    blocked = [row for row in rows if row["expected_outcome"] == "blocked"]
    assert {row["expected_reason"] for row in blocked} == set(gate.BLOCKED_REASONS.values())


def test_exact12_mapping_freezes_quarantine_review_and_no_bypass_precedence() -> None:
    rows = gate._category_mapping_rows()
    assert len(rows) == 12 and [row["mapping_order"] for row in rows] == [str(index) for index in range(1, 13)]
    assert all(row["real_provider_mapping_executed"] == "false" and row["mapping_contract_passed"] == "true" for row in rows)
    by_id = {row["mapping_case_id"]: row for row in rows}
    assert by_id["quarantine_over_template"]["expected_canonical_disposition"] == "quarantine_required"
    assert by_id["manual_visual_review_required_true"]["expected_canonical_disposition"] == "manual_review_required"
    assert by_id["deferred_or_new_rule"]["expected_outcome"] == "blocked"
    assert by_id["unknown_residue_warhead_pair"]["expected_outcome"] == "blocked"
    assert by_id["no_v1_bypass"]["expected_outcome"] == "blocked"


def test_exact11_issue_transition_changes_only_authorized_row_and_fields() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    predecessor = gate._csv_document(snapshot, gate.AUDIT_ISSUE_PATH).rows
    successor = gate._issue_rows(predecessor)
    assert len(successor) == 11
    changes = []
    for before, after in zip(predecessor, successor, strict=True):
        changed = {key for key in before if before[key] != after[key]}
        if changed:
            changes.append((before["issue_id"], changed))
    assert changes == [(gate.PRIMARY_ISSUE, {"status", "integration_transition"})]
    enum_issue = next(row for row in successor if row["issue_id"] == gate.PRIMARY_ISSUE)
    coverage = next(row for row in successor if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert enum_issue["status"] == "resolved" and enum_issue["issue_count"] == "1"
    assert coverage["status"] == "open" and coverage["affected_rules"].startswith("ADMIT_008|")


def test_manifest_readiness_is_truthful_and_mirrored(tmp_path: Path) -> None:
    manifest = gate.run_covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1(tmp_path)["manifest"]
    assert manifest["real_provider_value_count"] == 0 and manifest["real_provider_mapping_executed"] is False
    assert manifest["ready_for_admit_008_standalone_evaluator_interface_implementation"] is True
    assert manifest["admit_008_standalone_evaluator_implemented"] is False
    assert manifest["admit_008_unified_adapter_contract_frozen"] is False
    assert manifest["admit_008_registered_in_engine"] is False and manifest["exact7_runtime_modified"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False and manifest["ready_to_train_now"] is False
    assert all(manifest[key] is manifest["readiness"][key] for key in (*gate.TRUE_READINESS, *gate.FALSE_READINESS))


def test_production_defines_design_oracle_but_no_evaluator_result_adapter_or_runtime() -> None:
    tree = ast.parse(Path(gate.__file__).read_text(encoding="utf-8"))
    functions = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    assignments = {target.id for node in tree.body if isinstance(node, ast.Assign) for target in node.targets if isinstance(target, ast.Name)}
    assert "classify_admit_008_topology_restoration_disposition_design" in functions
    assert "evaluate_admit_008" not in functions and "Admit008EvaluationResult" not in classes
    assert "EVALUATOR_REGISTRY" not in assignments and "evaluate_all_rules" not in functions


@pytest.mark.parametrize("kind", ["extra", "missing", "symlink"])
def test_output_missing_extra_and_symlink_fail_closed(tmp_path: Path, kind: str) -> None:
    root = tmp_path / "output"
    gate.run_covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1(root)
    checker = _load_checker()
    if kind == "extra":
        (root / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    elif kind == "missing":
        (root / gate.ENUM_REGISTRY_FILENAME).unlink()
    else:
        victim = tmp_path / "victim"
        victim.write_text("unchanged", encoding="utf-8")
        (root / gate.ENUM_REGISTRY_FILENAME).unlink()
        (root / gate.ENUM_REGISTRY_FILENAME).symlink_to(victim)
    with pytest.raises((AssertionError, ValueError, FileNotFoundError)):
        checker._validate_disk(root, enforce_frozen_hashes=False)


def test_materializer_preserves_unexpected_output_and_symlink_victim(tmp_path: Path) -> None:
    extra = tmp_path / "extra"
    extra.mkdir()
    unexpected = extra / "unexpected.txt"
    unexpected.write_text("keep", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected"):
        gate.run_covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1(extra)
    assert unexpected.read_text(encoding="utf-8") == "keep"
    unsafe = tmp_path / "unsafe"
    unsafe.mkdir()
    victim = tmp_path / "victim"
    victim.write_text("unchanged", encoding="utf-8")
    (unsafe / gate.SOURCE_BOUNDARY_FILENAME).symlink_to(victim)
    with pytest.raises(ValueError, match="unsafe"):
        gate.run_covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1(unsafe)
    assert victim.read_text(encoding="utf-8") == "unchanged"


TAMPER_CASES = (
    "enum_order", "catchall_added", "not_applicable_added", "historical_phrase_added", "rule_id_added",
    "manual_required_passed", "quarantine_passed", "blocked_vague_reason", "allowed_blocked_member",
    "allowed_order_changed", "scalar_subclass_accepted", "trim_case_alias_allowed",
    "context_tuple_subclass_accepted", "scalar_failure_not_first", "context_invalid_state_cleared",
    "blocked_state_cleared", "quarantine_does_not_override_template", "review_required_as_approved",
    "deferred_as_approved", "unknown_pair_as_approved", "not_applicable_bypass", "issue_kept_open",
    "coverage_removes_admit008", "provider_mapping_validated", "provider_values_fabricated",
    "source_sha", "raw_source", "checkpoint_source", "semantic_rehashed", "readiness_mirror_drift",
    "unknown_manifest_key",
)


@pytest.mark.parametrize("case", TAMPER_CASES)
def test_semantic_tamper_with_manifest_rehash_fails_closed(tmp_path: Path, case: str) -> None:
    root = tmp_path / "output"
    gate.run_covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1(root)
    checker = _load_checker()

    if case in {"enum_order", "catchall_added", "not_applicable_added", "historical_phrase_added", "rule_id_added", "manual_required_passed", "quarantine_passed", "blocked_vague_reason"}:
        def mutate_enum(rows: list[dict[str, str]]) -> list[dict[str, str]]:
            if case == "enum_order":
                rows[0], rows[1] = rows[1], rows[0]
            elif case in {"catchall_added", "not_applicable_added", "historical_phrase_added", "rule_id_added"}:
                values = {
                    "catchall_added": "unapproved", "not_applicable_added": "not_applicable",
                    "historical_phrase_added": "approved_template_or_manual_review",
                    "rule_id_added": "CYS_SG_ACRYLAMIDE_LIKE_STEP8_MANUAL_REVIEWED_V1",
                }
                rows.append({**rows[-1], "enum_order": "5", "canonical_value": values[case]})
            elif case == "manual_required_passed":
                rows[2].update(passed_by_admit_008="true", blocked_by_admit_008="false", formal_reason="")
            elif case == "quarantine_passed":
                rows[3].update(passed_by_admit_008="true", blocked_by_admit_008="false", formal_reason="")
            else:
                rows[2]["formal_reason"] = rows[3]["formal_reason"] = "topology_restoration_unapproved"
            return rows
        _rewrite_csv(root, gate.ENUM_REGISTRY_FILENAME, mutate_enum)
    elif case in {"scalar_subclass_accepted", "scalar_failure_not_first", "context_tuple_subclass_accepted", "context_invalid_state_cleared", "blocked_state_cleared", "semantic_rehashed"}:
        def mutate_truth(rows: list[dict[str, str]]) -> None:
            if case == "scalar_subclass_accepted":
                row = next(row for row in rows if "type_str_subclass" in row["case_id"])
                row.update(expected_scalar_classification="canonical", expected_outcome="passed", expected_reason="")
            elif case == "scalar_failure_not_first":
                row = next(row for row in rows if "type_none" in row["case_id"])
                row["expected_reason"] = gate.CONTEXT_REASONS[0]
                row["scalar_failure_precedence"] = "false"
            elif case == "context_tuple_subclass_accepted":
                row = next(row for row in rows if "context_none" in row["case_id"])
                row["expected_context_valid"] = "true"
            elif case == "context_invalid_state_cleared":
                row = next(row for row in rows if "context_reversed" in row["case_id"])
                row["expected_canonical_value"] = row["expected_validated_candidate_fields"] = ""
            elif case == "blocked_state_cleared":
                row = next(row for row in rows if "canonical_manual_required" in row["case_id"])
                row["expected_canonical_value"] = row["expected_validated_candidate_fields"] = ""
            else:
                rows[0]["expected_reason"] = "fabricated"
        _rewrite_csv(root, gate.TRUTH_MATRIX_FILENAME, mutate_truth)
    elif case in {"quarantine_does_not_override_template", "review_required_as_approved", "deferred_as_approved", "unknown_pair_as_approved", "not_applicable_bypass"}:
        ids = {
            "quarantine_does_not_override_template": "quarantine_over_template",
            "review_required_as_approved": "manual_visual_review_required_true",
            "deferred_as_approved": "deferred_or_new_rule",
            "unknown_pair_as_approved": "unknown_residue_warhead_pair",
            "not_applicable_bypass": "no_v1_bypass",
        }
        def mutate_mapping(rows: list[dict[str, str]]) -> None:
            row = next(row for row in rows if row["mapping_case_id"] == ids[case])
            row.update(expected_canonical_disposition="approved_restoration_template", expected_outcome="passed", expected_reason="")
        _rewrite_csv(root, gate.CATEGORY_MAPPING_FILENAME, mutate_mapping)
    elif case in {"issue_kept_open", "coverage_removes_admit008"}:
        def mutate_issue(rows: list[dict[str, str]]) -> None:
            if case == "issue_kept_open":
                row = next(row for row in rows if row["issue_id"] == gate.PRIMARY_ISSUE)
                row.update(status="open", integration_transition="unchanged_open")
            else:
                row = next(row for row in rows if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
                row["affected_rules"] = row["affected_rules"].replace("ADMIT_008|", "")
        _rewrite_csv(root, gate.ISSUE_FILENAME, mutate_issue)
    elif case in {"source_sha", "raw_source", "checkpoint_source"}:
        def mutate_source(rows: list[dict[str, str]]) -> None:
            if case == "source_sha":
                rows[0]["filesystem_sha256"] = "0" * 64
            elif case == "raw_source":
                rows[0]["source_relative_path"] = "data/raw/forbidden.cif"
            else:
                rows[0]["source_relative_path"] = "checkpoints/forbidden.ckpt"
        _rewrite_csv(root, gate.SOURCE_BOUNDARY_FILENAME, mutate_source)
    else:
        def mutate_manifest(manifest: dict[str, object]) -> None:
            readiness = manifest["readiness"]
            assert isinstance(readiness, dict)
            if case == "allowed_blocked_member":
                manifest["allowed_topology_restoration_dispositions"] = list(gate.CANONICAL_ENUM_MEMBERS[:3])
            elif case == "allowed_order_changed":
                manifest["allowed_topology_restoration_dispositions"] = list(reversed(gate.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS))
            elif case == "trim_case_alias_allowed":
                manifest["alias_support"] = True
                manifest["scalar_normalization_applied"] = True
            elif case == "provider_mapping_validated":
                manifest["real_provider_topology_disposition_mapping_validated"] = True
                readiness["real_provider_topology_disposition_mapping_validated"] = True
            elif case == "provider_values_fabricated":
                manifest["real_provider_value_count"] = 1
                manifest["real_provider_value_count_nonzero"] = True
                readiness["real_provider_value_count_nonzero"] = True
            elif case == "readiness_mirror_drift":
                readiness["ready_for_bulk_download_now"] = True
            else:
                manifest["unexpected_semantic_claim"] = True
        _rewrite_manifest(root, mutate_manifest)
    with pytest.raises((AssertionError, ValueError, FileNotFoundError)):
        checker._validate_disk(root, enforce_frozen_hashes=False)


def test_materializer_preserves_frozen_sources_and_creates_no_partial_files(tmp_path: Path) -> None:
    before = {path: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() for path in gate.SOURCE_PATHS}
    gate.run_covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1(tmp_path)
    after = {path: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() for path in gate.SOURCE_PATHS}
    assert before == after == gate.SOURCE_SHA256
    assert not [path for path in tmp_path.iterdir() if path.suffix in (".tmp", ".part")]
