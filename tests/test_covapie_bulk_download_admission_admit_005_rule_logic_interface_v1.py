from __future__ import annotations

import ast
import builtins
import csv
import hashlib
import inspect
import io
import json
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate
    as oracle,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_005_rule_logic_interface as subject,
)


EXPECTED_CONTRACT_IDS = (
    "API_001", "API_002", "RESULT_001", "RESULT_002", "RESULT_003",
    "RESULT_004", "RESULT_005", "RESULT_006", "RESULT_007",
    "RESIDUE_001", "RESIDUE_002", "RESIDUE_003", "ATOM_001",
    "ATOM_002", "ATOM_003", "ATOM_004", "ATOM_005", "SCOPE_001",
    "SCOPE_002", "SCOPE_003", "VALIDATED_001", "ORACLE_001",
    "BOUNDARY_001", "BOUNDARY_002",
)


def _values(result: subject.Admit005EvaluationResult) -> tuple[object, ...]:
    return tuple(getattr(result, field.name) for field in fields(result))


def _oracle_values(residue: object, atom: object) -> tuple[object, ...]:
    scope = oracle.classify_admit_004_admit_005_atom_scope_design(residue, atom)
    atom_result = oracle.validate_generic_covalent_residue_atom_name(atom)
    canonical_residue = scope.canonical_residue_name or ""
    if scope.canonical_residue_name is None:
        canonical_atom = ""
        validated: tuple[tuple[str, str], ...] = ()
    elif atom_result.valid is not True:
        canonical_atom = ""
        validated = (("covalent_residue_name", canonical_residue),)
    else:
        assert type(atom_result.canonical_value) is str
        canonical_atom = atom_result.canonical_value
        validated = (
            ("covalent_residue_name", canonical_residue),
            ("covalent_residue_atom_name", canonical_atom),
        )
    return (
        "ADMIT_005", scope.admit_005_outcome,
        scope.admit_005_outcome == "passed",
        scope.admit_005_outcome != "passed", scope.reason,
        canonical_residue, canonical_atom, validated,
        subject.CANDIDATE_FIELDS, False,
    )


def _direct_construction_values(
    *,
    outcome: str,
    reason: str,
    canonical_residue: str,
    canonical_atom: str,
    validated: tuple[tuple[str, str], ...],
) -> dict[str, object]:
    return {
        "admission_rule_id": "ADMIT_005",
        "outcome": outcome,
        "passed": outcome == "passed",
        "blocks_candidate": outcome != "passed",
        "reason": reason,
        "canonical_residue_name": canonical_residue,
        "canonical_residue_atom_name": canonical_atom,
        "validated_candidate_fields": validated,
        "consumed_candidate_fields": subject.CANDIDATE_FIELDS,
        "evaluator_io_used": False,
    }


def test_public_signature_is_exactly_two_required_positional_parameters() -> None:
    signature = inspect.signature(subject.evaluate_admit_005)
    parameters = tuple(signature.parameters.values())
    assert tuple(parameter.name for parameter in parameters) == ("residue_name", "atom_name")
    assert all(parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for parameter in parameters)
    assert all(parameter.default is inspect.Parameter.empty for parameter in parameters)


def test_frozen_result_has_exact10_ordered_fields() -> None:
    assert tuple(field.name for field in fields(subject.Admit005EvaluationResult)) == subject.RESULT_FIELDS
    result = subject.evaluate_admit_005("CYS", "SG")
    with pytest.raises(FrozenInstanceError):
        result.reason = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "override",
    (
        {"admission_rule_id": "ADMIT_004"},
        {"outcome": "blocked", "passed": False, "blocks_candidate": True, "reason": "x"},
        {"passed": False},
        {"blocks_candidate": True},
        {"reason": "ADMIT_005_CYS_SG_SCOPE_REJECTED"},
        {"consumed_candidate_fields": ()},
        {"evaluator_io_used": True},
        {"validated_candidate_fields": ()},
    ),
)
def test_result_direct_construction_fails_closed_on_invariant_violation(override: dict[str, object]) -> None:
    values: dict[str, object] = {
        "admission_rule_id": "ADMIT_005", "outcome": "passed", "passed": True,
        "blocks_candidate": False, "reason": "", "canonical_residue_name": "CYS",
        "canonical_residue_atom_name": "SG",
        "validated_candidate_fields": (("covalent_residue_name", "CYS"), ("covalent_residue_atom_name", "SG")),
        "consumed_candidate_fields": subject.CANDIDATE_FIELDS, "evaluator_io_used": False,
    }
    values.update(override)
    with pytest.raises((TypeError, ValueError)):
        subject.Admit005EvaluationResult(**values)  # type: ignore[arg-type]


