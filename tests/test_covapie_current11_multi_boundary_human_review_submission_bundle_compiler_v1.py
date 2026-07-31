from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import inspect
import io
import json
import subprocess
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_current11_multi_boundary_human_review_sidecar_v1 as sidecar,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_submission_bundle_compiler_v1
    as compiler,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as ingestion_interface,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
    "covapie-envs/diffsbdd-legacy-test-v1/bin/python3.10"
)
SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(6, 11)
)
REVISION_ATOMS = [
    "C16", "C21", "C38", "N18", "N19",
    "N40", "N41", "O17", "O22", "O39",
]
REVISION_BOUNDARIES = [
    {
        "warhead_attachment_atom_id": "C16",
        "nonwarhead_boundary_atom_id": "C11",
        "boundary_bond_order": "single",
        "boundary_bond_id": "C11|C16|single",
    },
    {
        "warhead_attachment_atom_id": "C38",
        "nonwarhead_boundary_atom_id": "C33",
        "boundary_bond_order": "single",
        "boundary_bond_id": "C33|C38|single",
    },
]
COMPILED_FIELDS = (
    "multi_boundary_review_record_version",
    "item_index_0based",
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "source_evidence_record_sha256",
    "source_v1_quarantine_authority_record_sha256",
    "source_review_record_sha256",
    "proposed_warhead_atom_ids",
    "proposed_boundary_records",
    "scope_caveat",
    "review_decision",
    "reviewed_warhead_atom_ids",
    "reviewed_boundary_records",
    "reviewer_id",
    "review_rationale",
    "review_notes",
    "reviewer_provenance_attested",
    "reviewer_provenance_attestor_id",
    "submission_source_label",
    "review_completed",
    "multi_boundary_review_record_sha256",
)
BUNDLE_FIELDS = (
    "multi_boundary_submission_bundle_version",
    "source_submission_bundle_sha256",
    "source_ingestion_execution_bundle_filesystem_sha256",
    "source_ingestion_execution_bundle_sha256",
    "source_verified_multi_boundary_evidence_csv_sha256",
    "source_multi_boundary_review_worklist_csv_sha256",
    "source_readme_sha256",
    "submission_batch_id",
    "submission_items",
    "multi_boundary_submission_bundle_sha256",
)


