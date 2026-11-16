# Independent worker deadline repair

Date: 2026-11-16. Baseline: main
`8651ad1268c26cd6fa1e1f09424b5bedd8fdc0bd`, tree
`aca86fd8fae12fb56f4150ee9ca4f9ec44d7b804`, published through
[PR236](https://github.com/keith1117/TopoLab/pull/236).
Read-only recovery verified no open PR and successful baseline
[CI41941201733](https://github.com/keith1117/TopoLab/actions/runs/41941201733).

The owner requested continuation from the seed17 chat and repair of its current
blocker. This slice implements a public software worker deadline capability.
It grants no original-input read, formal role, historical retry, lease release,
scientific execution or transfer of a closed allowance.

## Blocker and acceptance

The surviving V37 delivery manifest SHA256 is
`365e9b94881081ce262dcd500e568453ebd51d3a0b96e4fb6d9658efb010feb9`.
The exact archived probe driver SHA256 is
`4654268b7004411b7784468a9311426420171db974b40a4855875217707cd8de`.
Its combined worker arms a one-shot work50 alarm. A nested `except BaseException`
catches the resulting `TimeoutError`, while the closing5 alarm is only installed
after nested cleanup returns. Blocked cleanup or filing therefore has no hard
deadline during that interval. This is an engineering defect; the earlier review
did not measure an actual overrun, memory exceedance or new scientific FAIL.

The acceptance boundary is an independent process terminating that worker at a
caller-fixed absolute deadline despite caught alarms or blocked worker cleanup.
Required observations are the termination request, actual worker exit and reap,
retained primary/secondary errors and an externally observed supervisor return.
Worker termination does not certify the complete execution environment.

## Change and verification

[`public_worker_deadline.py`](../../scripts/public_worker_deadline.py) is the
prospective outer entry point for a public software worker. The caller supplies
absolute Unix and monotonic deadlines; both precede launch and each may be at
most 55 seconds ahead. Metadata preparation, launch and waiting consume those
same deadlines. The supervisor independently checks both clocks and rejects a
backwards UTC observation. It requests SIGKILL for the owned, unreaped worker
process group on failure, then permits at most two seconds for reap. Neither a
caught worker alarm nor entry into cleanup resets the deadline.

Worker output goes to files, avoiding a blocking pipe drain in the supervisor.
The supervisor preserves the actual exit, original primary error and secondary
termination/reap/filing errors. A failed final report write retains a STOP packet
on stdout. `WORKER_EXITED` means that the worker exited0 and its exit was observed
before both deadlines; it does not assert that all descendants exited. The caller
must retain this supervisor's actual return; its report says NOT_CLAIMED for its
own future tool exit.

Public verification follows the existing CLI/process boundary:

- Root and a new independent author both reproduced RED against the exact
  archived `combined_main`: at offset50, nested cleanup had no hard alarm;
  its later closing5 was armed only at offset55. Only public clock/payload/file
  boundaries were replaced. No Docker or original input was accessed.
- Regression-first development then exercised real processes which catch the
  work alarm, ignore SIGTERM and sleep in cleanup. The supervisor still requests
  SIGKILL at the original absolute deadline, observes exit-9 and reaps the worker.
- Eight focused regressions cover that path, early0/nonzero37 exits and logs,
  expired no-launch, actual Popen failure, blocked worker FIFO filing, final
  report-write failure with retained primary/secondary errors, and a same-group
  descendant holding a file lock. No numerical tolerance changed.
- Root's integration wrapped the exact archived `combined_main` in this actual
  supervisor, replacing only the public payload and scaling the work alarm.
  The nested-cleanup marker was observed; worker exit-9 and supervisor exit1
  occurred in 2.033399 seconds. Independent fresh-path integration observed
  the same expected STOP in 2.01397 seconds, with no secondary errors.
- Independent focused verification: 8 passed in 3.43 seconds. The advisory report
  field was renamed from `containment_scope` to `signal_scope` to avoid claiming
  group closure when the leader exits early.

New different-author review found no blocking P1/P2 or scope overclaim; final
focused rerun passed8 in3.39s. Its external `independent-final-review.json` SHA256
is `3dddcf7e47426021cd1c600be21b27d53eb17678890b2259019aee5480a74132`.
Final reviewed helper SHA256 is
`e4923c8abcc151e914176162aadcb1332abe44e5d6ae4b4452d1e21e83caa7be`.
Initial independent elapsed415.552/3600s is retained; later review uses the same
original registered deadline, without resetting its elapsed time.

The first complete check exposed a naming integration defect: calling the new
standalone helper `p17_m2_deadline_executor.py` caused the historical
`p17_m2_*.py` source-closure glob to collect55 members instead of54. The focused
legacy test reproduced RED (1 failed/4 passed). That full run was interrupted after1 failed/2082 passed/1 platform skip in
1233.12s, with its failed log retained. Renaming the standalone tool to
`public_worker_deadline.py` keeps it outside historical execution closures;
no frozen closure, assertion, threshold or production compiler is changed.
A future caller must explicitly bind this new outer dependency in its own
compatible execution contract. Root focused checks passed34 in3.62s; independent
legacy-plus-worker checks passed34 in11.11s. Helper bytes are unchanged by the
rename; the old compilers and54-member assertion have no diff. Additive review
receipt SHA256 is
`1063a72245c0c822030ff82d6a1c8d9b09e1edc5bbf476cf6d5408c140f487be`.
Independent elapsed1575.527/3600s is measured from its original07:43:13 UTC start,
including the intervening wait; no clock or closed grant was reset. A complete
fresh check is still required after this integration correction.

The second complete check retained3 failed/2956 passed/1 platform skip in
1897.66s before interruption. One failure is confirmed environmental placement:
the unchanged source2 public fixture rejects every `TopoLab-data` path, including
this task's code clone located there. The new active clone is
`/private/tmp/topolab-worker-deadline-20261116`; all nine reviewed files were
copied byte-for-byte and the original persistent clone remains. No test guard,
compiler or scientific rule changed. The source2/closure/worker combination
passes71 in4.14s at the isolated location. The two other failed public native
checks retain their original non-complete-command and payload-exit-15 evidence;
their historical causes remain UNKNOWN pending separate diagnosis. At the isolated location the two native rechecks passed2 in81.46s, with
actual command exit0 and unchanged code/windows. This fresh pass cannot
retrospectively establish either old cause. Exact failed logs, relocation
bindings and fresh rechecks remain external. Independent relocation review
confirmed all nine copied files and unchanged guard/producer/checker bytes;
the named regression passed1 in13.91s with actual exit0. Its receipt SHA256 is
`0dad5e83c1dcdc0d8f64755bb2995200e9ab79e433ab460756c5916a4b14a63c`.
Independent elapsed3577.241/3600s retains the original07:43:13 UTC start and
08:43:13 UTC hard end; that review allowance is now closed without transfer.

Complete required checks and protected publication are recorded at the final
verification frontier below; baseline CI cannot substitute for them.

## Remaining boundary and next step

The helper signals only the worker's original process group. V37 deliberately
starts some helpers in separate sessions; Docker workloads also require their
existing independent exact-CID watchdog and ownership checks. Early leader exit
does not prove group closure. This slice does not run the real containment proof,
certify all detached helpers/namespace cleanup, establish an OS scheduling
guarantee, or prove supervisor startup-through-filing/actual return within FULL60.
Blocking supervisor filesystem operations and missing actual outer returns must
still prevent whole-executor acceptance. The real root integration and finite
caller contract must retain those requirements before any future formal launch.

V37 remains CLOSED_BLOCKED_AFTER_TWO_SOFTWARE_ROUNDS, formal0/6 and B/C0, with
all unstarted allowances closed. Its 35-path candidate remains unpublished;
this change imports none of it. Known NEW FULL lower334530 is retained. New
maintenance, review, regression, waiting, CI, retention and publication are
additional software costs, UNKNOWN_NOT_ZERO where not measured. The fresh
software-only scope records root<=10800 seconds from registration and new
independent review<=3600 seconds, at most two correction rounds; preregistration
recovery costs remain additional and unmeasured. No formal FULL charge or budget
is created by this helper. Historical
`12721.16417100014444982 > 7200` cannot pass unchanged all-paid feasibility;
full-fit PENDING4GiB, fixed P/17 unrepaired, uniform default and all old failures,
costs, UNKNOWNs, quotas and seals remain.

The single next prerequisite is complete prospective public integration of the
remaining candidate, its independent exact-CID watchdog, detached helpers and
actual outer return under a valid finite execution contract. Independently
accepted complete input must precede B resource admission and fixed C validation.
No scientific repair or final evidence access follows from this software pass.

## Evidence retention and final verification frontier

New evidence is external at
`/Users/keith1117/Documents/TopoLab-data/engineering-deadline-20261116`.
Its `recovered/` files match the prebound V37 manifest. Five related software
helpers/review records were copied byte-for-byte to persistent independent-inode
storage at
`/Users/keith1117/Documents/TopoLab-data/engineering-deadline-20261116-backup`;
`backup-anchor.json` outside that backup binds its manifest. The old archive was
not mutated. Its missing temporary mirror and UNKNOWN cause remain; this
five-file recovery does not certify the complete old 117-member archive today.

The two original dirty workspaces retain their original13+12 files and HEAD/index/
status baselines. A fresh independent clone, actively tested outside the evidence root, hosts this branch; no reset, clean,
stash, lease unlock or failed-scene reuse was performed.

The isolated complete check passed all five required commands: locked uv sync,
Ruff, mypy82 source files, full pytest and diff check. Full pytest returned0:
**3545 passed,2 skipped in1678.92s**. The unchanged skip conditions are the selected
Linux-x86-64 freestanding surface and an exact-URL Foundation integration needing
a new public parent. No test was deselected or tolerance changed; the skipped
Foundation integration is UNKNOWN_NOT_RUN here, not new acceptance.

Final independent-review, preservation and protected PR/main-CI receipts bind
this source in the external release closure. At report authoring publication
is pending; neither local checks nor later CI supplies scientific acceptance.
The new source bundle and persistent reviewed files support recovery if the
active temporary clone disappears. Execute future public regression from a
code path outside `TopoLab-data`, preserving its existing evidence-read guard.
