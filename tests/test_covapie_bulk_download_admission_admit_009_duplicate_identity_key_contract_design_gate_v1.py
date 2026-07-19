from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate as gate,
)

CHECKER_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1.py"
SPEC = importlib.util.spec_from_file_location("admit009_duplicate_checker", CHECKER_PATH)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
OUTPUT_ROOT = REPO_ROOT / checker.EXPECTED_OUTPUT_ROOT
KEY = gate.KEY_PREFIX + "1" * 64
LOW = gate.KEY_PREFIX + "0" * 64
HIGH = gate.KEY_PREFIX + "2" * 64
OTHER = gate.KEY_PREFIX + "f" * 64
POLICY = gate.POLICY_CONTRACT_VALUE


class StringSubclass(str):
    pass


class TupleSubclass(tuple):
    pass


def _copy_outputs(tmp_path: Path, name: str = "outputs") -> Path:
    destination = tmp_path / name
    shutil.copytree(OUTPUT_ROOT, destination)
    return destination


def _rewrite_csv(root: Path, name: str, header: tuple[str, ...], mutate) -> None:
    path = root / name
    rows = checker._csv(path, header)
    mutate(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest_path = root / checker.MANIFEST_FILE
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _rewrite_manifest(root: Path, mutate) -> None:
    path = root / checker.MANIFEST_FILE
    value = json.loads(path.read_text(encoding="utf-8"))
    mutate(value)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _assert_rejected(root: Path) -> None:
    with pytest.raises((ValueError, OSError, json.JSONDecodeError)):
        checker._validate_disk(root, enforce_frozen_hashes=False)


def test_success_state_exact_counts_and_readiness() -> None:
    state = gate.build_design_state()
    assert (len(state["contract_rows"]), len(state["context_rows"]), len(state["boundary_rows"])) == (34, 15, 18)
    assert len(state["truth_rows"]) == 32
    assert [row["truth_group"] for row in state["truth_rows"]] == ["scalar"] * 12 + ["policy"] * 4 + ["batch"] * 12 + ["outcome_state"] * 4
    assert all(row["truth_passed"] == "true" for row in state["truth_rows"])
    assert all((row["passed"] == "true") == (row["outcome"] == "passed") for row in state["truth_rows"])
    assert all((row["blocks_candidate"] == "true") == (row["outcome"] != "passed") for row in state["truth_rows"])
    assert all(state["readiness"][key] for key in gate.TRUE_READINESS)
    assert not any(state["readiness"][key] for key in gate.FALSE_READINESS)


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        (None, "DUPLICATE_IDENTITY_KEY_TYPE_INVALID"),
        (7, "DUPLICATE_IDENTITY_KEY_TYPE_INVALID"),
        (StringSubclass(KEY), "DUPLICATE_IDENTITY_KEY_TYPE_INVALID"),
        ("", "DUPLICATE_IDENTITY_KEY_EMPTY"),
        (gate.KEY_PREFIX + "é" * 64, "DUPLICATE_IDENTITY_KEY_NON_ASCII"),
        ("covapie_dup_v2_sha256_" + "1" * 64, "DUPLICATE_IDENTITY_KEY_SYNTAX_INVALID"),
        (gate.KEY_PREFIX + "A" * 64, "DUPLICATE_IDENTITY_KEY_SYNTAX_INVALID"),
        (gate.KEY_PREFIX + "1" * 63, "DUPLICATE_IDENTITY_KEY_SYNTAX_INVALID"),
        (gate.KEY_PREFIX + "1" * 65, "DUPLICATE_IDENTITY_KEY_SYNTAX_INVALID"),
        (gate.KEY_PREFIX + "g" * 64, "DUPLICATE_IDENTITY_KEY_SYNTAX_INVALID"),
        (" " + KEY, "DUPLICATE_IDENTITY_KEY_SYNTAX_INVALID"),
        (KEY + " ", "DUPLICATE_IDENTITY_KEY_SYNTAX_INVALID"),
    ],
)
def test_scalar_rejects_without_trim_casefold_or_coercion(value: object, reason: str) -> None:
    result = gate.classify_admit_009_duplicate_identity_key_design(value, (), POLICY)
    assert result["outcome"] == "invalid" and result["reason"] == reason
    assert result["passed"] is False and result["blocks_candidate"] is True
    assert result["canonical_duplicate_identity_key"] == ""
    assert result["validated_candidate_fields"] == ()
    assert result["policy_classification"] == result["batch_classification"] == "not_evaluated"


