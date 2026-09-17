from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


MODULE_ENV = "COVAPIE_FORMAL_ADMISSION_SUCCESSOR_MODULE"
RESULT_ENV = "COVAPIE_FORMAL_ADMISSION_SUCCESSOR_RESULT"


def _load_module():
    candidate = os.environ.get(MODULE_ENV)
    if candidate:
        path = Path(candidate).resolve(strict=True)
        spec = importlib.util.spec_from_file_location(
            "covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1_candidate",
            path,
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(
        "covalent_ext."
        "covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1"
    )


m = _load_module()


def _roots() -> tuple[Path, Path]:
    repository = Path(os.environ["COVAPIE_REPOSITORY_ROOT"]).resolve(strict=True)
    state = Path(os.environ["COVAPIE_STATE_ROOT"]).resolve(strict=True)
    return repository, state


def _rehash_successor(result: dict[str, object]) -> None:
    result["semantic_projection_sha256"] = m._sha256(
        m._canonical_json_bytes(result["semantic_projection"])
    )


@pytest.fixture(scope="session")
def real_bundle():
    repository, state = _roots()
    prepare_calls = 0
    original_prepare = (
        m.evaluation_owner.
        prepare_covapie_poa_4i3u_exact8_nongeometry_admission_evaluator_v1
    )

    def counted_prepare(**kwargs):
        nonlocal prepare_calls
        prepare_calls += 1
        return original_prepare(**kwargs)

    m.evaluation_owner.prepare_covapie_poa_4i3u_exact8_nongeometry_admission_evaluator_v1 = counted_prepare
    try:
        context = m.prepare_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
            repository_root=repository,
            state_root=state,
        )
    finally:
        m.evaluation_owner.prepare_covapie_poa_4i3u_exact8_nongeometry_admission_evaluator_v1 = original_prepare
    assert prepare_calls == 1
    evaluation_before = copy.deepcopy(context.frozen_evaluation_result)
    first = m.build_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
        context=context
    )
    second = m.build_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
        context=context
    )
    assert context.frozen_evaluation_result == evaluation_before
    first_bytes = m.serialize_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
        result=first,
        context=context,
    )
    second_bytes = m.serialize_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
        result=second,
        context=context,
    )
    assert first_bytes == second_bytes
    accounting = context.frozen_evaluation_result["semantic_projection"]["execution_accounting"]
    assert accounting["formal_split_build_public"] == 1
    assert accounting["inactive_adapter_prepare_public"] == 1
    assert accounting["structure_parse_count_reported_by_b1_prepare_and_validator"] == 16
    print(
        "REAL_EXECUTION_COUNTS=published_evaluator_prepare:1,"
        "formal_split_build:1,inactive_prepare:1,structure_parse:16,"
        "successor_result_build:2"
    )
    return SimpleNamespace(
        repository=repository,
        state=state,
        context=context,
        first=first,
        second=second,
        payload=first_bytes,
    )


def _source_variant(real_bundle):
    return copy.deepcopy(real_bundle.context.frozen_evaluation_result)


def test_fixed_source_constants_and_frozen_identities(real_bundle):
    context = real_bundle.context
    assert m.BASELINE_COMMIT == "ca28e3749ae08caf7af9f16273b79e2be46f87b3"
    assert [row.byte_count for row in context.source_bindings] == [52834, 144300]
    assert [row.sha256 for row in context.source_bindings] == [
        "92b9e4ea6839476575446f48fa21edfce47089aef7c0e5e5b4119ce7f360b235",
        "9d599bca7e1e5b63927051af25307c376cd63bba0053991090822562501f4828",
    ]
    assert [row.git_blob_sha1 for row in context.source_bindings] == [
        "209540298d6e00597e79b7068a11c17601c4fa50",
        "fd548d53b24a8071265bf4f25aba598177777d94",
    ]
    assert context.frozen_evaluation_result["semantic_projection_sha256"] == (
        "7fe0fccabf353c81d67e73a83500830e231703597ada3c6293277d8ddda73925"
    )


