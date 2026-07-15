"""Tests for Step14AU-E0-P2 residue-locator schema-extension design gate."""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import importlib
import importlib.util
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate as gate


CHECK_PATH = REPO_ROOT / (
    "scripts/check_covapie_bulk_download_admission_covalent_residue_locator_"
    "minimal_schema_extension_design_gate_v1.py"
)


def _load_check_module():
    spec = importlib.util.spec_from_file_location("step14au_e0_p2_check", CHECK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _hashes(root: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.iterdir())
    }


def _materialize(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    root = tmp_path / "outputs"
    manifest = gate.run_covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate_v1(root)
    return root, manifest


def test_import_has_no_materialization_side_effect(tmp_path: Path) -> None:
    output = tmp_path / "unexpected"
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    code = (
        "import pathlib; "
        "import covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate; "
        f"assert not pathlib.Path({str(output)!r}).exists()"
    )
    subprocess.run([sys.executable, "-c", code], check=True, env=env)


def test_exact_output_set(tmp_path: Path) -> None:
    root, _ = _materialize(tmp_path)
    assert {path.name for path in root.iterdir()} == {
        *gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME,
    }
    assert all(path.is_file() and not path.is_symlink() for path in root.iterdir())


def test_double_materialization_is_byte_identical(tmp_path: Path) -> None:
    root, first = _materialize(tmp_path)
    first_hashes = _hashes(root)
    second = gate.run_covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate_v1(root)
    assert first == second
    assert first_hashes == _hashes(root)


def test_manifest_has_no_nondeterministic_or_absolute_values(tmp_path: Path) -> None:
    _, manifest = _materialize(tmp_path)
    serialized = json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in serialized.lower()
    assert "hostname" not in serialized.lower()
    assert "/home/" not in serialized
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]


def test_source_boundary_exact_and_valid() -> None:
    rows = gate._source_boundary_rows()
    assert gate._validate_source_boundary_rows(rows)
    assert len(rows) == len(gate.SOURCE_PATHS) == 24
    assert [row["source_relative_path"] for row in rows] == [
        path.as_posix() for path in gate.SOURCE_PATHS
    ]
    assert all(row["tracked_by_git"] == "true" for row in rows)
    assert all(row["regular_file"] == "true" for row in rows)
    assert all(row["symlink"] == "false" for row in rows)
    assert all(row["source_boundary_passed"] == "true" for row in rows)


@pytest.mark.parametrize(
    ("mutation", "value"),
    (
        ("tracked_by_git", "false"),
        ("regular_file", "false"),
        ("symlink", "true"),
        ("sha256_expected", "0" * 64),
        ("sha256_observed", "0" * 64),
        ("source_boundary_passed", "false"),
    ),
)
def test_source_boundary_rejects_row_drift(mutation: str, value: str) -> None:
    rows = gate._source_boundary_rows()
    rows[0][mutation] = value
    assert not gate._validate_source_boundary_rows(rows)


@pytest.mark.parametrize("mode", ("missing", "extra", "reorder"))
def test_source_boundary_rejects_shape_or_order_drift(mode: str) -> None:
    rows = gate._source_boundary_rows()
    if mode == "missing":
        rows.pop()
    elif mode == "extra":
        rows.append(deepcopy(rows[-1]))
    else:
        rows[0], rows[1] = rows[1], rows[0]
    assert not gate._validate_source_boundary_rows(rows)


def test_d2_predecessor_truth() -> None:
    source = gate._load_d2_source()
    assert gate._validate_d2_predecessor(source)
    assert len(source["field_rows"]) == 17
    assert len(source["context_rows"]) == 18
    assert len(source["issue_rows"]) == 10
    assert all(
        name not in {row["field_name"] for row in source["field_rows"]}
        for name in gate.PROPOSED_FIELD_NAMES
    )
    assert source["manifest"]["candidate_record_id_semantics_integrated"] is True
    assert source["manifest"]["pdb_identifier_semantics_integrated"] is True
    assert source["manifest"]["ligand_comp_id_semantics_integrated"] is True


@pytest.mark.parametrize(
    ("section", "key", "value"),
    (
        ("manifest", "integrated_field_count", 22),
        ("manifest", "ready_for_bulk_download_now", True),
        ("manifest", "canonical_mask_task_count", 6),
    ),
)
def test_d2_predecessor_rejects_manifest_overclaim(
    section: str, key: str, value: object,
) -> None:
    source = deepcopy(gate._load_d2_source())
    source[section][key] = value
    assert not gate._validate_d2_predecessor(source)