@pytest.mark.parametrize(
    ("policy", "reason"),
    [
        (None, "DUPLICATE_IDENTITY_KEY_CONTRACT_TYPE_INVALID"),
        (StringSubclass(POLICY), "DUPLICATE_IDENTITY_KEY_CONTRACT_TYPE_INVALID"),
        ("covapie_duplicate_identity_key_contract_v2", "DUPLICATE_IDENTITY_KEY_CONTRACT_VALUE_INVALID"),
        (" " + POLICY, "DUPLICATE_IDENTITY_KEY_CONTRACT_VALUE_INVALID"),
    ],
)
def test_policy_fail_closed_and_retains_canonical_pair(policy: object, reason: str) -> None:
    result = gate.classify_admit_009_duplicate_identity_key_design(KEY, (), policy)
    assert result["outcome"] == "invalid" and result["reason"] == reason
    assert result["passed"] is False and result["blocks_candidate"] is True
    assert result["canonical_duplicate_identity_key"] == KEY
    assert result["validated_candidate_fields"] == ((gate.CANDIDATE_FIELD, KEY),)
    assert result["batch_classification"] == "not_evaluated"


@pytest.mark.parametrize(
    ("batch", "reason"),
    [
        (None, "BATCH_DUPLICATE_IDENTITY_KEYS_TYPE_INVALID"),
        ([], "BATCH_DUPLICATE_IDENTITY_KEYS_TYPE_INVALID"),
        (TupleSubclass(), "BATCH_DUPLICATE_IDENTITY_KEYS_TYPE_INVALID"),
        ((7,), "BATCH_DUPLICATE_IDENTITY_KEYS_MEMBER_TYPE_INVALID"),
        ((StringSubclass(OTHER),), "BATCH_DUPLICATE_IDENTITY_KEYS_MEMBER_TYPE_INVALID"),
        (("malformed",), "BATCH_DUPLICATE_IDENTITY_KEYS_MEMBER_INVALID"),
        ((HIGH, LOW), "BATCH_DUPLICATE_IDENTITY_KEYS_ORDER_OR_UNIQUENESS_INVALID"),
        ((OTHER, OTHER), "BATCH_DUPLICATE_IDENTITY_KEYS_ORDER_OR_UNIQUENESS_INVALID"),
    ],
)
def test_batch_rejects_without_sort_deduplicate_or_normalize(batch: object, reason: str) -> None:
    result = gate.classify_admit_009_duplicate_identity_key_design(KEY, batch, POLICY)
    assert result["outcome"] == "invalid" and result["reason"] == reason
    assert result["passed"] is False and result["blocks_candidate"] is True
    assert result["canonical_duplicate_identity_key"] == KEY
    assert result["validated_candidate_fields"] == ((gate.CANDIDATE_FIELD, KEY),)


def test_unique_duplicate_membership_and_self_exclusion_contract() -> None:
    unique = gate.classify_admit_009_duplicate_identity_key_design(KEY, (OTHER,), POLICY)
    duplicate = gate.classify_admit_009_duplicate_identity_key_design(KEY, (KEY,), POLICY)
    multiple = gate.classify_admit_009_duplicate_identity_key_design(KEY, (LOW, KEY, HIGH), POLICY)
    assert unique["outcome"] == "passed" and unique["passed"] and not unique["blocks_candidate"] and unique["reason"] == ""
    for result in (duplicate, multiple):
        assert result["outcome"] == "blocked" and not result["passed"] and result["blocks_candidate"]
        assert result["reason"] == "DUPLICATE_IDENTITY_KEY_ALREADY_PRESENT"
        assert result["canonical_duplicate_identity_key"] == KEY
        assert result["validated_candidate_fields"] == ((gate.CANDIDATE_FIELD, KEY),)
    assert "candidate_record_id" not in duplicate["consumed_candidate_fields"]
    assert duplicate["evaluator_io_used"] is False


def test_identity_equivalence_provider_and_collision_boundaries() -> None:
    boundary = {row["boundary_item"]: row for row in gate._boundary_rows()}
    for name in (
        "candidate_record_id", "ligand_graph_group_id", "ligand_scaffold_group_id",
        "leakage_group_id", "final_leakage_group_id", "same_leakage_group",
        "same_scaffold", "same_ligand_graph_group", "different_duplicate_identity_key",
    ):
        assert boundary[name]["is_duplicate_identity_key"] == "false"
        assert boundary[name]["exact_duplicate_claim_allowed"] == "false"
    assert boundary["same_duplicate_identity_key"]["exact_duplicate_claim_allowed"] == "true"
    assert boundary["real_provider_mapping"]["exact_duplicate_claim_allowed"] == "false"
    contract = {row["contract_item"]: row for row in gate._contract_rows()}
    assert contract["composition"]["exact_requirement"] == "atomic opaque producer-owned scalar"
    assert "producer fails closed" in contract["collision_handling"]["exact_requirement"]
    assert "evaluator does not detect" in contract["evaluator_collision_boundary"]["exact_requirement"]


