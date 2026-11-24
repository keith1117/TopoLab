"""Original 4,500-second clock for the formal R1 timing campaign."""

START_MS = 1795476230895
GLOBAL_END_MS = 1795670630895
WHOLE_MS = 4500 * 1000
RESULT_SUFFIX_MS = 7200 * 1000


def check(value, now_ms):
    start, end = value.get("whole_start_ms"), value.get("whole_end_ms")
    if (
        type(start) is not int
        or type(end) is not int
        or type(now_ms) is not int
        or not START_MS <= start <= now_ms <= end
        or end != start + WHOLE_MS
        or end + RESULT_SUFFIX_MS > GLOBAL_END_MS
    ):
        raise ValueError("NEW whole4500 original clock/bounds differ or exhausted")
    return end


def declare(requested_ms, now_ms):
    if type(requested_ms) is not int or type(now_ms) is not int or now_ms < requested_ms:
        raise ValueError("NEW original requested clock invalid/backwards")
    if requested_ms + WHOLE_MS + RESULT_SUFFIX_MS > GLOBAL_END_MS:
        raise ValueError("NEW complete4500 plus7200 result suffix unavailable")
    if now_ms - requested_ms > 30000:
        raise ValueError("NEW prepare prefix exhausted original first-SUP30 clock")
    value = {"whole_start_ms": requested_ms, "whole_end_ms": requested_ms + WHOLE_MS}
    check(value, now_ms)
    return value


def result_end(value, result_start_ms):
    end = check(value, result_start_ms)
    return min(result_start_ms + 1800 * 1000, end)
