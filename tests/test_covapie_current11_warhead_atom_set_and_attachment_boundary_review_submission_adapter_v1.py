"""Tests for the Current11 public review-submission adapter v1."""

from __future__ import annotations

import builtins
import copy
import hashlib
import inspect
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest
import rdkit

from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as ingestion_interface,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_submission_adapter_design_v1
    as design,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_submission_adapter_v1
    as implementation,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "84375060a0ddd9b281d17719331a316716bffd85"
BASE_PARENT = "9cd905d9ecf8e73fe16e947e8b881a520b31e2b4"
BASE_TREE = "e0217e89f5623013b4d3e33c4d0d64291fb5dd45"
BASE_SUBJECT = (
    "add CovaPIE Current11 warhead atom set and attachment boundary review "
    "submission adapter design v1"
)
CANDIDATE_SUBJECT = (
    "add CovaPIE Current11 warhead atom set and attachment boundary review "
    "submission adapter v1"
)
DESIGN_PATH = (
    "src/covalent_ext/"
    "covapie_current11_warhead_atom_set_and_attachment_boundary_review_"
    "submission_adapter_design_v1.py"
)
DESIGN_SHA256 = (
    "55080fef4932d13be5fa063d3545c1120cb1e2bcaba20ab3cbe04a50b8838a58"
)
DESIGN_MANIFEST_PATH = (
    "data/derived/covalent_small/"
    "covapie_current11_warhead_atom_set_and_attachment_boundary_review_"
    "submission_adapter_design_v1/"
    "covapie_current11_warhead_boundary_review_submission_adapter_design_"
    "manifest.json"
)
DESIGN_MANIFEST_SHA256 = (
    "40dfd4cedbfc35081b6b47ada2bc9a504bd5dea4c542f2efda5e698309777ec2"
)
EXACT4 = (
    "docs/covapie_current11_warhead_atom_set_and_attachment_boundary_review_"
    "submission_adapter_v1_summary.md",
    "scripts/check_covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_submission_adapter_v1.py",
    "src/covalent_ext/covapie_current11_warhead_atom_set_and_attachment_"
    "boundary_review_submission_adapter_v1.py",
    "tests/test_covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_submission_adapter_v1.py",
)


def git(*arguments: str) -> bytes:
    result = subprocess.run(
        ("git", *arguments),
        cwd=REPO_ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    return result.stdout


def committed(path: str) -> bytes:
    return git("show", f"{BASE_COMMIT}:{path}")


def test_fixed_runtime_versions() -> None:
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    assert pytest.__version__ == "9.1.0"
    assert rdkit.__version__ == "2022.03.2"


def test_formal_base_and_design_authority_sha256() -> None:
    identity = git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT,
    ).decode().splitlines()
    assert identity == [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]
    assert hashlib.sha256(committed(DESIGN_PATH)).hexdigest() == DESIGN_SHA256
    assert (
        hashlib.sha256(committed(DESIGN_MANIFEST_PATH)).hexdigest()
        == DESIGN_MANIFEST_SHA256
    )
    assert implementation.DESIGN_COMMIT == BASE_COMMIT
    assert implementation.DESIGN_PRODUCTION_SHA256 == DESIGN_SHA256


def test_exact4_path_boundary_modes_and_sizes() -> None:
    head = git("rev-parse", "HEAD").decode().strip()
    if head == BASE_COMMIT:
        assert git("diff", "--name-only") == b""
        assert git("diff", "--cached", "--name-only") == b""
        ordinary_untracked = tuple(sorted(
            git("ls-files", "--others", "--exclude-standard").decode().splitlines()
        ))
        assert ordinary_untracked == EXACT4
    else:
        raw = git("cat-file", "commit", head)
        headers, separator, message = raw.partition(b"\n\n")
        assert separator
        parents = tuple(
            line[7:].decode()
            for line in headers.splitlines()
            if line.startswith(b"parent ")
        )
        assert parents == (BASE_COMMIT,)
        assert message == (CANDIDATE_SUBJECT + "\n").encode()
        changed = tuple(sorted(
            git("diff-tree", "--no-commit-id", "--name-only", "-r", head)
            .decode().splitlines()
        ))
        assert changed == EXACT4
        assert git("status", "--porcelain=v1", "--untracked-files=all") == b""
    for relative in EXACT4:
        path = REPO_ROOT / relative
        info = path.lstat()
        assert stat.S_ISREG(info.st_mode)
        assert not path.is_symlink()
        assert stat.S_IMODE(info.st_mode) in {0o644, 0o664}
        assert info.st_size < 5 * 1024 * 1024
        if head != BASE_COMMIT:
            assert git("ls-tree", head, "--", relative).split(None, 1)[0] == b"100644"


