from __future__ import annotations

import ast
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
import tempfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1
    as gate,
)


STATE_ROOT = (ROOT.parent / "covapie-state").resolve(strict=True)
SCRIPT = ROOT / gate.SCRIPT_PATH
EXPECTED_CONTRACT_DIGEST = (
    "d0a428c19fe3c4aefc575065e7dcc7a7cfaf8593526d025d467cf6568b49c21d"
)
IGNORED_RAW_FIXTURE_OVERLAY = (
    "data/raw/covalent_sources/covpdb/independent_group_expansion_batch_000001/1ayu.cif",
    "data/raw/covalent_sources/covpdb/independent_group_expansion_batch_000001/1ayw.cif",
)


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1(
        repo_root=ROOT,
        state_root=STATE_ROOT,
    )


@pytest.fixture(scope="module")
def parsed(artifacts: dict[str, bytes]) -> dict[str, object]:
    return {
        "manifest": json.loads(artifacts[gate.ARTIFACT_NAMES[0]]),
        "tasks": _csv(artifacts[gate.ARTIFACT_NAMES[1]]),
        "states": _csv(artifacts[gate.ARTIFACT_NAMES[2]]),
        "report": json.loads(artifacts[gate.ARTIFACT_NAMES[3]]),
    }


@pytest.fixture()
def formal_payloads() -> dict[str, bytes]:
    canonical = STATE_ROOT / gate.CANONICAL_RELATIVE
    return {
        name: (canonical / name).read_bytes() for name in gate.FORMAL_ARTIFACTS
    }


