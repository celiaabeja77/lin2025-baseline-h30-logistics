"""The only suspiciousness formula in this baseline."""

import math


def ochiai(ef, ep, total_failure_traces):
    if any(type(value) is not int or value < 0 for value in (ef, ep, total_failure_traces)):
        raise ValueError("ef, ep and F must be non-negative integer counts.")
    if ef > total_failure_traces:
        raise ValueError("ef cannot exceed F.")
    F = total_failure_traces
    denominator = math.sqrt(F * (ef + ep))
    if denominator == 0:
        return 0.0
    score = ef / math.sqrt(F * (ef + ep))
    return score
