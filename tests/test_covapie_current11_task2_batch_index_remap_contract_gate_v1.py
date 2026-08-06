from __future__ import annotations

import ast
import copy
import csv
import hashlib
import importlib
import inspect
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import covalent_ext.covapie_current11_task2_batch_index_remap_contract_gate_v1 as gate


REPO = Path(__file__).resolve().parents[1]
STATE = Path("/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/covapie-state")
ERROR = "COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_CONTRACT_GATE_V1_ERROR"
NAMES = (
    "current11_task2_batch_index_remap_contract_manifest.json",
    "current11_task2_batch_index_remap_input_schema.json",
    "current11_task2_batch_index_remap_output_schema.json",
    "current11_task2_batch_index_remap_status_vocabulary.csv",
    "current11_task2_batch_index_remap_reference_vectors.json",
    "current11_task2_batch_index_remap_contract_gate_report.json",
)


@pytest.fixture(scope="session")
def artifacts() -> dict[str, bytes]:
    return gate.build_covapie_current11_task2_batch_index_remap_contract_gate_v1(
        repo_root=REPO,
        state_root=STATE,
    )


@pytest.fixture(scope="session")
def decoded(artifacts: dict[str, bytes]) -> dict[str, dict[str, object]]:
    return {name: json.loads(payload) for name, payload in artifacts.items() if name.endswith(".json")}


