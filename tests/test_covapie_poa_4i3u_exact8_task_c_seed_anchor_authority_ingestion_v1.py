from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import inspect
import json
import os
from pathlib import Path

import pytest


MODULE_ENV = "COVAPIE_POA_EXACT8_INGESTION_MODULE_PATH"
REPOSITORY_ENV = "COVAPIE_REPOSITORY_ROOT"
STATE_ENV = "COVAPIE_STATE_ROOT"


def _load_module():
    candidate = os.environ.get(MODULE_ENV)
    if candidate:
        path = Path(candidate)
        spec = importlib.util.spec_from_file_location(
            "covapie_poa_exact8_ingestion_candidate", path
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(
        "covalent_ext."
        "covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1"
    )


MODULE = _load_module()


@pytest.fixture(scope="session")
def roots() -> tuple[Path, Path]:
    repository = Path(os.environ[REPOSITORY_ENV]).resolve(strict=True)
    state = Path(os.environ[STATE_ENV]).resolve(strict=True)
    return repository, state


@pytest.fixture(scope="session")
def source_bundle(roots: tuple[Path, Path]) -> dict[str, bytes]:
    repository, state = roots
    bundle = {
        "signed": (state / MODULE.SIGNED_DECISION_RELATIVE_PATH_V1).read_bytes()
    }
    for spec in MODULE._SOURCE_SPECS_V1:
        root = state if spec["root"] == "state" else repository
        bundle[spec["key"]] = (root / spec["path"]).read_bytes()
    return bundle


def _mutate_json(
    source_bundle: dict[str, bytes], key: str, mutation
) -> dict[str, bytes]:
    changed = dict(source_bundle)
    document = json.loads(changed[key])
    mutation(document)
    changed[key] = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return changed


def _semantic_rejected(bundle: dict[str, bytes]) -> None:
    with pytest.raises(MODULE._InvariantError):
        MODULE._compile_source_bytes(bundle)


def _public_compile(roots: tuple[Path, Path]):
    repository, state = roots
    return MODULE.load_and_compile_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1(
        repository_root=repository,
        state_root=state,
    )


def _install_fake_signed_root(
    tmp_path: Path, payload: bytes, *, symlink_target: Path | None = None
) -> Path:
    signed = tmp_path / MODULE.SIGNED_DECISION_RELATIVE_PATH_V1
    signed.parent.mkdir(parents=True)
    if symlink_target is None:
        signed.write_bytes(payload)
        signed.chmod(0o664)
    else:
        signed.symlink_to(symlink_target)
    return tmp_path


def test_fixed_real_signed_record_compiles_and_maps_exact8(
    roots: tuple[Path, Path],
) -> None:
    result = _public_compile(roots)
    projection = result["semantic_projection"]
    events = projection["event_records"]
    assert len(events) == 8
    assert [row["canonical_event_id"] for row in events] == list(MODULE._EVENT_IDS_V1)
    assert all(row["minimal_seed_atom_ids"] == ["P", "O1P"] for row in events)
    assert all(row["primary_anchor_atom_id"] == "P" for row in events)
    assert [
        [atom["model_sample_local_index_0based"] for atom in row["seed_atom_mappings"]]
        for row in events
    ] == [[6, 3]] * 8
    assert [
        [atom["model_flat_index_0based"] for atom in row["seed_atom_mappings"]]
        for row in events
    ] == [[6 + 7 * index, 3 + 7 * index] for index in range(8)]
    assert [
        [atom["source_atom_site_row_index_0based"] for atom in row["seed_atom_mappings"]]
        for row in events
    ] == [[29014 + 7 * index, 29011 + 7 * index] for index in range(8)]
    assert projection["permission_boundary"]["RUNTIME_SEED_AUTHORITY_ACTIVATED"] is False
    assert projection["permission_boundary"]["NEW_FORMAL_ADMISSION_CREATED"] is False


def test_real_result_source_revalidation_passes(roots: tuple[Path, Path]) -> None:
    result = _public_compile(roots)
    repository, state = roots
    assert (
        MODULE.validate_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1(
            result=result,
            repository_root=repository,
            state_root=state,
        )
        is None
    )


def test_deterministic_double_compile_and_serialization(
    roots: tuple[Path, Path],
) -> None:
    first = _public_compile(roots)
    second = _public_compile(roots)
    first_bytes = MODULE.serialize_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1(first)
    second_bytes = MODULE.serialize_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1(second)
    assert first == second
    assert first_bytes == second_bytes
    assert first_bytes.endswith(b"\n")
    assert b"/cpfs" not in first_bytes


def test_public_entry_has_no_expected_digest_or_bypass_parameters() -> None:
    signature = inspect.signature(
        MODULE.load_and_compile_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1
    )
    assert tuple(signature.parameters) == ("repository_root", "state_root")
    forbidden = {"expected_sha256", "decision_path", "allow_unsigned", "skip_source_check"}
    assert forbidden.isdisjoint(signature.parameters)


@pytest.mark.parametrize("source_key", ["choice", "template"])
def test_choice_candidate_and_unsigned_template_rejected_by_formal_entry(
    roots: tuple[Path, Path], source_bundle: dict[str, bytes], tmp_path: Path,
    source_key: str,
) -> None:
    repository, _ = roots
    fake_state = _install_fake_signed_root(tmp_path, source_bundle[source_key])
    with pytest.raises(ValueError, match=MODULE.INGESTION_ERROR):
        MODULE.load_and_compile_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1(
            repository_root=repository,
            state_root=fake_state,
        )


def test_public_loader_rejects_source_hash_drift_before_semantic_parse(
    roots: tuple[Path, Path], source_bundle: dict[str, bytes], tmp_path: Path,
) -> None:
    repository, _ = roots
    signed = bytearray(source_bundle["signed"])
    signed[-2] = signed[-2] ^ 1
    fake_state = _install_fake_signed_root(tmp_path, bytes(signed))
    with pytest.raises(ValueError, match=MODULE.INGESTION_ERROR):
        MODULE.load_and_compile_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1(
            repository_root=repository,
            state_root=fake_state,
        )


def test_public_loader_rejects_symlink_path_drift(
    roots: tuple[Path, Path], tmp_path: Path,
) -> None:
    repository, state = roots
    real_signed = state / MODULE.SIGNED_DECISION_RELATIVE_PATH_V1
    fake_state = _install_fake_signed_root(
        tmp_path, b"", symlink_target=real_signed
    )
    with pytest.raises(ValueError, match=MODULE.INGESTION_ERROR):
        MODULE.load_and_compile_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1(
            repository_root=repository,
            state_root=fake_state,
        )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda doc: doc.pop("human_approval_recorded"),
        lambda doc: doc["human_approval"].pop("reviewer_id"),
        lambda doc: doc.__setitem__("schema_version", "wrong_schema"),
        lambda doc: doc.__setitem__("record_role", "wrong_role"),
        lambda doc: doc.__setitem__("decision_status", "UNSIGNED"),
        lambda doc: doc.__setitem__("human_approval_recorded", 1),
        lambda doc: doc["human_approval"].__setitem__("approval_recorded", "true"),
        lambda doc: doc["human_approval"].__setitem__("attestor_id", ""),
        lambda doc: doc["human_approval"].__setitem__("approved_at_utc", "2026-09-16T11:39:15+00:00"),
    ],
)
def test_signed_schema_approval_identity_status_and_exact_types_fail_closed(
    source_bundle: dict[str, bytes], mutation,
) -> None:
    _semantic_rejected(_mutate_json(source_bundle, "signed", mutation))