def _csv(payload: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    return tuple(reader.fieldnames or ()), list(reader)


def _mutate_csv(payload: bytes, row: int, field: str, value: str) -> bytes:
    columns, rows = _csv(payload)
    rows[row][field] = value
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _mutate_manifest(payloads: dict[str, bytes], mutate: object) -> dict[str, bytes]:
    copied = dict(payloads)
    name = "current11_dataset_partial_supervision_routing_manifest.json"
    value = json.loads(copied[name])
    assert callable(mutate)
    mutate(value)
    copied[name] = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    return copied


def _report(artifacts: dict[str, bytes]) -> dict[str, object]:
    value = json.loads(artifacts[gate.ARTIFACT_NAMES[3]])
    assert isinstance(value, dict)
    return value


def _run_checker(*arguments: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        (sys.executable, "-B", os.fspath(SCRIPT), *arguments),
        cwd=cwd,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        check=False,
    )


def _copy_exact4(destination: Path) -> None:
    for relative in gate.CANDIDATE_PATHS:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
        target.chmod(0o644)


def _overlay_required_ignored_raw_fixtures(destination: Path) -> None:
    for relative in IGNORED_RAW_FIXTURE_OVERLAY:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
        target.chmod(0o644)


def _git(directory: Path, *arguments: str) -> str:
    return subprocess.check_output(("git", *arguments), cwd=directory).decode().strip()


def _normalize_clone_modes(repository: Path) -> None:
    output = subprocess.check_output(
        ("git", "ls-files", "--stage", "-z"), cwd=repository
    ).decode("utf-8")
    for entry in filter(None, output.split("\0")):
        metadata, relative = entry.split("\t", 1)
        mode = metadata.split(" ", 1)[0]
        path = repository / relative
        if mode == "100644":
            path.chmod(0o644)
        elif mode == "100755":
            path.chmod(0o755)


def _lifecycle_clone(profile: str) -> tuple[dict[str, bytes], dict[str, object]]:
    temporary = Path(tempfile.mkdtemp(prefix="covapie-contract-lifecycle-"))
    clone = temporary / "repo"
    try:
        subprocess.run(("git", "clone", "--quiet", "--no-hardlinks", os.fspath(ROOT), os.fspath(clone)), check=True)
        _git(clone, "reset", "--hard", gate.BASE_COMMIT)
        _git(clone, "update-ref", "refs/remotes/origin/main", gate.BASE_COMMIT)
        assert _git(clone, "branch", "--show-current") == gate.BRANCH
        assert _git(clone, "rev-parse", "HEAD") == gate.BASE_COMMIT
        assert (
            _git(clone, "rev-parse", "refs/remotes/origin/main")
            == gate.BASE_COMMIT
        )
        assert (
            _git(
                clone,
                "log",
                "--format=%H",
                "--all",
                "--",
                *gate.CANDIDATE_PATHS,
            )
            == ""
        )
        _normalize_clone_modes(clone)
        _copy_exact4(clone)
        _overlay_required_ignored_raw_fixtures(clone)
        if profile != "precommit":
            _git(clone, "add", *gate.CANDIDATE_PATHS)
            subprocess.run(
                ("git", "-c", "user.name=CovaPIE Test", "-c", "user.email=covapie@example.invalid", "commit", "--quiet", "-m", gate.FORMAL_COMMIT_SUBJECT),
                cwd=clone,
                check=True,
            )
            if profile == "published":
                _git(clone, "update-ref", "refs/remotes/origin/main", "HEAD")
        built = gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1(
            repo_root=clone.resolve(strict=True), state_root=STATE_ROOT
        )
        lifecycle = _report(built)["repository_lifecycle"]
        assert isinstance(lifecycle, dict)
        return built, lifecycle
    finally:
        shutil.rmtree(temporary)


def test_unique_keyword_only_public_api() -> None:
    assert gate.__all__ == (
        "build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1",
    )
    function = gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1
    signature = inspect.signature(function)
    assert tuple(signature.parameters) == ("repo_root", "state_root")
    assert all(item.kind is inspect.Parameter.KEYWORD_ONLY for item in signature.parameters.values())
    with pytest.raises(TypeError):
        function(ROOT, STATE_ROOT)  # type: ignore[misc]


def test_silent_import() -> None:
    completed = subprocess.run(
        (sys.executable, "-B", "-c", f"import {gate.__name__}"),
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": "src", "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == b""


def test_stdlib_and_local_import_boundary() -> None:
    source = (ROOT / gate.MODULE_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        node.names[0].name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
    }
    imports.update(
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )
    assert imports <= {
        "__future__", "collections", "csv", "hashlib", "io", "json", "os",
        "pathlib", "stat", "subprocess", "typing", "covalent_ext",
    }


@pytest.mark.parametrize("forbidden", ("torch", "numpy", "rdkit", "openbabel"))
def test_forbidden_dependency_absent(forbidden: str) -> None:
    source = (ROOT / gate.MODULE_PATH).read_text(encoding="utf-8").lower()
    assert f"import {forbidden}" not in source
    assert f"from {forbidden}" not in source


def test_repository_exact4_safety() -> None:
    assert gate.CANDIDATE_PATHS == tuple(sorted((
        gate.MODULE_PATH, gate.SCRIPT_PATH, gate.TEST_PATH, gate.GUIDE_PATH,
    )))
    lifecycle = gate._repository_lifecycle(ROOT)
    assert lifecycle["candidate_paths"] == list(gate.CANDIDATE_PATHS)
    assert lifecycle["lifecycle_profile"] in {
        "current11_routing_tensor_projection_contract_gate_v1_precommit_candidate",
        "current11_routing_tensor_projection_contract_gate_v1_committed_unpushed",
        "current11_routing_tensor_projection_contract_gate_v1_published_successor",
    }
    for relative in gate.CANDIDATE_PATHS:
        path = ROOT / relative
        metadata = path.lstat()
        payload = path.read_bytes()
        assert stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
        assert stat.S_IMODE(metadata.st_mode) == 0o644
        assert len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf") and b"\0" not in payload
        payload.decode("utf-8")
        assert all(not line.rstrip(b"\r\n").endswith((b" ", b"\t")) for line in payload.splitlines(keepends=True))


def test_exact4_return_type_order_and_bytes(artifacts: dict[str, bytes]) -> None:
    assert type(artifacts) is dict
    assert tuple(artifacts) == gate.ARTIFACT_NAMES
    assert len(artifacts) == 4
    assert all(type(value) is bytes for value in artifacts.values())


def test_artifact_canonical_safety(artifacts: dict[str, bytes]) -> None:
    for payload in artifacts.values():
        assert len(payload) < 1024 * 1024
        assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
        assert b"\r" not in payload and b"\0" not in payload
        assert not payload.startswith(b"\xef\xbb\xbf")
        assert b"NaN" not in payload and b"Infinity" not in payload
        payload.decode("utf-8")


def test_deterministic_double_public_build(artifacts: dict[str, bytes]) -> None:
    second = gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1(
        repo_root=ROOT, state_root=STATE_ROOT
    )
    assert second == artifacts


def test_no_formal_state_mutation() -> None:
    canonical = STATE_ROOT / gate.CANONICAL_RELATIVE
    before = gate._formal_snapshot(canonical)
    gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1(
        repo_root=ROOT, state_root=STATE_ROOT
    )
    assert gate._formal_snapshot(canonical) == before


def test_no_repository_file_write() -> None:
    before = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in gate.CANDIDATE_PATHS}
    gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1(
        repo_root=ROOT, state_root=STATE_ROOT
    )
    after = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in gate.CANDIDATE_PATHS}
    assert before == after


