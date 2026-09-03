from __future__ import annotations

import ast
import copy
from dataclasses import asdict, dataclass, replace
import hashlib
import importlib.util
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_gd1_v1
    as gd1_predecessor,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_sr2_v1 as subject,
)
from covalent_ext import (
    covapie_sr2_completed_decision_ingestion_and_task_label_availability_v1
    as sr2_ingestion_owner,
)


ROOT = Path(__file__).resolve().parents[1]
SUBJECT_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_sr2_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_completed_human_decision_reconciliation_with_sr2_v1.py"
)
FORMAL_PATH = sr2_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix()
GENERIC_FIELDS = (
    "canonical_event_id",
    "review_unit_id",
    "human_review_completed",
    "legacy_completed_review_status",
    "task_relevance_disposition",
    "chemistry_disposition",
    "training_disposition",
    "human_training_excluded",
    "source_decision_schema",
    "source_decision_sha256",
    "source_binding_path",
)
FORBIDDEN_RICH_FIELDS = (
    "protein_reactive_atom",
    "ligand_reactive_atom",
    "role_profile",
    "selected_candidate",
    "warhead_atoms",
    "linker_atoms",
    "scaffold_atoms",
    "boundary_bonds",
    "canonical_mask_applicability",
    "PRE_geometry",
    "PRE_topology",
    "PRE_status",
    "POST_geometry",
    "POST_distance",
    "engineered_surrogate_context",
    "target_directed_medicinal_covalent_context",
    "future_training_candidate",
    "future_training_admission_candidate",
    "future_training_admission_status",
    "training_use_allowed",
    "training_admission",
    "formal_training_admitted",
    "training_materialization_allowed",
    "tensor_target",
    "current_runtime_model_usable",
    "reaction_family",
    "warhead_rule",
    "warhead_type",
)
RICH_ONLY_TOKENS = (
    "Candidate15",
    "SELECT_CANDIDATE_15",
    "C9-N11",
    "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
    "PRE_REACTION_UNRESOLVED",
    "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
    "ENGINEERED_SURROGATE_CONTEXT",
    "engineered Src S345C",
    "engineered Src T338M/S345C",
    "EGFR C797",
    "EGFR T790M",
    "CANDIDATE_REQUIRES_INDEPENDENT_FUTURE_ADMISSION",
)
BEFORE_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 111,
    "completed_positive_unit_count": 17,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "completed_total_event_count": 139,
    "completed_total_unit_count": 22,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 199,
    "unreviewed_unit_count": 109,
}
AFTER_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 115,
    "completed_positive_unit_count": 18,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "completed_total_event_count": 143,
    "completed_total_unit_count": 23,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 195,
    "unreviewed_unit_count": 108,
}
ALLOWED_CHANGED_FIELDS = {
    "current_review_status",
    "current_status_authority_sources_json",
    "calibration_eligible",
    "calibration_exclusion_reason",
}


@pytest.fixture(scope="module")
def bound() -> dict[str, object]:
    return sr2_ingestion_owner.load_frozen_formal_decision_v1(ROOT)


@pytest.fixture(scope="module")
def projection(bound: dict[str, object]) -> generic.NormalizedDecisionSource:
    return subject._project_validated_sr2_binding_v1(bound)


@pytest.fixture(scope="module")
def source_chains() -> tuple[
    tuple[generic.NormalizedDecisionSource, ...],
    tuple[generic.NormalizedDecisionSource, ...],
]:
    before = gd1_predecessor.load_real_completed_decision_sources_with_gd1_v1(
        ROOT
    )
    after = subject.load_real_completed_decision_sources_with_sr2_v1(ROOT)
    return before, after


@pytest.fixture(scope="module")
def reconciliations() -> tuple[
    generic.ReconciliationResult, generic.ReconciliationResult
]:
    before = (
        gd1_predecessor.reconcile_real_completed_human_decisions_with_gd1_v1(
            ROOT
        )
    )
    after = subject.reconcile_real_completed_human_decisions_with_sr2_v1(ROOT)
    return before, after


