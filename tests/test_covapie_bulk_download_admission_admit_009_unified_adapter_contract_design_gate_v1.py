from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import importlib.util
import json
import shutil
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import fields
from pathlib import Path
from types import SimpleNamespace

import pytest

from covalent_ext import covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate as oracle
from covalent_ext import covapie_bulk_download_admission_admit_009_rule_logic_interface as standalone
from covalent_ext import covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate as gate


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1"
CHECKER_PATH = ROOT / "scripts/check_covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1.py"
KEY = "covapie_dup_v1_sha256_" + "1" * 64
OTHER = "covapie_dup_v1_sha256_" + "f" * 64
POLICY = "covapie_duplicate_identity_key_contract_v1"


def _checker():
    spec = importlib.util.spec_from_file_location("admit009_adapter_checker", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _route(candidate: object, **overrides: object):
    kwargs = {
        "batch_context": {"batch_duplicate_identity_keys": (OTHER,)},
        "evaluation_context": {"duplicate_identity_key_contract": POLICY},
        "download_result_context": None,
        "stage_authorization_context": None,
    }
    kwargs.update(overrides)
    return gate.route_and_project_for_design(candidate, **kwargs)


def _rewrite_csv(path: Path, mutate) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = tuple(reader.fieldnames or ())
        rows = list(reader)
    mutate(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _refresh_manifest_output_hash(root: Path, filename: str) -> None:
    path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["output_sha256"][filename] = hashlib.sha256((root / filename).read_bytes()).hexdigest()
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class CountingMapping(Mapping):
    def __init__(self, values: dict[str, object]) -> None:
        self.values = values
        self.getitem_calls: list[object] = []
        self.iterated = False

    def __getitem__(self, key: object) -> object:
        self.getitem_calls.append(key)
        return self.values[key]  # type: ignore[index]

    def __iter__(self):
        self.iterated = True
        return iter(self.values)

    def __len__(self) -> int:
        return len(self.values)


def test_identity_and_exact_field_contracts() -> None:
    assert gate.ADMISSION_RULE_ID == "ADMIT_009"
    assert gate.ADMISSION_RULE_NAME == "duplicate_identity_precheck"
    assert gate.ADAPTER_ID == "covapie_admit_009_unified_adapter_v1"
    assert gate.CURRENT_REGISTERED_RULE_ORDER == tuple(f"ADMIT_{i:03d}" for i in range(1, 9))
    assert gate.FUTURE_REGISTERED_RULE_ORDER == tuple(f"ADMIT_{i:03d}" for i in range(1, 10))
    assert tuple(field.name for field in fields(gate.UnifiedAdmissionEvaluationDesignRecord)) == gate.RESULT_FIELDS
    assert gate.CONTEXT_ITEMS == ("duplicate_identity_key_contract", "batch_duplicate_identity_keys")
    contract = gate._contract_rows()
    assert (contract[6]["contract_group"], contract[6]["contract_subject"], contract[6]["contract_value"]) == (
        "runtime_continuity", "public_dispatch",
        "new_successor_function_same_exact8_signature_and_dispatch_semantics_uses_exact9_registry_not_exact8_function_identity",
    )
    assert all("evaluate_admission_rule_exact8_identity" not in row.values() for row in contract)
    runtime_tree = ast.parse((ROOT / gate.SOURCE_PATHS[0]).read_text(encoding="utf-8"))
    runtime_functions = {node.name for node in runtime_tree.body if isinstance(node, ast.FunctionDef)}
    runtime_assignments = {
        target.id: ast.unparse(node.value)
        for node in runtime_tree.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
    }
    assert "evaluate_admission_rule" in runtime_functions
    assert "evaluate_admission_rule" not in runtime_assignments
    assert runtime_assignments["UnifiedAdmissionRuleEvaluation"] == "predecessor.UnifiedAdmissionRuleEvaluation"
    assert runtime_assignments["UnifiedAdmissionDispatchError"] == "predecessor.UnifiedAdmissionDispatchError"


def test_exact18_snapshot_is_ordered_and_verified() -> None:
    snapshot = gate.build_frozen_source_snapshot(ROOT)
    assert len(snapshot.records) == 18
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert all(record.expected_sha256 == record.base_tree_sha256 == record.filesystem_sha256 for record in snapshot.records)


@pytest.mark.parametrize(
    ("overrides", "reason"),
    (
        ({"batch_context": None}, "ADMIT_009_BATCH_CONTEXT_MAPPING_REQUIRED"),
        ({"batch_context": {}}, "ADMIT_009_BATCH_DUPLICATE_IDENTITY_KEYS_REQUIRED"),
        ({"evaluation_context": None}, "ADMIT_009_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ({"evaluation_context": {}}, "ADMIT_009_DUPLICATE_IDENTITY_KEY_CONTRACT_REQUIRED"),
        ({"download_result_context": object()}, "ADMIT_009_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ({"stage_authorization_context": object()}, "ADMIT_009_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
    ),
)
def test_context_failures_are_exact6_and_precede_candidate(overrides: dict[str, object], reason: str) -> None:
    class Bomb:
        def __getitem__(self, key: object) -> object:
            raise AssertionError("candidate accessed")

    calls: list[str] = []
    with pytest.raises(gate.AdapterContractDesignError) as caught:
        _route(Bomb(), formal_evaluator=lambda *args: calls.append("formal"), oracle_callable=lambda *args: calls.append("oracle"), **overrides)
    error = caught.value
    assert tuple(getattr(error, name) for name in gate.DISPATCH_ERROR_FIELDS) == (
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "ADMIT_009", True, True, True, reason,
    )
    assert calls == []


def test_context_precedence_is_fixed() -> None:
    with pytest.raises(gate.AdapterContractDesignError) as caught:
        gate.route_and_project_for_design(
            object(), batch_context=None, evaluation_context=None,
            download_result_context=object(), stage_authorization_context=object(),
        )
    assert caught.value.reason == gate.CONTEXT_REASONS["batch_context"]


def test_mapping_subclasses_use_one_direct_lookup_without_iteration() -> None:
    candidate = CountingMapping({"duplicate_identity_key": KEY, "ignored": object()})
    batch = CountingMapping({"batch_duplicate_identity_keys": (OTHER,), "ignored": object()})
    policy = CountingMapping({"duplicate_identity_key_contract": POLICY, "ignored": object()})
    result = gate.route_and_project_for_design(
        candidate, batch_context=batch, evaluation_context=policy,
        download_result_context=None, stage_authorization_context=None,
    )
    assert result.outcome == "passed"
    assert candidate.getitem_calls == ["duplicate_identity_key"]
    assert batch.getitem_calls == ["batch_duplicate_identity_keys"]
    assert policy.getitem_calls == ["duplicate_identity_key_contract"]
    assert not candidate.iterated and not batch.iterated and not policy.iterated


def test_candidate_nonmapping_and_missing_are_adapter_invalid_without_calls() -> None:
    calls: list[str] = []
    formal = lambda *args: calls.append("formal")
    independent = lambda *args: calls.append("oracle")
    for candidate, reason in ((object(), gate.CANDIDATE_MAPPING_REASON), ({}, gate.MISSING_REASON)):
        result = _route(candidate, formal_evaluator=formal, oracle_callable=independent)
        assert (result.outcome, result.passed, result.blocks_candidate, result.reason) == ("invalid", False, True, reason)
        assert result.normalized_values == result.validated_candidate_fields == ()
        assert result.consumed_candidate_fields == gate.CANDIDATE_FIELDS
        assert result.consumed_context_items == gate.CONTEXT_ITEMS
    assert calls == []


@pytest.mark.parametrize("scalar", (None, 7, "", type("S", (str,), {})(KEY), "é", " " + KEY, "bad", KEY))
def test_present_candidate_values_are_forwarded_not_missing(scalar: object) -> None:
    seen: list[tuple[object, object, object]] = []
    def formal(a: object, b: object, c: object):
        seen.append((a, b, c))
        return standalone.evaluate_admit_009(a, b, c)
    _route({"duplicate_identity_key": scalar}, formal_evaluator=formal)
    assert len(seen) == 1 and seen[0][0] is scalar


def test_original_three_objects_and_exact_call_counts_are_preserved() -> None:
    scalar, batch, policy = KEY, (OTHER,), POLICY
    calls: list[tuple[str, object, object, object]] = []
    def formal(a: object, b: object, c: object):
        calls.append(("formal", a, b, c)); return standalone.evaluate_admit_009(a, b, c)
    def classify(a: object, b: object, c: object):
        calls.append(("oracle", a, b, c)); return oracle.classify_admit_009_duplicate_identity_key_design(a, b, c)
    result = gate.route_and_project_for_design(
        {"duplicate_identity_key": scalar}, batch_context={"batch_duplicate_identity_keys": batch},
        evaluation_context={"duplicate_identity_key_contract": policy},
        download_result_context=None, stage_authorization_context=None,
        formal_evaluator=formal, oracle_callable=classify,
    )
    assert [call[0] for call in calls] == ["formal", "oracle"]
    assert all(call[1] is scalar and call[2] is batch and call[3] is policy for call in calls)
    assert result.outcome == "passed"


def test_source_wrong_type_and_subclass_fail_before_oracle() -> None:
    source = standalone.evaluate_admit_009(KEY, (OTHER,), POLICY)
    class ResultSubclass(type(source)):
        pass
    subclass = object.__new__(ResultSubclass)
    for name in gate.STANDALONE_RESULT_FIELDS:
        object.__setattr__(subclass, name, getattr(source, name))
    for bad, expected_reason in ((object(), gate.SOURCE_TYPE_REASON), (subclass, gate.SOURCE_TYPE_REASON)):
        oracle_calls: list[object] = []
        with pytest.raises(gate.AdapterContractDesignError) as caught:
            _route({"duplicate_identity_key": KEY}, formal_evaluator=lambda *args, bad=bad: bad,
                   oracle_callable=lambda *args: oracle_calls.append(args))
        assert caught.value.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
        assert caught.value.adapter_ready is False and caught.value.reason == expected_reason
        assert oracle_calls == []


def test_source_storage_and_dataclass_order_are_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    source = standalone.evaluate_admit_009(KEY, (OTHER,), POLICY)
    monkeypatch.setattr(gate, "fields", lambda value: tuple(reversed(fields(standalone.Admit009EvaluationResult))))
    decision = gate.validate_source_shape_and_invariants_for_design(source)
    assert (decision.accepted, decision.reason, decision.adapter_ready) == (False, gate.SOURCE_INVARIANT_REASON, False)


def test_oracle_full_exact10_mismatch_is_adapter_not_ready() -> None:
    observed: list[object] = []
    def mismatching(a: object, b: object, c: object):
        observed.append(a)
        value = dict(oracle.classify_admit_009_duplicate_identity_key_design(a, b, c))
        value["reason"] = "duplicate_identity_key_already_present"
        value["outcome"] = "blocked"
        value["passed"] = False
        value["blocks_candidate"] = True
        return value
    with pytest.raises(gate.AdapterContractDesignError) as caught:
        _route({"duplicate_identity_key": KEY}, oracle_callable=mismatching)
    assert caught.value.reason == gate.SOURCE_INVARIANT_REASON
    assert caught.value.adapter_ready is False and len(observed) == 1


@pytest.mark.parametrize(
    ("scalar", "batch", "policy", "outcome"),
    ((KEY, (OTHER,), POLICY, "passed"), (KEY, (KEY,), POLICY, "blocked"),
     (None, (), POLICY, "invalid"), (KEY, (), None, "invalid"), (KEY, [], POLICY, "invalid")),
)
def test_projection_is_complete_passthrough(scalar: object, batch: object, policy: object, outcome: str) -> None:
    source = standalone.evaluate_admit_009(scalar, batch, policy)
    projected = gate.project_exact10_to_exact13_for_design(source)
    assert projected.outcome == outcome
    assert projected.normalized_values == projected.validated_candidate_fields == source.validated_candidate_fields
    assert projected.consumed_candidate_fields == source.consumed_candidate_fields
    assert projected.consumed_context_items == source.consumed_context_items
    assert projected.blocks_candidate is (outcome != "passed")
    assert projected.adapter_id == gate.ADAPTER_ID


def test_natural_evidence_counts_and_readiness() -> None:
    state = gate.build_design_state(ROOT)
    assert tuple(len(state[key]) for key in ("contract_rows", "routing_rows", "truth_rows", "safety_rows", "issue_rows")) == (75, 52, 49, 35, 11)
    _, manifest = gate._payloads(state)
    assert len(manifest) == 130 and len(manifest["readiness"]) == 36
    assert sum(manifest["readiness"].values()) == 20
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    assert "runtime_public_api_reused_by_identity" not in manifest
    assert manifest["future_exact9_public_dispatch_contract"] == (
        "new_successor_function_same_exact8_signature_and_dispatch_semantics_uses_exact9_registry"
    )
    assert manifest["runtime_result_type_reused_by_identity"] == "UnifiedAdmissionRuleEvaluation"
    assert manifest["runtime_dispatch_error_type_reused_by_identity"] == "UnifiedAdmissionDispatchError"
    assert manifest["future_first_eight_handler_identity_reused"] == {
        rule_id: True for rule_id in gate.CURRENT_REGISTERED_RULE_ORDER
    }


def test_issue_output_is_predecessor_byte_identical() -> None:
    predecessor = ROOT / gate.SOURCE_PATHS[7]
    output = OUTPUT_ROOT / gate.ISSUE_FILENAME
    assert output.read_bytes() == predecessor.read_bytes()
    assert hashlib.sha256(output.read_bytes()).hexdigest() == "2c461d4416742dda734789ba6768995c6d641fb2d1b6c460a0f80ea194482e92"


def test_double_materialization_is_byte_identical(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    gate.run_covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1(first, repo_root=ROOT)
    gate.run_covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1(second, repo_root=ROOT)
    assert {path.name: path.read_bytes() for path in first.iterdir()} == {path.name: path.read_bytes() for path in second.iterdir()}


def test_checker_accepts_outputs_and_frozen_hashes() -> None:
    checker = _checker()
    assert checker._validate_output_tree() == checker.FROZEN_OUTPUT_SHA256


def test_checker_false_hash_mode_rejects_semantic_tamper_with_refreshed_manifest(tmp_path: Path) -> None:
    checker = _checker()
    target = tmp_path / "outputs"
    shutil.copytree(OUTPUT_ROOT, target)
    manifest_path = target / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text())
    manifest["readiness"]["admit_009_registered_in_engine"] = True
    manifest["admit_009_registered_in_engine"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(AssertionError, match="manifest semantic mismatch|readiness mirror drift"):
        checker._validate_output_tree(target, enforce_frozen_hashes=False)


@pytest.mark.parametrize(
    ("filename", "mutate"),
    (
        (gate.CONTRACT_FILENAME, lambda rows: rows[6].update({
            "contract_group": "runtime_reuse", "contract_subject": "public_api",
            "contract_value": "evaluate_admission_rule_exact8_identity",
        })),
        (gate.ROUTING_FILENAME, lambda rows: rows[0].__setitem__("expected_reason", "wrong")),
        (gate.TRUTH_FILENAME, lambda rows: rows[0].__setitem__("expected_reason", "wrong")),
        (gate.SAFETY_FILENAME, lambda rows: rows[0].__setitem__("observed_executed", "false")),
    ),
)
def test_checker_rejects_csv_semantic_tamper_with_refreshed_manifest_hash(
    tmp_path: Path, filename: str, mutate
) -> None:
    checker = _checker()
    target = tmp_path / "outputs"
    shutil.copytree(OUTPUT_ROOT, target)
    _rewrite_csv(target / filename, mutate)
    _refresh_manifest_output_hash(target, filename)
    with pytest.raises(AssertionError):
        checker._validate_output_tree(target, enforce_frozen_hashes=False)


def test_checker_rejects_issue_transition_with_refreshed_manifest_hash(tmp_path: Path) -> None:
    checker = _checker()
    target = tmp_path / "outputs"
    shutil.copytree(OUTPUT_ROOT, target)
    _rewrite_csv(
        target / gate.ISSUE_FILENAME,
        lambda rows: next(row for row in rows if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE").__setitem__(
            "affected_rules", "ADMIT_010|ADMIT_011"
        ),
    )
    _refresh_manifest_output_hash(target, gate.ISSUE_FILENAME)
    with pytest.raises(AssertionError, match="issue bytes|coverage"):
        checker._validate_output_tree(target, enforce_frozen_hashes=False)


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("future_exact9_public_dispatch_contract", "reuse_exact8_evaluate_admission_rule_by_identity"),
        ("future_first_eight_handler_identity_reused", {"ADMIT_001": False}),
        ("context_routing_order", ["wrong"]),
        ("adapter_missing_categories", ["exact_none"]),
        ("provider_fields_consumed", ["provider_duplicate_key"]),
        ("real_provider_duplicate_identity_mapping_validated", True),
        ("admit_009_registered_in_engine", True),
        ("ready_for_training", True),
    ),
)
def test_checker_rejects_manifest_semantic_drift_without_frozen_hashes(
    tmp_path: Path, key: str, value: object
) -> None:
    checker = _checker()
    target = tmp_path / "outputs"
    shutil.copytree(OUTPUT_ROOT, target)
    manifest_path = target / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[key] = value
    if key in manifest["readiness"]:
        manifest["readiness"][key] = value
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker._validate_output_tree(target, enforce_frozen_hashes=False)


def test_checker_rejects_unknown_manifest_key_without_hash_enforcement(tmp_path: Path) -> None:
    checker = _checker()
    target = tmp_path / "outputs"
    shutil.copytree(OUTPUT_ROOT, target)
    manifest_path = target / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text())
    manifest["unknown"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(AssertionError, match="unknown key|key/readiness count"):
        checker._validate_output_tree(target, enforce_frozen_hashes=False)


def test_output_tree_rejects_extra_and_symlink(tmp_path: Path) -> None:
    checker = _checker()
    target = tmp_path / "outputs"
    shutil.copytree(OUTPUT_ROOT, target)
    (target / "extra").write_text("x")
    with pytest.raises(AssertionError, match="inventory"):
        checker._validate_output_tree(target, enforce_frozen_hashes=False)
    (target / "extra").unlink()
    (target / gate.CONTRACT_FILENAME).unlink()
    (target / gate.CONTRACT_FILENAME).symlink_to(OUTPUT_ROOT / gate.CONTRACT_FILENAME)
    with pytest.raises(AssertionError, match="inventory"):
        checker._validate_output_tree(target, enforce_frozen_hashes=False)


def test_design_source_has_no_runtime_handler_registry_or_dispatcher() -> None:
    checker = _checker()
    checker._verify_ast()


def test_production_and_checker_import_silently_without_output_changes() -> None:
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in OUTPUT_ROOT.iterdir()}
    command = (
        "import importlib.util; "
        "import covalent_ext.covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate; "
        f"s=importlib.util.spec_from_file_location('c', {str(CHECKER_PATH)!r}); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m)"
    )
    completed = subprocess.run((sys.executable, "-c", command), cwd=ROOT, capture_output=True, text=True, check=False)
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in OUTPUT_ROOT.iterdir()}
    assert completed.returncode == 0 and completed.stdout == completed.stderr == ""
    assert before == after


def test_generated_csvs_have_exact_headers_and_no_padding() -> None:
    checker = _checker()
    expectations = ((gate.CONTRACT_FILENAME, checker.CONTRACT_COLUMNS, 75),
                    (gate.ROUTING_FILENAME, checker.ROUTING_COLUMNS, 52),
                    (gate.TRUTH_FILENAME, checker.TRUTH_COLUMNS, 49),
                    (gate.SAFETY_FILENAME, checker.SAFETY_COLUMNS, 35),
                    (gate.ISSUE_FILENAME, checker.ISSUE_COLUMNS, 11))
    for name, header, count in expectations:
        with (OUTPUT_ROOT / name).open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
        assert tuple(reader.fieldnames or ()) == header and len(rows) == count
        assert all("padding" not in json.dumps(row).lower() for row in rows)


def test_required_exact52_negative_contract_inventory_is_explicit() -> None:
    cases = (
        "batch_context_nonmapping", "batch_required_key_missing", "evaluation_context_nonmapping",
        "policy_required_key_missing", "download_context_non_none", "stage_context_non_none",
        "context_failure_candidate_access", "context_failure_formal_call", "context_failure_oracle_call",
        "candidate_nonmapping_dispatch_error", "candidate_missing_formal_call", "none_folded_to_missing",
        "empty_folded_to_missing", "str_subclass_folded_to_missing", "mapping_subclass_rejected",
        "required_key_multiple_reads", "input_object_copied", "batch_sorted_or_deduplicated",
        "formal_argument_order", "formal_call_count", "source_nonexact_type_accepted",
        "result_subclass_accepted", "vars_not_exact_dict_or_order", "dataclass_field_order_drift",
        "partial_source_validation", "reconstruction_mismatch", "oracle_called_after_source_failure",
        "oracle_call_count", "oracle_object_identity", "partial_source_oracle_comparison",
        "passed_projection", "blocked_projection", "invalid_blocks_false",
        "policy_invalid_pair_lost", "batch_invalid_pair_lost", "normalized_validated_drift",
        "candidate_invalid_context_order", "adapter_id_drift", "dispatch_boundary_confusion",
        "coverage_removes_admit009", "issue_bytes_changed", "provider_mapping_claimed_validated",
        "fabricated_real_provider_key", "handler_or_registry_present", "exact8_runtime_modified",
        "source_sha_symlink_or_escape", "raw_or_checkpoint_source", "output_missing_extra_or_symlink",
        "semantic_tamper_refreshed_hash", "readiness_mirror_drift", "unknown_manifest_key",
        "import_side_effect",
    )
    assert len(cases) == len(set(cases)) == 52
    evidence = json.dumps({
        "contract": gate._contract_rows(), "routing": gate._routing_rows(),
        "truth": gate._truth_rows(), "safety": gate._safety_rows(),
        "readiness": gate.READINESS,
    }, sort_keys=True)
    anchors = (
        "batch_non_mapping", "batch_key_missing", "evaluation_non_mapping",
        "evaluation_key_missing", "candidate_bomb", "candidate_non_mapping",
        "candidate_key_absent", "formal_exactly_once", "oracle_exactly_once",
        "three_object_identity", "subclass_rejected", "storage_order_rejected",
        "dataclass_order_rejected", "reconstruction_rejected", "full_exact10_mismatch",
        "normalized_values", "adapter_invalid_consumed_context", "byte_identical_no_transition",
        "provider_key_generation", "actual_adapter_handler", "exact9_runtime", "raw_read",
        "checkpoint", "feature_semantics_audit_required_before_training",
    )
    assert all(anchor in evidence for anchor in anchors)
