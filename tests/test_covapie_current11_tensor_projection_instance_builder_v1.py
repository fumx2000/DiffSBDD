from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import io
import json
import os
import struct
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from covalent_ext import covapie_current11_tensor_projection_instance_builder_v1 as builder


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/covapie-state"
)
SCRIPT = REPO_ROOT / "scripts/check_covapie_current11_tensor_projection_instance_builder_v1.py"
INSTANCE_NAME = "current11_tensor_projection_instance.json"
REPORT_NAME = "current11_tensor_projection_instance_builder_report.json"
ERROR = "COVAPIE_CURRENT11_TENSOR_PROJECTION_INSTANCE_BUILDER_V1_ERROR"
EXPECTED_DIGEST = "b8e8078700bd019d4a11a00c17dc84fa05e406bbf61b51bf3e887988f3b89255"
EXPECTED_PAIR_VALUES = [
    [88, 3], [25, 3], [19, 3], [39, 3], [37, 27], [50, 21],
    [48, 16], [53, 20], [52, 21], [53, 18], [84, 5],
]


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return builder.build_covapie_current11_tensor_projection_instance_v1(
        repo_root=REPO_ROOT, state_root=STATE_ROOT
    )


@pytest.fixture(scope="module")
def instance(artifacts: dict[str, bytes]) -> dict[str, object]:
    return json.loads(artifacts[INSTANCE_NAME])


@pytest.fixture(scope="module")
def report(artifacts: dict[str, bytes]) -> dict[str, object]:
    return json.loads(artifacts[REPORT_NAME])


def _formal() -> dict[str, bytes]:
    canonical = STATE_ROOT / builder._FORMAL_RELATIVE
    return builder._read_formal(canonical)


def _flatten(matrix: object) -> list[object]:
    assert type(matrix) is list and len(matrix) == 11
    assert all(type(row) is list and len(row) == 25 for row in matrix)
    return [value for row in matrix for value in row]


def _decode_utf8(buffer: dict[str, object]) -> list[str]:
    raw = bytes(buffer["bytes_uint8"])
    offsets = buffer["offsets_int64"]
    return [raw[offsets[index] : offsets[index + 1]].decode() for index in range(11)]


