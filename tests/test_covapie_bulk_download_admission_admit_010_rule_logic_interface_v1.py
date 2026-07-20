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
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate
    as design,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_010_rule_logic_interface as subject,
)


CHECKER_PATH = subject.REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_010_rule_logic_interface_v1.py"
SPEC = importlib.util.spec_from_file_location("admit010_standalone_checker_tests", CHECKER_PATH)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)

CANDIDATE = "COVAPIE_LEAKAGE_GROUP_000001"


def _base() -> design.LeakageGroupAssignmentProvenanceContractV1:
    return subject._valid_contract(candidate=CANDIDATE)


def _result_values(
    *, outcome: str = "passed", reason: str = "", canonical: str = CANDIDATE,
    validated: object | None = None, contexts: object | None = None,
) -> dict[str, object]:
    return {
        "admission_rule_id": "ADMIT_010", "outcome": outcome,
        "passed": outcome == "passed", "blocks_candidate": outcome != "passed",
        "reason": reason, "canonical_leakage_group_id": canonical,
        "validated_candidate_fields": (
            (("leakage_group_id", canonical),) if canonical else ()
        ) if validated is None else validated,
        "consumed_candidate_fields": ("leakage_group_id",),
        "consumed_context_items": (
            ("leakage_group_assignment_provenance_contract",) if canonical else ()
        ) if contexts is None else contexts,
        "evaluator_io_used": False,
    }