@pytest.fixture(scope="module")
def checker():
    spec = importlib.util.spec_from_file_location(
        "sr2_reconciliation_checker", ROOT / CHECKER_RELATIVE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _mutated_bound(
    bound: dict[str, object], section: str, key: str, value: object
) -> dict[str, object]:
    candidate = copy.deepcopy(bound)
    formal = candidate["formal"]
    assert isinstance(formal, dict)
    target = formal[section]
    assert isinstance(target, dict)
    target[key] = value
    return candidate


def _replace_source_fact(
    source: generic.NormalizedDecisionSource, **updates: object
) -> generic.NormalizedDecisionSource:
    facts = (replace(source.facts[0], **updates), *source.facts[1:])
    return replace(source, facts=facts)


def test_public_api_is_exact4() -> None:
    assert subject.__all__ == (
        "CompletedDecisionReconciliationWithSR2Error",
        "project_sr2_completed_decision_v1",
        "load_real_completed_decision_sources_with_sr2_v1",
        "reconcile_real_completed_human_decisions_with_sr2_v1",
    )


def test_direct_predecessor_and_runtime_dependencies_are_exact3() -> None:
    tree = ast.parse((ROOT / SUBJECT_RELATIVE).read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 1
        for alias in node.names
        if alias.name.startswith("covapie_")
    }
    assert imports == {
        "covapie_completed_human_decision_reconciliation_v1",
        "covapie_completed_human_decision_reconciliation_with_gd1_v1",
        "covapie_sr2_completed_decision_ingestion_and_task_label_availability_v1",
    }
    text = (ROOT / SUBJECT_RELATIVE).read_text(encoding="utf-8").lower()
    assert "with_4m5" not in text
    assert "with_cer" not in text
    assert "with_1n0" not in text


def test_published_runtime_lineage_identities_are_exact() -> None:
    expected = (
        (
            "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py",
            35925,
            "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548",
        ),
        (
            "src/covalent_ext/"
            "covapie_completed_human_decision_reconciliation_with_gd1_v1.py",
            33608,
            "bc83f32892c5f6d07ad1cabec66a233f7af927420216cf9a4278abcc9f623690",
        ),
        (
            "src/covalent_ext/"
            "covapie_sr2_completed_decision_ingestion_and_task_label_availability_v1.py",
            97771,
            "c34e42ef8d4cd7fba6ca7d259e2c103f1a6e81d604f76a7581ba47ae7259c8a8",
        ),
    )
    for relative, byte_count, sha256 in expected:
        payload = (ROOT / relative).read_bytes()
        assert len(payload) == byte_count
        assert hashlib.sha256(payload).hexdigest() == sha256


def test_formal_validator_lifecycle_is_provenance_only(
    bound: dict[str, object],
) -> None:
    assert bound["formal_semantics_independently_validated"] is True
    assert bound["formal_validator_provenance_identity_only"] is True
    assert bound["formal_validator_imported"] is False
    assert bound["formal_validator_executed"] is False
    assert bound["formal_validator_subprocess_called"] is False
    assert bound["formal_validator_runtime_dependency"] is False


def test_rich_formal_completion_and_d1_d6_are_exact(
    bound: dict[str, object],
) -> None:
    events = subject._validate_rich_sr2_semantics_v1(bound)
    formal = bound["formal"]
    assert isinstance(formal, dict)
    assert formal["schema_version"] == "covapie_sr2_exact4_formal_human_decision_v1"
    assert formal["record_role"] == (
        "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY"
    )
    assert formal["approved"] is True
    assert formal["unsigned"] is False
    assert formal["decision_finalized"] is True
    assert formal["human_review_completed"] is True
    assert formal["human_decision_created"] is True
    assert formal["formal_authority_created"] is True
    assert formal["formal_authority_is_human"] is True
    assert formal["machine_approval"] is False
    human = formal["human_authorization"]
    assert human["D1_task_relevance"] == "RELEVANT"
    assert human["D2_chemistry"] == "POSITIVE"
    assert human["D3_reactive_pair"] == "CONFIRM_OBSERVED_PAIR"
    assert human["D4_role_candidate"] == "SELECT_CANDIDATE_15"
    assert human["D5_training_use"] == "INCLUDE"
    assert len(events) == 4
    d6 = human["D6_scientific_context"].encode("utf-8")
    assert len(d6) == 1236
    assert hashlib.sha256(d6).hexdigest() == (
        "532f50bf3fe296ea76a548d9e6dc9b38b6d4ec9b8b3535e75f0c0b4e377e6cfa"
    )


def test_sr2_exact4_identity_ranks_unit_and_contexts_are_exact(
    bound: dict[str, object],
) -> None:
    events = subject._validate_rich_sr2_semantics_v1(bound)
    formal = bound["formal"]
    assert isinstance(formal, dict)
    assert tuple(row["canonical_event_id"] for row in events) == (
        "COVAPIE_CYS_SG_EVENT_V1:2QLQ:A:CYS:345-:SG:C:SR2:C51",
        "COVAPIE_CYS_SG_EVENT_V1:2QLQ:B:CYS:345-:SG:E:SR2:C51",
        "COVAPIE_CYS_SG_EVENT_V1:2QQ7:A:CYS:345-:SG:C:SR2:C51",
        "COVAPIE_CYS_SG_EVENT_V1:2QQ7:B:CYS:345-:SG:D:SR2:C51",
    )
    assert tuple(row["scaleup_rank"] for row in events) == (321, 323, 337, 338)
    assert formal["identity"]["review_unit_id"] == (
        "COVAPIE_BULK_REVIEW_UNIT_A9BBD5309D7A5C08"
    )
    assert formal["identity"]["contexts_collapsed"] is False


def test_rich_pair_candidate15_roles_exact5_and_bound_runtime_are_proven(
    bound: dict[str, object],
) -> None:
    subject._validate_rich_sr2_semantics_v1(bound)
    formal = bound["formal"]
    assert isinstance(formal, dict)
    pair = formal["reactive_pair_authority"]
    role = formal["selected_role_partition"]
    tasks = formal["canonical_Exact5_and_sample_applicability"]
    assert (pair["protein_reactive_atom"], pair["ligand_reactive_atom"]) == (
        "SG",
        "C51",
    )
    assert pair["reactive_pair_sample_authority"] is True
    assert pair["reusable_pair_rule_created"] is False
    assert pair["cross_structure_regiochemistry_generalization"] is False
    assert role["selected_candidate_index_0based"] == 15
    assert role["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    assert role["W_L_S_counts"] == [9, 0, 18]
    assert role["boundary_bonds"] == [dict(sr2_ingestion_owner.BOUNDARY_BONDS[0])]
    assert role["applicable_task_ids"] == [0, 3, 4]
    assert role["human_selected"] is True
    assert role["machine_selected"] is False
    assert role["machine_recommended"] is False
    assert tasks["global_canonical_task_count"] == 5
    assert [row["semantic_name"] for row in tasks["global_canonical_Exact5"]] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert tasks["B3_present"] is True
    assert tasks["sixth_task_present"] is False


def test_rich_training_include_is_not_admission(
    bound: dict[str, object],
) -> None:
    subject._validate_rich_sr2_semantics_v1(bound)
    formal = bound["formal"]
    assert isinstance(formal, dict)
    training = formal["training_use_boundary"]
    derived = sr2_ingestion_owner._training_boundary()
    assert training["D5_human_choice"] == "INCLUDE"
    assert derived["training_use_allowed"] is True
    assert training["human_training_excluded"] is False
    assert training["future_training_admission_candidate"] is True
    assert derived["future_training_admission_status"] == (
        "CANDIDATE_REQUIRES_INDEPENDENT_FUTURE_ADMISSION"
    )
    assert training["formal_training_admitted"] is False
    assert training["training_admission_created"] is False
    assert training["training_materialization_allowed"] is False
    assert training["tensor_target_created"] is False
    assert training["current_runtime_model_usable"] is False
    assert training["parameter_update_authorization"] is False
    assert training["READY_FOR_TRAINING"] is False


def test_rich_pre_post_and_engineered_surrogate_caveat_are_proven(
    bound: dict[str, object],
) -> None:
    subject._validate_rich_sr2_semantics_v1(bound)
    formal = bound["formal"]
    assert isinstance(formal, dict)
    pre = formal["PRE_POST_boundary"]
    post = formal["POST_evidence_boundary"]
    engineered = formal["engineered_surrogate_caveat"]
    assert pre["PRE_source_graph_count_per_event"] == 1
    assert pre["PRE_mapping_count_per_event"] == 0
    assert pre["PRE_mapping_status"] == "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
    assert pre["PRE_status"] == "PRE_REACTION_UNRESOLVED"
    assert post["POST_source_evidence_count"] == 4
    assert engineered["ENGINEERED_SURROGATE_CONTEXT"] is True
    assert engineered["TARGET_DIRECTED_MEDICINAL_COVALENT_CONTEXT"] is True
    assert engineered["per_structure_context"] == [
        {"engineered_context": "engineered Src S345C", "pdb_id": "2QLQ"},
        {
            "engineered_context": "engineered Src T338M/S345C",
            "pdb_id": "2QQ7",
        },
    ]
    assert engineered["native_Src_S345_authority"] is False
    assert engineered["EGFR_C797_event_specific_authority"] is False
    assert engineered["EGFR_T790M_event_specific_structure_authority"] is False
    assert engineered["cross_target_transfer_authority"] is False


@pytest.mark.parametrize(
    ("section", "key", "value", "token"),
    (
        ("human_authorization", "D1_task_relevance", "NOT_RELEVANT", "SR2_D1_D5"),
        ("human_authorization", "D2_chemistry", "NEGATIVE", "SR2_D1_D5"),
        ("human_authorization", "D3_reactive_pair", "REJECT", "SR2_D1_D5"),
        (
            "human_authorization",
            "D4_role_candidate",
            "SELECT_CANDIDATE_14",
            "SR2_D1_D5",
        ),
        (
            "human_authorization",
            "D5_training_use",
            "EXCLUDE_FROM_TRAINING_ONLY",
            "SR2_D1_D5",
        ),
        (
            "training_use_boundary",
            "human_training_excluded",
            True,
            "SR2_RICH_TRAINING_INCLUDE_BOUNDARY_INVALID",
        ),
        (
            "training_use_boundary",
            "future_training_admission_candidate",
            False,
            "SR2_RICH_TRAINING_INCLUDE_BOUNDARY_INVALID",
        ),
        (
            "training_use_boundary",
            "formal_training_admitted",
            True,
            "SR2_RICH_TRAINING_INCLUDE_BOUNDARY_INVALID",
        ),
        (
            "training_use_boundary",
            "training_materialization_allowed",
            True,
            "SR2_RICH_TRAINING_INCLUDE_BOUNDARY_INVALID",
        ),
        (
            "training_use_boundary",
            "current_runtime_model_usable",
            True,
            "SR2_RICH_TRAINING_INCLUDE_BOUNDARY_INVALID",
        ),
        (
            "reactive_pair_authority",
            "ligand_reactive_atom",
            "C50",
            "SR2_SG_C51_PAIR_AUTHORITY_INVALID",
        ),
        (
            "selected_role_partition",
            "selected_candidate_index_0based",
            14,
            "SR2_CANDIDATE15_DIRECT_ROLE_PARTITION_INVALID",
        ),
        (
            "PRE_POST_boundary",
            "PRE_status",
            "PRE_REACTION_RESOLVED",
            "SR2_RICH_PRE_POST_BOUNDARY_INVALID",
        ),
        (
            "engineered_surrogate_caveat",
            "native_Src_S345_authority",
            True,
            "SR2_ENGINEERED_SURROGATE_CAVEAT_INVALID",
        ),
        (
            "engineered_surrogate_caveat",
            "EGFR_C797_event_specific_authority",
            True,
            "SR2_ENGINEERED_SURROGATE_CAVEAT_INVALID",
        ),
        (
            "engineered_surrogate_caveat",
            "cross_target_transfer_authority",
            True,
            "SR2_ENGINEERED_SURROGATE_CAVEAT_INVALID",
        ),
    ),
)
def test_critical_rich_mutations_fail_closed(
    bound: dict[str, object],
    section: str,
    key: str,
    value: object,
    token: str,
) -> None:
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithSR2Error, match=token
    ):
        subject._validate_rich_sr2_semantics_v1(
            _mutated_bound(bound, section, key, value)
        )


@pytest.mark.parametrize(
    ("key", "value"),
    (("B3_present", False), ("sixth_task_present", True)),
)
def test_exact5_mutations_fail_closed(
    bound: dict[str, object], key: str, value: object
) -> None:
    candidate = _mutated_bound(
        bound,
        "canonical_Exact5_and_sample_applicability",
        key,
        value,
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithSR2Error,
        match="SR2_CANONICAL_EXACT5_APPLICABILITY_INVALID",
    ):
        subject._validate_rich_sr2_semantics_v1(candidate)


def test_exact4_missing_duplicate_and_extra_events_fail_closed(
    bound: dict[str, object],
) -> None:
    for operation in ("missing", "duplicate", "extra"):
        candidate = copy.deepcopy(bound)
        formal = candidate["formal"]
        assert isinstance(formal, dict)
        events = formal["event_level_formal_human_decisions"]
        assert isinstance(events, list)
        if operation == "missing":
            events.pop()
        elif operation == "duplicate":
            events[-1] = copy.deepcopy(events[0])
        else:
            events.append(copy.deepcopy(events[0]))
        with pytest.raises(subject.CompletedDecisionReconciliationWithSR2Error):
            subject._validate_rich_sr2_semantics_v1(candidate)


def test_wrong_review_unit_fails_closed(bound: dict[str, object]) -> None:
    candidate = _mutated_bound(
        bound,
        "identity",
        "review_unit_id",
        "COVAPIE_BULK_REVIEW_UNIT_WRONG",
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithSR2Error,
        match="SR2_FORMAL_IDENTITY_NOT_EXACT4",
    ):
        subject._validate_rich_sr2_semantics_v1(candidate)


def test_generic_fact_schema_is_exact11_and_rich_fields_do_not_leak(
    projection: generic.NormalizedDecisionSource,
) -> None:
    assert tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__) == (
        GENERIC_FIELDS
    )
    subject._prove_generic_fact_schema_v1()
    for fact in projection.facts:
        assert tuple(fact.__dataclass_fields__) == GENERIC_FIELDS
        assert all(not hasattr(fact, field) for field in FORBIDDEN_RICH_FIELDS)
        serialized = repr(asdict(fact))
        assert all(token not in serialized for token in RICH_ONLY_TOKENS)


