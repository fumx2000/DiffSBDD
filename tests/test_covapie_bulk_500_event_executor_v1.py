from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import urllib.request

import pytest

from covalent_ext import covapie_bulk_500_event_executor_v1 as executor


ROOT = Path(__file__).resolve().parents[1]
ACTUAL_CACHE = ROOT.parent / executor.DEFAULT_CACHE_RELATIVE_TO_REPOSITORY_PARENT


@pytest.fixture(scope="module")
def inputs() -> dict[str, object]:
    return executor.load_published_executor_inputs_v1(ROOT)


@pytest.fixture(scope="module")
def actual_cache_before() -> dict[str, object]:
    return executor.snapshot_cache_tree_v1(ACTUAL_CACHE)


@pytest.fixture(scope="module")
def actual_preflight(actual_cache_before: dict[str, object]) -> dict[str, object]:
    result = executor.preflight_no_network_v1(repo_root=ROOT)
    assert executor.snapshot_cache_tree_v1(ACTUAL_CACHE) == actual_cache_before
    return result


def _pdb_payload(pdb_id: str) -> bytes:
    text = (
        f"data_{pdb_id}\n"
        f"_entry.id {pdb_id}\n"
        "_struct_conn.id covale1\n"
        "_atom_site.id 1\n"
    ).encode("utf-8")
    return gzip.compress(text, mtime=0)


def _ccd_payload(ccd_id: str) -> bytes:
    return (
        f"data_{ccd_id}\n"
        "loop_\n"
        "_chem_comp_atom.atom_id\n"
        "_chem_comp_atom.type_symbol\n"
        "_chem_comp_atom.charge\n"
        "C1 C 0\n"
        "C2 C 0\n"
        "#\n"
        "loop_\n"
        "_chem_comp_bond.atom_id_1\n"
        "_chem_comp_bond.atom_id_2\n"
        "_chem_comp_bond.value_order\n"
        "C1 C2 SING\n"
        "#\n"
    ).encode("utf-8")


def _cache_entry(
    payload_kind: str,
    identity: str,
    payload: bytes,
    **overrides: object,
) -> dict[str, object]:
    descriptor = executor._payload_descriptor(payload_kind, identity)
    entry: dict[str, object] = {
        "relative_path": descriptor["relative_path"],
        "source_url_or_endpoint": descriptor["url"],
        "source_dataset": executor.frozen_bulk.adapters.SOURCE_RCSB_PDB_DIRECT,
        "retrieval_identity_sha256": hashlib.sha256(
            executor.frozen_bulk._canonical_json(descriptor["retrieval_identity"])
        ).hexdigest(),
        "http_status": 200,
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "validation_status": "SHA256_AND_SIZE_RECORDED",
        "cache_reuse_status": "DOWNLOADED_BY_BULK_PILOT",
    }
    entry.update(overrides)
    return entry


def _write_cache(
    root: Path,
    payloads: list[tuple[str, str, bytes, dict[str, object]]] | None = None,
) -> None:
    entries = []
    for payload_kind, identity, payload, overrides in payloads or []:
        descriptor = executor._payload_descriptor(payload_kind, identity)
        path = root / descriptor["relative_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        entries.append(_cache_entry(payload_kind, identity, payload, **overrides))
    root.mkdir(parents=True, exist_ok=True)
    (root / "cache_manifest_v1.json").write_bytes(
        executor.frozen_bulk._canonical_json({
            "schema_version": "covapie_bulk_cache_manifest_v1",
            "snapshot_date": "synthetic-test-only",
            "payloads": sorted(entries, key=lambda item: item["relative_path"]),
        })
    )


def _forbidden(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("FORBIDDEN_PATH_CALLED")


def _published_repository_observation(**overrides: object) -> dict[str, object]:
    observation: dict[str, object] = {
        "branch": "main",
        "head": "d" * 40,
        "origin_main": "d" * 40,
        "ahead": 0,
        "behind": 0,
        "published_baseline_ancestor_of_head": True,
        "published_baseline_ancestor_of_origin_main": True,
        "modified_tracked": [],
        "staged": [],
        "untracked": [],
        "tracked_executor_paths": sorted(executor.EXECUTOR_IMPLEMENTATION_PATHS),
    }
    observation.update(overrides)
    return observation


def test_published_rehearsal_bindings_have_exact_bytes_and_sha() -> None:
    root = ROOT / executor.PUBLISHED_REHEARSAL_ROOT_RELATIVE
    for name, (expected_bytes, expected_sha) in (
        executor.PUBLISHED_REHEARSAL_BINDINGS.items()
    ):
        payload = (root / name).read_bytes()
        assert len(payload) == expected_bytes
        assert hashlib.sha256(payload).hexdigest() == expected_sha


def test_exact_population_and_requirement_counts(inputs: dict[str, object]) -> None:
    assert len(inputs["cohort_records"]) == 500
    assert len(inputs["historical_records"]) == 250
    assert len(inputs["incremental_records"]) == 250
    assert len(inputs["known_control_event_ids"]) == 27
    assert len(inputs["required_pdb_ids"]) == 290
    assert len(inputs["required_ccd_ids"]) == 225


def test_historical_250_is_frozen_prefix_and_incremental_sha_exact(
    inputs: dict[str, object],
) -> None:
    rows = inputs["cohort_rows"]
    historical_ids = [item["canonical_event_id"] for item in rows[:250]]
    historical_outcome_ids = [
        item["canonical_event_id"] for item in inputs["historical_outcomes"]
    ]
    assert historical_ids == historical_outcome_ids
    assert executor._ordered_ids_sha256(inputs["incremental_records"]) == (
        executor.INCREMENTAL_ORDERED_EVENT_IDS_SHA256
    )


def test_incremental_new_requirement_properties_are_136_and_102(
    inputs: dict[str, object],
) -> None:
    requirements = inputs["requirements"]
    pdb = requirements["pdb_requirements"]
    ccd = requirements["ccd_requirements"]
    assert pdb["incremental_new_unique_pdb_count"] == 136
    assert ccd["incremental_new_ccd_count"] == 102
    assert len({item["pdb_id"] for item in pdb["requirements"]}) == 290
    assert len({item["ccd_id"] for item in ccd["requirements"]}) == 225


def test_three_lanes_are_disjoint_and_controls_are_not_new_events(
    inputs: dict[str, object],
) -> None:
    historical = {
        item["canonical_event_id"] for item in inputs["historical_records"]
    }
    incremental = {
        item["canonical_event_id"] for item in inputs["incremental_records"]
    }
    controls = inputs["known_control_event_ids"]
    assert not historical & incremental
    assert not controls & (historical | incremental)


def test_loading_exact_workset_never_calls_old_selector_or_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        "select_structural_pilot_events_v1",
        "discover_covpdb_v1",
        "discover_covbinder_v1",
        "discover_rcsb_direct_v1",
        "discover_rcsb_specialist_seeded_v1",
    ):
        monkeypatch.setattr(executor.frozen_bulk, name, _forbidden)
    loaded = executor.load_published_executor_inputs_v1(ROOT)
    assert len(loaded["incremental_records"]) == 250


def test_default_preflight_survives_all_network_and_acquisition_blocks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _forbidden)
    monkeypatch.setattr(executor, "urlopen", _forbidden)
    monkeypatch.setattr(executor, "official_network_backend_v1", _forbidden)
    monkeypatch.setattr(executor.frozen_bulk, "urlopen", _forbidden)
    monkeypatch.setattr(executor.frozen_bulk.BulkCacheV1, "fetch", _forbidden)
    for name in (
        "discover_covpdb_v1",
        "discover_covbinder_v1",
        "discover_rcsb_direct_v1",
        "discover_rcsb_specialist_seeded_v1",
        "_acquire_structures_v1",
        "acquire_ccd_components_v1",
    ):
        monkeypatch.setattr(executor.frozen_bulk, name, _forbidden)
    result = executor.run_v1(repo_root=ROOT, cache_root=tmp_path / "absent")
    assert result["mode"] == executor.PREFLIGHT_NO_NETWORK
    assert result["network_performed"] is False
    assert result["cache_modified"] is False
    assert result["structural_processing_performed"] is False


