/* Independent-reviewer I1 public terminal/evaluation checker. Prior primary-draft
 * exposure is disclosed in the review; this is newly authored, not blinded.
 * Wire declarations implement the frozen interface, never candidate helpers. */
#include "audit.h"
#include "runtime.h"

typedef struct {
    int count[8]; /* updates, analyses, convergence, phase, selected, polish, initial, rechecks */
    int penalty[361];
    double compliance[361], volume[361], design_change[361], physical_change[361];
    double design[361][1728], physical[361][1728];
} HistoryWire;
typedef struct {
    unsigned char magic[8];
    HistoryWire state;
    double displacement[6825], reaction[6825];
} TerminalWire;
typedef struct {
    unsigned char magic[8];
    int outcome[4]; /* success, fallback, retained attempt status, evaluation return */
    HistoryWire attempt;
    TerminalWire terminal;
} EvaluationWire;
static union { TerminalWire plain; EvaluationWire evaluation; } input;
static AuditCase physical_case;

_Static_assert(sizeof(HistoryWire) == 9993960, "I1 history ABI");
_Static_assert(sizeof(TerminalWire) == 10103168, "I1 terminal ABI");
_Static_assert(sizeof(EvaluationWire) == 20097152, "I1 evaluation ABI");

static int finite_scalar(double x) {
    union { double value; unsigned long long bits; } number = {.value = x};
    return ((number.bits >> 52) & 2047) != 2047;
}
static double absolute_value(double x) { return x >= 0 ? x : -x; }
static int magic_is(const unsigned char *actual, const char *expected) {
    for (int i = 0; i != 8; ++i) if (actual[i] != (unsigned char)expected[i]) return 0;
    return 1;
}

/* Every published state is checked for finite fields, actual volume and changes.
 * Numerical solves are confined to the terminal certification windows below. */
static int history_shape(const HistoryWire *h, int complete) {
    int end = h->count[0], ne = physical_case.nx * physical_case.ny * physical_case.nz;
    if (end < (complete ? 1 : 0) || end > 360 || h->count[1] < 0 || h->count[1] > 364 ||
        h->count[2] < 0 || h->count[2] > 1 || h->count[3] < 0 || h->count[3] > 360 ||
        h->count[4] < 0 || h->count[4] > end || h->count[5] < 0 || h->count[5] > 20 ||
        h->count[6] < 0 || h->count[6] > 1 ||
        (h->count[7] != 0 && h->count[7] != 2)) return 1;
    if (!complete) return 0; /* a failed prefix never supplies a terminal certificate */
    int homotopy = h->penalty[0] == 1;
    if ((!homotopy && h->penalty[0] != 3) || h->penalty[end] != 3) return 1;
    if (homotopy && (physical_case.nx != 24 || physical_case.ny != 12 ||
        physical_case.nz != 6 || physical_case.direction != 1 || physical_case.volume >= 0.55 ||
        h->count[5] != 0 || h->count[7] != 0 || h->count[4] != end)) return 1;
    int transitions = 0;
    for (int j = 0; j <= end; ++j) {
        int expected = homotopy ? (j < 9 ? 1 : j < 17 ? 2 : 3) : 3;
        if (h->penalty[j] != expected || !finite_scalar(h->compliance[j]) || h->compliance[j] <= 0 ||
            !finite_scalar(h->volume[j]) || !finite_scalar(h->design_change[j]) ||
            !finite_scalar(h->physical_change[j]) || h->design_change[j] < 0 || h->physical_change[j] < 0) return 1;
        if (j && h->penalty[j] != h->penalty[j - 1]) ++transitions;
        double volume = 0, dx = 0, drho = 0;
        for (int e = 0; e != ne; ++e) {
            double x = h->design[j][e], rho = h->physical[j][e];
            if (!finite_scalar(x) || !finite_scalar(rho) || x < physical_case.minimum || x > 1 ||
                rho < physical_case.minimum || rho > 1) return 1;
            volume += rho / ne;
            if (j) {
                double a = absolute_value(x - h->design[j - 1][e]);
                double b = absolute_value(rho - h->physical[j - 1][e]);
                if (a > dx) dx = a;
                if (b > drho) drho = b;
            }
        }
        if (absolute_value(volume - h->volume[j]) > 1e-12 || absolute_value(volume - physical_case.volume) > 0.005 ||
            dx != h->design_change[j] || drho != h->physical_change[j]) return 1;
    }
    if (h->count[3] != (homotopy ? end - 16 : end) ||
        h->count[1] != end + 2 + transitions + h->count[6] + h->count[7]) return 1;
    if ((h->count[5] == 0) != (h->count[7] == 0) || h->count[4] < 1) return 1;
    if (!h->count[5] && h->count[4] != end) return 1;
    return 0;
}

static int terminal_window(const HistoryWire *h, int end, int *converged) {
    if (end < 1 || end > h->count[0] || h->penalty[end] != 3) return 1;
    int first = end > 10 ? end - 10 : 0;
    int plateau = end >= 11;
    for (int j = first; j <= end; ++j) {
        if (h->penalty[j] != 3) { plateau = 0; continue; }
        double compliance;
        if (i1_audit_density(&physical_case, h->design[j], h->physical[j], h->compliance[j], &compliance)) return 1;
        if (j > first && h->physical_change[j] > 0.01) plateau = 0;
    }
    double prior = h->compliance[first], current = h->compliance[end];
    double improvement = (prior - current) / prior;
    if (!finite_scalar(improvement) || improvement < 0 || improvement > 0.0002) plateau = 0;
    *converged = h->design_change[end] <= 0.01 || plateau;
    return 0;
}

