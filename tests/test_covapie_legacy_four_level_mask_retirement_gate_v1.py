from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import covapie_legacy_four_level_mask_retirement_gate_v1 as gate


EXPECTED_R2_SCOPE = {
    "src/covalent_ext/masking.py",
    "src/covalent_ext/schema.py",
    "src/covalent_ext/dataset.py",
    "scripts/check_covalent_masking.py",
    "scripts/check_covalent_dataset.py",
    "scripts/check_covalent_real_small.py",
    "tests/test_covalent_masking.py",
    "tests/test_b3_scaffold_only_mask_implementation_v0.py",
    "tests/test_covalent_real_small_builder.py",
    "tests/test_covalent_dataset.py",
}

LIFECYCLE_RESPONSE_CONTRACTS: dict[str, dict[str, object]] = {
    "r3_precommit_candidate": {
        "R3_gate_committed": False,
        "R3_gate_published": False,
        "ready_for_R3_commit_review": True,
        "legacy_four_level_full_runtime_retired": False,
        "ready_for_repository_cli_forwarding_C1": False,
        "recommended_next_step": (
            "commit_and_push_covapie_legacy_four_level_mask_retirement_gate_v1"
        ),
    },
    "r3_committed_unpushed": {
        "R3_gate_committed": True,
        "R3_gate_published": False,
        "ready_for_R3_commit_review": False,
        "legacy_four_level_full_runtime_retired": True,
        "ready_for_repository_cli_forwarding_C1": False,
        "recommended_next_step": (
            "push_covapie_legacy_four_level_mask_retirement_gate_v1"
        ),
    },
    "r3_published_successor": {
        "R3_gate_committed": True,
        "R3_gate_published": True,
        "ready_for_R3_commit_review": False,
        "legacy_four_level_full_runtime_retired": True,
        "ready_for_repository_cli_forwarding_C1": True,
        "recommended_next_step": "begin_repository_cli_forwarding_C1",
    },
}


@pytest.fixture(scope="session")
def responses() -> tuple[dict[str, object], dict[str, object], str, str]:
    before = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
    )
    first = gate.evaluate_covapie_legacy_four_level_mask_retirement_gate_v1(
        repo_root=ROOT
    )
    second = gate.evaluate_covapie_legacy_four_level_mask_retirement_gate_v1(
        repo_root=ROOT
    )
    after = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
    )
    return first, second, before, after


def _walk_values(value: object):
    yield value
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk_values(key)
            yield from _walk_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_values(item)


def _precommit_facts() -> dict[str, object]:
    return {
        "head": gate._R2_COMMIT,
        "origin_main": gate._R2_COMMIT,
        "ordinary_untracked_paths": list(gate._R3_PATHS),
        "tracked_gate_paths": [],
        "tracked_changes": [],
        "staged_changes": [],
        "regular_gate_paths": True,
        "r3_candidates": [],
    }


def _r3_candidate(*, published: bool) -> dict[str, object]:
    return {
        "commit": "a" * 40,
        "subject": gate._R3_SUBJECT,
        "parents": [gate._R2_COMMIT],
        "paths": list(gate._R3_PATHS),
        "head_ancestor": True,
        "origin_main_ancestor": published,
        "body_empty": True,
        "gate_commit_modes_bound": True,
        "gate_commit_blobs_bound": True,
        "gate_live_bytes_match_commit": True,
    }


