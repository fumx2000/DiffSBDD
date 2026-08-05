from __future__ import annotations

import copy
import csv
import hashlib
import importlib
import inspect
import io
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_current11_unit_000001_partial_supervision_routing_gate_v1 as gate,
)


SCRIPT = ROOT / gate.SCRIPT_PATH


def _locate_state() -> Path:
    local = ROOT.parent / "covapie-state"
    if local.is_dir():
        return local.resolve(strict=True)
    remote = subprocess.check_output(
        ("git", "config", "--get", "remote.origin.url"), cwd=ROOT
    ).decode("utf-8").strip()
    candidate = Path(remote).parent / "covapie-state"
    if not Path(remote).is_absolute() or not candidate.is_dir():
        raise AssertionError("formal state unavailable")
    return candidate.resolve(strict=True)


STATE_ROOT = _locate_state()


@pytest.fixture(scope="module")
def response() -> dict[str, object]:
    return gate.evaluate_covapie_current11_unit_000001_partial_supervision_routing_gate_v1(
        repo_root=ROOT,
        state_root=STATE_ROOT,
    )


def _payloads() -> tuple[dict[str, bytes], dict[str, bytes]]:
    repository = {
        source_id: (ROOT / relative).read_bytes()
        for source_id, (relative, _digest) in gate.REPO_SOURCES.items()
    }
    state = {
        source_id: (STATE_ROOT / relative).read_bytes()
        for source_id, (relative, _digest) in gate.STATE_SOURCES.items()
    }
    return repository, state


def _mutate_csv(payload: bytes, row_index: int, field: str, value: str) -> bytes:
    text = payload.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    fields = tuple(reader.fieldnames or ())
    rows = list(reader)
    rows[row_index][field] = value
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _source_snapshot() -> dict[str, object]:
    files: dict[str, object] = {}
    for root, specs in ((ROOT, gate.REPO_SOURCES), (STATE_ROOT, gate.STATE_SOURCES)):
        for source_id, (relative, _digest) in specs.items():
            path = root / relative
            metadata = path.lstat()
            payload = path.read_bytes()
            files[f"{root}:{source_id}"] = (
                metadata.st_dev,
                metadata.st_ino,
                stat.S_IMODE(metadata.st_mode),
                len(payload),
                hashlib.sha256(payload).hexdigest(),
            )
    dossier = STATE_ROOT / gate.DOSSIER_RELATIVE
    dossier_metadata = dossier.lstat()
    return {
        "files": files,
        "dossier": (
            dossier_metadata.st_dev,
            dossier_metadata.st_ino,
            stat.S_IMODE(dossier_metadata.st_mode),
            tuple(
                (child.name, hashlib.sha256(child.read_bytes()).hexdigest())
                for child in sorted(dossier.iterdir())
            ),
        ),
        "git": subprocess.check_output(
            ("git", "status", "--porcelain=v1", "--untracked-files=all"), cwd=ROOT
        ),
    }


def _record(response: dict[str, object], sample: str, task: str) -> dict[str, object]:
    records = response["routing_records"]
    assert isinstance(records, list)
    selected = [
        item for item in records
        if item["sample_index_row_id"] == sample and item["semantic_task_name"] == task
    ]
    assert len(selected) == 1
    return selected[0]


def test_unique_keyword_only_public_api() -> None:
    assert gate.__all__ == (
        "evaluate_covapie_current11_unit_000001_partial_supervision_routing_gate_v1",
    )
    signature = inspect.signature(
        gate.evaluate_covapie_current11_unit_000001_partial_supervision_routing_gate_v1
    )
    assert tuple(signature.parameters) == ("repo_root", "state_root")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    with pytest.raises(TypeError):
        gate.evaluate_covapie_current11_unit_000001_partial_supervision_routing_gate_v1(
            ROOT, STATE_ROOT
        )


