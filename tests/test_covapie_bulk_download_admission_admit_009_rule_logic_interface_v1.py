from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import inspect
import io
import json
import os
import shutil
import subprocess
import sys
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate
    as committed_oracle,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_009_rule_logic_interface as subject,
)


CHECKER_PATH = subject.REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_009_rule_logic_interface_v1.py"
SPEC = importlib.util.spec_from_file_location("admit009_interface_checker", CHECKER_PATH)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)

KEY = subject.KEY_PREFIX + "1" * 64
LOW = subject.KEY_PREFIX + "0" * 64
HIGH = subject.KEY_PREFIX + "2" * 64
OTHER = subject.KEY_PREFIX + "f" * 64
POLICY = subject.POLICY_CONTRACT_VALUE


def _values(
    *,
    outcome: str = "passed",
    reason: str = "",
    canonical: str = KEY,
    validated: tuple[tuple[str, str], ...] | None = None,
    contexts: tuple[str, ...] | None = None,
) -> dict[str, object]:
    pair = () if canonical == "" else ((subject.CANDIDATE_FIELDS[0], canonical),)
    return {
        "admission_rule_id": "ADMIT_009",
        "outcome": outcome,
        "passed": outcome == "passed",
        "blocks_candidate": outcome != "passed",
        "reason": reason,
        "canonical_duplicate_identity_key": canonical,
        "validated_candidate_fields": pair if validated is None else validated,
        "consumed_candidate_fields": subject.CANDIDATE_FIELDS,
        "consumed_context_items": subject.CONTEXT_ITEMS if contexts is None else contexts,
        "evaluator_io_used": False,
    }


