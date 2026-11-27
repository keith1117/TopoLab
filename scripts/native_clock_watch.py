"""Observe a registered publication or terminal check, preserving its actual stdout bytes."""

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAP = 4294967296


def watch_spec(contract, role, phase):
    if phase == "publication":
        reg = contract["roles"][role]
        inner, dispatch = reg["publication_timed_argv"], reg["publication_argv"]
    elif phase == "verification" and role in ("resource-preflight", "scientific-auditor"):
        reg = contract["b_caller_clock" if role == "resource-preflight" else "c_caller_clock"]
        inner, dispatch = reg["verification_timed_argv"], reg["verification_argv"]
    else:
        raise ValueError("unregistered measured metadata command")
    prof = inner[3]
    return {
        "argv": inner,
        "dispatch_argv": dispatch,
        "profile_path": prof,
        "log_path": prof + ".command.log",
        "dispatch_path": prof + ".dispatch.json",
        "timeout_seconds": 170,
    }


def checked_group(rows, timer):
    if (
        len(rows) > 2
        or any(
            row["pgid"] != timer or (row["pid"] != timer and row["parent"] != timer) for row in rows
        )
        or sum(row["parent"] == timer for row in rows) > 1
    ):
        raise ValueError("clock command has an unregistered descendant")


class Watcher:
    def __init__(self, spec, control):
        self.spec = spec
        self.control = control
        self.root = Path(spec["profile_path"] + ".samplers")
        control.private_mkdir(self.root)
        self.samples = []
        self.last = None
        self.known = set()

    def sample(self, resource, child, began):
        now = time.monotonic()
        if self.last is not None and now - self.last < 0.5:
            return
        index = len(self.samples)
        if index >= 342:
            raise ValueError("clock command exceeded registered sampler count")
        rows, helper = resource._snapshot(self.root, index, child.pid, self.known)
        self.known.update(r["pid"] for r in rows)
        if helper["problem"] is not None:
            raise ValueError("clock sampler failed: " + helper["problem"])
        prof = (self.root / helper["profile"]).read_bytes()
        own = resource._rss_self()
        peak = own + sum(r["rss_bytes"] for r in rows) + helper["native"]["rss_bytes"]
        peak += helper["timer_native_exit"]["native"]["rss_bytes"]
        row = {
            "offset_seconds": now - began,
            "rows": rows,
            "controller_rss_bytes": own,
            "helper": helper,
            "profile_text": prof.decode("ascii"),
        }
        self.samples.append(row)
        checked_group(rows, child.pid)
        self.last = now
        if peak > CAP:
            raise ValueError("clock native RSS sample exceeds 4GiB")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--contract-sha", required=True)
    parser.add_argument(
        "--role",
        required=True,
        choices=("resource-preflight", "scientific-producer", "scientific-auditor"),
    )
    parser.add_argument("--phase", required=True, choices=("publication", "verification"))
    args = parser.parse_args()
    if not sys.flags.isolated or Path.cwd() != ROOT:
        parser.error("exact isolated scientific checkout required")
    path = ROOT / "scripts/p17_m2_scientific_orchestration.py"
    loader = importlib.util.spec_from_file_location("p17_m2_scientific_orchestration", path)
    control = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(control)
    contract = control.read_contract(args.contract, args.contract_sha)
    if contract.get("entry_repair") != "native-bc-entry-20261126-r2":
        parser.error("new caller clock required")
    spec = watch_spec(contract, args.role, args.phase)
    if sys.orig_argv != control.startup_argv(
        spec["dispatch_argv"], args.contract_sha, contract["runtime"]
    ):
        parser.error("frozen native clock dispatcher required")
    watcher = Watcher(spec, control)
    record = control.observe_native(
        contract, args.contract_sha, args.role, "clock-" + args.phase, clock_watcher=watcher
    )
    target = Path(spec["dispatch_path"])
    preflush = target.with_name(target.stem + "-preflush.json")
    observed = {
        "schema": "topolab.native-clock-watch.v1",
        "record_text": target.read_text("ascii"),
        "preflush_text": preflush.read_text("ascii"),
        "samples": watcher.samples,
    }
    # A second observation covers assembling the complete sidecar after native close.
    resource, _ = control.native_helpers()
    control.canonical(observed)  # Materialize the complete packet before reading own highwater.
    observed["wrapper_rss_before_output"] = resource._rss_self()
    control.load("p17_m2_content_verified_control").put(
        Path(spec["profile_path"] + ".resource.json"), observed
    )
    raw, _ = control.read_native_log(Path(spec["log_path"]))
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()
    if record["status"] != "COMPLETED_WITH_NATIVE_RETURN" or record["exit_code"] != 0:
        if not raw:
            print(json.dumps({"native_clock_failure": record["cleanup_errors"]}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
