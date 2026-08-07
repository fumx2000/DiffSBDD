from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import inspect
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1 as gate


REPO = Path(__file__).resolve().parents[1]
STATE = REPO.parent / "covapie-state"
EXACT6 = (
    "current11_task2_batch_descriptor_compiler_contract_manifest.json",
    "current11_task2_batch_descriptor_compiler_input_schema.json",
    "current11_task2_batch_descriptor_compiler_output_schema.json",
    "current11_task2_batch_descriptor_compiler_status_vocabulary.csv",
    "current11_task2_batch_descriptor_compiler_reference_vectors.json",
    "current11_task2_batch_descriptor_compiler_contract_gate_report.json",
)
EXACT4 = (
    "src/covalent_ext/covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1.py",
    "scripts/check_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1.py",
    "tests/test_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1.py",
    "docs/covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1_guide.md",
)


def _import_roots(source: str) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".")[0])
    return roots


def _alias_snapshot(canonical: Path) -> tuple[object, ...]:
    link = os.readlink(canonical)
    target = canonical.parent / link
    inventory = tuple(sorted(os.listdir(target)))
    return (
        gate._path_snapshot(canonical), link, gate._path_snapshot(target), inventory,
        tuple((name, gate._path_snapshot(target / name)) for name in inventory),
    )


@pytest.fixture(scope="session")
def artifacts() -> dict[str, bytes]:
    return gate.build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1(
        repo_root=REPO, state_root=STATE
    )


@pytest.fixture(scope="session")
def parsed(artifacts: dict[str, bytes]) -> dict[str, dict[str, object]]:
    return {
        name: json.loads(payload)
        for name, payload in artifacts.items()
        if name.endswith(".json")
    }


def test_public_api_is_unique_keyword_only_and_exact_dict(artifacts: dict[str, bytes]) -> None:
    assert gate.__all__ == (
        "build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1",
    )
    signature = inspect.signature(gate.build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1)
    assert tuple(signature.parameters) == ("repo_root", "state_root")
    assert all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in signature.parameters.values())
    assert type(artifacts) is dict
    assert tuple(artifacts) == EXACT6


def test_import_is_silent_and_has_no_forbidden_imports(capsys: pytest.CaptureFixture[str]) -> None:
    importlib.reload(gate)
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""
    imported = _import_roots((REPO / EXACT4[0]).read_text(encoding="utf-8"))
    assert not imported & {"torch", "numpy", "rdkit", "openbabel", "subprocess", "requests"}
    assert imported <= set(sys.stdlib_module_names) | {"__future__", "covalent_ext"}


def test_import_guard_detects_forbidden_import_from_modules() -> None:
    source = "from numpy import array\nfrom torch import tensor\n"
    assert _import_roots(source) & {"numpy", "torch"} == {"numpy", "torch"}


def test_exact6_are_canonical_safe_bytes(artifacts: dict[str, bytes]) -> None:
    for name, payload in artifacts.items():
        assert type(payload) is bytes and 0 < len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf")
        assert b"\0" not in payload and b"\r" not in payload
        assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
        if name.endswith(".json"):
            assert gate._json(json.loads(payload)) == payload


def test_double_build_byte_identical(artifacts: dict[str, bytes]) -> None:
    status_before = subprocess.run(
        ["git", "status", "--short"], cwd=REPO, capture_output=True, check=True,
    ).stdout
    carrier_before = gate._formal_snapshot(STATE / gate._FORMAL_RELATIVE)
    routing_before = _alias_snapshot(
        STATE / "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1"
    )
    second = gate.build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1(
        repo_root=REPO, state_root=STATE
    )
    assert second == artifacts
    assert subprocess.run(
        ["git", "status", "--short"], cwd=REPO, capture_output=True, check=True,
    ).stdout == status_before
    assert gate._formal_snapshot(STATE / gate._FORMAL_RELATIVE) == carrier_before
    assert _alias_snapshot(
        STATE / "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1"
    ) == routing_before


