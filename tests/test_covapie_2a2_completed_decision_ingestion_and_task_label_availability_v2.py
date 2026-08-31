from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import shutil
import stat

import pytest

from covalent_ext import (
    covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1
    as two_a2_v1,
)
from covalent_ext import (
    covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2
    as subject,
)
from covalent_ext import (
    covapie_f24_completed_decision_ingestion_and_task_label_availability_v2
    as f24_v2,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    REPO_ROOT
    / "scripts/check_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py"
)


@pytest.fixture(scope="module")
def bound() -> dict[str, object]:
    return subject.load_frozen_two_a2_authority_v2(repo_root=REPO_ROOT)


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return subject.verify_published_two_a2_v1_projection_v2(repo_root=REPO_ROOT)


@pytest.fixture(scope="module")
def checker_module() -> object:
    spec = importlib.util.spec_from_file_location("covapie_2a2_v2_checker", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _source_path(record: dict[str, object]) -> Path:
    relative = Path(str(record["path"]))
    if record["path_namespace"] == "repository_relative":
        return REPO_ROOT / relative
    assert record["path_namespace"] == "project_parent_relative"
    return REPO_ROOT.parent / relative


def _embedded_record(bound: dict[str, object], role: str) -> dict[str, object]:
    records = bound["formal_evidence_bindings"]
    assert isinstance(records, list)
    matches = [record for record in records if record["source_role"] == role]
    assert len(matches) == 1
    return matches[0]


def _copy_record(record: dict[str, object], destination: Path) -> Path:
    shutil.copyfile(_source_path(record), destination)
    assert destination.stat().st_size == record["byte_count"]
    assert _sha(destination.read_bytes()) == record["sha256"]
    return destination


def test_exact_public_api_and_keyword_only_signatures() -> None:
    assert subject.__all__ == (
        "TwoA2SourceBindingV2Error",
        "load_frozen_two_a2_authority_v2",
        "verify_published_two_a2_v1_projection_v2",
    )
    assert issubclass(subject.TwoA2SourceBindingV2Error, ValueError)
    expected = {
        "load_frozen_two_a2_authority_v2": (
            "repo_root",
            "formal_decision_path",
            "repository_path_overrides",
        ),
        "verify_published_two_a2_v1_projection_v2": (
            "repo_root",
            "repository_path_overrides",
        ),
    }
    for name, parameter_names in expected.items():
        parameters = tuple(inspect.signature(getattr(subject, name)).parameters.values())
        assert tuple(parameter.name for parameter in parameters) == parameter_names
        assert all(
            parameter.kind is inspect.Parameter.KEYWORD_ONLY
            for parameter in parameters
        )


def test_strict_exact4_candidate_inventory(checker_module: object) -> None:
    assert checker_module.EXACT4_PATHS == (
        "src/covalent_ext/covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py",
        "scripts/check_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py",
        "tests/test_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py",
        "docs/covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    )
    assert not any(path.endswith((".json", ".csv")) for path in checker_module.EXACT4_PATHS)


@pytest.mark.parametrize(
    ("relative", "byte_count", "sha256"),
    [
        (two_a2_v1.SOURCE_RELATIVE, 81311, subject.TWO_A2_V1_OWNER_SHA256),
        (two_a2_v1.CHECKER_RELATIVE, 16795, subject.TWO_A2_V1_CHECKER_SHA256),
        (two_a2_v1.TEST_RELATIVE, 24462, subject.TWO_A2_V1_TEST_SHA256),
    ],
)
def test_two_a2_v1_code_is_frozen(
    relative: Path, byte_count: int, sha256: str
) -> None:
    payload = (REPO_ROOT / relative).read_bytes()
    assert len(payload) == byte_count
    assert _sha(payload) == sha256


@pytest.mark.parametrize(
    ("relative", "byte_count", "sha256"),
    [
        (
            subject.SOURCE_BINDING_POLICY_V2_RELATIVE,
            3704,
            subject.SOURCE_BINDING_POLICY_V2_SHA256,
        ),
        (subject.F24_V2_RELATIVE, 25212, subject.F24_V2_SHA256),
        (
            subject.F24_V2_CHECKER_RELATIVE,
            44863,
            subject.F24_V2_CHECKER_SHA256,
        ),
    ],
)
def test_b1_and_f24_v2_predecessor_identities(
    relative: Path, byte_count: int, sha256: str
) -> None:
    payload = (REPO_ROOT / relative).read_bytes()
    assert len(payload) == byte_count
    assert _sha(payload) == sha256


def test_f24_v2_projection_is_actually_called(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    original = f24_v2.verify_published_f24_v1_projection_v2

    def recording_call(*, repo_root: Path, repository_path_overrides: object = None) -> dict[str, bytes]:
        nonlocal calls
        calls += 1
        return original(
            repo_root=repo_root,
            repository_path_overrides=repository_path_overrides,
        )

    monkeypatch.setattr(
        f24_v2, "verify_published_f24_v1_projection_v2", recording_call
    )
    loaded = subject.load_frozen_two_a2_authority_v2(repo_root=REPO_ROOT)
    assert calls == 1
    assert loaded["published_f24_v2_predecessor"][
        "F24_V2_projection_actually_called"
    ] is True


def test_verify_bound_source_v2_is_actually_called(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    original = subject.verify_bound_source_v2

    def recording_call(**kwargs: object) -> bytes:
        nonlocal calls
        calls += 1
        return original(**kwargs)

    monkeypatch.setattr(subject, "verify_bound_source_v2", recording_call)
    subject.load_frozen_two_a2_authority_v2(repo_root=REPO_ROOT)
    assert calls >= 30


def test_ast_call_graph_retires_all_v1_gates(checker_module: object) -> None:
    result = checker_module._verify_production_ast(REPO_ROOT)
    checker_module._verify_two_a2_v1_pure_call_graph(REPO_ROOT)
    checker_module._verify_f24_v2_call_graph(REPO_ROOT)
    assert result["b1_bound_source_helper_used"] is True
    assert result["f24_v2_successor_called"] is True
    assert result["runtime_bound_before_role_validation"] is True
    for key in (
        "f24_v1_source_gate_active",
        "two_a2_v1_source_gate_active",
        "two_a2_v1_verify_binding_active",
        "two_a2_v1_verify_formal_evidence_bindings_active",
        "two_a2_v1_loader_active",
        "two_a2_v1_subprocess_validator_active",
        "two_a2_v1_materialization_active",
        "two_a2_v1_reconciliation_execution_active",
        "exact_posix_semantic_mode_active",
        "embedded_exact_posix_semantic_mode_active",
    ):
        assert result[key] is False


def test_production_has_no_direct_source_read_or_subprocess() -> None:
    text = Path(subject.__file__).read_text(encoding="utf-8")
    tree = ast.parse(text)
    assert not [
        call
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        and (
            isinstance(call.func, ast.Name)
            and call.func.id in {"open", "subprocess"}
            or isinstance(call.func, ast.Attribute)
            and call.func.attr in {"read_bytes", "read_text", "open", "run"}
        )
    ]


def test_exact13_source_binding_summary(bound: dict[str, object]) -> None:
    summary = bound["source_binding_v2"]
    assert summary == {
        "combined_helper": "verify_bound_source_v2",
        "direct_mode_bound_source_count": 2,
        "formal_embedded_evidence_count": 11,
        "formal_embedded_evidence_exact_count": 11,
        "total_historical_mode_bearing_records": 13,
        "historical_mode_counts": {"0664": 10, "0644": 2, "0600": 1},
        "expected_executable_classes": [False] * 13,
        "all_expected_executable": False,
        "formal_validator_expected_nonexecutable": True,
        "preparation_validator_expected_nonexecutable": True,
        "preview_validator_expected_nonexecutable": True,
        "embedded_1F8_0600_precedent_expected_nonexecutable": True,
        "exact_posix_numeric_mode_semantic_acceptance": False,
        "embedded_exact_posix_numeric_mode_semantic_acceptance": False,
    }


@pytest.mark.parametrize(
    ("role", "mode"),
    [
        ("2A2_FROZEN_REVISED1_FORMAL_HUMAN_DECISION", "0664"),
        ("2A2_FROZEN_REVISED1_FORMAL_VALIDATOR", "0664"),
        ("machine_evidence_manifest", "0664"),
        ("exact4_event_review", "0664"),
        ("graph_and_role_candidates", "0664"),
        ("human_review_guide", "0664"),
        ("unsigned_human_decision_template", "0664"),
        ("preparation_package_validator", "0664"),
        ("non_authoritative_human_review_scientific_preview", "0664"),
        ("human_review_scientific_preview_validator", "0664"),
        ("published_role_profile_runtime_owner", "0644"),
        ("canonical_role_and_task_semantics_owner", "0644"),
        ("published_1f8_event_task_label_availability", "0600"),
    ],
)
def test_historical_exact13_modes_are_preserved_as_provenance(
    bound: dict[str, object], role: str, mode: str
) -> None:
    records = [
        bound["formal_decision_binding"],
        bound["formal_validator_binding"],
        *bound["formal_evidence_bindings"],
    ]
    record = next(record for record in records if record["source_role"] == role)
    assert record["mode"] == mode
    assert subject._expected_executable_from_legacy_mode(mode, role) is False


@pytest.mark.parametrize("binding_index", [0, 1])
@pytest.mark.parametrize("live_mode", [0o600, 0o644, 0o660, 0o664])
def test_direct_exact2_safe_nonexecutable_modes_pass(
    tmp_path: Path, binding_index: int, live_mode: int
) -> None:
    relative, namespace, byte_count, sha256, role, historical_mode = (
        two_a2_v1.FORMAL_BINDINGS[binding_index]
    )
    source = REPO_ROOT.parent / relative if namespace == "project_parent_relative" else REPO_ROOT / relative
    replacement = tmp_path / (str(binding_index) + relative.suffix)
    shutil.copyfile(source, replacement)
    replacement.chmod(live_mode)
    payload = subject._verify_source(
        path=replacement,
        byte_count=byte_count,
        sha256=sha256,
        label=role,
        expected_executable=subject._expected_executable_from_legacy_mode(
            historical_mode, role
        ),
    )
    assert len(payload) == byte_count


@pytest.mark.parametrize("binding_index", [0, 1])
@pytest.mark.parametrize(
    ("live_mode", "token"),
    [
        (0o755, "SOURCE_EXECUTABLE_CLASS_MISMATCH"),
        (0o666, "SOURCE_WORLD_WRITABLE"),
        (0o777, "SOURCE_WORLD_WRITABLE"),
    ],
)
def test_direct_exact2_unsafe_modes_fail_closed(
    tmp_path: Path, binding_index: int, live_mode: int, token: str
) -> None:
    relative, namespace, byte_count, sha256, role, _mode = (
        two_a2_v1.FORMAL_BINDINGS[binding_index]
    )
    source = REPO_ROOT.parent / relative if namespace == "project_parent_relative" else REPO_ROOT / relative
    replacement = tmp_path / (str(binding_index) + relative.suffix)
    shutil.copyfile(source, replacement)
    replacement.chmod(live_mode)
    with pytest.raises(subject.TwoA2SourceBindingV2Error, match=token):
        subject._verify_source(
            path=replacement,
            byte_count=byte_count,
            sha256=sha256,
            label=role,
            expected_executable=False,
        )


def test_direct_formal_and_validator_public_safe_drift_pass(tmp_path: Path) -> None:
    decision = two_a2_v1.FORMAL_BINDINGS[0]
    validator = two_a2_v1.FORMAL_BINDINGS[1]
    decision_copy = tmp_path / "formal.json"
    validator_copy = tmp_path / "validator.py"
    shutil.copyfile(REPO_ROOT.parent / decision[0], decision_copy)
    shutil.copyfile(REPO_ROOT.parent / validator[0], validator_copy)
    decision_copy.chmod(0o600)
    validator_copy.chmod(0o644)
    loaded = subject.load_frozen_two_a2_authority_v2(
        repo_root=REPO_ROOT,
        formal_decision_path=decision_copy,
        repository_path_overrides={validator[0]: validator_copy},
    )
    assert loaded["formal_validator_result"]["status"] == "PASS"


@pytest.mark.parametrize("live_mode", [0o600, 0o644, 0o660, 0o664])
def test_embedded_1f8_safe_nonexecutable_modes_pass_b1(
    bound: dict[str, object], tmp_path: Path, live_mode: int
) -> None:
    record = _embedded_record(bound, "published_1f8_event_task_label_availability")
    replacement = _copy_record(record, tmp_path / "1f8.csv")
    replacement.chmod(live_mode)
    payload = subject._verify_source(
        path=replacement,
        byte_count=record["byte_count"],
        sha256=record["sha256"],
        label=record["source_role"],
        expected_executable=False,
    )
    assert len(payload) == record["byte_count"]


@pytest.mark.parametrize(
    ("live_mode", "token"),
    [
        (0o755, "SOURCE_EXECUTABLE_CLASS_MISMATCH"),
        (0o666, "SOURCE_WORLD_WRITABLE"),
        (0o777, "SOURCE_WORLD_WRITABLE"),
    ],
)
def test_embedded_1f8_unsafe_modes_fail_closed(
    bound: dict[str, object], tmp_path: Path, live_mode: int, token: str
) -> None:
    record = _embedded_record(bound, "published_1f8_event_task_label_availability")
    replacement = _copy_record(record, tmp_path / "1f8.csv")
    replacement.chmod(live_mode)
    with pytest.raises(subject.TwoA2SourceBindingV2Error, match=token):
        subject._verify_source(
            path=replacement,
            byte_count=record["byte_count"],
            sha256=record["sha256"],
            label=record["source_role"],
            expected_executable=False,
        )


def test_original_embedded_1f8_0600_to_0664_v2_passes(
    bound: dict[str, object], tmp_path: Path
) -> None:
    record = _embedded_record(bound, "published_1f8_event_task_label_availability")
    assert record["mode"] == "0600"
    replacement = _copy_record(record, tmp_path / "1f8.csv")
    replacement.chmod(0o664)
    loaded = subject.load_frozen_two_a2_authority_v2(
        repo_root=REPO_ROOT,
        repository_path_overrides={Path(record["path"]): replacement},
    )
    assert loaded["source_binding_v2"][
        "embedded_1F8_0600_precedent_expected_nonexecutable"
    ] is True


def test_original_embedded_1f8_case_false_fails_v1_and_passes_v2(
    checker_module: object, bound: dict[str, object]
) -> None:
    assert checker_module._verify_v1_embedded_false_failure_contract(
        REPO_ROOT, bound
    ) is True


@pytest.mark.parametrize(
    "role",
    [
        "published_role_profile_runtime_owner",
        "canonical_role_and_task_semantics_owner",
    ],
)
def test_embedded_0644_to_0664_public_passes(
    bound: dict[str, object], tmp_path: Path, role: str
) -> None:
    record = _embedded_record(bound, role)
    assert record["mode"] == "0644"
    replacement = _copy_record(record, tmp_path / (role + Path(record["path"]).suffix))
    replacement.chmod(0o664)
    loaded = subject.load_frozen_two_a2_authority_v2(
        repo_root=REPO_ROOT,
        repository_path_overrides={Path(record["path"]): replacement},
    )
    assert loaded["runtime_bound_before_role_validation"] is True


@pytest.mark.parametrize(
    "role",
    [
        "preparation_package_validator",
        "human_review_scientific_preview_validator",
    ],
)
def test_embedded_python_validators_remain_nonexecutable(
    bound: dict[str, object], tmp_path: Path, role: str
) -> None:
    record = _embedded_record(bound, role)
    replacement = _copy_record(record, tmp_path / (role + ".py"))
    replacement.chmod(0o755)
    with pytest.raises(
        subject.TwoA2SourceBindingV2Error,
        match="SOURCE_EXECUTABLE_CLASS_MISMATCH",
    ):
        subject.load_frozen_two_a2_authority_v2(
            repo_root=REPO_ROOT,
            repository_path_overrides={Path(record["path"]): replacement},
        )


def test_embedded_world_write_fails_closed(
    bound: dict[str, object], tmp_path: Path
) -> None:
    record = _embedded_record(bound, "preparation_package_validator")
    replacement = _copy_record(record, tmp_path / "validator.py")
    replacement.chmod(0o666)
    with pytest.raises(subject.TwoA2SourceBindingV2Error, match="SOURCE_WORLD_WRITABLE"):
        subject.load_frozen_two_a2_authority_v2(
            repo_root=REPO_ROOT,
            repository_path_overrides={Path(record["path"]): replacement},
        )


@pytest.mark.parametrize(
    ("failure", "token"),
    [
        ("byte_count", "SOURCE_BYTE_COUNT_MISMATCH"),
        ("sha256", "SOURCE_SHA256_MISMATCH"),
        ("symlink", "SOURCE_SYMLINK_FORBIDDEN"),
    ],
)
def test_embedded_content_and_object_failures(
    bound: dict[str, object], tmp_path: Path, failure: str, token: str
) -> None:
    record = _embedded_record(bound, "graph_and_role_candidates")
    original = _copy_record(record, tmp_path / "original.json")
    replacement = tmp_path / "replacement.json"
    if failure == "symlink":
        replacement.symlink_to(original.name)
    else:
        shutil.copyfile(original, replacement)
        payload = bytearray(replacement.read_bytes())
        if failure == "byte_count":
            payload.extend(b"\n")
        else:
            payload[0] ^= 1
        replacement.write_bytes(payload)
    with pytest.raises(subject.TwoA2SourceBindingV2Error, match=token):
        subject.load_frozen_two_a2_authority_v2(
            repo_root=REPO_ROOT,
            repository_path_overrides={Path(record["path"]): replacement},
        )


def test_unexpected_override_fails_closed(tmp_path: Path) -> None:
    target = tmp_path / "unexpected.txt"
    target.write_text("unexpected\n", encoding="utf-8")
    with pytest.raises(
        subject.TwoA2SourceBindingV2Error,
        match="REPOSITORY_PATH_OVERRIDE_UNEXPECTED",
    ):
        subject.load_frozen_two_a2_authority_v2(
            repo_root=REPO_ROOT,
            repository_path_overrides={Path("unexpected.txt"): target},
        )


@pytest.mark.parametrize(
    ("rank", "event_id_suffix", "protein_asym", "ligand_asym", "connection"),
    [
        (507, "A:CYS:148-:SG:E:2A2:SD", "A", "E", "covale1"),
        (508, "B:CYS:148-:SG:G:2A2:SD", "B", "G", "covale3"),
        (509, "C:CYS:148-:SG:I:2A2:SD", "C", "I", "covale6"),
        (510, "D:CYS:148-:SG:K:2A2:SD", "D", "K", "covale8"),
    ],
)
def test_exact4_scientific_identity(
    bound: dict[str, object],
    rank: int,
    event_id_suffix: str,
    protein_asym: str,
    ligand_asym: str,
    connection: str,
) -> None:
    events = bound["formal"]["event_level_human_decisions"]
    event = next(event for event in events if event["scaleup_rank"] == rank)
    assert event["canonical_event_id"].endswith(event_id_suffix)
    assert event["pdb_id"] == "3ORZ"
    assert event["protein_asym"] == protein_asym
    assert event["ligand_asym"] == ligand_asym
    assert event["selected_connection_id"] == connection
    assert event["cys_residue_id"] == "CYS:148-"
    assert [event["protein_reactive_atom"], event["ligand_reactive_atom"]] == ["SG", "SD"]


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("D1_task_relevance", "RELEVANT"),
        ("D2_chemistry", "POSITIVE"),
        ("D3_reactive_pair", "CONFIRM_OBSERVED_PAIR"),
        ("D4_role_partition", "SELECT_CANDIDATE_4"),
        ("D5_training_use", "EXCLUDE_FROM_TRAINING_ONLY"),
    ],
)
def test_d1_d5_exact_human_decisions(
    bound: dict[str, object], field: str, expected: str
) -> None:
    assert bound["formal"]["human_approval"][field] == expected


def test_d6_is_exact_frozen_human_approved_context(bound: dict[str, object]) -> None:
    formal = bound["formal"]
    context = formal["human_approval"]["D6_scientific_context"]
    assert context == formal["human_approved_context"]["D6_scientific_context"]
    assert formal["human_approved_context"]["exact_text_frozen"] is True
    assert _sha(context.encode("utf-8")) == (
        "2482f7778471c7160d73069e8cd55262c5e964e94ee0de4e45d5539bf1c08681"
    )


def test_candidate4_strict_role_partition(bound: dict[str, object]) -> None:
    role = bound["formal"]["selected_role_partition"]
    assert role["selected_candidate_index_0based"] == 4
    assert role["human_selected"] is True
    assert role["machine_selected"] is False
    assert role["machine_recommended"] is False
    assert role["role_profile"] == "STRICT_LINKER_PRESENT_V1"
    assert role["warhead_role_atom_ids"] == ["SD"]
    assert role["linker_atom_ids"] == ["C1", "C15", "C16", "C17", "O18"]
    assert role["scaffold_atom_ids"] == list(two_a2_v1.SCAFFOLD_ROLE)
    assert role["boundary_bonds"] == list(two_a2_v1.BOUNDARY_BONDS)
    assert role["role_counts"] == {"warhead": 1, "linker": 5, "scaffold": 13}


@pytest.mark.parametrize(
    ("task_id", "semantic_name", "alias"),
    [
        (0, "warhead_only", "A"),
        (1, "linker_plus_warhead", "B"),
        (2, "scaffold_plus_warhead", "B2"),
        (3, "scaffold_only", "B3"),
        (4, "scaffold_plus_linker_plus_warhead", "C"),
    ],
)
def test_canonical_exact5_all_apply(
    bound: dict[str, object], task_id: int, semantic_name: str, alias: str
) -> None:
    canonical = bound["formal"]["canonical_Exact5_and_sample_applicability"]
    task = next(task for task in canonical["tasks"] if task["task_id"] == task_id)
    assert task == {
        "display_alias": alias,
        "semantic_name": semantic_name,
        "structurally_applicable_to_2A2": True,
        "task_id": task_id,
    }
    assert canonical["sample_applicable_task_ids"] == [0, 1, 2, 3, 4]
    assert canonical["global_canonical_task_count"] == 5
    assert canonical["B3_present"] is True
    assert canonical["sixth_task_present"] is False


@pytest.mark.parametrize(
    ("section", "field", "expected"),
    [
        ("chemical_warhead_boundary", "chemical_warhead_atom_ids", None),
        ("chemical_warhead_boundary", "chemical_warhead_human_authoritative", False),
        ("chemical_warhead_boundary", "chemical_warhead_status", "PRE_DISULFIDE_REAGENT_NOT_FULLY_REPRESENTED"),
        ("chemical_warhead_boundary", "W_SD_is_sample_level_canonical_role_region", True),
        ("chemical_warhead_boundary", "W_SD_is_complete_PRE_chemical_warhead_definition", False),
        ("experimental_context_and_PRE_boundary", "engineered_target_site", "PDK1_T148C"),
        ("experimental_context_and_PRE_boundary", "native_cysteine_site", False),
        ("experimental_context_and_PRE_boundary", "disulfide_trapping_context", True),
        ("experimental_context_and_PRE_boundary", "observed_retained_fragment_context", True),
        ("experimental_context_and_PRE_boundary", "complete_PRE_disulfide_reagent_authority", False),
        ("experimental_context_and_PRE_boundary", "observed_graph_is_complete_authoritative_PRE_reagent", False),
        ("experimental_context_and_PRE_boundary", "PRE_topology_authority_created", False),
        ("experimental_context_and_PRE_boundary", "PRE_geometry_authority_created", False),
        ("experimental_context_and_PRE_boundary", "PRE_reconstruction_performed", False),
        ("experimental_context_and_PRE_boundary", "POST_to_PRE_copy_performed", False),
        ("experimental_context_and_PRE_boundary", "PRE_zero_fill_performed", False),
        ("POST_evidence_boundary", "POST_source_evidence_available", True),
        ("POST_evidence_boundary", "POST_source_evidence_count", 4),
        ("POST_evidence_boundary", "POST_geometry_training_authority_created", False),
        ("POST_evidence_boundary", "POST_geometry_training_target_created", False),
    ],
)
def test_chemical_pre_and_post_boundaries(
    bound: dict[str, object], section: str, field: str, expected: object
) -> None:
    assert bound["formal"][section][field] == expected


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("human_training_excluded", True),
        ("training_use_allowed", False),
        ("candidate_for_future_training_admission", False),
        ("formal_training_admitted", False),
        ("training_admission_created", False),
        ("training_materialization_allowed_now", False),
        ("formal_split_authority_created", False),
        ("tensor_target_created", False),
        ("current_runtime_model_usable", False),
        ("parameter_update_authorization", False),
    ],
)
def test_training_boundary(
    bound: dict[str, object], field: str, expected: bool
) -> None:
    assert bound["formal"]["training_use_human_decision"][field] is expected


