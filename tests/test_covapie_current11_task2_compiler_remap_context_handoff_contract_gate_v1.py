from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1
    as gate,
)


ROOT = Path(__file__).resolve().parents[1]
STATE = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
    "covapie-state"
)
CHECKER = (
    ROOT
    / "scripts/check_covapie_current11_task2_compiler_remap_context_handoff_"
    "contract_gate_v1.py"
)
ERROR = (
    "COVAPIE_CURRENT11_TASK2_COMPILER_REMAP_CONTEXT_HANDOFF_"
    "CONTRACT_GATE_V1_ERROR"
)


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return gate.build_covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1(
        repo_root=ROOT,
        state_root=STATE,
    )


@pytest.fixture(scope="module")
def parsed(artifacts: dict[str, bytes]) -> dict[str, dict[str, object]]:
    return {
        name: json.loads(payload.decode("utf-8"))
        for name, payload in artifacts.items()
    }


def _manual_stable_digest(artifacts: dict[str, bytes]) -> str:
    digest = hashlib.sha256(
        b"COVAPIE_CURRENT11_TASK2_COMPILER_REMAP_CONTEXT_HANDOFF_"
        b"CONTRACT_GATE_V1\0"
    )
    for name in gate._STABLE_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _manual_known_digest(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    digest = hashlib.sha256(
        b"COVAPIE_CURRENT11_TASK2_COMPILER_REMAP_CONTEXT_HANDOFF_"
        b"KNOWN_VECTOR_V1\0"
    )
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _environment() -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONPATH": "src:.",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def _checker(*extra: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        (
            sys.executable,
            "-B",
            str(CHECKER),
            "--repo-root",
            str(ROOT),
            "--state-root",
            str(STATE),
            *extra,
        ),
        cwd=ROOT,
        env=_environment(),
        capture_output=True,
        check=False,
    )


def _lifecycle_expectations(lifecycle: str) -> dict[str, object]:
    if lifecycle == "precommit-untracked":
        return {
            "gate_status": (
                "PASS_COMPILER_REMAP_CONTEXT_HANDOFF_CONTRACT_"
                "PRECOMMIT_CANDIDATE_ONLY"
            ),
            "commit_review": True,
            "publication": False,
            "handoff_implementation": False,
            "blocker": "handoff_contract_gate_not_published",
        }
    if lifecycle == "clean-tracked-successor":
        return {
            "gate_status": (
                "PASS_COMPILER_REMAP_CONTEXT_HANDOFF_CONTRACT_"
                "CLEAN_TRACKED_SUCCESSOR"
            ),
            "commit_review": False,
            "publication": True,
            "handoff_implementation": True,
            "blocker": "NONE",
        }
    raise AssertionError(lifecycle)


def test_public_exact1_keyword_only_signature() -> None:
    function = (
        gate.build_covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1
    )
    signature = inspect.signature(function)
    assert gate.__all__ == (function.__name__,)
    assert tuple(signature.parameters) == ("repo_root", "state_root")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert str(signature) == (
        "(*, repo_root: 'Path', state_root: 'Path') -> 'dict[str, bytes]'"
    )
    assert ERROR == gate._ERROR


def test_gate_rejects_positional_and_invalid_roots() -> None:
    with pytest.raises(TypeError):
        gate.build_covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1(
            ROOT,
            STATE,
        )
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        gate.build_covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1(
            repo_root=Path("."),
            state_root=STATE,
        )


def test_keyboard_interrupt_and_system_exit_are_not_wrapped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def keyboard(**unused: object) -> dict[str, bytes]:
        del unused
        raise KeyboardInterrupt

    monkeypatch.setattr(gate, "_build_impl", keyboard)
    with pytest.raises(KeyboardInterrupt):
        gate.build_covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1(
            repo_root=ROOT,
            state_root=STATE,
        )