def _load_checker_module():
    path = ROOT / "scripts/check_covapie_legacy_four_level_mask_retirement_gate_v1.py"
    spec = importlib.util.spec_from_file_location("covapie_r3_checker_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _response_with_lifecycle(
    response: dict[str, object],
    *,
    profile: str,
    commit: str | None,
) -> dict[str, object]:
    """Copy an Exact47 response, set one lifecycle, and recompute its digest."""

    if profile not in LIFECYCLE_RESPONSE_CONTRACTS:
        raise ValueError("unknown lifecycle profile")
    if profile == "r3_precommit_candidate":
        if commit is not None:
            raise ValueError("precommit lifecycle cannot have a commit")
    elif type(commit) is not str or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ValueError("committed lifecycle requires a lowercase commit hash")
    result = dict(response)
    result.update(LIFECYCLE_RESPONSE_CONTRACTS[profile])
    result["R3_gate_lifecycle_profile"] = profile
    result["R3_gate_commit"] = commit
    unsigned = {
        field: result[field]
        for field in gate.LEGACY_FOUR_LEVEL_MASK_RETIREMENT_GATE_RESPONSE_FIELDS
        if field != "legacy_four_level_mask_retirement_gate_response_sha256"
    }
    result["legacy_four_level_mask_retirement_gate_response_sha256"] = hashlib.sha256(
        gate._canonical_json_bytes(unsigned)
    ).hexdigest()
    return result


def test_public_api_all_signature_and_keyword_only() -> None:
    assert gate.__all__ == (
        "evaluate_covapie_legacy_four_level_mask_retirement_gate_v1",
    )
    function = gate.evaluate_covapie_legacy_four_level_mask_retirement_gate_v1
    signature = inspect.signature(function)
    assert list(signature.parameters) == ["repo_root"]
    assert signature.parameters["repo_root"].kind is inspect.Parameter.KEYWORD_ONLY
    with pytest.raises(TypeError):
        function(ROOT)  # type: ignore[misc]


def test_import_is_silent_and_has_no_output_side_effects() -> None:
    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": f"{ROOT}:{SRC}:{ROOT / 'scripts'}",
    }
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "import covalent_ext.covapie_legacy_four_level_mask_retirement_gate_v1",
        ],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_public_evaluation_is_deterministic_and_does_not_change_git_status(
    responses,
) -> None:
    first, second, before, after = responses
    assert first == second
    assert before == after


def test_exact47_field_order_and_canonical_digest(responses) -> None:
    response = responses[0]
    assert len(response) == 47
    assert tuple(response) == gate.LEGACY_FOUR_LEVEL_MASK_RETIREMENT_GATE_RESPONSE_FIELDS
    unsigned = {
        field: response[field]
        for field in gate.LEGACY_FOUR_LEVEL_MASK_RETIREMENT_GATE_RESPONSE_FIELDS
        if field != "legacy_four_level_mask_retirement_gate_response_sha256"
    }
    expected = hashlib.sha256(gate._canonical_json_bytes(unsigned)).hexdigest()
    assert response["legacy_four_level_mask_retirement_gate_response_sha256"] == expected
    if response["R3_gate_lifecycle_profile"] == "r3_precommit_candidate":
        assert expected == "0b960386ef57f4f1363f56dc0cb1823d6c5191c62dfa159eae1c76b760e80496"
    assert gate._validate_response(response)


def test_response_is_json_safe_and_contains_no_path_or_tensor(responses) -> None:
    response = responses[0]
    json.dumps(response, allow_nan=False, sort_keys=True)
    assert not any(isinstance(value, Path) for value in _walk_values(response))
    assert not any(type(value).__module__.startswith("torch") for value in _walk_values(response))


def test_r2_metadata_scope_modes_and_blob_sha_are_exact(responses) -> None:
    response = responses[0]
    assert response["source_R2_commit"] == gate._R2_COMMIT
    assert response["source_R2_parent"] == gate._R2_PARENT
    assert response["source_R2_tree"] == gate._R2_TREE
    assert response["source_R2_subject"] == gate._R2_SUBJECT
    assert set(response["source_R2_scope"]) == EXPECTED_R2_SCOPE
    assert len(response["source_R2_scope"]) == 10
    assert response["source_R2_file_sha256s"] == gate._R2_FILES
    for path, expected_sha in gate._R2_FILES.items():
        row = subprocess.check_output(
            ["git", "ls-tree", gate._R2_COMMIT, "--", path], cwd=ROOT, text=True
        )
        assert row.startswith("100644 blob ")
        payload = subprocess.check_output(["git", "show", f"{gate._R2_COMMIT}:{path}"], cwd=ROOT)
        assert hashlib.sha256(payload).hexdigest() == expected_sha