@pytest.mark.parametrize(
    "field",
    [
        "reaction_family_authority_created",
        "warhead_rule_authority_created",
        "warhead_type_authority_created",
        "reusable_chemistry_authority_created",
        "reusable_pair_authority_created",
        "reusable_role_authority_created",
        "generic_all_disulfide_trapping_EXCLUDE_rule_created",
    ],
)
def test_reusable_authorities_remain_false(
    bound: dict[str, object], field: str
) -> None:
    assert bound["formal"]["reusable_authority_boundary"][field] is False


def test_1f8_precedent_does_not_create_generic_rule(bound: dict[str, object]) -> None:
    precedent = bound["formal"]["published_1F8_same_context_precedent"]
    assert precedent["precedent_did_not_substitute_for_2A2_independent_review"] is True
    assert precedent["2A2_independent_human_review_completed"] is True
    assert precedent["generic_disulfide_trapping_exclusion_rule_created"] is False
    assert precedent["reusable_rule_created"] is False


@pytest.mark.parametrize(
    ("section", "expected"),
    [
        (
            "current_published_census_boundary",
            {
                "positive": 108,
                "relevant": 109,
                "training_INCLUDE": 44,
                "training_EXCLUDE": 64,
                "future_candidates": 27,
                "pair_sample_authority": 108,
                "role_sample_authority": 108,
                "A": 108,
                "B": 48,
                "B2": 48,
                "B3": 108,
                "C": 108,
            },
        ),
        (
            "future_census_informational",
            {
                "positive": 112,
                "relevant": 113,
                "training_INCLUDE": 44,
                "training_EXCLUDE": 68,
                "future_candidates": 27,
                "pair_sample_authority": 112,
                "role_sample_authority": 112,
                "A": 112,
                "B": 52,
                "B2": 52,
                "B3": 112,
                "C": 112,
            },
        ),
        (
            "current_2A2_global_census",
            {
                "positive": 112,
                "relevant": 113,
                "training_INCLUDE": 44,
                "training_EXCLUDE": 68,
                "future_candidates": 27,
                "pair_sample_authority": 112,
                "role_sample_authority": 112,
                "A": 112,
                "B": 52,
                "B2": 52,
                "B3": 112,
                "C": 112,
            },
        ),
    ],
)
def test_historical_projected_and_current_census_are_distinct(
    bound: dict[str, object], section: str, expected: dict[str, int]
) -> None:
    observed = bound[section]
    assert all(observed[key] == value for key, value in expected.items())