def test_contract_digest_manual_framing_and_report_excluded(artifacts: dict[str, bytes], parsed: dict[str, dict[str, object]]) -> None:
    digest = hashlib.sha256(gate._DOMAIN)
    for name in EXACT6[:5]:
        encoded = name.encode()
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(artifacts[name]).to_bytes(8, "big"))
        digest.update(artifacts[name])
    report = parsed[EXACT6[5]]
    assert digest.hexdigest() == report["contract_digest"] == gate._stable_digest(artifacts)
    changed = dict(artifacts)
    changed[EXACT6[5]] = b"different\n"
    assert gate._stable_digest(changed) == report["contract_digest"]


def test_contract_digest_fixed_known_vector() -> None:
    vector = {name: f"vector-{index}\n".encode() for index, name in enumerate(EXACT6[:5])}
    assert gate._stable_digest(vector) == "4ba56d47d2efcb9ae478e3b6b0b2b27dc030524e9020642a6704941bb8f4ac40"


def test_stable_artifacts_exclude_machine_lifecycle_nonce_and_self_digest(artifacts: dict[str, bytes], parsed: dict[str, dict[str, object]]) -> None:
    digest = parsed[EXACT6[5]]["contract_digest"].encode()
    forbidden = (str(REPO).encode(), str(STATE).encode(), b"origin/main", b"ahead", b"mtime", b"inode", b"d119fe50e06f875e3da69555c23712b1")
    for payload in list(artifacts.values())[:5]:
        assert digest not in payload
        assert not any(token in payload for token in forbidden)


def test_precommit_filter_hides_only_exact4_and_preserves_fifth(monkeypatch: pytest.MonkeyPatch) -> None:
    owner = gate._remap_gate._instance_builder._payload_builder._contract_gate
    original = owner._run_git
    fifth = "fifth_untracked_must_remain_visible.txt"

    def fake(root: Path, arguments: tuple[str, ...]) -> str:
        del root
        assert arguments in {
            ("status", "--porcelain=v1", "--untracked-files=all"),
            ("status", "--short"),
        }
        return "\n".join([*(f"?? {path}" for path in EXACT4), f"?? {fifth}"])

    monkeypatch.setattr(owner, "_run_git", fake)
    with gate._precommit_compatibility():
        for arguments in (
            ("status", "--porcelain=v1", "--untracked-files=all"),
            ("status", "--short"),
        ):
            assert owner._run_git(REPO, arguments) == f"?? {fifth}"
    assert owner._run_git is fake
    monkeypatch.setattr(owner, "_run_git", original)


def test_precommit_filter_rejects_tracked_shape_for_exact4(monkeypatch: pytest.MonkeyPatch) -> None:
    owner = gate._remap_gate._instance_builder._payload_builder._contract_gate
    original = owner._run_git

    def fake(root: Path, arguments: tuple[str, ...]) -> str:
        del root, arguments
        return f" M {EXACT4[0]}"

    monkeypatch.setattr(owner, "_run_git", fake)
    with gate._precommit_compatibility(), pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        owner._run_git(REPO, ("status", "--short"))
    assert owner._run_git is fake
    monkeypatch.setattr(owner, "_run_git", original)


def test_formal_carrier_binding_and_inventory(parsed: dict[str, dict[str, object]]) -> None:
    report = parsed[EXACT6[5]]
    manifest = parsed[EXACT6[0]]
    assert report["formal_runtime_carrier_verified"] is True
    assert report["formal_carrier_aggregate"] == gate._FORMAL_AGGREGATE
    assert report["formal_inventory_array_count"] == 12
    binding = manifest["formal_runtime_carrier_binding"]
    assert binding["canonical_relative_path"] == gate._FORMAL_RELATIVE
    assert binding["names_semantic_digest"] == gate._NAMES_DIGEST
    assert binding["hidden_nonce_bound"] is False


def test_formal_exact4_current_identity_and_modes() -> None:
    canonical = STATE / gate._FORMAL_RELATIVE
    assert canonical.is_symlink()
    match = gate._FORMAL_PATTERN.fullmatch(os.readlink(canonical))
    assert match and match.group(1) == gate._FORMAL_AGGREGATE
    target = canonical.parent / os.readlink(canonical)
    assert stat.S_IMODE(target.lstat().st_mode) == 0o755
    assert tuple(sorted(os.listdir(target))) == tuple(sorted(gate._FORMAL_NAMES))
    for name, (size, digest) in gate._FORMAL_IDENTITIES.items():
        path = target / name
        payload = path.read_bytes()
        assert stat.S_IMODE(path.lstat().st_mode) == 0o644
        assert (len(payload), hashlib.sha256(payload).hexdigest()) == (size, digest)