def test_v2_source_sha_frozen() -> None:
    assert hashlib.sha256((ROOT / gate.V2_MODULE_PATH).read_bytes()).hexdigest() == gate.V2_MODULE_SHA256


def test_v2_check_runs_exactly_twice(monkeypatch: pytest.MonkeyPatch) -> None:
    original = gate._v2._verify_existing
    calls = []
    def wrapped(**kwargs: object) -> object:
        calls.append(kwargs)
        return original(**kwargs)
    monkeypatch.setattr(gate._v2, "_verify_existing", wrapped)
    gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1(
        repo_root=ROOT, state_root=STATE_ROOT
    )
    assert len(calls) == 2 and calls[0] == calls[1]


def test_v2_check_failure_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate._v2, "_verify_existing", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("drift")))
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1(
            repo_root=ROOT, state_root=STATE_ROOT
        )


def test_v2_double_check_difference_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = gate._v2._verify_existing
    count = 0
    def changed(**kwargs: object) -> object:
        nonlocal count
        count += 1
        value = original(**kwargs)
        if count == 2:
            value = dict(value)
            value["routing_record_count"] = 274
        return value
    monkeypatch.setattr(gate._v2, "_verify_existing", changed)
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1(
            repo_root=ROOT, state_root=STATE_ROOT
        )


def test_formal_canonical_object_and_aggregate(parsed: dict[str, object]) -> None:
    report = parsed["report"]
    assert report["formal_canonical_identity"] == {"st_dev": 49, "st_ino": 69442074366}
    assert report["formal_object_identity"] == {"st_dev": 49, "st_ino": 69442074217}
    assert report["formal_canonical_readlink"] == gate.CANONICAL_READLINK
    assert report["formal_aggregate_sha256"] == gate.FORMAL_AGGREGATE_SHA256


def test_formal_exact4_identities(parsed: dict[str, object]) -> None:
    assert parsed["report"]["formal_exact4_sha256"] == {
        name: spec[2] for name, spec in gate.FORMAL_ARTIFACTS.items()
    }


def test_exact11_sample_order(parsed: dict[str, object]) -> None:
    samples = parsed["manifest"]["sample_order"]
    assert [(item["sample_index_row_id"], item["pdb_id"], item["ligand_comp_id"]) for item in samples] == list(gate.SAMPLE_ORDER)


def test_exact25_task_order(parsed: dict[str, object]) -> None:
    assert [item["semantic_task_name"] for item in parsed["manifest"]["task_order"]] == list(gate.TASK_ORDER)


def test_exact275_counts_and_order(formal_payloads: dict[str, bytes]) -> None:
    validated = gate._validate_formal(formal_payloads)
    records = validated["records"]
    assert len(records) == 275
    assert [(r["sample_index_row_id"], r["semantic_task_name"]) for r in records] == [
        (sample[0], task) for sample in gate.SAMPLE_ORDER for task in gate.TASK_ORDER
    ]