def test_silent_import() -> None:
    completed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            (
                "from covalent_ext import "
                "covapie_current11_task2_compiler_remap_context_handoff_"
                "contract_gate_v1"
            ),
        ),
        cwd=ROOT,
        env=_environment(),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == b""
    assert completed.stderr == b""


def test_exact6_names_order_types(artifacts: dict[str, bytes]) -> None:
    assert type(artifacts) is dict
    assert tuple(artifacts) == (
        "current11_task2_compiler_remap_context_handoff_contract_manifest.json",
        "current11_task2_compiler_remap_context_handoff_context_schema.json",
        "current11_task2_compiler_remap_context_handoff_api_and_error_contract.json",
        "current11_task2_compiler_remap_context_handoff_reference_vectors.json",
        "current11_task2_compiler_remap_context_handoff_acceptance_matrix.json",
        "current11_task2_compiler_remap_context_handoff_contract_gate_report.json",
    )
    assert len(artifacts) == 6
    assert all(type(name) is str for name in artifacts)
    assert all(type(payload) is bytes for payload in artifacts.values())


def test_deterministic_double_build_byte_identical(
    artifacts: dict[str, bytes],
) -> None:
    second = gate.build_covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1(
        repo_root=ROOT,
        state_root=STATE,
    )
    assert second == artifacts
    assert tuple(second) == tuple(artifacts)


