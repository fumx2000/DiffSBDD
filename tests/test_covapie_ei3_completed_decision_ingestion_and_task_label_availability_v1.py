from __future__ import annotations

import ast
import copy
import csv
import importlib.util
import io
import json
from pathlib import Path
import stat
import subprocess

import pytest

import covalent_ext.covapie_ei3_completed_decision_ingestion_and_task_label_availability_v1 as owner


REPO = Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO / owner.CHECKER_RELATIVE


def _checker():
    spec = importlib.util.spec_from_file_location("ei3_ingestion_checker", CHECKER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _formal() -> dict[str, object]:
    return json.loads((REPO.parent / owner.FORMAL_DECISION_RELATIVE).read_text())


def _graph() -> dict[str, object]:
    return json.loads((REPO.parent / owner.GRAPH_EVIDENCE_RELATIVE).read_text())


def _event_bytes() -> bytes:
    return (REPO.parent / owner.EVENT_EVIDENCE_RELATIVE).read_bytes()


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode() + b"\n"


def _csv_mutation(payload: bytes, mutate) -> bytes:
    reader = csv.DictReader(io.StringIO(payload.decode(), newline=""))
    header = list(reader.fieldnames or ())
    rows = list(reader)
    mutate(header, rows)
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _checker_artifacts(
    checker, artifacts: dict[str, bytes]
) -> dict[Path, bytes]:
    return {
        checker.SNAPSHOT: artifacts[owner.SNAPSHOT],
        checker.MATRIX: artifacts[owner.MATRIX],
        checker.SUMMARY: artifacts[owner.SUMMARY],
        checker.MANIFEST: artifacts[owner.MANIFEST],
    }


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _csv_bytes(header: list[str], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=header, extrasaction="raise", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _replace_payload_and_sync_manifest(
    checker,
    artifacts: dict[Path, bytes],
    relative: Path,
    payload: bytes,
) -> dict[Path, bytes]:
    changed = dict(artifacts)
    changed[relative] = payload
    manifest = json.loads(changed[checker.MANIFEST])
    matches = [
        row
        for row in manifest["output_artifact_bindings_excluding_manifest_self"]
        if row["path"] == relative.as_posix()
    ]
    assert len(matches) == 1
    import hashlib

    matches[0]["byte_count"] = len(payload)
    matches[0]["SHA256"] = hashlib.sha256(payload).hexdigest()
    changed[checker.MANIFEST] = _canonical_json_bytes(manifest)
    return changed


def _mutated_matrix_artifacts(
    checker,
    artifacts: dict[Path, bytes],
    field: str,
    value: str,
) -> dict[Path, bytes]:
    header, rows = checker.parse_csv(artifacts[checker.MATRIX], "TEST_MATRIX_MUTATION")
    rows[0][field] = value
    return _replace_payload_and_sync_manifest(
        checker,
        artifacts,
        checker.MATRIX,
        _csv_bytes(list(header), rows),
    )


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return owner.build_artifacts_v1(REPO)


@pytest.fixture(scope="module")
def snapshot(artifacts: dict[str, bytes]) -> dict[str, object]:
    return json.loads(artifacts[owner.SNAPSHOT])


def test_public_api_and_exact7_inventory() -> None:
    assert owner.__all__ == (
        "EI3IngestionSafetyError",
        "load_frozen_formal_decision_v1",
        "validate_completed_decision_projection_v1",
        "build_artifacts_v1",
        "materialize_artifacts_v1",
        "check_materialized_v1",
    )
    assert len(owner.CANDIDATE_PUBLICATION_PATHS) == 7
    assert set(owner.OUTPUT_FILENAMES) == {
        owner.SNAPSHOT, owner.MATRIX, owner.SUMMARY, owner.MANIFEST
    }
    assert len(owner.MATRIX_HEADER) != 79
    assert "target_pair_is_only_attachment" not in owner.MATRIX_HEADER
    assert {
        "target_covalent_connection_count", "metal_context_connection_count"
    }.issubset(owner.MATRIX_HEADER)


def test_frozen_sources_exact9_and_formal_internal_exact10() -> None:
    assert len(owner.ACTIVE_BINDINGS) == 9
    assert len(owner.FORMAL_INTERNAL_BINDINGS) == 10
    assert owner.FORMAL_BINDINGS[0][2:] == (
        68366,
        "f0cf2e1703a327d2ace42bb0aba900e1f4a5ef46de96cc2c5f4acf93add2f5f7",
        False,
        "EI3_FROZEN_FORMAL_HUMAN_DECISION",
        "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY",
    )
    assert owner.CENSUS_BINDING[2:4] == (
        559446,
        "9e45211a66a003be7f5f8c8b49b0a7f6f22bce362a06601708affff6a0ce4b4a",
    )


def test_formal_validator_is_identity_only_and_no_upstream_runtime() -> None:
    for relative in (owner.SOURCE_RELATIVE, owner.CHECKER_RELATIVE):
        tree = ast.parse((REPO / relative).read_text())
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        if relative == owner.SOURCE_RELATIVE:
            assert "subprocess" not in imports
            assert "runpy" not in imports
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        assert not any(
            isinstance(call.func, ast.Attribute)
            and call.func.attr in {"exec_module", "run_path"}
            for call in calls
        )
    checker = _checker()
    assert not hasattr(checker, "owner")


def test_schema_preflight_uses_real_ei3_paths() -> None:
    report = owner.schema_preflight_v1(_formal())
    assert report["status"] == "PASS"
    paths = set(report["actual_consumed_paths"])
    assert "$.sample_level_authority.sample_observed_pair_authority" in paths
    assert "$.PRE_boundary.frozen_source_projection.PRE_source_graph_mapping_count_per_event" in paths
    assert report["uses_ME7_sample_pair_authority"] is False
    assert report["uses_ME7_top_level_PRE_source_mapping_count_per_event"] is False


@pytest.mark.parametrize(
    ("mutate", "token"),
    [
        (lambda d: d.__setitem__("schema_version", "wrong"), "FORMAL_SCHEMA_DRIFT"),
        (lambda d: d["sample_identity"]["canonical_target_event_ids"].pop(), "$.sample_identity:canonical_target_event_ids"),
        (lambda d: d["sample_identity"]["canonical_target_event_ids"].append(d["sample_identity"]["canonical_target_event_ids"][0]), "$.sample_identity:canonical_target_event_ids"),
        (lambda d: d["sample_identity"]["canonical_target_event_ids"].append("EXTRA"), "$.sample_identity:canonical_target_event_ids"),
        (lambda d: d["authorization_record"].__setitem__("authorization_bound_candidate_SHA256", "0" * 64), "$.authorization_record:authorization_bound_candidate_SHA256"),
        (lambda d: d["frozen_candidate_binding"].__setitem__("SHA256", "0" * 64), "$.frozen_candidate_binding:SHA256"),
        (lambda d: d["approved_D1_D6"]["D2_task_generation_domain_relevance"].__setitem__("decision", "IN_DOMAIN"), "$.approved_D1_D6:D2_task_generation_domain_relevance"),
        (lambda d: d["approved_D1_D6"]["D6_later_training_use_disposition"].__setitem__("decision", "INCLUDE"), "$.approved_D1_D6:D6_later_training_use_disposition"),
        (lambda d: d["approved_D1_D6"]["D1_observed_covalent_chemistry"].__setitem__("chemistry_positive", False), "$.approved_D1_D6:D1_observed_covalent_chemistry"),
        (lambda d: d["approved_D1_D6"]["D4_role_partition_and_minimal_seed"].__setitem__("human_answered", False), "$.approved_D1_D6:D4_role_partition_and_minimal_seed"),
        (lambda d: d["approved_D1_D6"]["D5_structural_task_applicability"].__setitem__("human_answered", False), "$.approved_D1_D6:D5_structural_task_applicability"),
        (lambda d: d["sample_level_authority"].__setitem__("sample_observed_pair_authority", False), "$.sample_level_authority:sample_observed_pair_authority"),
        (lambda d: d["sample_level_authority"].__setitem__("role_partition_sample_authoritative", True), "$.sample_level_authority:role_partition_sample_authoritative"),
        (lambda d: d["PRE_boundary"]["frozen_source_projection"].__setitem__("PRE_source_graph_count_per_event", [1, 1, 1]), "$.PRE_boundary.frozen_source_projection:PRE_source_graph_count_per_event"),
        (lambda d: d["PRE_boundary"].__setitem__("accurate_PRE_required_before_training_feature_contract", True), "$.PRE_boundary:accurate_PRE_required_before_training_feature_contract"),
    ],
)
def test_formal_semantic_mutations_fail_closed(mutate, token: str) -> None:
    value = _formal()
    mutate(value)
    with pytest.raises(owner.EI3IngestionSafetyError, match=token.replace("$", r"\$")):
        owner._validate_formal(value)


def test_required_real_field_missing_reports_path() -> None:
    value = _formal()
    del value["sample_identity"]["scaleup_ranks"]
    with pytest.raises(
        owner.EI3IngestionSafetyError,
        match=r"REQUIRED_PATH_MISSING:\$\.sample_identity\.scaleup_ranks",
    ):
        owner._validate_formal(value)


@pytest.mark.parametrize(
    "key",
    [
        "role_profile", "role_partitions", "warhead_atom_ids", "linker_atom_ids",
        "scaffold_atom_ids", "minimal_seed", "minimal_seed_atom_ids", "primary_anchor",
        "applicable_task_ids",
    ],
)
def test_role_seed_task_nulls_cannot_be_filled(key: str) -> None:
    value = _formal()
    value["role_and_task_disposition"][key] = []
    with pytest.raises(owner.EI3IngestionSafetyError, match="ROLE_TASK_NULL_DRIFT:" + key):
        owner._validate_formal(value)


def test_historical_machine_snapshot_cannot_override_formal_authority() -> None:
    value = _formal()
    assert value["frozen_candidate_evidence_snapshot"]["source_machine_proposals"]["D3_reactive_atom_pair_confirmation_or_revision"]["human_selected"] is False
    assert value["sample_level_authority"]["sample_observed_pair_authority"] is True
    value["sample_level_authority"]["human_review_completed"] = False
    with pytest.raises(owner.EI3IngestionSafetyError, match="sample_level_authority:human_review_completed"):
        owner._validate_formal(value)


def test_wrong_bound_source_bytes_fail_before_semantic_use(tmp_path: Path) -> None:
    changed = tmp_path / "formal.json"
    changed.write_bytes((REPO.parent / owner.FORMAL_DECISION_RELATIVE).read_bytes() + b" ")
    with pytest.raises(owner.EI3IngestionSafetyError, match="SOURCE_BINDING_FAILED"):
        owner.load_frozen_formal_decision_v1(REPO, formal_decision_path=changed)


@pytest.mark.parametrize(
    ("column", "value", "token"),
    [
        ("canonical_event_id", "EXTRA", "EVENT_EVIDENCE_FIELD_DRIFT"),
        ("review_unit_id", "WRONG", "EVENT_EVIDENCE_FIELD_DRIFT"),
        ("protein_label_seq_id", "217", "EVENT_EVIDENCE_FIELD_DRIFT"),
        ("protein_auth_seq_id", "211", "EVENT_EVIDENCE_FIELD_DRIFT"),
        ("human_selected", "true", "EVENT_EVIDENCE_FIELD_DRIFT"),
        ("pre_source_graph_count", "1", "EVENT_EVIDENCE_FIELD_DRIFT"),
    ],
)
def test_event_evidence_semantic_mutations(column: str, value: str, token: str) -> None:
    payload = _csv_mutation(_event_bytes(), lambda _h, rows: rows[0].__setitem__(column, value))
    with pytest.raises(owner.EI3IngestionSafetyError, match=token):
        owner._validate_event_evidence(payload)


@pytest.mark.parametrize(
    ("mutate", "token"),
    [
        (lambda d: d["target_events"].pop(), "GRAPH_TARGET_EVENTS_NOT_EXACT3"),
        (lambda d: d["additional_instance_connection_context"][0].__setitem__("target_event", True), "GRAPH_METAL_CONTEXT:metalc8"),
        (lambda d: d["target_events"][0]["processing_observation"]["pre"].__setitem__("pre_source_graph_count", 1), "GRAPH_PRE_EVENT"),
        (lambda d: d["pre_post_observation_summary"].__setitem__("POST_to_PRE_copy_performed", True), "GRAPH_PRE_POST_SUMMARY_DRIFT"),
    ],
)
def test_graph_target_metal_and_pre_mutations(mutate, token: str) -> None:
    graph = _graph()
    mutate(graph)
    events = owner._validate_event_evidence(_event_bytes())
    with pytest.raises(owner.EI3IngestionSafetyError, match=token):
        owner._validate_graph_evidence(_json_bytes(graph), events)


def test_completed_projection_exact11_and_rich_evidence(snapshot: dict[str, object]) -> None:
    assert snapshot["normalization"] == {
        "source_D2": "OUT_OF_DOMAIN", "normalized_task_relevance": "NOT_RELEVANT",
        "source_D6": "NOT_APPLICABLE", "normalized_training_disposition": "NOT_APPLICABLE",
        "completed_lane": "COMPLETED_TASK_DOMAIN_NEGATIVE",
        "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
        "chemistry_disposition": "POSITIVE", "negative_chemistry": False,
    }
    facts = snapshot["generic_Exact11_compatibility"]["facts"]
    assert len(facts) == 3
    assert all(set(fact) == set(owner.GENERIC_FACT_FIELDS) for fact in facts)
    assert [row["component_endpoint"]["auth_seq_id"] for row in snapshot["events"]] == [1280, 1277, 1279]
    assert [row["protein_endpoint"]["label_seq_id"] for row in snapshot["events"]] == [211, 211, 211]
    assert [row["protein_endpoint"]["auth_seq_id"] for row in snapshot["events"]] == [217, 217, 217]


def test_matrix_nulls_counts_types_and_summary(artifacts: dict[str, bytes]) -> None:
    header, rows = owner._parse_csv(artifacts[owner.MATRIX], "TEST_MATRIX")
    assert header == owner.MATRIX_HEADER
    assert len(rows) == 3
    assert [row["target_covalent_connection_count"] for row in rows] == ["1", "1", "1"]
    assert [row["metal_context_connection_count"] for row in rows] == ["0", "0", "2"]
    nulls = {
        "selected_role_candidate_json", "role_profile_raw_json", "warhead_atom_ids_json",
        "linker_atom_ids_json", "scaffold_atom_ids_json", "minimal_seed_json",
        "minimal_seed_atom_ids_json", "primary_anchor_json", "structurally_applicable_task_ids_json",
    }
    assert all(row[column] == "null" for row in rows for column in nulls)
    assert all(row["role_profile_derived_state"] == "NOT_ESTABLISHED" for row in rows)
    summary = json.loads(artifacts[owner.SUMMARY])
    assert summary["human_review_completed_count"] == 3
    assert summary["pair_sample_authority_count"] == 3
    assert summary["role_partition_sample_authority_count"] == 0
    assert summary["event_task_label_rows_materialized_count"] == 0
    assert summary["mask_tensor_targets_created_count"] == 0


def test_manifest_bindings_and_determinism(artifacts: dict[str, bytes]) -> None:
    manifest = json.loads(artifacts[owner.MANIFEST])
    assert manifest["active_source_binding_count"] == 9
    assert manifest["formal_internal_source_binding_count"] == 10
    assert "manifest_sha256" not in json.dumps(manifest).lower()
    assert manifest["serialization_contract"]["csv_column_count"] == len(owner.MATRIX_HEADER)
    assert artifacts == owner.build_artifacts_v1(REPO)


@pytest.mark.parametrize(
    ("mutate", "token"),
    [
        (lambda d: d["events"][0].__setitem__("human_review_completed", False), "SNAPSHOT_EVENT_DRIFT"),
        (lambda d: d["events"][0].__setitem__("pair_sample_authority", False), "SNAPSHOT_EVENT_DRIFT"),
        (lambda d: d["events"][0].__setitem__("chemistry_disposition", "NEGATIVE"), "SNAPSHOT_EVENT_DRIFT"),
        (lambda d: d["events"][0].__setitem__("training_materialization_allowed", True), "SNAPSHOT_EVENT_DRIFT"),
        (lambda d: d["generic_Exact11_compatibility"]["facts"][0].__setitem__("coordinates", []), "GENERIC_EXACT11_FIELD_SET_DRIFT"),
    ],
)
def test_nonbyte_snapshot_semantic_negatives(snapshot: dict[str, object], mutate, token: str) -> None:
    value = copy.deepcopy(snapshot)
    mutate(value)
    with pytest.raises(owner.EI3IngestionSafetyError, match=token):
        owner._validate_snapshot_semantics(value)


def test_raw_comparator_and_noop_control(artifacts: dict[str, bytes], monkeypatch) -> None:
    corrupted = dict(artifacts)
    corrupted[owner.SUMMARY] = corrupted[owner.SUMMARY][:-1] + b" \n"
    with pytest.raises(owner.EI3IngestionSafetyError, match="RAW_TEST"):
        owner._compare_artifacts(corrupted, artifacts, "RAW_TEST")
    monkeypatch.setattr(owner, "_compare_artifacts", lambda *_args: None)
    with pytest.raises(owner.EI3IngestionSafetyError, match="RAW_COMPARATOR_CONTROL_DID_NOT_REJECT"):
        owner._raw_comparator_control_probe(REPO)


def test_independent_checker_semantic_and_raw_probes(artifacts: dict[str, bytes]) -> None:
    checker = _checker()
    values = _checker_artifacts(checker, artifacts)
    result = checker.independently_check_artifacts(REPO, values)
    assert result["semantic_check_path_exercised"] is True
    assert result["matrix_dispositions_source_bound"] is True
    assert result["matrix_snapshot_summary_consistent"] is True
    assert result["independent_canonical_byte_identity"] is True
    assert result["normal_checker_byte_path_uses_shared_comparator"] is True
    assert result["raw_byte_comparator_probe"] is True
    assert result["raw_probe_uses_same_comparator"] is True
    assert result["raw_byte_noop_comparator_would_fail_probe"] is True
    with pytest.raises(checker.CheckError, match="RAW_COMPARATOR_NOOP_CONTROL_DID_NOT_FAIL"):
        checker._raw_comparator_probe(values, comparator=lambda *_args: None)


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_value"),
    [
        ("chemistry_disposition", "NEGATIVE", "POSITIVE"),
        ("normalized_task_relevance_disposition", "RELEVANT", "NOT_RELEVANT"),
        ("training_disposition", "INCLUDE", "NOT_APPLICABLE"),
        ("accurate_PRE_required_before_training_feature_contract", "true", "false"),
        ("D4_formally_answered", "false", "true"),
        ("review_unit_id", "WRONG_UNIT", owner.EXPECTED_REVIEW_UNIT_ID),
        ("source_observed_pair", "SG:WRONG", "SG:C1"),
    ],
)
def test_hash_consistent_matrix_semantic_tamper_rejected_by_normal_entrypoint(
    artifacts: dict[str, bytes], field: str, bad_value: str, expected_value: str
) -> None:
    checker = _checker()
    values = _checker_artifacts(checker, artifacts)
    changed = _mutated_matrix_artifacts(checker, values, field, bad_value)
    expected = (
        checker.ERROR_PREFIX
        + ":MATRIX_FIELD_MISMATCH:"
        + owner.EXPECTED_EVENT_IDS[0]
        + ":"
        + field
        + ":actual="
        + json.dumps(bad_value, ensure_ascii=False, separators=(",", ":"))
        + ":expected="
        + json.dumps(expected_value, ensure_ascii=False, separators=(",", ":"))
    )
    with pytest.raises(checker.CheckError) as caught:
        checker.independently_check_artifacts(REPO, changed, run_raw_probe=False)
    assert str(caught.value) == expected
    assert "MANIFEST_OUTPUT_IDENTITY_DRIFT" not in str(caught.value)


@pytest.mark.parametrize(
    ("mutation", "expected_suffix"),
    [
        ("missing", "MATRIX_HEADER_MISSING:chemistry_disposition"),
        ("extra", "MATRIX_HEADER_EXTRA:unexpected_column"),
        ("duplicate", "CSV_HEADER_DUPLICATE_OR_EMPTY:MATRIX"),
        ("reordered", "MATRIX_HEADER_ORDER_DRIFT"),
    ],
)
def test_matrix_header_exact81_fail_closed(
    artifacts: dict[str, bytes], mutation: str, expected_suffix: str
) -> None:
    checker = _checker()
    values = _checker_artifacts(checker, artifacts)
    header, rows = checker.parse_csv(values[checker.MATRIX], "HEADER_MUTATION_BASE")
    changed_header = list(header)
    if mutation == "missing":
        changed_header.remove("chemistry_disposition")
        for row in rows:
            del row["chemistry_disposition"]
    elif mutation == "extra":
        changed_header.append("unexpected_column")
        for row in rows:
            row["unexpected_column"] = "x"
    elif mutation == "duplicate":
        changed_header.insert(24, "chemistry_disposition")
    else:
        changed_header[23], changed_header[24] = changed_header[24], changed_header[23]
    payload = _csv_bytes(changed_header, rows)
    changed = _replace_payload_and_sync_manifest(
        checker, values, checker.MATRIX, payload
    )
    with pytest.raises(checker.CheckError) as caught:
        checker.independently_check_artifacts(REPO, changed, run_raw_probe=False)
    assert str(caught.value) == checker.ERROR_PREFIX + ":" + expected_suffix


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_value"),
    [
        ("source_formal_D5", "UNSET", "NOT_DETERMINABLE"),
        ("role_profile_raw_json", "[]", "null"),
        ("B3_present", "false", "true"),
        ("sixth_task", "true", "false"),
        ("task_label_authority", "true", "false"),
        ("event_task_label_rows_materialized", "true", "false"),
        ("TRAINING_STARTED", "true", "false"),
    ],
)
def test_matrix_null_exact5_and_training_promotions_fail_semantically(
    artifacts: dict[str, bytes], field: str, bad_value: str, expected_value: str
) -> None:
    checker = _checker()
    values = _checker_artifacts(checker, artifacts)
    changed = _mutated_matrix_artifacts(checker, values, field, bad_value)
    with pytest.raises(checker.CheckError) as caught:
        checker.independently_check_artifacts(REPO, changed, run_raw_probe=False)
    expected = (
        checker.ERROR_PREFIX
        + ":MATRIX_FIELD_MISMATCH:"
        + owner.EXPECTED_EVENT_IDS[0]
        + ":"
        + field
        + ":actual="
        + json.dumps(bad_value, separators=(",", ":"))
        + ":expected="
        + json.dumps(expected_value, separators=(",", ":"))
    )
    assert str(caught.value) == expected


