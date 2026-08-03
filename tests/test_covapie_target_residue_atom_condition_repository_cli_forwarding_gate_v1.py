from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import importlib.util
import inspect
import io
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import stat
import subprocess
import sys
import tempfile
import types

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1
    as gate,
)


ERROR = gate._ERROR
PRECOMMIT_RESPONSE_SHA256 = (
    "da37c93ad73bc33198c64084fead287e56d21eb6d3bcba22850183f0dfb80490"
)


@pytest.fixture(scope="session")
def responses() -> tuple[dict[str, object], dict[str, object]]:
    before = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    first = gate.evaluate_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1(
        repo_root=ROOT
    )
    second = gate.evaluate_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1(
        repo_root=ROOT
    )
    after = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert before == after
    return first, second


@pytest.fixture(scope="session")
def response(responses) -> dict[str, object]:
    return responses[0]


def _load_checker_module():
    path = (
        ROOT
        / "scripts/check_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py"
    )
    spec = importlib.util.spec_from_file_location("covapie_c4_checker_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        "head": gate._C3_COMMIT,
        "origin_main": gate._C3_COMMIT,
        "ahead": 0,
        "behind": 0,
        "ordinary_untracked_paths": list(gate._C4_PATHS),
        "tracked_gate_paths": [],
        "tracked_changes": [],
        "staged_changes": [],
        "regular_gate_paths": True,
        "c4_candidates": [],
    }


def _c4_candidate(*, published: bool, commit: str = "a" * 40) -> dict[str, object]:
    return {
        "commit": commit,
        "subject": gate._C4_SUBJECT,
        "parents": [gate._C3_COMMIT],
        "paths": list(gate._C4_PATHS),
        "head_ancestor": True,
        "origin_main_ancestor": published,
        "body_empty": True,
        "gate_commit_modes_bound": True,
        "gate_commit_blobs_bound": True,
        "gate_live_bytes_match_commit": True,
    }


def _response_with_lifecycle(
    response: dict[str, object], *, profile: str, commit: str | None
) -> dict[str, object]:
    result = dict(response)
    result.update(gate._lifecycle_claims(profile))
    result["C4_gate_lifecycle_profile"] = profile
    result["C4_gate_commit"] = commit
    unsigned = {
        field: result[field]
        for field in gate.REPOSITORY_CLI_FORWARDING_GATE_RESPONSE_FIELDS
        if field != "repository_cli_forwarding_gate_response_sha256"
    }
    result["repository_cli_forwarding_gate_response_sha256"] = hashlib.sha256(
        gate._canonical_json_bytes(unsigned)
    ).hexdigest()
    return result


@contextlib.contextmanager
def _outside_repo_harness():
    parent = ROOT.parent
    path = Path(tempfile.mkdtemp(prefix="covapie-c4-harness-", dir=parent))
    assert path.parent == parent
    assert not path.is_relative_to(ROOT)
    initial = path.lstat()
    assert stat.S_ISDIR(initial.st_mode) and not stat.S_ISLNK(initial.st_mode)
    identity = (initial.st_dev, initial.st_ino)
    try:
        yield path
    finally:
        final = path.lstat()
        assert stat.S_ISDIR(final.st_mode) and not stat.S_ISLNK(final.st_mode)
        assert (final.st_dev, final.st_ino) == identity
        shutil.rmtree(path)


def test_public_api_all_signature_and_keyword_only() -> None:
    assert gate.__all__ == (
        "evaluate_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1",
    )
    function = gate.evaluate_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1
    signature = inspect.signature(function)
    assert list(signature.parameters) == ["repo_root"]
    assert signature.parameters["repo_root"].kind is inspect.Parameter.KEYWORD_ONLY
    with pytest.raises(TypeError):
        function(ROOT)  # type: ignore[misc]


def test_import_is_silent_and_does_not_import_torch_or_touch_checkpoint() -> None:
    script = """
import contextlib, io, sys
before = set(sys.modules)
out, err = io.StringIO(), io.StringIO()
with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
    import covalent_ext.covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1 as gate
print(out.getvalue() == '')
print(err.getvalue() == '')
print('torch' not in set(sys.modules) - before)
"""
    completed = subprocess.run(
        [sys.executable, "-B", "-c", script],
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": f"{ROOT}:{SRC}:{ROOT / 'scripts'}",
        },
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout == "True\nTrue\nTrue\n"
    assert completed.stderr == ""


def test_evaluator_is_deterministic_and_status_preserving(responses) -> None:
    assert responses[0] == responses[1]