@pytest.mark.parametrize("path", ["/tmp/x", "../x", "a/../b", "./x", "a//b", "x\x00y"])
def test_snapshot_helper_rejects_noncanonical_paths(path: str) -> None:
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._git_snapshot_blob_bytes(
            ROOT, commit=gate._R2_COMMIT, relative_path=path
        )


def test_snapshot_helper_rejects_invalid_commit_missing_nonblob_oversize_and_sha_drift() -> None:
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._git_snapshot_blob_bytes(ROOT, commit="bad", relative_path="README.md")
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._git_snapshot_blob_bytes(
            ROOT, commit=gate._R2_COMMIT, relative_path="does/not/exist"
        )
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._git_snapshot_blob_bytes(
            ROOT, commit=gate._R2_COMMIT, relative_path="src/covalent_ext"
        )
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._git_snapshot_blob_bytes(
            ROOT, commit=gate._R2_COMMIT, relative_path="README.md", maximum=2
        )
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._git_snapshot_blob_bytes(
            ROOT,
            commit=gate._R2_COMMIT,
            relative_path="README.md",
            expected_sha256="0" * 64,
        )


def test_snapshot_helpers_reject_empty_and_duplicate_paths(monkeypatch) -> None:
    def fake_git(_root, arguments):
        if arguments[:2] == ["cat-file", "-t"]:
            return b"blob\n"
        if arguments[:2] == ["cat-file", "-s"]:
            return b"0\n"
        raise AssertionError(arguments)

    monkeypatch.setattr(gate, "_git_bytes", fake_git)
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._git_snapshot_blob_bytes(
            ROOT, commit=gate._R2_COMMIT, relative_path="README.md"
        )
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._git_snapshot_blob_batch(
            ROOT,
            commit=gate._R2_COMMIT,
            relative_paths=["README.md", "README.md"],
        )


def test_scan_is_full_frozen_r2_tree_with_python_and_notebook_ast(responses) -> None:
    response = responses[0]
    assert response["scan_subject_commit"] == gate._R2_COMMIT
    assert response["scan_evidence_mode"] == "frozen_R2_commit_snapshot"
    assert response["scan_methods"] == list(gate._SCAN_METHODS)
    assert response["scanned_tracked_path_count"] == 4062
    assert response["scanned_python_path_count"] == 1243
    assert response["scanned_notebook_path_count"] == 1
    assert response["scanned_notebook_code_cell_count"] == 8
    assert response["python_parse_error_count"] == 0


def test_reference_inventory_is_exact_frozen_and_zero_active(responses) -> None:
    response = responses[0]
    assert response["active_legacy_reference_records"] == []
    assert response["active_legacy_reference_count"] == 0
    assert response["unresolved_legacy_reference_records"] == []
    assert response["unresolved_legacy_reference_count"] == 0
    retained = response["retained_read_only_reference_records"]
    assert len(retained) == gate._EXPECTED_RETAINED_RECORD_COUNT == 758
    assert response["reference_classification_counts"] == {
        "active_runtime": 0,
        "current_positive_test": 0,
        "negative_rejection_evidence": 3,
        "historical_read_only": 30,
        "design_or_documentation_evidence": 553,
        "gate_control_evidence": 172,
    }
    tuples = [
        (
            item["path"], item["line_or_cell"], item["symbol_or_token"],
            item["reference_kind"], item["classification"], item["retained_reason"],
        )
        for item in retained
    ]
    assert hashlib.sha256(gate._canonical_json_bytes(tuples)).hexdigest() == gate._EXPECTED_RETAINED_RECORDS_SHA256


