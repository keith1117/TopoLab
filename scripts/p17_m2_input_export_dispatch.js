/* Independently authored finite external-tool boundary for NEW R/v3.
 * No filesystem, native helper, numerical oracle or producer PASS is used here.
 * Root may append orchestration after the independent initial-source snapshot.
 */

const R_STABLE_IDENTITY = "topolab.v2.p17-m2-source-stable-export.v1";
const R_STABLE_CAPS = { "independent-public-check": 300, "exporter-r0": 300,
  "independent-r0": 300, "exporter-r1": 1200, "independent-r1": 1200,
  "shared-closeout": 300 };

function validateStableCleanup(cleanup) {
  const rows = cleanup?.observations;
  if (cleanup?.group_gone !== true || cleanup.final_group_gone !== true
      || typeof cleanup.initial_group_gone !== "boolean"
      || !Number.isInteger(cleanup.leader_exit)
      || cleanup.observation_limit_seconds !== 5 || cleanup.observation_limit_exceeded !== false
      || typeof cleanup.post_signal_observation_seconds !== "number"
      || !Number.isFinite(cleanup.post_signal_observation_seconds)
      || cleanup.post_signal_observation_seconds < 0 || cleanup.post_signal_observation_seconds > 5
      || !Array.isArray(cleanup.signals) || !cleanup.signals.every((s) => typeof s === "string")
      || !Array.isArray(rows) || rows.length === 0 || rows.length > 4096) {
    throw new Error("UNKNOWN_INCOMPLETE_STABLE_CLEANUP");
  }
  let last = 0;
  for (const row of rows) {
    if (typeof row?.group_gone !== "boolean" || typeof row.elapsed_seconds !== "number"
        || !Number.isFinite(row.elapsed_seconds) || row.elapsed_seconds < last) {
      throw new Error("UNKNOWN_STABLE_CLEANUP_OBSERVATION");
    }
    last = row.elapsed_seconds;
  }
  if (rows[0].group_gone !== cleanup.initial_group_gone
      || rows.at(-1).group_gone !== true || rows.at(-1).leader_exit !== cleanup.leader_exit) {
    throw new Error("stable cleanup initial/final facts differ");
  }
}

