// Run by the named actor at its actual tool boundary. The input is one fixed role.
export async function callBinding(tools, role, author) {
  const repo = "/private/tmp/topolab-staged-input-20261121";
  const evidence = "/Users/keith1117/Documents/TopoLab-data/staged-input-acceptance-20261121/binding";
  const python = repo + "/.venv/bin/python";
  const entry = repo + "/scripts/staged_public_binding.py";
  const actors = {
    preflight: "/root/full60_independent",
    prepare: "/root",
    "producer-availability": "/root",
    "independent-availability": "/root/full60_independent",
    "binding-producer": "/root",
    "binding-independent": "/root/full60_independent",
    "binding-closeout": "/root",
    "binding-certificate-auditor": "/root/full60_independent",
    finalize: "/root",
  };
  if (actors[role] !== author) throw Error("unregistered command or actor");
  const quote = (s) => "'" + s.replaceAll("'", "'\"'\"'") + "'";
  const environment = ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"].map(k => k + "=1");
  const named = !["preflight", "prepare", "finalize"].includes(role);
  if (named) {
    const reserve = await tools.exec_command({cmd:"exec env " + [...environment, python,
      "-I", entry, "reserve", role].join(" "), workdir:repo, login:false, yield_time_ms:30000,
      max_output_tokens:1000});
    if (reserve.exit_code !== 0 || reserve.session_id != null)
      return {accepted:false, role, stage:"reservation", result:reserve};
  }
  const start = Date.now();
  let argv = [python, "-I", entry, role];
  if (role === "prepare") argv.push(String(start));
  if (named) argv = ["/usr/bin/time", "-l", "-o", evidence + "/" + role + ".outer.time",
    python, "-I", entry, "supervise", role, String(start)];
  // All registered literals match shlex.join without shell quoting.
  if (![...environment, ...argv].every(s => /^[a-zA-Z0-9_./=-]+$/.test(s))) {
    throw Error("non-literal staged argv");
  }
  const request = {cmd:"exec env " + [...environment, ...argv].join(" "), workdir:repo,
    login:false, yield_time_ms:30000, max_output_tokens:5000};
  if (named || role === "preflight") {
    request.sandbox_permissions = "require_escalated";
    request.justification = named
      ? "允许这次已登记的公开角色对固定公开夹具执行核验，并使用宿主进程采样器保留实际退出和内存证据吗？"
      : "允许独立预检只读核对 GitHub 受保护主分支、CI 和既有正式元数据回执吗？";
  }
  const packet = {schema:"topolab.staged-binding.actual.v1", author, argv, request, responses:[]};
  const file = async (suffix, data) => {
    const script = "import sys;sys.path.insert(0," + JSON.stringify(repo + "/scripts") +
      ");import runpy;runpy.run_path(" + JSON.stringify(repo + "/scripts/full60_input_loader.py") +
      ")[\"install\"]();from staged_binding_evidence import write_pair;" +
      "import json;print(write_pair(sys.argv[1],json.loads(sys.argv[2])))";
    const cmd = [python, "-I", "-c", script, "binding/" + role + "-" + suffix + ".json",
      JSON.stringify(data)].map(quote).join(" ");
    const receipt = await tools.exec_command({cmd,workdir:repo,login:false,
      yield_time_ms:30000,max_output_tokens:300});
    if (receipt.exit_code !== 0) throw Error("actual return filing failed: " + receipt.output);
  };
  const caps = {preflight:300, prepare:120, finalize:180, "producer-availability":150,
    "independent-availability":150, "binding-producer":300, "binding-independent":300,
    "binding-closeout":180, "binding-certificate-auditor":120};
  const deadline = Math.min(start + (caps[role] - (named ? 10 : 0)) * 1000, Date.parse("2026-11-22T12:40:00Z"));
  let tool = "exec_command", arguments_ = request, requested = start, failure = null;
  let session = null;
  const secondary = [];
  const filingError = (error) => {
    if (failure === null) failure = String(error);
    else secondary.push(String(error));
  };
  try {
    for (let i = 0; i < 12; i++) {
      const result = await tools[tool](arguments_);
      const row = {tool, arguments:arguments_, requested_ms:requested, returned_ms:Date.now(), result};
      packet.responses.push(row);
      if (row.returned_ms > deadline || row.returned_ms < requested) failure = "role return clock";
      else if (typeof result.output !== "string" || result.output.includes("tokens truncated")
        || result.output.includes("Warning: truncated output")
        || (result.original_token_count ?? 0) > arguments_.max_output_tokens) failure = "incomplete output";
      else if (session != null && result.session_id != null && result.session_id !== session)
        failure = "poll session changed";
      else if (result.exit_code != null && (result.exit_code !== 0 || result.session_id != null))
        failure = "unsuccessful terminal return";
      try { await file("response-" + String(i), row); }
      catch (error) { filingError(error); }
      if (failure || secondary.length || result.exit_code != null) break;
      requested = Date.now();
      const left = deadline - requested;
      if (!Number.isInteger(result.session_id) || left < 5000 || i === 11) {
        failure = "live or incomplete return at bounded caller stop"; break;
      }
      session ??= result.session_id;
      tool = "write_stdin";
      arguments_ = {session_id:session, chars:"", yield_time_ms:Math.min(30000,left),
        max_output_tokens:5000};
    }
  } catch (error) { failure = failure || String(error); }
  const last = packet.responses.at(-1);
  if (!last || last.result.exit_code !== 0 || last.result.session_id != null)
    failure = failure || "successful terminal missing";
  try { await file("actual", packet); } catch (error) { filingError(error); }
  if (failure || secondary.length) {
    const stop = {role, start, failure, secondary, packet};
    try { await file("STOP", stop); } catch (error) { filingError(error); }
    return {accepted:false, ...stop};
  }
  return {accepted:true, role, start, returned:last.returned_ms, result:last.result};
}
