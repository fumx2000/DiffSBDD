from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_integration_gate as gate,
)


CHECKER_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_integration_gate_v1.py"


def _checker_module():
    spec = importlib.util.spec_from_file_location("covapie_e1d_checker_test", CHECKER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _materialize(root: Path) -> Path:
    result = gate.run_covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_integration_gate_v1(root)
    assert result["manifest"]["all_checks_passed"] is True
    return root


def _replace_snapshot_bytes(snapshot: gate.FrozenSourceSnapshot, path: Path, content: bytes) -> gate.FrozenSourceSnapshot:
    records = tuple(
        gate.FrozenSourceRecord(
            record.relative_path, record.expected_sha256, record.base_tree_sha256,
            record.filesystem_sha256, content if record.relative_path == path else record.content_bytes,
        )
        for record in snapshot.records
    )
    return gate.FrozenSourceSnapshot(records)


def test_exact12_source_order_structure_sha_and_base_tree_agreement() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    assert len(gate.SOURCE_PATHS) == len(set(gate.SOURCE_PATHS)) == 12
    assert tuple(gate.SOURCE_SHA256) == gate.SOURCE_PATHS
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert all(
        record.expected_sha256 == record.base_tree_sha256 == record.filesystem_sha256
        == hashlib.sha256(record.content_bytes).hexdigest() == gate.SOURCE_SHA256[record.relative_path]
        for record in snapshot.records
    )


def test_all_structural_checks_precede_first_source_content_read(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    original_structure = gate._structural_source_check
    original_read = Path.read_bytes

    def structural(path: Path, root: Path) -> bool:
        events.append(f"structure:{path}")
        return original_structure(path, root)

    def read(path: Path) -> bytes:
        events.append(f"read:{path}")
        return original_read(path)

    monkeypatch.setattr(gate, "_structural_source_check", structural)
    monkeypatch.setattr(Path, "read_bytes", read)
    gate.build_frozen_source_snapshot()
    first_read = next(index for index, event in enumerate(events) if event.startswith("read:"))
    assert first_read == 12
    assert all(event.startswith("structure:") for event in events[:12])


def test_structural_check_rejects_missing_symlink_and_unsafe_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class Result:
        returncode = 0
        stdout = "100644 blob 0123456789012345678901234567890123456789\tregular.csv\n"

    monkeypatch.setattr(gate, "_git", lambda *_args, **_kwargs: Result())
    regular = tmp_path / "regular.csv"
    regular.write_text("x\n", encoding="utf-8")
    assert gate._structural_source_check(Path("regular.csv"), tmp_path) is True
    assert gate._structural_source_check(Path("missing.csv"), tmp_path) is False
    symlink = tmp_path / "symlink.csv"
    symlink.symlink_to(regular)
    assert gate._structural_source_check(Path("symlink.csv"), tmp_path) is False
    assert gate._safe_relative_path(Path("../escape")) is False
    assert gate._safe_relative_path(Path("/absolute")) is False


def test_filesystem_hash_and_base_tree_drift_fail_closed_with_zero_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    snapshot = gate.build_frozen_source_snapshot()
    bad = _replace_snapshot_bytes(snapshot, gate.E1B_RULE_PATH, snapshot.records[0].content_bytes + b"drift")
    assert gate.validate_frozen_source_snapshot(bad) is False
    state = gate.build_integration_state(bad)
    assert state["all_checks_passed"] is state["integration_readiness"] is False
    assert (
        state["integrated_rule_count"], state["integrated_field_count"],
        state["integrated_context_count"], state["active_issue_count"],
    ) == (0, 0, 0, 0)

    original_git = gate._git

    def drift_git(arguments, repo_root, *, text=True):
        if arguments[:1] == ["show"] and arguments[1].endswith(gate.SOURCE_PATHS[0].as_posix()):
            return subprocess.CompletedProcess(["git", *arguments], 0, stdout=b"base-tree-drift\n", stderr=b"")
        return original_git(arguments, repo_root, text=text)

    monkeypatch.setattr(gate, "_git", drift_git)
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        gate.build_frozen_source_snapshot()


def test_source_failure_creates_no_success_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "build_frozen_source_snapshot", lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("failed")))
    root = tmp_path / "must-not-exist"
    with pytest.raises(RuntimeError, match="failed closed"):
        gate.run_covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_integration_gate_v1(root)
    assert not root.exists()