def test_source_exact11_and_exact22_provider(parsed: dict[str, dict[str, object]]) -> None:
    vectors = parsed[EXACT6[4]]
    provider = vectors["identity_provider"]
    assert len(provider) == 11
    assert sum(len(row["roles"]) for row in provider) == 22
    assert vectors["identity_provider_digest"] == gate._provider_digest(provider)
    canonical = vectors["canonical_runtime_observation"]
    assert len(canonical["batch_sample_keys"]) == 11
    assert canonical["ligand_lengths"] == list(gate._LIGAND_LENGTHS)
    assert canonical["pocket_lengths"] == list(gate._POCKET_LENGTHS)


def test_input_output_and_status_closed_shapes(parsed: dict[str, dict[str, object]], artifacts: dict[str, bytes]) -> None:
    input_schema = parsed[EXACT6[1]]
    output_schema = parsed[EXACT6[2]]
    assert tuple(input_schema["field_order"]) == gate._INPUT_FIELDS
    assert tuple(input_schema["required_fields"]) == gate._INPUT_FIELDS[:10]
    assert tuple(input_schema["optional_fields"]) == gate._INPUT_FIELDS[10:]
    assert tuple(output_schema["field_order"]) == gate._OUTPUT_FIELDS
    assert tuple(output_schema["adapter_input_exact18_field_order"]) == gate._EXACT18_FIELDS
    rows = artifacts[EXACT6[3]].decode().splitlines()
    assert len(rows) == 16
    assert tuple(row.split(",")[1] for row in rows[1:]) == gate._STATUS_ORDER


def test_validation_priority_and_exact30_invariants(parsed: dict[str, dict[str, object]]) -> None:
    manifest = parsed[EXACT6[0]]
    assert tuple(manifest["validation_order"]) == gate._VALIDATION_ORDER
    assert len(manifest["fail_closed_invariants"]) == 30
    assert manifest["auxiliary_module_scope"]["canonical_masks"] == [
        "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead",
        "scaffold_only", "scaffold_plus_linker_plus_warhead",
    ]


@pytest.mark.parametrize(
    "case_id",
    ["canonical_exact11", "reversed_exact11", "mixed_10_4_0_7_2", "subset_10_4_0", "no_joint", "empty_batch"],
)
def test_success_reference_cases(case_id: str, parsed: dict[str, dict[str, object]]) -> None:
    cases = {row["case_id"]: row for row in parsed[EXACT6[4]]["reference_cases"]}
    row = cases[case_id]
    assert row["expected_compiler_status"] == "COMPILED_EXACT"
    assert row["expected_failure_reason"] == "NONE"
    assert row["expected_exact18_present"] is True
    assert row["adapter_composition_required"] is True
    assert set(row["compiler_output"]["adapter_input_exact18"]) == set(gate._EXACT18_FIELDS)


def test_private_evaluator_returns_exact18_in_frozen_order(parsed: dict[str, dict[str, object]]) -> None:
    vectors = parsed[EXACT6[4]]
    canonical = next(row for row in vectors["reference_cases"] if row["case_id"] == "canonical_exact11")
    serialized_exact18 = canonical["compiler_output"]["adapter_input_exact18"]
    source = {field: copy.deepcopy(serialized_exact18[field]) for field in gate._EXACT18_FIELDS[:10]}
    output = gate._evaluate_reference_case_v1(
        copy.deepcopy(vectors["canonical_runtime_observation"]),
        source_contract=source,
        identity_provider=copy.deepcopy(vectors["identity_provider"]),
        expected_identity_provider_digest=vectors["identity_provider_digest"],
    )
    assert tuple(output) == gate._OUTPUT_FIELDS
    assert tuple(output["adapter_input_exact18"]) == gate._EXACT18_FIELDS