def _invalid(values: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        subject.Admit009EvaluationResult(**values)  # type: ignore[arg-type]


def test_exact_public_signature_exact10_result_type_storage_and_frozen() -> None:
    signature = inspect.signature(subject.evaluate_admit_009)
    parameters = tuple(signature.parameters.values())
    assert tuple(parameter.name for parameter in parameters) == (
        "duplicate_identity_key", "batch_duplicate_identity_keys", "duplicate_identity_key_contract",
    )
    assert all(parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for parameter in parameters)
    assert all(parameter.default is inspect.Parameter.empty for parameter in parameters)
    assert signature.return_annotation == "Admit009EvaluationResult"
    assert tuple(field.name for field in fields(subject.Admit009EvaluationResult)) == subject.RESULT_FIELDS
    result = subject.evaluate_admit_009(KEY, (), POLICY)
    assert type(result) is subject.Admit009EvaluationResult
    assert tuple(vars(result)) == subject.RESULT_FIELDS
    with pytest.raises(FrozenInstanceError):
        result.reason = "changed"  # type: ignore[misc]


def test_result_subclass_is_rejected() -> None:
    class ResultSubclass(subject.Admit009EvaluationResult):
        pass

    with pytest.raises(TypeError, match="subclasses"):
        ResultSubclass(**_values())  # type: ignore[arg-type]


@pytest.mark.parametrize("override", (
    {"admission_rule_id": "ADMIT_008"},
    {"outcome": "rejected", "passed": False, "blocks_candidate": True, "reason": "x"},
    {"passed": False},
    {"blocks_candidate": True},
    {"reason": subject.DUPLICATE_REASON},
    {"validated_candidate_fields": ()},
    {"consumed_candidate_fields": ()},
    {"consumed_context_items": ()},
    {"evaluator_io_used": True},
))
def test_general_result_invariants_fail_closed(override: dict[str, object]) -> None:
    values = _values()
    values.update(override)
    _invalid(values)


@pytest.mark.parametrize("values", (
    _values(outcome="invalid", reason=subject.SCALAR_REASONS[0], canonical=KEY, contexts=()),
    _values(outcome="invalid", reason=subject.SCALAR_REASONS[0], canonical="", validated=(("duplicate_identity_key", KEY),), contexts=()),
    _values(outcome="invalid", reason=subject.SCALAR_REASONS[0], canonical="", contexts=subject.CONTEXT_ITEMS[:1]),
    _values(outcome="invalid", reason=subject.POLICY_REASONS[0], canonical="", contexts=subject.CONTEXT_ITEMS[:1]),
    _values(outcome="invalid", reason=subject.POLICY_REASONS[1], contexts=subject.CONTEXT_ITEMS),
    _values(outcome="invalid", reason=subject.BATCH_REASONS[0], canonical="", contexts=subject.CONTEXT_ITEMS),
    _values(outcome="invalid", reason=subject.BATCH_REASONS[1], contexts=subject.CONTEXT_ITEMS[:1]),
    _values(outcome="blocked", reason=subject.BATCH_REASONS[0]),
    _values(outcome="blocked", reason=""),
    _values(outcome="invalid", reason="duplicate_identity_unresolved"),
))
def test_stage_and_reason_state_conflicts_fail_closed(values: dict[str, object]) -> None:
    _invalid(values)


def test_result_exact_types_reject_string_bool_tuple_pair_and_list_drift() -> None:
    class Text(str):
        pass

    class TupleSubclass(tuple):
        pass

    cases: list[tuple[str, object]] = [
        ("admission_rule_id", Text("ADMIT_009")),
        ("outcome", Text("passed")),
        ("reason", Text("")),
        ("canonical_duplicate_identity_key", Text(KEY)),
        ("passed", 1),
        ("blocks_candidate", 0),
        ("evaluator_io_used", 0),
        ("validated_candidate_fields", list((("duplicate_identity_key", KEY),))),
        ("validated_candidate_fields", TupleSubclass((("duplicate_identity_key", KEY),))),
        ("validated_candidate_fields", (["duplicate_identity_key", KEY],)),
        ("validated_candidate_fields", ((Text("duplicate_identity_key"), KEY),)),
        ("consumed_candidate_fields", ["duplicate_identity_key"]),
        ("consumed_context_items", TupleSubclass(subject.CONTEXT_ITEMS)),
    ]
    for name, replacement in cases:
        values = _values()
        values[name] = replacement
        _invalid(values)


@pytest.mark.parametrize(("value", "reason"), (
    (None, subject.SCALAR_REASONS[0]),
    (7, subject.SCALAR_REASONS[0]),
    (True, subject.SCALAR_REASONS[0]),
    ("", subject.SCALAR_REASONS[1]),
    (subject.KEY_PREFIX + "é" * 64, subject.SCALAR_REASONS[2]),
    ("covapie_dup_v2_sha256_" + "1" * 64, subject.SCALAR_REASONS[3]),
    (subject.KEY_PREFIX + "A" * 64, subject.SCALAR_REASONS[3]),
    (subject.KEY_PREFIX + "1" * 63, subject.SCALAR_REASONS[3]),
    (subject.KEY_PREFIX + "1" * 65, subject.SCALAR_REASONS[3]),
    (subject.KEY_PREFIX + "g" * 64, subject.SCALAR_REASONS[3]),
    (" " + KEY, subject.SCALAR_REASONS[3]),
    (KEY + " ", subject.SCALAR_REASONS[3]),
))
def test_scalar_validation_precedence_no_normalization_and_empty_state(value: object, reason: str) -> None:
    result = subject.evaluate_admit_009(value, object(), object())
    assert (result.outcome, result.passed, result.blocks_candidate, result.reason) == (
        "invalid", False, True, reason,
    )
    assert result.canonical_duplicate_identity_key == ""
    assert result.validated_candidate_fields == ()
    assert result.consumed_context_items == ()


def test_str_subclass_key_is_type_invalid() -> None:
    class Text(str):
        pass

    result = subject.evaluate_admit_009(Text(KEY), (), POLICY)
    assert result.reason == subject.SCALAR_REASONS[0]


@pytest.mark.parametrize(("policy", "reason"), (
    (None, subject.POLICY_REASONS[0]),
    ("wrong", subject.POLICY_REASONS[1]),
    (" " + POLICY, subject.POLICY_REASONS[1]),
))
def test_policy_validation_retains_pair_and_consumes_policy_only(policy: object, reason: str) -> None:
    result = subject.evaluate_admit_009(KEY, object(), policy)
    assert result.outcome == "invalid" and result.blocks_candidate is True and result.reason == reason
    assert result.canonical_duplicate_identity_key == KEY
    assert result.validated_candidate_fields == ((subject.CANDIDATE_FIELDS[0], KEY),)
    assert result.consumed_context_items == subject.CONTEXT_ITEMS[:1]


def test_policy_str_subclass_is_type_invalid() -> None:
    class Text(str):
        pass

    assert subject.evaluate_admit_009(KEY, (), Text(POLICY)).reason == subject.POLICY_REASONS[0]


@pytest.mark.parametrize(("batch", "reason"), (
    (None, subject.BATCH_REASONS[0]),
    ([], subject.BATCH_REASONS[0]),
    (set(), subject.BATCH_REASONS[0]),
    (frozenset(), subject.BATCH_REASONS[0]),
    ((7,), subject.BATCH_REASONS[1]),
    (("bad",), subject.BATCH_REASONS[2]),
    ((HIGH, LOW), subject.BATCH_REASONS[3]),
    ((OTHER, OTHER), subject.BATCH_REASONS[3]),
))
def test_batch_validation_no_sort_deduplicate_or_repair(batch: object, reason: str) -> None:
    result = subject.evaluate_admit_009(KEY, batch, POLICY)
    assert result.outcome == "invalid" and result.blocks_candidate is True and result.reason == reason
    assert result.canonical_duplicate_identity_key == KEY
    assert result.validated_candidate_fields == ((subject.CANDIDATE_FIELDS[0], KEY),)
    assert result.consumed_context_items == subject.CONTEXT_ITEMS


def test_batch_tuple_and_member_subclasses_are_rejected() -> None:
    class TupleSubclass(tuple):
        pass

    class Text(str):
        pass

    assert subject.evaluate_admit_009(KEY, TupleSubclass(), POLICY).reason == subject.BATCH_REASONS[0]
    assert subject.evaluate_admit_009(KEY, (Text(OTHER),), POLICY).reason == subject.BATCH_REASONS[1]


def test_unique_duplicate_and_multiple_membership_exact_outcomes() -> None:
    unique = subject.evaluate_admit_009(KEY, (OTHER,), POLICY)
    duplicate = subject.evaluate_admit_009(KEY, (KEY,), POLICY)
    multiple = subject.evaluate_admit_009(KEY, (LOW, KEY, HIGH), POLICY)
    assert (unique.outcome, unique.passed, unique.blocks_candidate, unique.reason) == ("passed", True, False, "")
    for result in (duplicate, multiple):
        assert (result.outcome, result.passed, result.blocks_candidate, result.reason) == (
            "blocked", False, True, subject.DUPLICATE_REASON,
        )
        assert result.canonical_duplicate_identity_key == KEY
        assert result.validated_candidate_fields == ((subject.CANDIDATE_FIELDS[0], KEY),)


def test_validation_precedence_short_circuits_later_stages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subject, "_validate_policy", lambda _: (_ for _ in ()).throw(AssertionError("policy reached")))
    assert subject.evaluate_admit_009(None, object(), object()).reason == subject.SCALAR_REASONS[0]
    monkeypatch.undo()
    monkeypatch.setattr(subject, "_validate_batch", lambda _: (_ for _ in ()).throw(AssertionError("batch reached")))
    assert subject.evaluate_admit_009(KEY, object(), None).reason == subject.POLICY_REASONS[0]