def test_same_reviewer_and_attestor_is_explicitly_accepted(
    roots: tuple[Path, Path],
) -> None:
    approval = _public_compile(roots)["semantic_projection"]["human_approval"]
    assert approval["reviewer_id"] == approval["attestor_id"] == "fmx"
    assert approval["same_identity_dual_role_explicitly_allowed"] is True


def test_strict_json_rejects_duplicate_keys(source_bundle: dict[str, bytes]) -> None:
    signed = source_bundle["signed"]
    duplicate = b'{"schema_version":"duplicate",' + signed.lstrip()[1:]
    changed = dict(source_bundle)
    changed["signed"] = duplicate
    _semantic_rejected(changed)


def test_strict_json_rejects_nan_and_infinity(source_bundle: dict[str, bytes]) -> None:
    for token in (b"NaN", b"Infinity", b"-Infinity"):
        changed = dict(source_bundle)
        changed["signed"] = b'{"x":' + token + b"}"
        _semantic_rejected(changed)


@pytest.mark.parametrize("case", ["duplicate", "missing", "extra", "reordered"])
def test_event_scope_duplicate_missing_extra_and_order_drift_rejected(
    source_bundle: dict[str, bytes], case: str,
) -> None:
    def mutation(doc):
        events = doc["approved_selection"]["apply_to_event_ids"]
        if case == "duplicate":
            events[-1] = events[0]
        elif case == "missing":
            events.pop()
            doc["approved_selection"]["apply_to_exact_event_count"] = 7
        elif case == "extra":
            events.append("COVAPIE_CYS_SG_EVENT_V1:4I3V:X:CYS:291-:SG:X:POA:C2")
            doc["approved_selection"]["apply_to_exact_event_count"] = 9
        else:
            events[0], events[1] = events[1], events[0]

    _semantic_rejected(_mutate_json(source_bundle, "signed", mutation))