def test_only_duplicate_semantics_issue_transitions() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    before = gate._csv_rows(snapshot, gate.AUDIT_ISSUE_PATH)
    after = gate._issue_rows(snapshot)
    assert len(before) == len(after) == 11
    changes = []
    for old, new in zip(before, after, strict=True):
        if old != new:
            changes.append((old, new))
            assert old["issue_id"] == gate.PRIMARY_BLOCKER
            assert {key for key in old if old[key] != new[key]} == {"status", "integration_transition"}
    assert len(changes) == 1
    coverage = next(row for row in after if row["issue_id"] == gate.COVERAGE_ISSUE)
    assert coverage["status"] == "open"
    assert coverage["affected_rules"] == "ADMIT_009|ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"
    assert coverage["integration_transition"] == "admit_008_implemented_and_removed_from_open_coverage_scope"


@pytest.mark.parametrize(
    ("filename", "header", "row_index", "field", "replacement"),
    [
        (checker.CONTRACT_FILE, checker.CONTRACT_HEADER, 1, "exact_requirement", "isinstance(value, str)"),
        (checker.CONTRACT_FILE, checker.CONTRACT_HEADER, 3, "exact_requirement", "uppercase accepted"),
        (checker.CONTRACT_FILE, checker.CONTRACT_HEADER, 6, "forbidden_behavior", "trim allowed"),
        (checker.CONTRACT_FILE, checker.CONTRACT_HEADER, 7, "exact_requirement", "parse chemical components"),
        (checker.CONTRACT_FILE, checker.CONTRACT_HEADER, 14, "exact_requirement", "evaluator handles collision"),
        (checker.CONTRACT_FILE, checker.CONTRACT_HEADER, 28, "exact_requirement", "invalid; duplicate_identity_unresolved"),
        (checker.CONTEXT_FILE, checker.CONTEXT_HEADER, 4, "exact_contract", "str subclasses allowed"),
        (checker.CONTEXT_FILE, checker.CONTEXT_HEADER, 6, "exact_contract", "list or tuple"),
        (checker.CONTEXT_FILE, checker.CONTEXT_HEADER, 9, "exact_contract", "automatically sorted"),
        (checker.BOUNDARY_FILE, checker.BOUNDARY_HEADER, 0, "is_duplicate_identity_key", "true"),
        (checker.BOUNDARY_FILE, checker.BOUNDARY_HEADER, 5, "is_duplicate_identity_key", "true"),
        (checker.BOUNDARY_FILE, checker.BOUNDARY_HEADER, 9, "exact_duplicate_claim_allowed", "true"),
        (checker.BOUNDARY_FILE, checker.BOUNDARY_HEADER, 14, "exact_statement", "different means chemically distinct"),
        (checker.BOUNDARY_FILE, checker.BOUNDARY_HEADER, 17, "exact_duplicate_claim_allowed", "true"),
        (checker.ISSUE_FILE, checker.ISSUE_HEADER, 0, "status", "changed"),
    ],
)
def test_semantic_tamper_with_refreshed_hash_rejected(
    tmp_path: Path, filename: str, header: tuple[str, ...], row_index: int, field: str, replacement: str,
) -> None:
    root = _copy_outputs(tmp_path)
    _rewrite_csv(root, filename, header, lambda rows: rows[row_index].__setitem__(field, replacement))
    _assert_rejected(root)


def test_duplicate_outcome_and_canonical_state_tamper_rejected(tmp_path: Path) -> None:
    for index, field, value in ((26, "outcome", "invalid"), (26, "reason", "duplicate_identity_unresolved"), (26, "canonical_duplicate_identity_key", ""), (30, "validated_candidate_fields", "[]"), (31, "validated_candidate_fields", "[]")):
        root = _copy_outputs(tmp_path, f"case_{index}_{field}")
        _rewrite_csv(root, checker.TRUTH_FILE, checker.TRUTH_HEADER, lambda rows, i=index, f=field, v=value: rows[i].__setitem__(f, v))
        _assert_rejected(root)
    for row_index, replacement in ((0, "false"), (12, "false"), (16, "false"), (26, "false"), (11, "true")):
        root = _copy_outputs(tmp_path, f"blocks_{row_index}")
        _rewrite_csv(
            root,
            checker.TRUTH_FILE,
            checker.TRUTH_HEADER,
            lambda rows, i=row_index, value=replacement: rows[i].__setitem__("blocks_candidate", value),
        )
        _assert_rejected(root)