def test_e1b_direct_matrices_counts_and_readiness() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    e1b = gate._validate_e1b(snapshot)
    assert (len(e1b["rules"]), len(e1b["fields"]), len(e1b["contexts"]), len(e1b["issues"])) == (15, 22, 18, 10)
    assert sum(row["semantics_complete"] == "true" for row in e1b["rules"]) == 6
    assert sum(row["implementation_semantics_complete"] == "true" for row in e1b["fields"]) == 11
    assert sum(row["implementation_ready"] == "true" for row in e1b["contexts"]) == 8
    rule_map = {row["admission_rule_id"]: row for row in e1b["rules"]}
    field_map = {row["field_name"]: row for row in e1b["fields"]}
    context_map = {row["context_item"]: row for row in e1b["contexts"]}
    assert rule_map["ADMIT_004"]["semantics_complete"] == "false"
    assert rule_map["ADMIT_004"]["deterministic_evaluation_possible_now"] == "false"
    assert rule_map["ADMIT_004"]["deterministic_evaluation_possible_after_contract_freeze"] == "true"
    assert rule_map["ADMIT_004"]["blocking_reasons"] == gate.IDENTITY_ISSUE
    assert rule_map["ADMIT_005"]["implementation_disposition"] == "rule_logic_ready"
    insertion = field_map["covalent_residue_insertion_code"]
    assert insertion["allowed_values_defined"] == insertion["exact_validation_defined"] == "false"
    assert insertion["normalization_defined"] == "true" and insertion["blocking_reasons"] == gate.IDENTITY_ISSUE
    identity = context_map["covalent_residue_identity_contract"]
    assert identity["deterministic_now"] == identity["exact_contract_defined"] == identity["implementation_ready"] == "false"


def test_e1c_direct_contract_examples_issues_and_readiness() -> None:
    e1c = gate._validate_e1c(gate.build_frozen_source_snapshot())
    assert len(e1c["contract"]) == 31 and all(row["contract_passed"] == "true" for row in e1c["contract"])
    assert len(e1c["examples"]) == 64 and all(row["example_passed"] == "true" for row in e1c["examples"])
    assert [sum(row["row_kind"] == kind for row in e1c["examples"]) for kind in (
        "present_valid_example", "present_invalid_example", "state_value_truth",
    )] == [35, 15, 14]
    assert len([row for row in e1c["examples"] if row["row_kind"] == "present_valid_example" and 8 <= int(row["case_id"].split("_")[-1]) <= 35]) == 28
    assert len(e1c["issues"]) == 10 and all(row["status"] == "open" for row in e1c["issues"])
    manifest = e1c["manifest"]
    assert manifest["insertion_present_value_grammar_design_frozen"] is True
    assert manifest["state_value_combination_contract_frozen"] is True
    assert manifest["exact_preserve_policy_frozen"] is True
    assert manifest["agreement_requires_struct_conn_atom_site_candidate_and_provenance_exact_equality"] is True
    assert manifest["ready_for_insertion_present_value_grammar_successor_integration"] is True
    assert manifest["insertion_present_value_grammar_integrated_into_effective_schema"] is False
    assert manifest["parser_quote_class_roundtrip_verified"] is False
    assert manifest["real_provider_present_value_roundtrip_ready"] is False


def test_admit_004_exact_overlay_and_other_fourteen_rules_unchanged() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    state = gate.build_integration_state(snapshot)
    source = list(gate._csv_document(snapshot, gate.E1B_RULE_PATH).rows)
    source_map = {row["admission_rule_id"]: row for row in source}
    output_map = {row["admission_rule_id"]: row for row in state["rule_rows"]}
    assert len(output_map) == 15
    target = output_map["ADMIT_004"]
    assert target["semantics_complete"] == target["deterministic_evaluation_possible_now"] == "true"
    assert target["deterministic_evaluation_possible_after_contract_freeze"] == "true"
    assert target["implementation_disposition"] == "rule_logic_ready" and target["blocking_reasons"] == ""
    assert target["integration_source_stage"] == gate.E1C_STAGE
    assert target["integration_applied"] == "true" and target["integration_reason"] == gate.INTEGRATION_REASON
    for column in ("candidate_field_dependencies", "batch_context_dependencies", "evaluation_context_dependencies", "source_stage"):
        assert target[column] == source_map["ADMIT_004"][column]
    assert all(output_map[key] == source_map[key] for key in source_map if key != "ADMIT_004")


