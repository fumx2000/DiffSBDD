from __future__ import annotations

import ast
import copy
import csv
import hashlib
import io
import json
import socket
import stat
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_cys_sg_exact12_bounded_targeted_structural_evidence_acquisition_authority_v1
    as owner,
)


EXPECTED_IDENTITIES = [
    "1A54/MDC",
    "2DJF/1ZB",
    "6VWE/JY1",
    "2R9F/K2Z",
    "4DCD/K36",
    "6WTT/K36",
    "4F49/K36",
    "6L70/K36",
    "6WTJ/K36",
    "7C8U/K36",
    "5WKJ/K36",
    "6WTK/UED",
]


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _build() -> dict[str, bytes]:
    return owner.build_covapie_cys_sg_exact12_bounded_targeted_structural_evidence_acquisition_authority_v1()


def _manifest(artifacts: dict[str, bytes] | None = None) -> dict:
    built = artifacts or _build()
    return json.loads(built[owner.MANIFEST_FILE])


def _native_rows() -> tuple[list[dict], list[dict[str, str]]]:
    payloads = owner._read_bound_inputs(owner.REPO_ROOT)
    worklist = owner._validate_published_inputs(payloads)
    requests = [
        owner._expected_request_row(index, row)
        for index, row in enumerate(worklist, start=1)
    ]
    return requests, worklist


def test_published_b0_commit_and_artifact_sha_binding(monkeypatch) -> None:
    assert owner.BASELINE_COMMIT == owner.PUBLISHED_B0_COMMIT == (
        "43e1d476175b24d4a1c9ba21d68d5ac5d183303b"
    )
    for path, expected in owner.PUBLISHED_B0_SHA256.items():
        assert _sha256((owner.REPO_ROOT / path).read_bytes()) == expected
    assert owner.PUBLISHED_B0_SHA256[owner.B0_WORKLIST] == (
        "77c8a447a5c6098b1b834837ee345e03db6ea6b00c7af8a886fa9668585d22f4"
    )

    bad_hashes = dict(owner.PUBLISHED_B0_SHA256)
    bad_hashes[owner.B0_WORKLIST] = "0" * 64
    monkeypatch.setattr(owner, "PUBLISHED_B0_SHA256", bad_hashes)
    with pytest.raises(
        owner.AuthorityValidationError, match="EXACT12_SOURCE_SHA_MISMATCH"
    ):
        _build()


def test_exact12_identity_cardinality_order_uniqueness_and_no_wildcard() -> None:
    rows = _csv_rows(_build()[owner.REQUEST_FILE])
    identities = [
        f"{row['pdb_id']}/{row['expected_ligand_component_id']}" for row in rows
    ]
    assert identities == EXPECTED_IDENTITIES
    assert len(rows) == len({row["pdb_id"] for row in rows}) == 12
    assert [row["request_index"] for row in rows] == [str(i) for i in range(1, 13)]
    for row in rows:
        assert not any(
            token in row[field]
            for field in (
                "pdb_id", "source_request_identity", "destination_identity",
            )
            for token in ("*", "?", "[", "]")
        )
        assert row["candidate_maximum_request_count"] == "1"


def test_b0_request_identity_and_authorization_origins_are_truthful() -> None:
    worklist = _csv_rows((owner.REPO_ROOT / owner.B0_WORKLIST).read_bytes())
    requests = _csv_rows(_build()[owner.REQUEST_FILE])
    assert [row["canonical_candidate_id"] for row in requests] == [
        row["canonical_candidate_id"] for row in worklist
    ]
    assert [row["b0_worklist_item_id"] for row in requests] == [
        row["worklist_item_id"] for row in worklist
    ]
    assert {row["b0_worklist_sha256"] for row in requests} == {
        owner.PUBLISHED_B0_SHA256[owner.B0_WORKLIST]
    }
    assert requests[0]["authorization_origin"] == (
        "INHERITED_PUBLISHED_BOUNDED_AUTHORITY"
    )
    assert requests[0]["authorization_decision"] == (
        "INHERITED_AUTHORIZED_EXACT_TARGET"
    )
    assert {row["authorization_origin"] for row in requests[1:]} == {
        "NEW_EXACT12_SUCCESSOR_AUTHORITY"
    }
    assert {row["authorization_decision"] for row in requests[1:]} == {
        "AUTHORIZED_EXACT_TARGET"
    }