def test_d2_admit_004_is_unchanged_and_blocked() -> None:
    row = next(
        row for row in gate._load_d2_source()["rule_rows"]
        if row["admission_rule_id"] == "ADMIT_004"
    )
    assert row["evaluation_phase"] == "pre_download"
    assert row["semantics_complete"] == "false"
    assert row["deterministic_evaluation_possible_now"] == "false"
    assert row["implementation_disposition"] == "interface_only_pending_semantics"
    assert set(row["blocking_reasons"].split("|")) == {
        gate.RESIDUE_IDENTITY_BLOCKER, gate.ATOM_NAME_BLOCKER,
    }


def test_representation_evidence_is_exactly_five_sources() -> None:
    evidence = gate._load_representation_evidence()
    assert gate._validate_representation_evidence(evidence)
    assert list(evidence) == [path.as_posix() for path in gate.REPRESENTATION_SOURCE_PATHS]


def test_representation_evidence_rejects_drift() -> None:
    evidence = gate._load_representation_evidence()
    evidence[gate.REPRESENTATION_SOURCE_PATHS[0].as_posix()] = "drift"
    assert not gate._validate_representation_evidence(evidence)


def test_backfill_evidence_exact_files_and_all_rows_complete() -> None:
    evidence = gate._load_backfill_evidence()
    assert list(evidence) == [path.as_posix() for path in gate.BACKFILL_SOURCE_PATHS]
    assert len(evidence) == 13
    specs = gate._derive_backfill_specs_from_committed_evidence(evidence)
    assert len(specs) == 11
    assert all(spec["evidence_complete"] is True for spec in specs)


def test_backfill_conflicts_are_computed_from_auth_and_label_values() -> None:
    specs = gate._derive_backfill_specs_from_committed_evidence(
        gate._load_backfill_evidence()
    )
    by_pdb = {str(spec["pdb_id"]): spec for spec in specs}
    assert {
        pdb: (
            spec["auth_asym_id"], spec["auth_seq_id"],
            spec["label_asym_id"], spec["label_seq_id"],
        )
        for pdb, spec in by_pdb.items() if spec["auth_label_conflict_observed"]
    } == {
        "6BV6": ("A", "346", "A", "275"),
        "6BV8": ("A", "353", "A", "282"),
        "6BV5": ("A", "353", "A", "282"),
    }
    assert sum(not bool(spec["auth_label_conflict_observed"]) for spec in specs) == 8
    assert all(
        spec["auth_asym_id"] == spec["label_asym_id"]
        and spec["auth_seq_id"] == spec["label_seq_id"]
        for spec in specs if not spec["auth_label_conflict_observed"]
    )


def test_backfill_selected_values_follow_auth_preference() -> None:
    specs = gate._derive_backfill_specs_from_committed_evidence(
        gate._load_backfill_evidence()
    )
    assert all(spec["inferred_locator_namespace"] == "auth" for spec in specs)
    assert all(spec["selected_chain_id"] == spec["auth_asym_id"] for spec in specs)
    assert all(spec["selected_residue_index"] == spec["auth_seq_id"] for spec in specs)


def test_backfill_evidence_drift_is_not_hidden_by_expected_contract() -> None:
    evidence = deepcopy(gate._load_backfill_evidence())
    event_path = gate.BACKFILL_SOURCE_PATHS[5].as_posix()
    evidence[event_path][0]["residue_auth_seq_id"] = "999"
    rows = gate._backfill_rows(evidence)
    assert rows[3]["audit_passed"] == "false"
    assert not gate._validate_backfill_rows(rows)
    result = gate._build_materialization(backfill_evidence=evidence)
    assert not result["all_backfill_audit_checks_passed"]
    assert not result["all_checks_passed"]
    manifest = gate._manifest_payload(
        result, {name: "x" for name in gate.CSV_OUTPUTS}
    )
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP


@pytest.mark.parametrize("value", ("auth", "label"))
def test_namespace_accepts_exact_canonical_values(value: str) -> None:
    result = gate.normalize_covalent_residue_locator_namespace(value)
    assert result.passed and result.canonical_namespace == value


