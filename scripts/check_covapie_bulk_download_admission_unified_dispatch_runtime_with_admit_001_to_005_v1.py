#!/usr/bin/env python3
"""Independent checker for the ADMIT_001-to-005 successor runtime."""

from __future__ import annotations

import csv
import hashlib
import inspect
import io
import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path
from types import MappingProxyType
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005
    as runtime,
)


EXPECTED_OUTPUT_SHA256 = {
    "covapie_admit_001_to_005_runtime_contract.csv": "36c43797e622177d70a0b206d50cd2780d9e3ed0e62b78a052daa287d466a2fb",
    "covapie_admit_001_to_005_runtime_truth_matrix.csv": "1bf3d62d9f6dfe01cdd8850b9bd67dfa30c9d099bde8d4f613a9ecf6989d47b2",
    "covapie_admit_001_to_005_registry_routing_and_oracle_audit.csv": "b7302fd4b0776711cec62283a15ade588d1822e68c39ddc7251c7512e0d650ad",
    "covapie_admit_001_to_005_runtime_safety_audit.csv": "6f74a0e3c89c8df62ff1547256f64afd291103b6b20b7ed00c04577809eee77b",
    "covapie_admit_001_to_005_runtime_issue_inventory.csv": "7f815f3358ae3e53d296bc3ec0a129cd459184a76aa5169649b73fb1440e28bc",
    "covapie_admit_001_to_005_runtime_manifest.json": "699143ca47d8ff51dbf9779fce2a95ef537d1d6053d93a73f941725d6219256e",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline=""))
    assert reader.fieldnames is not None
    rows = [dict(row) for row in reader]
    assert all(tuple(row) == tuple(reader.fieldnames) for row in rows)
    return tuple(reader.fieldnames), rows