def test_preflight_rejects_even_explicit_network_flag() -> None:
    with pytest.raises(
        executor.ExecutorSafetyError, match="AUTHORIZATION_INVALID_IN_PREFLIGHT"
    ):
        executor.run_v1(repo_root=ROOT, network_authorized=True)


def test_controlled_mode_requires_boolean_and_external_output_before_network(
    tmp_path: Path,
) -> None:
    calls: list[str] = []

    def backend(**_kwargs: object) -> bytes:
        calls.append("called")
        return b""

    with pytest.raises(executor.ExecutorSafetyError, match="NOT_AUTHORIZED"):
        executor.run_v1(
            repo_root=ROOT,
            mode=executor.CONTROLLED_NETWORK_EXECUTION,
            network_backend=backend,
        )
    with pytest.raises(executor.ExecutorSafetyError, match="OUTPUT_ROOT_REQUIRED"):
        executor.run_v1(
            repo_root=ROOT,
            mode=executor.CONTROLLED_NETWORK_EXECUTION,
            network_authorized=True,
            network_backend=backend,
        )
    assert calls == []


def test_actual_cache_preflight_reconciles_dynamic_coverage(
    actual_preflight: dict[str, object],
) -> None:
    assert (
        actual_preflight["current_valid_pdb_cache_hits"]
        + actual_preflight["current_missing_pdb_count"]
        == 290
    )
    assert (
        actual_preflight["current_valid_ccd_cache_hits"]
        + actual_preflight["current_missing_ccd_count"]
        == 225
    )
    assert (
        actual_preflight["current_valid_control_pdb_cache_hits"]
        + actual_preflight["current_missing_control_pdb_count"]
        == 21
    )
    assert (
        actual_preflight["current_valid_control_ccd_cache_hits"]
        + actual_preflight["current_missing_control_ccd_count"]
        == 15
    )
    assert actual_preflight["cache_integrity_failure_count"] == 0
    assert actual_preflight["network_performed"] is False
    assert actual_preflight["cache_modified"] is False
    assert actual_preflight["ready_for_controlled_network_execution"] is True
    assert actual_preflight["implementation_ready_for_publication"] is True
    observation = executor.observe_repository_publication_state_v1(ROOT)
    try:
        executor.validate_controlled_publication_observation_v1(observation)
    except executor.ExecutorSafetyError:
        expected_publication_gate = False
    else:
        expected_publication_gate = True
    assert actual_preflight[
        "controlled_network_execution_publication_gate_currently_satisfied"
    ] is expected_publication_gate


def test_actual_cache_snapshot_remains_unchanged(
    actual_cache_before: dict[str, object], actual_preflight: dict[str, object],
) -> None:
    assert actual_preflight["cache_snapshot"] == actual_cache_before
    assert executor.snapshot_cache_tree_v1(ACTUAL_CACHE) == actual_cache_before


def test_valid_pdb_hit_is_recognized_read_only(
    tmp_path: Path, inputs: dict[str, object],
) -> None:
    pdb_id = sorted(inputs["required_pdb_ids"])[0]
    payload = _pdb_payload(pdb_id)
    root = tmp_path / "cache"
    _write_cache(root, [("PDB", pdb_id, payload, {})])
    before = executor.snapshot_cache_tree_v1(root)
    observed = executor.inspect_cache_read_only_v1(cache_root=root, inputs=inputs)
    assert observed.summary["valid_pdb_hits"] == 1
    assert executor.snapshot_cache_tree_v1(root) == before


