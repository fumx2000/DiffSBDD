from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import torch


MODULE_ENV = (
    "COVAPIE_POA_4I3U_EXACT8_NONGEOMETRY_ADMISSION_EVALUATOR_V1_MODULE"
)
RESULT_ENV = (
    "COVAPIE_POA_4I3U_EXACT8_NONGEOMETRY_ADMISSION_EVALUATION_V1_RESULT"
)


def _load_module():
    candidate = os.environ.get(MODULE_ENV)
    if candidate:
        path = Path(candidate).resolve(strict=True)
        spec = importlib.util.spec_from_file_location(
            "covapie_poa_4i3u_exact8_nongeometry_admission_evaluator_v1_candidate",
            path,
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(
        "covalent_ext."
        "covapie_poa_4i3u_exact8_nongeometry_admission_evaluator_v1"
    )


m = _load_module()


def _canonical(value: object, *, newline: bool = False) -> bytes:
    payload = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return payload + (b"\n" if newline else b"")


def _rehash(result: dict[str, object]) -> None:
    result["semantic_projection_sha256"] = hashlib.sha256(
        _canonical(result["semantic_projection"])
    ).hexdigest()


def _tiny_git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(repository), *arguments),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def _tiny_repository(tmp_path: Path) -> tuple[Path, str, bytes]:
    repository = tmp_path / "tiny-lineage"
    repository.mkdir()
    _tiny_git(repository, "init", "-q")
    _tiny_git(repository, "config", "user.name", "CovaPIE Test")
    _tiny_git(repository, "config", "user.email", "covapie-test@example.invalid")
    payload = b"fixed-source-v1\n"
    (repository / "pinned.txt").write_bytes(payload)
    _tiny_git(repository, "add", "--", "pinned.txt")
    _tiny_git(repository, "commit", "-q", "-m", "baseline")
    return repository, _tiny_git(repository, "rev-parse", "HEAD"), payload


def _passing_facts(task_id: int = 0):
    task = m.CANONICAL_TASKS_V1[task_id]
    return m.ScopedEventTaskFactsV1(
        canonical_event_id="UNIT_EVENT",
        canonical_task_id=task[0],
        canonical_task_name=task[1],
        canonical_task_alias=task[2],
        source_bound=True,
        target_population_member=True,
        human_review_completed=True,
        training_use_disposition="INCLUDE",
        human_training_excluded=False,
        explicit_covalent_event=True,
        formal_group_id=m.FORMAL_GROUP_ID,
        formal_split="train",
        formal_split_authoritative=True,
        formal_sample_training_admitted_preserved_false=True,
        exact10_feature_inputs_valid=True,
        role_partition_and_reactive_indices_valid=True,
        source_local_flat_mapping_valid=True,
        generated_count=task[3],
        fixed_count=task[4],
        seed_count=task[5],
        seed_mapping_valid=True,
        pair_candidate_count=42,
        pair_positive_count=1,
        pair_negative_count=41,
        pair_indices_sample_local=True,
        observed_complex_distance_finite_and_valid=True,
        geometry_nan_component_count=2,
        geometry_valid_component_count=0,
        geometry_loss_component_count=0,
        inactive_admission_and_loss_masks=True,
    )


