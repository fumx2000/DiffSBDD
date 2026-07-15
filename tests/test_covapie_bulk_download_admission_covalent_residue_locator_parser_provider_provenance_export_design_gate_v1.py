from __future__ import annotations

import ast
import copy
import csv
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate
    as p2_gate,
    covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate
    as gate,
)


CHECK_PATH = REPO_ROOT / (
    "scripts/check_covapie_bulk_download_admission_covalent_residue_locator_"
    "parser_provider_provenance_export_design_gate_v1.py"
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hashes(root: Path) -> dict[str, str]:
    return {
        name: _hash(root / name)
        for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)
    }


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _load_check_module() -> object:
    spec = importlib.util.spec_from_file_location("step14au_e0_p4_check", CHECK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _materialize(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    root = tmp_path / "outputs"
    manifest = gate.run_covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate_v1(root)
    return root, manifest


def _explicit(value: str = "A") -> gate.InsertionCodeRawTokenResult:
    return gate.classify_insertion_code_raw_token(True, value)


def test_import_has_no_materialization_side_effect(tmp_path: Path) -> None:
    before = set(tmp_path.iterdir())
    subprocess.run(
        [sys.executable, "-c", (
            "from covalent_ext import "
            "covapie_bulk_download_admission_covalent_residue_locator_parser_"
            "provider_provenance_export_design_gate"
        )],
        cwd=tmp_path, env={"PYTHONPATH": str(REPO_ROOT / "src")}, check=True,
    )
    assert set(tmp_path.iterdir()) == before


def test_exact_six_outputs_and_manifest_has_no_self_hash(tmp_path: Path) -> None:
    root, manifest = _materialize(tmp_path)
    assert {path.name for path in root.iterdir()} == {*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME}
    assert manifest["output_files"] == [*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME]
    assert set(manifest["output_sha256"]) == set(gate.CSV_OUTPUTS)


def test_double_materialization_is_byte_identical(tmp_path: Path) -> None:
    root, first = _materialize(tmp_path)
    hashes = _hashes(root)
    second = gate.run_covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate_v1(root)
    assert second == first and _hashes(root) == hashes


def test_outputs_have_no_runtime_or_absolute_path_metadata(tmp_path: Path) -> None:
    root, manifest = _materialize(tmp_path)
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.iterdir())
    assert not any("timestamp" in key.lower() for key in manifest)
    assert re.search(r"20\d\d-\d\d-\d\d[T ]\d\d:\d\d", text) is None
    assert str(REPO_ROOT) not in text
    assert "hostname" not in text.lower() and '"uid"' not in text.lower()


def test_source_boundary_exact_order_and_hashes() -> None:
    rows = gate._source_boundary_rows()
    assert gate._validate_source_boundary_rows(rows)
    assert [row["source_relative_path"] for row in rows] == [path.as_posix() for path in gate.SOURCE_PATHS]
    assert {row["source_relative_path"]: row["sha256_observed"] for row in rows} == gate.SOURCE_SHA256


@pytest.mark.parametrize(
    "mutation",
    ["missing", "extra", "reorder", "expected_hash", "observed_hash", "symlink", "untracked"],
)
def test_source_boundary_mutations_fail_closed(mutation: str) -> None:
    rows = copy.deepcopy(gate._source_boundary_rows())
    if mutation == "missing":
        rows.pop()
    elif mutation == "extra":
        rows.append(copy.deepcopy(rows[-1]))
    elif mutation == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "expected_hash":
        rows[0]["sha256_expected"] = "0" * 64
    elif mutation == "observed_hash":
        rows[0]["sha256_observed"] = "0" * 64
    elif mutation == "symlink":
        rows[0]["symlink"] = "true"
    else:
        rows[0]["tracked_by_git"] = "false"
    assert not gate._validate_source_boundary_rows(rows)


def test_p3_predecessor_exact_truths() -> None:
    source = gate._load_p3_source()
    assert gate._validate_p3_predecessor(source)
    manifest = source["manifest"]
    assert (manifest["integrated_field_count"], manifest["integrated_rule_count"], manifest["integrated_context_count"], manifest["remaining_issue_count"]) == (22, 15, 18, 10)
    assert manifest["insertion_unknown_sample_count"] == 11
    assert manifest["fully_provable_pre_download_sample_count"] == 0


def test_p3_five_fields_and_insertion_value_remains_incomplete() -> None:
    fields = gate._load_p3_source()["fields"]
    assert all(any(row["field_name"] == name for row in fields) for name in gate.PROPOSED_FIELD_NAMES)
    row = next(row for row in fields if row["field_name"] == "covalent_residue_insertion_code")
    assert row["allowed_values_defined"] == "false"
    assert row["exact_validation_defined"] == "false"
    assert row["implementation_semantics_complete"] == "false"


def test_p3_readiness_and_masks_remain_closed() -> None:
    manifest = gate._load_p3_source()["manifest"]
    assert manifest["admit_004_rule_logic_ready"] is False
    assert manifest["ready_for_e1_residue_identity_semantics_design"] is False
    assert manifest["canonical_mask_pairs"] == [list(pair) for pair in gate.CANONICAL_MASK_PAIRS]
    assert ["scaffold_only", "B3"] in manifest["canonical_mask_pairs"]


def test_exact_parser_source_tag_registry_and_current_parsers_lack_tags() -> None:
    assert gate.PARSER_INSERTION_SOURCE_TAGS == (
        "_atom_site.pdbx_PDB_ins_code",
        "_struct_conn.pdbx_ptnr1_PDB_ins_code",
        "_struct_conn.pdbx_ptnr2_PDB_ins_code",
    )
    assert gate._parser_tags_currently_absent()


@pytest.mark.parametrize(
    "tag_present,raw_value,token_class,passed,reason",
    [
        (True, "A", "explicit_token", True, ""),
        (True, "1", "explicit_token", True, ""),
        (True, ".", "dot_not_applicable", True, ""),
        (True, "?", "question_unknown", True, ""),
        (False, "", "tag_missing", True, ""),
        (True, "", "parsed_empty", True, ""),
        (1, "", "invalid_token", False, "INSERTION_TAG_PRESENT_TYPE_INVALID"),
        (True, 1, "invalid_token", False, "INSERTION_RAW_VALUE_TYPE_INVALID"),
        (True, "Å", "invalid_token", False, "INSERTION_RAW_VALUE_NON_ASCII"),
        (True, " A", "invalid_token", False, "INSERTION_RAW_VALUE_WHITESPACE_INVALID"),
        (True, "A ", "invalid_token", False, "INSERTION_RAW_VALUE_WHITESPACE_INVALID"),
        (False, "A", "invalid_token", False, "INSERTION_TAG_MISSING_REQUIRES_EMPTY_RAW"),
    ],
)
def test_raw_token_classifier(
    tag_present: object, raw_value: object, token_class: str, passed: bool, reason: str,
) -> None:
    result = gate.classify_insertion_code_raw_token(tag_present, raw_value)
    assert (result.token_class, result.passed, result.blocking_reason) == (token_class, passed, reason)


def test_classifier_rejects_bool_substitutes_and_string_subclasses() -> None:
    class StringSubclass(str):
        pass
    assert not gate.classify_insertion_code_raw_token(0, "").passed
    assert not gate.classify_insertion_code_raw_token("true", "").passed
    assert not gate.classify_insertion_code_raw_token(True, StringSubclass("A")).passed


@pytest.mark.parametrize("index", range(12))
def test_resolution_matrix_case_is_exact(index: int) -> None:
    rows = gate._resolution_rows()
    assert len(rows) == 12 and gate._validate_resolution_rows(rows)
    assert rows[index]["resolution_case_id"] == f"RESOLVE_{index + 1:03d}"
    assert rows[index]["resolution_case_passed"] == "true"


def test_resolution_semantics_explicit_dot_unknown_conflict() -> None:
    rows = {row["resolution_case_id"]: row for row in gate._resolution_rows()}
    assert (rows["RESOLVE_001"]["observed_resolved_state"], rows["RESOLVE_001"]["observed_resolved_value"]) == ("present", "A")
    assert rows["RESOLVE_006"]["observed_resolved_state"] == "absent"
    assert rows["RESOLVE_007"]["observed_resolved_state"] == "unknown"
    assert rows["RESOLVE_003"]["observed_blocking_reason"] == "COVALENT_RESIDUE_INSERTION_CODE_SOURCE_CONFLICT"


def test_one_sided_evidence_never_promotes() -> None:
    for left, right in ((_explicit(), gate.classify_insertion_code_raw_token(True, "?")), (_explicit(), gate.classify_insertion_code_raw_token(True, "."))):
        result = gate.resolve_insertion_code_evidence(left, right)
        assert not result.passed and result.resolved_state == "unknown" and result.blocks_admit_004


@pytest.mark.parametrize("mutation", ["reorder", "wrong_state", "wrong_blocker", "coordinated_drift"])
def test_resolution_matrix_mutations_fail_closed(mutation: str) -> None:
    rows = copy.deepcopy(gate._resolution_rows())
    if mutation == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "wrong_state":
        rows[0]["observed_resolved_state"] = "unknown"
    elif mutation == "wrong_blocker":
        rows[2]["observed_blocking_reason"] = "wrong"
    else:
        rows[0]["expected_resolved_state"] = rows[0]["observed_resolved_state"] = "absent"
    assert not gate._validate_resolution_rows(rows)


def test_provider_exact_five_field_mapping_and_source_id() -> None:
    result = gate.build_locator_provider_export_fields(
        locator_namespace="auth",
        sample_preparation_input_id="SPREP_000001", pdb_id="6BV6", conn_id="covale1",
        residue_partner_side="ptnr1",
        struct_conn_residue_auth_asym_id="A", struct_conn_residue_auth_seq_id="145",
        struct_conn_residue_label_asym_id="B", struct_conn_residue_label_seq_id="44",
        selected_chain_id="A", selected_residue_index="145",
        matched_atom_site_id="C_a_phe_83_a_0", matched_residue_atom_name="SG",
        struct_conn_insertion_source_tag=gate.PARSER_INSERTION_SOURCE_TAGS[1],
        struct_conn_insertion_raw_value="A",
        atom_site_insertion_source_tag=gate.PARSER_INSERTION_SOURCE_TAGS[0],
        atom_site_insertion_raw_value="A",
    )
    assert tuple(result) == gate.PROPOSED_FIELD_NAMES
    assert result[gate.PROPOSED_FIELD_NAMES[3]] == "covapie:residue-locator:SPREP_000001:covale1:ptnr1"
    assert p2_gate.validate_covalent_residue_locator_provenance_sha256(result[gate.PROPOSED_FIELD_NAMES[4]]).passed


@pytest.mark.parametrize("side", ["", "partner1", "PTNR1", 1])
def test_provider_source_id_rejects_invalid_partner_side(side: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        gate.build_locator_provenance_source_id("SPREP_1", "conn1", side)


def test_canonical_payload_key_set_serialization_and_hash() -> None:
    payload = gate._sample_payload()
    expected = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    assert tuple(payload) == gate.CANONICAL_PAYLOAD_KEYS
    assert payload["schema_version"] == gate.CANONICAL_PAYLOAD_SCHEMA_VERSION
    assert gate.canonical_locator_provenance_payload_bytes(payload) == expected
    assert re.fullmatch(r"[0-9a-f]{64}", gate.sha256_canonical_locator_provenance_payload(payload))


def test_canonical_hash_is_order_independent_but_field_sensitive() -> None:
    payload = gate._sample_payload()
    reordered = dict(reversed(tuple(payload.items())))
    assert gate.canonical_locator_provenance_payload_bytes(reordered) == gate.canonical_locator_provenance_payload_bytes(payload)
    assert gate.sha256_canonical_locator_provenance_payload(reordered) == gate.sha256_canonical_locator_provenance_payload(payload)
    changed = dict(payload)
    changed["conn_id"] = "covale2"
    assert gate.sha256_canonical_locator_provenance_payload(changed) != gate.sha256_canonical_locator_provenance_payload(payload)


def test_payload_builder_accepts_reversed_kwargs_and_returns_canonical_order() -> None:
    payload = gate._sample_payload()
    reversed_inputs = dict(reversed(tuple((key, payload[key]) for key in gate.CANONICAL_PAYLOAD_KEYS[1:])))
    rebuilt = gate.build_canonical_locator_provenance_payload(**reversed_inputs)
    assert tuple(rebuilt) == gate.CANONICAL_PAYLOAD_KEYS
    assert rebuilt == payload


@pytest.mark.parametrize("mutation", ["missing", "extra", "non_string"])
def test_payload_builder_rejects_key_or_value_drift(mutation: str) -> None:
    payload = gate._sample_payload()
    inputs: dict[str, object] = {key: payload[key] for key in gate.CANONICAL_PAYLOAD_KEYS[1:]}
    if mutation == "missing":
        inputs.pop("conn_id")
    elif mutation == "extra":
        inputs["extra"] = "value"
    else:
        inputs["conn_id"] = 1
    with pytest.raises((TypeError, ValueError)):
        gate.build_canonical_locator_provenance_payload(**inputs)


@pytest.mark.parametrize("mutation", ["missing", "extra", "schema", "non_string"])
def test_payload_validation_rejects_contract_drift(mutation: str) -> None:
    payload: dict[str, object] = gate._sample_payload()
    if mutation == "missing":
        payload.pop("conn_id")
    elif mutation == "extra":
        payload["extra"] = "value"
    elif mutation == "schema":
        payload["schema_version"] = "drift"
    else:
        payload["conn_id"] = 1
    with pytest.raises((TypeError, ValueError)):
        gate.canonical_locator_provenance_payload_bytes(payload)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "struct_tag,struct_raw,atom_tag,atom_raw,state,value,accepted",
    [
        (gate.PARSER_INSERTION_SOURCE_TAGS[1], "A", gate.PARSER_INSERTION_SOURCE_TAGS[0], "A", "present", "A", True),
        (gate.PARSER_INSERTION_SOURCE_TAGS[1], "A", gate.PARSER_INSERTION_SOURCE_TAGS[0], "A", "absent", "", False),
        (gate.PARSER_INSERTION_SOURCE_TAGS[1], ".", gate.PARSER_INSERTION_SOURCE_TAGS[0], ".", "absent", "", True),
        (gate.PARSER_INSERTION_SOURCE_TAGS[1], ".", gate.PARSER_INSERTION_SOURCE_TAGS[0], ".", "unknown", "", False),
        ("", "", "", "", "unknown", "", True),
        ("", "", "", "", "absent", "", False),
    ],
)
def test_payload_evidence_self_consistency(
    struct_tag: str, struct_raw: str, atom_tag: str, atom_raw: str,
    state: str, value: str, accepted: bool,
) -> None:
    payload = gate._evidence_payload(
        struct_tag=struct_tag, struct_raw=struct_raw, atom_tag=atom_tag,
        atom_raw=atom_raw, state=state, value=value,
    )
    if accepted:
        assert gate.canonical_locator_provenance_payload_bytes(payload)
    else:
        with pytest.raises(ValueError):
            gate.canonical_locator_provenance_payload_bytes(payload)


@pytest.mark.parametrize(
    "side,struct_tag,struct_raw,atom_tag,atom_raw",
    [
        ("ptnr1", gate.PARSER_INSERTION_SOURCE_TAGS[2], "A", gate.PARSER_INSERTION_SOURCE_TAGS[0], "A"),
        ("ptnr2", gate.PARSER_INSERTION_SOURCE_TAGS[1], "A", gate.PARSER_INSERTION_SOURCE_TAGS[0], "A"),
        ("ptnr1", gate.PARSER_INSERTION_SOURCE_TAGS[1], "A", "_atom_site.wrong", "A"),
        ("ptnr1", "", "A", gate.PARSER_INSERTION_SOURCE_TAGS[0], "A"),
    ],
)
def test_payload_rejects_wrong_tag_side_or_missing_tag_with_raw(
    side: str, struct_tag: str, struct_raw: str, atom_tag: str, atom_raw: str,
) -> None:
    payload = gate._evidence_payload(
        struct_tag=struct_tag, struct_raw=struct_raw, atom_tag=atom_tag,
        atom_raw=atom_raw, state="present", value="A", side=side,
    )
    with pytest.raises(ValueError):
        gate.canonical_locator_provenance_payload_bytes(payload)


def test_missing_and_parsed_empty_payloads_have_distinct_bytes_and_hashes() -> None:
    missing = gate._evidence_payload(
        struct_tag="", struct_raw="", atom_tag="", atom_raw="",
        state="unknown", value="",
    )
    parsed_empty = gate._evidence_payload(
        struct_tag=gate.PARSER_INSERTION_SOURCE_TAGS[1], struct_raw="",
        atom_tag=gate.PARSER_INSERTION_SOURCE_TAGS[0], atom_raw="",
        state="unknown", value="",
    )
    assert gate.canonical_locator_provenance_payload_bytes(missing) != gate.canonical_locator_provenance_payload_bytes(parsed_empty)
    assert gate.sha256_canonical_locator_provenance_payload(missing) != gate.sha256_canonical_locator_provenance_payload(parsed_empty)


def test_provider_recomputes_resolution_and_allows_unknown_metadata() -> None:
    common = dict(
        locator_namespace="auth", sample_preparation_input_id="SPREP_1",
        pdb_id="6BV6", conn_id="conn1", residue_partner_side="ptnr1",
        struct_conn_residue_auth_asym_id="A", struct_conn_residue_auth_seq_id="145",
        struct_conn_residue_label_asym_id="B", struct_conn_residue_label_seq_id="44",
        selected_chain_id="A", selected_residue_index="145",
        matched_atom_site_id="C_a_phe_83_a_0", matched_residue_atom_name="SG",
    )
    present = gate.build_locator_provider_export_fields(
        **common,
        struct_conn_insertion_source_tag=gate.PARSER_INSERTION_SOURCE_TAGS[1],
        struct_conn_insertion_raw_value="A",
        atom_site_insertion_source_tag=gate.PARSER_INSERTION_SOURCE_TAGS[0],
        atom_site_insertion_raw_value="A",
    )
    unknown = gate.build_locator_provider_export_fields(
        **common,
        struct_conn_insertion_source_tag="", struct_conn_insertion_raw_value="",
        atom_site_insertion_source_tag="", atom_site_insertion_raw_value="",
    )
    assert (present[gate.PROPOSED_FIELD_NAMES[1]], present[gate.PROPOSED_FIELD_NAMES[2]]) == ("present", "A")
    assert (unknown[gate.PROPOSED_FIELD_NAMES[1]], unknown[gate.PROPOSED_FIELD_NAMES[2]]) == ("unknown", "")


def test_provider_rejects_invalid_token_and_caller_resolution_injection() -> None:
    inputs = dict(
        locator_namespace="auth", sample_preparation_input_id="SPREP_1",
        pdb_id="6BV6", conn_id="conn1", residue_partner_side="ptnr1",
        struct_conn_residue_auth_asym_id="A", struct_conn_residue_auth_seq_id="145",
        struct_conn_residue_label_asym_id="B", struct_conn_residue_label_seq_id="44",
        selected_chain_id="A", selected_residue_index="145",
        matched_atom_site_id="C_a_phe_83_a_0", matched_residue_atom_name="SG",
        struct_conn_insertion_source_tag=gate.PARSER_INSERTION_SOURCE_TAGS[1],
        struct_conn_insertion_raw_value=" A",
        atom_site_insertion_source_tag=gate.PARSER_INSERTION_SOURCE_TAGS[0],
        atom_site_insertion_raw_value="A",
    )
    with pytest.raises(ValueError):
        gate.build_locator_provider_export_fields(**inputs)
    with pytest.raises(TypeError):
        gate.build_locator_provider_export_fields(**inputs, resolution="forged")


@pytest.mark.parametrize(
    "side,struct_tag,atom_tag",
    [
        ("ptnr1", gate.PARSER_INSERTION_SOURCE_TAGS[2], gate.PARSER_INSERTION_SOURCE_TAGS[0]),
        ("ptnr2", gate.PARSER_INSERTION_SOURCE_TAGS[1], gate.PARSER_INSERTION_SOURCE_TAGS[0]),
        ("ptnr1", gate.PARSER_INSERTION_SOURCE_TAGS[1], "_atom_site.wrong"),
    ],
)
def test_provider_rejects_wrong_source_tag_or_partner_binding(
    side: str, struct_tag: str, atom_tag: str,
) -> None:
    with pytest.raises(ValueError):
        gate.build_locator_provider_export_fields(
            locator_namespace="auth", sample_preparation_input_id="SPREP_1",
            pdb_id="6BV6", conn_id="conn1", residue_partner_side=side,
            struct_conn_residue_auth_asym_id="A", struct_conn_residue_auth_seq_id="145",
            struct_conn_residue_label_asym_id="B", struct_conn_residue_label_seq_id="44",
            selected_chain_id="A", selected_residue_index="145",
            matched_atom_site_id="C_a_phe_83_a_0", matched_residue_atom_name="SG",
            struct_conn_insertion_source_tag=struct_tag,
            struct_conn_insertion_raw_value="A",
            atom_site_insertion_source_tag=atom_tag,
            atom_site_insertion_raw_value="A",
        )


@pytest.mark.parametrize(
    "sample,conn",
    [
        ("", "C"), ("A", ""), (" A", "C"), ("A ", "C"),
        ("Å", "C"), ("A/B", "C"), ("A\\B", "C"),
        ("A:B", "C"), ("A", "B:C"), (".", "C"), ("A", "?"),
    ],
)
def test_source_id_rejects_invalid_components(sample: str, conn: str) -> None:
    with pytest.raises(ValueError):
        gate.build_locator_provenance_source_id(sample, conn, "ptnr1")


def test_source_id_rejects_string_subclass_and_collision_pairs() -> None:
    class StringSubclass(str):
        pass
    with pytest.raises(TypeError):
        gate.build_locator_provenance_source_id(StringSubclass("A"), "C", "ptnr1")
    for sample, conn in (("A:B", "C"), ("A", "B:C")):
        with pytest.raises(ValueError):
            gate.build_locator_provenance_source_id(sample, conn, "ptnr1")


@pytest.mark.parametrize(
    "namespace,chain,index,passed,reason",
    [
        ("auth", "A", "145", True, ""),
        ("label", "B", "44", True, ""),
        ("auth", "A", "44", False, "LOCATOR_NAMESPACE_MIXED_SELECTION_FORBIDDEN"),
        ("label", "B", "145", False, "LOCATOR_NAMESPACE_MIXED_SELECTION_FORBIDDEN"),
        ("auth", "C", "999", False, "LOCATOR_NAMESPACE_SELECTED_VALUES_MISMATCH"),
    ],
)
def test_namespace_evidence_auth_label_mixed_and_mismatch(
    namespace: str, chain: str, index: str, passed: bool, reason: str,
) -> None:
    result = gate.resolve_locator_namespace_evidence(
        locator_namespace=namespace,
        struct_conn_residue_auth_asym_id="A", struct_conn_residue_auth_seq_id="145",
        struct_conn_residue_label_asym_id="B", struct_conn_residue_label_seq_id="44",
        selected_chain_id=chain, selected_residue_index=index,
    )
    assert (result.passed, result.blocking_reason) == (passed, reason)


def test_namespace_evidence_records_auth_label_conflict_without_rejecting_selection() -> None:
    result = gate.resolve_locator_namespace_evidence(
        locator_namespace="auth",
        struct_conn_residue_auth_asym_id="A", struct_conn_residue_auth_seq_id="145",
        struct_conn_residue_label_asym_id="B", struct_conn_residue_label_seq_id="44",
        selected_chain_id="A", selected_residue_index="145",
    )
    assert result.passed and result.auth_label_conflict_observed
    assert (result.expected_selected_chain_id, result.expected_selected_residue_index) == ("A", "145")


def test_namespace_evidence_rejects_missing_and_non_exact_values() -> None:
    missing = gate.resolve_locator_namespace_evidence(
        locator_namespace="auth",
        struct_conn_residue_auth_asym_id="", struct_conn_residue_auth_seq_id="145",
        struct_conn_residue_label_asym_id="B", struct_conn_residue_label_seq_id="44",
        selected_chain_id="", selected_residue_index="145",
    )
    invalid = gate.resolve_locator_namespace_evidence(
        locator_namespace="auth",
        struct_conn_residue_auth_asym_id=1, struct_conn_residue_auth_seq_id="145",
        struct_conn_residue_label_asym_id="B", struct_conn_residue_label_seq_id="44",
        selected_chain_id="A", selected_residue_index="145",
    )
    assert missing.blocking_reason == "LOCATOR_NAMESPACE_SELECTED_SOURCE_VALUE_MISSING"
    assert invalid.blocking_reason == "LOCATOR_NAMESPACE_EVIDENCE_TYPE_INVALID"


@pytest.mark.parametrize(
    "atom_site_id,atom_name,passed",
    [
        ("C_a_phe_83_a_0", "SG", True),
        ("opaque-id", "ca", True),
        ("", "SG", False),
        ("1", "", False),
        (".", "SG", False),
        ("1", "?", False),
        (" 1", "SG", False),
        ("1", "SĞ", False),
    ],
)
def test_matched_atom_site_row_identity_contract(
    atom_site_id: str, atom_name: str, passed: bool,
) -> None:
    assert gate.validate_matched_atom_site_row_identity(atom_site_id, atom_name).passed is passed


def test_matched_atom_site_row_identity_rejects_string_subclasses() -> None:
    class StringSubclass(str):
        pass
    assert not gate.validate_matched_atom_site_row_identity(StringSubclass("1"), "SG").passed
    assert not gate.validate_matched_atom_site_row_identity("1", StringSubclass("SG")).passed


def test_provider_recomputes_namespace_and_rejects_result_injection() -> None:
    inputs = dict(
        locator_namespace="auth", sample_preparation_input_id="SPREP_1", pdb_id="6BV6",
        conn_id="conn1", residue_partner_side="ptnr1",
        struct_conn_residue_auth_asym_id="A", struct_conn_residue_auth_seq_id="145",
        struct_conn_residue_label_asym_id="B", struct_conn_residue_label_seq_id="44",
        selected_chain_id="A", selected_residue_index="145",
        matched_atom_site_id="C_a_phe_83_a_0", matched_residue_atom_name="SG",
        struct_conn_insertion_source_tag=gate.PARSER_INSERTION_SOURCE_TAGS[1],
        struct_conn_insertion_raw_value="A",
        atom_site_insertion_source_tag=gate.PARSER_INSERTION_SOURCE_TAGS[0],
        atom_site_insertion_raw_value="A",
    )
    assert gate.build_locator_provider_export_fields(**inputs)[gate.PROPOSED_FIELD_NAMES[0]] == "auth"
    with pytest.raises(ValueError):
        gate.build_locator_provider_export_fields(**{**inputs, "selected_residue_index": "44"})
    with pytest.raises(TypeError):
        gate.build_locator_provider_export_fields(**inputs, namespace_resolution="forged")


def test_standalone_payload_reapplies_source_id_contract() -> None:
    for key, value in (("sample_preparation_input_id", "A:B"), ("conn_id", "")):
        payload = dict(gate._sample_payload())
        payload[key] = value
        with pytest.raises(ValueError):
            gate.canonical_locator_provenance_payload_bytes(payload)


def test_namespace_and_atom_site_evidence_are_hash_bound() -> None:
    label_base = gate._evidence_payload(
        struct_tag=gate.PARSER_INSERTION_SOURCE_TAGS[1], struct_raw="A",
        atom_tag=gate.PARSER_INSERTION_SOURCE_TAGS[0], atom_raw="A",
        state="present", value="A", namespace="label",
    )
    changed_auth = dict(label_base)
    changed_auth["struct_conn_residue_auth_seq_id"] = "146"
    assert gate.sha256_canonical_locator_provenance_payload(label_base) != gate.sha256_canonical_locator_provenance_payload(changed_auth)

    auth_payload = gate._sample_payload()
    label_payload = gate._evidence_payload(
        struct_tag=gate.PARSER_INSERTION_SOURCE_TAGS[1], struct_raw="A",
        atom_tag=gate.PARSER_INSERTION_SOURCE_TAGS[0], atom_raw="A",
        state="present", value="A", namespace="label",
    )
    assert gate.sha256_canonical_locator_provenance_payload(auth_payload) != gate.sha256_canonical_locator_provenance_payload(label_payload)
    for key, value in (("matched_atom_site_id", "opaque_atom_2"), ("matched_residue_atom_name", "CA")):
        changed = dict(auth_payload)
        changed[key] = value
        assert gate.sha256_canonical_locator_provenance_payload(auth_payload) != gate.sha256_canonical_locator_provenance_payload(changed)


def test_namespace_change_without_selected_value_change_fails() -> None:
    payload = dict(gate._sample_payload())
    payload["locator_namespace"] = "label"
    with pytest.raises(ValueError):
        gate.canonical_locator_provenance_payload_bytes(payload)


def test_contract_exact_48_full_rows() -> None:
    rows = gate._contract_rows()
    assert len(rows) == 48 and gate._validate_contract_rows(rows)
    assert [row["contract_item_id"] for row in rows] == [f"P4C_{i:03d}" for i in range(1, 49)]


@pytest.mark.parametrize("mutation", ["reorder", "wrong_id", "coordinated", "empty"])
def test_contract_mutations_fail_closed(mutation: str) -> None:
    rows = copy.deepcopy(gate._contract_rows())
    if mutation == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "wrong_id":
        rows[0]["contract_item_id"] = "P4C_999"
    elif mutation == "coordinated":
        rows[0]["expected_value"] = rows[0]["observed_value"] = "drift"
    else:
        rows = []
    assert not gate._validate_contract_rows(rows)


def test_contract_helper_failure_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "build_locator_provenance_source_id", lambda *args: (_ for _ in ()).throw(ValueError("failure")))
    rows = gate._contract_rows()
    assert any(row["contract_passed"] == "false" for row in rows)
    assert not gate._validate_contract_rows(rows)


