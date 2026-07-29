#!/usr/bin/env python3
"""Independent checker for the Current11 review-ingestion interface V1."""

from __future__ import annotations

import copy
import csv
import hashlib
import inspect
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import fields, replace
from pathlib import Path

import pytest
import rdkit

from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as iface,
)
from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle


ROOT = Path(__file__).resolve().parents[1]
SHA = re.compile(r"[0-9a-f]{64}")


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")


def git(*arguments: str) -> bytes:
    result = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise AssertionError(
            f"git failure {arguments!r}:"
            + result.stderr.decode("utf-8", "replace")
        )
    return result.stdout


def rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def independent_response_payload(response):
    return {
        "interface_response_version": response["interface_response_version"],
        "authority_context_record_sha256":
            response["authority_context_record_sha256"],
        "batch_passed": response["batch_passed"],
        "ingestion_result_records": [
            {
                field: record[field]
                for field in iface.design.INGESTION_RESULT_FIELDS
            }
            for record in response["ingestion_result_records"]
        ],
        "new_authority_records": [
            {
                field: record[field]
                for field in iface.design.AUTHORITY_RECORD_FIELDS
            }
            for record in response["new_authority_records"]
        ],
    }


def independent_validate_response(
    response, submissions, existing_authorities,
) -> None:
    assert type(response) is dict
    assert tuple(response) == iface.INTERFACE_RESPONSE_FIELDS
    assert response["interface_response_version"] == (
        iface.INTERFACE_RESPONSE_VERSION
    )
    assert type(response["authority_context_record_sha256"]) is str
    assert type(response["batch_passed"]) is bool
    assert type(response["ingestion_result_records"]) is tuple
    assert type(response["new_authority_records"]) is tuple
    assert type(response["interface_response_sha256"]) is str
    assert SHA.fullmatch(response["interface_response_sha256"])
    expected_hash = digest(canonical(independent_response_payload(response)))
    assert response["interface_response_sha256"] == expected_hash
    results = response["ingestion_result_records"]
    authorities = response["new_authority_records"]
    assert len(results) == len(submissions)
    for result, (review, envelope) in zip(results, submissions):
        for result_field, source, input_field in (
            ("sample_index_row_id", review, "sample_index_row_id"),
            ("review_record_sha256", review, "review_record_sha256"),
            (
                "ingestion_envelope_sha256",
                envelope,
                "ingestion_envelope_sha256",
            ),
            ("submission_batch_id", envelope, "submission_batch_id"),
            ("review_decision", review, "review_decision"),
        ):
            value = source.get(input_field) if hasattr(source, "get") else None
            if type(value) is str:
                assert result[result_field] == value
    if response["batch_passed"]:
        assert results
        assert all(
            result["outcome"] == "passed" and result["passed"] is True
            for result in results
        )
    else:
        assert not authorities
        assert all(result["outcome"] != "passed" for result in results)
    for result in results:
        iface.design.validate_ingestion_result(result)
    by_sha = {}
    by_sample = {}
    for authority in authorities:
        iface.design.validate_authority_record(authority)
        authority_sha = authority["authority_record_sha256"]
        sample = authority["sample_index_row_id"]
        assert SHA.fullmatch(authority_sha)
        assert authority_sha not in by_sha and sample not in by_sample
        by_sha[authority_sha] = authority
        by_sample[sample] = authority
    existing_by_sha = {
        authority.get("authority_record_sha256"): authority
        for authority in existing_authorities
        if isinstance(authority, dict)
        and type(authority.get("authority_record_sha256")) is str
    }
    non_replay = 0
    for result in results:
        if result["outcome"] != "passed":
            assert result["authority_disposition"] == ""
            assert result["authority_record_sha256"] == ""
            assert result["consumed_review_record"] is False
            assert result["consumed_ingestion_envelope"] is False
        elif not result["idempotent_replay"]:
            non_replay += 1
            authority = by_sha[result["authority_record_sha256"]]
            assert authority["sample_index_row_id"] == result[
                "sample_index_row_id"
            ]
            assert authority["source_review_record_sha256"] == result[
                "review_record_sha256"
            ]
            assert authority["review_decision"] == result["review_decision"]
            assert result["authority_record_sha256"] not in existing_by_sha
        else:
            assert result["authority_record_sha256"] not in by_sha
            authority = existing_by_sha[result["authority_record_sha256"]]
            iface.design.validate_authority_record(authority)
            assert authority["sample_index_row_id"] == result[
                "sample_index_row_id"
            ]
            assert authority["source_review_record_sha256"] == result[
                "review_record_sha256"
            ]
    assert len(authorities) == non_replay