function finishExternal(pending, completion, events, resourceEvidence, expectedPendingSha256,
  failureRecording = false, executionIdentity = null) {
  const stable = executionIdentity === R_STABLE_IDENTITY;
  const recording = failureRecording || stable;
  const object = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
  const pendingIsObject = object(pending), completionIsObject = object(completion);
  pending = pendingIsObject ? pending : {};
  completion = completionIsObject ? completion : {};
  const eventsAreList = Array.isArray(events);
  events = eventsAreList ? events : [];
  const identity = stable ? R_STABLE_IDENTITY : failureRecording
    ? "topolab.v2.p17-m2-input-failure-diagnostic-repair.v1"
    : "topolab.v2.p17-m2-input-export-preparation.v3";
  const caps = stable ? R_STABLE_CAPS : failureRecording ? { "public-fixture": 120 } : {
    "independent-public-check": 120,
    "exporter-r0": 120,
    "independent-r0": 120,
    "exporter-r1": 780,
    "independent-r1": 660,
    "shared-closeout": 60,
  };
  const cap = caps[pending.role];
  const result = {
    schema: stable ? "topolab.v2.m2-source-stable-export-exit.v1"
      : failureRecording ? "topolab.v2.m2-input-failure-exit.v1"
      : "topolab.v2.m2-input-export-exit.v2",
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
    actual_exit_codes: events.map((event) => object(event) ? event.exit_code ?? null : null),
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
    evidence_complete: false,
    domain_status: "STOP",
    primary_failure: completion.primary_failure ?? null,
    secondary_failures: completion.secondary_failures ?? [],
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
    require(pendingIsObject, "pending must be an object");
    require(Number.isInteger(cap) && /^[0-9a-f]{64}$/.test(pending.plan_sha256),
      "unregistered role/plan");
    for (const record of [pending]) {
      require(record.execution_identity === identity && record.role === pending.role
        && record.plan_sha256 === pending.plan_sha256 && record.frozen_FULL_seconds === cap,
      "v3 identity/plan/immutable FULL differs");
      require(record.clock_domain === "functions.exec.Date.now.UTC-seconds"
        && record.clock_resolution_seconds === 0.001,
      "unfrozen external clock identity/resolution");
    }
    require(eventsAreList && events.length > 0 && events.every(object),
      "UNKNOWN_MISSING_OR_MALFORMED_ACTUAL_OUTER_EVENT");
    const actor = validateActorWindow(pending);
    result.actor_activation_UTC_seconds = actor.activation;
    result.actor_window_seconds = stable ? 4500 : 2700;
    result.actor_deadlines_UTC = pending.actor_deadlines_UTC;
    result.clock_domain = events[0].clock_domain;
    result.T0 = number(events[0].start_seconds);
    result.T1 = number(events.at(-1).end_seconds);
    const whole = result.T1 - result.T0;
    require(whole >= 0, "outer clock regression");
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
      previousEnd = end;
    }
    if (pending.external_argv !== undefined) {
      require(JSON.stringify(pending.external_argv) === JSON.stringify(events.map((e) => e.argv)),
        "external literal argv differs");
    }
    // A valid raw interval remains a cost fact even when the actor window rejects it.
    result.whole_wall_seconds = whole;
    result.known_cost_lower_bound_seconds = Math.max(cap, Math.ceil(whole + 10));
    if (typeof result.inner_minimum_charge_seconds === "number"
        && Number.isFinite(result.inner_minimum_charge_seconds)
        && result.inner_minimum_charge_seconds >= 0) {
      result.known_cost_lower_bound_seconds = Math.max(result.known_cost_lower_bound_seconds,
        Math.ceil(result.inner_minimum_charge_seconds));
    }
    require(actor.activation <= result.T0 && result.T0 <= result.T1
      && result.T1 <= actor.deadline,
    "actual full role lies outside immutable actor window");
    require(events.every((event) => event.complete === true && Number.isInteger(event.exit_code)),
      "UNKNOWN_MISSING_ACTUAL_FINAL_EXIT");
    require(completionIsObject, "completion must be an object");
    const completedActor = validateActorWindow(completion);
    require(JSON.stringify(completedActor) === JSON.stringify(actor),
      "completion actor window differs");
    for (const key of ["execution_identity", "role", "plan_sha256", "frozen_FULL_seconds",
      "clock_domain", "clock_resolution_seconds"]) {
      require(completion[key] === pending[key], "completion identity differs");
    }
    require(completion.status === "PENDING_EXTERNAL_EXIT"
      && /^[0-9a-f]{64}$/.test(expectedPendingSha256)
      && completion.pending_sha256 === expectedPendingSha256,
    "internal terminal cannot certify future exit");
    // The Python independent checker runs INSIDE the measured finalizer. It
    // reconciles raw profile bytes and inner receipt details, never producer PASS.
    require(resourceEvidence?.status === "PENDING_EXTERNAL_EXIT"
      && resourceEvidence.full_role_evidence_accepted === false,
    resourceEvidence?.reason ?? "UNKNOWN_MISSING_INDEPENDENT_RESOURCE_EVIDENCE");
    if (recording) {
      require(resourceEvidence.evidence_complete === true
        && Number.isInteger(resourceEvidence.inner_actual_exit_code)
        && Array.isArray(resourceEvidence.actual_component_exit_codes),
      "UNKNOWN_INCOMPLETE_INDEPENDENT_RESOURCE_EVIDENCE");
    }
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
    require(completion.cleanup?.group_gone === true,
      "UNKNOWN_INCOMPLETE_GROUP_CLEANUP");
    if (stable) validateStableCleanup(completion.cleanup);
    require(Math.max(whole + 10, minimum) <= cap,
      "FAIL_FULL_NAMED_WALL_CHARGE_BINDING");
    result.evidence_complete = true;
    result.missing_evidence_cost = null;
    require(result.actual_exit_codes.every((exit) => exit === 0),
      "actual final serializer/outer exit nonzero");
    if (recording) {
      require(resourceEvidence.evidence_complete === true
        && resourceEvidence.inner_actual_exit_code === 0
        && (resourceEvidence.actual_component_exit_codes ?? []).every((code) => code === 0)
        && (stable ? completion.domain_status === "PASS" : completion.domain_status !== "STOP"),
      "payload/domain failure");
    }
    result.status = stable ? "PASS_R_STABLE_FULL_ROLE"
      : failureRecording ? "PASS_PUBLIC_SOFTWARE" : "PASS_R_V3_FULL_ROLE";
    result.domain_status = stable ? "PASS" : "PASS_PUBLIC_SOFTWARE";
    result.reason = null;
    result.missing_evidence_cost = null;
    result.full_role_evidence_accepted = true;
  } catch (error) {
    result.reason = String(error.message ?? error);
  }
  return result;
}

function finishExternalF(pending, completion, events, resourceEvidence, expectedPendingSha256) {
  return finishExternal(pending, completion, events, resourceEvidence, expectedPendingSha256, true);
}

