"""Tests for the additive Step14AU-E0-P5-B synthetic smoke."""

from __future__ import annotations

import ast
import copy
import csv
import hashlib
import importlib
import importlib.util
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (
    covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke
    as gate,
)


MODULE_PATH = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke.py"
CHECK_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke_v1.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("p5b_checker", CHECK_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _hashes(root: Path) -> dict[str, str]:
    return {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in gate.OUTPUT_FILES
    }


def _materialize(tmp_path: Path) -> Path:
    root = tmp_path / "outputs"
    result = gate.run_covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke_v1(root)
    assert result["all_checks_passed"] is True
    return root


def _case_rows() -> list[dict[str, object]]:
    return gate.materialize_synthetic_cases()


def test_import_has_no_materialization_side_effect(tmp_path: Path) -> None:
    code = (
        "import pathlib; "
        "import covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke; "
        "print(sorted(p.name for p in pathlib.Path('.').iterdir()))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env={"PYTHONPATH": str(REPO_ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    assert result.stdout.strip() == "[]"


def test_exact_output_set_and_double_materialization(tmp_path: Path) -> None:
    root = _materialize(tmp_path)
    first = _hashes(root)
    first_manifest = (root / gate.MANIFEST_FILENAME).read_bytes()
    gate.run_covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke_v1(root)
    assert _hashes(root) == first
    assert (root / gate.MANIFEST_FILENAME).read_bytes() == first_manifest
    assert {path.name for path in root.iterdir()} == set(gate.OUTPUT_FILES)


def test_outputs_have_no_nondeterministic_or_absolute_content(tmp_path: Path) -> None:
    root = _materialize(tmp_path)
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.iterdir())
    assert "timestamp" not in text.lower()
    assert str(REPO_ROOT) not in text
    assert "manifest_sha256" not in text


def test_source_boundary_is_exact_and_valid() -> None:
    rows = gate._source_boundary_rows()
    assert len(rows) == 9
    assert tuple(row["source_relative_path"] for row in rows) == tuple(
        path.as_posix() for path in gate.SOURCE_PATHS
    )
    assert gate.validate_source_boundary_rows(rows)


@pytest.mark.parametrize(
    ("mutation"),
    ["missing", "extra", "reorder", "hash", "untracked", "nonregular", "symlink"],
)
def test_source_boundary_rejects_drift(mutation: str) -> None:
    rows = copy.deepcopy(gate._source_boundary_rows())
    if mutation == "missing":
        rows.pop()
    elif mutation == "extra":
        rows.append(copy.deepcopy(rows[-1]))
    elif mutation == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "hash":
        rows[0]["sha256_observed"] = "0" * 64
    elif mutation == "untracked":
        rows[0]["tracked"] = False
    elif mutation == "nonregular":
        rows[0]["regular_file"] = False
    else:
        rows[0]["symlink"] = True
    assert not gate.validate_source_boundary_rows(rows)


def test_p4_predecessor_contract_is_frozen() -> None:
    checks = gate._p4_predecessor_checks()
    assert checks and all(checks.values())
    manifest = gate._p4_manifest()
    assert manifest["parser_provider_provenance_export_design_frozen"] is True
    assert manifest["parser_provider_provenance_export_implemented"] is False
    assert manifest["canonical_provenance_payload_key_count"] == 20
    assert len(gate.p4_gate.PARSER_INSERTION_SOURCE_TAGS) == 3
    assert len(gate.p4_gate.RAW_TOKEN_CLASSES) == 6
    assert manifest["predecessor_field_count"] == 22
    assert manifest["existing_sample_count"] == 11
    assert manifest["insertion_unknown_sample_count"] == 11
    assert manifest["insertion_absence_proven_sample_count"] == 0
    assert manifest["recommended_next_step"] == (
        "implement_covapie_covalent_residue_locator_parser_provider_"
        "provenance_export_smoke_v1"
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [("A", "A"), (".", "."), ("?", "?"), ("", "")],
)
def test_raw_parser_preserves_logical_tokens(value: str, expected: str) -> None:
    quoted = "''" if value == "" else value
    result = gate.parse_raw_preserving_mmcif_loop(
        f"data_x\nloop_\n_test.value\n{quoted}\n#\n", "_test."
    )
    assert result.passed and result.status == "parsed_loop"
    assert result.rows[0].as_dict()["_test.value"] == expected
    assert result.rows[0].row_ordinal_1based == 1


@pytest.mark.parametrize(
    ("text", "prefix", "status"),
    [
        (None, "_test.", "invalid_input"),
        ("data_x\n", "_test.", "loop_not_found"),
        ("loop_\n_test.a\n#\n", "_test.", "parsed_empty_loop"),
        ("loop_\n_test.a\n_test.b\nA\n#\n", "_test.", "token_count_not_divisible"),
    ],
)
def test_raw_parser_status_contract(text: object, prefix: str, status: str) -> None:
    result = gate.parse_raw_preserving_mmcif_loop(text, prefix)
    assert result.status == status
    assert result.passed is (status == "parsed_empty_loop")


def test_raw_parser_tag_presence_is_not_defaulted() -> None:
    result = gate.parse_raw_preserving_mmcif_loop(
        "loop_\n_test.a\nA\n#\n", "_test."
    )
    assert result.tags == ("_test.a",)
    assert "_test.missing" not in result.rows[0].as_dict()


def test_compatibility_view_matches_historical_parsers_and_is_nonmutating() -> None:
    text = gate._synthetic_mmcif(gate.CASE_SPECS[3])
    raw_atom = gate.parse_raw_preserving_mmcif_loop(text, "_atom_site.")
    raw_struct = gate.parse_raw_preserving_mmcif_loop(text, "_struct_conn.")
    atom_before = copy.deepcopy(raw_atom)
    struct_before = copy.deepcopy(raw_struct)
    atom = gate.build_historical_compatibility_view(raw_atom, gate.historical.ATOM_SITE_TAGS)
    struct = gate.build_historical_compatibility_view(raw_struct, gate.historical.STRUCT_CONN_TAGS)
    historical_atom = gate.historical.parse_atom_site_loop(text)
    historical_struct = gate.historical.parse_struct_conn_loop(text)
    assert (list(atom.tags), atom.legacy_rows(), atom.status) == historical_atom
    assert (list(struct.tags), struct.legacy_rows(), struct.status) == historical_struct
    assert raw_atom == atom_before and raw_struct == struct_before
    assert raw_atom.rows[0].as_dict()["_atom_site.pdbx_PDB_ins_code"] == "?"
    assert atom.rows[0].as_dict()["_atom_site.pdbx_PDB_ins_code"] == ""


def test_historical_and_expansion_module_hashes_match_frozen_sources() -> None:
    for index in (7, 8):
        path = gate.REPO_ROOT / gate.SOURCE_PATHS[index]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == gate.SOURCE_SHA256[
            gate.SOURCE_PATHS[index].as_posix()
        ]


@pytest.mark.parametrize(("index", "side"), [(0, "ptnr1"), (1, "ptnr2")])
def test_partner_side_is_explicit(index: int, side: str) -> None:
    row = _case_rows()[index]
    assert row["residue_partner_side"] == side
    assert row["struct_conn_insertion_source_tag"] == f"_struct_conn.pdbx_{side}_PDB_ins_code"


def test_partner_side_is_not_inferred_from_loop_order() -> None:
    spec = gate.CASE_SPECS[1]
    raw = gate.parse_raw_preserving_mmcif_loop(gate._synthetic_mmcif(spec), "_struct_conn.")
    event, reason = gate.select_synthetic_struct_conn_event(raw, spec)
    assert reason == "" and event is not None
    assert event.residue_partner_side == "ptnr2"


@pytest.mark.parametrize(
    ("case_index", "atom_id", "reason"),
    [
        (0, "ATOM1", ""),
        (12, "", "MATCHED_ATOM_SITE_ROW_NOT_FOUND"),
        (13, "", "MULTIPLE_MATCHED_ATOM_SITE_ROWS"),
    ],
)
def test_unique_matched_atom_row_contract(case_index: int, atom_id: str, reason: str) -> None:
    row = _case_rows()[case_index]
    assert row["matched_atom_site_id"] == atom_id
    assert row["provider_export_blocking_reason"] == reason
    if atom_id:
        assert row["matched_residue_atom_name"] == "SG"
        assert row["atom_site_insertion_raw_value"] == "A"


def test_all_synthetic_rows_equal_canonical_rows() -> None:
    rows = _case_rows()
    assert gate.validate_synthetic_case_rows(rows)
    assert tuple(row["smoke_case_id"] for row in rows) == gate.CASE_IDS
    assert Counter(row["provider_export_status"] for row in rows) == Counter(
        exported_pass=5, exported_blocking=5, rejected=6
    )


@pytest.mark.parametrize("index", range(3, 8))
def test_cases_four_through_eight_are_exported_blocking(index: int) -> None:
    row = _case_rows()[index]
    assert row["provider_export_status"] == "exported_blocking"
    assert row["resolved_insertion_state"] == "unknown"
    assert row["insertion_blocks_admit_004"] is True
    assert row["provider_export_blocking_reason"] == row["insertion_blocking_reason"]


@pytest.mark.parametrize("mutation", ["reorder", "wrong_id", "coordinated_drift", "empty"])
def test_case_validator_rejects_noncanonical_rows(mutation: str) -> None:
    rows = copy.deepcopy(_case_rows())
    if mutation == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "wrong_id":
        rows[0]["smoke_case_id"] = rows[1]["smoke_case_id"]
    elif mutation == "coordinated_drift":
        rows[0]["matched_atom_site_id"] = "DRIFT"
    else:
        rows.clear()
    assert not gate.validate_synthetic_case_rows(rows)


def test_sidecar_schema_and_provider_field_population() -> None:
    rows = _case_rows()
    assert len(gate.CASE_COLUMNS) == 33 and len(rows) == 16
    for row in rows:
        assert tuple(row) == gate.CASE_COLUMNS
        fields = [row[field] for field in gate.P3_FIELDS]
        if row["provider_export_status"] == "rejected":
            assert fields == ["", "", "", "", ""]
        else:
            assert fields[0] and fields[1] and fields[3]
            assert len(fields[4]) == 64
            int(fields[4], 16)
        assert not any("{" in str(value) or str(REPO_ROOT) in str(value) for value in row.values())


@pytest.mark.parametrize("index", [8, 11, 12, 13, 14])
def test_rejected_pre_resolution_cases_keep_insertion_fields_unavailable(index: int) -> None:
    row = _case_rows()[index]
    assert [
        row["resolved_insertion_state"],
        row["resolved_insertion_value"],
        row["insertion_evidence_agreement"],
        row["insertion_blocks_admit_004"],
        row["insertion_blocking_reason"],
    ] == ["", "", "", "", ""]
    assert row["provider_export_status"] == "rejected"
    assert row["provider_export_blocking_reason"]


def test_source_id_rejection_preserves_completed_insertion_resolution() -> None:
    row = _case_rows()[15]
    assert (
        row["resolved_insertion_state"],
        row["resolved_insertion_value"],
        row["insertion_evidence_agreement"],
        row["insertion_blocks_admit_004"],
        row["insertion_blocking_reason"],
    ) == ("present", "A", True, False, "")
    assert row["provider_export_status"] == "rejected"
    assert row["provider_export_blocking_reason"] == (
        "PROVENANCE_SOURCE_ID_COMPONENT_INVALID"
    )
    assert all(row[field] == "" for field in gate.P3_FIELDS)


def test_empty_case_row_starts_with_unavailable_insertion_evidence() -> None:
    row = gate._empty_case_row(gate.CASE_SPECS[0])
    assert [
        row["struct_conn_token_class"],
        row["atom_site_token_class"],
        row["resolved_insertion_state"],
        row["resolved_insertion_value"],
        row["insertion_evidence_agreement"],
        row["insertion_blocks_admit_004"],
        row["insertion_blocking_reason"],
    ] == ["", "", "", "", "", "", ""]
    assert row["provider_export_status"] == "rejected"
    assert row["provider_export_blocking_reason"] == ""
    assert [row[field] for field in gate.P3_FIELDS] == ["", "", "", "", ""]


@pytest.mark.parametrize(
    "reason", ["STRUCT_CONN_EVENT_NOT_FOUND", "MULTIPLE_STRUCT_CONN_EVENTS"]
)
def test_event_selection_failure_keeps_insertion_evidence_unavailable(
    monkeypatch: pytest.MonkeyPatch, reason: str
) -> None:
    monkeypatch.setattr(
        gate,
        "select_synthetic_struct_conn_event",
        lambda raw_result, spec: (None, reason),
    )
    row = gate.materialize_synthetic_case(gate.CASE_SPECS[0])
    assert row["provider_export_status"] == "rejected"
    assert row["provider_export_blocking_reason"] == reason
    assert [
        row["struct_conn_token_class"],
        row["atom_site_token_class"],
        row["resolved_insertion_state"],
        row["resolved_insertion_value"],
        row["insertion_evidence_agreement"],
        row["insertion_blocks_admit_004"],
        row["insertion_blocking_reason"],
    ] == ["", "", "", "", "", "", ""]
    assert [row[field] for field in gate.P3_FIELDS] == ["", "", "", "", ""]
    assert reason not in {
        str(row["struct_conn_token_class"]),
        str(row["atom_site_token_class"]),
        str(row["resolved_insertion_state"]),
        str(row["resolved_insertion_value"]),
        str(row["insertion_evidence_agreement"]),
        str(row["insertion_blocks_admit_004"]),
        str(row["insertion_blocking_reason"]),
    }


def test_materializer_rejects_symlink_output_root_before_write(tmp_path: Path) -> None:
    real_directory = tmp_path / "real-directory"
    real_directory.mkdir()
    output_link = tmp_path / "output-link"
    output_link.symlink_to(real_directory, target_is_directory=True)
    with pytest.raises(RuntimeError, match="output root must not be a symlink"):
        gate.run_covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke_v1(
            output_link
        )
    assert output_link.is_symlink()
    assert list(real_directory.iterdir()) == []


def test_p4_reload_changes_class_identity_but_not_outputs(tmp_path: Path) -> None:
    root = _materialize(tmp_path)
    before_hashes = _hashes(root)
    before_manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text())
    old_class = gate.p4_gate.InsertionCodeRawTokenResult
    importlib.reload(gate.p4_gate)
    assert gate.p4_gate.InsertionCodeRawTokenResult is not old_class
    result = gate.run_covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke_v1(root)
    assert result["all_checks_passed"] is True
    assert _hashes(root) == before_hashes
    assert json.loads((root / gate.MANIFEST_FILENAME).read_text()) == before_manifest