def test_inventory_has_no_broad_docs_data_or_tests_ignore() -> None:
    source = (SRC / "covalent_ext/covapie_legacy_four_level_mask_retirement_gate_v1.py").read_text()
    assert "ignore all docs" not in source
    assert "ignore all data" not in source
    assert "ignore all tests" not in source
    assert "_EXPECTED_RETAINED_RECORDS_SHA256" in source
    assert 'path.endswith(".md")' not in inspect.getsource(gate._classify_raw_reference)
    assert 'path.startswith("src/covalent_ext/")' not in inspect.getsource(
        gate._classify_raw_reference
    )
    assert "docs/future_mask_notes.md" not in gate._REVIEWED_RETAINED_PATH_POLICIES


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (("tests/future.py", "1", "A", "short_token_runtime_call"), "current_positive_test"),
        (("tests/future.py", "1", "B2", "exact_short_subscript_key"), "current_positive_test"),
        (("src/covalent_ext/future.py", "1", "B3", "short_token_runtime_call"), "active_runtime"),
        (("scripts/future.py", "1", "--mask_level", "cli_add_argument"), "active_runtime"),
    ],
)
def test_dangerous_legacy_reference_kinds_are_blockers_by_default(raw, expected) -> None:
    result = gate._classify_raw_reference(raw, negative_context_valid=True)
    assert result is not None
    assert result[0] == expected
    record = gate._record(raw, *result)
    assert record["active_runtime"] is True
    assert record["classification"] == expected


def test_unreviewed_controlled_text_is_unresolved_not_prefix_retained() -> None:
    raw = ("docs/future_mask_notes.md", "1", "B2", "controlled_text_short_alias_evidence")
    assert gate._classify_raw_reference(raw, negative_context_valid=True) is None


def test_negative_records_require_the_exact_sha_bound_rejection_context(monkeypatch) -> None:
    assert gate._negative_rejection_context_evidence(ROOT) is True
    reviewed = (gate._NEGATIVE_TEST_PATH, "160", "B2", "negative_short_token_collection")
    result = gate._classify_raw_reference(reviewed, negative_context_valid=True)
    assert result is not None and result[0] == "negative_rejection_evidence"
    raw = (gate._NEGATIVE_TEST_PATH, "1", "B2", "negative_short_token_collection")
    assert gate._classify_raw_reference(raw, negative_context_valid=False) is None
    positive_call = (gate._NEGATIVE_TEST_PATH, "1", "mask_scaffold", "python_call")
    result = gate._classify_raw_reference(positive_call, negative_context_valid=True)
    assert result is not None and result[0] == "current_positive_test"

    fake_positive = b'''\nfor unsupported in ["B3", "B2", "mask_scaffold", "legacy_short_B2"]:\n    expected_reactive_atom_region_for_mask_level_v0(unsupported)\n    note = "unsupported_mask_level: unexpectedly accepted"\n'''
    monkeypatch.setattr(gate, "_git_snapshot_blob_bytes", lambda *args, **kwargs: fake_positive)
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._negative_rejection_context_evidence(ROOT)


def test_required_negative_runtime_evidence_and_real_import_failures(responses) -> None:
    assert responses[0]["required_negative_runtime_evidence"] == {
        "legacy_builder_importable": False,
        "legacy_builder_callable": False,
        "legacy_registry_present": False,
        "legacy_schema_type_present": False,
        "legacy_cli_flag_present": False,
        "legacy_short_token_runtime_input_supported": False,
        "legacy_dataset_short_key_supported": False,
    }
    for statement in (
        "from covalent_ext.schema import MaskType",
        "from covalent_ext.masking import build_four_level_mask",
        "from covalent_ext.masking import MASK_BUILDERS",
        "from covalent_ext.masking import mask_scaffold",
    ):
        with pytest.raises(ImportError):
            exec(statement, {})


def test_short_aliases_fail_with_current_canonical_error_and_toy_masks_are_exact() -> None:
    negative, canonical = gate._negative_and_canonical_runtime_evidence(ROOT)
    assert all(value is False for value in negative.values())
    assert canonical["semantic_names_exact"] is True
    assert canonical["levels_exact"] is True
    assert canonical["dataset_exact_five"] is True
    assert canonical["toy_exact"] is True
    assert canonical["B2_B3_distinct"] is True


def test_live_canonical_core_is_byte_bound_before_runtime_oracle(monkeypatch) -> None:
    original = gate._read_live_regular_file

    def drift(root, path, *, require_non_executable=False):
        payload = original(root, path, require_non_executable=require_non_executable)
        return payload + b"# drift\n" if path.endswith("masking.py") else payload

    monkeypatch.setattr(gate, "_read_live_regular_file", drift)
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._negative_and_canonical_runtime_evidence(ROOT)