def test_valid_ccd_hit_delegates_to_frozen_parser(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, inputs: dict[str, object],
) -> None:
    ccd_id = sorted(inputs["required_ccd_ids"])[0]
    payload = _ccd_payload(ccd_id)
    root = tmp_path / "cache"
    _write_cache(root, [("CCD", ccd_id, payload, {})])
    original = executor.frozen_bulk.parse_ccd_cif_v1
    calls: list[str] = []

    def spy(value: bytes, *, ccd_id: str) -> dict[str, object]:
        calls.append(ccd_id)
        return original(value, ccd_id=ccd_id)

    monkeypatch.setattr(executor.frozen_bulk, "parse_ccd_cif_v1", spy)
    observed = executor.inspect_cache_read_only_v1(cache_root=root, inputs=inputs)
    assert observed.summary["valid_ccd_hits"] == 1
    assert ccd_id in calls


def test_missing_payload_is_not_a_hit(tmp_path: Path, inputs: dict[str, object]) -> None:
    root = tmp_path / "cache"
    _write_cache(root)
    observed = executor.inspect_cache_read_only_v1(cache_root=root, inputs=inputs)
    assert observed.summary["valid_pdb_hits"] == 0
    assert observed.summary["missing_pdb_count"] == 290
    assert observed.summary["valid_ccd_hits"] == 0
    assert observed.summary["missing_ccd_count"] == 225


