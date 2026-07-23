from __future__ import annotations

import ast
import csv
import errno
import hashlib
import importlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_014_formal_evaluator_interface_preconditions_audit
    as audit,
)

CHECKER_PATH = (
    REPO_ROOT
    / "scripts"
    / "check_covapie_bulk_download_admission_admit_014_formal_evaluator_interface_preconditions_audit_v1.py"
)
SPEC = importlib.util.spec_from_file_location("admit014_independent_checker", CHECKER_PATH)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


@pytest.fixture(scope="module")
def snapshot():
    return audit.build_frozen_source_snapshot()


@pytest.fixture(scope="module")
def payloads(snapshot):
    return audit._payloads(snapshot)


@pytest.fixture(scope="module")
def manifest(payloads):
    return json.loads(payloads[audit.MANIFEST])


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode(), newline="")))


def _hashes(root: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.iterdir()
    }


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


def _make_synthetic_lifecycle_repo(
    root: Path, *, tracked: bool = False, descendant: bool = False
) -> tuple[Path, str]:
    root.mkdir()
    assert _git(root, "init", "-q").returncode == 0
    (root / "baseline.txt").write_text("baseline\n", encoding="utf-8")
    assert _git(root, "add", "--", "baseline.txt").returncode == 0
    _commit(root, "baseline")
    base = _git(root, "rev-parse", "HEAD").stdout.strip()
    if descendant:
        (root / "unrelated-descendant.txt").write_text("descendant\n", encoding="utf-8")
        assert _git(root, "add", "--", "unrelated-descendant.txt").returncode == 0
        _commit(root, "unrelated descendant")
    for path in checker.EXACT10:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"fixture:{path.as_posix()}\n", encoding="utf-8")
    if tracked:
        assert _git(
            root, "add", "--", *(path.as_posix() for path in checker.EXACT10)
        ).returncode == 0
        _commit(root, "tracked Exact10")
    return root, base


def test_base_identity_and_ancestor() -> None:
    result = subprocess.run(
        ["git", "show", "-s", "--format=%H%n%P%n%T%n%s", audit.BASE_COMMIT],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        audit.BASE_COMMIT,
        audit.BASE_PARENT,
        audit.BASE_TREE,
        audit.BASE_SUBJECT,
    ]
    assert subprocess.run(
        ["git", "merge-base", "--is-ancestor", audit.BASE_COMMIT, "HEAD"],
        cwd=REPO_ROOT,
        check=False,
    ).returncode == 0


def test_canonical_cpython_3104_and_noncanonical_policy() -> None:
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    assert audit.CANONICAL_PYTHON_VERSION == "3.10.4"
    assert audit.NONCANONICAL_PYTHON_POLICY == (
        "evaluator_semantic_smoke_only; artifact_build_checker_and_frozen_ast_forbidden"
    )


def test_step14at_admit014_exact_registry_row(snapshot) -> None:
    row = next(
        row
        for row in audit._csv_rows(snapshot, audit.DESIGN_RULES)
        if row["admission_rule_id"] == "ADMIT_014"
    )
    assert row == {
        "admission_rule_id": "ADMIT_014",
        "admission_rule_name": "current_gate_grants_no_download_permission",
        "evidence_source": "current_design_gate",
        "required_status": "bulk_download_not_authorized_now",
        "failure_severity": "blocking",
        "blocking_reason": "bulk_download_not_authorized",
        "evaluation_phase": "current_step",
        "network_required": "false",
        "raw_structure_required": "false",
        "ready_for_future_implementation": "true",
    }


def test_ready_for_future_implementation_is_not_download_authorization(manifest) -> None:
    assert manifest["ready_for_future_implementation"] is True
    assert manifest["ready_for_future_implementation_means_contract_design_only"] is True
    assert manifest["ready_for_future_implementation_grants_download_permission"] is False
    assert manifest["current_gate_grants_download_permission"] is False


def test_current_runtime_known_but_not_registered(snapshot) -> None:
    runtime = audit._json(snapshot, audit.RUNTIME_MANIFEST)
    assert runtime["registered_rule_ids"] == [
        f"ADMIT_{index:03d}" for index in range(1, 14)
    ]
    assert runtime["known_not_registered_rule_ids"] == ["ADMIT_014", "ADMIT_015"]
    assert runtime["admit_014_registered_in_engine"] is False