def test_source_endpoint_format_and_destination_follow_published_1a54() -> None:
    existing = _csv_rows((owner.REPO_ROOT / owner.EXISTING_REQUESTS).read_bytes())
    inherited = next(row for row in existing if row["pdb_id"] == "1A54")
    rows = _csv_rows(_build()[owner.REQUEST_FILE])
    assert inherited["rcsb_mmcif_url"] == rows[0]["source_request_identity"]
    assert inherited["expected_raw_relative_path"] == rows[0]["destination_identity"]
    assert {row["source_policy_id"] for row in rows} == {owner.SOURCE_POLICY_ID}
    assert {row["structure_format"] for row in rows} == {"MMCIF"}
    assert [row["source_request_identity"] for row in rows] == [
        f"https://files.rcsb.org/download/{identity.split('/')[0]}.cif"
        for identity in EXPECTED_IDENTITIES
    ]
    assert [row["destination_identity"] for row in rows] == [
        owner.DESTINATION_ROOT.joinpath(
            f"{identity.split('/')[0].lower()}.cif"
        ).as_posix()
        for identity in EXPECTED_IDENTITIES
    ]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda rows: rows[1].update(
                source_request_identity="https://example.invalid/download/2DJF.cif"
            ),
            "EXACT12_SOURCE_POLICY_INVALID",
        ),
        (
            lambda rows: rows[1].update(
                source_request_identity="https://files.rcsb.org/download/XXXX.cif"
            ),
            "EXACT12_SOURCE_POLICY_INVALID",
        ),
        (
            lambda rows: rows[1].update(expected_ligand_component_id="BAD"),
            "EXACT12_REQUEST_ROW_CONTRACT_MISMATCH",
        ),
        (
            lambda rows: rows[1].update(
                destination_identity=(
                    owner.DESTINATION_ROOT / ".." / "escaped.cif"
                ).as_posix()
            ),
            "EXACT12_DESTINATION_ESCAPES_APPROVED_ROOT",
        ),
        (
            lambda rows: rows[1].update(source_request_identity="*"),
            "EXACT12_WILDCARD_REQUEST_FORBIDDEN",
        ),
    ],
)
def test_invalid_source_identity_or_destination_fails_closed(
    mutation, message: str,
) -> None:
    rows, worklist = _native_rows()
    mutation(rows)
    with pytest.raises(owner.AuthorityValidationError, match=message):
        owner.validate_request_rows_v1(rows, worklist)


def test_duplicate_and_over_cardinality_requests_fail_closed() -> None:
    rows, worklist = _native_rows()
    duplicate = copy.deepcopy(rows)
    duplicate[1]["pdb_id"] = duplicate[0]["pdb_id"]
    with pytest.raises(
        owner.AuthorityValidationError, match="EXACT12_DUPLICATE_PDB_REQUEST"
    ):
        owner.validate_request_rows_v1(duplicate, worklist)

    expanded = copy.deepcopy(rows) + [copy.deepcopy(rows[-1])]
    with pytest.raises(
        owner.AuthorityValidationError, match="EXACT12_MAXIMUM_CARDINALITY_EXCEEDED"
    ):
        owner.validate_request_rows_v1(expanded, worklist + [worklist[-1]])


