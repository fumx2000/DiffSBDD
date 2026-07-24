#!/usr/bin/env python3
"""Independent fail-closed checker for the revised ADMIT_015 Exact10."""
from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = "f54c0efabfb695653c9e55b3a53bda8cf200f353"
PARENT = "ce98b5542eea5ab4f81c0fc93b10147df5568735"
TREE = "64ae9c2dd24ecea627102b74d9cb2f72869336ca"
SUBJECT = "add CovaPIE unified dispatch runtime with ADMIT_001 to ADMIT_014 v1"
STAGE = "audit_covapie_admit_015_formal_evaluator_interface_preconditions_v1"
REVISION = (
    "revise_covapie_admit_015_non_destructive_failure_"
    "quarantine_and_recursive_lifecycle_v3"
)
PRODUCTION = Path(
    "src/covalent_ext/covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_preconditions_audit.py"
)
PRODUCTION_SHA256 = "18894150a91040b3a4c52a5f7aaedc279f6f31ededed82de1e704ec086e0cc0f"
PRODUCTION_AST_SHA256 = "c057b9ca7a955adcadc7b4f67658a84d0d2a7270e6dd60ded368fa90f3dac893"
CHECKER = Path(
    "scripts/check_covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_preconditions_audit_v1.py"
)
TEST = Path(
    "tests/test_covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_preconditions_audit_v1.py"
)
SUMMARY = Path(
    "docs/covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_preconditions_audit_v1_summary.md"
)
DERIVED = Path("data/derived/covalent_small") / (
    "covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_preconditions_audit_v1"
)
PRECONDITION = "covapie_admit_015_formal_evaluator_interface_precondition_inventory.csv"
RESPONSIBILITY = (
    "covapie_admit_015_authorization_evidence_and_routing_responsibility_matrix.csv"
)
SOURCE_AUDIT = "covapie_admit_015_source_boundary_audit.csv"
SAFETY = "covapie_admit_015_safety_training_boundary_audit.csv"
ISSUE = "covapie_admit_015_issue_readiness_inventory.csv"
MANIFEST = "covapie_admit_015_formal_evaluator_interface_preconditions_manifest.json"
FILES = (PRECONDITION, RESPONSIBILITY, SOURCE_AUDIT, SAFETY, ISSUE, MANIFEST)
FROZEN_OUTPUT_SHA256 = {
    PRECONDITION: "c52287ac5a435e58a400be0e33e17c1096b7b0d3b2671be0398a6be03e409839",
    RESPONSIBILITY: "9713eb3ebfa474488269d17f9efff39e953405dc1d9642074a203e4837585e95",
    SOURCE_AUDIT: "d34374760edf3432042588eb1f258ab75e75290d8a75be579f6056352ef5cd89",
    SAFETY: "967f5d22503b552ae2aaf34693799e789cbc38209d80ad1f4dd0e42bfd87587d",
    ISSUE: "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec",
    MANIFEST: "7f64389a018c9bc1170ffeb94d1f393aefc27f67edef1d85143659f43dc8d729",
}
EXACT10 = (PRODUCTION, CHECKER, TEST, SUMMARY, *(DERIVED / item for item in FILES))

PRE_COLUMNS = (
    "precondition_order", "precondition_id", "precondition_group",
    "precondition_subject", "required_state", "observed_state",
    "completion_status", "implementation_blocking", "evidence_paths",
    "evidence_sha256", "resolution_or_gap", "recommended_owner",
)
RESP_COLUMNS = (
    "matrix_order", "responsibility_group", "responsibility_item",
    "candidate_authority", "committed_precedent", "admit_015_contract_status",
    "allowed_source", "forbidden_sources", "type_semantics",
    "coercion_policy", "coexistence_boundary", "audit_passed",
)
SOURCE_COLUMNS = (
    "source_order", "source_relative_path", "expected_sha256",
    "base_tree_mode", "base_tree_blob", "index_mode", "index_blob",
    "index_stage", "base_tree_sha256", "filesystem_sha256", "tracked",
    "regular_file", "non_symlink", "pinned_read",
    "post_read_identity_verified", "final_leaf_identity_verified",
    "source_verified",
)
SAFETY_COLUMNS = (
    "audit_order", "audit_item", "required_state", "observed_state",
    "audit_passed", "blocking_reason",
)