def test_reconciliation_is_frozen_informational_only(bound: dict[str, object]) -> None:
    reconciliation = bound["reconciliation_informational"]
    assert reconciliation["reconciled_this_step"] is False
    assert reconciliation["materialized_this_step"] is False
    assert reconciliation["future_after_reconciliation"] == {
        "completed_positive_event_count": 95,
        "completed_positive_unit_count": 13,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_total_event_count": 119,
        "completed_total_unit_count": 17,
        "unreviewed_event_count": 219,
        "unreviewed_unit_count": 114,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "normalized_INCLUDE": 27,
        "normalized_EXCLUDE_FROM_TRAINING_ONLY": 68,
    }


@pytest.mark.parametrize(
    ("name", "byte_count", "sha256"),
    [
        (
            two_a2_v1.SNAPSHOT,
            29063,
            "87cfffd1c9e2e82db6d9aeba2dfedc907b459d89c0160c50fb9fbddee7393000",
        ),
        (
            two_a2_v1.MATRIX,
            8950,
            "f6533013dcb2eea5fcee579d906c7ab3009d1db8c9f2d9f906aca5ee0122f52b",
        ),
        (
            two_a2_v1.SUMMARY,
            4623,
            "6c5a92910becab41a4e3af0317fa3438d6a682e1dac4d4ef1d4e48fe34773ea2",
        ),
        (
            two_a2_v1.MANIFEST,
            19083,
            "af20556b9a9197d2c9ddfd3fc19d01ef43a51f935aa1fdc29bac0e4c5f410287",
        ),
    ],
)
def test_published_v1_artifact_bytes_are_unchanged(
    artifacts: dict[str, bytes], name: str, byte_count: int, sha256: str
) -> None:
    assert len(artifacts[name]) == byte_count
    assert _sha(artifacts[name]) == sha256