def test_exact8_canonical5_matrix_and_decisions(real_bundle):
    projection = real_bundle.first["semantic_projection"]
    rows = projection["event_task_admission_records"]
    assert len(rows) == 40
    expected = [
        (event_id, task_name)
        for event_id in m.TARGET_EVENT_IDS_V1
        for _, task_name, _ in m.CANONICAL_TASKS_V1
    ]
    assert [(row["canonical_event_id"], row["canonical_task_name"]) for row in rows] == expected
    assert len(set(expected)) == 40
    assert {row["admission_decision"] for row in rows} == {m.ADMIT_SCOPED}


def test_canonical_tasks_include_b3_and_no_sixth_task(real_bundle):
    tasks = real_bundle.first["semantic_projection"]["canonical_tasks"]
    assert [row["canonical_task_name"] for row in tasks] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert [row["canonical_task_alias"] for row in tasks] == ["A", "B", "B2", "B3", "C"]


def test_per_use_admission_mapping_and_non_c_seed_na(real_bundle):
    rows = real_bundle.first["semantic_projection"]["event_task_admission_records"]
    for row in rows:
        decisions = {item["use_name"]: item for item in row["use_decisions"]}
        for use_name in (
            "base_diffusion_inputs", "covalent_pair_prediction", "pair_contrastive"
        ):
            assert decisions[use_name]["source_eligibility"] == m.SOURCE_ELIGIBLE
            assert decisions[use_name]["admission_use_decision"] == m.USE_GRANTED
        seed = decisions["task_c_seed_condition"]
        if row["canonical_task_name"] == "scaffold_plus_linker_plus_warhead":
            assert seed["source_eligibility"] == m.SOURCE_ELIGIBLE
            assert seed["admission_use_decision"] == m.USE_GRANTED
            assert row["non_applicable_use_names"] == []
        else:
            assert seed["source_eligibility"] == m.SOURCE_NOT_APPLICABLE
            assert seed["admission_use_decision"] == m.USE_NOT_APPLICABLE
            assert row["non_applicable_use_names"] == ["task_c_seed_condition"]


def test_rule_basis_is_row_specific_and_all_passed(real_bundle):
    rows = real_bundle.first["semantic_projection"]["event_task_admission_records"]
    for row in rows:
        assert row["evaluation_record_key"] == {
            "canonical_event_id": row["canonical_event_id"],
            "canonical_task_name": row["canonical_task_name"],
        }
        assert [item["rule_id"] for item in row["source_rule_basis"]] == list(
            m.SOURCE_RULE_IDS_V1
        )
        assert all(item["passed"] is True for item in row["source_rule_basis"])


def test_formal_group_exact8_scope_excludes_other_members(real_bundle):
    population = real_bundle.first["semantic_projection"]["formal_population"]
    assert population["formal_group_id"] == m.FORMAL_GROUP_ID
    assert population["formal_split"] == "train"
    assert population["full_component_event_count"] == 24
    assert population["target_event_ids"] == list(m.TARGET_EVENT_IDS_V1)
    assert all("4I3U" in event_id for event_id in population["target_event_ids"])
    assert all("4I3V" not in event_id and "4I3W" not in event_id and "G3H" not in event_id for event_id in population["target_event_ids"])


def test_prohibited_uses_and_followup_conditions_are_explicit_per_row(real_bundle):
    projection = real_bundle.first["semantic_projection"]
    prohibited = [item["use_name"] for item in projection["use_policy"]["prohibited_use_definitions"]]
    assert prohibited == [name for name, _ in m.PROHIBITED_USE_DEFINITIONS_V1]
    assert "PRE_geometry_training_supervision" in prohibited
    assert "POST_geometry_training_supervision" in prohibited
    assert "model_execution" in prohibited
    assert "parameter_update" in prohibited
    expected_conditions = [item["condition_id"] for item in projection["use_policy"]["subsequent_execution_conditions"]]
    for row in projection["event_task_admission_records"]:
        assert row["prohibited_use_names"] == prohibited
        assert row["subsequent_execution_condition_ids"] == expected_conditions