def _validate_output_root(root: Path, expected_sha: dict[str, str]) -> None:
    assert root.is_dir() and not root.is_symlink()
    assert {path.name for path in root.iterdir()} == set(runtime.OUTPUT_FILES)
    assert set(expected_sha) == set(runtime.OUTPUT_FILES)
    for filename, expected in expected_sha.items():
        path = root / filename
        assert path.is_file() and not path.is_symlink()
        assert _sha256(path) == expected
    manifest = json.loads((root / runtime.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert type(manifest) is dict
    assert manifest["all_checks_passed"] is True
    assert manifest["registered_rule_count"] == 5
    assert manifest["registered_rule_ids"] == list(runtime.ADAPTER_READY_RULE_IDS)
    assert manifest["phase4_runtime_modified"] is False
    assert manifest["admit_005_implemented"] is True
    assert manifest["admit_005_registered"] is True
    assert manifest["admit_006_to_015_registered"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["feature_semantics_audit_required"] is True
    assert manifest["checker_freezes_all_six_output_sha256"] is True
    assert manifest["output_sha256_excludes_manifest_self_hash"] is True
    assert set(manifest["output_sha256"]) == set(runtime.CSV_OUTPUTS)
    for filename, claimed in manifest["output_sha256"].items():
        assert _sha256(root / filename) == claimed


def _assert_error(call: object, code: str, reason: str) -> runtime.UnifiedAdmissionDispatchError:
    try:
        call()
    except runtime.UnifiedAdmissionDispatchError as error:
        assert error.code == code
        assert error.reason == reason
        return error
    raise AssertionError("dispatch did not fail closed")


def _check_runtime_directly(snapshot: runtime.FrozenSourceSnapshot) -> None:
    assert runtime.UnifiedAdmissionRuleEvaluation is runtime.phase4.UnifiedAdmissionRuleEvaluation
    assert runtime.UnifiedAdmissionDispatchError is runtime.phase4.UnifiedAdmissionDispatchError
    assert runtime.RESULT_FIELDS is runtime.phase4.RESULT_FIELDS
    assert runtime.DISPATCH_ERROR_FIELDS is runtime.phase4.DISPATCH_ERROR_FIELDS
    assert runtime.RESULT_SCHEMA_VERSION is runtime.phase4.RESULT_SCHEMA_VERSION
    assert runtime.OUTCOME_VOCABULARY is runtime.phase4.OUTCOME_VOCABULARY
    assert len(runtime.RESULT_FIELDS) == 13
    assert len(runtime.DISPATCH_ERROR_FIELDS) == 6
    assert inspect.signature(runtime.evaluate_admission_rule) == inspect.signature(runtime.phase4.evaluate_admission_rule)

    assert type(runtime.EVALUATOR_REGISTRY) is MappingProxyType
    assert tuple(runtime.EVALUATOR_REGISTRY) == tuple(f"ADMIT_{index:03d}" for index in range(1, 6))
    for rule_id in runtime.KNOWN_RULE_IDS[:4]:
        assert runtime.EVALUATOR_REGISTRY[rule_id] is runtime.phase4.EVALUATOR_REGISTRY[rule_id]
        assert runtime.RULE_NAMES[rule_id] == runtime.phase4.RULE_NAMES[rule_id]
        assert runtime.ADAPTER_IDS[rule_id] == runtime.phase4.ADAPTER_IDS[rule_id]
    assert runtime.EVALUATOR_REGISTRY["ADMIT_005"] is runtime._evaluate_registered_admit_005
    assert not hasattr(runtime, "evaluate_all_rules")

    _assert_error(
        lambda: runtime.evaluate_admission_rule(5, {}),  # type: ignore[arg-type]
        "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
        "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
    )
    _assert_error(
        lambda: runtime.evaluate_admission_rule("ADMIT_999", {}),
        "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
        "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
    )
    for rule_id in runtime.KNOWN_RULE_IDS[5:]:
        error = _assert_error(
            lambda rule_id=rule_id: runtime.evaluate_admission_rule(rule_id, {}),
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
        )
        assert (error.known_rule, error.callable_discovered, error.adapter_ready) == (
            True,
            False,
            False,
        )

    counts = Counter()

    def forbidden(name: str) -> object:
        def call(*args: object) -> object:
            counts[name] += 1
            raise AssertionError(name)

        return call

    with (
        patch.object(runtime.admit005, "evaluate_admit_005", forbidden("formal")),
        patch.object(runtime.admit005_oracle, "classify_admit_004_admit_005_atom_scope_design", forbidden("scope")),
        patch.object(runtime.admit005_oracle, "validate_generic_covalent_residue_atom_name", forbidden("atom")),
    ):
        error = _assert_error(
            lambda: runtime.evaluate_admission_rule(
                "ADMIT_005",
                {},
                batch_context={},
                evaluation_context={},
                download_result_context={},
                stage_authorization_context={},
            ),
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            "ADMIT_005_BATCH_CONTEXT_MUST_BE_NONE",
        )
        assert error.adapter_ready is True
    assert counts == {}

    invalid = runtime.evaluate_admission_rule("ADMIT_005", {})
    assert invalid.reason == "ADMIT_005_CANDIDATE_FIELD_MISSING:covalent_residue_name"
    assert invalid.consumed_candidate_fields == runtime.ADMIT_005_CANDIDATE_FIELDS
    assert invalid.normalized_values == invalid.validated_candidate_fields == ()

    residue = object()
    atom = object()
    candidate = {
        "covalent_residue_name": residue,
        "covalent_residue_atom_name": atom,
        "extra": object(),
    }
    before = dict(candidate)
    source = runtime.admit005.evaluate_admit_005("CYS", "SG")
    scope = runtime.admit005_oracle.classify_admit_004_admit_005_atom_scope_design("CYS", "SG")
    atom_result = runtime.admit005_oracle.validate_generic_covalent_residue_atom_name("SG")
    calls: dict[str, list[object]] = {"formal": [], "scope": [], "atom": []}
    with (
        patch.object(runtime.admit005, "evaluate_admit_005", lambda r, a: calls["formal"].append((r, a)) or source),
        patch.object(runtime.admit005_oracle, "classify_admit_004_admit_005_atom_scope_design", lambda r, a: calls["scope"].append((r, a)) or scope),
        patch.object(runtime.admit005_oracle, "validate_generic_covalent_residue_atom_name", lambda a: calls["atom"].append(a) or atom_result),
    ):
        passed = runtime.evaluate_admission_rule("ADMIT_005", candidate)
    assert passed.outcome == "passed"
    assert calls == {"formal": [(residue, atom)], "scope": [(residue, atom)], "atom": [atom]}
    assert candidate == before

    standalone_rows = runtime._validate_predecessors(snapshot)["standalone_truth_rows"]
    distribution: Counter[str] = Counter()
    for row in standalone_rows:
        residue_value = runtime._decode_truth_input(row["residue_input_kind"], row["residue_input_display"])
        atom_value = runtime._decode_truth_input(row["atom_input_kind"], row["atom_input_display"])
        projected = runtime.evaluate_admission_rule(
            "ADMIT_005",
            {
                "covalent_residue_name": residue_value,
                "covalent_residue_atom_name": atom_value,
            },
        )
        assert projected.outcome == row["observed_outcome"]
        assert projected.reason == row["observed_reason"]
        assert projected.normalized_values == projected.validated_candidate_fields
        distribution[projected.outcome] += 1
    assert distribution == {"passed": 2, "rejected": 6, "invalid": 14}
    rejected = runtime.evaluate_admission_rule(
        "ADMIT_005",
        {"covalent_residue_name": "SER", "covalent_residue_atom_name": "SG"},
    )
    assert (rejected.outcome, rejected.passed, rejected.blocks_candidate) == (
        "rejected",
        False,
        True,
    )

    bad = runtime.admit005.evaluate_admit_005("CYS", "SG")
    object.__setattr__(bad, "evaluator_io_used", True)
    prevalidation_counts = Counter()
    with (
        patch.object(runtime.admit005, "evaluate_admit_005", lambda *args: prevalidation_counts.update(["formal"]) or bad),
        patch.object(runtime.admit005_oracle, "classify_admit_004_admit_005_atom_scope_design", lambda *args: prevalidation_counts.update(["scope"])),
        patch.object(runtime.admit005_oracle, "validate_generic_covalent_residue_atom_name", lambda *args: prevalidation_counts.update(["atom"])),
    ):
        error = _assert_error(
            lambda: runtime.evaluate_admission_rule(
                "ADMIT_005",
                {"covalent_residue_name": "CYS", "covalent_residue_atom_name": "SG"},
            ),
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            "ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        )
        assert error.adapter_ready is False
    assert prevalidation_counts == {"formal": 1}

    valid = runtime.admit005.evaluate_admit_005("CYS", "SG")
    mismatch_scope = runtime.admit005_oracle.classify_admit_004_admit_005_atom_scope_design("SER", "SG")
    good_atom = runtime.admit005_oracle.validate_generic_covalent_residue_atom_name("SG")
    mismatch_counts = Counter()
    with (
        patch.object(runtime.admit005, "evaluate_admit_005", lambda *args: mismatch_counts.update(["formal"]) or valid),
        patch.object(runtime.admit005_oracle, "classify_admit_004_admit_005_atom_scope_design", lambda *args: mismatch_counts.update(["scope"]) or mismatch_scope),
        patch.object(runtime.admit005_oracle, "validate_generic_covalent_residue_atom_name", lambda *args: mismatch_counts.update(["atom"]) or good_atom),
    ):
        _assert_error(
            lambda: runtime.evaluate_admission_rule(
                "ADMIT_005",
                {"covalent_residue_name": "CYS", "covalent_residue_atom_name": "SG"},
            ),
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            "ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        )
    assert mismatch_counts == {"formal": 1, "scope": 1, "atom": 1}

    for case in runtime._phase4_parity_definitions():
        values: list[object] = []
        for module in (runtime, runtime.phase4):
            try:
                values.append(module.evaluate_admission_rule(case["rule"], case["candidate"], **case["kwargs"]))
            except runtime.UnifiedAdmissionDispatchError as error:
                values.append(error)
        assert type(values[0]) is type(values[1])
        names = runtime.RESULT_FIELDS if type(values[0]) is runtime.UnifiedAdmissionRuleEvaluation else runtime.DISPATCH_ERROR_FIELDS
        assert tuple(getattr(values[0], name) for name in names) == tuple(
            getattr(values[1], name) for name in names
        )


def _check_outputs_and_negative_paths(state: dict[str, object]) -> None:
    default_root = REPO_ROOT / runtime.DEFAULT_OUTPUT_ROOT
    _validate_output_root(default_root, EXPECTED_OUTPUT_SHA256)

    contract_header, contract_rows = _csv(default_root / runtime.CONTRACT_FILENAME)
    truth_header, truth_rows = _csv(default_root / runtime.TRUTH_FILENAME)
    registry_header, registry_rows = _csv(default_root / runtime.REGISTRY_FILENAME)
    safety_header, safety_rows = _csv(default_root / runtime.SAFETY_FILENAME)
    issue_header, issue_rows = _csv(default_root / runtime.ISSUE_FILENAME)
    assert contract_header == runtime.CONTRACT_COLUMNS
    assert truth_header == runtime.TRUTH_COLUMNS
    assert registry_header == runtime.REGISTRY_COLUMNS
    assert safety_header == runtime.SAFETY_COLUMNS
    assert issue_header == runtime.ISSUE_COLUMNS
    assert len(contract_rows) == 35
    assert len({row["contract_id"] for row in contract_rows}) == 35
    assert len(truth_rows) == 71
    assert Counter(row["case_group"] for row in truth_rows) == state["truth_group_counts"]
    assert len(registry_rows) == 15
    assert tuple(row["admission_rule_id"] for row in registry_rows) == runtime.KNOWN_RULE_IDS
    assert all(row["registered"] == ("true" if index < 5 else "false") for index, row in enumerate(registry_rows))
    assert all(row["audit_passed"] == "true" for row in registry_rows)
    assert all(row["safety_passed"] == "true" for row in safety_rows)
    assert len(issue_rows) == 11
    issue_map = {row["issue_id"]: row for row in issue_rows}
    coverage = issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    assert coverage["affected_rules"] == "|".join(runtime.KNOWN_RULE_IDS[5:])
    assert coverage["integration_transition"] == "admit_005_implemented_and_removed_from_open_coverage_scope"
    assert coverage["severity"] == "blocking" and coverage["status"] == "open"
    assert coverage["issue_count"] == "1"
    assert issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["issue_count"] == "11"
    assert issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["status"] == "open"
    assert issue_map["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] == "open"

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "outputs"
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005_v1(root)
        first = {path.name: path.read_bytes() for path in root.iterdir()}
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005_v1(root)
        second = {path.name: path.read_bytes() for path in root.iterdir()}
        assert first == second
        generated_sha = {name: hashlib.sha256(content).hexdigest() for name, content in first.items()}
        assert generated_sha == EXPECTED_OUTPUT_SHA256
        assert not tuple(root.glob("*.tmp")) and not tuple(root.glob("*.part"))

        def fresh(name: str) -> Path:
            copy = Path(temporary) / name
            shutil.copytree(root, copy)
            return copy

        missing = fresh("missing")
        (missing / runtime.CONTRACT_FILENAME).unlink()
        try:
            _validate_output_root(missing, EXPECTED_OUTPUT_SHA256)
        except AssertionError:
            pass
        else:
            raise AssertionError("missing output accepted")

        extra = fresh("extra")
        (extra / "unexpected.txt").write_text("unexpected", encoding="utf-8")
        try:
            _validate_output_root(extra, EXPECTED_OUTPUT_SHA256)
        except AssertionError:
            pass
        else:
            raise AssertionError("extra output accepted")

        tamper = fresh("tamper")
        with (tamper / runtime.TRUTH_FILENAME).open("ab") as handle:
            handle.write(b"tamper")
        try:
            _validate_output_root(tamper, EXPECTED_OUTPUT_SHA256)
        except AssertionError:
            pass
        else:
            raise AssertionError("tampered output accepted")

        overclaim = fresh("overclaim")
        manifest_path = overclaim / runtime.MANIFEST_FILENAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["ready_for_training"] = True
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        try:
            _validate_output_root(overclaim, {**EXPECTED_OUTPUT_SHA256, runtime.MANIFEST_FILENAME: _sha256(manifest_path)})
        except AssertionError:
            pass
        else:
            raise AssertionError("readiness overclaim accepted")

        bad_hash = fresh("bad_hash")
        manifest_path = bad_hash / runtime.MANIFEST_FILENAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["output_sha256"][runtime.CONTRACT_FILENAME] = "0" * 64
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        try:
            _validate_output_root(bad_hash, {**EXPECTED_OUTPUT_SHA256, runtime.MANIFEST_FILENAME: _sha256(manifest_path)})
        except AssertionError:
            pass
        else:
            raise AssertionError("manifest hash tamper accepted")

        symlink_root = Path(temporary) / "symlink"
        symlink_root.mkdir()
        victim = Path(temporary) / "victim"
        victim.write_text("safe", encoding="utf-8")
        (symlink_root / runtime.CONTRACT_FILENAME).symlink_to(victim)
        try:
            runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005_v1(symlink_root)
        except ValueError:
            pass
        else:
            raise AssertionError("symlink output accepted")
        assert victim.read_text(encoding="utf-8") == "safe"


def main() -> None:
    assert len(runtime.SOURCE_PATHS) == 16
    assert tuple(runtime.SOURCE_SHA256) == runtime.SOURCE_PATHS
    snapshot = runtime.build_frozen_source_snapshot()
    assert runtime.validate_frozen_source_snapshot(snapshot)
    _check_runtime_directly(snapshot)
    state = runtime.build_runtime_state(snapshot)
    assert state["all_checks_passed"] is True
    assert state["validation_failures"] == []
    _check_outputs_and_negative_paths(state)
    # All reported fields have been asserted above.
    print("all_checks_passed=true")
    print("exact16_source_sha=16/16")
    print("phase2_type_identity=true")
    print("registered_rule_count=5")
    print("phase4_handler_identity_reused=4/4")
    print("truth_rows=71")
    print("contract_rows=35")
    print("registry_rows=15")
    print("exact22_distribution=2/6/14")
    print("frozen_output_sha=6/6")
    print("ready_for_bulk_download_now=false")
    print("ready_for_training=false")


if __name__ == "__main__":
    main()