static int checked_history(const HistoryWire *h) {
    if (history_shape(h, 1)) return 1;
    int selected = h->count[4], end = h->count[0], accepted;
    int checked_before = -1, before_accepted = 0;
    if (h->count[5]) {
        int before = end - h->count[5], eligible;
        if (physical_case.nx != 24 || physical_case.ny != 12 || physical_case.nz != 6 ||
            physical_case.direction != 1 || physical_case.volume >= 0.55 || before < 11 ||
            h->design_change[before] <= 0.01 || terminal_window(h, before, &eligible) || !eligible) return 1;
        checked_before = before;
        before_accepted = eligible;
    }
    if (selected == checked_before) accepted = before_accepted;
    else if (terminal_window(h, selected, &accepted)) return 1;
    if (selected != end) {
        int endpoint;
        if (h->count[5] != 20 || selected != end - 20 ||
            terminal_window(h, end, &endpoint) || endpoint || !accepted) return 1;
    }
    if (h->count[5] > 0 && h->count[5] < 20) accepted = 0;
    return h->count[2] != accepted;
}
static int checked_terminal(const TerminalWire *wire) {
    if (!magic_is(wire->magic, "I1PUB003") || checked_history(&wire->state)) return 1;
    return i1_audit_full(&physical_case, wire->state.physical[wire->state.count[4]],
        wire->displacement, wire->reaction);
}
static int quality(const HistoryWire *h, double reference) {
    int j = h->count[4];
    return h->count[2] && h->penalty[j] == 3 &&
        absolute_value(h->volume[j] - physical_case.volume) <= 0.005 && h->compliance[j] <= 1.001 * reference;
}
static int reference_read(const char *path, double *value) {
    if (rt_read_file(path, value, 8) != 8) return 1;
    return !finite_scalar(*value) || *value <= 0;
}
static int checked_evaluation(const EvaluationWire *wire, double reference) {
    if (!magic_is(wire->magic, "I1EVAL01") || wire->outcome[3] != 0 ||
        wire->outcome[0] < 0 || wire->outcome[0] > 1 || wire->outcome[1] < 0 || wire->outcome[1] > 1 ||
        wire->outcome[2] < 0 || wire->outcome[2] > 4 || checked_terminal(&wire->terminal)) return 1;
    const HistoryWire *attempt = &wire->attempt, *returned = &wire->terminal.state;
    if (!wire->outcome[1]) {
        /* The returned terminal has already been independently reconstructed.
         * Equality of every history byte makes a second solve redundant. */
        if (wire->outcome[2] != 0 || wire->outcome[0] != 1 || !quality(returned, reference)) return 1;
        const unsigned char *a = (const unsigned char *)attempt, *b = (const unsigned char *)returned;
        for (unsigned long j = 0; j != sizeof(*attempt); ++j) if (a[j] != b[j]) return 1;
        return 0;
    }
    int rejected = 1;
    if (wire->outcome[2] == 0 || wire->outcome[2] == 4) {
        if (checked_history(attempt)) return 1;
        rejected = !quality(attempt, reference);
        if ((wire->outcome[2] == 4) != rejected) return 1;
    } else if (history_shape(attempt, 0)) return 1;
    if (wire->outcome[1] != rejected || wire->outcome[0] != quality(returned, reference)) return 1;
    {
        if (returned->count[5] || returned->count[6] || returned->count[7] || returned->penalty[0] != 3) return 1;
        double expected = physical_case.volume;
        if (absolute_value(physical_case.minimum - physical_case.volume) <= 1e-6) expected = physical_case.minimum;
        else if (absolute_value(1 - physical_case.volume) <= 1e-6) expected = 1;
        int ne = physical_case.nx * physical_case.ny * physical_case.nz;
        for (int e = 0; e != ne; ++e)
            if (returned->design[0][e] != expected || returned->physical[0][e] != expected) return 1;
    }
    return 0;
}

int i1_main(unsigned long *stack) {
    if (stack[0] == 2 && !rt_arguments(stack, 2) && rt_equal((const char *)stack[2], "--preflight")) {
        if (rt_prepare() || rt_policy(0)) return 77;
        return rt_preflight(i1_audit_storage_bytes() + sizeof(input) + sizeof(physical_case), stack);
    }
    int evaluation = stack[0] == 5 && !rt_arguments(stack, 5) &&
        rt_equal((const char *)stack[2], "--public-evaluation");
    int terminal = stack[0] == 4 && !rt_arguments(stack, 4) &&
        rt_equal((const char *)stack[2], "--public-terminal");
    if (!terminal && !evaluation) return 64;
    if (rt_prepare() || rt_policy(0)) return 77;
    if (rt_read_file((const char *)stack[3], &physical_case, sizeof(physical_case)) != (long)sizeof(physical_case) ||
        !i1_audit_case_valid(&physical_case)) return 65;
    unsigned long size = evaluation ? sizeof(input.evaluation) : sizeof(input.plain);
    if (rt_read_file((const char *)stack[4], &input, size) != (long)size) return 65;
    i1_audit_reset_count();
    int rejected;
    if (evaluation) {
        double reference;
        if (reference_read((const char *)stack[5], &reference)) return 65;
        rejected = checked_evaluation(&input.evaluation, reference);
    } else rejected = checked_terminal(&input.plain);
    unsigned long analyses = i1_audit_analysis_count();
    rt_text("PUBLIC_AUDIT_ANALYSES="); rt_uint(analyses); rt_text("\n");
    if (rejected || analyses > 48) return 66;
    rt_text(evaluation ? "PUBLIC_EVALUATION_CHECK=PASS\n" : "PUBLIC_TERMINAL_CHECK=PASS\n");
    rt_text("SEPARATE_REVIEWER_AUTHOR=1\nRESOURCE_ADMISSION=UNKNOWN\nPILOT=DENIED\n");
    return 0;
}
