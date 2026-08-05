"""Tests for the Current11 dataset partial-supervision routing sidecar."""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import inspect
import io
import json
import os
import shutil
import stat
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
MODULE_NAME = "covalent_ext.covapie_current11_dataset_partial_supervision_routing_sidecar_v1"
CHECKER = ROOT / "scripts/check_covapie_current11_dataset_partial_supervision_routing_sidecar_v1.py"


def _module():
    return importlib.import_module(MODULE_NAME)


def _build():
    return _module().build_covapie_current11_dataset_partial_supervision_routing_sidecar_v1(
        repo_root=ROOT, state_root=STATE
    )


def _rows(payload: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    return tuple(reader.fieldnames or ()), list(reader)


def _manifest(artifacts: dict[str, bytes]) -> dict[str, object]:
    return json.loads(artifacts["current11_dataset_partial_supervision_routing_manifest.json"])


def _contract_inputs(artifacts: dict[str, bytes]):
    module = _module()
    manifest = _manifest(artifacts)
    _record_fields, records = _rows(artifacts[module.ARTIFACT_NAMES[0]])
    record_boolean_fields = {
        "direct_authority_found", "dedicated_transformation_review_available",
        "availability_mask_required", "current_runtime_consumer_available",
        "training_loss_authorized",
    }
    typed_records = [
        {
            key: value == "true" if key in record_boolean_fields else value
            for key, value in record.items()
        }
        for record in records
    ]
    task_fields, task_rows = _rows(artifacts[module.ARTIFACT_NAMES[1]])
    typed_tasks = [
        {
            key: (
                value == "true" if key in task_fields[-2:]
                else int(value) if key in task_fields[1:9]
                else value
            )
            for key, value in row.items()
        }
        for row in task_rows
    ]
    sample_fields, sample_rows = _rows(artifacts[module.ARTIFACT_NAMES[2]])
    typed_samples = [
        {
            key: (
                value == "true" if key in sample_fields[11:]
                else int(value) if key in sample_fields[3:11]
                else value
            )
            for key, value in row.items()
        }
        for row in sample_rows
    ]
    assert typed_tasks == manifest["task_coverage_summary"]
    assert typed_samples == manifest["sample_coverage_summary"]
    return manifest, typed_records, typed_tasks, typed_samples


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return _build()


def test_public_api_is_unique_keyword_only_and_silent_import(capsys: pytest.CaptureFixture[str]) -> None:
    module = importlib.reload(_module())
    assert capsys.readouterr() == ("", "")
    assert module.__all__ == (
        "build_covapie_current11_dataset_partial_supervision_routing_sidecar_v1",
    )
    signature = inspect.signature(module.build_covapie_current11_dataset_partial_supervision_routing_sidecar_v1)
    assert tuple(signature.parameters) == ("repo_root", "state_root")
    assert all(item.kind is inspect.Parameter.KEYWORD_ONLY for item in signature.parameters.values())


def test_module_imports_are_stdlib_or_local() -> None:
    tree = ast.parse((ROOT / _module().MODULE_PATH).read_text(encoding="utf-8"))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module != "__future__":
            roots.add((node.module or "").split(".")[0])
    assert roots <= set(sys.stdlib_module_names) | {"covalent_ext"}
    assert not {"torch", "rdkit", "openbabel"} & roots


def test_double_build_is_exact4_and_byte_identical(artifacts: dict[str, bytes]) -> None:
    assert artifacts == _build()
    assert tuple(artifacts) == _module().ARTIFACT_NAMES
    assert len(artifacts) == 4


def test_artifact_encoding_newlines_and_manifest_determinism(artifacts: dict[str, bytes]) -> None:
    for payload in artifacts.values():
        assert len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf")
        assert b"\0" not in payload and b"\r" not in payload
        assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
        payload.decode("utf-8")
    manifest_payload = artifacts[_module().ARTIFACT_NAMES[3]]
    parsed = json.loads(manifest_payload)
    assert manifest_payload == (
        json.dumps(parsed, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    ).encode()


def test_records_exact275_order_headers_and_boolean_contract(artifacts: dict[str, bytes]) -> None:
    fields, rows = _rows(artifacts[_module().ARTIFACT_NAMES[0]])
    assert fields == _module().RECORD_FIELDS
    assert len(rows) == 275
    for position, sample in enumerate(_module().EXPECTED_SAMPLES):
        block = rows[position * 25:(position + 1) * 25]
        assert [row["semantic_task_name"] for row in block] == list(_module().SEMANTIC_TASK_NAMES)
        assert {(row["sample_index_row_id"], row["pdb_id"], row["ligand_comp_id"]) for row in block} == {sample}
    assert {row["eligibility_state"] for row in rows} <= set(_module().ELIGIBILITY_STATE_VOCABULARY)
    assert {row["availability_mask_required"] for row in rows} == {"true"}
    assert {row["current_runtime_consumer_available"] for row in rows} == {"false"}
    assert {row["training_loss_authorized"] for row in rows} == {"false"}
    assert all(not any(value.startswith("/") for value in json.loads(row["supporting_source_ids_json"])) for row in rows)


def test_global_counts_and_task_coverage(artifacts: dict[str, bytes]) -> None:
    _fields, records = _rows(artifacts[_module().ARTIFACT_NAMES[0]])
    assert Counter(row["eligibility_state"] for row in records) == Counter(_module().EXPECTED_GLOBAL_COUNTS)
    fields, rows = _rows(artifacts[_module().ARTIFACT_NAMES[1]])
    assert fields == _module().TASK_COVERAGE_FIELDS
    assert len(rows) == 25
    assert [row["semantic_task_name"] for row in rows] == list(_module().SEMANTIC_TASK_NAMES)
    assert all(sum(int(row[field]) for field in fields[1:8]) == 11 for row in rows)
    assert {row["total_sample_count"] for row in rows} == {"11"}
    assert {row["current_runtime_consumer_available"] for row in rows} == {"false"}
    assert {row["training_loss_authorized"] for row in rows} == {"false"}


def test_sample_coverage_exact11_and_dedicated_two_of_nine(artifacts: dict[str, bytes]) -> None:
    fields, rows = _rows(artifacts[_module().ARTIFACT_NAMES[2]])
    assert fields == _module().SAMPLE_COVERAGE_FIELDS
    assert [(row["sample_index_row_id"], row["pdb_id"], row["ligand_comp_id"]) for row in rows] == list(_module().EXPECTED_SAMPLES)
    assert all(sum(int(row[field]) for field in fields[3:10]) == 25 for row in rows)
    assert {row["total_task_count"] for row in rows} == {"25"}
    dedicated = [row["sample_index_row_id"] for row in rows if row["dedicated_transformation_review_available"] == "true"]
    assert dedicated == [_module().EXPECTED_SAMPLES[7][0], _module().EXPECTED_SAMPLES[9][0]]
    for row in rows:
        assert row["dataset_level_routing_derivable"] == "true"
        assert row["current_runtime_consumer_available"] == "false"
        assert row["training_loss_authorized"] == "false"
        assert row["ready_for_tensor_materialization"] == "false"
        assert row["ready_for_training"] == "false"


def test_unit_exact50_parity_and_sample_differences(artifacts: dict[str, bytes]) -> None:
    manifest = _manifest(artifacts)
    assert manifest["unit_000001_parity"] == {
        "passed": True,
        "routing_record_count": 50,
        "sample_index_row_ids": [_module().EXPECTED_SAMPLES[7][0], _module().EXPECTED_SAMPLES[9][0]],
        "state_counts": {
            "admissible_now": 8,
            "admissible_as_observed_geometry_only": 2,
            "candidate_only_not_authoritative": 10,
            "blocked_missing_evidence": 13,
            "blocked_state_ambiguity": 7,
            "blocked_missing_human_approval": 10,
            "not_applicable": 0,
        },
    }
    _fields, rows = _rows(artifacts[_module().ARTIFACT_NAMES[0]])
    lookup = {(row["sample_index_row_id"], row["semantic_task_name"]): row for row in rows}
    assert lookup[(_module().EXPECTED_SAMPLES[7][0], "broken_edge_supervision")]["eligibility_state"] == "candidate_only_not_authoritative"
    assert lookup[(_module().EXPECTED_SAMPLES[7][0], "reversibility_supervision")]["eligibility_state"] == "candidate_only_not_authoritative"
    assert lookup[(_module().EXPECTED_SAMPLES[9][0], "broken_edge_supervision")]["eligibility_state"] == "blocked_state_ambiguity"
    assert lookup[(_module().EXPECTED_SAMPLES[9][0], "reversibility_supervision")]["eligibility_state"] == "blocked_missing_evidence"


def test_unit_record_lineage_and_published_binding_are_exact(
    artifacts: dict[str, bytes],
) -> None:
    module = _module()
    manifest = _manifest(artifacts)
    _fields, rows = _rows(artifacts[module.ARTIFACT_NAMES[0]])
    bindings = manifest["source_bindings"]
    expected_binding = {
        "source_kind": "published_derived_gate",
        "public_api": "evaluate_covapie_current11_unit_000001_partial_supervision_routing_gate_v1",
        "schema_version": "covapie_current11_unit_000001_partial_supervision_routing_gate_v1",
        "module_source_id": "unit_000001_gate_module",
        "state_projection_sha256": module.UNIT_STATE_PROJECTION_SHA256,
        "formal_candidate_commit": module.BASE_COMMIT,
        "lifecycle_profile": "partial_supervision_routing_gate_published_successor",
        "read_only": True,
    }
    assert bindings["published_unit_000001_gate"] == expected_binding
    for row in rows:
        sources = json.loads(row["supporting_source_ids_json"])
        expected_count = 1 if row["sample_index_row_id"] in module.UNIT_SAMPLE_IDS else 0
        assert sources.count("published_unit_000001_gate") == expected_count
        assert len(sources) == len(set(sources))
        assert all(not Path(source_id).is_absolute() for source_id in sources)
        assert set(sources) <= set(bindings)
        assert row["supporting_source_ids_json"] == json.dumps(
            sources, separators=(",", ":"), ensure_ascii=True
        )
    lookup = {(row["sample_index_row_id"], row["semantic_task_name"]): row for row in rows}
    focus_tasks = (
        (module.EXPECTED_SAMPLES[7][0], "broken_edge_supervision"),
        (module.EXPECTED_SAMPLES[7][0], "reversibility_supervision"),
        (module.EXPECTED_SAMPLES[7][0], "post_covalent_geometry_supervision"),
        (module.EXPECTED_SAMPLES[9][0], "broken_edge_supervision"),
        (module.EXPECTED_SAMPLES[9][0], "post_covalent_geometry_supervision"),
    )
    assert all(
        "published_unit_000001_gate"
        in json.loads(lookup[key]["supporting_source_ids_json"])
        for key in focus_tasks
    )


def test_other9_routes_do_not_inherit_unit_ambiguity(artifacts: dict[str, bytes]) -> None:
    _fields, rows = _rows(artifacts[_module().ARTIFACT_NAMES[0]])
    other = [row for row in rows if row["sample_index_row_id"] not in _module().UNIT_SAMPLE_IDS]
    by_task = {task: {row["eligibility_state"] for row in other if row["semantic_task_name"] == task} for task in _module().SEMANTIC_TASK_NAMES}
    for task in ("post_covalent_geometry_supervision", "complete_post_state_graph_supervision", "full_transformation_supervision", "reversibility_supervision"):
        assert by_task[task] == {"blocked_missing_evidence"}
    for task in ("formed_edge_supervision", "broken_edge_supervision", "leaving_group_supervision"):
        assert by_task[task] == {"candidate_only_not_authoritative"}


def test_exact5_including_b3_and_closed_vocabularies(artifacts: dict[str, bytes]) -> None:
    manifest = _manifest(artifacts)
    assert [(row["semantic_name"], row["display_alias"]) for row in manifest["canonical_mask_semantics"]] == list(_module().CANONICAL_MASK_SEMANTICS)
    assert manifest["eligibility_state_vocabulary"] == list(_module().ELIGIBILITY_STATE_VOCABULARY)
    assert manifest["blocking_reason_vocabulary"] == list(_module().BLOCKING_REASON_VOCABULARY)
    assert manifest["evidence_scope_vocabulary"] == list(_module().EVIDENCE_SCOPE_VOCABULARY)
    _fields, rows = _rows(artifacts[_module().ARTIFACT_NAMES[0]])
    mask_rows = [row for row in rows if row["semantic_task_name"].startswith("canonical_mask_")]
    assert len(mask_rows) == 55
    assert {row["eligibility_state"] for row in mask_rows} == {"blocked_missing_human_approval"}


def test_observed_geometry_is_not_promoted(artifacts: dict[str, bytes]) -> None:
    _fields, rows = _rows(artifacts[_module().ARTIFACT_NAMES[0]])
    observed = [row for row in rows if row["semantic_task_name"] == "observed_complex_geometry_supervision"]
    assert len(observed) == 11
    assert {row["eligibility_state"] for row in observed} == {"admissible_as_observed_geometry_only"}
    assert {row["blocking_reason_code"] for row in observed} == {"OBSERVED_COMPLEX_GEOMETRY_ONLY"}
    for task in ("pre_covalent_geometry_supervision", "post_covalent_geometry_supervision", "complete_post_state_graph_supervision"):
        assert not any(row["semantic_task_name"] == task and row["eligibility_state"].startswith("admissible") for row in rows)


def test_manifest_excludes_own_sha_and_readiness_is_fail_closed(artifacts: dict[str, bytes]) -> None:
    manifest = _manifest(artifacts)
    assert set(manifest["sidecar_files_excluding_manifest"]) == set(_module().ARTIFACT_NAMES[:3])
    assert _module().ARTIFACT_NAMES[3] not in json.dumps(manifest["sidecar_files_excluding_manifest"])
    readiness = manifest["readiness"]
    assert readiness["dataset_partial_supervision_routing_sidecar_implemented"] is True
    assert readiness["ready_for_sidecar_validation"] is True
    assert readiness["feature_semantics_reaudit_required_before_training"] is True
    false_keys = {
        "runtime_consumer_available", "training_loss_authorized", "tensor_materialized",
        "ready_for_formal_sidecar_materialization", "ready_for_tensor_materialization",
        "ready_for_dataloader_integration", "ready_for_model_integration", "ready_for_training",
    }
    assert all(readiness[key] is False for key in false_keys)


def test_checker_double_run_success_is_frozen(artifacts: dict[str, bytes]) -> None:
    command = [sys.executable, str(CHECKER), "--repo-root", str(ROOT), "--state-root", str(STATE)]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    first = subprocess.run(command, check=False, capture_output=True, env=env)
    second = subprocess.run(command, check=False, capture_output=True, env=env)
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout and first.stdout.count(b"\n") == 1
    output = json.loads(first.stdout)
    assert output["artifact_file_count"] == 4
    assert output["record_count"] == 275


@pytest.mark.parametrize(
    "arguments",
    (
        (),
        ("--repo-root", str(ROOT)),
        ("--state-root", str(STATE)),
        ("-h",),
        ("--help",),
        ("--unknown-option",),
        ("--output-dir",),
        ("--write",),
        ("--materialize",),
        ("--approve",),
        ("--tensorize",),
        ("--train",),
        ("--repo-root", str(ROOT), "--state-root", str(STATE), "extra-positional"),
    ),
    ids=(
        "no_arguments", "repo_only", "state_only", "short_help", "long_help",
        "unknown_option", "output_dir", "write", "materialize", "approve",
        "tensorize", "train", "extra_positional",
    ),
)
def test_checker_all_invalid_invocations_fail_closed(arguments: tuple[str, ...]) -> None:
    result = subprocess.run(
        [sys.executable, str(CHECKER), *arguments],
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    expected_error = b"ERROR " + _module().ERROR_TOKEN.encode("ascii") + b"\n"
    assert result.returncode == 1
    assert result.stdout == b""
    assert result.stderr == expected_error


def test_source_snapshot_read_only(artifacts: dict[str, bytes]) -> None:
    manifest = _manifest(artifacts)
    for binding in manifest["source_bindings"].values():
        if "relative_path" not in binding:
            continue
        root = ROOT if binding["root"] == "repo_root" else STATE
        payload = (root / binding["relative_path"]).read_bytes()
        assert len(payload) == binding["bytes"]
        assert hashlib.sha256(payload).hexdigest() == binding["sha256"]
        assert binding["read_only"] is True


def test_current_repository_matches_current_lifecycle() -> None:
    module = _module()
    facts = module._collect_lifecycle(ROOT)
    lifecycle = module._derive_lifecycle(facts)
    assert lifecycle["lifecycle_profile"] in {
        "dataset_partial_supervision_sidecar_precommit_candidate",
        "dataset_partial_supervision_sidecar_committed_unpushed",
        "dataset_partial_supervision_sidecar_published_successor",
    }
    assert facts["branch"] == "main"
    assert facts["base_ancestor_head"] is facts["base_ancestor_origin"] is True
    if lifecycle["lifecycle_profile"].endswith("precommit_candidate"):
        assert facts["head"] == facts["origin"] == module.BASE_COMMIT
        assert facts["untracked"] == module.CANDIDATE_PATHS
    elif lifecycle["lifecycle_profile"].endswith("committed_unpushed"):
        assert facts["head"] == lifecycle["formal_candidate_commit"]
        assert facts["origin"] == module.BASE_COMMIT
        assert (facts["ahead"], facts["behind"]) == (1, 0)
    else:
        assert lifecycle["formal_candidate_commit"]


def test_candidate_file_safety() -> None:
    module = _module()
    assert len(module.CANDIDATE_PATHS) == 4
    for relative in module.CANDIDATE_PATHS:
        path = ROOT / relative
        metadata = path.lstat()
        payload = path.read_bytes()
        assert not path.is_symlink() and stat.S_ISREG(metadata.st_mode)
        assert stat.S_IMODE(metadata.st_mode) == 0o644
        assert len(payload) < 1024 * 1024 and not payload.startswith(b"\xef\xbb\xbf")
        assert b"\0" not in payload


def test_lifecycle_exact3_in_base_anchored_temporary_git(
    tmp_path: Path, request: pytest.FixtureRequest,
) -> None:
    module = _module()
    repository = tmp_path / ROOT.name
    node = f"{module.TEST_PATH}::test_current_repository_matches_current_lifecycle"

    def cleanup() -> None:
        if repository.exists():
            shutil.rmtree(repository)

    request.addfinalizer(cleanup)
    subprocess.run(
        ("git", "clone", "--no-hardlinks", "--quiet", str(ROOT), str(repository)),
        cwd=tmp_path, check=True, capture_output=True,
    )

    def git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ("git", *arguments), cwd=repository, check=check,
            capture_output=True, text=True,
        )

    def run_node() -> None:
        completed = subprocess.run(
            (sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", node),
            cwd=repository,
            env={**os.environ, "PYTHONPATH": "src", "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True, text=True, check=False,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert "1 passed" in completed.stdout

    git("checkout", "-B", "main", module.BASE_COMMIT)
    git("update-ref", "refs/remotes/origin/main", module.BASE_COMMIT)
    for relative in module.CANDIDATE_PATHS:
        assert git("cat-file", "-e", f"{module.BASE_COMMIT}:{relative}", check=False).returncode != 0
        target = repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
        os.chmod(target, 0o644)
    run_node()

    git("add", "--", *module.CANDIDATE_PATHS)
    git(
        "-c", "user.name=CovaPIE Test", "-c", "user.email=test@example.invalid",
        "commit", "--quiet", "-m", module.FORMAL_COMMIT_SUBJECT,
    )
    formal = git("rev-parse", "HEAD").stdout.strip()
    assert git("show", "-s", "--format=%P", formal).stdout.split() == [module.BASE_COMMIT]
    run_node()

    git("update-ref", "refs/remotes/origin/main", formal)
    unrelated = repository / "UNRELATED_DATASET_SIDECAR_SUCCESSOR.txt"
    unrelated.write_text("unrelated successor\n", encoding="utf-8")
    os.chmod(unrelated, 0o644)
    git("add", "--", unrelated.name)
    git(
        "-c", "user.name=CovaPIE Test", "-c", "user.email=test@example.invalid",
        "commit", "--quiet", "-m", "unrelated dataset sidecar successor",
    )
    successor = git("rev-parse", "HEAD").stdout.strip()
    git("update-ref", "refs/remotes/origin/main", successor)
    run_node()
    cleanup()
    assert not os.path.lexists(repository)


def test_lifecycle_exact3_derivation() -> None:
    module = _module()
    base_live = {path: {"tracked": False, "mode": "100644", "blob": "a" * 40} for path in module.CANDIDATE_PATHS}
    precommit = {
        "head": module.BASE_COMMIT, "origin": module.BASE_COMMIT, "ahead": 0, "behind": 0,
        "branch": "main", "base_ancestor_head": True, "base_ancestor_origin": True,
        "tracked": (), "staged": (), "untracked": module.CANDIDATE_PATHS,
        "porcelain": tuple(sorted(f"?? {path}" for path in module.CANDIDATE_PATHS)),
        "path_commits": [], "live_paths": base_live,
    }
    assert module._derive_lifecycle(precommit)["lifecycle_profile"] == "dataset_partial_supervision_sidecar_precommit_candidate"
    commit_id = "b" * 40
    tracked_live = {path: {"tracked": True, "mode": "100644", "index_blob": "c" * 40, "blob": "c" * 40} for path in module.CANDIDATE_PATHS}
    commit = {
        "commit": commit_id, "parents": [module.BASE_COMMIT], "subject": module.FORMAL_COMMIT_SUBJECT,
        "changed_paths": module.CANDIDATE_PATHS,
        "changed_statuses": {path: "A" for path in module.CANDIDATE_PATHS},
        "path_modes": {path: "100644" for path in module.CANDIDATE_PATHS},
        "path_blobs": {path: "c" * 40 for path in module.CANDIDATE_PATHS},
        "ancestor_head": True, "ancestor_origin": False,
    }
    committed = {**precommit, "head": commit_id, "ahead": 1, "untracked": (), "porcelain": (), "path_commits": [commit], "live_paths": tracked_live}
    assert module._derive_lifecycle(committed)["lifecycle_profile"] == "dataset_partial_supervision_sidecar_committed_unpushed"
    published = {**committed, "origin": commit_id, "ahead": 0, "path_commits": [{**commit, "ancestor_origin": True}]}
    assert module._derive_lifecycle(published)["lifecycle_profile"] == "dataset_partial_supervision_sidecar_published_successor"


@pytest.mark.parametrize(
    ("task", "state", "dedicated", "expected_reason"),
    [
        ("observed_complex_geometry_supervision", "admissible_as_observed_geometry_only", False, "OBSERVED_COMPLEX_GEOMETRY_ONLY"),
        ("post_covalent_geometry_supervision", "blocked_state_ambiguity", True, "POST_STATE_AMBIGUOUS"),
        ("full_transformation_supervision", "blocked_missing_evidence", False, "FULL_TRANSFORMATION_INCOMPLETE"),
        ("reversibility_supervision", "blocked_missing_evidence", False, "SAMPLE_SPECIFIC_REVERSIBILITY_MISSING"),
    ],
)
def test_closed_reason_projection(task: str, state: str, dedicated: bool, expected_reason: str) -> None:
    scope, reason = _module()._record_metadata(task, state, dedicated)
    assert scope in _module().EVIDENCE_SCOPE_VOCABULARY
    assert reason == expected_reason and reason in _module().BLOCKING_REASON_VOCABULARY


@pytest.mark.parametrize(
    "mutation",
    [
        lambda rows: rows.pop(),
        lambda rows: rows.reverse(),
        lambda rows: rows[0].__setitem__("pdb_id", "XXXX"),
        lambda rows: rows.append(dict(rows[0])),
        lambda rows: rows.append({**rows[0], "sample_index_row_id": "CYS_SG_SAMPLE_INDEX_000012"}),
    ],
    ids=("missing_sample", "sample_order", "identity_drift", "duplicate_sample", "twelfth_sample"),
)
def test_sample_identity_fail_closed(mutation) -> None:
    module = _module()
    _fields, rows = _rows((ROOT / module.REPO_SOURCES["canonical_final_index"][0]).read_bytes())
    mutation(rows)
    payload = module._csv_bytes(_fields, rows)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        module._validate_samples(payload)


@pytest.mark.parametrize(
    "states",
    [
        (),
        _module().ELIGIBILITY_STATE_VOCABULARY + (_module().ELIGIBILITY_STATE_VOCABULARY[0],),
        _module().ELIGIBILITY_STATE_VOCABULARY + ("illegal",),
    ],
    ids=("task_or_state_missing", "duplicate_state", "illegal_or_extra_state"),
)
def test_vocabulary_drift_is_not_accepted(states) -> None:
    assert tuple(states) != _module().ELIGIBILITY_STATE_VOCABULARY


@pytest.mark.parametrize("mode", ("missing", "duplicate", "twenty_sixth"))
def test_task_vocabulary_drift_fails_full_builder(
    monkeypatch: pytest.MonkeyPatch, mode: str,
) -> None:
    module = _module()
    tasks = module.SEMANTIC_TASK_NAMES
    changed = tasks[:-1] if mode == "missing" else (
        tasks + (tasks[0],) if mode == "duplicate" else tasks + ("forbidden_task_26",)
    )
    monkeypatch.setattr(module, "SEMANTIC_TASK_NAMES", changed)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _build()


def test_illegal_eligibility_and_observed_post_upgrade_fail_full_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module()
    illegal = dict(module._OTHER9_STATES)
    illegal["sample_identity_supervision"] = "illegal_state"
    monkeypatch.setattr(module, "_OTHER9_STATES", illegal)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _build()
    monkeypatch.undo()
    promoted = dict(module._OTHER9_STATES)
    promoted["post_covalent_geometry_supervision"] = "admissible_as_observed_geometry_only"
    monkeypatch.setattr(module, "_OTHER9_STATES", promoted)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _build()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("explicit_bond_authority_class", "distance_only"),
        ("canonical_record_valid", "false"),
    ],
)
def test_pair_authority_fail_closed(field: str, value: str) -> None:
    module = _module()
    payloads = {key: (ROOT / relative).read_bytes() for key, (relative, _digest) in module.REPO_SOURCES.items() if (ROOT / relative).is_file()}
    samples, _paths = module._validate_samples(payloads["canonical_final_index"])
    _fields, rows = _rows(payloads["canonical_pair_matrix"])
    rows[0][field] = value
    payloads["canonical_pair_matrix"] = module._csv_bytes(_fields, rows)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        module._validate_pair_sources(samples, payloads)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("candidate_match_count", "0"),
        ("candidate_match_count", "2"),
        ("distance_used_for_mapping_selection", "true"),
    ],
)
def test_mapping_fail_closed(field: str, value: str) -> None:
    module = _module()
    payloads = {key: (ROOT / relative).read_bytes() for key, (relative, _digest) in module.REPO_SOURCES.items() if (ROOT / relative).is_file()}
    samples, _paths = module._validate_samples(payloads["canonical_final_index"])
    _fields, rows = _rows(payloads["atom_table_mapping_matrix"])
    rows[0][field] = value
    payloads["atom_table_mapping_matrix"] = module._csv_bytes(_fields, rows)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        module._validate_pair_sources(samples, payloads)


@pytest.mark.parametrize("distance", ("", "nan", "inf"))
def test_observed_distance_fail_closed(distance: str) -> None:
    module = _module()
    payloads = {key: (ROOT / relative).read_bytes() for key, (relative, _digest) in module.REPO_SOURCES.items() if (ROOT / relative).is_file()}
    samples, _paths = module._validate_samples(payloads["canonical_final_index"])
    key = f"observed_pair_table_{samples[0]['sample_index_row_id']}"
    _fields, rows = _rows(payloads[key])
    rows[0]["bond_distance_angstrom"] = distance
    payloads[key] = module._csv_bytes(_fields, rows)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        module._validate_pair_sources(samples, payloads)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("authority_status", "inactive"),
        ("sample_quarantined", True),
        ("pdb_id", "XXXX"),
    ],
)
def test_boundary_fail_closed(field: str, value: object) -> None:
    module = _module()
    samples, _paths = module._validate_samples((ROOT / module.REPO_SOURCES["canonical_final_index"][0]).read_bytes())
    value_json = json.loads((STATE / module.STATE_SOURCES["unified_boundary_authority"][0]).read_bytes())
    value_json["effective_authority_records"][0]["effective_authority_record"][field] = value
    payload = (json.dumps(value_json, separators=(",", ":")) + "\n").encode()
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        module._validate_boundary(samples, payload)


