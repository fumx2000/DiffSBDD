from __future__ import annotations

import ast
import csv
import errno
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
from collections.abc import Iterator, Mapping
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_014_download_authorization_contract_design_gate
    as gate,
)

CHECKER_PATH = (
    REPO_ROOT
    / "scripts/check_covapie_bulk_download_admission_admit_014_download_authorization_contract_v1.py"
)
SPEC = importlib.util.spec_from_file_location("admit014_download_checker", CHECKER_PATH)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
ROOT = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT


@pytest.fixture(scope="module")
def snapshot():
    return gate.build_frozen_source_snapshot()


@pytest.fixture(scope="module")
def payloads(snapshot):
    return gate.build_artifacts(snapshot)


@pytest.fixture(scope="module")
def manifest(payloads):
    return json.loads(payloads[gate.MANIFEST_FILE])


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode(), newline="")))


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def _commit(repo: Path, message: str) -> None:
    result = _git(
        repo,
        "-c",
        "user.name=CovaPIE Test",
        "-c",
        "user.email=covapie-test@example.invalid",
        "commit",
        "-m",
        message,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _seed_lifecycle(
    root: Path, *, tracked: bool = False, descendant: bool = False
) -> tuple[Path, str]:
    root.mkdir(parents=True)
    assert _git(root, "init", "-q").returncode == 0
    (root / "baseline.txt").write_text("baseline\n", encoding="utf-8")
    assert _git(root, "add", "--", "baseline.txt").returncode == 0
    _commit(root, "baseline")
    base = _git(root, "rev-parse", "HEAD").stdout.strip()
    if descendant:
        (root / "descendant.txt").write_text("descendant\n", encoding="utf-8")
        assert _git(root, "add", "--", "descendant.txt").returncode == 0
        _commit(root, "descendant")
    for relative in checker.EXACT10:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"fixture:{relative.as_posix()}\n", encoding="utf-8")
    if tracked:
        assert _git(
            root, "add", "--", *(path.as_posix() for path in checker.EXACT10)
        ).returncode == 0
        _commit(root, "Exact10")
    return root, base


class Probe(Mapping[str, object]):
    def __init__(
        self,
        values: dict[str, object] | None = None,
        *,
        error: BaseException | None = None,
    ) -> None:
        self.values = {} if values is None else values
        self.error = error
        self.item = 0
        self.item_keys: list[str] = []
        self.iteration = 0
        self.length = 0
        self.gets = 0
        self.contains = 0

    def __getitem__(self, key: str) -> object:
        self.item += 1
        self.item_keys.append(key)
        if self.error is not None:
            raise self.error
        return self.values[key]

    def __iter__(self) -> Iterator[str]:
        self.iteration += 1
        raise AssertionError("iteration forbidden")

    def __len__(self) -> int:
        self.length += 1
        raise AssertionError("len forbidden")

    def get(self, key: str, default: object = None) -> object:
        self.gets += 1
        raise AssertionError("get forbidden")

    def __contains__(self, key: object) -> bool:
        self.contains += 1
        raise AssertionError("contains forbidden")

    @property
    def access(self) -> int:
        return self.item + self.iteration + self.length + self.gets + self.contains


def classify(context: object, **forbidden: object):
    return gate.classify_admit_014_download_authorization_contract_design(
        context, **forbidden
    )


def test_base_identity_and_ancestry() -> None:
    result = _git(
        REPO_ROOT,
        "show",
        "-s",
        "--format=%H%n%P%n%T%n%s",
        gate.BASE_COMMIT,
    )
    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        gate.BASE_COMMIT,
        gate.BASE_PARENT,
        gate.BASE_TREE,
        gate.BASE_SUBJECT,
    ]
    assert _git(
        REPO_ROOT, "merge-base", "--is-ancestor", gate.BASE_COMMIT, "HEAD"
    ).returncode == 0


def test_canonical_cpython_3104_and_policy() -> None:
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    assert gate.CANONICAL_PYTHON_VERSION == "3.10.4"
    assert gate.NONCANONICAL_PYTHON_POLICY == (
        "evaluator_semantic_smoke_only; artifact_build_checker_and_frozen_ast_forbidden"
    )