def test_silent_import_and_stdlib_only_boundary() -> None:
    completed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            "import covalent_ext.covapie_current11_unit_000001_partial_supervision_routing_gate_v1",
        ),
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": "src", "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == b""
    source = (ROOT / gate.MODULE_PATH).read_text(encoding="utf-8")
    for forbidden in ("torch", "rdkit", "openbabel", "requests", "urllib.request"):
        assert forbidden not in source.lower()


def test_deterministic_double_evaluation_and_read_only(response: dict[str, object]) -> None:
    before = _source_snapshot()
    second = gate.evaluate_covapie_current11_unit_000001_partial_supervision_routing_gate_v1(
        repo_root=ROOT, state_root=STATE_ROOT
    )
    after = _source_snapshot()
    assert response == second
    assert json.dumps(response, sort_keys=True, separators=(",", ":")) == json.dumps(
        second, sort_keys=True, separators=(",", ":")
    )
    assert before == after


def test_top_level_contract_and_exact2_sample_order(response: dict[str, object]) -> None:
    assert tuple(response) == (
        "schema_version", "base_commit", "review_unit_id", "samples",
        "semantic_task_names", "eligibility_state_vocabulary", "canonical_mask_semantics",
        "source_bindings", "routing_records", "summary", "readiness", "repository_lifecycle",
    )
    assert response["schema_version"] == gate.SCHEMA_VERSION
    assert response["base_commit"] == gate.BASE_COMMIT
    assert response["review_unit_id"] == gate.REVIEW_UNIT_ID
    assert response["samples"] == [
        {
            "sample_index_row_id": "CYS_SG_SAMPLE_INDEX_000008",
            "pdb_id": "1AYU",
            "ligand_comp_id": "INA",
        },
        {
            "sample_index_row_id": "CYS_SG_SAMPLE_INDEX_000010",
            "pdb_id": "1AYW",
            "ligand_comp_id": "IN3",
        },
    ]


def test_exact25_and_exact7_vocabularies(response: dict[str, object]) -> None:
    assert tuple(response["semantic_task_names"]) == gate.SEMANTIC_TASK_NAMES
    assert len(set(response["semantic_task_names"])) == 25
    assert tuple(response["eligibility_state_vocabulary"]) == (
        "admissible_now",
        "admissible_as_observed_geometry_only",
        "candidate_only_not_authoritative",
        "blocked_missing_evidence",
        "blocked_state_ambiguity",
        "blocked_missing_human_approval",
        "not_applicable",
    )


def test_exact50_record_shape_order_and_runtime_boundary(response: dict[str, object]) -> None:
    records = response["routing_records"]
    assert isinstance(records, list) and len(records) == 50
    expected_keys = (
        "sample_index_row_id", "pdb_id", "ligand_comp_id", "semantic_task_name",
        "eligibility_state", "authority_basis", "evidence_scope", "supporting_source_ids",
        "blocking_gap", "safe_next_use", "availability_mask_required",
        "current_runtime_consumer_available", "training_loss_authorized",
    )
    for index, sample in enumerate(gate.SAMPLES):
        block = records[index * 25:(index + 1) * 25]
        assert tuple(item["semantic_task_name"] for item in block) == gate.SEMANTIC_TASK_NAMES
        assert {item["sample_index_row_id"] for item in block} == {sample[0]}
    assert all(tuple(item) == expected_keys for item in records)
    assert all(item["availability_mask_required"] is True for item in records)
    assert all(item["current_runtime_consumer_available"] is False for item in records)
    assert all(item["training_loss_authorized"] is False for item in records)