@pytest.mark.parametrize(
    "value", ("AUTH", "Auth", "LABEL", "Label", "", ".", "?", "mixed", " auth", "auth "),
)
def test_namespace_rejects_invalid_string_values(value: str) -> None:
    result = gate.normalize_covalent_residue_locator_namespace(value)
    assert not result.passed
    assert result.blocking_reason == "COVALENT_RESIDUE_LOCATOR_NAMESPACE_VALUE_INVALID"


@pytest.mark.parametrize("value", (None, 1, True, b"auth", 1.0))
def test_namespace_rejects_non_exact_strings(value: object) -> None:
    result = gate.normalize_covalent_residue_locator_namespace(value)
    assert not result.passed and not result.input_is_exact_str
    assert result.blocking_reason == "COVALENT_RESIDUE_LOCATOR_NAMESPACE_TYPE_INVALID"


def test_namespace_rejects_string_subclass() -> None:
    class StringSubclass(str):
        pass

    assert not gate.normalize_covalent_residue_locator_namespace(
        StringSubclass("auth")
    ).passed


def test_insertion_absent_empty_is_valid() -> None:
    result = gate.validate_covalent_residue_insertion_code("absent", "")
    assert result.passed and result.schema_combination_valid
    assert not result.blocks_admit_004


def test_insertion_present_basic_value_is_valid_but_grammar_not_frozen() -> None:
    result = gate.validate_covalent_residue_insertion_code("present", "A")
    assert result.passed and result.schema_combination_valid
    assert gate._manifest_payload(
        gate._build_materialization(), {name: "x" for name in gate.CSV_OUTPUTS}
    )["insertion_code_present_value_grammar_fully_frozen"] is False


def test_insertion_unknown_empty_is_expressible_but_blocks() -> None:
    result = gate.validate_covalent_residue_insertion_code("unknown", "")
    assert not result.passed and result.schema_combination_valid
    assert result.blocks_admit_004
    assert result.blocking_reason == "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN"


@pytest.mark.parametrize(
    ("state", "value", "reason"),
    (
        ("absent", "A", "COVALENT_RESIDUE_INSERTION_ABSENT_REQUIRES_EMPTY"),
        ("absent", ".", "COVALENT_RESIDUE_INSERTION_ABSENT_REQUIRES_EMPTY"),
        ("absent", "?", "COVALENT_RESIDUE_INSERTION_ABSENT_REQUIRES_EMPTY"),
        ("present", "", "COVALENT_RESIDUE_INSERTION_PRESENT_REQUIRES_NONEMPTY"),
        ("present", " ", "COVALENT_RESIDUE_INSERTION_PRESENT_VALUE_INVALID"),
        ("present", ".", "COVALENT_RESIDUE_INSERTION_PRESENT_VALUE_INVALID"),
        ("present", "?", "COVALENT_RESIDUE_INSERTION_PRESENT_VALUE_INVALID"),
        ("present", " A", "COVALENT_RESIDUE_INSERTION_PRESENT_VALUE_INVALID"),
        ("present", "A ", "COVALENT_RESIDUE_INSERTION_PRESENT_VALUE_INVALID"),
        ("present", "Å", "COVALENT_RESIDUE_INSERTION_PRESENT_VALUE_INVALID"),
        ("unknown", "A", "COVALENT_RESIDUE_INSERTION_UNKNOWN_REQUIRES_EMPTY"),
        ("UNKNOWN", "", "COVALENT_RESIDUE_INSERTION_STATE_VALUE_INVALID"),
        ("invalid", "", "COVALENT_RESIDUE_INSERTION_STATE_VALUE_INVALID"),
    ),
)
def test_insertion_rejects_invalid_combinations(
    state: object, value: object, reason: str,
) -> None:
    result = gate.validate_covalent_residue_insertion_code(state, value)
    assert not result.passed and result.blocks_admit_004
    assert result.blocking_reason == reason


@pytest.mark.parametrize(
    ("state", "value", "reason"),
    (
        (None, "", "COVALENT_RESIDUE_INSERTION_STATE_TYPE_INVALID"),
        (1, "", "COVALENT_RESIDUE_INSERTION_STATE_TYPE_INVALID"),
        ("absent", None, "COVALENT_RESIDUE_INSERTION_VALUE_TYPE_INVALID"),
        ("present", 1, "COVALENT_RESIDUE_INSERTION_VALUE_TYPE_INVALID"),
    ),
)
def test_insertion_rejects_non_exact_types(
    state: object, value: object, reason: str,
) -> None:
    assert gate.validate_covalent_residue_insertion_code(
        state, value
    ).blocking_reason == reason


