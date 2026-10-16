/* Independently authored I1 native role controller. Public software only.
 * The author reviewed the primary draft earlier; no implementation is reused.
 * Shared bounded syscall/hash/sealing interfaces are explicitly reviewed. */
#include "runtime.h"
#include "hashes.h"

static struct { int executable[2]; unsigned long launches; } control;

static _Noreturn void child_exit(int code) {
    rt_call(60, code, 0, 0, 0, 0, 0);
    for (;;) { } /* Linux exit cannot return. No fallback interpreter. */
}
static void close_images(void) {
    for (int r = 0; r != 2; ++r) if (control.executable[r] >= 0) {
        rt_call(3, control.executable[r], 0, 0, 0, 0, 0);
        control.executable[r] = -1;
    }
}
static int run_child(int image, const char *const *arguments, int output) {
    if (control.launches >= 2) return 71;
    ++control.launches;
    long pid = rt_call(57, 0, 0, 0, 0, 0, 0);
    if (pid < 0) return 71;
    if (pid == 0) {
        if (output >= 0 && rt_call(33, output, 1, 0, 0, 0, 0) != 1) child_exit(71);
        const char *empty_environment[1] = {0};
        rt_call(322, image, (long)"", (long)arguments, (long)empty_environment, 4096, 0);
        child_exit(71);
    }
    for (int observation = 0; observation != 2; ++observation) {
        int status = 0;
        if (rt_call(61, pid, (long)&status, 0, 0, 0, 0) == pid) {
            rt_text("CHILD_RAW_WAIT_STATUS="); rt_uint((unsigned long)status); rt_text("\n");
            return status == 0 ? 0 : 71;
        }
        if (observation == 0) rt_call(62, pid, 9, 0, 0, 0, 0);
    }
    rt_text("CHILD_EXIT=UNKNOWN_NOT_OBSERVED\n");
    return 71;
}

int i1_main(unsigned long *stack) {
    int ci = stack[0] == 5 && rt_equal((const char *)stack[2], "--ci-public-preflight");
    if (ci && rt_ci_environment(stack)) return 64;
    int startup = (ci && !rt_arguments(stack, 5)) ||
        (stack[0] == 4 && !rt_arguments(stack, 4) && rt_equal((const char *)stack[2], "--public-preflight"));
    int query = stack[0] == 8 && !rt_arguments(stack, 8) && rt_equal((const char *)stack[2], "--public-run");
    int evaluation = stack[0] == 9 && !rt_arguments(stack, 9) && rt_equal((const char *)stack[2], "--public-evaluate");
    if (!startup && !query && !evaluation) return 64;
    control.executable[0] = -1; control.executable[1] = -1;
    if (rt_prepare() || rt_policy(1) || rt_preflight(sizeof(control), stack)) return 77;
    control.executable[0] = rt_sealed_child((const char *)stack[3], query_hash);
    if (control.executable[0] < 0) return 65;
    control.executable[1] = rt_sealed_child((const char *)stack[4], audit_hash);
    if (control.executable[1] < 0) { close_images(); return 65; }
    int result = 0;
    if (startup) {
        for (int role = 0; role != 2 && !result; ++role) {
            const char *arguments[3] = {(const char *)stack[3 + role], "--preflight", 0};
            result = run_child(control.executable[role], arguments, -1);
        }
    } else {
        const char *output_path = (const char *)stack[evaluation ? 9 : 8];
        long output = rt_call(257, -100, (long)output_path, 0400301, 0600, 0, 0);
        if (output < 0) result = 73;
        else {
            const char *producer[6] = {(const char *)stack[3], evaluation ? "--public-evaluate" : "--public-case",
                (const char *)stack[5], (const char *)stack[6], evaluation ? (const char *)stack[8] : 0, 0};
            result = run_child(control.executable[0], producer, (int)output);
            rt_call(3, output, 0, 0, 0, 0, 0);
            if (result) rt_text("PUBLIC_PRODUCER_FAILED_PREFIX_RETAINED\n");
            else {
                const char *checker[6] = {(const char *)stack[4], evaluation ? "--public-evaluation" : "--public-terminal",
                    (const char *)stack[7], output_path, evaluation ? (const char *)stack[8] : 0, 0};
                result = run_child(control.executable[1], checker, -1);
            }
        }
    }
    close_images();
    if (result) return result;
    rt_text("INDEPENDENT_RESOURCE_ADMISSION=UNKNOWN\nPILOT=DENIED\n");
    return 0;
}
