from __future__ import annotations

import csv
import dataclasses
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_current11_observed_to_parent_atom_projection_authority_v1 as authority,
)
from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle  # noqa: E402


CHECKER_PATH = (
    ROOT
    / "scripts/"
    "check_covapie_current11_observed_to_parent_atom_projection_authority_v1.py"
)
SPEC = importlib.util.spec_from_file_location("current11_projection_checker", CHECKER_PATH)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
NESTED_LIFECYCLE_ENV = "COVAPIE_CURRENT11_PROJECTION_NESTED_LIFECYCLE"
FROZEN_DATA_SHA256 = {
    authority.SOURCE_INVENTORY_FILE:
        "d390552f2c81ca1d1822e4187f83f8e5d54a04f34479ee465e78f63af776f484",
    authority.MAPPING_FILE:
        "f803e0c5fb2585c8dae31dbff254749496f897f4bf9a5103455c6c675a132a1e",
    authority.BOND_FILE:
        "bd31b7c074c3d4226c26bfe0210b9c3460f38c5087f1157b1167749f91bfffe0",
    authority.READINESS_FILE:
        "ec7bb2c203a7b13f525c413171b734fdd9f8af934b6e7e8eaf3fc6ae141128a0",
    authority.FAILURE_FILE:
        "b691dab51399336aa29c1e8c54d93ed55059517bf09ea94823f6c7af23eb0a6d",
    authority.MANIFEST_FILE:
        "e553e9cb1518cd2c9465772758539e9610c8f81cd702dd0440e99fbd143fc0a7",
}


def _git(*arguments: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if check:
        assert result.returncode == 0, result.stderr
    return result.stdout


def _git_at(
    repository: Path,
    *arguments: str,
    input_bytes: bytes | None = None,
) -> bytes:
    result = subprocess.run(
        ("git", *arguments),
        cwd=repository,
        input=input_bytes,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "CovaPIE Boundary Test",
            "GIT_AUTHOR_EMAIL": "covapie-boundary@example.invalid",
            "GIT_COMMITTER_NAME": "CovaPIE Boundary Test",
            "GIT_COMMITTER_EMAIL": "covapie-boundary@example.invalid",
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+00:00",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _boundary_repository(
    root: Path,
    *,
    parent_kind: str = "base",
    subject: str = authority.FORMAL_COMMIT_SUBJECT,
    body: str = "",
    missing_path: bool = False,
    extra_path: bool = False,
    wrong_mode: bool = False,
    second_generation: bool = False,
) -> tuple[Path, str]:
    repository = root / "boundary"
    _git_at(root, "clone", "--no-checkout", "--shared", str(ROOT), str(repository))
    _git_at(
        repository,
        "update-ref",
        "refs/remotes/origin/main",
        authority.BASE_COMMIT,
    )
    _git_at(repository, "read-tree", authority.BASE_COMMIT)
    paths = authority.EXACT10_PATHS[:-1] if missing_path else authority.EXACT10_PATHS
    for index, relative in enumerate(paths):
        blob = _git_at(
            repository,
            "hash-object",
            "-w",
            (ROOT / relative).as_posix(),
        ).decode().strip()
        mode = "100755" if wrong_mode and index == 0 else "100644"
        _git_at(
            repository,
            "update-index",
            "--add",
            "--cacheinfo",
            mode,
            blob,
            relative.as_posix(),
        )
    if extra_path:
        blob = _git_at(
            repository, "hash-object", "-w", "--stdin", input_bytes=b"extra\n"
        ).decode().strip()
        _git_at(
            repository,
            "update-index",
            "--add",
            "--cacheinfo",
            "100644",
            blob,
            "extra_boundary_path.txt",
        )
    tree = _git_at(repository, "write-tree").decode().strip()
    if parent_kind == "base":
        parents = ("-p", authority.BASE_COMMIT)
    elif parent_kind == "wrong":
        parents = ("-p", authority.BASE_PARENT)
    elif parent_kind == "merge":
        parents = (
            "-p", authority.BASE_COMMIT, "-p", authority.BASE_PARENT,
        )
    else:
        raise AssertionError("unsupported parent kind")
    message = subject + "\n" + (("\n" + body + "\n") if body else "")
    candidate = _git_at(
        repository,
        "commit-tree",
        tree,
        *parents,
        input_bytes=message.encode("utf-8"),
    ).decode().strip()
    if second_generation:
        candidate = _git_at(
            repository,
            "commit-tree",
            tree,
            "-p",
            candidate,
            input_bytes=(authority.FORMAL_COMMIT_SUBJECT + "\n").encode(),
        ).decode().strip()
    _git_at(repository, "update-ref", "HEAD", candidate)
    return repository, candidate


def _base(path: Path) -> bytes:
    return _git("show", f"{authority.BASE_COMMIT}:{path.as_posix()}")


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _artifact_rows(name: str) -> list[dict[str, str]]:
    return _rows((ROOT / authority.OUTPUT_ROOT / name).read_bytes())


def _manifest() -> dict[str, object]:
    return json.loads((ROOT / authority.OUTPUT_ROOT / authority.MANIFEST_FILE).read_bytes())


def _bool(value: str) -> bool:
    assert value in ("true", "false")
    return value == "true"


def test_runtime_contract_is_exact_cpython_3104_pytest_910() -> None:
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    assert pytest.__version__ == "9.1.0"
    assert os.path.realpath(sys.executable) == (
        "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
        "covapie-envs/diffsbdd-legacy-test-v1/bin/python3.10"
    )


def test_formal_base_identity_lifecycle_and_exact9_predecessor_sha() -> None:
    shown = _git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", authority.BASE_COMMIT
    ).decode().splitlines()
    assert shown == [
        authority.BASE_COMMIT,
        authority.BASE_PARENT,
        authority.BASE_TREE,
        authority.BASE_SUBJECT,
    ]
    production_lifecycle = authority.validate_execution_boundary_v2(ROOT)
    checker_lifecycle = checker.validate_execution_boundary_independent()
    assert production_lifecycle == checker_lifecycle
    assert production_lifecycle in lifecycle.LIFECYCLES
    assert hashlib.sha256(_base(authority.EXACT9_SOURCE)).hexdigest() == (
        "b2bc177fdd2e10cfc643329f08a12a22684eaa6317a398ae1d4d1b834525d4cd"
    )
    assert hashlib.sha256(_base(authority.PARENT_ATOMS)).hexdigest() == (
        "d50b052c2ed2573ccfdcf66470a077744ad11f4a083daee11f20d794b3b23fe7"
    )
    assert hashlib.sha256(_base(authority.PARENT_BONDS)).hexdigest() == (
        "26957b9f78217c808d2dc021cfab1a2bf78dd1708c46c49f220ae32a3a09ebbf"
    )