@pytest.mark.parametrize(
    "value", ("step14au-e0-p1:tracked-evidence", "A", "a/b", "a.b_c-1:2"),
)
def test_provenance_source_id_accepts_valid_tokens(value: str) -> None:
    result = gate.normalize_covalent_residue_locator_provenance_source_id(value)
    assert result.passed and result.canonical_source_id == value


@pytest.mark.parametrize(
    "value", ("", ".", "?", " bad", "bad ", "bad value", "Å", "a" * 257),
)
def test_provenance_source_id_rejects_invalid_tokens(value: str) -> None:
    assert not gate.normalize_covalent_residue_locator_provenance_source_id(value).passed


@pytest.mark.parametrize("value", (None, 1, True, b"source"))
def test_provenance_source_id_rejects_non_strings(value: object) -> None:
    result = gate.normalize_covalent_residue_locator_provenance_source_id(value)
    assert not result.passed and not result.input_is_exact_str


def test_provenance_sha256_accepts_lowercase_64_hex() -> None:
    value = "0123456789abcdef" * 4
    result = gate.validate_covalent_residue_locator_provenance_sha256(value)
    assert result.passed and result.canonical_sha256 == value


@pytest.mark.parametrize(
    "value", ("", ".", "?", "A" * 64, "a" * 63, "a" * 65, "sha256:" + "a" * 64, "g" * 64),
)
def test_provenance_sha256_rejects_invalid_values(value: str) -> None:
    assert not gate.validate_covalent_residue_locator_provenance_sha256(value).passed


def test_contract_is_exact_40_rows() -> None:
    rows = gate._contract_rows()
    assert gate._validate_contract_rows(rows)
    assert len(rows) == 40
    assert [row["contract_item_id"] for row in rows] == [
        f"LOCEXT_{index:03d}" for index in range(1, 41)
    ]
    assert all(row["contract_passed"] == "true" for row in rows)
    assert all(row["blocking_reason"] == "" for row in rows)


@pytest.mark.parametrize("field", tuple(gate.CONTRACT_COLUMNS))
def test_contract_rejects_full_row_drift(field: str) -> None:
    rows = gate._contract_rows()
    rows[0][field] = "drift"
    assert not gate._validate_contract_rows(rows)


def test_contract_rejects_coordinated_expected_observed_drift() -> None:
    rows = gate._contract_rows()
    rows[1]["expected_value"] = "18"
    rows[1]["observed_value"] = "18"
    rows[1]["contract_passed"] = "true"
    assert not gate._validate_contract_rows(rows)


def test_contract_builder_failure_propagates() -> None:
    rows = gate._contract_rows()
    rows[0]["observed_value"] = "drift"
    result = gate._build_materialization(contract_rows=rows)
    assert not result["all_contract_checks_passed"]
    assert not result["all_checks_passed"]
    manifest = gate._manifest_payload(result, {name: "x" for name in gate.CSV_OUTPUTS})
    assert manifest["covalent_residue_locator_schema_extension_frozen"] is False
    assert manifest["ready_for_schema_extension_integration"] is False


def test_namespace_helper_failure_propagates_from_canonical_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = gate.normalize_covalent_residue_locator_namespace

    def broken(value: object):
        result = original(value)
        if value == "auth":
            return dataclasses.replace(
                result,
                passed=False,
                value_valid=False,
                canonical_namespace="",
                blocking_reason="COVALENT_RESIDUE_LOCATOR_NAMESPACE_VALUE_INVALID",
            )
        return result

    monkeypatch.setattr(gate, "normalize_covalent_residue_locator_namespace", broken)
    rows = gate._contract_rows()
    assert any(row["contract_passed"] == "false" for row in rows)
    assert not gate._validate_contract_rows(rows)
    result = gate._build_materialization(contract_rows=rows)
    assert not result["all_contract_checks_passed"]
    assert not result["all_checks_passed"]
    manifest = gate._manifest_payload(
        result, {name: "x" for name in gate.CSV_OUTPUTS}
    )
    assert manifest["covalent_residue_locator_schema_extension_frozen"] is False
    assert manifest["ready_for_schema_extension_integration"] is False
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP


