"""Independent checker for the ADMIT_015 unified-adapter design contract."""
from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import importlib.util
import inspect
import io
import json
import os
import re
import stat
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import fields
from pathlib import Path
from types import MappingProxyType


ROOT = Path(__file__).resolve().parents[1]
BASE = "b4a8770f27bdd263d0d3ad5c0a8b210e19954cbe"
PARENT = "809ec4f8c9494db893d2d66b7551856b2ead4401"
TREE = "593a8a9225d2a8d128e1145c12fd8ec1efb5fe5b"
SUBJECT = "add CovaPIE ADMIT_015 standalone evaluator interface v1"
PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_015_"
    "unified_adapter_contract_design_gate.py"
)
PRODUCTION_SHA256 = (
    "a11ce87b326612e251258072995ee26fb848212a7b7dde869a10de6e473ea60c"
)
CHECKER = Path(
    "scripts/"
    "check_covapie_bulk_download_admission_admit_015_"
    "unified_adapter_contract_v1.py"
)
TEST = Path(
    "tests/"
    "test_covapie_bulk_download_admission_admit_015_"
    "unified_adapter_contract_v1.py"
)
DOC = Path(
    "docs/"
    "covapie_bulk_download_admission_admit_015_"
    "unified_adapter_contract_v1_summary.md"
)
STAGE = (
    Path("data/derived/covalent_small")
    / "covapie_bulk_download_admission_admit_015_unified_adapter_contract_v1"
)
OUTPUTS = (
    "covapie_admit_015_unified_adapter_contract.csv",
    "covapie_admit_015_stage_authorization_projection_and_context_routing_matrix.csv",
    "covapie_admit_015_unified_result_projection_truth_matrix.csv",
    "covapie_admit_015_unified_adapter_safety_audit.csv",
    "covapie_admit_015_unified_adapter_issue_readiness_inventory.csv",
    "covapie_admit_015_unified_adapter_contract_manifest.json",
)
CANDIDATES = (PRODUCTION, CHECKER, TEST, DOC, *(STAGE / name for name in OUTPUTS))
OUTPUT_SHA256 = {
    OUTPUTS[0]: "16159caf1b55116fc2802e43f330d1c706041da4261e1a22039d7c8c4375ba34",
    OUTPUTS[1]: "9edfaecd8492423b61d9e93413a616a4b917219d8207808da7db0142a9aed06b",
    OUTPUTS[2]: "c40c8133f946cf39149224479590b65351c9b9229e9cc33a821616ed521ca2d3",
    OUTPUTS[3]: "586ced0297eff2b396d61d771073027bc2db982e6092d2e00a1b7dcc7ac08d2d",
    OUTPUTS[4]: "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec",
    OUTPUTS[5]: "43ffb247cda8cc641c0a9ba2892f66b0b54b2ed572c6f6d26a2e62cd37778449",
}
SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_admit_015_standalone_evaluator_interface.py", "eacb5c1ac583649a34cdb9dcde4c004a861da43609b9ffb964a715a427883a82"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_standalone_evaluator_interface_v1/covapie_admit_015_standalone_evaluator_interface_contract.csv", "1ad1b44677abf7cd262d5928aee17381e5767dd82880aee689be07cd8b031245"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_standalone_evaluator_interface_v1/covapie_admit_015_standalone_evaluator_interface_truth_matrix.csv", "e5e641d590b6a49e536193f7b523605dcfc700cd7196668995fb4ce442561fbf"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_standalone_evaluator_interface_v1/covapie_admit_015_standalone_evaluator_interface_source_boundary_audit.csv", "d9499b8851ae79be18c480ba40763c13aabfcee22502266889b4ea09125879d5"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_standalone_evaluator_interface_v1/covapie_admit_015_standalone_evaluator_interface_purity_audit.csv", "c5a734085889ff56adce29c23d3f910b088fbcc98ab1c98f08065fb29dbe7cd1"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_standalone_evaluator_interface_v1/covapie_admit_015_standalone_evaluator_interface_issue_readiness_inventory.csv", "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_standalone_evaluator_interface_v1/covapie_admit_015_standalone_evaluator_interface_manifest.json", "238aadcf819ffc2c30c5de063b1873ce16df59f82cb4be4b4d6222fbdc143758"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_contract_design_gate.py", "48e2135517cad1ad7744345c3cb5f45e5b29d9c91fd41850eb80a96785e0daa3"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_contract_v1/covapie_admit_015_formal_evaluator_routing_and_consumption_contract.csv", "a0c586281e96f063f67d7c47c1a0b8336a73cb0841b283ca1de64f30fe60cf66"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_contract_v1/covapie_admit_015_formal_evaluator_interface_truth_matrix.csv", "7b09b3c917e4bbc7d140daafa99a9b6a34584ce3a008e9f0193db804c57b4885"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_contract_v1/covapie_admit_015_formal_evaluator_interface_contract_manifest.json", "08ce241290c66e87881c983a563be9f406d904c39e99bd9c6830c78fc3b4b021"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/covapie_admit_015_training_authorization_truth_matrix.csv", "bc1070cb7df2db7ee05c4c8aa21ea9563a08974b620d44ee42c193c63b4fb37b"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/covapie_admit_015_training_authorization_contract_manifest.json", "16ea4bb5f781c6f6d8277fb4142258c2bee4849b942582e48692373caee5cda1"),
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014.py", "c5f5cfc57155f34ee2435228b3bf53ae8d1f6d81c32e097c43668c0b272fd1a2"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1/covapie_admit_001_to_014_runtime_contract.csv", "6646678c8c11c37ee8d4cc28429f92b1afe0b98f31d2832a4a8a142015b0e5b2"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1/covapie_admit_001_to_014_registry_and_identity_audit.csv", "92f578cf6d038c43c55b6768edce413191297f2c207e1f473769835b09b7f7ed"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1/covapie_admit_001_to_014_runtime_manifest.json", "bf7bbe3c2158f661c6e71835bf603af76ffbb315d4ef377c9f72da246619ba40"),
)
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome",
    "passed", "blocks_candidate", "reason", "normalized_values",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "adapter_id",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *arguments), cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )


def rows(name: str) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    stream = io.StringIO((STAGE / name).read_text(), newline="")
    reader = csv.DictReader(stream)
    return tuple(reader.fieldnames or ()), list(reader)


def verify_sources() -> None:
    identity = git("show", "-s", "--format=%H%n%P%n%T%n%s", BASE)
    assert identity.returncode == 0
    assert identity.stdout.splitlines() == [BASE, PARENT, TREE, SUBJECT]
    assert git("merge-base", "--is-ancestor", BASE, "HEAD").returncode == 0
    for relative, expected in SOURCE_BOUNDARY:
        path = Path(relative)
        assert not path.is_absolute() and ".." not in path.parts
        assert not relative.startswith(("data/raw/", "checkpoints/"))
        item = os.lstat(ROOT / path)
        assert stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode)
        indexed = git("ls-files", "--stage", "--", relative)
        assert indexed.returncode == 0 and indexed.stdout.rstrip().endswith(f" 0\t{relative}")
        assert sha(ROOT / path) == expected