def _invalid(values: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        subject.Admit010EvaluationResult(**values)


def test_public_signature_exact10_frozen_result_and_exact19_identity() -> None:
    signature = inspect.signature(subject.evaluate_admit_010)
    parameters = tuple(signature.parameters.values())
    assert tuple(parameter.name for parameter in parameters) == (
        "leakage_group_id", "leakage_group_assignment_provenance_contract",
    )
    assert all(parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for parameter in parameters)
    assert all(parameter.default is inspect.Parameter.empty for parameter in parameters)
    assert signature.return_annotation == "Admit010EvaluationResult"
    assert tuple(field.name for field in fields(subject.Admit010EvaluationResult)) == subject.RESULT_FIELDS
    assert "__slots__" not in subject.Admit010EvaluationResult.__dict__
    assert subject.LeakageGroupAssignmentProvenanceContractV1 is design.LeakageGroupAssignmentProvenanceContractV1
    result = subject.evaluate_admit_010(CANDIDATE, _base())
    assert type(result) is subject.Admit010EvaluationResult
    assert tuple(vars(result)) == subject.RESULT_FIELDS
    with pytest.raises(FrozenInstanceError):
        result.reason = "changed"  # type: ignore[misc]


def test_result_subclass_dict_and_mapping_are_not_exact_results() -> None:
    class ResultSubclass(subject.Admit010EvaluationResult):
        pass

    with pytest.raises(TypeError, match="subclasses"):
        ResultSubclass(**_result_values())
    assert type(_result_values()) is not subject.Admit010EvaluationResult


def test_direct_result_exact_types_fail_before_hostile_comparison() -> None:
    class Text(str):
        comparisons = 0

        def __eq__(self, other: object) -> bool:
            type(self).comparisons += 1
            raise AssertionError("comparison executed")

    class TupleSubclass(tuple):
        pass

    class Hostile:
        comparisons = 0

        def __eq__(self, other: object) -> bool:
            type(self).comparisons += 1
            raise AssertionError("comparison executed")

    cases = (
        ("admission_rule_id", Hostile()), ("admission_rule_id", Text("ADMIT_010")),
        ("outcome", Text("passed")), ("passed", 1), ("blocks_candidate", 0),
        ("reason", Text("")), ("canonical_leakage_group_id", Text(CANDIDATE)),
        ("validated_candidate_fields", [["leakage_group_id", CANDIDATE]]),
        ("validated_candidate_fields", TupleSubclass((("leakage_group_id", CANDIDATE),))),
        ("validated_candidate_fields", (TupleSubclass(("leakage_group_id", CANDIDATE)),)),
        ("validated_candidate_fields", ((Text("leakage_group_id"), CANDIDATE),)),
        ("validated_candidate_fields", (("leakage_group_id", Text(CANDIDATE)),)),
        ("consumed_candidate_fields", TupleSubclass(("leakage_group_id",))),
        ("consumed_context_items", TupleSubclass(("leakage_group_assignment_provenance_contract",))),
        ("evaluator_io_used", 0),
    )
    for name, replacement in cases:
        values = _result_values()
        values[name] = replacement
        _invalid(values)
    assert Text.comparisons == Hostile.comparisons == 0


@pytest.mark.parametrize("override", (
    {"admission_rule_id": "ADMIT_009"},
    {"outcome": "other", "passed": False, "blocks_candidate": True, "reason": "UNKNOWN"},
    {"passed": False}, {"blocks_candidate": True},
    {"reason": "leakage_group_unassigned"},
    {"outcome": "blocked", "passed": False, "blocks_candidate": True, "reason": ""},
    {"outcome": "invalid", "passed": False, "blocks_candidate": True, "reason": "leakage_group_unassigned"},
    {"validated_candidate_fields": ()}, {"consumed_candidate_fields": ()},
    {"consumed_context_items": ()}, {"evaluator_io_used": True},
    {"reason": "UNKNOWN_REASON"},
))
def test_general_and_cross_field_result_invariants_fail_closed(override: dict[str, object]) -> None:
    values = _result_values()
    values.update(override)
    _invalid(values)


@pytest.mark.parametrize("values", (
    _result_values(outcome="invalid", reason="LEAKAGE_GROUP_ID_TYPE_INVALID", canonical=CANDIDATE),
    _result_values(outcome="invalid", reason="LEAKAGE_GROUP_ID_TYPE_INVALID", canonical="", validated=(("leakage_group_id", CANDIDATE),)),
    _result_values(outcome="invalid", reason="LEAKAGE_GROUP_ID_TYPE_INVALID", canonical="", contexts=("leakage_group_assignment_provenance_contract",)),
    _result_values(outcome="blocked", reason="leakage_group_unassigned", canonical="", contexts=("leakage_group_assignment_provenance_contract",)),
    _result_values(outcome="invalid", reason="LEAKAGE_GROUP_ASSIGNMENT_POLICY_INVALID", canonical=""),
    _result_values(outcome="invalid", reason="LEAKAGE_GROUP_ASSIGNMENT_POLICY_INVALID", canonical=CANDIDATE, contexts=()),
    _result_values(outcome="invalid", reason="LEAKAGE_GROUP_ASSIGNMENT_POLICY_INVALID", canonical="bad"),
))
def test_scalar_short_and_retained_state_conflicts_fail_closed(values: dict[str, object]) -> None:
    _invalid(values)


@pytest.mark.parametrize(("candidate", "outcome", "reason"), (
    (None, "invalid", "LEAKAGE_GROUP_ID_TYPE_INVALID"),
    (7, "invalid", "LEAKAGE_GROUP_ID_TYPE_INVALID"),
    (True, "invalid", "LEAKAGE_GROUP_ID_TYPE_INVALID"),
    ("", "blocked", "leakage_group_unassigned"),
    ("COVAPIE_LEAKAGE_GROUP_00000é", "invalid", "LEAKAGE_GROUP_ID_NON_ASCII"),
    ("covapie_leakage_group_000001", "invalid", "LEAKAGE_GROUP_ID_SYNTAX_INVALID"),
    ("COVAPIE_LEAKAGE_GROUP_00001", "invalid", "LEAKAGE_GROUP_ID_SYNTAX_INVALID"),
    (" COVAPIE_LEAKAGE_GROUP_000001", "invalid", "LEAKAGE_GROUP_ID_SYNTAX_INVALID"),
))
def test_scalar_precedence_and_short_circuit(candidate: object, outcome: str, reason: str) -> None:
    result = subject.evaluate_admit_010(candidate, object())
    assert (result.outcome, result.passed, result.blocks_candidate, result.reason) == (outcome, False, True, reason)
    assert result.canonical_leakage_group_id == ""
    assert result.validated_candidate_fields == ()
    assert result.consumed_context_items == ()
    assert result.consumed_candidate_fields == ("leakage_group_id",)


def test_candidate_and_context_subclasses_are_rejected() -> None:
    class Text(str):
        pass

    class ContextSubclass(design.LeakageGroupAssignmentProvenanceContractV1):
        pass

    base = _base()
    context = ContextSubclass(*(getattr(base, field.name) for field in fields(base)))
    assert subject.evaluate_admit_010(Text(CANDIDATE), base).reason == "LEAKAGE_GROUP_ID_TYPE_INVALID"
    assert subject.evaluate_admit_010(CANDIDATE, context).reason == "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_TYPE_INVALID"


def test_exact71_natural_corpus_full_exact10_equivalence_and_input_immutability() -> None:
    cases = subject._natural_cases()
    assert len(cases) == 71
    groups = {group: sum(case[0] == group for case in cases) for group in checker.EXPECTED_GROUP_COUNTS}
    assert groups == checker.EXPECTED_GROUP_COUNTS
    for _group, case_id, candidate, context, _precedence in cases:
        before_candidate = repr(candidate)
        before_context = repr(context)
        formal = subject.evaluate_admit_010(candidate, context)
        oracle = {"admission_rule_id": "ADMIT_010", **dict(design.classify_admit_010_leakage_group_assignment_provenance_design(candidate, context))}
        assert {name: getattr(formal, name) for name in subject.RESULT_FIELDS} == oracle, case_id
        assert repr(candidate) == before_candidate and repr(context) == before_context


def test_hostile_runtime_fields_are_type_gated_without_comparison_and_do_not_materialize() -> None:
    class Hostile:
        comparisons = 0

        def _hit(self, *_: object) -> bool:
            type(self).comparisons += 1
            raise AssertionError("hostile comparison executed")

        __eq__ = __ne__ = __lt__ = __le__ = __gt__ = __ge__ = _hit

        def __len__(self) -> int:
            return int(self._hit())

        def __iter__(self) -> object:
            self._hit()
            return iter(())

    class HostileText(str):
        comparisons = 0

        def __eq__(self, other: object) -> bool:
            type(self).comparisons += 1
            raise AssertionError("hostile text comparison executed")

    base = _base()
    cases = (
        replace(base, contract_version=Hostile()),
        replace(base, contract_version=HostileText(subject.PROVENANCE_CONTRACT_VERSION)),
        replace(base, canonical_candidate_field_name=HostileText(subject.CANDIDATE_FIELD)),
        replace(base, assignment_policy=HostileText(subject.ASSIGNMENT_POLICY)),
        replace(base, assignment_passed=1), replace(base, split_assignments_written=0),
        replace(base, member_sample_index_row_ids=Hostile()),
        replace(base, member_sample_index_row_ids=["SAMPLE_000001"]),
        replace(base, member_count=True),
    )
    for context in cases:
        result = subject.evaluate_admit_010(CANDIDATE, context)
        assert type(result) is subject.Admit010EvaluationResult and result.blocks_candidate is True
    assert Hostile.comparisons == HostileText.comparisons == 0


def test_formal_call_graph_excludes_oracle_io_provider_grouping_split_and_training() -> None:
    path = Path(subject.__file__)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    calls = set()
    pending = ["evaluate_admit_010"]
    while pending:
        name = pending.pop()
        if name in calls:
            continue
        calls.add(name)
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in functions:
                pending.append(node.func.id)
    assert calls == {
        "evaluate_admit_010", "_formal_result", "_valid_sha256",
        "_valid_opaque_id", "_is_canonical_group_id",
    }
    evaluator_source = ast.get_source_segment(source, functions["evaluate_admit_010"])
    assert evaluator_source is not None
    for forbidden in ("classify_admit_010", "Path(", "open(", "subprocess", "provider", "split(", "training"):
        assert forbidden not in evaluator_source
    top_imports = [node for node in tree.body if isinstance(node, ast.ImportFrom)]
    assert all(alias.name != "classify_admit_010_leakage_group_assignment_provenance_design" for node in top_imports for alias in node.names)
    expected_body_sha256 = {
        "evaluate_admit_010": "654cf59cecfd10138d69ec123140aeada56beaa16560591539e5bd69ef718276",
        "_formal_result": "86e5781a7451def52f1de178fa5de619ead6e73136d26adee0ee9b7f4fee9f7d",
        "_valid_sha256": "ab4cb8c5e63e3d529f52e10b93ec296aac3e31f444880676a806492b68766b53",
        "_valid_opaque_id": "e55fd5da60e6bf00548b36398c640c4820e85028cfaf1e667b2b3d2b8541505a",
        "_is_canonical_group_id": "d4a4c6993f6296b1f0d906df7e59034e54bee05f3292e972da69e3c22b3a45ff",
    }
    for name, expected_sha256 in expected_body_sha256.items():
        segment = ast.get_source_segment(source, functions[name])
        assert segment is not None
        assert hashlib.sha256(segment.encode("utf-8")).hexdigest() == expected_sha256


def test_exact13_source_boundary_structure_sha_and_all_structure_before_reads(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    snapshot = subject.build_frozen_source_snapshot()
    assert subject.validate_frozen_source_snapshot(snapshot)
    assert len(snapshot.records) == 13 and tuple(subject.SOURCE_SHA256) == subject.SOURCE_PATHS
    assert subject._safe_relative_path(Path("../escape")) is False
    assert subject._safe_relative_path(Path("data/raw/forbidden.cif")) is False
    assert subject._safe_relative_path(Path("checkpoints/forbidden.ckpt")) is False
    fake_repo = tmp_path / "repo"
    outside = tmp_path / "outside"
    fake_repo.mkdir()
    outside.mkdir()
    (outside / "source.csv").write_text("outside", encoding="utf-8")
    (fake_repo / "escaped_parent").symlink_to(outside, target_is_directory=True)
    assert subject._resolved_safe_descendant(Path("escaped_parent/source.csv"), fake_repo) is False
    events: list[str] = []
    structure = subject._structural_source_check
    git = subject._git

    def observed_structure(path: Path, root: Path) -> bool:
        events.append("structure")
        return structure(path, root)

    def observed_git(arguments: object, root: Path, *, text: bool = True) -> object:
        args = tuple(arguments)  # type: ignore[arg-type]
        if args[:1] == ("show",) and len(args) == 2:
            events.append("read")
        return git(arguments, root, text=text)  # type: ignore[arg-type]

    monkeypatch.setattr(subject, "_structural_source_check", observed_structure)
    monkeypatch.setattr(subject, "_git", observed_git)
    subject.build_frozen_source_snapshot()
    assert events.index("read") == 13 and events[:13] == ["structure"] * 13


def test_issue_inventory_is_byte_identical_and_has_no_transition() -> None:
    state = subject.build_interface_state()
    source = subject._record(state["snapshot"], subject.AUTHORITATIVE_ISSUE_PATH).content_bytes
    assert state["issue_bytes"] == source
    assert hashlib.sha256(source).hexdigest() == "779932531b630072ff33721e689a2865defdad477df8335a9950c8e4537476bd"
    rows = state["issue_rows"]
    issue_map = {row["issue_id"]: row for row in rows}
    assert issue_map["LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED"]["status"] == "resolved"
    coverage = issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    assert coverage["status"] == "open"
    assert coverage["affected_rules"] == "ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"


def test_deterministic_materialization_and_unsafe_inventory_fail_closed_without_partial_write(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    first = subject.run_covapie_bulk_download_admission_admit_010_rule_logic_interface_v1(root)
    first_bytes = {name: (root / name).read_bytes() for name in subject.OUTPUT_FILES}
    second = subject.run_covapie_bulk_download_admission_admit_010_rule_logic_interface_v1(root)
    assert first["manifest"] == second["manifest"]
    assert first_bytes == {name: (root / name).read_bytes() for name in subject.OUTPUT_FILES}
    assert all((root / name).is_file() and not (root / name).is_symlink() for name in subject.OUTPUT_FILES)
    for kind in ("extra", "symlink", "fifo"):
        unsafe = tmp_path / kind
        shutil.copytree(root, unsafe)
        if kind == "extra":
            (unsafe / "extra.txt").write_text("x", encoding="utf-8")
        else:
            victim = unsafe / subject.CONTRACT_FILENAME
            victim.unlink()
            if kind == "symlink":
                victim.symlink_to(tmp_path / "outside")
            else:
                os.mkfifo(victim)
        before = {path.name: os.lstat(path).st_mtime_ns for path in unsafe.iterdir()}
        with pytest.raises(ValueError):
            subject.run_covapie_bulk_download_admission_admit_010_rule_logic_interface_v1(unsafe)
        assert before == {path.name: os.lstat(path).st_mtime_ns for path in unsafe.iterdir()}


def test_output_resolved_containment_relative_absolute_and_parent_symlink_fail_before_source_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    default_before = {
        name: (subject.REPO_ROOT / subject.DEFAULT_OUTPUT_ROOT / name).read_bytes()
        for name in subject.OUTPUT_FILES
    }
    relative = subject.run_covapie_bulk_download_admission_admit_010_rule_logic_interface_v1(
        subject.DEFAULT_OUTPUT_ROOT,
    )
    assert relative["output_root"] == subject.REPO_ROOT / subject.DEFAULT_OUTPUT_ROOT
    assert default_before == {
        name: (subject.REPO_ROOT / subject.DEFAULT_OUTPUT_ROOT / name).read_bytes()
        for name in subject.OUTPUT_FILES
    }

    absolute_root = tmp_path / "absolute" / "outputs"
    absolute_root.parent.mkdir()
    absolute = subject.run_covapie_bulk_download_admission_admit_010_rule_logic_interface_v1(
        absolute_root,
    )
    assert absolute["output_root"] == absolute_root
    checker._validate_output_tree(absolute_root, enforce_frozen_hashes=False)

    fake_repo = tmp_path / "repo"
    outside = tmp_path / "outside"
    fake_repo.mkdir()
    (outside / "nested").mkdir(parents=True)
    marker = outside / "nested" / "marker.txt"
    marker.write_text("unchanged", encoding="utf-8")
    (fake_repo / "linked").symlink_to(outside, target_is_directory=True)
    escaped_relative = Path("linked/nested/outputs")
    escaped_absolute = fake_repo / escaped_relative
    build_calls = 0

    def forbidden_build(*args: object, **kwargs: object) -> object:
        nonlocal build_calls
        build_calls += 1
        raise AssertionError("source build reached")

    monkeypatch.setattr(subject, "build_interface_state", forbidden_build)
    with pytest.raises(ValueError, match="resolved containment"):
        subject.run_covapie_bulk_download_admission_admit_010_rule_logic_interface_v1(
            escaped_relative, repo_root=fake_repo,
        )
    assert build_calls == 0
    assert marker.read_text(encoding="utf-8") == "unchanged"
    assert not escaped_absolute.exists()
    assert not tuple(outside.rglob("*.tmp"))

    read_calls = 0

    def forbidden_source_read() -> object:
        nonlocal read_calls
        read_calls += 1
        raise AssertionError("checker source read reached")

    monkeypatch.setattr(checker, "_read_verified_sources", forbidden_source_read)
    with pytest.raises(AssertionError, match="resolved containment"):
        checker._validate_output_tree(escaped_absolute, enforce_frozen_hashes=False)
    assert read_calls == 0

    direct_target = outside / "direct_outputs"
    direct_target.mkdir()
    direct_link = tmp_path / "direct_link"
    direct_link.symlink_to(direct_target, target_is_directory=True)
    with pytest.raises(ValueError, match="resolved containment"):
        subject.run_covapie_bulk_download_admission_admit_010_rule_logic_interface_v1(
            direct_link,
        )
    assert build_calls == 0


def _copied_output_tree(tmp_path: Path) -> Path:
    root = tmp_path / "outputs"
    shutil.copytree(subject.REPO_ROOT / subject.DEFAULT_OUTPUT_ROOT, root)
    return root


@pytest.mark.parametrize("mutation", (
    "project", "step", "stage", "admission_rule_id", "public_api",
    "result_type", "result_field_count", "reason_vocabulary_order",
    "leakage_group_regex", "provenance_identity", "formal_parity",
    "contract_row_count", "source_boundary_name", "source_input_count",
    "source_verification_sha", "source_verification_unknown",
    "source_structure_before_read", "issue_preserved", "coverage_status",
    "coverage_rules", "safety_row_count", "manifest_self_hash_rule",
    "recommended_next_step", "validation_failures", "nested_unknown",
    "top_level_unknown", "readiness_mirror",
))
def test_checker_rejects_complete_exact102_manifest_semantic_tamper(
    tmp_path: Path, mutation: str,
) -> None:
    root = _copied_output_tree(tmp_path)
    path = root / subject.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if mutation == "project":
        manifest["project"] = "TAMPERED"
    elif mutation == "step":
        manifest["step"] = "tampered"
    elif mutation == "stage":
        manifest["stage"] = "tampered"
    elif mutation == "admission_rule_id":
        manifest["admission_rule_id"] = "ADMIT_099"
    elif mutation == "public_api":
        manifest["public_api"] = "tampered()"
    elif mutation == "result_type":
        manifest["result_type"] = "dict"
    elif mutation == "result_field_count":
        manifest["result_field_count"] = 9
    elif mutation == "reason_vocabulary_order":
        manifest["reason_vocabulary"][1:3] = reversed(manifest["reason_vocabulary"][1:3])
    elif mutation == "leakage_group_regex":
        manifest["leakage_group_regex"] = ".*"
    elif mutation == "provenance_identity":
        manifest["provenance_type_direct_committed_identity"] = False
    elif mutation == "formal_parity":
        manifest["formal_design_exact10_parity"] = False
    elif mutation == "contract_row_count":
        manifest["contract_row_count"] = 40
    elif mutation == "source_boundary_name":
        manifest["source_boundary_name"] = "tampered"
    elif mutation == "source_input_count":
        manifest["source_input_count"] = 12
    elif mutation == "source_verification_sha":
        manifest["source_input_verification"][0]["expected_sha256"] = "0" * 64
    elif mutation == "source_verification_unknown":
        manifest["source_input_verification"][0]["unknown"] = True
    elif mutation == "source_structure_before_read":
        manifest["source_structural_checks_before_first_explicit_content_read"] = False
    elif mutation == "issue_preserved":
        manifest["issue_inventory_preserved_exactly"] = False
    elif mutation == "coverage_status":
        manifest["coverage_issue_status"] = "resolved"
    elif mutation == "coverage_rules":
        manifest["coverage_issue_affected_rules"] = "ADMIT_011–ADMIT_015"
    elif mutation == "safety_row_count":
        manifest["safety_row_count"] = 34
    elif mutation == "manifest_self_hash_rule":
        manifest["output_sha256_excludes_manifest_self_hash"] = False
    elif mutation == "recommended_next_step":
        manifest["recommended_next_step"] = "start_admit_011"
    elif mutation == "validation_failures":
        manifest["validation_failures"] = ["tampered"]
    elif mutation == "nested_unknown":
        manifest["output_materialization"]["unknown"] = True
    elif mutation == "top_level_unknown":
        manifest["unknown_manifest_key"] = True
    elif mutation == "readiness_mirror":
        manifest["ready_for_training"] = True
    else:  # pragma: no cover - parametrization is exhaustive
        raise AssertionError(mutation)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker._validate_output_tree(root, enforce_frozen_hashes=False)


@pytest.mark.parametrize("contract_id", (
    "RESULT_004", "RESULT_007", "IDENTITY_001", "ORACLE_001",
    "SOURCE_002", "PROVIDER_001", "BOUNDARY_001", "OUTPUT_001",
))
def test_checker_rejects_complete_exact41_contract_semantic_tamper_after_hash_refresh(
    tmp_path: Path, contract_id: str,
) -> None:
    root = _copied_output_tree(tmp_path)
    path = root / subject.CONTRACT_FILENAME
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline="")))
    target = next(row for row in rows if row["contract_id"] == contract_id)
    target["contract_value"] = "tampered_contract"
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=checker.CHECKER_CONTRACT_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(stream.getvalue(), encoding="utf-8")
    manifest_path = root / subject.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"][subject.CONTRACT_FILENAME] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker._validate_output_tree(root, enforce_frozen_hashes=False)


