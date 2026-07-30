from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import inspect
import io
import json
import os
import stat
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_current11_real_human_review_submission_bundle_compiler_v1
    as compiler,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as ingestion_interface,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_submission_adapter_design_v1
    as adapter_design,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_submission_adapter_v1
    as public_adapter,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / (
    "data/derived/covalent_small/"
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_packages_v1"
)
PACKAGE_INDEX = (
    PACKAGE_ROOT
    / "covapie_current11_warhead_boundary_review_package_index.csv"
)
PACKAGE_OPTIONS = (
    PACKAGE_ROOT
    / "covapie_current11_warhead_boundary_candidate_review_options.csv"
)
REVIEW_TEMPLATES = (
    PACKAGE_ROOT
    / "covapie_current11_warhead_boundary_review_record_templates.csv"
)
SUBMISSION_BATCH_ID = "covapie_current11_compiler_test_batch_v1"


def _load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PREPARER = _load_script(
    "covapie_current11_workspace_preparer_for_compiler_tests",
    REPO_ROOT
    / "scripts/"
    "prepare_covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "human_review_workspace_v1.py",
)
CLI = _load_script(
    "covapie_current11_submission_compiler_cli_for_tests",
    REPO_ROOT
    / "scripts/compile_covapie_current11_real_human_review_"
    "submission_bundle_v1.py",
)


def _csv_rows(payload: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with io.StringIO(payload.decode("utf-8"), newline="") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), list(reader)


def _csv_bytes(
    fields: tuple[str, ...],
    rows: list[dict[str, str]],
) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=fields,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _package_payloads() -> dict[str, bytes]:
    return {
        "package_index_csv": PACKAGE_INDEX.read_bytes(),
        "package_candidate_options_csv": PACKAGE_OPTIONS.read_bytes(),
        "review_record_templates_csv": REVIEW_TEMPLATES.read_bytes(),
    }


def _completed_worklist(
    *,
    revise_positions: frozenset[int] = frozenset(),
    extra_quarantine_positions: frozenset[int] = frozenset(),
) -> tuple[bytes, bytes]:
    workspace = PREPARER.build_workspace_payloads(REPO_ROOT)
    fields, rows = _csv_rows(workspace["review_worklist.csv"])
    _, options = _csv_rows(workspace["eligible_candidate_options.csv"])
    options_by_sample: dict[str, list[dict[str, str]]] = {}
    for option in options:
        options_by_sample.setdefault(option["sample_index_row_id"], []).append(
            option
        )
    for position, row in enumerate(rows):
        row.update(
            {
                "reviewer_id": "human-reviewer",
                "review_rationale": f"Human rationale for row {position}.",
                "review_notes": f"Preserved note for row {position}.",
                "reviewer_provenance_attested": "true",
                "reviewer_provenance_attestor_id": "human-attestor",
                "submission_source_label": "compiler-unit-test",
                "review_completed": "true",
            }
        )
        if (
            5 <= position <= 9
            or position in extra_quarantine_positions
        ):
            row.update(
                {
                    "review_decision": "quarantine",
                    "selected_bridge_candidate_index_0based": "",
                    "selected_bridge_candidate_record_sha256": "",
                    "reviewed_warhead_atom_ids_json": "[]",
                    "reviewed_warhead_attachment_atom_id": "",
                    "reviewed_nonwarhead_boundary_atom_id": "",
                    "reviewed_attachment_boundary_bond_order": "",
                    "reviewed_boundary_bond_id": "",
                }
            )
        elif position in revise_positions:
            row.update(
                {
                    "review_decision": "revise_atom_set_and_boundary",
                    "selected_bridge_candidate_index_0based": "",
                    "selected_bridge_candidate_record_sha256": "",
                    "reviewed_warhead_atom_ids_json": '["A1"]',
                    "reviewed_warhead_attachment_atom_id": "A1",
                    "reviewed_nonwarhead_boundary_atom_id": "Z1",
                    "reviewed_attachment_boundary_bond_order": "single",
                    "reviewed_boundary_bond_id": "A1|Z1|single",
                }
            )
        else:
            option = options_by_sample[row["sample_index_row_id"]][0]
            row.update(
                {
                    "review_decision": "select_admitted_candidate",
                    "selected_bridge_candidate_index_0based":
                        option["source_bridge_candidate_index_0based"],
                    "selected_bridge_candidate_record_sha256":
                        option["source_bridge_candidate_record_sha256"],
                    "reviewed_warhead_atom_ids_json":
                        option["warhead_side_atom_ids"],
                    "reviewed_warhead_attachment_atom_id":
                        option["warhead_attachment_atom_id"],
                    "reviewed_nonwarhead_boundary_atom_id":
                        option["nonwarhead_boundary_atom_id"],
                    "reviewed_attachment_boundary_bond_order":
                        option["boundary_bond_order"],
                    "reviewed_boundary_bond_id": option["boundary_bond_id"],
                }
            )
    return _csv_bytes(fields, rows), workspace["eligible_candidate_options.csv"]