def test_matrix_snapshot_endpoint_inconsistency_rejected_before_hash_gate(
    artifacts: dict[str, bytes],
) -> None:
    checker = _checker()
    values = _checker_artifacts(checker, artifacts)
    snapshot = json.loads(values[checker.SNAPSHOT])
    snapshot["events"][0]["protein_endpoint"]["coordinates_lexemes"][0] = "999.000"
    changed = _replace_payload_and_sync_manifest(
        checker,
        values,
        checker.SNAPSHOT,
        _canonical_json_bytes(snapshot),
    )
    with pytest.raises(checker.CheckError) as caught:
        checker.independently_check_artifacts(REPO, changed, run_raw_probe=False)
    assert str(caught.value).startswith(
        checker.ERROR_PREFIX
        + ":MATRIX_SNAPSHOT_ENDPOINT_MISMATCH:"
        + owner.EXPECTED_EVENT_IDS[0]
        + ":protein_coordinates:"
    )


def test_matrix_summary_count_is_rows_derived_and_cross_checked(
    artifacts: dict[str, bytes],
) -> None:
    checker = _checker()
    values = _checker_artifacts(checker, artifacts)
    summary = json.loads(values[checker.SUMMARY])
    summary["chemistry_positive_count"] = 2
    changed = _replace_payload_and_sync_manifest(
        checker, values, checker.SUMMARY, _canonical_json_bytes(summary)
    )
    with pytest.raises(checker.CheckError) as caught:
        checker.independently_check_artifacts(REPO, changed, run_raw_probe=False)
    assert str(caught.value) == (
        checker.ERROR_PREFIX
        + ":MATRIX_SUMMARY_COUNT_MISMATCH:chemistry_positive_count:actual=2:expected=3"
    )