def runtime_git(repository: Path, *arguments: str, env=None):
    result = subprocess.run(
        ("git", *arguments),
        cwd=repository,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr.decode("utf-8", "replace"))
    return result


def runtime_probe(repository: Path, expected_lifecycle: str) -> None:
    code = r'''
import copy, hashlib, subprocess
from pathlib import Path
from covalent_ext import covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1 as iface
root = Path.cwd()
def status():
    return subprocess.run(("git", "status", "--porcelain=v1", "--untracked-files=all"), cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
def evidence():
    output = root / iface.OUTPUT_ROOT
    return tuple((path.name, hashlib.sha256(path.read_bytes()).hexdigest()) for path in sorted(output.iterdir()) if path.is_file())
before_status = status()
before_evidence = evidence()
context = iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1(root)
iface.design.validate_ingestion_authority_context(context)
built = iface.build_result(root)
assert built.transaction_succeeded and not built.blocking_reasons
assert built.actual_lifecycle == EXPECTED
assert built.design_evidence is not None
case = next(case for case in iface._build_synthetic_truth_cases(built.design_evidence) if case.name == "valid_quarantine")
before_inputs = copy.deepcopy((case.submissions, case.authority_context, case.existing_authorities))
response = iface.evaluate_current11_warhead_boundary_review_ingestion_v1(submissions=case.submissions, authority_context=case.authority_context, existing_authorities=case.existing_authorities)
iface.validate_current11_warhead_boundary_review_ingestion_interface_response_v1(response, submissions=case.submissions, authority_context=case.authority_context, existing_authorities=case.existing_authorities)
assert response["batch_passed"] is True
assert len(response["new_authority_records"]) == 1
assert (case.submissions, case.authority_context, case.existing_authorities) == before_inputs
assert status() == before_status
assert evidence() == before_evidence
'''
    code = "EXPECTED = " + repr(expected_lifecycle) + "\n" + code
    result = subprocess.run(
        (sys.executable, "-B", "-c", code),
        cwd=repository,
        env={
            **os.environ,
            "PYTHONPATH": "src",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr.decode("utf-8", "replace"))
    assert result.stdout == b"" and result.stderr == b""
    records = runtime_git(
        repository, "worktree", "list", "--porcelain",
    ).stdout.decode().splitlines()
    assert sum(line.startswith("worktree ") for line in records) == 1


def descendant_runtime_probe(repository: Path, expected_depth: int) -> None:
    code = r'''
import copy, hashlib, subprocess
from pathlib import Path
from covalent_ext import covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1 as iface
root = Path.cwd()
def status():
    return subprocess.run(("git", "status", "--porcelain=v1", "--untracked-files=all"), cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
def evidence():
    output = root / iface.OUTPUT_ROOT
    return tuple((path.name, hashlib.sha256(path.read_bytes()).hexdigest()) for path in sorted(output.iterdir()) if path.is_file())
before_status = status()
before_evidence = evidence()
assert subprocess.run(("git", "merge-base", "--is-ancestor", iface.BASE_COMMIT, "HEAD"), cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False).returncode == 0
context = iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1(root)
iface.design.validate_ingestion_authority_context(context)
design_evidence = iface._committed_design_interface_evidence(context)
case = next(case for case in iface._build_synthetic_truth_cases(design_evidence) if case.name == "valid_quarantine")
before_inputs = copy.deepcopy((case.submissions, case.authority_context, case.existing_authorities))
response = iface.evaluate_current11_warhead_boundary_review_ingestion_v1(submissions=case.submissions, authority_context=case.authority_context, existing_authorities=case.existing_authorities)
iface.validate_current11_warhead_boundary_review_ingestion_interface_response_v1(response, submissions=case.submissions, authority_context=case.authority_context, existing_authorities=case.existing_authorities)
assert response["batch_passed"] is True
assert len(response["new_authority_records"]) == 1
assert (case.submissions, case.authority_context, case.existing_authorities) == before_inputs
assert status() == before_status
assert evidence() == before_evidence
assert DEPTH in (1, 2)
'''
    result = subprocess.run(
        (
            sys.executable, "-B", "-c",
            "DEPTH = " + repr(expected_depth) + "\n" + code,
        ),
        cwd=repository,
        env={
            **os.environ,
            "PYTHONPATH": "src",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr.decode("utf-8", "replace"))
    assert result.stdout == b"" and result.stderr == b""
    records = runtime_git(
        repository, "worktree", "list", "--porcelain",
    ).stdout.decode().splitlines()
    assert sum(line.startswith("worktree ") for line in records) == 1


def modified_design_descendant_probe(repository: Path) -> None:
    code = r'''
from pathlib import Path
from covalent_ext import covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1 as iface
try:
    iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1(Path.cwd())
except ValueError as error:
    assert str(error) == "INTERFACE_IMPORTED_DESIGN_SOURCE_INTEGRITY_INVALID"
else:
    raise AssertionError("modified design source was accepted")
'''
    result = subprocess.run(
        (sys.executable, "-B", "-c", code),
        cwd=repository,
        env={
            **os.environ,
            "PYTHONPATH": "src",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr.decode("utf-8", "replace"))
    assert result.stdout == b"" and result.stderr == b""


def saved_context_evaluator_integrity_probe(
    repository: Path, commit_env,
) -> None:
    code = r'''
import copy, subprocess
from pathlib import Path
from covalent_ext import covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1 as iface
root = Path.cwd()
def status():
    return subprocess.run(("git", "status", "--porcelain=v1", "--untracked-files=all"), cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
context = iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1(root)
evidence = iface._committed_design_interface_evidence(context)
case = next(case for case in iface._build_synthetic_truth_cases(evidence) if case.name == "valid_quarantine")
saved_inputs = copy.deepcopy((case.submissions, context, ()))
original_ingest = iface.design.ingest_review_batch
ingest_calls = []
def recording_ingest(*args, **kwargs):
    ingest_calls.append((args, kwargs))
    return original_ingest(*args, **kwargs)
iface.design.ingest_review_batch = recording_ingest
design_source = root / iface.DESIGN_PRODUCTION
frozen = design_source.read_bytes()
def blocked_without_ingest(label):
    before_status = status()
    before_calls = len(ingest_calls)
    emitted_authorities = []
    try:
        iface.evaluate_current11_warhead_boundary_review_ingestion_v1(submissions=case.submissions, authority_context=context, existing_authorities=())
    except ValueError as error:
        assert str(error) == "INTERFACE_IMPORTED_DESIGN_SOURCE_INTEGRITY_INVALID", label
    else:
        raise AssertionError(label + " saved-context drift was accepted")
    assert len(ingest_calls) == before_calls
    assert emitted_authorities == []
    assert status() == before_status
design_source.write_bytes(frozen + b"\n# checker uncommitted evaluator integrity probe\n")
blocked_without_ingest("uncommitted")
design_source.write_bytes(frozen)
restored = iface.evaluate_current11_warhead_boundary_review_ingestion_v1(submissions=case.submissions, authority_context=context, existing_authorities=())
assert tuple(restored) == iface.INTERFACE_RESPONSE_FIELDS
assert restored["batch_passed"] is True
assert len(restored["ingestion_result_records"]) == 1
assert len(restored["new_authority_records"]) == 1
iface.design.validate_ingestion_result(restored["ingestion_result_records"][0])
iface.design.validate_authority_record(restored["new_authority_records"][0])
assert restored["interface_response_sha256"] == iface.interface_response_sha256(restored)
design_source.write_bytes(frozen + b"\n# checker committed evaluator integrity probe\n")
subprocess.run(("git", "add", "--", iface.DESIGN_PRODUCTION.as_posix()), cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
subprocess.run(("git", "commit", "-m", "checker committed evaluator integrity probe"), cwd=root, env=COMMIT_ENV, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
blocked_without_ingest("committed")
design_source.write_bytes(frozen)
subprocess.run(("git", "add", "--", iface.DESIGN_PRODUCTION.as_posix()), cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
subprocess.run(("git", "commit", "-m", "checker restores frozen design source"), cwd=root, env=COMMIT_ENV, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
restored_again = iface.evaluate_current11_warhead_boundary_review_ingestion_v1(submissions=case.submissions, authority_context=context, existing_authorities=())
assert restored_again == restored
assert len(restored_again["new_authority_records"]) == 1
assert (case.submissions, context, ()) == saved_inputs
'''
    result = subprocess.run(
        (
            sys.executable, "-B", "-c",
            "COMMIT_ENV = " + repr(commit_env) + "\n" + code,
        ),
        cwd=repository,
        env={
            **os.environ,
            "PYTHONPATH": "src",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr.decode("utf-8", "replace"))
    assert result.stdout == b"" and result.stderr == b""


def exercise_single_worktree_runtime_matrix() -> tuple[str, tuple[int, ...]]:
    with tempfile.TemporaryDirectory(
        prefix="covapie-interface-runtime-matrix-",
    ) as temporary:
        top = Path(temporary)
        remote = top / "remote.git"
        repository = top / "repository"
        runtime_git(top, "init", "--bare", str(remote))
        runtime_git(
            remote,
            "fetch",
            str(ROOT),
            f"{iface.BASE_COMMIT}:refs/heads/main",
        )
        runtime_git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
        runtime_git(top, "clone", str(remote), str(repository))
        for path in iface.EXACT10_PATHS:
            target = repository / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / path, target)
        runtime_probe(repository, "pre_commit")
        runtime_git(
            repository,
            "add",
            "--",
            *(path.as_posix() for path in iface.EXACT10_PATHS),
        )
        commit_env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "CovaPIE Runtime Checker",
            "GIT_AUTHOR_EMAIL": "runtime-checker@example.invalid",
            "GIT_COMMITTER_NAME": "CovaPIE Runtime Checker",
            "GIT_COMMITTER_EMAIL": "runtime-checker@example.invalid",
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+00:00",
        }
        runtime_git(
            repository,
            "commit",
            "-m",
            iface.FORMAL_COMMIT_SUBJECT,
            env=commit_env,
        )
        candidate = runtime_git(
            repository, "rev-parse", "HEAD",
        ).stdout.decode().strip()
        runtime_git(repository, "checkout", "--detach", candidate)
        runtime_probe(repository, "detached_candidate_post_commit")
        runtime_git(repository, "checkout", "-B", "main", candidate)
        runtime_probe(repository, "formal_main_post_commit_unpushed")
        runtime_git(repository, "push", "origin", "main")
        runtime_probe(repository, "formal_main_post_push")
        depths = []
        for depth in (1, 2):
            unrelated = (
                repository / "docs"
                / f"synthetic-downstream-descendant-depth-{depth}.txt"
            )
            unrelated.write_text(
                f"synthetic downstream descendant depth {depth}\n",
                encoding="utf-8",
            )
            runtime_git(
                repository, "add", "--",
                unrelated.relative_to(repository).as_posix(),
            )
            runtime_git(
                repository,
                "commit",
                "-m",
                f"synthetic downstream descendant depth {depth}",
                env=commit_env,
            )
            descendant_runtime_probe(repository, depth)
            depths.append(depth)
        saved_context_evaluator_integrity_probe(repository, commit_env)
        design_source = repository / iface.DESIGN_PRODUCTION
        design_source.write_bytes(
            design_source.read_bytes()
            + b"\n# checker committed design integrity probe\n"
        )
        runtime_git(
            repository, "add", "--", iface.DESIGN_PRODUCTION.as_posix(),
        )
        runtime_git(
            repository,
            "commit",
            "-m",
            "synthetic descendant modifies frozen design source",
            env=commit_env,
        )
        modified_design_descendant_probe(repository)
        return candidate, tuple(depths)


def main() -> int:
    assert sys.implementation.name == "cpython"
    assert sys.version_info[:3] == (3, 10, 4)
    assert pytest.__version__ == "9.1.0"
    assert rdkit.__version__ == "2022.03.2"

    identity = git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", iface.BASE_COMMIT,
    ).decode().splitlines()
    assert identity == [
        iface.BASE_COMMIT,
        iface.BASE_PARENT,
        iface.BASE_TREE,
        iface.BASE_SUBJECT,
    ]
    current = iface.validate_execution_boundary_v1(ROOT)

    source_payloads = {}
    for path, expected in iface.FROZEN_BASE_SHA256.items():
        git("cat-file", "-e", f"{iface.BASE_COMMIT}:{path.as_posix()}")
        payload = git("show", f"{iface.BASE_COMMIT}:{path.as_posix()}")
        assert digest(payload) == expected
        source_payloads[path] = payload
    assert len(source_payloads) == 6
    design_manifest = json.loads(source_payloads[iface.DESIGN_MANIFEST])
    assert design_manifest["transaction_succeeded"] is True
    assert design_manifest[
        "ready_for_review_ingestion_interface_implementation"
    ] is True
    assert design_manifest["ready_for_review_ingestion_execution"] is False
    assert design_manifest["completed_review_record_count"] == 0
    assert design_manifest["ingestion_envelope_count"] == 0
    assert design_manifest["ingestion_result_count"] == 0
    assert design_manifest["authority_record_count"] == 0
    assert design_manifest["ingestion_result_field_count"] == 18
    assert design_manifest["authority_record_field_count"] == 27
    assert design_manifest["canonical_masks"] == list(iface.CANONICAL_MASKS)
    assert design_manifest["ready_for_training"] is False

    builder_signature = inspect.signature(
        iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1
    )
    assert tuple(builder_signature.parameters) == ("repo_root",)
    evaluator_signature = inspect.signature(
        iface.evaluate_current11_warhead_boundary_review_ingestion_v1
    )
    assert tuple(evaluator_signature.parameters) == (
        "submissions", "authority_context", "existing_authorities",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in evaluator_signature.parameters.values()
    )
    assert evaluator_signature.parameters["existing_authorities"].default == ()
    forbidden = {
        "repo_root", "file_path", "csv_path", "json_path", "raw_payload",
        "package_identity_by_sample", "options", "proposals_by_sample",
        "parent_atom_ids_by_ligand", "parent_bonds_by_ligand",
        "valid_sample_ids",
    }
    assert not forbidden & set(evaluator_signature.parameters)

    production_source = inspect.getsource(iface)
    assert "design.build_ingestion_authority_context(" not in production_source
    assert "design.build_result(" not in production_source
    builder_source = inspect.getsource(
        iface._build_committed_design_authority_context_v1
    )
    assert "validate_execution_boundary_v1" not in builder_source
    assert "_validate_public_runtime_repository_v1" in builder_source
    assert "_validate_imported_design_source_integrity_v1" in builder_source
    assert "validate_execution_boundary_v1" in inspect.getsource(
        iface.build_result
    )
    evaluator_source = inspect.getsource(
        iface.evaluate_current11_warhead_boundary_review_ingestion_v1
    )
    assert (
        evaluator_source.index(
            "_validate_public_evaluator_runtime_integrity_v1()"
        )
        < evaluator_source.index("_snapshot_value(submissions)")
        < evaluator_source.index("design.ingest_review_batch(")
    )
    evaluator_integrity_source = inspect.getsource(
        iface._validate_public_evaluator_runtime_integrity_v1
    )
    assert "build_current11" not in evaluator_integrity_source
    assert "build_result" not in evaluator_integrity_source
    assert iface._infer_interface_runtime_repository_root_v1() == ROOT
    assert iface._validate_public_evaluator_runtime_integrity_v1() == ROOT
    iface._validate_public_runtime_repository_v1(ROOT)
    iface._validate_imported_design_source_integrity_v1(ROOT)
    imported_source = Path(iface.design.__file__).resolve()
    expected_source = (ROOT / iface.DESIGN_PRODUCTION).resolve()
    source_info = expected_source.lstat()
    assert imported_source == expected_source
    assert stat.S_ISREG(source_info.st_mode)
    assert not expected_source.is_symlink()
    worktree_design = expected_source.read_bytes()
    head_design = git(
        "show", f"HEAD:{iface.DESIGN_PRODUCTION.as_posix()}",
    )
    assert worktree_design == head_design
    assert digest(worktree_design) == iface.IMPORTED_DESIGN_SOURCE_SHA256
    assert digest(head_design) == iface.IMPORTED_DESIGN_SOURCE_SHA256
    context = (
        iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1(
            ROOT
        )
    )
    iface.design.validate_ingestion_authority_context(context)
    assert [path for path, _ in context.source_payloads] == [
        path.as_posix() for path in iface.design.SOURCE_PATHS
    ]
    for (path_text, payload), path in zip(
        context.source_payloads, iface.design.SOURCE_PATHS,
    ):
        assert path_text == path.as_posix()
        expected_payload = git(
            "show", f"{iface.design.BASE_COMMIT}:{path.as_posix()}",
        )
        assert payload == expected_payload
        assert digest(payload) == iface.design.FROZEN_BASE_SHA256[path]

    built = iface.build_result(ROOT)
    assert built.transaction_succeeded and not built.blocking_reasons
    assert built.design_evidence is not None
    assert len(built.source_rows) == 6
    assert len(built.contract_rows) == 12
    assert len(built.truth_rows) == 18
    assert len(built.readiness_rows) == 11
    assert len(built.failure_rows) == 35
    cases = iface._build_synthetic_truth_cases(built.design_evidence)
    assert [case.name for case in cases] == [
        row["truth_case_name"] for row in built.truth_rows
    ]
    valid_quarantine = next(
        case for case in cases if case.name == "valid_quarantine"
    )
    call_order = []
    original_integrity = (
        iface._validate_public_evaluator_runtime_integrity_v1
    )
    original_ingest = iface.design.ingest_review_batch

    def ordered_integrity():
        call_order.append("integrity")
        return original_integrity()

    def ordered_ingest(*args, **kwargs):
        call_order.append("ingest")
        return original_ingest(*args, **kwargs)

    iface._validate_public_evaluator_runtime_integrity_v1 = ordered_integrity
    iface.design.ingest_review_batch = ordered_ingest
    try:
        ordered_response = (
            iface.evaluate_current11_warhead_boundary_review_ingestion_v1(
                submissions=valid_quarantine.submissions,
                authority_context=valid_quarantine.authority_context,
                existing_authorities=valid_quarantine.existing_authorities,
            )
        )
    finally:
        iface._validate_public_evaluator_runtime_integrity_v1 = (
            original_integrity
        )
        iface.design.ingest_review_batch = original_ingest
    assert ordered_response["batch_passed"] is True
    assert call_order == ["integrity", "ingest"]

    outcome_counts = {"passed": 0, "blocked": 0, "invalid": 0}
    for case in cases:
        before = copy.deepcopy((
            case.submissions, case.authority_context,
            case.existing_authorities,
        ))
        if case.name == "forged_authority_context_invalid":
            batch = iface.design.ingest_review_batch(
                case.submissions,
                authority_context=case.authority_context,
                existing_authorities=case.existing_authorities,
            )
            assert not batch.passed
            assert [row["reason"] for row in batch.result_records] == [
                "INGESTION_AUTHORITY_CONTEXT_INVALID"
            ]
            try:
                iface.evaluate_current11_warhead_boundary_review_ingestion_v1(
                    submissions=case.submissions,
                    authority_context=case.authority_context,
                    existing_authorities=case.existing_authorities,
                )
            except ValueError as error:
                assert str(error) == "INGESTION_AUTHORITY_CONTEXT_INVALID"
            else:
                raise AssertionError("forged context was accepted")
            outcome_counts["invalid"] += 1
            continue
        with tempfile.TemporaryDirectory(
            prefix="covapie-interface-no-write-",
        ) as temporary:
            temporary_path = Path(temporary)
            prior = Path.cwd()
            os.chdir(temporary_path)
            try:
                response = (
                    iface.evaluate_current11_warhead_boundary_review_ingestion_v1(
                        submissions=case.submissions,
                        authority_context=case.authority_context,
                        existing_authorities=case.existing_authorities,
                    )
                )
            finally:
                os.chdir(prior)
            assert tuple(temporary_path.iterdir()) == ()
        independent_validate_response(
            response, case.submissions, case.existing_authorities,
        )
        observed = (
            "passed"
            if response["batch_passed"]
            else "blocked"
            if any(
                row["outcome"] == "blocked"
                for row in response["ingestion_result_records"]
            )
            else "invalid"
        )
        assert observed == case.expected_outcome_class
        assert tuple(
            row["reason"] for row in response["ingestion_result_records"]
        ) == case.expected_reasons
        assert (
            len(response["new_authority_records"])
            == case.expected_new_authority_count
        )
        after = (
            case.submissions, case.authority_context,
            case.existing_authorities,
        )
        assert after == before
        repeated = iface.evaluate_current11_warhead_boundary_review_ingestion_v1(
            submissions=case.submissions,
            authority_context=case.authority_context,
            existing_authorities=case.existing_authorities,
        )
        assert repeated == response
        outcome_counts[observed] += 1
    assert outcome_counts == {"passed": 4, "blocked": 3, "invalid": 11}

    assert [row["contract_id"] for row in built.contract_rows] == [
        f"IFACE_{index:03d}" for index in range(1, 13)
    ]
    assert all(row["verified"] for row in built.contract_rows)
    assert all(row["verified"] for row in built.truth_rows)
    assert all(row["filesystem_write_count"] == 0 for row in built.truth_rows)
    for row in built.readiness_rows:
        assert row["review_package_available"] is True
        assert row["blank_review_template_available"] is True
        assert row["interface_implementation_available"] is True
        assert row["immutable_authority_context_available"] is True
        assert row["interface_synthetic_validation_passed"] is True
        assert row["completed_review_record_available"] is False
        assert row["human_provenance_envelope_available"] is False
        assert row["ready_for_real_ingestion_execution"] is False
        assert row["authority_record_available"] is False
        assert row["ready_for_candidate_warhead_smarts_materialization"] is False
        assert row["ready_for_role_proposal_generation"] is False
        assert row["ready_for_mask_materialization"] is False
        assert row["ready_for_model_integration"] is False
        assert row["ready_for_training"] is False

    assert len(fields(iface.InterfaceScenario)) == 35
    baseline = iface.InterfaceScenario()
    signatures = []
    for (name, field, value, expected), row in zip(
        iface.FAILURE_MUTATIONS, built.failure_rows,
    ):
        assert type(value) is type(getattr(baseline, field))
        assert value != getattr(baseline, field)
        mutated = replace(baseline, **{field: value})
        assert iface.observe_failure_scenario(mutated) == (expected,)
        assert iface.transaction_tables(mutated) == ((), (), ())
        assert row["failure_case_name"] == name
        assert row["expected_reason_verified"] is True
        assert row["fails_closed"] is True
        assert row["contract_row_count"] == 0
        assert row["truth_row_count"] == 0
        assert row["current11_readiness_row_count"] == 0
        assert row["actual_completed_review_count"] == 0
        assert row["actual_ingestion_envelope_count"] == 0
        assert row["actual_ingestion_result_count"] == 0
        assert row["actual_authority_record_count"] == 0
        assert row["training_ready"] is False
        assert row["verified"] is True
        signatures.append(row["mutation_signature"])
    assert len(signatures) == len(set(signatures)) == 35

    expected_payloads = iface.build_evidence_payloads(ROOT)
    assert tuple(expected_payloads) == iface.OUTPUT_FILES
    for name, payload in expected_payloads.items():
        assert (ROOT / iface.OUTPUT_ROOT / name).read_bytes() == payload
    assert len(rows(expected_payloads[iface.SOURCE_FILE])) == 6
    assert len(rows(expected_payloads[iface.CONTRACT_FILE])) == 12
    assert len(rows(expected_payloads[iface.TRUTH_FILE])) == 18
    assert len(rows(expected_payloads[iface.READINESS_FILE])) == 11
    assert len(rows(expected_payloads[iface.FAILURE_FILE])) == 35
    manifest = json.loads(expected_payloads[iface.MANIFEST_FILE])
    assert manifest["transaction_succeeded"] is True
    assert manifest["interface_implementation_completed"] is True
    assert manifest["ready_for_synthetic_interface_evaluation"] is True
    assert manifest["ready_for_real_review_ingestion_execution"] is False
    assert manifest["completed_review_record_count"] == 0
    assert manifest["human_provenance_envelope_count"] == 0
    assert manifest["actual_ingestion_result_count"] == 0
    assert manifest["actual_authority_record_count"] == 0
    assert manifest["candidate_warhead_smarts_materialized_count"] == 0
    assert manifest["approved_reaction_family_available_count"] == 0
    assert manifest["approved_warhead_rule_available_count"] == 0
    assert manifest["approved_warhead_smarts_count"] == 0
    assert manifest["human_gold_review_completed_count"] == 0
    assert manifest["training_label_approved_count"] == 0
    assert manifest["canonical_masks"] == list(iface.CANONICAL_MASKS)
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["ready_for_training"] is False
    assert manifest["supported_runtime_lifecycles"] == list(
        iface.SUPPORTED_RUNTIME_LIFECYCLES
    )
    assert manifest["formal_successor_runtime_compatible"] is True
    assert manifest["runtime_lifecycle_count"] == 4
    assert manifest["runtime_lifecycles_all_verified"] is True
    assert manifest["public_runtime_compatibility_scope"] == (
        iface.PUBLIC_RUNTIME_COMPATIBILITY_SCOPE
    )
    assert manifest["public_runtime_required_base_commit"] == iface.BASE_COMMIT
    assert manifest["artifact_build_lifecycle_strict"] is True
    assert manifest["public_runtime_requires_exact_interface_lifecycle"] is False
    assert manifest["downstream_descendant_runtime_compatible"] is True
    assert manifest["downstream_descendant_depths_verified"] == [1, 2]
    assert manifest["imported_design_source_integrity_required"] is True
    assert manifest["imported_design_source_sha256"] == (
        iface.IMPORTED_DESIGN_SOURCE_SHA256
    )
    assert manifest["working_tree_design_source_must_match_HEAD"] is True
    assert (
        manifest["downstream_callers_must_not_call_interface_build_result"]
        is True
    )
    assert manifest["public_evaluator_runtime_repository_guard_required"] is True
    assert manifest["public_evaluator_design_source_integrity_required"] is True
    assert (
        manifest[
            "public_evaluator_repository_root_inferred_from_interface_module"
        ]
        is True
    )
    assert (
        manifest[
            "public_evaluator_calls_design_ingest_only_after_integrity_validation"
        ]
        is True
    )
    assert manifest["saved_context_cannot_bypass_design_source_integrity"] is True
    assert manifest["business_payload_in_memory_only"] is True
    assert manifest["public_runtime_integrity_checks_read_only"] is True
    assert manifest["filesystem_persistence_allowed"] is False
    assert manifest["separate_design_base_worktree_required"] is False
    assert (
        manifest["authority_context_built_from_design_base_git_objects"]
        is True
    )
    assert manifest["design_lifecycle_bound_builder_called"] is False
    assert manifest["design_lifecycle_bound_build_result_called"] is False
    assert iface.MANIFEST_FILE not in manifest["output_sha256"]
    for name, expected in manifest["output_sha256"].items():
        assert digest((ROOT / iface.OUTPUT_ROOT / name).read_bytes()) == expected
    assert {
        path.name for path in (ROOT / iface.OUTPUT_ROOT).iterdir()
    } == set(iface.OUTPUT_FILES)

    runtime_candidate, descendant_depths = (
        exercise_single_worktree_runtime_matrix()
    )
    assert re.fullmatch(r"[0-9a-f]{40}", runtime_candidate)
    assert descendant_depths == (1, 2)

    with tempfile.TemporaryDirectory(
        prefix="covapie-interface-checker-",
    ) as temporary:
        workspace = Path(temporary) / "workspace"
        workspace.mkdir()
        report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
            ROOT,
            workspace,
            base_commit=iface.BASE_COMMIT,
            formal_commit_subject=iface.FORMAL_COMMIT_SUBJECT,
            exact_paths=iface.EXACT10_PATHS,
        )
        assert report.cleanup_verified and report.exact_path_count == 10
        assert tuple(
            state.lifecycle
            for state in (
                report.pre_commit,
                report.detached_candidate_post_commit,
                report.formal_main_post_commit_unpushed,
                report.formal_main_post_push,
            )
        ) == lifecycle.LIFECYCLES
        candidate = report.candidate_commit

    print("checker=passed")
    print("sources=6 contracts=12 truth_cases=18 samples=11")
    print("truth_outcomes=passed:4,blocked:3,invalid:11")
    print("response_fields=6 response_hash=true response_invariants=true")
    print("artifact_runtime_lifecycles=4 artifact_runtime_all_verified=true")
    print(
        "descendant_runtime_depths=1,2 "
        "descendant_runtime_all_verified=true"
    )
    print("builder_design_source_integrity=true")
    print("evaluator_design_source_integrity=true")
    print("saved_context_drift_bypass=false")
    print("separate_base_worktree=false")
    print("actual_reviews=0 envelopes=0 results=0 authorities=0")
    print("interface_implemented=true execution_ready=false")
    print("failure_mutations=35 all_fail_closed=true")
    print(f"current_lifecycle={current}")
    print(
        "hermetic_lifecycle="
        "pre_commit,detached_candidate_post_commit,"
        "formal_main_post_commit_unpushed,formal_main_post_push"
    )
    print(f"candidate_commit={candidate}")
    print(
        "recommended_next_step="
        "design_covapie_current11_warhead_atom_set_and_attachment_"
        "boundary_review_submission_adapter_v1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
