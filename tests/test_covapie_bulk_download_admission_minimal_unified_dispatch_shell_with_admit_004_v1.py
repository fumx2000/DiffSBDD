from __future__ import annotations

import ast
import builtins
import contextlib
import dataclasses
import hashlib
import importlib
import inspect
import io
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from types import MappingProxyType, SimpleNamespace

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004 as shell,
)
from covalent_ext.covapie_bulk_download_admission_admit_004_rule_logic_interface import (
    Admit004EvaluationResult,
)


def candidate(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = dict(shell._base_candidate())
    value.update(overrides)
    return value


def context(value: dict[str, object], **overrides: object) -> dict[str, object]:
    result = shell._base_context(value)  # type: ignore[arg-type]
    nested = result[shell.EVIDENCE_CONTEXT_KEY]
    assert isinstance(nested, dict)
    nested.update(overrides)
    return result


def test_exact12_source_order_and_sha_are_frozen() -> None:
    assert len(shell.SOURCE_PATHS) == 12
    assert len(set(shell.SOURCE_PATHS)) == 12
    assert tuple(shell.SOURCE_SHA256) == shell.SOURCE_PATHS
    assert tuple(shell.SOURCE_SHA256.values()) == (
        "510ba06546754fafdb02ab15b48636066e7b38e42b2f1ed0da9346a6485f150f",
        "2d46faffb7505483b5dabc05a9451d1b6eea0671c722f78674175a8559e8a304",
        "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa",
        "2d09f6ab5aa9c64419e7e7c4a90f6562a2883007f9b3ef82258a69b9df181b05",
        "5295ee97d8cc3c81cd376116c4dc87489e1b04a65d700a6d08a927d5c72a9951",
        "d05c54f805ad2118027124ae96c3bce132904e26bbd93daa3dc0298681aa159f",
        "62e21a2b4a982e734d6ecd02b1ec056fa0ddccfda6c41dd4bd90dfbe7eb47c3d",
        "5c05e166091a7a067014d9d4dbd8c7c4280b6f247c31765e14bf37d3f86adba3",
        "0c4fbc7f1307d3adb5c62dffb7668176b0ad54f2ff156b2f42ea02dec8d48250",
        "399fa0617aee4196c99051d99d26c75f54cbcc815a396425b7825dbeb9e7d83e",
        "7cf0a9ff421ba987655c4dac4564c04dbaa854cd4f725b18136642f223762d30",
        "f000c7959c0e8a9f561d60b332c5460b4de84279d3e5c11556638334297723a6",
    )


def test_frozen_snapshot_matches_base_tree_and_filesystem() -> None:
    snapshot = shell.build_frozen_source_snapshot()
    assert shell.validate_frozen_source_snapshot(snapshot)
    assert tuple(record.relative_path for record in snapshot.records) == shell.SOURCE_PATHS
    assert all(
        record.expected_sha256
        == record.base_tree_sha256
        == record.filesystem_sha256
        == hashlib.sha256(record.content_bytes).hexdigest()
        for record in snapshot.records
    )


def test_base_object_subject_and_current_lineage() -> None:
    shell._validate_expected_base_lineage(shell.REPO_ROOT)
    assert shell.EXPECTED_BASE_COMMIT == "8f4782dc601c8ddda69b038074fa1a878c762a6a"
    assert shell.EXPECTED_BASE_SUBJECT == "add CovaPIE unified admission rule engine contract design v1"


def test_non_descendant_head_ref_fails_closed() -> None:
    with pytest.raises(ValueError, match="not an ancestor"):
        shell._validate_expected_base_lineage(
            shell.REPO_ROOT, head_ref=f"{shell.EXPECTED_BASE_COMMIT}^"
        )


def test_invalid_head_ref_fails_before_git() -> None:
    with pytest.raises(ValueError, match="head ref"):
        shell._validate_expected_base_lineage(shell.REPO_ROOT, head_ref="--help")


def test_all_structural_checks_precede_first_source_read(monkeypatch: pytest.MonkeyPatch) -> None:
    checked: list[Path] = []
    monkeypatch.setattr(shell, "_validate_expected_base_lineage", lambda *args, **kwargs: None)

    def structural(path: Path, repo_root: Path) -> bool:
        checked.append(path)
        return path != shell.SOURCE_PATHS[-1]

    monkeypatch.setattr(shell, "_structural_source_check", structural)
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda self: (_ for _ in ()).throw(AssertionError("source bytes read too early")),
    )
    with pytest.raises(ValueError, match="structural"):
        shell.build_frozen_source_snapshot()
    assert tuple(checked) == shell.SOURCE_PATHS