def test_normal_and_raw_paths_use_runtime_shared_comparator(
    artifacts: dict[str, bytes], monkeypatch: pytest.MonkeyPatch
) -> None:
    checker = _checker()
    values = _checker_artifacts(checker, artifacts)
    calls: list[str] = []
    original = checker._compare_bytes

    def spy(actual, expected, token):
        calls.append(token)
        return original(actual, expected, token)

    monkeypatch.setattr(checker, "_compare_bytes", spy)
    result = checker.independently_check_artifacts(REPO, values)
    assert calls == [
        "INDEPENDENT_CANONICAL_BYTE_IDENTITY",
        "RAW_BYTE_NEGATIVE_PROBE",
    ]
    assert result["normal_checker_byte_path_uses_shared_comparator"] is True
    assert result["raw_probe_uses_same_comparator"] is True


def test_noncanonical_json_bytes_rejected_by_normal_byte_path(
    artifacts: dict[str, bytes],
) -> None:
    checker = _checker()
    values = _checker_artifacts(checker, artifacts)
    snapshot = json.loads(values[checker.SNAPSHOT])
    noncanonical = (json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n").encode()
    changed = _replace_payload_and_sync_manifest(
        checker, values, checker.SNAPSHOT, noncanonical
    )
    with pytest.raises(checker.CheckError) as caught:
        checker.independently_check_artifacts(REPO, changed, run_raw_probe=False)
    assert str(caught.value) == (
        checker.ERROR_PREFIX
        + ":INDEPENDENT_CANONICAL_BYTE_IDENTITY:"
        + checker.SNAPSHOT.name
    )


def test_runtime_noop_shared_comparator_causes_full_path_failure(
    artifacts: dict[str, bytes], monkeypatch: pytest.MonkeyPatch
) -> None:
    checker = _checker()
    values = _checker_artifacts(checker, artifacts)
    monkeypatch.setattr(checker, "_compare_bytes", lambda *_args: None)
    with pytest.raises(checker.CheckError) as caught:
        checker.independently_check_artifacts(REPO, values)
    assert str(caught.value) == (
        checker.ERROR_PREFIX + ":RAW_COMPARATOR_NOOP_CONTROL_DID_NOT_FAIL"
    )


@pytest.mark.parametrize("kind", ["wrong_check_error", "value_error"])
def test_raw_probe_rejects_unexpected_error_type_or_token(
    artifacts: dict[str, bytes], kind: str
) -> None:
    checker = _checker()
    values = _checker_artifacts(checker, artifacts)

    def unexpected(*_args):
        if kind == "wrong_check_error":
            raise checker.CheckError(checker.ERROR_PREFIX + ":WRONG_TOKEN")
        raise ValueError("unexpected")

    expected_type = checker.CheckError if kind == "wrong_check_error" else ValueError
    with pytest.raises(expected_type) as caught:
        checker._raw_comparator_probe(values, comparator=unexpected)
    expected_text = (
        checker.ERROR_PREFIX + ":WRONG_TOKEN"
        if kind == "wrong_check_error"
        else "unexpected"
    )
    assert str(caught.value) == expected_text


def test_real_candidate_lifecycle_and_materialized_inventory() -> None:
    checker = _checker()
    result = checker.check_git_lifecycle(REPO)
    assert result["profile"] in {"CANDIDATE_UNTRACKED", "TRACKED_CLEAN"}
    assert result["exact7_count"] == 7
    assert result["staged_modification_count"] == 0
    assert result["tracked_modification_count"] == 0


def test_checker_cli_runs_independently() -> None:
    result = subprocess.run(
        ["python", "-B", str(CHECKER_PATH)], cwd=REPO,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(REPO / "src")},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report, end = json.JSONDecoder().raw_decode(result.stdout.lstrip())
    assert report["status"] == "PASS"
    assert report["git_lifecycle"]["profile"] in {"CANDIDATE_UNTRACKED", "TRACKED_CLEAN"}
    assert "COVAPIE_EI3_COMPLETED_DECISION_INGESTION_V1_CHECK_PASS=true" in result.stdout[end:]


def test_exact7_regular_nonexecuting_and_text_safe() -> None:
    for relative in owner.CANDIDATE_PUBLICATION_PATHS:
        path = REPO / relative
        metadata = path.lstat()
        assert stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
        assert not metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        payload = path.read_bytes()
        assert len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf")
        assert b"\x00" not in payload and b"\r" not in payload
        assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
        assert all(not line.endswith((b" ", b"\t")) for line in payload.splitlines())
