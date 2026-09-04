from __future__ import annotations

import copy
import csv
import hashlib
import importlib
import importlib.util
import io
import json
from pathlib import Path
import sys

import pytest

from covalent_ext import covapie_4lh_completed_decision_ingestion_and_task_label_availability_v1 as owner


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return owner.build_artifacts_v1(REPO_ROOT)


@pytest.fixture(scope="module")
def snapshot(artifacts: dict[str, bytes]) -> dict[str, object]:
    return json.loads(artifacts[owner.SNAPSHOT])


def load_checker():
    path = REPO_ROOT / owner.CHECKER_RELATIVE
    spec = importlib.util.spec_from_file_location("check_4lh_ingestion_v1_for_tests", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_public_api_is_exact_and_compact() -> None:
    assert owner.__all__ == (
        "FourLHIngestionSafetyError",
        "load_frozen_formal_decision_v1",
        "validate_completed_decision_projection_v1",
        "build_artifacts_v1",
        "materialize_artifacts_v1",
        "check_materialized_v1",
    )


def test_schema_versions_and_exact7_inventory_are_exact() -> None:
    assert owner.SCHEMA_VERSION == "covapie_4lh_completed_decision_ingestion_and_task_label_availability_v1"
    assert len(owner.CANDIDATE_PUBLICATION_PATHS) == 7
    assert len(set(owner.CANDIDATE_PUBLICATION_PATHS)) == 7
    assert len(owner.OUTPUT_RELATIVE_PATHS) == 4
    assert {path.name for path in owner.OUTPUT_RELATIVE_PATHS} == set(owner.OUTPUT_FILENAMES)
    assert all((REPO_ROOT / path).is_file() for path in owner.CANDIDATE_PUBLICATION_PATHS)


def test_formal_exact2_semantic_digest_and_d6_are_bound() -> None:
    formal_path = REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE
    validator_path = REPO_ROOT.parent / owner.FORMAL_VALIDATOR_RELATIVE
    assert len(formal_path.read_bytes()) == 18475
    assert hashlib.sha256(formal_path.read_bytes()).hexdigest() == "bbcf803ec3dbb13267cb580185ad6ed209c4eff2f373361511c6b641ffede203"
    assert len(validator_path.read_bytes()) == 38299
    assert hashlib.sha256(validator_path.read_bytes()).hexdigest() == "18a35d13cb1e5a11d5a0e25137d4b59dfaebc0b37056c0d876016d3bcb7901dc"
    document = json.loads(formal_path.read_bytes())
    clone = copy.deepcopy(document)
    assert clone.pop("formal_semantic_canonical_sha256") == owner.FORMAL_SEMANTIC_CANONICAL_SHA256
    payload = json.dumps(clone, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    assert hashlib.sha256(payload).hexdigest() == owner.FORMAL_SEMANTIC_CANONICAL_SHA256
    assert len(owner.EXPECTED_D6.encode()) == 1501
    assert hashlib.sha256(owner.EXPECTED_D6.encode()).hexdigest() == owner.EXPECTED_D6_SHA256


def test_formal_d1_d5_and_authority_boundary(snapshot: dict[str, object]) -> None:
    assert snapshot["human_authorization"] == {
        "D1_task_relevance": "RELEVANT",
        "D2_chemistry": "POSITIVE",
        "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
        "D4_role_candidate": "SELECT_CANDIDATE_0",
        "D5_training_use": "INCLUDE",
        "D6_scientific_context": owner.EXPECTED_D6,
        "formal_decision_authority_is_human": True,
    }
    authority = snapshot["authority_boundary"]
    assert authority["projection_of_frozen_formal_human_authority"] is True
    assert authority["new_human_authority_created_by_ingestion"] is False
    assert authority["authoritative_task_labels_created"] is False
    assert authority["event_task_label_rows_materialized"] is False


@pytest.mark.parametrize("decision,value", [
    ("D1_task_relevance", "NOT_RELEVANT"),
    ("D2_chemistry", "NEGATIVE"),
])
def test_formal_d1_d2_drift_fails_even_with_refreshed_semantic_digest(decision: str, value: str) -> None:
    formal = json.loads((REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE).read_bytes())
    formal["formal_human_decision"][decision]["value"] = value
    formal.pop("formal_semantic_canonical_sha256")
    formal["formal_semantic_canonical_sha256"] = owner._sha256(owner._canonical_json(formal))
    with pytest.raises(owner.FourLHIngestionSafetyError):
        owner._validate_formal(formal)


def test_formal_validator_is_never_imported_or_executed(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = importlib.import_module

    def guarded_import(name: str, *args, **kwargs):
        assert "validate_4lh_formal_human_decision_v1" not in name
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(owner.importlib, "import_module", guarded_import)
    owner.load_frozen_formal_decision_v1(REPO_ROOT)
    source = (REPO_ROOT / owner.SOURCE_RELATIVE).read_text()
    assert "import validate_4lh_formal_human_decision_v1" not in source
    assert "from validate_4lh_formal_human_decision_v1" not in source


def test_supporting_exact4_current_census_and_pending_rank1_are_independent(snapshot: dict[str, object]) -> None:
    assert tuple(event["canonical_event_id"] for event in snapshot["events"]) == owner.EXPECTED_EVENT_IDS
    assert tuple(event["scaleup_rank"] for event in snapshot["events"]) == owner.EXPECTED_RANKS
    assert [event["POST_distance_frozen_lexeme"] for event in snapshot["events"]] == [row[5] for row in owner.EXPECTED_EVENTS]
    census = snapshot["current_census_boundary"]
    assert census["4LH_event_count"] == 4
    assert census["4LH_current_global_status"] == "CURRENTLY_UNREVIEWED"
    assert census["4LH_task_relevance"] == "UNRESOLVED"
    assert census["4LH_chemistry"] == "UNRESOLVED"
    assert census["4LH_training_use"] == "UNRESOLVED"
    assert census["current_pending_rank"] == 1
    assert census["census_modified_by_ingestion"] is False


def test_pair_role_partition_boundary_seed_and_runtime(snapshot: dict[str, object]) -> None:
    pair = snapshot["reactive_pair_authority"]
    assert pair["protein_reactive_atom"] == "SG"
    assert pair["ligand_reactive_atom"] == "CAP"
    assert pair["pair_authority_scope"] == owner.PAIR_AUTHORITY_SCOPE
    assert pair["cross_structure_regiochemistry_generalization"] is False
    assert pair["reusable_pair_rule_created"] is False
    assert pair["all_4LH_uses_CAP_authority"] is False
    role = snapshot["selected_role_partition"]
    assert role["W"] == list(owner.WARHEAD_ATOMS)
    assert role["L"] == []
    assert role["S"] == list(owner.SCAFFOLD_ATOMS)
    assert role["counts"] == {"W": 5, "L": 0, "S": 31, "Exact": 36}
    assert role["direct_scaffold_warhead_boundary"] == owner.BOUNDARY
    assert role["minimal_seed_atom_ids"] == ["CAJ", "CAN", "CBH"]
    assert role["primary_anchor_atom_id"] == "CBH"
    runtime = role["published_DIRECT_runtime_validation"]
    assert runtime["valid"] is True and runtime["reasons"] == []
    assert runtime["counts"] == {"W": 5, "L": 0, "S": 31}
    assert runtime["applicable_task_ids"] == [0, 3, 4]
    assert runtime["complete_payload_review_signature_bound"] is True


def frozen_graph_inputs() -> tuple[tuple[str, ...], tuple[tuple[str, str, str], ...]]:
    path = REPO_ROOT.parent / owner.GRAPH_EVIDENCE_RELATIVE
    graph = json.loads(path.read_bytes())["canonical_heavy_atom_graph"]
    atom_ids = tuple(sorted(row["atom_id"] for row in graph["atom_inventory"]))
    bonds = tuple(
        (row["atom_id_1"], row["atom_id_2"], row["bond_order"])
        for row in graph["bond_inventory"]
    )
    return atom_ids, bonds


def test_independent_frozen_graph_structural_proof_is_exact() -> None:
    atom_ids, bonds = frozen_graph_inputs()
    proof = owner._validate_partition_graph(atom_ids, bonds)
    assert proof == {
        "Exact36_count": 36,
        "partition_pairwise_disjoint": True,
        "partition_exhaustive": True,
        "W_connected": True,
        "L_connected_or_empty": True,
        "S_connected": True,
        "reactive_CAP_in_W": True,
        "cross_role_boundary_count": 1,
        "cross_role_boundary": {
            "scaffold_atom_id": "CBH",
            "warhead_atom_id": "NBA",
            "bond_order": "SING",
            "scaffold_role": "S",
            "warhead_role": "W",
        },
        "W_count": 5,
        "L_count": 0,
        "S_count": 31,
    }


def test_independent_graph_rejects_disconnected_W() -> None:
    atom_ids, bonds = frozen_graph_inputs()
    changed = tuple(
        bond for bond in bonds if frozenset(bond[:2]) != frozenset(("CAP", "CAQ"))
    )
    with pytest.raises(owner.FourLHIngestionSafetyError, match="GRAPH_W_DISCONNECTED"):
        owner._validate_partition_graph(atom_ids, changed)


def test_independent_graph_rejects_disconnected_S() -> None:
    atom_ids, bonds = frozen_graph_inputs()
    changed = tuple(
        bond for bond in bonds if frozenset(bond[:2]) != frozenset(("CAB", "NBO"))
    )
    with pytest.raises(owner.FourLHIngestionSafetyError, match="GRAPH_S_DISCONNECTED"):
        owner._validate_partition_graph(atom_ids, changed)


def test_independent_graph_rejects_second_S_W_boundary() -> None:
    atom_ids, bonds = frozen_graph_inputs()
    changed = (*bonds, ("CAJ", "CAP", "SING"))
    with pytest.raises(owner.FourLHIngestionSafetyError, match="BOUNDARY_NOT_UNIQUE"):
        owner._validate_partition_graph(atom_ids, changed)


def test_exact5_b3_no_sixth_and_label_availability_only(snapshot: dict[str, object]) -> None:
    contract = snapshot["canonical_task_contract"]
    assert [row["semantic_long_name"] for row in contract["global_canonical_tasks"]] == [
        "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead", "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert contract["global_canonical_task_count"] == 5
    assert contract["B3_present"] is True
    assert contract["sixth_task"] is False
    assert contract["direct_profile_applicable_task_ids"] == [0, 3, 4]
    assert contract["task_applicability"][1]["reason"] == "not_applicable_empty_linker_redundant_with_A"
    assert contract["task_applicability"][2]["reason"] == "not_applicable_empty_non_C_fixed_context"
    assert contract["authoritative_task_labels_created"] is False
    assert contract["event_task_label_rows_materialized"] is False
    assert contract["training_mask_targets_available_now"] is False


def test_include_future_candidate_but_no_training_admission(snapshot: dict[str, object]) -> None:
    training = snapshot["training_boundary"]
    assert training["human_training_use_disposition"] == "INCLUDE"
    assert training["training_use_human_authoritative"] is True
    assert training["future_training_admission_candidate"] is True
    assert training["future_training_admission_status"] == owner.FUTURE_STATUS
    for key in ("formal_training_admitted", "training_admission_created", "training_materialization_allowed", "formal_split_authority", "tensor_target_created", "training_mask_targets_available_now", "current_runtime_model_usable", "parameter_update_authorization", "ready_for_training"):
        assert training[key] is False


def test_pre_ambiguous_unresolved_and_post_evidence_boundary(snapshot: dict[str, object]) -> None:
    pre = snapshot["PRE_boundary"]
    assert pre["supporting_PRE_source_graph_count"] == 1
    assert pre["PRE_source_graph_present"] is True
    assert pre["PRE_source_graph_count"] == 1
    assert pre["PRE_mapping_count"] == 2
    assert pre["PRE_mapping_status"] == "PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS"
    assert pre["PRE_status"] == "PRE_REACTION_UNRESOLVED"
    for key in ("PRE_topology_authority", "PRE_geometry_authority", "PRE_coordinates_authority", "PRE_reconstruction_performed", "POST_to_PRE_copy", "PRE_zero_fill", "leaving_group_inferred", "reagent_inferred", "reaction_edit_inferred"):
        assert pre[key] is False
    post = snapshot["POST_boundary"]
    assert post["POST_source_evidence_available"] is True
    assert post["explicit_covalent_evidence"] is True
    assert post["distance_only_inference"] is False
    assert post["POST_geometry_training_authority"] is False
    assert post["POST_geometry_training_target_created"] is False


def test_matrix_exact4_projection(artifacts: dict[str, bytes]) -> None:
    reader = csv.DictReader(io.StringIO(artifacts[owner.MATRIX].decode(), newline=""))
    rows = list(reader)
    assert tuple(reader.fieldnames or ()) == owner.MATRIX_HEADER
    assert len(rows) == 4
    assert tuple(row["canonical_event_id"] for row in rows) == owner.EXPECTED_EVENT_IDS
    assert all(row["human_task_relevance_decision"] == "RELEVANT" for row in rows)
    assert all(row["human_chemistry_decision"] == "POSITIVE" for row in rows)
    assert all(row["protein_reactive_atom"] == "SG" and row["ligand_reactive_atom"] == "CAP" for row in rows)
    assert all(row["direct_profile_applicable_task_ids_json"] == "[0,3,4]" for row in rows)
    assert all(row["PRE_mapping_count"] == "2" for row in rows)
    assert all(row["formal_training_admitted"] == "false" for row in rows)


def test_matrix_connectivity_drift_fails_owner_and_checker(artifacts: dict[str, bytes]) -> None:
    changed = dict(artifacts)
    reader = csv.DictReader(io.StringIO(changed[owner.MATRIX].decode(), newline=""))
    rows = list(reader)
    rows[0]["warhead_connected"] = "false"
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=owner.MATRIX_HEADER, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    changed[owner.MATRIX] = stream.getvalue().encode()
    with pytest.raises(owner.FourLHIngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed, REPO_ROOT)
    checker = load_checker()
    with pytest.raises(RuntimeError, match="MATRIX_SEMANTIC_DRIFT:warhead_connected"):
        checker.independently_check_projection(REPO_ROOT, changed)


@pytest.mark.parametrize("artifact,mutation", [
    (owner.SNAPSHOT, ("human_authorization", "D1_task_relevance", "NOT_RELEVANT")),
    (owner.SNAPSHOT, ("reactive_pair_authority", "ligand_reactive_atom", "NBA")),
    (owner.SNAPSHOT, ("selected_role_partition", "W", ["CAQ", "CBE", "OAE", "NBA"])),
    (owner.SNAPSHOT, ("selected_role_partition", "direct_scaffold_warhead_boundary", {"scaffold_atom_id": "CAJ", "warhead_atom_id": "NBA", "bond_order": "SING"})),
    (owner.SNAPSHOT, ("selected_role_partition", "minimal_seed_atom_ids", ["CAJ", "CBH"])),
    (owner.SNAPSHOT, ("canonical_task_contract", "B3_present", False)),
    (owner.SNAPSHOT, ("canonical_task_contract", "direct_profile_applicable_task_ids", [0, 4])),
    (owner.SNAPSHOT, ("training_boundary", "formal_training_admitted", True)),
    (owner.SNAPSHOT, ("PRE_boundary", "PRE_mapping_count", 1)),
    (owner.SNAPSHOT, ("reusable_authority_boundary", "reusable_pair_authority", True)),
])
def test_high_value_projection_tamper_fails_closed(artifacts: dict[str, bytes], artifact: str, mutation: tuple[str, str, object]) -> None:
    changed = dict(artifacts)
    document = json.loads(changed[artifact])
    document[mutation[0]][mutation[1]] = mutation[2]
    changed[artifact] = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    with pytest.raises(owner.FourLHIngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed, REPO_ROOT)


def test_formal_source_binding_drift_fails_closed(tmp_path: Path) -> None:
    source = REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE
    changed = tmp_path / source.name
    changed.write_bytes(source.read_bytes() + b" ")
    with pytest.raises(owner.FourLHIngestionSafetyError):
        owner.load_frozen_formal_decision_v1(REPO_ROOT, formal_decision_path=changed)


def test_build_determinism_materialization_and_manifest_closure(artifacts: dict[str, bytes]) -> None:
    assert artifacts == owner.build_artifacts_v1(REPO_ROOT)
    checked = owner.check_materialized_v1(REPO_ROOT)
    assert checked["status"] == "PASS"
    assert checked["materialized_bytes_equal_fresh_build"] is True
    assert checked["deterministic_double_build"] is True
    manifest = json.loads(artifacts[owner.MANIFEST])
    assert manifest["candidate_publication_file_count"] == 7
    assert manifest["output_artifact_count"] == 4
    assert manifest["active_source_binding_count"] == 12
    assert manifest["manifest_self_SHA256_recorded"] is False
    assert manifest["frozen_formal_validator_provenance_identity_only"] is True
    assert manifest["frozen_formal_validator_imported"] is False
    assert manifest["frozen_formal_validator_executed"] is False
    assert manifest["frozen_formal_validator_subprocessed"] is False
    assert all(Path(row["path"]).is_absolute() is False for row in manifest["active_source_bindings"])


def test_checker_current_supported_lifecycle_profile_and_independent_projection(
    artifacts: dict[str, bytes],
) -> None:
    checker = load_checker()
    lifecycle = checker.check_git_lifecycle(REPO_ROOT)
    assert lifecycle["profile"] in {
        checker.CANDIDATE_UNTRACKED,
        checker.TRACKED_CLEAN,
    }
    if lifecycle["profile"] == checker.CANDIDATE_UNTRACKED:
        assert lifecycle["ordinary_untracked_count"] == 7
        assert lifecycle["HEAD"] == owner.BASELINE_COMMIT
        assert lifecycle["origin_main"] == owner.BASELINE_COMMIT
        assert lifecycle["ahead"] == 0
        assert lifecycle["behind"] == 0
    else:
        assert lifecycle["ordinary_untracked_count"] == 0
        assert lifecycle["behind"] == 0
    sources = checker.independently_check_sources(REPO_ROOT)
    assert sources["active_source_binding_count"] == 12
    assert sources["formal_validator_provenance_only"] is True
    projection = checker.independently_check_projection(REPO_ROOT, artifacts)
    assert projection["event_count"] == 4
    assert projection["applicable_task_ids"] == [0, 3, 4]


@pytest.mark.parametrize(
    "state",
    ("committed-unpushed", "pushed-successor", "later-clean-descendant"),
)
def test_checker_lifecycle_simulates_realistic_future_states(
    monkeypatch: pytest.MonkeyPatch, state: str
) -> None:
    checker = load_checker()
    expected = [path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS]
    successor = hashlib.sha256(b"4LH-revised1-successor").hexdigest()
    descendant = hashlib.sha256(b"4LH-revised1-later-descendant").hexdigest()
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
        if args == ("diff", "--name-only") or args == ("diff", "--cached", "--name-only"):
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


def test_checker_lifecycle_rejects_extra_untracked(monkeypatch: pytest.MonkeyPatch) -> None:
    checker = load_checker()
    real_git = checker.git

    def fake_git(root: Path, *args: str) -> str:
        if args == ("ls-files", "--others", "--exclude-standard"):
            return real_git(root, *args) + "\nunrelated.txt"
        return real_git(root, *args)

    monkeypatch.setattr(checker, "git", fake_git)
    with pytest.raises(RuntimeError, match="ORDINARY_UNTRACKED"):
        checker.check_git_lifecycle(REPO_ROOT)


def test_no_dynamic_metadata_or_forbidden_candidate_suffixes() -> None:
    forbidden = (".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pyc", ".tmp", ".part")
    assert not any(path.as_posix().endswith(forbidden) for path in owner.CANDIDATE_PUBLICATION_PATHS)
    manifest = json.loads((REPO_ROOT / owner.OUTPUT_ROOT_RELATIVE / owner.MANIFEST).read_bytes())
    assert manifest["determinism"] == {"canonical_JSON": True, "LF_only": True, "timestamps": False, "hostname": False, "pid": False, "absolute_machine_paths": False}
    assert manifest["operation_boundary"] == {"reconciliation": False, "census_refresh": False, "queue_refresh": False, "training": False, "tensorization": False, "dataset_mutation": False, "commit": False, "push": False}