def test_result_direct_construction_rejects_subclasses_and_nonexact_tuples() -> None:
    class Text(str):
        pass

    with pytest.raises(TypeError):
        subject.Admit005EvaluationResult(
            Text("ADMIT_005"), "passed", True, False, "", "CYS", "SG",
            (("covalent_residue_name", "CYS"), ("covalent_residue_atom_name", "SG")),
            subject.CANDIDATE_FIELDS, False,
        )


@pytest.mark.parametrize(
    "values",
    (
        _direct_construction_values(
            outcome="passed", reason="", canonical_residue="SER", canonical_atom="CA",
            validated=(("covalent_residue_name", "SER"), ("covalent_residue_atom_name", "CA")),
        ),
        _direct_construction_values(
            outcome="passed", reason="", canonical_residue="cys", canonical_atom="SG",
            validated=(("covalent_residue_name", "cys"), ("covalent_residue_atom_name", "SG")),
        ),
        _direct_construction_values(
            outcome="passed", reason="", canonical_residue="CYS", canonical_atom="CA",
            validated=(("covalent_residue_name", "CYS"), ("covalent_residue_atom_name", "CA")),
        ),
        _direct_construction_values(
            outcome="rejected", reason=subject.SCOPE_REJECTION_REASON,
            canonical_residue="CYS", canonical_atom="SG",
            validated=(("covalent_residue_name", "CYS"), ("covalent_residue_atom_name", "SG")),
        ),
        _direct_construction_values(
            outcome="rejected", reason=subject.RESIDUE_INVALID_REASONS[0],
            canonical_residue="SER", canonical_atom="CA",
            validated=(("covalent_residue_name", "SER"), ("covalent_residue_atom_name", "CA")),
        ),
        _direct_construction_values(
            outcome="rejected", reason=subject.ATOM_INVALID_REASONS[0],
            canonical_residue="SER", canonical_atom="CA",
            validated=(("covalent_residue_name", "SER"), ("covalent_residue_atom_name", "CA")),
        ),
        _direct_construction_values(
            outcome="rejected", reason="", canonical_residue="SER", canonical_atom="CA",
            validated=(("covalent_residue_name", "SER"), ("covalent_residue_atom_name", "CA")),
        ),
        _direct_construction_values(
            outcome="rejected", reason=subject.SCOPE_REJECTION_REASON,
            canonical_residue="ser", canonical_atom="CA",
            validated=(("covalent_residue_name", "ser"), ("covalent_residue_atom_name", "CA")),
        ),
        _direct_construction_values(
            outcome="rejected", reason=subject.SCOPE_REJECTION_REASON,
            canonical_residue="SER", canonical_atom="?",
            validated=(("covalent_residue_name", "SER"), ("covalent_residue_atom_name", "?")),
        ),
        _direct_construction_values(
            outcome="rejected", reason=subject.SCOPE_REJECTION_REASON,
            canonical_residue="SER", canonical_atom="C A",
            validated=(("covalent_residue_name", "SER"), ("covalent_residue_atom_name", "C A")),
        ),
        _direct_construction_values(
            outcome="invalid", reason=subject.SCOPE_REJECTION_REASON,
            canonical_residue="", canonical_atom="", validated=(),
        ),
        _direct_construction_values(
            outcome="invalid", reason="", canonical_residue="", canonical_atom="", validated=(),
        ),
        _direct_construction_values(
            outcome="invalid", reason=subject.RESIDUE_INVALID_REASONS[3],
            canonical_residue="CYS", canonical_atom="SG",
            validated=(("covalent_residue_name", "CYS"), ("covalent_residue_atom_name", "SG")),
        ),
        _direct_construction_values(
            outcome="invalid", reason=subject.RESIDUE_INVALID_REASONS[1],
            canonical_residue="CYS", canonical_atom="",
            validated=(("covalent_residue_name", "CYS"),),
        ),
        _direct_construction_values(
            outcome="invalid", reason=subject.ATOM_INVALID_REASONS[0],
            canonical_residue="", canonical_atom="", validated=(),
        ),
        _direct_construction_values(
            outcome="invalid", reason=subject.ATOM_INVALID_REASONS[4],
            canonical_residue="CYS", canonical_atom="?",
            validated=(("covalent_residue_name", "CYS"), ("covalent_residue_atom_name", "?")),
        ),
        _direct_construction_values(
            outcome="invalid", reason=subject.ATOM_INVALID_REASONS[1],
            canonical_residue="cys", canonical_atom="",
            validated=(("covalent_residue_name", "cys"),),
        ),
        _direct_construction_values(
            outcome="invalid", reason=subject.ATOM_INVALID_REASONS[2],
            canonical_residue="C-Y", canonical_atom="",
            validated=(("covalent_residue_name", "C-Y"),),
        ),
    ),
    ids=(
        "passed-ser-ca", "passed-lowercase-cys-sg", "passed-cys-ca",
        "rejected-cys-sg", "rejected-residue-invalid-reason",
        "rejected-atom-invalid-reason", "rejected-empty-reason",
        "rejected-lowercase-residue",
        "rejected-marker-atom", "rejected-whitespace-atom",
        "invalid-scope-reason", "invalid-empty-reason",
        "residue-invalid-with-cys-sg",
        "residue-invalid-with-residue-only", "atom-invalid-without-residue",
        "atom-invalid-with-populated-atom", "atom-invalid-lowercase-residue",
        "atom-invalid-syntax-residue",
    ),
)
def test_result_direct_construction_rejects_semantic_state_conflicts(
    values: dict[str, object],
) -> None:
    with pytest.raises((TypeError, ValueError)):
        subject.Admit005EvaluationResult(**values)  # type: ignore[arg-type]