def test_step14aua_explicit_context_lineage_is_authoritative(snapshot) -> None:
    executable = next(
        row
        for row in audit._csv_rows(snapshot, audit.PRECONDITION_RULES)
        if row["admission_rule_id"] == "ADMIT_014"
    )
    assert executable["candidate_field_dependencies"] == ""
    assert executable["batch_context_dependencies"] == ""
    assert executable["evaluation_context_dependencies"] == (
        "current_stage_download_authorized"
    )
    assert executable["semantics_complete"] == "true"
    assert executable["implementation_disposition"] == "rule_logic_ready"
    context = next(
        row
        for row in audit._csv_rows(snapshot, audit.PRECONDITION_CONTEXT)
        if row["context_item"] == "current_stage_download_authorized"
    )
    assert context == {
        "context_item": "current_stage_download_authorized",
        "context_scope": "stage",
        "required_by_rules": "ADMIT_014",
        "provided_by_future_caller": "true",
        "filesystem_access_inside_evaluator": "false",
        "network_access_inside_evaluator": "false",
        "deterministic_now": "true",
        "deterministic_after_contract_freeze": "true",
        "exact_contract_defined": "true",
        "implementation_ready": "true",
        "blocking_reasons": "",
    }


def test_current_runtime_is_single_rule_and_has_stage_envelope(snapshot) -> None:
    source = audit._source(snapshot, audit.RUNTIME_PRODUCTION).content.decode()
    tree = ast.parse(source)
    dispatcher = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "evaluate_admission_rule"
    )
    assert dispatcher.body[0].value.value == (
        "Evaluate exactly one registered rule without I/O or aggregation."
    )
    assert [argument.arg for argument in dispatcher.args.kwonlyargs][-1] == (
        "stage_authorization_context"
    )
    assert "_evaluate_registered_admit_014" not in {
        node.name for node in tree.body if isinstance(node, ast.FunctionDef)
    }


def test_no_download_provider_network_raw_or_training_readiness(manifest) -> None:
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["provider_mapping_validated"] is False
    assert manifest["real_provider_evaluation_ready"] is False
    assert manifest["ready_for_training"] is False
    assert all(value is False for value in manifest["safety"].values())


def test_precondition_matrix_contiguous_exact51(payloads) -> None:
    rows = _rows(payloads[audit.PRECONDITION])
    assert tuple(rows[0]) == audit.COLUMNS[audit.PRECONDITION]
    assert [row["precondition_order"] for row in rows] == [
        str(index) for index in range(1, 52)
    ]
    assert [row["precondition_id"] for row in rows] == [
        f"PRE_{index:03d}" for index in range(1, 52)
    ]


def test_precondition_complete_incomplete_and_blocking_counts(payloads, manifest) -> None:
    rows = _rows(payloads[audit.PRECONDITION])
    assert sum(row["completeness_status"] == "complete" for row in rows) == 25
    assert sum(row["completeness_status"] == "incomplete" for row in rows) == 26
    assert sum(row["implementation_blocking"] == "true" for row in rows) == 26
    assert all(row["precondition_passed"] == "true" for row in rows)
    assert manifest["precondition_complete_count"] == 25
    assert manifest["precondition_incomplete_count"] == 26


@pytest.mark.parametrize(
    ("subject", "complete"),
    [
        ("current gate explicitly grants no download permission", True),
        ("current no-permission blocking outcome", True),
        ("current-stage constant versus future-context evaluator scope", True),
        ("exact authorization field identity", True),
        ("authoritative permission producer identity", False),
        ("stage_authorization_context routing responsibility", False),
        ("closed authorization value vocabulary", False),
        ("missing authority behavior", False),
        ("invalid authority behavior", False),
        ("contradictory authority behavior", False),
        ("global-stage versus per-candidate scope", True),
        ("candidate_record responsibility", True),
        ("batch_context responsibility", True),
        ("download_result_context responsibility", True),
        ("dependency on ADMIT_001..013", True),
        ("public standalone signature", False),
        ("formal result contract", False),
        ("closed reason vocabulary", False),
        ("multi-invalid precedence", False),
        ("caller obligation to evaluate ADMIT_014 before any download", False),
        ("pure in-memory/no-I/O boundary", True),
    ],
)
def test_canonical_precondition_classification(payloads, subject: str, complete: bool) -> None:
    row = next(
        row
        for row in _rows(payloads[audit.PRECONDITION])
        if row["precondition_subject"] == subject
    )
    assert row["completeness_status"] == ("complete" if complete else "incomplete")
    assert row["implementation_blocking"] == ("false" if complete else "true")


