from __future__ import annotations

import copy
import csv
import dataclasses
import hashlib
import importlib.util
import inspect
import io
import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_current11_multi_boundary_human_review_sidecar_v1 as sidecar,
)
from covalent_ext import (
    covapie_current11_real_human_review_ingestion_execution_bundle_v1
    as execution_builder,
)
from covalent_ext import (
    covapie_current11_real_human_review_submission_bundle_compiler_v1
    as compiler,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as ingestion_design,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as ingestion_interface,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_submission_adapter_v1
    as public_adapter,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
    "covapie-envs/diffsbdd-legacy-test-v1/bin/python3.10"
)
EXPECTED_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(6, 11)
)
EXPECTED_ATOMS = (
    ["C19", "C21", "C22", "C42", "N18", "N41", "O23"],
    ["C15", "C16", "C17", "C18", "N14", "N23", "O42"],
    ["C21", "N18", "N19", "N40", "N41", "O22"],
    [
        "C17", "C20", "C21", "C42", "CH'", "N19", "NJ'", "NK'",
        "O22", "OI'", "S18",
    ],
    [
        "C17", "C21", "CH'", "N19", "N20", "NJ'", "NK'", "O18",
        "O22", "OI'",
    ],
)
EXPECTED_BOUNDARY_IDS = (
    ("C16|N18|single", "C39|N41|single"),
    ("C13|N14|single", "C24|N23|single"),
    ("C16|N18|single", "C38|N40|single"),
    ("C11|C17|single", "CB'|CH'|single"),
    ("C11|C17|single", "CB'|CH'|single"),
)
BOUNDARY_FIELDS = (
    "warhead_attachment_atom_id",
    "nonwarhead_boundary_atom_id",
    "boundary_bond_order",
    "boundary_bond_id",
)


