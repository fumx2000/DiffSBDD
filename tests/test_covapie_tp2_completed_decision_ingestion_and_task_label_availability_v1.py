from __future__ import annotations

import copy
import csv
import hashlib
import importlib
import importlib.util
import io
import json
from pathlib import Path

import pytest

from covalent_ext import covapie_tp2_completed_decision_ingestion_and_task_label_availability_v1 as owner


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return owner.build_artifacts_v1(REPO_ROOT)


@pytest.fixture(scope="module")
def snapshot(artifacts: dict[str, bytes]) -> dict[str, object]:
    return json.loads(artifacts[owner.SNAPSHOT])


def load_checker():
    path = REPO_ROOT / owner.CHECKER_RELATIVE
    spec = importlib.util.spec_from_file_location("check_tp2_ingestion_v1_for_tests", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def formal_document() -> dict[str, object]:
    return json.loads((REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE).read_bytes())


def graph_inputs() -> tuple[tuple[str, ...], tuple[tuple[str, str, str], ...]]:
    document = json.loads((REPO_ROOT.parent / owner.GRAPH_EVIDENCE_RELATIVE).read_bytes())
    graph = document["canonical_heavy_atom_graph"]
    atoms = tuple(sorted(row["atom_id"] for row in graph["atom_inventory"]))
    bonds = tuple((row["atom_id_1"], row["atom_id_2"], row["bond_order"]) for row in graph["bond_inventory"])
    return atoms, bonds


def test_public_api_and_exact7_inventory_are_exact() -> None:
    assert owner.__all__ == (
        "TP2IngestionSafetyError", "load_frozen_formal_decision_v1",
        "validate_completed_decision_projection_v1", "build_artifacts_v1",
        "materialize_artifacts_v1", "check_materialized_v1",
    )
    assert owner.BASELINE_COMMIT == "d5eae86a063a4a034b983dfa64ccfbe7ab1cd13b"
    assert len(owner.CANDIDATE_PUBLICATION_PATHS) == len(set(owner.CANDIDATE_PUBLICATION_PATHS)) == 7
    assert len(owner.OUTPUT_RELATIVE_PATHS) == 4
    assert all((REPO_ROOT / path).is_file() for path in owner.CANDIDATE_PUBLICATION_PATHS)


def test_formal_exact2_identity_semantic_digest_and_exact_d6() -> None:
    formal_path = REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE
    validator_path = REPO_ROOT.parent / owner.FORMAL_VALIDATOR_RELATIVE
    assert len(formal_path.read_bytes()) == 17825
    assert hashlib.sha256(formal_path.read_bytes()).hexdigest() == "95fc125eefe09dd7ed81c9e95f2b76a084b889ece239aed5eb96215409315dc0"
    assert len(validator_path.read_bytes()) == 38756
    assert hashlib.sha256(validator_path.read_bytes()).hexdigest() == "3953a2e2f8915fff7a034716fc361b952daaccf8f167a4abb9d433a473284566"
    formal = formal_document()
    assert owner._semantic_digest(formal) == owner.FORMAL_SEMANTIC_CANONICAL_SHA256
    assert formal["semantic_freeze"]["semantic_canonical_SHA256"] == owner.FORMAL_SEMANTIC_CANONICAL_SHA256
    assert len(owner.EXPECTED_D6.encode("utf-8")) == 2202
    assert hashlib.sha256(owner.EXPECTED_D6.encode("utf-8")).hexdigest() == owner.EXPECTED_D6_SHA256


def test_formal_d1_d6_and_human_state_are_projected(snapshot: dict[str, object]) -> None:
    assert snapshot["human_authorization"] == {
        "D1_task_relevance": "NOT_RELEVANT", "D2_chemistry": "POSITIVE",
        "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR", "D4_role_candidate": "SELECT_CANDIDATE_0",
        "D5_training_use": "NOT_APPLICABLE", "D6_scientific_context": owner.EXPECTED_D6,
        "formal_decision_authority_is_human": True,
    }
    identity = snapshot["formal_identity"]
    assert identity["reviewer_id"] == identity["attestor_id"] == "fmx"
    assert identity["authorization_origin"] == "EXTERNAL_HUMAN_CHAT_REVIEW"
    assert identity["machine_scientific_authority"] is False
    assert identity["machine_human_approval"] is False
    authority = snapshot["authority_boundary"]
    assert authority["projection_of_frozen_formal_human_authority"] is True
    assert authority["new_human_authority_created_by_ingestion"] is False


@pytest.mark.parametrize(
    "path,value",
    [
        (("formal_decisions", "D1_task_relevance", "decision"), "RELEVANT"),
        (("formal_decisions", "D2_chemistry", "decision"), "NEGATIVE"),
        (("formal_decisions", "D3_reactive_pair", "ligand_atom"), "C2"),
        (("formal_decisions", "D5_training_use", "decision"), "INCLUDE"),
        (("formal_decisions", "D5_training_use", "human_training_excluded"), True),
    ],
)
def test_formal_high_value_decision_tamper_fails(path: tuple[str, ...], value: object) -> None:
    formal = formal_document()
    target = formal
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(owner.TP2IngestionSafetyError):
        owner._validate_formal(formal)


def test_formal_validator_is_provenance_only(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = importlib.import_module

    def guarded_import(name: str, *args, **kwargs):
        assert "validate_tp2_formal_human_decision_v1" not in name
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(owner.importlib, "import_module", guarded_import)
    owner.load_frozen_formal_decision_v1(REPO_ROOT)
    source = (REPO_ROOT / owner.SOURCE_RELATIVE).read_text(encoding="utf-8")
    assert "import validate_tp2_formal_human_decision_v1" not in source
    assert "from validate_tp2_formal_human_decision_v1" not in source


def test_exact4_rank_systems_and_current_census_prestate(snapshot: dict[str, object]) -> None:
    events = snapshot["events"]
    assert tuple(event["canonical_event_id"] for event in events) == owner.EXPECTED_EVENT_IDS
    assert tuple(event["scaleup_rank"] for event in events) == (42, 43, 44, 45)
    assert all(event["raw_review_unit_priority_rank"] == 27 for event in events)
    census = snapshot["current_census_boundary"]
    assert census["TP2_event_count"] == 4
    assert census["TP2_current_global_status"] == "CURRENTLY_UNREVIEWED"
    assert census["TP2_human_review_completed"] is False
    assert census["TP2_task_relevance"] == census["TP2_chemistry"] == census["TP2_training_use"] == "UNRESOLVED"
    assert census["TP2_pair_authority"] is census["TP2_role_authority"] is False
    assert census["TP2_formal_training_admitted"] is False


def test_generic_exact11_compatibility_is_task_negative_chemistry_positive(snapshot: dict[str, object]) -> None:
    generic = snapshot["generic_Exact11_compatibility"]
    assert generic["generic_exact11_compatibility_pass"] is True
    assert generic["generic_fact_field_count"] == 11
    assert generic["generic_fact_fields"] == list(owner.GENERIC_FACT_FIELDS)
    assert generic["accepted_fact_count"] == 4
    assert generic["rich_fields_leaked"] is False
    for fact in generic["facts"]:
        assert set(fact) == set(owner.GENERIC_FACT_FIELDS)
        assert fact["legacy_completed_review_status"] == "COMPLETED_HUMAN_NEGATIVE"
        assert fact["task_relevance_disposition"] == "NOT_RELEVANT"
        assert fact["chemistry_disposition"] == "POSITIVE"
        assert fact["training_disposition"] == "NOT_APPLICABLE"
        assert fact["human_training_excluded"] is False


def test_strict_role_exact21_connectivity_boundaries_seed_and_runtime(snapshot: dict[str, object]) -> None:
    atoms, bonds = graph_inputs()
    proof = owner._validate_partition_graph(atoms, bonds)
    assert proof == {
        "Exact21_count": 21, "partition_pairwise_disjoint": True,
        "partition_exhaustive": True, "W_connected": True, "L_connected": True,
        "S_connected": True, "reactive_S1_in_W": True, "cross_role_boundary_count": 2,
        "cross_role_boundaries": [dict(boundary) for boundary in owner.BOUNDARY_BONDS],
        "W_count": 1, "L_count": 3, "S_count": 17,
    }
    role = snapshot["selected_role_partition"]
    assert role["role_profile"] == "STRICT_LINKER_PRESENT_V1"
    assert role["W"] == ["S1"]
    assert role["L"] == ["C2", "C3", "N4"]
    assert role["S"] == list(owner.SCAFFOLD_ATOMS)
    assert role["counts"] == {"W": 1, "L": 3, "S": 17, "Exact": 21}
    assert role["boundary_bonds"] == list(owner.BOUNDARY_BONDS)
    assert role["minimal_seed_atom_ids"] == ["C5", "O21", "C6"]
    assert role["primary_anchor_atom_id"] == "C5"
    runtime = role["published_runtime_validation"]
    assert runtime["role_valid"] is True and runtime["role_reasons"] == []
    assert runtime["seed_valid"] is True and runtime["seed_reasons"] == []
    assert runtime["applicable_task_ids"] == [0, 1, 2, 3, 4]


def test_graph_tamper_linker_disconnect_boundary_drift_and_role_overlap(monkeypatch: pytest.MonkeyPatch) -> None:
    atoms, bonds = graph_inputs()
    disconnected = tuple(bond for bond in bonds if frozenset(bond[:2]) != frozenset(("C2", "C3")))
    with pytest.raises(owner.TP2IngestionSafetyError, match="GRAPH_L_DISCONNECTED"):
        owner._validate_partition_graph(atoms, disconnected)
    boundary_drift = tuple(
        ("S1", "C3", order) if frozenset((left, right)) == frozenset(("S1", "C2")) else (left, right, order)
        for left, right, order in bonds
    )
    with pytest.raises(owner.TP2IngestionSafetyError, match="GRAPH_BOUNDARIES_NOT_EXACT2"):
        owner._validate_partition_graph(atoms, boundary_drift)
    monkeypatch.setattr(owner, "SCAFFOLD_ATOMS", (*owner.SCAFFOLD_ATOMS, "C2"))
    with pytest.raises(owner.TP2IngestionSafetyError, match="PAIRWISE_DISJOINT"):
        owner._validate_partition_graph(atoms, bonds)


def test_exact5_full_applicability_b3_no_sixth_and_no_labels(snapshot: dict[str, object]) -> None:
    contract = snapshot["canonical_task_contract"]
    assert [row["semantic_long_name"] for row in contract["global_canonical_tasks"]] == [
        "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead", "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert contract["global_canonical_task_count"] == 5
    assert contract["B3_present"] is True
    assert contract["sixth_task"] is False
    assert contract["strict_profile_applicable_task_ids"] == [0, 1, 2, 3, 4]
    assert all(row["structurally_applicable"] is True for row in contract["strict_profile_task_applicability"])
    assert contract["task_applicability_determined"] is True
    assert contract["authoritative_task_labels_created"] is False
    assert contract["event_task_label_rows_materialized"] is False
    assert contract["training_mask_targets_available_now"] is False


def test_task_domain_negative_training_pre_post_and_reusable_boundaries(snapshot: dict[str, object]) -> None:
    for event in snapshot["events"]:
        assert event["completed_lane"] == "COMPLETED_TASK_DOMAIN_NEGATIVE"
        assert event["task_relevance"] == "NOT_RELEVANT"
        assert event["chemistry"] == "POSITIVE"
        assert event["negative_chemistry"] is False
        assert event["task_domain_negative"] is True
        assert event["positive_generative_supervision_eligible"] is False
    training = snapshot["training_boundary"]
    assert training["human_training_use_disposition"] == "NOT_APPLICABLE"
    assert training["training_use_human_authoritative"] is True
    assert training["human_training_excluded"] is False
    assert all(training[key] is False for key in (
        "future_training_admission_candidate", "formal_training_admitted",
        "training_admission_created", "training_materialization_allowed", "formal_split_authority",
        "tensor_target_created", "training_mask_targets_available_now", "current_runtime_model_usable",
        "parameter_update_authorization", "ready_for_training",
    ))
    pre = snapshot["PRE_boundary"]
    assert pre["supporting_PRE_source_graph_count"] == pre["PRE_source_graph_count"] == pre["PRE_mapping_count"] == 0
    assert pre["PRE_source_graph_present"] is False
    assert pre["PRE_mapping_status"] == "PRE_SOURCE_GRAPH_NOT_AVAILABLE"
    assert pre["PRE_status"] == "PRE_REACTION_UNRESOLVED"
    post = snapshot["POST_boundary"]
    assert post["POST_source_evidence_available"] is True
    assert post["explicit_covalent_evidence"] is True
    assert post["distance_only_inference"] is False
    assert post["POST_geometry_training_authority"] is False
    assert all(value is False for value in snapshot["reusable_authority_boundary"].values())


def test_matrix_exact4_and_summary_counts(artifacts: dict[str, bytes]) -> None:
    reader = csv.DictReader(io.StringIO(artifacts[owner.MATRIX].decode("utf-8"), newline=""))
    rows = list(reader)
    assert tuple(reader.fieldnames or ()) == owner.MATRIX_HEADER
    assert len(rows) == 4
    assert tuple(row["canonical_event_id"] for row in rows) == owner.EXPECTED_EVENT_IDS
    assert all(row["legacy_completed_review_status"] == "COMPLETED_HUMAN_NEGATIVE" for row in rows)
    assert all(row["task_relevance"] == "NOT_RELEVANT" and row["chemistry"] == "POSITIVE" for row in rows)
    assert all(row["strict_profile_applicable_task_ids_json"] == "[0,1,2,3,4]" for row in rows)
    assert all(row["event_task_label_rows_materialized"] == "false" for row in rows)
    summary = json.loads(artifacts[owner.SUMMARY])
    required = {
        "event_count": 4, "chemistry_positive_event_count": 4,
        "task_not_relevant_event_count": 4,
        "task_domain_negative_chemistry_positive_event_count": 4,
        "pair_authoritative_event_count": 4, "role_authoritative_event_count": 4,
        "STRICT_profile_event_count": 4,
        "canonical_mask_structural_labels_available_event_count": 4,
        "task_applicability_determined_event_count": 4,
        "authoritative_task_label_event_count": 0,
        "training_NOT_APPLICABLE_event_count": 4,
        "future_training_admission_candidate_count": 0,
        "formal_training_admitted_count": 0, "POST_source_evidence_count": 4,
        "POST_training_authority_count": 0, "PRE_authority_count": 0,
    }
    for key, value in required.items():
        assert summary[key] == value


@pytest.mark.parametrize(
    "section,key,value",
    [
        ("canonical_task_contract", "B3_present", False),
        ("canonical_task_contract", "sixth_task", True),
        ("canonical_task_contract", "global_canonical_task_count", 6),
        ("canonical_task_contract", "strict_profile_applicable_task_ids", [0, 1, 2, 4]),
        ("training_boundary", "future_training_admission_candidate", True),
        ("training_boundary", "formal_training_admitted", True),
        ("PRE_boundary", "PRE_topology_authority", True),
        ("POST_boundary", "POST_geometry_training_authority", True),
        ("reusable_authority_boundary", "reusable_pair_authority", True),
        ("selected_role_partition", "L", ["C2", "C3"]),
        ("selected_role_partition", "boundary_bonds", []),
    ],
)
def test_high_value_projection_tamper_fails_closed(
    artifacts: dict[str, bytes], section: str, key: str, value: object,
) -> None:
    changed = dict(artifacts)
    document = json.loads(changed[owner.SNAPSHOT])
    document[section][key] = value
    changed[owner.SNAPSHOT] = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    with pytest.raises(owner.TP2IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed, REPO_ROOT)


def test_missing_exact4_event_and_matrix_connectivity_tamper_fail_owner_and_checker(artifacts: dict[str, bytes]) -> None:
    checker = load_checker()
    changed = dict(artifacts)
    reader = csv.DictReader(io.StringIO(changed[owner.MATRIX].decode("utf-8"), newline=""))
    rows = list(reader)
    rows.pop()
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=owner.MATRIX_HEADER, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    changed[owner.MATRIX] = stream.getvalue().encode("utf-8")
    with pytest.raises(owner.TP2IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed, REPO_ROOT)
    with pytest.raises(RuntimeError, match="MATRIX_INVENTORY_DRIFT"):
        checker.independently_check_projection(REPO_ROOT, changed)

    changed = dict(artifacts)
    reader = csv.DictReader(io.StringIO(changed[owner.MATRIX].decode("utf-8"), newline=""))
    rows = list(reader)
    rows[0]["linker_connected"] = "false"
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=owner.MATRIX_HEADER, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    changed[owner.MATRIX] = stream.getvalue().encode("utf-8")
    with pytest.raises(RuntimeError, match="MATRIX_SEMANTIC_DRIFT:linker_connected"):
        checker.independently_check_projection(REPO_ROOT, changed)


def test_source_and_current_census_drift_fail_closed(tmp_path: Path) -> None:
    formal = REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE
    changed_formal = tmp_path / formal.name
    changed_formal.write_bytes(formal.read_bytes() + b" ")
    with pytest.raises(owner.TP2IngestionSafetyError):
        owner.load_frozen_formal_decision_v1(REPO_ROOT, formal_decision_path=changed_formal)
    census = REPO_ROOT / owner.CENSUS_MATRIX_RELATIVE
    changed_census = tmp_path / census.name
    payload = census.read_bytes().replace(b"CURRENTLY_UNREVIEWED", b"CURRENTLY_IN_PROGRESS", 1)
    changed_census.write_bytes(payload)
    with pytest.raises(owner.TP2IngestionSafetyError):
        owner.load_frozen_formal_decision_v1(
            REPO_ROOT, repository_path_overrides={owner.CENSUS_MATRIX_RELATIVE: changed_census},
        )


def test_deterministic_materialization_and_manifest_closure(artifacts: dict[str, bytes]) -> None:
    assert artifacts == owner.build_artifacts_v1(REPO_ROOT)
    checked = owner.check_materialized_v1(REPO_ROOT)
    assert checked["status"] == "PASS"
    assert checked["materialized_bytes_equal_fresh_build"] is True
    assert checked["deterministic_double_build"] is True
    manifest = json.loads(artifacts[owner.MANIFEST])
    assert manifest["candidate_publication_file_count"] == 7
    assert manifest["output_artifact_count"] == 4
    assert manifest["active_source_binding_count"] == 14
    assert manifest["manifest_self_SHA256_recorded"] is False
    assert manifest["frozen_formal_validator_provenance_identity_only"] is True
    assert manifest["frozen_formal_validator_parsed"] is False
    assert manifest["frozen_formal_validator_imported"] is False
    assert manifest["frozen_formal_validator_executed"] is False
    assert manifest["frozen_formal_validator_subprocessed"] is False
    assert all(not Path(row["path"]).is_absolute() for row in manifest["active_source_bindings"])


def test_checker_current_lifecycle_and_independent_proofs(artifacts: dict[str, bytes]) -> None:
    checker = load_checker()
    lifecycle = checker.check_git_lifecycle(REPO_ROOT)
    assert lifecycle["profile"] in {checker.CANDIDATE_UNTRACKED, checker.TRACKED_CLEAN}
    if lifecycle["profile"] == checker.CANDIDATE_UNTRACKED:
        assert lifecycle["ordinary_untracked_count"] == 7
        assert lifecycle["HEAD"] == lifecycle["origin_main"] == owner.BASELINE_COMMIT
        assert lifecycle["ahead"] == lifecycle["behind"] == 0
    sources = checker.independently_check_sources(REPO_ROOT)
    assert sources["active_source_binding_count"] == 14
    assert sources["formal"]["semantic_SHA256"] == owner.FORMAL_SEMANTIC_CANONICAL_SHA256
    projection = checker.independently_check_projection(REPO_ROOT, artifacts)
    assert projection["event_count"] == 4
    assert projection["applicable_task_ids"] == [0, 1, 2, 3, 4]
    assert projection["runtime_and_generic"]["generic_Exact11_accepted_count"] == 4


@pytest.mark.parametrize("state", ("committed-unpushed", "pushed-successor", "later-clean-descendant"))
def test_checker_lifecycle_supports_both_profiles(monkeypatch: pytest.MonkeyPatch, state: str) -> None:
    checker = load_checker()
    expected = [path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS]
    successor = hashlib.sha256(b"TP2-successor").hexdigest()
    descendant = hashlib.sha256(b"TP2-later-descendant").hexdigest()
    if state == "committed-unpushed":
        head, origin, counts = successor, owner.BASELINE_COMMIT, "0\t1"
    elif state == "pushed-successor":
        head, origin, counts = successor, successor, "0\t0"
    else:
        head, origin, counts = descendant, successor, "0\t1"

    def fake_git(_root: Path, *args: str) -> str:
        if args == ("branch", "--show-current"):
            return "main"
        if args == ("rev-parse", "HEAD"):
            return head
        if args == ("rev-parse", "origin/main"):
            return origin
        if args[:3] == ("rev-list", "--left-right", "--count"):
            return counts
        if args in (("diff", "--name-only"), ("diff", "--cached", "--name-only")):
            return ""
        if args == ("ls-files", "--others", "--exclude-standard"):
            return ""
        if args[:2] == ("ls-files", "--"):
            return "\n".join(expected)
        if args[:2] == ("diff", "--name-only") and args[2] == owner.BASELINE_COMMIT + "..HEAD":
            return "\n".join(expected)
        raise AssertionError(args)

    monkeypatch.setattr(checker, "git", fake_git)
    monkeypatch.setattr(checker, "is_ancestor", lambda *_args: True)
    assert checker.check_git_lifecycle(REPO_ROOT)["profile"] == checker.TRACKED_CLEAN


def test_checker_rejects_extra_untracked(monkeypatch: pytest.MonkeyPatch) -> None:
    checker = load_checker()
    real_git = checker.git

    def fake_git(root: Path, *args: str) -> str:
        if args == ("ls-files", "--others", "--exclude-standard"):
            return real_git(root, *args) + "\nunrelated.txt"
        return real_git(root, *args)

    monkeypatch.setattr(checker, "git", fake_git)
    with pytest.raises(RuntimeError, match="ORDINARY_UNTRACKED"):
        checker.check_git_lifecycle(REPO_ROOT)


def test_no_dynamic_metadata_forbidden_suffix_or_operation_expansion(artifacts: dict[str, bytes]) -> None:
    assert not any(path.as_posix().endswith(owner_path) for path in owner.CANDIDATE_PUBLICATION_PATHS for owner_path in (".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pyc", ".tmp", ".part"))
    manifest = json.loads(artifacts[owner.MANIFEST])
    assert manifest["determinism"] == {"canonical_JSON": True, "LF_only": True, "timestamps": False, "hostname": False, "pid": False, "absolute_machine_paths": False}
    assert manifest["operation_boundary"] == {"reconciliation": False, "census_refresh": False, "queue_refresh": False, "training": False, "tensorization": False, "dataset_mutation": False, "commit": False, "push": False}