def test_partial_part_file_is_not_treated_as_cache_payload(
    tmp_path: Path, inputs: dict[str, object],
) -> None:
    pdb_id = sorted(inputs["required_pdb_ids"])[0]
    root = tmp_path / "cache"
    _write_cache(root)
    target = root / executor._payload_descriptor("PDB", pdb_id)["relative_path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.with_name(target.name + ".part").write_bytes(_pdb_payload(pdb_id))
    before = executor.snapshot_cache_tree_v1(root)
    observed = executor.inspect_cache_read_only_v1(cache_root=root, inputs=inputs)
    assert observed.summary["valid_pdb_hits"] == 0
    assert pdb_id in observed.summary["missing_pdb_ids"]
    assert executor.snapshot_cache_tree_v1(root) == before


@pytest.mark.parametrize(
    ("overrides", "reason"),
    (
        ({"sha256": "0" * 64}, "LEDGER_CONFLICT"),
        ({"byte_count": 999999}, "LEDGER_CONFLICT"),
        ({"retrieval_identity_sha256": "0" * 64}, "RETRIEVAL_IDENTITY_CONFLICT"),
        ({"source_url_or_endpoint": "https://example.invalid/arbitrary"}, "RETRIEVAL_IDENTITY_CONFLICT"),
    ),
)
def test_corrupt_or_incompatible_cache_entry_is_rejected(
    tmp_path: Path,
    inputs: dict[str, object],
    overrides: dict[str, object],
    reason: str,
) -> None:
    pdb_id = sorted(inputs["required_pdb_ids"])[0]
    payload = _pdb_payload(pdb_id)
    root = tmp_path / "cache"
    _write_cache(root, [("PDB", pdb_id, payload, overrides)])
    observed = executor.inspect_cache_read_only_v1(cache_root=root, inputs=inputs)
    assert observed.summary["valid_pdb_hits"] == 0
    assert observed.summary["cache_integrity_failure_count"] == 1
    assert reason in observed.summary["cache_integrity_failures"][f"PDB:{pdb_id}"]


def test_existing_conflicting_payload_is_never_overwritten(
    tmp_path: Path, inputs: dict[str, object],
) -> None:
    pdb_id = sorted(inputs["required_pdb_ids"])[0]
    payload = _pdb_payload(pdb_id)
    root = tmp_path / "cache"
    _write_cache(
        root,
        [("PDB", pdb_id, payload, {"retrieval_identity_sha256": "0" * 64})],
    )
    path = root / executor._payload_descriptor("PDB", pdb_id)["relative_path"]
    before_bytes = path.read_bytes()
    before_snapshot = executor.snapshot_cache_tree_v1(root)
    with pytest.raises(executor.ExecutorSafetyError, match="RETRIEVAL_IDENTITY_CONFLICT"):
        executor.acquire_payload_v1(
            repo_root=ROOT,
            cache_root=root,
            payload_kind="PDB",
            identity=pdb_id,
            budget=executor.DownloadBudgetV1(),
            network_authorized=True,
            network_backend=_forbidden,
            inputs=inputs,
        )
    assert path.read_bytes() == before_bytes
    assert executor.snapshot_cache_tree_v1(root) == before_snapshot


def test_preflight_preserves_payload_mtime_tree_and_ledger_bytes(
    tmp_path: Path, inputs: dict[str, object],
) -> None:
    pdb_id = sorted(inputs["required_pdb_ids"])[0]
    ccd_id = sorted(inputs["required_ccd_ids"])[0]
    root = tmp_path / "cache"
    _write_cache(
        root,
        [
            ("PDB", pdb_id, _pdb_payload(pdb_id), {}),
            ("CCD", ccd_id, _ccd_payload(ccd_id), {}),
        ],
    )
    ledger_before = (root / "cache_manifest_v1.json").read_bytes()
    snapshot_before = executor.snapshot_cache_tree_v1(root)
    result = executor.preflight_no_network_v1(repo_root=ROOT, cache_root=root)
    assert result["cache_modified"] is False
    assert (root / "cache_manifest_v1.json").read_bytes() == ledger_before
    assert executor.snapshot_cache_tree_v1(root) == snapshot_before


def test_download_smaller_than_remaining_budget_succeeds(
    tmp_path: Path, inputs: dict[str, object],
) -> None:
    pdb_id = sorted(inputs["required_pdb_ids"])[0]
    payload = _pdb_payload(pdb_id)
    root = tmp_path / "cache"
    budget = executor.DownloadBudgetV1(total_cap_bytes=len(payload) + 5)

    def backend(*, record_received_bytes: object, **_kwargs: object) -> bytes:
        record_received_bytes(len(payload))
        return payload

    result = executor.acquire_payload_v1(
        repo_root=ROOT,
        cache_root=root,
        payload_kind="PDB",
        identity=pdb_id,
        budget=budget,
        network_authorized=True,
        network_backend=backend,
        inputs=inputs,
    )
    assert result["status"] == "NEWLY_DOWNLOADED"
    assert result["executor_provenance"] == executor.EXECUTOR_DOWNLOAD_PROVENANCE
    assert budget.downloaded_this_execution_bytes == len(payload)
    assert budget.remaining_execution_download_budget == 5


def test_multiple_downloads_accumulate_exact_new_bytes(
    tmp_path: Path, inputs: dict[str, object],
) -> None:
    pdb_ids = sorted(inputs["required_pdb_ids"])[:2]
    payloads = {identity: _pdb_payload(identity) for identity in pdb_ids}
    budget = executor.DownloadBudgetV1(
        total_cap_bytes=sum(map(len, payloads.values())) + 7
    )
    root = tmp_path / "cache"
    for identity in pdb_ids:
        executor.acquire_payload_v1(
            repo_root=ROOT,
            cache_root=root,
            payload_kind="PDB",
            identity=identity,
            budget=budget,
            network_authorized=True,
            network_backend=lambda identity=identity, **_kwargs: payloads[identity],
            inputs=inputs,
        )
    assert budget.downloaded_this_execution_bytes == sum(map(len, payloads.values()))
    assert budget.remaining_execution_download_budget == 7


def test_invalid_science_payload_bytes_remain_charged_and_are_not_cached(
    tmp_path: Path, inputs: dict[str, object],
) -> None:
    pdb_id = sorted(inputs["required_pdb_ids"])[0]
    invalid = b"downloaded-but-not-gzip"
    budget = executor.DownloadBudgetV1(total_cap_bytes=1000)
    cache_root = tmp_path / "cache"
    with pytest.raises(
        executor.ExecutorSafetyError,
        match="DOWNLOADED_PDB_SCIENTIFIC_VALIDATION_FAILED",
    ):
        executor.acquire_payload_v1(
            repo_root=ROOT,
            cache_root=cache_root,
            payload_kind="PDB",
            identity=pdb_id,
            budget=budget,
            network_authorized=True,
            network_backend=lambda **_kwargs: invalid,
            inputs=inputs,
        )
    assert budget.network_bytes_received_this_execution == len(invalid)
    assert not (
        cache_root / executor._payload_descriptor("PDB", pdb_id)["relative_path"]
    ).exists()


def test_partial_failed_backend_bytes_remain_charged(
    tmp_path: Path, inputs: dict[str, object],
) -> None:
    pdb_id = sorted(inputs["required_pdb_ids"])[0]
    partial = b"partial-response"
    budget = executor.DownloadBudgetV1(total_cap_bytes=1000)

    def backend(*, record_received_bytes: object, **_kwargs: object) -> bytes:
        record_received_bytes(len(partial))
        raise OSError("synthetic connection reset")

    with pytest.raises(executor.ExecutorSafetyError, match="NETWORK_BACKEND_FAILED"):
        executor.acquire_payload_v1(
            repo_root=ROOT,
            cache_root=tmp_path / "cache",
            payload_kind="PDB",
            identity=pdb_id,
            budget=budget,
            network_authorized=True,
            network_backend=backend,
            inputs=inputs,
        )
    assert budget.network_bytes_received_this_execution == len(partial)


def test_cache_persistence_failure_does_not_release_received_bytes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, inputs: dict[str, object],
) -> None:
    pdb_id = sorted(inputs["required_pdb_ids"])[0]
    payload = _pdb_payload(pdb_id)
    budget = executor.DownloadBudgetV1(total_cap_bytes=1000)
    monkeypatch.setattr(
        executor,
        "_write_downloaded_cache_payload",
        lambda **_kwargs: (_ for _ in ()).throw(
            executor.ExecutorSafetyError("SYNTHETIC_CACHE_PERSISTENCE_FAILED")
        ),
    )
    with pytest.raises(executor.ExecutorSafetyError, match="CACHE_PERSISTENCE_FAILED"):
        executor.acquire_payload_v1(
            repo_root=ROOT,
            cache_root=tmp_path / "cache",
            payload_kind="PDB",
            identity=pdb_id,
            budget=budget,
            network_authorized=True,
            network_backend=lambda **_kwargs: payload,
            inputs=inputs,
        )
    assert budget.network_bytes_received_this_execution == len(payload)


def test_invalid_response_consuming_total_cap_blocks_all_later_requests(
    tmp_path: Path, inputs: dict[str, object],
) -> None:
    first_pdb = sorted(inputs["required_pdb_ids"])[0]
    invalid = b"invalid-full-budget"
    calls: list[str] = []

    def backend(*, url: str, **_kwargs: object) -> bytes:
        calls.append(url)
        return invalid

    acquisition = executor.acquire_required_payloads_v1(
        repo_root=ROOT,
        cache_root=tmp_path / "cache",
        network_authorized=True,
        network_backend=backend,
        total_download_cap_bytes=len(invalid),
    )
    assert len(calls) == 1
    assert first_pdb in calls[0]
    assert acquisition.result["network_bytes_received_this_execution"] == len(invalid)
    assert acquisition.result["network_request_count"] == 1
    assert acquisition.result["failed_pdb_count"] == 290
    assert "DOWNLOADED_PDB_SCIENTIFIC_VALIDATION_FAILED" in (
        acquisition.result["failures"][f"PDB:{first_pdb}"]
    )