def _direct_contract_inputs(
    parsed: dict[str, dict[str, object]],
) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]], str]:
    vectors = parsed[EXACT6[4]]
    canonical = next(row for row in vectors["reference_cases"] if row["case_id"] == "canonical_exact11")
    exact18 = canonical["compiler_output"]["adapter_input_exact18"]
    source = {field: copy.deepcopy(exact18[field]) for field in gate._EXACT18_FIELDS[:10]}
    return (
        copy.deepcopy(vectors["canonical_runtime_observation"]), source,
        copy.deepcopy(vectors["identity_provider"]), vectors["identity_provider_digest"],
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "schema_version", "pair_bool", "pair_float", "offset_bool",
        "entry_validity_int", "sample_validity_int", "duplicate_row_id",
        "identity_missing_field", "identity_empty", "identity_untrimmed",
    ],
)
def test_source_contract_exact_type_and_identity_drift_fails_closed(
    mutation: str, parsed: dict[str, dict[str, object]], monkeypatch: pytest.MonkeyPatch,
) -> None:
    observation, source, provider, provider_digest = _direct_contract_inputs(parsed)
    if mutation == "schema_version":
        source["schema_version"] = "drift"
    elif mutation == "pair_bool":
        source["source_pair_values_int64"][0][0] = True
    elif mutation == "pair_float":
        source["source_pair_values_int64"][0][1] = 3.0
    elif mutation == "offset_bool":
        source["source_sample_offsets_int64"][0] = False
    elif mutation == "entry_validity_int":
        source["source_entry_validity_bool"][0] = 1
    elif mutation == "sample_validity_int":
        source["source_sample_validity_bool"][0] = 1
    elif mutation == "duplicate_row_id":
        source["source_sample_order"][1]["sample_index_row_id"] = source["source_sample_order"][0]["sample_index_row_id"]
    elif mutation == "identity_missing_field":
        del source["source_sample_order"][0]["pdb_id"]
    elif mutation == "identity_empty":
        source["source_sample_order"][0]["pdb_id"] = ""
    else:
        source["source_sample_order"][0]["pdb_id"] = " 6BV6"

    def adapter_forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("failure cases must not call the public adapter")

    monkeypatch.setattr(
        gate._adapter, "build_covapie_current11_task2_batch_index_remap_adapter_v1",
        adapter_forbidden,
    )
    assert gate._validate_source_contract_exact_v1(source) is False
    output = gate._evaluate_reference_case_v1(
        observation, source_contract=source, identity_provider=provider,
        expected_identity_provider_digest=provider_digest,
    )
    assert output["compiler_status"] == "SOURCE_CONTRACT_MISMATCH"
    assert output["failure_reason"] == "SOURCE_CONTRACT_MISMATCH"
    assert output["adapter_input_exact18"] is None


@pytest.mark.parametrize("debug_kind", ["recursive", "non_json_safe"])
def test_debug_transport_fail_closed_without_exception(
    debug_kind: str, parsed: dict[str, dict[str, object]],
) -> None:
    observation, source, provider, provider_digest = _direct_contract_inputs(parsed)
    debug: dict[str, object] = {}
    if debug_kind == "recursive":
        debug["self"] = debug
    else:
        debug["value"] = object()
    observation["debug_rank_metadata"] = debug
    output = gate._evaluate_reference_case_v1(
        observation, source_contract=source, identity_provider=provider,
        expected_identity_provider_digest=provider_digest,
    )
    assert output["compiler_status"] == "BATCH_OBSERVATION_SCHEMA_MISMATCH"
    assert output["failure_reason"] == "BATCH_OBSERVATION_SCHEMA_MISMATCH"
    assert output["adapter_input_exact18"] is None