def test_batch_failure_precedes_membership() -> None:
    class BombContains:
        def __contains__(self, _: object) -> bool:
            raise AssertionError("membership reached")

    result = subject.evaluate_admit_009(KEY, BombContains(), POLICY)
    assert result.reason == subject.BATCH_REASONS[0]


def test_exact32_matches_checker_and_committed_design_oracle_all_exact10_fields() -> None:
    definitions = checker._definitions()
    assert len(definitions) == 32
    for _, _, key, batch, policy in definitions:
        observed = subject.evaluate_admit_009(key, batch, policy)
        expected = checker._checker_expected(key, batch, policy)
        design = committed_oracle.classify_admit_009_duplicate_identity_key_design(key, batch, policy)
        oracle_full = (
            "ADMIT_009", design["outcome"], design["passed"], design["blocks_candidate"],
            design["reason"], design["canonical_duplicate_identity_key"],
            design["validated_candidate_fields"], design["consumed_candidate_fields"],
            design["consumed_context_items"], design["evaluator_io_used"],
        )
        assert tuple(getattr(observed, name) for name in subject.RESULT_FIELDS) == tuple(
            getattr(expected, name) for name in subject.RESULT_FIELDS
        ) == oracle_full


def test_exact32_groups_and_materialized_complete_results() -> None:
    state = subject.build_interface_state()
    assert len(state["truth_rows"]) == 32
    assert {group: sum(row["case_group"] == group for row in state["truth_rows"]) for group in checker.CHECKER_GROUPS} == checker.CHECKER_GROUPS
    assert all(row["case_passed"] == row["formal_expected_equality"] == row["formal_design_oracle_equality"] == "true" for row in state["truth_rows"])
    assert all(row["expected_full_result"] == row["observed_full_result"] == row["committed_design_oracle_full_result"] for row in state["truth_rows"])