@pytest.fixture(scope="session")
def real_bundle():
    repository = Path(os.environ["COVAPIE_REPOSITORY_ROOT"]).resolve(strict=True)
    state = Path(os.environ["COVAPIE_STATE_ROOT"]).resolve(strict=True)
    counts = {
        "formal_split_build": 0,
        "inactive_prepare": 0,
        "b1_assemble": 0,
        "b1_validate": 0,
        "structure_parse": 0,
        "result_build": 0,
    }

    originals = {
        "formal_split_build": (
            m.split_owner.build_covapie_poa_full_component_formal_split_authority_v1
        ),
        "inactive_prepare": (
            m.adapter_owner.prepare_covapie_poa_4i3u_exact8_inactive_consumer_adapter_v1
        ),
        "b1_assemble": (
            m.b1_owner.assemble_covapie_poa_4i3u_exact8_real_preview_evidence_v1
        ),
        "b1_validate": (
            m.b1_owner.validate_covapie_poa_4i3u_exact8_real_preview_evidence_v1
        ),
        "structure_parse": m.b1_owner.structure_owner._parse_and_crosscheck_atom_site,
        "result_build": (
            m.build_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1
        ),
    }

    def counted(name):
        def wrapper(*args, **kwargs):
            counts[name] += 1
            return originals[name](*args, **kwargs)
        return wrapper

    m.split_owner.build_covapie_poa_full_component_formal_split_authority_v1 = counted(
        "formal_split_build"
    )
    m.adapter_owner.prepare_covapie_poa_4i3u_exact8_inactive_consumer_adapter_v1 = counted(
        "inactive_prepare"
    )
    m.b1_owner.assemble_covapie_poa_4i3u_exact8_real_preview_evidence_v1 = counted(
        "b1_assemble"
    )
    m.b1_owner.validate_covapie_poa_4i3u_exact8_real_preview_evidence_v1 = counted(
        "b1_validate"
    )
    m.b1_owner.structure_owner._parse_and_crosscheck_atom_site = counted(
        "structure_parse"
    )
    m.build_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1 = counted(
        "result_build"
    )
    try:
        context = m.prepare_covapie_poa_4i3u_exact8_nongeometry_admission_evaluator_v1(
            repository_root=repository, state_root=state
        )
        before = {
            "context_seal": context.context_seal_sha256,
            "prepared_seal": context.prepared.completeness_seal_sha256,
            "base_lig_coords": context.prepared.base_preview.model_input_batch[
                "lig_coords"
            ].clone(),
            "payload_lig_coords": tuple(
                payload.model_input_batch["lig_coords"].clone()
                for payload in context.payloads
            ),
            "payload_geometry": tuple(
                payload.supervision.pre_post_geometry_target_angstrom.clone()
                for payload in context.payloads
            ),
        }
        first = m.build_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
            context=context
        )
        first_bytes = m.serialize_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
            result=first, context=context
        )
        second = m.build_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
            context=context
        )
        second_bytes = m.serialize_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
            result=second, context=context
        )
        after = {
            "context_seal": context.context_seal_sha256,
            "prepared_seal": context.prepared.completeness_seal_sha256,
            "base_lig_coords": context.prepared.base_preview.model_input_batch[
                "lig_coords"
            ].clone(),
            "payload_lig_coords": tuple(
                payload.model_input_batch["lig_coords"].clone()
                for payload in context.payloads
            ),
            "payload_geometry": tuple(
                payload.supervision.pre_post_geometry_target_angstrom.clone()
                for payload in context.payloads
            ),
        }
    finally:
        m.split_owner.build_covapie_poa_full_component_formal_split_authority_v1 = originals[
            "formal_split_build"
        ]
        m.adapter_owner.prepare_covapie_poa_4i3u_exact8_inactive_consumer_adapter_v1 = originals[
            "inactive_prepare"
        ]
        m.b1_owner.assemble_covapie_poa_4i3u_exact8_real_preview_evidence_v1 = originals[
            "b1_assemble"
        ]
        m.b1_owner.validate_covapie_poa_4i3u_exact8_real_preview_evidence_v1 = originals[
            "b1_validate"
        ]
        m.b1_owner.structure_owner._parse_and_crosscheck_atom_site = originals[
            "structure_parse"
        ]
        m.build_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1 = originals[
            "result_build"
        ]
    print(
        "REAL_EXECUTION_COUNTS="
        + ",".join(f"{key}:{value}" for key, value in counts.items())
    )
    return {
        "context": context,
        "first": first,
        "second": second,
        "first_bytes": first_bytes,
        "second_bytes": second_bytes,
        "before": before,
        "after": after,
        "counts": counts,
    }


def test_pure_fact_layer_requires_human_include_and_formal_split_independently():
    facts = _passing_facts()
    assert m.evaluate_scoped_event_task_facts_v1(facts)["candidate_status"] == m.ELIGIBLE
    no_include = replace(facts, training_use_disposition="EXCLUDE_FROM_TRAINING_ONLY")
    no_formal = replace(facts, formal_split_authoritative=False)
    assert m.evaluate_scoped_event_task_facts_v1(no_include)["candidate_status"] == m.BLOCKED
    assert m.evaluate_scoped_event_task_facts_v1(no_formal)["candidate_status"] == m.BLOCKED