def test_inherited_explicit_context_model_is_selected_without_download_authority(
    manifest, payloads
) -> None:
    assert manifest["admit_014_evaluator_model"] == (
        "future_explicit_authorization_context"
    )
    assert manifest["admit_014_evaluator_model_selected"] is True
    assert manifest["current_stage_constant_guard_rejected"] is True
    assert manifest["authorization_context_item"] == (
        "current_stage_download_authorized"
    )
    assert manifest["authorization_context_scope"] == "stage"
    assert manifest["successor_runtime_envelope_ownership_frozen"] is False
    assert manifest["current_gate_grants_download_permission"] is False
    rows = _rows(payloads[audit.AUTHORIZATION])
    assert [rows[4]["authority_or_envelope"], rows[5]["authority_or_envelope"]] == [
        "current_stage_constant_guard",
        "future_explicit_authorization_context",
    ]
    assert rows[4]["authority_classification"] == "committed alternative rejected"
    assert rows[5]["authority_classification"] == "authoritative inherited selection"


def test_authorization_matrix_exact20_and_fail_closed(payloads, manifest) -> None:
    rows = _rows(payloads[audit.AUTHORIZATION])
    assert tuple(rows[0]) == audit.COLUMNS[audit.AUTHORIZATION]
    assert [row["case_id"] for row in rows] == [
        f"AUTH_{index:03d}" for index in range(1, 21)
    ]
    assert sum(row["completeness_status"] == "complete" for row in rows) == 10
    assert sum(row["completeness_status"] == "incomplete" for row in rows) == 10
    assert all(row["case_passed"] == "true" for row in rows)
    assert manifest["authorization_matrix_row_count"] == 20


def test_current_state_inventory_is_small_authoritative_exact13(payloads) -> None:
    rows = _rows(payloads[audit.CURRENT_STATE])
    assert tuple(rows[0]) == audit.COLUMNS[audit.CURRENT_STATE]
    assert len(rows) == 13
    assert all(row["state_passed"] == "true" for row in rows)
    assert not any("fixture" in row["authority_classification"] for row in rows)
    context = next(
        row
        for row in rows
        if row["state_item"]
        == "Step14AU-A current_stage_download_authorized context"
    )
    assert context["authority_classification"] == "authoritative"
    assert "context_scope=stage" in context["observed_current_state"]


def test_source_boundary_exact15_current_index_and_pinned(snapshot, payloads) -> None:
    assert len(snapshot) == 15
    assert tuple(source.path for source in snapshot) == audit.SOURCE_PATHS
    rows = _rows(payloads[audit.SOURCE_AUDIT])
    assert tuple(rows[0]) == audit.COLUMNS[audit.SOURCE_AUDIT]
    assert [row["source_relative_path"] for row in rows] == [
        path.as_posix() for path in audit.SOURCE_PATHS
    ]
    assert all(row["source_verified"] == "true" for row in rows)
    assert not any(
        row["source_relative_path"].startswith(("data/raw/", "checkpoints/"))
        for row in rows
    )


def test_exact30_issue_continuity_and_exact7_additions(snapshot, payloads) -> None:
    rows = _rows(payloads[audit.ISSUE])
    inherited = audit._csv_rows(snapshot, audit.RUNTIME_ISSUES)
    assert len(rows) == 30
    assert rows[:23] == inherited
    assert [row["issue_id"] for row in rows[23:]] == list(audit.NEW_ISSUES)
    assert all(row["severity"] == "blocking" for row in rows[23:])
    assert all(row["status"] == "open" for row in rows[23:])
    assert all(row["successor_effective_status"] == "open" for row in rows[23:])
    assert all(row["issue_origin"] == audit.STAGE for row in rows[23:])
    assert all("resolution" not in row["successor_transition_action"] for row in rows[23:])
    assert "ADMIT_014_EVALUATOR_SCOPE_UNRESOLVED" not in {
        row["issue_id"] for row in rows
    }
    assert "ADMIT_014_GLOBAL_VS_CANDIDATE_SCOPE_UNRESOLVED" not in {
        row["issue_id"] for row in rows
    }


def test_coverage_issue_still_includes_admit014_and_015(payloads) -> None:
    rows = _rows(payloads[audit.ISSUE])
    coverage = next(
        row
        for row in rows
        if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    )
    assert coverage["affected_rules"] == "ADMIT_014|ADMIT_015"


def test_critical_inherited_open_issues_remain_open(payloads) -> None:
    by_id = {row["issue_id"]: row for row in _rows(payloads[audit.ISSUE])}
    for issue_id in (
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
    ):
        assert by_id[issue_id]["successor_effective_status"] == "open"


