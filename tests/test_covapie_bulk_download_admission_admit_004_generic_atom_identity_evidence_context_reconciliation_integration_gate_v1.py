from __future__ import annotations

import ast
import csv
import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_integration_gate
    as gate,
)


def _csv_rows(content: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(content.decode("utf-8"), newline="")))


@pytest.fixture(scope="module")
def snapshots() -> tuple[gate.FrozenSourceSnapshot, ...]:
    return gate.freeze_source_snapshots()


@pytest.fixture(scope="module")
def predecessor_views(snapshots):
    return gate.validate_predecessors(snapshots)


@pytest.fixture(scope="module")
def outputs() -> dict[str, bytes]:
    return gate.build_output_bytes()


def test_exact12_order_and_expected_sha_contract():
    assert len(gate.SOURCE_SPECS) == 12
    assert [spec.relative_path for spec in gate.SOURCE_SPECS[:6]] == [
        f"{gate.E1D_DIR}/covapie_covalent_residue_insertion_present_value_grammar_integrated_rule_matrix.csv",
        f"{gate.E1D_DIR}/covapie_covalent_residue_insertion_present_value_grammar_integrated_field_matrix.csv",
        f"{gate.E1D_DIR}/covapie_covalent_residue_insertion_present_value_grammar_integrated_context_matrix.csv",
        f"{gate.E1D_DIR}/covapie_covalent_residue_insertion_present_value_grammar_integration_safety_audit.csv",
        f"{gate.E1D_DIR}/covapie_covalent_residue_insertion_present_value_grammar_integration_issue_inventory.csv",
        f"{gate.E1D_DIR}/covapie_covalent_residue_insertion_present_value_grammar_integration_manifest.json",
    ]
    assert [spec.relative_path for spec in gate.SOURCE_SPECS[6:]] == [
        f"{gate.E1E1_DIR}/covapie_admit_004_generic_atom_identity_evidence_context_reconciliation_contract.csv",
        f"{gate.E1E1_DIR}/covapie_admit_004_generic_atom_identity_evidence_context_truth_matrix.csv",
        f"{gate.E1E1_DIR}/covapie_admit_004_generic_atom_identity_evidence_context_source_boundary_audit.csv",
        f"{gate.E1E1_DIR}/covapie_admit_004_generic_atom_identity_evidence_context_safety_audit.csv",
        f"{gate.E1E1_DIR}/covapie_admit_004_generic_atom_identity_evidence_context_issue_readiness_inventory.csv",
        f"{gate.E1E1_DIR}/covapie_admit_004_generic_atom_identity_evidence_context_reconciliation_design_manifest.json",
    ]
    assert all(len(spec.expected_sha256) == 64 for spec in gate.SOURCE_SPECS)


def test_all_structure_checks_precede_first_source_byte_read():
    events: list[str] = []
    source_bytes = {
        spec.relative_path: (REPO_ROOT / spec.relative_path).read_bytes()
        for spec in gate.SOURCE_SPECS
    }

    def structure_reader(_root, _base, spec):
        events.append(f"structure:{spec.relative_path}")
        return gate.SourceStructure(True, True, True, True)

    def filesystem_reader(_root, spec):
        events.append(f"filesystem:{spec.relative_path}")
        return source_bytes[spec.relative_path]

    def base_reader(_root, _base, spec):
        events.append(f"base:{spec.relative_path}")
        return source_bytes[spec.relative_path]

    frozen = gate.freeze_source_snapshots(
        REPO_ROOT,
        structure_reader=structure_reader,
        filesystem_reader=filesystem_reader,
        base_blob_reader=base_reader,
    )
    assert len(frozen) == 12
    assert all(event.startswith("structure:") for event in events[:12])
    assert all(not event.startswith("structure:") for event in events[12:])