def test_private_canonical_validators_are_pure_and_exact() -> None:
    assert subject._canonical_residue_name_is_valid("CYS") is True
    assert subject._canonical_residue_name_is_valid("cys") is False
    assert subject._canonical_residue_name_is_valid("C-Y") is False
    assert subject._canonical_atom_name_is_valid("C1'") is True
    assert subject._canonical_atom_name_is_valid("ca") is True
    assert subject._canonical_atom_name_is_valid("?") is False
    assert subject._canonical_atom_name_is_valid("C A") is False


@pytest.mark.parametrize(
    ("value", "reason"),
    (
        (7, "COVALENT_RESIDUE_NAME_TYPE_INVALID"),
        ("", "COVALENT_RESIDUE_NAME_EMPTY"),
        ("CÝS", "COVALENT_RESIDUE_NAME_NON_ASCII"),
        ("C-Y", "COVALENT_RESIDUE_NAME_SYNTAX_INVALID"),
        ("A" * 33, "COVALENT_RESIDUE_NAME_SYNTAX_INVALID"),
    ),
)
def test_residue_validation_reason_vocabulary_and_order(value: object, reason: str) -> None:
    result = subject.evaluate_admit_005(value, "SG")
    assert result.outcome == "invalid" and result.reason == reason
    assert result.canonical_residue_name == "" and result.canonical_residue_atom_name == ""
    assert result.validated_candidate_fields == ()


def test_residue_exact_str_subclass_is_invalid_without_method_dispatch() -> None:
    class Text(str):
        def isascii(self) -> bool:
            raise AssertionError("str subclass method must not run")

    result = subject.evaluate_admit_005(Text("CYS"), "SG")
    assert result.reason == "COVALENT_RESIDUE_NAME_TYPE_INVALID"


def test_residue_grammar_boundary_and_uppercase_are_exact() -> None:
    assert subject.evaluate_admit_005("a", "SG").canonical_residue_name == "A"
    assert subject.evaluate_admit_005("a" * 32, "SG").canonical_residue_name == "A" * 32
    assert subject.evaluate_admit_005(" cys", "SG").reason == "COVALENT_RESIDUE_NAME_SYNTAX_INVALID"