def _valid_inputs(
    *,
    revise_positions: frozenset[int] = frozenset(),
    extra_quarantine_positions: frozenset[int] = frozenset(),
) -> dict[str, object]:
    worklist, eligible = _completed_worklist(
        revise_positions=revise_positions,
        extra_quarantine_positions=extra_quarantine_positions,
    )
    return {
        "review_worklist_csv": worklist,
        "eligible_candidate_options_csv": eligible,
        **_package_payloads(),
        "submission_batch_id": SUBMISSION_BATCH_ID,
    }


def _mutate_worklist(
    inputs: dict[str, object],
    mutation,
) -> dict[str, object]:
    result = dict(inputs)
    fields, rows = _csv_rows(result["review_worklist_csv"])
    mutation(rows)
    result["review_worklist_csv"] = _csv_bytes(fields, rows)
    return result


def _compile(inputs: dict[str, object]) -> bytes:
    return (
        compiler
        .compile_covapie_current11_real_human_review_submission_bundle_v1(
            **inputs
        )
    )


def test_public_signature_and_all_contract() -> None:
    function = (
        compiler
        .compile_covapie_current11_real_human_review_submission_bundle_v1
    )
    assert compiler.__all__ == (
        "compile_covapie_current11_real_human_review_submission_bundle_v1",
    )
    signature = inspect.signature(function)
    assert tuple(signature.parameters) == (
        "review_worklist_csv",
        "eligible_candidate_options_csv",
        "package_index_csv",
        "package_candidate_options_csv",
        "review_record_templates_csv",
        "submission_batch_id",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert signature.return_annotation in {bytes, "bytes"}


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("review_worklist_csv", bytearray()),
        ("eligible_candidate_options_csv", memoryview(b"")),
        ("package_index_csv", ""),
        ("package_candidate_options_csv", None),
        ("review_record_templates_csv", Path("templates.csv")),
        ("submission_batch_id", b"batch"),
        ("submission_batch_id", " batch "),
    ),
)
def test_exact_input_types_are_required(field: str, bad_value: object) -> None:
    inputs = _valid_inputs()
    inputs[field] = bad_value
    with pytest.raises(ValueError):
        _compile(inputs)


@pytest.mark.parametrize(
    "field",
    (
        "package_index_csv",
        "package_candidate_options_csv",
        "review_record_templates_csv",
    ),
)
def test_frozen_package_source_sha_tamper_is_rejected(field: str) -> None:
    inputs = _valid_inputs()
    inputs[field] = inputs[field] + b"\n"
    with pytest.raises(ValueError, match="frozen source SHA256 mismatch"):
        _compile(inputs)


def test_package_identity_tamper_is_rejected_after_source_hash_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _valid_inputs()
    fields, rows = _csv_rows(inputs["package_index_csv"])
    rows[0]["pdb_id"] = "TAMPERED"
    tampered = _csv_bytes(fields, rows)
    monkeypatch.setattr(
        compiler,
        "_PACKAGE_INDEX_SHA256",
        hashlib.sha256(tampered).hexdigest(),
    )
    inputs["package_index_csv"] = tampered
    with pytest.raises(ValueError, match="identity mismatch"):
        _compile(inputs)