def test_candidate_missing_or_approved_fails_closed() -> None:
    module = _module()
    samples, _paths = module._validate_samples((ROOT / module.REPO_SOURCES["canonical_final_index"][0]).read_bytes())
    payloads = {key: (ROOT / relative).read_bytes() for key, (relative, _digest) in module.REPO_SOURCES.items() if key in {"candidate_family_assignments", "family_rule_authority_binding", "role_input_authority"}}
    _fields, rows = _rows(payloads["candidate_family_assignments"])
    rows[0]["candidate_reaction_family_id"] = ""
    payloads["candidate_family_assignments"] = module._csv_bytes(_fields, rows)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        module._validate_candidates_and_roles(samples, payloads)
    _fields, rows = _rows((ROOT / module.REPO_SOURCES["candidate_family_assignments"][0]).read_bytes())
    rows[0]["training_label_approved"] = "true"
    payloads["candidate_family_assignments"] = module._csv_bytes(_fields, rows)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        module._validate_candidates_and_roles(samples, payloads)


def test_role_authority_upgrade_and_mask_drift_fail_closed() -> None:
    module = _module()
    samples, _paths = module._validate_samples((ROOT / module.REPO_SOURCES["canonical_final_index"][0]).read_bytes())
    payloads = {key: (ROOT / relative).read_bytes() for key, (relative, _digest) in module.REPO_SOURCES.items() if key in {"candidate_family_assignments", "family_rule_authority_binding", "role_input_authority"}}
    _fields, roles = _rows(payloads["role_input_authority"])
    roles[0]["role_seed_human_gold_review_completed"] = "true"
    payloads["role_input_authority"] = module._csv_bytes(_fields, roles)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        module._validate_candidates_and_roles(samples, payloads)
    _fields, masks = _rows((ROOT / module.REPO_SOURCES["canonical_mask_truth_table"][0]).read_bytes())
    for altered in (masks[:3] + masks[4:], masks + [dict(masks[0])]):
        with pytest.raises(ValueError, match=module.ERROR_TOKEN):
            module._validate_masks(module._csv_bytes(_fields, altered))