def test_exact62_field_order_and_canonical_digest(response) -> None:
    assert len(gate.REPOSITORY_CLI_FORWARDING_GATE_RESPONSE_FIELDS) == 62
    assert len(response) == 62
    assert tuple(response) == gate.REPOSITORY_CLI_FORWARDING_GATE_RESPONSE_FIELDS
    assert gate._validate_response(response)
    unsigned = {
        field: response[field]
        for field in gate.REPOSITORY_CLI_FORWARDING_GATE_RESPONSE_FIELDS
        if field != "repository_cli_forwarding_gate_response_sha256"
    }
    assert response["repository_cli_forwarding_gate_response_sha256"] == hashlib.sha256(
        json.dumps(
            unsigned,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def test_response_is_json_safe_without_path_or_tensor(response) -> None:
    assert json.loads(gate._canonical_json_bytes(response)) == response
    assert not any(isinstance(value, Path) for value in _walk_values(response))
    assert not any(type(value).__module__.startswith("torch") for value in _walk_values(response))


def test_actual_profile_uses_frozen_precommit_digest_only_when_precommit(response) -> None:
    if response["C4_gate_lifecycle_profile"] == "c4_precommit_candidate":
        assert response["repository_cli_forwarding_gate_response_sha256"] == PRECOMMIT_RESPONSE_SHA256


@pytest.mark.parametrize(
    ("name", "commit", "parent", "subject", "scope_count"),
    [
        ("source_R3_commit_identity", gate._R3_COMMIT, gate._R3_PARENT, gate._R3_SUBJECT, 4),
        ("source_C1_commit_identity", gate._C1_COMMIT, gate._C1_PARENT, gate._C1_SUBJECT, 2),
        ("source_C2_commit_identity", gate._C2_COMMIT, gate._C2_PARENT, gate._C2_SUBJECT, 1),
        ("source_C3_commit_identity", gate._C3_COMMIT, gate._C3_PARENT, gate._C3_SUBJECT, 1),
    ],
)
def test_predecessor_commit_identities_are_exact(
    response, name, commit, parent, subject, scope_count
) -> None:
    identity = response[name]
    assert identity["commit"] == commit
    assert identity["parent"] == parent
    assert identity["subject"] == subject
    assert identity["body_empty"] is True
    assert identity["single_parent"] is True
    assert identity["scope_count"] == scope_count
    assert identity["ancestor_of_HEAD"] is True
    assert identity["ancestor_of_origin_main"] is True


@pytest.mark.parametrize(
    ("response_field", "expected"),
    [
        ("source_R3_file_identities", gate._R3_FILES),
        ("source_C1_file_identities", gate._C1_FILES),
    ],
)
def test_multi_file_predecessor_identities_are_sha_mode_blob_and_live_bound(
    response, response_field, expected
) -> None:
    identities = response[response_field]
    assert set(identities) == set(expected)
    for path, sha256 in expected.items():
        assert identities[path]["sha256"] == sha256
        assert re.fullmatch(r"[0-9a-f]{40}", identities[path]["git_blob"])
        assert identities[path]["git_mode"] == "100644"
        assert identities[path]["live_bytes_match_commit"] is True


@pytest.mark.parametrize(
    ("field", "path", "sha256", "blob"),
    [
        ("source_C2_file_identity", gate._C2_PATH, gate._C2_SHA256, gate._C2_BLOB),
        ("source_C3_file_identity", gate._C3_PATH, gate._C3_SHA256, gate._C3_BLOB),
    ],
)
def test_single_runtime_file_identity_is_exact(response, field, path, sha256, blob) -> None:
    identity = response[field]
    assert identity == {
        "sha256": sha256,
        "git_blob": blob,
        "git_mode": "100644",
        "live_bytes_match_commit": True,
    }
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha256


def test_r3_evaluator_response_is_directly_bound(response) -> None:
    assert response["R3_gate_lifecycle_profile"] == "r3_published_successor"
    assert response["R3_gate_commit"] == gate._R3_COMMIT
    assert response["R3_gate_committed"] is True
    assert response["R3_gate_published"] is True
    assert response["R3_response_sha256"] == gate._R3_RESPONSE_SHA256
    assert response["active_legacy_reference_count"] == 0
    assert response["unresolved_legacy_reference_count"] == 0
    assert response["legacy_four_level_full_runtime_retired"] is True
    assert response["canonical_five_level_runtime_complete"] is True
    assert response["retirement_evidence_passed"] is True
    assert response["R3_formal_retirement_bound"] is True


def test_c1_public_api_parser_and_exact6_contract(response) -> None:
    assert response["C1_public_apis"] == list(gate._C1_APIS)
    assert response["C1_public_apis_keyword_only"] is True
    parser = response["C1_parser_contract"]
    assert parser["added_option_strings"] == list(gate._TARGET_OPTIONS)
    assert parser["added_option_count"] == 3
    assert parser["legacy_arguments_return_none"] is True
    exact6 = response["C1_exact6_contract"]
    assert exact6["selector_type"] == "Exact6"
    assert exact6["fields"] == list(gate._EXACT6_FIELDS)
    assert tuple(exact6["example"]) == gate._EXACT6_FIELDS
    assert exact6["example"] == {
        "chain_id": "A",
        "residue_sequence_number": 123,
        "residue_insertion_code": " ",
        "residue_name": "CYS",
        "atom_name": "SG",
        "element": "S",
    }


@pytest.mark.parametrize(
    "claim",
    [
        "loader_public_api_keyword_only",
        "torch_import_is_function_local",
        "frozen_checkpoint_identity_checked_before_deserialization",
        "conditioned_constructor_enabled",
        "single_key_migration_helper_called",
        "strict_migration_report_required",
        "checkpoint_bytes_rechecked_unchanged",
        "CPU_RNG_restored",
    ],
)
def test_c1_loader_contract_is_source_and_formal_gate_bound(response, claim) -> None:
    assert response["C1_conditioned_loader_contract"][claim] is True
    assert response["C1_conditioned_loader_contract"]["loader_executed_by_C4_gate"] is False


def test_existing_model_consumption_formal_gate_is_snapshot_and_bundle_bound(response) -> None:
    contract = response["source_model_consumption_formal_gate_contract"]
    assert contract["commit_identity"]["commit"] == gate._MODEL_GATE_COMMIT
    assert set(contract["commit_snapshot_file_identities"]) == set(gate._MODEL_GATE_FILES)
    assert contract["formal_bundle_size"] == gate._MODEL_GATE_BUNDLE_SIZE
    assert contract["formal_bundle_transport_sha256"] == gate._MODEL_GATE_BUNDLE_SHA256
    assert contract["formal_bundle_internal_sha256"] == gate._MODEL_GATE_INTERNAL_SHA256
    assert contract["model_consumption_gate_implemented"] is True
    assert contract["model_consumption_implemented"] is True
    assert contract["indicator_passed_into_dynamics"] is True
    assert contract["indicator_consumed_by_model"] is True
    assert contract["formal_gate_executed_by_C4_gate"] is False


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("C1_helper_module_import_site_count", 1),
        ("parser_helper_call_count", 1),
        ("parse_args_call_count", 1),
        ("resolver_call_count", 1),
        ("conditioned_loader_call_count", 1),
        ("legacy_loader_call_count", 1),
        ("model_to_call_count", 1),
        ("model_generate_ligands_call_count", 1),
        ("write_sdf_file_call_count", 1),
        ("selector_forwarding_keyword_count", 1),
        ("migration_helper_import_count", 0),
        ("manual_indicator_creation_count", 0),
        ("direct_prepare_pocket_call_count", 0),
        ("direct_ddpm_or_dynamics_call_count", 0),
    ],
)
def test_c2_exact_ast_counts(response, name, expected) -> None:
    assert response["C2_generate_ligands_ast_evidence"][name] == expected


