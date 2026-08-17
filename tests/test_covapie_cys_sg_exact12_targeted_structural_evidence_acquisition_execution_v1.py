from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from covalent_ext import (
    covapie_cys_sg_exact12_targeted_structural_evidence_acquisition_execution_v1
    as execution,
)


def _synthetic_mmcif(pdb_id: str, *, element: str = "C") -> bytes:
    return f"""\
data_{pdb_id}
#
loop_
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_comp_id
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
1 {element} C1 LIG 0.0 0.0 0.0
#
""".encode("utf-8")


@pytest.fixture(scope="module")
def authority() -> execution.PublishedAuthority:
    return execution.load_and_validate_published_authority_v1()


def _request(authority: execution.PublishedAuthority, index: int = 0) -> dict[str, str]:
    return dict(authority.request_rows[index])


def _transport(payload: bytes, *, status: int = 200, final_url: str | None = None):
    calls: list[tuple[str, int]] = []

    def call(url: str, timeout: int) -> execution.TransportResponse:
        calls.append((url, timeout))
        return execution.TransportResponse(payload, status, final_url or url)

    return call, calls


def test_published_commit_three_artifact_hashes_and_owner_binding(
    authority: execution.PublishedAuthority,
) -> None:
    execution.validate_published_git_identity_v1()
    assert execution.BASELINE_COMMIT == execution.PUBLISHED_AUTHORITY_COMMIT == (
        "988348892a7d08fc3d420821c55b192bbcd99254"
    )
    for path, expected in execution.PUBLISHED_AUTHORITY_SHA256.items():
        assert hashlib.sha256((execution.REPO_ROOT / path).read_bytes()).hexdigest() == expected
    assert hashlib.sha256(
        (execution.REPO_ROOT / execution.AUTHORITY_SOURCE_PATH).read_bytes()
    ).hexdigest() == execution.PUBLISHED_AUTHORITY_SOURCE_SHA256
    assert authority.manifest["targeted_download_authorized_for_exact12"] is True
    assert authority.manifest["ready_for_exact12_acquisition_execution"] is True
    assert authority.manifest["blocked_count"] == 0


def test_successor_runtime_does_not_consult_exact_live_head_or_origin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, ...]] = []

    def successor_safe_git(
        repo_root: Path, args: tuple[str, ...] | list[str],
    ) -> subprocess.CompletedProcess[str]:
        command = tuple(args)
        calls.append(command)
        forbidden = {
            ("rev-parse", "HEAD"),
            ("rev-parse", "refs/remotes/origin/main"),
            (
                "rev-list", "--left-right", "--count",
                "HEAD...refs/remotes/origin/main",
            ),
        }
        if command in forbidden:
            raise AssertionError(f"live authority consulted: {command!r}")
        assert command == ("diff", "--cached", "--name-only")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(execution, "_run_git", successor_safe_git)
    execution.validate_published_git_identity_v1(tmp_path)
    assert calls == [("diff", "--cached", "--name-only")]


def test_successor_runtime_still_fails_closed_on_staged_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def staged_git(
        repo_root: Path, args: tuple[str, ...] | list[str],
    ) -> subprocess.CompletedProcess[str]:
        assert tuple(args) == ("diff", "--cached", "--name-only")
        return subprocess.CompletedProcess(
            args, 0, stdout="candidate.py\n", stderr="",
        )

    monkeypatch.setattr(execution, "_run_git", staged_git)
    with pytest.raises(
        execution.ExecutionValidationError,
        match="EXACT12_EXECUTION_STAGED_INDEX_NOT_EMPTY",
    ):
        execution.validate_published_git_identity_v1(tmp_path)


def test_exact12_cardinality_membership_and_request_identity(
    authority: execution.PublishedAuthority,
) -> None:
    identities = tuple(
        (row["pdb_id"], row["expected_ligand_component_id"])
        for row in authority.request_rows
    )
    assert identities == execution.authority_owner.EXACT_IDENTITIES
    assert len(authority.request_rows) == len({row["pdb_id"] for row in authority.request_rows}) == 12
    for row in authority.request_rows:
        pdb_id = row["pdb_id"]
        assert row["source_request_identity"] == (
            f"https://files.rcsb.org/download/{pdb_id}.cif"
        )
        assert row["destination_identity"] == (
            "data/raw/covalent_sources/covpdb/"
            f"future_struct_conn_crosscheck_raw_v0/{pdb_id.lower()}.cif"
        )