def test_checker_owned_exact41_and_exact102_are_complete_without_production_builders(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(subject, "_contract_rows", lambda: (_ for _ in ()).throw(AssertionError("production contract builder called")))
    monkeypatch.setattr(subject, "_manifest_payload", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("production manifest builder called")))
    contracts = checker._expected_contract_rows()
    manifest = checker._expected_manifest()
    contract_path = subject.REPO_ROOT / subject.DEFAULT_OUTPUT_ROOT / subject.CONTRACT_FILENAME
    observed_contracts = tuple(csv.DictReader(io.StringIO(contract_path.read_text(encoding="utf-8"), newline="")))
    assert len(contracts) == 41 and contracts == observed_contracts
    assert type(manifest) is dict and len(manifest) == 102
    assert manifest == json.loads((subject.REPO_ROOT / subject.DEFAULT_OUTPUT_ROOT / subject.MANIFEST_FILENAME).read_text(encoding="utf-8"))


def test_checker_rejects_truth_semantic_tamper_after_manifest_hash_refresh(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    subject.run_covapie_bulk_download_admission_admit_010_rule_logic_interface_v1(root)
    checker._validate_output_tree(root, enforce_frozen_hashes=False)
    path = root / subject.TRUTH_FILENAME
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline="")))
    rows[0]["reason"] = "LEAKAGE_GROUP_ID_SYNTAX_INVALID"
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