@pytest.mark.parametrize(
    "claim",
    [
        "required_execution_order_proven",
        "legacy_loader_only_when_selector_is_none",
        "conditioned_loader_only_in_else",
        "conditioned_loader_failure_has_no_fallback",
        "selector_forwarded_to_every_batch",
        "resi_list_identity_preserved",
        "ref_ligand_identity_preserved",
        "pocket_selection_not_inferred_from_selector",
        "C1_logic_not_duplicated",
    ],
)
def test_c2_ast_semantics_are_bound(response, claim) -> None:
    assert response["C2_generate_ligands_ast_evidence"][claim] is True
    assert response["C2_generate_ligands_forwarding_bound"] is True


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("build_parser_target_flag_count", 0),
        ("actual_main_parser_helper_call_count", 1),
        ("resolver_call_count", 1),
        ("conditioned_loader_call_count", 1),
        ("legacy_loader_call_count", 1),
        ("model_to_call_count", 1),
        ("main_to_run_selector_forwarding_count", 1),
        ("run_to_prepare_selector_forwarding_count", 1),
        ("prepare_to_model_selector_forwarding_count", 1),
        ("build_long_form_mask_call_count", 1),
        ("sample_given_pocket_call_count", 1),
        ("ddpm_inpaint_call_count", 2),
        ("write_sdf_file_call_count", 1),
        ("manual_indicator_creation_count", 0),
        ("canonical_mask_count", 5),
    ],
)
def test_c3_exact_ast_counts(response, name, expected) -> None:
    assert response["C3_covalent_demo_ast_evidence"][name] == expected