@pytest.mark.parametrize(
    "case_id,expected",
    [
        ("duplicate_runtime_key", "BATCH_SAMPLE_KEY_DUPLICATED"),
        ("unknown_runtime_key", "BATCH_SAMPLE_KEY_UNKNOWN"),
        ("ambiguous_provider_match", "BATCH_SAMPLE_KEY_AMBIGUOUS"),
        ("non_source_known_sample", "NON_SOURCE_SAMPLE_NOT_ADMISSIBLE_IN_CURRENT11_COMPILER_V1"),
        ("invalid_key_type", "BATCH_SAMPLE_KEY_INVALID"),
        ("empty_key", "BATCH_SAMPLE_KEY_INVALID"),
        ("untrimmed_key", "BATCH_SAMPLE_KEY_INVALID"),
        ("wrong_runtime_schema", "BATCH_OBSERVATION_SCHEMA_MISMATCH"),
        ("wrong_sample_key_schema", "BATCH_OBSERVATION_SCHEMA_MISMATCH"),
        ("virtual_policy_mismatch", "VIRTUAL_NODE_POLICY_MISMATCH"),
        ("wrong_ligand_length", "ROLE_LENGTH_MISMATCH"),
        ("wrong_pocket_length", "ROLE_LENGTH_MISMATCH"),
        ("bool_length", "ROLE_LENGTH_MISMATCH"),
        ("float_length", "ROLE_LENGTH_MISMATCH"),
        ("wrong_ligand_membership", "MEMBERSHIP_MASK_MISMATCH"),
        ("wrong_pocket_membership", "MEMBERSHIP_MASK_MISMATCH"),
        ("bool_membership", "MEMBERSHIP_MASK_MISMATCH"),
        ("float_membership", "MEMBERSHIP_MASK_MISMATCH"),
        ("membership_wrong_ordinal_order", "MEMBERSHIP_MASK_MISMATCH"),
        ("consistency_buffer_mismatch", "ROLE_LENGTH_MISMATCH"),
        ("source_contract_override", "SOURCE_CONTRACT_MISMATCH"),
        ("provider_missing", "IDENTITY_PROVIDER_MISSING"),
        ("provider_digest_drift", "IDENTITY_PROVIDER_MISMATCH"),
        ("missing_pocket_role", "ROLE_TABLE_AUTHORITY_MISSING"),
        ("missing_ligand_role", "ROLE_TABLE_AUTHORITY_MISSING"),
        ("unknown_joint_descriptor", "BATCH_OBSERVATION_SCHEMA_MISMATCH"),
        ("unknown_top_level_field", "BATCH_OBSERVATION_SCHEMA_MISMATCH"),
        ("missing_required_field", "BATCH_OBSERVATION_SCHEMA_MISMATCH"),
        ("runtime_name_path_drift", "BATCH_SAMPLE_KEY_UNKNOWN"),
    ],
)
def test_hard_failure_matrix(case_id: str, expected: str, parsed: dict[str, dict[str, object]]) -> None:
    cases = {row["case_id"]: row for row in parsed[EXACT6[4]]["reference_cases"]}
    row = cases[case_id]
    assert row["expected_compiler_status"] == expected
    assert row["expected_failure_reason"] == expected
    assert row["expected_exact18_present"] is False
    assert row["adapter_composition_required"] is False
    assert row["compiler_output"]["adapter_input_exact18"] is None


@pytest.mark.parametrize(
    "case_id", ["wrong_ligand_length", "duplicate_runtime_key", "provider_digest_drift"],
)
def test_hard_failure_preserves_gate_level_readiness(
    case_id: str, parsed: dict[str, dict[str, object]],
) -> None:
    cases = {row["case_id"]: row for row in parsed[EXACT6[4]]["reference_cases"]}
    output = cases[case_id]["compiler_output"]
    readiness = output["readiness"]
    assert output["adapter_input_exact18"] is None
    assert output["compiler_status"] == output["failure_reason"]
    assert readiness["task2_batch_descriptor_compiler_contract_gate_passed"] is True
    assert readiness["formal_runtime_carrier_verified"] is True
    assert readiness["source_contract_verified"] is True
    assert readiness["identity_provider_verified"] is True
    assert readiness["ready_for_task2_batch_descriptor_compiler_implementation"] is True
    assert readiness["ready_for_training"] is False