@pytest.mark.parametrize("sample", (gate.SAMPLES[0][0], gate.SAMPLES[1][0]))
def test_common_sample_routing_matrix(response: dict[str, object], sample: str) -> None:
    expected = {
        "sample_identity_supervision": "admissible_now",
        "explicit_covalent_event_supervision": "admissible_now",
        "ligand_residue_atom_pair_supervision": "admissible_now",
        "warhead_boundary_supervision": "admissible_now",
        "observed_complex_geometry_supervision": "admissible_as_observed_geometry_only",
        "warhead_type_supervision": "candidate_only_not_authoritative",
        "reaction_family_supervision": "candidate_only_not_authoritative",
        "formed_edge_supervision": "candidate_only_not_authoritative",
        "leaving_group_supervision": "candidate_only_not_authoritative",
        "covalent_link_bond_order_supervision": "blocked_missing_evidence",
        "pre_covalent_geometry_supervision": "blocked_missing_evidence",
        "reaction_atom_map_supervision": "blocked_missing_evidence",
        "bond_order_delta_supervision": "blocked_missing_evidence",
        "formal_charge_delta_supervision": "blocked_missing_evidence",
        "protonation_transfer_supervision": "blocked_missing_evidence",
        "post_covalent_geometry_supervision": "blocked_state_ambiguity",
        "complete_post_state_graph_supervision": "blocked_state_ambiguity",
        "full_transformation_supervision": "blocked_state_ambiguity",
    }
    expected.update({
        task: "blocked_missing_human_approval"
        for task in gate.SEMANTIC_TASK_NAMES
        if task.startswith("canonical_mask_")
    })
    for task, state in expected.items():
        assert _record(response, sample, task)["eligibility_state"] == state


def test_sample_specific_broken_edge_and_reversibility(response: dict[str, object]) -> None:
    sample8, sample10 = gate.SAMPLES[0][0], gate.SAMPLES[1][0]
    assert _record(response, sample8, "broken_edge_supervision")["eligibility_state"] == (
        "candidate_only_not_authoritative"
    )
    assert _record(response, sample8, "reversibility_supervision")["eligibility_state"] == (
        "candidate_only_not_authoritative"
    )
    assert _record(response, sample10, "broken_edge_supervision")["eligibility_state"] == (
        "blocked_state_ambiguity"
    )
    assert _record(response, sample10, "reversibility_supervision")["eligibility_state"] == (
        "blocked_missing_evidence"
    )


def test_summary_exact_counts_and_checkpoint_impact(response: dict[str, object]) -> None:
    assert response["summary"] == {
        "sample_count": 2,
        "semantic_task_count": 25,
        "routing_record_count": 50,
        "admissible_now_task_sample_pair_count": 8,
        "observed_geometry_only_task_sample_pair_count": 2,
        "candidate_only_task_sample_pair_count": 10,
        "blocked_missing_evidence_task_sample_pair_count": 13,
        "blocked_state_ambiguity_task_sample_pair_count": 7,
        "blocked_missing_human_approval_task_sample_pair_count": 10,
        "not_applicable_task_sample_pair_count": 0,
        "explicit_pair_supervision_admissible": True,
        "link_bond_order_supervision_admissible": False,
        "observed_complex_geometry_admissible": True,
        "pre_covalent_geometry_supervision_admissible": False,
        "normalized_post_covalent_geometry_supervision_admissible": False,
        "full_post_state_supervision_admissible": False,
        "full_transformation_supervision_admissible": False,
        "canonical_mask_exact5_preserved": True,
        "current_runtime_consumer_available": False,
        "training_loss_authorized": False,
        "checkpoint_compatibility_impact": "none_metadata_only_gate",
    }


def test_canonical_exact5_order_and_b3(response: dict[str, object]) -> None:
    assert response["canonical_mask_semantics"] == [
        {"semantic_name": "warhead_only", "display_alias": "A"},
        {"semantic_name": "linker_plus_warhead", "display_alias": "B"},
        {"semantic_name": "scaffold_plus_warhead", "display_alias": "B2"},
        {"semantic_name": "scaffold_only", "display_alias": "B3"},
        {"semantic_name": "scaffold_plus_linker_plus_warhead", "display_alias": "C"},
    ]