def test_worklist_missing_candidate_semantics_and_dedicated_spread_fail_closed() -> None:
    module = _module()
    samples, _paths = module._validate_samples((ROOT / module.REPO_SOURCES["canonical_final_index"][0]).read_bytes())
    payloads = {key: (ROOT / relative).read_bytes() for key, (relative, _digest) in module.REPO_SOURCES.items() if key in {"candidate_family_assignments", "family_rule_authority_binding", "role_input_authority"}}
    candidates = module._validate_candidates_and_roles(samples, payloads)
    family = (STATE / module.STATE_SOURCES["formal_family_rule_worklist"][0]).read_bytes()
    transformation = (STATE / module.STATE_SOURCES["formal_transformation_worklist"][0]).read_bytes()
    _fields, rows = _rows(family)
    rows[0]["candidate_leaving_group_summary"] = "not_claimed"
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        module._validate_worklists(samples, candidates, module._csv_bytes(_fields, rows), transformation)
    _fields, rows = _rows(transformation)
    rows[0]["sample_index_row_ids_json"] = json.dumps([item[0] for item in module.EXPECTED_SAMPLES], separators=(",", ":"))
    rows[0]["sample_count"] = "11"
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        module._validate_worklists(samples, candidates, family, module._csv_bytes(_fields, rows))


