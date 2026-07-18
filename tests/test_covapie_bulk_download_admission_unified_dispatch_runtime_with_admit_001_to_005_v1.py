from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005
    as runtime,
)


@pytest.fixture(scope="module")
def snapshot() -> runtime.FrozenSourceSnapshot:
    return runtime.build_frozen_source_snapshot()


@pytest.fixture(scope="module")
def state(snapshot: runtime.FrozenSourceSnapshot) -> dict[str, Any]:
    value = runtime.build_runtime_state(snapshot)
    assert value["all_checks_passed"] is True
    return value


def _values(value: object, names: tuple[str, ...]) -> tuple[object, ...]:
    return tuple(getattr(value, name) for name in names)


def _valid_candidate() -> dict[str, object]:
    return {
        "covalent_residue_name": "CYS",
        "covalent_residue_atom_name": "SG",
    }


def test_exact16_order_and_sha_are_frozen(snapshot: runtime.FrozenSourceSnapshot) -> None:
    assert len(runtime.SOURCE_PATHS) == 16
    assert len(set(runtime.SOURCE_PATHS)) == 16
    assert tuple(runtime.SOURCE_SHA256) == runtime.SOURCE_PATHS
    assert runtime.validate_frozen_source_snapshot(snapshot)
    for record in snapshot.records:
        assert record.expected_sha256 == runtime.SOURCE_SHA256[record.relative_path]
        assert record.base_tree_sha256 == record.expected_sha256
        assert record.filesystem_sha256 == record.expected_sha256
        assert hashlib.sha256(record.content_bytes).hexdigest() == record.expected_sha256


def test_base_commit_subject_and_lineage() -> None:
    assert runtime.EXPECTED_BASE_COMMIT == "bb255f8f8a4f75f5b61965a589367618d3939850"
    assert runtime.EXPECTED_BASE_SUBJECT == "add CovaPIE ADMIT_005 unified adapter contract design v1"
    runtime._validate_expected_base_lineage(REPO_ROOT)


def test_non_descendant_lineage_fails_closed_without_head_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_git = runtime._git

    def deterministic_git(
        arguments: list[str], repo_root: Path, *, text: bool = True
    ) -> subprocess.CompletedProcess[Any]:
        if arguments[:2] == ["merge-base", "--is-ancestor"]:
            return subprocess.CompletedProcess(arguments, 1, "", "")
        return real_git(arguments, repo_root, text=text)

    monkeypatch.setattr(runtime, "_git", deterministic_git)
    with pytest.raises(ValueError, match="not an ancestor"):
        runtime.build_frozen_source_snapshot(head_ref="deterministic_non_descendant")


def test_all_structural_checks_precede_first_explicit_source_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    structural_calls: list[Path] = []
    real_structural = runtime._structural_source_check
    real_git = runtime._git

    def counted(path: Path, repo_root: Path) -> bool:
        structural_calls.append(path)
        return real_structural(path, repo_root)

    def guarded_git(
        arguments: list[str], repo_root: Path, *, text: bool = True
    ) -> subprocess.CompletedProcess[Any]:
        if arguments and arguments[0] == "show" and len(arguments) == 2 and ":" in arguments[1]:
            assert tuple(structural_calls) == runtime.SOURCE_PATHS
        return real_git(arguments, repo_root, text=text)

    monkeypatch.setattr(runtime, "_structural_source_check", counted)
    monkeypatch.setattr(runtime, "_git", guarded_git)
    assert runtime.validate_frozen_source_snapshot(runtime.build_frozen_source_snapshot())


def test_snapshot_rejects_wrong_shape(snapshot: runtime.FrozenSourceSnapshot) -> None:
    assert runtime.validate_frozen_source_snapshot(object()) is False
    assert runtime.validate_frozen_source_snapshot(runtime.FrozenSourceSnapshot(snapshot.records[:-1])) is False