@pytest.mark.parametrize(
    "rejected_structure",
    [
        gate.SourceStructure(True, True, False, False),
        gate.SourceStructure(True, True, True, False),
        gate.SourceStructure(False, True, True, True),
        gate.SourceStructure(True, False, True, True),
    ],
    ids=("missing", "symlink", "untracked", "base-tree-not-blob"),
)
def test_source_structure_failures_fail_closed_before_reads(rejected_structure):
    byte_reads: list[str] = []

    def structure_reader(_root, _base, spec):
        if spec == gate.SOURCE_SPECS[4]:
            return rejected_structure
        return gate.SourceStructure(True, True, True, True)

    def forbidden_reader(_root, spec):
        byte_reads.append(spec.relative_path)
        return b""

    def forbidden_base_reader(_root, _base, spec):
        byte_reads.append(spec.relative_path)
        return b""

    with pytest.raises(gate.IntegrationGateError) as exc_info:
        gate.freeze_source_snapshots(
            REPO_ROOT,
            structure_reader=structure_reader,
            filesystem_reader=forbidden_reader,
            base_blob_reader=forbidden_base_reader,
        )
    assert byte_reads == []
    assert exc_info.value.state["integrated_rule_count"] == 0
    assert exc_info.value.state["integrated_field_count"] == 0
    assert exc_info.value.state["integrated_context_count"] == 0
    assert exc_info.value.state["active_issue_count"] == 0
    assert exc_info.value.state["integration_readiness"] is False
    assert exc_info.value.state["all_checks_passed"] is False


@pytest.mark.parametrize("drift_side", ["filesystem", "base-tree"])
def test_source_hash_drift_fails_closed(drift_side):
    source_bytes = {
        spec.relative_path: (REPO_ROOT / spec.relative_path).read_bytes()
        for spec in gate.SOURCE_SPECS
    }
    target = gate.SOURCE_SPECS[2]

    def structure_reader(_root, _base, _spec):
        return gate.SourceStructure(True, True, True, True)

    def filesystem_reader(_root, spec):
        content = source_bytes[spec.relative_path]
        return content + b"drift" if drift_side == "filesystem" and spec == target else content

    def base_reader(_root, _base, spec):
        content = source_bytes[spec.relative_path]
        return content + b"drift" if drift_side == "base-tree" and spec == target else content

    with pytest.raises(gate.IntegrationGateError) as exc_info:
        gate.freeze_source_snapshots(
            REPO_ROOT,
            structure_reader=structure_reader,
            filesystem_reader=filesystem_reader,
            base_blob_reader=base_reader,
        )
    assert exc_info.value.state["integration_readiness"] is False
    assert exc_info.value.state["all_checks_passed"] is False


def test_exact12_snapshots_are_expected_base_filesystem_identical(snapshots):
    assert len(snapshots) == 12
    assert [snapshot.ordinal for snapshot in snapshots] == list(range(1, 13))
    assert all(
        snapshot.expected_sha256
        == snapshot.base_tree_sha256
        == snapshot.filesystem_sha256
        for snapshot in snapshots
    )
    assert all(snapshot.structure.passed for snapshot in snapshots)


def test_e1d_direct_predecessor_counts_and_readiness(predecessor_views):
    e1d, _e1e1 = predecessor_views
    assert len(e1d["rules"]) == 15
    assert len(e1d["fields"]) == 22
    assert len(e1d["contexts"]) == 18
    assert len(e1d["issues"]) == 9
    assert sum(row["semantics_complete"] == "true" for row in e1d["rules"]) == 7
    assert sum(
        row["implementation_semantics_complete"] == "true" for row in e1d["fields"]
    ) == 12
    assert sum(row["implementation_ready"] == "true" for row in e1d["contexts"]) == 9


def test_e1e1_direct_contract_truth_issue_and_readiness(predecessor_views):
    _e1d, e1e1 = predecessor_views
    assert len(e1e1["contract"]) == 28
    assert all(row["contract_passed"] == "true" for row in e1e1["contract"])
    assert len(e1e1["truth"]) == 36
    assert all(row["truth_passed"] == "true" for row in e1e1["truth"])
    assert len(e1e1["issues"]) == 10
    assert e1e1["issues"][-1]["issue_id"] == gate.RESOLVED_ISSUE_ID
    assert e1e1["manifest"]["ready_for_generic_atom_evidence_context_successor_integration"] is True
    assert e1e1["manifest"]["reconciled_admit_004_interface_implementation_ready"] is False