def test_future_training_field_schema_leak_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    @dataclass(frozen=True)
    class LeakedFact:
        canonical_event_id: str
        review_unit_id: str
        human_review_completed: bool
        legacy_completed_review_status: str
        task_relevance_disposition: str
        chemistry_disposition: str
        training_disposition: str
        human_training_excluded: bool
        source_decision_schema: str
        source_decision_sha256: str
        source_binding_path: str
        future_training_admission_candidate: bool

    monkeypatch.setattr(generic, "NormalizedCompletedDecisionFact", LeakedFact)
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithSR2Error,
        match="GENERIC_NORMALIZED_FACT_SCHEMA_NOT_EXACT11",
    ):
        subject._prove_generic_fact_schema_v1()


def test_sr2_generic_projection_provenance_and_dispositions_are_exact(
    projection: generic.NormalizedDecisionSource,
) -> None:
    binding = projection.binding
    assert binding.source_path == FORMAL_PATH
    assert binding.path_namespace == "repository_parent_relative"
    assert binding.byte_count == 34106
    assert binding.sha256 == (
        "b41c84d6519efce267410d5e95b017366c9b5b8820a6f5878c9a893404b6defa"
    )
    assert binding.schema_version == "covapie_sr2_exact4_formal_human_decision_v1"
    assert "snapshot" not in binding.source_path
    assert "matrix" not in binding.source_path
    assert "manifest" not in binding.source_path
    assert len(projection.facts) == 4
    for fact in projection.facts:
        assert fact.legacy_completed_review_status == generic.COMPLETED_HUMAN_POSITIVE
        assert fact.task_relevance_disposition == generic.TASK_RELEVANT
        assert fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        assert fact.training_disposition == generic.TRAINING_INCLUDE
        assert fact.human_training_excluded is False
        assert fact.source_decision_schema == binding.schema_version
        assert fact.source_decision_sha256 == binding.sha256
        assert fact.source_binding_path == binding.source_path
        generic._validate_fact(fact, binding)