def test_manifest_readiness_provider_runtime_and_training_boundaries() -> None:
    state = subject.build_interface_state()
    payloads, manifest = subject._payloads(state)
    assert set(manifest["readiness"]) == set(subject.READINESS)
    assert all(manifest[key] is manifest["readiness"][key] for key in subject.READINESS)
    assert all(manifest[key] is True for key in subject.TRUE_READINESS)
    assert all(manifest[key] is False for key in subject.FALSE_READINESS)
    assert manifest["leakage_group_id_provider_mapping_validated"] is False
    assert manifest["real_provider_leakage_group_id_count"] == 0
    assert manifest["admit_010_standalone_evaluator_implemented"] is True
    assert manifest["admit_010_unified_adapter_contract_frozen"] is False
    assert manifest["admit_010_registered_in_engine"] is False
    assert manifest["unified_dispatch_runtime_with_admit_001_to_010_implemented"] is False
    assert manifest["admit_011_started"] is False
    assert manifest["ready_for_bulk_download_now"] is manifest["ready_for_training"] is False
    assert subject.MANIFEST_FILENAME not in manifest["output_sha256"] and len(payloads) == 6


def test_production_checker_and_tests_compile_and_import_silently(tmp_path: Path) -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(subject.REPO_ROOT / "src")
    commands = (
        "import covalent_ext.covapie_bulk_download_admission_admit_010_rule_logic_interface",
        f"import importlib.util,sys;s=importlib.util.spec_from_file_location('check',{str(CHECKER_PATH)!r});m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)",
    )
    for command in commands:
        result = subprocess.run([sys.executable, "-c", command], cwd=tmp_path, env=environment, capture_output=True, text=True)
        assert result.returncode == 0 and result.stdout == result.stderr == ""
    assert tuple(tmp_path.iterdir()) == ()
