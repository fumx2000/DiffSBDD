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


MODULE_NAME = (
    "covalent_ext.covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_preconditions_audit"
)
ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
    "covapie-envs/diffsbdd-legacy-test-v1/bin/python3.10"
)
PRODUCTION = ROOT / (
    "src/covalent_ext/covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_preconditions_audit.py"
)
CHECKER = ROOT / (
    "scripts/check_covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_preconditions_audit_v1.py"
)
RUNTIME_ISSUE = ROOT / (
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1/"
    "covapie_admit_001_to_014_runtime_issue_readiness_inventory.csv"
)


@pytest.fixture(scope="module")
def audit():
    return importlib.import_module(MODULE_NAME)


@pytest.fixture(scope="module")
def snapshot(audit):
    return audit.build_frozen_source_snapshot()


@pytest.fixture(scope="module")
def payloads(audit, snapshot):
    return audit.build_artifact_payloads(snapshot)


@pytest.fixture(scope="module")
def checker():
    spec = importlib.util.spec_from_file_location("admit015_revised_checker", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


@pytest.fixture(scope="module")
def checker_sources(checker):
    return checker.attest_exact23()


def _csv(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode())))


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )


def test_base_identity_and_ancestry(audit):
    result = _git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", audit.BASE_COMMIT
    )
    assert result.stdout.splitlines() == [
        audit.BASE_COMMIT, audit.BASE_PARENT, audit.BASE_TREE, audit.BASE_SUBJECT
    ]
    assert _git("merge-base", "--is-ancestor", audit.BASE_COMMIT, "HEAD").returncode == 0


def test_canonical_python_contract(audit):
    assert sys.implementation.name == audit.CANONICAL_PYTHON_IMPLEMENTATION == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    assert audit.NONCANONICAL_PYTHON_POLICY.endswith(
        "artifact_build_checker_and_frozen_ast_forbidden"
    )


def test_source_boundary_git_identity(snapshot):
    assert len(snapshot) == 23
    for item in snapshot:
        index = _git("ls-files", "--stage", "--", item.path.as_posix())
        tree = _git("ls-tree", "f54c0efabfb695653c9e55b3a53bda8cf200f353",
                    "--", item.path.as_posix())
        assert index.returncode == tree.returncode == 0
        assert "\t" + item.path.as_posix() in index.stdout
        assert "\t" + item.path.as_posix() in tree.stdout
        assert item.sha256 == hashlib.sha256(item.content).hexdigest()


def test_source_boundary_is_ordered_and_safe(audit, snapshot):
    assert tuple(item.path for item in snapshot) == audit.SOURCE_PATHS
    assert all(not item.path.is_absolute() and ".." not in item.path.parts
               for item in snapshot)
    assert all(item.path.parts[:2] != ("data", "raw") for item in snapshot)
    assert all(item.path.parts[0] != "checkpoints" for item in snapshot)


def test_admit015_registry_identity(audit, snapshot):
    rows = audit._csv(snapshot, audit.DESIGN_RULES)
    row = next(item for item in rows if item["admission_rule_id"] == "ADMIT_015")
    assert row == {
        "admission_rule_id": "ADMIT_015",
        "admission_rule_name": "current_gate_grants_no_training_permission",
        "evidence_source": "current_design_gate",
        "required_status": "training_not_authorized_now",
        "failure_severity": "blocking",
        "blocking_reason": "training_not_authorized",
        "evaluation_phase": "current_step",
        "network_required": "false",
        "raw_structure_required": "false",
        "ready_for_future_implementation": "true",
    }


def test_exact14_runtime_current_state(audit, snapshot):
    runtime = audit._json(snapshot, audit.RUNTIME_MANIFEST)
    assert runtime["registered_rule_ids"] == [
        f"ADMIT_{index:03d}" for index in range(1, 15)
    ]
    assert runtime["known_not_registered_rule_ids"] == ["ADMIT_015"]
    assert runtime["admit_015_implemented"] is False
    assert runtime["admit_015_registered_in_engine"] is False
    assert "ADMIT_015" not in runtime["callable_discovered_rule_ids"]
    assert "ADMIT_015" not in runtime["adapter_ready_rule_ids"]


def test_coverage_permission_and_execution_count(audit, payloads):
    manifest = json.loads(payloads[audit.MANIFEST])
    assert manifest["issue_coverage"] == ["ADMIT_015"]
    assert manifest["current_permission"] is False
    assert manifest["authorized_admit_015_training_execution_count"] == 0
    assert manifest["issue_transition_count"] == 0


def test_stage_envelope_and_key_coexistence(audit, snapshot):
    contexts = {
        row["context_item"]: row for row in audit._csv(snapshot, audit.PRE_CONTEXT)
    }
    assert contexts["current_stage_download_authorized"]["required_by_rules"] == "ADMIT_014"
    assert contexts["current_stage_training_authorized"]["required_by_rules"] == "ADMIT_015"
    assert contexts["current_stage_download_authorized"]["context_scope"] == "stage"
    assert contexts["current_stage_training_authorized"]["context_scope"] == "stage"


def test_admit014_structural_precedent_is_not_admit015_contract(audit, payloads):
    rows = _csv(payloads[audit.RESPONSIBILITY])
    precedent_rows = [
        row for row in rows
        if row["admit_015_contract_status"]
        == "supported_but_admit015_contract_not_frozen"
    ]
    assert precedent_rows
    assert all("ADMIT_014" in row["committed_precedent"]
               or "Step14AU-A" in row["committed_precedent"]
               for row in precedent_rows)


@pytest.mark.parametrize("item", ["fallback", "alias", "OR", "AND as single permission"])
def test_download_training_key_isolation_forbids_composition(audit, payloads, item):
    rows = {row["responsibility_item"]: row
            for row in _csv(payloads[audit.RESPONSIBILITY])}
    assert rows[item]["admit_015_contract_status"] == "forbidden"
    assert rows[item]["audit_passed"] == "true"


@pytest.mark.parametrize(
    "source",
    [
        "candidate_record", "batch_context", "evaluation_context",
        "download_result_context", "provider_result", "environment_variable",
        "filesystem_marker", "artifact_sha", "git_commit_sha",
        "checkpoint_metadata", "training_config", "command_line_flag",
        "model_state", "dataloader_state",
    ],
)
def test_forbidden_authority_sources(audit, payloads, source):
    manifest = json.loads(payloads[audit.MANIFEST])
    assert source in manifest["forbidden_training_authority_sources"]


def test_precondition_ids_groups_and_statuses(audit, payloads):
    rows = _csv(payloads[audit.PRECONDITION])
    assert [row["precondition_id"] for row in rows] == [
        f"PRE_{index:03d}" for index in range(1, len(rows) + 1)
    ]
    assert len(rows) == 45
    assert {row["completion_status"] for row in rows} == {
        "complete", "incomplete",
        "supported_but_admit015_contract_not_frozen",
    }
    assert all(row["implementation_blocking"] == "true"
               for row in rows if row["completion_status"] != "complete")