def test_generic_positive_include_regression_has_no_admission_field(
    projection: generic.NormalizedDecisionSource,
) -> None:
    fact = projection.facts[0]
    generic._validate_fact(fact, projection.binding)
    assert fact.task_relevance_disposition == generic.TASK_RELEVANT
    assert fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
    assert fact.legacy_completed_review_status == generic.COMPLETED_HUMAN_POSITIVE
    assert fact.training_disposition == generic.TRAINING_INCLUDE
    assert fact.human_training_excluded is False
    assert not hasattr(fact, "training_admission")
    assert not hasattr(fact, "formal_training_admitted")


@pytest.mark.parametrize(
    "updates",
    (
        {"training_disposition": generic.TRAINING_EXCLUDE},
        {"human_training_excluded": True},
        {"legacy_completed_review_status": generic.COMPLETED_HUMAN_NEGATIVE},
        {"task_relevance_disposition": generic.TASK_NOT_RELEVANT},
        {"chemistry_disposition": generic.CHEMISTRY_NEGATIVE},
    ),
)
def test_projection_disposition_mutations_fail_closed(
    projection: generic.NormalizedDecisionSource, updates: dict[str, object]
) -> None:
    mutated = _replace_source_fact(projection, **updates)
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithSR2Error,
        match="SR2_SOURCE_PROJECTION_INVALID",
    ):
        subject._validate_projected_sr2_source_v1(mutated)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("sha256", "0" * 64),
        ("schema_version", "wrong_schema"),
        ("review_unit_id", "COVAPIE_BULK_REVIEW_UNIT_WRONG"),
    ),
)
def test_wrong_source_binding_identity_fails_closed(
    projection: generic.NormalizedDecisionSource, field: str, value: str
) -> None:
    binding = replace(projection.binding, **{field: value})
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithSR2Error,
        match="SR2_SOURCE_PROJECTION_IDENTITY_INVALID",
    ):
        subject._validate_projected_sr2_source_v1(
            replace(projection, binding=binding)
        )


