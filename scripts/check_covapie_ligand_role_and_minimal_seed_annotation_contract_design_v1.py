"""Independent checker for the ligand-role/minimal-seed annotation design V1."""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import io
import json
import stat
import subprocess
from pathlib import Path

from covalent_ext import (
    covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1 as contract,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1"
)
EXACT10 = (
    Path("src/covalent_ext/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"),
    Path("tests/test_covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"),
    Path("scripts/check_covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"),
    Path("docs/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1_summary.md"),
    OUTPUT_ROOT / contract.SOURCE_INVENTORY_FILE,
    OUTPUT_ROOT / contract.CONTRACT_REGISTRY_FILE,
    OUTPUT_ROOT / contract.RULE_REGISTRY_FILE,
    OUTPUT_ROOT / contract.READINESS_MATRIX_FILE,
    OUTPUT_ROOT / contract.FAILURE_MATRIX_FILE,
    OUTPUT_ROOT / contract.MANIFEST_FILE,
)
FORBIDDEN_SUFFIXES = {
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".npz",
    ".tar", ".zip", ".tgz", ".tmp", ".part",
}


def _fail(message: str) -> None:
    raise SystemExit(message)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _csv_bool(value: str, *, field: str) -> bool:
    if value not in {"true", "false"}:
        _fail(f"CSV bool invalid: {field}")
    return value == "true"


def _git(*args: str) -> bytes:
    result = subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        _fail(result.stderr.decode("utf-8", "replace").strip())
    return result.stdout


def _check_base_and_sources() -> None:
    identity = _git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", contract.BASE_COMMIT
    ).decode().splitlines()
    if identity != [
        contract.BASE_COMMIT,
        contract.BASE_PARENT,
        contract.BASE_TREE,
        contract.BASE_SUBJECT,
    ]:
        _fail("formal BASE identity drift")
    for path, expected in contract.FROZEN_SHA256.items():
        if path.as_posix().startswith(("data/raw/", "checkpoints/")):
            _fail("forbidden frozen source")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            _fail("forbidden frozen source suffix")
        if _sha(_git("show", f"{contract.BASE_COMMIT}:{path.as_posix()}")) != expected:
            _fail(f"frozen source SHA drift: {path}")


