from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
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
STATE_ROOT = ROOT.parent / "covapie-state"
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import covalent_ext.covapie_current11_reaction_transformation_evidence_overlay_contract_v1 as overlay  # noqa: E402


CHECKER = ROOT / overlay.CHECKER_PATH
SPEC = importlib.util.spec_from_file_location("transformation_overlay_checker_v1", CHECKER)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


def _csv(payload: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    return tuple(reader.fieldnames or ()), list(reader)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


_LIFECYCLE_SENSITIVE_NODES = (
    f"{overlay.TEST_PATH}::test_response_schema_order_and_exact_types",
    f"{overlay.TEST_PATH}::test_repository_candidate_matches_current_lifecycle",
)


def _git_text(repository: Path, *args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _is_lower_hex40(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 40
        and all(character in "0123456789abcdef" for character in value)
    )


def _assert_formal_candidate_commit(repository: Path, commit: str) -> None:
    assert _is_lower_hex40(commit)
    assert _git_text(repository, "show", "-s", "--format=%P", commit).split() == [
        overlay.BASE_COMMIT
    ]
    assert (
        _git_text(repository, "show", "-s", "--format=%s", commit)
        == overlay.FORMAL_COMMIT_SUBJECT
    )
    status_lines = _git_text(
        repository,
        "diff-tree",
        "--root",
        "--no-commit-id",
        "--name-status",
        "-r",
        commit,
    ).splitlines()
    statuses = {
        parts[1]: parts[0]
        for parts in (line.split("\t") for line in status_lines)
        if len(parts) == 2
    }
    assert tuple(sorted(statuses)) == overlay.CANDIDATE_PATHS
    assert statuses == {path: "A" for path in overlay.CANDIDATE_PATHS}
    for relative in overlay.CANDIDATE_PATHS:
        tree_metadata, tree_path = _git_text(
            repository, "ls-tree", commit, "--", relative
        ).split("\t", 1)
        tree_mode, tree_kind, commit_blob = tree_metadata.split()
        index_metadata, index_path = _git_text(
            repository, "ls-files", "--stage", "--", relative
        ).split("\t", 1)
        index_mode, index_blob, stage = index_metadata.split()
        worktree_blob = _git_text(
            repository, "hash-object", "--no-filters", "--", relative
        )
        assert tree_path == index_path == relative
        assert tree_mode == index_mode == "100644"
        assert tree_kind == "blob" and stage == "0"
        assert commit_blob == index_blob == worktree_blob


def _run_lifecycle_sensitive_nodes(repository: Path) -> None:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = "src"
    result = subprocess.run(
        (
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            *_LIFECYCLE_SENSITIVE_NODES,
        ),
        cwd=repository,
        env=environment,
        check=False,
        capture_output=True,
    )
    assert result.returncode == 0
    assert result.stderr == b""
    assert b"2 passed" in result.stdout


def _state_snapshot(path: Path) -> dict[str, object]:
    metadata = path.lstat()
    entries = tuple(sorted(path.iterdir(), key=lambda item: item.name))
    return {
        "identity": (metadata.st_dev, metadata.st_ino, stat.S_IMODE(metadata.st_mode)),
        "entries": tuple(item.name for item in entries),
        "sha256": {item.name: _sha(item.read_bytes()) for item in entries},
    }


@pytest.fixture(scope="module")
def response() -> dict[str, object]:
    return overlay.evaluate_covapie_current11_reaction_transformation_evidence_overlay_contract_v1(
        repo_root=ROOT,
        state_root=STATE_ROOT,
    )


def test_public_api_is_the_unique_keyword_only_api(response: dict[str, object]) -> None:
    public = [name for name in dir(overlay) if name.startswith("evaluate_covapie_")]
    assert public == [
        "evaluate_covapie_current11_reaction_transformation_evidence_overlay_contract_v1"
    ]
    signature = inspect.signature(
        overlay.evaluate_covapie_current11_reaction_transformation_evidence_overlay_contract_v1
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    with pytest.raises(TypeError):
        overlay.evaluate_covapie_current11_reaction_transformation_evidence_overlay_contract_v1(  # type: ignore[misc]
            ROOT, STATE_ROOT
        )
    assert response["schema_version"] == overlay.SCHEMA_VERSION


def test_public_api_is_deterministic_and_read_only(response: dict[str, object]) -> None:
    second = overlay.evaluate_covapie_current11_reaction_transformation_evidence_overlay_contract_v1(
        repo_root=ROOT,
        state_root=STATE_ROOT,
    )
    assert second == response


def test_import_is_silent_and_has_no_output_side_effect() -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(SRC)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        (
            sys.executable,
            "-c",
            "import covalent_ext.covapie_current11_reaction_transformation_evidence_overlay_contract_v1",
        ),
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
    )
    assert result.returncode == 0
    assert result.stdout == result.stderr == b""


def test_source_inventory_is_complete_sha_bound_and_verified() -> None:
    fields, rows = _csv((ROOT / overlay.SOURCE_INVENTORY_PATH).read_bytes())
    assert fields == overlay.SOURCE_INVENTORY_COLUMNS
    assert len(rows) == len(overlay.SOURCE_EVIDENCE)
    assert [row["evidence_id"] for row in rows] == [source.evidence_id for source in overlay.SOURCE_EVIDENCE]
    assert all(len(row["source_sha256"]) == 64 for row in rows)
    assert all(row["verified"] == "true" for row in rows)
    overlay._validate_source_inventory(ROOT, STATE_ROOT)


def test_source_inventory_covers_formal_review_package_exact9() -> None:
    _fields, rows = _csv((ROOT / overlay.SOURCE_INVENTORY_PATH).read_bytes())
    review_rows = [row for row in rows if row["evidence_id"].startswith("R")]
    assert len(review_rows) == 9
    assert {row["source_path"] for row in review_rows} == {
        path for _evidence_id, path, _digest in overlay.REVIEW_PACKAGE_EXACT9
    }
    assert all(row["source_commit_or_direct_producer"] == overlay.REVIEW_PACKAGE_COMMIT for row in review_rows)


def test_dossier_sources_are_non_authoritative_crosschecks_only() -> None:
    _fields, rows = _csv((ROOT / overlay.SOURCE_INVENTORY_PATH).read_bytes())
    dossier = [row for row in rows if row["source_namespace"] == "non_authoritative_state_aid"]
    assert len(dossier) == 6
    assert all(row["authority_scope"] == "non_authoritative_review_aid" for row in dossier)
    assert all(row["authoritative_for_transformation"] == "false" for row in dossier)
    assert all(row["lineage_note"] == "non_authoritative_human_review_aid_crosscheck" for row in dossier)


def test_authority_scopes_are_closed_and_post_authority_count_is_zero() -> None:
    _fields, rows = _csv((ROOT / overlay.SOURCE_INVENTORY_PATH).read_bytes())
    assert set(row["authority_scope"] for row in rows) <= set(overlay.AUTHORITY_SCOPES)
    assert sum(
        row["authority_scope"] == "formal_post_reaction_transformation_authority"
        for row in rows
    ) == 0
    assert all(row["authoritative_for_transformation"] == "false" for row in rows)


def test_exact41_field_order_is_frozen() -> None:
    fields, rows = _csv((ROOT / overlay.FIELD_CONTRACT_PATH).read_bytes())
    assert fields == overlay.FIELD_CONTRACT_COLUMNS
    assert len(rows) == len(overlay.ALL_FIELDS) == 41
    assert [row["field_order_0based"] for row in rows] == [str(index) for index in range(41)]
    assert [row["field_name"] for row in rows] == list(overlay.ALL_FIELDS)


def test_exact16_frozen_fields_have_derived_initial_values() -> None:
    _fields, rows = _csv((ROOT / overlay.FIELD_CONTRACT_PATH).read_bytes())
    frozen = rows[:16]
    assert [row["field_name"] for row in frozen] == list(overlay.FROZEN_FIELDS)
    assert all(row["frozen"] == "true" for row in frozen)
    assert all(row["human_or_authority_fillable"] == "false" for row in frozen)
    assert all(row["initial_value"] != "" for row in frozen)
    assert frozen[12]["initial_value"] == "4"
    assert frozen[13]["initial_value"] == "5"
    assert frozen[14]["initial_value"] == "absent"
    assert frozen[15]["initial_value"] == "true"


def test_exact25_future_fields_are_all_unfilled_and_not_prefilled() -> None:
    _fields, rows = _csv((ROOT / overlay.FIELD_CONTRACT_PATH).read_bytes())
    future = rows[16:]
    assert [row["field_name"] for row in future] == list(overlay.FUTURE_FIELDS)
    assert len(future) == 25
    assert all(row["frozen"] == "false" for row in future)
    assert all(row["human_or_authority_fillable"] == "true" for row in future)
    assert all(row["initial_value"] == "" for row in future)
    assert all(row["prefilled"] == "false" for row in future)
    assert all(row["current_coverage"] == "missing" for row in future)


def test_field_scopes_and_bool_attestation_vocabulary_are_closed() -> None:
    _fields, rows = _csv((ROOT / overlay.FIELD_CONTRACT_PATH).read_bytes())
    assert set(row["field_scope"] for row in rows) <= set(overlay.FIELD_SCOPES)
    by_name = {row["field_name"]: row for row in rows}
    for field in (
        "transformation_identity_explicitly_attested",
        "transformation_full_semantics_explicitly_attested",
        "review_completed",
    ):
        assert by_name[field]["allowed_values"] == "true;false"
        assert by_name[field]["initial_value"] == ""


def test_closed_decision_and_semantics_vocabularies() -> None:
    assert overlay.TRANSFORMATION_CLASSES == (
        "formed_bond_only",
        "formed_bond_plus_internal_bond_order_change",
        "formed_bond_plus_broken_bond",
        "formed_bond_plus_broken_and_bond_order_change",
        "other_explicit_graph_delta",
    )
    assert overlay.TRANSFORMATION_SCOPES == (
        "shared_exact2_sample_transformation",
        "sample_specific_transformations",
    )
    assert overlay.REVERSIBILITY_VALUES == ("reversible", "irreversible", "not_claimed")
    assert overlay.TRANSFORMATION_DECISIONS == (
        "approve_reaction_transformation_contract",
        "revise_reaction_transformation_contract",
        "quarantine_reaction_transformation_contract",
    )


def test_future_json_serialization_contract_is_canonical() -> None:
    value = {"samples": {overlay.SAMPLE_IDS[1]: [], overlay.SAMPLE_IDS[0]: []}}
    text = overlay._canonical_json_text(value)
    assert text == json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    )
    assert " " not in text


def test_atom_map_schema_supports_required_positive_map_records() -> None:
    schema = overlay.STRUCTURED_JSON_SCHEMAS["reviewed_atom_map_contract_json"]
    sample = schema["samples"]["<sample_id>"]
    assert set(sample) == {
        "target_residue_atom_map_number",
        "ligand_reactive_atom_map_number",
        "warhead_atom_map_numbers",
        "atom_records",
    }
    assert set(sample["atom_records"][0]) == {"map_number", "sample_atom_id", "element"}


def test_plural_attachment_schema_supports_exact_two_boundaries() -> None:
    schema = overlay.STRUCTURED_JSON_SCHEMAS[
        "reviewed_attachment_boundary_map_numbers_by_sample_json"
    ]
    records = schema["samples"]["<sample_id>"]
    assert len(records) == 2
    assert type(records[0]) is dict
    assert type(records[1]) is dict
    assert records[0] == records[1]
    expected_keys = (
        "warhead_attachment_atom_map_number",
        "nonwarhead_boundary_atom_map_number",
        "bond_order",
    )
    assert tuple(records[0]) == tuple(records[1]) == expected_keys
    assert not any(type(record) is str for record in records)
    frozen = json.loads(overlay._frozen_initial_values()["effective_attachment_boundaries_by_sample_json"])
    assert all(len(frozen["samples"][sample_id]) == 2 for sample_id in overlay.SAMPLE_IDS)


def test_atom_state_schema_supports_charge_and_nullable_hydrogen_count() -> None:
    schema = overlay.STRUCTURED_JSON_SCHEMAS[
        "reviewed_pre_or_post_atom_state_contract_json"
    ]
    record = schema["samples"]["<sample_id>"][0]
    assert set(record) == {
        "map_number",
        "element",
        "formal_charge",
        "explicit_hydrogen_count",
    }


def test_edge_and_change_schemas_use_map_number_endpoints() -> None:
    edge = overlay.STRUCTURED_JSON_SCHEMAS["reviewed_edge_list_json"]["samples"]["<sample_id>"][0]
    change = overlay.STRUCTURED_JSON_SCHEMAS["reviewed_bond_order_changes_json"]["samples"]["<sample_id>"][0]
    charge = overlay.STRUCTURED_JSON_SCHEMAS["reviewed_formal_charge_changes_json"]["samples"]["<sample_id>"][0]
    assert {"map_number_1", "map_number_2", "bond_order"} == set(edge)
    assert {"map_number_1", "map_number_2", "pre_bond_order", "post_bond_order"} == set(change)
    assert {"map_number", "pre_formal_charge", "post_formal_charge"} == set(charge)


def test_protonation_schema_distinguishes_attested_from_not_claimed() -> None:
    schema = overlay.STRUCTURED_JSON_SCHEMAS[
        "reviewed_protonation_transfer_contract_json"
    ]
    record = schema["samples"]["<sample_id>"]
    assert "explicitly_attested or not_claimed" in record["status"]
    assert "transfers" in record


def test_leaving_group_schema_is_explicit_and_map_number_based() -> None:
    schema = overlay.STRUCTURED_JSON_SCHEMAS[
        "reviewed_leaving_group_contract_json"
    ]
    sample = schema["samples"]["<sample_id>"]
    assert tuple(sample) == ("status", "leaving_group_records")
    assert sample["status"] == "<explicitly_attested or not_claimed>"
    assert type(sample["leaving_group_records"]) is list
    record = sample["leaving_group_records"][0]
    assert tuple(record) == ("leaving_atom_map_numbers", "broken_edge")
    assert record["leaving_atom_map_numbers"] == ["<positive int>"]
    assert tuple(record["broken_edge"]) == (
        "map_number_1",
        "map_number_2",
        "pre_bond_order",
    )
    assert all(
        type(value) is str and value.startswith("<") and value.endswith(">")
        for value in (
            *record["leaving_atom_map_numbers"],
            *record["broken_edge"].values(),
        )
    )


def test_missing_and_explicit_not_claimed_leaving_group_are_distinct() -> None:
    _fields, rows = _csv((ROOT / overlay.FIELD_CONTRACT_PATH).read_bytes())
    field = next(
        row for row in rows
        if row["field_name"] == "reviewed_leaving_group_contract_json"
    )
    unreviewed = field["initial_value"]
    explicit_not_claimed = overlay._canonical_json_text({
        "samples": {
            sample_id: {
                "status": "not_claimed",
                "leaving_group_records": [],
            }
            for sample_id in overlay.SAMPLE_IDS
        }
    })
    assert unreviewed == ""
    assert explicit_not_claimed != unreviewed
    parsed = json.loads(explicit_not_claimed)
    assert all(
        parsed["samples"][sample_id]
        == {"leaving_group_records": [], "status": "not_claimed"}
        for sample_id in overlay.SAMPLE_IDS
    )


def test_structured_schema_validator_rejects_string_attachment_placeholder() -> None:
    schemas = copy.deepcopy(overlay.STRUCTURED_JSON_SCHEMAS)
    schemas[
        "reviewed_attachment_boundary_map_numbers_by_sample_json"
    ]["samples"]["<sample_id>"][1] = "<exactly two records for UNIT_000001>"
    with pytest.raises(ValueError, match=overlay.ERROR):
        overlay._validate_structured_json_schema_contracts_v1(schemas)


def test_structured_schema_validator_rejects_missing_leaving_group_schema() -> None:
    schemas = copy.deepcopy(overlay.STRUCTURED_JSON_SCHEMAS)
    del schemas["reviewed_leaving_group_contract_json"]
    with pytest.raises(ValueError, match=overlay.ERROR):
        overlay._validate_structured_json_schema_contracts_v1(schemas)


def test_checker_independently_covers_structured_schema_contract() -> None:
    checker_source = inspect.getsource(checker._check_structured_schema_contract)
    assert "_validate_structured_json_schema_contracts_v1" not in checker_source
    assert "evaluate_covapie_" not in checker_source
    checker._check_structured_schema_contract(
        copy.deepcopy(overlay.STRUCTURED_JSON_SCHEMAS)
    )
    invalid = copy.deepcopy(overlay.STRUCTURED_JSON_SCHEMAS)
    invalid[
        "reviewed_attachment_boundary_map_numbers_by_sample_json"
    ]["samples"]["<sample_id>"][1] = "<old string placeholder>"
    with pytest.raises(ValueError, match=overlay.ERROR):
        checker._check_structured_schema_contract(invalid)


def test_exact2_gap_matrix_has_frozen_sample_identity() -> None:
    fields, rows = _csv((ROOT / overlay.GAP_MATRIX_PATH).read_bytes())
    assert fields == overlay.GAP_MATRIX_COLUMNS
    assert [row["sample_index_row_id"] for row in rows] == list(overlay.SAMPLE_IDS)
    assert [(row["pdb_id"], row["ligand_identity"]) for row in rows] == [
        ("1AYU", "INA"),
        ("1AYW", "IN3"),
    ]
    assert all(row["parent_review_unit_id"] == overlay.PARENT_REVIEW_UNIT_ID for row in rows)
    assert all(row["transformation_review_unit_id"] == overlay.TRANSFORMATION_REVIEW_UNIT_ID for row in rows)


def test_c21_and_cys_sg_identities_are_formally_crosschecked() -> None:
    _fields, rows = _csv((ROOT / overlay.GAP_MATRIX_PATH).read_bytes())
    assert all(row["ligand_reactive_atom_id"] == "C21" for row in rows)
    assert all(row["target_residue_atom"] == "CYS:SG" for row in rows)
    assert all(row["covalent_atom_pair_authority"] == "authoritative_resolved" for row in rows)


def test_pre_sum_four_and_conditional_sum_five_are_gap_signals_only() -> None:
    _fields, rows = _csv((ROOT / overlay.GAP_MATRIX_PATH).read_bytes())
    assert all(row["pre_reaction_center_bond_order_sum"] == "4" for row in rows)
    assert all(row["conditional_post_bond_order_sum_if_internal_bonds_unchanged"] == "5" for row in rows)
    manifest = json.loads((ROOT / overlay.MANIFEST_PATH).read_bytes())
    assert manifest["candidate_valence_ledger_is_gap_signal_only"] is True
    assert manifest["candidate_valence_ledger_is_reaction_authority"] is False


def test_no_post_reaction_authority_is_claimed() -> None:
    _fields, rows = _csv((ROOT / overlay.GAP_MATRIX_PATH).read_bytes())
    for row in rows:
        assert row["post_reaction_graph_authority"] == "missing"
        assert row["post_internal_bond_delta_authority"] == "missing"
        assert row["post_formal_charge_authority"] == "missing"
        assert row["post_protonation_authority"] == "missing"
        assert row["complete_rule_evidence_ready_for_human_decision"] == "false"


def test_singular_attachment_map_is_insufficient_for_exact2_boundaries() -> None:
    baseline = overlay._failure_baseline()
    assert baseline["future_contract"]["attachment_boundary_list_lengths"] == {
        sample_id: 2 for sample_id in overlay.SAMPLE_IDS
    }
    invalid = overlay._clone_json(baseline)
    overlay._apply_failure_mutation("X16", invalid)
    with pytest.raises(ValueError, match=overlay.ERROR):
        overlay._validate_failure_baseline(invalid)


def test_explicit_empty_list_differs_from_unreviewed_empty_string() -> None:
    explicit = overlay._canonical_json_text({
        "samples": {sample_id: [] for sample_id in overlay.SAMPLE_IDS}
    })
    assert overlay._reviewed_list_state(explicit) == "explicit_canonical_empty_list"
    assert overlay._reviewed_list_state("") == "unreviewed_empty_string"
    assert explicit != ""


def test_approved_smarts_and_approval_decision_are_not_generated() -> None:
    manifest = json.loads((ROOT / overlay.MANIFEST_PATH).read_bytes())
    assert manifest["approved_smarts_generated"] is False
    assert manifest["approval_decision_generated"] is False
    _fields, rows = _csv((ROOT / overlay.FIELD_CONTRACT_PATH).read_bytes())
    decision = next(row for row in rows if row["field_name"] == "transformation_review_decision")
    assert decision["initial_value"] == ""


def test_formal_worklist_and_authority_are_not_modified() -> None:
    manifest = json.loads((ROOT / overlay.MANIFEST_PATH).read_bytes())
    assert manifest["formal_worklist_modified"] is False
    assert manifest["authority_changed"] is False
    assert manifest["review_submission_compiled"] is False
    assert manifest["review_ingested"] is False
    assert manifest["authority_bundle_generated"] is False


def test_failure_registry_exact28_matches_specs() -> None:
    fields, rows = _csv((ROOT / overlay.FAILURE_MATRIX_PATH).read_bytes())
    assert fields == overlay.FAILURE_MATRIX_COLUMNS
    assert len(rows) == len(overlay.FAILURE_SPECS) == 28
    assert [row["case_id"] for row in rows] == [f"X{index:02d}" for index in range(1, 29)]
    assert [row["failure_case"] for row in rows] == [spec[1] for spec in overlay.FAILURE_SPECS]
    assert all(row["fails_closed"] == row["verified"] == "true" for row in rows)


@pytest.mark.parametrize("case_id", [f"X{index:02d}" for index in range(1, 29)])
def test_failure_mutations_exact28(case_id: str) -> None:
    baseline = overlay._failure_baseline()
    overlay._validate_failure_baseline(baseline)
    before = overlay._canonical_json_bytes(baseline)
    mutated = overlay._clone_json(baseline)
    overlay._apply_failure_mutation(case_id, mutated)
    after = overlay._canonical_json_bytes(mutated)
    assert before != after
    with pytest.raises(ValueError, match=overlay.ERROR):
        overlay._validate_failure_baseline(mutated)


def test_response_schema_order_and_exact_types(response: dict[str, object]) -> None:
    assert tuple(response) == overlay.RESPONSE_FIELDS
    assert all(type(response[field]) is int for field in overlay._RESPONSE_INT_FIELDS)
    assert all(type(response[field]) is bool for field in overlay._RESPONSE_BOOL_FIELDS)
    assert all(
        type(response[field]) is str
        for field in (
            "schema_version",
            "base_commit",
            "origin_main",
            "lifecycle_profile",
            "formal_candidate_commit",
            "response_sha256",
        )
    )
    assert type(response["artifact_sha256"]) is dict
    profile = response["lifecycle_profile"]
    formal_commit = response["formal_candidate_commit"]
    if profile == "transformation_overlay_precommit_candidate":
        assert formal_commit == ""
        assert response["origin_main"] == overlay.BASE_COMMIT
        assert (response["ahead"], response["behind"]) == (0, 0)
    elif profile == "transformation_overlay_committed_unpushed":
        assert _is_lower_hex40(formal_commit)
        assert formal_commit != overlay.BASE_COMMIT
        assert response["origin_main"] == overlay.BASE_COMMIT
        assert (response["ahead"], response["behind"]) == (1, 0)
    elif profile == "transformation_overlay_published_successor":
        assert _is_lower_hex40(formal_commit)
        assert formal_commit != overlay.BASE_COMMIT
    else:
        pytest.fail(f"unexpected lifecycle profile: {profile!r}")


def test_response_rejects_extra_or_missing_fields(response: dict[str, object]) -> None:
    lifecycle = {field: response[field] for field in overlay._LIFECYCLE_FIELDS}
    artifacts = response["artifact_sha256"]
    for invalid in (
        {**response, "extra": False},
        {key: value for key, value in response.items() if key != "gap_count"},
    ):
        with pytest.raises(ValueError, match=overlay.ERROR):
            overlay._validate_response(
                invalid,
                expected_lifecycle=lifecycle,
                expected_artifact_sha256=artifacts,
            )


def test_response_rejects_bool_as_int_and_rehashed_substitution(response: dict[str, object]) -> None:
    lifecycle = {field: response[field] for field in overlay._LIFECYCLE_FIELDS}
    artifacts = response["artifact_sha256"]
    invalid = dict(response)
    invalid["sample_count"] = True
    invalid["response_sha256"] = _sha(overlay._canonical_json_bytes({
        key: value for key, value in invalid.items() if key != "response_sha256"
    }))
    with pytest.raises(ValueError, match=overlay.ERROR):
        overlay._validate_response(
            invalid,
            expected_lifecycle=lifecycle,
            expected_artifact_sha256=artifacts,
        )


def test_response_rejects_valid_looking_lifecycle_witness_substitution(response: dict[str, object]) -> None:
    lifecycle = {field: response[field] for field in overlay._LIFECYCLE_FIELDS}
    invalid = dict(response)
    invalid["origin_main"] = "a" * 40
    invalid["response_sha256"] = _sha(overlay._canonical_json_bytes({
        key: value for key, value in invalid.items() if key != "response_sha256"
    }))
    with pytest.raises(ValueError, match=overlay.ERROR):
        overlay._validate_response(
            invalid,
            expected_lifecycle=lifecycle,
            expected_artifact_sha256=response["artifact_sha256"],
        )


def test_response_rejects_valid_looking_artifact_sha_witness_substitution(response: dict[str, object]) -> None:
    lifecycle = {field: response[field] for field in overlay._LIFECYCLE_FIELDS}
    invalid = copy.deepcopy(response)
    first = next(iter(invalid["artifact_sha256"]))
    invalid["artifact_sha256"][first] = "a" * 64
    invalid["response_sha256"] = _sha(overlay._canonical_json_bytes({
        key: value for key, value in invalid.items() if key != "response_sha256"
    }))
    with pytest.raises(ValueError, match=overlay.ERROR):
        overlay._validate_response(
            invalid,
            expected_lifecycle=lifecycle,
            expected_artifact_sha256=response["artifact_sha256"],
        )


def test_exact3_lifecycle_survives_real_temp_git_repository(tmp_path: Path) -> None:
    repository = tmp_path / "overlay-lifecycle"
    temporary_state = tmp_path / "covapie-state"
    subprocess.run(
        ("git", "clone", "--no-hardlinks", "--quiet", str(ROOT), str(repository)),
        check=True,
        capture_output=True,
    )
    temporary_state.symlink_to(STATE_ROOT.resolve(strict=True), target_is_directory=True)
    assert temporary_state.is_symlink()
    assert temporary_state.resolve(strict=True) == STATE_ROOT.resolve(strict=True)
    subprocess.run(
        ("git", "checkout", "-B", overlay.BRANCH, overlay.BASE_COMMIT),
        cwd=repository,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ("git", "update-ref", "refs/remotes/origin/main", overlay.BASE_COMMIT),
        cwd=repository,
        check=True,
        capture_output=True,
    )
    assert subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=repository, check=True,
        capture_output=True, text=True,
    ).stdout.strip() == overlay.BASE_COMMIT
    for relative in overlay.CANDIDATE_PATHS:
        assert subprocess.run(
            ("git", "cat-file", "-e", f"{overlay.BASE_COMMIT}:{relative}"),
            cwd=repository,
            check=False,
            capture_output=True,
        ).returncode != 0
        destination = repository / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
        os.chmod(destination, 0o644)
    precommit = overlay._derive_lifecycle(overlay._collect_lifecycle(repository))
    assert precommit["lifecycle_profile"] == "transformation_overlay_precommit_candidate"
    _run_lifecycle_sensitive_nodes(repository)

    subprocess.run(
        ("git", "add", "--", *overlay.CANDIDATE_PATHS),
        cwd=repository,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        (
            "git",
            "-c",
            "user.name=CovaPIE Test",
            "-c",
            "user.email=covapie-test@example.invalid",
            "commit",
            "-m",
            overlay.FORMAL_COMMIT_SUBJECT,
        ),
        cwd=repository,
        check=True,
        capture_output=True,
    )
    committed = overlay._derive_lifecycle(overlay._collect_lifecycle(repository))
    assert committed["lifecycle_profile"] == "transformation_overlay_committed_unpushed"
    formal_commit = committed["formal_candidate_commit"]
    assert _is_lower_hex40(formal_commit)
    assert isinstance(formal_commit, str)
    _run_lifecycle_sensitive_nodes(repository)

    subprocess.run(
        ("git", "update-ref", "refs/remotes/origin/main", formal_commit),
        cwd=repository,
        check=True,
        capture_output=True,
    )
    unrelated = repository / "UNRELATED_OVERLAY_SUCCESSOR.txt"
    unrelated.write_text("successor\n", encoding="utf-8")
    subprocess.run(
        ("git", "add", "--", unrelated.name), cwd=repository, check=True,
        capture_output=True,
    )
    subprocess.run(
        (
            "git", "-c", "user.name=CovaPIE Test",
            "-c", "user.email=covapie-test@example.invalid",
            "commit", "-m", "add unrelated overlay successor",
        ),
        cwd=repository,
        check=True,
        capture_output=True,
    )
    successor = subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=repository, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    subprocess.run(
        ("git", "update-ref", "refs/remotes/origin/main", successor),
        cwd=repository,
        check=True,
        capture_output=True,
    )
    published = overlay._derive_lifecycle(overlay._collect_lifecycle(repository))
    assert published["lifecycle_profile"] == "transformation_overlay_published_successor"
    assert published["formal_candidate_commit"] == formal_commit
    _run_lifecycle_sensitive_nodes(repository)

    temporary_state.unlink()
    shutil.rmtree(repository)
    assert not os.path.lexists(temporary_state)
    assert not repository.exists()