def test_structural_source_missing_and_symlink_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = Path("evidence.csv")

    def fake_git(arguments: object, repo_root: Path, *, text: bool = True) -> SimpleNamespace:
        return SimpleNamespace(
            returncode=0,
            stdout="100644 blob 0123456789abcdef\tevidence.csv\n",
            stderr="",
        )

    monkeypatch.setattr(shell, "_git", fake_git)
    assert shell._structural_source_check(path, tmp_path) is False
    victim = tmp_path / "victim"
    victim.write_text("victim", encoding="utf-8")
    (tmp_path / path).symlink_to(victim)
    assert shell._structural_source_check(path, tmp_path) is False
    assert victim.read_text(encoding="utf-8") == "victim"


def test_snapshot_content_hash_tamper_fails_closed() -> None:
    snapshot = shell.build_frozen_source_snapshot()
    first = dataclasses.replace(snapshot.records[0], content_bytes=b"tampered")
    tampered = shell.FrozenSourceSnapshot((first, *snapshot.records[1:]))
    assert shell.validate_frozen_source_snapshot(tampered) is False
    state = shell.build_phase2_state(tampered)
    assert state["all_checks_passed"] is False
    assert state["validation_failures"] == ["SOURCE_BOUNDARY_FAILED"]


def test_public_signature_is_exact_single_rule_api() -> None:
    signature = inspect.signature(shell.evaluate_admission_rule)
    assert tuple(signature.parameters) == (
        "admission_rule_id",
        "candidate_record",
        "batch_context",
        "evaluation_context",
        "download_result_context",
        "stage_authorization_context",
    )
    assert signature.parameters["admission_rule_id"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert signature.parameters["candidate_record"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert all(
        signature.parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        and signature.parameters[name].default is None
        for name in tuple(signature.parameters)[2:]
    )
    assert signature.return_annotation == "UnifiedAdmissionRuleEvaluation"


def test_unified_result_is_frozen_exact13() -> None:
    assert dataclasses.is_dataclass(shell.UnifiedAdmissionRuleEvaluation)
    assert shell.UnifiedAdmissionRuleEvaluation.__dataclass_params__.frozen is True
    assert tuple(
        field.name for field in dataclasses.fields(shell.UnifiedAdmissionRuleEvaluation)
    ) == shell.RESULT_FIELDS
    result = shell.evaluate_admission_rule(
        "ADMIT_004", candidate(), evaluation_context=context(candidate())
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.outcome = "blocked"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("outcome", "passed", "blocks", "reason"),
    (
        ("passed", False, False, ""),
        ("blocked", False, False, "blocked"),
        ("invalid", False, True, ""),
        ("rejected", False, True, ""),
    ),
)
def test_unified_result_invariants_fail_closed(
    outcome: str, passed: bool, blocks: bool, reason: str
) -> None:
    with pytest.raises(ValueError):
        shell.UnifiedAdmissionRuleEvaluation(
            shell.RESULT_SCHEMA_VERSION,
            "ADMIT_004",
            shell.ADMIT_004_RULE_NAME,
            outcome,
            passed,
            blocks,
            reason,
            (),
            (),
            (),
            (),
            False,
            shell.ADMIT_004_ADAPTER_ID,
        )


def test_dispatch_error_is_frozen_exact6_exception() -> None:
    assert issubclass(shell.UnifiedAdmissionDispatchError, Exception)
    assert shell.UnifiedAdmissionDispatchError.__dataclass_params__.frozen is True
    assert tuple(
        field.name for field in dataclasses.fields(shell.UnifiedAdmissionDispatchError)
    ) == shell.DISPATCH_ERROR_FIELDS
    error = shell.UnifiedAdmissionDispatchError(
        "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", "ADMIT_999", False, False, False, "reason"
    )
    assert str(error) == "reason"
    assert error.args == ("reason",)
    assert not hasattr(error, "outcome")
    assert not hasattr(error, "passed")
    with pytest.raises(dataclasses.FrozenInstanceError):
        error.reason = "changed"  # type: ignore[misc]


def test_all_five_dispatch_error_codes_are_accepted() -> None:
    for code in shell.DISPATCH_ERROR_CODES:
        error = shell.UnifiedAdmissionDispatchError(code, "", False, False, False, code)
        assert error.code == code
    with pytest.raises(ValueError, match="code"):
        shell.UnifiedAdmissionDispatchError("OTHER", "", False, False, False, "OTHER")


def test_registry_is_immutable_and_exactly_admit_004() -> None:
    assert isinstance(shell.EVALUATOR_REGISTRY, MappingProxyType)
    assert tuple(shell.EVALUATOR_REGISTRY) == ("ADMIT_004",)
    assert shell.EVALUATOR_REGISTRY["ADMIT_004"][0] == shell.ADMIT_004_RULE_NAME
    with pytest.raises(TypeError):
        shell.EVALUATOR_REGISTRY["ADMIT_005"] = object()  # type: ignore[index]


@pytest.mark.parametrize(
    ("rule_id", "expected_code", "known", "discovered"),
    (
        (4, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", False, False),
        ("ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", False, False),
        ("ADMIT_001", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", True, True),
        ("ADMIT_003", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", True, True),
        ("ADMIT_005", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", True, False),
        ("ADMIT_015", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", True, False),
    ),
)
def test_rule_id_dispatch_precedence(
    rule_id: object, expected_code: str, known: bool, discovered: bool
) -> None:
    with pytest.raises(shell.UnifiedAdmissionDispatchError) as captured:
        shell.evaluate_admission_rule(  # type: ignore[arg-type]
            rule_id,
            candidate(),
            batch_context={},
            evaluation_context=None,
            download_result_context={},
            stage_authorization_context={},
        )
    error = captured.value
    assert error.code == expected_code
    assert error.known_rule is known
    assert error.callable_discovered is discovered
    assert error.adapter_ready is False
    if expected_code == "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID":
        assert error.admission_rule_id == ""


def test_str_subclass_rule_id_is_type_invalid() -> None:
    class RuleId(str):
        pass

    with pytest.raises(shell.UnifiedAdmissionDispatchError) as captured:
        shell.evaluate_admission_rule(
            RuleId("ADMIT_004"), candidate(), evaluation_context={}
        )
    assert captured.value.code == "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"
    assert captured.value.admission_rule_id == ""


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    (
        ({"batch_context": {}, "evaluation_context": {}}, "ADMIT_004_BATCH_CONTEXT_MUST_BE_NONE"),
        ({"evaluation_context": None}, "ADMIT_004_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ({"evaluation_context": []}, "ADMIT_004_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ({"evaluation_context": {}, "download_result_context": {}}, "ADMIT_004_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ({"evaluation_context": {}, "stage_authorization_context": {}}, "ADMIT_004_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
    ),
)
def test_admit_004_context_routing_failures(kwargs: dict[str, object], reason: str) -> None:
    with pytest.raises(shell.UnifiedAdmissionDispatchError) as captured:
        shell.evaluate_admission_rule("ADMIT_004", candidate(), **kwargs)  # type: ignore[arg-type]
    error = captured.value
    assert error.code == "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"
    assert error.known_rule is True
    assert error.callable_discovered is True
    assert error.adapter_ready is True
    assert error.reason == reason


def test_context_routing_validation_order_is_fixed() -> None:
    with pytest.raises(shell.UnifiedAdmissionDispatchError) as captured:
        shell.evaluate_admission_rule(
            "ADMIT_004",
            candidate(),
            batch_context={},
            evaluation_context=[],  # type: ignore[arg-type]
            download_result_context={},
            stage_authorization_context={},
        )
    assert captured.value.reason == "ADMIT_004_BATCH_CONTEXT_MUST_BE_NONE"


def test_empty_evaluation_context_is_valid_routing_and_blocked_result() -> None:
    result = shell.evaluate_admission_rule("ADMIT_004", candidate(), evaluation_context={})
    assert result.outcome == "blocked"
    assert result.reason == "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_MISSING"
    assert result.consumed_context_items == ()


def test_projection_context_identity_and_exactly_one_evaluator_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = object()
    original = candidate(covalent_residue_chain_id=sentinel, unrelated="excluded")

    class Context(dict[str, object]):
        pass

    evaluation = Context()
    calls: list[tuple[object, object]] = []

    def fake_evaluator(projected: object, received_context: object) -> Admit004EvaluationResult:
        calls.append((projected, received_context))
        return Admit004EvaluationResult(
            "ADMIT_004",
            "passed",
            True,
            False,
            "",
            "CYS",
            tuple((field, "validated") for field in shell.ADMIT_004_CANDIDATE_FIELDS),
            shell.ADMIT_004_CANDIDATE_FIELDS,
            True,
            False,
        )

    monkeypatch.setattr(shell, "evaluate_admit_004", fake_evaluator)
    result = shell.evaluate_admission_rule(
        "ADMIT_004", original, evaluation_context=evaluation
    )
    assert result.outcome == "passed"
    assert len(calls) == 1
    projected, received_context = calls[0]
    assert isinstance(projected, dict)
    assert tuple(projected) == shell.ADMIT_004_CANDIDATE_FIELDS
    assert "unrelated" not in projected
    assert projected["covalent_residue_chain_id"] is sentinel
    assert received_context is evaluation
    assert original["unrelated"] == "excluded"


def test_non_mapping_candidate_is_forwarded_and_returns_invalid() -> None:
    non_mapping: object = []
    result = shell.evaluate_admission_rule(  # type: ignore[arg-type]
        "ADMIT_004", non_mapping, evaluation_context={}
    )
    assert result.outcome == "invalid"
    assert result.reason == "ADMIT_004_CANDIDATE_RECORD_MAPPING_INVALID"
    assert result.normalized_values == ()
    assert result.validated_candidate_fields == ()
    assert result.consumed_candidate_fields == shell.ADMIT_004_CANDIDATE_FIELDS


@pytest.mark.parametrize(
    ("candidate_value", "evaluation_value", "outcome", "reason", "context_items"),
    (
        (candidate(), context(candidate()), "passed", "", ("covalent_residue_identity_evidence_context",)),
        (candidate(covalent_residue_insertion_code_state="unknown"), {}, "blocked", "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN", ()),
        (candidate(), {shell.EVIDENCE_CONTEXT_KEY: []}, "invalid", "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_MAPPING_INVALID", ("covalent_residue_identity_evidence_context",)),
    ),
)
def test_admit_004_adapter_field_mapping(
    candidate_value: dict[str, object],
    evaluation_value: dict[str, object],
    outcome: str,
    reason: str,
    context_items: tuple[str, ...],
) -> None:
    result = shell.evaluate_admission_rule(
        "ADMIT_004", candidate_value, evaluation_context=evaluation_value
    )
    assert result.schema_version == shell.RESULT_SCHEMA_VERSION
    assert result.admission_rule_id == "ADMIT_004"
    assert result.admission_rule_name == shell.ADMIT_004_RULE_NAME
    assert result.outcome == outcome
    assert result.passed is (outcome == "passed")
    assert result.blocks_candidate is (outcome != "passed")
    assert result.reason == reason
    assert result.consumed_context_items == context_items
    assert result.evaluator_io_used is False
    assert result.adapter_id == shell.ADMIT_004_ADAPTER_ID


def test_lowercase_residue_normalized_values_mapping() -> None:
    value = candidate(covalent_residue_name="cys")
    result = shell.evaluate_admission_rule(
        "ADMIT_004", value, evaluation_context=context(value)
    )
    assert result.normalized_values == (("covalent_residue_name", "CYS"),)


def test_adapter_invalid_source_type_fails_closed() -> None:
    with pytest.raises(shell.UnifiedAdmissionDispatchError) as captured:
        shell._adapt_admit_004({"outcome": "passed"})
    assert captured.value.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    assert captured.value.reason == "ADMIT_004_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"


@pytest.mark.parametrize(
    "source",
    (
        Admit004EvaluationResult("ADMIT_999", "passed", True, False, "", "CYS", (), shell.ADMIT_004_CANDIDATE_FIELDS, False, False),
        Admit004EvaluationResult("ADMIT_004", "rejected", False, True, "rejected", "CYS", (), shell.ADMIT_004_CANDIDATE_FIELDS, False, False),
        Admit004EvaluationResult("ADMIT_004", "passed", False, False, "", "CYS", (), shell.ADMIT_004_CANDIDATE_FIELDS, False, False),
        Admit004EvaluationResult("ADMIT_004", "passed", True, False, "unexpected", "CYS", (), shell.ADMIT_004_CANDIDATE_FIELDS, False, False),
        Admit004EvaluationResult("ADMIT_004", "passed", True, False, "", "CYS", (), ("wrong",), False, False),
        Admit004EvaluationResult("ADMIT_004", "passed", True, False, "", "CYS", (), shell.ADMIT_004_CANDIDATE_FIELDS, False, True),
    ),
)
def test_adapter_source_invariants_fail_closed(source: Admit004EvaluationResult) -> None:
    with pytest.raises(shell.UnifiedAdmissionDispatchError) as captured:
        shell._adapt_admit_004(source)
    assert captured.value.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    assert captured.value.reason == "ADMIT_004_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"


def test_input_objects_are_not_mutated_and_repeated_calls_are_deterministic() -> None:
    value = candidate(covalent_residue_name="cys", extra="untouched")
    evaluation = context(value)
    candidate_before = repr(value)
    context_before = repr(evaluation)
    first = shell.evaluate_admission_rule(
        "ADMIT_004", value, evaluation_context=evaluation
    )
    second = shell.evaluate_admission_rule(
        "ADMIT_004", value, evaluation_context=evaluation
    )
    assert first == second
    assert repr(value) == candidate_before
    assert repr(evaluation) == context_before


def test_public_dispatch_path_does_not_use_filesystem_or_subprocess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    value = candidate()
    evaluation = context(value)

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("IO used by public dispatch")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(shell.subprocess, "run", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    result = shell.evaluate_admission_rule(
        "ADMIT_004", value, evaluation_context=evaluation
    )
    assert result.outcome == "passed"


def test_formal_truth_matrix_is_exact24_without_padding() -> None:
    rows = shell._truth_rows()
    assert len(rows) == 24
    assert len({row["case_id"] for row in rows}) == 24
    assert Counter(row["truth_group"] for row in rows) == Counter(
        {"passed": 3, "blocked": 4, "invalid_rule_result": 3, "dispatch_error": 14}
    )
    assert all(row["truth_passed"] == "true" for row in rows)


def test_registry_audit_is_exact15_and_fail_closed() -> None:
    rows = shell._registry_rows()
    assert len(rows) == 15
    assert tuple(row["admission_rule_id"] for row in rows) == shell.KNOWN_RULE_IDS
    assert [row["dispatch_disposition"] for row in rows[:3]] == [
        "adapter_not_ready_fail_closed"
    ] * 3
    assert rows[3]["dispatch_disposition"] == "registered_single_rule_runtime"
    assert [row["dispatch_disposition"] for row in rows[4:]] == [
        "known_not_registered_fail_closed"
    ] * 11
    assert all(row["audit_passed"] == "true" for row in rows)


def test_issue_inventory_is_unchanged_exact12_with_provider_11() -> None:
    snapshot = shell.build_frozen_source_snapshot()
    predecessor = shell._validate_predecessors(snapshot)
    state = shell.build_phase2_state(snapshot)
    assert state["issue_rows"] == [dict(row) for row in predecessor["issues"].rows]
    assert len(state["issue_rows"]) == 12
    issue_map = {row["issue_id"]: row for row in state["issue_rows"]}
    assert issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["issue_count"] == "11"
    for issue_id in (
        "UNIFIED_ADMISSION_LEGACY_EVALUATOR_ADAPTER_SEMANTICS_UNRESOLVED",
        "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
    ):
        assert issue_map[issue_id]["status"] == "open"
        assert issue_map[issue_id]["severity"] == "blocking"


def test_readiness_is_truthful_and_does_not_overclaim() -> None:
    state = shell.build_phase2_state()
    assert state["all_checks_passed"] is True
    payloads, manifest = shell._payloads(state)
    assert len(payloads) == 6
    assert all(manifest[item] is True for item in shell.TRUE_READINESS)
    assert all(manifest[item] is False for item in shell.FALSE_READINESS)
    assert manifest["unified_rule_engine_implemented"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False


def test_materialization_is_deterministic_and_exact6(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    shell.run_covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1(
        first
    )
    shell.run_covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1(
        second
    )
    assert {entry.name for entry in first.iterdir()} == set(shell.OUTPUT_FILES)
    assert {entry.name for entry in second.iterdir()} == set(shell.OUTPUT_FILES)
    assert all(
        (first / name).read_bytes() == (second / name).read_bytes()
        for name in shell.OUTPUT_FILES
    )
    assert not tuple(tmp_path.rglob("*.tmp"))
    assert not tuple(tmp_path.rglob("*.part"))


def test_materializer_rejects_extra_entry_before_writes(tmp_path: Path) -> None:
    root = tmp_path / "output"
    root.mkdir()
    extra = root / "extra"
    extra.write_bytes(b"unchanged")
    with pytest.raises(ValueError, match="unexpected"):
        shell.run_covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1(
            root
        )
    assert extra.read_bytes() == b"unchanged"
    assert {entry.name for entry in root.iterdir()} == {"extra"}


def test_materializer_symlink_victim_is_unchanged(tmp_path: Path) -> None:
    victim = tmp_path / "victim"
    victim.write_bytes(b"unchanged")
    root = tmp_path / "output"
    root.mkdir()
    (root / shell.CONTRACT_FILENAME).symlink_to(victim)
    with pytest.raises(ValueError, match="unsafe"):
        shell.run_covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1(
            root
        )
    assert victim.read_bytes() == b"unchanged"
    assert {entry.name for entry in root.iterdir()} == {shell.CONTRACT_FILENAME}


def test_materializer_rejects_symlink_output_root(tmp_path: Path) -> None:
    victim = tmp_path / "victim"
    victim.mkdir()
    root = tmp_path / "output"
    root.symlink_to(victim, target_is_directory=True)
    with pytest.raises(ValueError, match="real non-symlink"):
        shell.run_covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1(
            root
        )
    assert tuple(victim.iterdir()) == ()


def test_default_outputs_exact_set_hash_and_manifest() -> None:
    result = shell.run_covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1()
    root = result["output_root"]
    assert {entry.name for entry in root.iterdir()} == set(shell.OUTPUT_FILES)
    payloads, expected_manifest = shell._payloads(result["state"])
    assert all((root / name).read_bytes() == payloads[name] for name in shell.OUTPUT_FILES)
    manifest = json.loads((root / shell.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest == expected_manifest
    assert set(manifest["output_sha256"]) == set(shell.CSV_OUTPUTS)
    assert all(
        manifest["output_sha256"][name]
        == hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in shell.CSV_OUTPUTS
    )


def test_import_is_silent_and_has_no_materialization_side_effect(tmp_path: Path) -> None:
    module_name = (
        "covalent_ext."
        "covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004"
    )
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(shell.REPO_ROOT / "src")
    completed = subprocess.run(
        [sys.executable, "-c", f"import {module_name}"],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""
    assert tuple(tmp_path.iterdir()) == ()


def test_production_and_checker_import_boundaries() -> None:
    production_path = shell.REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004.py"
    checker_path = shell.REPO_ROOT / "scripts/check_covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1.py"
    production_tree = ast.parse(production_path.read_text(encoding="utf-8"))
    checker_tree = ast.parse(checker_path.read_text(encoding="utf-8"))
    external_imports = {
        node.module
        for node in production_tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
        and node.module.startswith("covalent_ext")
    }
    assert external_imports == {
        "covalent_ext.covapie_bulk_download_admission_admit_004_rule_logic_interface"
    }
    checker_external = {
        node.module
        for node in checker_tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
        and node.module.startswith("covalent_ext")
    }
    assert checker_external == {"covalent_ext"}


def test_no_all_rules_or_combined_verdict_implementation() -> None:
    source_path = shell.REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    top_level_functions = {
        node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "evaluate_all_rules" not in top_level_functions
    assert "evaluate_combined_candidate_verdict" not in top_level_functions
    assert not hasattr(shell, "evaluate_all_rules")


def test_checker_runs_direct_checks_and_reports_exact_counts() -> None:
    checker = shell.REPO_ROOT / "scripts/check_covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1.py"
    completed = subprocess.run(
        [sys.executable, str(checker)],
        cwd=shell.REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["all_checks_passed"] is True
    assert report["exact_source_count"] == 12
    assert report["truth_matrix_pass_count"] == 24
    assert report["registry_audit_pass_count"] == 15
    assert report["active_issue_count"] == 12
    assert report["provider_blocking_issue_count"] == 11
    assert report["registered_rule_ids"] == ["ADMIT_004"]
    assert len(report["output_sha256"]) == 6
    assert report["ready_for_bulk_download_now"] is False
    assert report["ready_for_training"] is False