def test_source_id_helper_failure_propagates_from_canonical_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = gate.normalize_covalent_residue_locator_provenance_source_id

    def broken(value: object):
        result = original(value)
        if value == "step14au-e0-p1:tracked-evidence":
            return dataclasses.replace(
                result,
                passed=False,
                syntax_valid=False,
                canonical_source_id="",
                blocking_reason=(
                    "COVALENT_RESIDUE_LOCATOR_PROVENANCE_SOURCE_ID_VALUE_INVALID"
                ),
            )
        return result

    monkeypatch.setattr(
        gate, "normalize_covalent_residue_locator_provenance_source_id", broken
    )
    rows = gate._contract_rows()
    assert any(row["contract_passed"] == "false" for row in rows)
    assert not gate._validate_contract_rows(rows)
    result = gate._build_materialization(contract_rows=rows)
    assert not result["all_checks_passed"]
    manifest = gate._manifest_payload(
        result, {name: "x" for name in gate.CSV_OUTPUTS}
    )
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP


def test_backfill_is_exact_11_rows_and_classification_counts() -> None:
    rows = gate._backfill_rows()
    assert gate._validate_backfill_rows(rows)
    assert len(rows) == 11
    assert sum(row["auth_label_conflict_observed"] == "true" for row in rows) == 3
    assert sum(row["backfill_classification"] == "AUTH_LABEL_CONFLICT" for row in rows) == 3
    assert sum(
        row["backfill_classification"] == "NAMESPACE_PROVABLE_INSERTION_UNKNOWN"
        for row in rows
    ) == 8
    assert not any(
        row["backfill_classification"] == "FULLY_PROVABLE_PRE_DOWNLOAD"
        for row in rows
    )


def test_backfill_keeps_all_insertion_states_unknown_and_none_admissible() -> None:
    rows = gate._backfill_rows()
    assert all(row["insertion_code_state"] == "unknown" for row in rows)
    assert all(row["insertion_code_value"] == "" for row in rows)
    assert all(
        row["admissible_for_e1_after_schema_extension_only"] == "false"
        for row in rows
    )
    assert all(row["audit_passed"] == "true" for row in rows)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("sample_index_row_id", "wrong"),
        ("pdb_id", "XXXX"),
        ("selected_residue_index", "26"),
        ("insertion_code_state", "absent"),
        ("backfill_classification", "FULLY_PROVABLE_PRE_DOWNLOAD"),
        ("admissible_for_e1_after_schema_extension_only", "true"),
    ),
)
def test_backfill_rejects_identity_or_truth_drift(field: str, value: str) -> None:
    rows = gate._backfill_rows()
    rows[3][field] = value
    assert not gate._validate_backfill_rows(rows)


def test_issue_inventory_is_exact_two_rows_without_sentinel() -> None:
    rows = gate._issue_rows()
    assert gate._validate_issue_rows(rows)
    assert [row["issue_id"] for row in rows] == list(gate.P2_ISSUE_IDS)
    assert all(row["issue_id"] != "NO_ISSUES" for row in rows)


def test_issue_inventory_does_not_replace_d2_domain_blockers() -> None:
    d2_ids = [row["issue_id"] for row in gate._load_d2_source()["issue_rows"]]
    assert len(d2_ids) == 10
    assert not set(gate.P2_ISSUE_IDS).intersection(d2_ids)


@pytest.mark.parametrize("mode", ("reorder", "drift", "sentinel"))
def test_issue_inventory_rejects_drift(mode: str) -> None:
    rows = gate._issue_rows()
    if mode == "reorder":
        rows.reverse()
    elif mode == "drift":
        rows[0]["issue_count"] = "10"
    else:
        rows[0]["issue_id"] = "NO_ISSUES"
    assert not gate._validate_issue_rows(rows)


def test_safety_is_exact_20_false_observations() -> None:
    rows = gate._safety_rows()
    assert gate._validate_safety_rows(rows)
    assert len(rows) == 20
    assert [row["safety_item"] for row in rows] == list(gate.SAFETY_ITEMS)
    assert all(row["required_status"] == "false" for row in rows)
    assert all(row["observed_status"] == "false" for row in rows)


