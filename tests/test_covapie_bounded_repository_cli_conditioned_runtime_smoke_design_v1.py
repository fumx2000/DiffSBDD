from __future__ import annotations

import ast
import hashlib
import inspect
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from Bio.PDB import PDBParser

from covalent_ext import (
    covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1 as design,
)


ROOT = Path(__file__).resolve().parents[1]
ERROR = "COVAPIE_BOUNDED_REPOSITORY_CLI_CONDITIONED_RUNTIME_SMOKE_DESIGN_INVALID"


@pytest.fixture(scope="session")
def response() -> dict[str, object]:
    return design.evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1(
        repo_root=ROOT
    )


def test_public_api_is_exact_and_keyword_only() -> None:
    assert design.__all__ == (
        "evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1",
    )
    signature = inspect.signature(
        design.evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1
    )
    assert list(signature.parameters) == ["repo_root"]
    assert signature.parameters["repo_root"].kind is inspect.Parameter.KEYWORD_ONLY


def test_import_is_silent_and_does_not_import_torch() -> None:
    code = """
import contextlib, importlib, io, sys
before = set(sys.modules)
stdout = io.StringIO()
stderr = io.StringIO()
with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
    module = importlib.import_module(
        'covalent_ext.covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1'
    )
assert stdout.getvalue() == ''
assert stderr.getvalue() == ''
assert 'torch' not in set(sys.modules) - before
assert module.__all__ == (
    'evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1',
)
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ".:src:scripts"},
        check=False,
        capture_output=True,
        timeout=30,
    )
    assert completed.returncode == 0
    assert completed.stdout == b""
    assert completed.stderr == b""


def test_response_is_json_safe_ordered_and_digest_bound(response: dict[str, object]) -> None:
    fields = design.BOUNDED_REPOSITORY_CLI_CONDITIONED_RUNTIME_SMOKE_DESIGN_RESPONSE_FIELDS
    assert fields == (
        "bounded_runtime_smoke_design_version",
        "bounded_runtime_smoke_design_error_contract",
        "bounded_runtime_smoke_design_complete",
        "bounded_runtime_smoke_implementation_deferred",
        "fresh_runtime_source_revalidation_required_before_implementation",
        "current_mainline_priority",
        "source_C4_commit_identity",
        "source_C4_file_identities",
        "C4_published_response_binding",
        "C4_published_checker_stdout_binding",
        "C4_published_bound",
        "repository_cli_selector_forwarding_complete",
        "selected_runtime_smoke_caller",
        "deferred_runtime_smoke_callers",
        "deferred_runtime_smoke_caller_count",
        "caller_scope_boundary",
        "source_C1_binding",
        "C1_public_apis",
        "real_checkpoint_binding",
        "source_C2_commit_identity",
        "source_C2_file_identity",
        "runtime_source_bindings",
        "C2_generate_ligands_ast_evidence",
        "C2_generate_ligands_bound",
        "canonical_mask_semantic_names",
        "canonical_mask_count",
        "temporary_PDB_contract",
        "Exact6_runtime_contract",
        "CLI_argv_contract",
        "CLI_argument_semantics",
        "child_environment_contract",
        "random_seed_contract",
        "resource_bounds",
        "subprocess_execution_contract",
        "transparent_observer_contract",
        "runtime_evidence_schema",
        "output_acceptance_contract",
        "parameter_immutability_contract",
        "checkpoint_immutability_contract",
        "temporary_workspace_contract",
        "timeout_contract",
        "real_runtime_smoke_executed",
        "model_forward_executed",
        "training_or_parameter_update",
        "RL_implementation_started",
        "feature_semantics_audit_required_before_training",
        "smoke_does_not_validate_feature_semantics",
        "ready_for_bounded_runtime_smoke_implementation",
        "recommended_next_step",
        "bounded_runtime_smoke_design_response_sha256",
    )
    assert tuple(response) == fields
    assert len(response) == len(fields) == 50
    assert fields[-1] == "bounded_runtime_smoke_design_response_sha256"
    unsigned = {field: response[field] for field in fields[:-1]}
    payload = json.dumps(
        unsigned,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    assert response[fields[-1]] == hashlib.sha256(payload).hexdigest()
    assert json.loads(design._canonical_json_bytes(response)) == response
    assert design._validate_response(response)


def test_evaluator_is_deterministic_for_canonical_values(response: dict[str, object]) -> None:
    reconstructed = json.loads(design._canonical_json_bytes(response))
    assert reconstructed == response
    assert design._canonical_json_bytes(reconstructed) == design._canonical_json_bytes(response)


@pytest.mark.parametrize("invalid_root", [Path("."), "."])
def test_evaluator_fails_closed_for_invalid_repo_root(invalid_root: object) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        design.evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1(
            repo_root=invalid_root  # type: ignore[arg-type]
        )


def test_response_validator_fails_closed_on_tampering(response: dict[str, object]) -> None:
    tampered = dict(response)
    tampered["ready_for_bounded_runtime_smoke_implementation"] = False
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        design._validate_response(tampered)


def test_read_regular_file_accepts_non_executable_0644_file(tmp_path: Path) -> None:
    path = tmp_path / "source.py"
    path.write_bytes(b"source\n")
    path.chmod(0o644)
    payload, metadata = design._read_regular_file(tmp_path, "source.py")
    assert payload == b"source\n"
    assert metadata.st_mode & 0o777 == 0o644


def test_read_regular_file_rejects_any_executable_bit(tmp_path: Path) -> None:
    path = tmp_path / "source.py"
    path.write_bytes(b"source\n")
    path.chmod(0o755)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        design._read_regular_file(tmp_path, "source.py")


def test_read_regular_file_rejects_symlink(tmp_path: Path) -> None:
    target = tmp_path / "target.py"
    target.write_bytes(b"source\n")
    target.chmod(0o644)
    (tmp_path / "source.py").symlink_to(target)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        design._read_regular_file(tmp_path, "source.py")


def test_read_regular_file_rejects_mode_drift_during_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "source.py"
    path.write_bytes(b"source\n")
    path.chmod(0o644)
    original_read_bytes = Path.read_bytes

    def read_then_drift(self: Path) -> bytes:
        payload = original_read_bytes(self)
        if self == path:
            self.chmod(0o600)
        return payload

    monkeypatch.setattr(Path, "read_bytes", read_then_drift)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        design._read_regular_file(tmp_path, "source.py")


def test_c4_published_response_is_exactly_bound(response: dict[str, object]) -> None:
    binding = response["C4_published_response_binding"]
    assert binding == {
        "exact_field_count": 62,
        "response_sha256": "b455fe78165cf13f8277a866e1bc8069c980f98080eb0026302c9047d1d8d224",
        "lifecycle_profile": "c4_published_successor",
        "gate_commit": "011b9558d4a59824e3ba51a0d896ec13100b2b1b",
        "gate_committed": True,
        "gate_published": True,
        "ready_for_repository_cli_runtime_smoke_planning": True,
    }
    assert response["C4_published_bound"] is True
    assert response["repository_cli_selector_forwarding_complete"] is True


def test_c4_exact_commit_and_four_file_identities(response: dict[str, object]) -> None:
    identity = response["source_C4_commit_identity"]
    assert identity["commit"] == "011b9558d4a59824e3ba51a0d896ec13100b2b1b"
    assert identity["parent"] == "bd36211b03792602f382c16badac61eed79c8f9c"
    assert identity["subject"] == "add CovaPIE target residue repository CLI forwarding gate C4 v1"
    assert identity["exact_path_scope_count"] == 4
    files = response["source_C4_file_identities"]
    assert {path: item["sha256"] for path, item in files.items()} == {
        "src/covalent_ext/covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py": "62a5e13a58e4fa3d6e4dc007eaf2eb842434c3d9d3245b843d2fae83fbb58622",
        "tests/test_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py": "b4bb07af5345782a7c1c6d28546a4da75d04c3d8f00ae2e65e1a92282d2f08d1",
        "scripts/check_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py": "a33b4985f6151eee116cda97324482ce9b025698636f21d6ec57e13dd8e786a2",
        "docs/covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1_guide.md": "4d6da36d0c027d06e2c5211d9d578205300800be3b0d5bf39136e50bfaae2974",
    }
    assert all(item["git_mode"] == "100644" for item in files.values())


def test_c4_checker_stdout_contract_is_frozen(response: dict[str, object]) -> None:
    assert response["C4_published_checker_stdout_binding"] == {
        "checker_path": "scripts/check_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py",
        "stdout_sha256": "4526973c08805ac70442e24bdce29f256a5a48d94ab6e5f616ead3aa5a42c553",
        "returncode": 0,
        "stderr_empty": True,
    }


def test_c1_helper_and_checkpoint_are_bound_without_loading(response: dict[str, object]) -> None:
    c1 = response["source_C1_binding"]
    assert c1["commit"] == "142e7f72b391ceed3bbecaf22846a08f56933ea5"
    assert c1["helper_sha256"] == "ff02657edd67d643bed4881b3c52df75cb950dffc45c19e5497b07dd65a52dfc"
    assert c1["ordinary_regular"] is True
    assert c1["symlink"] is False
    assert c1["executable"] is False
    assert c1["mode_stable_during_read"] is True
    assert c1["checkpoint_loaded_by_design"] is False
    assert c1["torch_model_imported_by_design"] is False
    assert response["C1_public_apis"] == [
        "add_covapie_target_residue_atom_condition_cli_arguments_v1",
        "resolve_covapie_target_residue_atom_condition_cli_args_v1",
        "load_covapie_target_residue_conditioned_model_from_checkpoint_v1",
    ]
    checkpoint = response["real_checkpoint_binding"]
    assert checkpoint["path"] == "checkpoints/crossdocked_fullatom_cond.ckpt"
    assert checkpoint["size"] == 17_861_341
    assert checkpoint["sha256"] == "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
    assert checkpoint["ordinary_regular"] is True
    assert checkpoint["symlink"] is False
    assert checkpoint["executable"] is False
    assert checkpoint["mode_stable_during_read"] is True
    assert checkpoint["deserialized_by_design"] is False
    assert checkpoint["direct_migration_helper_allowed"] is False
    assert checkpoint["strict_false_allowed"] is False


def test_c2_caller_identity_and_ast_are_bound(response: dict[str, object]) -> None:
    identity = response["source_C2_commit_identity"]
    file_identity = response["source_C2_file_identity"]
    evidence = response["C2_generate_ligands_ast_evidence"]
    assert identity["commit"] == "7cdaf807241e3dc4331d5c0a05eb6a63dd4d5ec4"
    assert identity["exact_path_scope"] == ["generate_ligands.py"]
    assert file_identity == {
        "sha256": "0739a7c194ab7794227a57fa28e7f7aea93b2013750e1ce1b1cde5d37b45d9c0",
        "git_blob": "418a4efa20d76d415b9f3fbc07a5654593df47e8",
        "git_mode": "100644",
        "live_bytes_match_commit": True,
        "ordinary_regular": True,
        "symlink": False,
        "executable": False,
        "mode_stable_during_read": True,
    }
    for field in (
        "parser_helper_call_count",
        "parse_args_call_count",
        "resolver_call_count",
        "conditioned_loader_call_count",
        "legacy_loader_call_count",
        "model_generate_ligands_call_count",
        "write_sdf_file_call_count",
        "selector_forwarding_keyword_count",
    ):
        assert evidence[field] == 1
    assert evidence["C1_helpers_each_imported_once"] is True
    assert evidence["selector_resolved_before_loader"] is True
    assert evidence["legacy_and_conditioned_branches_mutually_exclusive"] is True
    assert evidence["conditioned_loader_failure_has_no_legacy_fallback"] is True
    assert evidence["selector_forwarded_to_every_batch"] is True


def test_three_runtime_sources_are_exactly_bound_to_snapshot(response: dict[str, object]) -> None:
    bindings = response["runtime_source_bindings"]
    assert bindings["snapshot_commit"] == "011b9558d4a59824e3ba51a0d896ec13100b2b1b"
    current_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    current_origin = subprocess.run(
        ["git", "rev-parse", "origin/main"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert bindings["current_HEAD"] == current_head
    assert bindings["current_origin_main"] == current_origin
    assert bindings["snapshot_is_ancestor_of_HEAD"] is True
    assert bindings["snapshot_is_ancestor_of_origin_main"] is True
    assert bindings["all_live_bytes_match_snapshot"] is True
    assert bindings["source_count"] == 3
    assert bindings["drift_requires_design_revalidation_before_implementation"] is True
    expected = {
        "lightning_modules.py": (
            "7431b5cf24d4f918df961eb97c75f2e296c8b3c523fb627063f3a6c2f08fc983",
            "d19f18ec2841a9a3163d099f4df451d97ce795d4",
        ),
        "equivariant_diffusion/conditional_model.py": (
            "a61dc44f376b3efc0365f558b09470f71b35dd2606c216f5abf0ba06d5a1b4a9",
            "4c4ffab13830506f7442c8ccb2e7cdad5bbcfae2",
        ),
        "utils.py": (
            "2d8fdc954f025e70717b992a1382d8a020eff9170af8e92c961e74759287793b",
            "75450035d1dcd28590d487b3c5c0eaff79fced8a",
        ),
    }
    assert set(bindings["files"]) == set(expected)
    for path, (sha256, blob) in expected.items():
        item = bindings["files"][path]
        assert item == {
            "sha256": sha256,
            "git_blob": blob,
            "git_mode": "100644",
            "live_bytes_match_snapshot": True,
            "ordinary_regular": True,
            "symlink": False,
            "executable": False,
            "mode_stable_during_read": True,
        }


@pytest.mark.parametrize(
    ("current_head", "current_origin"),
    [
        pytest.param(
            "011b9558d4a59824e3ba51a0d896ec13100b2b1b",
            "011b9558d4a59824e3ba51a0d896ec13100b2b1b",
            id="precommit",
        ),
        pytest.param("d" * 40, "011b9558d4a59824e3ba51a0d896ec13100b2b1b", id="committed_unpushed"),
        pytest.param("d" * 40, "d" * 40, id="published"),
        pytest.param("f" * 40, "f" * 40, id="future_successor"),
    ],
)
def test_runtime_snapshot_lifecycle_accepts_all_successor_states(
    current_head: str, current_origin: str
) -> None:
    result = design._runtime_source_snapshot_lifecycle_from_facts(
        {
            "snapshot_commit": "011b9558d4a59824e3ba51a0d896ec13100b2b1b",
            "current_HEAD": current_head,
            "current_origin_main": current_origin,
            "snapshot_is_ancestor_of_HEAD": True,
            "snapshot_is_ancestor_of_origin_main": True,
        }
    )
    assert result["snapshot_commit"] == (
        "011b9558d4a59824e3ba51a0d896ec13100b2b1b"
    )
    assert result["current_HEAD"] == current_head
    assert result["current_origin_main"] == current_origin


@pytest.mark.parametrize(
    ("head_ancestor", "origin_ancestor"),
    [(False, True), (True, False)],
)
def test_runtime_snapshot_lifecycle_rejects_missing_ancestry(
    head_ancestor: bool, origin_ancestor: bool
) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        design._runtime_source_snapshot_lifecycle_from_facts(
            {
                "snapshot_commit": "011b9558d4a59824e3ba51a0d896ec13100b2b1b",
                "current_HEAD": "d" * 40,
                "current_origin_main": "d" * 40,
                "snapshot_is_ancestor_of_HEAD": head_ancestor,
                "snapshot_is_ancestor_of_origin_main": origin_ancestor,
            }
        )


def _valid_runtime_source_file_facts() -> dict[str, object]:
    return {
        "relative_path": "lightning_modules.py",
        "snapshot_sha256": "7431b5cf24d4f918df961eb97c75f2e296c8b3c523fb627063f3a6c2f08fc983",
        "snapshot_git_blob": "d19f18ec2841a9a3163d099f4df451d97ce795d4",
        "snapshot_git_mode": "100644",
        "live_sha256": "7431b5cf24d4f918df961eb97c75f2e296c8b3c523fb627063f3a6c2f08fc983",
        "live_bytes_match_snapshot": True,
        "ordinary_regular": True,
        "symlink": False,
        "executable": False,
        "mode_stable_during_read": True,
    }


def test_runtime_source_file_fact_compiler_accepts_exact_snapshot() -> None:
    result = design._runtime_source_file_identity_from_facts(
        _valid_runtime_source_file_facts()
    )
    assert result["live_bytes_match_snapshot"] is True
    assert result["git_mode"] == "100644"


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("snapshot_git_blob", "0" * 40),
        ("live_sha256", "0" * 64),
        ("live_bytes_match_snapshot", False),
        ("snapshot_git_mode", "100755"),
        ("ordinary_regular", False),
        ("symlink", True),
        ("executable", True),
        ("mode_stable_during_read", False),
    ],
)
def test_runtime_source_file_fact_compiler_fails_closed(
    field: str, invalid_value: object
) -> None:
    facts = _valid_runtime_source_file_facts()
    facts[field] = invalid_value
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        design._runtime_source_file_identity_from_facts(facts)


def test_frozen_conditional_runtime_has_exactly_two_dynamics_calls_for_one_step() -> None:
    tree = ast.parse(
        (ROOT / "equivariant_diffusion/conditional_model.py").read_text(
            encoding="utf-8"
        )
    )
    conditional = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "ConditionalDDPM"
    )
    methods = {
        node.name: node
        for node in conditional.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    reverse_step = methods["sample_p_zs_given_zt"]
    final_decode = methods["sample_p_xh_given_z0"]
    sampler = methods["sample_given_pocket"]
    assert len(design._calls(reverse_step, "self.dynamics")) == 1
    assert len(design._calls(final_decode, "self.dynamics")) == 1
    assert len(design._calls(sampler, "self.sample_p_zs_given_zt")) == 1
    assert len(design._calls(sampler, "self.sample_p_xh_given_z0")) == 1
    loops = [node for node in ast.walk(sampler) if isinstance(node, ast.For)]
    assert len(loops) == 1
    assert ast.unparse(loops[0].iter) == "reversed(range(0, timesteps))"

    lightning_tree = ast.parse(
        (ROOT / "lightning_modules.py").read_text(encoding="utf-8")
    )
    ligand_model = next(
        node
        for node in lightning_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "LigandPocketDDPM"
    )
    generate = next(
        node
        for node in ligand_model.body
        if isinstance(node, ast.FunctionDef) and node.name == "generate_ligands"
    )
    assert len(design._calls(generate, "self.ddpm.sample_given_pocket")) == 1
    assert "type(self.ddpm) == ConditionalDDPM" in ast.unparse(generate)


def test_selected_and_deferred_caller_boundary(response: dict[str, object]) -> None:
    assert response["selected_runtime_smoke_caller"] == "generate_ligands.py"
    assert response["deferred_runtime_smoke_callers"] == [
        "scripts/covalent_inpaint_demo.py"
    ]
    assert response["deferred_runtime_smoke_caller_count"] == 1
    boundary = response["caller_scope_boundary"]
    assert boundary["generate_ligands_only"] is True
    assert boundary["covalent_demo_runtime_smoke_deferred"] is True
    assert boundary["combine_callers_in_v1"] is False


def test_canonical_mask_contract_remains_exact_five(response: dict[str, object]) -> None:
    assert response["canonical_mask_semantic_names"] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert response["canonical_mask_count"] == 5


def test_frozen_pdb_bytes_are_exact(response: dict[str, object]) -> None:
    contract = response["temporary_PDB_contract"]
    payload = contract["pdb_text"].encode("utf-8")
    assert len(payload) == contract["byte_count"] == 505
    assert hashlib.sha256(payload).hexdigest() == contract["sha256"]
    assert contract["sha256"] == "ccad2ee5cd8cc2459003790d837bbdc68fede63cdb5ea575f433250048f302c3"
    assert payload.endswith(b"\n")
    assert b"\r" not in payload
    assert contract["atom_names"] == ["N", "CA", "C", "O", "CB", "SG"]
    assert contract["elements"] == ["N", "C", "C", "O", "C", "S"]
    assert contract["TER_present"] is True
    assert contract["END_present"] is True
    assert contract["repository_file_created"] is False


def test_frozen_pdb_parses_in_memory_to_unique_cys_a_1_sg(response: dict[str, object]) -> None:
    contract = response["temporary_PDB_contract"]
    structure = PDBParser(QUIET=True).get_structure(
        "minimal_cys_sg", io.StringIO(contract["pdb_text"])
    )
    models = list(structure.get_models())
    residues = list(structure.get_residues())
    atoms = list(structure.get_atoms())
    targets = [
        atom
        for atom in atoms
        if atom.get_name() == "SG"
        and atom.element == "S"
        and atom.get_parent().get_resname() == "CYS"
        and atom.get_parent().get_parent().id == "A"
        and atom.get_parent().id == (" ", 1, " ")
    ]
    assert len(models) == contract["model_count"] == 1
    assert len(residues) == contract["residue_count"] == 1
    assert len(atoms) == contract["atom_count"] == 6
    assert len(targets) == contract["SG_count"] == 1
    assert [atom.get_name() for atom in atoms] == contract["atom_names"]


def test_exact6_selector_is_explicit_and_unique(response: dict[str, object]) -> None:
    contract = response["Exact6_runtime_contract"]
    assert contract["selector"] == {
        "chain_id": "A",
        "residue_sequence_number": 1,
        "residue_insertion_code": " ",
        "residue_name": "CYS",
        "atom_name": "SG",
        "element": "S",
    }
    assert contract["unique_target_count"] == 1
    assert contract["target_inferred_from_reference_ligand"] is False
    assert contract["target_inferred_from_distance"] is False


def test_cli_argv_is_exact_and_omits_reference_ligand(response: dict[str, object]) -> None:
    assert response["CLI_argv_contract"] == [
        "generate_ligands.py",
        "checkpoints/crossdocked_fullatom_cond.ckpt",
        "--pdbfile",
        "<TEMP>/input/minimal_cys_sg.pdb",
        "--resi_list",
        "A:1",
        "--outfile",
        "<TEMP>/output/generated.sdf",
        "--n_samples",
        "1",
        "--batch_size",
        "1",
        "--num_nodes_lig",
        "4",
        "--timesteps",
        "1",
        "--target_residue_atom_conditioning",
        "--target_chain_id",
        "A",
        "--target_residue_sequence_number",
        "1",
    ]
    semantics = response["CLI_argument_semantics"]
    assert semantics["excluded_options"] == [
        "--ref_ligand",
        "--sanitize",
        "--relax",
        "--all_frags",
    ]
    assert semantics["pocket_ids"] == ["A:1"]
    assert semantics["ref_ligand"] is None


def test_cpu_environment_seeds_and_resource_bounds(response: dict[str, object]) -> None:
    assert response["child_environment_contract"] == {
        "CUDA_VISIBLE_DEVICES": "",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": ".:src:scripts",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
    }
    assert response["random_seed_contract"]["random.seed"] == 0
    assert response["random_seed_contract"]["numpy.random.seed"] == 0
    assert response["random_seed_contract"]["torch.manual_seed"] == 0
    bounds = response["resource_bounds"]
    assert bounds == {
        "device": "cpu",
        "cuda_available": False,
        "A100_used": False,
        "n_samples": 1,
        "batch_size": 1,
        "num_nodes_lig": 4,
        "timesteps": 1,
        "automatic_bound_expansion_allowed": False,
    }


def test_transparent_observers_must_call_original_and_use_no_mocks(response: dict[str, object]) -> None:
    observer = response["transparent_observer_contract"]
    assert observer["wrapper_target_count"] == 5
    assert observer["each_calls_original_exactly_once_per_observed_call"] is True
    assert observer["arguments_modified"] is False
    assert observer["return_values_modified"] is False
    assert observer["model_replaced"] is False
    assert observer["sampling_mocked"] is False
    assert observer["PDB_mocked"] is False
    assert observer["SDF_mocked"] is False
    assert observer["forward_probe_modifies_output"] is False
    probe = observer["forward_probe"]
    assert probe == {
        "hook_target": "model.ddpm.dynamics",
        "hook_API": "register_forward_hook",
        "ddpm_type": "ConditionalDDPM",
        "timesteps": 1,
        "expected_dynamics_forward_call_count": 2,
        "callback_action": "increment_counter_only",
        "callback_return_value": None,
        "inputs_modified": False,
        "output_modified": False,
        "remove_in_finally": True,
        "forbidden_hook_targets": [
            "model",
            "model.ddpm",
            "LigandPocketDDPM",
            "ConditionalDDPM",
        ],
        "forward_call_sources": [
            "sample_p_zs_given_zt_reverse_denoising_step",
            "sample_p_xh_given_z0_final_decode",
        ],
        "fail_closed_requires_exact_count": True,
        "greater_than_zero_only_is_insufficient": True,
        "model_forward_executed_required": True,
    }


def test_future_evidence_schema_covers_runtime_observations(response: dict[str, object]) -> None:
    schema = response["runtime_evidence_schema"]
    fields = schema["required_fields"]
    assert schema["required_field_count"] == len(fields) == 67
    assert len(fields) == len(set(fields))
    for required in (
        "resolver_call_count",
        "conditioned_loader_call_count",
        "legacy_loader_call_count",
        "indicator_true_count",
        "selector_object_is_resolver_output",
        "ddpm_type",
        "dynamics_forward_call_count",
        "model_forward_executed",
        "all_parameter_grads_none",
        "checkpoint_mtime_ns_before",
        "checkpoint_mtime_ns_after",
        "generated_molecule_count",
        "chemical_generation_quality_validated",
        "workspace_st_dev",
        "workspace_st_ino",
    ):
        assert required in fields
    assert schema["fail_closed_on_missing_or_extra_fields"] is True


def test_parameter_and_checkpoint_immutability_are_fail_closed(response: dict[str, object]) -> None:
    parameters = response["parameter_immutability_contract"]
    checkpoint = response["checkpoint_immutability_contract"]
    assert parameters["training_step_executed"] is False
    assert parameters["backward_executed"] is False
    assert parameters["optimizer_created"] is False
    assert parameters["optimizer_step_executed"] is False
    assert parameters["scheduler_step_executed"] is False
    assert parameters["all_parameter_grads_none"] is True
    assert parameters["state_dict_digest_before_equals_after"] is True
    assert parameters["parameter_values_modified"] is False
    assert parameters["parameter_versions_modified"] is False
    assert checkpoint == {
        "bytes_unchanged": True,
        "size_unchanged": True,
        "mtime_ns_unchanged": True,
        "sha256_unchanged": True,
        "torch_save_called": False,
        "save_checkpoint_called": False,
        "state_dict_written_to_disk": False,
    }


def test_zero_or_one_molecule_is_accepted_without_quality_claim(response: dict[str, object]) -> None:
    output = response["output_acceptance_contract"]
    assert output["generated_molecule_count_allowed"] == [0, 1]
    assert output["chemical_generation_quality_is_acceptance_condition"] is False
    assert output["nonempty_SDF_record_required"] is False
    assert output["chemical_generation_quality_validated"] is False


def test_temporary_workspace_uses_inode_guard_and_closed_path_allowlist(response: dict[str, object]) -> None:
    workspace = response["temporary_workspace_contract"]
    assert workspace["root_parent"] == "/tmp"
    assert workspace["must_not_exist_before_creation"] is True
    assert workspace["outside_repository"] is True
    assert workspace["record_st_dev_and_st_ino"] is True
    assert workspace["cleanup_only_if_st_dev_and_st_ino_match"] is True
    assert workspace["cleanup_follows_symlinks"] is False
    assert workspace["competitor_path_deleted"] is False
    assert workspace["other_paths_allowed"] is False
    assert workspace["runtime_generated_repository_paths"] == []


def test_timeout_and_process_contract_fail_closed(response: dict[str, object]) -> None:
    timeout = response["timeout_contract"]
    assert timeout["parent_timeout_seconds"] == 300
    assert timeout["timeout_fails_closed"] is True
    assert timeout["timeout_cleanup_required"] is True
    assert timeout["child_returncode_required"] == 0
    assert timeout["stderr_must_be_empty"] is True
    execution = response["subprocess_execution_contract"]
    assert execution["runpy_path"] == "generate_ligands.py"
    assert execution["runpy_run_name"] == "__main__"
    assert execution["real_conditioned_loader"] is True
    assert execution["real_generation"] is True
    assert execution["mocks_used"] is False
    assert execution["caller_main_executed_by_design"] is False
    assert execution["one_time_execution_only"] is True
    assert execution["repeat_without_new_user_authorization"] is False
    assert execution["post_smoke_mainline_priority"] == (
        "audit_covapie_five_module_training_path_completion_gaps_v1"
    )
    assert execution["smoke_success_does_not_establish_training_readiness"] is True
    assert execution["smoke_failure_does_not_authorize_architecture_expansion"] is True


def test_design_is_lifecycle_neutral_and_does_not_query_own_git_state() -> None:
    source = Path(design.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    string_literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and type(node.value) is str
    }
    assert "ls-files" not in string_literals
    assert "status" not in string_literals
    assert "write-tree" not in string_literals
    assert "commit-tree" not in string_literals


def test_design_does_not_execute_runtime_training_or_rl(response: dict[str, object]) -> None:
    assert response["real_runtime_smoke_executed"] is False
    assert response["model_forward_executed"] is False
    assert response["training_or_parameter_update"] is False
    assert response["RL_implementation_started"] is False
    assert response["feature_semantics_audit_required_before_training"] is True
    assert response["smoke_does_not_validate_feature_semantics"] is True
    assert response["bounded_runtime_smoke_design_complete"] is True
    assert response["bounded_runtime_smoke_implementation_deferred"] is False
    assert response[
        "fresh_runtime_source_revalidation_required_before_implementation"
    ] is True
    assert response["current_mainline_priority"] == (
        "implement_and_execute_bounded_covapie_repository_cli_conditioned_runtime_smoke_v1"
    )
    assert response["ready_for_bounded_runtime_smoke_implementation"] is True
    assert response["recommended_next_step"] == (
        "implement_and_execute_bounded_covapie_repository_cli_conditioned_runtime_smoke_v1"
    )