def test_ingestion_artifacts_cannot_replace_formal_generic_authority(
    projection: generic.NormalizedDecisionSource,
) -> None:
    artifact_paths = (
        "data/derived/covalent_small/"
        "covapie_sr2_completed_decision_ingestion_and_task_label_availability_v1/"
        + name
        for name in (
            "covapie_sr2_completed_human_decision_snapshot_v1.json",
            "covapie_sr2_event_task_label_availability_v1.csv",
            "covapie_sr2_completed_decision_ingestion_manifest_v1.json",
        )
    )
    for artifact in artifact_paths:
        binding = replace(projection.binding, source_path=artifact)
        facts = tuple(
            replace(fact, source_binding_path=artifact) for fact in projection.facts
        )
        with pytest.raises(
            subject.CompletedDecisionReconciliationWithSR2Error,
            match="SR2_SOURCE_PROJECTION_IDENTITY_INVALID",
        ):
            subject._validate_projected_sr2_source_v1(
                replace(projection, binding=binding, facts=facts)
            )


def test_source_chain_18_115_to_19_119_is_append_only(
    source_chains: tuple[
        tuple[generic.NormalizedDecisionSource, ...],
        tuple[generic.NormalizedDecisionSource, ...],
    ],
) -> None:
    before, after = source_chains
    assert tuple(len(source.facts) for source in before) == (
        8,
        16,
        8,
        9,
        8,
        8,
        8,
        7,
        6,
        5,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
    )
    assert len(before) == 18
    assert sum(len(source.facts) for source in before) == 115
    assert len(after) == 19
    assert sum(len(source.facts) for source in after) == 119
    assert after[:-1] == before
    assert len({source.binding.review_unit_id for source in before}) == 18
    assert len({source.binding.review_unit_id for source in after}) == 19
    assert len({source.binding.stable_identity for source in before}) == 18
    assert len({source.binding.stable_identity for source in after}) == 19
    all_ids = [fact.canonical_event_id for source in after for fact in source.facts]
    assert len(all_ids) == len(set(all_ids)) == 119