def test_bulk_boundaries_rh_boundary_and_k36_ued_separation() -> None:
    artifacts = _build()
    rows = _csv_rows(artifacts[owner.REQUEST_FILE])
    manifest = _manifest(artifacts)
    assert manifest["bulk_download_authorized"] is False
    assert manifest["targeted_download_authorized_for_exact12"] is True
    assert manifest["maximum_primary_acquisition_count"] == 12
    assert manifest["one_request_per_pdb_identity"] is True
    assert manifest["wildcard_request_allowed"] is False
    assert manifest["source_discovery_crawl_allowed"] is False
    assert manifest["six_vwe_rh_model_graph_claim_created"] is False
    assert manifest["k36_ued_bounded_request_count"] == 8
    assert [
        f"{row['pdb_id']}/{row['expected_ligand_component_id']}"
        for row in rows[4:]
    ] == EXPECTED_IDENTITIES[4:]


def test_historical_1a54_sha_is_provenance_not_remote_byte_requirement() -> None:
    rows = _csv_rows(_build()[owner.REQUEST_FILE])
    assert rows[0]["historical_raw_sha256_provenance_or_NONE"] == (
        owner.HISTORICAL_1A54_RAW_SHA256
    )
    assert {row["historical_raw_sha256_provenance_or_NONE"] for row in rows[1:]} == {
        "NONE"
    }
    assert {row["preknown_remote_payload_sha256_required"] for row in rows} == {
        "false"
    }
    assert _manifest()["historical_1a54_sha_treatment"] == (
        "HISTORICAL_PROVENANCE_ONLY_NOT_PREKNOWN_REMOTE_BYTE_REQUIREMENT"
    )


def test_policy_freezes_idempotence_atomic_integrity_and_finite_transport() -> None:
    policy = {
        row["policy_item"]: row["policy_value"]
        for row in _csv_rows(_build()[owner.POLICY_FILE])
    }
    assert policy["overwrite_allowed"] == "false"
    assert policy["valid_existing_file_action"] == (
        "VERIFY_AND_REUSE_WITHOUT_NETWORK"
    )
    assert policy["invalid_existing_file_action"] == "FAIL_CLOSED_NO_OVERWRITE"
    assert policy["temporary_path_policy"] == "FINAL_PATH_PLUS_DOT_PART"
    assert policy["atomic_write_policy"] == (
        "VERIFY_PART_THEN_OS_REPLACE_AND_REMOVE_PART"
    )
    assert policy["preknown_remote_sha256_required"] == "false"
    assert policy["maximum_attempts_per_identity"] == "1"
    assert policy["request_timeout_seconds"] == "30"
    assert policy["pagination_discovery_crawl_or_recursive_acquisition"] == "false"