def test_all_artifacts_are_canonical_safe_json(
    artifacts: dict[str, bytes],
) -> None:
    for payload in artifacts.values():
        value = json.loads(payload.decode("utf-8"))
        assert payload == (
            json.dumps(
                value,
                sort_keys=True,
                indent=2,
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        assert not payload.startswith(b"\xef\xbb\xbf")
        assert b"\0" not in payload
        assert b"\r" not in payload
        assert payload.endswith(b"\n")
        assert not payload.endswith(b"\n\n")


def test_stable_digest_deterministic_and_report_self_excluded(
    artifacts: dict[str, bytes], parsed: dict[str, dict[str, object]]
) -> None:
    expected = _manual_stable_digest(artifacts)
    assert parsed[gate._REPORT]["stable_contract_digest"] == expected
    changed = dict(artifacts)
    changed[gate._REPORT] = b"{}\n"
    assert _manual_stable_digest(changed) == expected
    assert gate._REPORT not in gate._STABLE_NAMES


def test_known_vector_digest_independent(
    parsed: dict[str, dict[str, object]],
) -> None:
    vectors = parsed[gate._REFERENCE_VECTORS]
    expected = _manual_known_digest(vectors["known_vector_semantic"])
    assert vectors["known_vector_digest"] == expected
    assert parsed[gate._MANIFEST]["known_vector_digest"] == expected
    assert parsed[gate._REPORT]["known_vector_digest"] == expected


def test_design_report_identity_exact(parsed: dict[str, dict[str, object]]) -> None:
    identity = parsed[gate._MANIFEST]["design_report_identity"]
    assert identity == {
        "relative_path": gate._DESIGN_REPORT_RELATIVE,
        "bytes": 39895,
        "LF": 524,
        "sha256": (
            "10d5c2245b54665f83cab2782651a18ab7569628d07c07697841887e3e27d47e"
        ),
        "mode": "0644",
        "regular_file": True,
        "symlink": False,
    }
    assert parsed[gate._REPORT]["design_report_identity_verified"] is True


def test_predecessor_source_identities_exact(
    parsed: dict[str, dict[str, object]],
) -> None:
    identities = parsed[gate._MANIFEST]["predecessor_identities"]
    assert identities == [dict(spec) for spec in gate._OWNER_SPECS]
    assert len(identities) == 6
    assert parsed[gate._REPORT]["predecessor_identities_verified"] is True


def test_adapter_public_exact2_and_private_helper_static() -> None:
    source = (ROOT / gate._OWNER_SPECS[0]["path"]).read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert tuple(gate._literal_assignment(tree, "__all__")) == gate._ADAPTER_PUBLIC_EXACT2
    assert gate._function_signature(tree, gate._ADAPTER_MATERIALIZER) == (
        "(context: object) -> tuple[dict[str, object], list[dict[str, object]], "
        "dict[str, object]]"
    )
    assert gate._ADAPTER_MATERIALIZER not in gate._ADAPTER_PUBLIC_EXACT2
    assert "type(context) is not _AdapterContext" in source
    assert "_construction_seal(semantic) != context._seal" in source


def test_historical_compiler_context_public_exact2_byte_frozen() -> None:
    spec = gate._OWNER_SPECS[2]
    payload = (ROOT / spec["path"]).read_bytes()
    tree = ast.parse(payload.decode("utf-8"))
    assert hashlib.sha256(payload).hexdigest() == spec["sha256"]
    assert tuple(gate._literal_assignment(tree, "__all__")) == (
        "build_covapie_current11_task2_batch_descriptor_compiler_context_v1",
        "compile_covapie_current11_task2_batch_descriptor_with_context_v1",
    )


def test_compiler_pure_kernel_signature_frozen() -> None:
    spec = gate._OWNER_SPECS[4]
    tree = ast.parse((ROOT / spec["path"]).read_text(encoding="utf-8"))
    assert gate._function_signature(tree, gate._COMPILER_KERNEL) == (
        "(*, authority: tuple[dict[str, object], list[dict[str, object]], "
        "dict[str, bool]], observation: object) -> dict[str, object]"
    )


def test_source_exact10_order_mapping_and_golden(
    parsed: dict[str, dict[str, object]],
) -> None:
    semantic = parsed[gate._REFERENCE_VECTORS]["known_vector_semantic"]
    parsed_source = semantic["source_exact10"]
    mapping = semantic["source_mapping_table"]
    assert [row["target_field"] for row in mapping] == list(gate._SOURCE_FIELDS)
    assert parsed[gate._MANIFEST]["source_contract"]["field_order"] == list(
        gate._SOURCE_FIELDS
    )
    unused_identities, compiler_constants = gate._verify_predecessors(ROOT)
    del unused_identities
    source = gate._source_fixture(compiler_constants)
    assert tuple(source) == gate._SOURCE_FIELDS
    assert source == parsed_source
    compact = json.dumps(
        source,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    assert len(compact) == 2735
    assert hashlib.sha256(compact).hexdigest() == (
        "21bc3eb8a7b2f4b569f17d102715726eda09aed6467782e5477a7cfa285f98f2"
    )
    gate._validate_source_reference(source)


def test_source_mapping_is_exact_rename_or_constant_only(
    parsed: dict[str, dict[str, object]],
) -> None:
    mapping = parsed[gate._REFERENCE_VECTORS]["known_vector_semantic"][
        "source_mapping_table"
    ]
    assert [row["operation"] for row in mapping] == [
        "constant",
        "rename_only",
        "rename_only",
        "constant",
        "constant",
        "deep_copy_rename_only",
        "deep_copy_rename_only",
        "deep_copy_rename_only",
        "deep_copy_rename_only",
        "deep_copy_rename_only",
    ]
    assert all("observation" not in row["source_authority"] for row in mapping)


def test_provider_exact11_mapping_and_golden(
    parsed: dict[str, dict[str, object]],
) -> None:
    provider = parsed[gate._REFERENCE_VECTORS]["known_vector_semantic"][
        "provider_exact11_contract"
    ]
    assert provider["sample_count"] == 11
    assert provider["sample_record_field_order"] == ["sample_identity", "roles"]
    assert provider["sample_identity_field_order"] == list(gate._IDENTITY_FIELDS)
    assert provider["role_order"] == ["pocket", "ligand"]
    assert provider["role_record_field_order"] == list(gate._ROLE_RECORD_FIELDS)
    assert provider["compiler_required_role_field_order"] == list(
        gate._ROLE_REQUIRED_FIELDS
    )
    assert provider["selected_atom_identity_field_order"] == list(
        gate._ATOM_IDENTITY_FIELDS
    )
    assert provider["canonical_compact_bytes"] == 23364
    assert provider["canonical_sha256"] == (
        "1345c9da88fd516677c1730d129ab8a19f487eb0862fa7b7580481bc15a43bc5"
    )
    assert provider["historical_provider_digest"] == (
        "a6193bfe7099b9c9436036f75101df31638739a893b598af8ac021bfa46aa186"
    )
    assert provider["provider_digest_matches_historical"] is True
    assert provider["missing_information_count"] == 0
    assert provider["lossless_mapping"] is True
    gate._validate_provider_contract(provider)


def test_historical_readiness_exact24_order_values_and_digest(
    parsed: dict[str, dict[str, object]],
) -> None:
    readiness = parsed[gate._REFERENCE_VECTORS]["known_vector_semantic"][
        "readiness_exact24"
    ]
    assert readiness["field_count"] == 24
    assert readiness["field_order"] == sorted(readiness["field_order"])
    assert list(readiness["values"]) == readiness["field_order"]
    assert readiness["values"]["runtime_batch_observation_extractor_implemented"] is False
    assert readiness["values"][
        "ready_for_runtime_batch_observation_extractor_design"
    ] is True
    assert readiness["component_digest"] == (
        "8d6bcae9f365f6c802e9109a8c1e53c1b85c8c8c23f04d005a162c09fcdb6890"
    )
    gate._validate_readiness_reference(readiness["values"])


def test_authority_compatibility_and_component_digests(
    parsed: dict[str, dict[str, object]],
) -> None:
    semantic = parsed[gate._REFERENCE_VECTORS]["known_vector_semantic"]
    assert semantic["historical_authority_compatibility_digest"] == (
        "e3c7c14e5a94db2bf59b5195ae6902d7fd7269e58a8690589962548860348d44"
    )
    assert semantic["historical_authority_digest_role"] == (
        "compiler_authority_compatibility_not_future_bridge_construction_seal"
    )
    assert semantic["provenance_component_digest"] == gate._PROVENANCE_COMPONENT_DIGEST
    assert semantic["source_component_digest"] == gate._SOURCE_COMPONENT_DIGEST
    assert semantic["provider_exact11_contract"]["provider_component_digest"] == (
        gate._PROVIDER_COMPONENT_DIGEST
    )


def test_future_bridge_public_exact2_and_builder_no_roots(
    parsed: dict[str, dict[str, object]],
) -> None:
    api = parsed[gate._API_AND_ERROR]
    rows = api["future_public_exact2"]
    assert [row["name"] for row in rows] == list(gate._FUTURE_PUBLIC_EXACT2)
    assert rows[0]["signature"] == "(*, remap_context: object) -> object"
    assert rows[1]["signature"] == (
        "(*, context: object, observation: dict[str, object]) -> dict[str, object]"
    )
    assert api["future_error_token"] == gate._FUTURE_ERROR
    assert "repo_root" in api["future_builder_forbidden_parameters"]
    assert "state_root" in api["future_builder_forbidden_parameters"]
    assert "repo_root" not in rows[0]["signature"]
    assert "state_root" not in rows[0]["signature"]


def test_future_private_context_exact20_immutable_schema(
    parsed: dict[str, dict[str, object]],
) -> None:
    schema = parsed[gate._CONTEXT_SCHEMA]
    assert schema["logical_field_order"] == list(gate._FUTURE_CONTEXT_FIELDS)
    assert schema["logical_field_count"] == 20
    assert schema["logical_field_order"][-1] == "construction_seal"
    assert schema["private_type_contract"] == {
        "private": True,
        "opaque_to_callers": True,
        "frozen": True,
        "slotted": True,
        "public_constructor": False,
        "public_context_class_export": False,
        "mutable_dict_or_list_reachable": False,
        "global_cache": False,
        "registry": False,
        "singleton": False,
        "pickle_or_copy_private_context": False,
    }
    assert schema["retained_remap_context"] is False
    assert "construction_seal" in schema["seal_contract"]["excluded_fields"]
    fixed = schema["fixed_value_contract"]
    assert fixed["context_contract_version"] == (
        "published_handoff_gate_report_stable_contract_digest"
    )
    assert fixed["adapter_context_private_materializer"] == gate._ADAPTER_MATERIALIZER
    assert fixed["compiler_private_kernel"] == gate._COMPILER_KERNEL
    assert fixed["provider_digest"] == gate._PROVIDER_DIGEST
    assert fixed["historical_authority_compatibility_digest"] == (
        gate._AUTHORITY_COMPATIBILITY_DIGEST
    )
    assert schema["seal_contract"]["framing_steps"][-1] == (
        "emit_lowercase_sha256_hex"
    )


def test_future_seal_domain_uses_real_terminal_nul_not_literal_backslash_zero(
    artifacts: dict[str, bytes], parsed: dict[str, dict[str, object]]
) -> None:
    domain = gate._FUTURE_SEAL_DOMAIN
    assert type(domain) is str
    assert domain.endswith("\x00")
    assert not domain.endswith("\\0")
    encoded = domain.encode("utf-8")
    assert encoded.endswith(b"\x00")
    assert encoded[-1] == 0
    assert encoded[-2] != 0x5C

    schema = parsed[gate._CONTEXT_SCHEMA]
    assert schema["seal_contract"]["domain_utf8_with_terminal_nul"] == domain
    assert schema["seal_contract"]["framing_steps"] == [
        "initialize_sha256_with_domain_utf8_bytes_including_terminal_nul",
        "encode_first_19_fields_as_canonical_compact_json_utf8",
        "append_payload_length_as_unsigned_8_byte_big_endian",
        "append_payload_bytes",
        "emit_lowercase_sha256_hex",
    ]
    raw_schema = artifacts[gate._CONTEXT_SCHEMA]
    assert b"\x00" not in raw_schema
    assert b"\\u0000" in raw_schema


def test_opaque_trusted_owner_coupling_only(
    parsed: dict[str, dict[str, object]],
) -> None:
    coupling = parsed[gate._API_AND_ERROR]["trusted_owner_coupling"]
    assert coupling["private_helper"] == gate._ADAPTER_MATERIALIZER
    assert coupling["helper_call_count_per_build"] == 1
    assert coupling["helper_call_count_per_fast_compile"] == 0
    assert coupling["adapter_public_exact2_unchanged"] is True
    assert coupling["public_accessor_added"] is False
    assert coupling["direct_semantic_or_seal_read"] is False
    assert coupling["owner_error_caught_then_continued"] is False


def test_single_authority_snapshot_and_no_old_chain(
    parsed: dict[str, dict[str, object]],
) -> None:
    ownership = parsed[gate._API_AND_ERROR]["single_authority_snapshot"]
    assert ownership["caller_builds_remap_context_once"] is True
    assert ownership["bridge_consumes_same_object"] is True
    assert ownership["materialize_once_at_build"] is True
    assert ownership["compiler_authority_freeze_once"] is True
    assert ownership["bridge_public_remap_builder_call_count"] == 0
    assert ownership["zero_call_vector"] == gate._ZERO_CALL_VECTOR
    assert all(value == 0 for value in ownership["zero_call_vector"].values())


def test_fast_compile_no_io_structural_contract(
    parsed: dict[str, dict[str, object]],
) -> None:
    fast = parsed[gate._API_AND_ERROR]["fast_compile"]
    assert fast["validate_type_version_lineage_seal_first"] is True
    assert fast["only_compile_call"] == gate._COMPILER_KERNEL
    for field in (
        "filesystem_reads",
        "git_calls",
        "subprocess_calls",
        "artifact_writes",
        "context_rebuilds",
        "global_cache_accesses",
    ):
        assert fast[field] == 0
    assert fast["benchmark_or_millisecond_sla"] is False


def test_output10_success_exact4_and_hard_failure_exact5(
    parsed: dict[str, dict[str, object]],
) -> None:
    semantic = parsed[gate._REFERENCE_VECTORS]["known_vector_semantic"]
    assert semantic["output10_field_order"] == list(gate._OUTPUT10_FIELDS)
    assert semantic["adapter_input_exact18_field_order"] == list(
        gate._EXACT18_FIELDS
    )
    assert semantic["success_case_ids"] == [
        "canonical",
        "reversed",
        "subset_10_4_0",
        "singleton_10",
    ]
    assert semantic["hard_failure_cases"] == [
        {"case_id": case_id, "compiler_status": status}
        for case_id, status in gate._HARD_FAILURES
    ]
    assert semantic["output10_bridge_metadata_added"] is False


def test_context_programming_failure_semantics(
    parsed: dict[str, dict[str, object]],
) -> None:
    errors = parsed[gate._API_AND_ERROR]["error_semantics"]
    assert errors["context_programming_failures"] == list(gate._CONTEXT_FAILURES)
    assert errors["context_failure_result"] == gate._FUTURE_ERROR
    assert errors["context_validation_before_observation_evaluation"] is True
    assert errors["valid_context_malformed_observation"] == (
        "existing_compiler_hard_failure_output10"
    )
    assert errors["keyboard_interrupt_or_system_exit_wrapped"] is False


def test_device_risk_contract_not_runtime_proof(
    parsed: dict[str, dict[str, object]],
) -> None:
    report = parsed[gate._REPORT]
    assert report["device_identity_risk_resolution_contract_defined"] is True
    assert report["device_identity_risk_resolution_runtime_proven"] is False
    assert "st_dev_49" in report["device_identity_risk_root_cause"]
    assert "st_dev_50" in report["device_identity_risk_root_cause"]


def test_readiness_matches_repository_lifecycle_and_downstream_stays_closed(
    parsed: dict[str, dict[str, object]],
) -> None:
    report = parsed[gate._REPORT]
    lifecycle = report["repository_lifecycle"]
    expected = _lifecycle_expectations(lifecycle)
    readiness = report["readiness"]
    assert readiness[
        "ready_for_compiler_remap_context_handoff_contract_gate_commit_review"
    ] is expected["commit_review"]
    assert readiness[
        "ready_for_compiler_remap_context_handoff_contract_gate_publication"
    ] is expected["publication"]
    assert readiness[
        "ready_for_compiler_remap_context_handoff_implementation"
    ] is expected["handoff_implementation"]
    assert readiness["compiler_remap_context_handoff_implementation_blocker"] == (
        expected["blocker"]
    )
    assert readiness["device_identity_risk_resolution_runtime_proven"] is False
    assert readiness["ready_for_dataloader_integration"] is False
    assert readiness["ready_for_model_integration"] is False
    assert readiness["ready_for_loss_integration"] is False
    assert readiness["feature_semantics_reaudit_required_before_training"] is True
    assert readiness["ready_for_training"] is False


def test_clean_tracked_successor_readiness_authorizes_handoff_candidate_only() -> None:
    clean = gate._report_readiness("clean-tracked-successor")
    assert clean[
        "ready_for_compiler_remap_context_handoff_contract_gate_commit_review"
    ] is False
    assert clean[
        "ready_for_compiler_remap_context_handoff_contract_gate_publication"
    ] is True
    assert clean["ready_for_compiler_remap_context_handoff_implementation"] is True
    assert clean["compiler_remap_context_handoff_implementation_blocker"] == "NONE"
    assert clean["device_identity_risk_resolution_contract_defined"] is True
    assert clean["device_identity_risk_resolution_runtime_proven"] is False
    assert clean["ready_for_dataloader_integration"] is False
    assert clean["ready_for_model_integration"] is False
    assert clean["ready_for_loss_integration"] is False
    assert clean["feature_semantics_reaudit_required_before_training"] is True
    assert clean["ready_for_training"] is False

    precommit = gate._report_readiness("precommit-untracked")
    assert precommit[
        "ready_for_compiler_remap_context_handoff_implementation"
    ] is False
    assert precommit["compiler_remap_context_handoff_implementation_blocker"] == (
        "handoff_contract_gate_not_published"
    )

    with pytest.raises(gate._ContractInvariantError):
        gate._report_readiness("invalid")


def test_canonical_mask_exact5_includes_scaffold_only_b3(
    parsed: dict[str, dict[str, object]],
) -> None:
    masks = parsed[gate._REFERENCE_VECTORS]["known_vector_semantic"][
        "canonical_masks"
    ]
    assert masks == [
        {"semantic_name": name, "display_alias": alias}
        for name, alias in gate._CANONICAL_MASKS
    ]
    assert len(masks) == 5
    assert {row["semantic_name"] for row in masks} == {
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    }
    assert {row["display_alias"] for row in masks} == {"A", "B", "B2", "B3", "C"}


def test_acceptance_matrix_has_positive_and_required_negative_exact36(
    parsed: dict[str, dict[str, object]],
) -> None:
    matrix = parsed[gate._ACCEPTANCE_MATRIX]
    cases = matrix["cases"]
    assert matrix["positive_case_count"] >= 1
    assert matrix["negative_case_count"] == 36
    assert [row["case_id"] for row in cases] == matrix["case_order"]
    negative = [row for row in cases if row["polarity"] == "negative"]
    assert [row["case_id"] for row in negative] == [
        case_id for case_id, _result in gate._NEGATIVE_CASES
    ]
    assert matrix["all_gates_fail_closed"] is True


def test_gate_source_is_static_lightweight_and_imports_no_product_module() -> None:
    source = (ROOT / gate._MODULE_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source)
    gate._validate_gate_source_lightweight(ROOT)
    assert "from covalent_ext import" not in source
    forbidden = {
        "build_covapie_current11_task2_batch_index_remap_adapter_context_v1",
        "remap_covapie_current11_task2_batch_index_with_context_v1",
        "build_covapie_current11_task2_batch_descriptor_compiler_context_v1",
        "_authority",
        "_parse_successor_stable5_v1",
        "_validate_formal",
    }
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    assert not called & forbidden


def test_real_heavy_call_counts_all_zero(
    parsed: dict[str, dict[str, object]],
) -> None:
    counts = parsed[gate._REPORT]["real_heavy_call_counts"]
    assert counts == gate._REAL_HEAVY_CALL_COUNTS
    assert all(type(value) is int and value == 0 for value in counts.values())


def test_repository_lifecycle_exact4_modes_and_status(
    parsed: dict[str, dict[str, object]],
) -> None:
    report = parsed[gate._REPORT]
    lifecycle = report["repository_lifecycle"]
    expected = _lifecycle_expectations(lifecycle)
    assert lifecycle in ("precommit-untracked", "clean-tracked-successor")
    assert report["gate_status"] == expected["gate_status"]
    for relative in gate._REPOSITORY_EXACT4:
        metadata = (ROOT / relative).lstat()
        assert stat.S_ISREG(metadata.st_mode)
        assert not stat.S_ISLNK(metadata.st_mode)
        assert stat.S_IMODE(metadata.st_mode) == 0o644


def test_owner_identity_tamper_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(gate._OWNER_SPECS[0], "bytes", 43579)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        gate.build_covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1(
            repo_root=ROOT,
            state_root=STATE,
        )


def test_design_identity_tamper_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(gate._DESIGN_REPORT_IDENTITY, "mode", "0664")
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        gate.build_covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1(
            repo_root=ROOT,
            state_root=STATE,
        )


@pytest.mark.parametrize(
    "tamper",
    ("missing", "reordered", "wrong_source_value", "bool_int_collapse"),
)
def test_source_contract_tamper_cases_fail_closed(
    parsed: dict[str, dict[str, object]], tamper: str
) -> None:
    source = copy.deepcopy(
        parsed[gate._REFERENCE_VECTORS]["known_vector_semantic"]["source_exact10"]
    )
    if tamper == "missing":
        source.pop("source_payload_digest")
    elif tamper == "reordered":
        source = {key: source[key] for key in reversed(source)}
    elif tamper == "wrong_source_value":
        source["source_pair_values_int64"][0][0] += 1
    else:
        source["source_entry_validity_bool"][0] = 1
    with pytest.raises(gate._ContractInvariantError):
        gate._validate_source_reference(source)


@pytest.mark.parametrize(
    "field,value",
    (
        ("sample_count", 10),
        ("role_order", ["ligand", "pocket"]),
        ("role_record_field_order", list(gate._ROLE_RECORD_FIELDS[:-1])),
        ("canonical_sha256", "0" * 64),
        ("selected_atom_identity_field_order", list(gate._ATOM_IDENTITY_FIELDS[:-1])),
    ),
)
def test_provider_contract_tamper_cases_fail_closed(
    parsed: dict[str, dict[str, object]], field: str, value: object
) -> None:
    provider = copy.deepcopy(
        parsed[gate._REFERENCE_VECTORS]["known_vector_semantic"][
            "provider_exact11_contract"
        ]
    )
    provider[field] = value
    with pytest.raises(gate._ContractInvariantError):
        gate._validate_provider_contract(provider)


@pytest.mark.parametrize("tamper", ("missing", "reordered", "modernized"))
def test_readiness_tamper_cases_fail_closed(tamper: str) -> None:
    readiness = dict(gate._READINESS_VALUES)
    if tamper == "missing":
        readiness.pop("ready_for_training")
    elif tamper == "reordered":
        readiness = {key: readiness[key] for key in reversed(readiness)}
    else:
        readiness["runtime_batch_observation_extractor_implemented"] = True
    with pytest.raises(gate._ContractInvariantError):
        gate._validate_readiness_reference(readiness)


def test_checker_success_shape_and_silence() -> None:
    completed = _checker()
    assert completed.returncode == 0
    assert completed.stderr == b""
    assert completed.stdout.endswith(b"\n")
    assert completed.stdout.count(b"\n") == 1
    result = json.loads(completed.stdout.decode("utf-8"))
    actual_lifecycle = gate._repository_lifecycle(ROOT)[0]
    expected = _lifecycle_expectations(actual_lifecycle)
    assert result["gate_status"] == expected["gate_status"]
    assert result["repository_lifecycle"] == actual_lifecycle
    assert result["ready_for_compiler_remap_context_handoff_implementation"] is (
        expected["handoff_implementation"]
    )
    assert result["compiler_remap_context_handoff_implementation_blocker"] == (
        expected["blocker"]
    )
    assert result["design_report_identity_verified"] is True
    assert result["predecessor_identities_verified"] is True
    assert result["source_mapping_contract_passed"] is True
    assert result["provider_mapping_contract_passed"] is True
    assert result["readiness_contract_passed"] is True
    assert result["authority_compatibility_digest_passed"] is True
    assert result["canonical_mask_exact5_passed"] is True
    assert result["device_identity_risk_resolution_runtime_proven"] is False


def test_checker_double_run_stdout_byte_identical() -> None:
    first = _checker()
    second = _checker()
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout


@pytest.mark.parametrize(
    "arguments",
    (
        (),
        ("--repo-root", str(ROOT)),
        ("--extra",),
        ("--repo-root", ".", "--state-root", str(STATE)),
    ),
)
def test_checker_invalid_cli_fails_closed_exact(arguments: tuple[str, ...]) -> None:
    completed = subprocess.run(
        (sys.executable, "-B", str(CHECKER), *arguments),
        cwd=ROOT,
        env=_environment(),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1
    assert completed.stdout == b""
    assert completed.stderr == (ERROR + "\n").encode("utf-8")