@pytest.mark.parametrize(
    ("value", "reason"),
    (
        (7, "COVALENT_RESIDUE_ATOM_NAME_TYPE_INVALID"),
        ("", "COVALENT_RESIDUE_ATOM_NAME_EMPTY"),
        ("SĠ", "COVALENT_RESIDUE_ATOM_NAME_NON_ASCII"),
        ("S G", "COVALENT_RESIDUE_ATOM_NAME_WHITESPACE_FORBIDDEN"),
        ("S\tG", "COVALENT_RESIDUE_ATOM_NAME_WHITESPACE_FORBIDDEN"),
        (".", "COVALENT_RESIDUE_ATOM_NAME_MARKER_FORBIDDEN"),
        ("?", "COVALENT_RESIDUE_ATOM_NAME_MARKER_FORBIDDEN"),
    ),
)
def test_atom_validation_reason_vocabulary_and_partial_mapping(value: object, reason: str) -> None:
    result = subject.evaluate_admit_005("cys", value)
    assert result.outcome == "invalid" and result.reason == reason
    assert result.canonical_residue_name == "CYS" and result.canonical_residue_atom_name == ""
    assert result.validated_candidate_fields == (("covalent_residue_name", "CYS"),)


def test_atom_exact_str_subclass_is_invalid() -> None:
    class Text(str):
        pass

    assert subject.evaluate_admit_005("CYS", Text("SG")).reason == "COVALENT_RESIDUE_ATOM_NAME_TYPE_INVALID"


@pytest.mark.parametrize("atom", ("SG", "CA", "ca", "N1", "OXT", "C1'", "A.B", "+"))
def test_generic_atom_names_are_valid_and_exact_preserved(atom: str) -> None:
    result = subject.evaluate_admit_005("SER", atom)
    assert result.canonical_residue_atom_name == atom
    assert result.validated_candidate_fields[-1] == ("covalent_residue_atom_name", atom)


@pytest.mark.parametrize(
    ("residue", "atom", "outcome", "reason"),
    (
        ("CYS", "SG", "passed", ""),
        ("cys", "SG", "passed", ""),
        ("CYS", "CA", "rejected", "ADMIT_005_CYS_SG_SCOPE_REJECTED"),
        ("CYS", "sg", "rejected", "ADMIT_005_CYS_SG_SCOPE_REJECTED"),
        ("SER", "SG", "rejected", "ADMIT_005_CYS_SG_SCOPE_REJECTED"),
        ("CYX", "SG", "rejected", "ADMIT_005_CYS_SG_SCOPE_REJECTED"),
    ),
)
def test_scope_boundary_uses_only_canonical_cys_and_exact_sg(residue: str, atom: str, outcome: str, reason: str) -> None:
    result = subject.evaluate_admit_005(residue, atom)
    assert result.outcome == outcome and result.reason == reason
    assert result.passed is (outcome == "passed")
    assert result.blocks_candidate is (outcome != "passed")


def test_residue_failure_has_precedence_and_does_not_inspect_atom() -> None:
    class Atom(str):
        def isascii(self) -> bool:
            raise AssertionError("atom must not be inspected")

        def __iter__(self):
            raise AssertionError("atom must not be inspected")

    result = subject.evaluate_admit_005("C-Y", Atom("?"))
    assert result.reason == "COVALENT_RESIDUE_NAME_SYNTAX_INVALID"
    assert result.canonical_residue_atom_name == ""


def test_consumed_fields_and_no_io_are_constant() -> None:
    for result in (
        subject.evaluate_admit_005("CYS", "SG"),
        subject.evaluate_admit_005("SER", "CA"),
        subject.evaluate_admit_005("", "?"),
    ):
        assert result.consumed_candidate_fields == subject.CANDIDATE_FIELDS
        assert result.evaluator_io_used is False


def test_repeated_calls_are_deterministic_and_inputs_unchanged() -> None:
    inputs = ["cys", "A.B"]
    before = list(inputs)
    assert subject.evaluate_admit_005(*inputs) == subject.evaluate_admit_005(*inputs)
    assert inputs == before


def test_formal_evaluator_uses_no_filesystem_network_or_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("I/O forbidden")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    assert subject.evaluate_admit_005("CYS", "SG").outcome == "passed"


def test_formal_evaluator_call_graph_excludes_all_design_oracles() -> None:
    tree = ast.parse(inspect.getsource(subject.evaluate_admit_005))
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not calls.intersection({
        "classify_admit_004_admit_005_atom_scope_design",
        "validate_generic_covalent_residue_atom_name",
        "normalize_covalent_residue_name",
        "validate_covalent_residue_atom_name",
    })