def test_wrong_worklist_field_inventory_is_rejected() -> None:
    inputs = _valid_inputs()
    fields, rows = _csv_rows(inputs["review_worklist_csv"])
    inputs["review_worklist_csv"] = _csv_bytes(fields[:-1], [
        {field: row[field] for field in fields[:-1]} for row in rows
    ])
    with pytest.raises(ValueError, match="field inventory mismatch"):
        _compile(inputs)


def test_non_exact_11_worklist_is_rejected() -> None:
    inputs = _valid_inputs()
    fields, rows = _csv_rows(inputs["review_worklist_csv"])
    inputs["review_worklist_csv"] = _csv_bytes(fields, rows[:-1])
    with pytest.raises(ValueError, match="exactly 11 rows"):
        _compile(inputs)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda rows: rows[1].__setitem__(
            "sample_index_row_id", rows[0]["sample_index_row_id"]
        ),
        lambda rows: rows[1].__setitem__("package_item_order_0based", "0"),
    ),
)
def test_duplicate_sample_or_order_is_rejected(mutation) -> None:
    with pytest.raises(ValueError):
        _compile(_mutate_worklist(_valid_inputs(), mutation))


def test_worklist_identity_tamper_is_rejected() -> None:
    inputs = _mutate_worklist(
        _valid_inputs(),
        lambda rows: rows[0].__setitem__("source_candidate_set_sha256", "0" * 64),
    )
    with pytest.raises(ValueError, match="frozen identity mismatch"):
        _compile(inputs)


def test_incomplete_review_is_rejected() -> None:
    inputs = _mutate_worklist(
        _valid_inputs(),
        lambda rows: rows[0].__setitem__("review_completed", "false"),
    )
    with pytest.raises(ValueError, match="review completion"):
        _compile(inputs)


def test_reviewer_provenance_false_is_rejected() -> None:
    inputs = _mutate_worklist(
        _valid_inputs(),
        lambda rows: rows[0].__setitem__(
            "reviewer_provenance_attested", "false"
        ),
    )
    with pytest.raises(ValueError, match="provenance attestation"):
        _compile(inputs)


def test_malformed_atom_json_is_rejected() -> None:
    inputs = _mutate_worklist(
        _valid_inputs(),
        lambda rows: rows[0].__setitem__(
            "reviewed_warhead_atom_ids_json", "["
        ),
    )
    with pytest.raises(ValueError, match=r"JSON list\[str\] required"):
        _compile(inputs)


def test_deeply_nested_atom_json_fails_closed_before_public_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _mutate_worklist(
        _valid_inputs(),
        lambda rows: rows[0].__setitem__(
            "reviewed_warhead_atom_ids_json",
            "[" * 2000 + "0" + "]" * 2000,
        ),
    )

    def forbidden_adapter(*, source_payload: bytes):
        raise AssertionError("public adapter must not be called")

    monkeypatch.setattr(
        public_adapter,
        "adapt_current11_warhead_boundary_review_submission_bundle_v1",
        forbidden_adapter,
    )
    with pytest.raises(ValueError, match=r"JSON list\[str\] required"):
        _compile(inputs)


@pytest.mark.parametrize(
    "atoms",
    (
        '["Z","A"]',
        '["A","A"]',
    ),
)
def test_unsorted_or_duplicate_atom_ids_are_rejected(atoms: str) -> None:
    inputs = _valid_inputs(revise_positions=frozenset({0}))
    inputs = _mutate_worklist(
        inputs,
        lambda rows: rows[0].__setitem__(
            "reviewed_warhead_atom_ids_json", atoms
        ),
    )
    with pytest.raises(ValueError, match="sorted and unique"):
        _compile(inputs)


def test_selected_candidate_not_found_is_rejected() -> None:
    inputs = _mutate_worklist(
        _valid_inputs(),
        lambda rows: rows[0].__setitem__(
            "selected_bridge_candidate_index_0based", "999"
        ),
    )
    with pytest.raises(ValueError, match="match full and eligible"):
        _compile(inputs)


def test_selected_candidate_sha_mismatch_is_rejected() -> None:
    inputs = _mutate_worklist(
        _valid_inputs(),
        lambda rows: rows[0].__setitem__(
            "selected_bridge_candidate_record_sha256", "0" * 64
        ),
    )
    with pytest.raises(ValueError, match="match full and eligible"):
        _compile(inputs)


