from __future__ import annotations

import csv
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit as gate,
)

CHECKER_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit_v1.py"
SPEC = importlib.util.spec_from_file_location("admit010_checker", CHECKER_PATH)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
OUTPUT_ROOT = REPO_ROOT / checker.EXPECTED_OUTPUT_ROOT


def _copy_outputs(tmp_path: Path, name: str = "outputs") -> Path:
    destination = tmp_path / name
    shutil.copytree(OUTPUT_ROOT, destination)
    return destination


def _rewrite_manifest(root: Path, mutate) -> None:
    path = root / checker.EXPECTED_FILES[5]
    manifest = json.loads(path.read_text(encoding="utf-8"))
    mutate(manifest)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _rewrite_csv(root: Path, file_index: int, mutate) -> None:
    path = root / checker.EXPECTED_FILES[file_index]
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    mutate(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    checker._refresh_hash(root, checker.EXPECTED_FILES[file_index])


def _assert_checker_rejects(root: Path) -> None:
    with pytest.raises((AssertionError, ValueError, FileNotFoundError)):
        checker._validate_disk(root, enforce_frozen_hashes=False)


def _authorized_hashes(root: Path) -> dict[str, str]:
    return {
        name: gate.hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in gate.OUTPUT_FILES
        if (root / name).is_file() and not (root / name).is_symlink()
    }


def _copy_authorized_outputs(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for name in gate.OUTPUT_FILES:
        shutil.copy2(OUTPUT_ROOT / name, root / name)


def test_exact21_preconditions_and_fail_closed_design_readiness() -> None:
    state = gate.build_audit_state()
    rows = state["precondition_rows"]
    assert len(rows) == 21
    assert [row["precondition_id"] for row in rows] == [f"PRE_{index:03d}" for index in range(1, 22)]
    assert all(row["audit_passed"] == "true" for row in rows)
    assert sum(row["verified"] == "true" for row in rows) == 17
    assert sum(row["verified"] == "false" for row in rows) == 4
    assert state["readiness"]["ready_for_admit_010_leakage_group_assignment_provenance_contract_design"] is True
    assert state["readiness"]["leakage_group_assignment_provenance_contract_frozen"] is False


def test_rule_field_context_and_historical_vocabulary() -> None:
    result = gate.run_covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit_v1()
    manifest = result["manifest"]
    assert manifest["admission_rule_id"] == "ADMIT_010"
    assert manifest["admission_rule_name"] == "leakage_group_assignment_before_split"
    assert manifest["evaluation_phase"] == "pre_final_split"
    assert manifest["candidate_field"] == "leakage_group_id"
    assert manifest["evaluation_context"] == "leakage_group_assignment_provenance_contract"
    assert manifest["required_status"] == "leakage_group_assigned"
    assert manifest["historical_blocking_reason"] == "leakage_group_unassigned"


def test_exact32_sources_and_exact9_issue_bytes_preserved() -> None:
    state = gate.build_audit_state()
    assert len(state["source_rows"]) == 32
    assert all(row["source_boundary_passed"] == "true" for row in state["source_rows"])
    assert len(state["issue_rows"]) == 11
    assert gate.hashlib.sha256(state["issue_bytes"]).hexdigest() == "bb159a201f103a4cc04087978a7ca2a7bec7574fb9fc55d3cc0b059415f679e6"
    blocker = next(row for row in state["issue_rows"] if row["issue_id"] == gate.PRIMARY_BLOCKER)
    coverage = next(row for row in state["issue_rows"] if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert blocker["status"] == "open" and blocker["integration_transition"] == "unchanged_open"
    assert coverage["affected_rules"] == "ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"


def test_occurrence_inventory_searches_all_terms_without_equivalence_promotion() -> None:
    state = gate.build_audit_state()
    rows = state["occurrence_rows"]
    assert len(rows) == 401
    assert all(row["audit_result"] == "observed_without_semantic_equivalence_promotion" for row in rows)
    assert state["term_search_counts"]["policy version"] == 0
    assert all(count > 0 for term, count in state["term_search_counts"].items() if term != "policy version")
    assert all(row["semantic_classification"] == "record_identifier_not_group_identifier" for row in rows if row["term"] == "assignment_id")


def test_observed_inventory_is_deduplicated_and_does_not_freeze_grammar() -> None:
    rows = gate.build_audit_state()["observed_rows"]
    assert len(rows) == 197
    keys = [(row["source_relative_path"], row["field_name"], row["observed_value"]) for row in rows]
    assert len(keys) == len(set(keys))
    assert {row["inferred_exact_builtin_type"] for row in rows} == {"str", "int", "bool"}
    assert all(row["general_grammar_frozen"] == "false" for row in rows)
    assert all(row["provenance_equivalence_inferred"] == "false" for row in rows)
    assert not any(row["field_name"] == "leakage_group_id" for row in rows)
    assert {row["observed_value"] for row in rows if row["field_name"] == "final_leakage_group_id"} == {f"COVAPIE_LEAKAGE_GROUP_{index:06d}" for index in range(1, 6)}


def test_assignment_split_final_ordering_and_membership_evidence() -> None:
    contracts = gate.build_audit_state()["contracts"]
    assignment = contracts["assignment_manifest"]
    split = contracts["split_manifest"]
    final = contracts["final_manifest"]
    assert assignment["stage"] == split["previous_stage"] == split["source_step14ap_stage"]
    assert assignment["split_assignments_written"] is False
    assert split["split_optimizer_executed"] is True
    assert final["previous_stage"] == split["stage"]
    assert final["source_step14aq_preconditions_passed"] is True
    group_rows = gate._csv_rows(gate.build_frozen_source_snapshot(), gate.GROUP_INVENTORY_PATH)
    assert len(group_rows) == 5 and sum(int(row["member_count"]) for row in group_rows) == 11


def test_candidate_final_mapping_and_substitutions_remain_unverified() -> None:
    manifest = json.loads((OUTPUT_ROOT / checker.EXPECTED_FILES[5]).read_text(encoding="utf-8"))
    assert manifest["canonical_candidate_field"] == "leakage_group_id"
    assert manifest["historical_artifact_field"] == "final_leakage_group_id"
    assert manifest["candidate_to_historical_field_mapping_status"] == "unverified"
    assert manifest["assignment_id_semantics"] == "record_identifier_not_group_identifier"
    assert manifest["duplicate_identity_key_substitution_allowed"] is False
    assert manifest["single_axis_group_substitution_allowed"] is False


def test_pure_memory_stop_boundary_and_future_names_absent() -> None:
    manifest = gate.materialize_audit()["manifest"]
    assert manifest["future_evaluator_runs_grouping_algorithm"] is False
    assert manifest["future_evaluator_accesses_filesystem_or_split_files"] is False
    assert manifest["split_assignment_proves_pre_split_assignment"] is False
    assert not hasattr(gate, "evaluate_admit_010")
    assert not hasattr(gate, "Admit010EvaluationResult")


def test_deterministic_double_materialization(tmp_path: Path) -> None:
    left, right = tmp_path / "left", tmp_path / "right"
    gate.materialize_audit(left)
    gate.materialize_audit(right)
    assert [path.name for path in sorted(left.iterdir())] == [path.name for path in sorted(right.iterdir())]
    assert all((left / name).read_bytes() == (right / name).read_bytes() for name in gate.OUTPUT_FILES)


def test_output_root_directory_symlink_rejected_without_target_write(tmp_path: Path) -> None:
    target = tmp_path / "external-target"
    target.mkdir()
    sentinel = target / "sentinel.txt"
    sentinel.write_text("unchanged", encoding="utf-8")
    root = tmp_path / "output-link"
    root.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="real directory"):
        gate.materialize_audit(root)
    assert sentinel.read_text(encoding="utf-8") == "unchanged"
    assert {entry.name for entry in target.iterdir()} == {"sentinel.txt"}


def test_output_root_regular_file_rejected(tmp_path: Path) -> None:
    root = tmp_path / "output-file"
    root.write_text("unchanged", encoding="utf-8")
    with pytest.raises(ValueError, match="real directory"):
        gate.materialize_audit(root)
    assert root.read_text(encoding="utf-8") == "unchanged"


def test_unexpected_entry_rejected_before_any_authorized_output_changes(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    _copy_authorized_outputs(root)
    before = _authorized_hashes(root)
    unexpected = root / "unexpected.txt"
    unexpected.write_text("do-not-clean", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected entry"):
        gate.materialize_audit(root)
    assert _authorized_hashes(root) == before
    assert unexpected.read_text(encoding="utf-8") == "do-not-clean"
    assert not list(root.glob("*.tmp"))


def test_authorized_output_symlink_rejected_without_external_target_write(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    root.mkdir()
    external = tmp_path / "external.csv"
    external.write_text("unchanged\n", encoding="utf-8")
    output = root / gate.PRECONDITION_FILENAME
    output.symlink_to(external)
    with pytest.raises(ValueError, match="regular non-symlink"):
        gate.materialize_audit(root)
    assert output.is_symlink()
    assert external.read_text(encoding="utf-8") == "unchanged\n"
    assert {entry.name for entry in root.iterdir()} == {gate.PRECONDITION_FILENAME}


def test_authorized_output_directory_rejected_without_partial_write(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    _copy_authorized_outputs(root)
    directory = root / gate.OBSERVED_FILENAME
    directory.unlink()
    directory.mkdir()
    before = _authorized_hashes(root)
    with pytest.raises(ValueError, match="regular non-symlink"):
        gate.materialize_audit(root)
    assert directory.is_dir() and not directory.is_symlink()
    assert _authorized_hashes(root) == before
    assert not list(root.glob("*.tmp"))


def test_safe_empty_output_root_succeeds_with_exact_regular_inventory(tmp_path: Path) -> None:
    root = tmp_path / "empty"
    root.mkdir()
    result = gate.materialize_audit(root)
    assert result["output_root"] == root
    assert {entry.name for entry in root.iterdir()} == set(gate.OUTPUT_FILES)
    assert all(stat.S_ISREG(os.lstat(root / name).st_mode) and not (root / name).is_symlink() for name in gate.OUTPUT_FILES)
    assert not list(root.glob("*.tmp"))


def test_safe_existing_six_regular_outputs_succeed_byte_identically(tmp_path: Path) -> None:
    root = tmp_path / "existing"
    _copy_authorized_outputs(root)
    before = _authorized_hashes(root)
    gate.materialize_audit(root)
    assert _authorized_hashes(root) == before
    assert not list(root.glob("*.tmp"))


def test_atomic_write_failure_cleans_same_directory_temp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "atomic"
    root.mkdir()
    destination = root / "output.csv"
    monkeypatch.setattr(gate.os, "replace", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("forced")))
    with pytest.raises(OSError, match="forced"):
        gate._atomic_write(destination, b"exact-bytes\n")
    assert not destination.exists()
    assert not list(root.glob("*.tmp"))


def test_checker_independently_exercises_materializer_output_safety() -> None:
    checker._validate_materializer_output_safety()


def test_checker_positive_and_exact_six_regular_outputs() -> None:
    manifest = checker._validate_disk()
    assert manifest["primary_blocker_status"] == "open"
    entries = list(OUTPUT_ROOT.iterdir())
    assert len(entries) == 6
    assert all(stat.S_ISREG(os.lstat(path).st_mode) and not path.is_symlink() for path in entries)


@pytest.mark.parametrize(
    ("area", "readiness_key"),
    [
        ("final_vs_provisional_group_distinction", "leakage_group_id_final_grammar_frozen"),
        ("assignment_policy_version_availability", "leakage_group_assignment_provenance_contract_frozen"),
        ("provider_mapping_status", "leakage_group_id_provider_mapping_validated"),
        ("real_evaluation_status", "real_candidate_evaluation"),
    ],
)
def test_rejects_precondition_and_readiness_overclaim(tmp_path: Path, area: str, readiness_key: str) -> None:
    root = _copy_outputs(tmp_path, area)
    _rewrite_csv(root, 0, lambda rows: next(row for row in rows if row["semantic_area"] == area).__setitem__("verified", "true"))
    _rewrite_manifest(root, lambda manifest: (manifest["readiness"].__setitem__(readiness_key, True), manifest.__setitem__(readiness_key, True)))
    _assert_checker_rejects(root)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("candidate_to_historical_field_mapping_status", "verified_equivalent"),
        ("assignment_id_semantics", "group_identifier"),
        ("duplicate_identity_key_substitution_allowed", True),
        ("single_axis_group_substitution_allowed", True),
        ("split_assignment_proves_pre_split_assignment", True),
        ("future_evaluator_runs_grouping_algorithm", True),
        ("future_evaluator_accesses_filesystem_or_split_files", True),
        ("primary_blocker_status", "resolved"),
    ],
)
def test_rejects_boundary_overclaim(tmp_path: Path, key: str, value: object) -> None:
    root = _copy_outputs(tmp_path, key)
    _rewrite_manifest(root, lambda manifest: manifest.__setitem__(key, value))
    _assert_checker_rejects(root)


def test_rejects_fabricated_policy_version_occurrence(tmp_path: Path) -> None:
    root = _copy_outputs(tmp_path)
    _rewrite_manifest(root, lambda manifest: manifest["term_search_counts"].__setitem__("policy version", 1))
    _assert_checker_rejects(root)


def test_rejects_assignment_id_promoted_to_group_id(tmp_path: Path) -> None:
    root = _copy_outputs(tmp_path)
    _rewrite_csv(root, 1, lambda rows: next(row for row in rows if row["term"] == "assignment_id").__setitem__("semantic_classification", "group_identifier"))
    _assert_checker_rejects(root)


def test_rejects_historical_values_promoted_to_grammar(tmp_path: Path) -> None:
    root = _copy_outputs(tmp_path)
    _rewrite_csv(root, 2, lambda rows: next(row for row in rows if row["field_name"] == "final_leakage_group_id").__setitem__("general_grammar_frozen", "true"))
    _assert_checker_rejects(root)


def test_rejects_provenance_inferred_from_equal_value(tmp_path: Path) -> None:
    root = _copy_outputs(tmp_path)
    _rewrite_csv(root, 2, lambda rows: next(row for row in rows if row["field_name"] == "final_leakage_group_id").__setitem__("provenance_equivalence_inferred", "true"))
    _assert_checker_rejects(root)


def test_rejects_duplicate_observed_value_tuple(tmp_path: Path) -> None:
    root = _copy_outputs(tmp_path)
    _rewrite_csv(root, 2, lambda rows: rows.append({**rows[0], "value_order": str(len(rows) + 1)}))
    _assert_checker_rejects(root)


def test_rejects_primary_blocker_resolved(tmp_path: Path) -> None:
    root = _copy_outputs(tmp_path)
    _rewrite_csv(root, 4, lambda rows: next(row for row in rows if row["issue_id"] == checker.EXPECTED_BLOCKER).__setitem__("status", "resolved"))
    _assert_checker_rejects(root)


def test_rejects_admit010_removed_from_coverage(tmp_path: Path) -> None:
    root = _copy_outputs(tmp_path)
    _rewrite_csv(root, 4, lambda rows: next(row for row in rows if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE").__setitem__("affected_rules", "ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"))
    _assert_checker_rejects(root)


def test_rejects_any_issue_byte_change(tmp_path: Path) -> None:
    root = _copy_outputs(tmp_path)
    path = root / checker.EXPECTED_FILES[4]
    path.write_bytes(path.read_bytes() + b"\n")
    checker._refresh_hash(root, checker.EXPECTED_FILES[4])
    _assert_checker_rejects(root)


@pytest.mark.parametrize("unsafe", [Path("data/raw/source.csv"), Path("checkpoints/model.ckpt"), Path("../escape.csv"), Path("/absolute.csv")])
def test_rejects_unsafe_source_boundary_path(unsafe: Path) -> None:
    assert gate._safe_relative_path(unsafe) is False


def test_rejects_source_sha_mismatch() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    first = snapshot.records[0]
    altered = gate.FrozenSourceRecord(first.relative_path, first.expected_sha256, first.base_tree_sha256, first.filesystem_sha256, first.content_bytes + b"x")
    assert gate.validate_frozen_source_snapshot(gate.FrozenSourceSnapshot((altered, *snapshot.records[1:]))) is False


def test_rejects_source_symlink_before_content_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    target.write_text("x", encoding="utf-8")
    link = tmp_path / "source.csv"
    link.symlink_to(target)
    monkeypatch.setattr(gate, "_git", lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="100644 blob deadbeef\tsource.csv\n"))
    assert gate._structural_source_check(Path("source.csv"), tmp_path) is False


def test_rejects_non_descendant_base() -> None:
    with pytest.raises(ValueError, match="not an ancestor"):
        gate._validate_expected_base_lineage(REPO_ROOT, head_ref=f"{gate.EXPECTED_BASE_COMMIT}^")


def test_rejects_missing_extra_and_symlink_outputs(tmp_path: Path) -> None:
    missing = _copy_outputs(tmp_path, "missing")
    (missing / checker.EXPECTED_FILES[0]).unlink()
    _assert_checker_rejects(missing)
    extra = _copy_outputs(tmp_path, "extra")
    (extra / "unexpected.txt").write_text("x", encoding="utf-8")
    _assert_checker_rejects(extra)
    linked = _copy_outputs(tmp_path, "linked")
    path = linked / checker.EXPECTED_FILES[0]
    target = tmp_path / "target.csv"
    target.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(target)
    _assert_checker_rejects(linked)


def test_checker_cli_and_silent_import() -> None:
    environment = {**os.environ, "PYTHONPATH": str(SRC_ROOT), "PYTHONDONTWRITEBYTECODE": "1"}
    checked = subprocess.run([sys.executable, "-B", str(CHECKER_PATH)], cwd=REPO_ROOT, env=environment, capture_output=True, text=True, check=False)
    assert checked.returncode == 0 and "primary_blocker_status=open" in checked.stdout and checked.stderr == ""
    imported = subprocess.run([sys.executable, "-B", "-c", "import covalent_ext.covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit"], cwd=REPO_ROOT, env=environment, capture_output=True, text=True, check=False)
    assert imported.returncode == 0 and imported.stdout == imported.stderr == ""
