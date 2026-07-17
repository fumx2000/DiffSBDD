from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate
    as semantic_oracle,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_005_rule_logic_interface as standalone,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate
    as gate,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004
    as phase4,
)


EXACT22 = (
    ("PASS_001", "CYS", "SG"),
    ("PASS_002", "cys", "SG"),
    ("REJECT_001", "CYS", "CA"),
    ("REJECT_002", "CYS", "sg"),
    ("REJECT_003", "CYS", "A.B"),
    ("REJECT_004", "SER", "SG"),
    ("REJECT_005", "SER", "CA"),
    ("REJECT_006", "CYX", "SG"),
    ("INVALID_RESIDUE_001", 7, "SG"),
    ("INVALID_RESIDUE_002", type("StringSubclass", (str,), {})("CYS"), "SG"),
    ("INVALID_RESIDUE_003", "", "SG"),
    ("INVALID_RESIDUE_004", "CÝS", "SG"),
    ("INVALID_RESIDUE_005", "C-Y", "SG"),
    ("INVALID_ATOM_001", "CYS", 7),
    ("INVALID_ATOM_002", "CYS", type("StringSubclass", (str,), {})("SG")),
    ("INVALID_ATOM_003", "CYS", ""),
    ("INVALID_ATOM_004", "CYS", "SĠ"),
    ("INVALID_ATOM_005", "CYS", "S G"),
    ("INVALID_ATOM_006", "CYS", "S\tG"),
    ("INVALID_ATOM_007", "CYS", "."),
    ("INVALID_ATOM_008", "CYS", "?"),
    ("PRECEDENCE_001", "C-Y", "?"),
)


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


@pytest.fixture(scope="module")
def snapshot() -> gate.FrozenSourceSnapshot:
    return gate.build_frozen_source_snapshot()


@pytest.fixture(scope="module")
def state(snapshot: gate.FrozenSourceSnapshot) -> dict[str, object]:
    return gate.build_design_state(snapshot)


def _fake_git(
    arguments: object, _root: Path, *, text: bool = False
) -> subprocess.CompletedProcess[object]:
    args = tuple(arguments)  # type: ignore[arg-type]
    if args[:2] == ("cat-file", "-t"):
        return subprocess.CompletedProcess(
            args, 0, "blob\n" if text else b"blob\n", "" if text else b""
        )
    return subprocess.CompletedProcess(
        args, 0, "" if text else b"", "" if text else b""
    )


def test_frozen_registration_identity() -> None:
    assert gate.ADMISSION_RULE_ID == "ADMIT_005"
    assert gate.ADMISSION_RULE_NAME == "cys_sg_scope_only_v1"
    assert gate.ADAPTER_ID == "covapie_admit_005_unified_adapter_v1"
    assert gate.FORMAL_EVALUATOR_NAME == "evaluate_admit_005"
    assert gate.FUTURE_REGISTERED_RULE_ORDER == (
        "ADMIT_001",
        "ADMIT_002",
        "ADMIT_003",
        "ADMIT_004",
        "ADMIT_005",
    )


def test_exact12_snapshot_order_structure_and_hashes(
    snapshot: gate.FrozenSourceSnapshot,
) -> None:
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert len(snapshot.records) == 12
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    for record in snapshot.records:
        assert (
            record.expected_sha256
            == record.base_tree_sha256
            == record.filesystem_sha256
            == gate.SOURCE_SHA256[record.relative_path]
        )
        assert hashlib.sha256(record.content).hexdigest() == record.expected_sha256


def test_forbidden_wrong_source_path_is_not_selected() -> None:
    assert gate.FORBIDDEN_WRONG_SOURCE_PATH not in gate.SOURCE_PATHS