def test_package_candidate_admitted_eligibility_tamper_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _valid_inputs()
    fields, rows = _csv_rows(inputs["package_candidate_options_csv"])
    rows[0]["candidate_admitted"] = "false"
    tampered = _csv_bytes(fields, rows)
    monkeypatch.setattr(
        compiler,
        "_PACKAGE_OPTIONS_SHA256",
        hashlib.sha256(tampered).hexdigest(),
    )
    inputs["package_candidate_options_csv"] = tampered
    with pytest.raises(ValueError, match="admitted/eligible mismatch"):
        _compile(inputs)


def test_eligible_projection_frozen_field_tamper_is_rejected_before_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _valid_inputs()
    fields, rows = _csv_rows(inputs["eligible_candidate_options_csv"])
    rows[0]["boundary_bond_id"] = "TAMPERED|BOUNDARY|single"
    inputs["eligible_candidate_options_csv"] = _csv_bytes(fields, rows)

    def forbidden_adapter(*, source_payload: bytes):
        raise AssertionError("public adapter must not be called")

    monkeypatch.setattr(
        public_adapter,
        "adapt_current11_warhead_boundary_review_submission_bundle_v1",
        forbidden_adapter,
    )
    with pytest.raises(ValueError, match="frozen ordered projection mismatch"):
        _compile(inputs)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("reviewed_warhead_atom_ids_json", '["WRONG"]'),
        ("reviewed_warhead_attachment_atom_id", "WRONG"),
        ("reviewed_nonwarhead_boundary_atom_id", "WRONG"),
        ("reviewed_attachment_boundary_bond_order", "double"),
        ("reviewed_boundary_bond_id", "WRONG|BOUNDARY|single"),
    ),
)
def test_selected_reviewed_evidence_mismatch_is_rejected(
    field: str,
    value: str,
) -> None:
    inputs = _mutate_worklist(
        _valid_inputs(),
        lambda rows: rows[0].__setitem__(field, value),
    )
    with pytest.raises(ValueError, match="does not exactly match"):
        _compile(inputs)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("selected_bridge_candidate_index_0based", "0"),
        ("reviewed_boundary_bond_id", "A|B|single"),
        ("reviewed_warhead_atom_ids_json", '["A"]'),
        ("reviewed_warhead_atom_ids_json", "[ ]"),
    ),
)
def test_quarantine_with_selected_or_boundary_evidence_is_rejected(
    field: str,
    value: str,
) -> None:
    inputs = _mutate_worklist(
        _valid_inputs(),
        lambda rows: rows[5].__setitem__(field, value),
    )
    with pytest.raises(ValueError, match="quarantine evidence"):
        _compile(inputs)


def test_valid_select_compiles() -> None:
    payload = json.loads(_compile(_valid_inputs()))
    assert payload["submission_items"][0]["review_record_payload"][
        "review_decision"
    ] == "select_admitted_candidate"


def test_valid_quarantine_compiles() -> None:
    payload = json.loads(
        _compile(_valid_inputs(extra_quarantine_positions=frozenset({0})))
    )
    review = payload["submission_items"][0]["review_record_payload"]
    assert review["review_decision"] == "quarantine"
    assert review["selected_bridge_candidate_index_0based"] is None
    assert review["reviewed_warhead_atom_ids"] == []


def test_valid_revise_compiles_exact_one_boundary_contract() -> None:
    payload = json.loads(
        _compile(_valid_inputs(revise_positions=frozenset({0})))
    )
    review = payload["submission_items"][0]["review_record_payload"]
    assert review["review_decision"] == "revise_atom_set_and_boundary"
    assert review["selected_bridge_candidate_index_0based"] is None
    assert review["reviewed_warhead_atom_ids"] == ["A1"]
    assert review["reviewed_boundary_bond_id"] == "A1|Z1|single"


