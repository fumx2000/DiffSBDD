from __future__ import annotations

import ast
import builtins
import copy
import dataclasses
import hashlib
import importlib.util
import inspect
import json
import os
import socket
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import get_type_hints

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.covalent_ext import (
    covapie_bulk_download_admission_admit_004_rule_logic_interface as interface,
)


CHECKER_PATH = (
    REPO_ROOT
    / "scripts/check_covapie_bulk_download_admission_admit_004_rule_logic_interface_v1.py"
)
RESULT_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_residue_name",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "evidence_context_consumed",
    "evaluator_io_used",
)


def candidate(**updates: object) -> dict[str, object]:
    value: dict[str, object] = interface._base_candidate()
    value.update(updates)
    return value


def context(value: Mapping[str, object], **updates: object) -> dict[str, object]:
    result = interface._base_context(value)  # type: ignore[arg-type]
    nested = result[interface.EVIDENCE_CONTEXT_KEY]
    assert isinstance(nested, dict)
    nested.update(updates)
    return result


def load_checker():
    spec = importlib.util.spec_from_file_location("admit_004_checker_for_test", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact12_source_order_structure_and_sha256() -> None:
    assert len(interface.SOURCE_PATHS) == len(set(interface.SOURCE_PATHS)) == 12
    assert tuple(interface.SOURCE_SHA256) == interface.SOURCE_PATHS
    snapshot = interface.build_frozen_source_snapshot()
    assert interface.validate_frozen_source_snapshot(snapshot)
    assert tuple(record.relative_path for record in snapshot.records) == interface.SOURCE_PATHS
    for record in snapshot.records:
        assert record.expected_sha256 == interface.SOURCE_SHA256[record.relative_path]
        assert record.expected_sha256 == record.base_tree_sha256 == record.filesystem_sha256
        assert hashlib.sha256(record.content_bytes).hexdigest() == record.expected_sha256


def test_all_structural_checks_precede_first_source_byte_read(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    original_structure = interface._structural_source_check
    original_read_bytes = Path.read_bytes

    def structure(path: Path, root: Path) -> bool:
        events.append(f"structure:{path}")
        return original_structure(path, root)

    def read_bytes(path: Path) -> bytes:
        if path in tuple(interface.REPO_ROOT / source for source in interface.SOURCE_PATHS):
            events.append(f"read:{path.relative_to(interface.REPO_ROOT)}")
        return original_read_bytes(path)

    monkeypatch.setattr(interface, "_structural_source_check", structure)
    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    interface.build_frozen_source_snapshot()
    first_read = next(index for index, event in enumerate(events) if event.startswith("read:"))
    assert first_read == 12
    assert all(event.startswith("structure:") for event in events[:first_read])


def test_source_missing_or_symlink_shape_fails_before_byte_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checked: list[Path] = []

    def structure(path: Path, _root: Path) -> bool:
        checked.append(path)
        return path != interface.SOURCE_PATHS[3]

    def forbidden_read(_path: Path) -> bytes:
        raise AssertionError("source bytes read after structural failure")

    monkeypatch.setattr(interface, "_structural_source_check", structure)
    monkeypatch.setattr(Path, "read_bytes", forbidden_read)
    with pytest.raises(ValueError, match="structural"):
        interface.build_frozen_source_snapshot()
    assert checked == list(interface.SOURCE_PATHS)


def test_source_filesystem_hash_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = Path.read_bytes
    target = interface.REPO_ROOT / interface.SOURCE_PATHS[0]

    def drift(path: Path) -> bytes:
        content = original(path)
        return content + b"drift" if path == target else content

    monkeypatch.setattr(Path, "read_bytes", drift)
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        interface.build_frozen_source_snapshot()


def test_source_base_tree_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = interface._git
    changed = False

    def git(arguments, repo_root, *, text=True):
        nonlocal changed
        result = original(arguments, repo_root, text=text)
        if arguments[0] == "show" and not changed:
            changed = True
            return subprocess.CompletedProcess(result.args, 0, stdout=result.stdout + b"drift", stderr=b"")
        return result

    monkeypatch.setattr(interface, "_git", git)
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        interface.build_frozen_source_snapshot()


def test_invalid_snapshot_zeroes_success_counts_and_readiness() -> None:
    snapshot = interface.build_frozen_source_snapshot()
    first = snapshot.records[0]
    corrupt = dataclasses.replace(first, content_bytes=first.content_bytes + b"drift")
    invalid = interface.FrozenSourceSnapshot((corrupt, *snapshot.records[1:]))
    state = interface.build_interface_state(invalid)
    assert state["interface_implementation_readiness"] is False
    assert state["contract_pass_count"] == 0
    assert state["truth_pass_count"] == 0
    assert state["all_checks_passed"] is False
    assert state["contract_rows"] == state["truth_rows"] == []


def test_source_failure_materializes_no_success_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    failure = interface._empty_state(failure="TEST_SOURCE_FAILURE")
    monkeypatch.setattr(interface, "build_interface_state", lambda: failure)
    output = tmp_path / "must_not_exist"
    with pytest.raises(RuntimeError, match="failed closed"):
        interface.run_covapie_bulk_download_admission_admit_004_rule_logic_interface_v1(output)
    assert not output.exists()


def test_e1e2_and_e1e1_direct_evidence_contracts() -> None:
    predecessor = interface._validate_predecessor_evidence(
        interface.build_frozen_source_snapshot()
    )
    admit_004 = next(row for row in predecessor["rules"] if row["admission_rule_id"] == "ADMIT_004")
    atom = next(
        row for row in predecessor["fields"] if row["field_name"] == "covalent_residue_atom_name"
    )
    evidence = next(
        row for row in predecessor["contexts"] if row["context_item"] == interface.EVIDENCE_CONTEXT_KEY
    )
    assert admit_004["candidate_field_dependencies"] == "|".join(interface.CANDIDATE_FIELDS)
    assert admit_004["evaluation_context_dependencies"].endswith(
        "covalent_residue_identity_evidence_context"
    )
    assert atom["source_value_contract"].startswith("generic exact non-empty ASCII")
    assert evidence["filesystem_access_inside_evaluator"] == "false"
    assert len(predecessor["e1e1_contract"]) == 28
    assert len(predecessor["e1e1_truth"]) == 36
    assert all(row["contract_passed"] == "true" for row in predecessor["e1e1_contract"])
    assert all(row["truth_passed"] == "true" for row in predecessor["e1e1_truth"])


def test_public_signature_and_runtime_invalid_inputs() -> None:
    signature = inspect.signature(interface.evaluate_admit_004)
    assert tuple(signature.parameters) == ("candidate_record", "evaluation_context")
    hints = get_type_hints(interface.evaluate_admit_004)
    assert hints["candidate_record"] == Mapping[str, object]
    assert hints["evaluation_context"] == Mapping[str, object]
    assert hints["return"] is interface.Admit004EvaluationResult
    result = interface.evaluate_admit_004([], {})  # type: ignore[arg-type]
    assert result.outcome == "invalid"


def test_frozen_result_dataclass_exact_schema() -> None:
    assert interface.Admit004EvaluationResult.__dataclass_params__.frozen is True
    assert tuple(field.name for field in dataclasses.fields(interface.Admit004EvaluationResult)) == RESULT_FIELDS
    value = candidate()
    result = interface.evaluate_admit_004(value, context(value))
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.reason = "changed"  # type: ignore[misc]


@pytest.mark.parametrize("missing_field", interface.CANDIDATE_FIELDS)
def test_each_exact9_missing_field_fails_in_frozen_order(missing_field: str) -> None:
    value = candidate()
    del value[missing_field]
    result = interface.evaluate_admit_004(value, {})
    assert result.outcome == "invalid"
    assert result.reason == f"ADMIT_004_CANDIDATE_FIELD_MISSING:{missing_field}"
    assert result.validated_candidate_fields == ()
    assert result.consumed_candidate_fields == interface.CANDIDATE_FIELDS


@pytest.mark.parametrize(
    ("field", "bad_value", "reason"),
    (
        ("covalent_residue_name", "C-Y", "COVALENT_RESIDUE_NAME_SYNTAX_INVALID"),
        ("covalent_residue_chain_id", "A A", "COVALENT_RESIDUE_CHAIN_ID_LEXICAL_INVALID"),
        ("covalent_residue_index", 42, "COVALENT_RESIDUE_INDEX_TYPE_INVALID"),
        ("covalent_residue_atom_name", "?", "COVALENT_RESIDUE_ATOM_NAME_MARKER_FORBIDDEN"),
        ("covalent_residue_locator_namespace", "AUTH", "COVALENT_RESIDUE_LOCATOR_NAMESPACE_INVALID"),
        ("covalent_residue_locator_provenance_source_id", "bad source", "COVALENT_RESIDUE_PROVENANCE_SOURCE_ID_INVALID"),
        ("covalent_residue_locator_provenance_sha256", "A" * 64, "COVALENT_RESIDUE_PROVENANCE_SHA256_INVALID"),
    ),
)
def test_candidate_field_syntax_failures(field: str, bad_value: object, reason: str) -> None:
    value = candidate(**{field: bad_value})
    result = interface.evaluate_admit_004(value, {})
    assert result.outcome == "invalid" and result.reason == reason
    assert result.blocks_candidate is True and result.validated_candidate_fields == ()


def test_insertion_grammar_slash_allowed_backslash_equals_forbidden() -> None:
    slash = candidate(
        covalent_residue_insertion_code_state="present",
        covalent_residue_insertion_code="A/B",
    )
    assert interface.evaluate_admit_004(slash, context(slash)).outcome == "passed"
    for bad in ("\\", "="):
        value = candidate(
            covalent_residue_insertion_code_state="present",
            covalent_residue_insertion_code=bad,
        )
        result = interface.evaluate_admit_004(value, {})
        assert result.outcome == "invalid"
        assert result.reason == "COVALENT_RESIDUE_INSERTION_PRESENT_CHARACTER_GRAMMAR_INVALID"


def test_generic_non_sg_atom_passes_admit_004() -> None:
    value = candidate(covalent_residue_name="SER", covalent_residue_atom_name="CA")
    result = interface.evaluate_admit_004(value, context(value))
    assert result.outcome == "passed" and result.canonical_residue_name == "SER"
    assert dict(result.validated_candidate_fields)["covalent_residue_atom_name"] == "CA"


def test_residue_uppercase_and_raw_attestation_binding() -> None:
    value = candidate(covalent_residue_name="cys")
    passed = interface.evaluate_admit_004(value, context(value))
    assert passed.outcome == "passed" and passed.canonical_residue_name == "CYS"
    assert dict(passed.validated_candidate_fields)["covalent_residue_name"] == "CYS"
    canonical_attestation = context(value)
    canonical_attestation[interface.EVIDENCE_CONTEXT_KEY]["attested_candidate_fields"][
        "covalent_residue_name"
    ] = "CYS"  # type: ignore[index]
    invalid = interface.evaluate_admit_004(value, canonical_attestation)
    assert invalid.outcome == "invalid"
    assert invalid.reason == "ADMIT_004_ATTESTED_CANDIDATE_BINDING_MISMATCH:covalent_residue_name"


def test_context_exact_six_keys_and_exact9_attestation() -> None:
    value = candidate()
    valid_context = context(value)
    nested = valid_context[interface.EVIDENCE_CONTEXT_KEY]
    assert isinstance(nested, dict)
    assert tuple(nested) == interface.NESTED_CONTEXT_KEYS
    assert tuple(nested["attested_candidate_fields"]) == interface.CANDIDATE_FIELDS
    for mutation in ("missing", "extra"):
        malformed = copy.deepcopy(valid_context)
        malformed_nested = malformed[interface.EVIDENCE_CONTEXT_KEY]
        assert isinstance(malformed_nested, dict)
        if mutation == "missing":
            del malformed_nested["schema_version"]
        else:
            malformed_nested["extra"] = "x"
        result = interface.evaluate_admit_004(value, malformed)
        assert result.outcome == "invalid"
        assert result.reason == "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_KEYSET_INVALID"


def test_mapping_subclasses_and_unrelated_keys_are_accepted() -> None:
    class CandidateMap(dict[str, object]):
        pass

    value = CandidateMap(candidate(unrelated="ignored"))
    valid_context = context(value)
    valid_context["engine_unrelated"] = "ignored"
    result = interface.evaluate_admit_004(value, MappingProxyType(valid_context))
    assert result.outcome == "passed"
    assert len(result.validated_candidate_fields) == 9


def test_formal_truth_matrix_exact50_unique_and_grouped() -> None:
    rows = interface._truth_rows()
    assert len(rows) == len({row["case_id"] for row in rows}) == 50
    assert all(row["truth_passed"] == "true" for row in rows)
    assert {
        group: sum(row["truth_group"] == group for row in rows)
        for group in ("passed", "blocked", "candidate_invalid", "context_invalid")
    } == {"passed": 6, "blocked": 7, "candidate_invalid": 19, "context_invalid": 18}


def test_invalid_precedes_unknown_blocking() -> None:
    unknown = candidate(
        covalent_residue_insertion_code_state="unknown", covalent_residue_insertion_code=""
    )
    malformed = context(unknown)
    malformed[interface.EVIDENCE_CONTEXT_KEY]["schema_version"] = "wrong"  # type: ignore[index]
    assert interface.evaluate_admit_004(unknown, malformed).outcome == "invalid"
    provider_invalid = context(
        unknown, provider_evidence_outcome="invalid", provider_evidence_reason="PROVIDER_INVALID"
    )
    result = interface.evaluate_admit_004(unknown, provider_invalid)
    assert result.outcome == "invalid" and result.reason == "PROVIDER_INVALID"


def test_blocked_precedence_is_frozen() -> None:
    unknown = candidate(
        covalent_residue_insertion_code_state="unknown", covalent_residue_insertion_code=""
    )
    provider_blocked = context(
        unknown, provider_evidence_outcome="blocked", provider_evidence_reason="PROVIDER_BLOCKED"
    )
    result = interface.evaluate_admit_004(unknown, provider_blocked)
    assert result.reason == interface.UNKNOWN_REASON
    assert interface.evaluate_admit_004(unknown, {}).reason == interface.UNKNOWN_REASON

    present = candidate(
        covalent_residue_insertion_code_state="present", covalent_residue_insertion_code="A"
    )
    all_blocked = context(
        present,
        provider_evidence_outcome="blocked",
        provider_evidence_reason="PROVIDER_BLOCKED",
        four_way_present_value_exact_equality_attested=False,
        present_value_quote_class_roundtrip_verified=False,
    )
    assert interface.evaluate_admit_004(present, all_blocked).reason == "PROVIDER_BLOCKED"
    attestations = context(
        present,
        four_way_present_value_exact_equality_attested=False,
        present_value_quote_class_roundtrip_verified=False,
    )
    assert interface.evaluate_admit_004(present, attestations).reason == interface.FOUR_WAY_REASON


def test_absent_false_flags_do_not_block_and_unknown_never_promoted() -> None:
    absent = candidate()
    flags_false = context(
        absent,
        four_way_present_value_exact_equality_attested=False,
        present_value_quote_class_roundtrip_verified=False,
    )
    assert interface.evaluate_admit_004(absent, flags_false).outcome == "passed"
    unknown = candidate(
        covalent_residue_insertion_code_state="unknown", covalent_residue_insertion_code=""
    )
    assert interface.evaluate_admit_004(unknown, context(unknown)).outcome == "blocked"


def test_result_boolean_consistency_for_every_truth_case() -> None:
    for outcome in ("passed", "blocked", "invalid"):
        result = interface._result(outcome, "" if outcome == "passed" else "reason")
        assert result.passed is (outcome == "passed")
        assert result.blocks_candidate is (outcome != "passed")
        assert result.admission_rule_id == "ADMIT_004"
        assert result.evaluator_io_used is False


def test_input_not_mutated_and_repeated_call_idempotent() -> None:
    value = candidate(extra="ignored")
    valid_context = context(value)
    before_candidate = copy.deepcopy(value)
    before_context = copy.deepcopy(valid_context)
    first = interface.evaluate_admit_004(value, valid_context)
    second = interface.evaluate_admit_004(value, valid_context)
    assert first == second
    assert value == before_candidate and valid_context == before_context


def test_evaluator_calls_no_io_network_or_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    value = candidate()
    valid_context = context(value)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("I/O primitive called by evaluator")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    result = interface.evaluate_admit_004(value, valid_context)
    assert result.outcome == "passed" and result.evaluator_io_used is False


def test_issue_inventory_and_provider_blocker_unchanged() -> None:
    state = interface.build_interface_state()
    predecessor = state["predecessor"]
    assert state["issue_rows"] == list(predecessor["issues"])
    assert len(state["issue_rows"]) == 9
    provider = next(
        row for row in state["issue_rows"] if row["issue_id"] == interface.PROVIDER_ISSUE
    )
    assert provider["status"] == "open"
    assert provider["severity"] == "blocking"
    assert provider["issue_count"] == "11"


def test_exact11_is_metadata_only_and_readiness_does_not_overclaim() -> None:
    state = interface.build_interface_state()
    payloads, manifest = interface._payloads(state)
    assert len(payloads) == 6
    assert manifest["exact11_count"] == manifest["exact11_expected_blocked_count"] == 11
    assert manifest["exact11_reason"] == interface.UNKNOWN_REASON
    assert manifest["exact11_real_rows_evaluated"] is False
    assert manifest["ready_for_admit_004_unified_rule_engine_integration"] is True
    for key in (
        "unified_rule_engine_integrated",
        "candidate_records_materialized",
        "ready_for_real_candidate_evaluation",
        "ready_for_bulk_download_now",
        "ready_for_training",
        "ready_to_train_now",
    ):
        assert manifest[key] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True


def test_deterministic_double_materialization(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    interface.run_covapie_bulk_download_admission_admit_004_rule_logic_interface_v1(first)
    interface.run_covapie_bulk_download_admission_admit_004_rule_logic_interface_v1(second)
    assert {path.name: path.read_bytes() for path in first.iterdir()} == {
        path.name: path.read_bytes() for path in second.iterdir()
    }
    assert not any(path.name.endswith((".tmp", ".part")) for path in first.iterdir())
    assert not any(path.name.endswith((".tmp", ".part")) for path in second.iterdir())


def test_output_missing_extra_hash_and_overclaim_fail_closed(tmp_path: Path) -> None:
    checker = load_checker()
    state = interface.build_interface_state()
    expected, _manifest = interface._payloads(state)
    roots = {kind: tmp_path / kind for kind in ("missing", "extra", "hash", "overclaim")}
    for root in roots.values():
        interface.run_covapie_bulk_download_admission_admit_004_rule_logic_interface_v1(root)
    (roots["missing"] / interface.CONTRACT_FILENAME).unlink()
    (roots["extra"] / "extra.txt").write_text("extra", encoding="utf-8")
    (roots["hash"] / interface.TRUTH_FILENAME).write_text("drift", encoding="utf-8")
    manifest_path = roots["overclaim"] / interface.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["ready_for_training"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    for root in roots.values():
        with pytest.raises(ValueError):
            checker.validate_output_root(root, expected)


def test_output_symlink_and_materializer_victim_fail_closed(tmp_path: Path) -> None:
    checker = load_checker()
    state = interface.build_interface_state()
    expected, _manifest = interface._payloads(state)
    victim = tmp_path / "victim.txt"
    victim.write_text("unchanged", encoding="utf-8")
    root = tmp_path / "root"
    root.mkdir()
    (root / interface.CONTRACT_FILENAME).symlink_to(victim)
    with pytest.raises(ValueError, match="unsafe"):
        interface.run_covapie_bulk_download_admission_admit_004_rule_logic_interface_v1(root)
    with pytest.raises(ValueError):
        checker.validate_output_root(root, expected)
    assert victim.read_text(encoding="utf-8") == "unchanged"
    assert not any(path.name.endswith((".tmp", ".part")) for path in root.iterdir())


def test_production_and_checker_import_only_standard_library() -> None:
    stdlib = set(sys.stdlib_module_names)
    for path in (Path(interface.__file__), CHECKER_PATH):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                roots.add(node.module.split(".", 1)[0])
        allowed_local = {"src"}
        assert roots <= stdlib | allowed_local | {"__future__"}
    source = Path(interface.__file__).read_text(encoding="utf-8")
    assert "generic_atom_identity_evidence_context_reconciliation_design_gate import" not in source


def test_import_smoke_has_no_output_or_materialization_side_effect(tmp_path: Path) -> None:
    probe = (
        "import pathlib; "
        "from src.covalent_ext import "
        "covapie_bulk_download_admission_admit_004_rule_logic_interface"
    )
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=interface.REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""
    assert tuple(tmp_path.iterdir()) == ()


def test_committed_output_exact_set_and_direct_checker_validation() -> None:
    checker = load_checker()
    state = interface.build_interface_state()
    expected, _manifest = interface._payloads(state)
    output_root = interface.REPO_ROOT / interface.DEFAULT_OUTPUT_ROOT
    hashes = checker.validate_output_root(output_root, expected)
    assert set(hashes) == set(interface.OUTPUT_FILES)
    assert len(hashes) == 6