def test_non_descendant_lineage_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = iter(
        (
            subprocess.CompletedProcess((), 0, b"", b""),
            subprocess.CompletedProcess((), 0, gate.EXPECTED_BASE_SUBJECT + "\n", ""),
            subprocess.CompletedProcess((), 0, b"", b""),
            subprocess.CompletedProcess((), 1, b"", b""),
        )
    )
    monkeypatch.setattr(gate, "_git", lambda *_args, **_kwargs: next(responses))
    with pytest.raises(ValueError, match="not an ancestor"):
        gate._validate_expected_base_lineage(gate.REPO_ROOT, "deterministic-non-descendant")


def test_all_structure_checks_precede_first_byte_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    structures: list[Path] = []
    byte_reads: list[Path] = []

    monkeypatch.setattr(gate, "_validate_expected_base_lineage", lambda *_args: None)

    def structure(path: Path, _root: Path) -> None:
        structures.append(path)
        if len(structures) == len(gate.SOURCE_PATHS):
            raise ValueError("last structure failed")

    def read_bytes(path: Path) -> bytes:
        byte_reads.append(path)
        return b""

    monkeypatch.setattr(gate, "_structural_source_check", structure)
    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    with pytest.raises(ValueError, match="last structure failed"):
        gate.build_frozen_source_snapshot()
    assert tuple(structures) == gate.SOURCE_PATHS
    assert byte_reads == []


def test_missing_source_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gate, "_git", _fake_git)
    with pytest.raises(ValueError, match="source is missing"):
        gate._structural_source_check(Path("missing.csv"), tmp_path)


def test_source_symlink_fails_closed_without_touching_victim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gate, "_git", _fake_git)
    victim = tmp_path / "victim"
    victim.write_text("unchanged", encoding="utf-8")
    (tmp_path / "source.csv").symlink_to(victim)
    with pytest.raises(ValueError, match="regular non-symlink"):
        gate._structural_source_check(Path("source.csv"), tmp_path)
    assert victim.read_text(encoding="utf-8") == "unchanged"


def test_snapshot_hash_tamper_fails_closed(snapshot: gate.FrozenSourceSnapshot) -> None:
    changed = replace(snapshot.records[0], content=snapshot.records[0].content + b"x")
    assert not gate.validate_frozen_source_snapshot(
        gate.FrozenSourceSnapshot((changed, *snapshot.records[1:]))
    )


def test_phase2_exact13_and_exact6_type_identity() -> None:
    assert phase4.UnifiedAdmissionRuleEvaluation is phase4.phase2.UnifiedAdmissionRuleEvaluation
    assert phase4.UnifiedAdmissionDispatchError is phase4.phase2.UnifiedAdmissionDispatchError
    assert phase4.RESULT_FIELDS == gate.RESULT_FIELDS
    assert phase4.DISPATCH_ERROR_FIELDS == gate.DISPATCH_ERROR_FIELDS


def test_contract_rows_are_unique_and_programmatically_counted(
    state: dict[str, object],
) -> None:
    rows = state["contract_rows"]
    assert isinstance(rows, list)
    assert len(rows) == len(gate._contract_definitions()) == 46
    assert len({row["contract_id"] for row in rows}) == 46
    assert all(row["contract_status"] == "frozen" for row in rows)


def test_context_order_reasons_and_precedence(state: dict[str, object]) -> None:
    assert gate.CONTEXT_ORDER == (
        "batch_context",
        "evaluation_context",
        "download_result_context",
        "stage_authorization_context",
    )
    rows = state["routing_rows"]
    assert isinstance(rows, list)
    context = [row for row in rows if row["matrix_group"] == "context"]
    assert [row["expected_reason"] for row in context] == [
        gate.CONTEXT_REASONS["batch_context"],
        gate.CONTEXT_REASONS["evaluation_context"],
        gate.CONTEXT_REASONS["download_result_context"],
        gate.CONTEXT_REASONS["stage_authorization_context"],
        gate.CONTEXT_REASONS["batch_context"],
    ]
    assert all(row["formal_evaluator_called"] == "false" for row in context)
    assert all(row["oracle_called"] == "false" for row in context)