def test_direct_source_bindings_and_scope_projection(response: dict[str, object]) -> None:
    bindings = response["source_bindings"]
    assert isinstance(bindings, dict)
    direct = bindings["direct_evidence_validation"]
    assert direct["struct_conn_value_order"] == {
        gate.SAMPLES[0][0]: "?",
        gate.SAMPLES[1][0]: "?",
    }
    assert direct["pair_and_observed_geometry"][gate.SAMPLES[0][0]] == {
        "explicit_bond_authority_class": "validated_struct_conn",
        "exact_one_mapping_role_count": 2,
        "distance_angstrom": "1.799",
        "distance_authority_scope": "observed_complex_geometry_only",
    }
    assert direct["pair_and_observed_geometry"][gate.SAMPLES[1][0]]["distance_angstrom"] == (
        "1.794"
    )
    assert all(
        item["reviewed_boundary_record_count"] == 2
        and item["complete_primary_role_partition_available"] is False
        for item in direct["boundary_authority"].values()
    )
    projection = direct["literature_scope_projection"]
    assert projection == {
        "class_scope_potential_leaving_group_evidence_found": True,
        "compound4_solution_release_product_evidence_found": True,
        "crystallographic_leaving_group_contract_supported": False,
        "complete_leaving_group_contract_supported": False,
        "compound4_apparent_irreversibility_evidence_found": True,
        "compound4_definitive_irreversibility_supported": False,
        "compound4_slow_release_uncertainty_present": True,
        "compound8_reversibility_evidence_found": False,
        "complete_reversibility_contract_supported": False,
    }


def test_blank_missing_semantics_remain_distinct(response: dict[str, object]) -> None:
    worklist = response["source_bindings"]["direct_evidence_validation"][
        "formal_transformation_worklist"
    ]
    assert worklist["future_nonblank_count"] == 0
    assert worklist["missing_semantics"] == (
        "blank_not_empty_list_not_not_claimed_not_false_not_negative_label"
    )


def test_readiness_is_fail_closed(response: dict[str, object]) -> None:
    assert response["readiness"] == {
        "partial_supervision_routing_gate_implemented": True,
        "evidence_level_partial_supervision_routes_available": True,
        "runtime_partial_supervision_consumer_available": False,
        "training_loss_authorized": False,
        "repository_schema_changed": False,
        "formal_worklist_modified": False,
        "formal_dossier_modified": False,
        "authority_changed": False,
        "tensor_materialized": False,
        "model_changed": False,
        "training_performed": False,
        "ready_for_partial_supervision_gate_validation": True,
        "ready_for_partial_supervision_tensor_materialization": False,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_formal_worklist_update": False,
        "ready_for_semantic_validation": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
    }