def test_published_v1_manifest_closure_and_boundaries(
    artifacts: dict[str, bytes]
) -> None:
    snapshot = json.loads(artifacts[two_a2_v1.SNAPSHOT])
    manifest = json.loads(artifacts[two_a2_v1.MANIFEST])
    assert manifest["candidate_source_bindings"] == subject._FROZEN_TWO_A2_V1_CANDIDATE_BINDINGS
    assert manifest["formal_evidence_bindings"] == snapshot["formal_evidence_bindings"]
    assert manifest["canonical_task_contract"]["B3_present"] is True
    assert manifest["canonical_task_contract"]["sixth_task_present"] is False
    assert manifest["chemical_warhead_vs_role_region"]["chemical_warhead_atom_ids"] is None
    assert manifest["human_authority_ingestion_semantics"]["training_admitted"] is False
    assert manifest["manifest_self_sha256_recorded"] is False
    assert manifest["ready_for_training"] is False


def test_runtime_bound_before_strict_role_validation(bound: dict[str, object]) -> None:
    assert bound["runtime_bound_before_role_validation"] is True
    runtime = bound["published_runtime_result"]
    assert runtime == {
        "validator": "validate_role_profile_v1",
        "valid": True,
        "reasons": [],
        "role_profile": "STRICT_LINKER_PRESENT_V1",
        "warhead_count": 1,
        "linker_count": 5,
        "scaffold_count": 13,
        "applicable_task_ids": [0, 1, 2, 3, 4],
    }