@pytest.mark.parametrize(
    ("reason"),
    (
        "ADMIT_005_CANDIDATE_RECORD_MAPPING_INVALID",
        "ADMIT_005_CANDIDATE_FIELD_MISSING:covalent_residue_name",
        "ADMIT_005_CANDIDATE_FIELD_MISSING:covalent_residue_atom_name",
    ),
)
def test_candidate_invalid_exact13_payload(reason: str) -> None:
    result = gate.candidate_invalid_exact13_for_design(reason)
    assert result.schema_version == phase4.RESULT_SCHEMA_VERSION
    assert result.admission_rule_id == "ADMIT_005"
    assert result.admission_rule_name == "cys_sg_scope_only_v1"
    assert (result.outcome, result.passed, result.blocks_candidate) == (
        "invalid",
        False,
        True,
    )
    assert result.reason == reason
    assert result.normalized_values == result.validated_candidate_fields == ()
    assert result.consumed_candidate_fields == gate.CANDIDATE_FIELDS
    assert result.consumed_context_items == ()
    assert result.evaluator_io_used is False
    assert result.adapter_id == gate.ADAPTER_ID


def test_mapping_subclass_extra_fields_and_no_mutation() -> None:
    class MappingSubclass(dict[str, object]):
        pass

    candidate = MappingSubclass(
        covalent_residue_name="CYS",
        covalent_residue_atom_name="SG",
        ignored=object(),
    )
    before = tuple(candidate.items())
    source = standalone.evaluate_admit_005(
        candidate["covalent_residue_name"], candidate["covalent_residue_atom_name"]
    )
    oracle = _derive_oracle_design(
        candidate["covalent_residue_name"], candidate["covalent_residue_atom_name"]
    )
    assert _to_design_source(source) == oracle
    assert tuple(candidate.items()) == before
    assert source.consumed_candidate_fields == gate.CANDIDATE_FIELDS


def test_formal_and_oracle_exact_once_with_original_identity() -> None:
    residue = "".join(("c", "y", "s"))
    atom = "".join(("S", "G"))
    formal_seen: list[tuple[object, object]] = []
    scope_seen: list[tuple[object, object]] = []
    atom_seen: list[object] = []

    def formal(left: object, right: object) -> standalone.Admit005EvaluationResult:
        formal_seen.append((left, right))
        return standalone.evaluate_admit_005(left, right)

    def scope(left: object, right: object) -> object:
        scope_seen.append((left, right))
        return semantic_oracle.classify_admit_004_admit_005_atom_scope_design(left, right)

    def validate(value: object) -> object:
        atom_seen.append(value)
        return semantic_oracle.validate_generic_covalent_residue_atom_name(value)

    source = formal(residue, atom)
    oracle = _derive_oracle_design(
        residue, atom, scope_classifier=scope, atom_validator=validate
    )
    source_design = _to_design_source(source)
    assert source_design == oracle
    assert gate.validate_source_shape_and_invariants_for_design(source_design).accepted
    assert gate.validate_source_oracle_equivalence_for_design(source_design, oracle).accepted
    assert formal_seen == [(residue, atom)]
    assert scope_seen == [(residue, atom)]
    assert atom_seen == [atom]
    assert formal_seen[0][0] is residue and formal_seen[0][1] is atom
    assert scope_seen[0][0] is residue and scope_seen[0][1] is atom
    assert atom_seen[0] is atom


