"""Summarize paired A3 sparse-solver runs and check their numerical agreement."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fallback", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    fallback: dict[str, Any] = json.loads(args.fallback.read_text(encoding="utf-8"))
    candidate: dict[str, Any] = json.loads(args.candidate.read_text(encoding="utf-8"))
    if fallback["environment"] != candidate["environment"]:
        raise ValueError("benchmark environments differ")
    if (
        fallback["configuration"]["thread_environment"]
        != candidate["configuration"]["thread_environment"]
    ):
        raise ValueError("thread controls differ")
    if len(fallback["cases"]) != len(candidate["cases"]):
        raise ValueError("mesh ladders differ")
    for old, new in zip(fallback["cases"], candidate["cases"], strict=True):
        if old["element_counts"] != new["element_counts"]:
            raise ValueError("mesh ladders differ")
        if old["nonzero_entries"] != new["nonzero_entries"]:
            raise ValueError("sparse structures differ")
        relative_compliance = abs(old["compliance"] - new["compliance"]) / abs(
            old["compliance"]
        )
        if relative_compliance > 1e-9:
            raise ValueError(f"{old['case']} compliance changed beyond 1e-9")
        if max(
            old["equilibrium_relative_residual"],
            new["equilibrium_relative_residual"],
        ) > 1e-8:
            raise ValueError(f"{old['case']} equilibrium residual exceeded 1e-8")
        old_time = old["total"]["repeated_median_seconds"]
        new_time = new["total"]["repeated_median_seconds"]
        print(
            f"{old['case']}: DOF={old['degrees_of_freedom']} "
            f"NNZ={old['nonzero_entries']} "
            f"cold={old['total']['cold_seconds']:.4f}/{new['total']['cold_seconds']:.4f}s "
            f"repeat={old_time:.4f}/{new_time:.4f}s "
            f"ratio={new_time / old_time:.3f} "
            f"peak_RSS={old['process_peak_rss_mib']:.1f}/{new['process_peak_rss_mib']:.1f}MiB "
            f"relative_compliance={relative_compliance:.3g}"
        )


if __name__ == "__main__":
    main()