@pytest.mark.parametrize(
    "claim",
    [
        "three_layer_selector_forwarding_identity_proven",
        "build_parser_R1_mask_contract_preserved",
        "actual_main_supports_three_C1_target_flags",
        "selector_resolved_before_loader",
        "legacy_conditioned_loader_branches_mutually_exclusive",
        "conditioned_loader_failure_has_no_fallback",
        "pocket_residues_from_get_pocket_from_ligand",
        "pocket_residues_identity_preserved",
        "selector_not_passed_to_mask_builder",
        "selector_not_passed_to_DDPM",
    ],
)
def test_c3_ast_semantics_are_bound(response, claim) -> None:
    assert response["C3_covalent_demo_ast_evidence"][claim] is True
    assert response["C3_covalent_demo_forwarding_bound"] is True


def test_supported_and_deferred_caller_boundary_is_exact(response) -> None:
    assert response["selected_v1_supported_callers"] == [
        "generate_ligands.py",
        "scripts/covalent_inpaint_demo.py",
    ]
    assert response["supported_caller_count"] == 2
    deferred = response["deferred_callers"]
    assert [item["caller"] for item in deferred] == [
        "test.py",
        "optimize.py",
        "inpaint.py",
        "colab/DiffSBDD.ipynb",
    ]
    assert response["deferred_caller_count"] == 4
    assert all(item["deferred"] is True and item["reason"] for item in deferred)
    assert not set(response["selected_v1_supported_callers"]) & {
        item["caller"] for item in deferred
    }


def test_canonical_mask_contract_is_exactly_five(response) -> None:
    assert response["canonical_mask_semantic_names"] == list(
        gate._CANONICAL_MASK_SEMANTICS
    )
    assert response["canonical_mask_count"] == 5
    assert response["canonical_B2_semantic"] == "scaffold_plus_warhead"
    assert response["canonical_B3_semantic"] == "scaffold_only"
    assert response["sixth_mask_added"] is False
    c3 = response["C3_covalent_demo_ast_evidence"]
    assert c3["canonical_B2_internal"] == "B2_scaffold_warhead"
    assert c3["canonical_B3_internal"] == "B3_scaffold_only"
    assert c3["sixth_mask_added"] is False


@pytest.mark.parametrize(
    "claim",
    [
        "partial_selector_rejected",
        "target_fields_without_enable_rejected",
        "unknown_target_field_rejected",
        "non_bool_enable_rejected",
        "unstripped_chain_rejected",
        "bool_residue_sequence_number_rejected",
        "conditioned_loader_failure_has_no_fallback",
    ],
)
def test_failure_contract_fails_closed(response, claim) -> None:
    assert response["failure_contract"]["canonical_error"] == gate._C1_ERROR
    assert response["failure_contract"][claim] is True


def test_automatic_target_inference_is_empty(response) -> None:
    assert response["automatic_target_inference_sources"] == []
    serialized = json.dumps(response["C1_exact6_contract"], sort_keys=True)
    for forbidden in (
        "resi_list",
        "ref_ligand",
        "nearest sulfur",
        "distance",
        "first CYS",
    ):
        assert forbidden not in serialized


def test_precommit_lifecycle_pure_helper() -> None:
    assert gate._lifecycle_from_facts(_precommit_facts()) == {
        "profile": "c4_precommit_candidate",
        "commit": None,
        "committed": False,
        "published": False,
    }


def test_committed_unpushed_lifecycle_pure_helper() -> None:
    facts = _precommit_facts()
    facts.update(
        {
            "head": "a" * 40,
            "ahead": 1,
            "ordinary_untracked_paths": [],
            "tracked_gate_paths": list(gate._C4_PATHS),
            "c4_candidates": [_c4_candidate(published=False)],
        }
    )
    assert gate._lifecycle_from_facts(facts) == {
        "profile": "c4_committed_unpushed",
        "commit": "a" * 40,
        "committed": True,
        "published": False,
    }