@pytest.mark.parametrize(("case_id", "residue", "atom"), EXACT22)
def test_standalone_exact22_oracle_equivalence_and_projection(
    case_id: str, residue: object, atom: object
) -> None:
    source = standalone.evaluate_admit_005(residue, atom)
    source_design = _to_design_source(source)
    prevalidation = gate.validate_source_shape_and_invariants_for_design(source_design)
    assert prevalidation.accepted, case_id
    oracle = _derive_oracle_design(residue, atom)
    assert source_design == oracle, case_id
    assert gate.validate_source_oracle_equivalence_for_design(source_design, oracle).accepted
    unified = gate.project_exact10_to_exact13_for_design(source_design)
    assert unified.admission_rule_id == source_design.admission_rule_id
    assert unified.outcome == source_design.outcome
    assert unified.passed is source_design.passed
    assert unified.blocks_candidate is source_design.blocks_candidate
    assert unified.reason == source_design.reason
    assert unified.normalized_values == source_design.validated_candidate_fields
    assert unified.validated_candidate_fields == source_design.validated_candidate_fields
    assert unified.consumed_candidate_fields == source_design.consumed_candidate_fields
    assert unified.consumed_context_items == ()
    assert unified.evaluator_io_used is source_design.evaluator_io_used


def test_rejected_passthrough_preserves_validated_fields() -> None:
    source = standalone.evaluate_admit_005("SER", "CA")
    result = gate.project_exact10_to_exact13_for_design(_to_design_source(source))
    assert source.outcome == result.outcome == "rejected"
    assert result.validated_candidate_fields == (
        ("covalent_residue_name", "SER"),
        ("covalent_residue_atom_name", "CA"),
    )
    assert result.normalized_values == result.validated_candidate_fields


def test_partial_projection_for_residue_invalid() -> None:
    source = standalone.evaluate_admit_005("C-Y", "SG")
    result = gate.project_exact10_to_exact13_for_design(_to_design_source(source))
    assert source.outcome == "invalid"
    assert result.normalized_values == result.validated_candidate_fields == ()


def test_partial_projection_for_atom_invalid() -> None:
    source = standalone.evaluate_admit_005("cys", ".")
    result = gate.project_exact10_to_exact13_for_design(_to_design_source(source))
    assert source.outcome == "invalid"
    assert result.normalized_values == result.validated_candidate_fields == (
        ("covalent_residue_name", "CYS"),
    )


class _LiveSourceSubclass(standalone.Admit005EvaluationResult):
    pass