def test_mixed_valid_invalid_partial_and_cache_reuse_share_one_byte_budget(
    tmp_path: Path, inputs: dict[str, object],
) -> None:
    pdb_ids = sorted(inputs["required_pdb_ids"])[:5]
    reused_id, valid_id, invalid_id, partial_id, blocked_id = pdb_ids
    root = tmp_path / "cache"
    reused_payload = _pdb_payload(reused_id)
    _write_cache(root, [("PDB", reused_id, reused_payload, {})])
    valid_payload = _pdb_payload(valid_id)
    invalid_payload = b"invalid-science"
    partial_payload = b"partial"
    expected_received = (
        len(valid_payload) + len(invalid_payload) + len(partial_payload)
    )
    budget = executor.DownloadBudgetV1(total_cap_bytes=expected_received)

    reused = executor.acquire_payload_v1(
        repo_root=ROOT,
        cache_root=root,
        payload_kind="PDB",
        identity=reused_id,
        budget=budget,
        network_authorized=True,
        network_backend=_forbidden,
        inputs=inputs,
    )
    assert reused["new_download_bytes"] == 0
    executor.acquire_payload_v1(
        repo_root=ROOT,
        cache_root=root,
        payload_kind="PDB",
        identity=valid_id,
        budget=budget,
        network_authorized=True,
        network_backend=lambda **_kwargs: valid_payload,
        inputs=inputs,
    )
    with pytest.raises(executor.ExecutorSafetyError, match="SCIENTIFIC_VALIDATION"):
        executor.acquire_payload_v1(
            repo_root=ROOT,
            cache_root=root,
            payload_kind="PDB",
            identity=invalid_id,
            budget=budget,
            network_authorized=True,
            network_backend=lambda **_kwargs: invalid_payload,
            inputs=inputs,
        )

    def partial_backend(
        *, record_received_bytes: object, **_kwargs: object,
    ) -> bytes:
        record_received_bytes(len(partial_payload))
        raise OSError("synthetic partial failure")

    with pytest.raises(executor.ExecutorSafetyError, match="NETWORK_BACKEND_FAILED"):
        executor.acquire_payload_v1(
            repo_root=ROOT,
            cache_root=root,
            payload_kind="PDB",
            identity=partial_id,
            budget=budget,
            network_authorized=True,
            network_backend=partial_backend,
            inputs=inputs,
        )
    with pytest.raises(executor.ExecutorSafetyError, match="EXHAUSTED_BEFORE_REQUEST"):
        executor.acquire_payload_v1(
            repo_root=ROOT,
            cache_root=root,
            payload_kind="PDB",
            identity=blocked_id,
            budget=budget,
            network_authorized=True,
            network_backend=_forbidden,
            inputs=inputs,
        )
    assert budget.network_bytes_received_this_execution == expected_received
    assert budget.remaining_execution_download_budget == 0


def test_response_larger_than_remaining_is_bounded_and_fails_closed(
    tmp_path: Path, inputs: dict[str, object],
) -> None:
    pdb_id = sorted(inputs["required_pdb_ids"])[0]
    payload = _pdb_payload(pdb_id)
    maximums: list[int] = []
    budget = executor.DownloadBudgetV1(total_cap_bytes=len(payload) - 1)

    def backend(*, maximum_bytes: int, **_kwargs: object) -> bytes:
        maximums.append(maximum_bytes)
        return payload

    with pytest.raises(executor.ExecutorSafetyError, match="EXCEEDED_REQUEST_BYTE_BOUND"):
        executor.acquire_payload_v1(
            repo_root=ROOT,
            cache_root=tmp_path / "cache",
            payload_kind="PDB",
            identity=pdb_id,
            budget=budget,
            network_authorized=True,
            network_backend=backend,
            inputs=inputs,
        )
    assert maximums == [len(payload) - 1]
    assert budget.hard_stopped is True
    assert budget.network_bytes_received_this_execution == len(payload) - 1


def test_no_subsequent_request_after_total_budget_is_exhausted(
    tmp_path: Path, inputs: dict[str, object],
) -> None:
    first_pdb = sorted(inputs["required_pdb_ids"])[0]
    first_payload = _pdb_payload(first_pdb)
    calls: list[str] = []

    def backend(*, url: str, **_kwargs: object) -> bytes:
        identity = url.rsplit("/", 1)[-1].split(".", 1)[0]
        calls.append(identity)
        return _pdb_payload(identity)

    result = executor.acquire_required_payloads_v1(
        repo_root=ROOT,
        cache_root=tmp_path / "cache",
        network_authorized=True,
        network_backend=backend,
        total_download_cap_bytes=len(first_payload),
    )
    assert calls == [first_pdb]
    assert result.result["new_download_bytes"] == len(first_payload)
    assert result.result["budget_remaining_bytes"] == 0
    assert result.result["network_request_count"] == 1
    assert result.result["cache_reuse_executor_provenance"] == (
        executor.REUSED_CACHE_PROVENANCE
    )
    assert result.result["new_download_executor_provenance"] == (
        executor.EXECUTOR_DOWNLOAD_PROVENANCE
    )
    assert result.result["historical_cache_ledger_entries_reauthored"] is False


def test_cache_reuse_consumes_zero_new_download_budget(
    tmp_path: Path, inputs: dict[str, object],
) -> None:
    pdb_id = sorted(inputs["required_pdb_ids"])[0]
    payload = _pdb_payload(pdb_id)
    root = tmp_path / "cache"
    _write_cache(root, [("PDB", pdb_id, payload, {})])
    budget = executor.DownloadBudgetV1(total_cap_bytes=1000)
    result = executor.acquire_payload_v1(
        repo_root=ROOT,
        cache_root=root,
        payload_kind="PDB",
        identity=pdb_id,
        budget=budget,
        network_authorized=True,
        network_backend=_forbidden,
        inputs=inputs,
    )
    assert result["status"] == "CACHE_REUSED"
    assert result["executor_provenance"] == executor.REUSED_CACHE_PROVENANCE
    assert result["new_download_bytes"] == 0
    assert budget.downloaded_this_execution_bytes == 0