@pytest.mark.parametrize(
    "mutation",
    (
        {"training_use_disposition": "EXCLUDE_FROM_TRAINING_ONLY"},
        {"formal_split": "test"},
        {"target_population_member": False},
        {"target_population_member": False, "formal_group_id": m.FORMAL_GROUP_ID},
    ),
)
def test_excluded_heldout_or_same_group_unapproved_event_is_blocked(mutation):
    result = m.evaluate_scoped_event_task_facts_v1(
        replace(_passing_facts(), **mutation)
    )
    assert result["candidate_status"] == m.BLOCKED
    assert result["blocked_reasons"]


def test_task_c_seed_is_required_without_inventing_a_non_c_dependency():
    missing_c = replace(_passing_facts(4), seed_count=0, seed_mapping_valid=False)
    non_c = replace(_passing_facts(0), seed_mapping_valid=False)
    assert m.evaluate_scoped_event_task_facts_v1(missing_c)["candidate_status"] == m.BLOCKED
    non_c_result = m.evaluate_scoped_event_task_facts_v1(non_c)
    assert non_c_result["candidate_status"] == m.ELIGIBLE
    assert non_c_result["eligibility"]["task_c_seed_condition"] == m.NOT_APPLICABLE


@pytest.mark.parametrize(
    "mutation",
    (
        {"pair_positive_count": 0},
        {"pair_negative_count": 0},
        {"pair_candidate_count": 43},
        {"pair_indices_sample_local": False},
    ),
)
def test_pair_domain_shortage_or_cross_sample_index_is_blocked(mutation):
    result = m.evaluate_scoped_event_task_facts_v1(
        replace(_passing_facts(), **mutation)
    )
    assert result["candidate_status"] == m.BLOCKED
    assert result["eligibility"]["pair_contrastive"] == m.BLOCKED


def test_nan_geometry_with_valid_and_loss_false_is_allowed_for_nongeometry():
    result = m.evaluate_scoped_event_task_facts_v1(_passing_facts())
    geometry_rule = next(
        row for row in result["rule_results"] if row["rule_id"] == "R11_GEOMETRY_EXCLUDED"
    )
    assert geometry_rule["passed"] is True
    assert result["candidate_status"] == m.ELIGIBLE


@pytest.mark.parametrize(
    "mutation",
    (
        {"geometry_nan_component_count": 1},
        {"geometry_valid_component_count": 1},
        {"geometry_loss_component_count": 1},
    ),
)
def test_geometry_fabrication_or_activation_is_rejected(mutation):
    result = m.evaluate_scoped_event_task_facts_v1(
        replace(_passing_facts(), **mutation)
    )
    assert result["candidate_status"] == m.BLOCKED


def test_observed_distance_is_not_accepted_as_geometry_target_authority():
    activated = replace(
        _passing_facts(), geometry_nan_component_count=0,
        geometry_valid_component_count=2, geometry_loss_component_count=2,
    )
    result = m.evaluate_scoped_event_task_facts_v1(activated)
    assert result["facts"]["observed_complex_distance_finite_and_valid"] is True
    assert result["candidate_status"] == m.BLOCKED


def test_pass_string_without_fixed_source_is_insufficient():
    facts = replace(_passing_facts(), source_bound=False)
    result = m.evaluate_scoped_event_task_facts_v1(facts)
    assert result["candidate_status"] == m.BLOCKED
    assert "PASS text alone" in " ".join(result["blocked_reasons"])


@pytest.mark.parametrize(
    "field,value",
    (
        ("source_bound", 1),
        ("canonical_task_id", True),
        ("pair_candidate_count", 42.0),
    ),
)
def test_fact_layer_rejects_bool_int_type_confusion(field, value):
    facts = replace(_passing_facts(), **{field: value})
    with pytest.raises(m.POA4I3UExact8NongeometryAdmissionEvaluatorError):
        m.evaluate_scoped_event_task_facts_v1(facts)


def test_baseline_equal_head_and_normal_successor_head_are_supported(tmp_path):
    repository, baseline, _ = _tiny_repository(tmp_path)
    m._validate_baseline_lineage(repository, baseline_commit=baseline)
    (repository / "successor.txt").write_text("successor\n")
    _tiny_git(repository, "add", "--", "successor.txt")
    _tiny_git(repository, "commit", "-q", "-m", "normal successor")
    assert _tiny_git(repository, "rev-parse", "HEAD") != baseline
    m._validate_baseline_lineage(repository, baseline_commit=baseline)