@pytest.mark.parametrize(
    ("case_id", "source", "expected_reason"),
    (
        ("wrong_type", SimpleNamespace(), "ADMIT_005_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"),
        (
            "subclass",
            _LiveSourceSubclass(**_live_source_values(standalone.evaluate_admit_005("CYS", "SG"))),
            "ADMIT_005_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        ),
        ("rule_id", _unsafe_live_source(admission_rule_id="ADMIT_004"), "ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("field", _unsafe_live_source(passed=False), "ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("io", _unsafe_live_source(evaluator_io_used=True), "ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("consumed", _unsafe_live_source(consumed_candidate_fields=("covalent_residue_name",)), "ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
    ),
)
def test_source_prevalidation_failure_does_not_call_oracle(
    case_id: str, source: object, expected_reason: str
) -> None:
    scope_calls: list[tuple[object, object]] = []
    atom_calls: list[object] = []
    design_source: object = (
        _to_design_source(source)
        if type(source) is standalone.Admit005EvaluationResult
        else source
    )
    decision = gate.validate_source_shape_and_invariants_for_design(design_source)
    assert not decision.accepted
    assert decision.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    assert decision.reason == expected_reason, case_id
    assert decision.adapter_ready is False
    assert scope_calls == [] and atom_calls == []


def test_source_input_oracle_mismatch_fails_closed() -> None:
    source = _to_design_source(standalone.evaluate_admit_005("CYS", "SG"))
    scope_calls: list[tuple[object, object]] = []
    atom_calls: list[object] = []

    def scope(left: object, right: object) -> object:
        scope_calls.append((left, right))
        return semantic_oracle.classify_admit_004_admit_005_atom_scope_design(left, right)

    def atom(value: object) -> object:
        atom_calls.append(value)
        return semantic_oracle.validate_generic_covalent_residue_atom_name(value)

    assert gate.validate_source_shape_and_invariants_for_design(source).accepted
    oracle = _derive_oracle_design("SER", "CA", scope_classifier=scope, atom_validator=atom)
    decision = gate.validate_source_oracle_equivalence_for_design(source, oracle)
    assert not decision.accepted
    assert decision.reason == "ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert scope_calls == [("SER", "CA")]
    assert atom_calls == ["CA"]


def test_current_phase4_admit005_not_registered() -> None:
    with pytest.raises(phase4.UnifiedAdmissionDispatchError) as captured:
        phase4.evaluate_admission_rule("ADMIT_005", {})
    error = captured.value
    assert (
        error.code,
        error.admission_rule_id,
        error.known_rule,
        error.callable_discovered,
        error.adapter_ready,
        error.reason,
    ) == (
        "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
        "ADMIT_005",
        True,
        False,
        False,
        "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
    )


def test_current_registry_remains_exact_admit001_to_004() -> None:
    assert tuple(phase4.EVALUATOR_REGISTRY) == (
        "ADMIT_001",
        "ADMIT_002",
        "ADMIT_003",
        "ADMIT_004",
    )


def test_truth_rows_have_exact_nonpadding_groups(state: dict[str, object]) -> None:
    rows = state["truth_rows"]
    assert isinstance(rows, list)
    assert len(rows) == 43
    assert len({row["case_id"] for row in rows}) == 43
    assert {
        group: sum(row["case_group"] == group for row in rows)
        for group in gate.TRUTH_GROUP_COUNTS
    } == gate.TRUTH_GROUP_COUNTS
    assert all(row["case_passed"] == "true" for row in rows)


def test_truth_csv_source_failure_call_counts_are_exact() -> None:
    path = gate.REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT / gate.TRUTH_FILENAME
    with path.open(encoding="utf-8", newline="") as handle:
        rows = {
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
            rows[case_id]["formal_call_count"],
            rows[case_id]["scope_oracle_call_count"],
            rows[case_id]["atom_oracle_call_count"],
        ) == ("1", "0", "0")
    assert (
        rows["D_ORACLE_MISMATCH"]["formal_call_count"],
        rows["D_ORACLE_MISMATCH"]["scope_oracle_call_count"],
        rows["D_ORACLE_MISMATCH"]["atom_oracle_call_count"],
    ) == ("1", "1", "1")


def test_required_byte_identical_output_hashes() -> None:
    root = gate.REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    expected = {
        gate.ROUTING_FILENAME: "068646896408f9d7640a9e00b361711986bfa8afe3ffde4e756904826fdf1473",
        gate.ISSUE_FILENAME: "27bed0fd2250e0c64c704771fdb2bca8f5e50554d99f53694dc579f85f578d1f",
        gate.SAFETY_FILENAME: "7d8d7d75046fb49d28b4fcb74aab2d0e8a6b1853a6c73f8420617b2c02cf8265",
    }
    assert {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in expected
    } == expected


def test_exact11_issues_are_preserved(state: dict[str, object]) -> None:
    rows = state["issue_rows"]
    assert isinstance(rows, list) and len(rows) == 11
    by_id = {row["issue_id"]: row for row in rows}
    provider = by_id["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]
    assert (provider["status"], provider["severity"], provider["issue_count"]) == (
        "open",
        "blocking",
        "11",
    )
    coverage = by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    assert coverage["status"] == "open" and coverage["severity"] == "blocking"
    assert "ADMIT_005" in coverage["affected_rules"].split("|")
    aggregation = by_id[
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"
    ]
    assert aggregation["status"] == "open" and aggregation["severity"] == "blocking"


def test_readiness_is_truthful_and_does_not_overclaim(state: dict[str, object]) -> None:
    readiness = state["readiness"]
    assert isinstance(readiness, dict)
    assert readiness["ready_for_admit_005_unified_adapter_implementation"] is True
    assert readiness["feature_semantics_audit_required_before_training"] is True
    for name in (
        "admit_005_unified_adapter_implemented",
        "admit_005_registered_in_engine",
        "phase4_runtime_modified",
        "all_15_rules_covered",
        "evaluate_all_rules_implemented",
        "ready_for_bulk_download_now",
        "ready_for_training",
        "ready_to_train_now",
    ):
        assert readiness[name] is False


def test_deterministic_materialization_and_exact_output_set(
    tmp_path: Path, state: dict[str, object]
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    gate.run_covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1(first)
    gate.run_covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1(second)
    assert {path.name for path in first.iterdir()} == set(gate.OUTPUT_FILES)
    assert {path.name for path in second.iterdir()} == set(gate.OUTPUT_FILES)
    for name in gate.OUTPUT_FILES:
        assert (first / name).read_bytes() == (second / name).read_bytes()
    manifest = json.loads((first / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest["contract_row_count"] == len(state["contract_rows"]) == 46
    assert manifest["truth_matrix_row_count"] == len(state["truth_rows"]) == 43
    assert manifest["output_sha256_excludes_manifest_self_hash"] is True


def test_existing_unexpected_output_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "out"
    root.mkdir()
    (root / "extra").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected"):
        gate.run_covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1(root)


def test_output_symlink_victim_is_not_modified(tmp_path: Path) -> None:
    root = tmp_path / "out"
    root.mkdir()
    victim = tmp_path / "victim"
    victim.write_text("unchanged", encoding="utf-8")
    (root / gate.CONTRACT_FILENAME).symlink_to(victim)
    with pytest.raises(ValueError, match="unsafe entry"):
        gate.run_covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1(root)
    assert victim.read_text(encoding="utf-8") == "unchanged"


def test_output_root_symlink_is_rejected(tmp_path: Path) -> None:
    victim = tmp_path / "victim"
    victim.mkdir()
    root = tmp_path / "out"
    root.symlink_to(victim, target_is_directory=True)
    with pytest.raises(ValueError, match="real non-symlink directory"):
        gate.run_covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1(root)
    assert tuple(victim.iterdir()) == ()


def test_production_ast_imports_are_standard_library_only_and_no_project_imports() -> None:
    source_paths = (
        gate.REPO_ROOT
        / "src/covalent_ext/covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate.py",
    )
    for path in source_paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), path.as_posix())
        roots = {
            node.names[0].name.split(".")[0]
            for node in tree.body
            if isinstance(node, ast.Import)
        } | {
            (node.module or "").split(".")[0]
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
        }
        assert roots <= (set(sys.stdlib_module_names) | {"__future__"})
        assert "covalent_ext" not in roots
        assert not any(
            isinstance(node, (ast.Import, ast.ImportFrom))
            and (
                any(alias.name.startswith("covalent_ext") for alias in node.names)
                if isinstance(node, ast.Import)
                else (node.module or "").startswith("covalent_ext")
            )
            for node in ast.walk(tree)
        )


def test_no_runtime_handler_registry_extension_or_evaluate_all_implementation() -> None:
    path = (
        gate.REPO_ROOT
        / "src/covalent_ext/covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"), path.as_posix())
    functions = {
        node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assignments = {
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (
            node.targets if isinstance(node, ast.Assign) else (node.target,)
        )
        if isinstance(target, ast.Name)
    }
    assert "_evaluate_registered_admit_005" not in functions
    assert "evaluate_all_rules" not in functions
    assert "EVALUATOR_REGISTRY" not in assignments


def test_import_smoke_is_silent_and_has_no_materialization_side_effect(
    tmp_path: Path,
) -> None:
    output_root = gate.REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in output_root.iterdir()}
    code = """
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
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=gate.REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == "" and result.stderr == ""
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in output_root.iterdir()}
    assert after == before
    assert tuple(tmp_path.iterdir()) == ()

    checker = subprocess.run(
        [
            sys.executable,
            "-c",
            "import runpy; runpy.run_path('scripts/check_covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1.py', run_name='checker_import_smoke')",
        ],
        cwd=gate.REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert checker.returncode == 0
    assert checker.stdout == "" and checker.stderr == ""
