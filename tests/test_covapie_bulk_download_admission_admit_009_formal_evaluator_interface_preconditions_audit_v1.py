from __future__ import annotations

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
    covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit as gate,
)

CHECKER_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit_v1.py"
SPEC = importlib.util.spec_from_file_location("admit009_checker", CHECKER_PATH)
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


def _assert_checker_rejects(root: Path) -> None:
    with pytest.raises((AssertionError, ValueError, FileNotFoundError)):
        checker._validate_disk(root, enforce_frozen_hashes=False)


def test_exact24_audit_truth_and_readiness() -> None:
    state = gate.build_audit_state()
    rows = state["precondition_rows"]
    assert len(rows) == 24
    assert [row["precondition_id"] for row in rows] == [f"PRE_{index:03d}" for index in range(1, 25)]
    assert all(row["precondition_passed"] == "true" for row in rows)
    assert sum(row["semantics_complete"] == "true" for row in rows) == 6
    assert sum(row["semantics_complete"] == "false" for row in rows) == 18
    assert all(row["semantics_complete"] == "true" for row in rows[:6])
    assert all(row["semantics_complete"] == "false" for row in rows[6:])
    assert state["readiness"]["ready_for_admit_009_duplicate_identity_key_contract_design"] is True
    assert state["readiness"]["ready_for_admit_009_standalone_evaluator_interface_implementation"] is False


def test_identity_context_and_stop_boundary() -> None:
    result = gate.run_covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit_v1()
    manifest = result["manifest"]
    assert manifest["admission_rule_id"] == "ADMIT_009"
    assert manifest["admission_rule_name"] == "duplicate_identity_precheck"
    assert manifest["evaluation_phase"] == "pre_download"
    assert manifest["candidate_field"] == "duplicate_identity_key"
    assert manifest["batch_context_item"] == "batch_duplicate_identity_keys"
    assert manifest["evaluation_policy_context_item"] == "duplicate_identity_key_contract"
    assert manifest["real_provider_duplicate_identity_key_count"] == 0
    assert not hasattr(gate, "evaluate_admit_009")
    assert not hasattr(gate, "Admit009EvaluationResult")