def test_readiness_exact_true_and_false_sets(manifest) -> None:
    assert manifest["readiness"] == {
        **{key: True for key in audit.TRUE_READINESS},
        **{key: False for key in audit.FALSE_READINESS},
    }
    assert all(manifest[key] is True for key in audit.TRUE_READINESS)
    assert all(manifest[key] is False for key in audit.FALSE_READINESS)


def test_recommended_next_step_is_contract_design_only(manifest) -> None:
    assert manifest["recommended_next_step"] == (
        "design_covapie_admit_014_download_authorization_contract_v1"
    )
    assert "implementation" not in manifest["recommended_next_step"]


def test_production_has_no_evaluator_result_adapter_registry_or_runtime() -> None:
    tree = ast.parse(
        (
            REPO_ROOT
            / "src/covalent_ext/covapie_bulk_download_admission_admit_014_formal_evaluator_interface_preconditions_audit.py"
        ).read_text(encoding="utf-8")
    )
    names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    assert "evaluate_admit_014" not in names
    assert "Admit014EvaluationResult" not in names
    assert "_evaluate_registered_admit_014" not in names
    assert "evaluate_admission_rule" not in names
    assert "EVALUATOR_REGISTRY" not in {
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }


def test_deterministic_build_and_inode_preserving_noop(tmp_path, payloads) -> None:
    root = tmp_path / "out"
    first = audit.materialize_audit(root)
    hashes = _hashes(root)
    root_inode = root.stat().st_ino
    inodes = {path.name: path.stat().st_ino for path in root.iterdir()}
    second = audit.materialize_audit(root)
    assert first == second
    assert hashes == _hashes(root)
    assert root.stat().st_ino == root_inode
    assert inodes == {path.name: path.stat().st_ino for path in root.iterdir()}
    assert {path.name: path.read_bytes() for path in root.iterdir()} == payloads


def test_existing_mismatch_fails_closed(tmp_path) -> None:
    root = tmp_path / "out"
    audit.materialize_audit(root)
    (root / audit.PRECONDITION).write_bytes(b"tampered\n")
    with pytest.raises(ValueError, match="existing output set mismatch"):
        audit.materialize_audit(root)


def test_materialization_gpfs_einval_fails_closed_without_replace(
    tmp_path, monkeypatch
) -> None:
    root = tmp_path / "out"
    replace_called = False

    def reject(*args):
        raise OSError(errno.EINVAL, "simulated GPFS EINVAL")

    def forbidden_replace(*args):
        nonlocal replace_called
        replace_called = True
        raise AssertionError("replacement fallback called")

    monkeypatch.setattr(audit, "_rename_noreplace", reject)
    monkeypatch.setattr(os, "replace", forbidden_replace)
    with pytest.raises(OSError) as captured:
        audit.materialize_audit(root)
    assert captured.value.errno == errno.EINVAL
    assert replace_called is False
    assert not root.exists()
    assert not list(tmp_path.glob(".*.staging"))


def test_source_content_replacement_is_rejected(monkeypatch) -> None:
    original = audit._pinned_read_relative

    def drift(path: Path) -> bytes:
        data = original(path)
        return data + b"\n" if path == audit.DESIGN_RULES else data

    monkeypatch.setattr(audit, "_pinned_read_relative", drift)
    with pytest.raises(ValueError, match="base/filesystem mismatch"):
        audit.build_frozen_source_snapshot()


@pytest.mark.parametrize("race", ["same_byte_leaf_replacement", "in_place_mutation", "parent_replacement", "root_replacement"])
def test_real_pinned_source_races_are_rejected(tmp_path, monkeypatch, race: str) -> None:
    repo = tmp_path / "repo"
    source = repo / "evidence" / "source.txt"
    source.parent.mkdir(parents=True)
    source.write_text("committed evidence\n", encoding="utf-8")
    monkeypatch.setattr(audit, "REPO_ROOT", repo)
    original_read = audit.os.read
    mutated = False

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal mutated, repo, source
        data = original_read(descriptor, size)
        if data and not mutated:
            mutated = True
            if race == "same_byte_leaf_replacement":
                replacement = source.with_name("replacement.txt")
                replacement.write_bytes(source.read_bytes())
                os.rename(replacement, source)
            elif race == "in_place_mutation":
                with source.open("ab") as handle:
                    handle.write(b"mutation")
            elif race == "parent_replacement":
                old_parent = repo / "evidence-old"
                os.rename(source.parent, old_parent)
                source.parent.mkdir()
                source.write_text("committed evidence\n", encoding="utf-8")
            else:
                old_repo = tmp_path / "repo-old"
                os.rename(repo, old_repo)
                repo.mkdir()
                (repo / "evidence").mkdir()
                source = repo / "evidence" / "source.txt"
                source.write_text("committed evidence\n", encoding="utf-8")
        return data

    monkeypatch.setattr(audit.os, "read", racing_read)
    with pytest.raises(ValueError):
        audit._pinned_read_relative(Path("evidence/source.txt"))


