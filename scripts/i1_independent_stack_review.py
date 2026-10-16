"""Reproduce I1 bounded constant-RSP facts, never complete resource admission.

The sibling imported module is the same independent reviewer's ELF parser, not
the primary inspector. No target ELF executes; explicit bounded/hash-bound
artifact/source reads are repeated. See its CLI and read boundary documentation.
Calls preserve caller RSP after return; callee frames count separately. The
assembly entry alignment/scratch bound still needs source/manual review.
"""

import collections
import re
import struct
import subprocess

from i1_independent_elf_review import (
    MAX_FUNCTIONS,
    arguments,
    load_evidence,
    require,
    review_evidence,
    write_review,
)

MAX_STATES = 262144


def review_stack(options):
    facts = review_evidence(options)
    _, files, _ = load_evidence(options)
    answer = {}
    total_states = 0
    for role, rolefacts in facts["roles"].items():
        data = files[role + "-objdump.txt"]
        groups = {}
        current = None
        for line in data.decode().splitlines():
            label = re.match("^([0-9a-f]+) <([^>]+)>:$", line)
            if label:
                current = label[2]
                groups[current] = []
                continue
            m = re.match("\\s*([0-9a-f]+):\\s+((?:[0-9a-f]{2}[ \\t]+)+)(.*)$", line)
            if m and m[3].strip():
                groups[current].append((int(m[1], 16), m[3].split("#")[0].strip()))
        require(len(groups) <= MAX_FUNCTIONS, "function cap")
        starts = {code[0][0]: name for name, code in groups.items()}
        noreturn = set()
        for name, code in groups.items():
            if name == "_start":
                continue
            local = {a for a, _ in code}
            has_return = any((asm.split()[0].startswith("ret") for _, asm in code))
            external_tail = any(
                (
                    asm.split()[0] in ("jmp", "jmpq") and int(asm.split()[1], 16) not in local
                    for _, asm in code
                )
            )
            if not has_return and (not external_tail):
                noreturn.add(name)
        require(
            noreturn == ({"child_exit.constprop.0"} if role == "controller" else set()),
            "independent structural condition line 23",
        )
        result = {}
        for name, code in groups.items():
            if name == "_start":
                continue
            require(name in rolefacts["frames"], name)
            addresses = {a: i for i, (a, _) in enumerate(code)}
            work = collections.deque([(0, 0, None)])
            visited = set()
            states_at = collections.defaultdict(set)
            max_descent = 0
            writes = []
            edge_count = 0
            while work:
                idx, sp, bp = work.popleft()
                state = (idx, sp, bp)
                if state in visited:
                    continue
                require(len(visited) <= MAX_STATES, "stack CFG state cap")
                total_states += 1
                require(total_states <= MAX_STATES, "total stack CFG state cap")
                visited.add(state)
                states_at[idx].add((sp, bp))
                require(
                    len(states_at[idx]) < 20, (role, name, "possible unbounded stack loop", state)
                )
                address, asm = code[idx]
                op, *rest = asm.split(None, 1)
                args = rest[0] if rest else ""
                oldsp = sp
                if op.startswith("push"):
                    require(op not in ("pushw", "pushf", "pushfw"), asm)
                    sp -= 8
                elif op.startswith("pop"):
                    require(op not in ("popw", "popf", "popfw"), asm)
                    sp += 8
                    if args == "%rbp":
                        bp = None
                    require(args != "%rsp", "independent structural condition line 48")
                elif op == "leave":
                    require(bp is not None, (role, name, asm))
                    sp = bp + 8
                    bp = None
                elif op == "mov" and args == "%rsp,%rbp":
                    bp = sp
                elif args.endswith(",%rsp"):
                    if op in ("sub", "add"):
                        m = re.fullmatch("\\$(0x[0-9a-f]+|[0-9]+),%rsp", args)
                        require(m, (role, name, asm))
                        n = int(m[1], 0)
                        sp += n if op == "add" else -n
                    elif op == "mov" and args == "%rbp,%rsp":
                        require(bp is not None, "independent structural condition line 59")
                        sp = bp
                    elif op == "lea":
                        m = re.fullmatch("(-?(?:0x[0-9a-f]+|[0-9]+))?\\(%rbp\\),%rsp", args)
                        require(m and bp is not None, (role, name, asm))
                        sp = bp + int(m[1] or "0", 0)
                    else:
                        raise ValueError((role, name, "unaccounted RSP assignment", asm))
                max_descent = max(max_descent, -sp)
                if sp != oldsp:
                    writes.append([hex(address), asm, oldsp, sp])
                successors = []
                if op.startswith("call") and starts[int(args.split()[0], 16)] in noreturn:
                    pass
                elif op.startswith("ret") or op == "ud2":
                    if op.startswith("ret"):
                        require(sp == 0, (role, name, "unbalanced return", asm, sp))
                elif op.startswith("j") or op.startswith("loop"):
                    target = int(args.split()[0], 16)
                    if target in addresses:
                        successors.append(addresses[target])
                    else:
                        require(
                            op in ("jmp", "jmpq"), (role, name, "conditional external branch", asm)
                        )
                        require(sp == 0, (role, name, "unbalanced tail jump", asm, sp))
                    if op not in ("jmp", "jmpq") and idx + 1 < len(code):
                        successors.append(idx + 1)
                elif idx + 1 < len(code):
                    successors.append(idx + 1)
                for nxt in successors:
                    edge_count += 1
                    work.append((nxt, sp, bp))
            report = rolefacts["frames"][name]
            require(len(writes) <= MAX_STATES, "RSP transition cap")
            require(max_descent <= report["bytes"], (role, name, max_descent, report))
            result[name] = {
                "actual_max_caller_rsp_descent": max_descent,
                "reported_max_frame": report["bytes"],
                "all_rsp_writes_constant_or_rbp_restore": True,
                "reachable_instruction_states": len(visited),
                "rsp_transitions": writes,
                "successor_edges": edge_count,
            }
        require(set(result) == set(rolefacts["frames"]), "independent structural condition line 88")
        answer[role] = result
    return {
        "source_sha": options.source_sha,
        "elf_executed": False,
        "roles": answer,
        "complete_resource_admission": "UNKNOWN_NOT_RESOURCE_ADMITTED",
        "remaining_mandatory_terms": facts["remaining_mandatory_terms"],
        "scope": "RSP constants/CFG only; P/K/kernel/startup/exit not established",
    }


def main():
    parser, args = arguments(__doc__)
    try:
        result = review_stack(args)
        write_review(args, "actual-stack-review.json", result)
    except (
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        OSError,
        StopIteration,
        struct.error,
        UnicodeError,
        subprocess.SubprocessError,
    ) as error:
        parser.exit(2, "UNKNOWN_REVIEW_REJECTED: " + str(error)[:400] + "\n")


if __name__ == "__main__":
    main()