@pytest.mark.parametrize("mutation", ("duplicate", "missing", "extra", "reorder"))
def test_relational_record_drift_fails_closed(formal_payloads: dict[str, bytes], mutation: str) -> None:
    name = "current11_dataset_partial_supervision_routing_records.csv"
    columns, rows = _csv(formal_payloads[name])
    if mutation == "duplicate":
        rows[1] = dict(rows[0])
    elif mutation == "missing":
        rows.pop()
    elif mutation == "extra":
        rows.append(dict(rows[-1]))
    else:
        rows[0], rows[1] = rows[1], rows[0]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    mutated = dict(formal_payloads); mutated[name] = stream.getvalue().encode()
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate._validate_formal(mutated)


@pytest.mark.parametrize(
    ("field", "value"),
    (("sample_index_row_id", "CYS_SG_SAMPLE_INDEX_999999"), ("pdb_id", "XXXX"), ("ligand_comp_id", "XXX"), ("semantic_task_name", "extra_task")),
)
def test_identity_or_key_drift_fails_closed(formal_payloads: dict[str, bytes], field: str, value: str) -> None:
    name = "current11_dataset_partial_supervision_routing_records.csv"
    mutated = dict(formal_payloads)
    mutated[name] = _mutate_csv(mutated[name], 0, field, value)
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate._validate_formal(mutated)


def test_exact7_code_mapping(parsed: dict[str, object]) -> None:
    states = parsed["states"]
    assert states[0] == gate.STATE_ENCODING_COLUMNS
    assert [(row["code"], row["eligibility_state"]) for row in states[1]] == [
        (str(code), state) for code, state in enumerate(gate.ELIGIBILITY_STATES)
    ]
    assert all(
        "routing metadata only; never a label" in row["applicability_rule"]
        for row in states[1]
    )


def test_exact_state_counts(parsed: dict[str, object]) -> None:
    assert parsed["report"]["eligibility_state_counts"] == gate.STATE_COUNTS


@pytest.mark.parametrize(
    ("field", "value"),
    (("eligibility_state", "unknown_state"), ("evidence_scope", "UNKNOWN_SCOPE"), ("blocking_reason_code", "UNKNOWN_REASON")),
)
def test_unknown_closed_vocabulary_fails(formal_payloads: dict[str, bytes], field: str, value: str) -> None:
    name = "current11_dataset_partial_supervision_routing_records.csv"
    mutated = dict(formal_payloads)
    mutated[name] = _mutate_csv(mutated[name], 0, field, value)
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate._validate_formal(mutated)


@pytest.mark.parametrize("vocabulary", ("eligibility_state_vocabulary", "evidence_scope_vocabulary", "blocking_reason_vocabulary"))
@pytest.mark.parametrize("mutation", ("extra", "reorder"))
def test_manifest_vocabulary_closed_and_ordered(formal_payloads: dict[str, bytes], vocabulary: str, mutation: str) -> None:
    def change(manifest: dict[str, object]) -> None:
        values = manifest[vocabulary]
        assert isinstance(values, list)
        if mutation == "extra": values.append("EXTRA")
        else: values[0], values[1] = values[1], values[0]
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate._validate_formal(_mutate_manifest(formal_payloads, change))


def test_exact5_and_b3(parsed: dict[str, object]) -> None:
    masks = parsed["manifest"]["canonical_mask_semantics"]
    assert len(masks) == 5
    assert [(item["semantic_name"], item["display_alias"]) for item in masks] == [(row[1], row[2]) for row in gate.CANONICAL_MASKS]
    assert masks[3]["semantic_name"] == "scaffold_only" and masks[3]["display_alias"] == "B3"


@pytest.mark.parametrize("mutation", ("sixth", "alias_only", "fourth_role"))
def test_mask_boundary_drift_fails(formal_payloads: dict[str, bytes], monkeypatch: pytest.MonkeyPatch, mutation: str) -> None:
    if mutation == "sixth":
        monkeypatch.setattr(gate, "CANONICAL_MASKS", gate.CANONICAL_MASKS + ((5,"seed_only","D",("seed",),()),))
    elif mutation == "alias_only":
        monkeypatch.setattr(gate, "CANONICAL_MASKS", ((0,"A","A",("warhead",),("scaffold","linker")),) + gate.CANONICAL_MASKS[1:])
    else:
        row = gate.CANONICAL_MASKS[0]
        monkeypatch.setattr(gate, "CANONICAL_MASKS", ((row[0],row[1],row[2],row[3]+("anchor",),row[4]),) + gate.CANONICAL_MASKS[1:])
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate._validate_formal(formal_payloads)