def test_public_api_signature_and_exposure() -> None:
    function = (
        implementation.
        adapt_current11_warhead_boundary_review_submission_bundle_v1
    )
    signature = inspect.signature(function)
    assert tuple(signature.parameters) == ("source_payload",)
    parameter = signature.parameters["source_payload"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty
    assert parameter.annotation in {bytes, "bytes"}
    assert signature.return_annotation in {dict[str, object], "dict[str, Any]"}
    assert implementation.__all__ == (
        "adapt_current11_warhead_boundary_review_submission_bundle_v1",
    )
    assert implementation.PUBLIC_FUNCTION_NAME in vars(implementation)
    assert implementation.PUBLIC_FUNCTION_NAME not in vars(design)


def test_all_exact28_public_reference_parity_and_statistics() -> None:
    _, _, items = design._synthetic_payloads(REPO_ROOT)
    cases = design._truth_cases(items)
    assert len(cases) == 28
    public_responses = []
    for case in cases:
        snapshot = copy.deepcopy(case.source_payload)
        public = (
            implementation.
            adapt_current11_warhead_boundary_review_submission_bundle_v1(
                source_payload=case.source_payload,
            )
        )
        reference = design._reference_adapt_submission_bundle_v1(
            source_payload=case.source_payload,
        )
        assert public == reference
        assert tuple(public) == design.ADAPTER_RESPONSE_FIELDS
        assert public["reason"] == case.expected_reason
        assert case.source_payload == snapshot
        public_responses.append(public)
    assert sum(row["adapter_passed"] for row in public_responses) == 4
    assert sum(not row["adapter_passed"] for row in public_responses) == 24


def test_four_success_cases_pass_committed_ingestion_interface() -> None:
    _, _, items = design._synthetic_payloads(REPO_ROOT)
    cases = design._truth_cases(items)[:4]
    assert [case.name for case in cases] == [
        "valid_select",
        "valid_revise",
        "valid_quarantine",
        "valid_partial_two_sample_bundle",
    ]
    for case in cases:
        adapted = (
            implementation.
            adapt_current11_warhead_boundary_review_submission_bundle_v1(
                source_payload=case.source_payload,
            )
        )
        context = (
            ingestion_interface.
            build_current11_warhead_boundary_review_ingestion_authority_context_v1(
                REPO_ROOT
            )
        )
        response = (
            ingestion_interface.
            evaluate_current11_warhead_boundary_review_ingestion_v1(
                submissions=adapted["adapted_submissions"],
                authority_context=context,
            )
        )
        ingestion_interface.validate_current11_warhead_boundary_review_ingestion_interface_response_v1(
            response,
            submissions=adapted["adapted_submissions"],
            authority_context=context,
        )
        assert response["batch_passed"] is True


@pytest.mark.parametrize("value", ("{}", {}, bytearray(b"{}"), memoryview(b"{}")))
def test_non_bytes_follow_design_failure_contract(value: object) -> None:
    public = (
        implementation.
        adapt_current11_warhead_boundary_review_submission_bundle_v1(
            source_payload=value,
        )
    )
    reference = design._reference_adapt_submission_bundle_v1(
        source_payload=value,
    )
    assert public == reference
    assert public["adapter_passed"] is False
    assert public["reason"] == "SOURCE_PAYLOAD_EXACT_TYPE_INVALID"


def test_public_delegate_exactly_once_and_does_not_revalidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, items = design._synthetic_payloads(REPO_ROOT)
    payload = design._truth_cases(items)[0].source_payload
    calls = {"delegate": 0, "validator": 0}
    original_delegate = design._reference_adapt_submission_bundle_v1
    original_validator = design._validate_reference_response

    def counted_delegate(*, source_payload):
        calls["delegate"] += 1
        return original_delegate(source_payload=source_payload)

    def counted_validator(response, *, source_payload):
        calls["validator"] += 1
        return original_validator(response, source_payload=source_payload)

    monkeypatch.setattr(
        design, "_reference_adapt_submission_bundle_v1", counted_delegate,
    )
    monkeypatch.setattr(design, "_validate_reference_response", counted_validator)
    implementation.adapt_current11_warhead_boundary_review_submission_bundle_v1(
        source_payload=payload,
    )
    assert calls == {"delegate": 1, "validator": 1}


def test_no_filesystem_git_or_lifecycle_calls_and_no_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, items = design._synthetic_payloads(REPO_ROOT)
    payload = design._truth_cases(items)[0].source_payload
    status_before = git("status", "--porcelain=v1", "--untracked-files=all")
    head_before = git("rev-parse", "HEAD")
    source = inspect.getsource(implementation)
    for forbidden in (
        "Path", "open(", "read_text", "read_bytes", "write_text",
        "write_bytes", "materialize", "build_result",
        "validate_execution_boundary_v1", "ingestion_interface",
    ):
        assert forbidden not in source

    def forbidden_call(*args, **kwargs):
        del args, kwargs
        raise AssertionError("forbidden side-effect call")

    monkeypatch.setattr(builtins, "open", forbidden_call)
    monkeypatch.setattr(subprocess, "run", forbidden_call)
    for name in ("build_result", "materialize", "validate_execution_boundary_v1"):
        monkeypatch.setattr(design, name, forbidden_call)
    for name in (
        "build_current11_warhead_boundary_review_ingestion_authority_context_v1",
        "evaluate_current11_warhead_boundary_review_ingestion_v1",
        "validate_current11_warhead_boundary_review_ingestion_interface_response_v1",
    ):
        monkeypatch.setattr(ingestion_interface, name, forbidden_call)
    snapshot = bytes(payload)
    response = (
        implementation.
        adapt_current11_warhead_boundary_review_submission_bundle_v1(
            source_payload=payload,
        )
    )
    assert response["adapter_passed"] is True
    assert payload == snapshot
    monkeypatch.undo()
    assert git("status", "--porcelain=v1", "--untracked-files=all") == status_before
    assert git("rev-parse", "HEAD") == head_before


def test_isolated_production_and_checker_imports_are_silent() -> None:
    code = (
        "import importlib.util, pathlib;"
        "import covalent_ext."
        "covapie_current11_warhead_atom_set_and_attachment_boundary_review_"
        "submission_adapter_v1;"
        "p=pathlib.Path('scripts/check_covapie_current11_warhead_atom_set_and_"
        "attachment_boundary_review_submission_adapter_v1.py');"
        "s=importlib.util.spec_from_file_location('checker_import_probe',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)"
    )
    result = subprocess.run(
        (sys.executable, "-B", "-c", code),
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": "src",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == b""
    assert result.stderr == b""


def test_actual_lifecycle_counts_masks_and_training_state_unchanged() -> None:
    manifest = json.loads(committed(DESIGN_MANIFEST_PATH))
    for field in (
        "actual_submission_payload_count",
        "completed_review_record_count",
        "human_provenance_envelope_count",
        "adapted_submission_count",
        "actual_ingestion_result_count",
        "actual_authority_record_count",
    ):
        assert manifest[field] == 0
    assert tuple(manifest["canonical_masks"]) == design.CANONICAL_MASKS
    assert len(design.CANONICAL_MASKS) == 5
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["ready_for_training"] is False
    assert manifest["formal_training_prerequisite"] == "feature-semantics audit"
    assert manifest["Step12D_scope"] == "smoke legality check only"