def test_predecessor_source_count_drift_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    source_chains: tuple[
        tuple[generic.NormalizedDecisionSource, ...],
        tuple[generic.NormalizedDecisionSource, ...],
    ],
) -> None:
    before, _after = source_chains
    monkeypatch.setattr(
        gd1_predecessor,
        "load_real_completed_decision_sources_with_gd1_v1",
        lambda _root: before[:-1],
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithSR2Error,
        match="PREDECESSOR_WITH_GD1_SOURCE_COMPOSITION_INVALID",
    ):
        subject.load_real_completed_decision_sources_with_sr2_v1(ROOT)


def test_cross_source_event_collision_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    projection: generic.NormalizedDecisionSource,
    source_chains: tuple[
        tuple[generic.NormalizedDecisionSource, ...],
        tuple[generic.NormalizedDecisionSource, ...],
    ],
) -> None:
    before, _after = source_chains
    colliding_id = before[0].facts[0].canonical_event_id
    colliding = _replace_source_fact(projection, canonical_event_id=colliding_id)
    monkeypatch.setattr(subject, "project_sr2_completed_decision_v1", lambda **_kw: colliding)
    monkeypatch.setattr(subject, "_validate_projected_sr2_source_v1", lambda _source: None)
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithSR2Error,
        match="SR2_EVENT_COLLISION_WITH_PREDECESSOR",
    ):
        subject.load_real_completed_decision_sources_with_sr2_v1(ROOT)


def test_sr2_predecessor_historical_state_is_exact(
    reconciliations: tuple[generic.ReconciliationResult, generic.ReconciliationResult],
) -> None:
    before, _after = reconciliations
    subject._prove_sr2_predecessor_historical_state_v1(before.reconciled_rows)
    target = [
        row
        for row in before.reconciled_rows
        if row["raw_review_unit_id"] == sr2_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
    ]
    assert len(target) == 4
    assert {row["canonical_event_id"] for row in target} == set(
        sr2_ingestion_owner.EXPECTED_EVENT_IDS
    )
    assert {row["raw_priority_rank"] for row in target} == {"22"}
    assert {row["raw_unit_event_count"] for row in target} == {"4"}
    assert {row["current_review_status"] for row in target} == {
        generic.CURRENTLY_UNREVIEWED
    }