def test_contract_issue_and_safety_rows_are_exact() -> None:
    state = gate.build_smoke_state()
    assert len(state["contract_rows"]) == 42
    assert len(state["issue_rows"]) == 2
    assert len(state["safety_rows"]) == 20
    assert gate.validate_contract_rows(state["contract_rows"])
    assert gate.validate_issue_rows(state["issue_rows"])
    assert gate.validate_safety_rows(state["safety_rows"])
    assert all(row["contract_passed"] is True for row in state["contract_rows"])
    assert all(row["safety_passed"] is True for row in state["safety_rows"])
    assert "NO_ISSUES" not in {row["issue_id"] for row in state["issue_rows"]}


@pytest.mark.parametrize("kind", ["contract", "issue", "safety"])
def test_audit_validators_reject_drift(kind: str) -> None:
    state = gate.build_smoke_state()
    if kind == "contract":
        rows = copy.deepcopy(state["contract_rows"])
        rows[0]["observed_value"] = "drift"
        assert not gate.validate_contract_rows(rows)
    elif kind == "issue":
        rows = copy.deepcopy(state["issue_rows"])
        rows[0]["issue_id"] = "NO_ISSUES"
        assert not gate.validate_issue_rows(rows)
    else:
        rows = copy.deepcopy(state["safety_rows"])
        rows[0]["observed_status"] = True
        assert not gate.validate_safety_rows(rows)