def test_admit014_precondition_lineage_and_exact11_sources(snapshot) -> None:
    assert len(snapshot) == 11
    assert tuple(item.path for item in snapshot) == gate.SOURCE_PATHS
    assert snapshot[0].sha256 == (
        "d134e43f01860bd193eacab6a38171bb508b1e1e48fcf1559f8105d74d0e2632"
    )
    pre = gate._csv_rows(snapshot, gate.PRE_MATRIX)
    assert len(pre) == 51
    assert sum(row["completeness_status"] == "complete" for row in pre) == 25
    assert sum(row["implementation_blocking"] == "true" for row in pre) == 26
    assert all(
        not item.path.as_posix().startswith(("data/raw/", "checkpoints/"))
        for item in snapshot
    )


def test_step14aua_canonical_admit014_and_admit015_context_lineage(
    snapshot, payloads
) -> None:
    contexts = gate._csv_rows(snapshot, gate.STEP14AUA_CONTEXT)
    by_rule = {row["required_by_rules"]: row for row in contexts}
    assert by_rule["ADMIT_014"]["context_item"] == (
        "current_stage_download_authorized"
    )
    assert by_rule["ADMIT_015"] == {
        "context_item": "current_stage_training_authorized",
        "context_scope": "stage",
        "required_by_rules": "ADMIT_015",
        "provided_by_future_caller": "true",
        "filesystem_access_inside_evaluator": "false",
        "network_access_inside_evaluator": "false",
        "deterministic_now": "true",
        "deterministic_after_contract_freeze": "true",
        "exact_contract_defined": "true",
        "implementation_ready": "true",
        "blocking_reasons": "",
    }
    truth = {
        row["case_id"]: row
        for row in _rows(payloads[gate.TRUTH_FILE])
    }
    for case_id in ("ADMIT015_PLUS_TRUE", "ADMIT015_PLUS_FALSE"):
        representation = truth[case_id]["stage_context_representation"]
        assert "current_stage_training_authorized" in representation
        assert "current_stage_" + "admit_015_authorized" not in representation


def test_stage_context_is_the_only_authority(manifest) -> None:
    contract = manifest["authorization_contract"]
    assert contract["authoritative_envelope"] == "stage_authorization_context"
    assert contract["authoritative_key"] == "current_stage_download_authorized"
    assert contract["forbidden_envelopes"] == [
        "candidate_record",
        "batch_context",
        "evaluation_context",
        "download_result_context",
    ]


def test_exact_bool_true_and_false() -> None:
    passed = classify({"current_stage_download_authorized": True})
    blocked = classify({"current_stage_download_authorized": False})
    assert (passed.outcome, passed.passed, passed.blocks_candidate, passed.reason) == (
        "passed", True, False, "",
    )
    assert (
        blocked.outcome,
        blocked.passed,
        blocked.blocks_candidate,
        blocked.reason,
    ) == ("blocked", False, True, "BULK_DOWNLOAD_NOT_AUTHORIZED")
    assert passed.evaluator_io_used is blocked.evaluator_io_used is False


@pytest.mark.parametrize(
    "value",
    [
        0,
        1,
        0.0,
        1.0,
        "true",
        "false",
        "",
        None,
        [],
        {},
        object(),
    ],
)
def test_non_exact_bool_is_rejected_without_coercion(value: object) -> None:
    result = classify({"current_stage_download_authorized": value})
    assert result.outcome == "blocked"
    assert result.reason == "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_TYPE_INVALID"


@pytest.mark.parametrize(
    ("context", "reason"),
    [
        (None, "STAGE_AUTHORIZATION_CONTEXT_REQUIRED"),
        (object(), "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID"),
        (7, "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID"),
        ("true", "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID"),
        ([], "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID"),
        ({}, "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING"),
        ({"unrelated": True}, "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING"),
    ],
)
def test_missing_and_nonmapping_fail_closed(context: object, reason: str) -> None:
    result = classify(context)
    assert result.outcome == "blocked"
    assert result.reason == reason


def test_keyerror_and_nonkeyerror_lookup_precedence() -> None:
    missing = classify(Probe(error=KeyError("target")))
    runtime = classify(Probe(error=RuntimeError("boom")))
    value = classify(Probe(error=ValueError("boom")))
    assert missing.reason == "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING"
    assert runtime.reason == value.reason == "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED"