def test_public_evaluator_call_graph_is_exact_pure_and_design_oracle_not_imported() -> None:
    checker._check_call_graph()
    source = Path(subject.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = tuple(
        node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
    )
    assert "duplicate_identity_key_contract_design_gate" not in ast.dump(ast.Module(body=list(imports), type_ignores=[]))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "evaluate_admit_009")
    forbidden = {"candidate_record_id", "ligand_comp_id", "scaffold", "leakage", "provider"}
    segment = ast.get_source_segment(source, function)
    assert segment is not None and forbidden.isdisjoint(set(segment.split()))


def test_exact13_source_structure_sha_and_safe_descendant_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    snapshot = subject.build_frozen_source_snapshot()
    assert subject.validate_frozen_source_snapshot(snapshot)
    assert len(snapshot.records) == 13 and tuple(subject.SOURCE_SHA256) == subject.SOURCE_PATHS
    assert subject._safe_relative_path(Path("../escape")) is False
    assert subject._safe_relative_path(Path("data/raw/forbidden.cif")) is False
    assert subject._safe_relative_path(Path("checkpoints/forbidden.ckpt")) is False
    original = subject.SOURCE_SHA256[subject.SOURCE_PATHS[0]]
    monkeypatch.setitem(subject.SOURCE_SHA256, subject.SOURCE_PATHS[0], "0" * 64)
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        subject.build_frozen_source_snapshot()
    monkeypatch.setitem(subject.SOURCE_SHA256, subject.SOURCE_PATHS[0], original)


def test_all_source_structure_checks_precede_first_byte_read(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    structure = subject._structural_source_check
    git = subject._git

    def observed_structure(path: Path, root: Path) -> bool:
        events.append(f"s:{path}")
        return structure(path, root)

    def observed_git(arguments: object, root: Path, *, text: bool = True) -> object:
        args = tuple(arguments)  # type: ignore[arg-type]
        if args[:1] == ("show",) and len(args) == 2:
            events.append("read")
        return git(arguments, root, text=text)  # type: ignore[arg-type]

    monkeypatch.setattr(subject, "_structural_source_check", observed_structure)
    monkeypatch.setattr(subject, "_git", observed_git)
    subject.build_frozen_source_snapshot()
    first = events.index("read")
    assert first == 13 and all(event.startswith("s:") for event in events[:first])


def test_issue_inventory_byte_identical_and_coverage_still_starts_admit009() -> None:
    state = subject.build_interface_state()
    source = subject._record(state["source_snapshot"], subject.AUTHORITATIVE_ISSUE_PATH).content_bytes
    observed = subject._csv_bytes(subject.ISSUE_COLUMNS, state["issue_rows"])
    assert observed == source == state["issue_bytes"]
    assert hashlib.sha256(observed).hexdigest() == checker.EXPECTED_SOURCE_SHA256[checker.EXPECTED_SOURCE_PATHS[6]]
    issue_map = {row["issue_id"]: row for row in state["issue_rows"]}
    assert issue_map["DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"]["status"] == "resolved"
    coverage = issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    assert coverage["status"] == "open" and coverage["affected_rules"].startswith("ADMIT_009|")


def test_checker_rejects_semantic_tamper_after_manifest_hash_refresh(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    subject.run_covapie_bulk_download_admission_admit_009_rule_logic_interface_v1(root)
    checker._validate_output_tree(root, enforce_frozen_hashes=False)
    path = root / subject.TRUTH_FILENAME
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline="")))
    rows[0]["observed_full_result"] = rows[11]["observed_full_result"]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=subject.TRUTH_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(stream.getvalue(), encoding="utf-8")
    manifest_path = root / subject.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"][subject.TRUTH_FILENAME] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker._validate_output_tree(root, enforce_frozen_hashes=False)