def test_missing_baseline_commit_is_rejected(tmp_path):
    repository, _, _ = _tiny_repository(tmp_path)
    with pytest.raises(
        m.POA4I3UExact8NongeometryAdmissionEvaluatorError,
        match="BASELINE_OR_HEAD_COMMIT_OBJECT_UNAVAILABLE",
    ):
        m._validate_baseline_lineage(repository, baseline_commit="0" * 40)


def test_head_outside_baseline_lineage_is_rejected(tmp_path):
    repository, baseline, _ = _tiny_repository(tmp_path)
    _tiny_git(repository, "switch", "-q", "--orphan", "unrelated")
    pinned = repository / "pinned.txt"
    if pinned.exists():
        pinned.unlink()
    (repository / "unrelated.txt").write_text("independent root\n")
    _tiny_git(repository, "add", "--", "unrelated.txt")
    _tiny_git(repository, "commit", "-q", "-m", "unrelated root")
    with pytest.raises(
        m.POA4I3UExact8NongeometryAdmissionEvaluatorError,
        match="BASELINE_IS_NOT_ANCESTOR_OF_HEAD",
    ):
        m._validate_baseline_lineage(repository, baseline_commit=baseline)


def test_git_ancestry_command_runtime_error_fails_closed(tmp_path, monkeypatch):
    repository, baseline, _ = _tiny_repository(tmp_path)
    real_run = m.subprocess.run

    def failing_merge_base(arguments, **kwargs):
        if "merge-base" in arguments:
            return subprocess.CompletedProcess(arguments, 128, "", "simulated error")
        return real_run(arguments, **kwargs)

    monkeypatch.setattr(m.subprocess, "run", failing_merge_base)
    with pytest.raises(
        m.POA4I3UExact8NongeometryAdmissionEvaluatorError,
        match="BASELINE_ANCESTRY_GIT_COMMAND_FAILED",
    ):
        m._validate_baseline_lineage(repository, baseline_commit=baseline)


def test_successor_does_not_allow_fixed_source_worktree_drift(tmp_path):
    repository, baseline, payload = _tiny_repository(tmp_path)
    blob = _tiny_git(repository, "rev-parse", f"{baseline}:pinned.txt")
    spec = (
        "unit_fixed_source", "pinned.txt", len(payload),
        hashlib.sha256(payload).hexdigest(), blob,
    )
    m._source_binding_from_spec(
        repository, spec, baseline_commit=baseline
    )
    (repository / "successor.txt").write_text("successor\n")
    _tiny_git(repository, "add", "--", "successor.txt")
    _tiny_git(repository, "commit", "-q", "-m", "normal successor")
    m._validate_baseline_lineage(repository, baseline_commit=baseline)
    (repository / "pinned.txt").write_bytes(b"drifted-source\n")
    with pytest.raises(
        m.POA4I3UExact8NongeometryAdmissionEvaluatorError,
        match="DIRECT_SOURCE_IDENTITY_MISMATCH:pinned.txt",
    ):
        m._source_binding_from_spec(
            repository, spec, baseline_commit=baseline
        )


def test_real_exact8_canonical5_evaluation(real_bundle):
    result = real_bundle["first"]
    projection = result["semantic_projection"]
    rows = projection["event_task_records"]
    assert len(rows) == 40
    assert len({row["canonical_event_id"] for row in rows}) == 8
    assert [row["canonical_task_name"] for row in rows[:5]] == [
        row[1] for row in m.CANONICAL_TASKS_V1
    ]
    assert all(row["candidate_status"] == m.ELIGIBLE for row in rows)
    assert projection["summary"]["batch_status"] == (
        "ALL_40_ELIGIBLE_FOR_SCOPED_NON_GEOMETRY_USE"
    )
    assert projection["summary"]["pair_candidate_count"] == 336
    assert projection["summary"]["pair_positive_count"] == 8
    assert projection["summary"]["pair_negative_count"] == 328
    assert projection["summary"]["total_pocket_node_count"] == 2106