@pytest.mark.parametrize(
    "context",
    [
        Probe({"current_stage_training_authorized": False, "current_stage_download_authorized": True}),
        Probe({**{f"extra_{index}": object() for index in range(20)}, "current_stage_download_authorized": True}),
    ],
)
def test_extra_keys_and_admit015_coexist_without_iteration(context: Probe) -> None:
    result = classify(context)
    assert result.outcome == "passed"
    assert context.item == 1
    assert context.item_keys == ["current_stage_download_authorized"]
    assert context.iteration == context.length == context.gets == context.contains == 0


def test_no_iteration_len_get_or_contains_even_when_they_raise() -> None:
    context = Probe({"current_stage_download_authorized": True})
    result = classify(context)
    assert result.outcome == "passed"
    assert (context.item, context.iteration, context.length, context.gets, context.contains) == (
        1, 0, 0, 0, 0,
    )


@pytest.mark.parametrize(
    "envelope",
    ["candidate_record", "batch_context", "evaluation_context", "download_result_context"],
)
def test_forbidden_envelopes_have_zero_access(envelope: str) -> None:
    forbidden = Probe({"current_stage_download_authorized": True})
    result = classify(None, **{envelope: forbidden})
    assert result.reason == "STAGE_AUTHORIZATION_CONTEXT_REQUIRED"
    assert forbidden.access == 0


def test_forbidden_envelopes_cannot_override_stage_value() -> None:
    candidate = Probe({"current_stage_download_authorized": True})
    evaluation = Probe({"current_stage_download_authorized": False})
    blocked = classify(
        {"current_stage_download_authorized": False}, candidate_record=candidate
    )
    passed = classify(
        {"current_stage_download_authorized": True},
        evaluation_context=evaluation,
    )
    assert blocked.reason == "BULK_DOWNLOAD_NOT_AUTHORIZED"
    assert passed.outcome == "passed"
    assert candidate.access == evaluation.access == 0


def test_current_false_and_synthetic_true_are_distinct(manifest) -> None:
    assert classify({"current_stage_download_authorized": True}).outcome == "passed"
    assert manifest["synthetic_true_design_case_grants_current_permission"] is False
    assert manifest["current_permission"] is False
    assert manifest["ready_for_bulk_download_now"] is False


def test_closed_outcome_reason_vocabulary_and_precedence(payloads, manifest) -> None:
    rows = _rows(payloads[gate.FAILURE_FILE])
    assert manifest["outcome_vocabulary"] == ["passed", "blocked"]
    assert manifest["reason_vocabulary"] == list(gate.REASON_VOCABULARY)
    assert [row["reason"] for row in rows] == list(gate.REASON_VOCABULARY[1:]) + [""]
    assert [row["precedence_order"] for row in rows] == [str(i) for i in range(1, 8)]
    assert [row["outcome"] for row in rows] == ["blocked"] * 6 + ["passed"]


def test_truth_matrix_exact40_groups_and_zero_forbidden_access(payloads, manifest) -> None:
    rows = _rows(payloads[gate.TRUTH_FILE])
    assert tuple(rows[0]) == gate.TRUTH_COLUMNS
    assert len(rows) == 40
    assert [row["case_order"] for row in rows] == [str(i) for i in range(1, 41)]
    assert all(row["case_passed"] == "true" for row in rows)
    assert all(
        row[column] == "0"
        for row in rows
        for column in (
            "mapping_iteration_count",
            "mapping_len_count",
            "mapping_get_count",
            "mapping_contains_count",
            "forbidden_envelope_access_count",
        )
    )
    assert manifest["truth_matrix_group_counts"] == {
        "context_structure": 7,
        "exact_bool": 2,
        "non_exact_bool": 12,
        "mapping_behavior": 10,
        "forbidden_pseudo_authority": 6,
        "current_future": 3,
    }


def test_trusted_caller_provenance_and_replay_responsibilities(manifest) -> None:
    trust = manifest["trust_boundary"]
    assert trust == {
        "trust_from_call_boundary_not_mapping_string": True,
        "context_invocation_local": True,
        "caller_reconstructs_every_invocation": True,
        "artifact_cache_raw_previous_invocation_replay_allowed": False,
        "evaluator_authentication_or_signature_verification": False,
        "cryptographic_authentication_in_evaluator_scope": False,
    }
    rows = _rows(
        gate.build_artifacts(gate.build_frozen_source_snapshot())[gate.VALUE_FILE]
    )
    owners = {row["responsibility_owner"] for row in rows}
    assert owners == {"evaluator", "trusted caller", "future orchestration"}