def _run_checker(*arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def test_unique_keyword_only_api_and_exact_builtin_dict(artifacts: dict[str, bytes]) -> None:
    assert builder.__all__ == ("build_covapie_current11_tensor_projection_instance_v1",)
    signature = inspect.signature(builder.build_covapie_current11_tensor_projection_instance_v1)
    assert tuple(signature.parameters) == ("repo_root", "state_root")
    assert all(
        value.kind is inspect.Parameter.KEYWORD_ONLY
        for value in signature.parameters.values()
    )
    assert type(artifacts) is dict
    assert tuple(artifacts) == (INSTANCE_NAME, REPORT_NAME)
    assert len(artifacts) == 2
    assert all(type(value) is bytes for value in artifacts.values())


def test_silent_import() -> None:
    process = subprocess.run(
        [sys.executable, "-c", "import covalent_ext.covapie_current11_tensor_projection_instance_builder_v1"],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0
    assert process.stdout == process.stderr == ""


def test_import_boundary_and_no_git_subprocess() -> None:
    source = Path(builder.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert all(name.split(".")[0] not in {"torch", "numpy", "rdkit", "openbabel"} for name in imports)
    assert "subprocess" not in {name.split(".")[0] for name in imports}
    assert all(name.split(".")[0] in sys.stdlib_module_names or name.startswith("covalent_ext") for name in imports if name != "__future__")


def test_build_is_read_only_and_does_not_read_audit_markdown(monkeypatch: pytest.MonkeyPatch) -> None:
    original_read = Path.read_bytes
    original_payload_api = builder._payload_builder.build_covapie_current11_tensor_projection_payload_bundle_v1
    calls = 0

    def guarded_read(path: Path) -> bytes:
        assert not str(path).endswith("payload_extraction_preconditions_report.md")
        return original_read(path)

    def counted(**kwargs: object) -> dict[str, bytes]:
        nonlocal calls
        calls += 1
        return original_payload_api(**kwargs)

    monkeypatch.setattr(Path, "read_bytes", guarded_read)
    monkeypatch.setattr(Path, "write_bytes", lambda *args, **kwargs: pytest.fail("write attempted"))
    monkeypatch.setattr(builder._payload_builder, "build_covapie_current11_tensor_projection_payload_bundle_v1", counted)
    before = builder._formal_snapshot(STATE_ROOT / builder._FORMAL_RELATIVE)
    result = builder.build_covapie_current11_tensor_projection_instance_v1(repo_root=REPO_ROOT, state_root=STATE_ROOT)
    assert tuple(result) == (INSTANCE_NAME, REPORT_NAME)
    assert calls == 2
    assert builder._formal_snapshot(STATE_ROOT / builder._FORMAL_RELATIVE) == before


def test_compatibility_filter_exact4_and_fifth_path(monkeypatch: pytest.MonkeyPatch) -> None:
    gate = builder._payload_builder._contract_gate
    exact = "\n".join(f"?? {path}" for path in builder._REPOSITORY_EXACT4)
    monkeypatch.setattr(gate, "_run_git", lambda root, arguments: exact + "\n?? fifth.txt\n")
    original = gate._run_git
    with builder._successor_status_compatibility():
        output = gate._run_git(REPO_ROOT, ("status", "--porcelain=v1", "--untracked-files=all"))
        assert output == "?? fifth.txt"
    assert gate._run_git is original


def test_fifth_untracked_path_makes_predecessor_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    gate = builder._payload_builder._contract_gate
    original = gate._run_git
    original_gate_api = gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1

    def inject_fifth(root: Path, arguments: object) -> str:
        output = original(root, arguments)
        if tuple(arguments) == ("status", "--porcelain=v1", "--untracked-files=all"):
            return output + ("" if output.endswith("\n") or not output else "\n") + "?? fifth.txt\n"
        return output

    monkeypatch.setattr(gate, "_run_git", inject_fifth)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        builder.build_covapie_current11_tensor_projection_instance_v1(
            repo_root=REPO_ROOT, state_root=STATE_ROOT
        )
    assert gate._run_git is inject_fifth
    assert gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1 is original_gate_api


@pytest.mark.parametrize("status", ["A  ", " M ", "R  ", "D  ", "T  ", "UU "])
def test_compatibility_filter_rejects_non_untracked_successor_shape(
    monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    gate = builder._payload_builder._contract_gate
    line = status + builder._REPOSITORY_EXACT4[0]
    monkeypatch.setattr(gate, "_run_git", lambda root, arguments: line)
    original = gate._run_git
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        with builder._successor_status_compatibility():
            gate._run_git(REPO_ROOT, ("status", "--porcelain=v1", "--untracked-files=all"))
    assert gate._run_git is original


def test_compatibility_filter_finally_restores(monkeypatch: pytest.MonkeyPatch) -> None:
    gate = builder._payload_builder._contract_gate
    monkeypatch.setattr(gate, "_run_git", lambda root, arguments: "")
    original = gate._run_git
    with pytest.raises(RuntimeError, match="sentinel"):
        with builder._successor_status_compatibility():
            raise RuntimeError("sentinel")
    assert gate._run_git is original


def test_canonical_json_exact2(artifacts: dict[str, bytes]) -> None:
    for payload in artifacts.values():
        assert payload == (json.dumps(json.loads(payload), sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode()
        assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
        assert b"\r" not in payload and b"\0" not in payload and not payload.startswith(b"\xef\xbb\xbf")
        assert len(payload) < 1024 * 1024


def test_exact24_and_no_lifecycle_or_absolute_path(instance: dict[str, object]) -> None:
    assert set(instance) == set(builder._INSTANCE_FIELDS)
    assert len(instance) == 24
    encoded = json.dumps(instance)
    keys: set[str] = set()

    def collect(value: object) -> None:
        if type(value) is dict:
            keys.update(value)
            for item in value.values():
                collect(item)
        elif type(value) is list:
            for item in value:
                collect(item)

    collect(instance)
    assert keys.isdisjoint({"head", "origin_main", "ahead", "behind", "lifecycle_profile", "st_dev", "st_ino", "mtime_ns"})
    assert str(REPO_ROOT) not in encoded and str(STATE_ROOT) not in encoded


def test_exact11_exact25_and_exact5_b3(instance: dict[str, object]) -> None:
    assert instance["sample_order"] == [
        {"sample_index": i, "sample_index_row_id": row, "pdb_id": pdb, "ligand_comp_id": ligand}
        for i, (row, pdb, ligand) in enumerate(builder._SAMPLES)
    ]
    assert instance["task_order"] == [
        {"task_index": i, "semantic_task_name": name}
        for i, name in enumerate(builder._TASKS)
    ]
    masks = instance["canonical_mask_semantics"]
    assert len(masks) == 5
    assert [(item["semantic_name"], item["display_alias"]) for item in masks] == [
        ("warhead_only", "A"),
        ("linker_plus_warhead", "B"),
        ("scaffold_plus_warhead", "B2"),
        ("scaffold_only", "B3"),
        ("scaffold_plus_linker_plus_warhead", "C"),
    ]


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("direct_authority_mask", None),
        ("data_availability_mask", 55),
        ("applicability_mask", 275),
        ("candidate_only_mask", 55),
        ("observed_geometry_only_mask", 11),
        ("state_ambiguity_mask", 7),
        ("human_approval_missing_mask", 55),
        ("loss_authorization_mask", 0),
        ("runtime_consumer_available_mask", 0),
        ("task_payload_validity", 55),
        ("candidate_payload_validity", 0),
    ],
)
def test_bool_matrix_shapes_and_counts(instance: dict[str, object], field: str, expected: int | None) -> None:
    flat = _flatten(instance[field])
    assert all(type(value) is bool for value in flat)
    if expected is not None:
        assert sum(flat) == expected


def test_eligibility_counts_and_derived_masks(instance: dict[str, object]) -> None:
    eligibility = instance["eligibility_state_code"]
    flat = _flatten(eligibility)
    assert all(type(value) is int and 0 <= value <= 6 for value in flat)
    counts = Counter(flat)
    assert {code: counts[code] for code in range(7)} == builder._ELIGIBILITY_COUNTS
    assert instance["applicability_mask"] == [[value != 6 for value in row] for row in eligibility]
    assert instance["candidate_only_mask"] == [[value == 2 for value in row] for row in eligibility]
    assert instance["observed_geometry_only_mask"] == [[value == 1 for value in row] for row in eligibility]
    assert instance["state_ambiguity_mask"] == [[value == 4 for value in row] for row in eligibility]
    assert instance["human_approval_missing_mask"] == [[value == 5 for value in row] for row in eligibility]


def test_routing_decode_and_direct_authority_parity(instance: dict[str, object]) -> None:
    formal = _formal()
    rows = list(csv.DictReader(io.StringIO(formal["current11_dataset_partial_supervision_routing_records.csv"].decode())))
    for cell, row in enumerate(rows):
        sample, task = divmod(cell, 25)
        assert builder._ELIGIBILITY[instance["eligibility_state_code"][sample][task]] == row["eligibility_state"]
        assert builder._EVIDENCE[instance["evidence_scope_code"][sample][task]] == row["evidence_scope"]
        assert builder._BLOCKING[instance["blocking_reason_code"][sample][task]] == row["blocking_reason_code"]
        assert instance["direct_authority_mask"][sample][task] is (row["direct_authority_found"] == "true")


def test_routing_reorder_and_unknown_code_fail_closed() -> None:
    formal = _formal()
    name = "current11_dataset_partial_supervision_routing_records.csv"
    lines = formal[name].splitlines(keepends=True)
    reordered = dict(formal)
    reordered[name] = b"".join([lines[0], lines[2], lines[1], *lines[3:]])
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        builder._routing(reordered)
    unknown = dict(formal)
    unknown[name] = formal[name].replace(b",admissible_now,", b",UNKNOWN,", 1)
    with pytest.raises((ValueError, IndexError), match=f"^{ERROR}$"):
        builder._routing(unknown)


def test_payload_slots_exact25(instance: dict[str, object]) -> None:
    slots = instance["task_payloads"]
    assert len(slots) == 25
    materialized = [item["task_index"] for item in slots if item["payload_materialized_in_memory"]]
    assert materialized == [0, 1, 2, 6, 12]
    for item in slots:
        if item["task_index"] in materialized:
            assert isinstance(item["payload_schema_version"], str)
            assert isinstance(item["source_payload_artifact_name"], str)
            assert type(item["payload"]) is dict
        else:
            assert item["payload_schema_version"] is None
            assert item["source_payload_artifact_name"] is None
            assert item["payload"] is None
    assert all("generation_mask" not in (item["source_payload_artifact_name"] or "") for item in slots)


def test_task0_and_task1_payloads(instance: dict[str, object]) -> None:
    task0 = instance["task_payloads"][0]["payload"]
    assert _decode_utf8(task0["sample_index_row_id"]) == [item[0] for item in builder._SAMPLES]
    assert _decode_utf8(task0["pdb_id"]) == [item[1] for item in builder._SAMPLES]
    assert _decode_utf8(task0["ligand_comp_id"]) == [item[2] for item in builder._SAMPLES]
    assert task0["sample_validity_bool"] == [True] * 11
    task1 = instance["task_payloads"][1]["payload"]
    assert task1["values_bool"] == task1["sample_validity_bool"] == [True] * 11
    assert task1["candidate_event"] is False and task1["bond_order_encoded"] is False


def test_task2_values_offsets_and_remap_boundary(instance: dict[str, object]) -> None:
    payload = instance["task_payloads"][2]["payload"]
    assert payload["values_int64"] == EXPECTED_PAIR_VALUES
    assert payload["values_logical_shape"] == [11, 2]
    assert payload["sample_offsets_int64"] == list(range(12))
    assert payload["entry_validity_bool"] == [True] * 11
    assert payload["batch_index_remap_required"] is True
    assert payload["permanent_chemical_identifier"] is False
    assert payload["model_input_allowed_now"] is False


def test_task6_counts_f1_and_semantic_boundary(instance: dict[str, object]) -> None:
    payload = instance["task_payloads"][6]["payload"]
    assert payload["global_local_token_count"] == 118
    assert payload["reviewed_warhead_atom_entry_count"] == 102
    assert payload["boundary_pair_count"] == 16
    raw = bytes(payload["token_bytes_uint8"])
    offsets = payload["token_offsets_int64"]
    tokens = [raw[offsets[i] : offsets[i + 1]].decode() for i in range(118)]
    assert "F1" in tokens
    assert payload["F1_numeric_ligand_atom_mapping_available"] is False
    assert payload["F1_raw_token_payload_valid"] is True
    assert payload["generation_mask_sample_labels_materialized"] is False


def test_task12_decimal_hex_and_observed_only_boundary(instance: dict[str, object]) -> None:
    payload = instance["task_payloads"][12]["payload"]
    expected = ["1.670", "1.800", "1.718", "1.802", "1.809", "1.762", "1.807", "1.799", "1.806", "1.794", "1.717"]
    assert payload["source_decimal_strings"] == expected
    packed = bytes.fromhex(payload["values_float32_le_hex"])
    assert len(packed) == 44
    assert [value[0] for value in struct.iter_unpack("<f", packed)] == pytest.approx([float(value) for value in expected])
    assert payload["logical_shape"] == [11, 1]
    assert payload["observed_complex_only"] is True
    assert payload["pre_covalent_geometry"] is False
    assert payload["post_covalent_geometry"] is False
    assert payload["post_state_inferred"] is False


def test_validity_availability_requires_payload_and_eligibility(instance: dict[str, object]) -> None:
    validity = instance["task_payload_validity"]
    eligibility = instance["eligibility_state_code"]
    expected = [[validity[s][t] and eligibility[s][t] in (0, 1) for t in range(25)] for s in range(11)]
    assert instance["data_availability_mask"] == expected == validity
    assert all(not validity[s][t] for s in range(11) for t in range(25) if eligibility[s][t] == 2)


def test_task_entry_validity_exact25_and_offsets(instance: dict[str, object]) -> None:
    entries = instance["task_payload_entry_validity"]
    assert len(entries) == 25
    assert [item["task_index"] for item in entries if item["entry_validity_materialized_in_memory"]] == [0, 1, 2, 6, 12]
    assert entries[0]["entry_validity"]["sample_validity_bool"] == [True] * 11
    assert all(values == [True] * 12 for values in entries[0]["entry_validity"]["utf8_offsets_validity_bool"].values())
    assert entries[2]["entry_validity"]["sample_offsets_int64"] == list(range(12))
    assert len(entries[6]["entry_validity"]["token_validity_bool"]) == 118
    assert len(entries[6]["entry_validity"]["warhead_entry_validity_bool"]) == 102
    assert len(entries[6]["entry_validity"]["boundary_entry_validity_bool"]) == 16
    assert len(entries[12]["entry_validity"]["float32_byte_validity_bool"]) == 44
    assert all(item["entry_validity"] is None for item in entries if item["task_index"] not in {0, 1, 2, 6, 12})


def test_candidate_slots_empty_but_candidate_eligibility_preserved(instance: dict[str, object]) -> None:
    slots = instance["candidate_payloads"]
    assert len(slots) == 25
    assert all(item["candidate_payload_materialized_in_memory"] is False and item["candidate_payload"] is None for item in slots)
    assert sum(_flatten(instance["candidate_only_mask"])) == 55
    assert sum(_flatten(instance["candidate_payload_validity"])) == 0


def test_provenance_exact55_order_content_and_relative_paths(instance: dict[str, object]) -> None:
    records = instance["task_payload_provenance"]
    assert len(records) == 55
    secondary = 0
    for cell, record in enumerate(records):
        sample, minor = divmod(cell, 5)
        task = [0, 1, 2, 6, 12][minor]
        assert record["cell_index"] == cell
        assert record["sample_index"] == sample
        assert record["semantic_task_name"] == builder._TASKS[task]
        assert record["payload_entry_locator"] == {"sample_index": sample, "task_index": task}
        assert record["payload_artifact_name"] == instance["task_payloads"][task]["source_payload_artifact_name"]
        assert record["payload_valid"] is record["provenance_complete"] is True
        assert record["candidate_promotion_used"] is record["inference_used"] is record["semantic_promotion_used"] is False
        secondary += len(record["secondary_source_bindings"])
        for binding in record["source_bindings"] + record["secondary_source_bindings"]:
            for key, value in binding.items():
                if "path" in key:
                    assert not Path(value).is_absolute()
    assert secondary == 22


def test_source_lineage_frozen_and_non_runtime(instance: dict[str, object]) -> None:
    lineage = instance["source_lineage"]
    assert lineage["projection_contract_gate"]["contract_digest"] == builder._CONTRACT_DIGEST
    assert lineage["payload_builder"]["payload_bundle_digest"] == builder._PAYLOAD_BUNDLE_DIGEST
    assert lineage["formal_routing_sidecar"]["formal_snapshot_sha256"] == builder._FORMAL_SNAPSHOT_SHA256
    assert lineage["non_runtime_lineage"]["runtime_dependency"] is False
    assert lineage["non_runtime_lineage"]["payload_authority"] is False


def test_manual_digest_and_known_vector(artifacts: dict[str, bytes], report: dict[str, object]) -> None:
    payload = artifacts[INSTANCE_NAME]
    name = INSTANCE_NAME.encode()
    digest = hashlib.sha256()
    digest.update(b"COVAPIE_CURRENT11_TENSOR_PROJECTION_INSTANCE_V1\0")
    digest.update(len(name).to_bytes(8, "big"))
    digest.update(name)
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    assert digest.hexdigest() == report["projection_instance_digest"] == EXPECTED_DIGEST
    assert builder._stable_digest(b"{}\n") == "2086155e10e3845716ec31e51bbb81a12c6432fd8b8094d1538ab4d3d665e1db"


def test_report_excluded_status_counts_and_readiness(report: dict[str, object]) -> None:
    assert report["builder_status"] == "PASS_IN_MEMORY_FULL_EXACT25_PROJECTION_INSTANCE_ONLY"
    expected = {
        "artifact_file_count": 2,
        "sample_count": 11,
        "task_count": 25,
        "routing_cell_count": 275,
        "payload_slot_count": 25,
        "eligibility_permitted_count": 55,
        "validated_payload_cell_count": 55,
        "task_payload_validity_true_count": 55,
        "data_availability_true_count": 55,
        "candidate_eligible_count": 55,
        "candidate_payload_materialized_count": 0,
        "candidate_payload_validity_true_count": 0,
        "applicability_true_count": 275,
        "observed_geometry_only_true_count": 11,
        "state_ambiguity_true_count": 7,
        "human_approval_missing_true_count": 55,
        "loss_authorization_true_count": 0,
        "runtime_consumer_available_true_count": 0,
        "provenance_record_count": 55,
    }
    assert all(report[key] == value for key, value in expected.items())
    assert report["artifact_identities"][1]["stable_digest_participation"] is False
    readiness = report["readiness"]
    assert readiness["projection_instance_builder_implemented"] is True
    assert readiness["projection_instance_builder_passed"] is True
    assert readiness["full_exact25_projection_schema_instantiated_in_memory"] is True
    assert readiness["routing_matrices_built_in_memory"] is True
    assert readiness["data_availability_matrix_built_in_memory"] is True
    assert readiness["ready_for_batch_index_remap_adapter_design"] is True
    assert readiness["formal_projection_instance_materialized"] is False
    assert readiness["torch_tensor_materialized"] is False
    assert readiness["numpy_artifact_materialized"] is False
    assert readiness["ready_for_dataloader_integration"] is False
    assert readiness["ready_for_model_integration"] is False
    assert readiness["feature_semantics_reaudit_required_before_training"] is True
    assert readiness["ready_for_training"] is False


def test_independent_double_build(artifacts: dict[str, bytes]) -> None:
    second = builder.build_covapie_current11_tensor_projection_instance_v1(repo_root=REPO_ROOT, state_root=STATE_ROOT)
    assert second == artifacts


def test_valid_cli_prints_only_compact_report(report: dict[str, object]) -> None:
    process = _run_checker("--repo-root", str(REPO_ROOT), "--state-root", str(STATE_ROOT))
    assert process.returncode == 0
    assert process.stderr == ""
    assert process.stdout == json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n"
    assert '"eligibility_state_code"' not in process.stdout
    assert '"task_payloads"' not in process.stdout


@pytest.mark.parametrize(
    "arguments",
    [
        ("-h",), ("--help",), ("--output", "x"), ("--output-dir", "x"),
        ("--write",), ("--materialize",), ("--tensorize",), ("--numpy",),
        ("--torch",), ("--task", "0"), ("--source", "x"),
        ("--payload-override", "x"), ("--matrix-override", "x"),
        ("--availability",), ("--candidate",), ("--loss",), ("--train",),
        ("--schema-override", "x"), ("extra",), (),
        ("--repo-root", str(REPO_ROOT)), ("--state-root", str(STATE_ROOT)),
    ],
)
def test_invalid_cli_is_uniform(arguments: tuple[str, ...]) -> None:
    process = _run_checker(*arguments)
    assert process.returncode == 1
    assert process.stdout == ""
    assert process.stderr == ERROR + "\n"