def test_published_successor_lifecycle_allows_unrelated_future_changes() -> None:
    facts = _precommit_facts()
    facts.update(
        {
            "head": "b" * 40,
            "origin_main": "c" * 40,
            "ordinary_untracked_paths": ["future/untracked.txt"],
            "tracked_gate_paths": list(gate._C4_PATHS),
            "tracked_changes": ["future/modified.py"],
            "staged_changes": ["future/staged.py"],
            "c4_candidates": [_c4_candidate(published=True)],
        }
    )
    assert gate._lifecycle_from_facts(facts) == {
        "profile": "c4_published_successor",
        "commit": "a" * 40,
        "committed": True,
        "published": True,
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("subject", "wrong"),
        ("parents", ["wrong"]),
        ("paths", ["wrong"]),
        ("body_empty", False),
        ("gate_commit_modes_bound", False),
        ("gate_commit_blobs_bound", False),
        ("gate_live_bytes_match_commit", False),
        ("head_ancestor", False),
    ],
)
def test_lifecycle_rejects_invalid_candidate_facts(field, value) -> None:
    candidate = _c4_candidate(published=False)
    candidate[field] = value
    facts = _precommit_facts()
    facts.update(
        {
            "head": "a" * 40,
            "ahead": 1,
            "ordinary_untracked_paths": [],
            "tracked_gate_paths": list(gate._C4_PATHS),
            "c4_candidates": [candidate],
        }
    )
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        gate._lifecycle_from_facts(facts)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("ordinary_untracked_paths", ["future/untracked.txt"]),
        ("tracked_changes", ["future/modified.py"]),
        ("staged_changes", ["future/staged.py"]),
        ("regular_gate_paths", False),
        ("ahead", 2),
        ("behind", 1),
    ],
)
def test_committed_unpushed_requires_exact_clean_one_ahead_profile(field, value) -> None:
    facts = _precommit_facts()
    facts.update(
        {
            "head": "a" * 40,
            "ahead": 1,
            "ordinary_untracked_paths": [],
            "tracked_gate_paths": list(gate._C4_PATHS),
            "c4_candidates": [_c4_candidate(published=False)],
            field: value,
        }
    )
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        gate._lifecycle_from_facts(facts)


@pytest.mark.parametrize(
    "field", ["ordinary_untracked_paths", "tracked_changes", "staged_changes"]
)
def test_published_successor_rejects_C4_self_drift(field) -> None:
    facts = _precommit_facts()
    facts.update(
        {
            "head": "b" * 40,
            "origin_main": "c" * 40,
            "ordinary_untracked_paths": [],
            "tracked_gate_paths": list(gate._C4_PATHS),
            "c4_candidates": [_c4_candidate(published=True)],
            field: [gate._C4_PATHS[0]],
        }
    )
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        gate._lifecycle_from_facts(facts)


def test_actual_lifecycle_is_valid_without_hardcoding_a_profile(response) -> None:
    lifecycle = gate._c4_lifecycle_evidence(ROOT)
    assert response["C4_gate_lifecycle_profile"] == lifecycle["profile"]
    assert response["C4_gate_commit"] == lifecycle["commit"]
    assert response["C4_gate_committed"] is lifecycle["committed"]
    assert response["C4_gate_published"] is lifecycle["published"]
    assert _load_checker_module()._validate_lifecycle_response(response)


def test_synthetic_responses_validate_all_three_lifecycle_profiles(response) -> None:
    checker = _load_checker_module()
    candidates = (
        _response_with_lifecycle(
            response, profile="c4_precommit_candidate", commit=None
        ),
        _response_with_lifecycle(
            response, profile="c4_committed_unpushed", commit="a" * 40
        ),
        _response_with_lifecycle(
            response, profile="c4_published_successor", commit="a" * 40
        ),
    )
    assert len(
        {
            candidate["repository_cli_forwarding_gate_response_sha256"]
            for candidate in candidates
        }
    ) == 3
    for candidate in candidates:
        assert gate._validate_response(candidate)
        assert checker._validate_lifecycle_response(candidate)


def test_synthetic_response_validators_reject_cross_field_drift(response) -> None:
    candidate = _response_with_lifecycle(
        response, profile="c4_precommit_candidate", commit=None
    )
    candidate["C4_gate_published"] = True
    unsigned = dict(candidate)
    unsigned.pop("repository_cli_forwarding_gate_response_sha256")
    candidate["repository_cli_forwarding_gate_response_sha256"] = hashlib.sha256(
        gate._canonical_json_bytes(unsigned)
    ).hexdigest()
    with pytest.raises(ValueError):
        gate._validate_response(candidate)
    with pytest.raises(ValueError):
        _load_checker_module()._validate_lifecycle_response(candidate)


class _FakeGeneratedModel:
    def __init__(self, records: dict[str, object]):
        self.records = records

    def to(self, device):
        self.records.setdefault("to", []).append(device)
        return self

    def generate_ligands(self, *args, **kwargs):
        self.records.setdefault("generate", []).append((args, kwargs))
        return [object(), object()]