@pytest.mark.parametrize(
    ("payload_kind", "expected_cap"),
    (
        ("PDB", 64 * 1024 * 1024),
        ("CCD", 4 * 1024 * 1024),
    ),
)
def test_payload_specific_cap_applies_with_ample_total_budget(
    tmp_path: Path,
    inputs: dict[str, object],
    payload_kind: str,
    expected_cap: int,
) -> None:
    identities = (
        inputs["required_pdb_ids"] if payload_kind == "PDB"
        else inputs["required_ccd_ids"]
    )
    identity = sorted(identities)[0]
    limits: list[int] = []

    def backend(*, maximum_bytes: int, **_kwargs: object) -> bytes:
        limits.append(maximum_bytes)
        raise executor.ExecutorSafetyError("SYNTHETIC_RESPONSE_TOO_LARGE")

    with pytest.raises(executor.ExecutorSafetyError, match="SYNTHETIC_RESPONSE_TOO_LARGE"):
        executor.acquire_payload_v1(
            repo_root=ROOT,
            cache_root=tmp_path / "cache",
            payload_kind=payload_kind,
            identity=identity,
            budget=executor.DownloadBudgetV1(total_cap_bytes=2 * 1024 * 1024 * 1024),
            network_authorized=True,
            network_backend=backend,
            inputs=inputs,
        )
    assert limits == [expected_cap]


@pytest.mark.parametrize(
    ("payload_kind", "identity"),
    (("PDB", "ZZZZ"), ("CCD", "ZZZ")),
)
def test_identity_outside_published_allowlist_fails_before_request(
    tmp_path: Path,
    inputs: dict[str, object],
    payload_kind: str,
    identity: str,
) -> None:
    with pytest.raises(executor.ExecutorSafetyError, match="OUTSIDE_PUBLISHED_ALLOWLIST"):
        executor.acquire_payload_v1(
            repo_root=ROOT,
            cache_root=tmp_path / "cache",
            payload_kind=payload_kind,
            identity=identity,
            budget=executor.DownloadBudgetV1(),
            network_authorized=True,
            network_backend=_forbidden,
            inputs=inputs,
        )


def test_arbitrary_url_fails_before_request(
    tmp_path: Path, inputs: dict[str, object],
) -> None:
    pdb_id = sorted(inputs["required_pdb_ids"])[0]
    with pytest.raises(executor.ExecutorSafetyError, match="URL_OUTSIDE_OFFICIAL"):
        executor.acquire_payload_v1(
            repo_root=ROOT,
            cache_root=tmp_path / "cache",
            payload_kind="PDB",
            identity=pdb_id,
            budget=executor.DownloadBudgetV1(),
            network_authorized=True,
            network_backend=_forbidden,
            requested_url="https://example.invalid/arbitrary",
            inputs=inputs,
        )


def test_official_backend_rejects_declared_oversize_before_body_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reads: list[int] = []

    class Response:
        status = 200
        headers = {"Content-Length": "11"}

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, count: int) -> bytes:
            reads.append(count)
            return b""

    monkeypatch.setattr(executor, "urlopen", lambda *_args, **_kwargs: Response())
    with pytest.raises(executor.ExecutorSafetyError, match="CONTENT_LENGTH_CAP"):
        executor.official_network_backend_v1(
            url="https://files.rcsb.org/download/1ATK.cif.gz",
            maximum_bytes=10,
            timeout_seconds=1,
            record_received_bytes=lambda _count: None,
        )
    assert reads == []


def test_official_backend_charges_partial_body_before_read_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Response:
        status = 200
        headers: dict[str, str] = {}

        def __init__(self) -> None:
            self.read_count = 0

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, _count: int) -> bytes:
            self.read_count += 1
            if self.read_count == 1:
                return b"partial"
            raise OSError("synthetic stream failure")

    monkeypatch.setattr(executor, "urlopen", lambda *_args, **_kwargs: Response())
    budget = executor.DownloadBudgetV1(total_cap_bytes=100)
    with pytest.raises(OSError, match="synthetic stream failure"):
        executor.official_network_backend_v1(
            url="https://files.rcsb.org/download/1ATK.cif.gz",
            maximum_bytes=100,
            timeout_seconds=1,
            record_received_bytes=budget.record_received_bytes,
        )
    assert budget.network_bytes_received_this_execution == len(b"partial")


def test_incremental_processing_delegates_all_science_to_frozen_owner(
    monkeypatch: pytest.MonkeyPatch, inputs: dict[str, object],
) -> None:
    calls: list[str] = []
    leakage_calls: list[int] = []
    historical_before = json.loads(json.dumps(inputs["historical_outcomes"]))
    controls_before = json.loads(json.dumps(inputs["control_outcomes"]))

    def process(event: dict[str, object], **_kwargs: object) -> dict[str, object]:
        calls.append(str(event["canonical_event_id"]))
        return {
            "canonical_event_id": event["canonical_event_id"],
            "terminal_outcome": "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY",
            "structural_processing": {},
        }

    def leakage(outcomes: list[dict[str, object]], **_kwargs: object) -> None:
        leakage_calls.append(len(outcomes))
        outcomes[0]["synthetic_frozen_mutation"] = True
        outcomes[250]["synthetic_control_mutation"] = True

    monkeypatch.setattr(executor.frozen_bulk, "process_event_structure_v1", process)
    monkeypatch.setattr(
        executor.frozen_bulk, "apply_leakage_predictions_read_only_v1", leakage
    )
    context = executor.ProcessingContextV1((), object(), set(), {})
    outcomes, metrics = executor.process_incremental_250_v1(
        incremental_records=inputs["incremental_records"],
        pdb_payloads={identity: b"validated" for identity in inputs["required_pdb_ids"]},
        ccd_components={identity: {} for identity in inputs["required_ccd_ids"]},
        processing_context=context,
        frozen_historical_outcomes=inputs["historical_outcomes"],
        frozen_control_outcomes=inputs["control_outcomes"],
    )
    assert calls == [
        item["canonical_event_id"] for item in inputs["incremental_records"]
    ]
    assert leakage_calls == [527]
    assert len(outcomes) == 250
    assert inputs["historical_outcomes"] == historical_before
    assert inputs["control_outcomes"] == controls_before
    assert metrics["incremental_events_attempted"] == 250
    assert metrics["incremental_events_structurally_completed"] == 250
    assert metrics["leakage_batch_population_count"] == 527
    assert metrics["frozen_control_outcomes_in_leakage_context"] == 27
    assert metrics["historical_or_control_outcomes_reauthored"] is False