def test_phase2_type_and_vocabulary_identity() -> None:
    assert runtime.UnifiedAdmissionRuleEvaluation is runtime.phase4.UnifiedAdmissionRuleEvaluation
    assert runtime.UnifiedAdmissionDispatchError is runtime.phase4.UnifiedAdmissionDispatchError
    assert runtime.RESULT_SCHEMA_VERSION is runtime.phase4.RESULT_SCHEMA_VERSION
    assert runtime.RESULT_FIELDS is runtime.phase4.RESULT_FIELDS
    assert runtime.DISPATCH_ERROR_FIELDS is runtime.phase4.DISPATCH_ERROR_FIELDS
    assert runtime.DISPATCH_ERROR_CODES is runtime.phase4.DISPATCH_ERROR_CODES
    assert runtime.OUTCOME_VOCABULARY is runtime.phase4.OUTCOME_VOCABULARY
    assert len(runtime.RESULT_FIELDS) == 13
    assert len(runtime.DISPATCH_ERROR_FIELDS) == 6


def test_public_signature_exactly_matches_phase4() -> None:
    assert inspect.signature(runtime.evaluate_admission_rule) == inspect.signature(
        runtime.phase4.evaluate_admission_rule
    )
    assert not hasattr(runtime, "evaluate_all_rules")


def test_static_registry_and_phase4_handler_identity() -> None:
    assert runtime.KNOWN_RULE_IDS == tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
    assert runtime.CALLABLE_DISCOVERED_RULE_IDS == tuple(f"ADMIT_{index:03d}" for index in range(1, 6))
    assert runtime.ADAPTER_READY_RULE_IDS == runtime.CALLABLE_DISCOVERED_RULE_IDS
    assert runtime.LEGACY_ADAPTER_NOT_READY_RULE_IDS == ()
    assert type(runtime.EVALUATOR_REGISTRY) is MappingProxyType
    assert tuple(runtime.EVALUATOR_REGISTRY) == runtime.ADAPTER_READY_RULE_IDS
    for rule_id in runtime.KNOWN_RULE_IDS[:4]:
        assert runtime.EVALUATOR_REGISTRY[rule_id] is runtime.phase4.EVALUATOR_REGISTRY[rule_id]
        assert runtime.RULE_NAMES[rule_id] == runtime.phase4.RULE_NAMES[rule_id]
        assert runtime.ADAPTER_IDS[rule_id] == runtime.phase4.ADAPTER_IDS[rule_id]
    assert runtime.EVALUATOR_REGISTRY["ADMIT_005"] is runtime._evaluate_registered_admit_005
    assert runtime.RULE_NAMES["ADMIT_005"] == "cys_sg_scope_only_v1"
    assert runtime.ADAPTER_IDS["ADMIT_005"] == "covapie_admit_005_unified_adapter_v1"