def test_generation_availability_loss_axes_independent(parsed: dict[str, object]) -> None:
    manifest = parsed["manifest"]
    assert manifest["generation_mask_availability_loss_are_independent_axes"] is True
    assert manifest["seed_anchor_is_orthogonal_to_exact5"] is True


def test_task_schema_exact25_by_25(parsed: dict[str, object]) -> None:
    columns, rows = parsed["tasks"]
    assert columns == gate.TASK_SCHEMA_COLUMNS and len(columns) == 25
    assert len(rows) == 25
    assert [row["task_index"] for row in rows] == [str(index) for index in range(25)]
    assert [row["semantic_task_name"] for row in rows] == list(gate.TASK_ORDER)


def test_task_schema_canonical_distributions(parsed: dict[str, object]) -> None:
    for row in parsed["tasks"][1]:
        distribution = json.loads(row["current11_state_distribution_json"])
        assert set(distribution) <= set(gate.ELIGIBILITY_STATES)
        assert all(type(value) is int and value >= 0 for value in distribution.values())
        assert json.dumps(distribution, sort_keys=True, separators=(",", ":")) == row["current11_state_distribution_json"]


def test_task_schema_all_loss_false(parsed: dict[str, object]) -> None:
    assert {row["loss_allowed_now"] for row in parsed["tasks"][1]} == {"false"}


@pytest.mark.parametrize("column", ("proposed_value_dtype", "proposed_logical_shape", "missing_representation", "applicability_representation", "downstream_consumer_boundary"))
def test_task_schema_required_semantics_nonempty(parsed: dict[str, object], column: str) -> None:
    assert all(row[column].strip() for row in parsed["tasks"][1])


@pytest.mark.parametrize(
    ("row_index", "field", "value"),
    (
        (0, "semantic_task_name", "reordered_or_extra_task"),
        (0, "proposed_value_dtype", "float64"),
        (0, "proposed_logical_shape", "[S,999]"),
        (0, "loss_allowed_now", "true"),
        (4, "data_availability_permitted_after_payload_validation", "true"),
        (12, "observed_geometry_only", "false"),
    ),
)
def test_task_schema_semantic_drift_fails_closed(
    formal_payloads: dict[str, bytes], row_index: int, field: str, value: str
) -> None:
    validated = gate._validate_formal(formal_payloads)
    rows = gate._task_schema_rows(validated)
    rows[row_index][field] = value
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate._validate_task_schema_rows(rows, validated)


def test_candidate_never_promoted_to_authoritative(parsed: dict[str, object]) -> None:
    for row in parsed["tasks"][1]:
        if row["candidate_only"] == "true":
            assert row["data_availability_permitted_after_payload_validation"] == "false"


def test_observed_geometry_not_semantically_promoted(parsed: dict[str, object]) -> None:
    rows = parsed["tasks"][1]
    observed = [row for row in rows if row["observed_geometry_only"] == "true"]
    assert len(observed) == 1
    assert observed[0]["semantic_task_name"] == "observed_complex_geometry_supervision"
    assert "no bond/order/post-state inference" in observed[0]["downstream_consumer_boundary"]


def test_projection_manifest_exact24_fields(parsed: dict[str, object]) -> None:
    fields = parsed["manifest"]["projection_fields"]
    assert len(fields) == 24
    assert [item["name"] for item in fields] == list(gate.PROJECTION_FIELD_NAMES)
    expected = {
        "name", "container_kind", "dtype", "rank", "logical_shape", "axes",
        "allowed_values", "missing_semantics", "invariants", "formal_source",
        "model_input_allowed_now", "loss_participation_allowed_now",
    }
    assert all(set(item) == expected for item in fields)


def test_projection_contract_only_boundary(parsed: dict[str, object]) -> None:
    report = parsed["report"]
    for field in (
        "projection_instance_materialized", "tensor_materialized",
        "task_payloads_materialized", "candidate_payloads_materialized",
        "task_payload_validity_materialized", "data_availability_mask_materialized",
    ):
        assert report[field] is False


