from __future__ import annotations

import ast
import csv
import errno
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_admit_015_training_authorization_contract as production,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / (
    "scripts/"
    "check_covapie_bulk_download_admission_admit_015_training_authorization_contract_v1.py"
)


def _load_checker():
    spec = importlib.util.spec_from_file_location("admit015_auth_checker_tests", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


checker = _load_checker()


def _csv(payloads: dict[str, bytes], name: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payloads[name].decode(), newline="")))


def _manifest(payloads: dict[str, bytes]) -> dict:
    return json.loads(payloads[production.MANIFEST])


@pytest.fixture(scope="module")
def sources():
    return production.build_frozen_source_snapshot()


@pytest.fixture(scope="module")
def payloads(sources):
    return production.build_artifact_payloads(sources)


def test_base_identity():
    assert (
        production.BASE_COMMIT,
        production.BASE_PARENT,
        production.BASE_TREE,
        production.BASE_SUBJECT,
    ) == (
        "4fb86e7d6b8cd27258362cae34eec196b117c265",
        "f54c0efabfb695653c9e55b3a53bda8cf200f353",
        "2a447517ce601e9440a7c1523866d459b192870c",
        "add CovaPIE ADMIT_015 formal evaluator interface preconditions audit v1",
    )


def test_exact18_source_boundary(sources):
    assert len(sources) == 18
    assert tuple((item.path.as_posix(), item.sha256) for item in sources) == checker.EXACT18
    assert all(item.mode in {"100644", "100755"} and len(item.blob) == 40 for item in sources)


@pytest.mark.parametrize("replaced_parent", ["intermediate", "upper"])
def test_checker_pinned_read_rejects_real_parent_replacement(
    tmp_path, monkeypatch, replaced_parent
):
    repo = tmp_path / "repo"
    source = repo / "a/b/source.txt"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"old bytes")
    monkeypatch.setattr(checker, "ROOT", repo)

    target_name = "b" if replaced_parent == "intermediate" else "a"
    target = repo / ("a/b" if replaced_parent == "intermediate" else "a")
    replacement = target.with_name(f"{target.name}.old")
    real_open = os.open
    real_read = os.read
    held_parent_fds = []
    observed_bindings = []
    replaced = False

    def capturing_open(path, flags, *args, **kwargs):
        fd = real_open(path, flags, *args, **kwargs)
        if path == target_name:
            held_parent_fds.append(fd)
        return fd

    def replacing_read(fd, size):
        nonlocal replaced
        chunk = real_read(fd, size)
        if chunk == b"" and not replaced:
            replaced = True
            target.rename(replacement)
            source.parent.mkdir(parents=True)
            source.write_bytes(b"new bytes")
            assert held_parent_fds
            observed_bindings.append(
                (
                    checker._identity(os.fstat(held_parent_fds[-1])),
                    checker._identity(os.stat(target, follow_symlinks=False)),
                )
            )
        return chunk

    monkeypatch.setattr(checker.os, "open", capturing_open)
    monkeypatch.setattr(checker.os, "read", replacing_read)
    with pytest.raises(
        AssertionError, match=r"pinned parent (?:FD|lexical) drift"
    ):
        checker._pinned_read(Path("a/b/source.txt"))

    assert replaced
    assert source.read_bytes() == b"new bytes"
    assert (
        replacement / ("source.txt" if replaced_parent == "intermediate"
                       else "b/source.txt")
    ).read_bytes() == b"old bytes"
    assert len(observed_bindings) == 1
    assert observed_bindings[0][0] != observed_bindings[0][1]
    assert observed_bindings[0][0][1] != observed_bindings[0][1][1]


def test_admit015_identity(payloads):
    identity = _manifest(payloads)["admission_rule_identity"]
    assert identity == {
        "admission_rule_id": "ADMIT_015",
        "admission_rule_name": "current_gate_grants_no_training_permission",
        "evidence_source": "current_design_gate",
        "required_status": "training_not_authorized_now",
        "failure_severity": "blocking",
        "blocking_reason": "training_not_authorized",
        "evaluation_phase": "current_step",
        "authorization_model": "future_explicit_authorization_context",
    }