def test_real_masks_seed_and_inactive_boundaries(real_bundle):
    context = real_bundle["context"]
    assert [
        (
            payload.summary.generated_count_per_event[0],
            payload.summary.fixed_count_per_event[0],
            payload.summary.seed_count_per_event[0],
        )
        for payload in context.payloads
    ] == [(2, 5, 0), (3, 4, 0), (6, 1, 0), (4, 3, 0), (7, 0, 2)]
    for payload in context.payloads:
        supervision = payload.supervision
        assert not bool(supervision.sample_training_admitted.any().item())
        assert not bool(supervision.ligand_active_diffusion_loss_mask.any().item())
        assert not bool(supervision.pair_head_candidate_loss_mask.any().item())
        assert not bool(supervision.pair_contrastive_sample_loss_mask.any().item())
        assert bool(torch.isnan(supervision.pre_post_geometry_target_angstrom).all().item())
        assert not bool(supervision.pre_post_geometry_component_valid_mask.any().item())
        assert not bool(supervision.pre_post_geometry_component_loss_mask.any().item())


def test_real_task_c_seed_mapping_is_p_o1p_local_6_3_primary_p(real_bundle):
    payload = real_bundle["context"].payloads[4]
    for mapping in payload.seed_anchor_mappings:
        assert mapping.approved_seed_atom_ids == ("P", "O1P")
        assert mapping.seed_model_sample_local_indices_0based == (6, 3)
        assert mapping.ligand_primary_anchor_atom_id == "P"
        assert mapping.primary_anchor_model_sample_local_index_0based == 6
        assert "PROTEIN_TARGET_CYS_SG" in mapping.ligand_anchor_distance_reference_semantics
    assert not bool(payload.supervision.ligand_base_fixed_mask.any().item())


def test_formal_group_is_24_but_only_exact8_is_targeted(real_bundle):
    context = real_bundle["context"]
    formal = context.formal_split_result
    assert formal.formal_group_id == m.FORMAL_GROUP_ID
    assert formal.formal_split == "train"
    assert formal.formal_split_authoritative is True
    assert formal.sample_training_admitted is False
    assert len(formal.full_member_canonical_event_ids) == 24
    assert len(context.target_event_ids) == 8
    assert all(":4I3U:" in event_id for event_id in context.target_event_ids)
    assert not any(":4I3V:" in event_id for event_id in context.target_event_ids)
    assert not any(":4I3W:" in event_id for event_id in context.target_event_ids)


def test_source_bindings_are_complete_metadata_not_payload_dump(real_bundle):
    projection = real_bundle["first"]["semantic_projection"]
    sources = projection["source_bindings"]
    assert len(sources["direct_policy_and_owner_bindings"]) == 8
    assert len(sources["inactive_adapter_transitive_repository_bindings"]) == 8
    assert sources["formal_split_repository_bindings"]
    assert len(sources["state_source_bindings"]) == 3
    serialized = real_bundle["first_bytes"]
    assert b'"lig_coords"' not in serialized
    assert b'"pocket_coords"' not in serialized
    assert b'"tensor"' not in serialized.lower()


def test_result_validator_rejects_source_sha_schema_strict_bool_and_uniqueness(real_bundle):
    context = real_bundle["context"]
    mutations = []
    bad_sha = copy.deepcopy(real_bundle["first"])
    bad_sha["semantic_projection"]["source_bindings"][
        "direct_policy_and_owner_bindings"
    ][0]["sha256"] = "0" * 64
    mutations.append(bad_sha)
    bad_schema = copy.deepcopy(real_bundle["first"])
    bad_schema["schema_version"] = "wrong"
    mutations.append(bad_schema)
    bad_bool = copy.deepcopy(real_bundle["first"])
    bad_bool["semantic_projection"]["permission_boundary"][
        "FORMAL_ADMISSION_EFFECTIVE"
    ] = 0
    mutations.append(bad_bool)
    duplicate = copy.deepcopy(real_bundle["first"])
    rows = duplicate["semantic_projection"]["event_task_records"]
    rows[5]["canonical_event_id"] = rows[0]["canonical_event_id"]
    rows[5]["facts"]["canonical_event_id"] = rows[0]["canonical_event_id"]
    mutations.append(duplicate)
    for result in mutations:
        _rehash(result)
        with pytest.raises(m.POA4I3UExact8NongeometryAdmissionEvaluatorError):
            m.validate_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
                result=result, context=context
            )


def test_tamper_and_recomputed_digest_still_fails_source_fact_recheck(real_bundle):
    result = copy.deepcopy(real_bundle["first"])
    result["semantic_projection"]["event_task_records"][0]["candidate_status"] = m.BLOCKED
    _rehash(result)
    with pytest.raises(m.POA4I3UExact8NongeometryAdmissionEvaluatorError):
        m.validate_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
            result=result, context=real_bundle["context"]
        )