def _load_script(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


PREDECESSOR_PREPARER = _load_script(
    "sidecar_predecessor_workspace_preparer_for_tests",
    REPO_ROOT
    / "scripts/"
    "prepare_covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "human_review_workspace_v1.py",
)
CLI = _load_script(
    "sidecar_workspace_cli_for_tests",
    REPO_ROOT
    / "scripts/"
    "prepare_covapie_current11_multi_boundary_human_review_sidecar_v1.py",
)


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


def _synthetic_completed_submission() -> bytes:
    workspace = PREDECESSOR_PREPARER.build_workspace_payloads(REPO_ROOT)
    fields, rows = _csv_rows(workspace["review_worklist.csv"])
    _, options = _csv_rows(workspace["eligible_candidate_options.csv"])
    first_option_by_sample: dict[str, dict[str, str]] = {}
    for option in options:
        first_option_by_sample.setdefault(
            option["sample_index_row_id"], option,
        )
    seeds = {
        seed.sample_index_row_id: seed
        for seed in sidecar._FROZEN_PROPOSAL_SEEDS
    }
    for position, row in enumerate(rows):
        sample = row["sample_index_row_id"]
        notes = f"Synthetic preserved review note {position}."
        if sample in seeds:
            seed = seeds[sample]
            notes = (
                "Exact audited proposed atom IDs "
                + json.dumps(
                    list(seed.proposed_warhead_atom_ids),
                    ensure_ascii=True,
                    separators=(",", ":"),
                )
                + "; exact canonical boundary IDs "
                + ", ".join(
                    boundary.boundary_bond_id
                    for boundary in seed.boundaries
                )
                + "."
            )
        row.update({
            "reviewer_id": "unit-test-human-reviewer",
            "review_rationale":
                f"Synthetic human rationale for item {position}.",
            "review_notes": notes,
            "reviewer_provenance_attested": "true",
            "reviewer_provenance_attestor_id": "unit-test-human-attestor",
            "submission_source_label": "sidecar-synthetic-unit-test",
            "review_completed": "true",
        })
        if 5 <= position <= 9:
            row.update({
                "review_decision": "quarantine",
                "selected_bridge_candidate_index_0based": "",
                "selected_bridge_candidate_record_sha256": "",
                "reviewed_warhead_atom_ids_json": "[]",
                "reviewed_warhead_attachment_atom_id": "",
                "reviewed_nonwarhead_boundary_atom_id": "",
                "reviewed_attachment_boundary_bond_order": "",
                "reviewed_boundary_bond_id": "",
            })
        else:
            option = first_option_by_sample[sample]
            row.update({
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
            })
    package_root = REPO_ROOT / PREDECESSOR_PREPARER.PACKAGE_ROOT
    return compiler.compile_covapie_current11_real_human_review_submission_bundle_v1(
        review_worklist_csv=_csv_bytes(fields, rows),
        eligible_candidate_options_csv=
            workspace["eligible_candidate_options.csv"],
        package_index_csv=
            (package_root / PREDECESSOR_PREPARER.INDEX_FILE).read_bytes(),
        package_candidate_options_csv=
            (package_root / PREDECESSOR_PREPARER.OPTIONS_FILE).read_bytes(),
        review_record_templates_csv=
            (package_root / PREDECESSOR_PREPARER.TEMPLATES_FILE).read_bytes(),
        submission_batch_id="covapie_current11_sidecar_synthetic_batch_v1",
    )


@pytest.fixture(scope="session")
def synthetic_sources() -> tuple[bytes, bytes]:
    submission = _synthetic_completed_submission()
    execution = execution_builder.build_covapie_current11_real_human_review_ingestion_execution_bundle_v1(
        source_submission_bundle=submission,
        repo_root=REPO_ROOT,
    )
    return submission, execution


def _build(sources: tuple[bytes, bytes]) -> dict[str, bytes]:
    submission, execution = sources
    return sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1(
        source_submission_bundle=submission,
        source_ingestion_execution_bundle=execution,
        repo_root=REPO_ROOT,
    )


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _rehash_execution_bundle(bundle: dict[str, object]) -> bytes:
    interface_response = {
        "interface_response_version":
            bundle["ingestion_interface_response_version"],
        "authority_context_record_sha256":
            bundle["authority_context_record_sha256"],
        "batch_passed": bundle["batch_passed"],
        "ingestion_result_records":
            tuple(bundle["ingestion_result_records"]),
        "new_authority_records": tuple(bundle["new_authority_records"]),
        "interface_response_sha256": "",
    }
    interface_response["interface_response_sha256"] = (
        ingestion_interface.interface_response_sha256(interface_response)
    )
    bundle["ingestion_interface_response_sha256"] = (
        interface_response["interface_response_sha256"]
    )
    bundle["ingestion_execution_bundle_sha256"] = hashlib.sha256(
        _canonical_json_bytes({
            field: bundle[field]
            for field in sidecar._EXECUTION_FIELDS
            if field != "ingestion_execution_bundle_sha256"
        })
    ).hexdigest()
    return json.dumps(
        bundle,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _mutated_execution(
    source: bytes,
    mutation,
) -> bytes:
    bundle = json.loads(source)
    mutation(bundle)
    return _rehash_execution_bundle(bundle)


def _rehash_authority_result(
    bundle: dict[str, object],
    position: int,
) -> None:
    authority = bundle["new_authority_records"][position]
    result = bundle["ingestion_result_records"][position]
    authority["authority_record_sha256"] = (
        ingestion_design.authority_record_sha256(authority)
    )
    result["authority_record_sha256"] = authority["authority_record_sha256"]
    result["authority_disposition"] = authority["authority_disposition"]
    result["ingestion_result_sha256"] = (
        ingestion_design.ingestion_result_sha256(result)
    )


def test_public_signature_and_all_contract() -> None:
    function = (
        sidecar
        .build_covapie_current11_multi_boundary_human_review_sidecar_v1
    )
    assert sidecar.__all__ == (
        "build_covapie_current11_multi_boundary_human_review_sidecar_v1",
    )
    signature = inspect.signature(function)
    assert tuple(signature.parameters) == (
        "source_submission_bundle",
        "source_ingestion_execution_bundle",
        "repo_root",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert signature.return_annotation in {
        dict[str, bytes], "dict[str, bytes]",
    }


@pytest.mark.parametrize(
    ("submission", "execution", "root"),
    (
        (bytearray(), b"{}", REPO_ROOT),
        (b"{}", bytearray(), REPO_ROOT),
        ("{}", b"{}", REPO_ROOT),
        (b"{}", "{}", REPO_ROOT),
        (b"{}", b"{}", str(REPO_ROOT)),
        (b"{}", b"{}", None),
    ),
)
def test_exact_input_types_are_required(
    submission: object,
    execution: object,
    root: object,
) -> None:
    with pytest.raises(ValueError):
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1(
            source_submission_bundle=submission,
            source_ingestion_execution_bundle=execution,
            repo_root=root,
        )


def test_public_predecessor_calls_are_exact_and_evaluator_is_not_called(
    synthetic_sources: tuple[bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"adapter": 0, "context": 0, "evaluator": 0}
    original_adapter = (
        public_adapter
        .adapt_current11_warhead_boundary_review_submission_bundle_v1
    )
    original_context = (
        ingestion_interface
        .build_current11_warhead_boundary_review_ingestion_authority_context_v1
    )

    def adapter(*, source_payload: bytes):
        calls["adapter"] += 1
        return original_adapter(source_payload=source_payload)

    def context(repo_root: Path):
        calls["context"] += 1
        return original_context(repo_root)

    def evaluator(*_arguments, **_keyword_arguments):
        calls["evaluator"] += 1
        raise AssertionError("ingestion evaluator must not be called")

    monkeypatch.setattr(
        public_adapter,
        "adapt_current11_warhead_boundary_review_submission_bundle_v1",
        adapter,
    )
    monkeypatch.setattr(
        ingestion_interface,
        "build_current11_warhead_boundary_review_ingestion_authority_context_v1",
        context,
    )
    monkeypatch.setattr(
        ingestion_interface,
        "evaluate_current11_warhead_boundary_review_ingestion_v1",
        evaluator,
    )
    _build(synthetic_sources)
    assert calls == {"adapter": 1, "context": 1, "evaluator": 0}


@pytest.mark.parametrize(
    "which",
    ("submission", "execution"),
)
def test_malformed_source_is_rejected(
    synthetic_sources: tuple[bytes, bytes],
    which: str,
) -> None:
    submission, execution = synthetic_sources
    if which == "submission":
        submission = b"{}"
    else:
        execution = b"{}"
    with pytest.raises(ValueError):
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1(
            source_submission_bundle=submission,
            source_ingestion_execution_bundle=execution,
            repo_root=REPO_ROOT,
        )


def test_submission_execution_source_sha_mismatch_is_rejected(
    synthetic_sources: tuple[bytes, bytes],
) -> None:
    submission, execution = synthetic_sources
    mutated = _mutated_execution(
        execution,
        lambda bundle: bundle.__setitem__(
            "source_submission_bundle_sha256", "0" * 64,
        ),
    )
    with pytest.raises(ValueError, match="EXECUTION_LINEAGE"):
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1(
            source_submission_bundle=submission,
            source_ingestion_execution_bundle=mutated,
            repo_root=REPO_ROOT,
        )


@pytest.mark.parametrize("case", ("missing", "non_quarantine"))
def test_target_authority_must_exist_and_remain_quarantined(
    synthetic_sources: tuple[bytes, bytes],
    case: str,
) -> None:
    submission, execution = synthetic_sources

    def mutation(bundle):
        if case == "missing":
            del bundle["new_authority_records"][5]
        else:
            authority = bundle["new_authority_records"][5]
            authority["authority_status"] = "active"
            _rehash_authority_result(bundle, 5)

    mutated = _mutated_execution(execution, mutation)
    with pytest.raises(ValueError):
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1(
            source_submission_bundle=submission,
            source_ingestion_execution_bundle=mutated,
            repo_root=REPO_ROOT,
        )


@pytest.mark.parametrize("lineage", ("review", "envelope"))
def test_authority_review_envelope_lineage_mismatch_is_rejected(
    synthetic_sources: tuple[bytes, bytes],
    lineage: str,
) -> None:
    submission, execution = synthetic_sources

    def mutation(bundle):
        authority = bundle["new_authority_records"][5]
        authority[
            "source_review_record_sha256"
            if lineage == "review"
            else "source_ingestion_envelope_sha256"
        ] = "0" * 64
        _rehash_authority_result(bundle, 5)

    mutated = _mutated_execution(execution, mutation)
    with pytest.raises(ValueError):
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1(
            source_submission_bundle=submission,
            source_ingestion_execution_bundle=mutated,
            repo_root=REPO_ROOT,
        )


@pytest.mark.parametrize("lineage", ("proposal", "assignment"))
def test_proposal_assignment_lineage_mismatch_is_rejected(
    synthetic_sources: tuple[bytes, bytes],
    lineage: str,
) -> None:
    submission, execution = synthetic_sources

    def mutation(bundle):
        authority = bundle["new_authority_records"][5]
        authority[
            "source_proposal_record_sha256"
            if lineage == "proposal"
            else "source_assignment_record_sha256"
        ] = "0" * 64
        _rehash_authority_result(bundle, 5)

    mutated = _mutated_execution(execution, mutation)
    with pytest.raises(ValueError):
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1(
            source_submission_bundle=submission,
            source_ingestion_execution_bundle=mutated,
            repo_root=REPO_ROOT,
        )


def _replace_first_seed(**changes):
    first = dataclasses.replace(sidecar._FROZEN_PROPOSAL_SEEDS[0], **changes)
    return (first, *sidecar._FROZEN_PROPOSAL_SEEDS[1:])


@pytest.mark.parametrize(
    ("case", "seeds"),
    (
        (
            "parent_atom_missing",
            _replace_first_seed(
                proposed_warhead_atom_ids=(
                    "C21", "C22", "C42", "N18", "N41", "O23", "ZZ",
                ),
            ),
        ),
        (
            "disconnected",
            _replace_first_seed(
                proposed_warhead_atom_ids=(
                    "C19", "C21", "C22", "C42", "N41", "O23", "O8",
                ),
            ),
        ),
        (
            "local_center_missing",
            _replace_first_seed(
                proposed_warhead_atom_ids=(
                    "C19", "C21", "C42", "N18", "N41", "O23",
                ),
            ),
        ),
        (
            "boundary_count_not_two",
            _replace_first_seed(
                proposed_warhead_atom_ids=(
                    "C16", "C19", "C21", "C22", "C42", "N18", "N41",
                    "O23",
                ),
            ),
        ),
    ),
)
def test_graph_atom_and_boundary_count_failures_are_closed(
    synthetic_sources: tuple[bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    seeds: tuple[object, ...],
) -> None:
    monkeypatch.setattr(sidecar, "_FROZEN_PROPOSAL_SEEDS", seeds)
    with pytest.raises(ValueError):
        _build(synthetic_sources)


@pytest.mark.parametrize("case", ("id", "order", "endpoint"))
def test_boundary_id_order_and_endpoint_mismatch_is_rejected(
    synthetic_sources: tuple[bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    first = sidecar._FROZEN_PROPOSAL_SEEDS[0]
    boundaries = list(first.boundaries)
    if case == "id":
        boundaries[0] = dataclasses.replace(
            boundaries[0], boundary_bond_id="C16|N18|double",
        )
    elif case == "order":
        boundaries.reverse()
    else:
        boundaries[0] = dataclasses.replace(
            boundaries[0], nonwarhead_boundary_atom_id="C15",
        )
    seeds = _replace_first_seed(boundaries=tuple(boundaries))
    monkeypatch.setattr(sidecar, "_FROZEN_PROPOSAL_SEEDS", seeds)
    with pytest.raises(ValueError):
        _build(synthetic_sources)


def test_exact5_outputs_frozen_values_fields_and_human_blanks(
    synthetic_sources: tuple[bytes, bytes],
) -> None:
    outputs = _build(synthetic_sources)
    assert type(outputs) is dict
    assert tuple(outputs) == (
        "verified_multi_boundary_evidence.csv",
        "multi_boundary_review_worklist.csv",
        "README.md",
    )
    evidence_fields, evidence = _csv_rows(
        outputs["verified_multi_boundary_evidence.csv"]
    )
    worklist_fields, worklist = _csv_rows(
        outputs["multi_boundary_review_worklist.csv"]
    )
    assert evidence_fields == sidecar._EVIDENCE_FIELDS
    assert worklist_fields == sidecar._WORKLIST_FIELDS
    assert len(evidence) == len(worklist) == 5
    assert tuple(row["sample_index_row_id"] for row in evidence) == (
        EXPECTED_SAMPLES
    )
    for position, (evidence_row, worklist_row) in enumerate(
        zip(evidence, worklist)
    ):
        atoms = json.loads(evidence_row["proposed_warhead_atom_ids_json"])
        boundaries = json.loads(
            evidence_row["proposed_boundary_records_json"]
        )
        derived = json.loads(
            evidence_row["graph_derived_boundary_records_json"]
        )
        assert atoms == EXPECTED_ATOMS[position]
        assert tuple(
            boundary["boundary_bond_id"] for boundary in boundaries
        ) == EXPECTED_BOUNDARY_IDS[position]
        assert boundaries == derived
        assert all(tuple(boundary) == BOUNDARY_FIELDS for boundary in boundaries)
        assert evidence_row["graph_derived_boundary_count"] == "2"
        assert all(evidence_row[field] == "true" for field in (
            "warhead_subgraph_connected",
            "contains_local_reaction_center",
            "contains_required_leaving_groups",
            "notes_match_parent_graph",
            "exact_two_boundaries_verified",
        ))
        assert worklist_row["proposed_warhead_atom_ids_json"] == (
            evidence_row["proposed_warhead_atom_ids_json"]
        )
        assert worklist_row["proposed_boundary_records_json"] == (
            evidence_row["proposed_boundary_records_json"]
        )
        assert worklist_row["review_decision"] == "not_reviewed"
        assert worklist_row["reviewed_warhead_atom_ids_json"] == "[]"
        assert worklist_row["reviewed_boundary_records_json"] == "[]"
        assert worklist_row["reviewer_id"] == ""
        assert worklist_row["review_rationale"] == ""
        assert worklist_row["review_notes"] == ""
        assert worklist_row["reviewer_provenance_attested"] == "false"
        assert worklist_row["reviewer_provenance_attestor_id"] == ""
        assert worklist_row["submission_source_label"] == ""
        assert worklist_row["review_completed"] == "false"
        assert worklist_row["multi_boundary_review_record_sha256"] == ""
    assert all(
        row["scope_caveat"] == ""
        for row in evidence[:3]
    )
    assert all(
        row["scope_caveat"]
        == "final multi-boundary gold core requires independent human review"
        for row in evidence[3:]
    )


def test_evidence_hashes_are_valid_and_unique(
    synthetic_sources: tuple[bytes, bytes],
) -> None:
    _, rows = _csv_rows(
        _build(synthetic_sources)["verified_multi_boundary_evidence.csv"]
    )
    observed = []
    for row in rows:
        expected = hashlib.sha256(_canonical_json_bytes({
            field: row[field]
            for field in sidecar._EVIDENCE_FIELDS
            if field != "evidence_record_sha256"
        })).hexdigest()
        assert row["evidence_record_sha256"] == expected
        observed.append(expected)
    assert len(set(observed)) == 5


def test_builder_is_deterministic_preserves_inputs_and_writes_no_files(
    synthetic_sources: tuple[bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    submission, execution = synthetic_sources
    snapshots = (bytes(submission), bytes(execution))
    first = _build(synthetic_sources)

    def forbidden(*_arguments, **_keyword_arguments):
        raise AssertionError("production builder attempted a file write")

    for method in ("write_bytes", "write_text", "touch", "mkdir"):
        monkeypatch.setattr(Path, method, forbidden)
    second = _build(synthetic_sources)
    assert first == second
    assert (submission, execution) == snapshots


def test_readme_states_decisions_compatibility_and_training_boundaries(
    synthetic_sources: tuple[bytes, bytes],
) -> None:
    readme = _build(synthetic_sources)["README.md"].decode("utf-8")
    allowed_decisions = (
        "accept_verified_two_boundary_proposal",
        "revise_two_boundary_atom_set_and_boundaries",
        "quarantine",
    )
    expected_decision_block = (
        "The only allowed completed review decisions are:\n\n"
        "- `accept_verified_two_boundary_proposal`\n"
        "- `revise_two_boundary_atom_set_and_boundaries`\n"
        "- `quarantine`\n\n"
        "`not_reviewed` means the review is incomplete and is not a "
        "completed decision."
    )
    assert expected_decision_block in readme
    for decision in allowed_decisions:
        assert readme.count(decision) >= 1
    for text in (
        "exactly five samples",
        "not a human decision",
        "do not edit that file",
        "must not be edited",
        "Proposed fields are not automatically copied into reviewed fields.",
        "`not_reviewed` means the review is incomplete",
        "exactly two reviewed boundary records",
        "000009 and 000010",
        "V1 quarantine authority remains valid",
        "does not create authority",
        "not been implemented",
        "not training input",
        "scaffold_only",
        "feature-semantics audit",
        "Step12D remains only a smoke legality check",
    ):
        assert text in readme


def test_cli_rejects_repo_internal_and_existing_output(
    tmp_path: Path,
    synthetic_sources: tuple[bytes, bytes],
) -> None:
    submission, execution = synthetic_sources
    submission_file = tmp_path / "submission.json"
    execution_file = tmp_path / "execution.json"
    submission_file.write_bytes(submission)
    execution_file.write_bytes(execution)
    with pytest.raises(ValueError, match="outside the Git repository"):
        CLI.prepare_sidecar_workspace(
            repo_root=REPO_ROOT,
            submission_file=submission_file,
            execution_file=execution_file,
            output_dir=REPO_ROOT / "forbidden-sidecar-output",
        )
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        CLI.prepare_sidecar_workspace(
            repo_root=REPO_ROOT,
            submission_file=submission_file,
            execution_file=execution_file,
            output_dir=existing,
        )


@pytest.mark.parametrize("source_name", ("submission", "execution"))
def test_cli_rejects_source_symlink(
    tmp_path: Path,
    synthetic_sources: tuple[bytes, bytes],
    source_name: str,
) -> None:
    submission, execution = synthetic_sources
    submission_real = tmp_path / "submission-real.json"
    execution_real = tmp_path / "execution-real.json"
    submission_real.write_bytes(submission)
    execution_real.write_bytes(execution)
    link = tmp_path / f"{source_name}-link.json"
    link.symlink_to(
        submission_real if source_name == "submission" else execution_real
    )
    with pytest.raises(ValueError, match="regular file"):
        CLI.prepare_sidecar_workspace(
            repo_root=REPO_ROOT,
            submission_file=
                link if source_name == "submission" else submission_real,
            execution_file=
                link if source_name == "execution" else execution_real,
            output_dir=tmp_path / "workspace",
        )


def test_cli_success_creates_only_exact3_0644_and_exact_stdout(
    tmp_path: Path,
    synthetic_sources: tuple[bytes, bytes],
    capsys: pytest.CaptureFixture[str],
) -> None:
    submission, execution = synthetic_sources
    submission_file = tmp_path / "submission.json"
    execution_file = tmp_path / "execution.json"
    submission_file.write_bytes(submission)
    execution_file.write_bytes(execution)
    source_snapshots = (
        submission_file.read_bytes(),
        execution_file.read_bytes(),
    )
    output = tmp_path / "sidecar"
    assert CLI.main((
        "--repo-root", str(REPO_ROOT),
        "--submission-file", str(submission_file),
        "--execution-file", str(execution_file),
        "--output-dir", str(output),
    )) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert tuple(
        line.split("=", 1)[0] for line in captured.out.splitlines()
    ) == (
        "output_dir",
        "source_submission_bundle_sha256",
        "source_execution_bundle_filesystem_sha256",
        "evidence_count",
        "worklist_count",
        "exact_two_boundary_verified_count",
        "pending_human_review_count",
    )
    assert tuple(sorted(path.name for path in output.iterdir())) == tuple(
        sorted((
            "verified_multi_boundary_evidence.csv",
            "multi_boundary_review_worklist.csv",
            "README.md",
        ))
    )
    assert all(
        stat.S_IMODE(path.stat().st_mode) == 0o644
        for path in output.iterdir()
    )
    assert (
        submission_file.read_bytes(),
        execution_file.read_bytes(),
    ) == source_snapshots


def test_cli_failure_leaves_no_workspace_or_temporary_residue(
    tmp_path: Path,
    synthetic_sources: tuple[bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    submission, execution = synthetic_sources
    submission_file = tmp_path / "submission.json"
    execution_file = tmp_path / "execution.json"
    submission_file.write_bytes(submission)
    execution_file.write_bytes(execution)
    output = tmp_path / "sidecar"

    def failed_link(*_arguments, **_keyword_arguments):
        raise OSError("synthetic publication failure")

    monkeypatch.setattr(os, "link", failed_link)
    with pytest.raises(OSError, match="synthetic publication failure"):
        CLI.prepare_sidecar_workspace(
            repo_root=REPO_ROOT,
            submission_file=submission_file,
            execution_file=execution_file,
            output_dir=output,
        )
    assert not output.exists()
    assert not list(tmp_path.glob(".sidecar.tmp-*"))


def test_cli_partial_publication_failure_cleans_owned_link_and_directories(
    tmp_path: Path,
    synthetic_sources: tuple[bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    submission, execution = synthetic_sources
    submission_file = tmp_path / "submission.json"
    execution_file = tmp_path / "execution.json"
    submission_file.write_bytes(submission)
    execution_file.write_bytes(execution)
    source_snapshots = (
        submission_file.read_bytes(),
        execution_file.read_bytes(),
    )
    output = tmp_path / "sidecar"
    real_link = os.link
    link_calls = 0

    def first_link_then_fail(source, target):
        nonlocal link_calls
        link_calls += 1
        if link_calls == 2:
            raise OSError("synthetic second-link publication failure")
        return real_link(source, target)

    monkeypatch.setattr(os, "link", first_link_then_fail)
    with pytest.raises(
        OSError, match="synthetic second-link publication failure",
    ):
        CLI.prepare_sidecar_workspace(
            repo_root=REPO_ROOT,
            submission_file=submission_file,
            execution_file=execution_file,
            output_dir=output,
        )
    assert link_calls == 2
    assert not output.exists()
    assert not list(tmp_path.glob(".sidecar.tmp-*"))
    assert (
        submission_file.read_bytes(),
        execution_file.read_bytes(),
    ) == source_snapshots


def test_cli_post_publication_mode_validation_failure_cleans_exact3(
    tmp_path: Path,
    synthetic_sources: tuple[bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    submission, execution = synthetic_sources
    submission_file = tmp_path / "submission.json"
    execution_file = tmp_path / "execution.json"
    submission_file.write_bytes(submission)
    execution_file.write_bytes(execution)
    output = tmp_path / "sidecar"
    real_link = os.link
    link_calls = 0

    def counted_link(source, target):
        nonlocal link_calls
        link_calls += 1
        return real_link(source, target)

    monkeypatch.setattr(os, "link", counted_link)
    monkeypatch.setattr(CLI.stat, "S_IMODE", lambda _mode: 0o600)
    with pytest.raises(ValueError, match="published workspace invariant"):
        CLI.prepare_sidecar_workspace(
            repo_root=REPO_ROOT,
            submission_file=submission_file,
            execution_file=execution_file,
            output_dir=output,
        )
    assert link_calls == 3
    assert not output.exists()
    assert not list(tmp_path.glob(".sidecar.tmp-*"))


def test_cli_publication_cleanup_failure_is_surfaced_and_test_cleans_residue(
    tmp_path: Path,
    synthetic_sources: tuple[bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    submission, execution = synthetic_sources
    submission_file = tmp_path / "submission.json"
    execution_file = tmp_path / "execution.json"
    submission_file.write_bytes(submission)
    execution_file.write_bytes(execution)
    output = tmp_path / "sidecar"
    first_name = "verified_multi_boundary_evidence.csv"
    owned_target = output / first_name
    real_link = os.link
    real_unlink = Path.unlink
    link_calls = 0

    def first_link_then_fail(source, target):
        nonlocal link_calls
        link_calls += 1
        if link_calls == 2:
            raise OSError("synthetic publication failure before cleanup")
        return real_link(source, target)

    def fail_owned_output_unlink(path: Path, *arguments, **keyword_arguments):
        if path == owned_target:
            raise OSError("synthetic owned-link cleanup failure")
        return real_unlink(path, *arguments, **keyword_arguments)

    monkeypatch.setattr(os, "link", first_link_then_fail)
    monkeypatch.setattr(Path, "unlink", fail_owned_output_unlink)
    try:
        with pytest.raises(
            OSError,
            match="sidecar workspace publication cleanup failed",
        ) as captured:
            CLI.prepare_sidecar_workspace(
                repo_root=REPO_ROOT,
                submission_file=submission_file,
                execution_file=execution_file,
                output_dir=output,
            )
        assert link_calls == 2
        assert isinstance(captured.value.__cause__, OSError)
        assert "synthetic publication failure before cleanup" in str(
            captured.value.__cause__
        )
        assert output.is_dir()
        assert tuple(path.name for path in output.iterdir()) == (first_name,)
        assert not list(tmp_path.glob(".sidecar.tmp-*"))
    finally:
        monkeypatch.undo()
        if owned_target.exists():
            owned_target.unlink()
        if output.exists():
            output.rmdir()
    assert not output.exists()
    assert not list(tmp_path.glob(".sidecar.tmp-*"))


def test_import_is_silent_and_has_no_output_side_effects() -> None:
    result = subprocess.run(
        (
            str(PYTHON),
            "-B",
            "-c",
            (
                "import "
                "covalent_ext."
                "covapie_current11_multi_boundary_human_review_sidecar_v1"
            ),
        ),
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": "src",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == b""
    assert result.stderr == b""