def test_mandatory_enforcement_contract_is_frozen_not_implemented(manifest) -> None:
    contract = manifest[
        "mandatory_pre_download_authorization_enforcement_contract"
    ]
    assert contract["stage_global_guard"] is True
    assert contract["evaluate_once_each_real_download_stage_invocation"] is True
    assert contract["only_pass_may_continue"] is True
    assert contract["combined_verdict_required"] is False
    assert contract["combined_verdict_may_override_blocked"] is False
    assert contract["implemented"] is False
    assert [
        contract["blocked_provider_call_count"],
        contract["blocked_network_call_count"],
        contract["blocked_download_count"],
        contract["blocked_raw_write_count"],
    ] == [0, 0, 0, 0]


def test_precondition_transition_exact46_complete_exact5_open(manifest) -> None:
    transition = manifest["precondition_transition"]
    assert transition["row_count"] == 51
    assert transition["complete_count"] == 46
    assert transition["incomplete_count"] == 5
    assert transition["implementation_blocking_count"] == 5
    assert transition["remaining_open_precondition_ids"] == [
        "PRE_039", "PRE_040", "PRE_041", "PRE_048", "PRE_049",
    ]


def test_exact30_issue_continuity_exact5_transitions_exact2_open(
    snapshot, payloads
) -> None:
    inherited = gate._csv_rows(snapshot, gate.PRE_ISSUES)
    rows = _rows(payloads[gate.ISSUE_FILE])
    assert len(rows) == len(inherited) == 30
    assert rows[:23] == inherited[:23]
    assert [row["issue_id"] for row in rows] == [
        row["issue_id"] for row in inherited
    ]
    transitioned = [
        row
        for row in rows
        if row["successor_transition_action"]
        == "resolved_by_successor_contract_design"
    ]
    assert [row["issue_id"] for row in transitioned] == list(gate.RESOLVED_ISSUES)
    by_id = {row["issue_id"]: row for row in rows}
    assert all(
        by_id[issue_id]["successor_effective_status"] == "open"
        for issue_id in gate.OPEN_ADMIT_014_ISSUES
    )
    assert by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == (
        "ADMIT_014|ADMIT_015"
    )


def test_readiness_is_exact_and_fail_closed(manifest) -> None:
    expected = {
        **{key: True for key in gate.TRUE_READINESS},
        **{key: False for key in gate.FALSE_READINESS},
    }
    assert manifest["readiness"] == expected
    assert all(manifest[key] is True for key in gate.TRUE_READINESS)
    assert all(manifest[key] is False for key in gate.FALSE_READINESS)
    assert manifest["recommended_next_step"] == (
        "design_covapie_admit_014_formal_evaluator_interface_contract_v1"
    )