def test_mixed_exact_11_bundle_and_field_type_order_contract() -> None:
    compiled = _compile(_valid_inputs(revise_positions=frozenset({0})))
    bundle = json.loads(compiled)
    assert tuple(bundle) == tuple(adapter_design.SUBMISSION_BUNDLE_FIELDS)
    assert len(bundle["submission_items"]) == 11
    assert [
        item["review_record_payload"]["review_decision"]
        for item in bundle["submission_items"]
    ].count("revise_atom_set_and_boundary") == 1
    for item in bundle["submission_items"]:
        assert tuple(item) == tuple(adapter_design.SUBMISSION_ITEM_FIELDS)
        review = item["review_record_payload"]
        assert tuple(review) == tuple(adapter_design.REVIEW_PAYLOAD_FIELDS)
        assert type(review["warhead_type_candidate_class_index_0based"]) is int
        assert type(review["total_candidate_count"]) is int
        assert type(review["admitted_candidate_count"]) is int
        assert type(review["reviewed_warhead_atom_ids"]) is list
        assert type(item["reviewer_provenance_attested"]) is bool
        assert "review_record_sha256" not in review


def test_compiled_bytes_are_accepted_by_public_adapter() -> None:
    compiled = _compile(_valid_inputs())
    response = (
        public_adapter
        .adapt_current11_warhead_boundary_review_submission_bundle_v1(
            source_payload=compiled
        )
    )
    assert response["adapter_passed"] is True
    assert response["reason"] == "PASSED"
    assert len(response["adapter_result_records"]) == 11
    assert len(response["adapted_submissions"]) == 11
    assert all(
        result["outcome"] == "adapted"
        for result in response["adapter_result_records"]
    )


def test_compiler_calls_public_adapter_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = (
        public_adapter
        .adapt_current11_warhead_boundary_review_submission_bundle_v1
    )
    calls: list[bytes] = []

    def counted(*, source_payload: bytes):
        calls.append(source_payload)
        return original(source_payload=source_payload)

    monkeypatch.setattr(
        public_adapter,
        "adapt_current11_warhead_boundary_review_submission_bundle_v1",
        counted,
    )
    compiled = _compile(_valid_inputs())
    assert calls == [compiled]


def test_malformed_adapter_success_response_fails_closed_as_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        public_adapter,
        "adapt_current11_warhead_boundary_review_submission_bundle_v1",
        lambda *, source_payload: {
            "adapter_passed": True,
            "reason": "PASSED",
            "adapter_result_records": ({"outcome": "adapted",
                                        "passed": True,
                                        "reason": "PASSED"},) * 11,
            "adapted_submissions": (({}, {}),) * 11,
        },
    )
    with pytest.raises(ValueError, match="adapter response invalid"):
        _compile(_valid_inputs())


def test_compiler_does_not_call_ingestion_interface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(**_kwargs):
        raise AssertionError("ingestion interface must not be called")

    monkeypatch.setattr(
        ingestion_interface,
        "evaluate_current11_warhead_boundary_review_ingestion_v1",
        forbidden,
    )
    assert len(json.loads(_compile(_valid_inputs()))["submission_items"]) == 11


def test_inputs_are_unchanged_and_output_is_deterministic() -> None:
    inputs = _valid_inputs()
    snapshots = {
        key: copy.copy(value)
        for key, value in inputs.items()
        if type(value) is bytes
    }
    first = _compile(inputs)
    second = _compile(inputs)
    assert first == second
    assert all(inputs[key] == value for key, value in snapshots.items())
    assert type(first) is bytes
    assert not first.startswith(b"\xef\xbb\xbf")
    assert b"\x00" not in first
    assert b"\n" not in first
    assert len(first) < adapter_design.MAX_SOURCE_PAYLOAD_BYTES


def _write_workspace(path: Path, inputs: dict[str, object]) -> None:
    path.mkdir()
    (path / "review_worklist.csv").write_bytes(inputs["review_worklist_csv"])
    (path / "eligible_candidate_options.csv").write_bytes(
        inputs["eligible_candidate_options_csv"]
    )


