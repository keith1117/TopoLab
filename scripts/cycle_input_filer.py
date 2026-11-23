"""File actual returns for the single formal input acceptance grant."""

import hashlib
import sys
from pathlib import Path

NOTE = "coordinator-launch-note-a1.json"
ACTIVATION = "formal-activation-entry-a1.json"


def dispatch(wire, argv):
    if argv[:1] == ["dispatch-note"]:
        wire.need(argv == ["dispatch-note", "--root", wire.FORMAL], "launch note root differs")
        raw = wire.canonical(
            dict(
                schema="topolab.input-cycle-coordinator-note.v1",
                author="/root",
                execution_identity=wire.IDENTITY,
                owner_budget_sha256=wire.BUDGET_SHA,
                root=wire.FORMAL,
                own_future_return="NOT_CLAIMED",
            )
        )
        for folder in (wire.EVIDENCE, wire.BACKUP):
            path = folder / NOTE
            try:
                wire.write_private(path, raw)
            except FileExistsError:
                wire.need(wire.read_private(path) == raw, "existing coordinator note differs")
        wire.need(
            not (wire.EVIDENCE / NOTE).samefile(wire.BACKUP / NOTE), "distinct copies required"
        )
        print(
            wire.canonical(dict(status="COORDINATOR_NOTE_RETAINED", sha256=wire.sha(raw))).decode(),
            end="",
        )
        return
    original = wire.persist

    def persist(packet, destination):
        wire.need(Path(destination).name not in (NOTE, ACTIVATION), "reserved launch file")
        return original(packet, destination)

    wire.persist = persist
    wire.main()


if __name__ == "__main__":
    entry = Path(__file__).resolve()
    path = entry.with_name("cycle_input_route.py")
    raw = path.read_bytes()
    route = {
        "__file__": str(path),
        "entry_digests": {
            str(entry): hashlib.sha256(entry.read_bytes()).hexdigest(),
            str(path): hashlib.sha256(raw).hexdigest(),
        },
    }
    exec(compile(raw, str(path), "exec"), route)
    dispatch(route["filer"](), sys.argv[1:])