def test_candidate_effectiveness_and_consumer_are_distinct(real_bundle):
    projection = real_bundle.first["semantic_projection"]
    policy = projection["admission_policy"]
    boundary = projection["permission_boundary"]
    assert policy["candidate_status"] == "PROPOSED_FOR_EXTERNAL_REVIEW_AND_PUBLICATION"
    assert policy["effective_status"] == "NOT_EFFECTIVE_UNTIL_REVIEWED_AND_PUBLISHED"
    assert policy["consumer_status"] == "NO_ACTIVE_TRAINING_CONSUMER_CONNECTED"
    assert boundary["FORMAL_ADMISSION_SUCCESSOR_CANDIDATE_CREATED"] is True
    assert boundary["FORMAL_ADMISSION_EFFECTIVE"] is False
    assert boundary["NEW_HUMAN_DECISION_CREATED"] is False
    assert boundary["ACTIVE_TRAINING_CONSUMER_CONNECTED"] is False
    assert boundary["READY_FOR_TRAINING"] is False


def test_feature_semantics_and_step12d_blockers_are_preserved(real_bundle):
    projection = real_bundle.first["semantic_projection"]
    boundary = projection["permission_boundary"]
    conditions = projection["use_policy"]["subsequent_execution_conditions"]
    text = " ".join(item["statement"] for item in conditions)
    assert boundary["FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER"] is True
    assert boundary["STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK"] is True
    assert "UNKNOWN_ATOM_FEATURE_POLICY" in text
    assert "feature_semantics_known=False" in text
    assert "smoke legality only" in text


def test_base_diffusion_permission_is_narrow_not_global_approval(real_bundle):
    boundary = real_bundle.first["semantic_projection"]["use_policy"][
        "base_diffusion_inputs_boundary"
    ]
    assert "validated base inputs" in boundary
    assert "does not approve every diffusion target" in boundary
    assert "loss" in boundary and "execution" in boundary


def test_result_contains_metadata_not_payload_coordinates_or_tensor_data(real_bundle):
    projection = real_bundle.first["semantic_projection"]
    assert set(projection) == {
        "admission_policy", "source_evaluation_identity", "formal_population",
        "canonical_tasks", "use_policy", "event_task_admission_records",
        "summary", "permission_boundary", "operations_not_executed",
    }
    serialized = real_bundle.payload.decode("utf-8")
    assert '"payloads"' not in serialized
    assert '"coordinates"' not in serialized
    assert '"tensor_data"' not in serialized


def test_source_mapping_rejects_missing_row(real_bundle):
    value = _source_variant(real_bundle)
    value["semantic_projection"]["event_task_records"].pop()
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError, match="EXACT40"):
        m._derive_successor_from_verified_evaluation(value)


def test_source_mapping_rejects_duplicate_row(real_bundle):
    value = _source_variant(real_bundle)
    rows = value["semantic_projection"]["event_task_records"]
    rows[-1] = copy.deepcopy(rows[0])
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError, match="KEY_MATRIX"):
        m._derive_successor_from_verified_evaluation(value)


@pytest.mark.parametrize(
    "foreign_event",
    [
        "COVAPIE_CYS_SG_EVENT_V1:4I3V:A:CYS:291-:SG:I:POA:C2",
        "COVAPIE_CYS_SG_EVENT_V1:4I3W:A:CYS:291-:SG:I:POA:C2",
        "COVAPIE_CYS_SG_EVENT_V1:G3H:A:CYS:291-:SG:I:POA:C2",
    ],
)
def test_source_mapping_rejects_unapproved_same_group_or_heldout_event(real_bundle, foreign_event):
    value = _source_variant(real_bundle)
    value["semantic_projection"]["formal_population"]["target_event_ids"][0] = foreign_event
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError, match="POPULATION_SCOPE"):
        m._derive_successor_from_verified_evaluation(value)


def test_source_mapping_rejects_wrong_or_sixth_task(real_bundle):
    value = _source_variant(real_bundle)
    row = value["semantic_projection"]["event_task_records"][0]
    row["canonical_task_id"] = 5
    row["canonical_task_name"] = "sixth_task"
    row["canonical_task_alias"] = "D"
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError, match="IDENTITY_TYPE"):
        m._derive_successor_from_verified_evaluation(value)