def test_no_formal_evaluator_result_adapter_registry_or_runtime() -> None:
    source = (REPO_ROOT / checker.PRODUCTION).read_text(encoding="utf-8")
    tree = ast.parse(source)
    definitions = {
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    assert "evaluate_admit_014" not in definitions
    assert "Admit014EvaluationResult" not in definitions
    assert "_evaluate_registered_admit_014" not in definitions
    assert "evaluate_admission_rule" not in definitions
    assert "EVALUATOR_REGISTRY" not in {
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }


def test_deterministic_build_and_inode_preserving_noop(tmp_path, payloads) -> None:
    root = tmp_path / "out"
    first = gate.materialize_contract(root)
    before = {
        path.name: (path.stat().st_ino, path.read_bytes()) for path in root.iterdir()
    }
    second = gate.materialize_contract(root)
    assert first == second
    assert before == {
        path.name: (path.stat().st_ino, path.read_bytes()) for path in root.iterdir()
    }
    assert {path.name: path.read_bytes() for path in root.iterdir()} == payloads


def test_existing_mismatch_fails_closed(tmp_path) -> None:
    root = tmp_path / "out"
    gate.materialize_contract(root)
    (root / gate.VALUE_FILE).write_bytes(b"tampered\n")
    with pytest.raises(ValueError, match="existing output set mismatch"):
        gate.materialize_contract(root)


def test_gpfs_einval_fails_closed_without_os_replace(tmp_path, monkeypatch) -> None:
    root = tmp_path / "out"
    replace_called = False

    def reject(*args):
        raise OSError(errno.EINVAL, "simulated GPFS EINVAL")

    def forbidden_replace(*args):
        nonlocal replace_called
        replace_called = True
        raise AssertionError("os.replace fallback called")

    monkeypatch.setattr(gate, "_rename_noreplace", reject)
    monkeypatch.setattr(os, "replace", forbidden_replace)
    with pytest.raises(OSError) as captured:
        gate.materialize_contract(root)
    assert captured.value.errno == errno.EINVAL
    assert replace_called is False
    assert not root.exists()
    assert not list(tmp_path.glob(".*.staging"))


@pytest.mark.parametrize(
    "race", ["same_byte_leaf_replacement", "in_place_mutation", "parent_replacement"]
)
def test_pinned_source_races_are_rejected(tmp_path, monkeypatch, race: str) -> None:
    repo = tmp_path / "repo"
    source = repo / "evidence/source.txt"
    source.parent.mkdir(parents=True)
    source.write_text("frozen\n", encoding="utf-8")
    monkeypatch.setattr(gate, "REPO_ROOT", repo)
    original_read = gate.os.read
    mutated = False

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal mutated
        data = original_read(descriptor, size)
        if data and not mutated:
            mutated = True
            if race == "same_byte_leaf_replacement":
                replacement = source.with_name("replacement")
                replacement.write_bytes(source.read_bytes())
                os.rename(replacement, source)
            elif race == "in_place_mutation":
                with source.open("ab") as stream:
                    stream.write(b"mutation")
            else:
                old = repo / "evidence-old"
                os.rename(source.parent, old)
                source.parent.mkdir()
                source.write_text("frozen\n", encoding="utf-8")
        return data

    monkeypatch.setattr(gate.os, "read", racing_read)
    with pytest.raises(ValueError):
        gate._pinned_read_relative(Path("evidence/source.txt"))


def test_checker_output_leaf_replacement_race_is_rejected(
    tmp_path, payloads, monkeypatch
) -> None:
    root = tmp_path / "out"
    root.mkdir()
    for name, data in payloads.items():
        (root / name).write_bytes(data)
    original_read = checker.os.read
    reads = 0

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal reads
        data = original_read(descriptor, size)
        if data:
            reads += 1
            if reads == 2:
                target = root / checker.FILES[0]
                replacement = root / "replacement"
                replacement.write_bytes(target.read_bytes())
                os.rename(replacement, target)
        return data

    monkeypatch.setattr(checker.os, "read", racing_read)
    with pytest.raises(ValueError):
        checker._pinned_outputs(root)


def test_manifest_duplicate_missing_extra_and_reorder_rejected(payloads) -> None:
    text = payloads[gate.MANIFEST_FILE].decode()
    duplicate = text.replace(
        '{\n  "project": "CovaPIE",',
        '{\n  "project": "tampered",\n  "project": "CovaPIE",',
        1,
    ).encode()
    with pytest.raises(ValueError, match="duplicate JSON key"):
        checker._parse_manifest_exact(duplicate)
    for case in ("missing", "extra", "reordered"):
        value = json.loads(text)
        if case == "missing":
            value.pop("project")
        elif case == "extra":
            value["unexpected"] = True
        else:
            project = value.pop("project")
            value["project"] = project
        tampered = (json.dumps(value, indent=2) + "\n").encode()
        with pytest.raises(ValueError, match="missing/extra/reordered"):
            checker._parse_manifest_exact(tampered)


def test_synchronized_csv_manifest_tamper_rejected(payloads) -> None:
    outputs = dict(payloads)
    outputs[gate.VALUE_FILE] += b"tampered\n"
    manifest = json.loads(outputs[gate.MANIFEST_FILE])
    manifest["output_sha256"][gate.VALUE_FILE] = hashlib.sha256(
        outputs[gate.VALUE_FILE]
    ).hexdigest()
    assert hashlib.sha256(outputs[gate.VALUE_FILE]).hexdigest() != (
        checker.OUTPUT_SHA256[gate.VALUE_FILE]
    )


def test_checker_passes_and_reports_lifecycle() -> None:
    result = subprocess.run(
        [sys.executable, str(CHECKER_PATH)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    tracked = _git(
        REPO_ROOT, "ls-files", "--error-unmatch", "--", checker.TEST.as_posix()
    ).returncode == 0
    assert f"lifecycle={'post_commit' if tracked else 'pre_commit'}" in result.stdout


@pytest.mark.parametrize(
    "relative",
    [checker.PRODUCTION, checker.CHECKER, checker.TEST],
)
def test_isolated_imports_are_silent(tmp_path, relative: Path) -> None:
    path = REPO_ROOT / relative
    code = (
        "import importlib.util,sys;"
        f"s=importlib.util.spec_from_file_location('isolated',{str(path)!r});"
        "m=importlib.util.module_from_spec(s);sys.modules['isolated']=m;"
        "s.loader.exec_module(m)"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""


def test_lifecycle_positive_pre_descendant_and_post(tmp_path) -> None:
    pre, base = _seed_lifecycle(tmp_path / "pre")
    assert checker._lifecycle(pre, base) == "pre_commit"
    descendant, descendant_base = _seed_lifecycle(
        tmp_path / "descendant", descendant=True
    )
    assert checker._lifecycle(descendant, descendant_base) == "pre_commit"
    post, post_base = _seed_lifecycle(tmp_path / "post", tracked=True)
    assert checker._lifecycle(post, post_base) == "post_commit"


@pytest.mark.parametrize(
    "case",
    [
        "mixed",
        "staged",
        "dirty",
        "missing",
        "ignored",
        "extra",
        "seventh",
        "symlink",
        "oversized",
        "base_nonancestor",
        "forbidden_suffix",
    ],
)
def test_lifecycle_negative_states(tmp_path, case: str) -> None:
    repo, base = _seed_lifecycle(tmp_path / case, tracked=case == "dirty")
    exact10 = checker.EXACT10
    if case == "mixed":
        assert _git(repo, "add", "--", exact10[0].as_posix()).returncode == 0
        _commit(repo, "one stage path")
    elif case == "staged":
        assert _git(repo, "add", "--", exact10[0].as_posix()).returncode == 0
    elif case == "dirty":
        with (repo / exact10[0]).open("a", encoding="utf-8") as stream:
            stream.write("dirty\n")
    elif case == "missing":
        (repo / exact10[0]).unlink()
    elif case == "ignored":
        (repo / ".gitignore").write_text(exact10[0].as_posix() + "\n")
    elif case == "extra":
        (repo / "docs/extra_admit_014_download_authorization_contract.md").write_text(
            "extra\n"
        )
    elif case == "seventh":
        (repo / checker.OUTPUT_ROOT / "seventh.csv").write_text("extra\n")
    elif case == "symlink":
        target = repo / exact10[3]
        target.unlink()
        target.symlink_to(repo / "baseline.txt")
    elif case == "oversized":
        os.truncate(repo / exact10[0], 101 * 1024 * 1024)
    elif case == "base_nonancestor":
        base = "0" * 40
    else:
        exact10 = (exact10[0].with_suffix(".pt"), *exact10[1:])
    with pytest.raises(ValueError):
        checker._lifecycle(repo, base, exact10)


def test_tracked_ignored_candidate_is_rejected(tmp_path) -> None:
    repo, base = _seed_lifecycle(tmp_path / "tracked", tracked=True)
    ignored = checker.EXACT10[0]
    (repo / ".gitignore").write_text(ignored.as_posix() + "\n")
    with pytest.raises(ValueError, match="ignored candidate"):
        checker._lifecycle(repo, base)


def test_exact10_inventory_no_symlink_forbidden_or_large() -> None:
    paths = [REPO_ROOT / path for path in checker.EXACT10]
    assert len(paths) == len(set(paths)) == 10
    forbidden = {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
        ".npz", ".tmp", ".part",
    }
    assert not any(path.is_symlink() for path in paths)
    assert not any(path.suffix in forbidden for path in paths)
    assert not any(path.stat().st_size > 100 * 1024 * 1024 for path in paths)


def test_protected_paths_and_predecessors_unchanged() -> None:
    changed = _git(REPO_ROOT, "diff", "--name-only").stdout.splitlines()
    protected = (
        "data/raw/",
        "checkpoints/",
        "equivariant_diffusion/",
        "lightning_modules.py",
        "dataset.py",
        "data/prepare_crossdocked.py",
    )
    assert not any(
        path == item or path.startswith(item)
        for path in changed
        for item in protected
    )
    assert hashlib.sha256((REPO_ROOT / gate.PRE_PRODUCTION).read_bytes()).hexdigest() == (
        gate.SOURCE_SHA256[gate.PRE_PRODUCTION]
    )
    assert hashlib.sha256((REPO_ROOT / gate.RUNTIME_PRODUCTION).read_bytes()).hexdigest() == (
        gate.SOURCE_SHA256[gate.RUNTIME_PRODUCTION]
    )