@pytest.mark.parametrize(
    "field,value",
    [
        ("selected_seed_candidate_id", "POA_4I3U_EXACT8_TASK_C_SEED_CANDIDATE_02"),
        ("selected_minimal_seed_atom_ids", ["P", "O2P"]),
        ("selected_primary_anchor_atom_id", "O2P"),
    ],
)
def test_other_candidate_seed_or_anchor_cannot_borrow_approval(
    source_bundle: dict[str, bytes], field: str, value,
) -> None:
    _semantic_rejected(
        _mutate_json(
            source_bundle,
            "signed",
            lambda doc: doc["approved_selection"].__setitem__(field, value),
        )
    )


@pytest.mark.parametrize("field", ["path", "path_namespace", "sha256"])
def test_signed_source_binding_path_namespace_and_sha_drift_rejected_semantically(
    source_bundle: dict[str, bytes], field: str,
) -> None:
    def mutation(doc):
        row = doc["source_bindings"][0]
        row[field] = "wrong" if field != "sha256" else "0" * 64

    _semantic_rejected(_mutate_json(source_bundle, "signed", mutation))


def test_o1p_validator_index_two_cannot_replace_model_local_three(
    source_bundle: dict[str, bytes],
) -> None:
    def mutation(doc):
        event = doc["per_event_approved_seed_and_anchor_mappings"][0]
        event["selected_seed_atom_mappings"][1]["model_sample_local_index_0based"] = 2
        event["selected_seed_indices_from_packet"]["model_sample_local_indices_0based"][1] = 2
        event["event_local_published_validator_call"]["seed_model_sample_local_indices_0based"][1] = 2

    _semantic_rejected(_mutate_json(source_bundle, "signed", mutation))


def test_cross_event_flat_and_source_indices_cannot_be_copied(
    source_bundle: dict[str, bytes],
) -> None:
    def mutation(doc):
        first = doc["per_event_approved_seed_and_anchor_mappings"][0]
        second = doc["per_event_approved_seed_and_anchor_mappings"][1]
        for index in range(2):
            for field in ("model_flat_index_0based", "source_atom_site_row_index_0based"):
                second["selected_seed_atom_mappings"][index][field] = first["selected_seed_atom_mappings"][index][field]
        second["selected_seed_indices_from_packet"]["model_flat_indices_0based"] = copy.deepcopy(
            first["selected_seed_indices_from_packet"]["model_flat_indices_0based"]
        )
        second["selected_seed_indices_from_packet"]["source_atom_site_row_indices_0based"] = copy.deepcopy(
            first["selected_seed_indices_from_packet"]["source_atom_site_row_indices_0based"]
        )

    _semantic_rejected(_mutate_json(source_bundle, "signed", mutation))


def test_b1_atom_site_and_local_mapping_are_independently_rebuilt(
    source_bundle: dict[str, bytes],
) -> None:
    def mutation(doc):
        atom = doc["events"][3]["ligand"]["atoms"][3]
        atom["atom_site_id"] = "29012"

    _semantic_rejected(_mutate_json(source_bundle, "b1", mutation))


def test_seed_outside_scaffold_role_is_rejected(source_bundle: dict[str, bytes]) -> None:
    def mutation(doc):
        decision = doc["role_human_decision"]
        decision["scaffold_atom_ids"] = ["P", "O2P", "O3P"]
        decision["linker_atom_ids"] = ["C1", "O1P"]

    _semantic_rejected(_mutate_json(source_bundle, "role_decision", mutation))