def test_insertion_field_exact_overlay_other_twenty_one_and_four_locators_unchanged() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    state = gate.build_integration_state(snapshot)
    source_map = {row["field_name"]: row for row in gate._csv_document(snapshot, gate.E1B_FIELD_PATH).rows}
    output_map = {row["field_name"]: row for row in state["field_rows"]}
    target = output_map["covalent_residue_insertion_code"]
    assert target["source_value_contract"] == gate.INSERTION_SOURCE_VALUE_CONTRACT
    assert all(target[column] == "true" for column in (
        "allowed_values_defined", "normalization_defined", "exact_validation_defined",
        "implementation_semantics_complete", "integration_applied",
    ))
    assert target["semantics_evidence"] == target["integration_source_stage"] == gate.E1C_STAGE
    assert target["blocking_reasons"] == "" and target["integration_reason"] == gate.INTEGRATION_REASON
    assert all(output_map[key] == source_map[key] for key in source_map if key != "covalent_residue_insertion_code")
    for name in (
        "covalent_residue_locator_namespace", "covalent_residue_insertion_code_state",
        "covalent_residue_locator_provenance_source_id", "covalent_residue_locator_provenance_sha256",
    ):
        assert output_map[name] == source_map[name]


def test_identity_context_exact_overlay_and_other_seventeen_unchanged() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    state = gate.build_integration_state(snapshot)
    source_map = {row["context_item"]: row for row in gate._csv_document(snapshot, gate.E1B_CONTEXT_PATH).rows}
    output_map = {row["context_item"]: row for row in state["context_rows"]}
    target = output_map["covalent_residue_identity_contract"]
    assert all(target[column] == "true" for column in (
        "deterministic_now", "deterministic_after_contract_freeze", "exact_contract_defined",
        "implementation_ready", "integration_applied",
    ))
    assert target["blocking_reasons"] == "" and target["integration_source_stage"] == gate.E1C_STAGE
    assert target["integration_reason"] == gate.INTEGRATION_REASON
    assert target["source_stage"] == source_map["covalent_residue_identity_contract"]["source_stage"]
    assert all(output_map[key] == source_map[key] for key in source_map if key != "covalent_residue_identity_contract")


def test_identity_issue_only_deleted_remaining_nine_and_provider_unchanged() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    state = gate.build_integration_state(snapshot)
    source = list(gate._csv_document(snapshot, gate.E1C_ISSUE_PATH).rows)
    source_map = {row["issue_id"]: row for row in source}
    output = state["issue_rows"]
    output_map = {row["issue_id"]: row for row in output}
    assert [row["issue_id"] for row in output] == [row["issue_id"] for row in source if row["issue_id"] != gate.IDENTITY_ISSUE]
    assert gate.IDENTITY_ISSUE not in output_map and len(output_map) == 9
    assert all(output_map[key] == source_map[key] for key in output_map)
    provider = output_map[gate.PROVIDER_ISSUE]
    assert provider["status"] == "open" and provider["severity"] == "blocking" and provider["issue_count"] == "11"


def test_counts_exact11_unknown_not_promoted_and_reason_preserved() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    e1b, e1c = gate._validate_e1b(snapshot), gate._validate_e1c(snapshot)
    state = gate.build_integration_state(snapshot)
    assert gate._validate_exact11_invariant(e1b, e1c)
    assert (
        state["integrated_rule_count"], state["integrated_field_count"],
        state["integrated_context_count"], state["active_issue_count"],
    ) == (15, 22, 18, 9)
    assert (
        state["semantics_complete_rule_count"],
        state["implementation_semantics_complete_field_count"],
        state["implementation_ready_context_count"],
    ) == (7, 12, 9)
    assert e1b["manifest"]["exact11_insertion_unknown_empty_count"] == 11
    assert e1b["manifest"]["exact11_insertion_blocked_count"] == 11
    assert e1b["manifest"]["exact11_effective_blocked_count"] == 11
    unknown = next(row for row in e1c["examples"] if row["case_id"] == "STATE_VALUE_007")
    assert unknown["observed_outcome"] == "blocked" and unknown["observed_reason"] == gate.UNKNOWN_REASON