def _run_c2_script(
    monkeypatch: pytest.MonkeyPatch,
    harness: Path,
    *,
    conditioned: bool,
    partial: bool = False,
    conditioned_failure: bool = False,
) -> dict[str, object]:
    from covalent_ext import covapie_target_residue_atom_condition_repository_cli_v1 as helper

    records: dict[str, object] = {"legacy_load": [], "conditioned_load": [], "sdf": []}
    model = _FakeGeneratedModel(records)

    class FakeLigandPocketDDPM:
        @classmethod
        def load_from_checkpoint(cls, *args, **kwargs):
            records["legacy_load"].append((args, kwargs))
            return model

    def conditioned_loader(**kwargs):
        records["conditioned_load"].append(kwargs)
        if conditioned_failure:
            raise ValueError(gate._C1_ERROR)
        return model

    monkeypatch.setattr(
        helper,
        "load_covapie_target_residue_conditioned_model_from_checkpoint_v1",
        conditioned_loader,
    )
    torch_module = types.ModuleType("torch")
    torch_module.cuda = types.SimpleNamespace(is_available=lambda: False)
    torch_module.ones = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("num_nodes path unexpectedly executed")
    )
    openbabel_package = types.ModuleType("openbabel")
    openbabel_module = types.ModuleType("openbabel.openbabel")
    openbabel_module.obErrorLog = types.SimpleNamespace(StopLogging=lambda: None)
    openbabel_package.openbabel = openbabel_module
    utils_module = types.ModuleType("utils")
    utils_module.write_sdf_file = lambda *args: records["sdf"].append(args)
    lightning_module = types.ModuleType("lightning_modules")
    lightning_module.LigandPocketDDPM = FakeLigandPocketDDPM
    for name, module in {
        "torch": torch_module,
        "openbabel": openbabel_package,
        "openbabel.openbabel": openbabel_module,
        "utils": utils_module,
        "lightning_modules": lightning_module,
    }.items():
        monkeypatch.setitem(sys.modules, name, module)

    argv = [
        "generate_ligands.py",
        str(harness / "checkpoint.ckpt"),
        "--pdbfile",
        str(harness / "protein.pdb"),
        "--resi_list",
        "A:10",
        "A:11",
        "--ref_ligand",
        str(harness / "reference.sdf"),
        "--outfile",
        str(harness / "output.sdf"),
        "--n_samples",
        "4",
        "--batch_size",
        "2",
    ]
    if conditioned or partial:
        argv.extend(["--target_residue_atom_conditioning", "--target_chain_id", "A"])
    if conditioned and not partial:
        argv.extend(["--target_residue_sequence_number", "123"])
    monkeypatch.setattr(sys, "argv", argv)
    runpy.run_path(str(ROOT / gate._C2_PATH), run_name="__main__")
    return records


def test_c2_runtime_mock_legacy_path_preserves_batches_pocket_and_sdf(monkeypatch) -> None:
    with _outside_repo_harness() as harness:
        records = _run_c2_script(monkeypatch, harness, conditioned=False)
    assert len(records["legacy_load"]) == 1
    assert records["conditioned_load"] == []
    assert len(records["generate"]) == 2
    for args, kwargs in records["generate"]:
        assert args[1] == 2
        assert args[2] == ["A:10", "A:11"]
        assert args[3].endswith("reference.sdf")
        assert kwargs["target_residue_atom_condition_spec"] is None
    assert len(records["sdf"]) == 1
    assert len(records["sdf"][0][1]) == 4


def test_c2_runtime_mock_conditioned_selector_is_same_for_every_batch(monkeypatch) -> None:
    with _outside_repo_harness() as harness:
        records = _run_c2_script(monkeypatch, harness, conditioned=True)
    assert records["legacy_load"] == []
    assert len(records["conditioned_load"]) == 1
    selectors = [
        kwargs["target_residue_atom_condition_spec"]
        for _args, kwargs in records["generate"]
    ]
    assert len(selectors) == 2 and selectors[0] is selectors[1]
    assert selectors[0] == {
        "chain_id": "A",
        "residue_sequence_number": 123,
        "residue_insertion_code": " ",
        "residue_name": "CYS",
        "atom_name": "SG",
        "element": "S",
    }


def test_c2_runtime_mock_partial_selector_fails_before_any_loader(monkeypatch) -> None:
    with _outside_repo_harness() as harness:
        with pytest.raises(ValueError, match=f"^{gate._C1_ERROR}$"):
            _run_c2_script(monkeypatch, harness, conditioned=True, partial=True)


