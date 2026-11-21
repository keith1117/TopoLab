import assert from "node:assert/strict";
import {test} from "node:test";
import {callBinding} from "../scripts/staged_binding_caller.mjs";

test("the registration caller retains a live response and stops within its own role clock", async () => {
  let time = Date.parse("2026-11-21T23:00:00Z"), polls = 0;
  const original = Date.now;
  Date.now = () => time;
  try {
    const run = await callBinding({
      async exec_command(args) {
        if (!args.cmd.includes("supervise independent-availability"))
          return {exit_code:0, output:"test receipt"};
        if (args.cmd.startsWith("exec env ")) {
          time += args.yield_time_ms;
          return {session_id:7, output:""};
        }
        return {exit_code:0, output:"test receipt"};
      },
      async write_stdin(args) {
        polls++;
        assert.equal(args.session_id,7);
        time += args.yield_time_ms;
        return {session_id:7, output:""};
      },
    },"independent-availability","/root/full60_independent");
    assert.equal(run.accepted,false);
    assert.equal(polls,4);
    assert.equal(run.packet.responses.at(-1).returned_ms-run.start,140000);
    assert.match(run.failure,/bounded caller stop/);
  } finally { Date.now = original; }
});

test("a changed session cannot become the next poll target", async (t) => {
  t.mock.method(Date, "now", () => Date.parse("2026-11-21T23:00:00Z"));
  let polls = 0;
  const run = await callBinding({
    async exec_command(args) {
      return args.cmd.startsWith("exec env ") && args.cmd.includes("supervise binding-independent")
        ? {session_id:3,output:""} : {exit_code:0,output:"test receipt"};
    },
    async write_stdin() { polls++; return {session_id:4,output:""}; },
  },"binding-independent","/root/full60_independent");
  assert.equal(run.accepted,false);
  assert.equal(run.failure,"poll session changed");
  assert.equal(polls,1);
});