def test_checker_is_deterministic_on_two_consecutive_runs() -> None:
    command = (
        sys.executable,
        str(CHECKER),
        "--repo-root",
        str(ROOT),
        "--state-root",
        str(STATE_ROOT),
    )
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    first = subprocess.run(command, cwd=ROOT, env=environment, check=False, capture_output=True)
    second = subprocess.run(command, cwd=ROOT, env=environment, check=False, capture_output=True)
    assert (first.returncode, second.returncode) == (0, 0)
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout
    report = json.loads(first.stdout)
    assert report["failure_count"] == 28
    assert report["formal_post_reaction_authority_count"] == 0


def test_repository_candidate_matches_current_lifecycle(
    response: dict[str, object],
) -> None:
    assert _git_text(ROOT, "branch", "--show-current") == overlay.BRANCH
    head = _git_text(ROOT, "rev-parse", "HEAD")
    origin = _git_text(ROOT, "rev-parse", "refs/remotes/origin/main")
    ahead_text, behind_text = _git_text(
        ROOT,
        "rev-list",
        "--left-right",
        "--count",
        "HEAD...refs/remotes/origin/main",
    ).split()
    ahead, behind = int(ahead_text), int(behind_text)
    untracked = tuple(sorted(_git_text(
        ROOT, "ls-files", "--others", "--exclude-standard"
    ).splitlines()))
    worktree = tuple(sorted(_git_text(ROOT, "diff", "--name-only").splitlines()))
    staged = tuple(sorted(
        _git_text(ROOT, "diff", "--cached", "--name-only").splitlines()
    ))
    porcelain = tuple(sorted(_git_text(
        ROOT, "status", "--porcelain=v1", "--untracked-files=all"
    ).splitlines()))
    tracked_candidates = tuple(sorted(_git_text(
        ROOT, "ls-files", "--", *overlay.CANDIDATE_PATHS
    ).splitlines()))
    candidate_paths = set(overlay.CANDIDATE_PATHS)
    assert response["origin_main"] == origin
    assert (response["ahead"], response["behind"]) == (ahead, behind)
    assert not candidate_paths.intersection(worktree)
    assert not candidate_paths.intersection(staged)
    for relative in overlay.CANDIDATE_PATHS:
        path = ROOT / relative
        metadata = path.lstat()
        assert stat.S_ISREG(metadata.st_mode)
        assert not path.is_symlink()
        assert stat.S_IMODE(metadata.st_mode) == 0o644

    profile = response["lifecycle_profile"]
    formal_commit = response["formal_candidate_commit"]
    if profile == "transformation_overlay_precommit_candidate":
        assert head == origin == overlay.BASE_COMMIT
        assert (ahead, behind) == (0, 0)
        assert untracked == overlay.CANDIDATE_PATHS
        assert porcelain == tuple(sorted(
            f"?? {path}" for path in overlay.CANDIDATE_PATHS
        ))
        assert tracked_candidates == ()
        assert worktree == staged == ()
    elif profile == "transformation_overlay_committed_unpushed":
        assert isinstance(formal_commit, str)
        assert head == formal_commit
        assert origin == overlay.BASE_COMMIT
        assert (ahead, behind) == (1, 0)
        _assert_formal_candidate_commit(ROOT, formal_commit)
        assert tracked_candidates == overlay.CANDIDATE_PATHS
        assert untracked == worktree == staged == porcelain == ()
    elif profile == "transformation_overlay_published_successor":
        assert isinstance(formal_commit, str)
        _assert_formal_candidate_commit(ROOT, formal_commit)
        for descendant in (head, origin):
            result = subprocess.run(
                ("git", "merge-base", "--is-ancestor", formal_commit, descendant),
                cwd=ROOT,
                check=False,
                capture_output=True,
            )
            assert result.returncode == 0
            assert result.stdout == result.stderr == b""
        assert tracked_candidates == overlay.CANDIDATE_PATHS
        assert not candidate_paths.intersection(untracked)
    else:
        pytest.fail(f"unexpected lifecycle profile: {profile!r}")