def test_c2_runtime_mock_conditioned_loader_failure_has_no_legacy_fallback(monkeypatch) -> None:
    with _outside_repo_harness() as harness:
        with pytest.raises(ValueError, match=f"^{gate._C1_ERROR}$"):
            _run_c2_script(
                monkeypatch,
                harness,
                conditioned=True,
                conditioned_failure=True,
            )


def _load_c3_module(monkeypatch: pytest.MonkeyPatch):
    torch_module = types.ModuleType("torch")
    torch_module.Tensor = object
    torch_module.cuda = types.SimpleNamespace(is_available=lambda: True)
    torch_module.device = lambda value: value
    torch_module.no_grad = lambda: contextlib.nullcontext()
    torch_module.nn = types.ModuleType("torch.nn")
    functional = types.ModuleType("torch.nn.functional")
    torch_module.nn.functional = functional
    bio_module = types.ModuleType("Bio")
    bio_pdb_module = types.ModuleType("Bio.PDB")
    bio_pdb_module.PDBParser = object
    rdkit_module = types.ModuleType("rdkit")
    chem_module = types.ModuleType("rdkit.Chem")
    rdkit_module.Chem = chem_module
    scatter_module = types.ModuleType("torch_scatter")
    scatter_module.scatter_mean = lambda *args, **kwargs: None
    builder_module = types.ModuleType("analysis.molecule_builder")
    builder_module.build_molecule = lambda *args, **kwargs: None
    builder_module.process_molecule = lambda *args, **kwargs: None
    constants_module = types.ModuleType("constants")
    constants_module.FLOAT_TYPE = object()
    constants_module.INT_TYPE = object()
    masking_module = types.ModuleType("covalent_ext.masking")
    masking_module.build_long_form_mask = lambda *args, **kwargs: None
    lightning_module = types.ModuleType("lightning_modules")
    lightning_module.LigandPocketDDPM = object
    utils_module = types.ModuleType("utils")
    modules = {
        "torch": torch_module,
        "torch.nn": torch_module.nn,
        "torch.nn.functional": functional,
        "Bio": bio_module,
        "Bio.PDB": bio_pdb_module,
        "rdkit": rdkit_module,
        "rdkit.Chem": chem_module,
        "torch_scatter": scatter_module,
        "analysis.molecule_builder": builder_module,
        "constants": constants_module,
        "covalent_ext.masking": masking_module,
        "lightning_modules": lightning_module,
        "utils": utils_module,
    }
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    path = ROOT / gate._C3_PATH
    spec = importlib.util.spec_from_file_location("covapie_c3_runtime_mock", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("conditioned", [False, True])
def test_c3_runtime_mock_main_to_run_to_prepare_to_model_identity(
    monkeypatch, conditioned, capsys
) -> None:
    module = _load_c3_module(monkeypatch)
    records: dict[str, object] = {
        "legacy_load": [],
        "conditioned_load": [],
        "run": [],
        "prepare": [],
        "sdf": [],
    }
    model = types.SimpleNamespace()
    model.to = lambda device: model
    model.prepare_pocket = lambda residues, **kwargs: records["prepare"].append(
        (residues, kwargs)
    ) or {"pocket": True}

    class FakeLigandPocketDDPM:
        @classmethod
        def load_from_checkpoint(cls, *args, **kwargs):
            records["legacy_load"].append((args, kwargs))
            return model

    selector_holder: dict[str, object] = {}

    def conditioned_loader(**kwargs):
        records["conditioned_load"].append(kwargs)
        return model

    residues = object()

    class FakePDBParser:
        def __init__(self, **kwargs):
            pass

        def get_structure(self, *args):
            return [{0: "unused"}][0] if False else [object()]

    module.PDBParser = FakePDBParser
    module.LigandPocketDDPM = FakeLigandPocketDDPM
    module.load_covapie_target_residue_conditioned_model_from_checkpoint_v1 = conditioned_loader
    module.utils.get_pocket_from_ligand = lambda pdb_model, ligand: residues
    module.utils.write_sdf_file = lambda *args: records["sdf"].append(args)
    actual_prepare = module.prepare_single_pocket

    class FakeFixed:
        def tolist(self):
            return [1, 0]

    mask_result = types.SimpleNamespace(
        mask_type="A_warhead_only",
        visible_atoms=(0,),
        masked_atoms=(1,),
        lig_fixed=FakeFixed(),
    )

    def run_wrapper(**kwargs):
        records["run"].append(kwargs)
        selector_holder["value"] = kwargs["target_residue_atom_condition_spec"]
        actual_prepare(
            kwargs["model"],
            kwargs["protein_pdb"],
            kwargs["ligand_sdf"],
            target_residue_atom_condition_spec=kwargs[
                "target_residue_atom_condition_spec"
            ],
        )
        return [object()], mask_result

    module.run_covalent_inpaint = run_wrapper
    with _outside_repo_harness() as harness:
        argv = [
            "covalent_inpaint_demo.py",
            "--protein_pdb",
            str(harness / "protein.pdb"),
            "--ligand_sdf",
            str(harness / "ligand.sdf"),
            "--scaffold_atoms",
            "0",
            "--linker_atoms",
            "1",
            "--warhead_atoms",
            "2",
            "--mask_semantic",
            "warhead_only",
            "--checkpoint",
            str(harness / "checkpoint.ckpt"),
            "--output",
            str(harness / "output" / "result.sdf"),
            "--device",
            "cpu",
        ]
        if conditioned:
            argv.extend(
                [
                    "--target_residue_atom_conditioning",
                    "--target_chain_id",
                    "A",
                    "--target_residue_sequence_number",
                    "123",
                ]
            )
        monkeypatch.setattr(sys, "argv", argv)
        assert module.main() == 0
    selector = selector_holder["value"]
    if conditioned:
        assert records["legacy_load"] == []
        assert len(records["conditioned_load"]) == 1
        assert selector["chain_id"] == "A"
    else:
        assert len(records["legacy_load"]) == 1
        assert records["conditioned_load"] == []
        assert selector is None
    assert records["run"][0]["model"] is model
    assert records["prepare"][0][0] is residues
    assert records["prepare"][0][1]["target_residue_atom_condition_spec"] is selector
    assert len(records["sdf"]) == 1
    capsys.readouterr()


def test_c3_runtime_mock_partial_selector_fails_before_loader(monkeypatch) -> None:
    module = _load_c3_module(monkeypatch)
    legacy_calls: list[object] = []
    conditioned_calls: list[object] = []

    class FakeLigandPocketDDPM:
        @classmethod
        def load_from_checkpoint(cls, *args, **kwargs):
            legacy_calls.append((args, kwargs))

    module.LigandPocketDDPM = FakeLigandPocketDDPM
    module.load_covapie_target_residue_conditioned_model_from_checkpoint_v1 = (
        lambda **kwargs: conditioned_calls.append(kwargs)
    )
    with _outside_repo_harness() as harness:
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "covalent_inpaint_demo.py",
                "--protein_pdb",
                str(harness / "protein.pdb"),
                "--ligand_sdf",
                str(harness / "ligand.sdf"),
                "--scaffold_atoms",
                "0",
                "--linker_atoms",
                "1",
                "--warhead_atoms",
                "2",
                "--mask_semantic",
                "warhead_only",
                "--checkpoint",
                str(harness / "checkpoint.ckpt"),
                "--output",
                str(harness / "result.sdf"),
                "--device",
                "cpu",
                "--target_residue_atom_conditioning",
                "--target_chain_id",
                "A",
            ],
        )
        with pytest.raises(ValueError, match=f"^{gate._C1_ERROR}$"):
            module.main()
    assert legacy_calls == []
    assert conditioned_calls == []


