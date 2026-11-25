// Schedule the single public first role and retain its actual external commands.
export async function firstRole({root, end, python, control}, host, dispatchRoleEvents) {
  const role = "independent-public-check";
  const initial = Date.now();
  const responses = {};
  const prepare = await host.call("prepare", [python, "-I", control, "prepare-public", "--root", root], end);
  await host.retain("prepare", prepare);
  responses.prepare = host.terminal(prepare);
  if (responses.prepare.code !== 0) return responses;
  const plan = JSON.parse(responses.prepare.output);
  if (plan.formal_authority !== false || !/^[0-9a-f]{64}$/.test(plan.plan_sha256)) {
    throw new Error("public preparation scope or digest differs");
  }
  if (Date.now() - initial > 30000) throw new Error("public preparation to first SUP exceeded 30 seconds");
  const roleEnd = Math.min(end, Date.now() + 290000);
  const tail = ["--root", root, "--plan-sha", plan.plan_sha256, "--role", role];
  async function dispatch(mode) {
    const packet = await host.call(mode, [python, "-I", control, mode, ...tail], roleEnd);
    return {packet};
  }

  async function retain(mode, actual) {
    await host.retain(mode, actual.packet);
    Object.assign(actual, host.terminal(actual.packet));
    responses[mode] = {code: actual.code, output: actual.output};
  }

  // Use the same scheduler as the released actors. Only the public transport,
  // temporary destinations and event-file names differ.
  await dispatchRoleEvents({
    dispatch,
    retain,
    accept: actual => actual.code === 0 && Date.now() <= roleEnd,
    async file(mode) {
      const name = "file-" + mode;
      const actual = await dispatch(name);
      await retain(name, actual);
      if (actual.code !== 0 || Date.now() > roleEnd) throw new Error("public filing failed: " + name);
    },
    async bind() {
      const actual = await dispatch("bind");
      await retain("bind", actual);
      return actual;
    }
  });
  return responses;
}