def test_builder_serialize_parse_validate_and_frozen_json_roundtrip(real_bundle):
    context = real_bundle["context"]
    frozen = Path(os.environ[RESULT_ENV]).read_bytes()
    fresh = m.build_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
        context=context
    )
    generated = m.serialize_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
        result=fresh, context=context
    )
    assert generated == frozen
    parsed_generated = json.loads(generated)
    assert m.validate_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
        result=parsed_generated, context=context
    )
    assert m.serialize_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
        result=parsed_generated, context=context
    ) == frozen
    parsed_frozen = json.loads(frozen)
    assert m.validate_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
        result=parsed_frozen, context=context
    )
    assert m.serialize_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
        result=parsed_frozen, context=context
    ) == frozen
    print("SUCCESSOR_JSON_ROUNDTRIP_PUBLIC_RESULT_BUILDS=1")


def test_dict_key_order_is_ignored_at_top_and_nested_levels(real_bundle):
    context = real_bundle["context"]
    parsed = json.loads(Path(os.environ[RESULT_ENV]).read_bytes())
    projection = parsed["semantic_projection"]
    projection["summary"] = {
        key: projection["summary"][key]
        for key in reversed(tuple(projection["summary"]))
    }
    projection["rule_definitions"][0] = {
        key: projection["rule_definitions"][0][key]
        for key in reversed(tuple(projection["rule_definitions"][0]))
    }
    parsed["semantic_projection"] = {
        key: projection[key] for key in reversed(tuple(projection))
    }
    reordered = {key: parsed[key] for key in reversed(tuple(parsed))}
    assert m.validate_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
        result=reordered, context=context
    )


def test_ordered_event_task_list_reordering_is_still_rejected(real_bundle):
    context = real_bundle["context"]
    parsed = json.loads(Path(os.environ[RESULT_ENV]).read_bytes())
    rows = parsed["semantic_projection"]["event_task_records"]
    rows[0], rows[1] = rows[1], rows[0]
    _rehash(parsed)
    with pytest.raises(m.POA4I3UExact8NongeometryAdmissionEvaluatorError):
        m.validate_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
            result=parsed, context=context
        )


@pytest.mark.parametrize("mutation", ("missing", "extra", "bool_as_int"))
def test_roundtrip_validator_preserves_key_and_strict_type_rejection(
    real_bundle, mutation
):
    context = real_bundle["context"]
    parsed = json.loads(Path(os.environ[RESULT_ENV]).read_bytes())
    if mutation == "missing":
        parsed.pop("record_role")
    elif mutation == "extra":
        parsed["unexpected"] = False
    else:
        parsed["semantic_projection"]["permission_boundary"][
            "FORMAL_ADMISSION_EFFECTIVE"
        ] = 0
        _rehash(parsed)
    with pytest.raises(m.POA4I3UExact8NongeometryAdmissionEvaluatorError):
        m.validate_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
            result=parsed, context=context
        )


def test_rule_and_feature_metadata_are_deeply_isolated_on_direct_returns(real_bundle):
    context = real_bundle["context"]
    frozen = Path(os.environ[RESULT_ENV]).read_bytes()
    first = m.build_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
        context=context
    )
    second = m.build_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
        context=context
    )
    first_rules = first["semantic_projection"]["rule_definitions"]
    second_rules = second["semantic_projection"]["rule_definitions"]
    first_features = first["semantic_projection"]["feature_semantics_and_use_check"]
    second_features = second["semantic_projection"]["feature_semantics_and_use_check"]
    assert first_rules is not second_rules
    assert first_rules[0] is not second_rules[0]
    assert first_rules[0]["fields"] is not second_rules[0]["fields"]
    assert first_rules[0] is not m.RULE_DEFINITIONS_V1[0]
    assert first_rules[0]["fields"] is not m.RULE_DEFINITIONS_V1[0]["fields"]
    assert first_features is not second_features
    assert first_features[0] is not second_features[0]
    assert first_features[0]["actual_fields"] is not second_features[0]["actual_fields"]
    assert first_features[0] is not m.FEATURE_USE_AUDIT_V1[0]
    assert (
        first_features[0]["actual_fields"]
        is not m.FEATURE_USE_AUDIT_V1[0]["actual_fields"]
    )
    expected_rule = copy.deepcopy(m.RULE_DEFINITIONS_V1[0])
    expected_feature = copy.deepcopy(m.FEATURE_USE_AUDIT_V1[0])
    first_rules[0]["statement"] = "DIRECT_RETURN_MUTATION"
    first_rules[0]["fields"].append("mutated field")
    first_features[0]["boundary"] = "DIRECT_RETURN_MUTATION"
    first_features[0]["actual_fields"].append("mutated field")
    _rehash(first)
    with pytest.raises(m.POA4I3UExact8NongeometryAdmissionEvaluatorError):
        m.validate_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
            result=first, context=context
        )
    assert second_rules[0] == expected_rule
    assert second_features[0] == expected_feature
    assert m.RULE_DEFINITIONS_V1[0] == expected_rule
    assert m.FEATURE_USE_AUDIT_V1[0] == expected_feature
    third = m.build_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
        context=context
    )
    assert m.serialize_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
        result=second, context=context
    ) == frozen
    assert m.serialize_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
        result=third, context=context
    ) == frozen
    print("SUCCESSOR_DEEP_ISOLATION_PUBLIC_RESULT_BUILDS=3")