def test_cli_rejects_repository_internal_output(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_workspace(workspace, _valid_inputs())
    destination = REPO_ROOT / "forbidden-compiler-output.json"
    with pytest.raises(ValueError, match="outside the Git repository"):
        CLI.compile_workspace_to_file(
            repo_root=REPO_ROOT,
            workspace_dir=workspace,
            output_file=destination,
            submission_batch_id=SUBMISSION_BATCH_ID,
        )
    assert not destination.exists()


def test_cli_rejects_existing_output(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_workspace(workspace, _valid_inputs())
    destination = tmp_path / "existing.json"
    destination.write_text("preserve", encoding="utf-8")
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        CLI.compile_workspace_to_file(
            repo_root=REPO_ROOT,
            workspace_dir=workspace,
            output_file=destination,
            submission_batch_id=SUBMISSION_BATCH_ID,
        )
    assert destination.read_text(encoding="utf-8") == "preserve"


def test_cli_rejects_output_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_workspace(workspace, _valid_inputs())
    destination = tmp_path / "submission.json"
    destination.symlink_to(tmp_path / "missing-target.json")
    with pytest.raises(FileExistsError, match="must not be a symlink"):
        CLI.compile_workspace_to_file(
            repo_root=REPO_ROOT,
            workspace_dir=workspace,
            output_file=destination,
            submission_batch_id=SUBMISSION_BATCH_ID,
        )
    assert destination.is_symlink()
    assert not (tmp_path / "missing-target.json").exists()


def test_cli_success_creates_only_one_0644_json_file(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_workspace(workspace, _valid_inputs())
    output_parent = tmp_path / "output"
    output_parent.mkdir()
    destination = output_parent / "submission.json"
    result = CLI.compile_workspace_to_file(
        repo_root=REPO_ROOT,
        workspace_dir=workspace,
        output_file=destination,
        submission_batch_id=SUBMISSION_BATCH_ID,
    )
    assert tuple(path.name for path in output_parent.iterdir()) == (
        "submission.json",
    )
    assert stat.S_IMODE(destination.stat().st_mode) == 0o644
    payload = destination.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == result["bundle_sha256"]
    assert len(json.loads(payload)["submission_items"]) == 11
    assert result["adapter_passed"] is True


def test_cli_atomic_failure_leaves_no_temp_or_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "submission.json"

    def failed_link(*_args, **_kwargs):
        raise OSError("synthetic link failure")

    monkeypatch.setattr(os, "link", failed_link)
    with pytest.raises(OSError, match="synthetic link failure"):
        CLI._atomic_create_external_file(destination, b"{}")
    assert list(tmp_path.iterdir()) == []


def test_cli_post_link_failure_removes_created_destination_and_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "submission.json"
    real_link = os.link

    def link_then_fail(*args, **kwargs):
        real_link(*args, **kwargs)
        raise OSError("synthetic post-link failure")

    monkeypatch.setattr(os, "link", link_then_fail)
    with pytest.raises(OSError, match="synthetic post-link failure"):
        CLI._atomic_create_external_file(destination, b"{}")
    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


def test_cli_post_link_validation_failure_removes_destination_and_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "submission.json"

    def failed_validation(**_kwargs):
        raise OSError("synthetic published validation failure")

    monkeypatch.setattr(
        CLI,
        "_validate_published_destination",
        failed_validation,
    )
    with pytest.raises(OSError, match="synthetic published validation failure"):
        CLI._atomic_create_external_file(destination, b"{}")
    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


def test_cli_main_stdout_summary_and_no_stderr(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = tmp_path / "workspace"
    _write_workspace(workspace, _valid_inputs())
    destination = tmp_path / "submission.json"
    status = CLI.main(
        (
            "--repo-root",
            str(REPO_ROOT),
            "--workspace-dir",
            str(workspace),
            "--output-file",
            str(destination),
            "--submission-batch-id",
            SUBMISSION_BATCH_ID,
        )
    )
    captured = capsys.readouterr()
    assert status == 0
    assert captured.err == ""
    assert captured.out.splitlines() == [
        f"output_path={destination}",
        "source_worklist_sha256="
        + hashlib.sha256(
            (workspace / "review_worklist.csv").read_bytes()
        ).hexdigest(),
        "bundle_sha256=" + hashlib.sha256(destination.read_bytes()).hexdigest(),
        "item_count=11",
        "decision_counts=select_admitted_candidate:6,"
        "revise_atom_set_and_boundary:0,quarantine:5",
        "adapter_passed=true",
    ]