def test_historical_prior_drift_and_fifth_unit_event_fail_closed(
    reconciliations: tuple[generic.ReconciliationResult, generic.ReconciliationResult],
) -> None:
    before, _after = reconciliations
    rows = [dict(row) for row in before.reconciled_rows]
    target = next(
        row
        for row in rows
        if row["canonical_event_id"] == sr2_ingestion_owner.EXPECTED_EVENT_IDS[0]
    )
    target["raw_priority_rank"] = "23"
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithSR2Error,
        match="SR2_PREDECESSOR_HISTORICAL_STATE_DRIFT",
    ):
        subject._prove_sr2_predecessor_historical_state_v1(rows)

    rows = [dict(row) for row in before.reconciled_rows]
    rows[100]["raw_review_unit_id"] = sr2_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithSR2Error,
        match="SR2_PREDECESSOR_HISTORICAL_STATE_DRIFT",
    ):
        subject._prove_sr2_predecessor_historical_state_v1(rows)


def test_reconciliation_summary_and_exact_row_delta(
    reconciliations: tuple[generic.ReconciliationResult, generic.ReconciliationResult],
) -> None:
    before, after = reconciliations
    assert before.review_summary == BEFORE_SUMMARY
    assert after.review_summary == AFTER_SUMMARY
    subject._validate_reconciliation_delta_v1(before, after)
    assert len(after.source_bindings) == 19
    assert len(after.normalized_facts) == 119


def test_only_sr2_exact4_rows_change_only_allowed_exact4_fields(
    reconciliations: tuple[generic.ReconciliationResult, generic.ReconciliationResult],
) -> None:
    before, after = reconciliations
    target_ids = set(sr2_ingestion_owner.EXPECTED_EVENT_IDS)
    expected_authority = generic._canonical_json([FORMAL_PATH])
    changed = 0
    unchanged = 0
    for left, right in zip(
        before.reconciled_rows, after.reconciled_rows, strict=True
    ):
        assert tuple(left) == tuple(right) == generic.HISTORICAL_RECONCILIATION_HEADER
        assert left["canonical_event_id"] == right["canonical_event_id"]
        fields = {key for key in left if left[key] != right[key]}
        if left["canonical_event_id"] not in target_ids:
            assert fields == set()
            assert left == right
            unchanged += 1
            continue
        assert fields == ALLOWED_CHANGED_FIELDS
        assert left["current_review_status"] == generic.CURRENTLY_UNREVIEWED
        assert right["current_review_status"] == generic.COMPLETED_HUMAN_POSITIVE
        assert right["current_status_authority_sources_json"] == expected_authority
        assert right["calibration_eligible"] == "false"
        assert right["calibration_exclusion_reason"] == (
            generic.COMPLETED_HUMAN_POSITIVE
        )
        changed += 1
    assert changed == 4
    assert unchanged == 334


def test_calibration_ineligible_does_not_mean_training_excluded(
    reconciliations: tuple[generic.ReconciliationResult, generic.ReconciliationResult],
) -> None:
    _before, after = reconciliations
    target_ids = set(sr2_ingestion_owner.EXPECTED_EVENT_IDS)
    facts = [
        fact
        for fact in after.normalized_facts
        if fact.canonical_event_id in target_ids
    ]
    rows = [
        row
        for row in after.reconciled_rows
        if row["canonical_event_id"] in target_ids
    ]
    assert len(facts) == len(rows) == 4
    assert all(fact.training_disposition == generic.TRAINING_INCLUDE for fact in facts)
    assert all(fact.human_training_excluded is False for fact in facts)
    assert all(
        fact.legacy_completed_review_status == generic.COMPLETED_HUMAN_POSITIVE
        for fact in facts
    )
    assert {row["current_review_status"] for row in rows} == {
        generic.COMPLETED_HUMAN_POSITIVE
    }
    assert {row["calibration_eligible"] for row in rows} == {"false"}