function finishExternalStable(pending, completion, events, resourceEvidence, expectedPendingSha256) {
  return finishExternal(pending, completion, events, resourceEvidence, expectedPendingSha256,
    true, R_STABLE_IDENTITY);
}

if (typeof module !== "undefined") module.exports = {
  finishExternal, finishExternalF, finishExternalStable,
};

function validateActorWindow(context) {
  const windowSeconds = context.execution_identity === R_STABLE_IDENTITY ? 4500 : 2700;
  const activation = context.actor_activation_UTC_seconds;
  const activationMillis = Math.round(activation * 1000);
  if (typeof activation !== "number" || !Number.isFinite(activation) || activation <= 0
      || !Number.isSafeInteger(activationMillis) || activationMillis / 1000 !== activation
      || context.actor_window_seconds !== windowSeconds) {
    throw new Error("prospective actor activation/window differs");
  }
  const deadline = activation + windowSeconds;
  const expected = new Date(activationMillis + windowSeconds * 1000).toISOString();
  const deadlines = context.actor_deadlines_UTC;
  if (!deadlines || Object.keys(deadlines).sort().join(",") !== "exporter,independent"
      || deadlines.exporter !== expected || deadlines.independent !== expected) {
    throw new Error("actor deadlines must equal immutable activation plus2700");
  }
  return { activation, deadline };
}

/* Versioned orchestration in the SAME trusted external-tool invocation.
 * Context is the frozen launch plan; dynamic telemetry is previous actual tool
 * OUTPUT, not a new source identity. No native process runs after final event.
 */