def test_import_performs_no_network_or_write(tmp_path: Path) -> None:
    module = (
        "covalent_ext."
        "covapie_cys_sg_exact12_targeted_structural_evidence_"
        "acquisition_execution_v1"
    )
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = os.pathsep.join((
        str(execution.REPO_ROOT), str(execution.REPO_ROOT / "src"),
    ))
    result = subprocess.run(
        (sys.executable, "-c", f"import {module}"), cwd=tmp_path, env=env,
        check=False, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
    assert list(tmp_path.iterdir()) == []


def test_valid_payload_uses_published_atom_site_parser() -> None:
    result = execution.validate_raw_mmcif_payload_v1(
        _synthetic_mmcif("1A54"), "1A54",
    )
    assert result.valid is True
    assert result.data_block_identity == "1A54"
    assert result.pdb_identity_matches is True
    assert result.atom_site_parseable is True
    assert result.atom_site_row_count == 1
    assert result.size_bytes > 0 and len(result.sha256) == 64
    assert execution.ATOM_SITE_PARSER_OWNER.endswith(
        "#extract_atom_site_loop_rows_v0"
    )


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        (_synthetic_mmcif("2DJF"), "MMCIF_PDB_IDENTITY_MISMATCH"),
        (b"<!doctype html><html><body>404</body></html>", "HTML_OR_ERROR_PAYLOAD"),
        (b"", "EMPTY_PAYLOAD"),
        (b"data_1A54\n_entry.id 1A54\n", "ATOM_SITE_MISSING_UNPARSEABLE_OR_EMPTY"),
        (
            b"data_1A54\nloop_\n_atom_site.Cartn_x\n_atom_site.Cartn_y\n"
            b"_atom_site.Cartn_z\n1 2\n#\n",
            "ATOM_SITE_MISSING_UNPARSEABLE_OR_EMPTY",
        ),
    ],
)
def test_wrong_html_empty_and_missing_or_unparseable_atom_site_rejected(
    payload: bytes, code: str,
) -> None:
    result = execution.validate_raw_mmcif_payload_v1(payload, "1A54")
    assert result.valid is False
    assert result.failure_code == code


def test_existing_valid_is_reused_with_zero_network(
    authority: execution.PublishedAuthority, tmp_path: Path,
) -> None:
    request = _request(authority)
    final = tmp_path / request["destination_identity"]
    final.parent.mkdir(parents=True)
    final.write_bytes(_synthetic_mmcif(request["pdb_id"]))

    def forbidden(url: str, timeout: int) -> execution.TransportResponse:
        raise AssertionError((url, timeout))

    record = execution._execute_request_v1(
        request, repo_root=tmp_path, transport=forbidden,
    )
    assert record["pre_execution_file_status"] == "EXISTING_VALID"
    assert record["action_taken"] == "REUSED_EXISTING_VALID"
    assert record["network_attempted"] is False
    assert record["network_attempt_count"] == 0
    assert record["final_atom_site_parseable"] is True
    assert record["acquisition_status"] == "VALID"


def test_existing_invalid_fails_closed_without_overwrite_or_network(
    authority: execution.PublishedAuthority, tmp_path: Path,
) -> None:
    request = _request(authority)
    final = tmp_path / request["destination_identity"]
    final.parent.mkdir(parents=True)
    original = b"not a structure\n"
    final.write_bytes(original)

    def forbidden(url: str, timeout: int) -> execution.TransportResponse:
        raise AssertionError((url, timeout))

    record = execution._execute_request_v1(
        request, repo_root=tmp_path, transport=forbidden,
    )
    assert record["pre_execution_file_status"] == "EXISTING_INVALID"
    assert record["action_taken"] == "FAILED_EXISTING_INVALID_NO_OVERWRITE"
    assert record["network_attempted"] is False
    assert final.read_bytes() == original


