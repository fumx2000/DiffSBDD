from __future__ import annotations

import ast
import dataclasses
import hashlib
import importlib
import importlib.util
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
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004
    as runtime,
)


@pytest.fixture(scope="module")
def snapshot() -> runtime.FrozenSourceSnapshot:
    return runtime.build_frozen_source_snapshot()


@pytest.fixture(scope="module")
def state(snapshot: runtime.FrozenSourceSnapshot) -> dict[str, Any]:
    value = runtime.build_phase4_state(snapshot)
    assert value["all_checks_passed"] is True
    return value


def _error_fields(error: runtime.UnifiedAdmissionDispatchError) -> tuple[object, ...]:
    return tuple(getattr(error, name) for name in runtime.DISPATCH_ERROR_FIELDS)


def _valid_spec(rule_id: str) -> tuple[object, str, object, str, dict[str, object], dict[str, object]]:
    if rule_id == "ADMIT_001":
        return (
            runtime.admit001_legacy,
            "evaluate_admit_001_candidate_record_id",
            runtime.admit001_oracle,
            "evaluate_candidate_record_id_batch_uniqueness",
            {"candidate_record_id": "REC_1"},
            {"batch_context": {"batch_candidate_record_ids": ["REC_1"]}},
        )
    if rule_id == "ADMIT_002":
        return (
            runtime.admit002_legacy,
            "evaluate_admit_002_pdb_identifier",
            runtime.admit002_oracle,
            "normalize_pdb_identifier",
            {"pdb_id": "1abc"},
            {},
        )
    if rule_id == "ADMIT_003":
        return (
            runtime.admit003_legacy,
            "evaluate_admit_003_ligand_comp_id",
            runtime.admit003_oracle,
            "normalize_ligand_comp_id",
            {"ligand_comp_id": "abc"},
            {},
        )
    raise AssertionError(rule_id)


def _real_legacy_source(rule_id: str) -> dict[str, object]:
    legacy_module, legacy_name, _, _, candidate, kwargs = _valid_spec(rule_id)
    function = vars(legacy_module)[legacy_name]
    if rule_id == "ADMIT_001":
        batch = kwargs["batch_context"]
        assert isinstance(batch, dict)
        return function(
            candidate["candidate_record_id"], batch["batch_candidate_record_ids"]
        )
    field = "pdb_id" if rule_id == "ADMIT_002" else "ligand_comp_id"
    return function(candidate[field])


def test_exact14_order_and_sha_constants_are_frozen() -> None:
    assert len(runtime.SOURCE_PATHS) == 14
    assert len(set(runtime.SOURCE_PATHS)) == 14
    assert tuple(runtime.SOURCE_SHA256) == runtime.SOURCE_PATHS
    assert tuple(runtime.SOURCE_SHA256.values()) == (
        "46023c4c3fc221a3e87c513210079e6ef5909ed7c377c1b52dc564fcf171f978",
        "702492ff08760f3cddcdedd724f8078795d998a736958c87bb39642fa793c097",
        "1290eb1cd88d95e6950c64204f16153cae6560aa7ba922ae4977d07b141535af",
        "91e23f622b1c5109110a7f3f7b1fc0ebe68a7e718600df2b87851843be51c4e8",
        "62392a4026f07ef3c6fb94832f45451d6437e001959b5140229c20150f34e707",
        "be79b98c695d989f27c694aab3d460990fea735ee8308b620eb6d10a98b3b757",
        "4a7465b6ec0550635578ef9e65cafd49467448e2fdfd3fe49889318b08f5421e",
        "32dd20579fb47aae0deb1e074fc8feeff5b92b8cbdd44b4089c7ef15a590a754",
        "3246a131a3815aa184338637edef6d8c9020b2dc23f41794e5697812467d269b",
        "625b1b5e2e4da30aa0fff80efd8fd3ceaceb1807bd3a376d169f5374bbd6fda7",
        "c78ed4986551913dea75dc220609f97154941ebda5afffaa84ff252e9d36df83",
        "74395681955025519e35569b8d7353139e4363a840908d0749f5ea5c2cb51e0d",
        "8d616a02b5f87ea98be3029879d55acd3c06c26e7286a46cb293bd6a4a7f6e11",
        "2623377368459484daf25828db556fc6e6a2436893c70497f0628d95ffbb1792",
    )


def test_snapshot_matches_expected_base_tree_and_filesystem(
    snapshot: runtime.FrozenSourceSnapshot,
) -> None:
    assert runtime.validate_frozen_source_snapshot(snapshot)
    assert tuple(record.relative_path for record in snapshot.records) == runtime.SOURCE_PATHS
    for record in snapshot.records:
        assert record.expected_sha256 == runtime.SOURCE_SHA256[record.relative_path]
        assert record.base_tree_sha256 == record.expected_sha256
        assert record.filesystem_sha256 == record.expected_sha256
        assert hashlib.sha256(record.content_bytes).hexdigest() == record.expected_sha256


def test_base_object_subject_and_successor_lineage() -> None:
    assert runtime.EXPECTED_BASE_COMMIT == "759f19b8e84d68a531b791ff683033812549ce80"
    assert runtime.EXPECTED_BASE_SUBJECT == (
        "add CovaPIE ADMIT_001 to ADMIT_003 legacy adapter contracts v1"
    )
    runtime._validate_expected_base_lineage(REPO_ROOT)


