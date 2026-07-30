#!/usr/bin/env python3
"""Independent checker for the Current11 public submission adapter v1."""

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
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

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


ROOT = Path(__file__).resolve().parents[1]
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
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr.decode("utf-8", "replace"))
    return result.stdout


def assert_base_and_exact4_boundary() -> None:
    identity = git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT,
    ).decode().splitlines()
    assert identity == [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]
    assert hashlib.sha256(
        git("show", f"{BASE_COMMIT}:{DESIGN_PATH}")
    ).hexdigest() == DESIGN_SHA256
    assert hashlib.sha256(
        git("show", f"{BASE_COMMIT}:{DESIGN_MANIFEST_PATH}")
    ).hexdigest() == DESIGN_MANIFEST_SHA256
    head = git("rev-parse", "HEAD").decode().strip()
    if head == BASE_COMMIT:
        assert git("diff", "--name-only") == b""
        assert git("diff", "--cached", "--name-only") == b""
        untracked = tuple(sorted(
            git("ls-files", "--others", "--exclude-standard").decode().splitlines()
        ))
        assert untracked == EXACT4
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
        info = (ROOT / relative).lstat()
        assert stat.S_ISREG(info.st_mode)
        assert stat.S_IMODE(info.st_mode) in {0o644, 0o664}
        assert info.st_size < 5 * 1024 * 1024
        if head != BASE_COMMIT:
            assert git("ls-tree", head, "--", relative).split(None, 1)[0] == b"100644"


def assert_public_signature() -> None:
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
    assert implementation.PUBLIC_FUNCTION_NAME not in vars(design)


def forbidden_call(*args, **kwargs):
    del args, kwargs
    raise AssertionError("forbidden public-adapter side-effect call")


def main() -> None:
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    assert pytest.__version__ == "9.1.0"
    assert rdkit.__version__ == "2022.03.2"
    assert_base_and_exact4_boundary()
    assert_public_signature()

    context, _, items = design._synthetic_payloads(ROOT)
    cases = design._truth_cases(items)
    assert len(cases) == 28
    adapted_count = 0
    invalid_count = 0
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
        assert case.source_payload == snapshot
        if public["adapter_passed"]:
            adapted_count += 1
        else:
            invalid_count += 1
    assert (adapted_count, invalid_count) == (4, 24)

    interface_passed = 0
    for case in cases[:4]:
        adapted = (
            implementation.
            adapt_current11_warhead_boundary_review_submission_bundle_v1(
                source_payload=case.source_payload,
            )
        )
        fresh_context = (
            ingestion_interface.
            build_current11_warhead_boundary_review_ingestion_authority_context_v1(
                ROOT
            )
        )
        response = (
            ingestion_interface.
            evaluate_current11_warhead_boundary_review_ingestion_v1(
                submissions=adapted["adapted_submissions"],
                authority_context=fresh_context,
            )
        )
        ingestion_interface.validate_current11_warhead_boundary_review_ingestion_interface_response_v1(
            response,
            submissions=adapted["adapted_submissions"],
            authority_context=fresh_context,
        )
        assert response["batch_passed"] is True
        interface_passed += 1
    assert interface_passed == 4
    del context

    payload = cases[0].source_payload
    payload_snapshot = bytes(payload)
    status_before = git("status", "--porcelain=v1", "--untracked-files=all")
    head_before = git("rev-parse", "HEAD")
    delegate_calls = 0
    original_delegate = design._reference_adapt_submission_bundle_v1

    def counted_delegate(*, source_payload):
        nonlocal delegate_calls
        delegate_calls += 1
        return original_delegate(source_payload=source_payload)

    forbidden_design = {
        name: mock.patch.object(design, name, forbidden_call)
        for name in (
            "build_result", "materialize", "validate_execution_boundary_v1",
        )
    }
    forbidden_interface = {
        name: mock.patch.object(ingestion_interface, name, forbidden_call)
        for name in (
            "build_current11_warhead_boundary_review_ingestion_authority_context_v1",
            "evaluate_current11_warhead_boundary_review_ingestion_v1",
            "validate_current11_warhead_boundary_review_ingestion_interface_response_v1",
        )
    }
    with ExitStack() as stack:
        stack.enter_context(mock.patch.object(
            design, "_reference_adapt_submission_bundle_v1", counted_delegate,
        ))
        stack.enter_context(mock.patch.object(builtins, "open", forbidden_call))
        stack.enter_context(mock.patch.object(subprocess, "run", forbidden_call))
        for patcher in (
            *forbidden_design.values(),
            *forbidden_interface.values(),
        ):
            stack.enter_context(patcher)
        probe = (
            implementation.
            adapt_current11_warhead_boundary_review_submission_bundle_v1(
                source_payload=payload,
            )
        )
    assert probe["adapter_passed"] is True
    assert delegate_calls == 1
    assert payload == payload_snapshot
    assert git("status", "--porcelain=v1", "--untracked-files=all") == status_before
    assert git("rev-parse", "HEAD") == head_before

    source = inspect.getsource(implementation)
    for forbidden in (
        "Path", "open(", "read_text", "read_bytes", "write_text",
        "write_bytes", "materialize", "build_result",
        "validate_execution_boundary_v1", "ingestion_interface",
    ):
        assert forbidden not in source

    manifest = json.loads(git("show", f"{BASE_COMMIT}:{DESIGN_MANIFEST_PATH}"))
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

    print("checker=passed")
    print("public_adapter_implemented=true")
    print(f"design_delegate_calls={delegate_calls}")
    print(
        f"truth_cases={len(cases)} adapted={adapted_count} "
        f"invalid={invalid_count}"
    )
    print("public_reference_parity=true")
    print(
        f"interface_compatibility_cases={interface_passed} all_passed=true"
    )
    print("input_immutable=true filesystem_effects=0 git_effects=0")
    print("actual_payloads=0 reviews=0 envelopes=0 results=0 authorities=0")
    print("real_submission_adaptation_executed=false")
    print("real_ingestion_execution_ready=false")
    print("canonical_masks=5 modules=0/5 training_ready=false")
    print(
        "recommended_next_step="
        "prepare_covapie_current11_real_human_review_submission_bundle_v1"
    )


if __name__ == "__main__":
    main()