def test_source_boundary_and_exact11_preservation() -> None:
    state = gate.build_audit_state()
    assert len(state["source_rows"]) == 17
    assert all(row["source_boundary_passed"] == "true" for row in state["source_rows"])
    assert len(state["issue_rows"]) == 11
    assert gate.hashlib.sha256(state["issue_bytes"]).hexdigest() == "1c11f931b103fe8d523115b00f85d095956042ea1168741b8ec42bbf24a38128"
    blocker = next(row for row in state["issue_rows"] if row["issue_id"] == gate.PRIMARY_BLOCKER)
    coverage = next(row for row in state["issue_rows"] if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert blocker["status"] == "open" and blocker["integration_transition"] == "unchanged_open"
    assert coverage["affected_rules"].split("|")[0] == "ADMIT_009"


def test_vocabulary_has_no_promoted_components_or_equivalence() -> None:
    rows = gate.build_audit_state()["vocabulary_rows"]
    assert len(rows) == 24
    assert sum(row["explicitly_declared_duplicate_key"] == "true" for row in rows) == 1
    assert all(row["explicitly_declared_duplicate_key_component"] == "false" for row in rows)
    assert all(row["exact_duplicate_equivalence_declared"] == "false" for row in rows)
    assert all(row["safe_to_use_in_duplicate_key_contract_now"] == "false" for row in rows)
    terms = {row["observed_term"] for row in rows}
    assert {"candidate_record_id", "sample_index_row_id", "assignment_id", "ligand_graph_group_id", "ligand_scaffold_group_id", "final_leakage_group_id"} <= terms


def test_occurrence_inventory_is_exact_and_non_promotional() -> None:
    rows = gate.build_audit_state()["occurrence_rows"]
    assert len(rows) == 103
    assert {row["matched_term"] for row in rows} == set(gate.MATCH_TERMS)
    assert all(row["occurrence_passed"] == "true" for row in rows)
    leakage = [row for row in rows if row["matched_term"] in {"leakage_group_id", "final_leakage_group_id"}]
    assert leakage and all("not thereby a duplicate key" in row["semantic_statement"] for row in leakage)


@pytest.mark.parametrize(
    "term",
    [
        "candidate_record_id", "sample_index_row_id", "assignment_id", "ligand_comp_id",
        "ligand_graph_group_id", "ligand_scaffold_group_id", "leakage_group_id",
        "final_leakage_group_id",
    ],
)
def test_rejects_identity_promoted_to_duplicate_key(tmp_path: Path, term: str) -> None:
    root = _copy_outputs(tmp_path, term)
    path = root / checker.EXPECTED_FILES[1]
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split(",")
    term_index = header.index("observed_term")
    declared_index = header.index("explicitly_declared_duplicate_key")
    changed = False
    for index in range(1, len(lines)):
        cells = lines[index].split(",")
        if cells[term_index] == term:
            cells[declared_index] = "true"
            lines[index] = ",".join(cells)
            changed = True
            break
    assert changed
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    checker._refresh_hash(root, checker.EXPECTED_FILES[1])
    _assert_checker_rejects(root)


def test_rejects_same_leakage_group_as_exact_duplicate(tmp_path: Path) -> None:
    root = _copy_outputs(tmp_path)
    path = root / checker.EXPECTED_FILES[1]
    text = path.read_text(encoding="utf-8").replace(
        "final_leakage_group_id,conservative multi-relation must-link group,leakage_group,false,false,false,false",
        "final_leakage_group_id,conservative multi-relation must-link group,leakage_group,false,false,true,false", 1,
    )
    path.write_text(text, encoding="utf-8")
    checker._refresh_hash(root, checker.EXPECTED_FILES[1])
    _assert_checker_rejects(root)


@pytest.mark.parametrize(
    ("precondition_id", "readiness_key"),
    [
        ("PRE_010", "admit_009_duplicate_key_composition_contract_available"),
        ("PRE_007", "admit_009_duplicate_key_exact_type_contract_available"),
        ("PRE_014", "admit_009_batch_container_contract_available"),
        ("PRE_017", "admit_009_self_exclusion_contract_available"),
        ("PRE_020", "admit_009_reason_outcome_contract_available"),
        ("PRE_023", "admit_009_independent_semantic_oracle_available"),
    ],
)
def test_rejects_semantic_gap_overclaim(tmp_path: Path, precondition_id: str, readiness_key: str) -> None:
    root = _copy_outputs(tmp_path, precondition_id)
    path = root / checker.EXPECTED_FILES[0]
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.startswith(precondition_id + ","):
            cells = line.split(",")
            cells[5] = "true"
            cells[6] = ""
            lines[index] = ",".join(cells)
            break
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    checker._refresh_hash(root, checker.EXPECTED_FILES[0])
    _rewrite_manifest(root, lambda m: (m.__setitem__(readiness_key, True), m["readiness"].__setitem__(readiness_key, True)))
    _assert_checker_rejects(root)


def test_rejects_fabricated_real_duplicate_key(tmp_path: Path) -> None:
    root = _copy_outputs(tmp_path)
    _rewrite_manifest(root, lambda m: m.__setitem__("real_provider_duplicate_identity_key_count", 1))
    _assert_checker_rejects(root)


def test_rejects_synthetic_group_as_real_provider_value(tmp_path: Path) -> None:
    root = _copy_outputs(tmp_path)
    path = root / checker.EXPECTED_FILES[1]
    text = path.read_text(encoding="utf-8").replace(
        "ligand_graph_group,false,false,false,false",
        "ligand_graph_group,false,true,false,true", 1,
    )
    path.write_text(text, encoding="utf-8")
    checker._refresh_hash(root, checker.EXPECTED_FILES[1])
    _assert_checker_rejects(root)


def test_rejects_duplicate_blocker_resolved(tmp_path: Path) -> None:
    root = _copy_outputs(tmp_path)
    path = root / checker.EXPECTED_FILES[4]
    path.write_text(path.read_text(encoding="utf-8").replace(
        f"{checker.EXPECTED_BLOCKER},implementation_semantics_gap,duplicate_identity_key,ADMIT_009,blocking,open,",
        f"{checker.EXPECTED_BLOCKER},implementation_semantics_gap,duplicate_identity_key,ADMIT_009,blocking,resolved,",
    ), encoding="utf-8")
    checker._refresh_hash(root, checker.EXPECTED_FILES[4])
    _assert_checker_rejects(root)


def test_rejects_admit009_removed_from_coverage(tmp_path: Path) -> None:
    root = _copy_outputs(tmp_path)
    path = root / checker.EXPECTED_FILES[4]
    text = path.read_text(encoding="utf-8").replace(
        "ADMIT_009|ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        "ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015", 1,
    )
    path.write_text(text, encoding="utf-8")
    checker._refresh_hash(root, checker.EXPECTED_FILES[4])
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
        gate._validate_expected_base_lineage(REPO_ROOT, head_ref="HEAD^")


def test_rejects_missing_extra_and_symlink_outputs(tmp_path: Path) -> None:
    missing = _copy_outputs(tmp_path, "missing")
    (missing / checker.EXPECTED_FILES[0]).unlink()
    _assert_checker_rejects(missing)
    extra = _copy_outputs(tmp_path, "extra")
    (extra / "unexpected.txt").write_text("x", encoding="utf-8")
    _assert_checker_rejects(extra)
    linked = _copy_outputs(tmp_path, "linked")
    path = linked / checker.EXPECTED_FILES[0]
    content = path.read_bytes()
    path.unlink()
    target = tmp_path / "target.csv"
    target.write_bytes(content)
    path.symlink_to(target)
    _assert_checker_rejects(linked)


def test_semantic_tamper_with_refreshed_manifest_hash_is_rejected(tmp_path: Path) -> None:
    root = _copy_outputs(tmp_path)
    path = root / checker.EXPECTED_FILES[1]
    path.write_text(path.read_text(encoding="utf-8").replace(
        "record_identifier,false,false,false,false",
        "record_identifier,true,true,true,true", 1,
    ), encoding="utf-8")
    checker._refresh_hash(root, checker.EXPECTED_FILES[1])
    _assert_checker_rejects(root)


def test_rejects_readiness_nested_top_level_drift(tmp_path: Path) -> None:
    root = _copy_outputs(tmp_path)
    _rewrite_manifest(root, lambda m: m["readiness"].__setitem__("ready_for_bulk_download_now", True))
    _assert_checker_rejects(root)


def test_rejects_unknown_manifest_key_and_validation_failure(tmp_path: Path) -> None:
    unknown = _copy_outputs(tmp_path, "unknown")
    _rewrite_manifest(unknown, lambda m: m.__setitem__("unknown_key", True))
    _assert_checker_rejects(unknown)
    failure = _copy_outputs(tmp_path, "failure")
    _rewrite_manifest(failure, lambda m: m.__setitem__("validation_failures", ["fabricated"]))
    _assert_checker_rejects(failure)


def test_production_and_checker_imports_are_silent_and_side_effect_free(tmp_path: Path) -> None:
    before = tuple(tmp_path.iterdir())
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(SRC_ROOT)!r}); "
        "import covalent_ext.covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit; "
        "import importlib.util; "
        f"s=importlib.util.spec_from_file_location('c', {str(CHECKER_PATH)!r}); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m)"
    )
    result = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, text=True, capture_output=True, check=False)
    assert result.returncode == 0 and result.stdout == "" and result.stderr == ""
    assert tuple(tmp_path.iterdir()) == before


def test_checker_accepts_frozen_outputs() -> None:
    manifest = checker._validate_disk(OUTPUT_ROOT)
    assert manifest["validation_failures"] == []
    assert manifest["ready_for_admit_009_standalone_evaluator_interface_implementation"] is False


def test_deterministic_double_materialization(tmp_path: Path) -> None:
    root = tmp_path / "materialized"
    first = gate.run_covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit_v1(root)
    first_bytes = {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    second = gate.run_covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit_v1(root)
    second_bytes = {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    assert first["manifest"] == second["manifest"]
    assert first_bytes == second_bytes
