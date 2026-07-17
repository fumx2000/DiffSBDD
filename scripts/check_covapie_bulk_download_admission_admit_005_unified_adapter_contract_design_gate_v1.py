#!/usr/bin/env python3
"""Fail-closed checker for the ADMIT_005 unified-adapter design contract."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import fields, replace
from pathlib import Path
from unittest.mock import patch

from covalent_ext import (
    covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate
    as semantic_oracle,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_005_rule_logic_interface as standalone,
)


EXPECTED_OUTPUT_SHA256 = {
    "covapie_admit_005_candidate_projection_and_context_routing_matrix.csv": "068646896408f9d7640a9e00b361711986bfa8afe3ffde4e756904826fdf1473",
    "covapie_admit_005_unified_adapter_contract.csv": "8525964731d5a478bc523fdcec2bd25d7c20d535344005f3074b91c86351075d",
    "covapie_admit_005_unified_adapter_contract_manifest.json": "b66f6551cb2aad3ac4b78afd5f0c41475697f5276af8fb7150f365a6e0adf269",
    "covapie_admit_005_unified_adapter_issue_readiness_inventory.csv": "27bed0fd2250e0c64c704771fdb2bca8f5e50554d99f53694dc579f85f578d1f",
    "covapie_admit_005_unified_adapter_safety_audit.csv": "7d8d7d75046fb49d28b4fcb74aab2d0e8a6b1853a6c73f8420617b2c02cf8265",
    "covapie_admit_005_unified_result_projection_truth_matrix.csv": "ceb9c5ec22b4d9819c80e4813f9c5f240c4c9e98a5dd428e61082eeb1d887946",
}


def _live_source_values(source: object) -> dict[str, object]:
    return {name: getattr(source, name) for name in gate.STANDALONE_RESULT_FIELDS}


def _to_design_source(source: object) -> gate.Admit005EvaluationDesignRecord:
    return gate.Admit005EvaluationDesignRecord(**_live_source_values(source))


def _derive_oracle_design(
    residue: object,
    atom_name: object,
    *,
    scope_classifier: object = semantic_oracle.classify_admit_004_admit_005_atom_scope_design,
    atom_validator: object = semantic_oracle.validate_generic_covalent_residue_atom_name,
) -> gate.Admit005EvaluationDesignRecord:
    scope = scope_classifier(residue, atom_name)  # type: ignore[operator]
    atom = atom_validator(atom_name)  # type: ignore[operator]
    if scope.canonical_residue_name is None:
        canonical_residue = canonical_atom = ""
        validated: tuple[tuple[str, str], ...] = ()
    elif not atom.valid:
        canonical_residue = scope.canonical_residue_name
        canonical_atom = ""
        validated = (("covalent_residue_name", canonical_residue),)
    else:
        canonical_residue = scope.canonical_residue_name
        canonical_atom = atom.canonical_value
        validated = (
            ("covalent_residue_name", canonical_residue),
            ("covalent_residue_atom_name", canonical_atom),
        )
    return gate.Admit005EvaluationDesignRecord(
        admission_rule_id="ADMIT_005",
        outcome=scope.admit_005_outcome,
        passed=scope.admit_005_outcome == "passed",
        blocks_candidate=scope.admit_005_outcome != "passed",
        reason=scope.reason,
        canonical_residue_name=canonical_residue,
        canonical_residue_atom_name=canonical_atom,
        validated_candidate_fields=validated,
        consumed_candidate_fields=gate.CANDIDATE_FIELDS,
        evaluator_io_used=False,
    )


def _unsafe_live_source(**overrides: object) -> standalone.Admit005EvaluationResult:
    baseline = standalone.evaluate_admit_005("CYS", "SG")
    values = _live_source_values(baseline)
    values.update(overrides)
    result = object.__new__(standalone.Admit005EvaluationResult)
    for name, value in values.items():
        object.__setattr__(result, name, value)
    return result
from covalent_ext import (
    covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate
    as gate,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004
    as phase4,
)


def _must_raise(expected: type[BaseException], function: object, *args: object) -> BaseException:
    try:
        function(*args)  # type: ignore[operator]
    except expected as error:
        return error
    raise AssertionError(f"{expected.__name__} was not raised")


def _verify_materialized(
    root: Path, expected_payloads: dict[str, bytes], expected_manifest: dict[str, object]
) -> None:
    entries = tuple(sorted(entry.name for entry in root.iterdir()))
    assert entries == tuple(sorted(gate.OUTPUT_FILES))
    for name in gate.OUTPUT_FILES:
        path = root / name
        assert path.is_file() and not path.is_symlink()
        assert path.read_bytes() == expected_payloads[name]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == EXPECTED_OUTPUT_SHA256[name]
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest == expected_manifest
    assert manifest["all_checks_passed"] is True
    assert manifest["admit_005_unified_adapter_implemented"] is False
    assert manifest["admit_005_registered_in_engine"] is False
    assert manifest["phase4_runtime_modified"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    for name, digest in manifest["output_sha256"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest


def _fake_git(arguments: object, _root: Path, *, text: bool = False) -> subprocess.CompletedProcess[object]:
    args = tuple(arguments)  # type: ignore[arg-type]
    if args[:2] == ("cat-file", "-t"):
        return subprocess.CompletedProcess(args, 0, "blob\n" if text else b"blob\n", "" if text else b"")
    return subprocess.CompletedProcess(args, 0, "" if text else b"", "" if text else b"")


def _check_source_negative_paths(snapshot: gate.FrozenSourceSnapshot) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with patch.object(gate, "_git", side_effect=_fake_git):
            error = _must_raise(ValueError, gate._structural_source_check, Path("missing.csv"), root)
            assert "missing" in str(error)
            victim = root / "victim.txt"
            victim.write_text("unchanged", encoding="utf-8")
            link = root / "source.csv"
            link.symlink_to(victim)
            error = _must_raise(ValueError, gate._structural_source_check, Path("source.csv"), root)
            assert "regular non-symlink" in str(error)
            assert victim.read_text(encoding="utf-8") == "unchanged"

    bad_record = replace(snapshot.records[0], content=snapshot.records[0].content + b"tamper")
    bad_snapshot = gate.FrozenSourceSnapshot((bad_record, *snapshot.records[1:]))
    assert gate.validate_frozen_source_snapshot(bad_snapshot) is False

    structure_calls: list[Path] = []
    byte_reads: list[Path] = []

    def structural(path: Path, _root: Path) -> None:
        structure_calls.append(path)
        if len(structure_calls) == len(gate.SOURCE_PATHS):
            raise ValueError("deterministic final structural failure")

    def byte_read(path: Path) -> bytes:
        byte_reads.append(path)
        return b""

    with (
        patch.object(gate, "_validate_expected_base_lineage", return_value=None),
        patch.object(gate, "_structural_source_check", side_effect=structural),
        patch.object(Path, "read_bytes", byte_read),
    ):
        error = _must_raise(ValueError, gate.build_frozen_source_snapshot, gate.REPO_ROOT)
    assert str(error) == "deterministic final structural failure"
    assert tuple(structure_calls) == gate.SOURCE_PATHS
    assert byte_reads == []

    responses = iter(
        (
            subprocess.CompletedProcess((), 0, b"", b""),
            subprocess.CompletedProcess((), 0, gate.EXPECTED_BASE_SUBJECT + "\n", ""),
            subprocess.CompletedProcess((), 0, b"", b""),
            subprocess.CompletedProcess((), 1, b"", b""),
        )
    )
    with patch.object(gate, "_git", side_effect=lambda *_args, **_kwargs: next(responses)):
        error = _must_raise(
            ValueError,
            gate._validate_expected_base_lineage,
            gate.REPO_ROOT,
            "deterministic-non-descendant",
        )
    assert "not an ancestor" in str(error)


def _check_output_negative_paths(
    expected_payloads: dict[str, bytes], expected_manifest: dict[str, object]
) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "out"
        gate.run_covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1(root)
        (root / gate.CONTRACT_FILENAME).unlink()
        _must_raise(AssertionError, _verify_materialized, root, expected_payloads, expected_manifest)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "out"
        gate.run_covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1(root)
        (root / "unexpected.txt").write_text("extra", encoding="utf-8")
        _must_raise(AssertionError, _verify_materialized, root, expected_payloads, expected_manifest)
        _must_raise(
            ValueError,
            gate.run_covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1,
            root,
        )

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "out"
        gate.run_covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1(root)
        (root / gate.TRUTH_FILENAME).write_bytes(b"tamper\n")
        _must_raise(AssertionError, _verify_materialized, root, expected_payloads, expected_manifest)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "out"
        gate.run_covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1(root)
        path = root / gate.MANIFEST_FILENAME
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["admit_005_unified_adapter_implemented"] = True
        path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
        _must_raise(AssertionError, _verify_materialized, root, expected_payloads, expected_manifest)

    with tempfile.TemporaryDirectory() as temporary:
        parent = Path(temporary)
        root = parent / "out"
        root.mkdir()
        victim = parent / "victim.txt"
        victim.write_text("unchanged", encoding="utf-8")
        (root / gate.CONTRACT_FILENAME).symlink_to(victim)
        _must_raise(
            ValueError,
            gate.run_covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1,
            root,
        )
        assert victim.read_text(encoding="utf-8") == "unchanged"


def main() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert all(
        record.expected_sha256
        == record.base_tree_sha256
        == record.filesystem_sha256
        == gate.SOURCE_SHA256[record.relative_path]
        for record in snapshot.records
    )
    _check_source_negative_paths(snapshot)

    state = gate.build_design_state(snapshot)
    assert state["all_checks_passed"] is True
    assert len(state["contract_rows"]) == 46
    assert len(state["routing_rows"]) == 13
    assert len(state["truth_rows"]) == 43
    assert len(state["safety_rows"]) == 30
    assert gate.TRUTH_GROUP_COUNTS == {
        "candidate_envelope": 7,
        "context_routing": 5,
        "standalone_exact22": 22,
        "source_fail_closed": 7,
        "boundary": 2,
    }
    assert len(state["issue_rows"]) == 11
    assert sum(row["issue_id"] == "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT" for row in state["issue_rows"]) == 1
    assert tuple(phase4.EVALUATOR_REGISTRY) == ("ADMIT_001", "ADMIT_002", "ADMIT_003", "ADMIT_004")
    assert phase4.UnifiedAdmissionRuleEvaluation is phase4.phase2.UnifiedAdmissionRuleEvaluation
    assert phase4.UnifiedAdmissionDispatchError is phase4.phase2.UnifiedAdmissionDispatchError
    assert tuple(field.name for field in fields(phase4.UnifiedAdmissionRuleEvaluation)) == gate.RESULT_FIELDS
    assert tuple(field.name for field in fields(phase4.UnifiedAdmissionDispatchError)) == gate.DISPATCH_ERROR_FIELDS

    production_path = gate.REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate.py"
    production_tree = ast.parse(production_path.read_text(encoding="utf-8"), production_path.as_posix())
    production_roots = {
        alias.name.split(".")[0]
        for node in ast.walk(production_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(production_tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert production_roots <= (set(sys.stdlib_module_names) | {"__future__"})
    assert "covalent_ext" not in production_roots

    import_code = """