def test_helper_failure_propagates_to_sections_and_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    original = gate._raw_parser_checks

    def failed_checks() -> dict[str, bool]:
        checks = original()
        checks["dot_preserved"] = False
        return checks

    monkeypatch.setattr(gate, "_raw_parser_checks", failed_checks)
    state = gate.build_smoke_state()
    assert state["sections"]["raw_parser"] is False
    assert state["sections"]["contract"] is False
    assert state["all_checks_passed"] is False


def test_manifest_truthfulness() -> None:
    manifest = gate._manifest_payload(gate.build_smoke_state(), {})
    assert manifest["parser_provider_provenance_export_synthetic_smoke_passed"] is True
    assert manifest["additive_raw_preserving_parser_adapter_implemented"] is True
    assert manifest["real_parser_pipeline_integration_implemented"] is False
    assert manifest["real_provider_pipeline_integration_implemented"] is False
    assert manifest["existing_real_sample_count"] == 11
    assert manifest["real_insertion_unknown_sample_count"] == 11
    assert manifest["real_insertion_absence_proven_sample_count"] == 0
    assert manifest["admit_004_rule_logic_ready"] is False
    assert manifest["ready_for_e1_residue_identity_semantics_design"] is False
    assert manifest["ready_for_real_candidate_evaluation"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert len(manifest["current_domain_blocking_reasons"]) == 10
    assert len(manifest["smoke_followup_issue_ids"]) == 2
    assert manifest["validation_failures"] == []


@pytest.mark.parametrize("section", gate.SECTION_NAMES)
def test_every_section_fails_closed(section: str) -> None:
    state = gate.build_smoke_state([section])
    manifest = gate._manifest_payload(state, {})
    assert manifest["all_checks_passed"] is False
    assert manifest["parser_provider_provenance_export_synthetic_smoke_passed"] is False
    assert manifest["ready_for_real_parser_provider_pipeline_integration_design"] is False
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP
    assert manifest["validation_failures"] == [f"{section.upper()}_VALIDATION_FAILED"]
    assert len(manifest["current_domain_blocking_reasons"]) == 10
    assert len(manifest["smoke_followup_issue_ids"]) == 2


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("synthetic_case_count", 15),
        ("real_parser_pipeline_integration_implemented", True),
        ("real_provider_pipeline_integration_implemented", True),
        ("real_insertion_unknown_sample_count", 10),
        ("real_insertion_absence_proven_sample_count", 1),
        ("admit_004_rule_logic_ready", True),
        ("ready_for_e1_residue_identity_semantics_design", True),
        ("ready_for_real_candidate_evaluation", True),
        ("ready_for_bulk_download_now", True),
        ("ready_for_training", True),
        ("ready_to_train_now", True),
    ],
)
def test_check_validator_rejects_manifest_overclaim(
    tmp_path: Path, key: str, value: object
) -> None:
    root = _materialize(tmp_path)
    path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(path.read_text())
    manifest[key] = value
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(AssertionError):
        _load_checker().validate_materialized_outputs(root)