@pytest.mark.parametrize("case", ["untracked", "index_blob", "index_mode", "symlink"])
def test_real_synthetic_git_source_index_and_leaf_drift_rejected(
    tmp_path, monkeypatch, case: str
) -> None:
    repo = tmp_path / case
    repo.mkdir()
    assert _git(repo, "init", "-q").returncode == 0
    path = Path("evidence/source.txt")
    target = repo / path
    target.parent.mkdir(parents=True)
    target.write_text("frozen\n", encoding="utf-8")
    assert _git(repo, "add", "--", path.as_posix()).returncode == 0
    _commit(repo, "frozen source")
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    parent = _git(repo, "show", "-s", "--format=%P", base).stdout.strip()
    tree = _git(repo, "show", "-s", "--format=%T", base).stdout.strip()
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    monkeypatch.setattr(audit, "REPO_ROOT", repo)
    monkeypatch.setattr(audit, "BASE_COMMIT", base)
    monkeypatch.setattr(audit, "BASE_PARENT", parent)
    monkeypatch.setattr(audit, "BASE_TREE", tree)
    monkeypatch.setattr(audit, "BASE_SUBJECT", "frozen source")
    monkeypatch.setattr(audit, "SOURCE_PATHS", (path,))
    monkeypatch.setattr(audit, "SOURCE_SHA256", {path: digest})
    if case == "untracked":
        assert _git(repo, "rm", "--cached", "--", path.as_posix()).returncode == 0
    elif case == "index_blob":
        target.write_text("drift\n", encoding="utf-8")
        assert _git(repo, "add", "--", path.as_posix()).returncode == 0
    elif case == "index_mode":
        target.chmod(0o755)
        assert _git(repo, "add", "--", path.as_posix()).returncode == 0
    else:
        target.unlink()
        target.symlink_to(repo / "baseline-missing")
    with pytest.raises(ValueError):
        audit.build_frozen_source_snapshot()


def test_output_identity_race_is_rejected(tmp_path, payloads, monkeypatch) -> None:
    root = tmp_path / "out"
    root.mkdir()
    for name, data in payloads.items():
        (root / name).write_bytes(data)
    original = audit._identity
    calls = 0

    def drift(item):
        nonlocal calls
        calls += 1
        value = original(item)
        if calls == 5:
            return (value[0], value[1] + 1, *value[2:])
        return value

    monkeypatch.setattr(audit, "_identity", drift)
    with pytest.raises(ValueError):
        audit._read_output_set(root, payloads)


def test_real_early_output_leaf_replacement_is_rejected(
    tmp_path, payloads, monkeypatch
) -> None:
    root = tmp_path / "out"
    root.mkdir()
    for name, data in payloads.items():
        (root / name).write_bytes(data)
    original_read = audit.os.read
    nonempty_reads = 0

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal nonempty_reads
        data = original_read(descriptor, size)
        if data:
            nonempty_reads += 1
            if nonempty_reads == 2:
                first = root / audit.FILES[0]
                replacement = root / "replacement"
                replacement.write_bytes(first.read_bytes())
                os.rename(replacement, first)
        return data

    monkeypatch.setattr(audit.os, "read", racing_read)
    with pytest.raises(ValueError):
        audit._read_output_set(root, payloads)


@pytest.mark.parametrize("race", ["leaf", "root", "parent"])
def test_real_checker_output_root_leaf_and_inventory_races_rejected(
    tmp_path, payloads, monkeypatch, race: str
) -> None:
    container = tmp_path / "container"
    root = container / "out"
    container.mkdir()
    root.mkdir()
    for name, data in payloads.items():
        (root / name).write_bytes(data)
    original_read = checker.os.read
    nonempty_reads = 0

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal nonempty_reads
        data = original_read(descriptor, size)
        if data:
            nonempty_reads += 1
            if nonempty_reads == 2:
                if race == "leaf":
                    first = root / checker.FILES[0]
                    replacement = root / "replacement"
                    replacement.write_bytes(first.read_bytes())
                    os.rename(replacement, first)
                elif race == "root":
                    old_root = container / "out-old"
                    os.rename(root, old_root)
                    root.mkdir()
                    for name in checker.FILES:
                        (root / name).write_bytes((old_root / name).read_bytes())
                else:
                    old_container = tmp_path / "container-old"
                    os.rename(container, old_container)
                    container.mkdir()
                    root.mkdir()
                    for name in checker.FILES:
                        (root / name).write_bytes(
                            (old_container / "out" / name).read_bytes()
                        )
        return data

    monkeypatch.setattr(checker.os, "read", racing_read)
    with pytest.raises(ValueError):
        checker._pinned_outputs(root)