def test_manifest_readiness_registration_and_unknown_key_tamper_rejected(tmp_path: Path) -> None:
    mutations = (
        lambda m: m["readiness"].__setitem__("real_provider_duplicate_identity_mapping_validated", True),
        lambda m: m.__setitem__("real_provider_duplicate_identity_key_count", 1),
        lambda m: m.__setitem__("admit_009_standalone_evaluator_implemented", True),
        lambda m: m.__setitem__("admit_009_registered_in_engine", True),
        lambda m: m.__setitem__("admit_009_unified_adapter_contract_frozen", True),
        lambda m: m.__setitem__("unknown_manifest_key", True),
        lambda m: m.__setitem__("validation_failures", ["tampered"]),
    )
    for index, mutation in enumerate(mutations):
        root = _copy_outputs(tmp_path, f"manifest_{index}")
        _rewrite_manifest(root, mutation)
        _assert_rejected(root)


def test_source_boundary_rejects_sha_unsafe_and_structural_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    assert len(gate.SOURCE_PATHS) == 16
    assert gate.SOURCE_PATHS[-1] == gate.UNIFIED_RESULT_CONTRACT_PATH
    assert gate.SOURCE_SHA256[gate.UNIFIED_RESULT_CONTRACT_PATH] == "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa"
    assert not gate._safe_relative_path(Path("../outside"))
    assert not gate._safe_relative_path(Path("data/raw/fixture.cif"))
    assert not gate._safe_relative_path(Path("checkpoints/model.ckpt"))
    original = gate.SOURCE_SHA256[gate.SOURCE_PATHS[0]]
    monkeypatch.setitem(gate.SOURCE_SHA256, gate.SOURCE_PATHS[0], "0" * 64)
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        gate.build_frozen_source_snapshot()
    monkeypatch.setitem(gate.SOURCE_SHA256, gate.SOURCE_PATHS[0], original)
    monkeypatch.setattr(gate, "_structural_source_check", lambda path, root: False)
    with pytest.raises(ValueError, match="structural"):
        gate.build_frozen_source_snapshot()


def test_output_missing_extra_and_symlink_rejected(tmp_path: Path) -> None:
    missing = _copy_outputs(tmp_path, "missing"); (missing / checker.CONTRACT_FILE).unlink(); _assert_rejected(missing)
    extra = _copy_outputs(tmp_path, "extra"); (extra / "extra.csv").write_text("x\n"); _assert_rejected(extra)
    symlink = _copy_outputs(tmp_path, "symlink"); target = symlink / checker.CONTRACT_FILE
    target.unlink(); target.symlink_to(OUTPUT_ROOT / checker.CONTRACT_FILE); _assert_rejected(symlink)


def test_no_formal_evaluator_result_adapter_or_registration_and_exact8_unchanged() -> None:
    assert not hasattr(gate, "evaluate_admit_009")
    assert not hasattr(gate, "Admit009EvaluationResult")
    source = Path(gate.__file__).read_text(encoding="utf-8")
    assert "def evaluate_admit_009" not in source and "class Admit009EvaluationResult" not in source
    exact8 = REPO_ROOT / gate.RUNTIME_SOURCE_PATH
    assert hashlib.sha256(exact8.read_bytes()).hexdigest() == gate.SOURCE_SHA256[gate.RUNTIME_SOURCE_PATH]
    manifest = json.loads((OUTPUT_ROOT / checker.MANIFEST_FILE).read_text(encoding="utf-8"))
    assert manifest["admit_009_registered_in_engine"] is False
    assert manifest["admit_010_standalone_evaluator_implemented"] is False
    assert manifest["evaluate_all_rules_implemented"] is False
    assert manifest["combined_candidate_verdict_implemented"] is False


def test_production_and_checker_imports_are_silent_and_side_effect_free(tmp_path: Path) -> None:
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(SRC_ROOT)!r}); "
        "import covalent_ext.covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate; "
        "import importlib.util; "
        f"s=importlib.util.spec_from_file_location('c', {str(CHECKER_PATH)!r}); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m)"
    )
    result = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, text=True, capture_output=True, check=False)
    assert result.returncode == 0 and result.stdout == result.stderr == ""
    assert sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*")) == before


def test_checker_accepts_frozen_outputs() -> None:
    manifest = checker._validate_disk(OUTPUT_ROOT)
    assert manifest["truth_pass_count"] == 32
    assert manifest["real_provider_duplicate_identity_key_count"] == 0


def test_deterministic_double_materialization(tmp_path: Path) -> None:
    first = tmp_path / "first"; second = tmp_path / "second"
    gate.run_covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1(first)
    gate.run_covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1(second)
    assert {path.name for path in first.iterdir()} == set(checker.EXPECTED_FILES)
    for name in checker.EXPECTED_FILES:
        assert (first / name).read_bytes() == (second / name).read_bytes() == (OUTPUT_ROOT / name).read_bytes()