@pytest.mark.parametrize("kind", ["contract", "case", "case_order", "status", "issue", "safety"])
def test_check_validator_rejects_csv_drift(tmp_path: Path, kind: str) -> None:
    root = _materialize(tmp_path)
    filename = {
        "contract": gate.CONTRACT_FILENAME,
        "case": gate.CASE_FILENAME,
        "case_order": gate.CASE_FILENAME,
        "status": gate.CASE_FILENAME,
        "issue": gate.ISSUE_FILENAME,
        "safety": gate.SAFETY_FILENAME,
    }[kind]
    path = root / filename
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = reader.fieldnames
    assert fields
    if kind == "contract":
        rows[0]["observed_value"] = "drift"
    elif kind == "case":
        rows[0]["matched_atom_site_id"] = "DRIFT"
    elif kind == "case_order":
        rows[0], rows[1] = rows[1], rows[0]
    elif kind == "status":
        rows[3]["provider_export_status"] = "rejected"
    elif kind == "issue":
        rows[0]["issue_id"] = "NO_ISSUES"
    else:
        rows[0]["observed_status"] = "true"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(AssertionError):
        _load_checker().validate_materialized_outputs(root)


@pytest.mark.parametrize("kind", ["missing", "extra", "symlink", "first_hash_changed"])
def test_check_validator_rejects_output_boundary_drift(tmp_path: Path, kind: str) -> None:
    root = _materialize(tmp_path)
    checker = _load_checker()
    hashes = _hashes(root)
    if kind == "missing":
        (root / gate.ISSUE_FILENAME).unlink()
    elif kind == "extra":
        (root / "extra.csv").write_text("x\n")
    elif kind == "symlink":
        target = root / gate.ISSUE_FILENAME
        copy_path = tmp_path / "external-issue.csv"
        shutil.copyfile(target, copy_path)
        target.unlink()
        target.symlink_to(copy_path)
        assert {path.name for path in root.iterdir()} == set(gate.OUTPUT_FILES)
    else:
        (root / gate.ISSUE_FILENAME).write_text("changed\n")
    with pytest.raises(AssertionError):
        checker.validate_materialized_outputs(root, hashes)


