"""Read-only planning and explicit execution of the frozen B3 data stage."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import tomllib
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from time import perf_counter

import torch

from topolab.b3_catalog import B3_CONTRACT_SHA256
from topolab.b3_dataset import B3_NUMERICAL_ANCHOR, B3DataContext, B3DataRuntime, B3DatasetManifest
from topolab.b3_materialization import b3_data_summary, index_path, read_b3_index, run_b3_data
from topolab.dataset_cli import inspect_repository, validate_external_output_root

_BLAS_VARIABLES = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)
_NUMERICAL_FILES = tuple(
    f"src/topolab/{name}.py"
    for name in ("mesh", "fem", "simp", "problem", "experiment", "baselines")
)


def capture_b3_runtime() -> B3DataRuntime:
    """Require the predeclared Apple CPU and actual one-thread numerical runtime."""

    if platform.system() != "Darwin":
        raise ValueError("B3 labels require the preregistered Apple M2 host")
    if any(os.environ.get(name) != "1" for name in _BLAS_VARIABLES):
        raise ValueError("set all four frozen BLAS/OpenMP thread variables to 1 before startup")
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 8:
        torch.set_num_interop_threads(8)
    cpu = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    memory = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip())
    return B3DataRuntime.model_validate(
        {
            "os_family": platform.system(),
            "os_version": platform.release(),
            "machine": platform.machine(),
            "cpu": cpu,
            "memory_bytes": memory,
            "torch_version": importlib.metadata.version("torch"),
            "blas_threads": 1,
            "torch_intraop_threads": torch.get_num_threads(),
            "torch_interop_threads": torch.get_num_interop_threads(),
        }
    )


def build_current_b3_manifest(cwd: Path) -> tuple[Path, B3DatasetManifest]:
    """Capture a clean, frozen, locally merged source revision without opening data."""

    snapshot = inspect_repository(cwd)
    contract = snapshot.root / "docs/b3_experiment_contract.md"
    if hashlib.sha256(contract.read_bytes()).hexdigest() != B3_CONTRACT_SHA256:
        raise ValueError("B3 contract bytes differ from the frozen preregistration")
    merged = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            snapshot.source_revision,
            "refs/remotes/origin/main",
        ],
        cwd=snapshot.root,
        check=False,
        capture_output=True,
    )
    if merged.returncode != 0:
        raise ValueError("B3 planning/execution requires a merged source revision")
    numerical = subprocess.run(
        ["git", "diff", "--quiet", B3_NUMERICAL_ANCHOR, "--", *_NUMERICAL_FILES],
        cwd=snapshot.root,
        check=False,
        capture_output=True,
    )
    if numerical.returncode != 0:
        raise ValueError("B3 numerical source differs from the frozen anchor")
    runtime = capture_b3_runtime()
    packages = tomllib.loads((snapshot.root / "uv.lock").read_text())["package"]
    locked = {row["name"]: row["version"].split("+")[0] for row in packages if "version" in row}
    for name in ("numpy", "scipy", "torch", "pydantic", "safetensors"):
        if importlib.metadata.version(name).split("+")[0] != locked.get(name):
            raise ValueError(f"installed {name} version differs from uv.lock")
    context = B3DataContext(
        source_revision=snapshot.source_revision, environment=snapshot.environment, runtime=runtime
    )
    return snapshot.root, B3DatasetManifest.from_context(context)


def main(argv: Sequence[str] | None = None) -> int:
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, help="external B3 data root")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true", help="generate and audit the fixed data")
    mode.add_argument("--audit", action="store_true", help="audit existing data without generating")
    args = parser.parse_args(argv)
    if (args.execute or args.audit) and args.output_root is None:
        parser.error("--execute/--audit requires --output-root")
    try:
        repository, manifest = build_current_b3_manifest(Path.cwd())
        root = (
            None
            if args.output_root is None
            else validate_external_output_root(repository, args.output_root)
        )
        if not args.execute and not args.audit:
            summary: dict[str, object] = {
                "mode": "plan",
                "state": "planned",
                "manifest_sha256": manifest.sha256(),
                "context": manifest.context.model_dump(mode="json"),
                "roles": dict(Counter(e.role for e in manifest.catalog.entries)),
                "labels": 560,
                "references": 48,
                "final_artifacts": 0,
            }
            if root is not None and index_path(root).exists():
                index = read_b3_index(root, manifest)
                summary["recorded"] = len(index.entries)
                summary["cumulative_seconds"] = index.cumulative_seconds
            print(json.dumps(summary, sort_keys=True, allow_nan=False))
            return 0
        if not Path(__file__).resolve().is_relative_to(repository):
            raise ValueError("B3 execution must load its implementation from the recorded checkout")
        assert root is not None
        index = run_b3_data(
            root,
            manifest,
            repository_root=repository,
            audit_only=args.audit,
            startup_seconds=perf_counter() - started,
        )
        summary = b3_data_summary(index)
        summary["mode"] = "audit" if args.audit else "execute"
        print(json.dumps(summary, sort_keys=True, allow_nan=False))
        return 0 if summary["data_gate_passed"] else 1
    except (OSError, ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