def test_independent_oracle_combination_matches_every_truth_case_field() -> None:
    for case in subject._truth_case_definitions():
        result = subject.evaluate_admit_005(case["residue"], case["atom"])
        assert _values(result) == _oracle_values(case["residue"], case["atom"])


def test_exact22_truth_rows_have_required_order_counts_and_precedence() -> None:
    rows = subject._truth_rows()
    assert len(rows) == len({row["case_id"] for row in rows}) == 22
    assert [row["case_id"] for row in rows[:2]] == ["PASS_001", "PASS_002"]
    assert {outcome: sum(row["observed_outcome"] == outcome for row in rows) for outcome in subject.OUTCOME_VOCABULARY} == {"passed": 2, "rejected": 6, "invalid": 14}
    assert rows[-1]["case_id"] == "PRECEDENCE_001"
    assert rows[-1]["observed_reason"] == "COVALENT_RESIDUE_NAME_SYNTAX_INVALID"
    assert all(row["case_passed"] == "true" for row in rows)
    assert hashlib.sha256(subject._csv_bytes(subject.TRUTH_COLUMNS, rows)).hexdigest() == "695c187ccd297671b74ae33a95c52e2c38f0f5d1c46b253b8dd84c682499b10f"


def test_exact24_contract_rows_are_ordered_unique_and_real() -> None:
    rows = subject._contract_rows()
    assert tuple(row["contract_id"] for row in rows) == EXPECTED_CONTRACT_IDS
    assert len({(row["contract_kind"], row["contract_subject"], row["contract_value"]) for row in rows}) == 24
    assert all(row["contract_status"] == "frozen" for row in rows)
    keyed = {row["contract_id"]: row for row in rows}
    assert keyed["RESULT_007"]["contract_value"] == "passed=>empty_reason_and_exact_CYS_SG|rejected=>scope_rejection_reason_and_valid_non_CYS_SG|invalid=>field_specific_reason_controls_partial_canonical_state"
    assert keyed["VALIDATED_001"]["contract_value"] == "residue_invalid_reason=>no_canonical_fields|atom_invalid_reason=>canonical_residue_only|passed_or_rejected=>canonical_residue_then_atom"


def test_exact12_source_snapshot_order_structure_and_sha() -> None:
    snapshot = subject.build_frozen_source_snapshot()
    assert subject.validate_frozen_source_snapshot(snapshot)
    assert tuple(record.relative_path for record in snapshot.records) == subject.SOURCE_PATHS
    assert all(record.expected_sha256 == record.base_tree_sha256 == record.filesystem_sha256 for record in snapshot.records)


def test_base_object_subject_and_successor_lineage_are_required(monkeypatch: pytest.MonkeyPatch) -> None:
    original = subject._git

    def fail_subject(arguments: object, repo_root: Path, *, text: bool = False) -> subprocess.CompletedProcess[object]:
        if tuple(arguments[:3]) == ("show", "-s", "--format=%s"):  # type: ignore[index]
            return subprocess.CompletedProcess(arguments, 0, "wrong\n", "")
        return original(arguments, repo_root, text=text)  # type: ignore[arg-type]

    monkeypatch.setattr(subject, "_git", fail_subject)
    with pytest.raises(ValueError, match="subject"):
        subject.build_frozen_source_snapshot()


def test_non_descendant_fails_closed_with_deterministic_monkeypatch(monkeypatch: pytest.MonkeyPatch) -> None:
    original = subject._git

    def fail_lineage(arguments: object, repo_root: Path, *, text: bool = False) -> subprocess.CompletedProcess[object]:
        if tuple(arguments[:2]) == ("merge-base", "--is-ancestor"):  # type: ignore[index]
            return subprocess.CompletedProcess(arguments, 1, b"", b"")
        return original(arguments, repo_root, text=text)  # type: ignore[arg-type]

    monkeypatch.setattr(subject, "_git", fail_lineage)
    with pytest.raises(ValueError, match="not an ancestor"):
        subject.build_frozen_source_snapshot(head_ref="HEAD")


