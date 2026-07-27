#!/usr/bin/env python
"""Independently check the final-training feature-semantics audit evidence."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path

from covalent_ext import (
    covapie_final_training_feature_semantics_and_unknown_atom_policy_audit_v1
    as audit,
)

ROOT = Path(__file__).resolve().parents[1]
EXACT10 = (
    Path(
        "src/covalent_ext/"
        "covapie_final_training_feature_semantics_and_unknown_atom_policy_"
        "audit_v1.py"
    ),
    Path(
        "tests/"
        "test_covapie_final_training_feature_semantics_and_unknown_atom_policy_"
        "audit_v1.py"
    ),
    Path(
        "scripts/"
        "check_covapie_final_training_feature_semantics_and_unknown_atom_policy_"
        "audit_v1.py"
    ),
    Path(
        "docs/"
        "covapie_final_training_feature_semantics_and_unknown_atom_policy_"
        "audit_v1_summary.md"
    ),
    audit.OUTPUT_ROOT / audit.SOURCE_INVENTORY_FILE,
    audit.OUTPUT_ROOT / audit.FEATURE_REGISTRY_FILE,
    audit.OUTPUT_ROOT / audit.UNKNOWN_POLICY_FILE,
    audit.OUTPUT_ROOT / audit.FAILURE_MATRIX_FILE,
    audit.OUTPUT_ROOT / audit.ISSUE_INVENTORY_FILE,
    audit.OUTPUT_ROOT / audit.MANIFEST_FILE,
)


def _git(*args: str) -> bytes:
    return subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _base(path: str | Path) -> bytes:
    path = Path(path)
    name = path.as_posix()
    if name.startswith("data/raw/"):
        raise AssertionError(f"raw source listed: {name}")
    if path.suffix.lower() in {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".npz", ".tar", ".zip",
        ".tgz", ".tmp", ".part",
    }:
        raise AssertionError(f"forbidden source listed: {name}")
    _git("cat-file", "-e", f"{audit.BASE_COMMIT}:{name}")
    return _git("show", f"{audit.BASE_COMMIT}:{name}")


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _truth(value: object) -> bool:
    return value is True or str(value).lower() == "true"


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _independent_atom_coverage() -> dict[str, dict[str, object]]:
    index = _rows(_base(audit.FINAL_DATASET_INDEX))
    assert len(index) == 11
    result = {}
    for domain, column in (
        ("protein_or_pocket_atom", "pocket_atom_table_path"),
        ("ligand_atom", "ligand_atom_table_path"),
    ):
        vocabulary: dict[str, int] = {}
        atom_count = explicit = missing = 0
        paths = []
        for sample in index:
            path = sample[column]
            paths.append(path)
            table = _rows(_base(path))
            assert table
            assert "type_symbol" in table[0]
            assert "atom_name" in table[0]
            for row in table:
                atom_count += 1
                token = row["type_symbol"]
                if token == "":
                    missing += 1
                else:
                    explicit += 1
                    vocabulary[token] = vocabulary.get(token, 0) + 1
        assert len(paths) == len(set(paths)) == 11
        supported = sum(
            count for token, count in vocabulary.items()
            if token in audit.CHECKPOINT_TOKEN_TO_INDEX
        )
        unsupported = sum(
            count for token, count in vocabulary.items()
            if token not in audit.CHECKPOINT_TOKEN_TO_INDEX
        )
        result[domain] = {
            "source_table_count": len(paths),
            "atom_row_count": atom_count,
            "observed_explicit_element_or_token_count": explicit,
            "observed_vocabulary": dict(sorted(vocabulary.items())),
            "supported_row_count": supported,
            "unknown_or_unsupported_row_count": unsupported,
            "missing_feature_value_count": missing,
        }
    return result


def _independent_source_and_lineage_checks(
    source_rows: list[dict[str, str]],
    registry_rows: list[dict[str, str]],
) -> None:
    assert len(source_rows) == 73
    paths = [row["source_path"] for row in source_rows]
    assert len(paths) == len(set(paths))
    assert all(_truth(row["committed_in_base"]) for row in source_rows)
    assert all(_truth(row["verified"]) for row in source_rows)
    assert all(not path.startswith("data/raw/") for path in paths)
    for row in source_rows:
        payload = _base(row["source_path"])
        assert _sha(payload) == row["source_sha256"]
    assert sum(row["source_role"] == "pocket_atom_table" for row in source_rows) == 11
    assert sum(row["source_role"] == "ligand_atom_table" for row in source_rows) == 11
    assert any(row["source_role"] == "feature_semantics_v0" for row in source_rows)
    assert any(row["source_role"] == "feature_tensorization_audit_v0" for row in source_rows)
    assert any(row["source_role"] == "step12d_smoke_evidence" for row in source_rows)

    step12d = _base(
        "src/covalent_ext/real_covalent_pretrained_forward_loss_smoke.py"
    ).decode("utf-8")
    assert "CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX" in step12d
    assert (
        'UNKNOWN_ATOM_FEATURE_POLICY = '
        '"zero_vector_for_atoms_outside_checkpoint_10d_vocab"'
    ) in step12d
    assert "one_hot = torch.zeros" in step12d
    assert "one_hot[row_idx, feature_idx] = 1.0" in step12d
    constants = _base("constants.py").decode("utf-8")
    assert "'atom_decoder': ['C', 'N', 'O', 'S', 'B', 'Br', 'Cl', 'P', 'I', 'F']" in constants
    assert "'others': 10" in constants
    config = _base("configs/crossdock_fullatom_cond.yml").decode("utf-8")
    assert "dataset: 'crossdock'" in config
    assert "pocket_representation: 'full-atom'" in config
    assert "normalize_factors: [1, 4]" in config
    adapter = _base("src/covalent_ext/batch_adapter.py").decode("utf-8")
    assert "combined.mean(dim=0)" in adapter
    assert "ligand_coords - center[:, None, :]" in adapter
    lightning = _base("lightning_modules.py").decode("utf-8")
    assert "'one_hot': data['lig_one_hot'].to(self.device, FLOAT_TYPE)" in lightning
    dynamics = _base("equivariant_diffusion/dynamics.py").decode("utf-8")
    assert "h_atoms = self.atom_encoder(h_atoms)" in dynamics
    assert "h_residues = self.residue_encoder(h_residues)" in dynamics
    diffusion = _base("equivariant_diffusion/en_diffusion.py").decode("utf-8")
    assert "ligand['x'] = ligand['x'] / self.norm_values[0]" in diffusion
    assert "(ligand['one_hot'].float() - self.norm_biases[1])" in diffusion
    assert "t[mask]" in dynamics

    current = [
        row for row in registry_rows
        if row["feature_status"] == "current_model_input"
    ]
    assert len(current) == 10
    for row in current:
        assert row["producer_path"] and row["producer_symbol"]
        assert row["consumer_path"] and row["consumer_symbol"]
        assert row["runtime_dtype"] not in {"", "not_applicable"}
        assert row["tensor_rank"] not in {"", "not_applicable"}
        assert row["tensor_shape_or_width"] not in {"", "not_applicable"}
        assert row["normalization_or_scaling"] not in {"", "not_applicable"}
        assert row["evidence_status"] in {
            "explicitly_defined", "deterministically_derived"
        }
    categorical = {
        row["feature_id"]: row for row in current
        if "categorical_10d" in row["feature_id"]
    }
    assert set(categorical) == {
        "model_ligand_atom_categorical_10d",
        "model_pocket_atom_categorical_10d",
    }
    expected_vocab = "C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9"
    assert all(row["vocabulary_or_value_domain"] == expected_vocab for row in categorical.values())
    assert all(row["checkpoint_compatible_current_width"] == "10" for row in categorical.values())
    coordinates = [
        row for row in current if row["feature_id"] in {
            "model_ligand_coordinates", "model_pocket_coordinates"
        }
    ]
    assert len(coordinates) == 2
    assert all(row["coordinate_unit"] == "angstrom" for row in coordinates)
    assert all(
        row["coordinate_frame"]
        == "per-sample joint ligand+pocket unweighted atom-centroid centered"
        for row in coordinates
    )
    assert all(
        row["normalization_or_scaling"]
        == "center subtraction then divide by normalize_factors[0]=1"
        for row in coordinates
    )


def _independent_issue_checks(
    issue_payload: bytes,
    issue_rows: list[dict[str, str]],
) -> None:
    predecessor = _base(audit.PREDECESSOR_ISSUES)
    assert issue_payload.startswith(predecessor)
    assert len(issue_rows) == 32
    assert [row["issue_id"] for row in issue_rows[-2:]] == [
        "FINAL_TRAINING_FEATURE_SEMANTICS_UNRESOLVED",
        "UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED",
    ]
    assert issue_rows[-2]["successor_effective_status"] == "resolved"
    assert issue_rows[-1]["successor_effective_status"] == "open"
    assert [
        row["issue_id"] for row in issue_rows
        if row["successor_effective_status"] == "open"
    ] == ["UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED"]


def _independent_safety_checks() -> None:
    source = (ROOT / EXACT10[0]).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert "torch" not in imports
    assert "numpy" not in imports
    assert "requests" not in imports
    assert "rdkit" not in imports
    assert "gemmi" not in imports
    assert 'if name.startswith("data/raw/")' in source
    assert "torch.load(" not in source
    assert "np.load(" not in source


def check() -> dict[str, object]:
    assert _git("rev-parse", audit.BASE_COMMIT).decode().strip() == audit.BASE_COMMIT
    built_first = audit.build_covapie_final_training_feature_semantics_audit_artifacts_v1(ROOT)
    built_second = audit.build_covapie_final_training_feature_semantics_audit_artifacts_v1(ROOT)
    assert built_first == built_second
    assert set(built_first) == set(audit.OUTPUT_FILES)
    for name, payload in built_first.items():
        assert (ROOT / audit.OUTPUT_ROOT / name).read_bytes() == payload

    source_rows = _rows(built_first[audit.SOURCE_INVENTORY_FILE])
    registry_rows = _rows(built_first[audit.FEATURE_REGISTRY_FILE])
    unknown_rows = _rows(built_first[audit.UNKNOWN_POLICY_FILE])
    failure_rows = _rows(built_first[audit.FAILURE_MATRIX_FILE])
    issue_rows = _rows(built_first[audit.ISSUE_INVENTORY_FILE])
    manifest = json.loads(built_first[audit.MANIFEST_FILE])
    _independent_source_and_lineage_checks(source_rows, registry_rows)
    coverage = _independent_atom_coverage()
    assert coverage["protein_or_pocket_atom"][
        "unknown_or_unsupported_row_count"
    ] == 329
    assert coverage["ligand_atom"]["unknown_or_unsupported_row_count"] == 16
    manifest_coverage = {
        row["domain"]: {
            key: value for key, value in row.items()
            if key in coverage[row["domain"]]
        }
        for row in manifest["atom_coverage"]
    }
    assert manifest_coverage == coverage
    assert len(unknown_rows) == 40
    assert {row["domain"] for row in unknown_rows} == {
        "protein_or_pocket_atom", "ligand_atom"
    }
    zero_rows = [
        row for row in unknown_rows
        if row["case_id"] == "silent zero-vector fallback"
    ]
    assert len(zero_rows) == 2
    assert all(not _truth(row["fails_closed"]) for row in zero_rows)
    assert all(
        row["allowed_training_policy"] == "unknown_atom_policy_unresolved"
        for row in unknown_rows
    )
    assert len(failure_rows) == len(audit.FAILURE_CASES) == 34
    assert [row["failure_case"] for row in failure_rows] == list(audit.FAILURE_CASES)
    assert all(row["observed_outcome"] == "invalid" for row in failure_rows)
    assert all(_truth(row["fails_closed"]) and _truth(row["verified"]) for row in failure_rows)
    _independent_issue_checks(built_first[audit.ISSUE_INVENTORY_FILE], issue_rows)
    _independent_safety_checks()

    assert manifest["canonical_masks"] == [
        {"semantic_name": name, "display_alias": alias}
        for name, alias in audit.CANONICAL_MASKS
    ]
    assert manifest["canonical_mask_count"] == 5
    assert manifest["planned_covalent_model_modules"] == list(
        audit.PLANNED_COVALENT_MODEL_MODULES
    )
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["step12d_smoke_legality_verified"] is True
    assert manifest["step12d_final_feature_semantics_contract"] is False
    assert manifest["step12d_training_readiness_authority"] is False
    assert manifest["feature_semantics_audit_completed"] is True
    assert manifest["feature_semantics_known"] is False
    assert manifest["unknown_atom_feature_policy_resolved"] is False
    assert manifest["checkpoint_compatibility_preserved"] is True
    assert manifest["ready_for_tensor_label_loss_mask_contract_design"] is False
    assert manifest["ready_for_tensorization"] is False
    assert manifest["ready_for_model_integration"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["tensorization_used"] is False
    assert manifest["checkpoint_access"] is False
    assert manifest["model_changed"] is False
    assert manifest["dataloader_changed"] is False
    assert manifest["training_used"] is False
    assert manifest["raw_read"] is False and manifest["raw_write"] is False
    for name, expected in manifest["evidence_sha256"].items():
        assert _sha(built_first[name]) == expected
    return manifest


def _render(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return str(value)


def main() -> None:
    manifest = check()
    keys = (
        "audit_outcome",
        "discovered_feature_count",
        "current_model_input_feature_count",
        "metadata_only_feature_count",
        "future_not_integrated_feature_count",
        "explicit_semantics_count",
        "deterministically_derived_semantics_count",
        "ambiguous_semantics_count",
        "missing_semantics_count",
        "contradictory_semantics_count",
        "protein_unknown_atom_policy",
        "ligand_unknown_atom_policy",
        "protein_unknown_atom_policy_resolved",
        "ligand_unknown_atom_policy_resolved",
        "feature_semantics_audit_completed",
        "feature_semantics_known",
        "unknown_atom_feature_policy_resolved",
        "checkpoint_compatibility_preserved",
        "ready_for_tensor_label_loss_mask_contract_design",
        "ready_for_tensorization",
        "ready_for_model_integration",
        "ready_for_training",
        "effective_open_issue_count",
        "effective_open_issues",
        "recommended_next_step",
    )
    for key in keys:
        print(f"{key}={_render(manifest[key])}")


if __name__ == "__main__":
    main()