def test_check_rejects_source_hash_constant_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _materialize(tmp_path)
    first_hashes = _hashes(root)
    checker = _load_checker()
    drifted = dict(checker.gate.SOURCE_SHA256)
    first_source = next(iter(drifted))
    drifted[first_source] = "0" * 64
    monkeypatch.setattr(checker.gate, "SOURCE_SHA256", drifted)
    with pytest.raises(AssertionError):
        checker.validate_materialized_outputs(root, first_hashes)


def test_production_static_boundary() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert not imported.intersection(
        {"requests", "urllib", "aiohttp", "torch", "numpy", "rdkit", "Bio", "gemmi", "pandas", "importlib", "inspect"}
    )
    forbidden_calls = (
        "model.forward",
        "trainer.fit",
        "importlib.reload",
        "inspect.getsource",
        "data/raw/covalent_sources",
    )
    assert not any(value in source for value in forbidden_calls)


def test_canonical_masks_are_exactly_five_with_b3() -> None:
    assert gate.CANONICAL_MASK_PAIRS == (
        ("warhead_only", "A"),
        ("linker_plus_warhead", "B"),
        ("scaffold_plus_warhead", "B2"),
        ("scaffold_only", "B3"),
        ("scaffold_plus_linker_plus_warhead", "C"),
    )