EXACT23: tuple[tuple[str, str], ...] = (
    ("src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_design_gate.py", "79ecb3fb1084ddc161d1bec1a7db664ffbeda71952e31e4233317ecd487905d6"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv", "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_schema_contract.csv", "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_safety_audit.csv", "388869caf582bdf624d0016cae385dc2268f6cc05f54ecc9bf140608bbd3b208"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_design_gate_manifest.json", "085cb2f2a6bfe9bebe9e503dd10aa0b4d6f9ad754ff99539b1bafb33c78b5444"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv", "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_rule_executability_matrix.csv", "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_implementation_precondition_manifest.json", "2304b5754d8052b4b186981a98c12f259608a3492947e069c2afab84084a0d52"),
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014.py", "c5f5cfc57155f34ee2435228b3bf53ae8d1f6d81c32e097c43668c0b272fd1a2"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1/covapie_admit_001_to_014_runtime_manifest.json", "bf7bbe3c2158f661c6e71835bf603af76ffbb315d4ef377c9f72da246619ba40"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1/covapie_admit_001_to_014_runtime_issue_readiness_inventory.csv", "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_rule_logic_interface_preconditions_audit_v1/covapie_admit_014_formal_evaluator_preconditions_manifest.json", "b9582357f392a6aa1af68012a1469c886b2de4b5af8196cddad56f94625e4b61"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_download_authorization_contract_v1/covapie_admit_014_download_authorization_truth_matrix.csv", "e4f39f5178b91906639670f5c1ddb1c02b40c802de9ce386aee2a6b6d49f8482"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_download_authorization_contract_v1/covapie_admit_014_download_authorization_value_and_trust_contract.csv", "b22f02efdd53dce995730a05cc5c12ffa659c2d98b345afc663b118cc104752d"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_download_authorization_contract_v1/covapie_admit_014_download_authorization_contract_manifest.json", "9c54c9d6cb11776b04938d9be048699041bfc4020dca4c00425faadaaaa5d4d2"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_formal_evaluator_interface_contract_v1/covapie_admit_014_formal_evaluator_interface_contract_manifest.json", "217490ef69526486b51117e4900d0669b4de466a023023ecb56ebdf0822fb731"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_rule_logic_interface_v1/covapie_admit_014_rule_logic_interface_manifest.json", "f1266a2a471ddac3a0966951ff681b19ebd7d2725ff8242942a9365f92f7e056"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_unified_adapter_contract_v1/covapie_admit_014_unified_adapter_contract_manifest.json", "fbcca891692e4b88d2da854425bef9ce38d1eced97df1c0ca826edad95357de0"),
    ("data/derived/covalent_small/covapie_final_dataset_qa_gate_v1/covapie_final_dataset_qa_v1_safety_training_boundary_audit.csv", "8ea6a53d04456443014ba250a0cfacf4983e39d2138d7035ad188dc1dcceebe5"),
    ("data/derived/covalent_small/covapie_final_dataset_qa_gate_v1/covapie_final_dataset_qa_v1_manifest.json", "4f7c884379f926af52101f40a7870b243f0309af3b1637dc65c8c0691acf9f35"),
    ("data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0/covapie_feature_semantics_audit_gate_manifest.json", "a625335dd670ceb53f1515237a676c25d156b510eb80113ea8c4073e1ae1879d"),
    ("data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0/covapie_feature_semantics_training_blockers.csv", "99af8f844b43ee6731f20b25ea4abc968e5eb7a12923f3797b3b2c6384d019d8"),
    ("data/derived/covalent_small/pretrained_masked_loss_smoke_v0/pretrained_masked_loss_smoke_manifest.json", "f2b3165d70c046f27defbe821afcc5294ff5cdf0037595cd5c42066ab27ea08b"),
)

PATHS = {name: Path(path) for name, path in (
    ("DESIGN_RULES", EXACT23[1][0]),
    ("PRE_CONTEXT", EXACT23[5][0]),
    ("PRE_RULES", EXACT23[6][0]),
    ("PRE_MANIFEST", EXACT23[7][0]),
    ("RUNTIME_PRODUCTION", EXACT23[8][0]),
    ("RUNTIME_MANIFEST", EXACT23[9][0]),
    ("RUNTIME_ISSUES", EXACT23[10][0]),
    ("AUTH014_TRUTH", EXACT23[12][0]),
    ("AUTH014_TRUST", EXACT23[13][0]),
    ("AUTH014_MANIFEST", EXACT23[14][0]),
    ("QA_MANIFEST", EXACT23[19][0]),
    ("FEATURE_MANIFEST", EXACT23[20][0]),
    ("FEATURE_BLOCKERS", EXACT23[21][0]),
    ("STEP12D_MANIFEST", EXACT23[22][0]),
)}

TRUE_KEYS = (
    "admit_015_rule_identity_verified",
    "admit_015_current_fail_closed_state_verified",
    "admit_015_known_not_registered_state_verified",
    "admit_015_authorization_precedent_audited",
    "admit_015_training_permission_responsibility_audited",
    "admit_015_formal_evaluator_interface_preconditions_audited",
    "admit_014_admit_015_isolation_audited",
    "feature_semantics_audit_required_before_training",
    "ready_for_admit_015_training_authorization_contract_design",
)
FALSE_KEYS = (
    "admit_015_training_authorization_contract_frozen",
    "admit_015_formal_evaluator_interface_contract_frozen",
    "evaluate_admit_015_implemented", "admit_015_result_type_implemented",
    "admit_015_standalone_evaluator_implemented",
    "admit_015_unified_adapter_contract_frozen",
    "admit_015_unified_adapter_implemented",
    "admit_015_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_015_implemented",
    "mandatory_training_authorization_enforcement_implemented",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "feature_semantics_audit_completed", "real_training_ready",
    "ready_for_training", "step12d_is_final_training_feature_contract",
)
READINESS_KEYS = TRUE_KEYS + FALSE_KEYS

Identity = tuple[int, int, int, int, int, int]


@dataclass(frozen=True)
class AttestedSource:
    path: Path
    content: bytes
    sha256: str
    mode: str
    blob: str


def _identity(item: os.stat_result) -> Identity:
    return (
        item.st_dev, item.st_ino, item.st_mode, item.st_size,
        item.st_mtime_ns, item.st_ctime_ns,
    )


def _git(args: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=text, check=False
    )


def _safe_relative(path: Path) -> bool:
    return (
        not path.is_absolute() and bool(path.parts) and ".." not in path.parts
        and path.parts[:2] != ("data", "raw")
        and path.parts[0] != "checkpoints"
        and DERIVED.as_posix() not in path.as_posix()
    )


def _pinned_read_relative(
    root: Path, path: Path, *, allow_candidate_derived: bool = False
) -> bytes:
    safe = _safe_relative(path) or (
        allow_candidate_derived
        and not path.is_absolute()
        and bool(path.parts)
        and ".." not in path.parts
        and path.parts[:2] != ("data", "raw")
        and path.parts[0] != "checkpoints"
        and DERIVED in path.parents
    )
    if not safe:
        raise AssertionError(f"unsafe pinned path: {path}")
    dflags = (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    )
    fflags = (
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    root_stat = os.lstat(root)
    root_id = _identity(root_stat)
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        raise AssertionError("unsafe pinned root")
    held: list[tuple[int, Identity, int | None, str | None]] = []
    leaf_fd = -1
    root_fd = os.open(root, dflags)
    if _identity(os.fstat(root_fd)) != root_id:
        os.close(root_fd)
        raise AssertionError("pinned root stat/open race")
    held.append((root_fd, root_id, None, None))
    try:
        current_fd = root_fd
        for part in path.parts[:-1]:
            lexical = os.stat(part, dir_fd=current_fd, follow_symlinks=False)
            lexical_id = _identity(lexical)
            if stat.S_ISLNK(lexical.st_mode) or not stat.S_ISDIR(lexical.st_mode):
                raise AssertionError(f"unsafe pinned parent: {path}")
            next_fd = os.open(part, dflags, dir_fd=current_fd)
            if _identity(os.fstat(next_fd)) != lexical_id:
                os.close(next_fd)
                raise AssertionError(f"pinned parent race: {path}")
            held.append((next_fd, lexical_id, current_fd, part))
            current_fd = next_fd
        lexical = os.stat(path.name, dir_fd=current_fd, follow_symlinks=False)
        leaf_id = _identity(lexical)
        if stat.S_ISLNK(lexical.st_mode) or not stat.S_ISREG(lexical.st_mode):
            raise AssertionError(f"unsafe pinned leaf: {path}")
        leaf_fd = os.open(path.name, fflags, dir_fd=current_fd)
        if _identity(os.fstat(leaf_fd)) != leaf_id:
            raise AssertionError(f"pinned leaf stat/open race: {path}")
        chunks = []
        while True:
            chunk = os.read(leaf_fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        if (
            _identity(os.fstat(leaf_fd)) != leaf_id
            or _identity(
                os.stat(path.name, dir_fd=current_fd, follow_symlinks=False)
            )
            != leaf_id
        ):
            raise AssertionError(f"pinned leaf post-read replacement: {path}")
        for fd, expected, parent_fd, name in held:
            if _identity(os.fstat(fd)) != expected:
                raise AssertionError(f"pinned parent FD drift: {path}")
            if parent_fd is not None and name is not None:
                if _identity(
                    os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
                ) != expected:
                    raise AssertionError(f"pinned parent lexical drift: {path}")
        if (
            _identity(os.fstat(root_fd)) != root_id
            or _identity(os.lstat(root)) != root_id
            or _identity(os.fstat(leaf_fd)) != leaf_id
            or _identity(
                os.stat(path.name, dir_fd=current_fd, follow_symlinks=False)
            )
            != leaf_id
        ):
            raise AssertionError(f"pinned final binding drift: {path}")
        return b"".join(chunks)
    finally:
        if leaf_fd >= 0:
            os.close(leaf_fd)
        for fd, _, _, _ in reversed(held):
            os.close(fd)


def attest_exact23() -> tuple[AttestedSource, ...]:
    identity = _git(["show", "-s", "--format=%H%n%P%n%T%n%s", BASE])
    ancestor = _git(["merge-base", "--is-ancestor", BASE, "HEAD"])
    if identity.returncode or ancestor.returncode or identity.stdout.splitlines() != [
        BASE, PARENT, TREE, SUBJECT
    ]:
        raise AssertionError("base identity/ancestry mismatch")
    attested = []
    for path_text, frozen_sha in EXACT23:
        path = Path(path_text)
        if not _safe_relative(path):
            raise AssertionError(f"unsafe Exact23 path: {path}")
        index = _git(["ls-files", "--stage", "--", path_text])
        tree = _git(["ls-tree", BASE, "--", path_text])
        ih, isep, ip = index.stdout.partition("\t")
        th, tsep, tp = tree.stdout.partition("\t")
        iv, tv = ih.split(), th.split()
        if (
            index.returncode or tree.returncode or not isep or not tsep
            or ip.strip() != path_text or tp.strip() != path_text
            or len(iv) != 3 or len(tv) != 3 or iv[2] != "0"
            or iv[0] not in {"100644", "100755"} or tv[0] != iv[0]
            or tv[1] != "blob" or tv[2] != iv[1]
            or len(iv[1]) != 40
            or any(char not in "0123456789abcdef" for char in iv[1])
        ):
            raise AssertionError(f"Exact23 base/index identity mismatch: {path}")
        content = _pinned_read_relative(ROOT, path)
        base = _git(["show", f"{BASE}:{path_text}"], text=False)
        digest = hashlib.sha256(content).hexdigest()
        if base.returncode or base.stdout != content or digest != frozen_sha:
            raise AssertionError(f"Exact23 frozen content mismatch: {path}")
        attested.append(AttestedSource(path, content, digest, iv[0], iv[1]))
    if tuple((item.path.as_posix(), item.sha256) for item in attested) != EXACT23:
        raise AssertionError("Exact23 order drift")
    return tuple(attested)


def _source_map(sources: tuple[AttestedSource, ...]) -> dict[Path, AttestedSource]:
    return {source.path: source for source in sources}


def _precondition_specs() -> tuple[tuple[str, str, str, str, str, bool, str, str], ...]:
    c = "complete"
    o = "incomplete"
    p = "supported_but_admit015_contract_not_frozen"
    return (
        ("rule_identity", "canonical ADMIT_015 registry row", "exact canonical identity", "verified committed Step14AT row", c, False, "identity frozen", "ADMIT_015 contract owner"),
        ("rule_identity", "failure severity and reason", "blocking|training_not_authorized", "verified committed registry fields", c, False, "current identity frozen", "ADMIT_015 contract owner"),
        ("rule_identity", "current-step no-I/O flags", "network=false|raw=false", "verified committed registry fields", c, False, "identity frozen", "ADMIT_015 contract owner"),
        ("current_runtime_state", "registration state", "known but not registered", "Exact14 manifest verified", c, False, "preserve until implementation", "runtime owner"),
        ("current_runtime_state", "callable and adapter state", "false|false", "Exact14 sets verified", c, False, "preserve fail closed", "runtime owner"),
        ("current_runtime_state", "open coverage", "ADMIT_015 only", "Exact30 coverage row verified", c, False, "zero transition in this audit", "runtime owner"),
        ("authorization_envelope_precedent", "candidate envelope name", "stage_authorization_context", "ADMIT_014 committed precedent", p, True, "precedent only; ADMIT_015 contract open", "authorization contract owner"),
        ("authorization_envelope_precedent", "candidate target key coexistence", "current_stage_training_authorized", "Step14AU-A committed coexistence name", p, True, "name precedent is not final contract", "authorization contract owner"),
        ("authorization_envelope_precedent", "trusted producer", "trusted_future_stage_orchestrator", "ADMIT_014 committed precedent", p, True, "must be independently frozen for ADMIT_015", "authorization contract owner"),
        ("training_authorization_responsibility", "unique recommended authority path", "stage_authorization_context.current_stage_training_authorized", "supported by committed structural precedent", p, True, "formal authorization contract required", "authorization contract owner"),
        ("training_authorization_responsibility", "omission behavior", "omission must fail closed", "ADMIT_014 fail-closed precedent", p, True, "ADMIT_015 reason not frozen", "authorization contract owner"),
        ("training_authorization_responsibility", "replay behavior", "no cross-invocation replay", "ADMIT_014 invocation-local precedent", p, True, "ADMIT_015 freshness contract open", "authorization contract owner"),
        ("ADMIT_014_ADMIT_015_isolation", "download true does not authorize training", "strictly independent", "audited required isolation", c, False, "isolation rule frozen", "authorization contract owner"),
        ("ADMIT_014_ADMIT_015_isolation", "training true does not authorize download", "strictly independent", "audited required isolation", c, False, "isolation rule frozen", "authorization contract owner"),
        ("ADMIT_014_ADMIT_015_isolation", "no alias/fallback/OR/AND", "all forbidden", "audited required isolation", c, False, "combined semantics undefined", "authorization contract owner"),
        ("input_and_type_semantics", "candidate value type", "exact builtin bool", "ADMIT_014 precedent only", p, True, "ADMIT_015 type contract open", "authorization contract owner"),
        ("input_and_type_semantics", "coercion", "no coercion", "ADMIT_014 precedent only", p, True, "ADMIT_015 contract must freeze it", "authorization contract owner"),
        ("input_and_type_semantics", "missing/invalid precedence", "fail closed with frozen precedence", "not frozen for ADMIT_015", o, True, "precedence unresolved", "formal interface owner"),
        ("formal_interface_design_inputs", "final evaluator signature", "exact signature", "not frozen in preconditions audit", o, True, "candidate design question only", "formal interface owner"),
        ("formal_interface_design_inputs", "independent oracle", "designed independently", "not designed", o, True, "oracle design unresolved", "formal interface owner"),
        ("formal_interface_design_inputs", "multi-invalid precedence", "exact deterministic order", "not frozen", o, True, "interface contract required", "formal interface owner"),
        ("result_schema_design_inputs", "result class name", "exact type name", "not frozen in preconditions audit", o, True, "candidate design question only", "formal interface owner"),
        ("result_schema_design_inputs", "result field count and order", "exact closed schema", "not frozen", o, True, "result contract required", "formal interface owner"),
        ("result_schema_design_inputs", "normalized projection", "exact representation", "not frozen", o, True, "projection contract required", "adapter contract owner"),
        ("reason_vocabulary_design_inputs", "outcome vocabulary", "closed exact vocabulary", "not frozen", o, True, "formal contract required", "formal interface owner"),
        ("reason_vocabulary_design_inputs", "reason vocabulary", "closed exact vocabulary", "not frozen", o, True, "formal contract required", "formal interface owner"),
        ("reason_vocabulary_design_inputs", "missing/type/false reasons", "exact precedence and strings", "not frozen", o, True, "authorization and interface contracts required", "formal interface owner"),
        ("purity_and_IO_boundary", "evaluator filesystem access", "none", "forbidden by audited boundary", c, False, "retain pure in-memory boundary", "formal interface owner"),
        ("purity_and_IO_boundary", "evaluator network/provider access", "none", "forbidden by audited boundary", c, False, "retain pure in-memory boundary", "formal interface owner"),
        ("purity_and_IO_boundary", "environment/config/checkpoint authority", "forbidden", "audited forbidden sources", c, False, "never authorize from these sources", "authorization contract owner"),
        ("adapter_and_runtime_boundary", "unified adapter contract", "frozen after evaluator contract", "not designed or frozen", o, True, "future separate stage", "adapter contract owner"),
        ("adapter_and_runtime_boundary", "adapter/handler implementation", "implemented after contract", "not implemented", o, True, "future separate stage", "runtime owner"),
        ("adapter_and_runtime_boundary", "registry/Exact15 runtime", "implemented after adapter", "not implemented", o, True, "future separate stage", "runtime owner"),
        ("mandatory_enforcement_boundary", "training authorization enforcement API", "exact mandatory guard", "not designed or implemented", o, True, "separate enforcement contract required", "training orchestration owner"),
        ("mandatory_enforcement_boundary", "combined permission semantics", "explicitly defined if needed", "undefined", o, True, "must not infer AND/OR", "training orchestration owner"),
        ("mandatory_enforcement_boundary", "cross-rule aggregation", "implemented only after contract", "not implemented", o, True, "open issue retained", "runtime owner"),
        ("feature_semantics_boundary", "feature-semantics audit required", "true before training", "verified committed requirement", c, False, "requirement frozen", "feature semantics owner"),
        ("feature_semantics_boundary", "historical UNKNOWN_ATOM policy", "formally audited/resolved", "not finalized for training", o, True, "historical blocker remains", "feature semantics owner"),
        ("feature_semantics_boundary", "Step12D scope", "smoke legality only", "verified; not final training contract", c, False, "do not promote smoke evidence", "feature semantics owner"),
        ("training_execution_boundary", "current permission", "false", "false", c, False, "current fail-closed state", "training orchestration owner"),
        ("training_execution_boundary", "authorized execution count", "0", "0", c, False, "no training execution", "training orchestration owner"),
        ("training_execution_boundary", "real training readiness", "false until all gates", "false", o, True, "authorization and feature audit incomplete", "training orchestration owner"),
        ("issue_and_readiness_continuity", "Exact30 issue inventory", "byte-identical", "inherited without transition", c, False, "coverage remains ADMIT_015", "runtime owner"),
        ("issue_and_readiness_continuity", "coverage issue status", "open", "open", c, False, "do not claim resolution", "runtime owner"),
        ("issue_and_readiness_continuity", "next authorized design step", "design_covapie_admit_015_training_authorization_contract_v1", "preconditions support contract design only", c, False, "stop after audit", "authorization contract owner"),
    )


def _evidence_paths() -> tuple[tuple[Path, ...], ...]:
    p = PATHS
    return (
        (p["DESIGN_RULES"],), (p["DESIGN_RULES"],), (p["DESIGN_RULES"],),
        (p["RUNTIME_MANIFEST"],), (p["RUNTIME_MANIFEST"],),
        (p["RUNTIME_ISSUES"], p["RUNTIME_MANIFEST"]),
        (p["AUTH014_TRUST"], p["RUNTIME_MANIFEST"]),
        (p["PRE_CONTEXT"], p["RUNTIME_MANIFEST"]),
        (p["AUTH014_TRUST"], p["RUNTIME_MANIFEST"]),
        (p["PRE_CONTEXT"], p["AUTH014_TRUST"], p["RUNTIME_MANIFEST"]),
        (p["AUTH014_TRUTH"], p["RUNTIME_MANIFEST"]),
        (p["AUTH014_TRUST"], p["RUNTIME_MANIFEST"]),
        (p["RUNTIME_PRODUCTION"], p["RUNTIME_MANIFEST"], p["PRE_CONTEXT"]),
        (p["PRE_CONTEXT"], p["RUNTIME_MANIFEST"]),
        (p["PRE_CONTEXT"], p["RUNTIME_MANIFEST"]),
        (p["AUTH014_TRUST"], p["RUNTIME_MANIFEST"]),
        (p["AUTH014_TRUST"], p["RUNTIME_MANIFEST"]),
        (p["AUTH014_MANIFEST"], p["RUNTIME_MANIFEST"]),
        *((p["RUNTIME_MANIFEST"],) for _ in range(8)),
        (p["AUTH014_MANIFEST"], p["RUNTIME_MANIFEST"]),
        (p["PRE_RULES"], p["PRE_MANIFEST"]),
        (p["PRE_RULES"], p["PRE_MANIFEST"]),
        (p["AUTH014_TRUST"], p["RUNTIME_MANIFEST"]),
        *((p["RUNTIME_MANIFEST"],) for _ in range(5)),
        (p["RUNTIME_ISSUES"], p["RUNTIME_MANIFEST"]),
        (p["QA_MANIFEST"], p["FEATURE_MANIFEST"]),
        (p["QA_MANIFEST"], p["FEATURE_MANIFEST"], p["FEATURE_BLOCKERS"]),
        (p["FEATURE_MANIFEST"], p["STEP12D_MANIFEST"]),
        (p["DESIGN_RULES"], p["RUNTIME_MANIFEST"]),
        (p["RUNTIME_MANIFEST"],),
        (p["QA_MANIFEST"], p["FEATURE_MANIFEST"], p["RUNTIME_MANIFEST"]),
        (p["RUNTIME_ISSUES"],), (p["RUNTIME_ISSUES"],),
        (p["RUNTIME_MANIFEST"],),
    )


def expected_preconditions(
    sources: tuple[AttestedSource, ...],
) -> list[dict[str, str]]:
    by_path = _source_map(sources)
    specs = _precondition_specs()
    evidence = _evidence_paths()
    if len(specs) != len(evidence) or len(specs) != 45:
        raise AssertionError("checker Exact45 cardinality drift")
    rows = []
    for order, (spec, paths) in enumerate(zip(specs, evidence), 1):
        group, subject, required, observed, status, blocking, gap, owner = spec
        if not paths or len(paths) != len(set(paths)):
            raise AssertionError("checker row-specific evidence drift")
        rows.append(dict(zip(PRE_COLUMNS, (
            str(order), f"PRE_{order:03d}", group, subject, required, observed,
            status, str(blocking).lower(),
            "|".join(path.as_posix() for path in paths),
            "|".join(by_path[path].sha256 for path in paths),
            gap, owner,
        ))))
    return rows


def expected_responsibilities() -> list[dict[str, str]]:
    forbidden = (
        "candidate_record|batch_context|evaluation_context|download_result_context|"
        "provider_result|environment_variable|filesystem_marker|artifact_sha|"
        "git_commit_sha|checkpoint_metadata|training_config|command_line_flag|"
        "model_state|dataloader_state"
    )
    specs = (
        ("authority", "authoritative envelope", "stage_authorization_context", "ADMIT_014 verified committed precedent", "supported_but_admit015_contract_not_frozen", "stage_authorization_context", forbidden, "exact builtin bool", "no coercion", "download and training keys isolated"),
        ("authority", "training target item", "current_stage_training_authorized", "Step14AU-A coexistence precedent", "supported_but_admit015_contract_not_frozen", "stage_authorization_context.current_stage_training_authorized", forbidden, "exact builtin bool", "no coercion", "never consume download key"),
        ("authority", "producer", "trusted_future_stage_orchestrator", "ADMIT_014 verified committed precedent", "supported_but_admit015_contract_not_frozen", "fresh trusted invocation input", forbidden, "exact builtin bool", "no coercion", "producer must construct keys independently"),
        ("freshness", "lifetime", "invocation-local", "ADMIT_014 verified committed precedent", "supported_but_admit015_contract_not_frozen", "current invocation", "cache|artifact|raw replay", "exact builtin bool", "no coercion", "no cross-invocation replay"),
        ("default", "omission", "omission must fail closed", "ADMIT_014 fail-closed precedent", "supported_but_admit015_contract_not_frozen", "target key only", "fallback to download key|defaults", "exact builtin bool", "no coercion", "missing training key cannot read download key"),
        ("isolation", "download True", "no training authority", "Exact14 runtime consumes download key only; ADMIT_015 is known-not-registered; Step14AU-A freezes coexistence names only", "supported_but_admit015_contract_not_frozen", "download key for ADMIT_014 only", "training authority", "exact builtin bool", "no coercion", "does not imply training; future ADMIT_015 contract not frozen"),
        ("isolation", "training True", "no download authority", "Exact14 runtime ignores training key; ADMIT_015 is known-not-registered; Step14AU-A freezes coexistence names only", "supported_but_admit015_contract_not_frozen", "training key is a candidate for future ADMIT_015 only", "download authority", "exact builtin bool", "no coercion", "does not imply download; future ADMIT_015 contract not frozen"),
        ("isolation", "fallback", "forbidden", "audit boundary", "forbidden", "none", "either key as substitute", "n/a", "forbidden", "no fallback"),
        ("isolation", "alias", "forbidden", "audit boundary", "forbidden", "none", "key aliasing", "n/a", "forbidden", "no alias"),
        ("isolation", "OR", "forbidden", "audit boundary", "forbidden", "none", "download OR training", "n/a", "forbidden", "combined semantics undefined"),
        ("isolation", "AND as single permission", "forbidden", "audit boundary", "forbidden", "none", "download AND training", "n/a", "forbidden", "combined semantics undefined"),
        ("formal_design", "evaluator signature", "candidate design question", "none", "not_frozen_in_preconditions_audit", "not selected", "all implicit sources", "not frozen", "not frozen", "future contract"),
        ("formal_design", "result class and fields", "candidate design question", "none", "not_frozen_in_preconditions_audit", "not selected", "all implicit sources", "not frozen", "not frozen", "future contract"),
        ("formal_design", "reason vocabulary", "candidate design question", "none", "not_frozen_in_preconditions_audit", "not selected", "all implicit sources", "not frozen", "not frozen", "future contract"),
        ("runtime", "adapter ID and handler", "candidate design question", "none", "not_frozen_in_preconditions_audit", "not selected", "current runtime", "not frozen", "not frozen", "future contract"),
        ("enforcement", "mandatory training guard", "future separate responsibility", "not implemented", "unresolved", "none now", forbidden, "not frozen", "not frozen", "must precede training"),
    )
    return [
        dict(zip(RESP_COLUMNS, (str(order), *spec, "true")))
        for order, spec in enumerate(specs, 1)
    ]


def expected_safety() -> list[dict[str, str]]:
    specs = (
        ("ADMIT_015 evaluator", "absent", "absent", ""),
        ("ADMIT_015 result type", "absent", "absent", ""),
        ("ADMIT_015 adapter/handler", "absent", "absent", ""),
        ("ADMIT_015 registry/Exact15 runtime", "absent", "absent", ""),
        ("mandatory training enforcement", "absent", "absent", ""),
        ("current training permission", "false", "false", "training_not_authorized"),
        ("authorized training execution count", "0", "0", "training_not_authorized"),
        ("feature semantics audit completed", "false", "false", "feature_semantics_audit_required"),
        ("Step12D final contract", "false", "false", "step12d_smoke_only"),
        ("ready for training", "false", "false", "training_not_authorized"),
        ("dataloader instantiated", "false", "false", ""),
        ("checkpoint loaded", "false", "false", ""),
        ("model forward/loss/backward", "false", "false", ""),
        ("optimizer/parameter update", "false", "false", ""),
        ("provider/network/download", "false", "false", ""),
        ("raw structure read/write", "false", "false", ""),
        ("canonical mask count", "5", "5", ""),
        ("canonical mask B3", "scaffold_only / B3 present", "present", ""),
        ("combined verdict", "not implemented", "not implemented", ""),
        ("cross-rule aggregation", "not implemented", "not implemented", ""),
    )
    return [
        dict(zip(SAFETY_COLUMNS, (
            str(order), item, required, observed, "true", reason,
        )))
        for order, (item, required, observed, reason) in enumerate(specs, 1)
    ]


def expected_source_rows(
    sources: tuple[AttestedSource, ...],
) -> list[dict[str, str]]:
    return [
        dict(zip(SOURCE_COLUMNS, (
            str(order), source.path.as_posix(), source.sha256, source.mode,
            source.blob, source.mode, source.blob, "0", source.sha256,
            source.sha256, "true", "true", "true", "true", "true", "true",
            "true",
        )))
        for order, source in enumerate(sources, 1)
    ]


def _parse_csv_exact(
    data: bytes, columns: tuple[str, ...],
) -> list[dict[str, str]]:
    try:
        table = list(csv.reader(io.StringIO(data.decode(), newline="")))
    except (UnicodeDecodeError, csv.Error) as error:
        raise AssertionError("invalid CSV encoding/shape") from error
    if not table or tuple(table[0]) != columns:
        raise AssertionError("CSV exact schema mismatch")
    rows = []
    for values in table[1:]:
        if len(values) != len(columns):
            raise AssertionError("CSV row width mismatch")
        rows.append(dict(zip(columns, values)))
    return rows


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _duplicate_rejecting_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise AssertionError(f"duplicate or invalid JSON key: {key!r}")
        result[key] = value
    return result


TOP_LEVEL_KEYS = (
    "project", "stage", "audit_revision", "base_commit", "base_parent",
    "base_tree", "base_subject", "canonical_evidence_python_implementation",
    "canonical_evidence_python_version",
    "ast_attestation_cross_python_version_portable",
    "noncanonical_python_policy", "python_runtime_migration_policy",
    "admission_rule_id", "admission_rule_name", "current_evidence_source",
    "current_required_status", "current_blocking_reason", "current_permission",
    "authorized_admit_015_training_execution_count",
    "current_registration_state", "current_callable_discovered_state",
    "current_adapter_ready_state", "current_runtime_coverage_open",
    "source_count", "source_boundary_schema", "source_boundary",
    "precondition_schema", "precondition_count", "precondition_complete_ids",
    "precondition_incomplete_ids", "precondition_blocking_ids",
    "responsibility_schema", "responsibility_count",
    "candidate_authoritative_envelope", "candidate_target_item",
    "admit_014_coexistence_item", "candidate_producer",
    "candidate_value_type", "candidate_coercion_policy", "candidate_lifetime",
    "candidate_default_policy", "candidate_replay_policy",
    "candidate_path_status", "download_training_key_fallback",
    "download_training_key_alias", "download_training_key_or",
    "download_training_key_and_as_single_permission",
    "combined_permission_semantics_defined",
    "forbidden_training_authority_sources", "formal_interface_not_frozen",
    "issue_schema", "issue_row_count", "issue_transition_count",
    "issue_inventory_source_sha256",
    "issue_inventory_byte_identical_to_exact14", "issue_coverage",
    "readiness", "canonical_masks", "canonical_mask_count",
    "canonical_mask_long_names_are_authoritative",
    "feature_semantics_audit_completed",
    "feature_semantics_audit_required_before_training",
    "historical_unknown_atom_feature_policy_resolved",
    "historical_feature_semantics_known", "step12d_status", "safety",
    "safety_schema", "safety_count", "output_files", "output_file_count",
    "output_sha256", "output_sha256_excludes_manifest_self_hash",
    "materialization", "recommended_next_step", "all_checks_passed",
    "admit_015_rule_identity_verified",
    "admit_015_current_fail_closed_state_verified",
    "admit_015_known_not_registered_state_verified",
    "admit_015_authorization_precedent_audited",
    "admit_015_training_permission_responsibility_audited",
    "admit_015_formal_evaluator_interface_preconditions_audited",
    "admit_014_admit_015_isolation_audited",
    "ready_for_admit_015_training_authorization_contract_design",
    "admit_015_training_authorization_contract_frozen",
    "admit_015_formal_evaluator_interface_contract_frozen",
    "evaluate_admit_015_implemented", "admit_015_result_type_implemented",
    "admit_015_standalone_evaluator_implemented",
    "admit_015_unified_adapter_contract_frozen",
    "admit_015_unified_adapter_implemented",
    "admit_015_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_015_implemented",
    "mandatory_training_authorization_enforcement_implemented",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented", "real_training_ready",
    "ready_for_training", "step12d_is_final_training_feature_contract",
)
SOURCE_ITEM_KEYS = ("order", "path", "sha256", "mode", "blob", "stage")
FORMAL_KEYS = (
    "evaluator_signature", "result_class_name", "result_field_count",
    "result_field_order", "outcome_vocabulary", "reason_vocabulary",
    "normalized_projection", "handler_signature", "adapter_id",
    "registry_location", "mandatory_enforcement_api",
)
MASK_KEYS = ("semantic_name", "alias")
SAFETY_KEYS = (
    "training", "parameter_update", "dataloader", "checkpoint",
    "model_forward", "loss", "backward", "optimizer", "provider", "network",
    "download", "raw_read_or_write",
)
MATERIALIZATION_KEYS = (
    "build_before_mutation", "exclusive_leaf_create",
    "rename_noreplace_required", "gpfs_einval_fails_closed",
    "os_replace_forbidden", "inode_preserving_exact_noop",
    "pinned_post_read_verification", "source_final_leaf_fd_retained",
    "output_final_set_traversal", "staging_lexical_binding_verified",
    "ownership_safe_cleanup",
    "failure_cleanup_is_non_destructive",
    "failure_cleanup_unlink_forbidden",
    "failure_cleanup_rmdir_forbidden",
    "failure_staging_may_be_retained",
    "concurrent_eexist_fails_closed",
    "preexisting_exact_destination_is_noop",
    "successful_publish_has_no_staging_residue",
    "unknown_identity_objects_are_never_deleted",
    "nested_exact_bool_types_verified", "bool_int_equivalence_rejected",
    "ignored_extra_stage_artifacts_rejected",
    "extra_derived_roots_rejected",
)


def _expect_exact_type(value: Any, expected: type, label: str) -> None:
    if type(value) is not expected:
        raise AssertionError(f"{label} exact type mismatch")


def _parse_manifest_exact(data: bytes) -> dict[str, Any]:
    try:
        document = json.loads(
            data.decode(), object_pairs_hook=_duplicate_rejecting_hook
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AssertionError("manifest JSON invalid") from error
    _expect_exact_type(document, dict, "manifest")
    if tuple(document) != TOP_LEVEL_KEYS:
        raise AssertionError("manifest top-level exact schema/order mismatch")
    for key in (
        "source_boundary_schema", "source_boundary", "precondition_schema",
        "precondition_complete_ids", "precondition_incomplete_ids",
        "precondition_blocking_ids", "responsibility_schema",
        "forbidden_training_authority_sources", "issue_schema",
        "issue_coverage", "canonical_masks", "safety_schema", "output_files",
    ):
        _expect_exact_type(document[key], list, key)
    for key in (
        "source_count", "precondition_count", "responsibility_count",
        "issue_row_count", "issue_transition_count", "canonical_mask_count",
        "safety_count", "output_file_count",
        "authorized_admit_015_training_execution_count",
    ):
        _expect_exact_type(document[key], int, key)
    for key in (
        "current_permission", "current_callable_discovered_state",
        "current_adapter_ready_state", "download_training_key_fallback",
        "download_training_key_alias", "download_training_key_or",
        "download_training_key_and_as_single_permission",
        "combined_permission_semantics_defined",
        "issue_inventory_byte_identical_to_exact14",
        "canonical_mask_long_names_are_authoritative",
        "feature_semantics_audit_completed",
        "feature_semantics_audit_required_before_training",
        "historical_unknown_atom_feature_policy_resolved",
        "historical_feature_semantics_known",
        "output_sha256_excludes_manifest_self_hash", "all_checks_passed",
        *TRUE_KEYS, *FALSE_KEYS,
    ):
        _expect_exact_type(document[key], bool, key)
    for key in (
        "formal_interface_not_frozen", "readiness", "safety",
        "output_sha256", "materialization",
    ):
        _expect_exact_type(document[key], dict, key)
    if any(type(item) is not str for item in document["forbidden_training_authority_sources"]):
        raise AssertionError("forbidden-source item type mismatch")
    if any(type(item) is not str for item in document["issue_schema"]):
        raise AssertionError("issue schema item type mismatch")
    for key in (
        "source_boundary_schema", "precondition_schema",
        "precondition_complete_ids", "precondition_incomplete_ids",
        "precondition_blocking_ids", "responsibility_schema",
        "forbidden_training_authority_sources", "issue_schema",
        "issue_coverage", "safety_schema", "output_files",
    ):
        if any(type(item) is not str for item in document[key]):
            raise AssertionError(f"{key} item exact type mismatch")
    if tuple(document["formal_interface_not_frozen"]) != FORMAL_KEYS:
        raise AssertionError("formal-interface nested schema/order mismatch")
    if tuple(document["readiness"]) != READINESS_KEYS:
        raise AssertionError("readiness nested schema/order mismatch")
    if tuple(document["safety"]) != SAFETY_KEYS:
        raise AssertionError("safety nested schema/order mismatch")
    if tuple(document["materialization"]) != MATERIALIZATION_KEYS:
        raise AssertionError("materialization nested schema/order mismatch")
    if tuple(document["output_sha256"]) != FILES[:-1]:
        raise AssertionError("output SHA exact5 schema/order mismatch")
    for mapping_name, keys in (
        ("formal_interface_not_frozen", FORMAL_KEYS),
        ("readiness", READINESS_KEYS),
        ("safety", SAFETY_KEYS),
        ("materialization", MATERIALIZATION_KEYS),
    ):
        for key in keys:
            _expect_exact_type(
                document[mapping_name][key],
                bool,
                f"{mapping_name}.{key}",
            )
    for name, digest in document["output_sha256"].items():
        _expect_exact_type(digest, str, f"output_sha256.{name}")
        if (
            len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise AssertionError(f"output SHA value invalid: {name}")
    for item in document["source_boundary"]:
        _expect_exact_type(item, dict, "source boundary item")
        if tuple(item) != SOURCE_ITEM_KEYS:
            raise AssertionError("source item nested schema/order mismatch")
        _expect_exact_type(item["order"], int, "source order")
        _expect_exact_type(item["stage"], int, "source stage")
        for key in ("path", "sha256", "mode", "blob"):
            _expect_exact_type(item[key], str, f"source {key}")
    for item in document["canonical_masks"]:
        _expect_exact_type(item, dict, "mask item")
        if tuple(item) != MASK_KEYS:
            raise AssertionError("mask nested schema/order mismatch")
        _expect_exact_type(item["semantic_name"], str, "mask semantic name")
        _expect_exact_type(item["alias"], str, "mask alias")
    return document


def _expected_manifest(
    sources: tuple[AttestedSource, ...],
    pre: list[dict[str, str]],
    responsibility: list[dict[str, str]],
    safety_rows: list[dict[str, str]],
    issues: bytes,
    payloads: dict[str, bytes],
) -> dict[str, Any]:
    complete = [row["precondition_id"] for row in pre
                if row["completion_status"] == "complete"]
    incomplete = [row["precondition_id"] for row in pre
                  if row["completion_status"] != "complete"]
    blocking = [row["precondition_id"] for row in pre
                if row["implementation_blocking"] == "true"]
    readiness = {
        **{key: True for key in TRUE_KEYS},
        **{key: False for key in FALSE_KEYS},
    }
    output_sha = {
        name: hashlib.sha256(payloads[name]).hexdigest() for name in FILES[:-1]
    }
    manifest: dict[str, Any] = {
        "project": "CovaPIE", "stage": STAGE, "audit_revision": REVISION,
        "base_commit": BASE, "base_parent": PARENT, "base_tree": TREE,
        "base_subject": SUBJECT,
        "canonical_evidence_python_implementation": "cpython",
        "canonical_evidence_python_version": "3.10.4",
        "ast_attestation_cross_python_version_portable": False,
        "noncanonical_python_policy":
            "evaluator_semantic_smoke_only; artifact_build_checker_and_frozen_ast_forbidden",
        "python_runtime_migration_policy": "explicit_contract_refresh_required",
        "admission_rule_id": "ADMIT_015",
        "admission_rule_name": "current_gate_grants_no_training_permission",
        "current_evidence_source": "current_design_gate",
        "current_required_status": "training_not_authorized_now",
        "current_blocking_reason": "training_not_authorized",
        "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "current_registration_state": "known_but_not_registered",
        "current_callable_discovered_state": False,
        "current_adapter_ready_state": False,
        "current_runtime_coverage_open": "ADMIT_015",
        "source_count": 23, "source_boundary_schema": list(SOURCE_COLUMNS),
        "source_boundary": [
            {"order": order, "path": source.path.as_posix(),
             "sha256": source.sha256, "mode": source.mode,
             "blob": source.blob, "stage": 0}
            for order, source in enumerate(sources, 1)
        ],
        "precondition_schema": list(PRE_COLUMNS), "precondition_count": 45,
        "precondition_complete_ids": complete,
        "precondition_incomplete_ids": incomplete,
        "precondition_blocking_ids": blocking,
        "responsibility_schema": list(RESP_COLUMNS),
        "responsibility_count": 16,
        "candidate_authoritative_envelope": "stage_authorization_context",
        "candidate_target_item": "current_stage_training_authorized",
        "admit_014_coexistence_item": "current_stage_download_authorized",
        "candidate_producer": "trusted_future_stage_orchestrator",
        "candidate_value_type": "exact builtin bool",
        "candidate_coercion_policy": "no coercion",
        "candidate_lifetime": "invocation-local",
        "candidate_default_policy": "omission must fail closed",
        "candidate_replay_policy": "no cross-invocation replay",
        "candidate_path_status":
            "recommended authoritative path pending formal authorization contract",
        "download_training_key_fallback": False,
        "download_training_key_alias": False,
        "download_training_key_or": False,
        "download_training_key_and_as_single_permission": False,
        "combined_permission_semantics_defined": False,
        "forbidden_training_authority_sources": (
            "candidate_record|batch_context|evaluation_context|"
            "download_result_context|provider_result|environment_variable|"
            "filesystem_marker|artifact_sha|git_commit_sha|checkpoint_metadata|"
            "training_config|command_line_flag|model_state|dataloader_state"
        ).split("|"),
        "formal_interface_not_frozen": {key: True for key in FORMAL_KEYS},
        "issue_schema": next(csv.reader(io.StringIO(issues.decode()))),
        "issue_row_count": 30, "issue_transition_count": 0,
        "issue_inventory_source_sha256": EXACT23[10][1],
        "issue_inventory_byte_identical_to_exact14": True,
        "issue_coverage": ["ADMIT_015"], "readiness": readiness,
        "canonical_masks": [
            {"semantic_name": "warhead_only", "alias": "A"},
            {"semantic_name": "linker_plus_warhead", "alias": "B"},
            {"semantic_name": "scaffold_plus_warhead", "alias": "B2"},
            {"semantic_name": "scaffold_only", "alias": "B3"},
            {"semantic_name": "scaffold_plus_linker_plus_warhead", "alias": "C"},
        ],
        "canonical_mask_count": 5,
        "canonical_mask_long_names_are_authoritative": True,
        "feature_semantics_audit_completed": False,
        "feature_semantics_audit_required_before_training": True,
        "historical_unknown_atom_feature_policy_resolved": False,
        "historical_feature_semantics_known": False,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "safety": {key: False for key in SAFETY_KEYS},
        "safety_schema": list(SAFETY_COLUMNS), "safety_count": 20,
        "output_files": list(FILES), "output_file_count": 6,
        "output_sha256": output_sha,
        "output_sha256_excludes_manifest_self_hash": True,
        "materialization": {key: True for key in MATERIALIZATION_KEYS},
        "recommended_next_step":
            "design_covapie_admit_015_training_authorization_contract_v1",
        "all_checks_passed": True,
    }
    manifest.update(readiness)
    if tuple(manifest) != TOP_LEVEL_KEYS:
        raise AssertionError("checker expected manifest schema drift")
    return manifest


def verify_exact6_semantics(
    payloads: dict[str, bytes],
    sources: tuple[AttestedSource, ...],
) -> dict[str, Any]:
    if tuple(payloads) != FILES:
        raise AssertionError("Exact6 name/order mismatch")
    for name in FILES:
        frozen = FROZEN_OUTPUT_SHA256[name]
        if (
            frozen != "TO_BE_FROZEN"
            and hashlib.sha256(payloads[name]).hexdigest() != frozen
        ):
            raise AssertionError(f"frozen output SHA mismatch: {name}")
    expected_pre = expected_preconditions(sources)
    expected_resp = expected_responsibilities()
    expected_sources = expected_source_rows(sources)
    expected_safe = expected_safety()
    actual_pre = _parse_csv_exact(payloads[PRECONDITION], PRE_COLUMNS)
    actual_resp = _parse_csv_exact(payloads[RESPONSIBILITY], RESP_COLUMNS)
    actual_sources = _parse_csv_exact(payloads[SOURCE_AUDIT], SOURCE_COLUMNS)
    actual_safe = _parse_csv_exact(payloads[SAFETY], SAFETY_COLUMNS)
    if actual_pre != expected_pre:
        raise AssertionError("Exact45 independently rebuilt semantics mismatch")
    if actual_resp != expected_resp:
        raise AssertionError("Exact16 independently rebuilt semantics mismatch")
    if actual_sources != expected_sources:
        raise AssertionError("Exact23 source-audit semantics mismatch")
    if actual_safe != expected_safe:
        raise AssertionError("Exact20 safety semantics mismatch")
    inherited_issues = _source_map(sources)[PATHS["RUNTIME_ISSUES"]].content
    if payloads[ISSUE] != inherited_issues:
        raise AssertionError("Exact30 issue bytes mismatch")
    issue_rows = _parse_csv_exact(
        payloads[ISSUE],
        tuple(next(csv.reader(io.StringIO(payloads[ISSUE].decode())))),
    )
    if len(issue_rows) != 30:
        raise AssertionError("Exact30 row count mismatch")
    coverage = next(
        row for row in issue_rows
        if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    )
    if (
        coverage["affected_rules"] != "ADMIT_015"
        or coverage["successor_effective_status"] != "open"
    ):
        raise AssertionError("issue coverage semantics mismatch")
    actual_manifest = _parse_manifest_exact(payloads[MANIFEST])
    expected_manifest = _expected_manifest(
        sources, expected_pre, expected_resp, expected_safe,
        inherited_issues, payloads,
    )
    if actual_manifest != expected_manifest:
        raise AssertionError("manifest independently rebuilt semantics mismatch")
    return actual_manifest


def _verify_candidate_ast() -> None:
    source_bytes = _pinned_read_relative(ROOT, PRODUCTION)
    if hashlib.sha256(source_bytes).hexdigest() != PRODUCTION_SHA256:
        raise AssertionError("candidate production SHA mismatch")
    source = source_bytes.decode()
    tree = ast.parse(source)
    normalized = ast.dump(tree, annotate_fields=True, include_attributes=False)
    if hashlib.sha256(normalized.encode()).hexdigest() != PRODUCTION_AST_SHA256:
        raise AssertionError("candidate production AST mismatch")
    forbidden_defs = {
        "evaluate_admit_015", "classify_admit_015_formal_evaluator_interface_design",
        "_evaluate_registered_admit_015", "evaluate_admission_rule",
        "train", "fit", "backward", "optimizer",
    }
    definitions = {
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    classes = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    if definitions & forbidden_defs or "Admit015EvaluationResult" in classes:
        raise AssertionError("premature evaluator/result/runtime definition")
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    if imports & {
        "torch", "numpy", "pytorch_lightning", "rdkit",
        "equivariant_diffusion", "dataset", "lightning_modules",
    }:
        raise AssertionError("forbidden model/training import")
    if "os.replace" in source:
        raise AssertionError("os.replace is forbidden")


def _load_production() -> Any:
    spec = importlib.util.spec_from_file_location("admit015_revised_candidate", ROOT / PRODUCTION)
    if spec is None or spec.loader is None:
        raise AssertionError("candidate import unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def _read_disk_exact6() -> dict[str, bytes]:
    return {
        name: _pinned_read_relative(
            ROOT, DERIVED / name, allow_candidate_derived=True
        )
        for name in FILES
    }


def _check_ignore(path: Path) -> bool:
    result = _git(["check-ignore", "--no-index", "-q", "--", path.as_posix()])
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise AssertionError(f"git check-ignore failed closed: {path}")


STAGE_FAMILY_TOKENS = (
    "covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_preconditions_audit",
    "covapie_admit_015_formal_evaluator_interface_precondition",
    "covapie_admit_015_authorization_evidence_and_routing_responsibility",
    "covapie_admit_015_source_boundary_audit",
    "covapie_admit_015_safety_training_boundary_audit",
    "covapie_admit_015_issue_readiness_inventory",
)
STAGE_FAMILY_SCAN_ROOTS = (
    Path("src/covalent_ext"),
    Path("scripts"),
    Path("tests"),
    Path("docs"),
)
FORBIDDEN_SUFFIXES = {
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
    ".tgz", ".npz", ".tmp", ".part",
}


def _is_stage_family_name(name: str) -> bool:
    candidate = name.lstrip(".")
    return any(token in candidate for token in STAGE_FAMILY_TOKENS)


def _is_stage_family_path(path: Path) -> bool:
    return _is_stage_family_name(path.as_posix())


def _scan_bounded_stage_root(
    scan_root: Path,
    discovered: set[Path],
) -> None:
    pending = [scan_root]
    while pending:
        current = pending.pop()
        try:
            entries = tuple(os.scandir(ROOT / current))
        except OSError as error:
            raise AssertionError(
                f"stage-family scan unavailable: {current}"
            ) from error
        for entry in entries:
            relative = current / entry.name
            if entry.is_symlink():
                raise AssertionError(
                    f"symlink blocks no-follow stage-family scan: {relative}"
                )
            if _is_stage_family_path(relative):
                discovered.add(relative)
            if entry.is_dir(follow_symlinks=False):
                pending.append(relative)


def _filesystem_stage_family() -> set[Path]:
    """Find stage-family paths independently of Git ignore visibility."""
    discovered: set[Path] = set()
    for scan_root in STAGE_FAMILY_SCAN_ROOTS:
        _scan_bounded_stage_root(scan_root, discovered)
    derived_parent = DERIVED.parent
    try:
        derived_entries = tuple(os.scandir(ROOT / derived_parent))
    except OSError as error:
        raise AssertionError("derived stage-family scan unavailable") from error
    for entry in derived_entries:
        if not _is_stage_family_name(entry.name):
            continue
        relative = derived_parent / entry.name
        discovered.add(relative)
        pending = (
            [relative] if entry.is_dir(follow_symlinks=False) else []
        )
        while pending:
            current = pending.pop()
            try:
                children = tuple(os.scandir(ROOT / current))
            except OSError as error:
                raise AssertionError(
                    f"derived stage-family inventory unavailable: {current}"
                ) from error
            for child in children:
                child_relative = current / child.name
                discovered.add(child_relative)
                if child.is_dir(follow_symlinks=False):
                    pending.append(child_relative)
    expected = {path for path in EXACT10} | {DERIVED}
    for path in sorted(discovered, key=Path.as_posix):
        try:
            item = os.lstat(ROOT / path)
        except OSError as error:
            raise AssertionError(
                f"stage-family path vanished during scan: {path}"
            ) from error
        if _check_ignore(path):
            raise AssertionError(f"ignored stage-family path: {path}")
        if stat.S_ISLNK(item.st_mode):
            raise AssertionError(f"symlink stage-family path: {path}")
        if path == DERIVED:
            if not stat.S_ISDIR(item.st_mode):
                raise AssertionError("Exact6 parent is not a directory")
            continue
        if (
            not stat.S_ISREG(item.st_mode)
            or item.st_size > 100 * 1024 * 1024
            or path.suffix.lower() in FORBIDDEN_SUFFIXES
        ):
            raise AssertionError(f"unsafe stage-family artifact: {path}")
    if discovered != expected:
        raise AssertionError("filesystem stage-family allowlist mismatch")
    return discovered


def _lifecycle() -> str:
    if _git(["merge-base", "--is-ancestor", BASE, "HEAD"]).returncode:
        raise AssertionError("base is not an ancestor")
    staged_all = _git(["diff", "--cached", "--name-only"])
    if staged_all.returncode or staged_all.stdout:
        raise AssertionError("staged index must be empty")
    states = []
    for path in EXACT10:
        try:
            item = os.lstat(ROOT / path)
        except FileNotFoundError as error:
            raise AssertionError(f"missing Exact10 member: {path}") from error
        if (
            stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode)
            or item.st_size > 100 * 1024 * 1024
            or path.suffix.lower() in FORBIDDEN_SUFFIXES
            or _check_ignore(path)
        ):
            raise AssertionError(f"unsafe/ignored Exact10 member: {path}")
        tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()])
        states.append("tracked" if tracked.returncode == 0 else "untracked")
    if len(set(states)) != 1:
        raise AssertionError("mixed Exact10 lifecycle")
    lifecycle = "post_commit" if states[0] == "tracked" else "pre_commit"
    untracked_result = _git(["ls-files", "--others", "--exclude-standard"])
    if untracked_result.returncode:
        raise AssertionError("untracked inventory unavailable")
    untracked = set(untracked_result.stdout.splitlines())
    exact = {path.as_posix() for path in EXACT10}
    working = _git(["diff", "--name-only"])
    if working.returncode:
        raise AssertionError("working diff unavailable")
    if lifecycle == "pre_commit":
        if untracked != exact or working.stdout:
            raise AssertionError("pre_commit lifecycle mismatch")
    else:
        if untracked or working.stdout:
            raise AssertionError("post_commit lifecycle mismatch")
    if set(os.listdir(ROOT / DERIVED)) != set(FILES):
        raise AssertionError("derived Exact6/seventh-file mismatch")
    _filesystem_stage_family()
    tracked_and_untracked = set(_git(["ls-files"]).stdout.splitlines()) | untracked
    stage_related = {
        path for path in tracked_and_untracked
        if (
            "admit_015_formal_evaluator_interface_preconditions_audit" in path
            or "admit_015_formal_evaluator_interface_precondition_inventory" in path
            or "admit_015_authorization_evidence_and_routing_responsibility" in path
            or "admit_015_source_boundary_audit" in path
            or "admit_015_safety_training_boundary_audit" in path
            or "admit_015_issue_readiness_inventory" in path
        )
    }
    if stage_related != exact:
        raise AssertionError("extra tracked/untracked stage file")
    return lifecycle


def main() -> int:
    if (sys.implementation.name, tuple(sys.version_info[:3])) != (
        "cpython", (3, 10, 4)
    ):
        raise RuntimeError("checker requires canonical CPython 3.10.4")
    sources = attest_exact23()
    _verify_candidate_ast()
    module = _load_production()
    actual = module.build_artifact_payloads()
    verify_exact6_semantics(actual, sources)
    returned = module.materialize_audit()
    disk = _read_disk_exact6()
    if disk != actual:
        raise AssertionError("disk Exact6 differs from actual rebuild")
    manifest = verify_exact6_semantics(disk, sources)
    if returned != manifest:
        raise AssertionError("materializer return/independent manifest mismatch")
    lifecycle = _lifecycle()
    report = {
        "stage": STAGE, "revision": REVISION, "base_commit": BASE,
        "lifecycle": lifecycle, "exact10_count": 10, "source_count": 23,
        "precondition_count": 45, "precondition_complete_count": 19,
        "precondition_supported_count": 8,
        "precondition_incomplete_count": 18,
        "precondition_blocking_count": 26, "responsibility_count": 16,
        "safety_count": 20, "issue_row_count": 30,
        "issue_transition_count": 0, "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "ready_for_training": False,
        "recommended_next_step":
            "design_covapie_admit_015_training_authorization_contract_v1",
        "all_checks_passed": True,
    }
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