def test_source_mapping_rejects_blocked_candidate(real_bundle):
    value = _source_variant(real_bundle)
    value["semantic_projection"]["event_task_records"][0]["candidate_status"] = m.SOURCE_BLOCKED
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError, match="SOURCE_RECORD_BLOCKED"):
        m._derive_successor_from_verified_evaluation(value)


def test_source_mapping_rejects_any_blocked_rule(real_bundle):
    value = _source_variant(real_bundle)
    value["semantic_projection"]["event_task_records"][0]["rule_results"][7]["passed"] = False
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError, match="SOURCE_RULE_BLOCKED"):
        m._derive_successor_from_verified_evaluation(value)


def test_source_mapping_rejects_any_blocked_required_use(real_bundle):
    value = _source_variant(real_bundle)
    value["semantic_projection"]["event_task_records"][0]["eligibility"]["pair_contrastive"] = m.SOURCE_BLOCKED
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError, match="REQUIRED_USE_NOT_ELIGIBLE"):
        m._derive_successor_from_verified_evaluation(value)


def test_source_mapping_rejects_non_c_seed_forged_true(real_bundle):
    value = _source_variant(real_bundle)
    value["semantic_projection"]["event_task_records"][0]["eligibility"]["task_c_seed_condition"] = m.SOURCE_ELIGIBLE
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError, match="REQUIRED_USE_NOT_ELIGIBLE"):
        m._derive_successor_from_verified_evaluation(value)


def test_source_mapping_rejects_schema_and_strict_types(real_bundle):
    wrong_schema = _source_variant(real_bundle)
    wrong_schema["schema_version"] = "other"
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError, match="FIXED_IDENTITY"):
        m._derive_successor_from_verified_evaluation(wrong_schema)
    wrong_bool = _source_variant(real_bundle)
    wrong_bool["semantic_projection"]["formal_population"]["formal_split_authoritative"] = 1
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError, match="POPULATION_SCOPE"):
        m._derive_successor_from_verified_evaluation(wrong_bool)
    wrong_int = _source_variant(real_bundle)
    wrong_int["semantic_projection"]["event_task_records"][0]["canonical_task_id"] = True
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError, match="IDENTITY_TYPE"):
        m._derive_successor_from_verified_evaluation(wrong_int)


def test_source_sha_drift_rejected_before_published_prepare(real_bundle, monkeypatch):
    original = m._read_regular

    def drifted(path, reason):
        payload = original(path, reason)
        if reason == "FIXED_SOURCE" and path.name.endswith("admission_evaluator_v1.py"):
            return payload + b"\n"
        return payload

    monkeypatch.setattr(m, "_read_regular", drifted)
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError, match="IDENTITY_MISMATCH"):
        m.prepare_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
            repository_root=real_bundle.repository,
            state_root=real_bundle.state,
        )


def test_baseline_gate_accepts_ancestor_without_head_equality(monkeypatch, tmp_path):
    git_calls = []

    def fake_git(repository, *arguments):
        git_calls.append(arguments)
        if arguments[:2] == ("cat-file", "-t"):
            return "commit"
        raise AssertionError(arguments)

    class Completed:
        returncode = 0

    monkeypatch.setattr(m, "_git", fake_git)
    monkeypatch.setattr(m.subprocess, "run", lambda *args, **kwargs: Completed())
    m._validate_baseline_lineage(tmp_path)
    assert git_calls == [("cat-file", "-t", m.BASELINE_COMMIT)]


def test_only_40_pass_admit_strings_cannot_validate(real_bundle):
    fake_projection = {
        "summary": {"event_task_admission_record_count": 40, "status": "PASS"},
        "event_task_admission_records": ["ADMIT"] * 40,
    }
    fake = {
        "schema_version": m.SCHEMA_VERSION,
        "record_role": m.RECORD_ROLE,
        "semantic_projection": fake_projection,
        "semantic_projection_sha256": m._sha256(m._canonical_json_bytes(fake_projection)),
    }
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError, match="REDERIVATION_MISMATCH"):
        m.validate_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
            result=fake,
            context=real_bundle.context,
        )