def test_dataset_consumers_and_r1_demo_are_canonical_only() -> None:
    assert len(gate._DATASET_CONSUMERS) == 4
    gate._canonical_consumer_evidence(ROOT)
    payload = gate._git_snapshot_blob_bytes(
        ROOT, commit=gate._R2_COMMIT, relative_path="scripts/covalent_inpaint_demo.py"
    )
    tree = ast.parse(payload.decode())
    flags = {
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and type(node.value) is str and node.value.startswith("--mask_")
    }
    assert "--mask_semantic" in flags
    assert "--mask_level" not in flags


def test_historical_b3_and_negative_test_boundaries_are_sha_bound_and_not_executed(
    responses,
) -> None:
    gate._historical_and_negative_evidence(ROOT)
    response = responses[0]
    assert response["historical_read_only_legacy_evidence_retained"] is True
    assert response["negative_legacy_token_rejection_evidence_retained"] is True


def test_precommit_lifecycle_pure_helper() -> None:
    expected = {
        "profile": "r3_precommit_candidate",
        "commit": None,
        "committed": False,
        "published": False,
    }
    assert gate._lifecycle_from_facts(_precommit_facts()) == expected


def test_actual_lifecycle_matches_response_and_checker_contract(responses) -> None:
    response = responses[0]
    lifecycle = gate._r3_lifecycle_evidence(ROOT)
    assert response["R3_gate_lifecycle_profile"] == lifecycle["profile"]
    assert response["R3_gate_commit"] == lifecycle["commit"]
    assert response["R3_gate_committed"] is lifecycle["committed"]
    assert response["R3_gate_published"] is lifecycle["published"]
    checker = _load_checker_module()
    assert checker._validate_lifecycle_response(response)


def test_synthetic_committed_unpushed_lifecycle() -> None:
    facts = _precommit_facts()
    facts.update(
        {
            "head": "b" * 40,
            "ordinary_untracked_paths": [],
            "tracked_gate_paths": list(gate._R3_PATHS),
            "regular_gate_paths": True,
            "r3_candidates": [_r3_candidate(published=False)],
        }
    )
    result = gate._lifecycle_from_facts(facts)
    assert result["profile"] == "r3_committed_unpushed"
    assert result["committed"] is True
    assert result["published"] is False


def test_synthetic_published_successor_allows_future_head_and_dirty_worktree() -> None:
    facts = _precommit_facts()
    facts.update(
        {
            "head": "c" * 40,
            "origin_main": "d" * 40,
            "ordinary_untracked_paths": ["future/C1.py"],
            "tracked_gate_paths": list(gate._R3_PATHS),
            "tracked_changes": ["future/C2.py"],
            "staged_changes": ["future/C3.py"],
            "regular_gate_paths": True,
            "r3_candidates": [_r3_candidate(published=True)],
        }
    )
    result = gate._lifecycle_from_facts(facts)
    assert result["profile"] == "r3_published_successor"
    assert result["committed"] is True
    assert result["published"] is True


def test_lifecycle_fails_closed_for_wrong_scope_subject_parent_or_extra_candidate() -> None:
    for mutation in ("subject", "parents", "paths"):
        candidate = _r3_candidate(published=False)
        candidate[mutation] = "wrong" if mutation == "subject" else ["wrong"]
        facts = _precommit_facts()
        facts.update(
            {
                "head": "b" * 40,
                "ordinary_untracked_paths": [],
                "tracked_gate_paths": list(gate._R3_PATHS),
                "r3_candidates": [candidate],
            }
        )
        with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
            gate._lifecycle_from_facts(facts)

    facts = _precommit_facts()
    facts.update(
        {
            "head": "b" * 40,
            "ordinary_untracked_paths": [],
            "tracked_gate_paths": list(gate._R3_PATHS),
            "r3_candidates": [_r3_candidate(published=False), _r3_candidate(published=False)],
        }
    )
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._lifecycle_from_facts(facts)