def test_no_network_or_raw_write_during_build_and_only_three_materialized_files(
    monkeypatch, tmp_path: Path,
) -> None:
    def forbidden_network(*args, **kwargs):
        raise AssertionError("network access forbidden in authority builder")

    monkeypatch.setattr(socket, "create_connection", forbidden_network)
    artifacts = _build()
    assert tuple(artifacts) == owner.OUTPUT_FILES
    assert not any(
        Path(name).suffix.lower() in {".cif", ".mmcif", ".pdb", ".part"}
        for name in artifacts
    )

    output = tmp_path / "authority"
    hashes = owner.materialize_covapie_cys_sg_exact12_bounded_targeted_structural_evidence_acquisition_authority_v1(
        output_root=output,
    )
    files = sorted(path.name for path in output.iterdir() if path.is_file())
    assert files == sorted(owner.OUTPUT_FILES)
    assert not list(output.rglob("*.tmp"))
    assert not list(output.rglob("*.part"))
    assert stat.S_IMODE(output.stat().st_mode) == 0o755
    assert all(stat.S_IMODE((output / name).stat().st_mode) == 0o644 for name in files)
    assert hashes == {name: _sha256(artifacts[name]) for name in owner.OUTPUT_FILES}

    source = Path(owner.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_from = {
        node.module for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "requests" not in imported
    assert "urllib.request" not in imported_from
    assert "urlopen" not in source
    assert "requests.get" not in source


def test_manifest_counts_are_derived_from_request_rows() -> None:
    artifacts = _build()
    rows = _csv_rows(artifacts[owner.REQUEST_FILE])
    manifest = _manifest(artifacts)
    authorized = {
        "INHERITED_AUTHORIZED_EXACT_TARGET", "AUTHORIZED_EXACT_TARGET",
    }
    assert manifest["requested_identity_count"] == len(rows)
    assert manifest["unique_pdb_identity_count"] == len({row["pdb_id"] for row in rows})
    assert manifest["authorized_exact_target_count"] == sum(
        row["authorization_decision"] in authorized for row in rows
    )
    assert manifest["inherited_authorized_count"] == sum(
        row["authorization_origin"] == "INHERITED_PUBLISHED_BOUNDED_AUTHORITY"
        for row in rows
    )
    assert manifest["newly_authorized_count"] == sum(
        row["authorization_origin"] == "NEW_EXACT12_SUCCESSOR_AUTHORITY"
        for row in rows
    )
    assert manifest["blocked_count"] == sum(
        row["authorization_decision"] not in authorized for row in rows
    )
    assert manifest["authorized_identity_list"] == EXPECTED_IDENTITIES
    assert manifest["blocked_identity_list"] == []


def test_double_build_is_byte_identical_and_hashes_cover_nonself_outputs() -> None:
    first = _build()
    second = _build()
    assert first == second
    manifest = _manifest(first)
    assert manifest["deterministic_output_hashes"] == {
        owner.REQUEST_FILE: _sha256(first[owner.REQUEST_FILE]),
        owner.POLICY_FILE: _sha256(first[owner.POLICY_FILE]),
    }
    assert manifest["manifest_self_sha256_recorded"] is False


def test_successor_publication_compatibility_has_no_live_git_gate(monkeypatch) -> None:
    source = Path(owner.__file__).read_text(encoding="utf-8")
    assert "rev-parse" not in source
    assert "origin/main" not in source
    assert "subprocess" not in source
    monkeypatch.chdir(Path("/"))
    assert _manifest()["ready_for_exact12_acquisition_authority_publication"] is True


def test_all_execution_model_geometry_training_and_rl_boundaries_are_false() -> None:
    manifest = _manifest()
    for key in (
        "network_request_executed",
        "network_executed",
        "download_executed",
        "targeted_acquisition_executed",
        "bulk_acquisition_executed",
        "raw_structure_downloaded",
        "raw_structure_modified",
        "geometry_executed",
        "inverse_reaction_chemistry_executed",
        "rdkit_minimization_executed",
        "model_forward",
        "backward",
        "optimizer_step",
        "trainer_fit",
        "rl",
        "ready_for_bulk_expansion",
        "ready_for_geometry_loss_activation",
        "ready_for_training",
    ):
        assert manifest[key] is False, key
    assert manifest["ready_for_exact12_acquisition_execution"] is True
    for key in {
        "feature_semantics_audit_required_before_training",
        "step12d_smoke_legality_not_final_training_feature_contract",
        "unknown_atom_feature_policy_requires_audit",
        "feature_semantics_known",
    }:
        assert key not in manifest


def test_committed_authority_artifacts_match_production_owner_when_present() -> None:
    artifacts = _build()
    output_root = owner.REPO_ROOT / owner.OUTPUT_ROOT
    if not output_root.exists():
        pytest.skip("production authority artifacts not materialized yet")
    assert sorted(path.name for path in output_root.iterdir() if path.is_file()) == sorted(
        owner.OUTPUT_FILES
    )
    for filename in owner.OUTPUT_FILES:
        path = output_root / filename
        assert path.read_bytes() == artifacts[filename]
        assert stat.S_IMODE(path.stat().st_mode) == 0o644