@pytest.mark.parametrize(
    ("field", "value"),
    (("formed_bond_order", "double"), ("candidate_reaction_delta_class", "[]")),
    ids=("candidate_bond_order_upgraded", "missing_broken_edge_empty_list"),
)
def test_candidate_transformation_semantics_fail_closed(field: str, value: str) -> None:
    module = _module()
    samples, _paths = module._validate_samples((ROOT / module.REPO_SOURCES["canonical_final_index"][0]).read_bytes())
    candidate_payloads = {
        key: (ROOT / relative).read_bytes()
        for key, (relative, _digest) in module.REPO_SOURCES.items()
        if key in {"candidate_family_assignments", "family_rule_authority_binding", "role_input_authority"}
    }
    candidates = module._validate_candidates_and_roles(samples, candidate_payloads)
    family_path = STATE / module.STATE_SOURCES["formal_family_rule_worklist"][0]
    transformation = (STATE / module.STATE_SOURCES["formal_transformation_worklist"][0]).read_bytes()
    fields, rows = _rows(family_path.read_bytes())
    rows[0][field] = value
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        module._validate_worklists(
            samples, candidates, module._csv_bytes(fields, rows), transformation
        )


def test_default_reversibility_and_global_sample_record_fail_full_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module()
    changed = dict(module._OTHER9_STATES)
    changed["reversibility_supervision"] = "candidate_only_not_authoritative"
    monkeypatch.setattr(module, "_OTHER9_STATES", changed)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _build()
    monkeypatch.undo()
    original = module._build_records

    def global_only(*args, **kwargs):
        row = original(*args, **kwargs)[0]
        return [{**row, "global_sample_eligible": True}]

    monkeypatch.setattr(module, "_build_records", global_only)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _build()