def test_rule_overlay_changes_only_admit_004(predecessor_views, outputs):
    e1d, _e1e1 = predecessor_views
    actual = _csv_rows(outputs[gate.RULE_OUTPUT])
    assert len(actual) == 15
    for before, after in zip(e1d["rules"], actual):
        if before["admission_rule_id"] != "ADMIT_004":
            assert after == before
    target = next(row for row in actual if row["admission_rule_id"] == "ADMIT_004")
    assert target["candidate_field_dependencies"] == gate.EXPECTED_CANDIDATE_DEPENDENCIES
    assert target["evaluation_context_dependencies"] == (
        "covalent_residue_identity_contract|covalent_residue_identity_evidence_context"
    )
    assert target["integration_source_stage"] == gate.E1E1_STAGE
    assert target["integration_applied"] == "true"
    assert target["integration_reason"] == gate.INTEGRATION_REASON


def test_field_overlay_changes_only_atom_contract(predecessor_views, outputs):
    e1d, _e1e1 = predecessor_views
    actual = _csv_rows(outputs[gate.FIELD_OUTPUT])
    assert len(actual) == 22
    for before, after in zip(e1d["fields"], actual):
        if before["field_name"] != "covalent_residue_atom_name":
            assert after == before
    target = next(row for row in actual if row["field_name"] == "covalent_residue_atom_name")
    assert target["source_value_contract"] == gate.ATOM_SOURCE_VALUE_CONTRACT
    assert target["candidate_record_field"] == "true"
    assert target["dependent_rules"] == "ADMIT_004|ADMIT_005"
    assert target["normalization_defined"] == "true"
    assert target["semantics_evidence"] == gate.E1E1_STAGE


def test_context_overlay_inserts_exact_row_and_preserves_original_18(predecessor_views, outputs):
    e1d, _e1e1 = predecessor_views
    actual = _csv_rows(outputs[gate.CONTEXT_OUTPUT])
    assert len(actual) == 19
    position = [row["context_item"] for row in actual].index(gate.EVIDENCE_CONTEXT_ITEM)
    assert actual[position - 1]["context_item"] == "covalent_residue_identity_contract"
    assert actual[:position] + actual[position + 1 :] == e1d["contexts"]
    assert actual[position] == {
        "context_item": gate.EVIDENCE_CONTEXT_ITEM,
        "context_scope": "evaluation_record_evidence",
        "required_by_rules": "ADMIT_004",
        "provided_by_future_caller": "true",
        "filesystem_access_inside_evaluator": "false",
        "network_access_inside_evaluator": "false",
        "deterministic_now": "true",
        "deterministic_after_contract_freeze": "true",
        "exact_contract_defined": "true",
        "implementation_ready": "true",
        "blocking_reasons": "",
        "source_stage": gate.E1E1_STAGE,
        "integration_source_stage": gate.E1E1_STAGE,
        "integration_applied": "true",
        "integration_reason": gate.INTEGRATION_REASON,
    }


def test_issue_overlay_removes_only_reconciliation_issue_and_preserves_provider(predecessor_views, outputs):
    e1d, e1e1 = predecessor_views
    actual = _csv_rows(outputs[gate.ISSUE_OUTPUT])
    assert actual == e1d["issues"] == e1e1["issues"][:9]
    assert gate.RESOLVED_ISSUE_ID not in [row["issue_id"] for row in actual]
    provider = next(row for row in actual if row["issue_id"] == gate.PROVIDER_ISSUE_ID)
    assert (provider["status"], provider["severity"], provider["issue_count"]) == (
        "open",
        "blocking",
        "11",
    )