def test_tamper_and_recomputed_digest_still_rejected(real_bundle):
    tampered = copy.deepcopy(real_bundle.first)
    tampered["semantic_projection"]["event_task_admission_records"][0]["admission_decision"] = "ADMIT_ALL"
    _rehash_successor(tampered)
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError, match="REDERIVATION_MISMATCH"):
        m.validate_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
            result=tampered,
            context=real_bundle.context,
        )


def test_successor_strict_bool_and_int_tamper_rejected(real_bundle):
    wrong_bool = copy.deepcopy(real_bundle.first)
    wrong_bool["semantic_projection"]["permission_boundary"]["FORMAL_ADMISSION_EFFECTIVE"] = 0
    _rehash_successor(wrong_bool)
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError):
        m.validate_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
            result=wrong_bool, context=real_bundle.context
        )
    wrong_int = copy.deepcopy(real_bundle.first)
    wrong_int["semantic_projection"]["summary"]["event_count"] = True
    _rehash_successor(wrong_int)
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError):
        m.validate_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
            result=wrong_int, context=real_bundle.context
        )


def test_dict_key_order_is_semantic_but_list_order_is_strict(real_bundle):
    reordered = {
        key: copy.deepcopy(real_bundle.first[key])
        for key in reversed(list(real_bundle.first))
    }
    projection = reordered["semantic_projection"]
    reordered["semantic_projection"] = {
        key: projection[key] for key in reversed(list(projection))
    }
    assert m.validate_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
        result=reordered, context=real_bundle.context
    )
    bad_order = copy.deepcopy(real_bundle.first)
    bad_order["semantic_projection"]["event_task_admission_records"][0:2] = reversed(
        bad_order["semantic_projection"]["event_task_admission_records"][0:2]
    )
    _rehash_successor(bad_order)
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError):
        m.validate_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
            result=bad_order, context=real_bundle.context
        )


def test_input_unchanged_and_results_deeply_isolated(real_bundle):
    assert real_bundle.first == real_bundle.second
    assert real_bundle.first is not real_bundle.second
    first_rows = real_bundle.first["semantic_projection"]["event_task_admission_records"]
    second_rows = real_bundle.second["semantic_projection"]["event_task_admission_records"]
    assert first_rows is not second_rows
    assert first_rows[0]["source_rule_basis"] is not second_rows[0]["source_rule_basis"]
    mutated = copy.deepcopy(real_bundle.first)
    mutated["semantic_projection"]["event_task_admission_records"][0]["source_rule_basis"][0]["passed"] = False
    assert real_bundle.second["semantic_projection"]["event_task_admission_records"][0]["source_rule_basis"][0]["passed"] is True
    assert real_bundle.context.frozen_evaluation_result["semantic_projection"]["event_task_records"][0]["candidate_status"] == m.SOURCE_ELIGIBLE


def test_json_roundtrip_validate_and_reserialize_is_byte_identical(real_bundle):
    parsed = json.loads(real_bundle.payload)
    assert m.validate_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
        result=parsed,
        context=real_bundle.context,
    )
    again = m.serialize_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
        result=parsed,
        context=real_bundle.context,
    )
    assert again == real_bundle.payload


def test_query_grants_base_and_task_c_seed(real_bundle):
    event_id = m.TARGET_EVENT_IDS_V1[0]
    base = m.query_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
        result=real_bundle.first,
        context=real_bundle.context,
        canonical_event_id=event_id,
        canonical_task_name="warhead_only",
        use_name="base_diffusion_inputs",
    )
    assert base["admission_use_decision"] == m.USE_GRANTED
    seed = m.query_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
        result=real_bundle.first,
        context=real_bundle.context,
        canonical_event_id=event_id,
        canonical_task_name="scaffold_plus_linker_plus_warhead",
        use_name="task_c_seed_condition",
    )
    assert seed["admission_use_decision"] == m.USE_GRANTED
    assert seed["formal_admission_effective"] is False


