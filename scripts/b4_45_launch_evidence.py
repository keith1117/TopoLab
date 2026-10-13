"""First-only finite public launch/receipt evidence, never a numerical producer."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def load(path):
    def pairs(items):
        value = {}
        for k, v in items:
            if k in value:
                raise ValueError("duplicate JSON key")
            value[k] = v
        return value

    def constant(v):
        raise ValueError("nonfinite constant " + v)

    return json.loads(path.read_bytes(), object_pairs_hook=pairs, parse_constant=constant)


def files(path):
    return {p.name: sha(p.read_bytes()) for p in path.iterdir() if p.is_file()}


def main():
    source, contract_path, evidence = map(Path, sys.argv[1:])
    evidence.mkdir()
    save(
        evidence / "pending.json",
        {
            "phase": "BEFORE_PUBLIC_CASE_LOOP",
            "software_only": True,
            "contract_sha256": sha(contract_path.read_bytes()),
        },
    )
    rows, failure = [], None
    try:
        c = load(contract_path)
        fixture = source / c["fixture_path"]
        assert sha(fixture.read_bytes()) == c["fixture_sha256"]
        f = load(fixture)
        assert f["cases"] == c["public_cases"] and len(f["cases"]) == 12
        assert f["source_sha256"] == c["public_source_sha256"]
        assert all(sha(v.encode()) == f["source_sha256"][k] for k, v in f["source_texts"].items())
        runner = source / "src/topolab/launch_preflight.py"
        baseline = c["source_inputs_at_starting_main_sha256"]
        good_output = None
        for case in f["cases"]:
            case_dir = evidence / case["id"]
            case_dir.mkdir()
            probe = case_dir / "probe"
            probe.mkdir()
            marker_path = probe / (f["module_name"] + ".py")
            marker_path.write_text(f["source_texts"][case["source"]])
            request = {
                "version": "topolab.public-launch-preflight.v1",
                "source_root": str(source),
                "expected_executable": str(source / ".venv/bin/python"),
                "expected_cwd": str(source),
                "expected_source_revision": c["starting_main"],
                "expected_lock_sha256": baseline["uv.lock"],
                "expected_pyproject_sha256": baseline["pyproject.toml"],
                "expected_package_sha256": baseline["src/topolab/__init__.py"],
                "probe_root": str(probe),
                "expected_probe_origin": str(marker_path),
                "expected_probe_sha256": f["source_sha256"][case["source"]],
                "path_mode": "source",
            }
            ident = case["id"]
            if ident == "wrong_interpreter":
                request["expected_executable"] += "-deliberately-absent"
            elif ident == "wrong_cwd":
                request["expected_cwd"] += "/deliberately-absent"
            elif ident == "wrong_lock":
                request["expected_lock_sha256"] = "0" * 64
            elif ident == "missing_package_origin":
                request["path_mode"] = "without_source"
            elif ident == "shadow_probe_origin":
                shadow = case_dir / "shadow"
                shadow.mkdir()
                (shadow / marker_path.name).write_bytes(marker_path.read_bytes())
                request["probe_root"], request["path_mode"] = str(shadow), "shadow_probe"
            elif ident == "changed_probe_bytes":
                marker_path.write_text(
                    "# prescribed public changed bytes\n" + marker_path.read_text()
                )
            elif ident == "changed_package_hash":
                request["expected_package_sha256"] = "0" * 64
            request_path = case_dir / "request.json"
            save(request_path, request)
            output = good_output if ident == "existing_receipt_refusal" else case_dir / "output"
            assert output is not None
            before_existing = files(output) if output.exists() else None
            argv = [
                str(source / ".venv/bin/python"),
                "-I",
                str(runner),
                str(request_path),
                str(output),
            ]
            save(
                case_dir / "before.json",
                {
                    "argv": argv,
                    "request_sha256": sha(request_path.read_bytes()),
                    "existing_output_sha256": before_existing,
                },
            )
            result = subprocess.run(argv, cwd=source, capture_output=True)
            (case_dir / "controller_stdout.log").write_bytes(result.stdout)
            (case_dir / "controller_stderr.log").write_bytes(result.stderr)
            disposition = json.loads(result.stdout)["status"]
            expected_code = (
                0
                if disposition == "PASS_PUBLIC_PREFLIGHT"
                else (2 if disposition == "REFUSED_EXISTING_OUTPUT" else 1)
            )
            after = files(output)
            matches = disposition == case["expected_status"] and result.returncode == expected_code
            if ident == "existing_receipt_refusal":
                matches = matches and before_existing == after
            else:
                matches = matches and all(n in after for n in ("pending.json", "terminal.json"))
            row = {
                "id": ident,
                "expected_status": case["expected_status"],
                "actual_status": disposition,
                "exit_code": result.returncode,
                "passed": matches,
                "output": str(output),
                "before_existing_sha256": before_existing,
                "after_output_sha256": after,
                "request_sha256": sha(request_path.read_bytes()),
                "controller_stdout_sha256": sha(result.stdout),
                "controller_stderr_sha256": sha(result.stderr),
            }
            save(case_dir / "observed.json", row)
            rows.append(row)
            if ident == "clean_external_launch":
                good_output = output
            if not matches:
                raise ValueError("unexpected formal case disposition: " + ident)
    except Exception as exc:
        import traceback

        failure = {
            "type": type(exc).__name__,
            "detail": str(exc),
            "traceback": traceback.format_exc(),
        }
    receipt = {
        "version": "topolab.b4_45.public-launch-evidence.v1",
        "passed": failure is None,
        "formal_calls": 1,
        "formal_retry": False,
        "cases": rows,
        "failure": failure,
        "not_evaluated": [c0["id"] for c0 in c["public_cases"][len(rows) :]]
        if "c" in locals()
        else "UNKNOWN",
        "numeric_cases": 0,
        "real_payload_reads": 0,
        "fits": 0,
        "software_only": True,
    }
    save(evidence / "primary.json", receipt)
    print(
        json.dumps({"passed": receipt["passed"], "completed_cases": len(rows), "failure": failure})
    )
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