def test_inputs_immutable_results_isolated_and_bytes_deterministic(real_bundle):
    assert real_bundle["first_bytes"] == real_bundle["second_bytes"]
    assert real_bundle["first"] is not real_bundle["second"]
    assert real_bundle["before"]["context_seal"] == real_bundle["after"]["context_seal"]
    assert real_bundle["before"]["prepared_seal"] == real_bundle["after"]["prepared_seal"]
    assert torch.equal(
        real_bundle["before"]["base_lig_coords"],
        real_bundle["after"]["base_lig_coords"],
    )
    for before, after in zip(
        real_bundle["before"]["payload_lig_coords"],
        real_bundle["after"]["payload_lig_coords"],
        strict=True,
    ):
        assert torch.equal(before, after)
    for before, after in zip(
        real_bundle["before"]["payload_geometry"],
        real_bundle["after"]["payload_geometry"],
        strict=True,
    ):
        assert torch.equal(torch.isnan(before), torch.isnan(after))
    changed = copy.deepcopy(real_bundle["first"])
    changed["semantic_projection"]["summary"]["event_count"] = 99
    assert real_bundle["second"]["semantic_projection"]["summary"]["event_count"] == 8


def test_prepare_build_and_parse_counts_are_layered(real_bundle):
    assert real_bundle["counts"] == {
        "formal_split_build": 1,
        "inactive_prepare": 1,
        "b1_assemble": 1,
        "b1_validate": 1,
        "structure_parse": 16,
        "result_build": 2,
    }


def test_feature_use_boundary_and_unavailable_supervision_are_explicit(real_bundle):
    projection = real_bundle["first"]["semantic_projection"]
    subjects = {
        row["subject"] for row in projection["feature_semantics_and_use_check"]
    }
    assert subjects == {
        "element_channels", "roles_and_masks", "indices", "task_c_seed",
        "reactive_pair_and_domains", "coordinates_and_distance",
    }
    unavailable = set(projection["explicitly_unavailable_supervision"])
    assert "PRE_geometry_training_supervision" in unavailable
    assert "POST_geometry_training_supervision" in unavailable
    assert "warhead_type_classification_target" in unavailable
    assert "reaction_family_target" in unavailable
    boundary = projection["permission_boundary"]
    assert boundary == m.PERMISSION_BOUNDARY_V1


def test_zz_freeze_unique_real_result_without_overwrite(real_bundle):
    destination_value = os.environ.get(RESULT_ENV)
    if not destination_value:
        pytest.skip("candidate freeze path not configured for installed-path test")
    destination = Path(destination_value)
    expected_parent = Path(os.environ[MODULE_ENV]).resolve(strict=True).parent
    assert destination.parent.resolve(strict=True) == expected_parent
    payload = real_bundle["first_bytes"]
    if destination.exists():
        assert destination.is_file() and not destination.is_symlink()
        assert destination.read_bytes() == payload
    else:
        with destination.open("xb") as handle:
            handle.write(payload)
    assert destination.read_bytes() == payload
    print(
        "FROZEN_RESULT_BYTES=" + str(len(payload))
        + " SHA256=" + hashlib.sha256(payload).hexdigest()
    )