def test_deterministic_materialization_outputs_and_fail_closed_entries(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    first = subject.run_covapie_bulk_download_admission_admit_009_rule_logic_interface_v1(root)
    first_bytes = {name: (root / name).read_bytes() for name in subject.OUTPUT_FILES}
    second = subject.run_covapie_bulk_download_admission_admit_009_rule_logic_interface_v1(root)
    assert first["manifest"] == second["manifest"]
    assert first_bytes == {name: (root / name).read_bytes() for name in subject.OUTPUT_FILES}
    assert all((root / name).is_file() and not (root / name).is_symlink() for name in subject.OUTPUT_FILES)
    extra = tmp_path / "extra"
    shutil.copytree(root, extra)
    (extra / "unexpected.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        subject.run_covapie_bulk_download_admission_admit_009_rule_logic_interface_v1(extra)
    unsafe = tmp_path / "unsafe"
    unsafe.mkdir()
    outside = tmp_path / "outside"
    outside.write_text("unchanged", encoding="utf-8")
    (unsafe / subject.CONTRACT_FILENAME).symlink_to(outside)
    with pytest.raises(ValueError):
        subject.run_covapie_bulk_download_admission_admit_009_rule_logic_interface_v1(unsafe)
    assert outside.read_text(encoding="utf-8") == "unchanged"


def test_manifest_readiness_provider_registry_and_stop_boundaries_truthful() -> None:
    state = subject.build_interface_state()
    payloads, manifest = subject._payloads(state)
    assert set(manifest["readiness"]) == set(subject.READINESS)
    assert all(manifest[key] is manifest["readiness"][key] for key in subject.READINESS)
    assert manifest["real_provider_duplicate_identity_key_count"] == 0
    assert manifest["real_provider_duplicate_identity_mapping_validated"] is False
    assert manifest["admit_009_standalone_evaluator_implemented"] is True
    assert manifest["admit_009_unified_adapter_contract_frozen"] is False
    assert manifest["admit_009_registered_in_engine"] is False
    assert manifest["unified_dispatch_runtime_with_admit_001_to_009_implemented"] is False
    assert manifest["admit_010_standalone_evaluator_implemented"] is False
    assert manifest["evaluate_all_rules_implemented"] is False
    assert manifest["combined_candidate_verdict_implemented"] is False
    assert manifest["ready_for_bulk_download_now"] is manifest["ready_for_training"] is False
    assert subject.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert len(payloads) == 6


def test_production_and_checker_imports_are_silent_without_materialization(tmp_path: Path) -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(subject.REPO_ROOT / "src")
    commands = (
        "import covalent_ext.covapie_bulk_download_admission_admit_009_rule_logic_interface",
        f"import importlib.util,sys;s=importlib.util.spec_from_file_location('check',{str(CHECKER_PATH)!r});m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)",
    )
    for command in commands:
        result = subprocess.run([sys.executable, "-c", command], cwd=tmp_path, env=environment, capture_output=True, text=True)
        assert result.returncode == 0 and result.stdout == result.stderr == ""
    assert tuple(tmp_path.iterdir()) == ()