def test_safety_audit_has_exact_executed_and_unexecuted_rows(outputs):
    actual = _csv_rows(outputs[gate.SAFETY_OUTPUT])
    assert len(actual) == 25
    assert [row["safety_item"] for row in actual] == list(
        gate.SAFETY_EXECUTED + gate.SAFETY_NOT_EXECUTED
    )
    assert all(row["safety_passed"] == "true" for row in actual)
    assert all(row["observed_executed"] == "true" for row in actual[:8])
    assert all(row["observed_executed"] == "false" for row in actual[8:])


def test_manifest_counts_exact11_and_non_overclaim(outputs):
    manifest = json.loads(outputs[gate.MANIFEST_OUTPUT])
    assert (
        manifest["integrated_rule_count"],
        manifest["integrated_field_count"],
        manifest["integrated_context_count"],
        manifest["active_issue_count"],
    ) == (15, 22, 19, 9)
    assert (
        manifest["semantics_complete_rule_count"],
        manifest["implementation_semantics_complete_field_count"],
        manifest["implementation_ready_context_count"],
    ) == (7, 12, 10)
    assert manifest["exact11_count"] == 11
    assert manifest["exact11_insertion_unknown_count"] == 11
    assert manifest["exact11_insertion_value_empty_count"] == 11
    assert manifest["exact11_effective_blocked_count"] == 11
    assert manifest["exact11_passed_count"] == 0
    assert manifest["exact11_reason"] == gate.EXACT11_REASON
    assert manifest["provider_blocking_issue_count"] == 11
    assert manifest["reconciled_admit_004_interface_implementation_ready"] is True
    assert manifest["admit_004_evaluator_implemented"] is False
    assert manifest["ready_for_real_candidate_evaluation"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert gate.MANIFEST_OUTPUT not in manifest["output_sha256"]
    assert not any(key in manifest for key in ("timestamp", "hostname", "host"))


def test_double_build_is_byte_identical(outputs):
    assert gate.build_output_bytes() == outputs


def test_double_materialization_is_byte_identical_and_exact_six(tmp_path):
    destination = tmp_path / "outputs"
    first_hashes = gate.materialize(destination)
    first_bytes = {path.name: path.read_bytes() for path in destination.iterdir()}
    second_hashes = gate.materialize(destination)
    second_bytes = {path.name: path.read_bytes() for path in destination.iterdir()}
    assert first_hashes == second_hashes
    assert first_bytes == second_bytes
    assert set(first_bytes) == set(gate.OUTPUT_FILENAMES)
    assert gate.validate_output_directory(destination) == first_hashes


def test_materialize_rejects_symlink_and_nonregular_outputs_before_any_write(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_sentinel = outside / "sentinel.bin"
    outside_sentinel.write_bytes(b"ROOT-SYMLINK-SENTINEL")
    linked_root = tmp_path / "linked-output-root"
    linked_root.symlink_to(outside, target_is_directory=True)
    with pytest.raises(gate.IntegrationGateError):
        gate.materialize(linked_root)
    assert {path.name: path.read_bytes() for path in outside.iterdir()} == {
        "sentinel.bin": b"ROOT-SYMLINK-SENTINEL"
    }

    symlink_destination = tmp_path / "symlink-output"
    symlink_destination.mkdir()
    victim = tmp_path / "victim.bin"
    victim_bytes = b"OUTPUT-SYMLINK-VICTIM"
    victim.write_bytes(victim_bytes)
    (symlink_destination / gate.RULE_OUTPUT).symlink_to(victim)
    other_before = {}
    for index, name in enumerate(gate.OUTPUT_FILENAMES[1:], start=1):
        content = f"UNCHANGED-{index}".encode("ascii")
        (symlink_destination / name).write_bytes(content)
        other_before[name] = content
    with pytest.raises(gate.IntegrationGateError):
        gate.materialize(symlink_destination)
    assert victim.read_bytes() == victim_bytes
    assert {
        name: (symlink_destination / name).read_bytes() for name in other_before
    } == other_before

    directory_destination = tmp_path / "directory-output"
    directory_destination.mkdir()
    (directory_destination / gate.RULE_OUTPUT).mkdir()
    directory_other_before = {}
    for index, name in enumerate(gate.OUTPUT_FILENAMES[1:], start=1):
        content = f"DIRECTORY-UNCHANGED-{index}".encode("ascii")
        (directory_destination / name).write_bytes(content)
        directory_other_before[name] = content
    with pytest.raises(gate.IntegrationGateError):
        gate.materialize(directory_destination)
    assert (directory_destination / gate.RULE_OUTPUT).is_dir()
    assert {
        name: (directory_destination / name).read_bytes()
        for name in directory_other_before
    } == directory_other_before

    regular_destination = tmp_path / "regular-output"
    first_hashes = gate.materialize(regular_destination)
    first_bytes = {
        name: (regular_destination / name).read_bytes()
        for name in gate.OUTPUT_FILENAMES
    }
    second_hashes = gate.materialize(regular_destination)
    second_bytes = {
        name: (regular_destination / name).read_bytes()
        for name in gate.OUTPUT_FILENAMES
    }
    assert second_hashes == first_hashes
    assert second_bytes == first_bytes
    assert not any(
        path.name.endswith((".tmp", ".part"))
        for path in regular_destination.iterdir()
    )


@pytest.mark.parametrize("failure_kind", ["missing", "extra", "symlink", "hash", "overclaim"])
def test_output_missing_extra_symlink_hash_and_manifest_overclaim_fail_closed(tmp_path, failure_kind):
    destination = tmp_path / "outputs"
    gate.materialize(destination)
    if failure_kind == "missing":
        (destination / gate.RULE_OUTPUT).unlink()
    elif failure_kind == "extra":
        (destination / "extra.csv").write_text("extra\n", encoding="utf-8")
    elif failure_kind == "symlink":
        target = destination / gate.RULE_OUTPUT
        target.unlink()
        os.symlink(gate.FIELD_OUTPUT, target)
    elif failure_kind == "hash":
        with (destination / gate.FIELD_OUTPUT).open("ab") as stream:
            stream.write(b"drift")
    else:
        path = destination / gate.MANIFEST_OUTPUT
        manifest = json.loads(path.read_bytes())
        manifest["ready_for_bulk_download_now"] = True
        path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    with pytest.raises(gate.IntegrationGateError) as exc_info:
        gate.validate_output_directory(destination)
    assert exc_info.value.state["integration_readiness"] is False
    assert exc_info.value.state["all_checks_passed"] is False


def test_production_and_checker_use_standard_library_only_and_no_evaluator():
    production_path = Path(gate.__file__)
    checker_path = REPO_ROOT / "scripts" / (
        "check_covapie_bulk_download_admission_admit_004_generic_atom_identity_"
        "evidence_context_reconciliation_integration_gate_v1.py"
    )
    allowed_roots = {
        "__future__",
        "ast",
        "csv",
        "covalent_ext",
        "dataclasses",
        "hashlib",
        "io",
        "json",
        "os",
        "pathlib",
        "stat",
        "subprocess",
        "sys",
        "tempfile",
        "typing",
    }
    for path in (production_path, checker_path):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module.split(".")[0])
        assert set(imports) <= allowed_roots
    assert not hasattr(gate, "evaluate_admit_004")
    assert all("data/raw" not in spec.relative_path for spec in gate.SOURCE_SPECS)


def test_production_and_checker_import_smoke_have_no_output(capsys):
    importlib.reload(gate)
    checker_path = REPO_ROOT / "scripts" / (
        "check_covapie_bulk_download_admission_admit_004_generic_atom_identity_"
        "evidence_context_reconciliation_integration_gate_v1.py"
    )
    spec = importlib.util.spec_from_file_location("step14au_e1_e2_checker", checker_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_gate_cli_materialization_is_not_triggered_by_import(tmp_path):
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(SRC_ROOT)!r}); "
        "import covalent_ext.covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_integration_gate"
    )
    result = subprocess.run(
        (sys.executable, "-c", code),
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert list(tmp_path.iterdir()) == []