@pytest.mark.parametrize(
    "subject",
    [
        "final evaluator signature", "result class name",
        "result field count and order", "outcome vocabulary",
        "reason vocabulary", "unified adapter contract",
        "registry/Exact15 runtime", "training authorization enforcement API",
    ],
)
def test_unresolved_contract_items_remain_open(audit, payloads, subject):
    row = next(item for item in _csv(payloads[audit.PRECONDITION])
               if item["precondition_subject"] == subject)
    assert row["completion_status"] == "incomplete"
    assert row["implementation_blocking"] == "true"


def test_feature_semantics_and_step12d_boundary(audit, snapshot, payloads):
    feature = audit._json(snapshot, audit.FEATURE_MANIFEST)
    step12d = audit._json(snapshot, audit.STEP12D_MANIFEST)
    manifest = json.loads(payloads[audit.MANIFEST])
    assert feature["feature_semantics_known_for_training"] is False
    assert feature["unknown_atom_feature_policy_finalized_for_training"] is False
    assert feature["step12d_was_smoke_legality_only"] is True
    assert step12d["feature_semantics_known"] is False
    assert manifest["feature_semantics_audit_completed"] is False
    assert manifest["step12d_is_final_training_feature_contract"] is False


def test_canonical_five_masks_include_b3(audit, payloads):
    manifest = json.loads(payloads[audit.MANIFEST])
    assert manifest["canonical_masks"] == [
        {"semantic_name": "warhead_only", "alias": "A"},
        {"semantic_name": "linker_plus_warhead", "alias": "B"},
        {"semantic_name": "scaffold_plus_warhead", "alias": "B2"},
        {"semantic_name": "scaffold_only", "alias": "B3"},
        {"semantic_name": "scaffold_plus_linker_plus_warhead", "alias": "C"},
    ]
    assert manifest["canonical_mask_count"] == 5
    assert manifest["canonical_mask_long_names_are_authoritative"] is True