def test_formal_validator_report_is_frozen_compatibility_metadata(
    bound: dict[str, object]
) -> None:
    report = bound["formal_validator_result"]
    assert report["status"] == "PASS"
    assert report["exact_file_count"] == 2
    assert [row["mode"] for row in report["files"]] == ["0o664", "0o664"]
    assert report["ingestion_started"] is False
    assert report["ready_for_training"] is False


def test_checker_accepts_exact_two_lifecycle_profiles(checker_module: object) -> None:
    expected = set(checker_module.EXACT4_PATHS)
    candidate = checker_module.classify_lifecycle_from_facts(
        tracked_exact4=set(),
        ordinary_untracked=expected,
        status_entries=tuple(f"?? {path}" for path in sorted(expected)),
        working_diff=set(),
        cached_diff=set(),
    )
    tracked = checker_module.classify_lifecycle_from_facts(
        tracked_exact4=expected,
        ordinary_untracked=set(),
        status_entries=(),
        working_diff=set(),
        cached_diff=set(),
    )
    assert (candidate, tracked) == ("CANDIDATE_UNTRACKED", "TRACKED_CLEAN")


@pytest.mark.parametrize(
    ("tracked", "untracked", "status", "working", "cached"),
    [
        ("partial", "all", "candidate", "none", "none"),
        ("none", "all", "extra", "none", "none"),
        ("all", "none", "none", "dirty", "none"),
        ("all", "none", "none", "none", "staged"),
        ("none", "missing", "candidate", "none", "none"),
        ("all", "none", "extra", "none", "none"),
    ],
)
def test_checker_rejects_partial_staged_dirty_missing_and_extra_lifecycle(
    checker_module: object,
    tracked: str,
    untracked: str,
    status: str,
    working: str,
    cached: str,
) -> None:
    expected = set(checker_module.EXACT4_PATHS)
    tracked_set = {
        "none": set(),
        "partial": {checker_module.EXACT4_PATHS[0]},
        "all": expected,
    }[tracked]
    untracked_set = {
        "none": set(),
        "missing": set(list(expected)[1:]),
        "all": expected,
    }[untracked]
    statuses = {
        "none": (),
        "candidate": tuple(f"?? {path}" for path in sorted(untracked_set)),
        "extra": (*tuple(f"?? {path}" for path in sorted(untracked_set)), "?? extra.txt"),
    }[status]
    with pytest.raises(ValueError, match="GIT_LIFECYCLE_PROFILE_INVALID"):
        checker_module.classify_lifecycle_from_facts(
            tracked_exact4=tracked_set,
            ordinary_untracked=untracked_set,
            status_entries=statuses,
            working_diff={"dirty.txt"} if working == "dirty" else set(),
            cached_diff={"staged.txt"} if cached == "staged" else set(),
        )


def test_ready_for_integration_but_not_training(bound: dict[str, object]) -> None:
    assert bound["historical_F24_prior_census_preserved"] is True
    assert bound["historical_informational_future_projection_preserved"] is True
    assert bound["current_2A2_global_census_unchanged"] is True
    assert bound["reconciled_this_step"] is False
    assert bound["ready_for_training"] is False