@pytest.mark.parametrize(
    "candidate_fact",
    [
        "body_empty",
        "gate_commit_modes_bound",
        "gate_commit_blobs_bound",
        "gate_live_bytes_match_commit",
        "head_ancestor",
    ],
)
def test_candidate_commit_metadata_tree_blob_and_live_bindings_fail_closed(candidate_fact) -> None:
    candidate = _r3_candidate(published=False)
    candidate[candidate_fact] = False
    facts = _precommit_facts()
    facts.update(
        {
            "head": "b" * 40,
            "ordinary_untracked_paths": [],
            "tracked_gate_paths": list(gate._R3_PATHS),
            "r3_candidates": [candidate],
        }
    )
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._lifecycle_from_facts(facts)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("ordinary_untracked_paths", ["future/untracked.txt"]),
        ("tracked_changes", ["future/modified.py"]),
        ("staged_changes", ["future/staged.py"]),
        ("regular_gate_paths", False),
    ],
)
def test_committed_unpushed_requires_a_globally_clean_regular_tree(field, value) -> None:
    facts = _precommit_facts()
    facts.update(
        {
            "head": "b" * 40,
            "ordinary_untracked_paths": [],
            "tracked_gate_paths": list(gate._R3_PATHS),
            "r3_candidates": [_r3_candidate(published=False)],
            field: value,
        }
    )
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._lifecycle_from_facts(facts)


@pytest.mark.parametrize("field", ["tracked_changes", "staged_changes"])
def test_committed_unpushed_rejects_r3_self_drift(field) -> None:
    facts = _precommit_facts()
    facts.update(
        {
            "head": "b" * 40,
            "ordinary_untracked_paths": [],
            "tracked_gate_paths": list(gate._R3_PATHS),
            "r3_candidates": [_r3_candidate(published=False)],
            field: [gate._R3_PATHS[0]],
        }
    )
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._lifecycle_from_facts(facts)


@pytest.mark.parametrize("field", ["ordinary_untracked_paths", "tracked_changes", "staged_changes"])
def test_published_successor_rejects_r3_self_drift(field) -> None:
    facts = _precommit_facts()
    facts.update(
        {
            "head": "c" * 40,
            "origin_main": "d" * 40,
            "ordinary_untracked_paths": [],
            "tracked_gate_paths": list(gate._R3_PATHS),
            "r3_candidates": [_r3_candidate(published=True)],
            field: [gate._R3_PATHS[0]],
        }
    )
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._lifecycle_from_facts(facts)


@pytest.mark.parametrize("failure", ["nonregular", "live_mismatch"])
def test_published_successor_rejects_nonregular_or_commit_live_mismatch(failure) -> None:
    candidate = _r3_candidate(published=True)
    facts = _precommit_facts()
    facts.update(
        {
            "head": "c" * 40,
            "origin_main": "d" * 40,
            "ordinary_untracked_paths": [],
            "tracked_gate_paths": list(gate._R3_PATHS),
            "r3_candidates": [candidate],
        }
    )
    if failure == "nonregular":
        facts["regular_gate_paths"] = False
    else:
        candidate["gate_live_bytes_match_commit"] = False
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._lifecycle_from_facts(facts)


def test_checker_pure_validator_accepts_all_three_exact_profiles(responses) -> None:
    checker = _load_checker_module()
    actual = responses[0]
    original = dict(actual)
    candidates = (
        _response_with_lifecycle(
            actual, profile="r3_precommit_candidate", commit=None
        ),
        _response_with_lifecycle(
            actual, profile="r3_committed_unpushed", commit="a" * 40
        ),
        _response_with_lifecycle(
            actual, profile="r3_published_successor", commit="a" * 40
        ),
    )
    assert actual == original
    assert len({candidate["legacy_four_level_mask_retirement_gate_response_sha256"] for candidate in candidates}) == 3
    for candidate in candidates:
        assert len(candidate) == 47
        assert tuple(candidate) == gate.LEGACY_FOUR_LEVEL_MASK_RETIREMENT_GATE_RESPONSE_FIELDS
        assert gate._validate_response(candidate)
        assert checker._validate_lifecycle_response(candidate)