def test_new_valid_payload_is_verified_before_atomic_replace(
    authority: execution.PublishedAuthority, tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request(authority)
    payload = _synthetic_mmcif(request["pdb_id"])
    transport, calls = _transport(payload)
    events: list[str] = []
    original_validate = execution.validate_raw_mmcif_payload_v1
    original_replace = execution.os.replace

    def tracked_validate(data: bytes, pdb_id: str) -> execution.RawPayloadValidation:
        events.append("validate")
        return original_validate(data, pdb_id)

    def tracked_replace(source: os.PathLike[str], target: os.PathLike[str]) -> None:
        events.append("replace")
        original_replace(source, target)

    monkeypatch.setattr(execution, "validate_raw_mmcif_payload_v1", tracked_validate)
    monkeypatch.setattr(execution.os, "replace", tracked_replace)
    record = execution._execute_request_v1(
        request, repo_root=tmp_path, transport=transport,
    )
    final = tmp_path / request["destination_identity"]
    part = final.with_suffix(final.suffix + ".part")
    assert calls == [(request["source_request_identity"], 30)]
    assert events == ["validate", "replace", "validate"]
    assert record["part_verified_before_promotion"] is True
    assert record["atomic_promotion_performed"] is True
    assert record["final_sha256"] == record["part_sha256"]
    assert record["final_size_bytes"] == record["part_size_bytes"]
    assert final.read_bytes() == payload
    assert not part.exists()


def test_bad_payload_never_promotes_and_cleans_part(
    authority: execution.PublishedAuthority, tmp_path: Path,
) -> None:
    request = _request(authority)
    transport, calls = _transport(b"<html>error</html>")
    record = execution._execute_request_v1(
        request, repo_root=tmp_path, transport=transport,
    )
    final = tmp_path / request["destination_identity"]
    assert len(calls) == 1
    assert record["action_taken"] == "FAILED_DOWNLOADED_PAYLOAD_INVALID"
    assert record["primary_failure_code_or_NONE"] == "HTML_OR_ERROR_PAYLOAD"
    assert record["atomic_promotion_performed"] is False
    assert not final.exists()
    assert not final.with_suffix(final.suffix + ".part").exists()


def test_network_exception_has_one_attempt_and_no_part_leftover(
    authority: execution.PublishedAuthority, tmp_path: Path,
) -> None:
    request = _request(authority)
    calls: list[str] = []

    def failing(url: str, timeout: int) -> execution.TransportResponse:
        calls.append(url)
        raise execution.BoundedTransportError("TRANSPORT_TIMEOUT")

    record = execution._execute_request_v1(
        request, repo_root=tmp_path, transport=failing,
    )
    final = tmp_path / request["destination_identity"]
    assert calls == [request["source_request_identity"]]
    assert record["network_attempt_count"] == 1
    assert record["primary_failure_code_or_NONE"] == "TRANSPORT_TIMEOUT"
    assert not final.exists()
    assert not final.with_suffix(final.suffix + ".part").exists()


def test_cross_host_response_fails_closed_with_one_primary_attempt(
    authority: execution.PublishedAuthority, tmp_path: Path,
) -> None:
    request = _request(authority)
    transport, calls = _transport(
        _synthetic_mmcif(request["pdb_id"]),
        final_url="https://example.org/download/1A54.cif",
    )
    record = execution._execute_request_v1(
        request, repo_root=tmp_path, transport=transport,
    )
    assert len(calls) == record["network_attempt_count"] == 1
    assert record["primary_failure_code_or_NONE"] == (
        "CROSS_HOST_REDIRECT_FORBIDDEN"
    )
    assert not (tmp_path / request["destination_identity"]).exists()


def test_no_wildcard_dynamic_host_or_runtime_discovery(
    authority: execution.PublishedAuthority,
) -> None:
    assert len(authority.request_rows) == 12
    for row in authority.request_rows:
        source = urlsplit(row["source_request_identity"])
        assert source.scheme == "https"
        assert source.netloc == execution.SOURCE_HOST
        assert source.query == source.fragment == ""
        assert not any(token in row["source_request_identity"] for token in "*?[]")
        assert int(row["candidate_maximum_request_count"]) == 1


def test_1a54_historical_sha_mismatch_is_not_an_integrity_failure() -> None:
    payload = _synthetic_mmcif("1A54")
    assert hashlib.sha256(payload).hexdigest() != execution.HISTORICAL_1A54_RAW_SHA256
    result = execution.validate_raw_mmcif_payload_v1(payload, "1A54")
    assert result.valid is True


def _captured_rows(
    authority: execution.PublishedAuthority,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    records: list[dict[str, object]] = []
    recovery_rows: list[dict[str, object]] = []
    for request in authority.request_rows:
        payload = _synthetic_mmcif(request["pdb_id"])
        validation = execution.validate_raw_mmcif_payload_v1(
            payload, request["pdb_id"],
        )
        record = execution._base_execution_record(request)
        record.update({
            "pre_execution_file_status": "EXISTING_VALID",
            "action_taken": "REUSED_EXISTING_VALID",
            "request_status": "NOT_ATTEMPTED_REUSED_EXISTING_VALID",
            "response_or_transport_status": "NOT_APPLICABLE",
            "final_file_exists": True,
            "final_data_block_identity": validation.data_block_identity,
            "final_sha256": validation.sha256,
            "final_size_bytes": validation.size_bytes,
            "final_pdb_identity_matches": True,
            "final_atom_site_parseable": True,
            "final_atom_site_row_count": validation.atom_site_row_count,
            "final_atom_site_rh_present": False,
            "acquisition_status": "VALID",
        })
        records.append(record)
        recovery_rows.append({
            "canonical_candidate_id": request["canonical_candidate_id"],
            "pdb_id": request["pdb_id"],
            "ligand_component_id": request["expected_ligand_component_id"],
            "acquisition_status": "VALID",
            "local_raw_structure_found": True,
            "raw_sha256": validation.sha256,
            "explicit_connection_evidence_status": "STRUCT_CONN_LOOP_ABSENT",
            "cys_sg_event_recovered": False,
            "protein_chain_if_recovered": "NONE",
            "cys_residue_sequence_if_recovered": "NONE",
            "cys_insertion_code_if_recovered": "NONE",
            "reactive_residue_atom_if_recovered": "NONE",
            "ligand_chain_or_instance_if_recovered": "NONE",
            "reactive_ligand_atom_if_recovered": "NONE",
            "coordinate_status": "COORDINATE_EVIDENCE_INCOMPLETE",
            "ligand_component_identity_status": (
                "UNRESOLVED_NO_EXPLICIT_EXACT_EVENT"
            ),
            "structural_recovery_status": "STRUCT_CONN_EXACT_PAIR_MISSING",
            "recovery_disposition": "HUMAN_STRUCTURAL_REVIEW_REQUIRED",
            "primary_remaining_issue": "EXPLICIT_CONNECTION_EVIDENCE_REQUIRED",
        })
    return records, recovery_rows


def test_same_captured_records_serialize_and_materialize_byte_identically(
    authority: execution.PublishedAuthority, tmp_path: Path,
) -> None:
    records, recovery_rows = _captured_rows(authority)
    safety = execution.GitRawSafety(12, 0, 0, 0, True)
    first = execution.build_execution_artifacts_v1(records, recovery_rows, safety)
    second = execution.build_execution_artifacts_v1(records, recovery_rows, safety)
    assert first == second
    assert list(execution.deserialize_execution_records_v1(
        first[execution.EXECUTION_AUDIT_FILE]
    )) == records
    assert list(execution.deserialize_recovery_snapshot_v1(
        first[execution.RECOVERY_SNAPSHOT_FILE]
    )) == recovery_rows
    hashes, identical = execution.materialize_execution_artifacts_twice_v1(
        records, recovery_rows, safety, tmp_path,
    )
    assert identical is True
    assert set(hashes) == set(execution.OUTPUT_FILES)
    assert stat.S_IMODE(tmp_path.stat().st_mode) == 0o755
    for filename in execution.OUTPUT_FILES:
        assert (tmp_path / filename).read_bytes() == first[filename]
        assert stat.S_IMODE((tmp_path / filename).stat().st_mode) == 0o644


def test_manifest_records_no_geometry_model_or_training_side_effects(
    authority: execution.PublishedAuthority,
) -> None:
    records, recovery_rows = _captured_rows(authority)
    artifacts = execution.build_execution_artifacts_v1(
        records, recovery_rows, execution.GitRawSafety(12, 0, 0, 0, True),
    )
    manifest = json.loads(artifacts[execution.EXECUTION_MANIFEST_FILE])
    for field in (
        "bulk_acquisition_executed", "inverse_reaction_reconstruction_executed",
        "pre_geometry_generation_executed", "torsion_enumeration_executed",
        "mmff_executed", "uff_executed", "rdkit_minimization_executed",
        "geometry_executed", "model_forward", "backward", "optimizer_step",
        "trainer_fit", "training_executed", "rl",
    ):
        assert manifest[field] is False
    assert manifest["distance_only_inference_used"] is False
    assert manifest["ready_for_geometry_loss_activation"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["manifest_self_sha256_recorded"] is False
    assert manifest["formal_network_execution_owner_sha256"] == (
        execution.FORMAL_NETWORK_EXECUTION_OWNER_SHA256
    )
    assert manifest["formal_network_execution_reexecuted_after_runtime_repair"] is False
    assert manifest["successor_runtime_compatibility_repair_applied_after_capture"] is True
    assert manifest["published_successor_runtime_compatible"] is True
    assert manifest["live_head_exact_authority_required"] is False
    assert manifest["live_origin_main_exact_authority_required"] is False
    assert manifest["ahead_behind_exact_authority_required"] is False


def test_post_acquisition_remaining_issue_does_not_request_acquired_raw_again() -> None:
    recovered = {
        "cys_sg_event_recovered": False,
        "explicit_connection_evidence_status": "STRUCT_CONN_LOOP_ABSENT",
        "structural_recovery_status": "STRUCT_CONN_EXACT_PAIR_MISSING",
        "primary_remaining_issue": "RAW_MMCIF_REACQUISITION_REQUIRED",
    }
    issue = execution._post_acquisition_remaining_issue_v1(recovered, "1A54")
    assert issue == (
        "EXPLICIT_CONNECTION_AUTHORITY_ABSENT_IN_ACQUIRED_MMCIF_"
        "HUMAN_STRUCTURAL_REVIEW_REQUIRED"
    )
    assert "REACQUISITION" not in issue


def test_actual_captured_csvs_round_trip_and_rebuild_deterministically() -> None:
    output_root = execution.REPO_ROOT / execution.OUTPUT_ROOT
    execution_payload = (
        output_root / execution.EXECUTION_AUDIT_FILE
    ).read_bytes()
    recovery_payload = (
        output_root / execution.RECOVERY_SNAPSHOT_FILE
    ).read_bytes()
    execution_records = execution.deserialize_execution_records_v1(
        execution_payload,
    )
    recovery_records = execution.deserialize_recovery_snapshot_v1(
        recovery_payload,
    )
    assert execution._csv_bytes(
        execution_records, execution.EXECUTION_COLUMNS,
    ) == execution_payload
    assert execution._csv_bytes(
        recovery_records, execution.RECOVERY_COLUMNS,
    ) == recovery_payload
    safety = execution.GitRawSafety(12, 0, 0, 0, True)
    first = execution.build_execution_artifacts_v1(
        execution_records, recovery_records, safety,
    )
    second = execution.build_execution_artifacts_v1(
        execution_records, recovery_records, safety,
    )
    assert first == second
    assert first[execution.EXECUTION_AUDIT_FILE] == execution_payload
    assert first[execution.RECOVERY_SNAPSHOT_FILE] == recovery_payload