def test_frozen_control_can_participate_as_leakage_bridge_reference(
    monkeypatch: pytest.MonkeyPatch, inputs: dict[str, object],
) -> None:
    bridge_control_id = inputs["control_outcomes"][0]["canonical_event_id"]
    controls_before = json.loads(json.dumps(inputs["control_outcomes"]))

    def process(event: dict[str, object], **_kwargs: object) -> dict[str, object]:
        return {
            "canonical_event_id": event["canonical_event_id"],
            "terminal_outcome": "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY",
            "structural_processing": {},
        }

    def leakage(batch: list[dict[str, object]], **_kwargs: object) -> None:
        control_ids = {
            item["canonical_event_id"] for item in batch[250:277]
        }
        assert bridge_control_id in control_ids
        batch[277]["synthetic_linked_via_control"] = bridge_control_id

    monkeypatch.setattr(executor.frozen_bulk, "process_event_structure_v1", process)
    monkeypatch.setattr(
        executor.frozen_bulk, "apply_leakage_predictions_read_only_v1", leakage
    )
    outcomes, _metrics = executor.process_incremental_250_v1(
        incremental_records=inputs["incremental_records"],
        pdb_payloads={identity: b"validated" for identity in inputs["required_pdb_ids"]},
        ccd_components={identity: {} for identity in inputs["required_ccd_ids"]},
        processing_context=executor.ProcessingContextV1((), object(), set(), {}),
        frozen_historical_outcomes=inputs["historical_outcomes"],
        frozen_control_outcomes=inputs["control_outcomes"],
    )
    assert outcomes[0]["synthetic_linked_via_control"] == bridge_control_id
    assert inputs["control_outcomes"] == controls_before


def test_historical_records_cannot_enter_incremental_processing_lane(
    inputs: dict[str, object],
) -> None:
    with pytest.raises(executor.ExecutorSafetyError, match="WORKSET_NOT_EXACT"):
        executor.process_incremental_250_v1(
            incremental_records=inputs["historical_records"],
            pdb_payloads={},
            ccd_components={},
            processing_context=executor.ProcessingContextV1((), object(), set(), {}),
            frozen_historical_outcomes=inputs["historical_outcomes"],
            frozen_control_outcomes=inputs["control_outcomes"],
        )


def test_cumulative_view_preserves_frozen_predecessor_and_lane_labels(
    inputs: dict[str, object],
) -> None:
    incremental = [
        {
            "canonical_event_id": item["canonical_event_id"],
            "terminal_outcome": "STRUCTURAL_EVIDENCE_INCOMPLETE",
        }
        for item in inputs["incremental_records"]
    ]
    view = executor.finalize_cumulative_view_v1(
        inputs=inputs, incremental_outcomes=incremental
    )
    assert len(view["events"]) == 500
    assert len(view["known_control_references"]) == 27
    assert all(
        item["lane"] == executor.FROZEN_HISTORICAL_PREDECESSOR
        for item in view["events"][:250]
    )
    assert all(
        item["lane"] == executor.NEW_INCREMENTAL_EXECUTION
        for item in view["events"][250:]
    )
    assert [item["processing_outcome"] for item in view["events"][:250]] == (
        inputs["historical_outcomes"]
    )
    assert view["historical_predecessor_recomputed"] is False


def test_controlled_state_roots_accept_only_canonical_disjoint_namespaces(
) -> None:
    cache = executor.canonical_controlled_cache_root_v1(ROOT)
    output = executor.controlled_output_namespace_v1(ROOT)
    assert executor.validate_controlled_state_roots_v1(
        repo_root=ROOT, cache_root=cache, output_root=output
    ) == (cache, output)
    child = output / "attempt-001"
    assert executor.validate_controlled_state_roots_v1(
        repo_root=ROOT, cache_root=cache, output_root=child
    ) == (cache, child)


def test_controlled_state_roots_reject_arbitrary_cache_root(tmp_path: Path) -> None:
    with pytest.raises(executor.ExecutorSafetyError, match="CACHE_ROOT_NOT_CANONICAL"):
        executor.validate_controlled_state_roots_v1(
            repo_root=ROOT,
            cache_root=tmp_path / "redirected-cache",
            output_root=executor.controlled_output_namespace_v1(ROOT),
        )
    with pytest.raises(executor.ExecutorSafetyError, match="CACHE_ROOT_NOT_CANONICAL"):
        executor.run_v1(
            repo_root=ROOT,
            mode=executor.CONTROLLED_NETWORK_EXECUTION,
            network_authorized=True,
            cache_root=tmp_path / "redirected-cache",
            output_root=executor.controlled_output_namespace_v1(ROOT),
            network_backend=_forbidden,
        )


