from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import shutil

import pytest

from covalent_ext import (
    covapie_f24_completed_decision_ingestion_and_task_label_availability_v1
    as f24_v1,
)
from covalent_ext import (
    covapie_f24_completed_decision_ingestion_and_task_label_availability_v2
    as subject,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    REPO_ROOT
    / "scripts/"
    "check_covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py"
)


@pytest.fixture(scope="module")
def checker() -> object:
    spec = importlib.util.spec_from_file_location("f24_v2_checker_for_tests", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bound() -> dict[str, object]:
    return subject.load_frozen_f24_authority_v2(repo_root=REPO_ROOT)


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return subject.verify_published_f24_v1_projection_v2(repo_root=REPO_ROOT)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_exact_public_api_and_thin_surface(checker: object) -> None:
    checker._verify_public_api()
    assert subject.__all__ == (
        "F24SourceBindingV2Error",
        "load_frozen_f24_authority_v2",
        "verify_published_f24_v1_projection_v2",
    )
    assert tuple(inspect.signature(subject.load_frozen_f24_authority_v2).parameters) == (
        "repo_root",
        "formal_decision_path",
        "repository_path_overrides",
    )
    assert tuple(
        inspect.signature(subject.verify_published_f24_v1_projection_v2).parameters
    ) == ("repo_root", "repository_path_overrides")
    assert not any(
        token in name
        for name in vars(subject)
        if not name.startswith("_")
        for token in ("materialize", "mutation", "registry", "resolver", "cache")
    )


def test_strict_exact4_candidate_only(checker: object) -> None:
    assert len(checker.EXACT4_PATHS) == len(set(checker.EXACT4_PATHS)) == 4
    records = checker.verify_exact4_file_hygiene(REPO_ROOT)
    assert [record["path"] for record in records] == list(checker.EXACT4_PATHS)
    assert all(record["mode"] in {"0644", "0664"} for record in records)
    assert not any(path.endswith((".json", ".csv")) for path in checker.EXACT4_PATHS)


def test_f24_v1_frozen_owner_checker_tests_and_artifacts() -> None:
    expected = {
        f24_v1.SOURCE_RELATIVE: (77160, subject.F24_V1_OWNER_SHA256),
        f24_v1.CHECKER_RELATIVE: (15600, subject.F24_V1_CHECKER_SHA256),
        f24_v1.TEST_RELATIVE: (23978, subject.F24_V1_TEST_SHA256),
        f24_v1.OUTPUT_ROOT_RELATIVE / f24_v1.SNAPSHOT: (
            22044,
            "d53ff475b0d86b076b5649916cd7118821e8c883daba5727b1efd7f051b8de11",
        ),
        f24_v1.OUTPUT_ROOT_RELATIVE / f24_v1.MATRIX: (
            7641,
            "516c3ea3ac291c5039e1def72a891b54fd42d5aa45388f27b436a655467cd28c",
        ),
        f24_v1.OUTPUT_ROOT_RELATIVE / f24_v1.SUMMARY: (
            3462,
            "be67578dac2c6593bc75b256cd9c344c90f8650662443ff5cd316bb68b18b385",
        ),
        f24_v1.OUTPUT_ROOT_RELATIVE / f24_v1.MANIFEST: (
            16125,
            "02f56545297fb78c2b2cbd205115d9dca680a8446bfb753109428b698bdd5dfd",
        ),
    }
    for relative, (byte_count, digest) in expected.items():
        path = REPO_ROOT / relative
        assert path.stat().st_size == byte_count
        assert sha(path) == digest


def test_b1_and_dual_v2_identities_are_frozen() -> None:
    assert subject.SOURCE_BINDING_POLICY_V2_SHA256 == (
        "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee"
    )
    assert subject.OZJ_V2_SHA256 == (
        "51af9985cf4de28d48cc55eab71b536472220221d160ee6070677512ba22ef21"
    )
    assert subject.OZJ_V2_CHECKER_SHA256 == (
        "dec67ac8e86273d49b3da048a7286b900b1171f93ffe85a07a6c1830383dd825"
    )
    assert subject.YUN_V2_SHA256 == (
        "a10c929ea86258ac39bc787b3108d622b65c97617e62b19a44bf3711fbffbd52"
    )
    assert subject.YUN_V2_CHECKER_SHA256 == (
        "f0de27832eb557d1f1150ecddc00a023c7e1d81642cc1c92ef606b302c2a54b2"
    )


def test_b1_and_both_v2_projections_are_actually_called(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[str] = []
    original_verify = subject.verify_bound_source_v2
    original_ozj = subject.ozj_v2.verify_published_ozj_v1_projection_v2
    original_yun = subject.yun_v2.verify_published_yun_v1_projection_v2

    def recording_verify(**kwargs: object) -> bytes:
        observed.append("B1:" + str(kwargs["label"]))
        return original_verify(**kwargs)

    def recording_ozj(**kwargs: object) -> dict[str, bytes]:
        observed.append("OZJ_V2")
        return original_ozj(**kwargs)

    def recording_yun(**kwargs: object) -> dict[str, bytes]:
        observed.append("YUN_V2")
        return original_yun(**kwargs)

    monkeypatch.setattr(subject, "verify_bound_source_v2", recording_verify)
    monkeypatch.setattr(
        subject.ozj_v2, "verify_published_ozj_v1_projection_v2", recording_ozj
    )
    monkeypatch.setattr(
        subject.yun_v2, "verify_published_yun_v1_projection_v2", recording_yun
    )
    subject.load_frozen_f24_authority_v2(repo_root=REPO_ROOT)
    assert any(item.startswith("B1:") for item in observed)
    assert observed.count("OZJ_V2") == 1
    # OZJ V2 itself exercises YUN V2; F24 also exercises YUN V2 directly.
    assert observed.count("YUN_V2") >= 2


def test_ast_and_transitive_call_graph_contract(checker: object) -> None:
    result = checker._verify_production_ast(REPO_ROOT)
    checker._verify_f24_v1_pure_call_graph(REPO_ROOT)
    assert result["b1_bound_source_helper_used"] is True
    assert result["direct_source_read_bypass_count"] == 0
    assert result["runtime_bound_before_role_validation"] is True
    assert result["f24_v1_source_gate_active"] is False
    assert result["f24_v1_verify_binding_active"] is False
    assert result["f24_v1_verify_bindings_active"] is False
    assert result["f24_v1_loader_active"] is False
    assert result["f24_v1_subprocess_validator_active"] is False
    assert result["f24_v1_materialization_active"] is False
    assert result["ozj_v1_source_gate_active"] is False
    assert result["yun_v1_source_gate_active"] is False
    assert result["exact_posix_semantic_mode_active"] is False


def test_exact8_mode_inventory_and_both_py_nonexecutable(
    bound: dict[str, object],
) -> None:
    source_binding = bound["source_binding_v2"]
    assert source_binding == {
        "combined_helper": "verify_bound_source_v2",
        "legacy_mode_metadata_classification": [
            "LEGACY_PROVENANCE_METADATA_PRESERVED",
            "SECURITY_EXECUTABLE_CLASS_INPUT",
        ],
        "historical_mode_bound_source_count": 8,
        "historical_modes": ["0664"] * 8,
        "expected_executable_classes": [False] * 8,
        "formal_validator_expected_executable": False,
        "review_package_validator_expected_executable": False,
        "exact_posix_numeric_mode_semantic_acceptance": False,
    }
    assert f24_v1.FORMAL_BINDINGS[1][0].suffix == ".py"
    assert f24_v1.PREPARATION_BINDINGS[-1][0].suffix == ".py"
    assert subject._expected_executable_from_legacy_mode("0664") is False


MODE_BINDINGS = (
    (f24_v1.FORMAL_BINDINGS[0], "formal_decision"),
    (f24_v1.FORMAL_BINDINGS[1], "formal_validator_py"),
    (f24_v1.PREPARATION_BINDINGS[-1], "review_validator_py"),
)


@pytest.mark.parametrize(("binding", "label"), MODE_BINDINGS)
@pytest.mark.parametrize("mode", [0o600, 0o644, 0o660, 0o664])
def test_safe_nonexecutable_mode_variants_pass(
    tmp_path: Path,
    binding: tuple[Path, str, int, str, str, str | None],
    label: str,
    mode: int,
) -> None:
    relative = binding[0]
    replacement = tmp_path / (label + relative.suffix)
    shutil.copyfile(REPO_ROOT.parent / relative, replacement)
    replacement.chmod(mode)
    observed = subject.load_frozen_f24_authority_v2(
        repo_root=REPO_ROOT,
        repository_path_overrides={relative: replacement},
    )
    assert observed["formal"]["approved"] is True


@pytest.mark.parametrize(("binding", "label"), MODE_BINDINGS)
@pytest.mark.parametrize(
    ("mode", "token"),
    [
        (0o755, "SOURCE_EXECUTABLE_CLASS_MISMATCH"),
        (0o666, "SOURCE_WORLD_WRITABLE"),
        (0o777, "SOURCE_WORLD_WRITABLE"),
    ],
)
def test_unsafe_mode_variants_fail_closed(
    tmp_path: Path,
    binding: tuple[Path, str, int, str, str, str | None],
    label: str,
    mode: int,
    token: str,
) -> None:
    relative = binding[0]
    replacement = tmp_path / (label + relative.suffix)
    shutil.copyfile(REPO_ROOT.parent / relative, replacement)
    replacement.chmod(mode)
    with pytest.raises(subject.F24SourceBindingV2Error, match=token):
        subject.load_frozen_f24_authority_v2(
            repo_root=REPO_ROOT,
            repository_path_overrides={relative: replacement},
        )


def test_wrong_byte_count_fails_closed(tmp_path: Path) -> None:
    relative = f24_v1.FORMAL_BINDINGS[0][0]
    replacement = tmp_path / "formal.json"
    shutil.copyfile(REPO_ROOT.parent / relative, replacement)
    replacement.write_bytes(replacement.read_bytes() + b"\n")
    with pytest.raises(subject.F24SourceBindingV2Error, match="SOURCE_BYTE_COUNT_MISMATCH"):
        subject.load_frozen_f24_authority_v2(
            repo_root=REPO_ROOT,
            formal_decision_path=replacement,
        )


def test_same_size_wrong_sha_fails_closed(tmp_path: Path) -> None:
    relative = f24_v1.FORMAL_BINDINGS[0][0]
    replacement = tmp_path / "formal.json"
    shutil.copyfile(REPO_ROOT.parent / relative, replacement)
    payload = bytearray(replacement.read_bytes())
    payload[0] ^= 1
    replacement.write_bytes(payload)
    with pytest.raises(subject.F24SourceBindingV2Error, match="SOURCE_SHA256_MISMATCH"):
        subject.load_frozen_f24_authority_v2(
            repo_root=REPO_ROOT,
            formal_decision_path=replacement,
        )


def test_symlink_and_unexpected_override_fail_closed(tmp_path: Path) -> None:
    relative = f24_v1.FORMAL_BINDINGS[0][0]
    target = tmp_path / "target.json"
    shutil.copyfile(REPO_ROOT.parent / relative, target)
    link = tmp_path / "formal-link.json"
    link.symlink_to(target.name)
    with pytest.raises(subject.F24SourceBindingV2Error, match="SOURCE_SYMLINK_FORBIDDEN"):
        subject.load_frozen_f24_authority_v2(
            repo_root=REPO_ROOT,
            formal_decision_path=link,
        )
    with pytest.raises(
        subject.F24SourceBindingV2Error,
        match="REPOSITORY_PATH_OVERRIDE_UNEXPECTED",
    ):
        subject.load_frozen_f24_authority_v2(
            repo_root=REPO_ROOT,
            repository_path_overrides={Path("unexpected.txt"): target},
        )


def test_v1_source_mode_drift_false_failure_and_v2_pass(tmp_path: Path) -> None:
    binding = f24_v1.FORMAL_BINDINGS[0]
    replacement = tmp_path / binding[0].name
    shutil.copyfile(REPO_ROOT.parent / binding[0], replacement)
    replacement.chmod(0o644)
    with pytest.raises(f24_v1.F24IngestionSafetyError, match="SOURCE_MODE_DRIFT"):
        f24_v1._verify_binding(REPO_ROOT, binding, {binding[0]: replacement})
    observed = subject.load_frozen_f24_authority_v2(
        repo_root=REPO_ROOT,
        formal_decision_path=replacement,
    )
    assert observed["formal"]["approved"] is True


def test_dual_predecessor_record_exact(bound: dict[str, object]) -> None:
    assert bound["dual_published_v2_predecessors"] == {
        "published_OZJ_V2_successor_bound": True,
        "OZJ_V2_sha256": subject.OZJ_V2_SHA256,
        "OZJ_V2_published_commit": subject.OZJ_V2_PUBLISHED_COMMIT,
        "OZJ_V2_projection_actually_called": True,
        "OZJ_V1_ingestion_projection_preserved": True,
        "published_YUN_V2_successor_bound": True,
        "YUN_V2_sha256": subject.YUN_V2_SHA256,
        "YUN_V2_published_commit": subject.YUN_V2_PUBLISHED_COMMIT,
        "YUN_V2_projection_actually_called": True,
        "YUN_V1_DIRECT_INCLUDE_projection_preserved": True,
    }


def test_exact4_science_d1_d6_and_no_machine_selection(
    bound: dict[str, object],
) -> None:
    formal = bound["formal"]
    events = formal["event_level_human_decisions"]
    approval = formal["human_approval"]
    assert len(events) == 4
    assert [event["canonical_event_id"] for event in events] == list(
        f24_v1.EXPECTED_EVENT_IDS
    )
    assert [event["scaleup_rank"] for event in events] == [593, 594, 595, 596]
    assert {event["pdb_id"] for event in events} == {"3V4X"}
    assert {event["protein_residue"] for event in events} == {"CYS:111-"}
    assert {event["protein_reactive_atom"] for event in events} == {"SG"}
    assert {event["ligand_reactive_atom"] for event in events} == {"C8"}
    assert [approval[f"D{index}_{name}"] for index, name in (
        (1, "task_relevance"),
        (2, "chemistry"),
        (3, "reactive_pair"),
        (4, "role_partition"),
        (5, "training_use"),
    )] == [
        "RELEVANT",
        "POSITIVE",
        "CONFIRM_OBSERVED_PAIR",
        "REVISE_ROLE_PARTITION",
        "INCLUDE",
    ]
    assert approval["D6_scientific_context"] == f24_v1.EXPECTED_D6
    assert approval["human_selected_role_candidate_index_0based"] is None
    assert approval["machine_auto_selection_performed"] is False
    assert approval["machine_recommended_candidate"] is None


def test_chemical_warhead_and_role_region_hard_boundary(
    bound: dict[str, object],
) -> None:
    formal = bound["formal"]
    chemical = formal["chemical_warhead_annotation"]
    role = formal["selected_role_partition"]
    distinction = formal["chemical_warhead_vs_role_region_distinction"]
    assert chemical["chemical_warhead_atom_ids"] == ["C1", "C2", "C8", "O2", "O6"]
    assert role["warhead_role_atom_ids"] == ["C1", "C2", "C4", "C8", "O2", "O5", "O6"]
    assert set(chemical["chemical_warhead_atom_ids"]) != set(
        role["warhead_role_atom_ids"]
    )
    assert chemical["human_authoritative"] is True
    assert distinction["sets_are_intentionally_distinct"] is True
    proximal = distinction["proximal_hydroxymethyl_substituent"]
    assert proximal["atom_ids"] == ["C4", "O5"]
    assert proximal["chemical_beta_lactone_core_member"] is False
    assert proximal["absorbed_into_warhead_role_region"] is True


def test_direct_role_partition_boundary_and_minimal_seed(
    bound: dict[str, object],
) -> None:
    role = bound["formal"]["selected_role_partition"]
    assert role["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    assert role["linker_atom_ids"] == []
    assert role["scaffold_atom_ids"] == list(f24_v1.SCAFFOLD_ROLE)
    assert role["direct_scaffold_warhead_boundary"] == {
        "bond_order": "SING",
        "boundary_valid": True,
        "scaffold_atom_id": "C5",
        "warhead_atom_id": "C2",
    }
    assert role["machine_candidate_selected"] is False
    assert role["selected_candidate_index_0based"] is None
    assert f24_v1._role_projection()["minimal_seed_status"] == "UNRESOLVED_NOT_CREATED"
    assert f24_v1._role_projection()["minimal_seed_authority_available"] is False


def test_canonical_exact5_direct_applicability() -> None:
    contract = f24_v1._canonical_task_contract()
    assert [row["semantic_long_name"] for row in contract["global_canonical_tasks"]] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert [row["display_alias"] for row in contract["global_canonical_tasks"]] == [
        "A", "B", "B2", "B3", "C",
    ]
    assert contract["global_canonical_task_count"] == 5
    assert contract["direct_profile_applicable_task_ids"] == [0, 3, 4]
    assert contract["B3_present"] is True
    assert contract["sixth_task_present"] is False


def test_include_future_candidate_is_not_admission() -> None:
    training = f24_v1._training_boundary()
    assert training["formal_event_training_use_decision"] == "INCLUDE"
    assert training["human_training_excluded"] is False
    assert training["training_use_allowed"] is True
    assert training["training_use_include"] is True
    assert training["candidate_for_future_training_admission"] is True
    assert training["future_training_candidate_derived_by_ingestion"] is True
    assert training["future_training_candidate_is_training_admission"] is False
    assert training["training_admitted"] is False
    assert training["training_admission_created"] is False
    assert training["training_materialization_allowed_now"] is False
    assert training["formal_split_authority_created"] is False
    assert training["tensor_target_created"] is False
    assert training["current_runtime_model_usable"] is False
    assert training["parameter_update_authorization"] is False
    assert training["ready_for_training"] is False


def test_pre_post_and_reusable_authority_boundaries() -> None:
    geometry = f24_v1._geometry_boundary()
    reusable = f24_v1._reusable_boundary()
    assert geometry == {
        "POST_source_evidence_available": True,
        "POST_source_evidence_count": 4,
        "POST_geometry_training_authority_created": False,
        "POST_geometry_training_target_available_now": False,
        "PRE_topology_authority_available": False,
        "PRE_geometry_authority_available": False,
        "PRE_geometry_training_label_available_now": False,
        "PRE_reconstruction_performed": False,
        "POST_to_PRE_copy_performed": False,
        "PRE_zero_fill_performed": False,
    }
    assert set(reusable.values()) == {False}


def test_published_v1_exact4_projection_and_manifest_semantics(
    artifacts: dict[str, bytes],
    bound: dict[str, object],
) -> None:
    assert tuple(artifacts) == f24_v1.OUTPUT_FILENAMES
    assert [hashlib.sha256(artifacts[name]).hexdigest() for name in f24_v1.OUTPUT_FILENAMES] == [
        "d53ff475b0d86b076b5649916cd7118821e8c883daba5727b1efd7f051b8de11",
        "516c3ea3ac291c5039e1def72a891b54fd42d5aa45388f27b436a655467cd28c",
        "be67578dac2c6593bc75b256cd9c344c90f8650662443ff5cd316bb68b18b385",
        "02f56545297fb78c2b2cbd205115d9dca680a8446bfb753109428b698bdd5dfd",
    ]
    manifest = json.loads(artifacts[f24_v1.MANIFEST])
    assert manifest["formal_decision_binding"] == bound["formal_decision_binding"]
    assert manifest["formal_validator_binding"] == bound["formal_validator_binding"]
    assert manifest["preparation_exact6_bindings"] == bound["preparation_exact6_bindings"]
    assert manifest["immutable_semantic_owner_bindings"] == bound[
        "immutable_semantic_owner_bindings"
    ]
    assert manifest["precedent_bindings"] == bound["precedent_bindings"]
    assert manifest["current_published_census_bindings"] == bound[
        "current_published_census_bindings"
    ]
    assert manifest["chemical_warhead_vs_role_region"][
        "sets_are_intentionally_distinct"
    ] is True
    assert manifest["ready_for_training"] is False


def test_historical_and_current_census_are_distinct_and_unchanged(
    bound: dict[str, object], checker: object
) -> None:
    historical = checker._verify_historical_census(bound)
    current = checker._verify_current_2a2_census(REPO_ROOT)
    assert historical == {
        "positive": 104,
        "relevant": 105,
        "include": 40,
        "exclude": 64,
        "future": 23,
        "pair": 104,
        "role": 104,
    }
    assert current == {
        "positive": 112,
        "relevant": 113,
        "include": 44,
        "exclude": 68,
        "future": 27,
        "pair": 112,
        "role": 112,
        "A": 112,
        "B": 52,
        "B2": 52,
        "B3": 112,
        "C": 112,
    }


def test_lifecycle_accepts_exactly_candidate_and_tracked_clean(checker: object) -> None:
    expected = set(checker.EXACT4_PATHS)
    candidate = checker.classify_lifecycle_from_facts(
        tracked_exact4=set(),
        ordinary_untracked=expected,
        status_entries=tuple(f"?? {path}" for path in sorted(expected)),
        working_diff=set(),
        cached_diff=set(),
    )
    tracked = checker.classify_lifecycle_from_facts(
        tracked_exact4=expected,
        ordinary_untracked=set(),
        status_entries=(),
        working_diff=set(),
        cached_diff=set(),
    )
    assert {candidate, tracked} == {"CANDIDATE_UNTRACKED", "TRACKED_CLEAN"}


@pytest.mark.parametrize(
    ("tracked", "untracked", "status", "working", "cached"),
    [
        ({"partial"}, set(), (), set(), set()),
        (set(), set(), (), set(), set()),
        (set(), {"extra"}, ("?? extra",), set(), set()),
        (set(), set(), (), {"dirty"}, set()),
        (set(), set(), (), set(), {"staged"}),
    ],
)
def test_partial_staged_dirty_extra_lifecycle_fails_closed(
    checker: object,
    tracked: set[str],
    untracked: set[str],
    status: tuple[str, ...],
    working: set[str],
    cached: set[str],
) -> None:
    with pytest.raises(ValueError, match="GIT_LIFECYCLE_PROFILE_INVALID"):
        checker.classify_lifecycle_from_facts(
            tracked_exact4=tracked,
            ordinary_untracked=untracked,
            status_entries=status,
            working_diff=working,
            cached_diff=cached,
        )