def test_permitted_55_is_not_availability(parsed: dict[str, object]) -> None:
    report = parsed["report"]
    assert report["eligibility_permitted_authoritative_or_observed_count"] == 55
    assert "data_available_count" not in report
    assert report["data_availability_mask_materialized"] is False


def test_candidate_55_is_not_extracted_payload(parsed: dict[str, object]) -> None:
    report = parsed["report"]
    assert report["candidate_eligible_count"] == 55
    assert report["candidate_payloads_materialized"] is False


@pytest.mark.parametrize("field", ("training_loss_authorized", "current_runtime_consumer_available"))
@pytest.mark.parametrize("source", ("records", "tasks", "samples"))
def test_formal_true_loss_or_runtime_fails(formal_payloads: dict[str, bytes], field: str, source: str) -> None:
    names = {
        "records": "current11_dataset_partial_supervision_routing_records.csv",
        "tasks": "current11_dataset_partial_supervision_task_coverage.csv",
        "samples": "current11_dataset_partial_supervision_sample_coverage.csv",
    }
    name = names[source]
    mutated = dict(formal_payloads)
    mutated[name] = _mutate_csv(mutated[name], 0, field, "true")
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate._validate_formal(mutated)


def test_loss_and_runtime_exact275_false(parsed: dict[str, object]) -> None:
    report = parsed["report"]
    assert report["loss_authorized_true_count"] == 0
    assert report["runtime_consumer_available_true_count"] == 0
    contract = parsed["manifest"]["current_all_false_authority_contract"]
    assert contract["shape"] == [11, 25]
    assert contract["loss_authorization_mask_materialized"] is False
    assert contract["runtime_consumer_available_mask_materialized"] is False


def test_digest_domain_framing_and_known_vector(artifacts: dict[str, bytes]) -> None:
    stable = {name: artifacts[name] for name in gate.CONTRACT_ARTIFACT_NAMES}
    assert gate._contract_digest(stable) == EXPECTED_CONTRACT_DIGEST
    digest = hashlib.sha256()
    digest.update(gate.CONTRACT_DIGEST_DOMAIN_TAG)
    for name in gate.CONTRACT_ARTIFACT_NAMES:
        encoded = name.encode()
        digest.update(len(encoded).to_bytes(8, "big")); digest.update(encoded)
        digest.update(len(artifacts[name]).to_bytes(8, "big")); digest.update(artifacts[name])
    assert digest.hexdigest() == EXPECTED_CONTRACT_DIGEST


def test_digest_excludes_report_and_lifecycle(artifacts: dict[str, bytes]) -> None:
    stable = {name: artifacts[name] for name in gate.CONTRACT_ARTIFACT_NAMES}
    changed_report = dict(artifacts)
    changed_report[gate.ARTIFACT_NAMES[3]] = b"different lifecycle report\n"
    assert gate._contract_digest(stable) == gate._contract_digest({name: changed_report[name] for name in gate.CONTRACT_ARTIFACT_NAMES})


def test_gate_report_truthful_summary(parsed: dict[str, object]) -> None:
    report = parsed["report"]
    assert report["schema_version"] == gate.GATE_REPORT_SCHEMA_VERSION
    assert report["gate_status"] == "PASS_CONTRACT_ONLY"
    assert report["artifact_file_count"] == 4
    assert report["formal_sidecar_check_passed"] is True
    assert report["formal_double_check_identical"] is True
    assert (report["sample_count"], report["task_count"], report["routing_record_count"], report["mask_count"]) == (11, 25, 275, 5)


def test_no_object_dtype_or_hidden_cast_semantics(parsed: dict[str, object]) -> None:
    manifest = parsed["manifest"]
    assert manifest["serialization_rules"]["python_object_tensor_forbidden"] is True
    assert manifest["serialization_rules"]["implicit_casts_forbidden"] is True
    assert manifest["serialization_rules"]["bool_as_integer_index_forbidden"] is True
    assert manifest["serialization_rules"]["float_as_category_or_index_forbidden"] is True
    assert all("object" not in row["proposed_value_dtype"].lower() for row in parsed["tasks"][1])