@pytest.mark.parametrize(
    "field",
    ("current_runtime_consumer_available", "training_loss_authorized"),
)
def test_record_runtime_or_training_true_fails_full_builder(
    monkeypatch: pytest.MonkeyPatch, field: str,
) -> None:
    module = _module()
    original = module._build_records

    def altered(*args, **kwargs):
        records = original(*args, **kwargs)
        records[0][field] = True
        return records

    monkeypatch.setattr(module, "_build_records", altered)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _build()


def test_sample_tensor_readiness_true_fails_full_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module()
    original = module._coverage

    def altered(records):
        tasks, samples = original(records)
        samples[0]["ready_for_tensor_materialization"] = True
        return tasks, samples

    monkeypatch.setattr(module, "_coverage", altered)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _build()


def test_manifest_self_sha_field_fails_closed(artifacts: dict[str, bytes]) -> None:
    module = _module()
    manifest, records, task_rows, sample_rows = _contract_inputs(artifacts)
    manifest["manifest_sha256"] = "0" * 64
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        module._validate_manifest_contract(manifest, records, task_rows, sample_rows)


@pytest.mark.parametrize("mutation", ("remove_unit", "add_other9", "duplicate_unit"))
def test_published_unit_record_lineage_drift_fails_closed(
    artifacts: dict[str, bytes], mutation: str,
) -> None:
    module = _module()
    manifest, records, task_rows, sample_rows = _contract_inputs(artifacts)
    if mutation == "add_other9":
        record = next(
            row for row in records
            if row["sample_index_row_id"] not in module.UNIT_SAMPLE_IDS
        )
    else:
        record = next(
            row for row in records
            if row["sample_index_row_id"] in module.UNIT_SAMPLE_IDS
        )
    sources = json.loads(record["supporting_source_ids_json"])
    if mutation == "remove_unit":
        sources.remove("published_unit_000001_gate")
    else:
        sources.append("published_unit_000001_gate")
    record["supporting_source_ids_json"] = json.dumps(
        sources, separators=(",", ":"), ensure_ascii=True
    )
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        module._validate_manifest_contract(manifest, records, task_rows, sample_rows)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("formal_candidate_commit", "0" * 40),
        ("lifecycle_profile", "partial_supervision_routing_gate_committed_unpushed"),
        ("state_projection_sha256", "0" * 64),
        ("module_source_id", "coverage_audit_lineage"),
    ),
)
def test_published_unit_binding_drift_fails_closed(
    artifacts: dict[str, bytes], field: str, value: str,
) -> None:
    module = _module()
    manifest, records, task_rows, sample_rows = _contract_inputs(artifacts)
    manifest["source_bindings"]["published_unit_000001_gate"][field] = value
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        module._validate_manifest_contract(manifest, records, task_rows, sample_rows)