def test_manifest_identity_readiness_true_but_evaluator_provider_and_downstream_false(tmp_path: Path) -> None:
    root = _materialize(tmp_path / "out")
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    true_keys = (
        "insertion_present_value_grammar_integrated_into_effective_schema",
        "residue_identity_semantics_integrated_into_effective_schema",
        "covalent_residue_identity_contract_fully_integrated", "admit_004_rule_logic_ready",
        "ready_for_admit_004_rule_logic_implementation", "admit_005_rule_logic_ready",
        "invalid_state_value_outcomes_fail_closed",
        "agreement_requires_struct_conn_atom_site_candidate_and_provenance_exact_equality",
        "feature_semantics_audit_required_before_training",
    )
    false_keys = (
        "admit_004_evaluator_implemented", "parser_quote_class_roundtrip_verified",
        "real_provider_present_value_roundtrip_ready", "real_provider_export_blocking_rows_resolved",
        "candidate_records_materialized", "ready_for_real_candidate_evaluation",
        "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
    )
    assert all(manifest[key] is True for key in true_keys)
    assert all(manifest[key] is False for key in false_keys)
    assert manifest["resolved_issue_ids"] == [gate.IDENTITY_ISSUE]
    assert manifest["provider_blocking_issue_count"] == 11
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert not any(key in manifest for key in ("timestamp", "hostname", "host", "manifest_sha256"))


def test_safety_rows_exact_and_no_padding() -> None:
    rows = gate._safety_rows()
    assert [row["safety_item"] for row in rows] == [*gate.TRUE_SAFETY_ITEMS, *gate.FALSE_SAFETY_ITEMS]
    assert len(rows) == 23 and all(row["safety_passed"] == "true" for row in rows)
    assert all(row["observed_executed"] == "true" for row in rows[:8])
    assert all(row["observed_executed"] == "false" for row in rows[8:])


def test_deterministic_double_materialization_and_checker(tmp_path: Path) -> None:
    first, second = _materialize(tmp_path / "first"), _materialize(tmp_path / "second")
    assert {path.name for path in first.iterdir()} == set(gate.OUTPUT_FILES)
    assert all((first / name).read_bytes() == (second / name).read_bytes() for name in gate.OUTPUT_FILES)
    assert _checker_module().check(first)["all_checks_passed"] is True
    assert not list(tmp_path.rglob("*.tmp")) and not list(tmp_path.rglob("*.part"))


@pytest.mark.parametrize("mutation", ["missing", "extra", "symlink", "hash", "overclaim"])
def test_checker_output_missing_extra_symlink_hash_and_overclaim_fail_closed(
    tmp_path: Path, mutation: str,
) -> None:
    root = _materialize(tmp_path / "out")
    check = _checker_module().check
    target = root / gate.RULE_FILENAME
    if mutation == "missing":
        target.unlink()
    elif mutation == "extra":
        (root / "extra.csv").write_text("x\n", encoding="utf-8")
    elif mutation == "symlink":
        copy = tmp_path / "rule-copy.csv"
        copy.write_bytes(target.read_bytes())
        target.unlink()
        target.symlink_to(copy)
    elif mutation == "hash":
        target.write_bytes(target.read_bytes() + b"drift\n")
    else:
        path = root / gate.MANIFEST_FILENAME
        value = json.loads(path.read_text(encoding="utf-8"))
        value["ready_for_bulk_download_now"] = True
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises((AssertionError, FileNotFoundError)):
        check(root)


def test_import_has_no_stdout_stderr_or_output_side_effects() -> None:
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        importlib.reload(sys.modules[gate.__name__])
    assert stdout.getvalue() == stderr.getvalue() == ""


def test_production_and_checker_use_standard_library_only_and_no_forbidden_behavior() -> None:
    allowed = set(sys.stdlib_module_names) | {"__future__", "covalent_ext"}
    forbidden = {"torch", "numpy", "rdkit", "Bio", "gemmi", "dataset", "lightning_modules"}
    for path in (Path(gate.__file__), CHECKER_PATH):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        assert imported <= allowed and imported.isdisjoint(forbidden)
    assert all(path.parts[0] != "data" or path.parts[:2] != ("data", "raw") for path in gate.SOURCE_PATHS)
    assert all("checkpoint" not in path.parts for path in gate.SOURCE_PATHS)
    safety = {row["safety_item"]: row for row in gate._safety_rows()}
    for item in gate.FALSE_SAFETY_ITEMS:
        assert safety[item]["expected_executed"] == safety[item]["observed_executed"] == "false"


def test_output_root_rejects_extra_and_symlink_entries(tmp_path: Path) -> None:
    extra_root = tmp_path / "extra"
    extra_root.mkdir()
    (extra_root / "unexpected").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected"):
        _materialize(extra_root)
    regular = tmp_path / "regular"
    regular.mkdir()
    link_root = tmp_path / "link-root"
    link_root.symlink_to(regular, target_is_directory=True)
    with pytest.raises(ValueError, match="non-symlink"):
        _materialize(link_root)