def test_checker_pure_validator_rejects_cross_field_and_commit_inconsistency(responses) -> None:
    checker = _load_checker_module()
    invalid = _response_with_lifecycle(
        responses[0], profile="r3_precommit_candidate", commit=None
    )
    invalid["R3_gate_published"] = True
    with pytest.raises(ValueError, match="CHECK_INVALID$"):
        checker._validate_lifecycle_response(invalid)
    invalid = _response_with_lifecycle(
        responses[0], profile="r3_committed_unpushed", commit="a" * 40
    )
    invalid["R3_gate_commit"] = "not-a-commit"
    with pytest.raises(ValueError, match="CHECK_INVALID$"):
        checker._validate_lifecycle_response(invalid)


def test_actual_lifecycle_claims_are_internally_consistent(responses) -> None:
    response = responses[0]
    assert response["retirement_evidence_passed"] is True
    assert response["R3_gate_implemented"] is True
    assert gate._validate_response(response)
    checker = _load_checker_module()
    assert checker._validate_lifecycle_response(response)
    expected = _response_with_lifecycle(
        response,
        profile=response["R3_gate_lifecycle_profile"],
        commit=response["R3_gate_commit"],
    )
    assert response == expected


def test_actual_lifecycle_assertions_are_structurally_lifecycle_neutral() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }

    pure_calls = {
        gate._attribute_chain(node.func)
        for node in ast.walk(functions["test_precommit_lifecycle_pure_helper"])
        if isinstance(node, ast.Call)
    }
    assert "gate._lifecycle_from_facts" in pure_calls
    assert "gate._r3_lifecycle_evidence" not in pure_calls

    actual_calls = {
        gate._attribute_chain(node.func)
        for node in ast.walk(
            functions["test_actual_lifecycle_matches_response_and_checker_contract"]
        )
        if isinstance(node, ast.Call)
    }
    assert "gate._r3_lifecycle_evidence" in actual_calls
    assert "checker._validate_lifecycle_response" in actual_calls

    digest = "0b960386ef57f4f1363f56dc0cb1823d6c5191c62dfa159eae1c76b760e80496"
    exact47 = functions["test_exact47_field_order_and_canonical_digest"]
    parents = {
        child: parent
        for parent in ast.walk(exact47)
        for child in ast.iter_child_nodes(parent)
    }
    digest_nodes = [
        node
        for node in ast.walk(exact47)
        if isinstance(node, ast.Constant) and node.value == digest
    ]
    assert len(digest_nodes) == 1
    ancestor = parents[digest_nodes[0]]
    while not isinstance(ancestor, ast.If):
        ancestor = parents[ancestor]
    condition = ast.unparse(ancestor.test)
    assert "R3_gate_lifecycle_profile" in condition
    assert "r3_precommit_candidate" in condition


def test_canonical_five_level_response_contract(responses) -> None:
    response = responses[0]
    assert response["canonical_mask_semantic_names"] == list(gate._CANONICAL_SEMANTICS)
    assert response["canonical_mask_count"] == 5
    assert response["canonical_B2_semantic"] == "scaffold_plus_warhead"
    assert response["canonical_B3_semantic"] == "scaffold_only"
    assert response["sixth_mask_added"] is False
    assert response["canonical_five_level_runtime_complete"] is True


def test_no_model_forward_training_backward_optimizer_or_checkpoint_save() -> None:
    source_path = SRC / "covalent_ext/covapie_legacy_four_level_mask_retirement_gate_v1.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = {
        gate._attribute_chain(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    assert not any(
        name and name.split(".")[-1] in {"backward", "step", "save", "save_checkpoint", "fit"}
        for name in calls
    )
    assert "checkpoints/" not in source


def test_training_boundary_remains_closed(responses) -> None:
    response = responses[0]
    assert response["training_or_parameter_update"] is False
    assert response["feature_semantics_audit_required_before_training"] is True
