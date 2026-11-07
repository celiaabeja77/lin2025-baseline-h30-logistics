"""Independently audit every saved spectrum, score, tie, and Top-K result.

Also recheck original saved grounded trace transitions with the dataset's
read-only helper. This is verification of recorded evidence, not a new UP run.
"""

import argparse
import csv
import math
import re
import runpy
from collections import Counter
from pathlib import Path

from run_all import fingerprint, sha
from src.pddl_assertions import load_domain
from src.utils import read_json, write_json


def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def canonical(text):
    return " ".join(re.findall(r"[()]|[^()\s]+", text.casefold()))


def grounded(text, assignment):
    return re.sub(r"\?[\w-]+", lambda m: assignment[m.group().casefold()], text)


def parameter_lists(text):
    # Independent parameter extraction for these non-nested STRIPS declarations.
    return {name.casefold(): re.findall(r"\?[\w-]+", args.casefold())
            for name, args in re.findall(r":action\s+(\S+)\s+:parameters\s*\(([^)]*)\)", text, re.I)}


def verify(project, output):
    manifest = read_json(output / "run_manifest.json")
    assert fingerprint(project) == manifest["input_sha256"], "Input preservation failed"
    for entry in manifest["baseline_modules_reused_byte_identically"]:
        assert sha(Path(__file__).parent / entry["copy"]) == entry["sha256"]
    summary = {r["case_id"]: r for r in rows(output / "summary.csv")}
    top = {(r["case_id"], int(r["k"])): r for r in rows(output / "top_k_summary.csv")}
    counters = Counter()
    reference_checked = set()
    # Loading this helper does not call its mutating main() function.
    recorded_trace_check = runpy.run_path(str(project / "verify_package.py"), run_name="read_only_audit")["verify_trace"]
    reference_domain = load_domain(project / "reference/domain.pddl")
    for cid in manifest["cases"]:
        path = project / cid / "domain.pddl"
        domain = load_domain(path)
        params = parameter_lists(path.read_text(encoding="utf-8-sig"))
        traces = [read_json(p) for p in sorted((project / "traces/official_2success_2failure/by_domain" / cid).glob("*.trace.json"))]
        assert len(traces) == 4 and sum(t["success"] for t in traces) == 2
        assert len({t["problem_id"] for t in traces}) == 4
        counts = {}
        vectors = {a.assertion_id: [] for a in domain.assertions}
        for trace in traces:
            plan = project / "traces/official_2success_2failure" / trace["plan_path"]
            assert trace["plan_sha256"] == sha(plan)
            counters["recorded_mutant_steps_checked"] += recorded_trace_check(trace, plan)
            counters["successful_traces" if trace["success"] else "failed_traces"] += 1
            touched = set()
            for step in trace["steps"]:
                action = step["action_name"].casefold()
                assignment = dict(zip(params[action], (arg.casefold() for arg in step["arguments"])))
                matching = [a for a in domain.assertions if a.action.casefold() == action]
                checked = {canonical(p) for p in step["grounded_preconditions"]}
                expected_checks = {canonical(grounded(a.literal, assignment)) for a in matching if a.section == "precondition"}
                assert checked == expected_checks, (cid, trace["trace_id"], step["step"], "PDDL checks")
                for component, key in (("add_effect", "grounded_effect_add_list"), ("delete_effect", "grounded_effect_delete_list")):
                    expected_effects = set()
                    for assertion in matching:
                        if assertion.component_type == component:
                            literal = grounded(assertion.literal, assignment)
                            if component == "delete_effect":
                                literal = re.fullmatch(r"\(not\s+(.*)\)", literal, re.I).group(1)
                            expected_effects.add(canonical(literal))
                    assert expected_effects == {canonical(p) for p in step[key]}, (cid, "PDDL effects")
                if step["attempted"]:
                    for assertion in matching:
                        if (assertion.section == "precondition" and canonical(grounded(assertion.literal, assignment)) in checked) or (assertion.section == "effect" and step["executed"]):
                            touched.add(assertion.assertion_id)
            for assertion in domain.assertions:
                vectors[assertion.assertion_id].append(int(assertion.assertion_id in touched))
            reference_path = project / "traces/official_2success_2failure/evaluation/reference_traces" / (trace["problem_id"] + ".trace.json")
            reference = read_json(reference_path)
            assert reference["success"] and reference["problem_goals"] == trace["problem_goals"]
            assert reference["plan_sha256"] == trace["plan_sha256"]
            assert reference["problem_sha256"] == trace["problem_sha256"]
            if reference_path not in reference_checked:
                recorded_trace_check(reference, plan)
                reference_checked.add(reference_path)
        F = sum(not t["success"] for t in traces)
        for aid, vector in vectors.items():
            ef = sum(v for v, t in zip(vector, traces) if not t["success"])
            ep = sum(v for v, t in zip(vector, traces) if t["success"])
            score = ef / math.sqrt(F * (ef + ep)) if F * (ef + ep) else 0.0
            counts[aid] = (ef, ep, score)
        saved_matrix = {r["assertion_id"]: r for r in rows(output / cid / "coverage_matrix.csv")}
        ranking = rows(output / cid / "ranking.csv")
        blind = rows(output / cid / "ranking_blind.csv")
        assert sha(output / cid / "ranking_blind.csv") == manifest["blind_ranking_sha256"][cid]
        assert len(ranking) == len(domain.assertions) == len(blind)
        assert [{k: v for k, v in r.items() if k != "is_ground_truth"} for r in ranking] == blind
        for row in ranking:
            aid = row["assertion_id"]
            assert [int(saved_matrix[aid][t["trace_id"]]) for t in traces] == vectors[aid]
            ef, ep, score = counts[aid]
            assert (int(row["ef"]), int(row["ep"]), int(row["total_failure_traces"])) == (ef, ep, F)
            assert float(row["ochiai"]) == score
            better = sum(c[2] > score for c in counts.values())
            tied = sum(c[2] == score for c in counts.values())
            assert (int(row["best_rank"]), int(row["worst_rank"]), int(row["tie_group_size"])) == (better + 1, better + tied, tied)
            assert float(row["average_rank"]) == (2 * better + 1 + tied) / 2
        gold = read_json(project / "evaluation" / cid / "fault_info.json")
        # Independently check the single declared add/delete/replace against D*.
        expected = [(a.action.casefold(), a.section, canonical(a.literal)) for a in reference_domain.assertions]
        target = [i for i, a in enumerate(reference_domain.assertions)
                  if a.action.casefold() == gold["faulty_action"].casefold() and a.section == gold["component"].lstrip(":")]
        offset = gold["original_slot_1based"] - 1
        actual = [(a.action.casefold(), a.section, canonical(a.literal)) for a in domain.assertions]
        original, replacement = gold["original_assertion"], gold["replacement_assertion"]
        if original is None:
            position = target[-1] + 1 if offset == len(target) else target[offset]
            expected.insert(position, (gold["faulty_action"].casefold(), gold["component"].lstrip(":"), canonical(replacement)))
        else:
            position = target[offset]
            assert expected[position][2] == canonical(original)
            if replacement is None:
                expected.pop(position)
            else:
                expected[position] = (expected[position][0], expected[position][1], canonical(replacement))
        assert actual == expected, (cid, "single edit differs from gold")
        marked = [r for r in ranking if r["is_ground_truth"] == "true"]
        if replacement is None:
            assert not marked and summary[cid]["ground_truth_in_candidate_set"] == "false"
            assert all(summary[cid][key] == "" for key in ("ef", "ep", "ground_truth_score", "best_rank", "worst_rank", "tie_group_size"))
            counters["missing_assertion_cases"] += 1
        else:
            assert len(marked) == 1 and canonical(marked[0]["literal"]) == canonical(replacement)
            assert summary[cid]["ground_truth_assertion"] == marked[0]["assertion_id"]
            for field in ("ef", "ep", "best_rank", "worst_rank", "average_rank", "tie_group_size"):
                assert summary[cid][field] == marked[0][field]
            assert summary[cid]["ground_truth_score"] == marked[0]["ochiai"]
            counters["rankable_cases"] += 1
        for k in (1, 3, 5):
            selected = [r for r in ranking if int(r["best_rank"]) <= k]
            assert rows(output / cid / f"top{k}.csv") == selected
            row = top[(cid, k)]
            assert int(row["num_candidates"]) == len(selected)
            strict = bool(marked and int(marked[0]["worst_rank"]) <= k)
            aware = bool(marked and int(marked[0]["best_rank"]) <= k)
            assert row["strict_hit"] == summary[cid][f"strict_top{k}"] == str(strict).lower()
            assert row["tie_aware_hit"] == summary[cid][f"tie_aware_top{k}"] == str(aware).lower()
        counters["assertion_rows_checked"] += len(ranking)
        counters["coverage_bits_checked"] += len(ranking) * len(traces)
        counters["cases_checked"] += 1
    for metric in rows(output / "top_k_metrics.csv"):
        k = int(metric["k"])
        selected = [r for (cid, kk), r in top.items() if kk == k and
                    (metric["scope"].startswith("all_cases") or summary[cid]["ground_truth_in_candidate_set"] == "true")]
        assert int(metric["num_evaluated_cases"]) == len(selected)
        for name in ("strict", "tie_aware"):
            hits = sum(r[name + "_hit"] == "true" for r in selected)
            assert int(metric[name + "_hits"]) == hits
            assert float(metric[name + "_accuracy"]) == hits / len(selected)
    assert fingerprint(project) == manifest["input_sha256"]
    audit = {"status": "pass", **counters, "reference_traces_checked": len(reference_checked),
             "input_files_unchanged": True, "blind_and_evaluated_rankings_identical_except_gold_marker": True,
             "all_source_grounded_conditions_and_effects_match_parsed_PDDL": True,
             "all_single_assertion_edits_rechecked_against_reference": True,
             "all_topk_candidate_lists_and_both_metric_denominators_recomputed": True,
             "verification_scope": "Independent saved-evidence arithmetic and recorded transition checks; no new planner/simulator run"}
    write_json(output / "verification.json", audit)
    print(audit)
    return audit


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=root.parent / "experiments/logistics_challenge_30_validated")
    parser.add_argument("--results", type=Path, default=root / "results")
    args = parser.parse_args()
    verify(args.project.resolve(), args.results.resolve())