def test_issue_inventory_exact30_and_byte_identity(audit, payloads):
    assert payloads[audit.ISSUE] == RUNTIME_ISSUE.read_bytes()
    rows = _csv(payloads[audit.ISSUE])
    assert len(rows) == 30
    coverage = next(row for row in rows
                    if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert coverage["affected_rules"] == "ADMIT_015"
    assert coverage["successor_effective_status"] == "open"


def test_readiness_exact_truth(audit, payloads):
    manifest = json.loads(payloads[audit.MANIFEST])
    assert all(manifest[key] is True for key in audit.TRUE_READINESS)
    assert all(manifest[key] is False for key in audit.FALSE_READINESS)
    assert manifest["ready_for_training"] is False
    assert manifest["real_training_ready"] is False


def test_no_evaluator_result_adapter_registry_or_enforcement_definitions():
    tree = ast.parse(PRODUCTION.read_text())
    definitions = {node.name for node in ast.walk(tree)
                   if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    assert "evaluate_admit_015" not in definitions
    assert "Admit015EvaluationResult" not in definitions
    assert "_evaluate_registered_admit_015" not in definitions
    assert "evaluate_admission_rule" not in definitions
    assert "EVALUATOR_REGISTRY" not in PRODUCTION.read_text()
    assert "training_authorization_enforcement" not in definitions


def test_no_training_or_model_imports():
    tree = ast.parse(PRODUCTION.read_text())
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert not imports & {
        "torch", "numpy", "pytorch_lightning", "rdkit",
        "equivariant_diffusion", "dataset", "lightning_modules",
    }


def test_deterministic_build(audit, snapshot):
    first = audit.build_artifact_payloads(snapshot)
    second = audit.build_artifact_payloads(snapshot)
    assert first == second
    assert list(first) == list(audit.FILES)


def test_manifest_has_no_self_hash(audit, payloads):
    manifest = json.loads(payloads[audit.MANIFEST])
    assert audit.MANIFEST not in manifest["output_sha256"]
    assert set(manifest["output_sha256"]) == set(audit.FILES[:-1])


def test_materialization_and_inode_preserving_noop(audit, tmp_path):
    root = tmp_path / "audit"
    first = audit.materialize_audit(root)
    inode = {name: (root / name).stat().st_ino for name in audit.FILES}
    second = audit.materialize_audit(root)
    assert first == second
    assert inode == {name: (root / name).stat().st_ino for name in audit.FILES}


def test_existing_mismatch_fails_closed(audit, tmp_path):
    root = tmp_path / "audit"
    audit.materialize_audit(root)
    target = root / audit.SAFETY
    target.write_bytes(target.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="existing output mismatch"):
        audit.materialize_audit(root)


def test_extra_output_fails_closed(audit, tmp_path):
    root = tmp_path / "audit"
    audit.materialize_audit(root)
    (root / "seventh.csv").write_text("unexpected\n")
    with pytest.raises(ValueError, match="existing output mismatch"):
        audit.materialize_audit(root)


def test_missing_output_fails_closed(audit, tmp_path):
    root = tmp_path / "audit"
    audit.materialize_audit(root)
    (root / audit.SAFETY).unlink()
    with pytest.raises(ValueError, match="existing output mismatch"):
        audit.materialize_audit(root)


def test_symlink_output_fails_closed(audit, tmp_path):
    root = tmp_path / "audit"
    audit.materialize_audit(root)
    target = root / audit.SAFETY
    target.unlink()
    target.symlink_to(root / audit.PRECONDITION)
    with pytest.raises(ValueError, match="unsafe output leaf"):
        audit.materialize_audit(root)


def test_eexist_exact_destination_is_noop(audit, tmp_path, monkeypatch):
    root = tmp_path / "audit"
    audit.materialize_audit(root)

    def exists(*_args):
        raise OSError(17, "File exists")

    monkeypatch.setattr(audit, "_rename_noreplace", exists)
    assert audit.materialize_audit(root)["all_checks_passed"] is True


def test_no_os_replace_fallback():
    assert "os.replace" not in PRODUCTION.read_text()


def test_source_mismatch_fails_closed(audit, monkeypatch):
    original = audit.SOURCE_SHA256[audit.DESIGN_RULES]
    monkeypatch.setitem(audit.SOURCE_SHA256, audit.DESIGN_RULES, "0" * 64)
    with pytest.raises(ValueError, match="source content mismatch"):
        audit.build_frozen_source_snapshot()
    assert original != "0" * 64


def test_source_symlink_rejected(audit, tmp_path):
    link = tmp_path / "link"
    link.symlink_to(ROOT / "README.md")
    assert audit._safe_source(link) is False


def test_safety_rows_cover_no_execution(audit, payloads):
    rows = {row["audit_item"]: row for row in _csv(payloads[audit.SAFETY])}
    for item in (
        "dataloader instantiated", "checkpoint loaded",
        "model forward/loss/backward", "optimizer/parameter update",
        "provider/network/download", "raw structure read/write",
    ):
        assert rows[item]["required_state"] == rows[item]["observed_state"] == "false"
        assert rows[item]["audit_passed"] == "true"


def test_candidate_path_is_recommendation_not_contract(audit, payloads):
    manifest = json.loads(payloads[audit.MANIFEST])
    assert manifest["candidate_authoritative_envelope"] == "stage_authorization_context"
    assert manifest["candidate_target_item"] == "current_stage_training_authorized"
    assert manifest["admit_014_coexistence_item"] == "current_stage_download_authorized"
    assert manifest["candidate_path_status"] == (
        "recommended authoritative path pending formal authorization contract"
    )
    assert manifest["admit_015_training_authorization_contract_frozen"] is False


def test_formal_interface_not_frozen_map(audit, payloads):
    not_frozen = json.loads(payloads[audit.MANIFEST])["formal_interface_not_frozen"]
    assert len(not_frozen) == 11
    assert all(not_frozen.values())


def test_exact6_schemas(audit, payloads):
    expected = {
        audit.PRECONDITION: audit.COLUMNS[audit.PRECONDITION],
        audit.RESPONSIBILITY: audit.COLUMNS[audit.RESPONSIBILITY],
        audit.SOURCE_AUDIT: audit.COLUMNS[audit.SOURCE_AUDIT],
        audit.SAFETY: audit.COLUMNS[audit.SAFETY],
    }
    for name, columns in expected.items():
        reader = csv.DictReader(io.StringIO(payloads[name].decode()))
        assert tuple(reader.fieldnames or ()) == columns
        assert list(reader)


def test_manifest_schema_rejects_synchronized_tamper_by_payload_comparison(
    audit, snapshot, payloads
):
    tampered = dict(payloads)
    document = json.loads(tampered[audit.MANIFEST])
    document["ready_for_training"] = True
    tampered[audit.MANIFEST] = (json.dumps(document, indent=2) + "\n").encode()
    assert tampered != audit.build_artifact_payloads(snapshot)


def test_isolated_import_is_silent_and_has_no_output_side_effect(tmp_path):
    code = (
        "import importlib, os;"
        f"importlib.import_module({MODULE_NAME!r});"
        "assert os.listdir('.') == []"
    )
    result = subprocess.run(
        [str(PYTHON), "-c", code], cwd=tmp_path, capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""


def test_checker_ast_is_independent_of_production_rows():
    source = CHECKER.read_text()
    assert "from covalent_ext" not in source
    assert "sources = attest_exact23()" in source
    assert "_verify_candidate_ast()" in source
    assert "_load_production()" in source
    assert source.index("sources = attest_exact23()") < source.index(
        "module = _load_production()"
    )


def test_protected_paths_have_no_diff():
    protected = [
        "data/raw", "checkpoints", "equivariant_diffusion",
        "lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py",
    ]
    assert _git("diff", "--name-only", "--", *protected).stdout == ""
    assert _git("diff", "--cached", "--name-only", "--", *protected).stdout == ""


def test_recommended_next_step_exact(audit, payloads):
    manifest = json.loads(payloads[audit.MANIFEST])
    assert manifest["recommended_next_step"] == (
        "design_covapie_admit_015_training_authorization_contract_v1"
    )


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _replace_same_bytes(path: Path, backup: Path, data: bytes) -> None:
    os.rename(path, backup)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(descriptor, data)
    finally:
        os.close(descriptor)


@pytest.mark.parametrize(
    "race",
    [
        "same_byte_leaf_replacement",
        "unlink_recreate",
        "in_place_write",
        "stat_open_race",
        "parent_replacement",
        "repo_root_replacement",
        "replacement_before_final_leaf_check",
    ],
)
def test_production_source_final_leaf_real_filesystem_races(
    audit, tmp_path, monkeypatch, race
):
    repo = tmp_path / "repo"
    relative = Path("a/b/source.txt")
    leaf = repo / relative
    original = b"committed evidence bytes\n"
    _write_bytes(leaf, original)
    monkeypatch.setattr(audit, "REPO_ROOT", repo)
    original_stat = os.stat
    original_lstat = os.lstat
    original_open = os.open
    original_read = os.read
    leaf_stat_count = 0
    root_lstat_count = 0
    replaced = False

    def replace_leaf() -> None:
        nonlocal replaced
        if replaced:
            return
        replaced = True
        backup = leaf.with_name(f"{leaf.name}.old")
        _replace_same_bytes(leaf, backup, original)

    def wrapped_stat(path, *args, **kwargs):
        nonlocal leaf_stat_count
        if path == relative.name and kwargs.get("dir_fd") is not None:
            leaf_stat_count += 1
            trigger = (
                race in {"same_byte_leaf_replacement", "unlink_recreate"}
                and leaf_stat_count == 2
            ) or (
                race == "replacement_before_final_leaf_check"
                and leaf_stat_count == 3
            )
            if trigger:
                replace_leaf()
            if race == "parent_replacement" and leaf_stat_count == 2:
                old_parent = leaf.parent.with_name("b.old")
                os.rename(leaf.parent, old_parent)
                leaf.parent.mkdir()
                _write_bytes(leaf, original)
        return original_stat(path, *args, **kwargs)

    def wrapped_lstat(path, *args, **kwargs):
        nonlocal root_lstat_count
        if Path(path) == repo:
            root_lstat_count += 1
            if race == "repo_root_replacement" and root_lstat_count == 2:
                old_root = repo.with_name("repo.old")
                os.rename(repo, old_root)
                repo.mkdir()
        return original_lstat(path, *args, **kwargs)

    def wrapped_open(path, flags, *args, **kwargs):
        if (
            race == "stat_open_race"
            and path == relative.name
            and kwargs.get("dir_fd") is not None
        ):
            replace_leaf()
        return original_open(path, flags, *args, **kwargs)

    def wrapped_read(fd, size):
        data = original_read(fd, size)
        if race == "in_place_write" and data == b"" and not replaced:
            descriptor = original_open(leaf, os.O_WRONLY | os.O_TRUNC)
            try:
                os.write(descriptor, b"changed evidence bytes!\n")
            finally:
                os.close(descriptor)
            replace_marker[0] = True
        return data

    replace_marker = [False]
    if race in {
        "same_byte_leaf_replacement", "unlink_recreate",
        "parent_replacement", "replacement_before_final_leaf_check",
    }:
        monkeypatch.setattr(audit.os, "stat", wrapped_stat)
    elif race == "repo_root_replacement":
        monkeypatch.setattr(audit.os, "lstat", wrapped_lstat)
    elif race == "stat_open_race":
        monkeypatch.setattr(audit.os, "open", wrapped_open)
    elif race == "in_place_write":
        monkeypatch.setattr(audit.os, "read", wrapped_read)
    with pytest.raises(ValueError):
        audit._pinned_read(relative)


def test_checker_source_final_leaf_real_replacement(
    checker, tmp_path, monkeypatch
):
    repo = tmp_path / "repo"
    relative = Path("source/evidence.csv")
    leaf = repo / relative
    data = b"a,b\n1,2\n"
    _write_bytes(leaf, data)
    original_stat = os.stat
    count = 0

    def wrapped_stat(path, *args, **kwargs):
        nonlocal count
        if path == relative.name and kwargs.get("dir_fd") is not None:
            count += 1
            if count == 3:
                _replace_same_bytes(leaf, leaf.with_suffix(".old"), data)
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(checker.os, "stat", wrapped_stat)
    with pytest.raises(AssertionError, match="final binding"):
        checker._pinned_read_relative(repo, relative)


def test_checker_exact23_independent_attestation(checker, checker_sources):
    assert len(checker_sources) == 23
    assert tuple(
        (source.path.as_posix(), source.sha256) for source in checker_sources
    ) == checker.EXACT23
    assert all(len(source.blob) == 40 for source in checker_sources)
    assert "SOURCE_PATHS" not in CHECKER.read_text()
    assert "SOURCE_SHA256" not in CHECKER.read_text()


def test_row_specific_precondition_provenance(
    audit, checker, checker_sources, payloads
):
    rows = _csv(payloads[audit.PRECONDITION])
    expected = checker.expected_preconditions(checker_sources)
    assert rows == expected
    pairs = {(row["evidence_paths"], row["evidence_sha256"]) for row in rows}
    assert len(pairs) > 10
    source_paths = {path for path, _ in checker.EXACT23}
    for row in rows:
        paths = row["evidence_paths"].split("|")
        shas = row["evidence_sha256"].split("|")
        assert len(paths) == len(shas)
        assert len(paths) == len(set(paths))
        assert set(paths) <= source_paths
        assert paths
        if row["completion_status"] == "complete":
            assert len(paths) >= 1
        elif row["completion_status"] == (
            "supported_but_admit015_contract_not_frozen"
        ):
            assert any("admit_014" in path or "implementation_precondition" in path
                       for path in paths)
            assert any("001_to_014_runtime_manifest" in path for path in paths)


def test_responsibility_rows_6_7_do_not_overstate_precedent(
    audit, checker, payloads
):
    rows = _csv(payloads[audit.RESPONSIBILITY])
    assert rows == checker.expected_responsibilities()
    for row in rows[5:7]:
        assert row["admit_015_contract_status"] == (
            "supported_but_admit015_contract_not_frozen"
        )
        assert "candidate isolation requirement" not in row["committed_precedent"]
        assert "known-not-registered" in row["committed_precedent"]
        assert "Step14AU-A" in row["committed_precedent"]
        assert "contract not frozen" in row["coexistence_boundary"]


@pytest.mark.parametrize("leaf_index", [0, 2, 5])
def test_exact6_first_middle_last_leaf_real_replacement(
    audit, payloads, tmp_path, monkeypatch, leaf_index
):
    root = tmp_path / "audit"
    audit.materialize_audit(root)
    target_name = audit.FILES[leaf_index]
    target = root / target_name
    original_read = os.read
    completed_leaf_reads = 0

    def wrapped_read(fd, size):
        nonlocal completed_leaf_reads
        data = original_read(fd, size)
        if data == b"":
            if completed_leaf_reads == leaf_index:
                _replace_same_bytes(
                    target, tmp_path / f"{target.name}.old",
                    payloads[target_name],
                )
            completed_leaf_reads += 1
        return data

    monkeypatch.setattr(audit.os, "read", wrapped_read)
    with pytest.raises(ValueError, match="leaf replacement"):
        audit._read_output_set(root, payloads)


@pytest.mark.parametrize("target_kind", ["root", "parent"])
def test_output_root_and_parent_real_replacement(
    audit, payloads, tmp_path, monkeypatch, target_kind
):
    parent = tmp_path / "parent"
    parent.mkdir()
    root = parent / "audit"
    audit.materialize_audit(root)
    original_listdir = os.listdir
    replaced = False

    def write_exact(destination: Path) -> None:
        destination.mkdir(parents=True)
        for name, data in payloads.items():
            _write_bytes(destination / name, data)

    def wrapped_listdir(path):
        nonlocal replaced
        result = original_listdir(path)
        if not replaced:
            replaced = True
            if target_kind == "root":
                os.rename(root, parent / "audit.old")
                write_exact(root)
            else:
                os.rename(parent, tmp_path / "parent.old")
                parent.mkdir()
                write_exact(root)
        return result

    monkeypatch.setattr(audit.os, "listdir", wrapped_listdir)
    with pytest.raises(ValueError, match="binding"):
        audit._read_output_set(root, payloads)


def _write_payload_set(root: Path, payloads: dict[str, bytes]) -> None:
    root.mkdir()
    for name, data in payloads.items():
        _write_bytes(root / name, data)


def _failure_staging_dirs(parent: Path, destination: Path) -> list[Path]:
    return [
        path for path in parent.iterdir()
        if path != destination
        and path.is_dir()
        and (".staging" in path.name or path.name.endswith(".retained"))
    ]


def _assert_exact_payload_tree(
    root: Path, payloads: dict[str, bytes]
) -> None:
    assert set(path.name for path in root.iterdir()) == set(payloads)
    for name, data in payloads.items():
        assert (root / name).read_bytes() == data


def _destination_snapshot(root: Path) -> tuple:
    item = os.lstat(root)
    if root.is_symlink():
        return ("symlink", item.st_ino, os.readlink(root))
    rows = []
    for path in sorted(root.iterdir()):
        stat_result = os.lstat(path)
        value = os.readlink(path) if path.is_symlink() else path.read_bytes()
        rows.append((path.name, stat_result.st_ino, stat_result.st_mode, value))
    return ("directory", item.st_ino, tuple(rows))


def _forbid_destructive_failure_cleanup(audit, monkeypatch) -> list[str]:
    calls: list[str] = []

    def forbidden(*_args, **_kwargs):
        calls.append("called")
        raise AssertionError("destructive failure cleanup is forbidden")

    monkeypatch.setattr(audit.os, "unlink", forbidden)
    monkeypatch.setattr(audit.os, "rmdir", forbidden)
    return calls


def test_production_contains_no_failure_unlink_or_rmdir():
    source = PRODUCTION.read_text()
    assert "os.unlink(" not in source
    assert "os.rmdir(" not in source


def test_failure_staging_lexical_mismatch_preserves_owned_and_foreign_trees(
    audit, tmp_path, monkeypatch
):
    root = tmp_path / "audit"
    original_write = audit._write_leaf
    paths: dict[str, Path] = {}
    destructive_calls = _forbid_destructive_failure_cleanup(
        audit, monkeypatch
    )

    def replace_staging_after_first_write(directory_fd, name, data):
        result = original_write(directory_fd, name, data)
        if not paths:
            staging = Path(os.readlink(f"/proc/self/fd/{directory_fd}"))
            owned = staging.with_name(f"{staging.name}.owned-away")
            os.rename(staging, owned)
            staging.mkdir()
            (staging / "foreign.txt").write_bytes(b"foreign staging\n")
            paths.update(staging=staging, owned=owned)
        return result

    monkeypatch.setattr(audit, "_write_leaf", replace_staging_after_first_write)
    with pytest.raises(
        RuntimeError, match="failure staging retained at"
    ) as captured:
        audit.materialize_audit(root)
    assert paths["staging"].joinpath("foreign.txt").read_bytes() == (
        b"foreign staging\n"
    )
    assert len(list(paths["owned"].iterdir())) == 1
    assert next(paths["owned"].iterdir()).read_bytes() != b""
    assert destructive_calls == []
    assert not root.exists()


@pytest.mark.parametrize("position", ["first", "middle", "last"])
def test_failure_retention_preserves_foreign_and_owned_first_middle_last(
    audit, payloads, tmp_path, monkeypatch, position
):
    root = tmp_path / "audit"
    names = list(audit.FILES)
    target = {
        "first": names[0],
        "middle": names[len(names) // 2],
        "last": names[-1],
    }[position]
    recorded: dict[str, int] = {}
    destructive_calls = _forbid_destructive_failure_cleanup(
        audit, monkeypatch
    )

    def fail_after_foreign_replacement(
        source, destination, parent_fd, *_ownership
    ):
        owned_away = source / f".{target}.owned"
        os.rename(source / target, owned_away)
        _write_bytes(source / target, b"foreign replacement\n")
        recorded["owned"] = owned_away.stat().st_ino
        recorded["foreign"] = (source / target).stat().st_ino
        raise OSError(errno.EIO, "publish failure")

    monkeypatch.setattr(
        audit, "_rename_noreplace", fail_after_foreign_replacement
    )
    with pytest.raises(
        RuntimeError, match="failure staging retained at"
    ) as captured:
        audit.materialize_audit(root)
    retained = _failure_staging_dirs(tmp_path, root)
    assert len(retained) == 1
    stage = retained[0]
    assert str(stage) in str(captured.value)
    assert (stage / target).read_bytes() == b"foreign replacement\n"
    assert (stage / target).stat().st_ino == recorded["foreign"]
    owned = stage / f".{target}.owned"
    assert owned.read_bytes() == payloads[target]
    assert owned.stat().st_ino == recorded["owned"]
    assert len(list(stage.iterdir())) == len(audit.FILES) + 1
    assert destructive_calls == []
    assert not root.exists()


def test_retained_name_preexisting_is_never_overwritten_or_deleted(
    audit, payloads, tmp_path, monkeypatch
):
    root = tmp_path / "audit"
    preexisting = tmp_path / ".fixed.retained"
    preexisting.mkdir()
    marker = preexisting / "foreign.txt"
    marker.write_bytes(b"foreign retained name\n")
    marker_inode = marker.stat().st_ino
    destructive_calls = _forbid_destructive_failure_cleanup(
        audit, monkeypatch
    )
    monkeypatch.setattr(
        audit, "_new_retained_name", lambda _name: preexisting.name
    )
    monkeypatch.setattr(
        audit,
        "_rename_noreplace",
        lambda *_args: (_ for _ in ()).throw(OSError(errno.EINVAL, "failure")),
    )
    with pytest.raises(RuntimeError, match="failure staging retained at"):
        audit.materialize_audit(root)
    assert marker.read_bytes() == b"foreign retained name\n"
    assert marker.stat().st_ino == marker_inode
    staging = [
        path for path in tmp_path.iterdir()
        if path.name.endswith(".staging")
    ]
    assert len(staging) == 1
    _assert_exact_payload_tree(staging[0], payloads)
    assert destructive_calls == []


def test_real_concurrent_eexist_identical_fails_closed_and_retains_staging(
    audit, payloads, tmp_path, monkeypatch
):
    root = tmp_path / "audit"
    calls = 0
    destination_inodes: dict[str, int] = {}
    destructive_calls = _forbid_destructive_failure_cleanup(
        audit, monkeypatch
    )

    def concurrent_eexist(source, destination, parent_fd, *ownership):
        nonlocal calls
        calls += 1
        _write_payload_set(root, payloads)
        destination_inodes.update(
            {name: (root / name).stat().st_ino for name in audit.FILES}
        )
        raise OSError(errno.EEXIST, "concurrent destination")

    monkeypatch.setattr(audit, "_rename_noreplace", concurrent_eexist)
    with pytest.raises(RuntimeError, match="failure staging retained at"):
        audit.materialize_audit(root)
    assert calls == 1
    _assert_exact_payload_tree(root, payloads)
    assert destination_inodes == {
        name: (root / name).stat().st_ino for name in audit.FILES
    }
    retained = _failure_staging_dirs(tmp_path, root)
    assert len(retained) == 1
    _assert_exact_payload_tree(retained[0], payloads)
    assert destructive_calls == []


@pytest.mark.parametrize(
    "variant", ["mismatch", "extra", "missing", "symlink"]
)
def test_real_concurrent_eexist_nonidentical_fails_closed(
    audit, payloads, tmp_path, monkeypatch, variant
):
    root = tmp_path / "audit"
    calls = 0
    before: list[tuple] = []
    destructive_calls = _forbid_destructive_failure_cleanup(
        audit, monkeypatch
    )

    def concurrent_eexist(source, destination, parent_fd, *ownership):
        nonlocal calls
        calls += 1
        if variant == "symlink":
            foreign = tmp_path / "foreign"
            foreign.mkdir()
            root.symlink_to(foreign, target_is_directory=True)
        else:
            root.mkdir()
            for name, data in payloads.items():
                if variant != "missing" or name != audit.SAFETY:
                    _write_bytes(root / name, data)
            if variant == "mismatch":
                (root / audit.SAFETY).write_bytes(b"tamper\n")
            elif variant == "extra":
                (root / "foreign.txt").write_text("foreign")
        before.append(_destination_snapshot(root))
        raise OSError(errno.EEXIST, "concurrent destination")

    monkeypatch.setattr(audit, "_rename_noreplace", concurrent_eexist)
    with pytest.raises(RuntimeError, match="failure staging retained at"):
        audit.materialize_audit(root)
    assert calls == 1
    assert before == [_destination_snapshot(root)]
    retained = _failure_staging_dirs(tmp_path, root)
    assert len(retained) == 1
    _assert_exact_payload_tree(retained[0], payloads)
    assert destructive_calls == []


def test_gpfs_einval_fails_closed_with_complete_retained_staging(
    audit, payloads, tmp_path, monkeypatch
):
    root = tmp_path / "audit"
    destructive_calls = _forbid_destructive_failure_cleanup(
        audit, monkeypatch
    )

    def fail_publish(*_args):
        raise OSError(errno.EINVAL, "Invalid argument")

    monkeypatch.setattr(audit, "_rename_noreplace", fail_publish)
    with pytest.raises(RuntimeError, match="failure staging retained at"):
        audit.materialize_audit(root)
    retained = _failure_staging_dirs(tmp_path, root)
    assert len(retained) == 1
    _assert_exact_payload_tree(retained[0], payloads)
    assert destructive_calls == []
    assert not root.exists()


def test_normal_first_publish_has_no_staging_or_retained_residue(
    audit, payloads, tmp_path, monkeypatch
):
    root = tmp_path / "audit"
    destructive_calls = _forbid_destructive_failure_cleanup(
        audit, monkeypatch
    )
    manifest = audit.materialize_audit(root)
    assert manifest["all_checks_passed"] is True
    _assert_exact_payload_tree(root, payloads)
    assert _failure_staging_dirs(tmp_path, root) == []
    assert destructive_calls == []


def test_preexisting_exact_destination_is_inode_preserving_noop_without_staging(
    audit, payloads, tmp_path, monkeypatch
):
    root = tmp_path / "audit"
    audit.materialize_audit(root)
    before = {name: (root / name).stat().st_ino for name in audit.FILES}

    def staging_forbidden(*_args, **_kwargs):
        raise AssertionError("pre-existing exact no-op must not create staging")

    monkeypatch.setattr(audit.tempfile, "mkdtemp", staging_forbidden)
    manifest = audit.materialize_audit(root)
    assert manifest["all_checks_passed"] is True
    assert before == {name: (root / name).stat().st_ino for name in audit.FILES}
    _assert_exact_payload_tree(root, payloads)


def _reordered(mapping: dict, key: str) -> dict:
    return {key: mapping[key], **{k: v for k, v in mapping.items() if k != key}}


@pytest.mark.parametrize(
    "mutation",
    ["duplicate", "missing", "extra", "reorder", "wrong_type"],
)
def test_manifest_top_level_exact_schema_rejections(
    checker, payloads, mutation
):
    original = payloads["covapie_admit_015_formal_evaluator_interface_preconditions_manifest.json"]
    document = json.loads(original)
    if mutation == "duplicate":
        tampered = original.rstrip()[:-1] + b',\n  "project": "duplicate"\n}\n'
    elif mutation == "missing":
        document.pop("project")
        tampered = (json.dumps(document, indent=2) + "\n").encode()
    elif mutation == "extra":
        document["extra"] = True
        tampered = (json.dumps(document, indent=2) + "\n").encode()
    elif mutation == "reorder":
        tampered = (json.dumps(_reordered(document, "stage"), indent=2) + "\n").encode()
    else:
        document["source_count"] = True
        tampered = (json.dumps(document, indent=2) + "\n").encode()
    with pytest.raises(AssertionError):
        checker._parse_manifest_exact(tampered)


@pytest.mark.parametrize(
    "nested_key", [
        "source_boundary", "formal_interface_not_frozen", "readiness",
        "canonical_masks", "safety", "materialization", "output_sha256",
    ],
)
@pytest.mark.parametrize("mutation", ["missing", "extra", "reorder"])
def test_manifest_nested_exact_schema_rejections(
    checker, payloads, nested_key, mutation
):
    document = json.loads(payloads[checker.MANIFEST])
    target = document[nested_key]
    if isinstance(target, list):
        target = target[0]
    first = next(iter(target))
    if mutation == "missing":
        target.pop(first)
    elif mutation == "extra":
        target["extra"] = True
    else:
        reordered = _reordered(target, list(target)[-1])
        if isinstance(document[nested_key], list):
            document[nested_key][0] = reordered
        else:
            document[nested_key] = reordered
    tampered = (json.dumps(document, indent=2) + "\n").encode()
    with pytest.raises(AssertionError):
        checker._parse_manifest_exact(tampered)


def test_manifest_nested_duplicate_rejected(checker, payloads):
    original = payloads[checker.MANIFEST].decode()
    needle = '"evaluator_signature": true,'
    tampered = original.replace(
        needle, needle + '\n    "evaluator_signature": true,', 1
    ).encode()
    with pytest.raises(AssertionError, match="duplicate"):
        checker._parse_manifest_exact(tampered)


def test_manifest_materialization_nested_duplicate_rejected(checker, payloads):
    original = payloads[checker.MANIFEST].decode()
    needle = '"failure_cleanup_is_non_destructive": true,'
    tampered = original.replace(
        needle,
        needle + '\n    "failure_cleanup_is_non_destructive": true,',
        1,
    ).encode()
    with pytest.raises(AssertionError, match="duplicate"):
        checker._parse_manifest_exact(tampered)


def _rewrite_csv(
    checker, data: bytes, columns: tuple[str, ...],
    row_index: int, field: str, value: str,
) -> bytes:
    rows = checker._parse_csv_exact(data, columns)
    rows[row_index][field] = value
    return checker._csv_bytes(columns, rows)


@pytest.mark.parametrize(
    "case",
    [
        "pre_subject", "pre_status", "pre_blocking", "pre_evidence_path",
        "pre_evidence_sha", "responsibility_status",
        "responsibility_allowed", "responsibility_coexistence",
        "source_blob", "source_order", "safety_observed",
        "issue_noncoverage", "issue_coverage", "readiness",
        "current_permission", "execution_count", "canonical_b3",
        "formal_not_frozen", "recommended_next", "materialization_claim",
        "readiness_false_as_zero", "readiness_true_as_one",
        "formal_true_as_one", "safety_false_as_zero",
        "materialization_true_as_one", "source_stage_zero_as_false",
        "precondition_count_as_true", "output_sha_nonstring",
        "materialization_new_false_as_zero",
        "materialization_new_true_as_one",
    ],
)
def test_synchronized_semantic_tamper_rejected_after_sha_bypass(
    checker, checker_sources, payloads, monkeypatch, case
):
    tampered = dict(payloads)
    changed_output: str | None = None
    manifest = json.loads(tampered[checker.MANIFEST])
    if case.startswith("pre_"):
        field, value = {
            "pre_subject": ("precondition_subject", "tampered subject"),
            "pre_status": ("completion_status", "complete"),
            "pre_blocking": ("implementation_blocking", "false"),
            "pre_evidence_path": ("evidence_paths", checker.EXACT23[0][0]),
            "pre_evidence_sha": ("evidence_sha256", "0" * 64),
        }[case]
        tampered[checker.PRECONDITION] = _rewrite_csv(
            checker, tampered[checker.PRECONDITION], checker.PRE_COLUMNS,
            6, field, value,
        )
        changed_output = checker.PRECONDITION
    elif case.startswith("responsibility_"):
        field, value = {
            "responsibility_status": (
                "admit_015_contract_status", "verified_committed_precedent"
            ),
            "responsibility_allowed": ("allowed_source", "training_config"),
            "responsibility_coexistence": (
                "coexistence_boundary", "download implies training"
            ),
        }[case]
        tampered[checker.RESPONSIBILITY] = _rewrite_csv(
            checker, tampered[checker.RESPONSIBILITY], checker.RESP_COLUMNS,
            5, field, value,
        )
        changed_output = checker.RESPONSIBILITY
    elif case in {"source_blob", "source_order"}:
        field, value = {
            "source_blob": ("base_tree_blob", "0" * 40),
            "source_order": ("source_order", "2"),
        }[case]
        tampered[checker.SOURCE_AUDIT] = _rewrite_csv(
            checker, tampered[checker.SOURCE_AUDIT], checker.SOURCE_COLUMNS,
            0, field, value,
        )
        changed_output = checker.SOURCE_AUDIT
    elif case == "safety_observed":
        tampered[checker.SAFETY] = _rewrite_csv(
            checker, tampered[checker.SAFETY], checker.SAFETY_COLUMNS,
            5, "observed_state", "true",
        )
        changed_output = checker.SAFETY
    elif case.startswith("issue_"):
        issue_columns = tuple(
            next(csv.reader(io.StringIO(tampered[checker.ISSUE].decode())))
        )
        issue_rows = checker._parse_csv_exact(tampered[checker.ISSUE], issue_columns)
        if case == "issue_noncoverage":
            issue_rows[0]["successor_effective_status"] = "resolved"
        else:
            row = next(
                item for item in issue_rows
                if item["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
            )
            row["affected_rules"] = ""
        tampered[checker.ISSUE] = checker._csv_bytes(issue_columns, issue_rows)
        changed_output = checker.ISSUE
    else:
        if case == "readiness":
            manifest["readiness"]["ready_for_training"] = True
        elif case == "current_permission":
            manifest["current_permission"] = True
        elif case == "execution_count":
            manifest["authorized_admit_015_training_execution_count"] = 1
        elif case == "canonical_b3":
            manifest["canonical_masks"][3]["semantic_name"] = "wrong"
        elif case == "formal_not_frozen":
            manifest["formal_interface_not_frozen"]["evaluator_signature"] = False
        elif case == "recommended_next":
            manifest["recommended_next_step"] = "wrong"
        elif case == "materialization_claim":
            manifest["materialization"]["ownership_safe_cleanup"] = False
        elif case == "readiness_false_as_zero":
            manifest["readiness"]["ready_for_training"] = 0
        elif case == "readiness_true_as_one":
            manifest["readiness"]["admit_015_rule_identity_verified"] = 1
        elif case == "formal_true_as_one":
            manifest["formal_interface_not_frozen"]["evaluator_signature"] = 1
        elif case == "safety_false_as_zero":
            manifest["safety"]["training"] = 0
        elif case == "materialization_true_as_one":
            manifest["materialization"]["ownership_safe_cleanup"] = 1
        elif case == "materialization_new_false_as_zero":
            manifest["materialization"][
                "failure_cleanup_is_non_destructive"
            ] = 0
        elif case == "materialization_new_true_as_one":
            manifest["materialization"][
                "concurrent_eexist_fails_closed"
            ] = 1
        elif case == "source_stage_zero_as_false":
            manifest["source_boundary"][0]["stage"] = False
        elif case == "precondition_count_as_true":
            manifest["precondition_count"] = True
        elif case == "output_sha_nonstring":
            manifest["output_sha256"][checker.PRECONDITION] = 0
    if changed_output is not None:
        manifest["output_sha256"][changed_output] = hashlib.sha256(
            tampered[changed_output]
        ).hexdigest()
    tampered[checker.MANIFEST] = (
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    ).encode()
    monkeypatch.setattr(
        checker,
        "FROZEN_OUTPUT_SHA256",
        {name: hashlib.sha256(tampered[name]).hexdigest()
         for name in checker.FILES},
    )
    with pytest.raises(AssertionError):
        checker.verify_exact6_semantics(tampered, checker_sources)


def _git_in(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False
    )


def _lifecycle_repo(checker, tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    assert _git_in(repo, "init", "-q").returncode == 0
    _git_in(repo, "config", "user.name", "Lifecycle Test")
    _git_in(repo, "config", "user.email", "lifecycle@invalid")
    assert _git_in(repo, "commit", "--allow-empty", "-qm", "base").returncode == 0
    base = _git_in(repo, "rev-parse", "HEAD").stdout.strip()
    for relative in checker.EXACT10:
        source = ROOT / relative
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return repo, base


def test_lifecycle_real_pre_and_post_commit(
    checker, tmp_path, monkeypatch
):
    repo, base = _lifecycle_repo(checker, tmp_path)
    monkeypatch.setattr(checker, "ROOT", repo)
    monkeypatch.setattr(checker, "BASE", base)
    assert checker._lifecycle() == "pre_commit"
    assert _git_in(repo, "add", "--", *(path.as_posix() for path in checker.EXACT10)).returncode == 0
    assert _git_in(repo, "commit", "-qm", "candidate").returncode == 0
    assert checker._lifecycle() == "post_commit"


def _ignore_in_repo(repo: Path, relative: Path, *, directory: bool = False) -> None:
    exclude = repo / ".git/info/exclude"
    suffix = "/" if directory else ""
    exclude.write_text(
        exclude.read_text() + f"\n/{relative.as_posix()}{suffix}\n"
    )
    assert _git_in(
        repo, "check-ignore", "--no-index", "-q", "--", relative.as_posix()
    ).returncode == 0


@pytest.mark.parametrize(
    "failure",
    [
        "mixed", "staged", "dirty", "missing", "ignored", "tracked_ignored",
        "check_ignore_error", "extra_stage_file", "seventh_file",
        "tracked_extra_stage_file", "forbidden_suffix", "oversized", "symlink",
        "ignored_extra_docs", "ignored_extra_production", "ignored_seventh",
        "ignored_extra_derived_root", "empty_extra_derived_root",
        "ignored_only_extra_derived_root", "symlink_extra",
        "oversized_extra", "ignored_nested_docs",
        "nonignored_nested_docs", "ignored_nested_production",
        "nested_scripts", "nested_tests", "nested_symlink_directory",
        "nested_forbidden_suffix", "nested_oversized",
        "nested_empty_stage_directory", "tracked_nested_docs",
        "base_nonancestor",
    ],
)
def test_lifecycle_fail_closed_cases(
    checker, tmp_path, monkeypatch, failure
):
    repo, base = _lifecycle_repo(checker, tmp_path)
    monkeypatch.setattr(checker, "ROOT", repo)
    monkeypatch.setattr(checker, "BASE", base)
    first = checker.EXACT10[0]
    if failure in {"dirty", "tracked_ignored"}:
        _git_in(repo, "add", "--", *(path.as_posix() for path in checker.EXACT10))
        _git_in(repo, "commit", "-qm", "candidate")
    if failure == "mixed":
        _git_in(repo, "add", "--", first.as_posix())
        _git_in(repo, "commit", "-qm", "one tracked")
    elif failure == "staged":
        _git_in(repo, "add", "--", first.as_posix())
    elif failure == "dirty":
        (repo / first).write_bytes((repo / first).read_bytes() + b"\n")
    elif failure == "missing":
        (repo / first).unlink()
    elif failure in {"ignored", "tracked_ignored"}:
        _ignore_in_repo(repo, first)
    elif failure == "check_ignore_error":
        original_git = checker._git

        def failing_git(args, **kwargs):
            if args and args[0] == "check-ignore":
                return subprocess.CompletedProcess(args, 2, "", "failure")
            return original_git(args, **kwargs)

        monkeypatch.setattr(checker, "_git", failing_git)
    elif failure in {"extra_stage_file", "forbidden_suffix"}:
        suffix = ".tmp" if failure == "forbidden_suffix" else ".extra"
        extra = repo / (
            "docs/covapie_bulk_download_admission_admit_015_"
            f"formal_evaluator_interface_preconditions_audit_v1{suffix}"
        )
        extra.write_text("extra")
    elif failure == "tracked_extra_stage_file":
        _git_in(repo, "add", "--", *(path.as_posix() for path in checker.EXACT10))
        _git_in(repo, "commit", "-qm", "candidate")
        extra = repo / (
            "docs/covapie_bulk_download_admission_admit_015_"
            "formal_evaluator_interface_preconditions_audit_v1_extra.md"
        )
        extra.write_text("tracked extra")
        _git_in(repo, "add", "--", extra.relative_to(repo).as_posix())
        _git_in(repo, "commit", "-qm", "tracked extra")
    elif failure == "seventh_file":
        (repo / checker.DERIVED / "seventh.csv").write_text("extra")
    elif failure == "ignored_extra_docs":
        relative = Path(
            "docs/covapie_bulk_download_admission_admit_015_"
            "formal_evaluator_interface_preconditions_audit_v1_ignored.md"
        )
        (repo / relative).write_text("ignored extra")
        _ignore_in_repo(repo, relative)
    elif failure == "ignored_extra_production":
        relative = Path(
            "src/covalent_ext/covapie_bulk_download_admission_admit_015_"
            "formal_evaluator_interface_preconditions_audit_ignored.py"
        )
        (repo / relative).write_text("ignored extra")
        _ignore_in_repo(repo, relative)
    elif failure == "ignored_seventh":
        relative = checker.DERIVED / "ignored-seventh.csv"
        (repo / relative).write_text("ignored seventh")
        _ignore_in_repo(repo, relative)
    elif failure == "ignored_extra_derived_root":
        relative = checker.DERIVED.with_name(
            checker.DERIVED.name + "_ignored"
        )
        (repo / relative).mkdir()
        _ignore_in_repo(repo, relative, directory=True)
    elif failure == "empty_extra_derived_root":
        relative = checker.DERIVED.with_name(
            checker.DERIVED.name + "_empty"
        )
        (repo / relative).mkdir()
    elif failure == "ignored_only_extra_derived_root":
        relative = checker.DERIVED.with_name(
            checker.DERIVED.name + "_ignored_contents"
        )
        (repo / relative).mkdir()
        ignored_child = relative / "ignored.txt"
        (repo / ignored_child).write_text("ignored only")
        _ignore_in_repo(repo, ignored_child)
    elif failure == "symlink_extra":
        relative = Path(
            "docs/covapie_bulk_download_admission_admit_015_"
            "formal_evaluator_interface_preconditions_audit_v1_extra.md"
        )
        (repo / relative).symlink_to(repo / first)
    elif failure == "oversized_extra":
        relative = Path(
            "docs/covapie_bulk_download_admission_admit_015_"
            "formal_evaluator_interface_preconditions_audit_v1_extra.md"
        )
        with (repo / relative).open("wb") as handle:
            handle.truncate(100 * 1024 * 1024 + 1)
    elif failure in {"ignored_nested_docs", "nonignored_nested_docs"}:
        relative = Path(
            "docs/nested/covapie_bulk_download_admission_admit_015_"
            "formal_evaluator_interface_preconditions_audit_v1_hidden.md"
        )
        (repo / relative).parent.mkdir()
        (repo / relative).write_text("nested docs")
        if failure == "ignored_nested_docs":
            _ignore_in_repo(repo, relative)
    elif failure == "ignored_nested_production":
        relative = Path(
            "src/covalent_ext/nested/"
            "covapie_bulk_download_admission_admit_015_"
            "formal_evaluator_interface_preconditions_audit_hidden.py"
        )
        (repo / relative).parent.mkdir()
        (repo / relative).write_text("nested production")
        _ignore_in_repo(repo, relative)
    elif failure == "nested_scripts":
        relative = Path(
            "scripts/nested/check_covapie_bulk_download_admission_admit_015_"
            "formal_evaluator_interface_preconditions_audit_v1_hidden.py"
        )
        (repo / relative).parent.mkdir()
        (repo / relative).write_text("nested script")
    elif failure == "nested_tests":
        relative = Path(
            "tests/nested/test_covapie_bulk_download_admission_admit_015_"
            "formal_evaluator_interface_preconditions_audit_v1_hidden.py"
        )
        (repo / relative).parent.mkdir()
        (repo / relative).write_text("nested test")
    elif failure == "nested_symlink_directory":
        outside = tmp_path / "outside-stage-family"
        outside.mkdir()
        (outside / (
            "covapie_bulk_download_admission_admit_015_"
            "formal_evaluator_interface_preconditions_audit_v1_hidden.md"
        )).write_text("hidden behind symlink")
        (repo / "docs/nested-link").symlink_to(
            outside, target_is_directory=True
        )
    elif failure == "nested_forbidden_suffix":
        relative = Path(
            "docs/nested/covapie_bulk_download_admission_admit_015_"
            "formal_evaluator_interface_preconditions_audit_v1.tmp"
        )
        (repo / relative).parent.mkdir()
        (repo / relative).write_text("forbidden")
    elif failure == "nested_oversized":
        relative = Path(
            "docs/nested/covapie_bulk_download_admission_admit_015_"
            "formal_evaluator_interface_preconditions_audit_v1_large.md"
        )
        (repo / relative).parent.mkdir()
        with (repo / relative).open("wb") as handle:
            handle.truncate(100 * 1024 * 1024 + 1)
    elif failure == "nested_empty_stage_directory":
        relative = Path(
            "docs/nested/covapie_bulk_download_admission_admit_015_"
            "formal_evaluator_interface_preconditions_audit_v1_empty"
        )
        (repo / relative).mkdir(parents=True)
    elif failure == "tracked_nested_docs":
        _git_in(repo, "add", "--", *(path.as_posix() for path in checker.EXACT10))
        _git_in(repo, "commit", "-qm", "candidate")
        relative = Path(
            "docs/nested/covapie_bulk_download_admission_admit_015_"
            "formal_evaluator_interface_preconditions_audit_v1_tracked.md"
        )
        (repo / relative).parent.mkdir()
        (repo / relative).write_text("tracked nested")
        _git_in(repo, "add", "--", relative.as_posix())
        _git_in(repo, "commit", "-qm", "tracked nested extra")
    elif failure == "oversized":
        with (repo / first).open("wb") as handle:
            handle.truncate(100 * 1024 * 1024 + 1)
    elif failure == "symlink":
        (repo / first).unlink()
        (repo / first).symlink_to(repo / checker.EXACT10[1])
    elif failure == "base_nonancestor":
        monkeypatch.setattr(checker, "BASE", "0" * 40)
    with pytest.raises(AssertionError):
        checker._lifecycle()


def test_checker_independently_rebuilds_all_exact6_semantics(
    checker, checker_sources, payloads
):
    manifest = checker.verify_exact6_semantics(dict(payloads), checker_sources)
    assert manifest["source_count"] == 23
    assert manifest["precondition_count"] == 45
    assert manifest["responsibility_count"] == 16
    assert manifest["safety_count"] == 20
    assert manifest["issue_row_count"] == 30