@pytest.mark.parametrize(
    ("profile", "expected"),
    (
        ("precommit", "current11_routing_tensor_projection_contract_gate_v1_precommit_candidate"),
        ("committed", "current11_routing_tensor_projection_contract_gate_v1_committed_unpushed"),
        ("published", "current11_routing_tensor_projection_contract_gate_v1_published_successor"),
    ),
)
def test_repository_lifecycle_exact3(profile: str, expected: str) -> None:
    built, lifecycle = _lifecycle_clone(profile)
    assert lifecycle["lifecycle_profile"] == expected
    assert _report(built)["contract_digest"] == EXPECTED_CONTRACT_DIGEST


def test_current_lifecycle_matches_runtime(parsed: dict[str, object]) -> None:
    expected = gate._repository_lifecycle(ROOT)
    assert parsed["report"]["repository_lifecycle"] == expected


def test_cli_success_one_compact_json_line() -> None:
    completed = _run_checker("--repo-root", os.fspath(ROOT), "--state-root", os.fspath(STATE_ROOT))
    assert completed.returncode == 0 and completed.stderr == b""
    assert completed.stdout.count(b"\n") == 1
    decoded = json.loads(completed.stdout)
    assert decoded["gate_status"] == "PASS_CONTRACT_ONLY"
    assert completed.stdout == (json.dumps(decoded, sort_keys=True, separators=(",", ":")) + "\n").encode()
    assert b"sample_identity_supervision" not in completed.stdout


@pytest.mark.parametrize(
    "arguments",
    (
        (), ("-h",), ("--help",), ("--output", "x"), ("--output-dir", "x"),
        ("--materialize",), ("--tensorize",), ("--train",), ("--loss",),
        ("--approve",), ("--payload", "x"), ("--availability", "x"),
        ("--schema-override", "x"), ("extra",), ("--repo-root", os.fspath(ROOT)),
        ("--state-root", os.fspath(STATE_ROOT)), ("--unknown",), ("--repo", os.fspath(ROOT)),
    ),
)
def test_cli_rejects_invalid_interface(arguments: tuple[str, ...]) -> None:
    completed = _run_checker(*arguments)
    assert completed.returncode == 1 and completed.stdout == b""
    assert completed.stderr == (gate.ERROR_TOKEN + "\n").encode()


def test_cli_writes_no_file() -> None:
    before = subprocess.check_output(("git", "status", "--porcelain=v1", "--untracked-files=all"), cwd=ROOT)
    completed = _run_checker("--repo-root", os.fspath(ROOT), "--state-root", os.fspath(STATE_ROOT))
    after = subprocess.check_output(("git", "status", "--porcelain=v1", "--untracked-files=all"), cwd=ROOT)
    assert completed.returncode == 0 and before == after


@pytest.mark.parametrize("bad", (Path("relative"), STATE_ROOT / "missing"))
def test_api_rejects_bad_roots(bad: Path) -> None:
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1(
            repo_root=bad, state_root=STATE_ROOT
        )


def test_feature_semantics_boundary(parsed: dict[str, object]) -> None:
    boundary = parsed["manifest"]["feature_semantics_boundary"]
    assert boundary == {
        "step12d_smoke_legality_verified": True,
        "step12d_final_feature_semantics_contract": False,
        "step12d_training_readiness_authority": False,
        "unknown_atom_feature_policy": "UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED",
        "feature_semantics_known": False,
        "feature_semantics_reaudit_required_before_training": True,
    }


def test_readiness_fail_closed(parsed: dict[str, object]) -> None:
    readiness = parsed["report"]["readiness"]
    assert readiness["tensor_projection_contract_gate_implemented"] is True
    assert readiness["tensor_projection_contract_gate_passed"] is True
    assert readiness["ready_for_tensor_projection_materialization"] is False
    assert readiness["ready_for_tensor_materialization"] is False
    assert readiness["ready_for_dataloader_integration"] is False
    assert readiness["ready_for_model_integration"] is False
    assert readiness["feature_semantics_reaudit_required_before_training"] is True
    assert readiness["ready_for_training"] is False
    assert readiness["training_performed"] is False