def test_anchor_outside_seed_is_rejected(source_bundle: dict[str, bytes]) -> None:
    _semantic_rejected(
        _mutate_json(
            source_bundle,
            "signed",
            lambda doc: doc["approved_selection"].__setitem__(
                "selected_primary_anchor_atom_id", "C1"
            ),
        )
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda doc: doc["approved_scope_and_nonclaims"].__setitem__("training_admission_granted", True),
        lambda doc: doc["approved_scope_and_nonclaims"].__setitem__("geometry_supervision_changed_or_approved", True),
        lambda doc: doc["approved_scope_and_nonclaims"].__setitem__("task_C_generated_or_fixed_mask_changed", True),
        lambda doc: doc["authority_and_execution_boundary"].__setitem__("RUNTIME_SEED_AUTHORITY_ACTIVATED", True),
    ],
)
def test_signed_record_cannot_expand_permissions(
    source_bundle: dict[str, bytes], mutation,
) -> None:
    _semantic_rejected(_mutate_json(source_bundle, "signed", mutation))


def test_b1_training_admission_or_task_c_fixed_mask_drift_rejected(
    source_bundle: dict[str, bytes],
) -> None:
    admitted = _mutate_json(
        source_bundle,
        "b1",
        lambda doc: doc["events"][0]["formal_metadata"].__setitem__("training_admitted", True),
    )
    _semantic_rejected(admitted)

    def fixed_mask(doc):
        task_c = doc["events"][0]["canonical_exact5_structural_masks"][4]
        task_c["fixed_atom_local_indices"] = [6]
        task_c["fixed_count"] = 1

    _semantic_rejected(_mutate_json(source_bundle, "b1", fixed_mask))


def test_b1_historical_candidate_status_is_not_used_as_publication_gate(
    source_bundle: dict[str, bytes],
) -> None:
    changed = _mutate_json(
        source_bundle,
        "b1",
        lambda doc: doc.__setitem__("candidate_status", "SOME_OTHER_HISTORICAL_LABEL"),
    )
    assert MODULE._compile_source_bytes(changed)["semantic_projection"]["event_count"] == 8


def test_tampered_result_with_recomputed_digest_still_fails_source_revalidation(
    roots: tuple[Path, Path],
) -> None:
    result = _public_compile(roots)
    result["semantic_projection"]["event_records"][0]["primary_anchor_atom_id"] = "O1P"
    projection_bytes = MODULE._canonical_json_bytes(result["semantic_projection"])
    result["semantic_projection_sha256"] = hashlib.sha256(projection_bytes).hexdigest()
    repository, state = roots
    with pytest.raises(ValueError, match=MODULE.INGESTION_ERROR):
        MODULE.validate_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1(
            result=result,
            repository_root=repository,
            state_root=state,
        )


def test_result_permission_tamper_rejected_even_with_recomputed_digest(
    roots: tuple[Path, Path],
) -> None:
    result = _public_compile(roots)
    boundary = result["semantic_projection"]["permission_boundary"]
    boundary["NEW_FORMAL_ADMISSION_CREATED"] = True
    result["semantic_projection_sha256"] = hashlib.sha256(
        MODULE._canonical_json_bytes(result["semantic_projection"])
    ).hexdigest()
    repository, state = roots
    with pytest.raises(ValueError, match=MODULE.INGESTION_ERROR):
        MODULE.validate_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1(
            result=result,
            repository_root=repository,
            state_root=state,
        )


def test_compile_deep_copies_inputs_and_results_are_isolated(
    source_bundle: dict[str, bytes],
) -> None:
    documents = {
        "signed": MODULE._strict_json(source_bundle["signed"]),
        "choice": MODULE._strict_json(source_bundle["choice"]),
        "packet": MODULE._strict_json(source_bundle["packet"]),
        "template": MODULE._strict_json(source_bundle["template"]),
        "role_decision": MODULE._strict_json(source_bundle["role_decision"]),
        "topology": MODULE._strict_json(source_bundle["topology"]),
        "b1": MODULE._strict_json(source_bundle["b1"]),
    }
    before = copy.deepcopy(documents)
    first = MODULE._compile_documents(documents)
    first["semantic_projection"]["event_records"][0]["minimal_seed_atom_ids"][0] = "MUTATED"
    assert documents == before
    second = MODULE._compile_documents(documents)
    assert second["semantic_projection"]["event_records"][0]["minimal_seed_atom_ids"] == ["P", "O1P"]


def test_serializer_rejects_digest_mismatch(roots: tuple[Path, Path]) -> None:
    result = _public_compile(roots)
    result["semantic_projection_sha256"] = "0" * 64
    with pytest.raises(ValueError, match=MODULE.INGESTION_ERROR):
        MODULE.serialize_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1(result)
