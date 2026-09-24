"""Run the versioned canonical problem through the public job boundary."""

import argparse
import json
from importlib.resources import files
from pathlib import Path
from tempfile import mkdtemp

from topolab.jobs import RunManager, RunStatus
from topolab.problem import TopologyProblem

DEMO_CASE_VERSION = "canonical-demo.v1"
_CASE_RESOURCE = "examples/canonical_demo_v1.json"


def load_canonical_demo_problem() -> TopologyProblem:
    """Validate the packaged example with the public problem contract."""

    return TopologyProblem.model_validate_json(
        files("topolab").joinpath(_CASE_RESOURCE).read_text(encoding="utf-8")
    )


def main(argv: list[str] | None = None) -> int:
    """Execute one local demo and save its complete run snapshot outside Git."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="external directory for the run snapshot (default: a new temporary directory)",
    )
    arguments = parser.parse_args(argv)
    output_dir = (
        Path(mkdtemp(prefix="topolab-demo-v1-"))
        if arguments.output_dir is None
        else arguments.output_dir
    ).resolve()
    if any((parent / ".git").exists() for parent in (output_dir, *output_dir.parents)):
        parser.error("--output-dir must be outside a Git repository")

    problem = load_canonical_demo_problem()
    with RunManager(max_workers=1) as manager:
        submitted = manager.submit(problem)
        snapshot = manager.wait(submitted.run_id)

    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / f"{DEMO_CASE_VERSION}-{snapshot.run_id}.json"
    with result_path.open("x", encoding="utf-8") as output:
        output.write(snapshot.model_dump_json(indent=2) + "\n")

    result = snapshot.result
    print(
        json.dumps(
            {
                "case_version": DEMO_CASE_VERSION,
                "run_id": snapshot.run_id,
                "status": snapshot.status.value,
                "converged": None if result is None else result.converged,
                "compliance": None if result is None else result.compliance,
                "volume_fraction": (
                    None
                    if result is None
                    else sum(result.physical_density) / len(result.physical_density)
                ),
                "result_path": str(result_path),
            },
            sort_keys=True,
        )
    )
    if snapshot.status is RunStatus.SUCCEEDED and result is not None and result.converged:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