def test_all_structural_checks_precede_first_source_byte_read(monkeypatch: pytest.MonkeyPatch) -> None:
    original = subject._git
    structural_count = 0
    first_read_count = -1

    def observed(arguments: object, repo_root: Path, *, text: bool = False) -> subprocess.CompletedProcess[object]:
        nonlocal structural_count, first_read_count
        if tuple(arguments[:2]) == ("ls-files", "--error-unmatch"):  # type: ignore[index]
            structural_count += 1
        if arguments[0] == "show" and len(arguments) == 2 and ":" in arguments[1]:  # type: ignore[index]
            if first_read_count == -1:
                first_read_count = structural_count
        return original(arguments, repo_root, text=text)  # type: ignore[arg-type]

    monkeypatch.setattr(subject, "_git", observed)
    subject.build_frozen_source_snapshot()
    assert structural_count == first_read_count == 12


def test_source_missing_and_symlink_fail_before_content_read(monkeypatch: pytest.MonkeyPatch) -> None:
    original_lstat = Path.lstat
    target = (subject.REPO_ROOT / subject.SOURCE_PATHS[0]).resolve()

    def missing(path: Path) -> os.stat_result:
        if path == target:
            raise FileNotFoundError(path)
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", missing)
    with pytest.raises(ValueError, match="missing"):
        subject.build_frozen_source_snapshot()
    monkeypatch.setattr(Path, "lstat", original_lstat)

    def symlink(path: Path) -> os.stat_result:
        observed = original_lstat(path)
        if path == target:
            values = list(observed)
            values[0] = stat.S_IFLNK | 0o777
            return os.stat_result(values)
        return observed

    monkeypatch.setattr(Path, "lstat", symlink)
    with pytest.raises(ValueError, match="regular non-symlink"):
        subject.build_frozen_source_snapshot()


def test_source_hash_mismatch_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = Path.read_bytes
    target = subject.REPO_ROOT / subject.SOURCE_PATHS[0]

    def tampered(path: Path) -> bytes:
        content = original(path)
        return content + b"tamper" if path == target else content

    monkeypatch.setattr(Path, "read_bytes", tampered)
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        subject.build_frozen_source_snapshot()


def test_exact12_source_audit_is_ordered_and_all_verified() -> None:
    state = subject.build_interface_state()
    rows = state["source_audit_rows"]
    assert len(rows) == 12
    assert tuple(row["source_relative_path"] for row in rows) == tuple(path.as_posix() for path in subject.SOURCE_PATHS)
    assert all(row["source_verified"] == "true" for row in rows)