@pytest.mark.parametrize(
    "race",
    [
        "partial_extra",
        "partial_missing",
        "post_traversal_extra",
        "post_traversal_missing",
    ],
)
def test_real_checker_exact6_post_traversal_inventory_races_rejected(
    tmp_path, payloads, monkeypatch, race: str
) -> None:
    root = tmp_path / "out"
    root.mkdir()
    for name, data in payloads.items():
        (root / name).write_bytes(data)

    if race.startswith("partial_"):
        original_read = checker.os.read
        nonempty_reads = 0

        def racing_read(descriptor: int, size: int) -> bytes:
            nonlocal nonempty_reads
            data = original_read(descriptor, size)
            if data:
                nonempty_reads += 1
                if nonempty_reads == 2:
                    if race == "partial_extra":
                        (root / "seventh.csv").write_bytes(b"extra\n")
                    else:
                        (root / checker.FILES[0]).unlink()
            return data

        monkeypatch.setattr(checker.os, "read", racing_read)
    else:
        original_listdir = checker.os.listdir
        listdir_calls = 0

        def racing_listdir(path) -> list[str]:
            nonlocal listdir_calls
            listdir_calls += 1
            if listdir_calls == 2:
                if race == "post_traversal_extra":
                    (root / "seventh.csv").write_bytes(b"extra\n")
                else:
                    (root / checker.FILES[0]).unlink()
            return original_listdir(path)

        monkeypatch.setattr(checker.os, "listdir", racing_listdir)

    with pytest.raises(ValueError, match="inventory drift after traversal"):
        checker._pinned_outputs(root)


@pytest.mark.parametrize(
    "race", ["root_replacement", "leaf_replacement", "extra", "missing"]
)
def test_real_existing_set_output_traversal_races_rejected(
    tmp_path, payloads, monkeypatch, race: str
) -> None:
    root = tmp_path / "out"
    root.mkdir()
    for name, data in payloads.items():
        (root / name).write_bytes(data)
    original_read = audit.os.read
    output_reads = 0
    mutated = False

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal output_reads, mutated
        data = original_read(descriptor, size)
        try:
            descriptor_path = Path(os.readlink(f"/proc/self/fd/{descriptor}"))
        except OSError:
            return data
        if data and descriptor_path.parent == root:
            output_reads += 1
            if output_reads == 2 and not mutated:
                mutated = True
                if race == "root_replacement":
                    original_root = tmp_path / "out-original"
                    os.rename(root, original_root)
                    root.mkdir()
                    for name in audit.FILES:
                        (root / name).write_bytes(
                            (original_root / name).read_bytes()
                        )
                elif race == "leaf_replacement":
                    first = root / audit.FILES[0]
                    replacement = root / "replacement"
                    replacement.write_bytes(first.read_bytes())
                    os.rename(replacement, first)
                elif race == "extra":
                    (root / "seventh.csv").write_bytes(b"extra\n")
                else:
                    (root / audit.FILES[0]).unlink()
        return data

    monkeypatch.setattr(audit.os, "read", racing_read)
    with pytest.raises(ValueError):
        audit.materialize_audit(root)


def test_real_materializer_destination_binding_race_rejected(
    tmp_path, monkeypatch
) -> None:
    root = tmp_path / "out"
    original = audit._rename_noreplace

    def hijack(source: Path, destination: Path, parent_fd: int | None = None) -> None:
        original(source, destination, parent_fd)
        backup = destination.with_name(destination.name + "-original")
        os.rename(destination, backup)
        destination.mkdir()
        for leaf in backup.iterdir():
            (destination / leaf.name).write_bytes(leaf.read_bytes())

    monkeypatch.setattr(audit, "_rename_noreplace", hijack)
    with pytest.raises(ValueError, match="destination name/inode binding"):
        audit.materialize_audit(root)