def test_c3_build_parser_remains_pure_R1_mask_surface(monkeypatch) -> None:
    module = _load_c3_module(monkeypatch)
    parser = module.build_parser()
    options = set(parser._option_string_actions)
    assert not set(gate._TARGET_OPTIONS) & options
    assert "--mask_semantic" in options
    action = parser._option_string_actions["--mask_semantic"]
    assert tuple(action.choices) == gate._CANONICAL_MASK_SEMANTICS


def test_gate_source_has_no_runtime_model_training_or_persistence_calls() -> None:
    path = ROOT / gate._C4_PATHS[0]
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    call_names = {
        gate._attribute_chain(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    assert "torch" not in imports
    forbidden = {
        "torch.load",
        "model.generate_ligands",
        "model.prepare_pocket",
        "model.forward",
        "model.backward",
        "optimizer.step",
        "torch.save",
        "Path.write_bytes",
        "Path.write_text",
        "open",
    }
    assert not forbidden & call_names


def test_training_runtime_smoke_and_RL_boundaries_remain_closed(response) -> None:
    assert response["real_repository_cli_runtime_smoke_executed"] is False
    assert response["training_or_parameter_update"] is False
    assert response["RL_implementation_started"] is False
    assert response["checkpoint_loaded_by_C4_gate"] is False
    assert response["model_forward_executed_by_C4_gate"] is False
    assert response["feature_semantics_audit_required_before_training"] is True
    assert response["Step12D_smoke_is_not_final_training_feature_contract"] is True