def test_exact11_issues_are_copied_byte_field_order_and_provider_blocker_stays_11() -> None:
    state = subject.build_interface_state()
    source = subject._csv_document(state["source_snapshot"], subject.SOURCE_PATHS[2])
    assert state["issue_rows"] == list(source.rows)
    provider = [row for row in state["issue_rows"] if row["issue_id"] == "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]
    assert [(row["status"], row["severity"], row["issue_count"]) for row in provider] == [("open", "blocking", "11")]
    coverage = next(row for row in state["issue_rows"] if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert "ADMIT_005" in coverage["affected_rules"].split("|")


def test_readiness_is_exact_and_does_not_overclaim() -> None:
    state = subject.build_interface_state()
    assert state["readiness"] == subject.READINESS
    assert state["readiness"]["ready_for_admit_005_unified_adapter_contract_design"] is True
    assert state["readiness"]["admit_005_candidate_projection_contract_frozen"] is False
    assert state["readiness"]["admit_005_context_routing_contract_frozen"] is False
    assert state["readiness"]["admit_005_registered_in_engine"] is False
    assert state["readiness"]["ready_for_training"] is False


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in root.iterdir()}


def test_deterministic_double_materialization_and_exact_output_set(tmp_path: Path) -> None:
    root = tmp_path / "output"
    subject.run_covapie_bulk_download_admission_admit_005_rule_logic_interface_v1(root)
    first = _tree_bytes(root)
    subject.run_covapie_bulk_download_admission_admit_005_rule_logic_interface_v1(root)
    second = _tree_bytes(root)
    assert first == second
    assert set(first) == set(subject.OUTPUT_FILES)
    assert not tuple(root.glob("*.tmp")) and not tuple(root.glob("*.part"))


def test_materializer_rejects_extra_and_unsafe_existing_entries(tmp_path: Path) -> None:
    extra_root = tmp_path / "extra"
    extra_root.mkdir()
    (extra_root / "extra.txt").write_text("x")
    with pytest.raises(ValueError, match="unexpected"):
        subject.run_covapie_bulk_download_admission_admit_005_rule_logic_interface_v1(extra_root)
    file_root = tmp_path / "file"
    file_root.write_text("x")
    with pytest.raises(ValueError, match="output root"):
        subject.run_covapie_bulk_download_admission_admit_005_rule_logic_interface_v1(file_root)


def test_materializer_symlink_victim_is_not_modified(tmp_path: Path) -> None:
    root = tmp_path / "output"
    root.mkdir()
    victim = tmp_path / "victim"
    victim.write_text("unchanged")
    (root / subject.CONTRACT_FILENAME).symlink_to(victim)
    with pytest.raises(ValueError, match="unsafe"):
        subject.run_covapie_bulk_download_admission_admit_005_rule_logic_interface_v1(root)
    assert victim.read_text() == "unchanged"


def test_materialized_csv_counts_hashes_and_manifest_claims(tmp_path: Path) -> None:
    root = tmp_path / "output"
    result = subject.run_covapie_bulk_download_admission_admit_005_rule_logic_interface_v1(root)
    manifest = json.loads((root / subject.MANIFEST_FILENAME).read_text())
    assert manifest == result["manifest"]
    assert manifest["output_files"] == list(subject.OUTPUT_FILES)
    assert manifest["output_file_count"] == 6
    for name in subject.CSV_OUTPUTS:
        assert manifest["output_sha256"][name] == hashlib.sha256((root / name).read_bytes()).hexdigest()
    assert subject.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert manifest["direct_result_construction_fail_closed"] is True
    assert manifest["result_outcome_reason_canonical_state_bound"] is True
    assert manifest["result_reason_class_mapping_frozen"] is True
    assert manifest["readiness"] == subject.READINESS
    assert len(list(csv.DictReader(io.StringIO((root / subject.CONTRACT_FILENAME).read_text())))) == 24
    assert len(list(csv.DictReader(io.StringIO((root / subject.TRUTH_FILENAME).read_text())))) == 22
    assert len(list(csv.DictReader(io.StringIO((root / subject.SOURCE_AUDIT_FILENAME).read_text())))) == 12
    assert len(list(csv.DictReader(io.StringIO((root / subject.ISSUE_FILENAME).read_text())))) == 11


def test_production_module_uses_only_python_standard_library() -> None:
    source = Path(subject.__file__).read_text()
    tree = ast.parse(source)
    roots = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
    assert set(roots).issubset(set(sys.stdlib_module_names) | {"__future__"})


def test_import_has_no_stdout_stderr_or_materialization_side_effect() -> None:
    output_root = subject.REPO_ROOT / subject.DEFAULT_OUTPUT_ROOT
    before = _tree_bytes(output_root) if output_root.exists() else None
    completed = subprocess.run(
        [sys.executable, "-c", "import covalent_ext.covapie_bulk_download_admission_admit_005_rule_logic_interface"],
        cwd=subject.REPO_ROOT, env={**os.environ, "PYTHONPATH": str(subject.REPO_ROOT / "src")},
        check=False, capture_output=True, text=True,
    )
    assert completed.returncode == 0 and completed.stdout == completed.stderr == ""
    after = _tree_bytes(output_root) if output_root.exists() else None
    assert before == after


def test_no_candidate_projection_context_routing_adapter_or_registration_api_exists() -> None:
    public_functions = {
        name for name, value in vars(subject).items()
        if (
            inspect.isfunction(value)
            and value.__module__ == subject.__name__
            and not name.startswith("_")
        )
    }
    assert public_functions == {
        "evaluate_admit_005",
        "build_frozen_source_snapshot",
        "validate_frozen_source_snapshot",
        "build_interface_state",
        "run_covapie_bulk_download_admission_admit_005_rule_logic_interface_v1",
    }
    assert "evaluate_admission_rule" not in public_functions
    assert "evaluate_all_rules" not in public_functions


def test_checker_passes_and_asserts_direct_evidence() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/check_covapie_bulk_download_admission_admit_005_rule_logic_interface_v1.py"],
        cwd=subject.REPO_ROOT, env={**os.environ, "PYTHONPATH": str(subject.REPO_ROOT / "src")},
        check=False, capture_output=True, text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "admit_005_truth_matrix=22/22" in completed.stdout
    assert "direct_result_semantic_invariants=10/10" in completed.stdout
    assert "ADMIT_005_STANDALONE_EVALUATOR_INTERFACE_CHECK=PASS" in completed.stdout