@pytest.mark.parametrize("field", ("required_status", "observed_status", "safety_passed"))
def test_safety_rejects_overclaim(field: str) -> None:
    rows = gate._safety_rows()
    rows[0][field] = "true" if field != "safety_passed" else "false"
    assert not gate._validate_safety_rows(rows)


def test_manifest_readiness_and_counts(tmp_path: Path) -> None:
    _, manifest = _materialize(tmp_path)
    assert manifest["covalent_residue_locator_schema_extension_frozen"] is True
    assert manifest["covalent_residue_locator_schema_extension_integrated"] is False
    assert manifest["current_effective_schema_modified_current_step"] is False
    assert manifest["current_effective_field_count"] == 17
    assert manifest["proposed_extension_field_count"] == 5
    assert manifest["proposed_post_extension_field_count"] == 22
    assert manifest["proposed_field_names"] == list(gate.PROPOSED_FIELD_NAMES)
    assert manifest["admit_004_rule_logic_ready"] is False
    assert manifest["ready_for_e1_residue_identity_semantics_design"] is False
    assert manifest["parser_insertion_code_support_required"] is True
    assert manifest["provider_provenance_binding_required"] is True
    assert manifest["ready_for_real_candidate_evaluation"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["blocking_reasons"] == list(gate.P2_ISSUE_IDS)


def test_manifest_records_only_non_manifest_output_hashes(tmp_path: Path) -> None:
    root, manifest = _materialize(tmp_path)
    assert manifest["output_sha256"] == {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in gate.CSV_OUTPUTS
    }


def test_all_builder_failures_propagate() -> None:
    mutations = (
        ("source_rows", gate._source_boundary_rows(), "source_boundary_passed", "false"),
        ("contract_rows", gate._contract_rows(), "observed_value", "drift"),
        ("backfill_rows", gate._backfill_rows(), "insertion_code_state", "absent"),
        ("safety_rows", gate._safety_rows(), "observed_status", "true"),
        ("issue_rows", gate._issue_rows(), "issue_count", "0"),
    )
    for parameter, rows, field, value in mutations:
        rows[0][field] = value
        result = gate._build_materialization(**{parameter: rows})
        assert not result["all_checks_passed"], parameter


def test_success_manifest_recommends_schema_integration() -> None:
    result = gate._build_materialization()
    manifest = gate._manifest_payload(
        result, {name: "x" for name in gate.CSV_OUTPUTS}
    )
    assert result["all_checks_passed"]
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP


@pytest.mark.parametrize(
    "section", ("contract", "backfill", "source", "safety", "issues"),
)
def test_failed_sections_recommend_blocker_resolution(section: str) -> None:
    if section == "contract":
        rows = gate._contract_rows()
        rows[0]["observed_value"] = "drift"
        result = gate._build_materialization(contract_rows=rows)
    elif section == "backfill":
        rows = gate._backfill_rows()
        rows[0]["audit_passed"] = "false"
        result = gate._build_materialization(backfill_rows=rows)
    elif section == "source":
        rows = gate._source_boundary_rows()
        rows[0]["source_boundary_passed"] = "false"
        result = gate._build_materialization(source_rows=rows)
    elif section == "safety":
        rows = gate._safety_rows()
        rows[0]["observed_status"] = "true"
        result = gate._build_materialization(safety_rows=rows)
    else:
        rows = gate._issue_rows()
        rows[0]["issue_count"] = "0"
        result = gate._build_materialization(issue_rows=rows)
    manifest = gate._manifest_payload(
        result, {name: "x" for name in gate.CSV_OUTPUTS}
    )
    assert not result["all_checks_passed"]
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP


def test_canonical_five_masks_include_b3_and_no_sixth() -> None:
    assert gate.CANONICAL_MASK_PAIRS == (
        ("warhead_only", "A"),
        ("linker_plus_warhead", "B"),
        ("scaffold_plus_warhead", "B2"),
        ("scaffold_only", "B3"),
        ("scaffold_plus_linker_plus_warhead", "C"),
    )


def _write_csv_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


@pytest.mark.parametrize(
    ("filename", "field", "value"),
    (
        (gate.CSV_OUTPUTS[0], "observed_value", "drift"),
        (gate.CSV_OUTPUTS[1], "selected_residue_index", "999"),
        (gate.CSV_OUTPUTS[2], "sha256_observed", "0" * 64),
        (gate.CSV_OUTPUTS[3], "observed_status", "true"),
        (gate.CSV_OUTPUTS[4], "issue_count", "0"),
    ),
)
def test_check_rejects_csv_content_drift(
    tmp_path: Path, filename: str, field: str, value: str,
) -> None:
    root, _ = _materialize(tmp_path)
    first_hashes = _hashes(root)
    rows = _csv(root / filename)
    rows[0][field] = value
    _write_csv_rows(root / filename, rows)
    first_hashes[filename] = hashlib.sha256((root / filename).read_bytes()).hexdigest()
    check = _load_check_module()
    with pytest.raises(AssertionError):
        check._validate_disk_outputs(root, first_hashes)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("output_file_count", 7),
        ("current_effective_field_count", 22),
        ("proposed_extension_field_count", 6),
        ("proposed_field_names", [*gate.PROPOSED_FIELD_NAMES, "extra_field"]),
        ("insertion_unknown_sample_count", 10),
        ("fully_provable_pre_download_sample_count", 1),
        ("admit_004_rule_logic_ready", True),
        ("ready_for_e1_residue_identity_semantics_design", True),
        ("ready_for_real_candidate_evaluation", True),
        ("ready_for_bulk_download_now", True),
        ("ready_for_training", True),
        ("insertion_code_present_value_grammar_fully_frozen", True),
    ),
)
def test_check_rejects_manifest_truthfulness_drift(
    tmp_path: Path, field: str, value: object,
) -> None:
    root, manifest = _materialize(tmp_path)
    first_hashes = _hashes(root)
    manifest[field] = value
    manifest_path = root / gate.MANIFEST_FILENAME
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    first_hashes[gate.MANIFEST_FILENAME] = hashlib.sha256(
        manifest_path.read_bytes()
    ).hexdigest()
    check = _load_check_module()
    with pytest.raises(AssertionError):
        check._validate_disk_outputs(root, first_hashes)


