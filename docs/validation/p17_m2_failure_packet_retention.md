# Public failure packet and out-of-window accounting repair

Owner instruction2026-10-22 authorizes only two confirmed software defects,
regression tests first and minimal changes. Baseline main is
`447592c854bd927b3e3020966c609d625bd6fd30` (PR214). This is public software
maintenance under [roadmap Section6](../planning/TopoLab_v2_development_roadmap.md#6-current-sequence-after-the-delivery-reassessment),
not a new formal identity, source admission or scientific result.

## Behavior and minimal changes

1. In `dispatchRoleStable`, both shared tool calls could return before the
   final-frontier deadline/reserve check threw. The exception bypassed packet
   retention and left the role active. The dispatcher now retains the complete
   pending/completion/events/terminal packet, raw tool returns and collector
   binding, records the frontier failure and observed time, and clears active
   state. A failed closure is STOP_NO_RETRY with acceptance false; it supplies no
   successful formal-close/release marker. Existing primary failure facts and
   reasons remain. Consumed-role and final-filing guards still refuse reuse.
2. JS `finishExternal` and Python `audit_full_role_v2` rejected actor-window
   overrun before certifying otherwise valid raw event time and cost. Both now
   validate the entire clock/order/argv stream and record its span and charge
   before applying the unchanged actor-window rejection. Invalid streams retain
   UNKNOWN whole-wall. Complete/exit/resource/domain checks remain required for
   acceptance. The independent implementations remain separate.

The immutable FULL, actor deadline,4500s window,360s frontier reserve,4GiB,
1ms resolution and `max(FULL,ceil(whole+10),ceil(inner minimum))` rules are
unchanged. A valid raw interval1000→5500.001 is4500.001s and costs at least
4511s; it still STOPs outside deadline5500. The exact endpoint5500 costs4510s
and still fails the role FULL300. Malformed clock/argv cannot certify a span.
This synthetic counterexample establishes a recording defect, not historical
underbilling or recovered historical evidence.

## Test-first evidence

The public seam is the real exported dispatcher/JS checker and independent
Python audit. Only external tool returns and time are mocked; no formal CLI is
run. A synthetic six-role chain exercises the dispatcher through shared return.
Fresh fixtures contain no historical source/data/receipt/backup/sealed input.

- Before the first fix: normal closeout passed; late tool return and late
  post-return closure each failed because the retained packet was absent
  (2 failed/1 passed). The same tests passed after the first minimal patch.
- Before the second fix: both adapters lost valid spans for fractional/integer
  overrun, missing exit and bad completion (8 failed/6 passed). Exact deadline
  and malformed-stream controls retained their expected outcomes.
- After both fixes: all17 new cases passed. The existing focused population
  plus these cases passed316/316. Ruff passed; mypy passed82 source files.
- Complete locked regression:2434 passed/1 selected Linux-only platform skip,
  pytest-reported684.14s. `uv sync --dev --locked`, `uv run ruff check .`,
  `uv run mypy src`, complete thread-bounded `uv run pytest` and
  `git diff --check` all passed. Relative documentation links passed.
  This elapsed test view does not replace whole-slice/CI billing.

Tests also require full packet equality across returned/stored/latest views,
raw returns and collector retention, active-state completion, actual exits,
STOP/no acceptance, no false release, refused retry/final filing and no extra
external calls after rejection. No tolerance or fixture rule is loosened.

## Delivery boundary and remaining blocker

No formal role ran, no old quota/window/grant reopened, and no original scientific input or
historical receipt/model/label/backup was read. The original checkout's uncommitted
changes are preserved; implementation is isolated from it. Historical frozen
protocols and reports retain bytes. Software/debug/test/CI costs are additional;
unmeasured whole-slice cost/fees remain UNKNOWN_NOT_ZERO, never drawn from a
closed formal allowance.

R-CUSTODY remains NO_SOURCE_ADMISSION_KEEP_STOP: feasible attributed iCloud
project control and current OneDrive Documents mapping/scoped exclusion remain
missing. Fixed P/17 is unrepaired, uniform remains default, science is paused,
and FULL_V2_OPEN_NO_ADMITTED_ROUTE/4GiB/independent preflight and all old
failures/costs/UNKNOWN/consumed quotas/seals remain. There is no automatic next
slice, formal rerun or scientific progress claim from this repair.