@pytest.mark.parametrize(
    "output_root",
    (
        ROOT / "executor-output",
        ROOT.parent / "covapie-state",
        ROOT.parent / "covapie-state/bulk-multisource-cys-sg-v1",
        ROOT.parent / "covapie-state/bulk-multisource-cys-sg-v1/output-child",
        ROOT.parent / "covapie-state/manual-review/current11-warhead-boundary-v1",
    ),
)
def test_controlled_state_roots_reject_other_or_overlapping_output_lanes(
    output_root: Path,
) -> None:
    with pytest.raises(executor.ExecutorSafetyError, match="OUTPUT_ROOT_OUTSIDE"):
        executor.validate_controlled_state_roots_v1(
            repo_root=ROOT,
            cache_root=executor.canonical_controlled_cache_root_v1(ROOT),
            output_root=output_root,
        )


def test_controlled_state_roots_have_explicit_overlap_defense(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = executor.canonical_controlled_cache_root_v1(ROOT)
    monkeypatch.setattr(executor, "controlled_output_namespace_v1", lambda _root: cache)
    with pytest.raises(executor.ExecutorSafetyError, match="ROOTS_OVERLAP"):
        executor.validate_controlled_state_roots_v1(
            repo_root=ROOT, cache_root=cache, output_root=cache / "output"
        )


def test_synthetic_clean_tracked_publication_state_is_accepted() -> None:
    accepted = executor.validate_controlled_publication_observation_v1(
        _published_repository_observation()
    )
    assert set(accepted["tracked_executor_paths"]) == set(
        executor.EXECUTOR_IMPLEMENTATION_PATHS
    )


@pytest.mark.parametrize(
    ("overrides", "reason"),
    (
        ({"untracked": sorted(executor.EXECUTOR_IMPLEMENTATION_PATHS)}, "UNTRACKED"),
        ({"modified_tracked": ["src/covalent_ext/covapie_bulk_500_event_executor_v1.py"]}, "WORKTREE"),
        ({"staged": ["tests/test_covapie_bulk_500_event_executor_v1.py"]}, "INDEX"),
        ({"origin_main": "e" * 40}, "HEAD_ORIGIN"),
        ({"ahead": 1}, "AHEAD_BEHIND"),
        ({"behind": 1}, "AHEAD_BEHIND"),
        ({"tracked_executor_paths": []}, "PATHS_NOT_TRACKED"),
    ),
)
def test_controlled_publication_gate_rejects_unpublished_or_dirty_states(
    overrides: dict[str, object], reason: str,
) -> None:
    with pytest.raises(executor.ExecutorSafetyError, match=reason):
        executor.validate_controlled_publication_observation_v1(
            _published_repository_observation(**overrides)
        )


def test_publication_gate_failure_has_zero_network_cache_or_output_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = executor.canonical_controlled_cache_root_v1(ROOT)
    output = (
        executor.controlled_output_namespace_v1(ROOT)
        / "synthetic-publication-gate-failure-test"
    )
    cache_before = executor.snapshot_cache_tree_v1(cache)
    output_before = executor.snapshot_cache_tree_v1(output)
    backend_calls: list[str] = []

    def backend(**_kwargs: object) -> bytes:
        backend_calls.append("called")
        return b""

    monkeypatch.setattr(
        executor,
        "observe_repository_publication_state_v1",
        lambda _root: _published_repository_observation(
            untracked=sorted(executor.EXECUTOR_IMPLEMENTATION_PATHS),
            tracked_executor_paths=[],
        ),
    )
    with pytest.raises(executor.ExecutorSafetyError, match="UNTRACKED"):
        executor.run_v1(
            repo_root=ROOT,
            mode=executor.CONTROLLED_NETWORK_EXECUTION,
            network_authorized=True,
            cache_root=cache,
            output_root=output,
            network_backend=backend,
        )
    assert backend_calls == []
    assert executor.snapshot_cache_tree_v1(cache) == cache_before
    assert executor.snapshot_cache_tree_v1(output) == output_before


def test_frozen_predecessor_and_successor_artifacts_remain_byte_identical(
    tmp_path: Path,
) -> None:
    protected = [
        executor.rehearsal.FROZEN_BULK_SOURCE_RELATIVE,
        *executor.rehearsal.PILOT_INPUT_SHA256,
        *executor.rehearsal.LIVE_ROUTING_INPUT_SHA256,
        executor.rehearsal.FEATURE_RESOLUTION_MANIFEST_RELATIVE,
        Path(
            "data/derived/covalent_small/covapie_bulk_post_only_cys_sg_human_review_v1/"
            "covapie_post_only_human_review_decisions_v1.json"
        ),
        Path(
            "data/derived/covalent_small/covapie_bulk_post_only_cys_sg_human_review_v1/"
            "covapie_post_only_human_review_progress_v1.json"
        ),
        executor.frozen_bulk.AUTHORITY_REGISTRY_RELATIVE,
        *(
            executor.PUBLISHED_REHEARSAL_ROOT_RELATIVE / name
            for name in executor.rehearsal.OUTPUT_FILENAMES
        ),
    ]
    before = {path: (ROOT / path).read_bytes() for path in protected}
    result = executor.preflight_no_network_v1(
        repo_root=ROOT, cache_root=tmp_path / "absent-cache"
    )
    assert result["network_performed"] is False
    assert {path: (ROOT / path).read_bytes() for path in protected} == before


def test_repository_binding_uses_synchronized_descendant_semantics() -> None:
    observation = executor.verify_synchronized_descendant_repository_v1(ROOT)
    assert observation["branch"] == "main"
    assert observation["head"] == observation["origin_main"]
    assert observation["ahead"] == observation["behind"] == 0
    assert observation["published_baseline_ancestor_of_head"] is True
    assert observation["published_baseline_ancestor_of_origin_main"] is True