def test_cli_double_run_is_canonical_deterministic_and_read_only() -> None:
    before = _source_snapshot()
    command = (
        sys.executable, "-B", str(SCRIPT), "--repo-root", str(ROOT),
        "--state-root", str(STATE_ROOT),
    )
    runs = [subprocess.run(command, cwd=ROOT, capture_output=True, check=False) for _ in range(2)]
    assert [run.returncode for run in runs] == [0, 0]
    assert runs[0].stderr == runs[1].stderr == b""
    assert runs[0].stdout == runs[1].stdout
    assert runs[0].stdout.endswith(b"\n") and runs[0].stdout.count(b"\n") == 1
    decoded = json.loads(runs[0].stdout)
    assert runs[0].stdout == (
        json.dumps(decoded, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n"
    ).encode("ascii")
    assert before == _source_snapshot()


@pytest.mark.parametrize(
    "arguments",
    (
        (),
        ("--repo-root", str(ROOT)),
        ("--state-root", str(STATE_ROOT)),
        ("--repo-root", str(ROOT), "--state-root", str(STATE_ROOT), "--write"),
        ("--output-dir", str(ROOT)),
        ("--materialize",),
        ("--approve",),
        ("--train",),
    ),
)
def test_cli_fails_closed_with_unified_token(arguments: tuple[str, ...]) -> None:
    completed = subprocess.run(
        (sys.executable, "-B", str(SCRIPT), *arguments),
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1
    assert completed.stdout == b""
    assert gate.ERROR_TOKEN.encode("ascii") in completed.stderr


def test_failure_distance_only_pair_is_not_authority() -> None:
    repository, _state = _payloads()
    repository["canonical_pair_matrix"] = _mutate_csv(
        repository["canonical_pair_matrix"], 7, "explicit_bond_authority_class", "distance_only"
    )
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_pair_evidence(repository)


def test_failure_candidate_single_cannot_authorize_link_bond_order(response: dict[str, object]) -> None:
    mutated = copy.deepcopy(response)
    record = _record(mutated, gate.SAMPLES[0][0], "covalent_link_bond_order_supervision")
    record["eligibility_state"] = "admissible_now"
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_output_contract(mutated)


def test_failure_struct_conn_unknown_order_drift() -> None:
    repository, _state = _payloads()
    payload = repository["mmcif_1ayu"].replace(
        b"1.799 ? ? \n", b"1.799 sing ? \n", 1
    )
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_struct_conn(payload, ligand="INA", distance="1.799")


def test_failure_pair_authority_drift() -> None:
    repository, _state = _payloads()
    repository["canonical_pair_matrix"] = _mutate_csv(
        repository["canonical_pair_matrix"], 9, "explicit_bond_authority_class", "candidate"
    )
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_pair_evidence(repository)


@pytest.mark.parametrize("value", ("0", "2"))
def test_failure_exact_one_mapping_missing_or_duplicate(value: str) -> None:
    repository, _state = _payloads()
    repository["atom_table_mapping_matrix"] = _mutate_csv(
        repository["atom_table_mapping_matrix"], 14, "candidate_match_count", value
    )
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_pair_evidence(repository)


def test_failure_observed_distance_cannot_upgrade_post_geometry(response: dict[str, object]) -> None:
    mutated = copy.deepcopy(response)
    record = _record(mutated, gate.SAMPLES[0][0], "post_covalent_geometry_supervision")
    record["eligibility_state"] = "admissible_as_observed_geometry_only"
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_output_contract(mutated)


@pytest.mark.parametrize("replacement", ("[]", "not_claimed"))
def test_failure_blank_cannot_become_empty_or_not_claimed(replacement: str) -> None:
    _repository, state = _payloads()
    mutated = _mutate_csv(
        state["formal_transformation_worklist"], 0, "reviewed_broken_edges_json", replacement
    )
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_transformation_worklist(mutated)


def test_failure_compound4_evidence_cannot_propagate_to_compound8() -> None:
    _repository, state = _payloads()
    _fields, rows = gate._csv_rows(state["primary_source_inventory"])
    index = next(i for i, row in enumerate(rows) if row["evidence_id"] == "PL-E018")
    mutated = _mutate_csv(state["primary_source_inventory"], index, "compound_id", "8")
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_literature(state["primary_source_manifest"], mutated)


def test_failure_class_scope_cannot_become_sample_complete() -> None:
    _repository, state = _payloads()
    _fields, rows = gate._csv_rows(state["primary_source_inventory"])
    index = next(i for i, row in enumerate(rows) if row["evidence_id"] == "PL-E023")
    mutated = _mutate_csv(state["primary_source_inventory"], index, "sample_specific", "true")
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_literature(state["primary_source_manifest"], mutated)


def test_failure_solution_and_crystal_states_cannot_merge() -> None:
    _repository, state = _payloads()
    _fields, rows = gate._csv_rows(state["primary_source_inventory"])
    index = next(i for i, row in enumerate(rows) if row["evidence_id"] == "PL-E020")
    mutated = _mutate_csv(
        state["primary_source_inventory"], index, "state_scope", "crystallographic_sample"
    )
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_literature(state["primary_source_manifest"], mutated)


def test_failure_boundary_cardinality_drift() -> None:
    _repository, state = _payloads()
    value = json.loads(state["unified_boundary_authority"])
    record = next(
        row for row in value["effective_authority_records"]
        if row["sample_index_row_id"] == gate.SAMPLES[0][0]
    )
    record["effective_boundary_cardinality"] = 1
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_boundary_authority(json.dumps(value).encode("utf-8"))


def test_failure_candidate_family_cannot_upgrade_to_authority() -> None:
    repository, _state = _payloads()
    mutated = _mutate_csv(
        repository["candidate_family_assignments"], 7, "review_status", "approved"
    )
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_candidate_assignments(mutated)


def test_failure_b3_missing() -> None:
    repository, _state = _payloads()
    fields, rows = gate._csv_rows(repository["canonical_mask_truth_table"])
    rows.pop(3)
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_masks(stream.getvalue().encode("utf-8"))


def test_failure_sixth_mask() -> None:
    repository, _state = _payloads()
    fields, rows = gate._csv_rows(repository["canonical_mask_truth_table"])
    extra = dict(rows[-1])
    extra.update({"task_id": "5", "semantic_name": "forbidden_sixth", "display_alias": "D"})
    rows.append(extra)
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_masks(stream.getvalue().encode("utf-8"))


def test_failure_global_eligibility_cannot_replace_task_matrix(response: dict[str, object]) -> None:
    mutated = copy.deepcopy(response)
    mutated["routing_records"] = []
    mutated["samples"][0]["eligible"] = True
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_output_contract(mutated)


def test_failure_missing_task(response: dict[str, object]) -> None:
    mutated = copy.deepcopy(response)
    mutated["routing_records"].pop(4)
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_output_contract(mutated)


def test_failure_duplicate_task(response: dict[str, object]) -> None:
    mutated = copy.deepcopy(response)
    mutated["routing_records"][4] = copy.deepcopy(mutated["routing_records"][3])
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_output_contract(mutated)


def test_failure_twenty_sixth_task(response: dict[str, object]) -> None:
    mutated = copy.deepcopy(response)
    extra = copy.deepcopy(mutated["routing_records"][0])
    extra["semantic_task_name"] = "forbidden_twenty_sixth_task"
    mutated["routing_records"].insert(25, extra)
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_output_contract(mutated)


def test_failure_illegal_eligibility_state(response: dict[str, object]) -> None:
    mutated = copy.deepcopy(response)
    mutated["routing_records"][0]["eligibility_state"] = "unknown"
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_output_contract(mutated)


def test_failure_source_sha_drift() -> None:
    relative, _digest = gate.REPO_SOURCES["canonical_pair_matrix"]
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._read_frozen(ROOT, relative, "0" * 64)


def test_failure_filled_formal_worklist() -> None:
    _repository, state = _payloads()
    mutated = _mutate_csv(
        state["formal_transformation_worklist"], 0,
        "reviewed_transformation_version", "unauthorized_v1",
    )
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_transformation_worklist(mutated)


@pytest.mark.parametrize(
    "field",
    ("current_runtime_consumer_available", "training_loss_authorized"),
)
def test_failure_runtime_or_training_authorization_true(
    response: dict[str, object], field: str,
) -> None:
    mutated = copy.deepcopy(response)
    mutated["routing_records"][0][field] = True
    with pytest.raises(ValueError, match=gate.ERROR_TOKEN):
        gate._validate_output_contract(mutated)


def test_current_repository_matches_current_lifecycle() -> None:
    facts = gate._collect_lifecycle(ROOT)
    lifecycle = gate._derive_lifecycle(facts)
    assert lifecycle["lifecycle_profile"] in {
        "partial_supervision_routing_gate_precommit_candidate",
        "partial_supervision_routing_gate_committed_unpushed",
        "partial_supervision_routing_gate_published_successor",
    }
    assert facts["branch"] == "main"
    assert facts["base_ancestor_head"] is facts["base_ancestor_origin"] is True
    if lifecycle["lifecycle_profile"].endswith("precommit_candidate"):
        assert facts["head"] == facts["origin"] == gate.BASE_COMMIT
        assert facts["untracked"] == gate.CANDIDATE_PATHS
    elif lifecycle["lifecycle_profile"].endswith("committed_unpushed"):
        assert facts["head"] == lifecycle["formal_candidate_commit"]
        assert facts["origin"] == gate.BASE_COMMIT
        assert (facts["ahead"], facts["behind"]) == (1, 0)
    else:
        assert lifecycle["formal_candidate_commit"]


def test_lifecycle_exact3_in_base_anchored_temporary_git(
    tmp_path: Path,
    request: pytest.FixtureRequest,
) -> None:
    repository = tmp_path / ROOT.name
    node = f"{gate.TEST_PATH}::test_current_repository_matches_current_lifecycle"

    def cleanup() -> None:
        if repository.exists():
            shutil.rmtree(repository)

    request.addfinalizer(cleanup)
    subprocess.run(
        ("git", "clone", "--no-hardlinks", "--quiet", str(ROOT), str(repository)),
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    def git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ("git", *arguments), cwd=repository, check=check,
            capture_output=True, text=True,
        )

    def run_node() -> None:
        completed = subprocess.run(
            (
                sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", node,
            ),
            cwd=repository,
            env={**os.environ, "PYTHONPATH": "src", "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert "1 passed" in completed.stdout

    git("checkout", "-B", "main", gate.BASE_COMMIT)
    git("update-ref", "refs/remotes/origin/main", gate.BASE_COMMIT)
    for relative in gate.CANDIDATE_PATHS:
        assert git("cat-file", "-e", f"{gate.BASE_COMMIT}:{relative}", check=False).returncode != 0
        target = repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
        os.chmod(target, 0o644)
    run_node()

    git("add", "--", *gate.CANDIDATE_PATHS)
    git(
        "-c", "user.name=CovaPIE Test", "-c", "user.email=test@example.invalid",
        "commit", "--quiet", "-m", gate.FORMAL_COMMIT_SUBJECT,
    )
    formal = git("rev-parse", "HEAD").stdout.strip()
    assert git("show", "-s", "--format=%P", formal).stdout.split() == [gate.BASE_COMMIT]
    run_node()

    git("update-ref", "refs/remotes/origin/main", formal)
    unrelated = repository / "UNRELATED_PARTIAL_SUPERVISION_SUCCESSOR.txt"
    unrelated.write_text("unrelated successor\n", encoding="utf-8")
    os.chmod(unrelated, 0o644)
    git("add", "--", unrelated.name)
    git(
        "-c", "user.name=CovaPIE Test", "-c", "user.email=test@example.invalid",
        "commit", "--quiet", "-m", "unrelated partial supervision successor",
    )
    successor = git("rev-parse", "HEAD").stdout.strip()
    git("update-ref", "refs/remotes/origin/main", successor)
    run_node()
    cleanup()
    assert not os.path.lexists(repository)


def test_candidate_exact4_file_safety() -> None:
    assert len(gate.CANDIDATE_PATHS) == 4
    forbidden_suffixes = (
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
        ".npz", ".tmp", ".part",
    )
    for relative in gate.CANDIDATE_PATHS:
        path = ROOT / relative
        metadata = path.lstat()
        payload = path.read_bytes()
        assert stat.S_ISREG(metadata.st_mode) and not path.is_symlink()
        assert stat.S_IMODE(metadata.st_mode) == 0o644
        assert len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf")
        assert b"\0" not in payload
        payload.decode("utf-8")
        assert not relative.lower().endswith(forbidden_suffixes)
