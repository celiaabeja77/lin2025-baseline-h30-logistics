"""Exact-score ties receive one shared rank interval, never an arbitrary rank."""

import math
from dataclasses import asdict
from itertools import groupby

from .ochiai import ochiai


def tie_aware_ranking(rows):
    rows = [dict(row) for row in rows]
    if len({row["assertion_id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate assertion_id in ranking.")
    if any(not math.isfinite(row["ochiai"]) or not 0 <= row["ochiai"] <= 1 for row in rows):
        raise ValueError("Ochiai scores must be finite and between zero and one.")
    # Stable order inside a group is display order only; no per-item rank exists.
    rows.sort(key=lambda row: row["ochiai"], reverse=True)
    ranked, start = [], 1
    for _, group in groupby(rows, key=lambda row: row["ochiai"]):
        tied = list(group)
        end = start + len(tied) - 1
        for row in tied:
            row.update(best_rank=start, worst_rank=end, average_rank=(start + end) / 2,
                       tie_group_size=len(tied))
            ranked.append(row)
        start = end + 1
    return ranked


def rank_assertions(case_id, assertions, counts):
    rows = []
    for assertion in assertions:
        fields = asdict(assertion)
        fields.pop("index")
        spectrum = counts[assertion.assertion_id]
        rows.append({"case_id": case_id, **fields, **spectrum,
                     "ochiai": ochiai(spectrum["ef"], spectrum["ep"],
                                      spectrum["total_failure_traces"])})
    return tie_aware_ranking(rows)