def verify_candidate_ast() -> None:
    assert sha(ROOT / PRODUCTION) == PRODUCTION_SHA256
    tree = ast.parse((ROOT / PRODUCTION).read_text())
    functions = {
        node.name for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assignments = {
        target.id
        for node in tree.body if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (
            node.targets if isinstance(node, ast.Assign) else (node.target,)
        )
        if isinstance(target, ast.Name)
    }
    assert "_evaluate_registered_admit_015" not in functions
    assert "evaluate_admission_rule" not in functions
    assert "EVALUATOR_REGISTRY" not in assignments
    assert "simulate_admit_015_unified_adapter_contract_design" in functions
    assert "os.replace" not in (ROOT / PRODUCTION).read_text()


def verify_artifacts() -> dict[str, object]:
    assert tuple(sorted(path.name for path in STAGE.iterdir())) == tuple(sorted(OUTPUTS))
    assert {name: sha(ROOT / STAGE / name) for name in OUTPUTS} == OUTPUT_SHA256
    expected_headers = (
        ("contract_order", "contract_id", "contract_group", "contract_subject", "contract_value", "contract_status"),
        ("matrix_order", "matrix_group", "case_id", "routing_condition", "envelope_representation", "candidate_key_access_count", "adapter_stage_key_access_count", "formal_call_count", "oracle_call_count", "formal_stage_key_access_count", "oracle_stage_key_access_count", "identity_preserved", "expected_dispatch_code", "expected_reason", "expected_result_json", "case_passed"),
        ("case_order", "case_id", "case_group", "routing_condition", "source_result_representation", "oracle_result_representation", "expected_unified_result_json", "observed_unified_result_json", "exact13_type_value_equality", "case_passed"),
        ("audit_order", "audit_item", "expected_state", "observed_state", "safety_passed"),
    )
    counts = []
    for index, (name, expected) in enumerate(
        zip(OUTPUTS[:4], expected_headers, strict=True)
    ):
        header, content = rows(name)
        assert header == expected
        if index == 0:
            assert all(row["contract_status"] == "frozen" for row in content)
        elif index == 3:
            assert all(row["safety_passed"] == "true" for row in content)
        else:
            assert all(row["case_passed"] == "true" for row in content)
        counts.append(len(content))
    assert counts == [54, 42, 61, 32]
    assert (STAGE / OUTPUTS[4]).read_bytes() == (
        ROOT / SOURCE_BOUNDARY[5][0]
    ).read_bytes()
    manifest = json.loads((STAGE / OUTPUTS[5]).read_bytes())
    assert manifest["output_files"] == list(OUTPUTS)
    assert manifest["output_sha256"] == {
        name: OUTPUT_SHA256[name] for name in OUTPUTS[:5]
    }
    assert OUTPUTS[5] not in manifest["output_sha256"]
    assert manifest["source_input_paths"] == [path for path, _ in SOURCE_BOUNDARY]
    assert manifest["source_input_sha256"] == dict(SOURCE_BOUNDARY)
    assert manifest["result_fields"] == list(RESULT_FIELDS)
    assert manifest["precondition_transition"] == {
        "complete_count": 50,
        "implementation_blocking_count": 1,
        "incomplete_count": 1,
        "remaining_open_precondition_ids": ["PRE_032|PRE_033|PRE_034|PRE_035|PRE_036|PRE_038|PRE_042"],
        "resolution": (
            "ADMIT_015 five-envelope routing, standalone Exact9 attestation, "
            "oracle equivalence and typed Exact13 projection frozen"
        ),
        "resolved_precondition_ids": ["PRE_031"],
        "row_count": 51,
    }
    assert manifest["coverage_issue_affected_rules"] == "ADMIT_015"
    assert manifest["issue_transition_count"] == 0
    readiness = manifest["readiness"]
    assert readiness["admit_015_unified_adapter_contract_frozen"] is True
    assert readiness["admit_015_unified_adapter_implemented"] is False
    assert readiness["admit_015_registered_in_engine"] is False
    assert readiness["unified_dispatch_runtime_with_admit_001_to_014_implemented"] is False
    assert manifest["current_permission"] is False
    assert manifest["authorized_admit_015_training_execution_count"] == 0
    return manifest


class Probe(Mapping[str, object]):
    def __init__(self, value: object) -> None:
        self.value = value
        self.accesses: list[str] = []
        self.iterations = self.lengths = self.gets = self.contains = 0

    def __getitem__(self, key: str) -> object:
        self.accesses.append(key)
        return self.value

    def __iter__(self):
        self.iterations += 1
        raise AssertionError

    def __len__(self) -> int:
        self.lengths += 1
        raise AssertionError

    def get(self, key: str, default: object = None) -> object:
        self.gets += 1
        raise AssertionError

    def __contains__(self, key: object) -> bool:
        self.contains += 1
        raise AssertionError


def import_production():
    spec = importlib.util.spec_from_file_location("admit015_adapter_design_check", ROOT / PRODUCTION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def verify_semantics(module) -> None:
    assert tuple(module.RESULT_FIELDS) == RESULT_FIELDS
    assert module.CURRENT_REGISTERED_RULE_ORDER == tuple(
        f"ADMIT_{index:03d}" for index in range(1, 14)
    )
    assert module.FUTURE_REGISTERED_RULE_ORDER[-1] == "ADMIT_015"
    assert module.FUTURE_KNOWN_NOT_REGISTERED == ("ADMIT_015",)
    invalid = module.simulate_admit_015_unified_adapter_contract_design(
        object(), batch_context=None, evaluation_context=None,
        download_result_context=None, stage_authorization_context=object(),
    )
    assert tuple(vars(invalid)) == RESULT_FIELDS
    assert invalid.reason == "ADMIT_015_CANDIDATE_RECORD_MAPPING_INVALID"
    assert invalid.validated_candidate_fields == ()
    probe = Probe(True)
    result = module.simulate_admit_015_unified_adapter_contract_design(
        {}, batch_context=None, evaluation_context=None,
        download_result_context=None, stage_authorization_context=probe,
    )
    assert result.normalized_values == (
        ("current_stage_training_authorized", "true"),
    )
    assert result.validated_candidate_fields == ()
    assert result.consumed_candidate_fields == ()
    assert result.consumed_context_items == (
        "current_stage_training_authorized",
    )
    assert probe.accesses == [
        "current_stage_training_authorized",
        "current_stage_training_authorized",
    ]
    assert (probe.iterations, probe.lengths, probe.gets, probe.contains) == (0, 0, 0, 0)
    for envelope, reason in (
        ("batch_context", "ADMIT_015_BATCH_CONTEXT_MUST_BE_NONE"),
        ("evaluation_context", "ADMIT_015_EVALUATION_CONTEXT_MUST_BE_NONE"),
        ("download_result_context", "ADMIT_015_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
    ):
        kwargs = {
            "batch_context": None, "evaluation_context": None,
            "download_result_context": None,
            "stage_authorization_context": None,
        }
        kwargs[envelope] = {}
        try:
            module.simulate_admit_015_unified_adapter_contract_design({}, **kwargs)
        except module.AdapterContractDesignError as error:
            assert error.code == "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"
            assert error.reason == reason
        else:
            raise AssertionError("routing error required")


def lifecycle() -> str:
    tracked = []
    staged = []
    dirty = []
    for path in CANDIDATES:
        relative = path.as_posix()
        listed = git("ls-files", "--error-unmatch", "--", relative)
        if listed.returncode == 0:
            tracked.append(relative)
        cached = git("diff", "--cached", "--name-only", "--", relative)
        assert cached.returncode == 0
        if cached.stdout:
            staged.append(relative)
        changed = git("diff", "--name-only", "--", relative)
        assert changed.returncode == 0
        if changed.stdout:
            dirty.append(relative)
        ignored = git("check-ignore", "-q", "--", relative)
        assert ignored.returncode in (0, 1)
        assert ignored.returncode == 1
    assert not staged and not dirty
    if not tracked:
        return "pre_commit"
    assert len(tracked) == len(CANDIDATES)
    return "post_commit"


def main() -> None:
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    verify_sources()
    verify_candidate_ast()
    manifest = verify_artifacts()
    module = import_production()
    verify_semantics(module)
    before = {
        name: os.lstat(ROOT / STAGE / name).st_ino for name in OUTPUTS
    }
    module.run_covapie_bulk_download_admission_admit_015_unified_adapter_contract_design_gate_v1()
    after = {
        name: os.lstat(ROOT / STAGE / name).st_ino for name in OUTPUTS
    }
    assert before == after
    state = lifecycle()
    print("CovaPIE ADMIT_015 unified adapter contract v1: PASS")
    print(f"lifecycle={state}")
    print("base=44b4306adfa42ef3587f87d08a4f66ed60101fa7")
    print("source_boundary=Exact17")
    print("shared_result=Exact13")
    print("rows=54/42/61/32/30")
    print(f"manifest_sha256={OUTPUT_SHA256[OUTPUTS[5]]}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")


# revised1 hardening implementation follows.  The original small helpers above
# remain readable historical scaffolding; the definitions below replace every
# checker entry point used by main and by the targeted race/tamper tests.

MAX_CANDIDATE_BYTES = 100 * 1024 * 1024
READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
DIRECTORY_FLAGS = (
    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
)
FORBIDDEN_SUFFIXES = {
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".tmp", ".part",
}
EXACT10 = CANDIDATES
TOP_LEVEL_EXACT4 = (PRODUCTION, CHECKER, TEST, DOC)


def _sha_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _full_identity(
    item: os.stat_result,
) -> tuple[int, int, int, int, int, int]:
    return (
        item.st_dev,
        item.st_ino,
        item.st_mode,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
    )


def _pinned_source_read(repo_root: Path, relative: Path) -> bytes:
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("source path escape")
    root_lexical = os.lstat(repo_root)
    root_identity = _full_identity(root_lexical)
    if (
        not stat.S_ISDIR(root_lexical.st_mode)
        or stat.S_ISLNK(root_lexical.st_mode)
        or repo_root.resolve(strict=True) != repo_root
    ):
        raise ValueError("unsafe repository root")
    root_fd = os.open(repo_root, DIRECTORY_FLAGS)
    descriptors = [root_fd]
    bindings: list[
        tuple[int, str, int, tuple[int, int, int, int, int, int]]
    ] = []
    leaf_fd = -1
    try:
        if _full_identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("repository root stat/open race")
        parent_fd = root_fd
        for part in relative.parts[:-1]:
            lexical = os.stat(part, dir_fd=parent_fd, follow_symlinks=False)
            expected = _full_identity(lexical)
            if not stat.S_ISDIR(lexical.st_mode) or stat.S_ISLNK(
                lexical.st_mode
            ):
                raise ValueError("unsafe source parent")
            child_fd = os.open(
                part, DIRECTORY_FLAGS, dir_fd=parent_fd
            )
            if _full_identity(os.fstat(child_fd)) != expected:
                os.close(child_fd)
                raise ValueError("source parent stat/open race")
            bindings.append((parent_fd, part, child_fd, expected))
            descriptors.append(child_fd)
            parent_fd = child_fd
        before = os.stat(
            relative.name, dir_fd=parent_fd, follow_symlinks=False
        )
        leaf_identity = _full_identity(before)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_ISLNK(before.st_mode)
            or before.st_size > MAX_CANDIDATE_BYTES
        ):
            raise ValueError("unsafe source leaf")
        leaf_fd = os.open(relative.name, READ_FLAGS, dir_fd=parent_fd)
        if _full_identity(os.fstat(leaf_fd)) != leaf_identity:
            raise ValueError("source leaf stat/open race")
        chunks = []
        while True:
            chunk = os.read(leaf_fd, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        after_fd = _full_identity(os.fstat(leaf_fd))
        after_name = os.stat(
            relative.name, dir_fd=parent_fd, follow_symlinks=False
        )
        if (
            after_fd != leaf_identity
            or _full_identity(after_name) != leaf_identity
            or not stat.S_ISREG(after_name.st_mode)
            or stat.S_ISLNK(after_name.st_mode)
        ):
            raise ValueError("source leaf changed during traversal")
        for lexical_parent_fd, name, child_fd, expected in reversed(bindings):
            lexical = os.stat(
                name, dir_fd=lexical_parent_fd, follow_symlinks=False
            )
            if (
                _full_identity(lexical) != expected
                or _full_identity(os.fstat(child_fd)) != expected
                or not stat.S_ISDIR(lexical.st_mode)
                or stat.S_ISLNK(lexical.st_mode)
            ):
                raise ValueError("source parent binding changed")
        final_root = os.lstat(repo_root)
        if (
            _full_identity(final_root) != root_identity
            or _full_identity(os.fstat(root_fd)) != root_identity
            or not stat.S_ISDIR(final_root.st_mode)
            or stat.S_ISLNK(final_root.st_mode)
        ):
            raise ValueError("repository root binding changed")
        final_leaf = os.stat(
            relative.name, dir_fd=parent_fd, follow_symlinks=False
        )
        if (
            _full_identity(os.fstat(leaf_fd)) != leaf_identity
            or _full_identity(final_leaf) != leaf_identity
            or not stat.S_ISREG(final_leaf.st_mode)
            or stat.S_ISLNK(final_leaf.st_mode)
        ):
            raise ValueError("source final leaf binding changed")
        return b"".join(chunks)
    finally:
        if leaf_fd >= 0:
            os.close(leaf_fd)
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _parse_index_entry(
    output: str, relative: str,
) -> tuple[str, str, int]:
    line = output.rstrip("\n")
    try:
        metadata, observed_path = line.split("\t", 1)
        mode, blob, raw_stage = metadata.split(" ")
        stage_number = int(raw_stage)
    except ValueError as error:
        raise ValueError("index entry malformed") from error
    if (
        observed_path != relative
        or mode not in {"100644", "100755"}
        or re.fullmatch(r"[0-9a-f]{40}", blob) is None
    ):
        raise ValueError("index entry identity drift")
    return mode, blob, stage_number


def _parse_tree_entry(
    output: str, relative: str,
) -> tuple[str, str]:
    line = output.rstrip("\n")
    try:
        metadata, observed_path = line.split("\t", 1)
        mode, kind, blob = metadata.split(" ")
    except ValueError as error:
        raise ValueError("tree entry malformed") from error
    if (
        observed_path != relative
        or mode not in {"100644", "100755"}
        or kind != "blob"
        or re.fullmatch(r"[0-9a-f]{40}", blob) is None
    ):
        raise ValueError("tree entry identity drift")
    return mode, blob


def verify_sources() -> tuple[dict[str, object], ...]:
    identity = git("show", "-s", "--format=%H%n%P%n%T%n%s", BASE)
    if (
        identity.returncode != 0
        or identity.stdout.splitlines() != [BASE, PARENT, TREE, SUBJECT]
        or git("merge-base", "--is-ancestor", BASE, "HEAD").returncode != 0
    ):
        raise ValueError("base identity/ancestry failure")
    records = []
    for source_order, (relative, expected) in enumerate(SOURCE_BOUNDARY, 1):
        path = Path(relative)
        if (
            path.is_absolute()
            or ".." in path.parts
            or relative.startswith(("data/raw/", "checkpoints/"))
            or path.suffix in FORBIDDEN_SUFFIXES
        ):
            raise ValueError("unsafe source boundary")
        index = git("ls-files", "--stage", "--", relative)
        tree_result = git("ls-tree", BASE, "--", relative)
        if index.returncode or tree_result.returncode:
            raise ValueError("source index/tree command failed")
        index_mode, index_blob, index_stage = _parse_index_entry(
            index.stdout, relative
        )
        base_mode, base_blob = _parse_tree_entry(
            tree_result.stdout, relative
        )
        if (
            index_stage != 0
            or index_mode != base_mode
            or index_blob != base_blob
        ):
            raise ValueError("source index/base mode/blob/stage drift")
        base = subprocess.run(
            ("git", "cat-file", "blob", base_blob),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        index_bytes = subprocess.run(
            ("git", "cat-file", "blob", index_blob),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        current = _pinned_source_read(ROOT, path)
        if (
            base.returncode
            or index_bytes.returncode
            or base.stdout != index_bytes.stdout
            or index_bytes.stdout != current
            or _sha_bytes(current) != expected
        ):
            raise ValueError("source blob/bytes/SHA drift")
        records.append({
            "source_order": source_order,
            "source_relative_path": relative,
            "base_tree_mode": base_mode,
            "base_tree_blob": base_blob,
            "index_mode": index_mode,
            "index_blob": index_blob,
            "index_stage": index_stage,
            "expected_sha256": expected,
            "base_tree_sha256": _sha_bytes(base.stdout),
            "filesystem_sha256": _sha_bytes(current),
        })
    return tuple(records)


def _pinned_outputs(root: Path) -> dict[str, bytes]:
    parent = root.parent
    parent_lexical = os.lstat(parent)
    parent_identity = _full_identity(parent_lexical)
    if (
        not stat.S_ISDIR(parent_lexical.st_mode)
        or stat.S_ISLNK(parent_lexical.st_mode)
    ):
        raise ValueError("unsafe output parent")
    parent_fd = os.open(parent, DIRECTORY_FLAGS)
    root_fd = -1
    leaves: list[
        tuple[str, int, tuple[int, int, int, int, int, int], bytes]
    ] = []
    try:
        if _full_identity(os.fstat(parent_fd)) != parent_identity:
            raise ValueError("output parent stat/open race")
        root_lexical = os.stat(
            root.name, dir_fd=parent_fd, follow_symlinks=False
        )
        root_identity = _full_identity(root_lexical)
        if not stat.S_ISDIR(root_lexical.st_mode) or stat.S_ISLNK(
            root_lexical.st_mode
        ):
            raise ValueError("unsafe output root")
        root_fd = os.open(root.name, DIRECTORY_FLAGS, dir_fd=parent_fd)
        if _full_identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("output root stat/open race")
        initial = tuple(os.listdir(root_fd))
        if len(initial) != len(OUTPUTS) or set(initial) != set(OUTPUTS):
            raise ValueError("missing or extra Exact6 output")
        for name in OUTPUTS:
            before = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            expected = _full_identity(before)
            if (
                not stat.S_ISREG(before.st_mode)
                or stat.S_ISLNK(before.st_mode)
                or before.st_size > MAX_CANDIDATE_BYTES
            ):
                raise ValueError("unsafe output leaf")
            descriptor = os.open(name, READ_FLAGS, dir_fd=root_fd)
            if _full_identity(os.fstat(descriptor)) != expected:
                os.close(descriptor)
                raise ValueError("output leaf stat/open race")
            chunks = []
            while True:
                chunk = os.read(descriptor, 1 << 16)
                if not chunk:
                    break
                chunks.append(chunk)
            leaves.append((name, descriptor, expected, b"".join(chunks)))
        result = {}
        for name, descriptor, expected, content in leaves:
            relative = os.stat(
                name, dir_fd=root_fd, follow_symlinks=False
            )
            if (
                _full_identity(os.fstat(descriptor)) != expected
                or _full_identity(relative) != expected
                or not stat.S_ISREG(relative.st_mode)
                or stat.S_ISLNK(relative.st_mode)
            ):
                raise ValueError("output first leaf binding drift")
            result[name] = content

        def check_root_parent_binding() -> None:
            final_parent = os.lstat(parent)
            final_root = os.stat(
                root.name, dir_fd=parent_fd, follow_symlinks=False
            )
            if (
                _full_identity(final_parent) != parent_identity
                or _full_identity(os.fstat(parent_fd)) != parent_identity
                or _full_identity(final_root) != root_identity
                or _full_identity(os.fstat(root_fd)) != root_identity
                or not stat.S_ISDIR(final_parent.st_mode)
                or stat.S_ISLNK(final_parent.st_mode)
                or not stat.S_ISDIR(final_root.st_mode)
                or stat.S_ISLNK(final_root.st_mode)
            ):
                raise ValueError("output parent/root binding drift")

        check_root_parent_binding()
        second_inventory = tuple(os.listdir(root_fd))
        if (
            len(second_inventory) != len(OUTPUTS)
            or set(second_inventory) != set(OUTPUTS)
        ):
            raise ValueError("Exact6 second inventory drift")
        for name, descriptor, expected, _ in leaves:
            relative = os.stat(
                name, dir_fd=root_fd, follow_symlinks=False
            )
            if (
                _full_identity(os.fstat(descriptor)) != expected
                or _full_identity(relative) != expected
                or not stat.S_ISREG(relative.st_mode)
                or stat.S_ISLNK(relative.st_mode)
            ):
                raise ValueError("output final leaf binding drift")
        check_root_parent_binding()
        return result
    finally:
        for _, descriptor, _, _ in leaves:
            os.close(descriptor)
        if root_fd >= 0:
            os.close(root_fd)
        os.close(parent_fd)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate manifest key: {key}")
        result[key] = value
    return result


MANIFEST_TOP_LEVEL_KEYS = tuple(sorted((
    "Admit015EvaluationResult_implemented", "adapter_id",
    "admission_rule_id", "admission_rule_name",
    "admit_015_context_routing_contract_frozen",
    "admit_015_training_authorization_contract_frozen",
    "admit_015_exact13_projection_frozen",
    "admit_015_formal_evaluator_interface_contract_frozen",
    "admit_015_preconditions_audited", "admit_015_registered_in_engine",
    "admit_015_rule_logic_implemented",
    "admit_015_source_oracle_equivalence_contract_frozen",
    "admit_015_standalone_evaluator_implemented",
    "admit_015_unified_adapter_contract_frozen",
    "admit_015_unified_adapter_implemented", "all_checks_passed",
    "ast_attestation_cross_python_version_portable",
    "authorized_admit_015_training_execution_count",
    "candidate_invalid_call_counts", "candidate_invalid_projection",
    "candidate_mapping_invalid_reason", "candidate_record_contract",
    "canonical_evidence_python_implementation",
    "canonical_evidence_python_version",
    "canonical_mask_count", "canonical_masks",
    "combined_candidate_verdict_implemented",
    "context_failure_dispatch_code", "context_routing_order",
    "context_routing_reasons", "contract_row_count",
    "coverage_issue_affected_rules",
    "cross_rule_aggregation_implemented", "current_permission",
    "current_registered_rule_order", "dispatch_error_fields",
    "evaluate_admit_015_implemented", "exact13_projection",
    "expected_base_commit", "expected_base_parent",
    "expected_base_subject", "expected_base_tree",
    "feature_semantics_audit_completed",
    "feature_semantics_audit_required_before_training",
    "feature_semantics_note",
    "first_fourteen_handler_object_identity_preserved",
    "forbidden_envelope_contract", "formal_evaluator",
    "formal_result_type", "future_adapter_handler",
    "future_adapter_handler_implemented",
    "future_adapter_handler_signature",
    "future_adapter_handler_signature_evidence",
    "future_known_not_registered_rule_ids",
    "future_registered_rule_order", "future_registry_mapping_proxy_type",
    "historical_feature_semantics_known",
    "historical_unknown_atom_feature_policy_resolved",
    "independent_oracle", "independent_oracle_result_type",
    "issue_inventory_preserved_byte_identical",
    "issue_inventory_row_count", "issue_inventory_sha256",
    "issue_transition_count",
    "lifecycle_policy",
    "mandatory_training_authorization_enforcement_api_frozen",
    "mandatory_training_authorization_enforcement_implemented",
    "manifest_schema_version", "materialization_policy",
    "noncanonical_python_policy",
    "oracle_exact9_validation", "output_file_count", "output_files",
    "output_read_policy", "output_sha256",
    "output_sha256_excludes_manifest_self_hash",
    "precondition_transition", "project",
    "projection_truth_matrix_row_count", "provider_mapping_implemented",
    "provider_mapping_validated", "public_dispatcher_signature_preserved",
    "public_dispatcher_single_rule", "python_runtime_migration_policy",
    "raw_accessed", "readiness", "ready_for_bulk_download_now",
    "ready_for_training",
    "ready_for_unified_dispatch_runtime_with_admit_001_to_015_implementation",
    "real_download_executed", "real_provider_evaluation_ready",
    "real_training_ready",
    "recommended_next_step", "registry_changed",
    "remaining_open_issue_ids", "result_fields",
    "result_schema_version", "routing_matrix_row_count", "runtime_changed",
    "safety_row_count", "shared_dispatch_error_identity_preserved",
    "shared_result_identity_preserved", "source_boundary_name",
    "source_exact9_validation", "source_failure_dispatch_code",
    "source_input_count", "source_input_paths", "source_input_sha256",
    "source_input_verification", "source_invariant_invalid_reason",
    "source_oracle_full_exact9_exact_type_value_equality_required",
    "source_path_list_sha256", "source_path_sha256_pairs_sha256",
    "source_read_policy",
    "source_type_invalid_reason",
    "source_validation_before_candidate_or_output_read",
    "source_validation_before_oracle", "stage",
    "stage_authorization_contract", "standalone_result_fields", "step",
    "step12d_is_final_training_feature_contract", "step12d_status",
    "synthetic_true_case_changes_current_permission",
    "unified_dispatch_runtime_with_admit_001_to_014_implemented",
    "unified_dispatch_runtime_with_admit_001_to_015_implemented",
    "validation_failures",
)))
MANIFEST_NESTED_KEYS = {
    "forbidden_envelope_contract": tuple(sorted((
        "batch_context", "evaluation_context", "download_result_context",
    ))),
    "stage_authorization_contract": tuple(sorted((
        "authoritative_envelope", "authoritative_key", "value_contract",
        "adapter_prevalidation", "adapter_direct_target_access_count",
        "formal_call_count", "oracle_call_count",
        "stable_mapping_formal_target_access_count",
        "stable_mapping_oracle_target_access_count",
        "stable_mapping_total_target_access_count", "target_access_order",
        "none_or_non_mapping_target_access_count",
        "identity_preserved_to_formal", "identity_preserved_to_oracle",
        "download_coexistence_item",
    ))),
    "candidate_record_contract": tuple(sorted((
        "mapping_required", "candidate_key_access_count", "authority_source",
    ))),
    "candidate_invalid_call_counts": tuple(sorted((
        "formal", "oracle", "candidate_key_access", "stage_target_access",
    ))),
    "exact13_projection": tuple(sorted((
        "copied_fields", "fixed_fields", "normalized_values",
        "validated_candidate_fields", "consumed_candidate_fields",
        "consumed_context_items",
    ))),
    "precondition_transition": tuple(sorted((
        "row_count", "complete_count", "supported_but_not_frozen_count",
        "incomplete_count",
        "implementation_blocking_count", "resolved_precondition_ids",
        "resolution", "remaining_open_precondition_ids",
    ))),
    "readiness": tuple(sorted((
        "admit_015_preconditions_audited",
        "admit_015_training_authorization_contract_frozen",
        "admit_015_formal_evaluator_interface_contract_frozen",
        "admit_015_standalone_evaluator_implemented",
        "evaluate_admit_015_implemented",
        "Admit015EvaluationResult_implemented",
        "admit_015_rule_logic_implemented",
        "admit_015_unified_adapter_contract_frozen",
        "admit_015_exact13_projection_frozen",
        "admit_015_context_routing_contract_frozen",
        "admit_015_source_oracle_equivalence_contract_frozen",
        "ready_for_unified_dispatch_runtime_with_admit_001_to_015_implementation",
        "unified_dispatch_runtime_with_admit_001_to_014_implemented",
        "feature_semantics_audit_required_before_training",
        "feature_semantics_audit_completed",
        "admit_015_unified_adapter_implemented",
        "future_adapter_handler_implemented",
        "admit_015_registered_in_engine",
        "unified_dispatch_runtime_with_admit_001_to_015_implemented",
        "mandatory_training_authorization_enforcement_api_frozen",
        "mandatory_training_authorization_enforcement_implemented",
        "historical_unknown_atom_feature_policy_resolved",
        "historical_feature_semantics_known", "real_training_ready",
        "provider_mapping_validated", "real_provider_evaluation_ready",
        "ready_for_bulk_download_now",
        "combined_candidate_verdict_implemented",
        "cross_rule_aggregation_implemented", "ready_for_training",
        "step12d_is_final_training_feature_contract",
    ))),
    "output_sha256": tuple(sorted(OUTPUTS[:5])),
    "source_input_sha256": tuple(sorted(
        path for path, _ in SOURCE_BOUNDARY
    )),
    "future_adapter_handler_signature_evidence": tuple(sorted((
        "signature_text", "parameter_order", "parameter_kinds",
        "required_count", "annotations", "return_annotation",
        "has_varargs", "has_varkw",
    ))),
    "source_read_policy": tuple(sorted((
        "six_field_identity", "leaf_fd_retained_through_final_checks",
        "second_leaf_fd_check", "second_leaf_lexical_check",
        "parent_fd_and_lexical_checks", "root_fd_and_lexical_checks",
    ))),
    "output_read_policy": tuple(sorted((
        "exact6_inventory", "all_leaf_fds_retained", "second_inventory",
        "second_leaf_checks", "second_root_parent_checks",
    ))),
    "materialization_policy": tuple(sorted((
        "authenticated_retained_path_reported_only_when_binding_verified",
        "binding_lost_reports_authenticated_path_none",
        "binding_lost_reports_frozen_identity",
        "build_before_mutation", "exclusive_leaf_create",
        "rename_noreplace_required", "staging_fd_lexical_binding",
        "binding_rechecked_inside_rename", "gpfs_einval_fails_closed",
        "held_parent_fd_only_is_insufficient_for_path_authentication",
        "no_atomic_parent_path_compare_and_rename_claim",
        "concurrent_eexist_fails_closed", "os_replace_forbidden",
        "parent_binding_loss_reports_authenticated_path_none",
        "parent_binding_rechecked_inside_rename",
        "parent_lexical_binding_required_for_authenticated_retained_path",
        "exact_noop_inode_preserving", "successful_publish_no_residue",
        "failure_staging_object_retained", "failure_staging_retained",
        "failure_unlink_forbidden", "failure_rmdir_forbidden",
        "foreign_lexical_name_never_reported_as_owned",
        "last_known_name_is_not_authority", "unknown_identity_never_deleted",
    ))),
    "lifecycle_policy": tuple(sorted((
        "bounded_recursive_no_follow", "ignored_stage_artifacts_rejected",
        "nested_stage_artifacts_rejected",
        "sibling_derived_roots_rejected", "exact10_allowlist",
    ))),
}
SOURCE_VERIFICATION_KEYS = tuple(sorted((
    "source_order", "source_relative_path", "tracked", "base_tree_blob",
    "base_tree_mode", "index_blob", "index_mode", "index_stage",
    "filesystem_regular", "non_symlink", "parent_chain_non_symlink",
    "safe_descendant", "pinned_fd_read", "post_read_identity_verified",
    "expected_sha256", "base_tree_sha256", "filesystem_sha256",
    "source_verified",
)))


def _parse_manifest_exact(data: bytes) -> dict[str, object]:
    try:
        manifest = json.loads(
            data.decode("utf-8"), object_pairs_hook=_unique_object
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("manifest JSON invalid") from error
    if type(manifest) is not dict or tuple(manifest) != MANIFEST_TOP_LEVEL_KEYS:
        raise ValueError("manifest exact top-level schema/order drift")
    for name, expected in MANIFEST_NESTED_KEYS.items():
        value = manifest[name]
        if type(value) is not dict or tuple(value) != expected:
            raise ValueError(f"manifest nested schema/order drift: {name}")
    projection = manifest["exact13_projection"]
    if (
        type(projection["fixed_fields"]) is not dict
        or tuple(projection["fixed_fields"])
        != tuple(sorted(("schema_version", "admission_rule_name", "adapter_id")))
    ):
        raise ValueError("manifest projection fixed_fields schema/order drift")
    evidence = manifest["future_adapter_handler_signature_evidence"]
    if (
        type(evidence["annotations"]) is not dict
        or tuple(evidence["annotations"]) != tuple(sorted((
            "candidate_record", "batch_context", "evaluation_context",
            "download_result_context", "stage_authorization_context",
        )))
    ):
        raise ValueError("manifest signature annotations schema/order drift")
    verification = manifest["source_input_verification"]
    if type(verification) is not list or len(verification) != 17:
        raise ValueError("manifest source verification Exact17 drift")
    for item in verification:
        if type(item) is not dict or tuple(item) != SOURCE_VERIFICATION_KEYS:
            raise ValueError("manifest source verification schema/order drift")
    return manifest


STANDALONE_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_stage_authorization_record",
    "validated_stage_authorization_fields",
    "consumed_stage_authorization_fields", "evaluator_io_used",
)
ROUTING_HEADER = (
    "matrix_order", "matrix_group", "case_id", "routing_condition",
    "envelope_representation", "candidate_key_access_count",
    "adapter_stage_key_access_count", "formal_call_count",
    "oracle_call_count", "formal_stage_key_access_count",
    "oracle_stage_key_access_count", "identity_preserved",
    "expected_dispatch_code", "expected_reason", "expected_result_json",
    "observed_dispatch_code", "observed_reason", "observed_result_json",
    "observed_call_order", "observed_identity_preserved",
    "observed_candidate_key_access_count",
    "observed_adapter_stage_key_access_count",
    "observed_formal_call_count", "observed_oracle_call_count",
    "observed_formal_stage_key_access_count",
    "observed_oracle_stage_key_access_count", "case_passed",
)
TRUTH_HEADER = (
    "case_order", "case_id", "case_group", "routing_condition",
    "source_result_representation", "oracle_result_representation",
    "expected_unified_result_json", "observed_unified_result_json",
    "exact13_type_value_equality", "case_passed",
)
TARGET_ITEM = "current_stage_training_authorized"
DOWNLOAD_ITEM = "current_stage_download_authorized"
SOURCE_TYPE_ERROR = "ADMIT_015_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
SOURCE_INVARIANT_ERROR = "ADMIT_015_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"


def _csv_payload(
    content: bytes, expected_header: tuple[str, ...],
) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content.decode(), newline=""))
    if tuple(reader.fieldnames or ()) != expected_header:
        raise ValueError("CSV exact header drift")
    result = list(reader)
    if any(
        tuple(row) != expected_header
        or any(value is None for value in row.values())
        for row in result
    ):
        raise ValueError("CSV row shape drift")
    return result


def _exact_json(value: object, names: tuple[str, ...]) -> str:
    return json.dumps(
        {name: getattr(value, name) for name in names},
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _expected_unified_json(
    outcome: str,
    reason: str,
    *,
    normalized: tuple[tuple[str, str], ...] = (),
    consumed: tuple[str, ...] = (),
) -> str:
    value = {
        "schema_version": "covapie_unified_admission_rule_evaluation_v1",
        "admission_rule_id": "ADMIT_015",
        "admission_rule_name": "current_gate_grants_no_training_permission",
        "outcome": outcome,
        "passed": outcome == "passed",
        "blocks_candidate": outcome != "passed",
        "reason": reason,
        "normalized_values": normalized,
        "validated_candidate_fields": (),
        "consumed_candidate_fields": (),
        "consumed_context_items": consumed,
        "evaluator_io_used": False,
        "adapter_id": "covapie_admit_015_unified_adapter_v1",
    }
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def _expected_error_json(code: str, reason: str, ready: bool) -> str:
    return json.dumps(
        {
            "code": code,
            "admission_rule_id": "ADMIT_015",
            "known_rule": True,
            "callable_discovered": True,
            "adapter_ready": ready,
            "reason": reason,
        },
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _independent_route_specs() -> tuple[dict[str, object], ...]:
    context_code = "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"
    adapter_code = "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    batch_reason = "ADMIT_015_BATCH_CONTEXT_MUST_BE_NONE"
    evaluation_reason = "ADMIT_015_EVALUATION_CONTEXT_MUST_BE_NONE"
    download_reason = "ADMIT_015_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"
    candidate_reason = "ADMIT_015_CANDIDATE_RECORD_MAPPING_INVALID"
    required_reason = "STAGE_AUTHORIZATION_CONTEXT_REQUIRED"
    mapping_reason = "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID"
    missing_reason = "CURRENT_STAGE_TRAINING_AUTHORIZED_MISSING"
    lookup_reason = "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED"
    false_reason = "TRAINING_NOT_AUTHORIZED"
    required = _expected_unified_json("blocked", required_reason)
    mapping = _expected_unified_json("blocked", mapping_reason)
    missing = _expected_unified_json(
        "blocked", missing_reason, consumed=(TARGET_ITEM,)
    )
    lookup = _expected_unified_json(
        "blocked", lookup_reason, consumed=(TARGET_ITEM,)
    )
    false_result = _expected_unified_json(
        "blocked", false_reason,
        normalized=((TARGET_ITEM, "false"),), consumed=(TARGET_ITEM,),
    )
    true_result = _expected_unified_json(
        "passed", "", normalized=((TARGET_ITEM, "true"),),
        consumed=(TARGET_ITEM,),
    )
    candidate = _expected_unified_json("invalid", candidate_reason)

    def entry(
        group: str,
        case_id: str,
        scenario: str,
        *,
        code: str = "",
        reason: str = "",
        result: str = "",
        formal: int = 0,
        oracle: int = 0,
        formal_access: int = 0,
        oracle_access: int = 0,
        identity: str = "n/a",
    ) -> dict[str, object]:
        return {
            "group": group, "case_id": case_id, "scenario": scenario,
            "code": code, "reason": reason, "result": result,
            "formal": formal, "oracle": oracle,
            "formal_access": formal_access,
            "oracle_access": oracle_access, "identity": identity,
        }

    context = lambda reason: _expected_error_json(
        context_code, reason, True
    )
    adapter = lambda reason: _expected_error_json(
        adapter_code, reason, False
    )
    specs = (
        entry("routing_failure", "batch_non_none", "batch_object", code=context_code, reason=batch_reason, result=context(batch_reason)),
        entry("routing_failure", "batch_empty_mapping", "batch_mapping", code=context_code, reason=batch_reason, result=context(batch_reason)),
        entry("routing_failure", "evaluation_non_none", "evaluation_object", code=context_code, reason=evaluation_reason, result=context(evaluation_reason)),
        entry("routing_failure", "evaluation_empty_mapping", "evaluation_mapping", code=context_code, reason=evaluation_reason, result=context(evaluation_reason)),
        entry("routing_failure", "download_non_none", "download_object", code=context_code, reason=download_reason, result=context(download_reason)),
        entry("routing_failure", "download_empty_mapping", "download_mapping", code=context_code, reason=download_reason, result=context(download_reason)),
        entry("routing_failure", "multiple_invalid_batch_first", "all_invalid", code=context_code, reason=batch_reason, result=context(batch_reason)),
        entry("routing_failure", "multiple_invalid_evaluation_first", "evaluation_download_candidate_invalid", code=context_code, reason=evaluation_reason, result=context(evaluation_reason)),
        entry("routing_failure", "multiple_invalid_download_first", "download_candidate_invalid", code=context_code, reason=download_reason, result=context(download_reason)),
        entry("candidate", "candidate_non_mapping", "candidate_invalid", reason=candidate_reason, result=candidate),
        entry("candidate", "candidate_empty", "candidate_empty", reason=required_reason, result=required, formal=1, oracle=1, identity="true"),
        entry("candidate", "candidate_instrumented", "candidate_probe", reason=required_reason, result=required, formal=1, oracle=1, identity="true"),
        entry("stage", "stage_none", "stage_none", reason=required_reason, result=required, formal=1, oracle=1, identity="true"),
        entry("stage", "stage_object", "stage_object", reason=mapping_reason, result=mapping, formal=1, oracle=1, identity="true"),
        entry("stage", "stage_empty_mapping", "stage_empty", reason=missing_reason, result=missing, formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
        entry("stage", "stage_false", "stage_false", reason=false_reason, result=false_result, formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
        entry("stage", "stage_true", "stage_true", result=true_result, formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
        entry("stage", "stage_extra_keys", "stage_extra", result=true_result, formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
        entry("stage", "stage_keyerror", "stage_keyerror", reason=missing_reason, result=missing, formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
        entry("stage", "stage_runtimeerror", "stage_runtimeerror", reason=lookup_reason, result=lookup, formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
        entry("stage", "stage_valueerror", "stage_valueerror", reason=lookup_reason, result=lookup, formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
        entry("calls", "formal_once", "stage_true", result=true_result, formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
        entry("calls", "oracle_once", "stage_true", result=true_result, formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
        entry("calls", "source_invalid_no_oracle", "source_wrong_type", code=adapter_code, reason=SOURCE_TYPE_ERROR, result=adapter(SOURCE_TYPE_ERROR), formal=1, identity="true"),
        entry("calls", "nonrepeatable_mismatch", "nonrepeatable", code=adapter_code, reason=SOURCE_INVARIANT_ERROR, result=adapter(SOURCE_INVARIANT_ERROR), formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
        entry("source_failure", "source_wrong_type", "source_wrong_type", code=adapter_code, reason=SOURCE_TYPE_ERROR, result=adapter(SOURCE_TYPE_ERROR), formal=1, identity="true"),
        entry("source_failure", "source_subclass", "source_subclass", code=adapter_code, reason=SOURCE_TYPE_ERROR, result=adapter(SOURCE_TYPE_ERROR), formal=1, identity="true"),
        entry("source_failure", "source_storage_order", "source_storage", code=adapter_code, reason=SOURCE_INVARIANT_ERROR, result=adapter(SOURCE_INVARIANT_ERROR), formal=1, identity="true"),
        entry("source_failure", "source_type_drift", "source_type_drift", code=adapter_code, reason=SOURCE_INVARIANT_ERROR, result=adapter(SOURCE_INVARIANT_ERROR), formal=1, identity="true"),
        entry("source_failure", "source_invariant", "source_invariant", code=adapter_code, reason=SOURCE_INVARIANT_ERROR, result=adapter(SOURCE_INVARIANT_ERROR), formal=1, identity="true"),
        entry("oracle_failure", "oracle_wrong_type", "oracle_wrong_type", code=adapter_code, reason=SOURCE_INVARIANT_ERROR, result=adapter(SOURCE_INVARIANT_ERROR), formal=1, oracle=1, identity="true"),
        entry("oracle_failure", "oracle_storage", "oracle_storage", code=adapter_code, reason=SOURCE_INVARIANT_ERROR, result=adapter(SOURCE_INVARIANT_ERROR), formal=1, oracle=1, identity="true"),
        entry("oracle_failure", "oracle_mismatch", "oracle_mismatch", code=adapter_code, reason=SOURCE_INVARIANT_ERROR, result=adapter(SOURCE_INVARIANT_ERROR), formal=1, oracle=1, identity="true"),
        entry("oracle_failure", "oracle_exception", "oracle_exception", code=adapter_code, reason=SOURCE_INVARIANT_ERROR, result=adapter(SOURCE_INVARIANT_ERROR), formal=1, oracle=1, identity="true"),
        entry("projection", "candidate_fields_empty", "stage_true", result=true_result, formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
        entry("projection", "consumed_context", "stage_true", result=true_result, formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
        entry("projection", "false_lowercase", "stage_false", reason=false_reason, result=false_result, formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
        entry("projection", "true_lowercase", "stage_true", result=true_result, formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
        entry("registry", "current_exact14", "stage_true", result=true_result, formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
        entry("registry", "future_exact15", "stage_true", result=true_result, formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
        entry("registry", "known_unregistered", "stage_true", result=true_result, formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
        entry("registry", "handler_identity", "stage_true", result=true_result, formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true"),
    )
    route_text = (
        ("batch_non_none", "first failure: batch must be None", "batch=object"),
        ("batch_empty_mapping", "empty mapping is not None", "batch={}"),
        ("evaluation_non_none", "second failure: evaluation must be None", "evaluation=object"),
        ("evaluation_empty_mapping", "empty mapping is not None", "evaluation={}"),
        ("download_non_none", "third failure: download result must be None", "download=object"),
        ("download_empty_mapping", "empty mapping is not None", "download={}"),
        ("multiple_invalid_batch_first", "batch wins over all later failures", "all forbidden non-None"),
        ("multiple_invalid_evaluation_first", "evaluation wins over download and candidate", "evaluation/download non-None"),
        ("multiple_invalid_download_first", "download wins over candidate", "download non-None candidate invalid"),
        ("candidate_non_mapping", "fourth check returns invalid Exact13", "candidate=object"),
        ("candidate_empty", "empty Mapping is valid and never read", "candidate={};stage=None"),
        ("candidate_instrumented", "candidate Mapping key access remains zero", "candidate=instrumented;stage=None"),
        ("stage_none", "None forwarded without routing error", "stage=None"),
        ("stage_object", "non-Mapping forwarded without routing error", "stage=object"),
        ("stage_empty_mapping", "empty Mapping accessed by formal then oracle", "stage={}"),
        ("stage_false", "exact False accessed twice and projected lowercase", "stage={target:False}"),
        ("stage_true", "exact True accessed twice and projected lowercase", "stage={target:True}"),
        ("stage_extra_keys", "extra keys and download item not accessed", "stage={target:True,download:True,extra:1}"),
        ("stage_keyerror", "KeyError evaluated independently twice", "stage=KeyError mapping"),
        ("stage_runtimeerror", "RuntimeError evaluated independently twice", "stage=RuntimeError mapping"),
        ("stage_valueerror", "ValueError evaluated independently twice", "stage=ValueError mapping"),
        ("formal_once", "formal called exactly once", "stable Mapping"),
        ("oracle_once", "oracle called once after source validation", "stable Mapping"),
        ("source_invalid_no_oracle", "source prevalidation precedes oracle", "formal wrong type"),
        ("nonrepeatable_mismatch", "formal/oracle mismatch fails closed", "stateful Mapping"),
        ("source_wrong_type", "exact formal result type required", "formal=object"),
        ("source_subclass", "formal result subclass rejected", "formal=subclass"),
        ("source_storage_order", "Exact9 storage order required", "formal=reordered"),
        ("source_type_drift", "Exact9 top-level types required", "formal=type drift"),
        ("source_invariant", "Exact9 constructor invariants required", "formal=contradiction"),
        ("oracle_wrong_type", "exact oracle result type required", "oracle=object"),
        ("oracle_storage", "oracle Exact9 storage/order required", "oracle=reordered"),
        ("oracle_mismatch", "all Exact9 types and values must match", "oracle=value drift"),
        ("oracle_exception", "oracle exception fails closed", "oracle=raises"),
        ("candidate_fields_empty", "stage fields never become candidate fields", "valid source"),
        ("consumed_context", "consumed stage field maps to context item", "valid source"),
        ("false_lowercase", "False projects to exact lowercase false", "stage={target:False}"),
        ("true_lowercase", "True projects to exact lowercase true", "stage={target:True}"),
        ("current_exact14", "current registry remains ADMIT_001..014", "ADMIT_001..014"),
        ("future_exact15", "future order appends ADMIT_015 only", "ADMIT_001..015"),
        ("known_unregistered", "ADMIT_015 is currently known-not-registered", "ADMIT_015"),
        ("handler_identity", "first fourteen handler identities preserved", "identity_preserved"),
    )
    if tuple(spec["case_id"] for spec in specs) != tuple(
        case_id for case_id, _, _ in route_text
    ):
        raise ValueError("independent routing identity/text drift")
    return tuple(
        {
            **spec,
            "condition": condition,
            "envelope": envelope,
        }
        for spec, (_, condition, envelope) in zip(
            specs, route_text, strict=True
        )
    )


class _IndependentCandidateProbe(Mapping[str, object]):
    def __init__(self) -> None:
        self.access_count = 0

    def __getitem__(self, key: str) -> object:
        self.access_count += 1
        raise AssertionError("candidate read")

    def __iter__(self):
        self.access_count += 1
        raise AssertionError("candidate iteration")

    def __len__(self) -> int:
        self.access_count += 1
        raise AssertionError("candidate length")

    def get(self, key: str, default: object = None) -> object:
        self.access_count += 1
        raise AssertionError("candidate get")

    def __contains__(self, key: object) -> bool:
        self.access_count += 1
        raise AssertionError("candidate contains")


class _IndependentStageProbe(Mapping[str, object]):
    def __init__(
        self,
        values: Mapping[str, object] | None = None,
        *,
        error: BaseException | None = None,
        alternating: bool = False,
    ) -> None:
        self.values = {} if values is None else dict(values)
        self.error = error
        self.alternating = alternating
        self.access_count = 0

    def __getitem__(self, key: str) -> object:
        self.access_count += 1
        if self.error is not None:
            raise self.error
        if self.alternating:
            return self.access_count == 1
        return self.values[key]

    def __iter__(self):
        raise AssertionError("stage iteration")

    def __len__(self) -> int:
        raise AssertionError("stage length")


def _mutate_independent_exact9(value: object, scenario: str) -> object:
    if scenario.endswith("wrong_type"):
        return object()
    if scenario == "source_subclass":
        try:
            subclass = type("_IndependentSourceSubclass", (type(value),), {})
        except TypeError:
            return object()
        instance = object.__new__(subclass)
        for name in STANDALONE_FIELDS:
            object.__setattr__(instance, name, getattr(value, name))
        return instance
    if scenario in {"source_storage", "oracle_storage"}:
        storage = vars(value)
        reordered = {name: storage[name] for name in reversed(tuple(storage))}
        storage.clear()
        storage.update(reordered)
    elif scenario == "source_type_drift":
        object.__setattr__(value, "outcome", 1)
    elif scenario == "source_invariant":
        object.__setattr__(value, "outcome", "passed")
    return value


def _execute_independent_route(
    module: object, spec: Mapping[str, object],
) -> dict[str, object]:
    formal_module = importlib.import_module(
        "covalent_ext."
        "covapie_bulk_download_admission_admit_015_standalone_evaluator_interface"
    )
    oracle_module = importlib.import_module(
        "covalent_ext."
        "covapie_bulk_download_admission_admit_015_"
        "formal_evaluator_interface_contract_design_gate"
    )
    scenario = spec["scenario"]
    candidate: object = {}
    stage: object = _IndependentStageProbe({TARGET_ITEM: True})
    batch = evaluation = download = None
    if scenario == "batch_object":
        batch = object()
    elif scenario == "batch_mapping":
        batch = {}
    elif scenario == "evaluation_object":
        evaluation = object()
    elif scenario == "evaluation_mapping":
        evaluation = {}
    elif scenario == "download_object":
        download = object()
    elif scenario == "download_mapping":
        download = {}
    elif scenario == "all_invalid":
        batch, evaluation, download, candidate = object(), object(), object(), object()
    elif scenario == "evaluation_download_candidate_invalid":
        evaluation, download, candidate = object(), object(), object()
    elif scenario == "download_candidate_invalid":
        download, candidate = object(), object()
    elif scenario == "candidate_invalid":
        candidate, stage = object(), _IndependentStageProbe()
    elif scenario == "candidate_empty":
        stage = None
    elif scenario == "candidate_probe":
        candidate, stage = _IndependentCandidateProbe(), None
    elif scenario == "stage_none":
        stage = None
    elif scenario == "stage_object":
        stage = object()
    elif scenario == "stage_empty":
        stage = _IndependentStageProbe()
    elif scenario == "stage_false":
        stage = _IndependentStageProbe({TARGET_ITEM: False})
    elif scenario == "stage_extra":
        stage = _IndependentStageProbe({
            TARGET_ITEM: True, DOWNLOAD_ITEM: True, "extra": 1,
        })
    elif scenario == "stage_keyerror":
        stage = _IndependentStageProbe(error=KeyError(TARGET_ITEM))
    elif scenario == "stage_runtimeerror":
        stage = _IndependentStageProbe(error=RuntimeError("checker"))
    elif scenario == "stage_valueerror":
        stage = _IndependentStageProbe(error=ValueError("checker"))
    elif scenario == "nonrepeatable":
        stage = _IndependentStageProbe(alternating=True)
    elif str(scenario).startswith(("source_", "oracle_")):
        stage = None

    calls: list[str] = []
    identities: list[bool] = []
    formal_access = oracle_access = 0
    source_representation = "not_called"
    oracle_representation = "not_called"

    def access_count() -> int:
        return (
            stage.access_count
            if isinstance(stage, _IndependentStageProbe)
            else 0
        )

    def formal_call(*, stage_authorization_context: object) -> object:
        nonlocal formal_access, source_representation
        calls.append("formal")
        identities.append(stage_authorization_context is stage)
        before = access_count()
        value = formal_module.evaluate_admit_015(
            stage_authorization_context=stage_authorization_context
        )
        formal_access += access_count() - before
        if str(scenario).startswith("source_"):
            value = _mutate_independent_exact9(value, str(scenario))
        source_representation = (
            "type=subclass"
            if scenario == "source_subclass"
            else _exact_json(value, STANDALONE_FIELDS)
            if type(value) is formal_module.Admit015EvaluationResult
            else f"type={type(value).__name__}"
        )
        return value

    def oracle_call(*, stage_authorization_context: object) -> object:
        nonlocal oracle_access, oracle_representation
        calls.append("oracle")
        identities.append(stage_authorization_context is stage)
        before = access_count()
        if scenario == "oracle_exception":
            oracle_representation = "exception=RuntimeError"
            raise RuntimeError("checker oracle")
        oracle_stage = object() if scenario == "oracle_mismatch" else stage
        value = (
            oracle_module
            .classify_admit_015_formal_evaluator_interface_design(
                stage_authorization_context=oracle_stage
            )
        )
        oracle_access += access_count() - before
        if str(scenario).startswith("oracle_"):
            value = _mutate_independent_exact9(value, str(scenario))
        oracle_representation = (
            _exact_json(value, STANDALONE_FIELDS)
            if type(value)
            is oracle_module.Admit015EvaluationResultContractDesign
            else f"type={type(value).__name__}"
        )
        return value

    code = reason = result_json = ""
    try:
        result = module.simulate_admit_015_unified_adapter_contract_design(
            candidate,
            batch_context=batch,
            evaluation_context=evaluation,
            download_result_context=download,
            stage_authorization_context=stage,
            formal_evaluator=formal_call,
            oracle_callable=oracle_call,
        )
        reason = result.reason
        result_json = _exact_json(result, RESULT_FIELDS)
    except module.AdapterContractDesignError as error:
        code = error.code
        reason = error.reason
        result_json = json.dumps(
            {
                name: getattr(error, name)
                for name in (
                    "code", "admission_rule_id", "known_rule",
                    "callable_discovered", "adapter_ready", "reason",
                )
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
    candidate_access = (
        candidate.access_count
        if isinstance(candidate, _IndependentCandidateProbe)
        else 0
    )
    total_stage_access = access_count()
    return {
        "code": code, "reason": reason, "result": result_json,
        "call_order": "|".join(calls),
        "identity": (
            "n/a" if not identities else str(all(identities)).lower()
        ),
        "candidate_access": candidate_access,
        "adapter_access": total_stage_access - formal_access - oracle_access,
        "formal": calls.count("formal"), "oracle": calls.count("oracle"),
        "formal_access": formal_access, "oracle_access": oracle_access,
        "source_representation": source_representation,
        "oracle_representation": oracle_representation,
    }


def _verify_routing(
    module: object, routing: list[dict[str, str]],
) -> dict[str, dict[str, object]]:
    specs = _independent_route_specs()
    if len(specs) != 42 or len(routing) != 42:
        raise ValueError("routing Exact42 drift")
    observations = {}
    for index, (spec, row) in enumerate(zip(specs, routing, strict=True), 1):
        actual = _execute_independent_route(module, spec)
        expected_order = (
            "formal|oracle" if spec["oracle"] == 1
            else "formal" if spec["formal"] == 1
            else ""
        )
        expected_pairs = {
            "matrix_order": str(index),
            "matrix_group": str(spec["group"]),
            "case_id": str(spec["case_id"]),
            "routing_condition": str(spec["condition"]),
            "envelope_representation": str(spec["envelope"]),
            "candidate_key_access_count": "0",
            "adapter_stage_key_access_count": "0",
            "formal_call_count": str(spec["formal"]),
            "oracle_call_count": str(spec["oracle"]),
            "formal_stage_key_access_count": str(spec["formal_access"]),
            "oracle_stage_key_access_count": str(spec["oracle_access"]),
            "identity_preserved": str(spec["identity"]),
            "expected_dispatch_code": str(spec["code"]),
            "expected_reason": str(spec["reason"]),
            "expected_result_json": str(spec["result"]),
        }
        observed_pairs = {
            "observed_dispatch_code": str(actual["code"]),
            "observed_reason": str(actual["reason"]),
            "observed_result_json": str(actual["result"]),
            "observed_call_order": str(actual["call_order"]),
            "observed_identity_preserved": str(actual["identity"]),
            "observed_candidate_key_access_count": str(
                actual["candidate_access"]
            ),
            "observed_adapter_stage_key_access_count": str(
                actual["adapter_access"]
            ),
            "observed_formal_call_count": str(actual["formal"]),
            "observed_oracle_call_count": str(actual["oracle"]),
            "observed_formal_stage_key_access_count": str(
                actual["formal_access"]
            ),
            "observed_oracle_stage_key_access_count": str(
                actual["oracle_access"]
            ),
        }
        if (
            any(row[name] != value for name, value in expected_pairs.items())
            or any(row[name] != value for name, value in observed_pairs.items())
            or actual["code"] != spec["code"]
            or actual["reason"] != spec["reason"]
            or actual["result"] != spec["result"]
            or actual["call_order"] != expected_order
            or actual["identity"] != spec["identity"]
            or actual["candidate_access"] != 0
            or actual["adapter_access"] != 0
            or actual["formal"] != spec["formal"]
            or actual["oracle"] != spec["oracle"]
            or actual["formal_access"] != spec["formal_access"]
            or actual["oracle_access"] != spec["oracle_access"]
            or row["case_passed"] != "true"
        ):
            raise ValueError(f"independent routing case failed: {spec['case_id']}")
        observations[str(spec["case_id"])] = actual
    return observations


def verify_candidate_ast() -> dict[str, object]:
    content = _pinned_source_read(ROOT, PRODUCTION)
    digest = _sha_bytes(content)
    if digest != PRODUCTION_SHA256:
        raise ValueError("production SHA drift")
    tree = ast.parse(content)
    top_functions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    top_assignments = {
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (
            node.targets if isinstance(node, ast.Assign) else (node.target,)
        )
        if isinstance(target, ast.Name)
    }
    if (
        "_evaluate_registered_admit_015" in top_functions
        or "evaluate_admission_rule" in top_functions
        or "EVALUATOR_REGISTRY" in top_assignments
        or "simulate_admit_015_unified_adapter_contract_design"
        not in top_functions
        or "FUTURE_HANDLER_SIGNATURE_DESIGN" not in top_assignments
        or b"os.replace" in content
    ):
        raise ValueError("production design-only AST boundary drift")
    return {"content": content, "sha256": digest}


def import_production() -> object:
    spec = importlib.util.spec_from_file_location(
        "admit015_adapter_design_revised1_check", ROOT / PRODUCTION
    )
    if spec is None or spec.loader is None:
        raise ValueError("production isolated import unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _expected_future_signature() -> inspect.Signature:
    return inspect.Signature(
        parameters=(
            inspect.Parameter(
                "candidate_record",
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=object,
            ),
            inspect.Parameter(
                "batch_context",
                inspect.Parameter.KEYWORD_ONLY,
                annotation=object,
            ),
            inspect.Parameter(
                "evaluation_context",
                inspect.Parameter.KEYWORD_ONLY,
                annotation=object,
            ),
            inspect.Parameter(
                "download_result_context",
                inspect.Parameter.KEYWORD_ONLY,
                annotation=object,
            ),
            inspect.Parameter(
                "stage_authorization_context",
                inspect.Parameter.KEYWORD_ONLY,
                annotation=object,
            ),
        ),
        return_annotation="UnifiedAdmissionRuleEvaluation",
    )


def _assert_future_signature(module: object) -> str:
    expected = _expected_future_signature()
    actual = module.FUTURE_HANDLER_SIGNATURE_DESIGN
    if (
        type(actual) is not inspect.Signature
        or actual != expected
        or len(actual.parameters) != 5
        or any(
            parameter.default is not inspect.Parameter.empty
            or parameter.annotation is not object
            for parameter in actual.parameters.values()
        )
        or any(
            parameter.kind in {
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            }
            for parameter in actual.parameters.values()
        )
        or actual.return_annotation != "UnifiedAdmissionRuleEvaluation"
    ):
        raise ValueError("future handler inspect.Signature drift")
    text = "_evaluate_registered_admit_015" + str(expected)
    if module.FUTURE_HANDLER_SIGNATURE_TEXT != text:
        raise ValueError("future handler signature text drift")
    return text


def _expect_adapter_failure(
    module: object,
    *,
    formal_callable: object | None = None,
    oracle_callable: object | None = None,
    expected_reason: str,
) -> None:
    try:
        module.simulate_admit_015_unified_adapter_contract_design(
            {},
            batch_context=None,
            evaluation_context=None,
            download_result_context=None,
            stage_authorization_context=None,
            formal_evaluator=formal_callable,
            oracle_callable=oracle_callable,
        )
    except module.AdapterContractDesignError as error:
        if (
            error.code != "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
            or error.reason != expected_reason
            or error.adapter_ready is not False
        ):
            raise ValueError("negative Exact9 failure representation drift")
    else:
        raise ValueError("negative Exact9 case did not fail closed")


def _source_negative_value(
    formal_module: object, mutation: str,
) -> object:
    value = formal_module.evaluate_admit_015(
        stage_authorization_context=None
    )
    if mutation == "subclass":
        try:
            subtype = type("_CheckerSourceSubclass", (type(value),), {})
        except TypeError:
            return object()
        instance = object.__new__(subtype)
        for name in STANDALONE_FIELDS:
            object.__setattr__(instance, name, getattr(value, name))
        return instance
    if mutation == "storage_reorder":
        storage = vars(value)
        reordered = {name: storage[name] for name in reversed(tuple(storage))}
        storage.clear()
        storage.update(reordered)
    elif mutation == "top_level_type":
        object.__setattr__(value, "outcome", 1)
    elif mutation == "admission_rule_id":
        object.__setattr__(value, "admission_rule_id", "ADMIT_999")
    elif mutation == "evaluator_io":
        object.__setattr__(value, "evaluator_io_used", True)
    elif mutation == "outcome_reason":
        object.__setattr__(value, "outcome", "passed")
    elif mutation == "canonical":
        object.__setattr__(
            value, "canonical_stage_authorization_record",
            (("unexpected", True),),
        )
    elif mutation == "validated_tuple":
        object.__setattr__(
            value, "validated_stage_authorization_fields", (1,)
        )
    elif mutation == "consumed_tuple":
        object.__setattr__(
            value, "consumed_stage_authorization_fields", (1,)
        )
    return value


def _oracle_negative_value(
    oracle_module: object, mutation: str,
) -> object:
    value = (
        oracle_module
        .classify_admit_015_formal_evaluator_interface_design(
            stage_authorization_context=None
        )
    )
    if mutation == "subclass":
        try:
            subtype = type("_CheckerOracleSubclass", (type(value),), {})
        except TypeError:
            return object()
        instance = object.__new__(subtype)
        for name in STANDALONE_FIELDS:
            object.__setattr__(instance, name, getattr(value, name))
        return instance
    if mutation == "storage_reorder":
        storage = vars(value)
        reordered = {name: storage[name] for name in reversed(tuple(storage))}
        storage.clear()
        storage.update(reordered)
    elif mutation == "top_level_type":
        object.__setattr__(value, "outcome", 1)
    elif mutation == "admission_rule_id":
        object.__setattr__(value, "admission_rule_id", "ADMIT_999")
    return value


def _verify_negative_exact9_contracts(module: object) -> None:
    formal_module = importlib.import_module(
        "covalent_ext."
        "covapie_bulk_download_admission_admit_015_standalone_evaluator_interface"
    )
    oracle_module = importlib.import_module(
        "covalent_ext."
        "covapie_bulk_download_admission_admit_015_"
        "formal_evaluator_interface_contract_design_gate"
    )
    oracle_calls = []
    _expect_adapter_failure(
        module,
        formal_callable=lambda **kwargs: object(),
        oracle_callable=lambda **kwargs: oracle_calls.append(kwargs),
        expected_reason=SOURCE_TYPE_ERROR,
    )
    if oracle_calls:
        raise ValueError("source-invalid route did not skip oracle")
    for mutation in (
        "subclass", "storage_reorder", "top_level_type",
        "admission_rule_id", "evaluator_io", "outcome_reason", "canonical",
        "validated_tuple", "consumed_tuple",
    ):
        calls = []
        _expect_adapter_failure(
            module,
            formal_callable=lambda mutation=mutation, **kwargs: (
                _source_negative_value(formal_module, mutation)
            ),
            oracle_callable=lambda **kwargs: calls.append(kwargs),
            expected_reason=(
                SOURCE_TYPE_ERROR
                if mutation == "subclass"
                else SOURCE_INVARIANT_ERROR
            ),
        )
        if calls:
            raise ValueError("source negative unexpectedly called oracle")
    for mutation in (
        "wrong_type", "subclass", "storage_reorder", "top_level_type",
        "admission_rule_id",
    ):
        if mutation == "wrong_type":
            oracle_callable = lambda **kwargs: object()
        else:
            oracle_callable = lambda mutation=mutation, **kwargs: (
                _oracle_negative_value(oracle_module, mutation)
            )
        _expect_adapter_failure(
            module,
            oracle_callable=oracle_callable,
            expected_reason=SOURCE_INVARIANT_ERROR,
        )
    _expect_adapter_failure(
        module,
        oracle_callable=lambda **kwargs: (_ for _ in ()).throw(
            RuntimeError("oracle exception")
        ),
        expected_reason=SOURCE_INVARIANT_ERROR,
    )
    _expect_adapter_failure(
        module,
        oracle_callable=lambda **kwargs: (
            oracle_module
            .classify_admit_015_formal_evaluator_interface_design(
                stage_authorization_context=object()
            )
        ),
        expected_reason=SOURCE_INVARIANT_ERROR,
    )


def _independent_projection_json(source: object) -> str:
    canonical = source.canonical_stage_authorization_record
    if canonical == ():
        normalized: tuple[tuple[str, str], ...] = ()
    else:
        normalized = ((
            TARGET_ITEM, "true" if canonical[0][1] else "false"
        ),)
    return _expected_unified_json(
        source.outcome,
        source.reason,
        normalized=normalized,
        consumed=source.consumed_stage_authorization_fields,
    )


def _truth_stage_cases() -> tuple[tuple[str, str, object], ...]:
    return (
        ("STAGE_NONE", "business", None),
        ("STAGE_OBJECT", "business", object()),
        ("STAGE_EMPTY", "business", _IndependentStageProbe()),
        ("STAGE_KEYERROR", "business", _IndependentStageProbe()),
        ("STAGE_RUNTIMEERROR", "business", _IndependentStageProbe(error=RuntimeError("x"))),
        ("STAGE_VALUEERROR", "business", _IndependentStageProbe(error=ValueError("x"))),
        ("TYPE_INT_ZERO", "exact_bool_negative", _IndependentStageProbe({TARGET_ITEM: 0})),
        ("TYPE_INT_ONE", "exact_bool_negative", _IndependentStageProbe({TARGET_ITEM: 1})),
        ("TYPE_STRING_FALSE", "exact_bool_negative", _IndependentStageProbe({TARGET_ITEM: "false"})),
        ("TYPE_STRING_TRUE", "exact_bool_negative", _IndependentStageProbe({TARGET_ITEM: "true"})),
        ("TYPE_NONE", "exact_bool_negative", _IndependentStageProbe({TARGET_ITEM: None})),
        ("TYPE_FLOAT", "exact_bool_negative", _IndependentStageProbe({TARGET_ITEM: 0.0})),
        ("TYPE_LIST", "exact_bool_negative", _IndependentStageProbe({TARGET_ITEM: []})),
        ("TYPE_TUPLE", "exact_bool_negative", _IndependentStageProbe({TARGET_ITEM: ()})),
        ("TYPE_OBJECT", "exact_bool_negative", _IndependentStageProbe({TARGET_ITEM: object()})),
        ("EXACT_FALSE", "projection", _IndependentStageProbe({TARGET_ITEM: False})),
        ("EXACT_TRUE", "projection", _IndependentStageProbe({TARGET_ITEM: True})),
        ("ADMIT015_COEXIST", "coexistence", _IndependentStageProbe({TARGET_ITEM: True, DOWNLOAD_ITEM: False})),
        ("EXTRA_KEYS", "coexistence", _IndependentStageProbe({TARGET_ITEM: False, "extra": object()})),
    )


def _verify_truth(
    module: object,
    truth: list[dict[str, str]],
    routing: list[dict[str, str]],
    routing_observations: Mapping[str, Mapping[str, object]],
) -> None:
    if len(truth) != 61:
        raise ValueError("truth Exact61 drift")
    formal_module = importlib.import_module(
        "covalent_ext."
        "covapie_bulk_download_admission_admit_015_standalone_evaluator_interface"
    )
    oracle_module = importlib.import_module(
        "covalent_ext."
        "covapie_bulk_download_admission_admit_015_"
        "formal_evaluator_interface_contract_design_gate"
    )
    for index, ((case_id, group, stage), row) in enumerate(
        zip(_truth_stage_cases(), truth[:19], strict=True), 1
    ):
        source = formal_module.evaluate_admit_015(
            stage_authorization_context=stage
        )
        oracle_result = (
            oracle_module
            .classify_admit_015_formal_evaluator_interface_design(
                stage_authorization_context=stage
            )
        )
        observed = module.simulate_admit_015_unified_adapter_contract_design(
            {},
            batch_context=None,
            evaluation_context=None,
            download_result_context=None,
            stage_authorization_context=stage,
        )
        expected_json = _independent_projection_json(source)
        observed_json = _exact_json(observed, RESULT_FIELDS)
        expected_row = {
            "case_order": str(index),
            "case_id": case_id,
            "case_group": group,
            "routing_condition": "valid five-envelope route",
            "source_result_representation": _exact_json(
                source, STANDALONE_FIELDS
            ),
            "oracle_result_representation": _exact_json(
                oracle_result, STANDALONE_FIELDS
            ),
            "expected_unified_result_json": expected_json,
            "observed_unified_result_json": observed_json,
            "exact13_type_value_equality": "true",
            "case_passed": "true",
        }
        if row != expected_row or expected_json != observed_json:
            raise ValueError(f"independent truth case failed: {case_id}")
    for index, (route, row) in enumerate(
        zip(routing, truth[19:], strict=True), 20
    ):
        observation = routing_observations[route["case_id"]]
        equality = (
            route["expected_result_json"] == route["observed_result_json"]
        )
        expected_row = {
            "case_order": str(index),
            "case_id": f"ROUTING_{route['case_id'].upper()}",
            "case_group": f"routing_{route['matrix_group']}",
            "routing_condition": route["routing_condition"],
            "source_result_representation": observation[
                "source_representation"
            ],
            "oracle_result_representation": observation[
                "oracle_representation"
            ],
            "expected_unified_result_json": route[
                "expected_result_json"
            ],
            "observed_unified_result_json": route[
                "observed_result_json"
            ],
            "exact13_type_value_equality": str(equality).lower(),
            "case_passed": "true",
        }
        if (
            row != expected_row
            or not row["observed_unified_result_json"]
            or route["case_passed"] != "true"
        ):
            raise ValueError(
                f"routing/truth actual evidence drift: {route['case_id']}"
            )


def _verify_registry_identity(module: object) -> None:
    runtime = importlib.import_module(
        "covalent_ext."
        "covapie_bulk_download_admission_unified_dispatch_runtime_"
        "with_admit_001_to_014"
    )
    predecessor = runtime.predecessor
    expected_current = tuple(f"ADMIT_{index:03d}" for index in range(1, 15))
    registry = runtime.EVALUATOR_REGISTRY
    signature = inspect.signature(runtime.evaluate_admission_rule)
    predecessor_signature = inspect.signature(
        predecessor.evaluate_admission_rule
    )
    parameters = tuple(signature.parameters.values())
    future_handler_design = object()
    future_registry = MappingProxyType({
        **registry,
        "ADMIT_015": future_handler_design,
    })
    if (
        type(registry) is not MappingProxyType
        or tuple(registry) != expected_current
        or tuple(runtime.CALLABLE_DISCOVERED_RULE_IDS) != expected_current
        or tuple(runtime.ADAPTER_READY_RULE_IDS) != expected_current
        or any(
            registry[f"ADMIT_{index:03d}"]
            is not predecessor.EVALUATOR_REGISTRY[f"ADMIT_{index:03d}"]
            for index in range(1, 14)
        )
        or registry["ADMIT_014"] is not runtime._evaluate_registered_admit_014
        or runtime.UnifiedAdmissionRuleEvaluation
        is not predecessor.UnifiedAdmissionRuleEvaluation
        or runtime.UnifiedAdmissionDispatchError
        is not predecessor.UnifiedAdmissionDispatchError
        or tuple(runtime.KNOWN_RULE_IDS)
        != tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
        or "ADMIT_015" in runtime.ADAPTER_READY_RULE_IDS
        or "ADMIT_015" in runtime.CALLABLE_DISCOVERED_RULE_IDS
        or signature != predecessor_signature
        or tuple(parameter.name for parameter in parameters) != (
            "admission_rule_id", "candidate_record", "batch_context",
            "evaluation_context", "download_result_context",
            "stage_authorization_context",
        )
        or parameters[0].kind is not inspect.Parameter.POSITIONAL_OR_KEYWORD
        or parameters[1].kind is not inspect.Parameter.POSITIONAL_OR_KEYWORD
        or any(
            parameter.kind is not inspect.Parameter.KEYWORD_ONLY
            for parameter in parameters[2:]
        )
        or tuple(module.CURRENT_REGISTERED_RULE_ORDER) != expected_current
        or tuple(module.FUTURE_REGISTERED_RULE_ORDER)
        != (*expected_current, "ADMIT_015")
        or tuple(module.FUTURE_KNOWN_NOT_REGISTERED) != ()
        or type(future_registry) is not MappingProxyType
        or tuple(future_registry) != (*expected_current, "ADMIT_015")
        or any(
            future_registry[rule_id] is not registry[rule_id]
            for rule_id in expected_current
        )
        or future_registry["ADMIT_015"] is not future_handler_design
        or module.FUTURE_KNOWN_NOT_REGISTERED
    ):
        raise ValueError("current/future registry identity contract drift")


def _verify_manifest_semantics(
    manifest: Mapping[str, object],
    source_records: tuple[dict[str, object], ...],
    signature_text: str,
) -> None:
    true_readiness = (
        "admit_015_preconditions_audited",
        "admit_015_training_authorization_contract_frozen",
        "admit_015_formal_evaluator_interface_contract_frozen",
        "admit_015_standalone_evaluator_implemented",
        "evaluate_admit_015_implemented",
        "Admit015EvaluationResult_implemented",
        "admit_015_rule_logic_implemented",
        "admit_015_unified_adapter_contract_frozen",
        "admit_015_exact13_projection_frozen",
        "admit_015_context_routing_contract_frozen",
        "admit_015_source_oracle_equivalence_contract_frozen",
        "ready_for_unified_dispatch_runtime_with_admit_001_to_015_implementation",
        "unified_dispatch_runtime_with_admit_001_to_014_implemented",
        "feature_semantics_audit_required_before_training",
    )
    false_readiness = (
        "admit_015_unified_adapter_implemented",
        "future_adapter_handler_implemented",
        "admit_015_registered_in_engine",
        "unified_dispatch_runtime_with_admit_001_to_015_implemented",
        "mandatory_training_authorization_enforcement_api_frozen",
        "mandatory_training_authorization_enforcement_implemented",
        "provider_mapping_validated",
        "real_provider_evaluation_ready",
        "ready_for_bulk_download_now",
        "combined_candidate_verdict_implemented",
        "cross_rule_aggregation_implemented",
        "feature_semantics_audit_completed",
        "historical_unknown_atom_feature_policy_resolved",
        "historical_feature_semantics_known",
        "real_training_ready",
        "ready_for_training",
        "step12d_is_final_training_feature_contract",
    )
    expected_readiness = {
        **{name: True for name in true_readiness},
        **{name: False for name in false_readiness},
    }
    expected_signature_evidence = {
        "annotations": {
            "batch_context": "object",
            "candidate_record": "object",
            "download_result_context": "object",
            "evaluation_context": "object",
            "stage_authorization_context": "object",
        },
        "has_varargs": False,
        "has_varkw": False,
        "parameter_kinds": [
            "POSITIONAL_OR_KEYWORD", "KEYWORD_ONLY", "KEYWORD_ONLY",
            "KEYWORD_ONLY", "KEYWORD_ONLY",
        ],
        "parameter_order": [
            "candidate_record", "batch_context", "evaluation_context",
            "download_result_context", "stage_authorization_context",
        ],
        "required_count": 5,
        "return_annotation": "UnifiedAdmissionRuleEvaluation",
        "signature_text": signature_text,
    }
    if (
        manifest["future_adapter_handler_signature"] != signature_text
        or manifest["future_adapter_handler_signature_evidence"]
        != expected_signature_evidence
        or manifest["forbidden_envelope_contract"] != {
            "batch_context": "exact None",
            "download_result_context": "exact None",
            "evaluation_context": "exact None",
        }
        or manifest["candidate_record_contract"] != {
            "authority_source": False,
            "candidate_key_access_count": 0,
            "mapping_required": True,
        }
        or manifest["candidate_invalid_call_counts"] != {
            "candidate_key_access": 0, "formal": 0,
            "oracle": 0, "stage_target_access": 0,
        }
        or manifest["stage_authorization_contract"] != {
            "adapter_direct_target_access_count": 0,
            "adapter_prevalidation": False,
            "download_coexistence_item":
                "current_stage_download_authorized",
            "authoritative_envelope": "stage_authorization_context",
            "authoritative_key": "current_stage_training_authorized",
            "formal_call_count": 1,
            "identity_preserved_to_formal": True,
            "identity_preserved_to_oracle": True,
            "none_or_non_mapping_target_access_count": 0,
            "oracle_call_count": 1,
            "stable_mapping_formal_target_access_count": 1,
            "stable_mapping_oracle_target_access_count": 1,
            "stable_mapping_total_target_access_count": 2,
            "target_access_order": ["formal", "oracle"],
            "value_contract": "exact bool False|True; no normalization",
        }
        or manifest["exact13_projection"] != {
            "consumed_candidate_fields": [],
            "consumed_context_items":
                "source.consumed_stage_authorization_fields",
            "copied_fields": [
                "admission_rule_id", "outcome", "passed",
                "blocks_candidate", "reason", "evaluator_io_used",
            ],
            "fixed_fields": {
                "adapter_id": "covapie_admit_015_unified_adapter_v1",
                "admission_rule_name":
                    "current_gate_grants_no_training_permission",
                "schema_version":
                    "covapie_unified_admission_rule_evaluation_v1",
            },
            "normalized_values": (
                "source canonical exact bool pair projected to lowercase "
                "exact string false|true"
            ),
            "validated_candidate_fields": [],
        }
        or manifest["precondition_transition"] != {
            "complete_count": 38,
            "implementation_blocking_count": 7,
            "incomplete_count": 7,
            "supported_but_not_frozen_count": 0,
            "remaining_open_precondition_ids": [
                "PRE_032", "PRE_033", "PRE_034", "PRE_035",
                "PRE_036", "PRE_038", "PRE_042",
            ],
            "resolution": (
                "ADMIT_015 five-envelope routing, standalone Exact9 "
                "attestation, oracle equivalence and typed Exact13 "
                "projection frozen"
            ),
            "resolved_precondition_ids": ["PRE_031"],
            "row_count": 45,
        }
        or manifest["current_permission"] is not False
        or manifest["authorized_admit_015_training_execution_count"] != 0
        or manifest["coverage_issue_affected_rules"] != "ADMIT_015"
        or manifest["issue_inventory_row_count"] != 30
        or manifest["issue_inventory_sha256"]
        != SOURCE_BOUNDARY[5][1]
        or manifest["issue_inventory_preserved_byte_identical"] is not True
        or manifest["recommended_next_step"]
        != "implement_covapie_unified_dispatch_runtime_with_admit_001_to_015_v1"
        or manifest["future_adapter_handler_implemented"] is not False
        or manifest["registry_changed"] is not False
        or manifest["runtime_changed"] is not False
        or manifest["readiness"] != expected_readiness
        or any(
            manifest[name] is not expected
            for name, expected in expected_readiness.items()
        )
        or manifest["contract_row_count"] != 54
        or manifest["routing_matrix_row_count"] != 42
        or manifest["projection_truth_matrix_row_count"] != 61
        or manifest["safety_row_count"] != 32
        or manifest["source_input_count"] != 17
        or manifest["output_file_count"] != 6
        or manifest["validation_failures"] != []
        or manifest["all_checks_passed"] is not True
    ):
        raise ValueError("manifest semantic contract drift")
    verification = manifest["source_input_verification"]
    for expected, actual in zip(source_records, verification, strict=True):
        for key, value in expected.items():
            if actual[key] != value:
                raise ValueError(f"manifest source identity drift: {key}")
        if (
            actual["tracked"] is not True
            or actual["source_verified"] is not True
            or actual["index_stage"] != 0
            or actual["index_blob"] != actual["base_tree_blob"]
            or actual["index_mode"] != actual["base_tree_mode"]
            or any(
                actual[name] is not True
                for name in (
                    "filesystem_regular", "non_symlink",
                    "parent_chain_non_symlink", "safe_descendant",
                    "pinned_fd_read", "post_read_identity_verified",
                )
            )
            or re.fullmatch(r"[0-9a-f]{40}", actual["base_tree_blob"]) is None
            or re.fullmatch(r"[0-9a-f]{40}", actual["index_blob"]) is None
        ):
            raise ValueError("manifest Exact17 blob evidence drift")


def _assert_exact_object(
    actual: object, expected: object, path: str,
) -> None:
    if type(actual) is not type(expected):
        raise ValueError(f"{path} exact type mismatch")
    if type(expected) is dict:
        if tuple(actual) != tuple(expected):
            raise ValueError(f"{path} exact keys/order mismatch")
        for key in expected:
            _assert_exact_object(
                actual[key], expected[key], f"{path}.{key}"
            )
    elif type(expected) is list:
        if len(actual) != len(expected):
            raise ValueError(f"{path} exact list length mismatch")
        for index, (left, right) in enumerate(
            zip(actual, expected, strict=True)
        ):
            _assert_exact_object(left, right, f"{path}[{index}]")
    elif actual != expected:
        raise ValueError(f"{path} exact value mismatch")


def _expected_manifest(
    payloads: Mapping[str, bytes],
    source_records: tuple[dict[str, object], ...],
    signature_text: str,
) -> dict[str, object]:
    true_readiness = (
        "admit_015_preconditions_audited",
        "admit_015_training_authorization_contract_frozen",
        "admit_015_formal_evaluator_interface_contract_frozen",
        "admit_015_standalone_evaluator_implemented",
        "evaluate_admit_015_implemented",
        "Admit015EvaluationResult_implemented",
        "admit_015_rule_logic_implemented",
        "admit_015_unified_adapter_contract_frozen",
        "admit_015_exact13_projection_frozen",
        "admit_015_context_routing_contract_frozen",
        "admit_015_source_oracle_equivalence_contract_frozen",
        "ready_for_unified_dispatch_runtime_with_admit_001_to_015_"
        "implementation",
        "unified_dispatch_runtime_with_admit_001_to_014_implemented",
        "feature_semantics_audit_required_before_training",
    )
    false_readiness = (
        "admit_015_unified_adapter_implemented",
        "future_adapter_handler_implemented",
        "admit_015_registered_in_engine",
        "unified_dispatch_runtime_with_admit_001_to_015_implemented",
        "mandatory_training_authorization_enforcement_api_frozen",
        "mandatory_training_authorization_enforcement_implemented",
        "provider_mapping_validated",
        "real_provider_evaluation_ready",
        "ready_for_bulk_download_now",
        "combined_candidate_verdict_implemented",
        "cross_rule_aggregation_implemented",
        "feature_semantics_audit_completed",
        "historical_unknown_atom_feature_policy_resolved",
        "historical_feature_semantics_known",
        "real_training_ready",
        "ready_for_training",
        "step12d_is_final_training_feature_contract",
    )
    readiness = {
        **{name: True for name in true_readiness},
        **{name: False for name in false_readiness},
    }
    source_verification = []
    for record in source_records:
        source_verification.append({
            "source_order": record["source_order"],
            "source_relative_path": record["source_relative_path"],
            "tracked": True,
            "base_tree_blob": record["base_tree_blob"],
            "base_tree_mode": record["base_tree_mode"],
            "index_blob": record["index_blob"],
            "index_mode": record["index_mode"],
            "index_stage": record["index_stage"],
            "filesystem_regular": True,
            "non_symlink": True,
            "parent_chain_non_symlink": True,
            "safe_descendant": True,
            "pinned_fd_read": True,
            "post_read_identity_verified": True,
            "expected_sha256": record["expected_sha256"],
            "base_tree_sha256": record["base_tree_sha256"],
            "filesystem_sha256": record["filesystem_sha256"],
            "source_verified": True,
        })
    current_order = [
        f"ADMIT_{index:03d}" for index in range(1, 15)
    ]
    future_order = [
        f"ADMIT_{index:03d}" for index in range(1, 16)
    ]
    expected = {
        "project": "CovaPIE",
        "step": "ADMIT_015 unified adapter contract design gate v1",
        "stage": (
            "covapie_bulk_download_admission_admit_015_"
            "unified_adapter_contract_v1"
        ),
        "manifest_schema_version": (
            "covapie_admit_015_unified_adapter_contract_manifest_v1"
        ),
        "expected_base_commit": BASE,
        "expected_base_parent": PARENT,
        "expected_base_tree": TREE,
        "expected_base_subject": SUBJECT,
        "canonical_evidence_python_implementation": "cpython",
        "canonical_evidence_python_version": "3.10.4",
        "ast_attestation_cross_python_version_portable": False,
        "noncanonical_python_policy": (
            "evaluator_semantic_smoke_only; artifact_build_checker_and_"
            "frozen_ast_forbidden"
        ),
        "python_runtime_migration_policy": (
            "explicit_contract_refresh_required"
        ),
        "admission_rule_id": "ADMIT_015",
        "admission_rule_name": (
            "current_gate_grants_no_training_permission"
        ),
        "adapter_id": "covapie_admit_015_unified_adapter_v1",
        "formal_evaluator": "evaluate_admit_015",
        "formal_result_type": "Admit015EvaluationResult",
        "independent_oracle": (
            "classify_admit_015_formal_evaluator_interface_design"
        ),
        "independent_oracle_result_type": (
            "Admit015EvaluationResultContractDesign"
        ),
        "future_adapter_handler": "_evaluate_registered_admit_015",
        "future_adapter_handler_signature": signature_text,
        "future_adapter_handler_signature_evidence": {
            "signature_text": signature_text,
            "parameter_order": [
                "candidate_record", "batch_context", "evaluation_context",
                "download_result_context", "stage_authorization_context",
            ],
            "parameter_kinds": [
                "POSITIONAL_OR_KEYWORD", "KEYWORD_ONLY", "KEYWORD_ONLY",
                "KEYWORD_ONLY", "KEYWORD_ONLY",
            ],
            "required_count": 5,
            "annotations": {
                "candidate_record": "object",
                "batch_context": "object",
                "evaluation_context": "object",
                "download_result_context": "object",
                "stage_authorization_context": "object",
            },
            "return_annotation": "UnifiedAdmissionRuleEvaluation",
            "has_varargs": False,
            "has_varkw": False,
        },
        "future_adapter_handler_implemented": False,
        "result_schema_version": (
            "covapie_unified_admission_rule_evaluation_v1"
        ),
        "result_fields": list(RESULT_FIELDS),
        "standalone_result_fields": [
            "admission_rule_id", "outcome", "passed", "blocks_candidate",
            "reason", "canonical_stage_authorization_record",
            "validated_stage_authorization_fields",
            "consumed_stage_authorization_fields", "evaluator_io_used",
        ],
        "dispatch_error_fields": [
            "code", "admission_rule_id", "known_rule",
            "callable_discovered", "adapter_ready", "reason",
        ],
        "context_routing_order": [
            "batch_context_must_be_none",
            "evaluation_context_must_be_none",
            "download_result_context_must_be_none",
            "candidate_record_mapping_validation",
            "stage_authorization_context_forwarded_without_adapter_"
            "prevalidation",
            "formal_evaluator_exactly_once",
            "standalone_source_exact9_validation",
            "independent_design_oracle_exactly_once",
            "full_exact9_exact_type_value_equality",
            "exact9_to_exact13_projection",
        ],
        "context_routing_reasons": {
            "batch_context": "ADMIT_015_BATCH_CONTEXT_MUST_BE_NONE",
            "evaluation_context": (
                "ADMIT_015_EVALUATION_CONTEXT_MUST_BE_NONE"
            ),
            "download_result_context": (
                "ADMIT_015_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"
            ),
        },
        "forbidden_envelope_contract": {
            "batch_context": "exact None",
            "evaluation_context": "exact None",
            "download_result_context": "exact None",
        },
        "stage_authorization_contract": {
            "authoritative_envelope": "stage_authorization_context",
            "authoritative_key": TARGET_ITEM,
            "value_contract": "exact bool False|True; no normalization",
            "adapter_prevalidation": False,
            "adapter_direct_target_access_count": 0,
            "formal_call_count": 1,
            "oracle_call_count": 1,
            "stable_mapping_formal_target_access_count": 1,
            "stable_mapping_oracle_target_access_count": 1,
            "stable_mapping_total_target_access_count": 2,
            "target_access_order": ["formal", "oracle"],
            "none_or_non_mapping_target_access_count": 0,
            "identity_preserved_to_formal": True,
            "identity_preserved_to_oracle": True,
            "download_coexistence_item": DOWNLOAD_ITEM,
        },
        "candidate_record_contract": {
            "mapping_required": True,
            "candidate_key_access_count": 0,
            "authority_source": False,
        },
        "candidate_mapping_invalid_reason": (
            "ADMIT_015_CANDIDATE_RECORD_MAPPING_INVALID"
        ),
        "candidate_invalid_projection": json.loads(
            _expected_unified_json(
                "invalid",
                "ADMIT_015_CANDIDATE_RECORD_MAPPING_INVALID",
            )
        ),
        "candidate_invalid_call_counts": {
            "formal": 0,
            "oracle": 0,
            "candidate_key_access": 0,
            "stage_target_access": 0,
        },
        "context_failure_dispatch_code": (
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"
        ),
        "source_failure_dispatch_code": (
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
        ),
        "source_type_invalid_reason": SOURCE_TYPE_ERROR,
        "source_invariant_invalid_reason": SOURCE_INVARIANT_ERROR,
        "source_exact9_validation": (
            "exact type; vars exact dict and order; dataclass fields; "
            "top-level exact types; constructor reconstruction; fixed "
            "identity/I/O and all result invariants"
        ),
        "source_validation_before_oracle": True,
        "oracle_exact9_validation": (
            "exact type; vars exact dict and order; dataclass fields; "
            "top-level exact types; constructor reconstruction and "
            "invariants"
        ),
        "source_oracle_full_exact9_exact_type_value_equality_required": True,
        "exact13_projection": {
            "copied_fields": [
                "admission_rule_id", "outcome", "passed",
                "blocks_candidate", "reason", "evaluator_io_used",
            ],
            "fixed_fields": {
                "schema_version": (
                    "covapie_unified_admission_rule_evaluation_v1"
                ),
                "admission_rule_name": (
                    "current_gate_grants_no_training_permission"
                ),
                "adapter_id": "covapie_admit_015_unified_adapter_v1",
            },
            "normalized_values": (
                "source canonical exact bool pair projected to lowercase "
                "exact string false|true"
            ),
            "validated_candidate_fields": [],
            "consumed_candidate_fields": [],
            "consumed_context_items": (
                "source.consumed_stage_authorization_fields"
            ),
        },
        "current_registered_rule_order": current_order,
        "future_registered_rule_order": future_order,
        "future_known_not_registered_rule_ids": [],
        "first_fourteen_handler_object_identity_preserved": True,
        "shared_result_identity_preserved": True,
        "shared_dispatch_error_identity_preserved": True,
        "public_dispatcher_signature_preserved": True,
        "public_dispatcher_single_rule": True,
        "future_registry_mapping_proxy_type": True,
        "precondition_transition": {
            "row_count": 45,
            "complete_count": 38,
            "supported_but_not_frozen_count": 0,
            "incomplete_count": 7,
            "implementation_blocking_count": 7,
            "resolved_precondition_ids": ["PRE_031"],
            "resolution": (
                "ADMIT_015 five-envelope routing, standalone Exact9 "
                "attestation, oracle equivalence and typed Exact13 "
                "projection frozen"
            ),
            "remaining_open_precondition_ids": [
                "PRE_032", "PRE_033", "PRE_034", "PRE_035",
                "PRE_036", "PRE_038", "PRE_042",
            ],
        },
        "issue_inventory_row_count": 30,
        "issue_inventory_preserved_byte_identical": True,
        "issue_inventory_sha256": SOURCE_BOUNDARY[5][1],
        "issue_transition_count": 0,
        "coverage_issue_affected_rules": "ADMIT_015",
        "remaining_open_issue_ids": [
            "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
            "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
            "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
            "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
        ],
        "contract_row_count": 54,
        "routing_matrix_row_count": 42,
        "projection_truth_matrix_row_count": 61,
        "safety_row_count": 32,
        "source_boundary_name": (
            "fixed_ordered_exact17_committed_source_boundary"
        ),
        "source_input_count": 17,
        "source_input_paths": [path for path, _ in SOURCE_BOUNDARY],
        "source_input_sha256": dict(SOURCE_BOUNDARY),
        "source_path_list_sha256": (
            "92b73089a212f5584eaf1599e0fc9d960778f36dda594b0a6f182b5b7ccad4fe"
        ),
        "source_path_sha256_pairs_sha256": (
            "c55c0c9a08a77025b2742a21eecc616b760688feb749a97da014dfbe0971f66c"
        ),
        "source_input_verification": source_verification,
        "source_validation_before_candidate_or_output_read": True,
        "source_read_policy": {
            "six_field_identity": True,
            "leaf_fd_retained_through_final_checks": True,
            "second_leaf_fd_check": True,
            "second_leaf_lexical_check": True,
            "parent_fd_and_lexical_checks": True,
            "root_fd_and_lexical_checks": True,
        },
        "output_read_policy": {
            "exact6_inventory": True,
            "all_leaf_fds_retained": True,
            "second_inventory": True,
            "second_leaf_checks": True,
            "second_root_parent_checks": True,
        },
        "materialization_policy": {
            "authenticated_retained_path_reported_only_when_binding_verified": True,
            "binding_lost_reports_authenticated_path_none": True,
            "binding_lost_reports_frozen_identity": True,
            "build_before_mutation": True,
            "exclusive_leaf_create": True,
            "rename_noreplace_required": True,
            "staging_fd_lexical_binding": True,
            "binding_rechecked_inside_rename": True,
            "gpfs_einval_fails_closed": True,
            "held_parent_fd_only_is_insufficient_for_path_authentication": True,
            "no_atomic_parent_path_compare_and_rename_claim": True,
            "concurrent_eexist_fails_closed": True,
            "os_replace_forbidden": True,
            "parent_binding_loss_reports_authenticated_path_none": True,
            "parent_binding_rechecked_inside_rename": True,
            "parent_lexical_binding_required_for_authenticated_retained_path": True,
            "exact_noop_inode_preserving": True,
            "successful_publish_no_residue": True,
            "failure_staging_object_retained": True,
            "failure_staging_retained": True,
            "failure_unlink_forbidden": True,
            "failure_rmdir_forbidden": True,
            "foreign_lexical_name_never_reported_as_owned": True,
            "last_known_name_is_not_authority": True,
            "unknown_identity_never_deleted": True,
        },
        "lifecycle_policy": {
            "bounded_recursive_no_follow": True,
            "ignored_stage_artifacts_rejected": True,
            "nested_stage_artifacts_rejected": True,
            "sibling_derived_roots_rejected": True,
            "exact10_allowlist": True,
        },
        "output_file_count": 6,
        "output_files": list(OUTPUTS),
        "output_sha256": {
            name: _sha_bytes(payloads[name]) for name in OUTPUTS[:5]
        },
        "output_sha256_excludes_manifest_self_hash": True,
        "readiness": readiness,
        **readiness,
        "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "combined_candidate_verdict_implemented": False,
        "cross_rule_aggregation_implemented": False,
        "mandatory_training_authorization_enforcement_api_frozen": False,
        "mandatory_training_authorization_enforcement_implemented": False,
        "provider_mapping_implemented": False,
        "real_provider_evaluation_ready": False,
        "real_download_executed": False,
        "synthetic_true_case_changes_current_permission": False,
        "raw_accessed": False,
        "runtime_changed": False,
        "registry_changed": False,
        "step12d_status": (
            "smoke_legality_only_not_final_training_feature_contract"
        ),
        "canonical_masks": [
            {"semantic_name": "warhead_only", "alias": "A"},
            {"semantic_name": "linker_plus_warhead", "alias": "B"},
            {"semantic_name": "scaffold_plus_warhead", "alias": "B2"},
            {"semantic_name": "scaffold_only", "alias": "B3"},
            {
                "semantic_name": "scaffold_plus_linker_plus_warhead",
                "alias": "C",
            },
        ],
        "canonical_mask_count": 5,
        "feature_semantics_note": (
            "feature-semantics audit remains mandatory before training; "
            "Step12D was only a smoke legality check"
        ),
        "recommended_next_step": (
            "implement_covapie_unified_dispatch_runtime_with_admit_001_"
            "to_015_v1"
        ),
        "validation_failures": [],
        "all_checks_passed": True,
    }
    return json.loads(json.dumps(expected, sort_keys=True))


def _expected_contract_rows() -> list[dict[str, str]]:
    current = "|".join(f"ADMIT_{index:03d}" for index in range(1, 15))
    future = "|".join(f"ADMIT_{index:03d}" for index in range(1, 16))
    definitions = (
        (
            "identity",
            "rule",
            "ADMIT_015|current_gate_grants_no_training_permission|"
            "covapie_admit_015_unified_adapter_v1",
        ),
        (
            "identity",
            "formal_evaluator",
            "evaluate_admit_015|Admit015EvaluationResult",
        ),
        (
            "identity",
            "oracle",
            "classify_admit_015_formal_evaluator_interface_design|"
            "Admit015EvaluationResultContractDesign",
        ),
        (
            "identity",
            "future_handler",
            "_evaluate_registered_admit_015(candidate_record: object, *, "
            "batch_context: object, evaluation_context: object, "
            "download_result_context: object, "
            "stage_authorization_context: object) -> "
            "'UnifiedAdmissionRuleEvaluation'",
        ),
        (
            "routing",
            "five_envelopes",
            "candidate_record|batch_context|evaluation_context|"
            "download_result_context|stage_authorization_context",
        ),
        (
            "routing",
            "precedence",
            "batch_context_must_be_none|evaluation_context_must_be_none|"
            "download_result_context_must_be_none|"
            "candidate_record_mapping_validation|"
            "stage_authorization_context_forwarded_without_adapter_"
            "prevalidation|formal_evaluator_exactly_once|"
            "standalone_source_exact9_validation|"
            "independent_design_oracle_exactly_once|"
            "full_exact9_exact_type_value_equality|"
            "exact9_to_exact13_projection",
        ),
        ("routing", "batch", "exact_None"),
        ("routing", "evaluation", "exact_None"),
        ("routing", "download_result", "exact_None"),
        (
            "routing",
            "stage_authorization",
            "forward_same_object_no_prevalidation",
        ),
        (
            "candidate",
            "mapping_only",
            "Mapping_envelope_only_zero_key_access",
        ),
        (
            "candidate",
            "non_mapping_reason",
            "ADMIT_015_CANDIDATE_RECORD_MAPPING_INVALID",
        ),
        (
            "candidate",
            "invalid_projection",
            _expected_unified_json(
                "invalid",
                "ADMIT_015_CANDIDATE_RECORD_MAPPING_INVALID",
            ),
        ),
        ("authority", "envelope", "stage_authorization_context_only"),
        ("authority", "key", TARGET_ITEM),
        ("authority", "exact_bool", "False|True_no_normalization"),
        ("authority", "adapter_direct_access", "0"),
        (
            "authority",
            "stable_mapping_total_access",
            "2_formal_then_oracle",
        ),
        ("authority", "none_or_non_mapping_access", "0"),
        ("authority", "coexistence_item", DOWNLOAD_ITEM),
        (
            "routing",
            "private_sentinel",
            "not_imported_read_or_passed",
        ),
        (
            "formal",
            "call",
            "keyword_only_exactly_once_after_routing",
        ),
        (
            "formal",
            "identity",
            "stage_context_exact_object_identity_preserved",
        ),
        (
            "source",
            "exact9_fields",
            "admission_rule_id|outcome|passed|blocks_candidate|reason|"
            "canonical_stage_authorization_record|"
            "validated_stage_authorization_fields|"
            "consumed_stage_authorization_fields|evaluator_io_used",
        ),
        (
            "source",
            "validation",
            "exact_type_storage_order_types_reconstruction_reason_pair_"
            "invariants",
        ),
        (
            "source",
            "type_failure",
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY|"
            "ADMIT_015_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID|"
            "adapter_ready=false",
        ),
        (
            "source",
            "invariant_failure",
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY|"
            "ADMIT_015_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID|"
            "adapter_ready=false",
        ),
        (
            "oracle",
            "call",
            "same_stage_context_exactly_once_after_source_validation",
        ),
        (
            "oracle",
            "identity",
            "stage_context_exact_object_identity_preserved",
        ),
        (
            "oracle",
            "equality",
            "full_Exact9_exact_type_value_storage_order",
        ),
        ("projection", "exact13_fields", "|".join(RESULT_FIELDS)),
        (
            "projection",
            "normalized",
            "canonical_stage_bool_to_lowercase_string",
        ),
        ("projection", "validated_candidate", "always_empty"),
        ("projection", "consumed_candidate", "always_empty"),
        (
            "projection",
            "consumed_context",
            "source_consumed_stage_authorization_fields",
        ),
        ("projection", "false", "false"),
        ("projection", "true", "true"),
        (
            "projection",
            "no_schema_widening",
            "Exact13_exact_string_pairs_only",
        ),
        (
            "projection",
            "validated_stage_note",
            "retained_by_normalized_values_not_candidate_fields",
        ),
        ("registry", "current_order", current),
        ("registry", "future_order", future),
        ("registry", "future_callable", future),
        ("registry", "future_adapter_ready", future),
        ("registry", "future_known_not_registered", ""),
        (
            "registry",
            "first14_identity",
            "exact_object_identity_preserved",
        ),
        ("precondition", "resolved", "PRE_031"),
        (
            "precondition",
            "remaining",
            "PRE_032|PRE_033|PRE_034|PRE_035|PRE_036|PRE_038|PRE_042",
        ),
        (
            "precondition",
            "counts",
            "total=45|complete=38|supported=0|incomplete=7|blocking=7",
        ),
        (
            "issue",
            "continuity",
            "Exact30_byte_identical_zero_transitions",
        ),
        ("issue", "coverage", "ADMIT_015"),
        (
            "boundary",
            "runtime",
            "design_only_no_handler_registry_dispatcher_runtime_mutation",
        ),
        (
            "boundary",
            "aggregation",
            "no_combined_verdict_or_cross_rule_aggregation",
        ),
        (
            "boundary",
            "operations",
            "no_provider_network_download_raw_model_checkpoint_dataloader_"
            "training",
        ),
        (
            "training",
            "prerequisite",
            "feature_semantics_audit_required_Step12D_smoke_only",
        ),
    )
    return [
        {
            "contract_order": str(index),
            "contract_id": f"CONTRACT_{index:03d}",
            "contract_group": group,
            "contract_subject": subject,
            "contract_value": value,
            "contract_status": "frozen",
        }
        for index, (group, subject, value) in enumerate(definitions, 1)
    ]


def _expected_safety_rows() -> list[dict[str, str]]:
    states = (
        ("production_design_only", True),
        ("shared_exact13_preserved", True),
        ("five_envelope_routing_frozen", True),
        ("stage_authority_only", True),
        ("adapter_direct_target_access_count_zero", True),
        ("formal_exactly_once", True),
        ("oracle_exactly_once", True),
        ("stage_context_identity_preserved", True),
        ("source_exact9_attested", True),
        ("oracle_exact9_attested", True),
        ("full_exact9_equivalence_required", True),
        ("bool_lowercase_projection", True),
        ("candidate_fields_empty", True),
        ("consumed_context_projection", True),
        ("pre_031_resolved", True),
        ("remaining_preconditions_open", True),
        ("issue_inventory_byte_identical", True),
        ("canonical_runtime", True),
        ("deterministic_materialization", True),
        ("runtime_handler_implemented", False),
        ("registry_changed", False),
        ("exact15_runtime_implemented", False),
        ("mandatory_enforcement_implemented", False),
        ("provider_mapping_implemented", False),
        ("network_executed", False),
        ("download_executed", False),
        ("raw_accessed", False),
        ("combined_verdict_implemented", False),
        ("cross_rule_aggregation_implemented", False),
        ("training_executed", False),
        ("current_main_staged", False),
        ("current_main_committed_or_pushed", False),
    )
    return [
        {
            "audit_order": str(index),
            "audit_item": name,
            "expected_state": str(state).lower(),
            "observed_state": str(state).lower(),
            "safety_passed": "true",
        }
        for index, (name, state) in enumerate(states, 1)
    ]


def _verify_artifact_payloads(
    payloads: Mapping[str, bytes],
    module: object,
    source_records: tuple[dict[str, object], ...],
) -> dict[str, object]:
    if tuple(payloads) != OUTPUTS:
        raise ValueError("Exact6 output order/inventory drift")
    actual_sha = {
        name: _sha_bytes(payloads[name]) for name in OUTPUTS
    }
    if actual_sha != OUTPUT_SHA256:
        raise ValueError("Exact6 frozen SHA drift")
    contract = _csv_payload(
        payloads[OUTPUTS[0]],
        (
            "contract_order", "contract_id", "contract_group",
            "contract_subject", "contract_value", "contract_status",
        ),
    )
    routing = _csv_payload(payloads[OUTPUTS[1]], ROUTING_HEADER)
    truth = _csv_payload(payloads[OUTPUTS[2]], TRUTH_HEADER)
    safety = _csv_payload(
        payloads[OUTPUTS[3]],
        (
            "audit_order", "audit_item", "expected_state",
            "observed_state", "safety_passed",
        ),
    )
    issue = _csv_payload(
        payloads[OUTPUTS[4]],
        (
            "inherited_order", "issue_id", "issue_type", "affected_fields",
            "affected_rules", "severity", "status", "blocking_scope",
            "blocking_reason", "issue_origin", "integration_transition",
            "issue_count", "inherited_effective_status",
            "inherited_transition_stage", "inherited_transition_action",
            "inherited_transition_evidence", "successor_effective_status",
            "successor_transition_stage", "successor_transition_action",
            "successor_transition_evidence",
        ),
    )
    if (
        [len(contract), len(routing), len(truth), len(safety), len(issue)]
        != [54, 42, 61, 32, 30]
        or contract != _expected_contract_rows()
        or safety != _expected_safety_rows()
        or payloads[OUTPUTS[4]]
        != _pinned_source_read(ROOT, Path(SOURCE_BOUNDARY[5][0]))
    ):
        raise ValueError("Exact6 schema/row/issue identity drift")
    manifest = _parse_manifest_exact(payloads[OUTPUTS[5]])
    if (
        manifest["output_files"] != list(OUTPUTS)
        or manifest["output_sha256"]
        != {name: actual_sha[name] for name in OUTPUTS[:5]}
        or OUTPUTS[5] in manifest["output_sha256"]
        or manifest["source_input_paths"]
        != [path for path, _ in SOURCE_BOUNDARY]
        or manifest["source_input_sha256"] != dict(SOURCE_BOUNDARY)
        or manifest["result_fields"] != list(RESULT_FIELDS)
    ):
        raise ValueError("manifest output/source/schema drift")
    signature_text = _assert_future_signature(module)
    expected_manifest = _expected_manifest(
        payloads, source_records, signature_text
    )
    _assert_exact_object(manifest, expected_manifest, "manifest")
    _verify_manifest_semantics(manifest, source_records, signature_text)
    routing_observations = _verify_routing(module, routing)
    _verify_truth(module, truth, routing, routing_observations)
    return manifest


def verify_semantics(module: object) -> None:
    if (
        tuple(module.RESULT_FIELDS) != RESULT_FIELDS
        or (
            module.ADMISSION_RULE_ID,
            module.ADMISSION_RULE_NAME,
            module.ADAPTER_ID,
        )
        != (
            "ADMIT_015",
            "current_gate_grants_no_training_permission",
            "covapie_admit_015_unified_adapter_v1",
        )
    ):
        raise ValueError("adapter/shared Exact13 identity drift")
    _assert_future_signature(module)
    _verify_negative_exact9_contracts(module)
    _verify_registry_identity(module)


def _git_at(
    repo_root: Path, *arguments: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *arguments), cwd=repo_root, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )


STAGE_FAMILY_TOKENS = (
    "covapie_bulk_download_admission_admit_015_unified_adapter_contract",
    "covapie_admit_015_unified_adapter_contract",
    "admit_015_unified_adapter_contract",
    "covapie_admit_015_stage_authorization_projection_and_context_"
    "routing_matrix",
    "covapie_admit_015_unified_result_projection_truth_matrix",
    "covapie_admit_015_unified_adapter_safety_audit",
    "covapie_admit_015_unified_adapter_issue_readiness_inventory",
    "covapie_admit_015_unified_adapter_contract_manifest",
)
STAGE_FAMILY_SCAN_ROOTS = (
    Path("src/covalent_ext"),
    Path("scripts"),
    Path("tests"),
    Path("docs"),
)


def _check_ignore(path: Path, repo_root: Path) -> bool:
    result = _git_at(
        repo_root,
        "check-ignore",
        "--no-index",
        "-q",
        "--",
        path.as_posix(),
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise ValueError(f"git check-ignore failed closed: {path}")


def _is_stage_family_name(name: str) -> bool:
    candidate = name.lstrip(".")
    return any(token in candidate for token in STAGE_FAMILY_TOKENS)


def _is_stage_family_path(path: Path) -> bool:
    return _is_stage_family_name(path.as_posix())


def _scan_bounded_stage_root(
    scan_root: Path,
    discovered: set[Path],
    repo_root: Path,
) -> None:
    pending = [scan_root]
    while pending:
        current = pending.pop()
        try:
            entries = tuple(os.scandir(repo_root / current))
        except OSError as error:
            raise ValueError(
                f"stage-family scan unavailable: {current}"
            ) from error
        for entry in entries:
            relative = current / entry.name
            if entry.is_symlink():
                raise ValueError(
                    "symlink blocks no-follow stage-family scan: "
                    f"{relative}"
                )
            if _is_stage_family_path(relative):
                discovered.add(relative)
            if entry.is_dir(follow_symlinks=False):
                pending.append(relative)


def _filesystem_stage_family(
    repo_root: Path,
    exact10: tuple[Path, ...],
) -> set[Path]:
    discovered: set[Path] = set()
    for scan_root in STAGE_FAMILY_SCAN_ROOTS:
        _scan_bounded_stage_root(scan_root, discovered, repo_root)
    derived_parent = STAGE.parent
    try:
        derived_entries = tuple(
            os.scandir(repo_root / derived_parent)
        )
    except OSError as error:
        raise ValueError(
            "derived stage-family scan unavailable"
        ) from error
    for entry in derived_entries:
        if not _is_stage_family_name(entry.name):
            continue
        relative = derived_parent / entry.name
        discovered.add(relative)
        if entry.is_symlink():
            raise ValueError(
                f"symlink derived stage-family root: {relative}"
            )
        pending = (
            [relative] if entry.is_dir(follow_symlinks=False) else []
        )
        while pending:
            current = pending.pop()
            try:
                children = tuple(os.scandir(repo_root / current))
            except OSError as error:
                raise ValueError(
                    "derived stage-family inventory unavailable: "
                    f"{current}"
                ) from error
            for child in children:
                child_relative = current / child.name
                discovered.add(child_relative)
                if child.is_symlink():
                    raise ValueError(
                        "symlink derived stage-family path: "
                        f"{child_relative}"
                    )
                if child.is_dir(follow_symlinks=False):
                    pending.append(child_relative)
    expected = set(exact10) | {STAGE}
    for path in sorted(discovered, key=Path.as_posix):
        try:
            item = os.lstat(repo_root / path)
        except OSError as error:
            raise ValueError(
                f"stage-family path vanished during scan: {path}"
            ) from error
        if _check_ignore(path, repo_root):
            raise ValueError(f"ignored stage-family path: {path}")
        if stat.S_ISLNK(item.st_mode):
            raise ValueError(f"symlink stage-family path: {path}")
        if path == STAGE:
            if not stat.S_ISDIR(item.st_mode):
                raise ValueError("Exact6 root is not a directory")
            continue
        if (
            not stat.S_ISREG(item.st_mode)
            or item.st_size > MAX_CANDIDATE_BYTES
            or path.suffix.lower() in FORBIDDEN_SUFFIXES
        ):
            raise ValueError(f"unsafe stage-family artifact: {path}")
    if discovered != expected:
        raise ValueError("filesystem stage-family allowlist mismatch")
    return discovered


def _lifecycle(repo_root: Path = ROOT, base: str = BASE) -> str:
    if _git_at(
        repo_root, "merge-base", "--is-ancestor", base, "HEAD"
    ).returncode != 0:
        raise ValueError("base nonancestor")
    if len(EXACT10) != 10 or len(set(EXACT10)) != 10:
        raise ValueError("Exact10 path drift")
    states: list[str] = []
    for path in EXACT10:
        relative = path.as_posix()
        target = repo_root / path
        try:
            item = os.lstat(target)
        except FileNotFoundError as error:
            raise ValueError("missing Exact10 candidate") from error
        if (
            not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or item.st_size > MAX_CANDIDATE_BYTES
            or path.suffix in FORBIDDEN_SUFFIXES
        ):
            raise ValueError("unsafe Exact10 candidate")
        if _check_ignore(path, repo_root):
            raise ValueError(f"ignored candidate: {path}")
        index = _git_at(repo_root, "ls-files", "--stage", "--", relative)
        if index.returncode != 0:
            raise ValueError("candidate index check failed")
        if index.stdout:
            _parse_index_entry(index.stdout, relative)
            state = "post_commit"
        else:
            state = "pre_commit"
        cached = _git_at(
            repo_root, "diff", "--cached", "--name-only", "--", relative
        )
        dirty = _git_at(
            repo_root, "diff", "--name-only", "--", relative
        )
        if (
            cached.returncode
            or dirty.returncode
            or cached.stdout
            or dirty.stdout
        ):
            raise ValueError("staged or dirty candidate")
        untracked_one = _git_at(
            repo_root,
            "ls-files",
            "--others",
            "--exclude-standard",
            "--",
            relative,
        )
        if untracked_one.returncode:
            raise ValueError("candidate untracked state unavailable")
        if state == "pre_commit":
            if untracked_one.stdout.splitlines() != [relative]:
                raise ValueError("invalid pre-commit candidate")
        elif untracked_one.stdout:
            raise ValueError("dirty post-commit candidate")
        states.append(state)
    if len(set(states)) != 1:
        raise ValueError("mixed candidate lifecycle")
    untracked_result = _git_at(
        repo_root, "ls-files", "--others", "--exclude-standard"
    )
    cached_all = _git_at(repo_root, "diff", "--cached", "--name-only")
    dirty_all = _git_at(repo_root, "diff", "--name-only")
    if (
        untracked_result.returncode != 0
        or cached_all.returncode != 0
        or dirty_all.returncode != 0
        or cached_all.stdout
        or dirty_all.stdout
    ):
        raise ValueError("repository lifecycle is staged or dirty")
    expected_untracked = (
        {path.as_posix() for path in EXACT10}
        if states[0] == "pre_commit"
        else set()
    )
    if set(untracked_result.stdout.splitlines()) != expected_untracked:
        raise ValueError("candidate untracked inventory drift")
    if {
        path.name for path in (repo_root / STAGE).iterdir()
    } != set(OUTPUTS):
        raise ValueError("same-stage Exact6 drift")
    _filesystem_stage_family(repo_root, EXACT10)
    tracked_inventory = _git_at(repo_root, "ls-files")
    if tracked_inventory.returncode:
        raise ValueError("tracked inventory unavailable")
    stage_related = {
        path
        for path in (
            set(tracked_inventory.stdout.splitlines())
            | set(untracked_result.stdout.splitlines())
        )
        if _is_stage_family_path(Path(path))
    }
    if stage_related != {path.as_posix() for path in EXACT10}:
        raise ValueError("extra tracked/untracked stage-family path")
    return states[0]


def lifecycle() -> str:
    return _lifecycle(ROOT, BASE)


def main() -> None:
    if (
        sys.implementation.name != "cpython"
        or tuple(sys.version_info[:3]) != (3, 10, 4)
    ):
        raise ValueError("canonical CPython 3.10.4 required")
    source_records = verify_sources()
    verify_candidate_ast()
    module = import_production()
    verify_semantics(module)
    payloads = _pinned_outputs(ROOT / STAGE)
    manifest = _verify_artifact_payloads(payloads, module, source_records)
    before = {
        name: os.lstat(ROOT / STAGE / name).st_ino for name in OUTPUTS
    }
    module.run_covapie_bulk_download_admission_admit_015_unified_adapter_contract_design_gate_v1()
    after = {
        name: os.lstat(ROOT / STAGE / name).st_ino for name in OUTPUTS
    }
    if before != after:
        raise ValueError("inode-preserving materialization no-op drift")
    state = lifecycle()
    print("CovaPIE ADMIT_015 unified adapter contract v1: PASS")
    print(f"lifecycle={state}")
    print(f"base={BASE}")
    print("source_boundary=Exact17_git_blob_verified")
    print("shared_result=Exact13")
    print("rows=54/42/61/32/30")
    print(f"manifest_sha256={OUTPUT_SHA256[OUTPUTS[5]]}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")


if __name__ == "__main__":
    main()