import sys
import covalent_ext.covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate
for stem in (
    'covapie_bulk_download_admission_admit_005_rule_logic_interface',
    'covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004',
    'covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate',
):
    assert not any(name.rsplit('.', 1)[-1] == stem for name in sys.modules)
"""
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(gate.REPO_ROOT / "src")
    import_result = subprocess.run(
        [sys.executable, "-c", import_code],
        cwd=gate.REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert import_result.returncode == 0
    assert import_result.stdout == import_result.stderr == ""

    class _StringSubclass(str):
        pass

    exact22 = (
        ("CYS", "SG"), ("cys", "SG"), ("CYS", "CA"), ("CYS", "sg"),
        ("CYS", "A.B"), ("SER", "SG"), ("SER", "CA"), ("CYX", "SG"),
        (7, "SG"), (_StringSubclass("CYS"), "SG"), ("", "SG"), ("CÝS", "SG"),
        ("C-Y", "SG"), ("CYS", 7), ("CYS", _StringSubclass("SG")), ("CYS", ""),
        ("CYS", "SĠ"), ("CYS", "S G"), ("CYS", "S\tG"), ("CYS", "."),
        ("CYS", "?"), ("C-Y", "?"),
    )
    for residue_value, atom_value in exact22:
        live_source = standalone.evaluate_admit_005(residue_value, atom_value)
        assert type(live_source) is standalone.Admit005EvaluationResult
        source_design = _to_design_source(live_source)
        assert gate.validate_source_shape_and_invariants_for_design(source_design).accepted
        oracle_design = _derive_oracle_design(residue_value, atom_value)
        assert gate.validate_source_oracle_equivalence_for_design(source_design, oracle_design).accepted
        projection = gate.project_exact10_to_exact13_for_design(source_design)
        assert projection.outcome == live_source.outcome
        assert projection.validated_candidate_fields == live_source.validated_candidate_fields

    residue = "".join(("c", "y", "s"))
    atom = "".join(("S", "G"))
    scope_seen: list[tuple[object, object]] = []
    atom_seen: list[object] = []

    def scope_spy(left: object, right: object) -> object:
        scope_seen.append((left, right))
        return semantic_oracle.classify_admit_004_admit_005_atom_scope_design(left, right)

    def atom_spy(value: object) -> object:
        atom_seen.append(value)
        return semantic_oracle.validate_generic_covalent_residue_atom_name(value)

    source = _to_design_source(standalone.evaluate_admit_005(residue, atom))
    assert gate.validate_source_shape_and_invariants_for_design(source).accepted
    oracle = _derive_oracle_design(
        residue, atom, scope_classifier=scope_spy, atom_validator=atom_spy
    )
    assert source == oracle
    assert scope_seen == [(residue, atom)] and atom_seen == [atom]
    assert scope_seen[0][0] is residue and scope_seen[0][1] is atom and atom_seen[0] is atom
    projected = gate.project_exact10_to_exact13_for_design(source)
    assert projected.outcome == source.outcome
    assert projected.normalized_values == source.validated_candidate_fields
    assert projected.validated_candidate_fields == source.validated_candidate_fields
    rejected = _to_design_source(standalone.evaluate_admit_005("SER", "CA"))
    rejected_projection = gate.project_exact10_to_exact13_for_design(rejected)
    assert rejected_projection.outcome == "rejected"
    assert rejected_projection.validated_candidate_fields == rejected.validated_candidate_fields

    class _SourceSubclass(standalone.Admit005EvaluationResult):
        pass

    valid_live = standalone.evaluate_admit_005("CYS", "SG")
    prevalidation_failures: tuple[object, ...] = (
        object(),
        _SourceSubclass(**_live_source_values(valid_live)),
        _unsafe_live_source(admission_rule_id="ADMIT_004"),
        _unsafe_live_source(passed=False),
        _unsafe_live_source(evaluator_io_used=True),
        _unsafe_live_source(consumed_candidate_fields=("covalent_residue_name",)),
    )
    failure_scope_calls: list[tuple[object, object]] = []
    failure_atom_calls: list[object] = []
    for failure_source in prevalidation_failures:
        design_input: object = (
            _to_design_source(failure_source)
            if type(failure_source) is standalone.Admit005EvaluationResult
            else failure_source
        )
        decision = gate.validate_source_shape_and_invariants_for_design(design_input)
        assert not decision.accepted
        assert decision.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
        assert decision.adapter_ready is False
    assert failure_scope_calls == [] and failure_atom_calls == []

    mismatch_scope_calls: list[tuple[object, object]] = []
    mismatch_atom_calls: list[object] = []

    def mismatch_scope(left: object, right: object) -> object:
        mismatch_scope_calls.append((left, right))
        return semantic_oracle.classify_admit_004_admit_005_atom_scope_design(left, right)

    def mismatch_atom(value: object) -> object:
        mismatch_atom_calls.append(value)
        return semantic_oracle.validate_generic_covalent_residue_atom_name(value)

    mismatch_source = _to_design_source(valid_live)
    assert gate.validate_source_shape_and_invariants_for_design(mismatch_source).accepted
    mismatch_oracle = _derive_oracle_design(
        "SER", "CA", scope_classifier=mismatch_scope, atom_validator=mismatch_atom
    )
    mismatch_decision = gate.validate_source_oracle_equivalence_for_design(
        mismatch_source, mismatch_oracle
    )
    assert not mismatch_decision.accepted
    assert mismatch_scope_calls == [("SER", "CA")]
    assert mismatch_atom_calls == ["CA"]

    payloads, manifest = gate._payloads(state)
    actual_root = gate.REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    _verify_materialized(actual_root, payloads, manifest)
    with (actual_root / gate.TRUTH_FILENAME).open(encoding="utf-8", newline="") as handle:
        truth_failures = {
            row["case_id"]: row
            for row in csv.DictReader(handle)
            if row["case_group"] == "source_fail_closed"
        }
    for case_id in (
        "D_WRONG_TYPE",
        "D_SUBCLASS",
        "D_RULE_ID",
        "D_FIELD_INVARIANT",
        "D_IO_TRUE",
        "D_CONSUMED_FIELDS",
    ):
        assert (
            truth_failures[case_id]["formal_call_count"],
            truth_failures[case_id]["scope_oracle_call_count"],
            truth_failures[case_id]["atom_oracle_call_count"],
        ) == ("1", "0", "0")
    assert (
        truth_failures["D_ORACLE_MISMATCH"]["formal_call_count"],
        truth_failures["D_ORACLE_MISMATCH"]["scope_oracle_call_count"],
        truth_failures["D_ORACLE_MISMATCH"]["atom_oracle_call_count"],
    ) == ("1", "1", "1")

    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        first_root = Path(first) / "out"
        second_root = Path(second) / "out"
        gate.run_covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1(first_root)
        gate.run_covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1(second_root)
        first_bytes = {name: (first_root / name).read_bytes() for name in gate.OUTPUT_FILES}
        second_bytes = {name: (second_root / name).read_bytes() for name in gate.OUTPUT_FILES}
        assert first_bytes == second_bytes == payloads

    _check_output_negative_paths(payloads, manifest)
    assert not tuple(actual_root.glob("*.tmp"))
    assert not tuple(actual_root.glob("*.part"))

    output_sha256 = {
        name: hashlib.sha256((actual_root / name).read_bytes()).hexdigest()
        for name in gate.OUTPUT_FILES
    }
    assert output_sha256 == EXPECTED_OUTPUT_SHA256
    assert manifest["all_checks_passed"] is True
    assert manifest["production_standard_library_only"] is True
    assert manifest["production_project_module_imports"] is False
    assert manifest["predecessor_modules_not_imported_or_executed_by_production"] is True
    assert manifest["source_prevalidation_precedes_oracle"] is True
    assert manifest["source_type_failure_oracle_calls"] == 0
    assert manifest["source_invariant_failure_oracle_calls"] == 0
    assert manifest["oracle_mismatch_scope_oracle_calls"] == 1
    assert manifest["oracle_mismatch_atom_oracle_calls"] == 1
    assert manifest["output_sha256_frozen_by_checker"] is True
    assert manifest["ready_for_admit_005_unified_adapter_implementation"] is True
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False

    print(f"source_count={len(snapshot.records)}")
    print(f"contract_rows={len(state['contract_rows'])}")
    print(f"routing_rows={len(state['routing_rows'])}")
    print(f"truth_rows={len(state['truth_rows'])}")
    print(f"safety_rows={len(state['safety_rows'])}")
    print(f"truth_group_counts={json.dumps(gate.TRUTH_GROUP_COUNTS, sort_keys=True)}")
    print(f"issue_rows={len(state['issue_rows'])}")
    print(f"output_sha256={json.dumps(output_sha256, sort_keys=True)}")
    print("source_prevalidation_before_oracle=true")
    print("source_prevalidation_failures_oracle_calls=0/0")
    print("oracle_mismatch_oracle_calls=1/1")
    print("frozen_output_sha=6/6")
    print("ready_for_admit_005_unified_adapter_implementation=true")
    print("ready_for_bulk_download_now=false")
    print("ready_for_training=false")
    print("all_checks_passed=true")


if __name__ == "__main__":
    main()