def test_pre_commit_boundary_accepts_exact_base(tmp_path: Path) -> None:
    repository = tmp_path / "pre"
    _git_at(tmp_path, "clone", "--no-checkout", "--shared", str(ROOT), str(repository))
    _git_at(repository, "update-ref", "HEAD", authority.BASE_COMMIT)
    assert authority.validate_execution_boundary_v2(repository) == "pre_commit"


def test_exact_successor_commit_boundary_is_accepted(tmp_path: Path) -> None:
    repository, candidate = _boundary_repository(tmp_path)
    assert candidate != authority.BASE_COMMIT
    assert _git_at(
        repository, "show", "-s", "--format=%P", candidate
    ).decode().strip() == authority.BASE_COMMIT
    assert authority.validate_execution_boundary_v2(repository) in (
        "detached_candidate_post_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    )


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"parent_kind": "wrong"}, "successor_parent_not_exact_BASE"),
        ({"parent_kind": "merge"}, "successor_parent_not_exact_BASE"),
        ({"subject": "wrong subject"}, "successor_subject_mismatch"),
        ({"body": "nonempty body"}, "successor_commit_body_nonempty"),
        ({"missing_path": True}, "successor_changed_path_inventory_mismatch"),
        ({"extra_path": True}, "successor_changed_path_inventory_mismatch"),
        ({"wrong_mode": True}, "successor_exact10_file_mode_invalid"),
        ({"second_generation": True}, "successor_parent_not_exact_BASE"),
    ],
    ids=(
        "wrong-parent", "merge-commit", "wrong-subject", "nonempty-body",
        "missing-path", "extra-path", "wrong-mode", "second-generation",
    ),
)
def test_invalid_successor_boundaries_fail_closed(
    tmp_path: Path,
    kwargs: dict[str, object],
    reason: str,
) -> None:
    repository, _candidate = _boundary_repository(tmp_path, **kwargs)
    with pytest.raises(ValueError, match=reason):
        authority.validate_execution_boundary_v2(repository)