def test_issue_inventory_exact_and_separate_from_domain_blockers() -> None:
    rows = gate._issue_rows()
    assert gate._validate_issue_rows(rows)
    assert tuple(row["issue_id"] for row in rows) == gate.DESIGN_FOLLOWUP_ISSUE_IDS
    assert not set(gate.DESIGN_FOLLOWUP_ISSUE_IDS).intersection(gate.DOMAIN_BLOCKING_REASONS)
    assert all(row["issue_id"] != "NO_ISSUES" for row in rows)


def test_safety_exact_20_all_false() -> None:
    rows = gate._safety_rows()
    assert len(rows) == 20 and gate._validate_safety_rows(rows)
    assert all(row["required_status"] == row["observed_status"] == "false" for row in rows)


def test_safety_overclaim_fails_closed() -> None:
    rows = copy.deepcopy(gate._safety_rows())
    rows[0]["observed_status"] = "true"
    assert not gate._validate_safety_rows(rows)


def test_manifest_exact_readiness_and_issue_separation(tmp_path: Path) -> None:
    _, manifest = _materialize(tmp_path)
    assert manifest["parser_provider_provenance_export_design_frozen"] is True
    assert manifest["parser_provider_provenance_export_implemented"] is False
    assert manifest["canonical_provenance_payload_key_count"] == 20
    assert manifest["namespace_evidence_binding_contract_ready"] is True
    assert manifest["provider_recomputes_namespace_evidence"] is True
    assert manifest["provider_recomputes_insertion_evidence"] is True
    assert manifest["atom_site_row_binding_contract_ready"] is True
    assert manifest["ready_for_parser_provider_provenance_export_smoke_implementation"] is True
    assert manifest["insertion_unknown_sample_count"] == 11
    assert manifest["insertion_absence_proven_sample_count"] == 0
    assert manifest["admit_004_rule_logic_ready"] is False
    assert manifest["ready_for_e1_residue_identity_semantics_design"] is False
    assert manifest["ready_for_real_candidate_evaluation"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["current_domain_blocking_reasons"] == list(gate.DOMAIN_BLOCKING_REASONS)
    assert manifest["design_followup_issue_ids"] == list(gate.DESIGN_FOLLOWUP_ISSUE_IDS)


@pytest.mark.parametrize("section", tuple(gate.SECTION_FAILURE_IDS))
def test_each_section_failure_blocks_without_polluting_issues(section: str) -> None:
    result = gate._build_materialization({section: False})
    manifest = gate._manifest_payload(result, {})
    assert manifest["all_checks_passed"] is False
    assert manifest["parser_provider_provenance_export_design_frozen"] is False
    assert manifest["ready_for_parser_provider_provenance_export_smoke_implementation"] is False
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP
    assert manifest["validation_failures"] == [gate.SECTION_FAILURE_IDS[section]]
    assert manifest["current_domain_blocking_reasons"] == list(gate.DOMAIN_BLOCKING_REASONS)
    assert manifest["design_followup_issue_ids"] == list(gate.DESIGN_FOLLOWUP_ISSUE_IDS)


def test_check_validator_accepts_canonical_outputs(tmp_path: Path) -> None:
    root, manifest = _materialize(tmp_path)
    check = _load_check_module()
    check._validate_manifest(manifest, root)


@pytest.mark.parametrize(
    "filename,column,value",
    [
        (gate.CSV_OUTPUTS[0], "observed_value", "drift"),
        (gate.CSV_OUTPUTS[1], "observed_resolved_state", "drift"),
        (gate.CSV_OUTPUTS[2], "sha256_observed", "0" * 64),
        (gate.CSV_OUTPUTS[3], "observed_status", "true"),
        (gate.CSV_OUTPUTS[4], "issue_id", "drift"),
    ],
)
def test_check_validator_rejects_csv_drift(
    tmp_path: Path, filename: str, column: str, value: str,
) -> None:
    root, manifest = _materialize(tmp_path)
    rows = _csv(root / filename)
    rows[0][column] = value
    _write_csv(root / filename, rows)
    check = _load_check_module()
    with pytest.raises(AssertionError):
        check._validate_manifest(manifest, root)


@pytest.mark.parametrize(
    "key,value",
    [
        ("source_input_count", 9),
        ("raw_token_class_count", 5),
        ("resolution_matrix_case_count", 11),
        ("insertion_unknown_sample_count", 10),
        ("insertion_absence_proven_sample_count", 1),
        ("admit_004_rule_logic_ready", True),
        ("ready_for_e1_residue_identity_semantics_design", True),
        ("parser_provider_provenance_export_implemented", True),
        ("ready_for_real_candidate_evaluation", True),
        ("ready_for_bulk_download_now", True),
        ("ready_for_training", True),
        ("stage", "drift"),
        ("recommended_next_step", "drift"),
        ("current_domain_blocking_reasons", ["drift"]),
        ("design_followup_issue_ids", ["drift"]),
        ("validation_failures", ["forged"]),
        ("parser_insertion_source_tags", ["drift"]),
        ("canonical_provenance_payload_key_count", 19),
        ("namespace_evidence_binding_contract_ready", False),
        ("provider_recomputes_namespace_evidence", False),
        ("provider_recomputes_insertion_evidence", False),
        ("atom_site_row_binding_contract_ready", False),
    ],
)
def test_check_validator_rejects_manifest_overclaim(
    tmp_path: Path, key: str, value: object,
) -> None:
    root, manifest = _materialize(tmp_path)
    drifted = copy.deepcopy(manifest)
    drifted[key] = value
    check = _load_check_module()
    with pytest.raises(AssertionError):
        check._validate_manifest(drifted, root)


def test_check_rejects_source_hash_constant_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, manifest = _materialize(tmp_path)
    drifted = dict(gate.SOURCE_SHA256)
    drifted[next(iter(drifted))] = "0" * 64
    monkeypatch.setattr(gate, "SOURCE_SHA256", drifted)
    check = _load_check_module()
    with pytest.raises(AssertionError):
        check._validate_manifest_and_outputs(manifest, root, _hashes(root))


def test_check_rejects_real_disk_mutation_after_first_hash(tmp_path: Path) -> None:
    root, manifest = _materialize(tmp_path)
    first_hashes = _hashes(root)
    with (root / gate.CSV_OUTPUTS[0]).open("a", encoding="utf-8") as handle:
        handle.write("post-hash-drift\n")
    check = _load_check_module()
    with pytest.raises(AssertionError):
        check._validate_manifest_and_outputs(manifest, root, first_hashes)


def test_check_rejects_extra_missing_and_symlink_output(tmp_path: Path) -> None:
    root, _ = _materialize(tmp_path)
    check = _load_check_module()
    (root / "extra.csv").write_text("x\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        check._validate_exact_outputs(root)
    (root / "extra.csv").unlink()
    victim = root / gate.CSV_OUTPUTS[0]
    victim.unlink()
    with pytest.raises(AssertionError):
        check._validate_exact_outputs(root)
    victim.symlink_to(REPO_ROOT / gate.SOURCE_PATHS[0])
    with pytest.raises(AssertionError):
        check._validate_exact_outputs(root)


def test_production_static_boundary() -> None:
    source_path = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert not imports.intersection({"requests", "urllib", "aiohttp", "torch", "numpy", "rdkit", "Bio", "gemmi", "pandas", "inspect", "importlib"})
    assert "data/raw/covalent_sources" not in source
    assert "trainer.fit" not in source and "model.forward" not in source
    assert "importlib.reload" not in source and "getsource" not in source