def test_query_revalidates_published_source(real_bundle, monkeypatch):
    calls = 0
    original = (
        m.evaluation_owner.
        validate_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1
    )

    def counted(**kwargs):
        nonlocal calls
        calls += 1
        return original(**kwargs)

    monkeypatch.setattr(
        m.evaluation_owner,
        "validate_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1",
        counted,
    )
    result = m.query_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
        result=real_bundle.first,
        context=real_bundle.context,
        canonical_event_id=m.TARGET_EVENT_IDS_V1[0],
        canonical_task_name="warhead_only",
        use_name="pair_contrastive",
    )
    assert result["admission_use_decision"] == m.USE_GRANTED
    assert calls >= 1


def test_query_results_are_deeply_isolated(real_bundle):
    kwargs = dict(
        result=real_bundle.first,
        context=real_bundle.context,
        canonical_event_id=m.TARGET_EVENT_IDS_V1[0],
        canonical_task_name="warhead_only",
        use_name="pair_contrastive",
    )
    first = m.query_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(**kwargs)
    second = m.query_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(**kwargs)
    first["required_source_rule_ids"].append("FORGED")
    assert "FORGED" not in second["required_source_rule_ids"]


@pytest.mark.parametrize(
    ("event_id", "task_name", "use_name", "reason"),
    [
        ("UNKNOWN_EVENT", "warhead_only", "base_diffusion_inputs", "EVENT_OUT_OF_SCOPE"),
        (m.TARGET_EVENT_IDS_V1[0], "sixth_task", "base_diffusion_inputs", "TASK_OUT_OF_SCOPE"),
        (m.TARGET_EVENT_IDS_V1[0], "warhead_only", "unknown_use", "UNKNOWN_OR_PROHIBITED"),
        (m.TARGET_EVENT_IDS_V1[0], "warhead_only", "PRE_geometry_training_supervision", "UNKNOWN_OR_PROHIBITED"),
    ],
)
def test_query_unknown_event_task_use_and_geometry_fail_closed(
    real_bundle, event_id, task_name, use_name, reason
):
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError, match=reason):
        m.query_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
            result=real_bundle.first,
            context=real_bundle.context,
            canonical_event_id=event_id,
            canonical_task_name=task_name,
            use_name=use_name,
        )


def test_query_non_c_seed_na_is_not_converted_to_grant(real_bundle):
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError, match="USE_NOT_GRANTED"):
        m.query_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
            result=real_bundle.first,
            context=real_bundle.context,
            canonical_event_id=m.TARGET_EVENT_IDS_V1[0],
            canonical_task_name="scaffold_only",
            use_name="task_c_seed_condition",
        )


def test_materializer_compares_existing_and_never_overwrites(real_bundle, tmp_path):
    target = tmp_path / "successor.json"
    assert m.materialize_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
        result=real_bundle.first, context=real_bundle.context, target_path=target
    ) is True
    assert m.materialize_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
        result=real_bundle.first, context=real_bundle.context, target_path=target
    ) is False
    target.write_bytes(b"different\n")
    with pytest.raises(m.POA4I3UExact8NongeometryFormalAdmissionSuccessorError, match="DIFFERENT_BYTES"):
        m.materialize_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
            result=real_bundle.first, context=real_bundle.context, target_path=target
        )
    assert target.read_bytes() == b"different\n"


def test_result_path_selection_is_independent_of_module_path():
    candidate = os.environ.get(RESULT_ENV)
    if candidate:
        assert Path(candidate).name == (
            "poa_4i3u_exact8_nongeometry_formal_admission_successor_v1.json"
        )
    if not os.environ.get(MODULE_ENV):
        assert m.__name__.startswith("covalent_ext.")


def test_zz_materialize_unique_real_result_without_overwrite(real_bundle):
    configured = os.environ.get(RESULT_ENV)
    if configured:
        target = Path(configured)
    else:
        target = (
            real_bundle.repository
            / "data/derived/covalent_small/"
            "covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1/"
            "poa_4i3u_exact8_nongeometry_formal_admission_successor_v1.json"
        )
    created = m.materialize_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
        result=real_bundle.first,
        context=real_bundle.context,
        target_path=target,
    )
    assert target.read_bytes() == real_bundle.payload
    assert created is True or created is False
    print(
        f"FROZEN_SUCCESSOR_RESULT={target} BYTES={len(real_bundle.payload)} "
        f"SHA256={m._sha256(real_bundle.payload)} CREATED={str(created).lower()}"
    )