def _load_predecessor_checker():
    path = (
        REPO_ROOT
        / "scripts/check_prepare_covapie_current11_multi_boundary_"
        "human_review_sidecar_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "multi_boundary_compiler_predecessor_checker_for_tests", path,
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _csv_rows(
    payload: bytes,
) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with io.StringIO(payload.decode("utf-8"), newline="") as stream:
        reader = csv.DictReader(stream)
        return tuple(reader.fieldnames or ()), list(reader)


def _csv_bytes(
    fields: tuple[str, ...],
    rows: list[dict[str, str]],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=fields,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _json_cell(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    )


def _canonical_sha(record: dict[str, object], excluded: str) -> str:
    return hashlib.sha256(json.dumps(
        {key: value for key, value in record.items() if key != excluded},
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


@pytest.fixture(scope="session")
def synthetic_sources() -> tuple[bytes, bytes]:
    predecessor = _load_predecessor_checker()
    return predecessor._synthetic_sources(REPO_ROOT)


@pytest.fixture
def completed_workspace(
    synthetic_sources: tuple[bytes, bytes],
) -> dict[str, bytes]:
    submission, execution = synthetic_sources
    workspace = (
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1(
            source_submission_bundle=submission,
            source_ingestion_execution_bundle=execution,
            repo_root=REPO_ROOT,
        )
    )
    fields, rows = _csv_rows(
        workspace["multi_boundary_review_worklist.csv"]
    )
    for position, row in enumerate(rows):
        row.update({
            "review_decision":
                "revise_two_boundary_atom_set_and_boundaries"
                if position == 2
                else "accept_verified_two_boundary_proposal",
            "reviewed_warhead_atom_ids_json":
                _json_cell(REVISION_ATOMS)
                if position == 2
                else row["proposed_warhead_atom_ids_json"],
            "reviewed_boundary_records_json":
                _json_cell(REVISION_BOUNDARIES)
                if position == 2
                else row["proposed_boundary_records_json"],
            "reviewer_id": "fmx",
            "review_rationale":
                f"Synthetic completed human rationale {position}.",
            "review_notes":
                f"Synthetic completed human notes {position}.",
            "reviewer_provenance_attested": "true",
            "reviewer_provenance_attestor_id": "fmx",
            "submission_source_label":
                "multi-boundary-compiler-synthetic-review",
            "review_completed": "true",
            "multi_boundary_review_record_sha256": "",
        })
    return {
        "evidence": workspace["verified_multi_boundary_evidence.csv"],
        "worklist": _csv_bytes(fields, rows),
        "readme": workspace["README.md"],
        "submission": submission,
        "execution": execution,
    }


def _compile(workspace: dict[str, bytes]) -> bytes:
    return (
        compiler
        .compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1(
            verified_multi_boundary_evidence_csv=workspace["evidence"],
            multi_boundary_review_worklist_csv=workspace["worklist"],
            readme_md=workspace["readme"],
            source_submission_bundle=workspace["submission"],
            source_ingestion_execution_bundle=workspace["execution"],
            repo_root=REPO_ROOT,
            submission_batch_id=
                "covapie_current11_multi_boundary_synthetic_batch_v1",
        )
    )


def _mutate_worklist(
    workspace: dict[str, bytes],
    mutation,
) -> dict[str, bytes]:
    changed = dict(workspace)
    fields, rows = _csv_rows(changed["worklist"])
    mutation(rows)
    changed["worklist"] = _csv_bytes(fields, rows)
    return changed


def test_public_api_signature_all_and_exact_input_types(
    completed_workspace: dict[str, bytes],
) -> None:
    function = (
        compiler
        .compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1
    )
    assert compiler.__all__ == (
        "compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1",
    )
    signature = inspect.signature(function)
    assert tuple(signature.parameters) == (
        "verified_multi_boundary_evidence_csv",
        "multi_boundary_review_worklist_csv",
        "readme_md",
        "source_submission_bundle",
        "source_ingestion_execution_bundle",
        "repo_root",
        "submission_batch_id",
    )
    assert all(
        value.kind is inspect.Parameter.KEYWORD_ONLY
        for value in signature.parameters.values()
    )
    assert signature.return_annotation in {bytes, "bytes"}

    arguments: dict[str, object] = {
        "verified_multi_boundary_evidence_csv":
            completed_workspace["evidence"],
        "multi_boundary_review_worklist_csv":
            completed_workspace["worklist"],
        "readme_md": completed_workspace["readme"],
        "source_submission_bundle": completed_workspace["submission"],
        "source_ingestion_execution_bundle":
            completed_workspace["execution"],
        "repo_root": REPO_ROOT,
        "submission_batch_id": "meaningful-batch",
    }
    for field, invalid in (
        ("verified_multi_boundary_evidence_csv", bytearray()),
        ("multi_boundary_review_worklist_csv", bytearray()),
        ("readme_md", ""),
        ("source_submission_bundle", memoryview(b"")),
        ("source_ingestion_execution_bundle", bytearray()),
        ("repo_root", str(REPO_ROOT)),
        ("submission_batch_id", ""),
        ("submission_batch_id", " padded "),
    ):
        trial = dict(arguments)
        trial[field] = invalid
        with pytest.raises(ValueError):
            function(**trial)


def test_import_is_silent() -> None:
    result = subprocess.run(
        [
            str(PYTHON), "-B", "-c",
            "import covalent_ext."
            "covapie_current11_multi_boundary_human_review_"
            "submission_bundle_compiler_v1",
        ],
        cwd=REPO_ROOT,
        env={
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(REPO_ROOT / "src"),
        },
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""


def test_public_predecessor_calls_no_evaluator_no_writes_and_inputs_unchanged(
    completed_workspace: dict[str, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"sidecar": 0, "context": 0, "evaluator": 0}
    original_sidecar = (
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1
    )
    original_context = (
        ingestion_interface
        .build_current11_warhead_boundary_review_ingestion_authority_context_v1
    )

    def counted_sidecar(**arguments):
        calls["sidecar"] += 1
        return original_sidecar(**arguments)

    def counted_context(repo_root: Path):
        calls["context"] += 1
        return original_context(repo_root)

    def forbidden_evaluator(*_arguments, **_keyword_arguments):
        calls["evaluator"] += 1
        raise AssertionError("ingestion evaluator called")

    def forbidden_write(*_arguments, **_keyword_arguments):
        raise AssertionError("compiler attempted a filesystem write")

    monkeypatch.setattr(
        sidecar,
        "build_covapie_current11_multi_boundary_human_review_sidecar_v1",
        counted_sidecar,
    )
    monkeypatch.setattr(
        ingestion_interface,
        "build_current11_warhead_boundary_review_ingestion_authority_context_v1",
        counted_context,
    )
    monkeypatch.setattr(
        ingestion_interface,
        "evaluate_current11_warhead_boundary_review_ingestion_v1",
        forbidden_evaluator,
    )
    for name in ("write_bytes", "write_text", "touch", "mkdir"):
        monkeypatch.setattr(Path, name, forbidden_write)
    snapshots = {
        key: bytes(value) for key, value in completed_workspace.items()
    }
    _compile(completed_workspace)
    assert calls == {"sidecar": 1, "context": 2, "evaluator": 0}
    assert completed_workspace == snapshots


def test_success_exact_contract_digests_profile_and_determinism(
    completed_workspace: dict[str, bytes],
) -> None:
    first = _compile(completed_workspace)
    second = _compile(completed_workspace)
    assert first == second
    assert not first.startswith(b"\xef\xbb\xbf")
    assert b"\x00" not in first
    assert not first.endswith(b"\n")
    assert len(first) < 1024 * 1024
    bundle = json.loads(first)
    assert tuple(bundle) == BUNDLE_FIELDS
    assert bundle["multi_boundary_submission_bundle_version"] == (
        "covapie_current11_multi_boundary_human_review_submission_bundle_v1"
    )
    assert bundle["multi_boundary_submission_bundle_sha256"] == (
        _canonical_sha(
            bundle, "multi_boundary_submission_bundle_sha256",
        )
    )
    assert len(bundle["submission_items"]) == 5
    assert [
        record["review_decision"]
        for record in bundle["submission_items"]
    ] == [
        "accept_verified_two_boundary_proposal",
        "accept_verified_two_boundary_proposal",
        "revise_two_boundary_atom_set_and_boundaries",
        "accept_verified_two_boundary_proposal",
        "accept_verified_two_boundary_proposal",
    ]
    digests = set()
    for position, record in enumerate(bundle["submission_items"]):
        assert tuple(record) == COMPILED_FIELDS
        assert record["item_index_0based"] == position
        assert type(record["item_index_0based"]) is int
        assert type(record["proposed_warhead_atom_ids"]) is list
        assert type(record["proposed_boundary_records"]) is list
        assert type(record["reviewed_warhead_atom_ids"]) is list
        assert type(record["reviewed_boundary_records"]) is list
        assert record["reviewer_provenance_attested"] is True
        assert record["review_completed"] is True
        assert record["multi_boundary_review_record_sha256"] == (
            _canonical_sha(
                record, "multi_boundary_review_record_sha256",
            )
        )
        digests.add(record["multi_boundary_review_record_sha256"])
    assert len(digests) == 5
    revision = bundle["submission_items"][2]
    assert revision["reviewed_warhead_atom_ids"] == REVISION_ATOMS
    assert revision["reviewed_boundary_records"] == REVISION_BOUNDARIES


@pytest.mark.parametrize(
    "case",
    ("evidence_malformed", "evidence_mismatch", "readme_malformed",
     "readme_mismatch", "worklist_malformed"),
)
def test_malformed_or_nonreference_exact3_is_rejected(
    completed_workspace: dict[str, bytes],
    case: str,
) -> None:
    changed = dict(completed_workspace)
    if case == "evidence_malformed":
        changed["evidence"] = b"not,csv\n"
    elif case == "evidence_mismatch":
        changed["evidence"] = changed["evidence"].replace(
            b"1AU3", b"9ZZZ", 1,
        )
    elif case == "readme_malformed":
        changed["readme"] = b"\xef\xbb\xbf" + changed["readme"]
    elif case == "readme_mismatch":
        changed["readme"] += b"drift"
    else:
        changed["worklist"] = b"not,csv\n"
    with pytest.raises(ValueError):
        _compile(changed)


@pytest.mark.parametrize("source", ("evidence", "worklist"))
def test_malformed_quoted_csv_is_strictly_rejected_before_later_validation(
    completed_workspace: dict[str, bytes],
    monkeypatch: pytest.MonkeyPatch,
    source: str,
) -> None:
    changed = dict(completed_workspace)
    needle = b",1AU3," if source == "evidence" else b",fmx,"
    malformed = changed[source].replace(
        needle,
        b",\"" + needle[1:-1] + b"\"trailing,",
        1,
    )
    assert malformed != changed[source]
    changed[source] = malformed

    with io.StringIO(malformed.decode("utf-8"), newline="") as stream:
        tolerated = list(csv.DictReader(stream, strict=False))
    assert len(tolerated) == 5
    assert all(None not in row for row in tolerated)

    if source == "evidence":
        original = (
            sidecar
            .build_covapie_current11_multi_boundary_human_review_sidecar_v1
        )

        def malformed_reference(**arguments):
            outputs = dict(original(**arguments))
            outputs["verified_multi_boundary_evidence.csv"] = malformed
            return outputs

        monkeypatch.setattr(
            sidecar,
            "build_covapie_current11_multi_boundary_human_review_sidecar_v1",
            malformed_reference,
        )
    with pytest.raises(
        ValueError,
        match=f"MULTI_BOUNDARY_{source.upper()}_CSV_INVALID",
    ) as caught:
        _compile(changed)
    assert type(caught.value) is ValueError


@pytest.mark.parametrize(
    "case",
    ("frozen", "reordered", "duplicate", "missing"),
)
def test_worklist_frozen_lineage_order_and_exact5_are_enforced(
    completed_workspace: dict[str, bytes],
    case: str,
) -> None:
    def mutation(rows):
        if case == "frozen":
            rows[0]["pdb_id"] = "9ZZZ"
        elif case == "reordered":
            rows[0], rows[1] = rows[1], rows[0]
        elif case == "duplicate":
            rows[1] = dict(rows[0])
        else:
            rows.pop()

    with pytest.raises(ValueError):
        _compile(_mutate_worklist(completed_workspace, mutation))


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("review_completed", "false"),
        ("review_decision", "not_reviewed"),
        ("review_decision", "unknown_fourth_decision"),
        ("multi_boundary_review_record_sha256", "0" * 64),
        ("reviewer_id", ""),
        ("review_rationale", ""),
        ("review_notes", ""),
        ("reviewer_provenance_attested", "false"),
        ("reviewer_provenance_attestor_id", ""),
        ("submission_source_label", ""),
    ),
)
def test_incomplete_unknown_prefilled_or_missing_provenance_is_rejected(
    completed_workspace: dict[str, bytes],
    field: str,
    value: str,
) -> None:
    with pytest.raises(ValueError):
        _compile(_mutate_worklist(
            completed_workspace,
            lambda rows: rows[0].__setitem__(field, value),
        ))


@pytest.mark.parametrize("case", ("malformed", "unsorted", "duplicate"))
def test_reviewed_atom_json_canonical_set_contract_is_enforced(
    completed_workspace: dict[str, bytes],
    case: str,
) -> None:
    def mutation(rows):
        if case == "malformed":
            rows[0]["reviewed_warhead_atom_ids_json"] = "{"
        else:
            atoms = json.loads(rows[0]["reviewed_warhead_atom_ids_json"])
            if case == "unsorted":
                atoms[0], atoms[1] = atoms[1], atoms[0]
            else:
                atoms[-1] = atoms[0]
            rows[0]["reviewed_warhead_atom_ids_json"] = _json_cell(atoms)

    with pytest.raises(ValueError):
        _compile(_mutate_worklist(completed_workspace, mutation))


def test_lone_surrogate_reviewed_atom_fails_closed_without_writes_or_mutation(
    completed_workspace: dict[str, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    changed = _mutate_worklist(
        completed_workspace,
        lambda rows: rows[0].__setitem__(
            "reviewed_warhead_atom_ids_json", _json_cell(["\ud800"]),
        ),
    )
    assert b"\\ud800" in changed["worklist"]
    changed["worklist"].decode("utf-8")
    snapshots = {key: bytes(value) for key, value in changed.items()}
    writes = []

    def forbidden_write(*_arguments, **_keyword_arguments):
        writes.append(True)
        raise AssertionError("compiler attempted a filesystem write")

    for name in ("write_bytes", "write_text", "touch", "mkdir"):
        monkeypatch.setattr(Path, name, forbidden_write)
    with pytest.raises(
        ValueError,
        match="MULTI_BOUNDARY_UTF8_TOKEN_INVALID",
    ) as caught:
        _compile(changed)
    assert type(caught.value) is ValueError
    assert not isinstance(caught.value, UnicodeEncodeError)
    assert changed == snapshots
    assert writes == []


@pytest.mark.parametrize(
    "case",
    ("malformed", "count", "field_order", "canonical_id"),
)
def test_reviewed_boundary_json_exact_schema_and_canonical_id_are_enforced(
    completed_workspace: dict[str, bytes],
    case: str,
) -> None:
    def mutation(rows):
        if case == "malformed":
            rows[0]["reviewed_boundary_records_json"] = "{"
            return
        boundaries = json.loads(rows[0]["reviewed_boundary_records_json"])
        if case == "count":
            boundaries.pop()
        elif case == "field_order":
            first = boundaries[0]
            boundaries[0] = {
                "boundary_bond_id": first["boundary_bond_id"],
                "warhead_attachment_atom_id":
                    first["warhead_attachment_atom_id"],
                "nonwarhead_boundary_atom_id":
                    first["nonwarhead_boundary_atom_id"],
                "boundary_bond_order": first["boundary_bond_order"],
            }
        else:
            boundaries[0]["boundary_bond_id"] = "wrong"
        rows[0]["reviewed_boundary_records_json"] = _json_cell(boundaries)

    with pytest.raises(ValueError):
        _compile(_mutate_worklist(completed_workspace, mutation))


@pytest.mark.parametrize("token", ("boundary_bond_id", "endpoint"))
def test_lone_surrogate_boundary_token_fails_closed(
    completed_workspace: dict[str, bytes],
    token: str,
) -> None:
    def mutation(rows):
        boundaries = json.loads(rows[0]["reviewed_boundary_records_json"])
        if token == "boundary_bond_id":
            boundaries[0]["boundary_bond_id"] = "\ud800"
        else:
            boundaries[0]["warhead_attachment_atom_id"] = "\ud800"
            boundaries[0]["boundary_bond_id"] = "C16|X|single"
        rows[0]["reviewed_boundary_records_json"] = _json_cell(boundaries)

    changed = _mutate_worklist(completed_workspace, mutation)
    assert b"\\ud800" in changed["worklist"]
    changed["worklist"].decode("utf-8")
    with pytest.raises(
        ValueError,
        match="MULTI_BOUNDARY_UTF8_TOKEN_INVALID",
    ) as caught:
        _compile(changed)
    assert type(caught.value) is ValueError
    assert not isinstance(caught.value, UnicodeEncodeError)


def test_accept_compares_parsed_semantics_not_json_spacing(
    completed_workspace: dict[str, bytes],
) -> None:
    changed = _mutate_worklist(
        completed_workspace,
        lambda rows: rows[0].update({
            "reviewed_warhead_atom_ids_json": json.dumps(
                json.loads(rows[0]["proposed_warhead_atom_ids_json"]),
                indent=1,
            ),
            "reviewed_boundary_records_json": json.dumps(
                json.loads(rows[0]["proposed_boundary_records_json"]),
                indent=1,
            ),
        }),
    )
    _compile(changed)


def test_accept_mismatch_and_quarantine_nonempty_evidence_are_rejected(
    completed_workspace: dict[str, bytes],
) -> None:
    mismatch = _mutate_worklist(
        completed_workspace,
        lambda rows: rows[0].__setitem__(
            "reviewed_warhead_atom_ids_json",
            rows[1]["reviewed_warhead_atom_ids_json"],
        ),
    )
    with pytest.raises(ValueError):
        _compile(mismatch)

    quarantine = _mutate_worklist(
        completed_workspace,
        lambda rows: rows[0].__setitem__("review_decision", "quarantine"),
    )
    with pytest.raises(ValueError):
        _compile(quarantine)


def test_completed_quarantine_requires_and_accepts_empty_reviewed_evidence(
    completed_workspace: dict[str, bytes],
) -> None:
    changed = _mutate_worklist(
        completed_workspace,
        lambda rows: rows[0].update({
            "review_decision": "quarantine",
            "reviewed_warhead_atom_ids_json": "[]",
            "reviewed_boundary_records_json": "[]",
        }),
    )
    bundle = json.loads(_compile(changed))
    assert bundle["submission_items"][0]["review_decision"] == "quarantine"
    assert bundle["submission_items"][0]["reviewed_warhead_atom_ids"] == []
    assert bundle["submission_items"][0]["reviewed_boundary_records"] == []


def test_valid_000008_revision_is_graph_validated(
    completed_workspace: dict[str, bytes],
) -> None:
    record = json.loads(_compile(completed_workspace))["submission_items"][2]
    assert record["reviewed_warhead_atom_ids"] == REVISION_ATOMS
    assert record["reviewed_boundary_records"] == REVISION_BOUNDARIES


@pytest.mark.parametrize("missing_atom", ("O17", "O39"))
def test_000008_revision_missing_terminal_oxygen_is_rejected(
    completed_workspace: dict[str, bytes],
    missing_atom: str,
) -> None:
    atoms = [atom for atom in REVISION_ATOMS if atom != missing_atom]
    with pytest.raises(ValueError):
        _compile(_mutate_worklist(
            completed_workspace,
            lambda rows: rows[2].__setitem__(
                "reviewed_warhead_atom_ids_json", _json_cell(atoms),
            ),
        ))


@pytest.mark.parametrize("case", ("endpoint", "order"))
def test_revision_wrong_boundary_endpoint_or_order_is_rejected(
    completed_workspace: dict[str, bytes],
    case: str,
) -> None:
    boundaries = copy.deepcopy(REVISION_BOUNDARIES)
    if case == "endpoint":
        boundaries[0].update({
            "nonwarhead_boundary_atom_id": "C12",
            "boundary_bond_id": "C12|C16|single",
        })
    else:
        boundaries[0].update({
            "boundary_bond_order": "double",
            "boundary_bond_id": "C11|C16|double",
        })
    with pytest.raises(ValueError):
        _compile(_mutate_worklist(
            completed_workspace,
            lambda rows: rows[2].__setitem__(
                "reviewed_boundary_records_json", _json_cell(boundaries),
            ),
        ))


def test_disconnected_revision_is_rejected(
    completed_workspace: dict[str, bytes],
) -> None:
    atoms = sorted((*REVISION_ATOMS, "C1"), key=lambda value: value.encode())
    with pytest.raises(ValueError, match="DISCONNECTED"):
        _compile(_mutate_worklist(
            completed_workspace,
            lambda rows: rows[2].__setitem__(
                "reviewed_warhead_atom_ids_json", _json_cell(atoms),
            ),
        ))


def test_revision_missing_local_center_atom_is_rejected(
    completed_workspace: dict[str, bytes],
) -> None:
    atoms = [atom for atom in REVISION_ATOMS if atom != "N19"]
    with pytest.raises(ValueError):
        _compile(_mutate_worklist(
            completed_workspace,
            lambda rows: rows[2].__setitem__(
                "reviewed_warhead_atom_ids_json", _json_cell(atoms),
            ),
        ))


def test_revision_graph_derived_boundary_count_other_than_two_is_rejected(
    completed_workspace: dict[str, bytes],
) -> None:
    atoms = [atom for atom in REVISION_ATOMS if atom != "O39"]
    with pytest.raises(ValueError, match="GRAPH_BOUNDARY"):
        _compile(_mutate_worklist(
            completed_workspace,
            lambda rows: rows[2].__setitem__(
                "reviewed_warhead_atom_ids_json", _json_cell(atoms),
            ),
        ))