@pytest.mark.parametrize(
    ("rule_id", "code", "known", "discovered", "ready", "reported_id"),
    (
        (5, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", False, False, False, ""),
        ("ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", False, False, False, "ADMIT_999"),
        ("ADMIT_006", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", True, False, False, "ADMIT_006"),
        ("ADMIT_015", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", True, False, False, "ADMIT_015"),
    ),
)
def test_global_dispatch_errors(
    rule_id: object,
    code: str,
    known: bool,
    discovered: bool,
    ready: bool,
    reported_id: str,
) -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(rule_id, {})  # type: ignore[arg-type]
    assert _values(caught.value, runtime.DISPATCH_ERROR_FIELDS) == (
        code,
        reported_id,
        known,
        discovered,
        ready,
        code,
    )


@pytest.mark.parametrize("rule_id", runtime.KNOWN_RULE_IDS[5:])
def test_every_admit006_to_015_is_not_registered(rule_id: str) -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(rule_id, {})
    assert caught.value.code == "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"


@pytest.mark.parametrize("case", runtime._phase4_parity_definitions(), ids=lambda case: case["id"])
def test_phase4_representative_parity(case: dict[str, Any]) -> None:
    def invoke(module: object) -> object:
        try:
            return module.evaluate_admission_rule(case["rule"], case["candidate"], **case["kwargs"])
        except runtime.UnifiedAdmissionDispatchError as error:
            return error

    successor = invoke(runtime)
    predecessor = invoke(runtime.phase4)
    assert type(successor) is type(predecessor)
    names = runtime.RESULT_FIELDS if type(successor) is runtime.UnifiedAdmissionRuleEvaluation else runtime.DISPATCH_ERROR_FIELDS
    assert _values(successor, names) == _values(predecessor, names)


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    (
        ({"batch_context": {}}, "ADMIT_005_BATCH_CONTEXT_MUST_BE_NONE"),
        ({"evaluation_context": {}}, "ADMIT_005_EVALUATION_CONTEXT_MUST_BE_NONE"),
        ({"download_result_context": {}}, "ADMIT_005_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ({"stage_authorization_context": {}}, "ADMIT_005_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
        (
            {
                "batch_context": {},
                "evaluation_context": {},
                "download_result_context": {},
                "stage_authorization_context": {},
            },
            "ADMIT_005_BATCH_CONTEXT_MUST_BE_NONE",
        ),
    ),
)
def test_admit005_context_order_and_zero_calls(
    monkeypatch: pytest.MonkeyPatch, kwargs: dict[str, object], reason: str
) -> None:
    counts = {"formal": 0, "scope": 0, "atom": 0}

    def forbidden(name: str) -> Any:
        def call(*args: object) -> object:
            counts[name] += 1
            raise AssertionError(name)

        return call

    monkeypatch.setattr(runtime.admit005, "evaluate_admit_005", forbidden("formal"))
    monkeypatch.setattr(runtime.admit005_oracle, "classify_admit_004_admit_005_atom_scope_design", forbidden("scope"))
    monkeypatch.setattr(runtime.admit005_oracle, "validate_generic_covalent_residue_atom_name", forbidden("atom"))
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule("ADMIT_005", {}, **kwargs)
    assert _values(caught.value, runtime.DISPATCH_ERROR_FIELDS) == (
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "ADMIT_005",
        True,
        True,
        True,
        reason,
    )
    assert counts == {"formal": 0, "scope": 0, "atom": 0}


@pytest.mark.parametrize(
    ("candidate", "reason"),
    (
        ([], "ADMIT_005_CANDIDATE_RECORD_MAPPING_INVALID"),
        ({"covalent_residue_atom_name": "SG"}, "ADMIT_005_CANDIDATE_FIELD_MISSING:covalent_residue_name"),
        ({"covalent_residue_name": "CYS"}, "ADMIT_005_CANDIDATE_FIELD_MISSING:covalent_residue_atom_name"),
        ({}, "ADMIT_005_CANDIDATE_FIELD_MISSING:covalent_residue_name"),
    ),
)
def test_candidate_envelope_invalid_exact13_and_zero_calls(
    monkeypatch: pytest.MonkeyPatch, candidate: object, reason: str
) -> None:
    monkeypatch.setattr(runtime.admit005, "evaluate_admit_005", lambda *args: pytest.fail("formal called"))
    monkeypatch.setattr(runtime.admit005_oracle, "classify_admit_004_admit_005_atom_scope_design", lambda *args: pytest.fail("scope called"))
    monkeypatch.setattr(runtime.admit005_oracle, "validate_generic_covalent_residue_atom_name", lambda *args: pytest.fail("atom called"))
    result = runtime.evaluate_admission_rule("ADMIT_005", candidate)  # type: ignore[arg-type]
    assert _values(result, runtime.RESULT_FIELDS) == (
        runtime.RESULT_SCHEMA_VERSION,
        "ADMIT_005",
        "cys_sg_scope_only_v1",
        "invalid",
        False,
        True,
        reason,
        (),
        (),
        runtime.ADMIT_005_CANDIDATE_FIELDS,
        (),
        False,
        "covapie_admit_005_unified_adapter_v1",
    )


def test_mapping_subclass_extra_fields_identity_and_no_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Candidate(dict[str, object]):
        pass

    residue = object()
    atom = object()
    extra = object()
    candidate = Candidate(
        covalent_residue_name=residue,
        covalent_residue_atom_name=atom,
        extra=extra,
    )
    before = dict(candidate)
    source = runtime.admit005.evaluate_admit_005("CYS", "SG")
    formal_args: list[tuple[object, object]] = []
    scope_args: list[tuple[object, object]] = []
    atom_args: list[object] = []
    monkeypatch.setattr(runtime.admit005, "evaluate_admit_005", lambda r, a: formal_args.append((r, a)) or source)
    scope_result = runtime.admit005_oracle.classify_admit_004_admit_005_atom_scope_design("CYS", "SG")
    atom_result = runtime.admit005_oracle.validate_generic_covalent_residue_atom_name("SG")
    monkeypatch.setattr(runtime.admit005_oracle, "classify_admit_004_admit_005_atom_scope_design", lambda r, a: scope_args.append((r, a)) or scope_result)
    monkeypatch.setattr(runtime.admit005_oracle, "validate_generic_covalent_residue_atom_name", lambda a: atom_args.append(a) or atom_result)
    result = runtime.evaluate_admission_rule("ADMIT_005", candidate)
    assert result.outcome == "passed"
    assert formal_args == [(residue, atom)]
    assert scope_args == [(residue, atom)]
    assert atom_args == [atom]
    assert candidate == before
    assert candidate["extra"] is extra


@pytest.mark.parametrize(
    ("residue", "atom", "outcome", "reason", "validated"),
    (
        ("CYS", "SG", "passed", "", (("covalent_residue_name", "CYS"), ("covalent_residue_atom_name", "SG"))),
        ("SER", "SG", "rejected", "ADMIT_005_CYS_SG_SCOPE_REJECTED", (("covalent_residue_name", "SER"), ("covalent_residue_atom_name", "SG"))),
        (7, "SG", "invalid", "COVALENT_RESIDUE_NAME_TYPE_INVALID", ()),
        ("CYS", 7, "invalid", "COVALENT_RESIDUE_ATOM_NAME_TYPE_INVALID", (("covalent_residue_name", "CYS"),)),
    ),
)
def test_exact13_projection_and_rejected_passthrough(
    residue: object,
    atom: object,
    outcome: str,
    reason: str,
    validated: tuple[tuple[str, str], ...],
) -> None:
    result = runtime.evaluate_admission_rule(
        "ADMIT_005",
        {"covalent_residue_name": residue, "covalent_residue_atom_name": atom},
    )
    assert result.outcome == outcome
    assert result.passed is (outcome == "passed")
    assert result.blocks_candidate is (outcome != "passed")
    assert result.reason == reason
    assert result.normalized_values == validated
    assert result.validated_candidate_fields == validated
    assert result.consumed_candidate_fields == runtime.ADMIT_005_CANDIDATE_FIELDS
    assert result.consumed_context_items == ()
    assert result.evaluator_io_used is False


@pytest.mark.parametrize(
    ("source_factory", "reason"),
    (
        (lambda valid: object(), "ADMIT_005_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"),
        (
            lambda valid: type("SourceSubclass", (runtime.admit005.Admit005EvaluationResult,), {})(
                *(_values(valid, runtime.admit005.RESULT_FIELDS))
            ),
            "ADMIT_005_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        ),
        (lambda valid: _mutate(valid, "admission_rule_id", "ADMIT_004"), "ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "passed", False), "ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "evaluator_io_used", True), "ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "consumed_candidate_fields", ("covalent_residue_name",)), "ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
    ),
)
def test_source_prevalidation_fails_before_oracles(
    monkeypatch: pytest.MonkeyPatch,
    source_factory: Any,
    reason: str,
) -> None:
    source = source_factory(runtime.admit005.evaluate_admit_005("CYS", "SG"))
    counts = {"formal": 0, "scope": 0, "atom": 0}
    monkeypatch.setattr(runtime.admit005, "evaluate_admit_005", lambda *args: counts.__setitem__("formal", counts["formal"] + 1) or source)
    monkeypatch.setattr(runtime.admit005_oracle, "classify_admit_004_admit_005_atom_scope_design", lambda *args: counts.__setitem__("scope", counts["scope"] + 1) or pytest.fail("scope called"))
    monkeypatch.setattr(runtime.admit005_oracle, "validate_generic_covalent_residue_atom_name", lambda *args: counts.__setitem__("atom", counts["atom"] + 1) or pytest.fail("atom called"))
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule("ADMIT_005", _valid_candidate())
    assert caught.value.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    assert caught.value.adapter_ready is False
    assert caught.value.reason == reason
    assert counts == {"formal": 1, "scope": 0, "atom": 0}


def _mutate(value: object, name: str, replacement: object) -> object:
    object.__setattr__(value, name, replacement)
    return value


def test_oracle_mismatch_calls_all_once_and_has_no_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = runtime.admit005.evaluate_admit_005("CYS", "SG")
    mismatch_scope = runtime.admit005_oracle.classify_admit_004_admit_005_atom_scope_design("SER", "SG")
    real_atom = runtime.admit005_oracle.validate_generic_covalent_residue_atom_name("SG")
    counts = Counter()
    monkeypatch.setattr(runtime.admit005, "evaluate_admit_005", lambda *args: counts.update(["formal"]) or source)
    monkeypatch.setattr(runtime.admit005_oracle, "classify_admit_004_admit_005_atom_scope_design", lambda *args: counts.update(["scope"]) or mismatch_scope)
    monkeypatch.setattr(runtime.admit005_oracle, "validate_generic_covalent_residue_atom_name", lambda *args: counts.update(["atom"]) or real_atom)
    monkeypatch.setattr(runtime, "_project_admit005_exact13", lambda *args: pytest.fail("projected"))
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule("ADMIT_005", _valid_candidate())
    assert caught.value.reason == "ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert counts == {"formal": 1, "scope": 1, "atom": 1}


def test_exact22_distribution_and_projection(snapshot: runtime.FrozenSourceSnapshot) -> None:
    predecessor = runtime._validate_predecessors(snapshot)
    counts: Counter[str] = Counter()
    for row in predecessor["standalone_truth_rows"]:
        residue = runtime._decode_truth_input(row["residue_input_kind"], row["residue_input_display"])
        atom = runtime._decode_truth_input(row["atom_input_kind"], row["atom_input_display"])
        result = runtime.evaluate_admission_rule("ADMIT_005", {"covalent_residue_name": residue, "covalent_residue_atom_name": atom})
        assert result.outcome == row["observed_outcome"]
        assert result.reason == row["observed_reason"]
        counts[result.outcome] += 1
    assert counts == {"passed": 2, "rejected": 6, "invalid": 14}


def test_runtime_state_rows_and_groups(state: dict[str, Any]) -> None:
    assert len(state["truth_rows"]) == 71
    assert state["truth_group_counts"] == {
        "global_dispatch": 12,
        "phase4_parity": 14,
        "admit005_context": 5,
        "admit005_candidate": 8,
        "admit005_exact22": 22,
        "admit005_source_prevalidation": 6,
        "admit005_oracle_mismatch": 1,
        "registry_boundary": 3,
    }
    assert len(state["contract_rows"]) == len(runtime._contract_definitions()) == 35
    assert len(state["registry_rows"]) == 15
    assert all(row["case_passed"] == "true" for row in state["truth_rows"])


def test_issue_inventory_updates_only_coverage_row(state: dict[str, Any]) -> None:
    old = list(state["predecessor"]["phase4_issue_rows"])
    new = state["issue_rows"]
    assert len(old) == len(new) == 11
    for old_row, new_row in zip(old, new, strict=True):
        if old_row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE":
            assert new_row["affected_rules"] == "|".join(runtime.KNOWN_RULE_IDS[5:])
            assert new_row["integration_transition"] == "admit_005_implemented_and_removed_from_open_coverage_scope"
            for key in runtime.ISSUE_COLUMNS:
                if key not in ("affected_rules", "integration_transition"):
                    assert new_row[key] == old_row[key]
        else:
            assert new_row == old_row


def test_manifest_readiness_and_truthfulness(state: dict[str, Any]) -> None:
    _, manifest = runtime._payloads(state)
    assert manifest["runtime_dependency_imports_authorized"] is True
    assert manifest["frozen_source_snapshot_explicit_byte_reads_preflighted"] is True
    assert manifest["phase4_runtime_modified"] is False
    assert manifest["phase4_handlers_reused_by_identity"] is True
    assert manifest["registered_rule_count"] == 5
    assert manifest["registered_rule_ids"] == list(runtime.ADAPTER_READY_RULE_IDS)
    assert manifest["admit_005_implemented"] is True
    assert manifest["admit_005_registered"] is True
    assert manifest["admit_006_to_015_registered"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["feature_semantics_audit_required"] is True
    assert manifest["output_sha256_excludes_manifest_self_hash"] is True
    assert runtime.MANIFEST_FILENAME not in manifest["output_sha256"]


def test_double_materialization_is_byte_identical(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005_v1(root)
    first = {path.name: path.read_bytes() for path in root.iterdir()}
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005_v1(root)
    second = {path.name: path.read_bytes() for path in root.iterdir()}
    assert first == second
    assert set(first) == set(runtime.OUTPUT_FILES)
    assert not tuple(root.glob("*.tmp"))
    assert not tuple(root.glob("*.part"))


@pytest.mark.parametrize("unsafe_name", ("unexpected.txt", "nested"))
def test_materializer_rejects_unexpected_entries(tmp_path: Path, unsafe_name: str) -> None:
    root = tmp_path / "outputs"
    root.mkdir()
    unsafe = root / unsafe_name
    if unsafe_name == "nested":
        unsafe.mkdir()
    else:
        unsafe.write_text("safe", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected"):
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005_v1(root)


def test_materializer_symlink_victim_is_not_modified(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    root.mkdir()
    victim = tmp_path / "victim"
    victim.write_text("do-not-touch", encoding="utf-8")
    (root / runtime.CONTRACT_FILENAME).symlink_to(victim)
    with pytest.raises(ValueError, match="unsafe"):
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005_v1(root)
    assert victim.read_text(encoding="utf-8") == "do-not-touch"


def test_output_root_symlink_is_rejected(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="real non-symlink"):
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005_v1(link)


def test_default_outputs_match_generated_payloads(state: dict[str, Any]) -> None:
    payloads, _ = runtime._payloads(state)
    root = REPO_ROOT / runtime.DEFAULT_OUTPUT_ROOT
    assert {path.name for path in root.iterdir()} == set(runtime.OUTPUT_FILES)
    for filename in runtime.OUTPUT_FILES:
        assert (root / filename).read_bytes() == payloads[filename]


def test_import_has_no_output_side_effect(tmp_path: Path) -> None:
    script = "from covalent_ext import covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005"
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(SRC_ROOT)},
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""
    assert list(tmp_path.iterdir()) == []


def test_no_disallowed_runtime_dependency_import() -> None:
    source = (REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005.py").read_text(encoding="utf-8")
    import_section = source.split("PROJECT =", 1)[0]
    assert "admit_005_unified_adapter_contract_design_gate" not in import_section
    assert "torch" not in import_section
    assert "numpy" not in import_section
    assert "rdkit" not in import_section