def test_authoritative_envelope_key_producer(payloads):
    contract = _manifest(payloads)["authorization_contract"]
    assert contract["authoritative_envelope"] == "stage_authorization_context"
    assert contract["authoritative_key"] == "current_stage_training_authorized"
    assert contract["context_scope"] == "stage"
    assert contract["producer_boundary"] == "trusted_future_stage_orchestrator"


@pytest.mark.parametrize(
    ("value", "outcome", "reason"),
    [
        (False, "blocked", "TRAINING_NOT_AUTHORIZED"),
        (True, "passed", ""),
    ],
)
def test_exact_bool_true_false(value, outcome, reason):
    result = production.classify_admit_015_training_authorization_contract_design(
        {"current_stage_training_authorized": value}
    )
    assert (result.outcome, result.reason) == (outcome, reason)


class Truthy:
    def __bool__(self):
        return True


class Falsy:
    def __bool__(self):
        return False


@pytest.mark.parametrize(
    "value",
    [0, 1, 0.0, 1.0, "false", "true", "", None, [], {}, Truthy(), Falsy()],
    ids=[
        "int-zero", "int-one", "float-zero", "float-one", "string-false",
        "string-true", "empty-string", "none", "list", "dict",
        "custom-truthy", "custom-falsy",
    ],
)
def test_twelve_non_exact_bool_classes_fail_closed(value):
    result = production.classify_admit_015_training_authorization_contract_design(
        {"current_stage_training_authorized": value}
    )
    assert result.outcome == "blocked"
    assert result.reason == "CURRENT_STAGE_TRAINING_AUTHORIZED_TYPE_INVALID"


@pytest.mark.parametrize(
    ("context", "reason"),
    [
        (None, "STAGE_AUTHORIZATION_CONTEXT_REQUIRED"),
        (object(), "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID"),
        ({}, "CURRENT_STAGE_TRAINING_AUTHORIZED_MISSING"),
    ],
)
def test_context_and_missing_fail_closed(context, reason):
    result = production.classify_admit_015_training_authorization_contract_design(context)
    assert (result.outcome, result.reason) == ("blocked", reason)


class LookupFailure(dict):
    def __getitem__(self, key):
        raise RuntimeError("lookup")


def test_lookup_exception_fail_closed():
    result = production.classify_admit_015_training_authorization_contract_design(
        LookupFailure()
    )
    assert result.reason == "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED"


def test_failure_precedence_and_vocabularies(payloads):
    manifest = _manifest(payloads)
    assert manifest["outcome_vocabulary"] == ["passed", "blocked"]
    assert manifest["reason_vocabulary"] == list(checker.REASONS)
    assert manifest["failure_precedence"] == list(checker.REASONS[1:] + ("",))


def test_exact40_count_order_groups_and_access(payloads):
    rows = _csv(payloads, production.TRUTH)
    assert len(rows) == 40
    assert [row["case_order"] for row in rows] == [str(i) for i in range(1, 41)]
    counts = {
        group: sum(row["case_group"] == group for row in rows)
        for group in dict.fromkeys(row["case_group"] for row in rows)
    }
    assert counts == {
        "context_structure": 7,
        "exact_bool": 2,
        "non_exact_bool": 12,
        "mapping_behavior": 10,
        "forbidden_pseudo_authority": 6,
        "current_future": 3,
    }
    assert all(row["case_passed"] == "true" for row in rows)
    assert sum(int(row["forbidden_envelope_access_count"]) for row in rows) == 0
    assert all(row["mapping_iteration_count"] == "0" for row in rows)
    assert all(row["mapping_len_count"] == "0" for row in rows)
    assert all(row["mapping_get_count"] == "0" for row in rows)
    assert all(row["mapping_contains_count"] == "0" for row in rows)


def test_full_contract_truth_value_safety_independent_rows(payloads, sources):
    assert _csv(payloads, production.CONTRACT) == checker._expected_contract_rows()
    assert _csv(payloads, production.TRUTH) == checker._expected_truth_rows(sources)
    assert _csv(payloads, production.VALUE_TRUST) == checker._expected_value_rows()
    assert _csv(payloads, production.SAFETY) == checker._expected_safety_rows()