def test_frozen_sources_are_always_read_from_base_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_git = authority._git
    shown_specs: list[str] = []

    def recording_git(repo_root: Path, *arguments: str, **kwargs):
        if (
            arguments
            and arguments[0] == "show"
            and arguments[-1].startswith(authority.BASE_COMMIT + ":")
        ):
            shown_specs.append(arguments[-1])
        return real_git(repo_root, *arguments, **kwargs)

    monkeypatch.setattr(authority, "_git", recording_git)
    payloads = authority.load_frozen_sources(ROOT)
    assert len(payloads) == 21
    assert len(shown_specs) == 21
    assert set(shown_specs) == {
        f"{authority.BASE_COMMIT}:{path.as_posix()}"
        for path in authority.FROZEN_BASE_SHA256
    }


def test_all_checked_base_sources_are_frozen_and_tracked() -> None:
    assert len(authority.FROZEN_BASE_SHA256) == 21
    assert len(authority.LIGAND_ATOM_TABLES) == 11
    for path, expected_sha in authority.FROZEN_BASE_SHA256.items():
        payload = _base(path)
        assert hashlib.sha256(payload).hexdigest() == expected_sha
        assert _git(
            "cat-file", "-e", f"{authority.BASE_COMMIT}:{path.as_posix()}"
        ) == b""


def test_source_inventory_truthfully_distinguishes_row_level_authority() -> None:
    rows = _artifact_rows(authority.SOURCE_INVENTORY_FILE)
    assert len(rows) == 21
    by_path = {row["source_path"]: row for row in rows}
    projection = by_path[authority.HEAVY_PROJECTION.as_posix()]
    assert projection["Current11_coverage"] == (
        "11/11 samples;323/323 retained-heavy ligand rows"
    )
    assert _bool(projection["source_row_index_present"])
    assert _bool(projection["retained_local_index_present"])
    for path in authority.LIGAND_ATOM_TABLES:
        row = by_path[path.as_posix()]
        assert _bool(row["BASE_tracked"])
        assert _bool(row["row_level_atom_names_present"])
        assert _bool(row["element_present"])
        assert "1/11 samples;" in row["Current11_coverage"]
        assert _bool(row["verified"])
    for path in set(authority.FROZEN_BASE_SHA256) - set(authority.LIGAND_ATOM_TABLES):
        assert not _bool(by_path[path.as_posix()]["row_level_atom_names_present"])


def test_phase_a_observed_authority_is_exact_current11_and_323() -> None:
    payloads = authority.load_frozen_sources(ROOT)
    samples, observed, evidence, source_rows = authority._phase_a(payloads)
    assert len(samples) == len(evidence) == 11
    assert len({row["sample_index_row_id"] for row in samples}) == 11
    assert len({row["ligand_comp_id"] for row in samples}) == 9
    assert len(observed) == 323
    assert len(source_rows) == 21
    assert {
        (row["sample_index_row_id"], row["pdb_id"], row["ligand_comp_id"])
        for row in samples
    } == {
        (row["sample_index_row_id"], row["pdb_id"], row["ligand_comp_id"])
        for row in _rows(_base(authority.GRAPH_EVIDENCE))
    }


def test_sample_local_and_source_full_indices_are_unique_and_contiguous() -> None:
    rows = _artifact_rows(authority.MAPPING_FILE)
    by_sample: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_sample[row["sample_index_row_id"]].append(row)
    assert len(by_sample) == 11
    for sample_rows in by_sample.values():
        names = [row["observed_atom_name"] for row in sample_rows]
        source = [int(row["source_full_atom_row_index"]) for row in sample_rows]
        local = [
            int(row["retained_heavy_local_index_0based"]) for row in sample_rows
        ]
        assert len(names) == len(set(names))
        assert len(source) == len(set(source))
        assert len(local) == len(set(local))
        assert sorted(local) == list(range(len(sample_rows)))