def test_candidate_files_are_regular_0644_utf8_and_under_one_mib() -> None:
    for relative in overlay.CANDIDATE_PATHS:
        path = ROOT / relative
        metadata = path.lstat()
        payload = path.read_bytes()
        assert stat.S_ISREG(metadata.st_mode) and not path.is_symlink()
        assert stat.S_IMODE(metadata.st_mode) == 0o644
        assert 0 < len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf") and b"\x00" not in payload
        payload.decode("utf-8")


def test_forbidden_artifact_and_protected_source_safety() -> None:
    forbidden = (".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".tmp", ".part")
    assert all(not path.endswith(forbidden) for path in overlay.CANDIDATE_PATHS)
    assert all(not path.startswith("data/raw/") for path in overlay.CANDIDATE_PATHS)
    checker._check_safety(ROOT)


def test_source_has_no_raw_network_chemistry_model_or_training_execution() -> None:
    source = (ROOT / overlay.MODULE_PATH).read_text(encoding="utf-8").lower()
    forbidden_imports = (
        "import torch",
        "import rdkit",
        "import openbabel",
        "import requests",
        "import urllib",
        "import socket",
    )
    assert all(token not in source for token in forbidden_imports)
    assert "data/raw/" not in source
    assert "molfromsmarts" not in source
    assert "hassubstructmatch" not in source
    assert "reactionfromsmarts" not in source


def test_formal_workspace_is_unchanged_before_and_after_api_call() -> None:
    canonical = STATE_ROOT / "manual-review" / overlay.WORKSPACE_NAME
    object_directory = canonical.parent / overlay.WORKSPACE_TARGET
    before_link = (canonical.lstat().st_dev, canonical.lstat().st_ino, str(canonical.readlink()))
    before = _state_snapshot(object_directory)
    overlay.evaluate_covapie_current11_reaction_transformation_evidence_overlay_contract_v1(
        repo_root=ROOT, state_root=STATE_ROOT
    )
    after_link = (canonical.lstat().st_dev, canonical.lstat().st_ino, str(canonical.readlink()))
    after = _state_snapshot(object_directory)
    assert before_link == after_link
    assert before == after


def test_dossier_exact6_is_unchanged_before_and_after_api_call() -> None:
    dossier = STATE_ROOT / overlay.DOSSIER_RELATIVE
    before = _state_snapshot(dossier)
    overlay.evaluate_covapie_current11_reaction_transformation_evidence_overlay_contract_v1(
        repo_root=ROOT, state_root=STATE_ROOT
    )
    after = _state_snapshot(dossier)
    assert before == after


def test_manifest_binds_other_four_artifacts_but_not_itself() -> None:
    manifest = json.loads((ROOT / overlay.MANIFEST_PATH).read_bytes())
    assert set(manifest["evidence_sha256"]) == {
        Path(path).name for path in overlay.ARTIFACT_PATHS[:-1]
    }
    assert Path(overlay.MANIFEST_PATH).name not in manifest["evidence_sha256"]
    for relative in overlay.ARTIFACT_PATHS[:-1]:
        assert manifest["evidence_sha256"][Path(relative).name] == _sha(
            (ROOT / relative).read_bytes()
        )


def test_manifest_has_no_timestamp_or_machine_specific_absolute_path() -> None:
    payload = (ROOT / overlay.MANIFEST_PATH).read_text(encoding="utf-8")
    assert "timestamp" not in payload.lower()
    assert str(ROOT) not in payload
    assert str(STATE_ROOT) not in payload


def test_approval_fail_closed_invariants_are_exact28() -> None:
    assert len(overlay.APPROVAL_INVARIANTS) == 28
    assert len(set(overlay.APPROVAL_INVARIANTS)) == 28
    assert "conditional_center_bond_order_conflict_explicitly_resolved" in overlay.APPROVAL_INVARIANTS
    assert "approved_smarts_not_derived_from_candidate_graph" in overlay.APPROVAL_INVARIANTS


def test_training_boundary_and_feature_semantics_warning_remain_frozen(response: dict[str, object]) -> None:
    manifest = json.loads((ROOT / overlay.MANIFEST_PATH).read_bytes())
    assert response["training_used"] is False
    assert response["tensor_materialized"] is False
    assert response["model_changed"] is False
    assert response["feature_semantics_reaudit_required_before_training"] is True
    assert response["ready_for_training"] is False
    assert manifest["feature_semantics_reaudit_required_before_training"] is True
    assert manifest["ready_for_training"] is False
