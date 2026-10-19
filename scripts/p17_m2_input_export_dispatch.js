/* Independently authored finite external-tool boundary for NEW R/v2.
 * No filesystem, native helper, numerical oracle or producer PASS is used here.
 * Root may append orchestration after the independent initial-source snapshot.
 */

function finishExternal(pending, completion, events, resourceEvidence, expectedPendingSha256) {
  const identity = "topolab.v2.p17-m2-input-export-preparation.v2";
  const caps = {
    "independent-public-check": 120,
    "exporter-r0": 120,
    "independent-r0": 120,
    "exporter-r1": 780,
    "independent-r1": 660,
    "shared-closeout": 60,
  };
  const cap = caps[pending.role];
  const result = {
    schema: "topolab.v2.m2-input-export-exit.v2",
    execution_identity: identity,
    role: pending.role,
    plan_sha256: pending.plan_sha256,
    pending_sha256: completion.pending_sha256,
    frozen_FULL_seconds: cap ?? null,
    status: "STOP_NO_RETRY",
    reason: "UNKNOWN_INCOMPLETE_OUTER_EVIDENCE",
    clock_domain: null,
    T0: null,
    T1: null,
    whole_wall_seconds: null,
    raw_tool_events: events,
    actual_exit_codes: events.map((event) => event.exit_code ?? null),
    RSS_envelope_bytes: resourceEvidence?.RSS_envelope_bytes ?? null,
    RSS_components_bytes: resourceEvidence?.RSS_components_bytes ?? null,
    inner_minimum_charge_seconds: resourceEvidence?.inner_minimum_charge_seconds ?? null,
    cleanup: completion.cleanup ?? null,
    known_cost_lower_bound_seconds: cap ?? null,
    missing_evidence_cost: "UNKNOWN_NOT_ZERO",
    full_role_evidence_accepted: false,
    source_successor_admitted: false,
    B_C_admission: false,
    a_priori_allocation_guarantee: false,
  };
  function require(condition, message) {
    if (!condition) throw new Error(message);
  }
  function number(value) {
    require(typeof value === "number" && Number.isFinite(value) && value >= 0,
      "missing/nonfinite/negative external numeric field");
    return value;
  }
  try {
    require(Number.isInteger(cap) && /^[0-9a-f]{64}$/.test(pending.plan_sha256),
      "unregistered role/plan");
    for (const record of [pending, completion]) {
      require(record.execution_identity === identity && record.role === pending.role
        && record.plan_sha256 === pending.plan_sha256 && record.frozen_FULL_seconds === cap,
      "v2 identity/plan/immutable FULL differs");
      require(record.clock_domain === "functions.exec.Date.now.UTC-seconds"
        && record.clock_resolution_seconds === 0.001,
      "unfrozen external clock identity/resolution");
    }
    require(completion.status === "PENDING_EXTERNAL_EXIT"
      && /^[0-9a-f]{64}$/.test(expectedPendingSha256)
      && completion.pending_sha256 === expectedPendingSha256,
    "internal terminal cannot certify future exit");
    require(events.length > 0, "UNKNOWN_MISSING_ACTUAL_OUTER_EVENT");
    result.clock_domain = events[0].clock_domain;
    result.T0 = number(events[0].start_seconds);
    result.T1 = number(events.at(-1).end_seconds);
    const whole = result.T1 - result.T0;
    require(whole >= 0, "outer clock regression");
    result.whole_wall_seconds = whole;
    result.known_cost_lower_bound_seconds = Math.max(cap, Math.ceil(whole + 10));
    let previousEnd = result.T0;
    const ids = new Set();
    for (const event of events) {
      const start = number(event.start_seconds);
      const end = number(event.end_seconds);
      const nativeWall = number(event.wall_seconds);
      require(typeof event.event_id === "string" && event.event_id.length > 0
        && !ids.has(event.event_id), "duplicate/missing external event ID");
      ids.add(event.event_id);
      require(typeof event.clock_domain === "string" && event.clock_domain.length > 0
        && event.clock_domain === result.clock_domain
        && event.clock_domain === "functions.exec.Date.now.UTC-seconds" && previousEnd <= start
        && start <= end && end <= result.T1 && nativeWall <= end - start + 0.001,
      "external event clock/order/wall differs");
      require(Array.isArray(event.argv) && event.argv.length > 0
        && event.argv.every((word) => typeof word === "string"),
      "external argv missing");
      require(event.complete === true && Number.isInteger(event.exit_code),
        "UNKNOWN_MISSING_ACTUAL_FINAL_EXIT");
      previousEnd = end;
    }
    if (pending.external_argv !== undefined) {
      require(JSON.stringify(pending.external_argv) === JSON.stringify(events.map((e) => e.argv)),
        "external literal argv differs");
    }
    // The Python independent checker runs INSIDE the measured finalizer. It
    // reconciles raw profile bytes and inner receipt details, never producer PASS.
    require(resourceEvidence?.status === "PENDING_EXTERNAL_EXIT"
      && resourceEvidence.full_role_evidence_accepted === false,
    resourceEvidence?.reason ?? "UNKNOWN_MISSING_INDEPENDENT_RESOURCE_EVIDENCE");
    for (const key of ["execution_identity", "role", "plan_sha256", "pending_sha256",
      "frozen_FULL_seconds"]) {
      require(resourceEvidence[key] === completion[key], "independent resource identity differs");
    }
    const rss = number(resourceEvidence.RSS_envelope_bytes);
    require(Number.isInteger(rss) && rss > 0 && rss <= 4294967296,
      "missing RSS or retained 4GiB exceeded");
    const minimum = number(resourceEvidence.inner_minimum_charge_seconds);
    result.known_cost_lower_bound_seconds = Math.max(cap, Math.ceil(whole + 10),
      Math.ceil(minimum));
    require(result.actual_exit_codes.every((exit) => exit === 0),
      "actual final serializer/outer exit nonzero");
    require(completion.cleanup?.group_gone === true,
      "UNKNOWN_INCOMPLETE_GROUP_CLEANUP");
    require(Math.max(whole + 10, minimum) <= cap,
      "FAIL_FULL_NAMED_WALL_CHARGE_BINDING");
    result.status = "PASS_R_V2_FULL_ROLE";
    result.reason = null;
    result.missing_evidence_cost = null;
    result.full_role_evidence_accepted = true;
  } catch (error) {
    result.reason = String(error.message ?? error);
  }
  return result;
}