def test_exact_mapping_element_match_and_reactive_atom_counts() -> None:
    rows = _artifact_rows(authority.MAPPING_FILE)
    assert len(rows) == 323
    assert all(
        row["observed_atom_name"] == row["parent_ccd_atom_id"] for row in rows
    )
    assert all(
        row["observed_type_symbol"] == row["parent_ccd_type_symbol"] for row in rows
    )
    assert all(_bool(row["atom_name_exact_match"]) for row in rows)
    assert all(_bool(row["element_exact_match"]) for row in rows)
    assert all(row["authority_class"] == authority.AUTHORITY_CLASS for row in rows)
    reactive = [row for row in rows if _bool(row["reactive_ligand_atom"])]
    assert len(reactive) == 11
    assert len({row["sample_index_row_id"] for row in reactive}) == 11


def test_parent_expansion_is_324_and_only_zya_f1_is_missing() -> None:
    payloads = authority.load_frozen_sources(ROOT)
    parent_atoms = _rows(payloads[authority.PARENT_ATOMS])
    samples = _rows(payloads[authority.PARENT_READINESS])
    mapping = _artifact_rows(authority.MAPPING_FILE)
    parent_by_component: dict[str, set[str]] = defaultdict(set)
    for row in parent_atoms:
        parent_by_component[row["ligand_comp_id"]].add(row["ccd_atom_id"])
    assert sum(len(parent_by_component[row["ligand_comp_id"]]) for row in samples) == 324
    mapped_by_sample: dict[str, set[str]] = defaultdict(set)
    for row in mapping:
        mapped_by_sample[row["sample_index_row_id"]].add(row["parent_ccd_atom_id"])
    missing = []
    for sample in samples:
        sample_id = sample["sample_index_row_id"]
        component = sample["ligand_comp_id"]
        missing.extend(
            (sample_id, component, atom_id)
            for atom_id in sorted(parent_by_component[component] - mapped_by_sample[sample_id])
        )
    assert missing == [("CYS_SG_SAMPLE_INDEX_000005", "ZYA", "F1")]