@pytest.fixture()
def canonical_authority(decoded: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    records = decoded[NAMES[4]]["exact22_source_to_local"]
    tables = []
    for sample in records:
        roles = {}
        for role in sample["roles"]:
            roles[role["role"]] = {
                **copy.deepcopy(role),
                "parser_output_atom_count": role["retained_heavy_count"],
                "source_to_parser_local": {str(role["selected_source_row_index_0based"]): role["selected_parser_local_index"]},
            }
        tables.append({"sample_identity": copy.deepcopy(sample["sample_identity"]), "roles": roles})
    return tables


@pytest.fixture()
def canonical_case(canonical_authority: list[dict[str, object]]) -> dict[str, object]:
    return gate._reference_input(list(range(11)), canonical_authority)


def _manual_digest(artifacts: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    digest.update(b"COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_CONTRACT_GATE_V1\0")
    for name in NAMES[:5]:
        encoded = name.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(artifacts[name]).to_bytes(8, "big"))
        digest.update(artifacts[name])
    return digest.hexdigest()


def test_unique_keyword_only_public_api() -> None:
    assert gate.__all__ == ("build_covapie_current11_task2_batch_index_remap_contract_gate_v1",)
    signature = inspect.signature(gate.build_covapie_current11_task2_batch_index_remap_contract_gate_v1)
    assert tuple(signature.parameters) == ("repo_root", "state_root")
    assert all(value.kind is inspect.Parameter.KEYWORD_ONLY for value in signature.parameters.values())


def test_exact_builtin_dict_exact6_order_and_bytes(artifacts: dict[str, bytes]) -> None:
    assert type(artifacts) is dict
    assert tuple(artifacts) == NAMES
    assert len(artifacts) == 6
    assert all(type(value) is bytes for value in artifacts.values())


def test_artifact_encoding_and_canonical_serialization(artifacts: dict[str, bytes]) -> None:
    for name, payload in artifacts.items():
        assert len(payload) < 1024 * 1024
        assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
        assert b"\0" not in payload and b"\r" not in payload
        assert not payload.startswith(b"\xef\xbb\xbf")
        if name.endswith(".json"):
            assert gate._json(json.loads(payload)) == payload
    rows = list(csv.DictReader(io.StringIO(artifacts[NAMES[3]].decode(), newline="")))
    assert len(rows) == 18


def test_silent_import_and_no_heavy_imports() -> None:
    code = "import sys; import covalent_ext.covapie_current11_task2_batch_index_remap_contract_gate_v1; print(','.join(sorted(set(sys.modules)&{'torch','numpy','rdkit','openbabel'})))"
    run = subprocess.run([sys.executable, "-c", code], cwd=REPO, env={**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONDONTWRITEBYTECODE": "1"}, text=True, capture_output=True, check=False)
    assert run.returncode == 0 and run.stderr == "" and run.stdout == "\n"


def test_module_has_no_subprocess_or_public_adapter() -> None:
    source = Path(gate.__file__).read_text()
    tree = ast.parse(source)
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    assert "subprocess" not in imports
    assert "torch" not in imports and "numpy" not in imports and "rdkit" not in imports and "openbabel" not in imports
    assert not any(name for name in gate.__all__ if "adapter" in name)


def test_design_markdown_is_nonruntime_lineage(decoded: dict[str, dict[str, object]]) -> None:
    lineage = decoded[NAMES[0]]["source_lineage"]["non_runtime_lineage"]
    assert lineage == {"relative_path": gate._DESIGN_RELATIVE, "SHA256": gate._DESIGN_SHA, "runtime_dependency": False, "contract_authority": False}
    source = Path(gate.__file__).read_text()
    assert "_read_regular(state, _DESIGN_RELATIVE" not in source


def test_stable_artifacts_exclude_absolute_paths_and_lifecycle(artifacts: dict[str, bytes]) -> None:
    forbidden = (str(REPO), str(STATE), '"HEAD"', "origin/main", "ahead", "behind", "mtime", "inode")
    combined = b"".join(artifacts[name] for name in NAMES[:5]).decode()
    assert all(value not in combined for value in forbidden)


def test_predecessor_lineage_and_digests(decoded: dict[str, dict[str, object]]) -> None:
    manifest = decoded[NAMES[0]]
    lineage = manifest["source_lineage"]
    assert lineage["projection_instance_builder"]["module_SHA256"] == gate._PROJECTION_MODULE_SHA
    assert lineage["projection_instance_builder"]["projection_digest"] == gate._PROJECTION_DIGEST
    assert lineage["payload_builder"]["module_SHA256"] == gate._PAYLOAD_MODULE_SHA
    assert lineage["payload_builder"]["payload_digest"] == gate._PAYLOAD_DIGEST
    assert lineage["projection_contract_gate"]["module_SHA256"] == gate._CONTRACT_MODULE_SHA
    assert lineage["projection_contract_gate"]["contract_digest"] == gate._CONTRACT_DIGEST


def test_projection_exact2_identities(decoded: dict[str, dict[str, object]]) -> None:
    assert decoded[NAMES[0]]["source_lineage"]["projection_instance_builder"]["Exact2_SHA256"] == gate._PROJECTION_EXACT2
    report = decoded[NAMES[5]]
    assert report["projection_exact2_double_build_identical"] is True
    assert report["projection_instance_builder_passed"] is True
    assert report["payload_builder_passed"] is True
    assert report["projection_contract_gate_passed"] is True


def test_compatibility_filters_only_exact4_and_retains_fifth(monkeypatch: pytest.MonkeyPatch) -> None:
    underlying = gate._instance_builder._payload_builder._contract_gate
    original = underlying._run_git
    fifth = "?? unrelated.txt"
    monkeypatch.setattr(underlying, "_run_git", lambda _root, _args: "\n".join([*(f"?? {p}" for p in gate._REPOSITORY_EXACT4), fifth]))
    patched_original = underlying._run_git
    with gate._predecessor_status_compatibility():
        assert underlying._run_git(REPO, ("status", "--porcelain=v1", "--untracked-files=all")) == fifth
    assert underlying._run_git is patched_original
    monkeypatch.setattr(underlying, "_run_git", original)


def test_compatibility_rejects_non_untracked_shape_and_restores(monkeypatch: pytest.MonkeyPatch) -> None:
    underlying = gate._instance_builder._payload_builder._contract_gate
    path = gate._REPOSITORY_EXACT4[0]
    fake = lambda _root, _args: f" M {path}"
    monkeypatch.setattr(underlying, "_run_git", fake)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        with gate._predecessor_status_compatibility():
            underlying._run_git(REPO, ("status", "--porcelain=v1", "--untracked-files=all"))
    assert underlying._run_git is fake


def test_compatibility_nested_restoration(monkeypatch: pytest.MonkeyPatch) -> None:
    underlying = gate._instance_builder._payload_builder._contract_gate
    fake = lambda _root, _args: ""
    monkeypatch.setattr(underlying, "_run_git", fake)
    with gate._predecessor_status_compatibility():
        outer = underlying._run_git
        with gate._predecessor_status_compatibility():
            assert underlying._run_git is not outer
        assert underlying._run_git is outer
    assert underlying._run_git is fake


def test_runtime_source_inventory_exact(decoded: dict[str, dict[str, object]]) -> None:
    inventory = decoded[NAMES[0]]["source_lineage"]["runtime_source_code"]
    assert [row["relative_path"] for row in inventory] == list(gate._RUNTIME_SOURCES)
    assert len(inventory) == 5
    for row in inventory:
        expected = gate._RUNTIME_SOURCES[row["relative_path"]]
        assert (row["bytes"], row["LF"], row["SHA256"], row["Git_blob"]) == expected


def test_runtime_symbols_and_anchors_are_bounded(decoded: dict[str, dict[str, object]]) -> None:
    inventory = decoded[NAMES[0]]["source_lineage"]["runtime_source_code"]
    assert sum(len(row["semantic_anchors"]) for row in inventory) == decoded[NAMES[5]]["runtime_semantic_anchor_count"]
    for row in inventory:
        assert row["validated_symbols"] == list(gate._RUNTIME_VALIDATED_SYMBOLS[row["relative_path"]])
        assert row["semantic_anchors"] == list(gate._RUNTIME_ANCHORS[row["relative_path"]])


def test_runtime_source_anchor_drift_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    changed = dict(gate._RUNTIME_ANCHORS)
    changed["dataset.py"] = (*changed["dataset.py"], "impossible semantic anchor")
    monkeypatch.setattr(gate, "_RUNTIME_ANCHORS", changed)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        gate._runtime_inventory(REPO)


def test_heavy_projection_semantics_are_frozen(decoded: dict[str, dict[str, object]]) -> None:
    assert gate._classify("H") == "explicit_hydrogen"
    assert gate._classify("C") == "supported_checkpoint_heavy_atom"
    assert gate._classify("Xe") == "unsupported_nonhydrogen"
    assert gate._classify("bad") == "missing_or_invalid"
    records = decoded[NAMES[4]]["exact22_source_to_local"]
    assert sum(role["unsupported_nonhydrogen_count"] for sample in records for role in sample["roles"]) == 0
    assert all(role["source_to_parser_exact_one"] and role["selected_row_retained"] for sample in records for role in sample["roles"])


def test_current11_source_contract_exact(decoded: dict[str, dict[str, object]]) -> None:
    source = decoded[NAMES[0]]["current11_source_contract"]
    assert [row["sample_index_row_id"] for row in source["sample_order"]] == [row[0] for row in gate._SAMPLES]
    assert source["pair_values_source_row_indices"] == [list(value) for value in gate._SOURCE_PAIRS]
    assert source["sample_pair_offsets"] == list(range(12))
    assert source["entry_validity"] == [True] * 11 and source["sample_validity"] == [True] * 11
    assert source["locator_semantics"] == "derived_row_index_bound_to_exact_atom_table_bytes_and_order"
    assert source["permanent_chemical_identifier"] is False and source["model_input_allowed_now"] is False and source["batch_index_remap_required"] is True


def test_exact22_counts_and_vectors(decoded: dict[str, dict[str, object]]) -> None:
    records = decoded[NAMES[4]]["exact22_source_to_local"]
    assert len(records) == 11 and sum(len(row["roles"]) for row in records) == 22
    pocket = [row["roles"][0] for row in records]
    ligand = [row["roles"][1] for row in records]
    assert [row["row_count"] for row in pocket] == list(gate._POCKET_ROWS)
    assert [row["row_count"] for row in ligand] == list(gate._LIGAND_ROWS)
    assert [row["explicit_hydrogen_count"] for row in pocket] == list(gate._POCKET_H)
    assert [row["explicit_hydrogen_count"] for row in ligand] == list(gate._LIGAND_H)
    assert [row["retained_heavy_count"] for row in pocket] == list(gate._POCKET_RETAINED)
    assert [row["retained_heavy_count"] for row in ligand] == list(gate._LIGAND_RETAINED)
    assert [row["selected_parser_local_index"] for row in pocket] == list(gate._POCKET_LOCAL)
    assert [row["selected_parser_local_index"] for row in ligand] == list(gate._LIGAND_LOCAL)


def test_exact22_paths_hashes_and_selected_identity(decoded: dict[str, dict[str, object]]) -> None:
    records = decoded[NAMES[4]]["exact22_source_to_local"]
    for sample in records:
        for role in sample["roles"]:
            path = REPO / role["relative_path"]
            assert path.is_file() and not path.is_symlink()
            payload = path.read_bytes()
            assert hashlib.sha256(payload).hexdigest() == role["SHA256"] == role["row_order_digest"]
            assert role["selected_atom_identity"]["atom_site_id"]
            assert role["committed_projection_matrix_local_index"] == role["selected_parser_local_index"]


def test_four_index_spaces_and_join_contract(decoded: dict[str, dict[str, object]]) -> None:
    manifest = decoded[NAMES[0]]
    assert [row["name"] for row in manifest["index_space_definitions"]] == ["source_atom_table_data_row_index", "parser_sample_local_index", "collated_batch_segment_index", "dynamics_joint_global_node_index"]
    join = manifest["join_contract"]
    assert join["name"] == gate._JOIN
    assert join["all_required_bindings_must_match"] is True and join["single_field_fallback_forbidden"] is True
    assert len(join["required_composite_binding"]["atom_identity"]) == 8


def test_input_exact18_schema(decoded: dict[str, dict[str, object]]) -> None:
    schema = decoded[NAMES[1]]
    assert schema["schema_version"] == gate._INPUT_SCHEMA
    assert len(schema["field_order"]) == 18
    assert [row["field_name"] for row in schema["fields"]] == schema["field_order"]
    assert schema["required_fields"] == schema["field_order"][:15]
    assert schema["optional_fields"] == schema["field_order"][15:]
    assert len(schema["forbidden_input_semantics"]) == 10
    assert all(row["model_input_allowed_now"] is False and row["loss_participation_allowed_now"] is False for row in schema["fields"])


def test_input_schema_exact_shapes(decoded: dict[str, dict[str, object]]) -> None:
    fields = {row["field_name"]: row for row in decoded[NAMES[1]]["fields"]}
    assert fields["source_sample_order"]["logical_shape"] == "[S]"
    assert fields["batch_sample_order"]["logical_shape"] == "[B]"
    assert fields["batch_sample_atom_identity_tables"]["logical_shape"] == "[B]"
    assert fields["source_entry_validity_bool"]["logical_shape"] == "[P]"
    assert fields["source_sample_validity_bool"]["logical_shape"] == "[S]"


def test_reference_input_uses_exact_declared_fields(canonical_case: dict[str, object]) -> None:
    assert set(gate._INPUT_FIELD_ORDER[:15]).issubset(canonical_case)
    assert set(canonical_case).issubset(set(gate._INPUT_FIELD_ORDER))
    assert set(canonical_case) - set(gate._INPUT_FIELD_ORDER[:15]) == {"joint_layout_descriptor"}
    assert not set(canonical_case) & gate._LEGACY_INPUT_ALIASES
    synthetic = gate._synthetic_case()
    assert set(synthetic).issubset(set(gate._INPUT_FIELD_ORDER))
    assert "synthetic_future_case" not in synthetic
    assert synthetic["parser_schema_version"] == gate._PARSER_SCHEMA
    assert synthetic["collate_schema_version"] == gate._COLLATE_SCHEMA


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_projection_digest", "0" * 64),
        ("source_payload_digest", "0" * 64),
        ("parser_schema_version", "wrong_parser_v1"),
        ("collate_schema_version", "wrong_collate_v1"),
    ],
)
def test_lineage_and_schema_version_mismatch_fail_closed(canonical_case: dict[str, object], canonical_authority: list[dict[str, object]], field: str, value: str) -> None:
    canonical_case[field] = value
    output = gate._evaluate_reference_case(canonical_case, authoritative_tables=canonical_authority)
    assert output["remap_status"] == output["failure_reason"] == "SCHEMA_VERSION_MISMATCH"
    assert output["pair_values_source_row_indices"] == []
    assert output["pair_values_parser_local_indices"] == []
    assert output["pair_values_batch_indices"] == []


@pytest.mark.parametrize("field", list(gate._INPUT_FIELD_ORDER[:15]))
def test_missing_required_input_field_is_schema_mismatch(canonical_case: dict[str, object], canonical_authority: list[dict[str, object]], field: str) -> None:
    canonical_case.pop(field)
    output = gate._evaluate_reference_case(canonical_case, authoritative_tables=canonical_authority)
    assert output["remap_status"] == output["failure_reason"] == "SCHEMA_VERSION_MISMATCH"


@pytest.mark.parametrize(
    ("official", "legacy"),
    [
        ("source_pair_values_int64", "source_pair_values"),
        ("source_sample_offsets_int64", "source_sample_offsets"),
        ("source_entry_validity_bool", "source_entry_validity"),
        ("source_sample_validity_bool", "source_sample_validity"),
    ],
)
def test_legacy_input_alias_is_rejected(canonical_case: dict[str, object], canonical_authority: list[dict[str, object]], official: str, legacy: str) -> None:
    canonical_case[legacy] = canonical_case.pop(official)
    output = gate._evaluate_reference_case(canonical_case, authoritative_tables=canonical_authority)
    assert output["remap_status"] == output["failure_reason"] == "SCHEMA_VERSION_MISMATCH"
    assert output["pair_values_batch_indices"] == []


def test_unknown_extra_input_field_is_rejected(canonical_case: dict[str, object], canonical_authority: list[dict[str, object]]) -> None:
    canonical_case["unknown_extra"] = True
    output = gate._evaluate_reference_case(canonical_case, authoritative_tables=canonical_authority)
    assert output["remap_status"] == output["failure_reason"] == "SCHEMA_VERSION_MISMATCH"


def test_exact_optional_input_fields_are_accepted(canonical_case: dict[str, object], canonical_authority: list[dict[str, object]]) -> None:
    canonical_case["debug_coordinates"] = None
    canonical_case["debug_rank_metadata"] = {"rank": 0, "debug_only": True}
    output = gate._evaluate_reference_case(canonical_case, authoritative_tables=canonical_authority)
    assert output["remap_status"] == "REMAPPED_EXACT"


def test_invalid_source_identity_fails_deterministically(canonical_case: dict[str, object], canonical_authority: list[dict[str, object]]) -> None:
    canonical_case["source_sample_order"][0].pop("pdb_id")
    output = gate._evaluate_reference_case(canonical_case, authoritative_tables=canonical_authority)
    assert output["remap_status"] == output["failure_reason"] == "SOURCE_TABLE_IDENTITY_MISMATCH"


def test_success_output_digests_come_from_validated_input(canonical_case: dict[str, object], canonical_authority: list[dict[str, object]]) -> None:
    output = gate._evaluate_reference_case(canonical_case, authoritative_tables=canonical_authority)
    assert output["remap_status"] == "REMAPPED_EXACT"
    assert output["source_projection_digest"] == canonical_case["source_projection_digest"] == gate._PROJECTION_DIGEST
    assert output["source_payload_digest"] == canonical_case["source_payload_digest"] == gate._PAYLOAD_DIGEST


def test_output_exact17_schema_and_joint_normalization(decoded: dict[str, dict[str, object]]) -> None:
    schema = decoded[NAMES[2]]
    assert schema["schema_version"] == gate._OUTPUT_SCHEMA
    assert len(schema["field_order"]) == 17
    joint = next(row for row in schema["fields"] if row["field_name"] == "pair_values_joint_global_indices")
    assert joint["presence"] == "always" and joint["nullability"] is True
    assert schema["joint_field_normalization"]["unavailable_value"] is None
    assert schema["joint_field_normalization"]["segment_success_preserved_when_unavailable"] is True
    assert schema["numeric_placeholder_semantics"] == {"sentinel_placeholder_usage_forbidden": True, "valid_zero_index_allowed": True, "negative_index_allowed": False, "missing_numeric_entry_is_omitted": True, "joint_unavailable_representation": None}


def test_output_schema_exact_shapes(decoded: dict[str, dict[str, object]]) -> None:
    fields = {row["field_name"]: row for row in decoded[NAMES[2]]["fields"]}
    assert fields["pair_sample_indices"]["logical_shape"] == "[P_batch]"
    assert fields["sample_pair_offsets"]["logical_shape"] == "[B+1]"
    assert fields["entry_validity"]["logical_shape"] == "[P_batch]"
    assert fields["sample_validity"]["logical_shape"] == "[B]"


def test_status_exact18_order_scope_and_closed_failure_reason(artifacts: dict[str, bytes]) -> None:
    rows = list(csv.DictReader(io.StringIO(artifacts[NAMES[3]].decode(), newline="")))
    assert [row["status"] for row in rows] == [row[0] for row in gate._STATUS_ROWS]
    assert rows[0]["scope"] == "entry|overall|joint" and rows[0]["is_success"] == "true"
    assert rows[1]["scope"] == "source_entry" and rows[1]["is_nonmember"] == "true" and rows[1]["overall_status_allowed"] == "false"
    assert rows[16]["scope"] == "joint" and rows[16]["is_hard_failure"] == "false"
    assert {row["status"] for row in rows if row["is_hard_failure"] == "true"} == set(gate._HARD_FAILURES)
    assert "maybe" not in artifacts[NAMES[3]].decode() and "probably" not in artifacts[NAMES[3]].decode()


def test_canonical_reference_vectors(decoded: dict[str, dict[str, object]]) -> None:
    reference = decoded[NAMES[4]]["canonical_exact11_batch_reference"]
    assert reference["batch_contract"]["batch_role_lengths"] == {"ligand": list(gate._LIGAND_RETAINED), "pocket": list(gate._POCKET_RETAINED)}
    assert reference["batch_contract"]["batch_role_offsets"] == {"ligand": [0, 13, 26, 39, 64, 92, 135, 177, 219, 262, 302, 323], "pocket": [0, 66, 170, 266, 474, 662, 940, 1207, 1464, 1713, 1974, 2202]}
    assert (reference["batch_contract"]["N_lig"], reference["batch_contract"]["N_pocket"], reference["batch_contract"]["joint_total"]) == (323, 2202, 2525)
    output = reference["output"]
    assert output["pair_values_parser_local_indices"] == [[p, l] for p, l in zip(gate._POCKET_LOCAL, gate._LIGAND_LOCAL)]
    assert output["pair_values_batch_indices"] == [[49, 3], [81, 16], [182, 29], [299, 42], [505, 91], [712, 113], [988, 151], [1260, 197], [1516, 240], [1766, 280], [2058, 307]]
    assert [row[0] for row in output["pair_values_joint_global_indices"]] == [372, 404, 505, 622, 828, 1035, 1311, 1583, 1839, 2089, 2381]
    assert [row[1] for row in output["pair_values_joint_global_indices"]] == [3, 16, 29, 42, 91, 113, 151, 197, 240, 280, 307]
    assert output["sample_pair_offsets"] == list(range(12))


def test_permutation_reference_cases_recompute(decoded: dict[str, dict[str, object]]) -> None:
    cases = decoded[NAMES[4]]["permutation_reference_cases"]
    assert [case["source_sample_indices"] for case in cases] == [list(reversed(range(11))), [10, 4, 0, 7, 2]]
    for case in cases:
        output = case["output"]
        assert output["remap_status"] == "REMAPPED_EXACT"
        assert case["batch_contract"]["batch_role_offsets"]["ligand"][-1] == case["batch_contract"]["N_lig"]
        assert case["batch_contract"]["batch_role_offsets"]["pocket"][-1] == case["batch_contract"]["N_pocket"]
        assert output["pair_sample_indices"] == list(range(len(case["source_sample_indices"])))
        assert output["sample_pair_offsets"] == list(range(len(case["source_sample_indices"]) + 1))


def test_subset_not_in_batch_no_placeholders(decoded: dict[str, dict[str, object]]) -> None:
    case = decoded[NAMES[4]]["subset_reference_cases"][0]
    output = case["output"]
    assert case["source_sample_indices"] == [10, 4, 0]
    assert len(output["pair_values_batch_indices"]) == 3
    assert output["sample_pair_offsets"] == [0, 1, 2, 3]
    assert sum(row["status"] == "NOT_IN_BATCH" for row in output["source_entry_outcomes"]) == 8
    assert all(row["status"] == "REMAPPED_EXACT" for row in output["source_entry_outcomes"] if row["source_entry_index"] in {0, 4, 10})


def test_no_joint_layout_is_segment_success(decoded: dict[str, dict[str, object]]) -> None:
    output = decoded[NAMES[4]]["no_joint_layout_reference_case"]["output"]
    assert output["remap_status"] == "REMAPPED_EXACT" and output["failure_reason"] == "NONE"
    assert output["pair_values_joint_global_indices"] is None
    assert output["provenance"]["joint_index_status"] == "JOINT_INDEX_SPACE_UNAVAILABLE"
    assert len(output["pair_values_batch_indices"]) == 11


def test_synthetic_future_p_gt_1_ragged(decoded: dict[str, dict[str, object]]) -> None:
    case = decoded[NAMES[4]]["synthetic_future_p_gt_1_reference_case"]
    output = case["output"]
    assert case["source_pair_counts_by_sample"] == [2, 0, 1]
    assert case["source_sample_offsets_int64"] == [0, 2, 2, 3]
    assert case["batch_source_sample_order"] == [2, 0, 1]
    assert output["sample_pair_offsets"] == [0, 1, 3, 3]
    assert output["pair_sample_indices"] == [0, 1, 1]
    assert output["pair_values_source_row_indices"] == [[0, 0], [1, 2], [3, 4]]
    assert output["pair_values_parser_local_indices"][0] == [0, 0]
    assert output["pair_values_batch_indices"][0] == [0, 0]


@pytest.mark.parametrize(
    ("field", "value", "delete"),
    [
        ("pdb_id", None, True),
        ("sample_index_row_id", "", False),
        ("ligand_comp_id", " L0 ", False),
        ("pdb_id", 7, False),
        ("pdb_id", None, False),
    ],
)
def test_batch_identity_unknown_has_reachable_failures(canonical_case: dict[str, object], canonical_authority: list[dict[str, object]], field: str, value: object, delete: bool) -> None:
    identity = canonical_case["batch_sample_order"][0]
    if delete:
        identity.pop(field)
    else:
        identity[field] = value
    output = gate._evaluate_reference_case(canonical_case, authoritative_tables=canonical_authority)
    assert output["remap_status"] == output["failure_reason"] == "BATCH_SAMPLE_IDENTITY_UNKNOWN"
    assert output["pair_values_batch_indices"] == []


def test_complete_non_source_zero_pair_sample_succeeds(canonical_case: dict[str, object], canonical_authority: list[dict[str, object]]) -> None:
    identity = {"sample_index_row_id": "NON_SOURCE_SAMPLE_000001", "sample_preparation_input_id": "NON_SOURCE_PREP_000001", "pdb_id": "9ZZZ", "ligand_comp_id": "ZZZ"}
    table = copy.deepcopy(canonical_authority[0])
    table["sample_identity"] = copy.deepcopy(identity)
    canonical_case["batch_sample_order"].append(identity)
    canonical_case["batch_sample_atom_identity_tables"].append(table)
    for role in ("pocket", "ligand"):
        length = table["roles"][role]["parser_output_atom_count"]
        canonical_case["batch_role_lengths"][role].append(length)
        canonical_case["batch_role_offsets"][role].append(canonical_case["batch_role_offsets"][role][-1] + length)
        canonical_case["batch_membership_masks"][role].extend([11] * length)
    output = gate._evaluate_reference_case(canonical_case, authoritative_tables=canonical_authority)
    assert output["remap_status"] == "REMAPPED_EXACT"
    assert output["sample_pair_offsets"][-2:] == [11, 11]
    assert len(output["sample_validity"]) == 12
    assert len(output["pair_values_batch_indices"]) == 11


@pytest.mark.parametrize(
    ("mutation", "status"),
    [
        (lambda role: (role.__setitem__("SHA256", "0" * 64), role.__setitem__("row_order_digest", "0" * 64)), "SOURCE_TABLE_IDENTITY_MISMATCH"),
        (lambda role: role.__setitem__("relative_path", "another/safe/nonempty/path.csv"), "SOURCE_TABLE_IDENTITY_MISMATCH"),
        (lambda role: role["selected_atom_identity"].__setitem__("atom_name", "DIFFERENT_NONEMPTY_NAME"), "SOURCE_ATOM_IDENTITY_MISMATCH"),
        (lambda role: role["selected_atom_identity"].pop("label_seq_id"), "SOURCE_ATOM_IDENTITY_MISMATCH"),
        (lambda role: role["selected_atom_identity"].__setitem__("label_seq_id", "DIFFERENT"), "SOURCE_ATOM_IDENTITY_MISMATCH"),
        (lambda role: role.__setitem__("selected_parser_local_index", role["selected_parser_local_index"] + 1), "SOURCE_TABLE_IDENTITY_MISMATCH"),
    ],
    ids=("self-consistent-wrong-sha", "path", "atom-name", "missing-label-seq", "changed-label-seq", "in-range-local"),
)
def test_authoritative_table_and_exact8_atom_comparison(canonical_case: dict[str, object], canonical_authority: list[dict[str, object]], mutation, status: str) -> None:
    role = canonical_case["batch_sample_atom_identity_tables"][0]["roles"]["pocket"]
    mutation(role)
    output = gate._evaluate_reference_case(canonical_case, authoritative_tables=canonical_authority)
    assert output["remap_status"] == output["failure_reason"] == status
    assert output["pair_values_source_row_indices"] == []


def test_valid_zero_indices_succeed_and_negative_fails() -> None:
    case = gate._synthetic_case()
    authority = gate._synthetic_authority()
    output = gate._evaluate_reference_case(case, authoritative_tables=authority)
    assert output["remap_status"] == "REMAPPED_EXACT"
    assert output["pair_values_source_row_indices"][0] == [0, 0]
    assert output["pair_values_parser_local_indices"][0] == [0, 0]
    assert output["pair_values_batch_indices"][0] == [0, 0]
    assert output["entry_validity"][0] is True
    case["source_pair_values_int64"][2][0] = -1
    failed = gate._evaluate_reference_case(case, authoritative_tables=authority)
    assert failed["remap_status"] == failed["failure_reason"] == "SOURCE_ROW_OUT_OF_RANGE"
    assert failed["pair_values_batch_indices"] == []


@pytest.mark.parametrize(
    ("mutation", "status"),
    [
        (lambda case: case.__setitem__("schema_version", "wrong"), "SCHEMA_VERSION_MISMATCH"),
        (lambda case: (case["source_sample_order"].append(copy.deepcopy(case["source_sample_order"][0])), case["source_sample_offsets_int64"].append(case["source_sample_offsets_int64"][-1]), case["source_sample_validity_bool"].append(True)), "SOURCE_SAMPLE_DUPLICATED"),
        (lambda case: case["batch_sample_order"].__setitem__(1, copy.deepcopy(case["batch_sample_order"][0])), "BATCH_SAMPLE_DUPLICATED"),
        (lambda case: case["batch_sample_atom_identity_tables"][0]["roles"]["pocket"].__setitem__("parser_output_atom_count", 65), "PARSER_COUNT_MISMATCH"),
        (lambda case: case["batch_role_offsets"]["ligand"].__setitem__(1, 12), "COLLATE_OFFSET_MISSING"),
        (lambda case: case["batch_membership_masks"]["pocket"].__setitem__(0, 9), "COLLATE_LENGTH_MISMATCH"),
        (lambda case: case["source_pair_values_int64"][0].__setitem__(0, 999), "SOURCE_ROW_OUT_OF_RANGE"),
        (lambda case: case["batch_sample_atom_identity_tables"][0]["roles"]["pocket"]["source_to_parser_local"].clear(), "PARSER_ATOM_NOT_FOUND"),
        (lambda case: case["batch_sample_atom_identity_tables"][0]["roles"]["pocket"]["source_to_parser_local"].__setitem__("88", [49, 50]), "PARSER_ATOM_NOT_UNIQUE"),
        (lambda case: case["batch_sample_atom_identity_tables"][0]["roles"].__setitem__("pocket", case["batch_sample_atom_identity_tables"][0]["roles"]["ligand"]), "ROLE_MISMATCH"),
        (lambda case: case["batch_sample_atom_identity_tables"][0]["roles"]["pocket"].__setitem__("SHA256", "0" * 64), "SOURCE_TABLE_IDENTITY_MISMATCH"),
        (lambda case: case["batch_sample_atom_identity_tables"][0]["roles"]["pocket"]["selected_atom_identity"].__setitem__("atom_name", ""), "SOURCE_ATOM_IDENTITY_MISMATCH"),
        (lambda case: case["source_entry_validity_bool"].__setitem__(0, False), "ENTRY_INVALID"),
        (lambda case: case.__setitem__("joint_layout_descriptor", "unknown_layout"), "SCHEMA_VERSION_MISMATCH"),
    ],
    ids=("schema", "source-duplicate", "batch-duplicate", "count", "offset", "membership", "range", "not-found", "not-unique", "role-swap", "table-identity", "atom-identity", "invalid-entry", "unknown-joint"),
)
def test_reference_evaluator_fail_closed(canonical_case: dict[str, object], canonical_authority: list[dict[str, object]], mutation, status: str) -> None:
    mutation(canonical_case)
    output = gate._evaluate_reference_case(canonical_case, authoritative_tables=canonical_authority)
    assert output["remap_status"] == status
    assert output["failure_reason"] == status
    assert output["pair_values_source_row_indices"] == []
    assert output["pair_values_parser_local_indices"] == []
    assert output["pair_values_batch_indices"] == []


def test_unknown_failure_status_is_rejected() -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        gate._reference_fail("maybe")


def test_stable_digest_manual_parity_and_report_excluded(artifacts: dict[str, bytes], decoded: dict[str, dict[str, object]]) -> None:
    expected = decoded[NAMES[5]]["contract_digest"]
    assert _manual_digest(artifacts) == expected
    changed = dict(artifacts)
    changed[NAMES[5]] = b"changed\n"
    assert _manual_digest(changed) == expected


def test_digest_framing_known_vector() -> None:
    tag = b"known\0"
    framed = hashlib.sha256()
    framed.update(tag)
    for name, payload in (("a", b"x"), ("bc", b"yz")):
        encoded = name.encode()
        framed.update(len(encoded).to_bytes(8, "big"))
        framed.update(encoded)
        framed.update(len(payload).to_bytes(8, "big"))
        framed.update(payload)
    manual = tag + (1).to_bytes(8, "big") + b"a" + (1).to_bytes(8, "big") + b"x" + (2).to_bytes(8, "big") + b"bc" + (2).to_bytes(8, "big") + b"yz"
    assert framed.hexdigest() == hashlib.sha256(manual).hexdigest() == "59202b778cde7c577ac91214f520b0fd3fa688f9094c545caa6d5418d72a38c7"


def test_report_counts_status_and_readiness(decoded: dict[str, dict[str, object]]) -> None:
    report = decoded[NAMES[5]]
    assert report["gate_status"] == "PASS_CONTRACT_ONLY"
    assert (report["artifact_file_count"], report["runtime_source_identity_count"], report["source_atom_table_count"], report["source_pair_count"], report["source_to_parser_local_valid_count"], report["status_vocabulary_count"]) == (6, 5, 22, 11, 22, 18)
    assert report["canonical_reference_case_passed"] and report["no_joint_reference_case_passed"] and report["synthetic_p_gt_1_reference_case_passed"]
    readiness = report["readiness"]
    assert readiness["task2_batch_index_remap_contract_gate_implemented"] is True
    assert readiness["task2_batch_index_remap_contract_gate_passed"] is True
    assert readiness["public_batch_index_remap_adapter_implemented"] is False
    assert readiness["torch_tensor_materialized"] is False and readiness["numpy_artifact_materialized"] is False
    assert readiness["feature_semantics_reaudit_required_before_training"] is True and readiness["ready_for_training"] is False


def test_checkpoint_and_auxiliary_boundaries(decoded: dict[str, dict[str, object]]) -> None:
    manifest = decoded[NAMES[0]]
    assert manifest["checkpoint_compatibility"] == {"checkpoint_state_dict_change_required": False, "base_model_parameter_shape_change_required": False, "base_atom_feature_width_change_required": False, "egnn_or_se3_backbone_change_required": False}
    scope = manifest["auxiliary_module_scope"]
    assert scope["directly_advanced"] == ["target_residue_atom_condition_adapter", "covalent_pair_prediction_head"]
    assert set(scope["not_ready"]) == {"role_mask_anchor_encoding", "pre_post_geometry_prediction_head", "covalent_pair_contrastive_loss"}


def test_fail_closed_invariants_cover_extended_cases(decoded: dict[str, dict[str, object]]) -> None:
    invariants = decoded[NAMES[0]]["fail_closed_invariants"]
    assert len(invariants) == 30
    combined = " ".join(invariants)
    for phrase in ("distributed sampler", "padding", "empty valid-pair", "ragged P greater than one", "zero pairs", "NOT_IN_BATCH"):
        assert phrase in combined


def test_deterministic_independent_double_build(artifacts: dict[str, bytes]) -> None:
    second = gate.build_covapie_current11_task2_batch_index_remap_contract_gate_v1(repo_root=REPO, state_root=STATE)
    assert second == artifacts


def test_cli_success_is_one_compact_report_line(artifacts: dict[str, bytes]) -> None:
    script = REPO / "scripts/check_covapie_current11_task2_batch_index_remap_contract_gate_v1.py"
    run = subprocess.run([sys.executable, str(script), "--repo-root", str(REPO), "--state-root", str(STATE)], cwd=REPO, env={**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONDONTWRITEBYTECODE": "1"}, text=True, capture_output=True, check=False)
    assert run.returncode == 0 and run.stderr == "" and run.stdout.count("\n") == 1
    assert json.loads(run.stdout) == json.loads(artifacts[NAMES[5]])
    assert run.stdout == json.dumps(json.loads(run.stdout), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n"


@pytest.mark.parametrize(
    "arguments",
    [
        [], ["-h"], ["--help"], ["--repo-root", str(REPO)], ["--state-root", str(STATE)],
        ["--repo-root", str(REPO), "--state-root", str(STATE), "extra"],
        *[["--repo-root", str(REPO), "--state-root", str(STATE), flag] for flag in ("--write", "--materialize", "--remap", "--adapter", "--tensorize", "--torch", "--numpy", "--batch", "--sample-order", "--joint-layout", "--source", "--loss", "--train")],
        *[["--repo-root", str(REPO), "--state-root", str(STATE), flag, "x"] for flag in ("--output", "--output-dir", "--schema-override", "--status-override")],
    ],
)
def test_cli_rejects_invalid_arguments(arguments: list[str]) -> None:
    script = REPO / "scripts/check_covapie_current11_task2_batch_index_remap_contract_gate_v1.py"
    run = subprocess.run([sys.executable, str(script), *arguments], cwd=REPO, env={**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONDONTWRITEBYTECODE": "1"}, text=True, capture_output=True, check=False)
    assert run.returncode == 1 and run.stdout == "" and run.stderr == ERROR + "\n"


def test_formal_sidecar_identity_is_frozen(decoded: dict[str, dict[str, object]]) -> None:
    formal = decoded[NAMES[0]]["source_lineage"]["formal_routing_sidecar"]
    canonical = STATE / formal["canonical_relative_path"]
    assert canonical.is_symlink() and os.readlink(canonical) == formal["readlink"] == gate._FORMAL_READLINK
    assert formal["aggregate"] == gate._FORMAL_AGGREGATE and formal["snapshot_SHA256"] == gate._FORMAL_SNAPSHOT
    for name, digest in formal["Exact4_SHA256"].items():
        assert hashlib.sha256((canonical.parent / os.readlink(canonical) / name).read_bytes()).hexdigest() == digest


def test_no_repository_or_state_writes_from_api(artifacts: dict[str, bytes]) -> None:
    command = ("git", "status", "--short")
    before_status = subprocess.run(command, cwd=REPO, text=True, capture_output=True, check=True).stdout
    formal_path = STATE / gate._FORMAL_RELATIVE
    before_formal = gate._formal_snapshot(formal_path)
    second = gate.build_covapie_current11_task2_batch_index_remap_contract_gate_v1(repo_root=REPO, state_root=STATE)
    after_status = subprocess.run(command, cwd=REPO, text=True, capture_output=True, check=True).stdout
    after_formal = gate._formal_snapshot(formal_path)
    assert second == artifacts
    assert after_status == before_status
    assert after_formal == before_formal
    status_lines = before_status.splitlines()
    expected_precommit = {f"?? {path}" for path in gate._REPOSITORY_EXACT4 if (REPO / path).exists()}
    assert status_lines == [] or (len(status_lines) == len(expected_precommit) == 4 and set(status_lines) == expected_precommit)
    assert not any(path.suffix in {".pt", ".pth", ".npz", ".pkl", ".lmdb"} for path in REPO.rglob("*") if path.is_file() and path.stat().st_mtime_ns > Path(gate.__file__).stat().st_mtime_ns)