def test_check_rejects_source_hash_constant_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _ = _materialize(tmp_path)
    first_hashes = _hashes(root)
    check = _load_check_module()
    hashes = dict(check.gate.SOURCE_SHA256)
    hashes[next(iter(hashes))] = "0" * 64
    monkeypatch.setattr(check.gate, "SOURCE_SHA256", hashes)
    with pytest.raises(AssertionError):
        check._validate_disk_outputs(root, first_hashes)


@pytest.mark.parametrize("mode", ("extra", "missing", "symlink"))
def test_check_rejects_output_set_or_file_type_drift(
    tmp_path: Path, mode: str,
) -> None:
    root, _ = _materialize(tmp_path)
    first_hashes = _hashes(root)
    target = root / gate.CSV_OUTPUTS[0]
    if mode == "extra":
        (root / "extra.csv").write_text("extra\n", encoding="utf-8")
    elif mode == "missing":
        target.unlink()
    else:
        target.unlink()
        target.symlink_to(root / gate.CSV_OUTPUTS[3])
    check = _load_check_module()
    with pytest.raises(AssertionError):
        check._validate_disk_outputs(root, first_hashes)


def test_check_rejects_output_changed_after_first_hash(tmp_path: Path) -> None:
    root, _ = _materialize(tmp_path)
    first_hashes = _hashes(root)
    with (root / gate.CSV_OUTPUTS[0]).open("a", encoding="utf-8") as handle:
        handle.write("post-hash-drift\n")
    check = _load_check_module()
    with pytest.raises(AssertionError):
        check._validate_disk_outputs(root, first_hashes)


def test_production_static_boundary() -> None:
    source = Path(gate.__file__).read_text(encoding="utf-8")
    forbidden_imports = (
        "import requests", "import urllib", "import aiohttp", "import torch",
        "import numpy", "import rdkit", "from Bio", "import gemmi", "import pandas",
        "import sklearn", "import inspect", "import ast", "import importlib",
    )
    assert all(token not in source for token in forbidden_imports)
    assert "model.forward" not in source
    assert "trainer.fit" not in source
    assert "Path(__file__).read_text" not in source
    assert "data/raw/covalent_sources" not in source


def test_module_reload_does_not_modify_materialized_outputs() -> None:
    root = gate.REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    before = _hashes(root)
    importlib.reload(gate)
    assert _hashes(root) == before