def _check_exact10_and_evidence() -> tuple[dict, dict[str, bytes]]:
    if len(EXACT10) != 10 or len(set(EXACT10)) != 10:
        _fail("Exact10 identity drift")
    for relative in EXACT10:
        path = ROOT / relative
        if not path.is_file() or path.is_symlink():
            _fail(f"invalid Exact10 path: {relative}")
        if stat.S_IMODE(path.stat().st_mode) != 0o644:
            _fail(f"invalid Exact10 mode: {relative}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            _fail(f"forbidden Exact10 suffix: {relative}")
        if path.stat().st_size >= 100 * 1024 * 1024:
            _fail(f"oversize Exact10 file: {relative}")
    actual_output_names = {
        path.name for path in (ROOT / OUTPUT_ROOT).iterdir() if path.is_file()
    }
    if actual_output_names != set(contract.OUTPUT_FILES):
        _fail("output evidence is not Exact6")
    expected = contract.build_artifacts(ROOT)
    observed = {
        name: (ROOT / OUTPUT_ROOT / name).read_bytes()
        for name in contract.OUTPUT_FILES
    }
    if observed != expected:
        _fail("checked evidence differs from deterministic builder")
    manifest = json.loads(observed[contract.MANIFEST_FILE])
    if contract.MANIFEST_FILE in manifest.get("evidence_sha256", {}):
        _fail("manifest records its own SHA")
    for name, expected_sha in manifest["evidence_sha256"].items():
        if _sha(observed[name]) != expected_sha:
            _fail(f"manifest evidence SHA mismatch: {name}")
    return manifest, observed


def _check_contract_semantics(manifest: dict, observed: dict[str, bytes]) -> None:
    if tuple(manifest["canonical_roles"]) != ("scaffold", "linker", "warhead"):
        _fail("Exact3 role vocabulary drift")
    tasks = manifest["canonical_tasks"]
    if [row["semantic_name"] for row in tasks] != [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]:
        _fail("Exact5 task identity drift")
    if len(tasks) != 5:
        _fail("sixth mask introduced")
    b3 = next(row for row in tasks if row["semantic_name"] == "scaffold_only")
    if b3["target"] != ["scaffold"] or b3["context"] != ["linker", "warhead"]:
        _fail("B3 identity drift")
    if contract.validate_exact3_partition(
        range(6), (0, 1), (2, 3), (4, 5)
    ):
        _fail("valid Exact3 partition rejected")
    if "partition_overlap" not in contract.validate_exact3_partition(
        range(5), (0, 1), (1, 2), (3, 4)
    ):
        _fail("partition overlap did not fail closed")
    graph = contract.classify_linker_components(
        range(5), ((0, 1), (1, 2), (2, 3), (3, 4)), (4,), (0, 1)
    )
    if graph["bridge_count"] != 1:
        _fail("linker bridge reconstruction failed")
    seed_reasons = contract.validate_minimal_seed(
        (0, 1), (0, 1), (2, 3), (4,), ((0, 1),), 0
    )
    if seed_reasons:
        _fail("valid minimal seed rejected")
    if tuple(manifest["annotation_statuses"]) != contract.ANNOTATION_STATUSES:
        _fail("annotation status vocabulary drift")


def _check_source_inventory(observed: dict[str, bytes]) -> None:
    rows = _rows(observed[contract.SOURCE_INVENTORY_FILE])
    if len(rows) != 17:
        _fail("source inventory is not Exact17")
    paths = [row["source_path"] for row in rows]
    if len(set(paths)) != 17 or set(paths) != {
        path.as_posix() for path in contract.FROZEN_SHA256
    }:
        _fail("source inventory path identity drift")
    for row in rows:
        path = Path(row["source_path"])
        if path.as_posix().startswith(("data/raw/", "checkpoints/")):
            _fail("source inventory contains forbidden path")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            _fail("source inventory contains forbidden suffix")
        if row["evidence_class"] not in {
            "authoritative", "supporting", "gap_evidence",
        }:
            _fail("source inventory evidence class drift")
        _csv_bool(
            row["provides_actual_current11_value"],
            field="provides_actual_current11_value",
        )
        _csv_bool(row["schema_only"], field="schema_only")
        if not _csv_bool(row["verified"], field="verified"):
            _fail("source inventory row not verified")
        payload = _git(
            "show", f"{contract.BASE_COMMIT}:{path.as_posix()}"
        )
        if _sha(payload) != row["sha256"]:
            _fail(f"source inventory BASE SHA mismatch: {path}")


def _check_contract_registry(observed: dict[str, bytes]) -> None:
    rows = _rows(observed[contract.CONTRACT_REGISTRY_FILE])
    required = {
        "role_vocabulary",
        "role_atom_set_partition",
        "warhead_match_contract",
        "scaffold_core_proposal",
        "linker_bridge",
        "scaffold_remainder",
        "scaffold_linker_boundary",
        "linker_warhead_boundary",
        "minimal_seed",
        "primary_direction_plane_anchors",
        "annotation_status",
        "ambiguity_reasons",
        "human_review_decision",
        "five_mask_derivation_prerequisites",
    }
    if len(rows) != 14 or {row["semantic_name"] for row in rows} != required:
        _fail("contract registry is not Exact14")
    if len({row["contract_id"] for row in rows}) != 14:
        _fail("contract registry IDs are not unique")
    for row in rows:
        if row["status"] != "designed_with_input_authority_gap":
            _fail("contract registry input-authority gap status drift")
        if not row["blocking_reason"]:
            _fail("contract registry blocker missing")
        if not _csv_bool(row["verified"], field="verified"):
            _fail("contract registry row not verified")


def _check_rule_registry(observed: dict[str, bytes]) -> None:
    rows = _rows(observed[contract.RULE_REGISTRY_FILE])
    if len(rows) != 21 or len({row["rule_id"] for row in rows}) != 21:
        _fail("rule registry is not Exact21")
    priorities = [int(row["priority"]) for row in rows]
    if priorities != list(range(10, 211, 10)):
        _fail("rule priority order drift")
    allowed_statuses = {
        "required", "proposal_only", "supporting_only", "review_required",
    }
    if any(row["rule_status"] not in allowed_statuses for row in rows):
        _fail("rule status vocabulary drift")
    by_name = {row["rule_name"]: row for row in rows}
    ringless = by_name.get("ringless fallback requires review")
    if ringless is None or "cannot be auto-exact" not in ringless["rule_semantics"]:
        _fail("ringless auto-exact prohibition missing")
    if "current11 human gold review required" not in by_name:
        _fail("human gold rule missing")
    if any(
        not _csv_bool(row["fails_closed"], field="fails_closed")
        or not _csv_bool(row["verified"], field="verified")
        for row in rows
    ):
        _fail("rule registry fail-closed evidence drift")


def _check_readiness(observed: dict[str, bytes]) -> None:
    readiness = _rows(observed[contract.READINESS_MATRIX_FILE])
    if len(readiness) != 11 or len({r["sample_index_row_id"] for r in readiness}) != 11:
        _fail("current11 readiness cardinality drift")
    for row in readiness:
        for field in (
            "retained_heavy_atom_mapping_available",
            "ligand_reactive_atom_available",
            "residue_reactive_atom_available",
        ):
            if not _csv_bool(row[field], field=field):
                _fail(f"current11 positive authority audit drift: {field}")
        for field in (
            "pre_reaction_connectivity_available",
            "pre_reaction_bond_order_available",
            "reaction_family_label_available",
            "approved_warhead_rule_available",
            "role_proposal_generation_ready",
            "minimal_seed_proposal_generation_ready",
            "human_gold_review_completed",
        ):
            if _csv_bool(row[field], field=field):
                _fail(f"current11 fail-closed readiness drift: {field}")
        if not _csv_bool(row["verified"], field="verified"):
            _fail("current11 readiness row not verified")


def _check_failure_evidence(observed: dict[str, bytes]) -> None:
    failures = _rows(observed[contract.FAILURE_MATRIX_FILE])
    if len(failures) != 42:
        _fail("failure matrix is not Exact42")
    if len({row["mutation_signature"] for row in failures}) != 42:
        _fail("failure mutation signatures are not Exact42 unique")
    if [row["failure_case"] for row in failures] != list(
        contract.FAILURE_MUTATIONS
    ):
        _fail("failure case identity/order drift")
    baseline_fields = {
        field.name: getattr(contract.BASELINE_SCENARIO, field.name)
        for field in dataclasses.fields(contract.BASELINE_SCENARIO)
    }
    for row, (case, specification) in zip(
        failures, contract.FAILURE_MUTATIONS.items(), strict=True
    ):
        fields = specification["fields"]
        expected_reasons = specification["expected_reasons"]
        serialized_fields = json.dumps(
            fields, sort_keys=True, separators=(",", ":")
        )
        if row["mutated_fields"] != serialized_fields:
            _fail(f"failure mutated fields drift: {case}")
        if not fields:
            _fail(f"failure mutation empty: {case}")
        for field_name, value in fields.items():
            if field_name not in baseline_fields:
                _fail(f"failure mutation field unknown: {field_name}")
            if type(value) is not type(baseline_fields[field_name]):
                _fail(f"failure mutation exact type drift: {field_name}")
            if value == baseline_fields[field_name]:
                _fail(f"failure mutation does not change baseline: {field_name}")
        if row["mutation_signature"] != contract.mutation_signature(fields):
            _fail("failure mutation signature drift")
        if row["expected_reasons"].split(";") != list(expected_reasons):
            _fail(f"failure expected reasons drift: {case}")
        scenario = dataclasses.replace(contract.BASELINE_SCENARIO, **fields)
        evaluation = contract.evaluate_annotation_scenario(scenario)
        if evaluation.valid or not evaluation.reasons:
            _fail("failure scenario did not fail closed")
        if row["observed_reasons"].split(";") != list(evaluation.reasons):
            _fail(f"failure observed reasons drift: {case}")
        if not all(reason in evaluation.reasons for reason in expected_reasons):
            _fail(f"failure expected reason not observed: {case}")
        if not _csv_bool(
            row["expected_reasons_verified"],
            field="expected_reasons_verified",
        ):
            _fail(f"failure expected reasons not verified: {case}")
        for field in (
            "ready_for_role_annotation_proposal_generation",
            "ready_for_mask_materialization",
            "ready_for_model_integration",
            "ready_for_training",
        ):
            if _csv_bool(row[field], field=field):
                _fail(f"invalid scenario readiness true: {field}")
        if not _csv_bool(row["fails_closed"], field="fails_closed"):
            _fail("failure row does not fail closed")
        if not _csv_bool(row["verified"], field="verified"):
            _fail("failure row not verified")


def _check_runtime_bypass_probes() -> None:
    for field_name in (
        "warhead_boundary_count",
        "linker_bridge_count",
        "scaffold_linker_boundary_count",
    ):
        for invalid_value in (True, 1.0):
            observation = contract.evaluate_annotation_scenario(
                dataclasses.replace(
                    contract.BASELINE_SCENARIO,
                    **{field_name: invalid_value},
                )
            )
            expected = f"scenario_field_type_invalid:{field_name}"
            if observation.valid or observation.reasons != (expected,):
                _fail(f"runtime scalar bypass probe passed: {field_name}")
    status_probes = (
        (
            {"human_review_completed": False},
            "gold_curated_without_human_review",
        ),
        (
            {"annotation_status": "auto_exact", "training_eligible": True},
            "non_gold_annotation_training_eligible",
        ),
        (
            {"ringless_fallback_used": True, "annotation_status": "auto_exact"},
            "ringless_fallback_auto_exact_forbidden",
        ),
    )
    for fields, expected_reason in status_probes:
        observation = contract.evaluate_annotation_scenario(
            dataclasses.replace(contract.BASELINE_SCENARIO, **fields)
        )
        if observation.valid or expected_reason not in observation.reasons:
            _fail(f"runtime status bypass probe passed: {expected_reason}")
    if contract.validate_exact3_partition(
        (False, 1, 2), (0,), (1,), (2,)
    ) != ("partition_index_type_invalid",):
        _fail("partition bool index bypass")
    if contract.validate_exact3_partition(
        (0.0, 1, 2), (0,), (1,), (2,)
    ) != ("partition_index_type_invalid",):
        _fail("partition float index bypass")
    for vertices in ((False, 1), (0.0, 1)):
        try:
            contract.classify_linker_components(
                vertices, ((0, 1),), (1,), (0,)
            )
        except ValueError as error:
            if str(error) != "graph_vertex_index_type_invalid":
                _fail("graph index bypass reason drift")
        else:
            _fail("graph index bypass")
    if contract.validate_minimal_seed(
        (0, 1), (0, 1), (2,), (3,), ((0, 1),), False
    ) != ("primary_anchor_type_invalid",):
        _fail("minimal-seed bool primary anchor bypass")


def _check_truthful_manifest(manifest: dict) -> None:
    required_false = (
        "role_annotation_materialized",
        "minimal_seed_materialized",
        "current11_gold_review_completed",
        "masking_code_changed",
        "schema_changed",
        "dataloader_changed",
        "model_changed",
        "forward_changed",
        "loss_changed",
        "checkpoint_access",
        "raw_read",
        "npz_read",
        "lmdb_read",
        "compressed_archive_read",
        "rdkit_current11_segmentation_run",
        "image_generated",
        "structure_file_written",
        "tensor_materialized",
        "training_used",
        "ready_for_current11_role_annotation_proposal_generation",
        "ready_for_current11_minimal_seed_proposal_generation",
        "ready_for_mask_materialization",
        "ready_for_tensorization",
        "ready_for_model_integration",
        "ready_for_training",
    )
    if not manifest.get("contract_design_completed"):
        _fail("contract design completion not asserted")
    if any(manifest.get(field) is not False for field in required_false):
        _fail("manifest execution/readiness boundary drift")
    if manifest.get("canonical_task_count") != 5:
        _fail("canonical task count drift")
    if manifest.get("planned_covalent_model_module_count") != 5:
        _fail("planned module count drift")
    if manifest.get("integrated_covalent_model_module_count") != 0:
        _fail("integrated module count drift")
    required_true = (
        "annotation_scenario_exact_scalar_types_verified",
        "boundary_and_bridge_counts_exact_int_verified",
        "gold_curated_requires_human_review",
        "training_eligibility_requires_gold_curated",
        "ringless_fallback_auto_exact_forbidden",
        "public_role_atom_index_helpers_exact_types_verified",
        "boolean_rejected_for_role_atom_indices",
        "duplicate_role_atom_indices_rejected",
        "failure_mutation_signatures_unique",
        "failure_expected_reasons_verified",
        "failure_mutation_exact_types_verified",
    )
    if any(manifest.get(field) is not True for field in required_true):
        _fail("manifest hardening flag drift")
    if manifest.get("failure_matrix_row_count") != 42:
        _fail("manifest failure row count drift")
    if manifest.get("failure_mutation_signature_count") != 42:
        _fail("manifest failure signature count drift")
    if manifest.get("recommended_next_step") != (
        "resolve_covapie_role_annotation_input_authority_gaps_v1"
    ):
        _fail("recommended next step is not evidence-driven")


def main() -> None:
    _check_base_and_sources()
    manifest, observed = _check_exact10_and_evidence()
    _check_contract_semantics(manifest, observed)
    _check_source_inventory(observed)
    _check_contract_registry(observed)
    _check_rule_registry(observed)
    _check_readiness(observed)
    _check_failure_evidence(observed)
    _check_runtime_bypass_probes()
    _check_truthful_manifest(manifest)
    summary = {
        "base_commit": contract.BASE_COMMIT,
        "canonical_role_count": 3,
        "canonical_task_count": 5,
        "contract_registry_row_count": manifest["contract_registry_row_count"],
        "current11_readiness_row_count": manifest["current11_readiness_row_count"],
        "failure_matrix_row_count": manifest["failure_matrix_row_count"],
        "ready_for_current11_role_annotation_proposal_generation": False,
        "ready_for_current11_minimal_seed_proposal_generation": False,
        "ready_for_training": False,
        "verified": True,
    }
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