def test_non_descendant_head_ref_fails_closed() -> None:
    parent = subprocess.run(
        ["git", "rev-parse", f"{runtime.EXPECTED_BASE_COMMIT}^"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    with pytest.raises(ValueError, match="not an ancestor"):
        runtime.build_frozen_source_snapshot(head_ref=parent)


def test_all_structural_checks_precede_first_source_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_structural = runtime._structural_source_check
    real_git = runtime._git
    structural_calls: list[Path] = []

    def counted_structural(path: Path, repo_root: Path) -> bool:
        structural_calls.append(path)
        return real_structural(path, repo_root)

    def guarded_git(
        arguments: list[str], repo_root: Path, *, text: bool = True
    ) -> subprocess.CompletedProcess[Any]:
        if arguments and arguments[0] == "show" and len(arguments) == 2 and ":" in arguments[1]:
            assert tuple(structural_calls) == runtime.SOURCE_PATHS
        return real_git(arguments, repo_root, text=text)

    monkeypatch.setattr(runtime, "_structural_source_check", counted_structural)
    monkeypatch.setattr(runtime, "_git", guarded_git)
    built = runtime.build_frozen_source_snapshot()
    assert runtime.validate_frozen_source_snapshot(built)


def test_missing_and_symlink_source_structures_fail_closed(tmp_path: Path) -> None:
    missing = tmp_path / "missing.py"
    assert runtime._structural_source_check(missing, REPO_ROOT) is False
    victim = tmp_path / "victim"
    victim.write_text("safe", encoding="utf-8")
    link = tmp_path / "link"
    link.symlink_to(victim)
    assert runtime._structural_source_check(link, REPO_ROOT) is False
    assert victim.read_text(encoding="utf-8") == "safe"


def test_snapshot_content_hash_tamper_fails_closed(
    snapshot: runtime.FrozenSourceSnapshot,
) -> None:
    first = snapshot.records[0]
    corrupt = dataclasses.replace(first, content_bytes=first.content_bytes + b"\n")
    tampered = runtime.FrozenSourceSnapshot((corrupt, *snapshot.records[1:]))
    assert runtime.validate_frozen_source_snapshot(tampered) is False
    failed = runtime.build_phase4_state(tampered)
    assert failed["all_checks_passed"] is False


def test_phase2_exact13_exact6_type_identity_reused() -> None:
    assert runtime.UnifiedAdmissionRuleEvaluation is runtime.phase2.UnifiedAdmissionRuleEvaluation
    assert runtime.UnifiedAdmissionDispatchError is runtime.phase2.UnifiedAdmissionDispatchError
    assert tuple(
        field.name for field in dataclasses.fields(runtime.UnifiedAdmissionRuleEvaluation)
    ) == runtime.RESULT_FIELDS
    assert tuple(
        field.name for field in dataclasses.fields(runtime.UnifiedAdmissionDispatchError)
    ) == runtime.DISPATCH_ERROR_FIELDS
    assert len(runtime.RESULT_FIELDS) == 13
    assert len(runtime.DISPATCH_ERROR_FIELDS) == 6
    assert runtime.DISPATCH_ERROR_CODES == runtime.phase2.DISPATCH_ERROR_CODES


def test_public_signature_is_exact() -> None:
    signature = inspect.signature(runtime.evaluate_admission_rule)
    assert tuple(signature.parameters) == (
        "admission_rule_id",
        "candidate_record",
        "batch_context",
        "evaluation_context",
        "download_result_context",
        "stage_authorization_context",
    )
    assert signature.parameters["batch_context"].kind is inspect.Parameter.KEYWORD_ONLY
    assert all(
        signature.parameters[name].default is None
        for name in (
            "batch_context",
            "evaluation_context",
            "download_result_context",
            "stage_authorization_context",
        )
    )


def test_registry_is_immutable_static_and_exact001_to004() -> None:
    assert type(runtime.EVALUATOR_REGISTRY) is MappingProxyType
    assert tuple(runtime.EVALUATOR_REGISTRY) == (
        "ADMIT_001",
        "ADMIT_002",
        "ADMIT_003",
        "ADMIT_004",
    )
    assert all(callable(value) for value in runtime.EVALUATOR_REGISTRY.values())
    assert runtime.ADAPTER_READY_RULE_IDS == tuple(runtime.EVALUATOR_REGISTRY)
    assert runtime.LEGACY_ADAPTER_NOT_READY_RULE_IDS == ()
    with pytest.raises(TypeError):
        runtime.EVALUATOR_REGISTRY["ADMIT_005"] = lambda: None  # type: ignore[index]


@pytest.mark.parametrize(
    ("rule_id", "expected"),
    (
        (1, ("UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "", False, False, False)),
        ("ADMIT_999", ("UNIFIED_ADMISSION_RULE_ID_UNKNOWN", "ADMIT_999", False, False, False)),
        ("ADMIT_005", ("UNIFIED_ADMISSION_RULE_NOT_REGISTERED", "ADMIT_005", True, False, False)),
        ("ADMIT_015", ("UNIFIED_ADMISSION_RULE_NOT_REGISTERED", "ADMIT_015", True, False, False)),
    ),
)
def test_global_dispatch_precedence(
    rule_id: object, expected: tuple[object, ...]
) -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(  # type: ignore[arg-type]
            rule_id,
            {},
            batch_context={},
            evaluation_context={},
            download_result_context={},
            stage_authorization_context={},
        )
    assert _error_fields(caught.value)[:5] == expected


def test_rule_id_str_subclass_is_exact_type_invalid() -> None:
    class RuleIdSubclass(str):
        pass

    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(RuleIdSubclass("ADMIT_001"), {})
    assert caught.value.code == "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"
    assert caught.value.admission_rule_id == ""


CONTEXT_CASES = (
    ("ADMIT_001", {}, {}, "ADMIT_001_BATCH_CONTEXT_MAPPING_REQUIRED"),
    ("ADMIT_001", {}, {"batch_context": {}}, "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_REQUIRED"),
    ("ADMIT_001", {}, {"batch_context": {"batch_candidate_record_ids": set()}}, "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_EXACT_LIST_OR_TUPLE_REQUIRED"),
    ("ADMIT_001", {}, {"batch_context": {"batch_candidate_record_ids": []}}, "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_NONEMPTY_REQUIRED"),
    ("ADMIT_001", {}, {"batch_context": {"batch_candidate_record_ids": ["bad space"]}}, "ADMIT_001_BATCH_CANDIDATE_RECORD_ID_MEMBER_INVALID"),
    ("ADMIT_001", {}, {"batch_context": {"batch_candidate_record_ids": ["REC_1"]}, "evaluation_context": {}}, "ADMIT_001_EVALUATION_CONTEXT_MUST_BE_NONE"),
    ("ADMIT_001", {}, {"batch_context": {"batch_candidate_record_ids": ["REC_1"]}, "download_result_context": {}}, "ADMIT_001_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
    ("ADMIT_001", {}, {"batch_context": {"batch_candidate_record_ids": ["REC_1"]}, "stage_authorization_context": {}}, "ADMIT_001_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
    ("ADMIT_002", {"pdb_id": "1abc"}, {"batch_context": {}}, "ADMIT_002_BATCH_CONTEXT_MUST_BE_NONE"),
    ("ADMIT_002", {"pdb_id": "1abc"}, {"evaluation_context": {}}, "ADMIT_002_EVALUATION_CONTEXT_MUST_BE_NONE"),
    ("ADMIT_002", {"pdb_id": "1abc"}, {"download_result_context": {}}, "ADMIT_002_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
    ("ADMIT_002", {"pdb_id": "1abc"}, {"stage_authorization_context": {}}, "ADMIT_002_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
    ("ADMIT_003", {"ligand_comp_id": "ABC"}, {"batch_context": {}}, "ADMIT_003_BATCH_CONTEXT_MUST_BE_NONE"),
    ("ADMIT_003", {"ligand_comp_id": "ABC"}, {"evaluation_context": {}}, "ADMIT_003_EVALUATION_CONTEXT_MUST_BE_NONE"),
    ("ADMIT_003", {"ligand_comp_id": "ABC"}, {"download_result_context": {}}, "ADMIT_003_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
    ("ADMIT_003", {"ligand_comp_id": "ABC"}, {"stage_authorization_context": {}}, "ADMIT_003_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
)


@pytest.mark.parametrize(("rule_id", "candidate", "kwargs", "reason"), CONTEXT_CASES)
def test_exact16_context_routing_errors(
    rule_id: str,
    candidate: dict[str, object],
    kwargs: dict[str, object],
    reason: str,
) -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(rule_id, candidate, **kwargs)
    error = caught.value
    assert error.code == "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"
    assert error.reason == reason
    assert _error_fields(error)[1:5] == (rule_id, True, True, True)


def test_context_routing_order_is_fixed() -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(
            "ADMIT_001",
            {},
            batch_context={},
            evaluation_context={},
            download_result_context={},
            stage_authorization_context={},
        )
    assert caught.value.reason == "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_REQUIRED"
    for rule_id, field in (("ADMIT_002", "pdb_id"), ("ADMIT_003", "ligand_comp_id")):
        with pytest.raises(runtime.UnifiedAdmissionDispatchError) as next_error:
            runtime.evaluate_admission_rule(
                rule_id,
                {field: "ABC"},
                batch_context={},
                evaluation_context={},
                download_result_context={},
                stage_authorization_context={},
            )
        assert next_error.value.reason == f"{rule_id}_BATCH_CONTEXT_MUST_BE_NONE"


@pytest.mark.parametrize(
    ("rule_id", "candidate", "kwargs", "reason", "field", "contexts", "adapter_id", "name"),
    (
        ("ADMIT_001", [], {"batch_context": {"batch_candidate_record_ids": ["REC_1"]}}, "ADMIT_001_CANDIDATE_RECORD_MAPPING_INVALID", "candidate_record_id", ("batch_candidate_record_ids",), "covapie_admit_001_unified_adapter_v1", "unique_candidate_identity"),
        ("ADMIT_001", {}, {"batch_context": {"batch_candidate_record_ids": ["REC_1"]}}, "ADMIT_001_CANDIDATE_FIELD_MISSING:candidate_record_id", "candidate_record_id", ("batch_candidate_record_ids",), "covapie_admit_001_unified_adapter_v1", "unique_candidate_identity"),
        ("ADMIT_002", [], {}, "ADMIT_002_CANDIDATE_RECORD_MAPPING_INVALID", "pdb_id", (), "covapie_admit_002_unified_adapter_v1", "valid_pdb_id_format"),
        ("ADMIT_002", {}, {}, "ADMIT_002_CANDIDATE_FIELD_MISSING:pdb_id", "pdb_id", (), "covapie_admit_002_unified_adapter_v1", "valid_pdb_id_format"),
        ("ADMIT_003", [], {}, "ADMIT_003_CANDIDATE_RECORD_MAPPING_INVALID", "ligand_comp_id", (), "covapie_admit_003_unified_adapter_v1", "ligand_or_het_identity_present"),
        ("ADMIT_003", {}, {}, "ADMIT_003_CANDIDATE_FIELD_MISSING:ligand_comp_id", "ligand_comp_id", (), "covapie_admit_003_unified_adapter_v1", "ligand_or_het_identity_present"),
    ),
)
def test_exact6_adapter_side_invalid_payloads(
    rule_id: str,
    candidate: object,
    kwargs: dict[str, object],
    reason: str,
    field: str,
    contexts: tuple[str, ...],
    adapter_id: str,
    name: str,
) -> None:
    result = runtime.evaluate_admission_rule(rule_id, candidate, **kwargs)  # type: ignore[arg-type]
    assert dataclasses.astuple(result) == (
        runtime.RESULT_SCHEMA_VERSION,
        rule_id,
        name,
        "invalid",
        False,
        True,
        reason,
        (),
        (),
        (field,),
        contexts,
        False,
        adapter_id,
    )


@pytest.mark.parametrize("rule_id", ("ADMIT_001", "ADMIT_002", "ADMIT_003"))
def test_context_and_candidate_projection_failures_call_neither_evaluator(
    monkeypatch: pytest.MonkeyPatch, rule_id: str
) -> None:
    legacy_module, legacy_name, oracle_module, oracle_name, _, kwargs = _valid_spec(rule_id)
    legacy_calls = 0
    oracle_calls = 0

    def legacy(*args: object) -> object:
        nonlocal legacy_calls
        legacy_calls += 1
        raise AssertionError

    def oracle(*args: object) -> object:
        nonlocal oracle_calls
        oracle_calls += 1
        raise AssertionError

    monkeypatch.setattr(legacy_module, legacy_name, legacy)
    monkeypatch.setattr(oracle_module, oracle_name, oracle)
    invalid_candidate: object = []
    result = runtime.evaluate_admission_rule(rule_id, invalid_candidate, **kwargs)  # type: ignore[arg-type]
    assert result.outcome == "invalid"
    assert legacy_calls == 0
    assert oracle_calls == 0


@pytest.mark.parametrize("rule_id", ("ADMIT_001", "ADMIT_002", "ADMIT_003"))
def test_original_values_context_identity_extra_exclusion_and_no_mutation(
    monkeypatch: pytest.MonkeyPatch, rule_id: str
) -> None:
    legacy_module, legacy_name, oracle_module, oracle_name, candidate, kwargs = _valid_spec(rule_id)
    field = {"ADMIT_001": "candidate_record_id", "ADMIT_002": "pdb_id", "ADMIT_003": "ligand_comp_id"}[rule_id]
    value = "".join(str(candidate[field]))
    candidate = {field: value, "extra": object()}
    batch_ids: object | None = None
    if rule_id == "ADMIT_001":
        batch_ids = [value]
        kwargs = {"batch_context": {"batch_candidate_record_ids": batch_ids}}
    before_keys = tuple(candidate)
    extra = candidate["extra"]
    real_legacy = vars(legacy_module)[legacy_name]
    real_oracle = vars(oracle_module)[oracle_name]
    calls = {"legacy": 0, "oracle": 0}

    def checked_legacy(*args: object) -> object:
        calls["legacy"] += 1
        assert args[0] is value
        assert extra not in args
        if batch_ids is not None:
            assert args[1] is batch_ids
        return real_legacy(*args)

    def checked_oracle(*args: object) -> object:
        calls["oracle"] += 1
        assert args[0] is value
        assert extra not in args
        if batch_ids is not None:
            assert args[1] is batch_ids
        return real_oracle(*args)

    monkeypatch.setattr(legacy_module, legacy_name, checked_legacy)
    monkeypatch.setattr(oracle_module, oracle_name, checked_oracle)
    result = runtime.evaluate_admission_rule(rule_id, candidate, **kwargs)
    assert result.outcome == "passed"
    assert calls == {"legacy": 1, "oracle": 1}
    assert tuple(candidate) == before_keys
    assert candidate[field] is value
    assert candidate["extra"] is extra


def test_pdb_str_subclass_behavior_is_preserved() -> None:
    class PdbSubclass(str):
        pass

    value = PdbSubclass("1AbC")
    result = runtime.evaluate_admission_rule("ADMIT_002", {"pdb_id": value})
    assert result.outcome == "passed"
    assert result.normalized_values == (("pdb_id", "pdb_00001abc"),)


@pytest.mark.parametrize("rule_id", ("ADMIT_001", "ADMIT_002", "ADMIT_003"))
def test_legacy_source_non_exact_dict_fails_before_oracle(
    monkeypatch: pytest.MonkeyPatch, rule_id: str
) -> None:
    legacy_module, legacy_name, oracle_module, oracle_name, candidate, kwargs = _valid_spec(rule_id)
    oracle_calls = 0

    class DictSubclass(dict[str, object]):
        pass

    def oracle(*args: object) -> object:
        nonlocal oracle_calls
        oracle_calls += 1
        raise AssertionError

    monkeypatch.setattr(legacy_module, legacy_name, lambda *args: DictSubclass())
    monkeypatch.setattr(oracle_module, oracle_name, oracle)
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(rule_id, candidate, **kwargs)
    assert caught.value.reason == f"{rule_id}_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
    assert oracle_calls == 0


@pytest.mark.parametrize("rule_id", ("ADMIT_001", "ADMIT_002", "ADMIT_003"))
@pytest.mark.parametrize("corruption", ("missing", "extra", "order"))
def test_legacy_exact_key_shape_fails_closed(
    monkeypatch: pytest.MonkeyPatch, rule_id: str, corruption: str
) -> None:
    legacy_module, legacy_name, oracle_module, oracle_name, candidate, kwargs = _valid_spec(rule_id)
    source = _real_legacy_source(rule_id)
    if corruption == "missing":
        source.pop(next(reversed(source)))
    elif corruption == "extra":
        source["extra"] = ""
    else:
        source = dict(reversed(tuple(source.items())))
    oracle_calls = 0

    def oracle(*args: object) -> object:
        nonlocal oracle_calls
        oracle_calls += 1
        raise AssertionError

    monkeypatch.setattr(legacy_module, legacy_name, lambda *args: source)
    monkeypatch.setattr(oracle_module, oracle_name, oracle)
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(rule_id, candidate, **kwargs)
    assert caught.value.reason == f"{rule_id}_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert oracle_calls == 0


@pytest.mark.parametrize("rule_id", ("ADMIT_001", "ADMIT_002", "ADMIT_003"))
def test_legacy_field_types_fail_before_oracle(
    monkeypatch: pytest.MonkeyPatch, rule_id: str
) -> None:
    legacy_module, legacy_name, oracle_module, oracle_name, candidate, kwargs = _valid_spec(rule_id)
    source = _real_legacy_source(rule_id)
    source["passed"] = 1
    oracle_calls = 0

    def oracle(*args: object) -> object:
        nonlocal oracle_calls
        oracle_calls += 1
        raise AssertionError

    monkeypatch.setattr(legacy_module, legacy_name, lambda *args: source)
    monkeypatch.setattr(oracle_module, oracle_name, oracle)
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(rule_id, candidate, **kwargs)
    assert caught.value.reason == f"{rule_id}_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert oracle_calls == 0


@pytest.mark.parametrize("rule_id", ("ADMIT_001", "ADMIT_002", "ADMIT_003"))
@pytest.mark.parametrize("corruption", ("known_reason", "canonical"))
def test_known_wrong_legacy_values_fail_oracle_equivalence(
    monkeypatch: pytest.MonkeyPatch, rule_id: str, corruption: str
) -> None:
    legacy_module, legacy_name, oracle_module, oracle_name, candidate, kwargs = _valid_spec(rule_id)
    source = _real_legacy_source(rule_id)
    if corruption == "known_reason":
        source["blocking_reason"] = next(
            reason for reason in runtime.REASON_OUTCOMES[rule_id] if reason
        )
    else:
        canonical_key = {
            "ADMIT_001": "normalized_candidate_record_id",
            "ADMIT_002": "canonical_pdb_id",
            "ADMIT_003": "canonical_ligand_comp_id",
        }[rule_id]
        source[canonical_key] = "KNOWN_WRONG_CANONICAL"
    real_oracle = vars(oracle_module)[oracle_name]
    calls = 0

    def oracle(*args: object) -> object:
        nonlocal calls
        calls += 1
        return real_oracle(*args)

    monkeypatch.setattr(legacy_module, legacy_name, lambda *args: source)
    monkeypatch.setattr(oracle_module, oracle_name, oracle)
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(rule_id, candidate, **kwargs)
    assert caught.value.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    assert caught.value.reason == f"{rule_id}_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert caught.value.adapter_ready is False
    assert calls == 1


@pytest.mark.parametrize("rule_id", ("ADMIT_001", "ADMIT_002", "ADMIT_003"))
def test_unknown_reason_equal_in_legacy_and_oracle_fails_unmapped(
    monkeypatch: pytest.MonkeyPatch, rule_id: str
) -> None:
    legacy_module, legacy_name, oracle_module, oracle_name, candidate, kwargs = _valid_spec(rule_id)
    if rule_id == "ADMIT_001":
        source = {
            "admission_rule_id": rule_id,
            "passed": False,
            "normalized_candidate_record_id": "REC_1",
            "blocking_reason": "UNKNOWN_REASON",
        }
        oracle = SimpleNamespace(
            passed=False,
            candidate_syntax_valid=True,
            canonical_candidate_record_id="REC_1",
            blocking_reason="UNKNOWN_REASON",
        )
    elif rule_id == "ADMIT_002":
        source = {
            "admission_rule_id": rule_id,
            "passed": False,
            "canonical_pdb_id": "",
            "input_form": "invalid",
            "blocking_reason": "UNKNOWN_REASON",
        }
        oracle = SimpleNamespace(
            syntax_valid=False,
            canonical_pdb_id="",
            input_form="invalid",
            blocking_reason="UNKNOWN_REASON",
        )
    else:
        source = {
            "admission_rule_id": rule_id,
            "passed": False,
            "canonical_ligand_comp_id": "",
            "blocking_reason": "UNKNOWN_REASON",
        }
        oracle = SimpleNamespace(
            passed=False,
            canonical_ligand_comp_id="",
            blocking_reason="UNKNOWN_REASON",
        )
    monkeypatch.setattr(legacy_module, legacy_name, lambda *args: source)
    monkeypatch.setattr(oracle_module, oracle_name, lambda *args: oracle)
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(rule_id, candidate, **kwargs)
    assert caught.value.reason == f"{rule_id}_UNIFIED_ADAPTER_REASON_UNMAPPED"


@pytest.mark.parametrize("rule_id", ("ADMIT_001", "ADMIT_002", "ADMIT_003"))
def test_valid_adapter_calls_legacy_and_oracle_exactly_once(
    monkeypatch: pytest.MonkeyPatch, rule_id: str
) -> None:
    legacy_module, legacy_name, oracle_module, oracle_name, candidate, kwargs = _valid_spec(rule_id)
    real_legacy = vars(legacy_module)[legacy_name]
    real_oracle = vars(oracle_module)[oracle_name]
    calls = {"legacy": 0, "oracle": 0}

    def legacy(*args: object) -> object:
        calls["legacy"] += 1
        return real_legacy(*args)

    def oracle(*args: object) -> object:
        calls["oracle"] += 1
        return real_oracle(*args)

    monkeypatch.setattr(legacy_module, legacy_name, legacy)
    monkeypatch.setattr(oracle_module, oracle_name, oracle)
    result = runtime.evaluate_admission_rule(rule_id, candidate, **kwargs)
    assert result.outcome == "passed"
    assert calls == {"legacy": 1, "oracle": 1}


@pytest.mark.parametrize(
    ("rule_id", "candidate", "kwargs", "outcome", "reason", "normalized", "validated"),
    (
        ("ADMIT_001", {"candidate_record_id": "REC_1"}, {"batch_context": {"batch_candidate_record_ids": ["REC_2"]}}, "blocked", "candidate_record_id_missing_from_batch", (("candidate_record_id", "REC_1"),), (("candidate_record_id", "REC_1"),)),
        ("ADMIT_001", {"candidate_record_id": ""}, {"batch_context": {"batch_candidate_record_ids": ["REC_2"]}}, "invalid", "candidate_record_id_empty", (), ()),
        ("ADMIT_002", {"pdb_id": "1AbC"}, {}, "passed", "", (("pdb_id", "pdb_00001abc"),), (("pdb_id", "pdb_00001abc"),)),
        ("ADMIT_002", {"pdb_id": ""}, {}, "invalid", "pdb_id_empty", (), ()),
        ("ADMIT_003", {"ligand_comp_id": "abc"}, {}, "passed", "", (("ligand_comp_id", "ABC"),), (("ligand_comp_id", "ABC"),)),
        ("ADMIT_003", {"ligand_comp_id": ""}, {}, "invalid", "LIGAND_COMP_ID_EMPTY", (), ()),
    ),
)
def test_unified_field_mappings(
    rule_id: str,
    candidate: dict[str, object],
    kwargs: dict[str, object],
    outcome: str,
    reason: str,
    normalized: tuple[tuple[str, str], ...],
    validated: tuple[tuple[str, str], ...],
) -> None:
    result = runtime.evaluate_admission_rule(rule_id, candidate, **kwargs)
    assert result.outcome == outcome
    assert result.passed is (outcome == "passed")
    assert result.blocks_candidate is (outcome != "passed")
    assert result.reason == reason
    assert result.normalized_values == normalized
    assert result.validated_candidate_fields == validated
    assert result.evaluator_io_used is False


def test_admit004_result_delegates_once_and_preserves_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = runtime._admit004_candidate()
    context = runtime._admit004_context(candidate)
    direct = runtime.phase2.evaluate_admission_rule(
        "ADMIT_004", candidate, evaluation_context=context
    )
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def delegated(*args: object, **kwargs: object) -> runtime.UnifiedAdmissionRuleEvaluation:
        calls.append((args, kwargs))
        return direct

    monkeypatch.setattr(runtime.phase2, "evaluate_admission_rule", delegated)
    observed = runtime.evaluate_admission_rule(
        "ADMIT_004", candidate, evaluation_context=context
    )
    assert observed is direct
    assert len(calls) == 1
    assert calls[0][0] == ("ADMIT_004", candidate)
    assert calls[0][1] == {
        "batch_context": None,
        "evaluation_context": context,
        "download_result_context": None,
        "stage_authorization_context": None,
    }


def test_admit004_result_and_error_equal_direct_phase2() -> None:
    candidate = runtime._admit004_candidate()
    context = runtime._admit004_context(candidate)
    assert runtime.evaluate_admission_rule(
        "ADMIT_004", candidate, evaluation_context=context
    ) == runtime.phase2.evaluate_admission_rule(
        "ADMIT_004", candidate, evaluation_context=context
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as direct:
        runtime.phase2.evaluate_admission_rule(
            "ADMIT_004", candidate, batch_context={}, evaluation_context=context
        )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as successor:
        runtime.evaluate_admission_rule(
            "ADMIT_004", candidate, batch_context={}, evaluation_context=context
        )
    assert _error_fields(successor.value) == _error_fields(direct.value)


def test_public_dispatch_path_uses_no_filesystem_network_or_subprocess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("forbidden public dispatch side effect")

    monkeypatch.setattr(runtime, "_git", forbidden)
    monkeypatch.setattr(runtime.os, "lstat", forbidden)
    assert runtime.evaluate_admission_rule(
        "ADMIT_002", {"pdb_id": "1abc"}
    ).outcome == "passed"
    assert runtime.evaluate_admission_rule(
        "ADMIT_003", {"ligand_comp_id": "abc"}
    ).outcome == "passed"


def test_truth_matrix_exact56_without_padding(state: dict[str, Any]) -> None:
    rows = state["truth_rows"]
    assert len(rows) == 56
    assert len({row["case_id"] for row in rows}) == 56
    assert Counter(row["truth_group"] for row in rows) == {
        "passed": 8,
        "blocked": 4,
        "invalid_rule_result": 24,
        "dispatch_error": 20,
    }
    assert all(row["truth_passed"] == "true" for row in rows)
    assert not any("PADDING" in row["case_id"] for row in rows)


def test_registry_audit_exact15(state: dict[str, Any]) -> None:
    rows = state["registry_rows"]
    assert len(rows) == 15
    assert tuple(row["admission_rule_id"] for row in rows) == runtime.KNOWN_RULE_IDS
    assert tuple(row["admission_rule_id"] for row in rows if row["registered"] == "true") == (
        "ADMIT_001",
        "ADMIT_002",
        "ADMIT_003",
        "ADMIT_004",
    )
    assert all(row["audit_passed"] == "true" for row in rows)
    assert all(
        row["dispatch_disposition"] == "known_not_registered_fail_closed"
        for row in rows[4:]
    )


def test_issue_transition_exact12_to11_only_removes_pending(state: dict[str, Any]) -> None:
    source = state["predecessor"]["phase3_issues"].rows
    expected = [dict(row) for row in source if row["issue_id"] != runtime.REMOVED_ISSUE_ID]
    assert state["issue_rows"] == expected
    assert len(state["issue_rows"]) == 11
    issue_map = {row["issue_id"]: row for row in state["issue_rows"]}
    provider = issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]
    assert (provider["status"], provider["severity"], provider["issue_count"]) == (
        "open",
        "blocking",
        "11",
    )
    for issue_id in (
        "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
    ):
        assert issue_map[issue_id]["status"] == "open"
        assert issue_map[issue_id]["severity"] == "blocking"


def test_readiness_is_truthful_and_does_not_overclaim(state: dict[str, Any]) -> None:
    payloads, manifest = runtime._payloads(state)
    assert tuple(payloads) == runtime.OUTPUT_FILES
    for item in runtime.TRUE_READINESS:
        assert manifest["readiness"][item] is True
        assert manifest[item] is True
    for item in runtime.FALSE_READINESS:
        assert manifest["readiness"][item] is False
        assert manifest[item] is False
    assert manifest["registered_rule_count"] == 4
    assert manifest["recommended_next_step"] == (
        "audit_covapie_admit_005_formal_evaluator_interface_preconditions_v1"
    )


def test_payload_materialization_is_byte_deterministic(state: dict[str, Any]) -> None:
    first, first_manifest = runtime._payloads(state)
    second, second_manifest = runtime._payloads(state)
    assert first == second
    assert first_manifest == second_manifest
    manifest_text = first[runtime.MANIFEST_FILENAME].decode("utf-8")
    assert "timestamp" not in manifest_text.lower()
    assert str(REPO_ROOT) not in manifest_text
    assert runtime.MANIFEST_FILENAME not in first_manifest["output_sha256"]


def test_double_materialization_exact6_is_byte_identical(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1(first)
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1(second)
    assert {entry.name for entry in first.iterdir()} == set(runtime.OUTPUT_FILES)
    assert {entry.name for entry in second.iterdir()} == set(runtime.OUTPUT_FILES)
    assert all(
        (first / name).read_bytes() == (second / name).read_bytes()
        for name in runtime.OUTPUT_FILES
    )
    assert not tuple(tmp_path.rglob("*.tmp"))
    assert not tuple(tmp_path.rglob("*.part"))


def test_materializer_symlink_victim_fails_closed(tmp_path: Path) -> None:
    victim = tmp_path / "victim"
    victim.write_bytes(b"unchanged")
    output = tmp_path / "output"
    output.mkdir()
    (output / runtime.CONTRACT_FILENAME).symlink_to(victim)
    with pytest.raises(ValueError, match="unsafe"):
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1(output)
    assert victim.read_bytes() == b"unchanged"
    assert {entry.name for entry in output.iterdir()} == {runtime.CONTRACT_FILENAME}


def test_materializer_rejects_extra_entry_before_writes(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    extra = output / "extra.txt"
    extra.write_text("unchanged", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected"):
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1(output)
    assert extra.read_text(encoding="utf-8") == "unchanged"
    assert {entry.name for entry in output.iterdir()} == {"extra.txt"}


def test_default_outputs_exact_set_bytes_hashes_and_manifest(state: dict[str, Any]) -> None:
    root = REPO_ROOT / runtime.DEFAULT_OUTPUT_ROOT
    assert {entry.name for entry in root.iterdir()} == set(runtime.OUTPUT_FILES)
    expected, manifest = runtime._payloads(state)
    for name in runtime.OUTPUT_FILES:
        path = root / name
        assert path.is_file() and not path.is_symlink()
        assert path.read_bytes() == expected[name]
    actual_manifest = json.loads((root / runtime.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert actual_manifest == manifest
    for name in runtime.CSV_OUTPUTS:
        assert actual_manifest["output_sha256"][name] == hashlib.sha256(
            (root / name).read_bytes()
        ).hexdigest()


@pytest.mark.parametrize(
    "failure_kind", ("missing", "extra", "tamper", "overclaim", "symlink")
)
def test_checker_output_failures_are_direct_and_fail_closed(
    tmp_path: Path, state: dict[str, Any], failure_kind: str
) -> None:
    checker_path = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1.py"
    spec = importlib.util.spec_from_file_location(
        f"covapie_phase4_checker_{failure_kind}", checker_path
    )
    assert spec is not None and spec.loader is not None
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    expected_payloads, expected_manifest = runtime._payloads(state)
    root = tmp_path / failure_kind
    root.mkdir()
    for name, content in expected_payloads.items():
        (root / name).write_bytes(content)
    victim = tmp_path / "victim"
    if failure_kind == "missing":
        (root / runtime.CONTRACT_FILENAME).unlink()
    elif failure_kind == "extra":
        (root / "unexpected.csv").write_text("unexpected\n", encoding="utf-8")
    elif failure_kind == "tamper":
        (root / runtime.TRUTH_FILENAME).write_bytes(b"tampered\n")
    elif failure_kind == "overclaim":
        manifest_path = root / runtime.MANIFEST_FILENAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["ready_for_training"] = True
        manifest["readiness"]["ready_for_training"] = True
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    else:
        victim.write_bytes(b"victim-must-remain-unchanged")
        link = root / runtime.SAFETY_FILENAME
        link.unlink()
        link.symlink_to(victim)
    with pytest.raises((AssertionError, FileNotFoundError)):
        checker.validate_output_root(root, expected_payloads, expected_manifest)
    if failure_kind == "symlink":
        assert victim.read_bytes() == b"victim-must-remain-unchanged"


def test_import_smoke_is_silent_and_has_no_materialization_side_effect(tmp_path: Path) -> None:
    before = tuple((REPO_ROOT / runtime.DEFAULT_OUTPUT_ROOT).iterdir())
    code = (
        "import sys; sys.path.insert(0, 'src'); "
        "import covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""
    after = tuple((REPO_ROOT / runtime.DEFAULT_OUTPUT_ROOT).iterdir())
    assert before == after


def test_production_and_checker_import_boundaries() -> None:
    production_tree = ast.parse(
        (REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004.py").read_text(encoding="utf-8")
    )
    checker_tree = ast.parse(
        (REPO_ROOT / "scripts/check_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1.py").read_text(encoding="utf-8")
    )
    forbidden = {"torch", "numpy", "rdkit", "requests", "urllib", "pandas"}
    for tree in (production_tree, checker_tree):
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            (node.module or "").split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        assert imported.isdisjoint(forbidden)
    production_source = ast.unparse(production_tree)
    assert "__import__" not in production_source
    assert "eval(" not in production_source


def test_no_all_rules_combined_verdict_or_cross_rule_aggregation_implementation() -> None:
    assert not hasattr(runtime, "evaluate_all_rules")
    assert not hasattr(runtime, "combined_candidate_verdict")
    tree = ast.parse(
        (REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004.py").read_text(encoding="utf-8")
    )
    defined = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    assert "evaluate_all_rules" not in defined
    assert "combined_candidate_verdict" not in defined
    assert "aggregate_admission_rules" not in defined


def test_checker_runs_direct_checks_and_reports_exact_counts() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/check_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1.py",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "all_checks_passed=true" in completed.stdout
    assert "source_input_count=14" in completed.stdout
    assert "truth_matrix=56/56" in completed.stdout
    assert "registry_audit=15/15" in completed.stdout
    assert "active_issue_count=11" in completed.stdout
    assert completed.stderr == ""