def test_exact40_literal_case_identity_continuity(payloads, sources):
    precedent = checker._parse_csv(sources[9].content, checker.TRUTH_COLUMNS)
    current = _csv(payloads, production.TRUTH)
    assert [row["case_id"] for row in current] == [
        row["case_id"] for row in precedent
    ]
    assert current[24]["case_id"] == "ADMIT015_PLUS_TRUE"
    assert current[25]["case_id"] == "ADMIT015_PLUS_FALSE"
    assert "current_stage_training_authorized" in current[24][
        "stage_context_representation"
    ]
    assert "current_stage_download_authorized" in current[24][
        "stage_context_representation"
    ]


def test_download_training_isolation(payloads):
    isolation = _manifest(payloads)["download_training_isolation_contract"]
    assert all(value is False for value in isolation.values())
    missing = production.classify_admit_015_training_authorization_contract_design(
        {"current_stage_download_authorized": True}
    )
    assert missing.reason == "CURRENT_STAGE_TRAINING_AUTHORIZED_MISSING"
    both = production.classify_admit_015_training_authorization_contract_design(
        {
            "current_stage_download_authorized": False,
            "current_stage_training_authorized": True,
        }
    )
    assert both.outcome == "passed"


def test_current_permission_synthetic_true_and_execution_count(payloads):
    manifest = _manifest(payloads)
    assert manifest["current_permission"] is False
    assert manifest["authorized_admit_015_training_execution_count"] == 0
    assert manifest["synthetic_true_design_case_grants_current_permission"] is False
    assert manifest["synthetic_true_design_case_starts_real_training"] is False
    assert manifest["ready_for_training_now"] is False


def test_precondition_exact12_transition_and_remaining_exact14(payloads):
    transition = _manifest(payloads)["precondition_transition"]
    assert transition["resolved_precondition_ids"] == list(checker.RESOLVED_PRE)
    assert transition["remaining_open_precondition_ids"] == list(checker.OPEN_PRE)
    assert (
        transition["complete_count"],
        transition["supported_but_not_frozen_count"],
        transition["incomplete_count"],
        transition["implementation_blocking_count"],
    ) == (31, 0, 14, 14)


def test_independent_precondition_transition_rows_and_hash(payloads, sources):
    inherited_columns = tuple(
        next(csv.reader(io.StringIO(sources[1].content.decode())))
    )
    inherited = checker._parse_csv(sources[1].content, inherited_columns)
    transitioned, digest = checker._expected_transition(sources)
    resolved = set(checker.RESOLVED_PRE)
    for before, after in zip(inherited, transitioned):
        changed = {
            key for key in inherited_columns if before[key] != after[key]
        }
        if before["precondition_id"] in resolved:
            assert changed == {
                "observed_state", "completion_status",
                "implementation_blocking", "resolution_or_gap",
            }
        else:
            assert changed == set()
    assert digest == _manifest(payloads)["precondition_transition"][
        "transition_rows_sha256"
    ]


def test_exact30_byte_identity(payloads):
    assert payloads[production.ISSUE] == (
        ROOT
        / "data/derived/covalent_small/"
        "covapie_bulk_download_admission_admit_015_"
        "formal_evaluator_interface_preconditions_audit_v1/"
        "covapie_admit_015_issue_readiness_inventory.csv"
    ).read_bytes()
    assert hashlib.sha256(payloads[production.ISSUE]).hexdigest() == (
        "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec"
    )


def test_future_mandatory_responsibility_not_implemented(payloads):
    responsibility = _manifest(payloads)[
        "future_mandatory_training_authorization_responsibility"
    ]
    assert responsibility["evaluate_once_each_real_training_invocation"] is True
    assert responsibility["blocked_must_not_continue"] is True
    assert responsibility["combined_verdict_may_override_blocked"] is False
    assert responsibility["api_frozen"] is False
    assert responsibility["implemented"] is False
    assert all(
        responsibility[key] == 0
        for key in (
            "blocked_dataloader_instantiation_count",
            "blocked_checkpoint_load_count",
            "blocked_model_forward_count",
            "blocked_loss_count",
            "blocked_backward_count",
            "blocked_optimizer_creation_count",
            "blocked_parameter_update_count",
            "blocked_checkpoint_write_count",
        )
    )


