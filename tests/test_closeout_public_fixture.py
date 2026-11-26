"""Public receipt integrity and single-use filing at the closeout boundary."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def from_source(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def control(tmp_path, monkeypatch):
    native = from_source("p17_m2_content_verified_control")
    module = from_source("closeout_public_control")
    wire = from_source("staged_input_filer")
    intents = from_source("cycle_filing_intent")
    monkeypatch.syspath_prepend(str(SCRIPTS))
    root = tmp_path / "public"
    root.mkdir()
    receipts = root / "receipts"
    receipts.mkdir()
    # macOS's /var alias is unsuitable for the no-follow custody writer.
    root = root.resolve()
    wire.EVIDENCE = root.with_name("source-evidence")
    wire.BACKUP = wire.EVIDENCE.with_name("source-evidence-backup")
    for folder in (wire.EVIDENCE, wire.BACKUP):
        folder.mkdir()
    return SimpleNamespace(module=module, native=native, wire=wire, intents=intents, root=root)


def source_packet(ctx, mode):
    native, wire, role = ctx.native, ctx.wire, ctx.module.SHARED
    plan = "c" * 64
    argv = native.argv_for(ctx.root, mode, plan, role)
    if mode == "supervise":
        native.put(
            ctx.root / "receipts" / (role + "-pending.json"),
            dict(
                plan_sha256=plan,
                external_argv=[argv, native.argv_for(ctx.root, "record", plan, role)],
            ),
        )
        output = dict(status="PENDING_EXTERNAL_EXIT", controller_exit=0)
    else:
        value = dict(completion=dict(status="PENDING_EXTERNAL_EXIT"))
        native.put(ctx.root / "receipts" / (role + "-wire.json"), value)
        output = ctx.module.compact(native, mode, role, plan, value)
    request = dict(cmd=wire.literal_command(argv), workdir=str(Path.cwd()))
    start = 1000 if mode == "supervise" else 1010
    row = dict(
        tool="exec_command",
        arguments=request,
        requested_ms=start,
        returned_ms=start + 1,
        result=dict(exit_code=0, output=native.canonical(output).decode()),
    )
    return dict(
        schema=wire.ACTUAL_SCHEMA,
        author=ctx.module.AUTHOR,
        event_id=f"{role}-{mode}",
        argv=argv,
        request=request,
        responses=[row],
    )


def test_public_record_custody_and_single_filing(control):
    c = control
    for mode in ("supervise", "record"):
        packet = source_packet(c, mode)
        args = (c.native, c.wire, c.intents, c.root, "c" * 64, c.module.SHARED, mode)
        saved = c.module.save_packet(*args, packet)
        assert saved["bytes"] == len(c.wire.canonical(packet))
        assert c.module.paired(c.wire.EVIDENCE, Path(saved["path"]).name) == c.wire.canonical(
            packet
        )
        pins = (saved["sha256"], saved["file_intent_sha256"], saved["program_sha256"])
        with pytest.raises(ValueError):
            c.module.file_event(*args, "0" * 64, *pins[1:])
        assert c.module.file_event(*args, *pins)["status"] == "ACTUAL_EVENT_FILED"
        with pytest.raises(ValueError):
            c.module.file_event(*args, *pins)
    events = json.loads((c.root / "shared-closeout-events.json").read_bytes())
    assert [item["event_id"] for item in events] == [
        "shared-closeout-supervise",
        "shared-closeout-record",
    ]


def test_changed_original_public_output_cannot_create_intent(control):
    c = control
    packet = source_packet(c, "supervise")
    packet["responses"][0]["result"]["output"] = "{}"
    with pytest.raises(ValueError, match="returned native output"):
        c.module.save_packet(
            c.native, c.wire, c.intents, c.root, "c" * 64, c.module.SHARED, "supervise", packet
        )
    assert list(c.wire.EVIDENCE.iterdir()) == []


def test_public_entry_rejects_formal_target_before_read():
    c = from_source("closeout_public_control")
    with pytest.raises(ValueError, match="literal fixture"):
        c.claim_for(Path("/private/tmp/unregistered"))


def test_public_loader_records_same_compiled_buffer(tmp_path, monkeypatch):
    fixture = from_source("closeout_public_control")
    path = tmp_path / "loader.py"
    raw = b"loaded_source_sha256 = {}\nvalue = 7\n"
    path.write_bytes(raw)
    # Restore the prior runtime module after this isolated public software test.
    monkeypatch.setitem(sys.modules, "full60_input_loader", None)
    loader = fixture.source_loader(path, fixture.digest(raw))
    assert loader.value == 7
    assert loader.loaded_source_sha256[str(path.resolve())] == fixture.digest(raw)
    changed = raw.replace(b"7", b"8")
    path.write_bytes(changed)
    with pytest.raises(ValueError, match="compiled public loader differs"):
        fixture.source_loader(path, fixture.digest(raw))
    assert sys.modules["full60_input_loader"] is loader
    assert loader.loaded_source_sha256[str(path.resolve())] != fixture.digest(changed)


@pytest.mark.parametrize(
    ("results", "window", "error", "polls"),
    [
        ([{"session_id": 17}, {"session_id": 29}], 90000, "owned session", [17]),
        ([{"session_id": "17"}], 90000, "owned session", []),
        ([{"session_id": 17, "exit_code": 0}], 90000, "owned session", []),
        ([{"session_id": 17}, {"session_id": 17, "exit_code": 0}], 90000, "owned session", [17]),
        ([{"session_id": 17}, {"exit_code": "0"}], 90000, "terminal exit", [17]),
        ([{"session_id": 17}, {"session_id": 17}, {"exit_code": 1}], 90000, "failed", [17, 17]),
        ([{"session_id": 17}], 1000, "polling window", []),
        ([{"session_id": 17}], 90000, "transport rejected", [17]),
    ],
)
def test_schedule_stops_with_exact_original_rows(results, window, error, polls):
    # The whole public schedule starts at prepare. A provider that loses the session
    # must stop here and retain every returned row, including the malformed response.
    program = """
    import {publicCloseout} from './scripts/closeout_public_schedule.mjs';
    const [results, window] = JSON.parse(process.argv[1]);
    const trace = [], originals = [];
    async function invoke(tool, args) {
      trace.push([tool, args.session_id]);
      if (originals.length === results.length) throw Error('transport rejected');
      const row = {tool, arguments:args, requested_ms:Date.now(), returned_ms:Date.now(),
        result:{output:'', ...results[originals.length]}};
      originals.push(row);
      return row;
    }
    const out = await publicCloseout({end:Date.now()+window, root:'public-fixture',
      control:'public-control', python:'python', checkout:'.'},
      {invoke}, {literalCommand:()=>'mock'});
    console.log(JSON.stringify({out, trace, originals}));
    """
    result = subprocess.run(
        ["node", "--input-type=module", "-e", program, json.dumps([results, window])],
        cwd=SCRIPTS.parent,
        capture_output=True,
        text=True,
        check=True,
    )
    observed = json.loads(result.stdout)
    report = observed["out"]
    assert report["stage"] == "prepare" and report["status"] == "STOP_PUBLIC_CLOSEOUT"
    assert error in report["error"]
    assert list(report["calls"]) == ["prepare"] and report["roles"] == {}
    assert report["calls"]["prepare"]["responses"] == observed["originals"]
    assert observed["trace"] == [["exec_command", None], *[["write_stdin", pid] for pid in polls]]