def test_all_reference_cases_share_exact_gate_readiness(parsed: dict[str, dict[str, object]]) -> None:
    cases = parsed[EXACT6[4]]["reference_cases"]
    assert len(cases) == 35
    expected = gate._gate_readiness()
    assert all(row["compiler_output"]["readiness"] == expected for row in cases)
    assert expected["task2_batch_descriptor_compiler_contract_gate_implemented"] is True
    assert expected["task2_batch_descriptor_compiler_contract_designed"] is True
    assert expected["task2_batch_descriptor_compiler_implemented"] is False
    assert expected["ready_for_training"] is False


def test_public_adapter_composition_and_empty_compatibility(parsed: dict[str, dict[str, object]]) -> None:
    vectors = parsed[EXACT6[4]]
    report = parsed[EXACT6[5]]
    assert set(vectors["public_adapter_compositions"]) == {
        "canonical_exact11", "reversed_exact11", "mixed_10_4_0_7_2",
        "subset_10_4_0", "no_joint", "empty_batch",
    }
    assert all(row["remap_status"] == "REMAPPED_EXACT" for row in vectors["public_adapter_compositions"].values())
    assert report["public_adapter_composition_case_count"] == 6
    assert report["public_adapter_composition_all_passed"] is True
    assert report["empty_batch_adapter_compatible"] is True
    assert vectors["public_adapter_compositions"]["empty_batch"]["pair_values_batch_indices"] == []


def test_no_joint_is_successful_component_unavailability(parsed: dict[str, dict[str, object]]) -> None:
    cases = {row["case_id"]: row for row in parsed[EXACT6[4]]["reference_cases"]}
    row = cases["no_joint"]
    assert row["expected_joint_component_status"] == "JOINT_LAYOUT_UNAVAILABLE"
    assert row["compiler_output"]["adapter_input_exact18"]["joint_layout_descriptor"] is None
    assert parsed[EXACT6[4]]["public_adapter_compositions"]["no_joint"]["pair_values_joint_global_indices"] is None


def test_readiness_is_truthful_and_training_fail_closed(parsed: dict[str, dict[str, object]]) -> None:
    readiness = parsed[EXACT6[5]]["readiness"]
    assert readiness["task2_batch_descriptor_compiler_contract_gate_implemented"] is True
    assert readiness["task2_batch_descriptor_compiler_contract_gate_passed"] is True
    assert readiness["task2_batch_descriptor_compiler_implemented"] is False
    assert readiness["runtime_batch_observation_extractor_implemented"] is False
    assert readiness["ready_for_task2_batch_descriptor_compiler_implementation"] is True
    assert readiness["feature_semantics_reaudit_required_before_training"] is True
    assert readiness["ready_for_training"] is False


def test_design_markdown_is_non_runtime_lineage(parsed: dict[str, dict[str, object]], monkeypatch: pytest.MonkeyPatch) -> None:
    lineage = parsed[EXACT6[0]]["source_lineage"]["non_runtime_design"]
    assert lineage["read_by_gate"] is False and lineage["contract_authority"] is False
    original = Path.read_bytes

    def guarded(self: Path) -> bytes:
        assert str(self).replace("\\", "/").endswith(gate._DESIGN_RELATIVE) is False
        return original(self)

    monkeypatch.setattr(Path, "read_bytes", guarded)
    gate._validate_formal(STATE)


def test_repository_exact4_modes_and_text_safety() -> None:
    for relative in EXACT4:
        path = REPO / relative
        metadata = path.lstat()
        payload = path.read_bytes()
        assert stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
        assert stat.S_IMODE(metadata.st_mode) == 0o644
        assert len(payload) < 1024 * 1024 and not payload.startswith(b"\xef\xbb\xbf")
        assert b"\0" not in payload and b"\r" not in payload
        assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
        assert all(not line.endswith((b" ", b"\t")) for line in payload.splitlines())


@pytest.mark.parametrize(
    "arguments",
    [[], ["-h"], ["--help"], ["--output", "x"], ["--write"], ["extra"], ["--repo-root", str(REPO)]],
)
def test_checker_rejects_invalid_cli(arguments: list[str]) -> None:
    environment = {**os.environ, "PYTHONPATH": "src", "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [sys.executable, "scripts/check_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1.py", *arguments],
        cwd=REPO, env=environment, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 1 and result.stdout == ""
    assert result.stderr == gate._ERROR + "\n"