def test_fifth_reconciliation_row_field_change_fails_closed(
    reconciliations: tuple[generic.ReconciliationResult, generic.ReconciliationResult],
) -> None:
    before, after = reconciliations
    rows = [dict(row) for row in after.reconciled_rows]
    target = next(
        row
        for row in rows
        if row["canonical_event_id"] == sr2_ingestion_owner.EXPECTED_EVENT_IDS[0]
    )
    target["training_disposition"] = generic.TRAINING_INCLUDE
    mutated = replace(after, reconciled_rows=tuple(rows))
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithSR2Error,
        match="SR2_RECONCILIATION_ROW_ORDER_OR_SCHEMA_CHANGED",
    ):
        subject._validate_reconciliation_delta_v1(before, mutated)


def test_non_sr2_mutation_fails_closed(
    reconciliations: tuple[generic.ReconciliationResult, generic.ReconciliationResult],
) -> None:
    before, after = reconciliations
    rows = [dict(row) for row in after.reconciled_rows]
    target_ids = set(sr2_ingestion_owner.EXPECTED_EVENT_IDS)
    non_target = next(
        row for row in rows if row["canonical_event_id"] not in target_ids
    )
    non_target["raw_priority_rank"] = str(int(non_target["raw_priority_rank"]) + 1)
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithSR2Error,
        match="SR2_NON_TARGET_ROW_CHANGED",
    ):
        subject._validate_reconciliation_delta_v1(
            before, replace(after, reconciled_rows=tuple(rows))
        )


def test_generic_reconciliation_is_deterministic(
    source_chains: tuple[
        tuple[generic.NormalizedDecisionSource, ...],
        tuple[generic.NormalizedDecisionSource, ...],
    ],
) -> None:
    _before, sources = source_chains
    historical = generic.load_real_historical_reconciliation_v1(ROOT)
    adapted = (
        gd1_predecessor.four_m5_predecessor.onl_successor
        ._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    first = generic.reconcile_completed_human_decisions_v1(adapted, sources)
    second = generic.reconcile_completed_human_decisions_v1(adapted, sources)
    assert first == second


def test_production_exposes_no_writer_or_materializer() -> None:
    assert not hasattr(subject, "materialize")
    assert not hasattr(subject, "materialize_artifacts_v1")
    assert not hasattr(subject, "write")
    tree = ast.parse((ROOT / SUBJECT_RELATIVE).read_text(encoding="utf-8"))
    calls = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    assert not calls & {
        "open",
        "write",
        "write_bytes",
        "write_text",
        "mkdir",
        "materialize_artifacts_v1",
    }
    assert not (
        ROOT
        / "data/derived/covalent_small/"
        "covapie_completed_human_decision_reconciliation_with_sr2_v1"
    ).exists()


def test_candidate_and_future_tracked_lifecycle_profiles(checker) -> None:
    expected = set(checker.EXACT4_PATHS)
    assert checker.classify_repository_profile(
        expected_paths=checker.EXACT4_PATHS,
        tracked_paths=set(),
        ordinary_untracked=expected,
        status_lines=tuple("?? " + path for path in checker.EXACT4_PATHS),
        working_diff=set(),
        cached_diff=set(),
    ) == checker.CANDIDATE_UNTRACKED
    assert checker.classify_repository_profile(
        expected_paths=checker.EXACT4_PATHS,
        tracked_paths=expected,
        ordinary_untracked=set(),
        status_lines=(),
        working_diff=set(),
        cached_diff=set(),
    ) == checker.TRACKED_CLEAN


def test_future_tracked_lifecycle_allows_later_unrelated_commits(checker) -> None:
    checker.validate_repository_relation_values(
        profile=checker.TRACKED_CLEAN,
        expected_paths=set(checker.EXACT4_PATHS),
        head="later-head",
        origin_main="intermediate-origin",
        ahead=3,
        behind=0,
        baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True,
        changed_since_baseline={*checker.EXACT4_PATHS, "docs/later.md"},
    )


def test_checker_architecture_and_candidate_inventory_are_exact4(checker) -> None:
    architecture = checker._verify_architecture(ROOT)
    assert architecture["public_api"] == subject.__all__
    assert architecture["generic_schema_forked"] is False
    assert architecture["generic_reconciler_forked"] is False
    expected = {
        SUBJECT_RELATIVE.as_posix(),
        CHECKER_RELATIVE.as_posix(),
        "tests/test_covapie_completed_human_decision_reconciliation_with_sr2_v1.py",
        "docs/covapie_completed_human_decision_reconciliation_with_sr2_v1_guide.md",
    }
    assert len(expected) == 4
    assert not any(path.startswith("data/derived/") for path in expected)