def test_real_duplicate_top_level_manifest_key_rejected(payloads) -> None:
    text = payloads[audit.MANIFEST].decode()
    tampered = text.replace(
        '{\n  "project": "CovaPIE",',
        '{\n  "project": "tampered",\n  "project": "CovaPIE",',
        1,
    ).encode()
    with pytest.raises(ValueError, match="duplicate JSON key"):
        checker._parse_manifest_exact(tampered)


@pytest.mark.parametrize("case", ["missing", "extra", "reordered"])
def test_real_manifest_top_level_shape_tamper_rejected(payloads, case: str) -> None:
    manifest = json.loads(payloads[audit.MANIFEST])
    if case == "missing":
        manifest.pop("project")
    elif case == "extra":
        manifest["unexpected"] = True
    else:
        project = manifest.pop("project")
        manifest["project"] = project
    tampered = (json.dumps(manifest, indent=2) + "\n").encode()
    with pytest.raises(ValueError, match="missing/extra/reordered"):
        checker._parse_manifest_exact(tampered)


def test_real_manifest_nested_readiness_drift_rejected(payloads) -> None:
    manifest = checker._parse_manifest_exact(payloads[audit.MANIFEST])
    manifest["readiness"]["admit_014_evaluator_scope_resolved"] = False
    with pytest.raises(ValueError, match="readiness drift"):
        checker._validate_manifest_readiness(manifest)


def test_real_synchronized_csv_and_manifest_sha_tamper_rejected(payloads) -> None:
    outputs = dict(payloads)
    outputs[audit.PRECONDITION] += b"tampered\n"
    manifest = json.loads(outputs[audit.MANIFEST])
    manifest["output_sha256"][audit.PRECONDITION] = hashlib.sha256(
        outputs[audit.PRECONDITION]
    ).hexdigest()
    outputs[audit.MANIFEST] = (json.dumps(manifest, indent=2) + "\n").encode()
    with pytest.raises(ValueError, match="frozen output SHA mismatch"):
        checker._validate_output_hashes(outputs)