if (typeof module !== "undefined") module.exports = { finishExternal };

/* Versioned orchestration in the SAME trusted external-tool invocation.
 * Context is the frozen launch plan; dynamic telemetry is previous actual tool
 * OUTPUT, not a new source identity. No native process runs after final event.
 */
async function dispatchRoleV2(context, role) {
  if (context.execution_identity !== "topolab.v2.p17-m2-input-export-preparation.v2"
      || !Object.hasOwn(context.external_argv, role)) throw new Error("unregistered R/v2");
  const previous = load("r2-last-packet") ?? null;
  const order = ["independent-public-check", "exporter-r0", "independent-r0",
    "exporter-r1", "independent-r1", "shared-closeout"];
  const index = order.indexOf(role);
  if (index < 0) throw new Error("unregistered R/v2 role");
  if (load("r2-active-role") || load("r2-attempted-" + role)) {
    throw new Error("one named launch only; active or consumed role");
  }
  if (index === 0 && previous !== null) throw new Error("prior prefix closes fresh entry");
  if (index > 0 && role !== "shared-closeout" && previous?.pending?.role !== order[index - 1]) {
    throw new Error("exact predecessor required before dispatch");
  }
  if (role === "shared-closeout" && (!previous || previous.pending.role === role)) {
    throw new Error("one real prefix required for closeout");
  }
  if (role !== "independent-public-check" && role !== "shared-closeout"
      && previous?.terminal?.status !== "PASS_R_V2_FULL_ROLE") {
    throw new Error("STOP refuses source suffix before dispatch");
  }
  const deadlines = { exporter: "2026-10-19T07:33:59Z",
    independent: "2026-10-19T06:34:17Z" };
  const caps = { "independent-public-check": 120, "exporter-r0": 120,
    "independent-r0": 120, "exporter-r1": 780,
    "independent-r1": 660, "shared-closeout": 60 };
  if (JSON.stringify(context.actor_deadlines_UTC) !== JSON.stringify(deadlines)
      || context.FULL_caps_seconds[role] !== caps[role]
      || Date.now() + caps[role] * 1000 > Math.min(
        Date.parse(deadlines.exporter), Date.parse(deadlines.independent))) {
    throw new Error("original actor window cannot cover complete named role");
  }
  store("r2-attempted-" + role, true);
  store("r2-active-role", role);
  const events = [];
  const packets = [];
  function quote(word) { return "'" + word.replaceAll("'", "'\\''") + "'"; }
  for (const [index, argv] of context.external_argv[role].entries()) {
    const env = { ...context.thread_environment,
      TOPOLAB_R2_PREVIOUS_TOOL_RECORDS: JSON.stringify(index === 0 && previous ? [previous] : []) };
    const cmd = Object.entries(env).map(([k, v]) => k + "=" + quote(v)).join(" ")
      + " " + argv.map(quote).join(" ");
    const event = {
      event_id: role + (index === 0 ? ":supervise" : ":finalize"),
      clock_domain: "functions.exec.Date.now.UTC-seconds",
      start_seconds: Date.now() / 1000,
      argv, wall_seconds: 0, exit_code: null, complete: false, tool_results: [],
    };
    let output = "";
    try {
      let reply = await tools.exec_command({
        cmd, workdir: context.repository,
        sandbox_permissions: "require_escalated",
        justification: "按所有者已授权的新R/v2冻结计划执行一次" + role
          + "，含已登记计时/RSS/退出；不运行B/C、不重试或扩大输入。",
        yield_time_ms: 1000, max_output_tokens: 12000,
      });
      for (;;) {
        event.tool_results.push(reply);
        output += reply.output;
        event.wall_seconds += reply.wall_time_seconds;
        if (reply.session_id === undefined) break;
        reply = await tools.write_stdin({ session_id: reply.session_id, chars: "",
          yield_time_ms: 1000, max_output_tokens: 12000 });
      }
      event.exit_code = reply.exit_code;
      event.complete = Number.isInteger(reply.exit_code);
      if (output.trim()) packets[index] = JSON.parse(output);
    } catch (error) {
      event.error = String(error.message ?? error);
      event.unparsed_output = output;
    }
    event.end_seconds = Date.now() / 1000;
    events.push(event);
  }
  const last = packets[1] ?? {};
  const pending = last.pending ?? packets[0]?.pending ?? {
    execution_identity: context.execution_identity, role, plan_sha256: context.plan_sha256,
    frozen_FULL_seconds: context.FULL_caps_seconds[role],
    clock_domain: "functions.exec.Date.now.UTC-seconds", clock_resolution_seconds: 0.001,
  };
  const completion = last.completion ?? {
    ...pending, status: "PENDING_EXTERNAL_EXIT", cleanup: { group_gone: null },
    pending_sha256: null,
  };
  const resourceEvidence = last.resourceEvidence ?? {
    status: "STOP_NO_RETRY", reason: "UNKNOWN_MISSING_FINALIZER_EVIDENCE",
  };
  const terminal = finishExternal(pending, completion, events, resourceEvidence,
    packets[0]?.pending_sha256);
  terminal.charge_record_sha256 = packets[0]?.pending_sha256 ?? null;
  const packet = { pending, completion, events, terminal };
  store("r2-last-packet", packet);
  store("r2-packet-" + role, packet);
  store("r2-active-role", null);
  text({ role, status: terminal.status, reason: terminal.reason,
    charged_seconds: terminal.frozen_FULL_seconds,
    whole_wall_seconds: terminal.whole_wall_seconds,
    RSS_envelope_bytes: terminal.RSS_envelope_bytes,
    actual_exit_codes: terminal.actual_exit_codes });
  return packet;
}

if (typeof module !== "undefined") module.exports.dispatchRoleV2 = dispatchRoleV2;