def test_readiness_feature_semantics_and_masks(payloads):
    manifest = _manifest(payloads)
    readiness = manifest["readiness"]
    assert readiness["admit_015_training_authorization_contract_frozen"] is True
    assert readiness["admit_015_formal_evaluator_interface_contract_frozen"] is False
    assert readiness["evaluate_admit_015_implemented"] is False
    assert readiness["admit_015_independent_oracle_implemented"] is False
    assert readiness["admit_015_registered_in_engine"] is False
    assert readiness["mandatory_training_authorization_enforcement_api_frozen"] is False
    assert readiness["mandatory_training_authorization_enforcement_implemented"] is False
    assert readiness["feature_semantics_audit_completed"] is False
    assert readiness["ready_for_training"] is False
    assert manifest["canonical_mask_count"] == 5
    assert manifest["canonical_masks"] == [
        {"semantic_name": "warhead_only", "alias": "A"},
        {"semantic_name": "linker_plus_warhead", "alias": "B"},
        {"semantic_name": "scaffold_plus_warhead", "alias": "B2"},
        {"semantic_name": "scaffold_only", "alias": "B3"},
        {"semantic_name": "scaffold_plus_linker_plus_warhead", "alias": "C"},
    ]


def test_no_evaluator_result_oracle_adapter_registry_runtime_ast():
    source = (ROOT / production.__file__).read_text() if not Path(
        production.__file__
    ).is_absolute() else Path(production.__file__).read_text()
    tree = ast.parse(source)
    functions = {
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    classes = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert "evaluate_admit_015" not in functions
    assert "Admit015EvaluationResult" not in classes
    assert "_evaluate_registered_admit_015" not in functions
    assert "evaluate_admission_rule" not in functions


def test_no_model_training_imports_or_calls():
    source = Path(production.__file__).read_text()
    tree = ast.parse(source)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert not imports & {
        "torch", "numpy", "pytorch_lightning", "rdkit",
        "equivariant_diffusion", "dataset", "lightning_modules",
    }
    assert "os.replace" not in source


def test_deterministic_build(sources):
    first = production.build_artifact_payloads(sources)
    second = production.build_artifact_payloads(sources)
    assert first == second


def test_preexisting_exact_noop_preserves_inodes(tmp_path, payloads):
    root = tmp_path / "exact"
    root.mkdir()
    for name, data in payloads.items():
        (root / name).write_bytes(data)
    before = {name: (root / name).stat().st_ino for name in payloads}
    returned = production.materialize_contract(root)
    after = {name: (root / name).stat().st_ino for name in payloads}
    assert before == after
    assert returned == _manifest(payloads)


def test_normal_atomic_publish(tmp_path, payloads):
    root = tmp_path / "published"
    returned = production.materialize_contract(root)
    assert returned == _manifest(payloads)
    assert {path.name for path in root.iterdir()} == set(production.FILES)
    assert {name: (root / name).read_bytes() for name in production.FILES} == payloads
    assert not list(tmp_path.glob(f".{root.name}.*.staging"))


def test_einval_failure_is_non_destructive_and_retained(tmp_path, monkeypatch):
    root = tmp_path / "blocked"

    def fail(*args, **kwargs):
        raise OSError(errno.EINVAL, "GPFS")

    monkeypatch.setattr(production, "_rename_noreplace", fail)
    with pytest.raises(RuntimeError, match="failure staging retained"):
        production.materialize_contract(root)
    assert not root.exists()
    retained = list(tmp_path.glob(f".{root.name}.*.staging.*.retained"))
    assert len(retained) == 1
    assert {path.name for path in retained[0].iterdir()} == set(production.FILES)


def test_eexist_failure_does_not_overwrite_destination(tmp_path, monkeypatch, payloads):
    root = tmp_path / "concurrent"

    def race(source, destination, parent_fd, staging_fd=None, staging_identity=None):
        root.mkdir()
        (root / "owner.txt").write_text("other owner")
        raise OSError(errno.EEXIST, "exists")

    monkeypatch.setattr(production, "_rename_noreplace", race)
    with pytest.raises(RuntimeError, match="failure staging retained"):
        production.materialize_contract(root)
    assert (root / "owner.txt").read_text() == "other owner"


def test_independent_checker_accepts_exact6(payloads, sources):
    assert checker.verify_exact6_semantics(dict(payloads), sources)["all_checks_passed"]


def _rewrite_csv(
    data: bytes,
    columns: tuple[str, ...],
    row_index: int,
    field: str,
    value: str,
) -> bytes:
    rows = checker._parse_csv(data, columns)
    rows[row_index][field] = value
    return checker._csv_bytes(columns, rows)


def _reordered(mapping: dict, key: str) -> dict:
    return {key: mapping[key], **{item: value for item, value in mapping.items()
                                  if item != key}}


@pytest.mark.parametrize(
    "case",
    [
        "contract_routing_item", "contract_observed_design",
        "contract_authority_status", "truth_case_id",
        "truth_observed_reason", "truth_target_access",
        "truth_forbidden_access", "truth_case_passed", "value_key",
        "value_coercion", "value_owner", "safety_evaluator_present",
        "safety_ready_true", "safety_b3_absent", "issue_noncoverage",
        "issue_coverage", "manifest_extra", "manifest_missing",
        "manifest_reorder", "manifest_nested_extra",
        "manifest_nested_reorder", "manifest_output_sha_wrong",
        "manifest_permission_zero", "manifest_execution_false",
        "manifest_readiness_one", "manifest_materialization_one",
        "manifest_source_stage_false", "manifest_transition_sha_wrong",
        "manifest_recommended_next_wrong",
    ],
)
def test_sha_bypass_synchronized_semantic_tamper_rejected(
    payloads, sources, monkeypatch, case
):
    tampered = dict(payloads)
    manifest = json.loads(tampered[production.MANIFEST])
    changed_output = None
    if case.startswith("contract_"):
        field, value = {
            "contract_routing_item": ("routing_item", "tampered authority"),
            "contract_observed_design": ("observed_design", "tampered design"),
            "contract_authority_status": ("authority_status", "allowed"),
        }[case]
        tampered[production.CONTRACT] = _rewrite_csv(
            tampered[production.CONTRACT], production.CONTRACT_COLUMNS,
            0, field, value,
        )
        changed_output = production.CONTRACT
    elif case.startswith("truth_"):
        field, value = {
            "truth_case_id": ("case_id", "DRIFTED_CASE"),
            "truth_observed_reason": ("observed_reason", "WRONG_REASON"),
            "truth_target_access": ("target_key_access_count", "2"),
            "truth_forbidden_access": ("forbidden_envelope_access_count", "1"),
            "truth_case_passed": ("case_passed", "false"),
        }[case]
        tampered[production.TRUTH] = _rewrite_csv(
            tampered[production.TRUTH], production.TRUTH_COLUMNS,
            24, field, value,
        )
        changed_output = production.TRUTH
    elif case.startswith("value_"):
        row_index, field, value = {
            "value_key": (1, "observed_contract", "current_stage_download_authorized"),
            "value_coercion": (7, "observed_contract", "allowed"),
            "value_owner": (0, "responsibility_owner", "candidate"),
        }[case]
        tampered[production.VALUE_TRUST] = _rewrite_csv(
            tampered[production.VALUE_TRUST], production.VALUE_TRUST_COLUMNS,
            row_index, field, value,
        )
        changed_output = production.VALUE_TRUST
    elif case.startswith("safety_"):
        row_index, value = {
            "safety_evaluator_present": (2, "present"),
            "safety_ready_true": (22, "true"),
            "safety_b3_absent": (29, "absent"),
        }[case]
        tampered[production.SAFETY] = _rewrite_csv(
            tampered[production.SAFETY], production.SAFETY_COLUMNS,
            row_index, "observed_state", value,
        )
        changed_output = production.SAFETY
    elif case.startswith("issue_"):
        issue_columns = tuple(
            next(csv.reader(io.StringIO(tampered[production.ISSUE].decode())))
        )
        issue_rows = checker._parse_csv(tampered[production.ISSUE], issue_columns)
        if case == "issue_noncoverage":
            issue_rows[0]["successor_effective_status"] = "resolved"
        else:
            coverage = next(
                row for row in issue_rows
                if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
            )
            coverage["affected_rules"] = ""
        tampered[production.ISSUE] = checker._csv_bytes(
            issue_columns, issue_rows
        )
        changed_output = production.ISSUE
    elif case == "manifest_extra":
        manifest["extra"] = True
    elif case == "manifest_missing":
        manifest.pop("project")
    elif case == "manifest_reorder":
        manifest = _reordered(manifest, "stage")
    elif case == "manifest_nested_extra":
        manifest["authorization_contract"]["extra"] = False
    elif case == "manifest_nested_reorder":
        manifest["authorization_contract"] = _reordered(
            manifest["authorization_contract"], "authoritative_key"
        )
    elif case == "manifest_output_sha_wrong":
        manifest["output_sha256"][production.CONTRACT] = "0" * 64
    elif case == "manifest_permission_zero":
        manifest["current_permission"] = 0
    elif case == "manifest_execution_false":
        manifest["authorized_admit_015_training_execution_count"] = False
    elif case == "manifest_readiness_one":
        manifest["readiness"]["admit_015_preconditions_audited"] = 1
    elif case == "manifest_materialization_one":
        manifest["materialization"]["build_before_mutation"] = 1
    elif case == "manifest_source_stage_false":
        manifest["source_boundary"][0]["index_stage"] = False
    elif case == "manifest_transition_sha_wrong":
        manifest["precondition_transition"]["transition_rows_sha256"] = "0" * 64
    elif case == "manifest_recommended_next_wrong":
        manifest["recommended_next_step"] = "wrong"
    if changed_output is not None:
        manifest["output_sha256"][changed_output] = hashlib.sha256(
            tampered[changed_output]
        ).hexdigest()
    tampered[production.MANIFEST] = (
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    ).encode()
    monkeypatch.setattr(
        checker,
        "FROZEN_OUTPUT_SHA256",
        {
            name: hashlib.sha256(tampered[name]).hexdigest()
            for name in checker.FILES
        },
    )
    with pytest.raises(AssertionError):
        checker.verify_exact6_semantics(tampered, sources)


def test_manifest_duplicate_rejected(payloads):
    original = payloads[production.MANIFEST]
    tampered = original.rstrip()[:-1] + b',\n  "project": "duplicate"\n}\n'
    with pytest.raises(AssertionError, match="duplicate"):
        checker._parse_manifest_exact(tampered)


def _git_in(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False
    )


def _lifecycle_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    assert _git_in(repo, "init", "-q").returncode == 0
    _git_in(repo, "config", "user.name", "Lifecycle Test")
    _git_in(repo, "config", "user.email", "lifecycle@invalid")
    assert _git_in(repo, "commit", "--allow-empty", "-qm", "base").returncode == 0
    base = _git_in(repo, "rev-parse", "HEAD").stdout.strip()
    for relative in checker.EXACT10:
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    return repo, base


def _ignore_in_repo(repo: Path, relative: Path, *, directory: bool = False):
    exclude = repo / ".git/info/exclude"
    suffix = "/" if directory else ""
    exclude.write_text(
        exclude.read_text() + f"\n/{relative.as_posix()}{suffix}\n"
    )
    assert _git_in(
        repo, "check-ignore", "--no-index", "-q", "--", relative.as_posix()
    ).returncode == 0


def test_recursive_lifecycle_pre_and_post_commit(tmp_path, monkeypatch):
    repo, base = _lifecycle_repo(tmp_path)
    monkeypatch.setattr(checker, "ROOT", repo)
    monkeypatch.setattr(checker, "BASE", base)
    assert checker._lifecycle() == "pre_commit"
    assert _git_in(
        repo, "add", "--", *(path.as_posix() for path in checker.EXACT10)
    ).returncode == 0
    assert _git_in(repo, "commit", "-qm", "candidate").returncode == 0
    assert checker._lifecycle() == "post_commit"


def test_issue_inventory_is_in_recursive_stage_family():
    assert (
        "covapie_admit_015_issue_readiness_inventory"
        in checker.STAGE_FAMILY_TOKENS
    )


def test_issue_inventory_token_closes_previous_ignored_bypass(
    tmp_path, monkeypatch
):
    repo, base = _lifecycle_repo(tmp_path)
    relative = Path("docs/covapie_admit_015_issue_readiness_inventory.csv")
    (repo / relative).write_text("ignored issue inventory extra")
    _ignore_in_repo(repo, relative)
    monkeypatch.setattr(checker, "ROOT", repo)
    monkeypatch.setattr(checker, "BASE", base)

    complete_tokens = checker.STAGE_FAMILY_TOKENS
    monkeypatch.setattr(
        checker,
        "STAGE_FAMILY_TOKENS",
        tuple(
            token for token in complete_tokens
            if token != "covapie_admit_015_issue_readiness_inventory"
        ),
    )
    assert checker._lifecycle() == "pre_commit"

    monkeypatch.setattr(checker, "STAGE_FAMILY_TOKENS", complete_tokens)
    with pytest.raises(AssertionError, match="ignored stage-family path"):
        checker._lifecycle()


@pytest.mark.parametrize(
    "failure",
    [
        "ignored_exact10", "ignored_top_extra", "ignored_nested_extra",
        "tracked_nested_extra", "nonignored_nested_extra", "seventh_exact6",
        "sibling_derived_root", "empty_sibling_root", "symlink_directory",
        "forbidden_suffix", "oversized", "mixed", "staged", "dirty",
        "missing", "check_ignore_error", "base_nonancestor",
        "issue_ignored_top", "issue_ignored_nested",
        "issue_nonignored_nested", "issue_tracked_nested",
        "issue_symlink", "issue_forbidden_suffix",
    ],
)
def test_recursive_lifecycle_fail_closed(
    tmp_path, monkeypatch, failure
):
    repo, base = _lifecycle_repo(tmp_path)
    monkeypatch.setattr(checker, "ROOT", repo)
    monkeypatch.setattr(checker, "BASE", base)
    first = checker.EXACT10[0]
    if failure in {"dirty", "tracked_nested_extra", "issue_tracked_nested"}:
        _git_in(repo, "add", "--", *(path.as_posix() for path in checker.EXACT10))
        _git_in(repo, "commit", "-qm", "candidate")
    if failure == "ignored_exact10":
        _ignore_in_repo(repo, first)
    elif failure == "ignored_top_extra":
        relative = Path(
            "docs/covapie_bulk_download_admission_admit_015_"
            "training_authorization_contract_v1_ignored.md"
        )
        (repo / relative).write_text("ignored")
        _ignore_in_repo(repo, relative)
    elif failure in {
        "ignored_nested_extra", "tracked_nested_extra",
        "nonignored_nested_extra",
    }:
        relative = Path(
            "docs/nested/covapie_bulk_download_admission_admit_015_"
            "training_authorization_contract_v1_extra.md"
        )
        (repo / relative).parent.mkdir(parents=True)
        (repo / relative).write_text("nested")
        if failure == "ignored_nested_extra":
            _ignore_in_repo(repo, relative)
        elif failure == "tracked_nested_extra":
            _git_in(repo, "add", "--", relative.as_posix())
            _git_in(repo, "commit", "-qm", "tracked nested extra")
    elif failure == "seventh_exact6":
        (repo / checker.DERIVED / "seventh.csv").write_text("extra")
    elif failure in {"sibling_derived_root", "empty_sibling_root"}:
        sibling = checker.DERIVED.parent / (
            checker.STAGE + (
                "_sibling" if failure == "sibling_derived_root" else "_empty"
            )
        )
        (repo / sibling).mkdir()
        if failure == "sibling_derived_root":
            (repo / sibling / "extra.csv").write_text("extra")
    elif failure == "symlink_directory":
        target = repo / "outside"
        target.mkdir()
        relative = Path(
            "docs/covapie_bulk_download_admission_admit_015_"
            "training_authorization_contract_v1_symlink"
        )
        (repo / relative).symlink_to(target, target_is_directory=True)
    elif failure in {
        "issue_ignored_top", "issue_ignored_nested",
        "issue_nonignored_nested", "issue_tracked_nested",
    }:
        relative = Path(
            "docs/covapie_admit_015_issue_readiness_inventory.csv"
            if failure == "issue_ignored_top"
            else "docs/nested/covapie_admit_015_issue_readiness_inventory.csv"
        )
        (repo / relative).parent.mkdir(parents=True, exist_ok=True)
        (repo / relative).write_text("issue inventory extra")
        if failure in {"issue_ignored_top", "issue_ignored_nested"}:
            _ignore_in_repo(repo, relative)
        elif failure == "issue_tracked_nested":
            _git_in(repo, "add", "--", relative.as_posix())
            _git_in(repo, "commit", "-qm", "tracked issue inventory extra")
    elif failure == "issue_symlink":
        target = repo / "outside_issue.csv"
        target.write_text("outside")
        relative = Path(
            "docs/covapie_admit_015_issue_readiness_inventory.csv"
        )
        (repo / relative).symlink_to(target)
    elif failure == "issue_forbidden_suffix":
        relative = Path(
            "docs/covapie_admit_015_issue_readiness_inventory.tmp"
        )
        (repo / relative).write_text("forbidden")
    elif failure in {"forbidden_suffix", "oversized"}:
        suffix = ".tmp" if failure == "forbidden_suffix" else ".large"
        relative = Path(
            "docs/covapie_bulk_download_admission_admit_015_"
            f"training_authorization_contract_v1_extra{suffix}"
        )
        with (repo / relative).open("wb") as stream:
            if failure == "oversized":
                stream.truncate(100 * 1024 * 1024 + 1)
            else:
                stream.write(b"extra")
    elif failure == "mixed":
        _git_in(repo, "add", "--", first.as_posix())
        _git_in(repo, "commit", "-qm", "mixed")
    elif failure == "staged":
        _git_in(repo, "add", "--", first.as_posix())
    elif failure == "dirty":
        (repo / first).write_bytes((repo / first).read_bytes() + b"\n")
    elif failure == "missing":
        (repo / first).unlink()
    elif failure == "check_ignore_error":
        original_git = checker._git

        def failing_git(args, **kwargs):
            if args and args[0] == "check-ignore":
                return subprocess.CompletedProcess(args, 2, "", "failure")
            return original_git(args, **kwargs)

        monkeypatch.setattr(checker, "_git", failing_git)
    elif failure == "base_nonancestor":
        monkeypatch.setattr(checker, "BASE", "0" * 40)
    with pytest.raises((AssertionError, FileNotFoundError)):
        checker._lifecycle()


@pytest.mark.parametrize(
    "relative",
    [
        "src/covalent_ext/covapie_bulk_download_admission_admit_015_training_authorization_contract.py",
        "scripts/check_covapie_bulk_download_admission_admit_015_training_authorization_contract_v1.py",
        "tests/test_covapie_bulk_download_admission_admit_015_training_authorization_contract_v1.py",
    ],
)
def test_isolated_import_is_silent(relative, tmp_path):
    code = (
        "import importlib.util,sys;"
        f"p={str(ROOT / relative)!r};"
        "s=importlib.util.spec_from_file_location('isolated_candidate',p);"
        "m=importlib.util.module_from_spec(s);"
        "sys.modules[s.name]=m;"
        "s.loader.exec_module(m)"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path, env=env,
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_exact_manifest_json_types(payloads):
    manifest = _manifest(payloads)
    assert type(manifest["current_permission"]) is bool
    assert type(manifest["authorized_admit_015_training_execution_count"]) is int
    assert type(manifest["source_count"]) is int
    assert all(type(item["index_stage"]) is int for item in manifest["source_boundary"])
    assert all(type(value) is bool for value in manifest["readiness"].values())
    assert production.MANIFEST not in manifest["output_sha256"]


def test_protected_paths_unchanged():
    result = subprocess.run(
        [
            "git", "diff", "--name-only", "--", "data/raw", "checkpoints",
            "equivariant_diffusion", "lightning_modules.py", "dataset.py",
            "data/prepare_crossdocked.py",
        ],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    assert result.stdout == ""