def test_checker_validates_exact_bytes_and_precommit_lifecycle() -> None:
    result = subprocess.run(
        [sys.executable, str(CHECKER_PATH)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", checker.TEST.as_posix()],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0
    assert f"lifecycle={'post_commit' if tracked else 'pre_commit'}" in result.stdout
    assert f"{audit.STAGE}_passed" in result.stdout


@pytest.mark.parametrize(
    "relative_path",
    [
        "src/covalent_ext/covapie_bulk_download_admission_admit_014_formal_evaluator_interface_preconditions_audit.py",
        "scripts/check_covapie_bulk_download_admission_admit_014_formal_evaluator_interface_preconditions_audit_v1.py",
        "tests/test_covapie_bulk_download_admission_admit_014_formal_evaluator_interface_preconditions_audit_v1.py",
    ],
)
def test_isolated_import_is_silent(tmp_path, relative_path: str) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    command = (
        "import importlib.util;"
        f"s=importlib.util.spec_from_file_location('isolated', {str(REPO_ROOT / relative_path)!r});"
        "m=importlib.util.module_from_spec(s);"
        "import sys;sys.modules['isolated']=m;"
        "s.loader.exec_module(m)"
    )
    result = subprocess.run(
        [sys.executable, "-c", command],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_synthetic_lifecycle_positive_states(tmp_path) -> None:
    pre, pre_base = _make_synthetic_lifecycle_repo(tmp_path / "pre")
    assert checker._lifecycle(pre, pre_base) == "pre_commit"

    descendant, descendant_base = _make_synthetic_lifecycle_repo(
        tmp_path / "descendant", descendant=True
    )
    assert checker._lifecycle(descendant, descendant_base) == "pre_commit"

    post, post_base = _make_synthetic_lifecycle_repo(
        tmp_path / "post", tracked=True
    )
    assert checker._lifecycle(post, post_base) == "post_commit"

    unrelated, unrelated_base = _make_synthetic_lifecycle_repo(
        tmp_path / "unrelated"
    )
    (unrelated / "unrelated-untracked.txt").write_text("u\n", encoding="utf-8")
    (unrelated / "unrelated-staged.txt").write_text("s\n", encoding="utf-8")
    assert _git(unrelated, "add", "--", "unrelated-staged.txt").returncode == 0
    assert checker._lifecycle(unrelated, unrelated_base) == "pre_commit"


def test_tracked_post_commit_ignored_candidate_is_rejected(tmp_path) -> None:
    repo, base = _make_synthetic_lifecycle_repo(
        tmp_path / "tracked-ignored", tracked=True
    )
    ignored_path = checker.EXACT10[0]
    (repo / ".gitignore").write_text(
        ignored_path.as_posix() + "\n", encoding="utf-8"
    )
    ordinary = _git(repo, "check-ignore", "-q", "--", ignored_path.as_posix())
    no_index = _git(
        repo,
        "check-ignore",
        "--no-index",
        "-q",
        "--",
        ignored_path.as_posix(),
    )
    assert ordinary.returncode == 1
    assert no_index.returncode == 0
    with pytest.raises(ValueError, match="ignored candidate"):
        checker._lifecycle(repo, base)


def test_check_ignore_command_error_fails_closed(
    tmp_path, monkeypatch
) -> None:
    repo, base = _make_synthetic_lifecycle_repo(tmp_path / "ignore-error")
    original_git = checker._git

    def failing_git(
        args: list[str], repo_root: Path = checker.REPO_ROOT
    ) -> subprocess.CompletedProcess[str]:
        if args[:3] == ["check-ignore", "--no-index", "-q"]:
            return subprocess.CompletedProcess(args, 128, "", "simulated git error")
        return original_git(args, repo_root)

    monkeypatch.setattr(checker, "_git", failing_git)
    with pytest.raises(ValueError, match="candidate ignore check failed"):
        checker._lifecycle(repo, base)


@pytest.mark.parametrize(
    "case",
    [
        "mixed",
        "stage_path_staged",
        "dirty",
        "missing",
        "ignored",
        "extra_top_level",
        "seventh_exact6",
        "symlink",
        "oversized",
        "base_nonancestor",
        "forbidden_suffix",
    ],
)
def test_synthetic_lifecycle_negative_states(tmp_path, case: str) -> None:
    tracked = case == "dirty"
    repo, base = _make_synthetic_lifecycle_repo(
        tmp_path / case, tracked=tracked
    )
    exact10 = checker.EXACT10
    if case == "mixed":
        first = exact10[0]
        assert _git(repo, "add", "--", first.as_posix()).returncode == 0
        _commit(repo, "one tracked stage file")
    elif case == "stage_path_staged":
        assert _git(repo, "add", "--", exact10[0].as_posix()).returncode == 0
    elif case == "dirty":
        with (repo / exact10[0]).open("a", encoding="utf-8") as handle:
            handle.write("dirty\n")
    elif case == "missing":
        (repo / exact10[0]).unlink()
    elif case == "ignored":
        (repo / ".gitignore").write_text(
            exact10[0].as_posix() + "\n", encoding="utf-8"
        )
    elif case == "extra_top_level":
        extra = (
            repo
            / "docs"
            / "extra_admit_014_formal_evaluator_interface_preconditions_audit.md"
        )
        extra.write_text("extra\n", encoding="utf-8")
    elif case == "seventh_exact6":
        (repo / checker.OUTPUT_ROOT / "seventh.csv").write_text(
            "extra\n", encoding="utf-8"
        )
    elif case == "symlink":
        target = repo / exact10[3]
        target.unlink()
        target.symlink_to(repo / "baseline.txt")
    elif case == "oversized":
        os.truncate(repo / exact10[0], 101 * 1024 * 1024)
    elif case == "base_nonancestor":
        base = "0" * 40
    elif case == "forbidden_suffix":
        exact10 = (exact10[0].with_suffix(".pt"), *exact10[1:])
    with pytest.raises(ValueError):
        checker._lifecycle(repo, base, exact10)


def test_exact10_only_and_no_forbidden_suffix_or_symlink() -> None:
    paths = [REPO_ROOT / path for path in checker.EXACT10]
    assert len(paths) == len(set(paths)) == 10
    forbidden = {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
        ".npz", ".tmp", ".part",
    }
    assert not any(path.suffix in forbidden for path in paths)
    assert not any(path.is_symlink() for path in paths)
    assert not any(path.stat().st_size > 100 * 1024 * 1024 for path in paths)


def test_protected_paths_and_predecessor_runtime_unchanged() -> None:
    changed = subprocess.run(
        ["git", "diff", "--name-only"], cwd=REPO_ROOT, capture_output=True,
        text=True, check=True,
    ).stdout.splitlines()
    protected = (
        "data/raw/", "checkpoints/", "equivariant_diffusion/",
        "lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py",
    )
    assert not any(
        path == item or path.startswith(item)
        for path in changed
        for item in protected
    )
    assert hashlib.sha256(
        (REPO_ROOT / audit.RUNTIME_PRODUCTION).read_bytes()
    ).hexdigest() == audit.PREDECESSOR_PRODUCTION_SHA256
