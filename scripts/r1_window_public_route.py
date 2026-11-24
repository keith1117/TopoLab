"""Use the native staged filer for one literal, independently owned public graph."""

import hashlib
from pathlib import Path

path = Path(__file__).resolve().with_name("formal_input_route.py")
raw = path.read_bytes()
digests = globals().get("entry_digests", {})
digests[str(path)] = hashlib.sha256(raw).hexdigest()
route = {"__file__": str(path), "entry_digests": digests}
exec(compile(raw, str(path), "exec"), route)
sibling = route["sibling"]
scope = sibling("r1_window_scope")


def filer(root):
    root = scope.public_root(root)
    evidence = Path(str(root) + "-evidence")
    wire = route["filer"](
        repo=scope.CHECKOUT,
        evidence=evidence,
        identity=scope.PUBLIC_ID,
        budget=scope.BUDGET,
        target=None,
        control_entry="r1_window_public_control.py",
    )
    wire.PUBLIC = str(root)
    wire.ROOTS = (str(root),)
    wire.graph_root = str(root)
    wire.return_projection = sibling("r0_caller_receipt").project
    wire.window_public = True
    wire.actor_prefix = lambda actor: "r1-window-" + actor
    return wire


def argv_root(argv):
    if "--root" in argv:
        return scope.public_root(argv[argv.index("--root") + 1])
    if argv[:1] == ["persist"] and "--destination" in argv:
        parent = Path(argv[argv.index("--destination") + 1]).parent
        for root in scope.PUBLIC:
            if parent == Path(str(root) + "-evidence"):
                return root
    raise ValueError("public caller requires a registered root")


def main(name, entry, argv):
    if name == "filer":
        sibling("cycle_filing_intent").dispatch(filer(argv_root(argv)), sibling, argv)
    else:
        wire = filer(argv_root(argv))
        sibling("staged_input_waiter", wire=wire, window=sibling("r1_window_public_clock")).main()