def test_frozen_source_sha_drift_fails_closed(tmp_path: Path) -> None:
    module = _module()
    relative = "frozen/source.txt"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(b"changed\n")
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        module._read_frozen(tmp_path, relative, hashlib.sha256(b"original\n").hexdigest())


def test_unit_parity_drift_and_global_count_drift_fail_closed(
    artifacts: dict[str, bytes], monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module()
    from covalent_ext.covapie_current11_unit_000001_partial_supervision_routing_gate_v1 import evaluate_covapie_current11_unit_000001_partial_supervision_routing_gate_v1
    unit = evaluate_covapie_current11_unit_000001_partial_supervision_routing_gate_v1(repo_root=ROOT, state_root=STATE)
    for sample_id in module.UNIT_SAMPLE_IDS:
        altered = json.loads(json.dumps(unit))
        record = next(
            item for item in altered["routing_records"]
            if item["sample_index_row_id"] == sample_id
            and item["semantic_task_name"] == "broken_edge_supervision"
        )
        record["eligibility_state"] = "admissible_now"
        with pytest.raises(ValueError, match=module.ERROR_TOKEN):
            module._unit_records(altered)
    original = module._build_records

    def drifted_records(*args, **kwargs):
        records = original(*args, **kwargs)
        records[0]["eligibility_state"] = "blocked_missing_evidence"
        return records

    monkeypatch.setattr(module, "_build_records", drifted_records)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _build()


def test_coverage_audit_and_unit_source_sha_are_frozen() -> None:
    module = _module()
    coverage_path = STATE / module.STATE_SOURCES["coverage_audit_lineage"][0]
    unit_path = ROOT / module.REPO_SOURCES["unit_000001_gate_module"][0]
    assert hashlib.sha256(coverage_path.read_bytes()).hexdigest() == module.STATE_SOURCES["coverage_audit_lineage"][1]
    assert len(coverage_path.read_bytes()) == 164395 and coverage_path.read_bytes().count(b"\n") == 547
    assert hashlib.sha256(unit_path.read_bytes()).hexdigest() == module.REPO_SOURCES["unit_000001_gate_module"][1]


@pytest.mark.parametrize("key", ("runtime_consumer_available", "training_loss_authorized", "ready_for_tensor_materialization"))
def test_readiness_true_is_rejected_by_contract(key: str) -> None:
    readiness = _module()._readiness()
    assert readiness[key] is False
    readiness[key] = True
    assert readiness != _module()._readiness()