def test_zya_f1_leaving_group_and_parent_bond_are_evidence_driven() -> None:
    evidence = {
        row["sample_index_row_id"]: row
        for row in _rows(_base(authority.GRAPH_EVIDENCE))
    }["CYS_SG_SAMPLE_INDEX_000005"]
    assert evidence["ligand_comp_id"] == "ZYA"
    assert evidence["reaction_delta_class"] == "covalent_leaving_group_loss"
    assert evidence["leaving_group_atom_ids"] == "F1"
    assert evidence["parent_leaving_group_bond_verified"] == "True"
    assert evidence["atom_inventory_reconciliation_status"] == (
        "validated_post_covalent_leaving_group_loss"
    )
    assert evidence["parent_ccd_heavy_atom_count"] == "29"
    assert evidence["observed_post_covalent_heavy_atom_count"] == "28"
    assert evidence["heavy_atom_count_delta"] == "-1"
    f1_atoms = [
        row for row in _rows(_base(authority.PARENT_ATOMS))
        if row["ligand_comp_id"] == "ZYA" and row["ccd_atom_id"] == "F1"
    ]
    assert len(f1_atoms) == 1
    assert f1_atoms[0]["ccd_type_symbol"] == "F"
    f1_bonds = [
        row for row in _rows(_base(authority.PARENT_BONDS))
        if row["ligand_comp_id"] == "ZYA"
        and "F1" in (row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"])
    ]
    assert f1_bonds
    projected = [
        row for row in _artifact_rows(authority.BOND_FILE)
        if row["sample_index_row_id"] == "CYS_SG_SAMPLE_INDEX_000005"
        and "F1" in (row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"])
    ]
    assert len(projected) == len(f1_bonds) == 1
    assert projected[0]["projection_disposition"] == (
        "verified_leaving_group_endpoint_missing"
    )
    assert not _bool(projected[0]["projected_to_observed_graph"])


def test_projected_bond_classification_and_endpoint_indices() -> None:
    rows = _artifact_rows(authority.BOND_FILE)
    assert len(rows) == 337
    dispositions = Counter(row["projection_disposition"] for row in rows)
    assert dispositions == {
        "retained_observed_bond": 336,
        "verified_leaving_group_endpoint_missing": 1,
    }
    for row in rows:
        projected = _bool(row["projected_to_observed_graph"])
        left_valid = _bool(row["retained_heavy_local_index_1_valid"])
        right_valid = _bool(row["retained_heavy_local_index_2_valid"])
        if projected:
            assert left_valid and right_valid
            assert row["retained_heavy_local_index_1"]
            assert row["retained_heavy_local_index_2"]
        else:
            assert left_valid != right_valid
            assert row["projection_disposition"] == (
                "verified_leaving_group_endpoint_missing"
            )


def test_observed_graphs_are_connected_deterministic_and_order_invariant() -> None:
    result = authority.build_projection_result(ROOT)
    assert result.transaction_succeeded
    assert len(result.sample_graph_sha256) == 11
    assert result.parent_expanded_atom_count == 324
    assert result.parent_expanded_bond_count == 337
    assert result.projected_bond_count == 336
    assert result.verified_leaving_group_bond_count == 1
    assert result.missing_parent_atom_count == 1
    assert result.unexplained_missing_parent_atom_count == 0
    atoms = (("C2", "C", 0), ("C1", "C", 0), ("O1", "O", -1))
    bonds = (("C2", "O1", "single"), ("C1", "C2", "double"))
    sha = authority.canonical_observed_graph_sha256(atoms, bonds)
    assert sha == authority.canonical_observed_graph_sha256(reversed(atoms), bonds)
    assert sha == authority.canonical_observed_graph_sha256(atoms, reversed(bonds))


def test_readiness_is_graph_positive_and_downstream_fail_closed() -> None:
    rows = _artifact_rows(authority.READINESS_FILE)
    assert len(rows) == 11
    for row in rows:
        for field in (
            "parent_component_graph_authority_available",
            "observed_atom_projection_exact",
            "observed_projected_graph_available",
            "parent_graph_valid",
            "observed_graph_valid",
            "pre_reaction_connectivity_available",
            "pre_reaction_bond_order_available",
            "reactive_ligand_atom_available",
            "retained_local_index_contiguous",
        ):
            assert _bool(row[field])
        for field in (
            "reaction_family_label_available",
            "approved_warhead_rule_available",
            "role_proposal_available",
            "minimal_seed_proposal_available",
            "human_gold_review_completed",
            "ready_for_mask_materialization",
            "ready_for_tensorization",
            "ready_for_model_integration",
            "ready_for_training",
        ):
            assert not _bool(row[field])
        assert row["planned_covalent_model_module_count"] == "5"
        assert row["integrated_covalent_model_module_count"] == "0"
        assert len(row["observed_graph_sha256"]) == 64


def test_transaction_never_materializes_partial_mapping_or_bonds() -> None:
    sample_mapping = ({"row": "mapping"},)
    sample_bonds = ({"row": "bond"},)
    assert authority.transaction_tables(
        True, True, sample_mapping, sample_bonds
    ) == (sample_mapping, sample_bonds)
    assert authority.transaction_tables(
        False, True, sample_mapping, sample_bonds
    ) == ((), ())
    assert authority.transaction_tables(
        True, False, sample_mapping, sample_bonds
    ) == ((), ())


def test_builder_failure_writes_header_only_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def blocked(_repo_root: Path):
        raise ValueError("atom_row_coverage_incomplete")

    monkeypatch.setattr(authority, "build_projection_result", blocked)
    payloads = authority.build_evidence_payloads(ROOT)
    assert len(_rows(payloads[authority.MAPPING_FILE])) == 0
    assert len(_rows(payloads[authority.BOND_FILE])) == 0
    manifest = json.loads(payloads[authority.MANIFEST_FILE])
    assert manifest["transaction_succeeded"] is False
    assert manifest["transaction_blocking_reasons"] == [
        "atom_row_coverage_incomplete"
    ]
    assert manifest["recommended_next_step"] == (
        "resolve_covapie_current11_observed_atom_row_authority_blockers_v1"
    )


@pytest.mark.parametrize(
    ("case", "field", "value", "reason"),
    [
        (case, mutation[0], mutation[1], mutation[2])
        for case, mutation in authority.FAILURE_MUTATIONS.items()
    ],
)
def test_failure_mutations_are_exact_typed_unique_and_fail_closed(
    case: str, field: str, value: object, reason: str
) -> None:
    baseline = authority.BASELINE_SCENARIO
    old = getattr(baseline, field)
    assert type(old) is type(value)
    assert old != value
    scenario = dataclasses.replace(baseline, **{field: value})
    observation = authority.observe_failure_scenario(scenario)
    assert reason in observation.reasons, case
    assert observation.fails_closed
    assert not observation.ready_for_reaction_family_rule_design
    assert not observation.ready_for_role_proposal_generation
    assert not observation.ready_for_mask_materialization
    assert not observation.ready_for_model_integration
    assert not observation.ready_for_training


def test_failure_matrix_has_unique_signatures_and_all_required_cases() -> None:
    rows = _artifact_rows(authority.FAILURE_FILE)
    assert len(rows) == len(authority.FAILURE_MUTATIONS) == 24
    assert {row["failure_case"] for row in rows} == set(authority.FAILURE_MUTATIONS)
    assert len({row["mutation_signature"] for row in rows}) == 24
    for row in rows:
        assert _bool(row["expected_reasons_verified"])
        assert _bool(row["fails_closed"])
        assert _bool(row["verified"])
        assert row["expected_reasons"] in row["observed_reasons"].split(";")
        assert not _bool(row["ready_for_training"])


def test_manifest_is_direct_evidence_bound_without_self_hash() -> None:
    manifest = _manifest()
    assert manifest["transaction_succeeded"] is True
    assert manifest["current11_sample_count"] == 11
    assert manifest["unique_component_count"] == 9
    assert manifest["parent_sample_expanded_heavy_atom_count"] == 324
    assert manifest["observed_retained_heavy_atom_count"] == 323
    assert manifest["exact_mapping_count"] == 323
    assert manifest["element_exact_match_count"] == 323
    assert manifest["reactive_ligand_atom_count"] == 11
    assert manifest["missing_parent_atom_count"] == 1
    assert manifest["unexplained_missing_parent_atom_count"] == 0
    assert manifest["parent_sample_expanded_bond_count"] == 337
    assert manifest["projected_observed_bond_count"] == 336
    assert manifest["observed_graph_valid_count"] == 11
    assert manifest["reaction_family_label_available_count"] == 0
    assert manifest["approved_warhead_rule_available_count"] == 0
    assert manifest["role_proposal_available_count"] == 0
    assert manifest["minimal_seed_proposal_available_count"] == 0
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["ready_for_training"] is False
    assert authority.MANIFEST_FILE not in manifest["output_sha256"]
    for name in authority.OUTPUT_FILES[:-1]:
        payload = (ROOT / authority.OUTPUT_ROOT / name).read_bytes()
        assert manifest["output_sha256"][name] == hashlib.sha256(payload).hexdigest()


def test_builder_is_byte_deterministic_and_matches_materialized_files() -> None:
    first = authority.build_evidence_payloads(ROOT)
    second = authority.build_evidence_payloads(ROOT)
    assert first == second
    assert tuple(first) == authority.OUTPUT_FILES
    for name, payload in first.items():
        assert payload == (ROOT / authority.OUTPUT_ROOT / name).read_bytes()


def test_independent_checker_reconstructs_authority() -> None:
    result = checker.check()
    assert result["lifecycle"] in lifecycle.LIFECYCLES
    assert result["mapping_count"] == 323
    assert result["parent_expanded_atom_count"] == 324
    assert result["parent_expanded_bond_count"] == 337
    assert result["projected_bond_count"] == 336
    assert result["leaving_group_bond_count"] == 1
    assert result["graph_count"] == 11
    assert result["failure_count"] == 24


def test_six_data_artifacts_remain_byte_frozen() -> None:
    built = authority.build_evidence_payloads(ROOT)
    assert set(built) == set(FROZEN_DATA_SHA256)
    for name, expected_sha in FROZEN_DATA_SHA256.items():
        materialized = (ROOT / authority.OUTPUT_ROOT / name).read_bytes()
        assert built[name] == materialized
        assert hashlib.sha256(materialized).hexdigest() == expected_sha


def test_shared_hermetic_lifecycle_exact4(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.environ.get(NESTED_LIFECYCLE_ENV) == "1":
        production_state = authority.validate_execution_boundary_v2(ROOT)
        checker_state = checker.validate_execution_boundary_independent()
        assert production_state == checker_state
        assert production_state in lifecycle.LIFECYCLES
        built = authority.build_evidence_payloads(ROOT)
        for name, expected_sha in FROZEN_DATA_SHA256.items():
            assert hashlib.sha256(built[name]).hexdigest() == expected_sha
        return

    reference_payloads = {
        name: (ROOT / authority.OUTPUT_ROOT / name).read_bytes()
        for name in authority.OUTPUT_FILES
    }
    real_capture = lifecycle._capture_state
    observed_states: list[str] = []
    targeted_counts: list[int] = []
    checker_outputs: list[bytes] = []

    def capture(repository: Path, **kwargs):
        state = real_capture(repository, **kwargs)
        assert authority.validate_execution_boundary_v2(repository) == state.lifecycle
        built = authority.build_evidence_payloads(repository)
        for name, reference in reference_payloads.items():
            assert built[name] == reference
            assert (repository / authority.OUTPUT_ROOT / name).read_bytes() == reference

        environment = {
            **os.environ,
            NESTED_LIFECYCLE_ENV: "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": "src",
        }
        targeted = subprocess.run(
            (
                sys.executable, "-B", "-m", "pytest", "-q",
                "-p", "no:cacheprovider", checker.EXACT10[1].as_posix(),
            ),
            cwd=repository,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            check=False,
        )
        assert targeted.returncode == 0, targeted.stdout + targeted.stderr
        assert targeted.stderr == b""
        match = re.search(rb"(\d+) passed", targeted.stdout)
        assert match
        targeted_counts.append(int(match.group(1)))
        checked = subprocess.run(
            (sys.executable, "-B", checker.EXACT10[2].as_posix()),
            cwd=repository,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            check=False,
        )
        assert checked.returncode == 0, checked.stdout + checked.stderr
        assert checked.stderr == b""
        observed_states.append(state.lifecycle)
        checker_outputs.append(checked.stdout)
        return state

    monkeypatch.setattr(lifecycle, "_capture_state", capture)
    report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
        ROOT,
        tmp_path,
        base_commit=authority.BASE_COMMIT,
        formal_commit_subject=authority.FORMAL_COMMIT_SUBJECT,
        exact_paths=authority.EXACT10_PATHS,
    )
    assert observed_states == list(lifecycle.LIFECYCLES)
    assert len(set(targeted_counts)) == 1
    assert len(set(checker_outputs)) == 1
    assert report.candidate_parent == authority.BASE_COMMIT
    assert report.candidate_subject == authority.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert report.cleanup_verified is True
    assert tuple(tmp_path.iterdir()) == ()


def test_isolated_import_has_no_output_or_file_side_effects() -> None:
    before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (ROOT / authority.OUTPUT_ROOT).iterdir()
        if path.is_file()
    }
    code = (
        "import sys;"
        f"sys.path.insert(0,{str(ROOT / 'src')!r});"
        "import covalent_ext."
        "covapie_current11_observed_to_parent_atom_projection_authority_v1"
    )
    result = subprocess.run(
        (sys.executable, "-B", "-c", code),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 0
    assert result.stdout == b""
    assert result.stderr == b""
    after = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (ROOT / authority.OUTPUT_ROOT).iterdir()
        if path.is_file()
    }
    assert after == before


def test_exact10_scope_and_protected_source_safety() -> None:
    assert authority.EXACT10_PATHS == checker.EXACT10
    assert len(authority.EXACT10_PATHS) == 10
    assert authority.OUTPUT_FILES == (
        "covapie_observed_atom_projection_source_inventory.csv",
        "covapie_current11_observed_to_parent_atom_mapping_authority.csv",
        "covapie_current11_parent_and_observed_projected_bond_authority.csv",
        "covapie_current11_observed_projection_readiness_matrix.csv",
        "covapie_current11_observed_projection_failure_matrix.csv",
        "covapie_current11_observed_to_parent_atom_projection_authority_manifest.json",
    )
    protected = (
        "data/raw", "checkpoints", "equivariant_diffusion",
        "lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py",
    )
    changed = set(_git("diff", "--name-only").decode().splitlines())
    changed |= set(_git("diff", "--cached", "--name-only").decode().splitlines())
    assert not any(
        path == prefix or path.startswith(prefix.rstrip("/") + "/")
        for path in changed for prefix in protected
    )
    source = Path(authority.__file__).read_text(encoding="utf-8")
    assert "COVAPIE_SKIP_CURRENT_TREE_BOUNDARY" not in source
    assert "SKIP_CURRENT_TREE" not in source