async function dispatchRoleV3(context, role, stable = false) {
  const identity = stable ? R_STABLE_IDENTITY : "topolab.v2.p17-m2-input-export-preparation.v3";
  const prefix = stable ? "rstable" : "r3";
  if (context.execution_identity !== identity
      || !Object.hasOwn(context.external_argv, role)) throw new Error("unregistered R/v3");
  const binding = JSON.stringify({
    plan_sha256: context.plan_sha256,
    actor_activation_UTC_seconds: context.actor_activation_UTC_seconds,
    actor_window_seconds: context.actor_window_seconds,
    actor_deadlines_UTC: context.actor_deadlines_UTC,
  });
  const frozen = load(prefix + "-activation");
  if (frozen !== undefined && frozen !== binding) {
    throw new Error("one immutable activation/plan only; no reactivation");
  }
  if (frozen === undefined) store(prefix + "-activation", binding);
  const actor = validateActorWindow(context);
  const previous = load(prefix + "-last-packet") ?? null;
  const order = ["independent-public-check", "exporter-r0", "independent-r0",
    "exporter-r1", "independent-r1", "shared-closeout"];
  const index = order.indexOf(role);
  if (index < 0) throw new Error("unregistered R/v3 role");
  if (load(prefix + "-active-role") || load(prefix + "-attempted-" + role)) {
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
      && previous?.terminal?.status !== (stable ? "PASS_R_STABLE_FULL_ROLE" : "PASS_R_V3_FULL_ROLE")) {
    throw new Error("STOP refuses source suffix before dispatch");
  }
  if (stable && role === "shared-closeout"
      && previous?.terminal?.cleanup?.group_gone !== true) {
    throw new Error("unconfirmed cleanup refuses closeout process");
  }
  const caps = stable ? R_STABLE_CAPS : { "independent-public-check": 120, "exporter-r0": 120,
    "independent-r0": 120, "exporter-r1": 780,
    "independent-r1": 660, "shared-closeout": 60 };
  const now = Date.now() / 1000;
  const remainingFull = stable ? order.slice(index).reduce((n, name) => n + caps[name], 0)
    + 240 + 360 : index === 0 ? 1860 : caps[role];
  if (!/^[0-9a-f]{64}$/.test(context.plan_sha256)
      || context.FULL_caps_seconds[role] !== caps[role]
      || now < actor.activation || now + remainingFull > actor.deadline) {
    throw new Error("immutable actor window cannot cover complete registered work");
  }
  if (!stable) {
    store(prefix + "-attempted-" + role, true);
    store(prefix + "-active-role", role);
  }
  const events = [];
  const packets = [];
  function quote(word) { return "'" + word.replaceAll("'", "'\\''") + "'"; }
  for (const [index, argv] of context.external_argv[role].entries()) {
    const env = { ...context.thread_environment,
      [stable ? "TOPOLAB_RSTABLE_PREVIOUS_TOOL_RECORDS" : "TOPOLAB_R3_PREVIOUS_TOOL_RECORDS"]:
        JSON.stringify(index === 0 && previous ? [previous] : []) };
    const cmd = Object.entries(env).map(([k, v]) => k + "=" + quote(v)).join(" ")
      + " " + argv.map(quote).join(" ");
    const event = {
      event_id: role + (index === 0 ? ":supervise" : ":finalize"),
      clock_domain: "functions.exec.Date.now.UTC-seconds",
      start_seconds: Date.now() / 1000,
      argv, wall_seconds: 0, exit_code: null, complete: false, tool_results: [],
    };
    if (stable && index === 0) {
      const first = event.start_seconds;
      const ledger = load("rstable-ledger") ?? { FULL_booked_seconds: 300,
        setup_seconds: first - actor.activation, between_roles_seconds: 0,
        shared_closeout_booked_on_first_dispatch: true, roles: [] };
      if (previous) ledger.between_roles_seconds += first - previous.events.at(-1).end_seconds;
      if (role !== "shared-closeout") ledger.FULL_booked_seconds += caps[role];
      if (first < actor.activation || first + remainingFull > actor.deadline
          || ledger.setup_seconds < 0 || ledger.setup_seconds > 300
          || ledger.between_roles_seconds < 0 || ledger.between_roles_seconds > 240
          || ledger.FULL_booked_seconds + ledger.setup_seconds
            + ledger.between_roles_seconds + 360 > 4500) {
        throw new Error("actual first event cannot cover FULL/setup/coordination/reserve");
      }
      ledger.roles.push({role, frozen_FULL_seconds: caps[role], dispatch_UTC_seconds: first});
      store("rstable-ledger", ledger);
      store(prefix + "-attempted-" + role, true);
      store(prefix + "-active-role", role);
    }
    let output = "";
    try {
      let reply = await tools.exec_command({
        cmd, workdir: context.repository,
        sandbox_permissions: "require_escalated",
        justification: "按所有者已授权的" + (stable ? "R-STABLE" : "R/v3") + "冻结计划执行一次" + role
          + "，含已登记计时/RSS/退出；不运行B/C、不重试或扩大输入。",
        yield_time_ms: 1000, max_output_tokens: stable ? 32768 : 12000,
      });
      for (;;) {
        event.tool_results.push(reply);
        output += reply.output;
        event.wall_seconds += reply.wall_time_seconds;
        if (reply.session_id === undefined) break;
        reply = await tools.write_stdin({ session_id: reply.session_id, chars: "",
          yield_time_ms: 1000, max_output_tokens: stable ? 32768 : 12000 });
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
    actor_activation_UTC_seconds: context.actor_activation_UTC_seconds,
    actor_window_seconds: context.actor_window_seconds,
    actor_deadlines_UTC: context.actor_deadlines_UTC,
  };
  const completion = last.completion ?? {
    ...pending, status: "PENDING_EXTERNAL_EXIT", cleanup: { group_gone: null },
    pending_sha256: null,
  };
  const resourceEvidence = last.resourceEvidence ?? {
    status: "STOP_NO_RETRY", reason: "UNKNOWN_MISSING_FINALIZER_EVIDENCE",
  };
  const terminal = (stable ? finishExternalStable : finishExternal)(
    pending, completion, events, resourceEvidence, packets[0]?.pending_sha256);
  terminal.charge_record_sha256 = packets[0]?.pending_sha256 ?? null;
  const packet = { pending, completion, events, terminal };
  if (stable && last.full_collector_record) packet.full_collector_record = last.full_collector_record;
  if (stable && role === "shared-closeout") {
    const closed = Date.now() / 1000;
    try {
      if (closed > actor.deadline || closed - events.at(-1).end_seconds > 360) {
        throw new Error("final frontier retention/release exceeds reserve");
      }
      const ledger = load("rstable-ledger");
      ledger.final_frontier_seconds = closed - events.at(-1).end_seconds;
      if (ledger.FULL_booked_seconds + ledger.setup_seconds + ledger.between_roles_seconds
          + ledger.final_frontier_seconds > 4500) {
        throw new Error("actual formal close exceeds disjoint FULL ledger");
      }
      packet.formal_close_UTC_seconds = closed;
      packet.custodian_release = { by: context.source_controls.custodian,
        UTC_seconds: closed, plan_sha256: context.plan_sha256, source_roles_closed: true };
      ledger.formal_closed_UTC_seconds = closed;
      store("rstable-ledger", ledger);
      store("rstable-formal-close", closed);
    } catch (error) {
      const reason = String(error.message ?? error);
      terminal.status = "STOP_NO_RETRY";
      terminal.reason ??= reason;
      terminal.domain_status = "STOP";
      terminal.full_role_evidence_accepted = false;
      terminal.secondary_failures = [
        ...(Array.isArray(terminal.secondary_failures) ? terminal.secondary_failures : []),
        { stage: "shared-closeout-frontier", reason, observed_UTC_seconds: closed,
          final_frontier_seconds: closed - events.at(-1).end_seconds },
      ];
    }
  }
  store(prefix + "-last-packet", packet);
  store(prefix + "-packet-" + role, packet);
  store(prefix + "-active-role", null);
  text({ role, status: terminal.status, reason: terminal.reason,
    charged_seconds: terminal.frozen_FULL_seconds,
    whole_wall_seconds: terminal.whole_wall_seconds,
    RSS_envelope_bytes: terminal.RSS_envelope_bytes,
    actual_exit_codes: terminal.actual_exit_codes });
  return packet;
}

async function dispatchRoleStable(context, role) {
  return dispatchRoleV3(context, role, true);
}

async function dispatchFinalFilingStable(context) {
  const previous = load("rstable-last-packet");
  const closed = load("rstable-formal-close");
  const argv = context.final_helper_external_argv.map((word) =>
    word === "<PLAN_SHA256>" ? context.plan_sha256 : word);
  const expected = [context.python_executable, "-I",
    context.repository + "/scripts/p17_m2_input_export_control.py", "final-helper", "--r-stable",
    "--plan", context.output_root + "/launch_plan.json", "--plan-sha", context.plan_sha256];
  const now = Date.now() / 1000;
  if (context.execution_identity !== R_STABLE_IDENTITY
      || load("rstable-final-filing-attempted") || load("rstable-active-role")
      || previous?.pending?.role !== "shared-closeout"
      || previous.terminal.status !== "PASS_R_STABLE_FULL_ROLE"
      || previous.terminal.cleanup?.group_gone !== true
      || !Number.isFinite(closed) || closed !== previous.formal_close_UTC_seconds
      || now < closed || now + 180 > closed + 7200
      || JSON.stringify(argv) !== JSON.stringify(expected)) {
    throw new Error("one frozen NEW-only result filing after actual shared return");
  }
  store("rstable-final-filing-attempted", true);
  const quote = (word) => "'" + word.replaceAll("'", "'\\''") + "'";
  const env = { ...context.thread_environment,
    TOPOLAB_RSTABLE_PREVIOUS_TOOL_RECORDS: JSON.stringify([previous]) };
  const cmd = Object.entries(env).map(([k, v]) => k + "=" + quote(v)).join(" ")
    + " " + argv.map(quote).join(" ");
  const event = { argv, start_seconds: Date.now() / 1000, tool_results: [],
    clock_domain: "functions.exec.Date.now.UTC-seconds", exit_code: null, complete: false };
  let output = "", record = null;
  try {
    let reply = await tools.exec_command({cmd, workdir: context.repository,
      sandbox_permissions: "require_escalated",
      justification: "按已批准R-STABLE合同一次归档NEW最终返回及独立备份；180秒结果辅助，不访问旧源。",
      yield_time_ms: 1000, max_output_tokens: 12000});
    for (;;) {
      event.tool_results.push(reply);
      output += reply.output;
      if (reply.session_id === undefined) break;
      reply = await tools.write_stdin({session_id: reply.session_id, chars: "",
        yield_time_ms: 1000, max_output_tokens: 12000});
    }
    event.exit_code = reply.exit_code;
    event.complete = Number.isInteger(reply.exit_code);
    record = JSON.parse(output);
  } catch (error) {
    event.error = String(error.message ?? error);
    event.unparsed_output = output;
  }
  event.end_seconds = Date.now() / 1000;
  const result = { event, record, whole_wall_seconds: event.end_seconds - event.start_seconds,
    status: "PENDING_INDEPENDENT_FINAL_AUDIT", preparation_complete: false, B_C_admission: false };
  store("rstable-final-filing-actual-return", result);
  text({ status: result.status, actual_exit: event.exit_code,
    whole_wall_seconds: result.whole_wall_seconds });
  return result;
}

if (typeof module !== "undefined") {
  module.exports.dispatchRoleV3 = dispatchRoleV3;
  module.exports.dispatchRoleStable = dispatchRoleStable;
  module.exports.validateActorWindow = validateActorWindow;
  module.exports.dispatchFinalFilingStable = dispatchFinalFilingStable;
}
